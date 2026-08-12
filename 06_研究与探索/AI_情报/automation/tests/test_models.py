"""Unit tests for immutable Stage 1.4 intelligence models."""

from dataclasses import FrozenInstanceError
from datetime import UTC, date, datetime, timedelta

import pytest

from pipeline.models import (
    CandidateItem,
    CollectionStatus,
    CollectorType,
    Confidence,
    EternaTag,
    Evidence,
    EvidenceRelation,
    FactCitation,
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


NOW = datetime(2026, 8, 12, 8, 0, tzinfo=UTC)


def candidate(**overrides: object) -> CandidateItem:
    values: dict[str, object] = {
        "candidate_id": "candidate-global-1",
        "region": Region.GLOBAL,
        "source_reference": "OpenAI",
        "source_type": SourceType.OFFICIAL,
        "source_priority": SourcePriority.P0,
        "source_credibility": SourceCredibility.HIGH,
        "source_fact_citation": FactCitation.YES,
        "collector_type": CollectorType.RSS_FEED,
        "source_url": "https://openai.com/news/example",
        "title": "示例模型发布",
        "source_excerpt": "公开的最小必要摘要。",
        "source_published_at": NOW - timedelta(hours=1),
        "collected_at": NOW,
        "first_seen_at": NOW,
        "last_seen_at": NOW,
        "eterna_tags": [EternaTag.AGENT, EternaTag.AI_CODING],
        "raw_evidence_reference": "https://openai.com/news/example",
        "collection_status": CollectionStatus.COLLECTED,
    }
    values.update(overrides)
    return CandidateItem(**values)  # type: ignore[arg-type]


def evidence(**overrides: object) -> Evidence:
    values: dict[str, object] = {
        "evidence_id": "evidence-global-1",
        "candidate_references": ["candidate-global-1"],
        "source_reference": "OpenAI",
        "source_url": "https://openai.com/news/example",
        "source_published_at": NOW - timedelta(hours=1),
        "collected_at": NOW,
        "source_priority": SourcePriority.P0,
        "source_credibility": SourceCredibility.HIGH,
        "is_primary_source": True,
        "relation": EvidenceRelation.SUPPORTS,
        "traceability": {
            "candidate_reference": "candidate-global-1",
            "accessible": True,
        },
        "evidence_note": "官方一手发布。",
    }
    values.update(overrides)
    return Evidence(**values)  # type: ignore[arg-type]


def event(**overrides: object) -> IntelligenceEvent:
    history = StatusHistoryEntry(
        changed_at=NOW,
        previous_status=InformationStatus.UNCONFIRMED,
        new_status=InformationStatus.CONFIRMED,
        evidence_references=["evidence-global-1"],
        reason="官方来源确认。",
    )
    values: dict[str, object] = {
        "event_id": "event-global-1",
        "canonical_title": "示例模型正式发布",
        "region": Region.GLOBAL,
        "technical_categories": [
            TechnicalCategory.MODEL,
            TechnicalCategory.AI_CODING,
        ],
        "first_seen_at": NOW,
        "last_seen_at": NOW,
        "evidence_references": ["evidence-global-1", "evidence-global-2"],
        "information_status": InformationStatus.CONFIRMED,
        "current_confidence": Confidence.HIGH,
        "importance": Importance.HIGH,
        "why_it_matters": "改变开发者可使用的模型能力。",
        "eterna_tags": [EternaTag.AGENT, EternaTag.STUDIO_NEXT],
        "status_history": [history],
    }
    values.update(overrides)
    return IntelligenceEvent(**values)  # type: ignore[arg-type]


def report(**overrides: object) -> IntelligenceReport:
    values: dict[str, object] = {
        "report_id": "report-global-2026-08-12",
        "region": Region.GLOBAL,
        "report_date": date(2026, 8, 12),
        "report_timezone": "Asia/Shanghai",
        "coverage_started_at": NOW - timedelta(days=1),
        "coverage_ended_at": NOW,
        "event_references": ["event-global-1", "event-global-2"],
        "core_summary": "本窗口包含一项重要模型更新。",
        "importance_order": [
            ImportanceOrderEntry(
                event_reference="event-global-1",
                reason="Importance 为 High。",
            )
        ],
        "eterna_value_extraction": {
            "attention_level": "值得跟踪",
            "domains": ["Studio Next", "Agent / Tool Use"],
        },
        "report_generated_at": NOW + timedelta(minutes=5),
        "source_coverage_statistics": {
            "P0": {"observed": 3, "unavailable": 0},
            "missing_critical_p0": False,
        },
    }
    values.update(overrides)
    return IntelligenceReport(**values)  # type: ignore[arg-type]


def test_candidate_valid_and_optional_published_at_pass() -> None:
    assert candidate().source_published_at is not None
    assert candidate(source_published_at=None).source_published_at is None


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("region", "global"),
        ("collection_status", "Complete"),
        ("eterna_tags", ["Agent"]),
    ],
)
def test_candidate_invalid_frozen_value_fails(field: str, value: object) -> None:
    with pytest.raises(ModelValidationError):
        candidate(**{field: value})


def test_candidate_naive_datetime_fails() -> None:
    with pytest.raises(ModelValidationError, match="timezone-aware"):
        candidate(collected_at=datetime(2026, 8, 12, 8, 0))


