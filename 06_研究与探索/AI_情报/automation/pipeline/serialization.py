"""Strict deterministic serialization for Stage 1.4 intelligence models."""

from __future__ import annotations

from datetime import date, datetime
from enum import Enum
import json
import re
from typing import Mapping, TypeVar

from pipeline.errors import AutomationError
from pipeline.models import (
    CandidateItem,
    CollectionStatus,
    CollectorType,
    Confidence,
    EternaTag,
    Evidence,
    EvidenceRelation,
    FactCitation,
    FrozenJsonValue,
    Importance,
    ImportanceOrderEntry,
    InformationStatus,
    IntelligenceEvent,
    IntelligenceReport,
    ModelValidationError,
    Region,
    SourceCredibility,
    SourcePriority,
    SourceType,
    StatusHistoryEntry,
    TechnicalCategory,
)


class SerializationError(AutomationError):
    """Raised when serialized input does not exactly match the frozen model."""


Model = (
    CandidateItem
    | Evidence
    | IntelligenceEvent
    | IntelligenceReport
    | StatusHistoryEntry
    | ImportanceOrderEntry
)
ModelType = type[Model]
EnumType = TypeVar("EnumType", bound=Enum)

_DATE_PATTERN = re.compile(r"[0-9]{4}-[0-9]{2}-[0-9]{2}")

_CANDIDATE_FIELDS = (
    "candidate_id",
    "region",
    "source_reference",
    "source_type",
    "source_priority",
    "source_credibility",
    "source_fact_citation",
    "collector_type",
    "source_url",
    "title",
    "source_excerpt",
    "source_published_at",
    "collected_at",
    "first_seen_at",
    "last_seen_at",
    "eterna_tags",
    "raw_evidence_reference",
    "collection_status",
)
_EVIDENCE_FIELDS = (
    "evidence_id",
    "candidate_references",
    "source_reference",
    "source_url",
    "source_published_at",
    "collected_at",
    "source_priority",
    "source_credibility",
    "is_primary_source",
    "relation",
    "traceability",
    "evidence_note",
)
_STATUS_HISTORY_FIELDS = (
    "changed_at",
    "previous_status",
    "new_status",
    "evidence_references",
    "reason",
)
_EVENT_FIELDS = (
    "event_id",
    "canonical_title",
    "region",
    "technical_categories",
    "first_seen_at",
    "last_seen_at",
    "evidence_references",
    "information_status",
    "current_confidence",
    "importance",
    "why_it_matters",
    "eterna_tags",
    "status_history",
)
_IMPORTANCE_ORDER_FIELDS = ("event_reference", "reason")
_REPORT_FIELDS = (
    "report_id",
    "region",
    "report_date",
    "report_timezone",
    "coverage_started_at",
    "coverage_ended_at",
    "event_references",
    "core_summary",
    "importance_order",
    "eterna_value_extraction",
    "report_generated_at",
    "source_coverage_statistics",
)


def _iso_datetime(value: datetime) -> str:
    return value.isoformat()


def _thaw_json(value: FrozenJsonValue) -> object:
    if isinstance(value, Mapping):
        return {key: _thaw_json(value[key]) for key in sorted(value)}
    if type(value) is tuple:
        return [_thaw_json(item) for item in value]
    return value


def _status_history_to_dict(value: StatusHistoryEntry) -> dict[str, object]:
    return {
        "changed_at": _iso_datetime(value.changed_at),
        "previous_status": value.previous_status.value,
        "new_status": value.new_status.value,
        "evidence_references": list(value.evidence_references),
        "reason": value.reason,
    }


def _importance_order_to_dict(value: ImportanceOrderEntry) -> dict[str, object]:
    return {
        "event_reference": value.event_reference,
        "reason": value.reason,
    }


