"""Deterministic RawCollectorRecord to CandidateItem normalization."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
import ipaddress
import json
from typing import Sequence
from urllib.parse import urlsplit, urlunsplit

from collectors.base import CollectionBatch, RawCollectorRecord
from pipeline.errors import AutomationError
from pipeline.models import (
    CandidateItem,
    CollectionStatus,
    CollectorType,
    EternaTag,
    FactCitation,
    ModelValidationError,
    Region,
    SourceCredibility,
    SourcePriority,
    SourceType,
)
from pipeline.registry import (
    RegistryEntry,
    RegistryValidationError,
    SourceRegistry,
)
from pipeline.state import (
    RegionState,
    StateError,
    register_candidate_observation,
)


class NormalizationError(AutomationError):
    """One record cannot be normalized without guessing or weakening a gate."""


@dataclass(frozen=True, slots=True)
class NormalizationItemError:
    item_index: int
    source_reference: str
    message: str

    def __post_init__(self) -> None:
        if type(self.item_index) is not int or self.item_index < 0:
            raise ValueError("item_index must be a non-negative integer")
        if type(self.source_reference) is not str or not self.source_reference:
            raise ValueError("source_reference must be non-empty text")
        if type(self.message) is not str or not self.message or len(self.message) > 512:
            raise ValueError("message must be bounded non-empty text")


@dataclass(frozen=True, slots=True)
class NormalizationBatch:
    candidates: tuple[CandidateItem, ...]
    item_errors: tuple[NormalizationItemError, ...]
    state: RegionState

    def __post_init__(self) -> None:
        candidates = tuple(self.candidates)
        item_errors = tuple(self.item_errors)
        if any(type(item) is not CandidateItem for item in candidates):
            raise ValueError("candidates must contain CandidateItem values")
        if any(type(item) is not NormalizationItemError for item in item_errors):
            raise ValueError("item_errors must contain NormalizationItemError values")
        if type(self.state) is not RegionState:
            raise ValueError("state must be a RegionState")
        object.__setattr__(self, "candidates", candidates)
        object.__setattr__(self, "item_errors", item_errors)


def _canonical_json(value: object) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        allow_nan=False,
        sort_keys=True,
        separators=(",", ":"),
    )


def _sha256(value: object) -> str:
    return hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest()


def _public_hostname(hostname: str) -> str:
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        pass
    else:
        if not address.is_global:
            raise NormalizationError("Source URL must not use a non-public IP address")
        return address.compressed.lower()
    try:
        normalized = hostname.encode("idna").decode("ascii").lower()
    except UnicodeError as exc:
        raise NormalizationError("Source URL hostname is invalid") from exc
    if normalized == "localhost" or normalized.endswith(".local"):
        raise NormalizationError("Source URL must use a public hostname")
    return normalized


def canonicalize_public_url(value: str) -> str:
    """Canonicalize syntax only; never resolve redirects or infer a destination."""

    if type(value) is not str or not value or value != value.strip():
        raise NormalizationError("Source URL must be non-empty trimmed text")
    if any(character.isspace() for character in value):
        raise NormalizationError("Source URL must not contain whitespace")
    try:
        parsed = urlsplit(value)
        port = parsed.port
    except ValueError as exc:
        raise NormalizationError("Source URL is malformed") from exc
    scheme = parsed.scheme.lower()
    if scheme not in {"http", "https"} or parsed.hostname is None:
        raise NormalizationError("Source URL must be public HTTP(S)")
    if parsed.username is not None or parsed.password is not None:
        raise NormalizationError("Source URL must not contain userinfo credentials")

    hostname = _public_hostname(parsed.hostname)
    rendered_host = f"[{hostname}]" if ":" in hostname else hostname
    if port is not None and not (
        (scheme == "http" and port == 80) or (scheme == "https" and port == 443)
    ):
        rendered_host = f"{rendered_host}:{port}"
    return urlunsplit(
        (scheme, rendered_host, parsed.path or "/", parsed.query, "")
    )


def _registered_orgs(entry: RegistryEntry, host: str) -> tuple[str, ...]:
    organizations: list[str] = []
    for url in entry.urls:
        try:
            parsed = urlsplit(canonicalize_public_url(url))
        except NormalizationError:
            continue
        parts = tuple(part for part in parsed.path.split("/") if part)
        if parsed.hostname == host and len(parts) == 1 and not parsed.query:
            organizations.append(parts[0])
    return tuple(organizations)


def _validate_api_source_url(
    canonical_url: str,
    collector_type: CollectorType,
    entry: RegistryEntry,
) -> None:
    if collector_type is not CollectorType.OFFICIAL_API:
        return
    parsed = urlsplit(canonical_url)
    parts = tuple(part for part in parsed.path.split("/") if part)
    host = parsed.hostname or ""

    if host == "github.com":
        allowed = _registered_orgs(entry, "github.com")
        if (
            parsed.scheme != "https"
            or len(parts) < 2
            or not allowed
            or parts[0].casefold() not in {item.casefold() for item in allowed}
        ):
            raise NormalizationError(
                "GitHub record URL does not belong to the registered organization"
            )
        return

    if host == "huggingface.co":
        allowed = _registered_orgs(entry, "huggingface.co")
        if parts and parts[0] in {"datasets", "spaces"}:
            organization_index = 1
        else:
            organization_index = 0
        if (
            parsed.scheme != "https"
            or len(parts) <= organization_index + 1
            or not allowed
            or parts[organization_index].casefold()
            not in {item.casefold() for item in allowed}
        ):
            raise NormalizationError(
                "Hugging Face record URL does not belong to the registered organization"
            )
        return

    raise NormalizationError("Official API record uses an unsupported public host")


def _identity_material(
    record: RawCollectorRecord,
    canonical_url: str,
) -> dict[str, str]:
    source_object_id = record.source_object_id
    if source_object_id is not None:
        identity_kind = "source_object_id"
        identity_value = source_object_id
    else:
        identity_kind = "canonical_url"
        identity_value = canonical_url
    if not identity_value:
        raise NormalizationError("Candidate identity has no stable source basis")
    return {
        "region": record.region.value,
        "source_reference": record.source_reference,
        "identity_kind": identity_kind,
        "identity_value": identity_value,
    }


def candidate_identity(
    record: RawCollectorRecord,
    canonical_url: str,
) -> tuple[str, str]:
    """Return deterministic observation and Candidate identities."""

    material = _identity_material(record, canonical_url)
    candidate_digest = _sha256({"namespace": "candidate-v1", **material})
    observation_digest = _sha256({"namespace": "observation-v1", **material})
    return f"observation_{observation_digest}", f"candidate_{candidate_digest}"


def _normalized_datetime(value: datetime | None) -> str | None:
    if value is None:
        return None
    return value.astimezone(UTC).isoformat().replace("+00:00", "Z")


def content_fingerprint(record: RawCollectorRecord, canonical_url: str) -> str:
    """Fingerprint source content while excluding observation time."""

    return _sha256(
        {
            "title": record.title,
            "excerpt": record.excerpt,
            "source_published_at": _normalized_datetime(record.published_at),
            "source_url": canonical_url,
        }
    )


def _registry_projection(
    registry: SourceRegistry,
    record: RawCollectorRecord,
) -> tuple[
    RegistryEntry,
    SourceType,
    SourcePriority,
    SourceCredibility,
    FactCitation,
    tuple[EternaTag, ...],
]:
    try:
        entry = registry.get(record.source_reference)
        source_type = SourceType(entry.source_type)
        priority = SourcePriority(entry.priority)
        credibility = SourceCredibility(entry.credibility)
        fact_citation = FactCitation(entry.fact_citation)
        eterna_tags = tuple(EternaTag(value) for value in entry.eterna_tags)
    except (RegistryValidationError, ValueError) as exc:
        raise NormalizationError(
            "Source Registry fields cannot be projected without guessing"
        ) from exc
    if entry.region != record.region.value:
        raise NormalizationError("Raw record Region does not match Source Registry")
    return entry, source_type, priority, credibility, fact_citation, eterna_tags


def normalize_record(
    record: RawCollectorRecord,
    registry: SourceRegistry,
    state: RegionState,
) -> tuple[CandidateItem, RegionState]:
    """Normalize one record and return its immutable Candidate plus updated State."""

    if type(record) is not RawCollectorRecord:
        raise NormalizationError("record must be a RawCollectorRecord")
    if type(registry) is not SourceRegistry:
        raise NormalizationError("registry must be a SourceRegistry")
    if type(state) is not RegionState:
        raise NormalizationError("state must be a RegionState")
    if record.region is not state.region:
        raise NormalizationError("Raw record Region does not match RegionState")

    (
        registry_entry,
        source_type,
        priority,
        credibility,
        fact_citation,
        eterna_tags,
    ) = _registry_projection(registry, record)
    canonical_url = canonicalize_public_url(record.source_url)
    _validate_api_source_url(canonical_url, record.collector_type, registry_entry)
    observation_key, candidate_id = candidate_identity(record, canonical_url)
    fingerprint = content_fingerprint(record, canonical_url)

    try:
        updated_state = register_candidate_observation(
            state,
            observation_key=observation_key,
            candidate_id=candidate_id,
            source_reference=record.source_reference,
            observed_at=record.collected_at,
            canonical_url=canonical_url,
            source_object_id=record.source_object_id,
            content_fingerprint=fingerprint,
        )
        state_record = next(
            item
            for item in updated_state.candidates
            if item.observation_key == observation_key
        )
        candidate = CandidateItem(
            candidate_id=candidate_id,
            region=record.region,
            source_reference=record.source_reference,
            source_type=source_type,
            source_priority=priority,
            source_credibility=credibility,
            source_fact_citation=fact_citation,
            collector_type=record.collector_type,
            source_url=canonical_url,
            title=record.title,
            source_excerpt=record.excerpt,
            source_published_at=record.published_at,
            collected_at=record.collected_at,
            first_seen_at=state_record.first_seen_at,
            last_seen_at=state_record.last_seen_at,
            eterna_tags=eterna_tags,
            raw_evidence_reference=record.raw_reference,
            collection_status=(
                CollectionStatus.COLLECTED
                if record.excerpt is not None
                else CollectionStatus.METADATA_ONLY
            ),
        )
    except (StateError, ModelValidationError, StopIteration) as exc:
        raise NormalizationError(
            "Candidate normalization violated frozen state or model rules"
        ) from exc
    return candidate, updated_state


def normalize_batch(
    records: CollectionBatch | Sequence[RawCollectorRecord],
    registry: SourceRegistry,
    state: RegionState,
) -> NormalizationBatch:
    """Normalize valid siblings in input order and expose each rejected record."""

    if type(records) is CollectionBatch:
        raw_records = records.records
    elif isinstance(records, Sequence) and not isinstance(records, (str, bytes)):
        raw_records = tuple(records)
    else:
        raise NormalizationError("records must be a CollectionBatch or record sequence")

    candidates: list[CandidateItem] = []
    errors: list[NormalizationItemError] = []
    current_state = state
    for index, record in enumerate(raw_records):
        if type(record) is not RawCollectorRecord:
            errors.append(
                NormalizationItemError(
                    item_index=index,
                    source_reference="Unknown source",
                    message="Item is not a RawCollectorRecord",
                )
            )
            continue
        try:
            candidate, next_state = normalize_record(record, registry, current_state)
        except NormalizationError as exc:
            errors.append(
                NormalizationItemError(
                    item_index=index,
                    source_reference=record.source_reference,
                    message=str(exc)[:512],
                )
            )
            continue
        candidates.append(candidate)
        current_state = next_state
    return NormalizationBatch(tuple(candidates), tuple(errors), current_state)


__all__ = (
    "NormalizationBatch",
    "NormalizationError",
    "NormalizationItemError",
    "candidate_identity",
    "canonicalize_public_url",
    "content_fingerprint",
    "normalize_batch",
    "normalize_record",
)