def test_candidate_last_seen_before_first_seen_fails() -> None:
    with pytest.raises(ModelValidationError, match="last_seen_at"):
        candidate(last_seen_at=NOW - timedelta(seconds=1))


def test_evidence_valid_and_contradicts_pass() -> None:
    assert evidence().relation is EvidenceRelation.SUPPORTS
    assert evidence(relation=EvidenceRelation.CONTRADICTS).relation is EvidenceRelation.CONTRADICTS


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("evidence_id", ""),
        ("candidate_references", []),
        ("relation", "Supports"),
        ("source_priority", "P0"),
        ("source_credibility", "High"),
        ("collected_at", datetime(2026, 8, 12, 8, 0)),
    ],
)
def test_evidence_invalid_value_fails(field: str, value: object) -> None:
    with pytest.raises(ModelValidationError):
        evidence(**{field: value})


@pytest.mark.parametrize("status", list(InformationStatus))
def test_event_all_information_status_values_pass(status: InformationStatus) -> None:
    assert event(information_status=status).information_status is status


@pytest.mark.parametrize("confidence", list(Confidence))
def test_event_all_confidence_values_pass(confidence: Confidence) -> None:
    assert event(current_confidence=confidence).current_confidence is confidence


@pytest.mark.parametrize("importance", list(Importance))
def test_event_all_importance_values_pass(importance: Importance) -> None:
    assert event(importance=importance).importance is importance


@pytest.mark.parametrize("category", list(TechnicalCategory))
def test_event_all_technical_categories_pass(category: TechnicalCategory) -> None:
    assert event(technical_categories=[category]).technical_categories == (category,)


@pytest.mark.parametrize("tag", list(EternaTag))
def test_all_eterna_tags_pass(tag: EternaTag) -> None:
    assert candidate(eterna_tags=[tag]).eterna_tags == (tag,)
    assert event(eterna_tags=[tag]).eterna_tags == (tag,)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("information_status", "confirmed"),
        ("current_confidence", "HIGH"),
        ("importance", "Important"),
        ("technical_categories", ["Model"]),
        ("eterna_tags", ["Studio"]),
    ],
)
def test_event_invalid_frozen_value_fails(field: str, value: object) -> None:
    with pytest.raises(ModelValidationError):
        event(**{field: value})


def test_event_reference_and_status_history_order_is_preserved() -> None:
    second = StatusHistoryEntry(
        changed_at=NOW + timedelta(minutes=1),
        previous_status=InformationStatus.CONFIRMED,
        new_status=InformationStatus.HIGH_CONFIDENCE_SIGNAL,
        evidence_references=["evidence-global-3"],
        reason="新增冲突证据。",
    )
    value = event(
        evidence_references=["evidence-global-2", "evidence-global-1"],
        status_history=[event().status_history[0], second],
    )

    assert value.evidence_references == ("evidence-global-2", "evidence-global-1")
    assert value.status_history[1] == second


def test_event_last_seen_before_first_seen_fails() -> None:
    with pytest.raises(ModelValidationError, match="last_seen_at"):
        event(last_seen_at=NOW - timedelta(seconds=1))


@pytest.mark.parametrize("region", list(Region))
def test_report_global_and_china_pass(region: Region) -> None:
    assert report(region=region).region is region


def test_report_invalid_timezone_fails() -> None:
    with pytest.raises(ModelValidationError, match="IANA timezone"):
        report(report_timezone="UTC+08:00")


def test_report_coverage_end_before_start_fails() -> None:
    with pytest.raises(ModelValidationError, match="coverage_ended_at"):
        report(coverage_ended_at=NOW - timedelta(days=2))


def test_report_invalid_report_date_type_fails() -> None:
    with pytest.raises(ModelValidationError):
        report(report_date="2026-08-12")


def test_report_event_order_is_preserved_and_empty_report_is_allowed() -> None:
    assert report().event_references == ("event-global-1", "event-global-2")
    assert report(event_references=[], importance_order=[]).event_references == ()


def test_models_are_frozen_and_mutable_inputs_are_isolated() -> None:
    tags = [EternaTag.AGENT]
    traceability = {"path": ["candidate-global-1"]}
    values = {"domains": ["Studio Next"]}
    item = candidate(eterna_tags=tags)
    proof = evidence(traceability=traceability)
    daily = report(eterna_value_extraction=values)

    tags.append(EternaTag.AFTELLE)
    traceability["path"].append("candidate-global-2")
    values["domains"].append("Aftelle")

    assert item.eterna_tags == (EternaTag.AGENT,)
    assert proof.traceability["path"] == ("candidate-global-1",)
    assert daily.eterna_value_extraction["domains"] == ("Studio Next",)
    with pytest.raises(FrozenInstanceError):
        item.title = "changed"  # type: ignore[misc]


def test_flexible_nested_values_reject_sensitive_keys_and_objects() -> None:
    with pytest.raises(ModelValidationError, match="sensitive"):
        evidence(traceability={"api_key": "not-allowed"})
    with pytest.raises(ModelValidationError, match="JSON-compatible"):
        report(source_coverage_statistics={"bad": object()})
    with pytest.raises(ModelValidationError, match="must not be empty"):
        evidence(traceability={})
    with pytest.raises(ModelValidationError, match="must not be empty"):
        report(eterna_value_extraction={})