def to_dict(value: Model) -> dict[str, object]:
    """Return one model as a JSON-compatible object with stable field ordering."""

    if type(value) is CandidateItem:
        return {
            "candidate_id": value.candidate_id,
            "region": value.region.value,
            "source_reference": value.source_reference,
            "source_type": value.source_type.value,
            "source_priority": value.source_priority.value,
            "source_credibility": value.source_credibility.value,
            "source_fact_citation": value.source_fact_citation.value,
            "collector_type": value.collector_type.value,
            "source_url": value.source_url,
            "title": value.title,
            "source_excerpt": value.source_excerpt,
            "source_published_at": (
                _iso_datetime(value.source_published_at)
                if value.source_published_at is not None
                else None
            ),
            "collected_at": _iso_datetime(value.collected_at),
            "first_seen_at": _iso_datetime(value.first_seen_at),
            "last_seen_at": _iso_datetime(value.last_seen_at),
            "eterna_tags": [tag.value for tag in value.eterna_tags],
            "raw_evidence_reference": value.raw_evidence_reference,
            "collection_status": value.collection_status.value,
        }
    if type(value) is Evidence:
        return {
            "evidence_id": value.evidence_id,
            "candidate_references": list(value.candidate_references),
            "source_reference": value.source_reference,
            "source_url": value.source_url,
            "source_published_at": (
                _iso_datetime(value.source_published_at)
                if value.source_published_at is not None
                else None
            ),
            "collected_at": _iso_datetime(value.collected_at),
            "source_priority": value.source_priority.value,
            "source_credibility": value.source_credibility.value,
            "is_primary_source": value.is_primary_source,
            "relation": value.relation.value,
            "traceability": _thaw_json(value.traceability),
            "evidence_note": value.evidence_note,
        }
    if type(value) is StatusHistoryEntry:
        return _status_history_to_dict(value)
    if type(value) is IntelligenceEvent:
        return {
            "event_id": value.event_id,
            "canonical_title": value.canonical_title,
            "region": value.region.value,
            "technical_categories": [
                category.value for category in value.technical_categories
            ],
            "first_seen_at": _iso_datetime(value.first_seen_at),
            "last_seen_at": _iso_datetime(value.last_seen_at),
            "evidence_references": list(value.evidence_references),
            "information_status": value.information_status.value,
            "current_confidence": value.current_confidence.value,
            "importance": value.importance.value,
            "why_it_matters": value.why_it_matters,
            "eterna_tags": [tag.value for tag in value.eterna_tags],
            "status_history": [
                _status_history_to_dict(entry) for entry in value.status_history
            ],
        }
    if type(value) is ImportanceOrderEntry:
        return _importance_order_to_dict(value)
    if type(value) is IntelligenceReport:
        return {
            "report_id": value.report_id,
            "region": value.region.value,
            "report_date": value.report_date.isoformat(),
            "report_timezone": value.report_timezone,
            "coverage_started_at": _iso_datetime(value.coverage_started_at),
            "coverage_ended_at": _iso_datetime(value.coverage_ended_at),
            "event_references": list(value.event_references),
            "core_summary": value.core_summary,
            "importance_order": [
                _importance_order_to_dict(entry) for entry in value.importance_order
            ],
            "eterna_value_extraction": _thaw_json(value.eterna_value_extraction),
            "report_generated_at": _iso_datetime(value.report_generated_at),
            "source_coverage_statistics": _thaw_json(
                value.source_coverage_statistics
            ),
        }
    raise SerializationError("Unsupported model type")


def _object(value: object, fields: tuple[str, ...], model_name: str) -> dict[str, object]:
    if type(value) is not dict:
        raise SerializationError(f"{model_name} payload must be an object")
    actual = set(value)
    expected = set(fields)
    if actual != expected:
        unknown = sorted(actual - expected)
        missing = sorted(expected - actual)
        raise SerializationError(
            f"{model_name} fields do not match; unknown={unknown}, missing={missing}"
        )
    return value


def _enum(value: object, enum_type: type[EnumType], field_name: str) -> EnumType:
    if type(value) is not str:
        raise SerializationError(f"{field_name} must be text")
    try:
        return enum_type(value)
    except ValueError as exc:
        raise SerializationError(f"{field_name} has an unsupported value") from exc


def _datetime(value: object, field_name: str, *, optional: bool = False) -> datetime | None:
    if optional and value is None:
        return None
    if type(value) is not str:
        raise SerializationError(f"{field_name} must be an ISO 8601 datetime")
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise SerializationError(f"{field_name} is not a valid ISO 8601 datetime") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise SerializationError(f"{field_name} must be timezone-aware")
    return parsed


