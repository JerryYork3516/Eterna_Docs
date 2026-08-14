"""Immutable raw Collector values and bounded failure semantics."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import ipaddress
import json
from types import MappingProxyType
from typing import Mapping, TypeAlias
from urllib.parse import urlsplit

from pipeline.errors import AutomationError
from pipeline.models import CollectorType, FrozenJsonValue, Region, freeze_json_value


MAX_TITLE_LENGTH = 4_096
MAX_EXCERPT_LENGTH = 16_384
MAX_REFERENCE_LENGTH = 8_192


class CollectionErrorKind(str, Enum):
    NETWORK_ERROR = "Network error"
    TIMEOUT = "Timeout"
    HTTP_ERROR = "HTTP error"
    RATE_LIMITED = "Rate limited"
    INVALID_CONTENT = "Invalid content"
    UNSUPPORTED_CONTENT = "Unsupported content"
    RESPONSE_TOO_LARGE = "Response too large"
    ACCESS_DENIED = "Access denied"
    REDIRECT_LIMIT = "Redirect limit"
    SOURCE_DISABLED = "Source disabled"
    SOURCE_REJECTED = "Source rejected"


class CollectionError(AutomationError):
    """A safe, caller-visible failure for one configured source."""

    def __init__(
        self,
        kind: CollectionErrorKind,
        message: str,
        *,
        status_code: int | None = None,
    ) -> None:
        self.kind = kind
        self.status_code = status_code
        super().__init__(message)


@dataclass(frozen=True, slots=True)
class CollectionItemError:
    """A bounded item-level parse failure that does not hide valid siblings."""

    item_index: int
    kind: CollectionErrorKind
    message: str

    def __post_init__(self) -> None:
        if type(self.item_index) is not int or self.item_index < -1:
            raise ValueError("item_index must be -1 or a non-negative integer")
        if type(self.kind) is not CollectionErrorKind:
            raise ValueError("kind must be a CollectionErrorKind")
        _text(self.message, "message", max_length=512)


def _text(value: object, field_name: str, *, max_length: int) -> str:
    if type(value) is not str or not value or value != value.strip():
        raise ValueError(f"{field_name} must be non-empty trimmed text")
    if len(value) > max_length:
        raise ValueError(f"{field_name} exceeds the maximum supported length")
    return value


def _optional_text(value: object, field_name: str, *, max_length: int) -> str | None:
    if value is None:
        return None
    return _text(value, field_name, max_length=max_length)


def _aware_datetime(value: object, field_name: str) -> datetime:
    if type(value) is not datetime:
        raise ValueError(f"{field_name} must be a datetime")
    try:
        offset = value.utcoffset()
    except (OverflowError, ValueError) as exc:
        raise ValueError(f"{field_name} has an invalid timezone") from exc
    if value.tzinfo is None or offset is None:
        raise ValueError(f"{field_name} must be timezone-aware")
    return value


def _public_url(value: object, field_name: str) -> str:
    text = _text(value, field_name, max_length=MAX_REFERENCE_LENGTH)
    if any(character.isspace() for character in text):
        raise ValueError(f"{field_name} must not contain whitespace")
    try:
        parsed = urlsplit(text)
        _ = parsed.port
    except ValueError as exc:
        raise ValueError(f"{field_name} is malformed") from exc
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError(f"{field_name} must be an HTTP(S) URL")
    if parsed.username is not None or parsed.password is not None:
        raise ValueError(f"{field_name} must not contain credentials")
    hostname = parsed.hostname.lower()
    if hostname == "localhost" or hostname.endswith(".local"):
        raise ValueError(f"{field_name} must use a public hostname")
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        pass
    else:
        if not address.is_global:
            raise ValueError(f"{field_name} must not use a non-public IP address")
    return text


@dataclass(frozen=True, slots=True)
class RawCollectorRecord:
    """A minimal pre-Normalizer record; explicitly not a CandidateItem."""

    source_reference: str
    region: Region
    collector_type: CollectorType
    source_url: str
    source_object_id: str | None
    title: str
    excerpt: str | None
    published_at_raw: str | None
    published_at: datetime | None
    collected_at: datetime
    raw_reference: str
    metadata: Mapping[str, FrozenJsonValue]

    def __post_init__(self) -> None:
        _text(self.source_reference, "source_reference", max_length=512)
        if type(self.region) is not Region:
            raise ValueError("region must be a Region value")
        if type(self.collector_type) is not CollectorType:
            raise ValueError("collector_type must be a CollectorType value")
        _public_url(self.source_url, "source_url")
        _optional_text(self.source_object_id, "source_object_id", max_length=1_024)
        _text(self.title, "title", max_length=MAX_TITLE_LENGTH)
        _optional_text(self.excerpt, "excerpt", max_length=MAX_EXCERPT_LENGTH)
        _optional_text(
            self.published_at_raw,
            "published_at_raw",
            max_length=1_024,
        )
        if self.published_at is not None:
            _aware_datetime(self.published_at, "published_at")
        _aware_datetime(self.collected_at, "collected_at")
        _text(self.raw_reference, "raw_reference", max_length=MAX_REFERENCE_LENGTH)
        frozen = freeze_json_value(self.metadata, "metadata")
        if not isinstance(frozen, Mapping):
            raise ValueError("metadata must be an object")
        object.__setattr__(self, "metadata", MappingProxyType(dict(frozen)))


@dataclass(frozen=True, slots=True)
class CollectionBatch:
    """The records and bounded item failures from exactly one source request."""

    records: tuple[RawCollectorRecord, ...]
    item_errors: tuple[CollectionItemError, ...] = ()

    def __post_init__(self) -> None:
        records = tuple(self.records)
        errors = tuple(self.item_errors)
        if any(type(record) is not RawCollectorRecord for record in records):
            raise ValueError("records must contain RawCollectorRecord values")
        if any(type(error) is not CollectionItemError for error in errors):
            raise ValueError("item_errors must contain CollectionItemError values")
        object.__setattr__(self, "records", records)
        object.__setattr__(self, "item_errors", errors)


JsonValue: TypeAlias = None | bool | int | float | str | list["JsonValue"] | dict[str, "JsonValue"]


def parse_json_bytes(body: bytes) -> JsonValue:
    """Parse strict JSON without duplicate keys or non-finite numbers."""

    def unique_pairs(pairs: list[tuple[str, JsonValue]]) -> dict[str, JsonValue]:
        result: dict[str, JsonValue] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON object field")
            result[key] = value
        return result

    def reject_constant(value: str) -> None:
        raise ValueError(f"unsupported JSON constant: {value}")

    try:
        return json.loads(
            body.decode("utf-8"),
            object_pairs_hook=unique_pairs,
            parse_constant=reject_constant,
        )
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError) as exc:
        raise CollectionError(
            CollectionErrorKind.INVALID_CONTENT,
            "Collector response is not valid strict UTF-8 JSON",
        ) from exc


def parse_source_datetime(raw: object) -> datetime | None:
    """Parse only an explicit source timestamp; never infer from collection time."""

    if raw is None:
        return None
    if type(raw) is not str or not raw or len(raw) > 1_024:
        raise ValueError("source timestamp must be non-empty text")
    try:
        value = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("source timestamp is not valid ISO 8601") from exc
    return _aware_datetime(value, "source timestamp")
