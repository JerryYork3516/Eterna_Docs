"""Immutable Stage 1.4 intelligence data model values."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
from enum import Enum
import math
from types import MappingProxyType
from typing import Mapping, TypeAlias
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from pipeline.errors import AutomationError


class ModelValidationError(AutomationError):
    """Raised when a Stage 1.4 model value violates the frozen contract."""


class Region(str, Enum):
    GLOBAL = "Global"
    CHINA = "China"


class SourceType(str, Enum):
    OFFICIAL = "Official"
    PERSON = "Person"
    COMMUNITY = "Community"
    MEDIA = "Media"


class SourcePriority(str, Enum):
    P0 = "P0"
    P1 = "P1"
    P2 = "P2"
    P3 = "P3"


class SourceCredibility(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class FactCitation(str, Enum):
    YES = "Yes"
    CONDITIONAL = "Conditional"
    NO = "No"


class CollectorType(str, Enum):
    OFFICIAL_API = "Official API"
    RSS_FEED = "RSS / Feed"
    WEB_PAGE_MONITOR = "Web Page Monitor"
    SEARCH_DISCOVERY = "Search Discovery"


class CollectionStatus(str, Enum):
    COLLECTED = "Collected"
    METADATA_ONLY = "Metadata only"
    UNAVAILABLE = "Unavailable"
    REJECTED = "Rejected"


class EvidenceRelation(str, Enum):
    SUPPORTS = "Supports"
    CONTRADICTS = "Contradicts"
    SUPPLEMENTS = "Supplements"


class InformationStatus(str, Enum):
    CONFIRMED = "Confirmed"
    HIGH_CONFIDENCE_SIGNAL = "High-confidence signal"
    UNCONFIRMED = "Unconfirmed"
    COMMUNITY_TREND = "Community trend"


class Confidence(str, Enum):
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class Importance(str, Enum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class TechnicalCategory(str, Enum):
    MODEL = "Model"
    AGENT = "Agent"
    AI_CODING = "AI Coding"
    VOICE_STS = "Voice / STS"
    MULTIMODAL = "Multimodal"
    ROBOTICS_EMBODIED_AI = "Robotics / Embodied AI"
    OPEN_SOURCE = "Open Source"
    INFRASTRUCTURE = "Infrastructure"
    RESEARCH = "Research"
    PRODUCT = "Product"
    BUSINESS_ECOSYSTEM = "Business / Ecosystem"


class EternaTag(str, Enum):
    DIGITAL_RESIDENT = "Digital Resident"
    AFTELLE = "Aftelle"
    STUDIO_NEXT = "Studio Next"
    RUNTIME_CORE = "Runtime Core"
    ECCS = "ECCS"
    VOICE_STS = "Voice / STS"
    MULTIMODAL = "Multimodal"
    AGENT = "Agent"
    AI_CODING = "AI Coding"
    BUSINESS_ECOSYSTEM = "Business / Ecosystem"


JsonScalar: TypeAlias = None | bool | int | float | str
FrozenJsonValue: TypeAlias = JsonScalar | tuple["FrozenJsonValue", ...] | Mapping[str, "FrozenJsonValue"]

_SENSITIVE_KEY_FRAGMENTS = (
    "apikey",
    "token",
    "secret",
    "password",
    "cookie",
    "session",
    "authorization",
    "credential",
    "recipient",
    "email",
)


def _require_nonempty_text(value: object, field_name: str, *, max_length: int = 4096) -> str:
    if type(value) is not str or not value or value != value.strip():
        raise ModelValidationError(f"{field_name} must be non-empty trimmed text")
    if len(value) > max_length:
        raise ModelValidationError(f"{field_name} exceeds the maximum supported length")
    return value


def _require_optional_text(value: object, field_name: str) -> str | None:
    if value is None:
        return None
    return _require_nonempty_text(value, field_name, max_length=100_000)


def _require_enum(value: object, enum_type: type[Enum], field_name: str) -> None:
    if type(value) is not enum_type:
        raise ModelValidationError(f"{field_name} must be a {enum_type.__name__} value")


def _require_aware_datetime(value: object, field_name: str) -> datetime:
    if type(value) is not datetime:
        raise ModelValidationError(f"{field_name} must be a datetime")
    try:
        offset = value.utcoffset()
    except (OverflowError, ValueError) as exc:
        raise ModelValidationError(f"{field_name} has an invalid timezone") from exc
    if value.tzinfo is None or offset is None:
        raise ModelValidationError(f"{field_name} must be timezone-aware")
    return value


def _require_optional_aware_datetime(value: object, field_name: str) -> datetime | None:
    if value is None:
        return None
    return _require_aware_datetime(value, field_name)


def _require_date(value: object, field_name: str) -> date:
    if type(value) is not date:
        raise ModelValidationError(f"{field_name} must be a date")
    return value


def _require_timezone_name(value: object, field_name: str) -> str:
    timezone_name = _require_nonempty_text(value, field_name, max_length=255)
    try:
        ZoneInfo(timezone_name)
    except (ZoneInfoNotFoundError, ValueError) as exc:
        raise ModelValidationError(f"{field_name} must be a valid IANA timezone") from exc
    return timezone_name


def _tuple_of(
    value: object,
    expected_type: type,
    field_name: str,
    *,
    nonempty: bool = False,
) -> tuple:
    if type(value) not in {list, tuple}:
        raise ModelValidationError(f"{field_name} must be an ordered list or tuple")
    items = tuple(value)
    if nonempty and not items:
        raise ModelValidationError(f"{field_name} must not be empty")
    for item in items:
        if type(item) is not expected_type:
            raise ModelValidationError(
                f"{field_name} entries must be {expected_type.__name__} values"
            )
    return items


def _text_references(
    value: object,
    field_name: str,
    *,
    nonempty: bool = False,
) -> tuple[str, ...]:
    items = _tuple_of(value, str, field_name, nonempty=nonempty)
    for item in items:
        _require_nonempty_text(item, f"{field_name} entry", max_length=512)
    return items


def _normalized_key(key: str) -> str:
    return "".join(character.lower() for character in key if character.isalnum())


def freeze_json_value(value: object, field_name: str = "value") -> FrozenJsonValue:
    """Copy and deeply freeze a JSON-compatible value without accepting secrets."""

    if value is None or type(value) in {bool, int, str}:
        return value
    if type(value) is float:
        if not math.isfinite(value):
            raise ModelValidationError(f"{field_name} must not contain NaN or infinity")
        return value
    if type(value) in {list, tuple}:
        return tuple(
            freeze_json_value(item, f"{field_name}[{index}]")
            for index, item in enumerate(value)
        )
    if isinstance(value, Mapping):
        frozen: dict[str, FrozenJsonValue] = {}
        for key, nested in value.items():
            if type(key) is not str or not key or key != key.strip():
                raise ModelValidationError(f"{field_name} object keys must be non-empty text")
            normalized = _normalized_key(key)
            if any(fragment in normalized for fragment in _SENSITIVE_KEY_FRAGMENTS):
                raise ModelValidationError(f"{field_name} contains a forbidden sensitive field")
            frozen[key] = freeze_json_value(nested, f"{field_name}.{key}")
        return MappingProxyType(frozen)
    raise ModelValidationError(f"{field_name} contains a non-JSON-compatible value")


@dataclass(frozen=True, slots=True)
class StatusHistoryEntry:
    """Minimum frozen representation of one append-only status change."""

    changed_at: datetime
    previous_status: InformationStatus
    new_status: InformationStatus
    evidence_references: tuple[str, ...]
    reason: str

    def __post_init__(self) -> None:
        _require_aware_datetime(self.changed_at, "changed_at")
        _require_enum(self.previous_status, InformationStatus, "previous_status")
        _require_enum(self.new_status, InformationStatus, "new_status")
        object.__setattr__(
            self,
            "evidence_references",
            _text_references(
                self.evidence_references,
                "evidence_references",
                nonempty=True,
            ),
        )
        _require_nonempty_text(self.reason, "reason")


@dataclass(frozen=True, slots=True)
class ImportanceOrderEntry:
    """Minimum frozen representation of an auditable report ordering decision."""

    event_reference: str
    reason: str

    def __post_init__(self) -> None:
        _require_nonempty_text(self.event_reference, "event_reference", max_length=512)
        _require_nonempty_text(self.reason, "reason")


@dataclass(frozen=True, slots=True)
class CandidateItem:
    candidate_id: str
    region: Region
    source_reference: str
    source_type: SourceType
    source_priority: SourcePriority
    source_credibility: SourceCredibility
    source_fact_citation: FactCitation
    collector_type: CollectorType
    source_url: str
    title: str
    source_excerpt: str | None
    source_published_at: datetime | None
    collected_at: datetime
    first_seen_at: datetime
    last_seen_at: datetime
    eterna_tags: tuple[EternaTag, ...]
    raw_evidence_reference: str
    collection_status: CollectionStatus

    def __post_init__(self) -> None:
        _require_nonempty_text(self.candidate_id, "candidate_id", max_length=512)
        _require_enum(self.region, Region, "region")
        _require_nonempty_text(self.source_reference, "source_reference", max_length=512)
        _require_enum(self.source_type, SourceType, "source_type")
        _require_enum(self.source_priority, SourcePriority, "source_priority")
        _require_enum(self.source_credibility, SourceCredibility, "source_credibility")
        _require_enum(self.source_fact_citation, FactCitation, "source_fact_citation")
        _require_enum(self.collector_type, CollectorType, "collector_type")
        _require_nonempty_text(self.source_url, "source_url", max_length=8192)
        _require_nonempty_text(self.title, "title", max_length=4096)
        _require_optional_text(self.source_excerpt, "source_excerpt")
        _require_optional_aware_datetime(self.source_published_at, "source_published_at")
        _require_aware_datetime(self.collected_at, "collected_at")
        _require_aware_datetime(self.first_seen_at, "first_seen_at")
        _require_aware_datetime(self.last_seen_at, "last_seen_at")
        if self.last_seen_at < self.first_seen_at:
            raise ModelValidationError("last_seen_at must not precede first_seen_at")
        object.__setattr__(
            self,
            "eterna_tags",
            _tuple_of(self.eterna_tags, EternaTag, "eterna_tags"),
        )
        _require_nonempty_text(
            self.raw_evidence_reference,
            "raw_evidence_reference",
            max_length=8192,
        )
        _require_enum(self.collection_status, CollectionStatus, "collection_status")


@dataclass(frozen=True, slots=True)
class Evidence:
    evidence_id: str
    candidate_references: tuple[str, ...]
    source_reference: str
    source_url: str
    source_published_at: datetime | None
    collected_at: datetime
    source_priority: SourcePriority
    source_credibility: SourceCredibility
    is_primary_source: bool
    relation: EvidenceRelation
    traceability: Mapping[str, FrozenJsonValue]
    evidence_note: str | None

    def __post_init__(self) -> None:
        _require_nonempty_text(self.evidence_id, "evidence_id", max_length=512)
        object.__setattr__(
            self,
            "candidate_references",
            _text_references(
                self.candidate_references,
                "candidate_references",
                nonempty=True,
            ),
        )
        _require_nonempty_text(self.source_reference, "source_reference", max_length=512)
        _require_nonempty_text(self.source_url, "source_url", max_length=8192)
        _require_optional_aware_datetime(self.source_published_at, "source_published_at")
        _require_aware_datetime(self.collected_at, "collected_at")
        _require_enum(self.source_priority, SourcePriority, "source_priority")
        _require_enum(self.source_credibility, SourceCredibility, "source_credibility")
        if type(self.is_primary_source) is not bool:
            raise ModelValidationError("is_primary_source must be boolean")
        _require_enum(self.relation, EvidenceRelation, "relation")
        frozen_traceability = freeze_json_value(self.traceability, "traceability")
        if not isinstance(frozen_traceability, Mapping):
            raise ModelValidationError("traceability must be an object")
        if not frozen_traceability:
            raise ModelValidationError("traceability must not be empty")
        object.__setattr__(self, "traceability", frozen_traceability)
        _require_optional_text(self.evidence_note, "evidence_note")


@dataclass(frozen=True, slots=True)
class IntelligenceEvent:
    event_id: str
    canonical_title: str
    region: Region
    technical_categories: tuple[TechnicalCategory, ...]
    first_seen_at: datetime
    last_seen_at: datetime
    evidence_references: tuple[str, ...]
    information_status: InformationStatus
    current_confidence: Confidence
    importance: Importance
    why_it_matters: str
    eterna_tags: tuple[EternaTag, ...]
    status_history: tuple[StatusHistoryEntry, ...]

    def __post_init__(self) -> None:
        _require_nonempty_text(self.event_id, "event_id", max_length=512)
        _require_nonempty_text(self.canonical_title, "canonical_title", max_length=4096)
        _require_enum(self.region, Region, "region")
        object.__setattr__(
            self,
            "technical_categories",
            _tuple_of(
                self.technical_categories,
                TechnicalCategory,
                "technical_categories",
                nonempty=True,
            ),
        )
        _require_aware_datetime(self.first_seen_at, "first_seen_at")
        _require_aware_datetime(self.last_seen_at, "last_seen_at")
        if self.last_seen_at < self.first_seen_at:
            raise ModelValidationError("last_seen_at must not precede first_seen_at")
        object.__setattr__(
            self,
            "evidence_references",
            _text_references(
                self.evidence_references,
                "evidence_references",
                nonempty=True,
            ),
        )
        _require_enum(self.information_status, InformationStatus, "information_status")
        _require_enum(self.current_confidence, Confidence, "current_confidence")
        _require_enum(self.importance, Importance, "importance")
        _require_nonempty_text(self.why_it_matters, "why_it_matters")
        object.__setattr__(
            self,
            "eterna_tags",
            _tuple_of(self.eterna_tags, EternaTag, "eterna_tags"),
        )
        object.__setattr__(
            self,
            "status_history",
            _tuple_of(
                self.status_history,
                StatusHistoryEntry,
                "status_history",
            ),
        )


@dataclass(frozen=True, slots=True)
class IntelligenceReport:
    report_id: str
    region: Region
    report_date: date
    report_timezone: str
    coverage_started_at: datetime
    coverage_ended_at: datetime
    event_references: tuple[str, ...]
    core_summary: str
    importance_order: tuple[ImportanceOrderEntry, ...]
    eterna_value_extraction: Mapping[str, FrozenJsonValue]
    report_generated_at: datetime
    source_coverage_statistics: Mapping[str, FrozenJsonValue]

    def __post_init__(self) -> None:
        _require_nonempty_text(self.report_id, "report_id", max_length=512)
        _require_enum(self.region, Region, "region")
        _require_date(self.report_date, "report_date")
        _require_timezone_name(self.report_timezone, "report_timezone")
        _require_aware_datetime(self.coverage_started_at, "coverage_started_at")
        _require_aware_datetime(self.coverage_ended_at, "coverage_ended_at")
        if self.coverage_ended_at < self.coverage_started_at:
            raise ModelValidationError(
                "coverage_ended_at must not precede coverage_started_at"
            )
        object.__setattr__(
            self,
            "event_references",
            _text_references(self.event_references, "event_references"),
        )
        _require_nonempty_text(self.core_summary, "core_summary", max_length=100_000)
        object.__setattr__(
            self,
            "importance_order",
            _tuple_of(
                self.importance_order,
                ImportanceOrderEntry,
                "importance_order",
            ),
        )
        frozen_value = freeze_json_value(
            self.eterna_value_extraction,
            "eterna_value_extraction",
        )
        if not isinstance(frozen_value, Mapping):
            raise ModelValidationError("eterna_value_extraction must be an object")
        if not frozen_value:
            raise ModelValidationError("eterna_value_extraction must not be empty")
        object.__setattr__(self, "eterna_value_extraction", frozen_value)
        _require_aware_datetime(self.report_generated_at, "report_generated_at")
        frozen_stats = freeze_json_value(
            self.source_coverage_statistics,
            "source_coverage_statistics",
        )
        if not isinstance(frozen_stats, Mapping):
            raise ModelValidationError("source_coverage_statistics must be an object")
        if not frozen_stats:
            raise ModelValidationError("source_coverage_statistics must not be empty")
        object.__setattr__(self, "source_coverage_statistics", frozen_stats)