def _date(value: object, field_name: str) -> date:
    if type(value) is not str or _DATE_PATTERN.fullmatch(value) is None:
        raise SerializationError(f"{field_name} must use YYYY-MM-DD")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise SerializationError(f"{field_name} is not a valid calendar date") from exc


def _array(value: object, field_name: str) -> list[object]:
    if type(value) is not list:
        raise SerializationError(f"{field_name} must be an array")
    return value


def _string_array(value: object, field_name: str) -> list[str]:
    items = _array(value, field_name)
    if any(type(item) is not str for item in items):
        raise SerializationError(f"{field_name} entries must be text")
    return items


def _mapping(value: object, field_name: str) -> dict[str, object]:
    if type(value) is not dict:
        raise SerializationError(f"{field_name} must be an object")
    return value


def _status_history_from_dict(value: object) -> StatusHistoryEntry:
    payload = _object(value, _STATUS_HISTORY_FIELDS, "StatusHistoryEntry")
    return StatusHistoryEntry(
        changed_at=_datetime(payload["changed_at"], "changed_at"),
        previous_status=_enum(
            payload["previous_status"], InformationStatus, "previous_status"
        ),
        new_status=_enum(payload["new_status"], InformationStatus, "new_status"),
        evidence_references=_string_array(
            payload["evidence_references"], "evidence_references"
        ),
        reason=payload["reason"],
    )


def _importance_order_from_dict(value: object) -> ImportanceOrderEntry:
    payload = _object(value, _IMPORTANCE_ORDER_FIELDS, "ImportanceOrderEntry")
    return ImportanceOrderEntry(
        event_reference=payload["event_reference"],
        reason=payload["reason"],
    )


