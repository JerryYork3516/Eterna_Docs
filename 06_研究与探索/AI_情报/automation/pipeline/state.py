"""Region-isolated, non-sensitive state with strict recovery boundaries."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import date, datetime
from enum import Enum
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
from typing import TypeVar
from urllib.parse import urlsplit

from pipeline.errors import AutomationError
from pipeline.models import EvidenceRelation, InformationStatus, Region, StatusHistoryEntry
from pipeline.path_policy import (
    PathPolicyError,
    validate_legacy_state_path,
    validate_write_path,
)


SUPPORTED_STATE_SCHEMA_VERSION = 1
STATE_PATHS = {
    Region.GLOBAL: "06_研究与探索/AI_情报/automation/state/global.json",
    Region.CHINA: "06_研究与探索/AI_情报/automation/state/china.json",
}

_SHA256_PATTERN = re.compile(r"[0-9a-f]{64}")
_GIT_SHA_PATTERN = re.compile(r"[0-9a-f]{40}")
_DATE_PATTERN = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")
_EMAIL_PATTERN = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_CREDENTIAL_PATTERNS = (
    re.compile(r"\bBearer\s+[A-Za-z0-9._~+/=-]+", re.IGNORECASE),
    re.compile(r"\bsk-[A-Za-z0-9_-]{12,}"),
    re.compile(r"\bgh[pousr]_[A-Za-z0-9]{12,}"),
)


class StateError(AutomationError):
    """Base error for persisted Region state."""


class StateValidationError(StateError):
    """Raised when state does not satisfy its strict schema or invariants."""


class StateConflictError(StateError):
    """Raised when an existing stable identity would be rewritten."""


class StaleStateError(StateError):
    """Raised when optimistic concurrency detects a newer state file."""


class StateIOError(StateError):
    """Raised when a state file cannot be loaded or atomically saved."""


class DeliveryStatus(str, Enum):
    NOT_ATTEMPTED = "Not attempted"
    IN_PROGRESS = "In progress"
    DELIVERED = "Delivered"
    DELIVERY_FAILED = "Delivery failed"


class GitCommitStatus(str, Enum):
    NOT_COMMITTED = "Not committed"
    COMMIT_FAILED = "Commit failed"
    COMMITTED = "Committed"
    PUSH_FAILED = "Push failed"
    PUSHED = "Pushed"


def _text(value: object, field_name: str, *, max_length: int = 8192) -> str:
    if type(value) is not str or not value or value != value.strip():
        raise StateValidationError(f"{field_name} must be non-empty trimmed text")
    if len(value) > max_length:
        raise StateValidationError(f"{field_name} exceeds the maximum supported length")
    if _EMAIL_PATTERN.search(value) or any(pattern.search(value) for pattern in _CREDENTIAL_PATTERNS):
        raise StateValidationError(f"{field_name} contains forbidden sensitive content")
    return value


def _optional_text(value: object, field_name: str, *, max_length: int = 8192) -> str | None:
    if value is None:
        return None
    return _text(value, field_name, max_length=max_length)


def _aware_datetime(value: object, field_name: str) -> datetime:
    if type(value) is not datetime:
        raise StateValidationError(f"{field_name} must be a datetime")
    try:
        offset = value.utcoffset()
    except (OverflowError, ValueError) as exc:
        raise StateValidationError(f"{field_name} has an invalid timezone") from exc
    if value.tzinfo is None or offset is None:
        raise StateValidationError(f"{field_name} must be timezone-aware")
    return value


def _date(value: object, field_name: str) -> date:
    if type(value) is not date:
        raise StateValidationError(f"{field_name} must be a date")
    return value


def _enum(value: object, enum_type: type[Enum], field_name: str) -> None:
    if type(value) is not enum_type:
        raise StateValidationError(f"{field_name} must be a {enum_type.__name__} value")


def _items(value: object, expected_type: type, field_name: str) -> tuple:
    if type(value) not in {list, tuple}:
        raise StateValidationError(f"{field_name} must be an ordered list or tuple")
    result = tuple(value)
    if any(type(item) is not expected_type for item in result):
        raise StateValidationError(
            f"{field_name} entries must be {expected_type.__name__} values"
        )
    return result


def _references(value: object, field_name: str, *, nonempty: bool = False) -> tuple[str, ...]:
    result = _items(value, str, field_name)
    if nonempty and not result:
        raise StateValidationError(f"{field_name} must not be empty")
    for item in result:
        _text(item, f"{field_name} entry", max_length=512)
    if len(set(result)) != len(result):
        raise StateValidationError(f"{field_name} must not contain duplicates")
    return result


def _sha256(value: object, field_name: str) -> str:
    if type(value) is not str or _SHA256_PATTERN.fullmatch(value) is None:
        raise StateValidationError(f"{field_name} must be a lowercase SHA-256 hex digest")
    return value


def _optional_sha256(value: object, field_name: str) -> str | None:
    if value is None:
        return None
    return _sha256(value, field_name)


def _public_url(value: object, field_name: str) -> str:
    url = _text(value, field_name)
    if any(character.isspace() for character in url):
        raise StateValidationError(f"{field_name} must not contain whitespace")
    try:
        parsed = urlsplit(url)
        _ = parsed.port
    except ValueError as exc:
        raise StateValidationError(f"{field_name} is malformed") from exc
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        raise StateValidationError(f"{field_name} must be an http or https URL")
    if parsed.username is not None or parsed.password is not None:
        raise StateValidationError(f"{field_name} must not contain credentials")
    return url


def _optional_public_url(value: object, field_name: str) -> str | None:
    if value is None:
        return None
    return _public_url(value, field_name)


def _revision(value: object) -> int:
    if type(value) is not int or value < 1:
        raise StateValidationError("revision must be a positive integer")
    return value


@dataclass(frozen=True, slots=True)
class CandidateStateRecord:
    observation_key: str
    candidate_id: str
    source_reference: str
    canonical_url: str | None
    source_object_id: str | None
    content_fingerprint: str | None
    first_seen_at: datetime
    last_seen_at: datetime

    def __post_init__(self) -> None:
        _text(self.observation_key, "observation_key", max_length=512)
        _text(self.candidate_id, "candidate_id", max_length=512)
        _text(self.source_reference, "source_reference", max_length=512)
        _optional_public_url(self.canonical_url, "canonical_url")
        _optional_text(self.source_object_id, "source_object_id", max_length=1024)
        _optional_sha256(self.content_fingerprint, "content_fingerprint")
        if self.canonical_url is None and self.source_object_id is None and self.content_fingerprint is None:
            raise StateValidationError("candidate state requires at least one stable observation basis")
        _aware_datetime(self.first_seen_at, "first_seen_at")
        _aware_datetime(self.last_seen_at, "last_seen_at")
        if self.last_seen_at < self.first_seen_at:
            raise StateValidationError("last_seen_at must not precede first_seen_at")


@dataclass(frozen=True, slots=True)
class EvidenceStateRecord:
    evidence_id: str
    candidate_references: tuple[str, ...]
    relation: EvidenceRelation = EvidenceRelation.SUPPORTS
    independent_confirmation: bool = True
    duplicate_of_evidence_id: str | None = None
    content_signature: str | None = None

    def __post_init__(self) -> None:
        _text(self.evidence_id, "evidence_id", max_length=512)
        object.__setattr__(
            self,
            "candidate_references",
            _references(self.candidate_references, "candidate_references", nonempty=True),
        )
        _enum(self.relation, EvidenceRelation, "relation")
        if type(self.independent_confirmation) is not bool:
            raise StateValidationError("independent_confirmation must be a boolean")
        _optional_text(
            self.duplicate_of_evidence_id,
            "duplicate_of_evidence_id",
            max_length=512,
        )
        if self.independent_confirmation and self.duplicate_of_evidence_id is not None:
            raise StateValidationError(
                "independent Evidence must not reference a duplicate Evidence"
            )
        if not self.independent_confirmation and self.duplicate_of_evidence_id is None:
            raise StateValidationError(
                "non-independent Evidence requires duplicate_of_evidence_id"
            )
        if self.duplicate_of_evidence_id == self.evidence_id:
            raise StateValidationError("Evidence must not be a duplicate of itself")
        _optional_sha256(self.content_signature, "content_signature")


@dataclass(frozen=True, slots=True)
class EventStateRecord:
    event_id: str
    evidence_references: tuple[str, ...]
    initial_status: InformationStatus | None
    information_status: InformationStatus | None
    status_history: tuple[StatusHistoryEntry, ...]

    def __post_init__(self) -> None:
        _text(self.event_id, "event_id", max_length=512)
        object.__setattr__(
            self,
            "evidence_references",
            _references(self.evidence_references, "evidence_references", nonempty=True),
        )
        if (self.initial_status is None) is not (self.information_status is None):
            raise StateValidationError(
                "Event analysis status must be entirely absent or entirely present"
            )
        if self.initial_status is not None:
            _enum(self.initial_status, InformationStatus, "initial_status")
            _enum(self.information_status, InformationStatus, "information_status")
        history = _items(self.status_history, StatusHistoryEntry, "status_history")
        if self.initial_status is None and history:
            raise StateValidationError("pre-analysis Event must not have status_history")
        for index, entry in enumerate(history):
            _aware_datetime(entry.changed_at, f"status_history[{index}].changed_at")
            _text(entry.reason, f"status_history[{index}].reason")
            if entry.previous_status is entry.new_status:
                raise StateValidationError("status_history entries must change status")
            if index and entry.changed_at < history[index - 1].changed_at:
                raise StateValidationError("status_history timestamps must not regress")
            if index and entry.previous_status is not history[index - 1].new_status:
                raise StateValidationError("status_history status chain is inconsistent")
            if any(reference not in self.evidence_references for reference in entry.evidence_references):
                raise StateValidationError("status_history references unknown Event evidence")
        if history:
            if history[0].previous_status is not self.initial_status:
                raise StateValidationError("status_history initial status is inconsistent")
            if history[-1].new_status is not self.information_status:
                raise StateValidationError("information_status must match the final history status")
        elif self.information_status is not self.initial_status:
            raise StateValidationError("Event without history must retain its initial status")
        object.__setattr__(self, "status_history", history)


@dataclass(frozen=True, slots=True)
class ReportStateRecord:
    idempotency_key: str
    region: Region
    report_date: date
    revision: int
    report_path: str
    content_hash: str
    git_status: GitCommitStatus
    commit_sha: str | None

    def __post_init__(self) -> None:
        _text(self.idempotency_key, "idempotency_key", max_length=512)
        _enum(self.region, Region, "region")
        _date(self.report_date, "report_date")
        _revision(self.revision)
        _text(self.report_path, "report_path")
        _sha256(self.content_hash, "content_hash")
        _enum(self.git_status, GitCommitStatus, "git_status")
        if self.commit_sha is not None and (
            type(self.commit_sha) is not str
            or _GIT_SHA_PATTERN.fullmatch(self.commit_sha) is None
        ):
            raise StateValidationError("commit_sha must be a lowercase 40-character Git SHA")
        if self.git_status in {
            GitCommitStatus.COMMITTED,
            GitCommitStatus.PUSH_FAILED,
            GitCommitStatus.PUSHED,
        }:
            if self.commit_sha is None:
                raise StateValidationError(
                    "committed, push-failed, or pushed reports require commit_sha"
                )
        elif self.commit_sha is not None:
            raise StateValidationError(
                "not-committed or commit-failed reports must not carry commit_sha"
            )
        if self.idempotency_key != report_idempotency_key(
            self.region, self.report_date, self.revision
        ):
            raise StateValidationError("report idempotency_key is inconsistent")
        if self.report_path != report_path(self.region, self.report_date):
            raise StateValidationError("report_path is inconsistent with Region and report_date")


@dataclass(frozen=True, slots=True)
class DeliveryStateRecord:
    idempotency_key: str
    region: Region
    report_date: date
    revision: int
    status: DeliveryStatus

    def __post_init__(self) -> None:
        _text(self.idempotency_key, "idempotency_key", max_length=512)
        _enum(self.region, Region, "region")
        _date(self.report_date, "report_date")
        _revision(self.revision)
        _enum(self.status, DeliveryStatus, "status")
        if self.idempotency_key != delivery_idempotency_key(
            self.region, self.report_date, self.revision
        ):
            raise StateValidationError("delivery idempotency_key is inconsistent")


Record = TypeVar(
    "Record",
    CandidateStateRecord,
    EvidenceStateRecord,
    EventStateRecord,
    ReportStateRecord,
    DeliveryStateRecord,
)


def _unique_sorted(records: object, expected_type: type[Record], key_name: str) -> tuple[Record, ...]:
    items = _items(records, expected_type, expected_type.__name__)
    keys = [getattr(item, key_name) for item in items]
    if len(set(keys)) != len(keys):
        raise StateValidationError(f"duplicate {key_name} in Region state")
    return tuple(sorted(items, key=lambda item: getattr(item, key_name)))


@dataclass(frozen=True, slots=True)
class RegionState:
    schema_version: int
    region: Region
    candidates: tuple[CandidateStateRecord, ...]
    evidences: tuple[EvidenceStateRecord, ...]
    events: tuple[EventStateRecord, ...]
    reports: tuple[ReportStateRecord, ...]
    deliveries: tuple[DeliveryStateRecord, ...]

    def __post_init__(self) -> None:
        if type(self.schema_version) is not int or self.schema_version != SUPPORTED_STATE_SCHEMA_VERSION:
            raise StateValidationError(f"unsupported schema_version: {self.schema_version!r}")
        _enum(self.region, Region, "region")
        candidates = _unique_sorted(self.candidates, CandidateStateRecord, "observation_key")
        evidences = _unique_sorted(self.evidences, EvidenceStateRecord, "evidence_id")
        events = _unique_sorted(self.events, EventStateRecord, "event_id")
        reports = _unique_sorted(self.reports, ReportStateRecord, "idempotency_key")
        deliveries = _unique_sorted(self.deliveries, DeliveryStateRecord, "idempotency_key")
        if any(record.region is not self.region for record in reports):
            raise StateValidationError("report Region does not match Region state")
        if any(record.region is not self.region for record in deliveries):
            raise StateValidationError("delivery Region does not match Region state")
        candidate_ids = {record.candidate_id for record in candidates}
        if any(
            reference not in candidate_ids
            for evidence in evidences
            for reference in evidence.candidate_references
        ):
            raise StateValidationError("Evidence state references an unknown candidate_id")
        evidence_ids = {record.evidence_id for record in evidences}
        if any(
            evidence.duplicate_of_evidence_id not in evidence_ids
            for evidence in evidences
            if evidence.duplicate_of_evidence_id is not None
        ):
            raise StateValidationError("Evidence duplicate references an unknown evidence_id")
        if any(
            reference not in evidence_ids
            for event in events
            for reference in event.evidence_references
        ):
            raise StateValidationError("Event state references an unknown evidence_id")
        evidence_by_id = {record.evidence_id: record for record in evidences}
        if any(
            evidence_by_id[reference].duplicate_of_evidence_id
            not in event.evidence_references
            for event in events
            for reference in event.evidence_references
            if evidence_by_id[reference].duplicate_of_evidence_id is not None
        ):
            raise StateValidationError(
                "Near Duplicate Evidence and its primary must remain in the same Event"
            )
        report_keys = {record.idempotency_key for record in reports}
        if any(
            report_idempotency_key(record.region, record.report_date, record.revision)
            not in report_keys
            for record in deliveries
        ):
            raise StateValidationError("Delivery state has no matching Report state")
        object.__setattr__(self, "candidates", candidates)
        object.__setattr__(self, "evidences", evidences)
        object.__setattr__(self, "events", events)
        object.__setattr__(self, "reports", reports)
        object.__setattr__(self, "deliveries", deliveries)


@dataclass(frozen=True, slots=True)
class LoadedRegionState:
    state: RegionState
    digest: str


def empty_region_state(region: Region) -> RegionState:
    _enum(region, Region, "region")
    return RegionState(
        schema_version=SUPPORTED_STATE_SCHEMA_VERSION,
        region=region,
        candidates=(),
        evidences=(),
        events=(),
        reports=(),
        deliveries=(),
    )


def format_revision(revision: int) -> str:
    return f"r{_revision(revision)}"


def report_idempotency_key(region: Region, report_date_value: date, revision: int) -> str:
    _enum(region, Region, "region")
    _date(report_date_value, "report_date")
    return f"report|{region.value}|{report_date_value.isoformat()}|{format_revision(revision)}"


def delivery_idempotency_key(region: Region, report_date_value: date, revision: int) -> str:
    _enum(region, Region, "region")
    _date(report_date_value, "report_date")
    return f"delivery|{region.value}|{report_date_value.isoformat()}|{format_revision(revision)}"


def report_path(region: Region, report_date_value: date) -> str:
    _enum(region, Region, "region")
    _date(report_date_value, "report_date")
    return (
        "06_研究与探索/每日AI资讯/"
        f"{report_date_value.isoformat()}_{region.value}_AI_News.md"
    )


def sha256_bytes(data: bytes) -> str:
    if type(data) is not bytes:
        raise StateValidationError("sha256_bytes input must be bytes")
    return hashlib.sha256(data).hexdigest()


def sha256_text(text: str) -> str:
    if type(text) is not str:
        raise StateValidationError("sha256_text input must be text")
    return sha256_bytes(text.encode("utf-8"))


def _replace_record(records: tuple[Record, ...], old: Record, new: Record) -> tuple[Record, ...]:
    return tuple(new if record is old else record for record in records)


def register_candidate_observation(
    state: RegionState,
    *,
    observation_key: str,
    candidate_id: str,
    source_reference: str,
    observed_at: datetime,
    canonical_url: str | None = None,
    source_object_id: str | None = None,
    content_fingerprint: str | None = None,
) -> RegionState:
    proposed = CandidateStateRecord(
        observation_key=observation_key,
        candidate_id=candidate_id,
        source_reference=source_reference,
        canonical_url=canonical_url,
        source_object_id=source_object_id,
        content_fingerprint=content_fingerprint,
        first_seen_at=observed_at,
        last_seen_at=observed_at,
    )
    existing = next((item for item in state.candidates if item.observation_key == observation_key), None)
    if existing is None:
        return replace(state, candidates=state.candidates + (proposed,))
    stable_fields = (
        "candidate_id",
        "source_reference",
        "source_object_id",
    )
    if any(getattr(existing, field) != getattr(proposed, field) for field in stable_fields):
        raise StateConflictError("candidate observation would rebind stable identity")
    if existing.source_object_id is None and existing.canonical_url != canonical_url:
        raise StateConflictError("candidate observation would rebind stable identity")
    if (
        existing.source_object_id is not None
        and existing.canonical_url is not None
        and canonical_url is not None
        and urlsplit(existing.canonical_url).hostname
        != urlsplit(canonical_url).hostname
    ):
        raise StateConflictError("candidate observation cannot move across source hosts")
    if observed_at < existing.last_seen_at:
        raise StateConflictError("candidate last_seen_at must not regress")
    if (
        observed_at == existing.last_seen_at
        and canonical_url == existing.canonical_url
        and content_fingerprint == existing.content_fingerprint
    ):
        return state
    updated = replace(
        existing,
        canonical_url=canonical_url,
        content_fingerprint=content_fingerprint,
        last_seen_at=observed_at,
    )
    return replace(state, candidates=_replace_record(state.candidates, existing, updated))


def register_evidence_reference(
    state: RegionState,
    *,
    evidence_id: str,
    candidate_references: object,
    relation: EvidenceRelation = EvidenceRelation.SUPPORTS,
    independent_confirmation: bool = True,
    duplicate_of_evidence_id: str | None = None,
    content_signature: str | None = None,
) -> RegionState:
    proposed = EvidenceStateRecord(
        evidence_id=evidence_id,
        candidate_references=candidate_references,
        relation=relation,
        independent_confirmation=independent_confirmation,
        duplicate_of_evidence_id=duplicate_of_evidence_id,
        content_signature=content_signature,
    )
    existing = next((item for item in state.evidences if item.evidence_id == evidence_id), None)
    if existing is not None:
        if existing != proposed:
            raise StateConflictError("evidence_id would be rebound to different Evidence state")
        return state
    return replace(state, evidences=state.evidences + (proposed,))


def register_event_state(
    state: RegionState,
    *,
    event_id: str,
    evidence_references: object,
    information_status: InformationStatus | None = None,
) -> RegionState:
    proposed = EventStateRecord(
        event_id=event_id,
        evidence_references=evidence_references,
        initial_status=information_status,
        information_status=information_status,
        status_history=(),
    )
    existing = next((item for item in state.events if item.event_id == event_id), None)
    if existing is not None:
        if existing != proposed:
            raise StateConflictError("event_id is already registered with different state")
        return state
    return replace(state, events=state.events + (proposed,))


def append_event_evidence(
    state: RegionState,
    *,
    event_id: str,
    evidence_references: object,
) -> RegionState:
    existing = next((item for item in state.events if item.event_id == event_id), None)
    if existing is None:
        raise StateConflictError("event_id is not registered")
    additions = _references(evidence_references, "evidence_references", nonempty=True)
    combined = existing.evidence_references + tuple(
        item for item in additions if item not in existing.evidence_references
    )
    if combined == existing.evidence_references:
        return state
    updated = replace(existing, evidence_references=combined)
    return replace(state, events=_replace_record(state.events, existing, updated))


def append_event_status(
    state: RegionState,
    *,
    event_id: str,
    entry: StatusHistoryEntry,
) -> RegionState:
    existing = next((item for item in state.events if item.event_id == event_id), None)
    if existing is None:
        raise StateConflictError("event_id is not registered")
    if type(entry) is not StatusHistoryEntry:
        raise StateValidationError("entry must be a StatusHistoryEntry")
    if existing.information_status is None:
        raise StateConflictError("pre-analysis Event has no status to transition")
    if entry.previous_status is not existing.information_status:
        raise StateConflictError("previous_status does not match current Event status")
    if existing.status_history and entry.changed_at < existing.status_history[-1].changed_at:
        raise StateConflictError("status_history timestamp must not regress")
    updated = replace(
        existing,
        information_status=entry.new_status,
        status_history=existing.status_history + (entry,),
    )
    return replace(state, events=_replace_record(state.events, existing, updated))


def register_report(
    state: RegionState,
    *,
    report_date_value: date,
    revision: int,
    report_path_value: str,
    content_hash: str,
) -> RegionState:
    try:
        validate_write_path(state.region.value, report_path_value)
    except PathPolicyError as exc:
        raise StateValidationError("report_path is outside the Region allowlist") from exc
    proposed = ReportStateRecord(
        idempotency_key=report_idempotency_key(state.region, report_date_value, revision),
        region=state.region,
        report_date=report_date_value,
        revision=revision,
        report_path=report_path_value,
        content_hash=content_hash,
        git_status=GitCommitStatus.NOT_COMMITTED,
        commit_sha=None,
    )
    existing = next(
        (item for item in state.reports if item.idempotency_key == proposed.idempotency_key),
        None,
    )
    if existing is None:
        return replace(state, reports=state.reports + (proposed,))
    if existing.content_hash != proposed.content_hash:
        raise StateConflictError("same report revision has a different content_hash")
    if existing.report_path != proposed.report_path:
        raise StateConflictError("same report revision has a different report_path")
    return state


def set_report_git_result(
    state: RegionState,
    *,
    idempotency_key: str,
    status: GitCommitStatus,
    commit_sha: str | None,
) -> RegionState:
    existing = next((item for item in state.reports if item.idempotency_key == idempotency_key), None)
    if existing is None:
        raise StateConflictError("report idempotency_key is not registered")
    _enum(status, GitCommitStatus, "status")
    transitions = {
        GitCommitStatus.NOT_COMMITTED: frozenset(
            {GitCommitStatus.COMMIT_FAILED, GitCommitStatus.COMMITTED}
        ),
        GitCommitStatus.COMMIT_FAILED: frozenset({GitCommitStatus.COMMITTED}),
        GitCommitStatus.COMMITTED: frozenset(
            {GitCommitStatus.PUSH_FAILED, GitCommitStatus.PUSHED}
        ),
        GitCommitStatus.PUSH_FAILED: frozenset({GitCommitStatus.PUSHED}),
        GitCommitStatus.PUSHED: frozenset(),
    }
    if status is existing.git_status and commit_sha == existing.commit_sha:
        return state
    if status not in transitions[existing.git_status]:
        raise StateConflictError(
            f"illegal Git state transition: {existing.git_status.value} -> {status.value}"
        )
    if existing.commit_sha is not None and commit_sha != existing.commit_sha:
        raise StateConflictError("Git state transition must preserve the recorded commit_sha")
    updated = replace(existing, git_status=status, commit_sha=commit_sha)
    return replace(state, reports=_replace_record(state.reports, existing, updated))


def register_delivery(
    state: RegionState,
    *,
    report_date_value: date,
    revision: int,
) -> RegionState:
    report_key = report_idempotency_key(state.region, report_date_value, revision)
    if all(item.idempotency_key != report_key for item in state.reports):
        raise StateConflictError("delivery requires a matching Report state")
    proposed = DeliveryStateRecord(
        idempotency_key=delivery_idempotency_key(state.region, report_date_value, revision),
        region=state.region,
        report_date=report_date_value,
        revision=revision,
        status=DeliveryStatus.NOT_ATTEMPTED,
    )
    existing = next(
        (item for item in state.deliveries if item.idempotency_key == proposed.idempotency_key),
        None,
    )
    if existing is not None:
        return state
    return replace(state, deliveries=state.deliveries + (proposed,))


_DELIVERY_TRANSITIONS = {
    DeliveryStatus.NOT_ATTEMPTED: frozenset({DeliveryStatus.IN_PROGRESS}),
    DeliveryStatus.IN_PROGRESS: frozenset(
        {DeliveryStatus.DELIVERED, DeliveryStatus.DELIVERY_FAILED}
    ),
    DeliveryStatus.DELIVERY_FAILED: frozenset({DeliveryStatus.IN_PROGRESS}),
    DeliveryStatus.DELIVERED: frozenset(),
}


def transition_delivery(
    state: RegionState,
    *,
    idempotency_key: str,
    new_status: DeliveryStatus,
) -> RegionState:
    existing = next(
        (item for item in state.deliveries if item.idempotency_key == idempotency_key),
        None,
    )
    if existing is None:
        raise StateConflictError("delivery idempotency_key is not registered")
    _enum(new_status, DeliveryStatus, "new_status")
    if new_status is DeliveryStatus.IN_PROGRESS:
        report_key = report_idempotency_key(
            existing.region,
            existing.report_date,
            existing.revision,
        )
        report = next(item for item in state.reports if item.idempotency_key == report_key)
        if report.git_status is not GitCommitStatus.PUSHED:
            raise StateConflictError("delivery cannot start before the report is pushed")
    if new_status not in _DELIVERY_TRANSITIONS[existing.status]:
        raise StateConflictError(
            f"illegal Delivery Status transition: {existing.status.value} -> {new_status.value}"
        )
    updated = replace(existing, status=new_status)
    return replace(state, deliveries=_replace_record(state.deliveries, existing, updated))


_TOP_LEVEL_FIELDS = (
    "schema_version",
    "region",
    "candidates",
    "evidences",
    "events",
    "reports",
    "deliveries",
)
_CANDIDATE_FIELDS = (
    "observation_key",
    "candidate_id",
    "source_reference",
    "canonical_url",
    "source_object_id",
    "content_fingerprint",
    "first_seen_at",
    "last_seen_at",
)
_EVIDENCE_FIELDS = (
    "evidence_id",
    "candidate_references",
    "relation",
    "independent_confirmation",
    "duplicate_of_evidence_id",
    "content_signature",
)
_EVENT_FIELDS = (
    "event_id",
    "evidence_references",
    "initial_status",
    "information_status",
    "status_history",
)
_HISTORY_FIELDS = (
    "changed_at",
    "previous_status",
    "new_status",
    "evidence_references",
    "reason",
)
_REPORT_FIELDS = (
    "idempotency_key",
    "region",
    "report_date",
    "revision",
    "report_path",
    "content_hash",
    "git_status",
    "commit_sha",
)
_DELIVERY_FIELDS = (
    "idempotency_key",
    "region",
    "report_date",
    "revision",
    "status",
)


def _history_to_dict(entry: StatusHistoryEntry) -> dict[str, object]:
    return {
        "changed_at": entry.changed_at.isoformat(),
        "previous_status": entry.previous_status.value,
        "new_status": entry.new_status.value,
        "evidence_references": list(entry.evidence_references),
        "reason": entry.reason,
    }


def state_to_dict(state: RegionState) -> dict[str, object]:
    if type(state) is not RegionState:
        raise StateValidationError("state must be a RegionState")
    return {
        "schema_version": state.schema_version,
        "region": state.region.value,
        "candidates": [
            {
                "observation_key": item.observation_key,
                "candidate_id": item.candidate_id,
                "source_reference": item.source_reference,
                "canonical_url": item.canonical_url,
                "source_object_id": item.source_object_id,
                "content_fingerprint": item.content_fingerprint,
                "first_seen_at": item.first_seen_at.isoformat(),
                "last_seen_at": item.last_seen_at.isoformat(),
            }
            for item in state.candidates
        ],
        "evidences": [
            {
                "evidence_id": item.evidence_id,
                "candidate_references": list(item.candidate_references),
                "relation": item.relation.value,
                "independent_confirmation": item.independent_confirmation,
                "duplicate_of_evidence_id": item.duplicate_of_evidence_id,
                "content_signature": item.content_signature,
            }
            for item in state.evidences
        ],
        "events": [
            {
                "event_id": item.event_id,
                "evidence_references": list(item.evidence_references),
                "initial_status": (
                    item.initial_status.value if item.initial_status is not None else None
                ),
                "information_status": (
                    item.information_status.value
                    if item.information_status is not None
                    else None
                ),
                "status_history": [_history_to_dict(entry) for entry in item.status_history],
            }
            for item in state.events
        ],
        "reports": [
            {
                "idempotency_key": item.idempotency_key,
                "region": item.region.value,
                "report_date": item.report_date.isoformat(),
                "revision": item.revision,
                "report_path": item.report_path,
                "content_hash": item.content_hash,
                "git_status": item.git_status.value,
                "commit_sha": item.commit_sha,
            }
            for item in state.reports
        ],
        "deliveries": [
            {
                "idempotency_key": item.idempotency_key,
                "region": item.region.value,
                "report_date": item.report_date.isoformat(),
                "revision": item.revision,
                "status": item.status.value,
            }
            for item in state.deliveries
        ],
    }


def _object(value: object, fields: tuple[str, ...], name: str) -> dict[str, object]:
    if type(value) is not dict:
        raise StateValidationError(f"{name} must be an object")
    actual = set(value)
    expected = set(fields)
    if actual != expected:
        raise StateValidationError(
            f"{name} fields do not match; unknown={sorted(actual - expected)}, "
            f"missing={sorted(expected - actual)}"
        )
    return value


def _array(value: object, field_name: str) -> list[object]:
    if type(value) is not list:
        raise StateValidationError(f"{field_name} must be an array")
    return value


EnumType = TypeVar("EnumType", bound=Enum)


def _parse_enum(value: object, enum_type: type[EnumType], field_name: str) -> EnumType:
    if type(value) is not str:
        raise StateValidationError(f"{field_name} must be text")
    try:
        return enum_type(value)
    except ValueError as exc:
        raise StateValidationError(f"{field_name} has an unsupported value") from exc


def _parse_datetime(value: object, field_name: str) -> datetime:
    if type(value) is not str:
        raise StateValidationError(f"{field_name} must be an ISO 8601 datetime")
    try:
        result = datetime.fromisoformat(value)
    except ValueError as exc:
        raise StateValidationError(f"{field_name} is not a valid ISO 8601 datetime") from exc
    return _aware_datetime(result, field_name)


def _parse_date(value: object, field_name: str) -> date:
    if type(value) is not str or _DATE_PATTERN.fullmatch(value) is None:
        raise StateValidationError(f"{field_name} must use YYYY-MM-DD")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise StateValidationError(f"{field_name} is not a valid calendar date") from exc


def _parse_string_array(value: object, field_name: str) -> tuple[str, ...]:
    items = _array(value, field_name)
    if any(type(item) is not str for item in items):
        raise StateValidationError(f"{field_name} entries must be text")
    return tuple(items)


def _history_from_dict(value: object) -> StatusHistoryEntry:
    payload = _object(value, _HISTORY_FIELDS, "StatusHistoryEntry")
    return StatusHistoryEntry(
        changed_at=_parse_datetime(payload["changed_at"], "changed_at"),
        previous_status=_parse_enum(
            payload["previous_status"], InformationStatus, "previous_status"
        ),
        new_status=_parse_enum(payload["new_status"], InformationStatus, "new_status"),
        evidence_references=_parse_string_array(
            payload["evidence_references"], "evidence_references"
        ),
        reason=payload["reason"],
    )


def state_from_dict(value: object, *, expected_region: Region | None = None) -> RegionState:
    payload = _object(value, _TOP_LEVEL_FIELDS, "RegionState")
    schema_version = payload["schema_version"]
    if type(schema_version) is not int or schema_version != SUPPORTED_STATE_SCHEMA_VERSION:
        raise StateValidationError(f"unsupported schema_version: {schema_version!r}")
    region = _parse_enum(payload["region"], Region, "region")
    if expected_region is not None:
        _enum(expected_region, Region, "expected_region")
        if region is not expected_region:
            raise StateValidationError("State Region does not match expected Region")
    candidates = []
    for raw in _array(payload["candidates"], "candidates"):
        item = _object(raw, _CANDIDATE_FIELDS, "CandidateStateRecord")
        candidates.append(
            CandidateStateRecord(
                observation_key=item["observation_key"],
                candidate_id=item["candidate_id"],
                source_reference=item["source_reference"],
                canonical_url=item["canonical_url"],
                source_object_id=item["source_object_id"],
                content_fingerprint=item["content_fingerprint"],
                first_seen_at=_parse_datetime(item["first_seen_at"], "first_seen_at"),
                last_seen_at=_parse_datetime(item["last_seen_at"], "last_seen_at"),
            )
        )
    evidences = []
    for raw in _array(payload["evidences"], "evidences"):
        item = _object(raw, _EVIDENCE_FIELDS, "EvidenceStateRecord")
        evidences.append(
            EvidenceStateRecord(
                evidence_id=item["evidence_id"],
                candidate_references=_parse_string_array(
                    item["candidate_references"], "candidate_references"
                ),
                relation=_parse_enum(item["relation"], EvidenceRelation, "relation"),
                independent_confirmation=item["independent_confirmation"],
                duplicate_of_evidence_id=item["duplicate_of_evidence_id"],
                content_signature=item["content_signature"],
            )
        )
    events = []
    for raw in _array(payload["events"], "events"):
        item = _object(raw, _EVENT_FIELDS, "EventStateRecord")
        events.append(
            EventStateRecord(
                event_id=item["event_id"],
                evidence_references=_parse_string_array(
                    item["evidence_references"], "evidence_references"
                ),
                initial_status=(
                    None
                    if item["initial_status"] is None
                    else _parse_enum(
                        item["initial_status"], InformationStatus, "initial_status"
                    )
                ),
                information_status=(
                    None
                    if item["information_status"] is None
                    else _parse_enum(
                        item["information_status"],
                        InformationStatus,
                        "information_status",
                    )
                ),
                status_history=tuple(
                    _history_from_dict(entry)
                    for entry in _array(item["status_history"], "status_history")
                ),
            )
        )
    reports = []
    for raw in _array(payload["reports"], "reports"):
        item = _object(raw, _REPORT_FIELDS, "ReportStateRecord")
        reports.append(
            ReportStateRecord(
                idempotency_key=item["idempotency_key"],
                region=_parse_enum(item["region"], Region, "region"),
                report_date=_parse_date(item["report_date"], "report_date"),
                revision=item["revision"],
                report_path=item["report_path"],
                content_hash=item["content_hash"],
                git_status=_parse_enum(item["git_status"], GitCommitStatus, "git_status"),
                commit_sha=item["commit_sha"],
            )
        )
    deliveries = []
    for raw in _array(payload["deliveries"], "deliveries"):
        item = _object(raw, _DELIVERY_FIELDS, "DeliveryStateRecord")
        deliveries.append(
            DeliveryStateRecord(
                idempotency_key=item["idempotency_key"],
                region=_parse_enum(item["region"], Region, "region"),
                report_date=_parse_date(item["report_date"], "report_date"),
                revision=item["revision"],
                status=_parse_enum(item["status"], DeliveryStatus, "status"),
            )
        )
    return RegionState(
        schema_version=schema_version,
        region=region,
        candidates=tuple(candidates),
        evidences=tuple(evidences),
        events=tuple(events),
        reports=tuple(reports),
        deliveries=tuple(deliveries),
    )


def state_to_json(state: RegionState) -> str:
    try:
        return json.dumps(
            state_to_dict(state),
            ensure_ascii=False,
            allow_nan=False,
            sort_keys=True,
            separators=(",", ":"),
        )
    except (TypeError, ValueError) as exc:
        raise StateValidationError("State cannot be serialized as JSON") from exc


def _reject_constant(_value: str) -> None:
    raise StateValidationError("JSON constants NaN and Infinity are forbidden")


def _strict_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise StateValidationError("duplicate JSON object field is forbidden")
        result[key] = value
    return result


def state_from_json(text: str, *, expected_region: Region | None = None) -> RegionState:
    if type(text) is not str:
        raise StateValidationError("State JSON input must be text")
    try:
        payload = json.loads(
            text,
            object_pairs_hook=_strict_object,
            parse_constant=_reject_constant,
        )
    except StateValidationError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise StateValidationError("State JSON is invalid") from exc
    return state_from_dict(payload, expected_region=expected_region)


def state_digest(state: RegionState) -> str:
    return sha256_text(state_to_json(state))


def _state_target(
    region: Region,
    repo_relative_path: str,
    repo_root: Path,
) -> Path:
    _enum(region, Region, "region")
    if repo_relative_path != STATE_PATHS[region]:
        raise StateValidationError("State path is not the official Region state path")
    try:
        validated = validate_legacy_state_path(
            region.value,
            repo_relative_path,
            repo_root=repo_root,
        )
    except PathPolicyError as exc:
        raise StateValidationError("State path is outside the Region allowlist") from exc
    return repo_root.joinpath(*validated.parts)


def load_region_state(
    repo_relative_path: str,
    *,
    expected_region: Region,
    repo_root: Path,
) -> LoadedRegionState:
    target = _state_target(expected_region, repo_relative_path, repo_root)
    try:
        text = target.read_text(encoding="utf-8")
    except (OSError, UnicodeError) as exc:
        raise StateIOError("Cannot read Region state file") from exc
    state = state_from_json(text, expected_region=expected_region)
    return LoadedRegionState(state=state, digest=state_digest(state))


def _fsync_parent(path: Path) -> None:
    try:
        descriptor = os.open(path, os.O_RDONLY)
    except OSError:
        return
    try:
        os.fsync(descriptor)
    except OSError:
        pass
    finally:
        os.close(descriptor)


def save_region_state(
    state: RegionState,
    repo_relative_path: str,
    *,
    repo_root: Path,
    expected_previous_digest: str | None,
    create_new: bool = False,
) -> str:
    if type(state) is not RegionState:
        raise StateValidationError("state must be a RegionState")
    target = _state_target(state.region, repo_relative_path, repo_root)
    if target.exists():
        if create_new:
            raise StateConflictError("State file already exists")
        if expected_previous_digest is None:
            raise StaleStateError("expected_previous_digest is required")
        _sha256(expected_previous_digest, "expected_previous_digest")
        current = load_region_state(
            repo_relative_path,
            expected_region=state.region,
            repo_root=repo_root,
        )
        if current.digest != expected_previous_digest:
            raise StaleStateError("Region state changed after it was loaded")
    else:
        if not create_new or expected_previous_digest is not None:
            raise StateConflictError("Missing State file requires explicit create_new")
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            raise StateIOError("Cannot create Region state directory") from exc

    canonical = state_to_json(state)
    temporary_path: Path | None = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=target.parent,
            prefix=f".{target.name}.",
            suffix=".tmp",
            delete=False,
        ) as temporary:
            temporary_path = Path(temporary.name)
            temporary.write(canonical)
            temporary.write("\n")
            temporary.flush()
            os.fsync(temporary.fileno())
        os.replace(temporary_path, target)
        temporary_path = None
        _fsync_parent(target.parent)
    except OSError as exc:
        raise StateIOError("Atomic Region state save failed") from exc
    finally:
        if temporary_path is not None:
            try:
                temporary_path.unlink(missing_ok=True)
            except OSError:
                pass
    return state_digest(state)