def from_dict(model_type: ModelType, value: object) -> Model:
    """Build one model from an exact JSON-compatible object."""

    try:
        if model_type is CandidateItem:
            payload = _object(value, _CANDIDATE_FIELDS, "CandidateItem")
            return CandidateItem(
                candidate_id=payload["candidate_id"],
                region=_enum(payload["region"], Region, "region"),
                source_reference=payload["source_reference"],
                source_type=_enum(payload["source_type"], SourceType, "source_type"),
                source_priority=_enum(
                    payload["source_priority"], SourcePriority, "source_priority"
                ),
                source_credibility=_enum(
                    payload["source_credibility"],
                    SourceCredibility,
                    "source_credibility",
                ),
                source_fact_citation=_enum(
                    payload["source_fact_citation"],
                    FactCitation,
                    "source_fact_citation",
                ),
                collector_type=_enum(
                    payload["collector_type"], CollectorType, "collector_type"
                ),
                source_url=payload["source_url"],
                title=payload["title"],
                source_excerpt=payload["source_excerpt"],
                source_published_at=_datetime(
                    payload["source_published_at"],
                    "source_published_at",
                    optional=True,
                ),
                collected_at=_datetime(payload["collected_at"], "collected_at"),
                first_seen_at=_datetime(payload["first_seen_at"], "first_seen_at"),
                last_seen_at=_datetime(payload["last_seen_at"], "last_seen_at"),
                eterna_tags=[
                    _enum(item, EternaTag, "eterna_tags entry")
                    for item in _array(payload["eterna_tags"], "eterna_tags")
                ],
                raw_evidence_reference=payload["raw_evidence_reference"],
                collection_status=_enum(
                    payload["collection_status"],
                    CollectionStatus,
                    "collection_status",
                ),
            )
        if model_type is Evidence:
            payload = _object(value, _EVIDENCE_FIELDS, "Evidence")
            return Evidence(
                evidence_id=payload["evidence_id"],
                candidate_references=_string_array(
                    payload["candidate_references"], "candidate_references"
                ),
                source_reference=payload["source_reference"],
                source_url=payload["source_url"],
                source_published_at=_datetime(
                    payload["source_published_at"],
                    "source_published_at",
                    optional=True,
                ),
                collected_at=_datetime(payload["collected_at"], "collected_at"),
                source_priority=_enum(
                    payload["source_priority"], SourcePriority, "source_priority"
                ),
                source_credibility=_enum(
                    payload["source_credibility"],
                    SourceCredibility,
                    "source_credibility",
                ),
                is_primary_source=payload["is_primary_source"],
                relation=_enum(payload["relation"], EvidenceRelation, "relation"),
                traceability=_mapping(payload["traceability"], "traceability"),
                evidence_note=payload["evidence_note"],
            )
        if model_type is StatusHistoryEntry:
            return _status_history_from_dict(value)
        if model_type is IntelligenceEvent:
            payload = _object(value, _EVENT_FIELDS, "IntelligenceEvent")
            return IntelligenceEvent(
                event_id=payload["event_id"],
                canonical_title=payload["canonical_title"],
                region=_enum(payload["region"], Region, "region"),
                technical_categories=[
                    _enum(item, TechnicalCategory, "technical_categories entry")
                    for item in _array(
                        payload["technical_categories"], "technical_categories"
                    )
                ],
                first_seen_at=_datetime(payload["first_seen_at"], "first_seen_at"),
                last_seen_at=_datetime(payload["last_seen_at"], "last_seen_at"),
                evidence_references=_string_array(
                    payload["evidence_references"], "evidence_references"
                ),
                information_status=_enum(
                    payload["information_status"],
                    InformationStatus,
                    "information_status",
                ),
                current_confidence=_enum(
                    payload["current_confidence"],
                    Confidence,
                    "current_confidence",
                ),
                importance=_enum(payload["importance"], Importance, "importance"),
                why_it_matters=payload["why_it_matters"],
                eterna_tags=[
                    _enum(item, EternaTag, "eterna_tags entry")
                    for item in _array(payload["eterna_tags"], "eterna_tags")
                ],
                status_history=[
                    _status_history_from_dict(item)
                    for item in _array(payload["status_history"], "status_history")
                ],
            )
        if model_type is ImportanceOrderEntry:
            return _importance_order_from_dict(value)
        if model_type is IntelligenceReport:
            payload = _object(value, _REPORT_FIELDS, "IntelligenceReport")
            return IntelligenceReport(
                report_id=payload["report_id"],
                region=_enum(payload["region"], Region, "region"),
                report_date=_date(payload["report_date"], "report_date"),
                report_timezone=payload["report_timezone"],
                coverage_started_at=_datetime(
                    payload["coverage_started_at"], "coverage_started_at"
                ),
                coverage_ended_at=_datetime(
                    payload["coverage_ended_at"], "coverage_ended_at"
                ),
                event_references=_string_array(
                    payload["event_references"], "event_references"
                ),
                core_summary=payload["core_summary"],
                importance_order=[
                    _importance_order_from_dict(item)
                    for item in _array(payload["importance_order"], "importance_order")
                ],
                eterna_value_extraction=_mapping(
                    payload["eterna_value_extraction"], "eterna_value_extraction"
                ),
                report_generated_at=_datetime(
                    payload["report_generated_at"], "report_generated_at"
                ),
                source_coverage_statistics=_mapping(
                    payload["source_coverage_statistics"],
                    "source_coverage_statistics",
                ),
            )
    except ModelValidationError as exc:
        raise SerializationError(str(exc)) from exc
    raise SerializationError("Unsupported model type")


def to_json(value: Model) -> str:
    """Serialize one model to deterministic UTF-8-compatible JSON text."""

    try:
        return json.dumps(
            to_dict(value),
            ensure_ascii=False,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        )
    except (TypeError, ValueError) as exc:
        raise SerializationError("Model cannot be serialized as JSON") from exc


def _reject_constant(_value: str) -> None:
    raise SerializationError("JSON constants NaN and Infinity are forbidden")


def _strict_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in pairs:
        if key in result:
            raise SerializationError("Duplicate JSON object field is forbidden")
        result[key] = value
    return result


def from_json(model_type: ModelType, text: str) -> Model:
    """Deserialize deterministic-model JSON without coercion or schema upgrades."""

    if type(text) is not str:
        raise SerializationError("JSON input must be text")
    try:
        payload = json.loads(
            text,
            object_pairs_hook=_strict_object,
            parse_constant=_reject_constant,
        )
    except SerializationError:
        raise
    except (json.JSONDecodeError, TypeError, ValueError) as exc:
        raise SerializationError("JSON input is invalid") from exc
    return from_dict(model_type, payload)
