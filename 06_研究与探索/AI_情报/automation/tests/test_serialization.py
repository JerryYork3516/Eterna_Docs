"""Strict offline serialization tests for all Stage 1.4 model layers."""

from copy import deepcopy
import json

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
    InformationStatus,
    IntelligenceEvent,
    IntelligenceReport,
    Region,
    SourceCredibility,
    SourcePriority,
    SourceType,
    TechnicalCategory,
)
from pipeline.serialization import (
    SerializationError,
    from_dict,
    from_json,
    to_dict,
    to_json,
)


def candidate_payload() -> dict[str, object]:
    return {
        "candidate_id": "candidate-global-1",
        "region": "Global",
        "source_reference": "OpenAI",
        "source_type": "Official",
        "source_priority": "P0",
        "source_credibility": "High",
        "source_fact_citation": "Yes",
        "collector_type": "RSS / Feed",
        "source_url": "https://openai.com/news/example",
        "title": "示例模型发布",
        "source_excerpt": "公开的最小必要摘要。",
        "source_published_at": "2026-08-12T07:00:00+00:00",
        "collected_at": "2026-08-12T08:00:00+00:00",
        "first_seen_at": "2026-08-12T08:00:00+00:00",
        "last_seen_at": "2026-08-12T08:00:00+00:00",
        "eterna_tags": ["Agent", "AI Coding"],
        "raw_evidence_reference": "https://openai.com/news/example",
        "collection_status": "Collected",
    }


def evidence_payload() -> dict[str, object]:
    return {
        "evidence_id": "evidence-global-1",
        "candidate_references": ["candidate-global-1"],
        "source_reference": "OpenAI",
        "source_url": "https://openai.com/news/example",
        "source_published_at": "2026-08-12T07:00:00+00:00",
        "collected_at": "2026-08-12T08:00:00+00:00",
        "source_priority": "P0",
        "source_credibility": "High",
        "is_primary_source": True,
        "relation": "Contradicts",
        "traceability": {
            "accessible": True,
            "candidate_reference": "candidate-global-1",
        },
        "evidence_note": "保留冲突证据。",
    }


def event_payload() -> dict[str, object]:
    return {
        "event_id": "event-global-1",
        "canonical_title": "示例模型正式发布",
        "region": "Global",
        "technical_categories": ["Model", "AI Coding"],
        "first_seen_at": "2026-08-12T08:00:00+00:00",
        "last_seen_at": "2026-08-12T08:30:00+00:00",
        "evidence_references": ["evidence-global-2", "evidence-global-1"],
        "information_status": "Confirmed",
        "current_confidence": "High",
        "importance": "High",
        "why_it_matters": "改变开发者可使用的模型能力。",
        "eterna_tags": ["Agent", "Studio Next"],
        "status_history": [
            {
                "changed_at": "2026-08-12T08:30:00+00:00",
                "previous_status": "Unconfirmed",
                "new_status": "Confirmed",
                "evidence_references": ["evidence-global-2"],
                "reason": "官方来源确认。",
            },
            {
                "changed_at": "2026-08-12T08:31:00+00:00",
                "previous_status": "Confirmed",
                "new_status": "High-confidence signal",
                "evidence_references": ["evidence-global-1"],
                "reason": "新增冲突证据，保留历史。",
            },
        ],
    }


def report_payload(region: str = "Global") -> dict[str, object]:
    return {
        "report_id": f"report-{region.lower()}-2026-08-12",
        "region": region,
        "report_date": "2026-08-12",
        "report_timezone": "Asia/Shanghai",
        "coverage_started_at": "2026-08-11T08:00:00+08:00",
        "coverage_ended_at": "2026-08-12T08:00:00+08:00",
        "event_references": ["event-2", "event-1"],
        "core_summary": "本窗口包含一项重要模型更新。",
        "importance_order": [
            {"event_reference": "event-2", "reason": "Importance 为 Critical。"},
            {"event_reference": "event-1", "reason": "Importance 为 High。"},
        ],
        "eterna_value_extraction": {
            "attention_level": "值得跟踪",
            "domains": ["Studio Next", "Agent / Tool Use"],
        },
        "report_generated_at": "2026-08-12T08:05:00+08:00",
        "source_coverage_statistics": {
            "P0": {"observed": 3, "unavailable": 0},
            "missing_critical_p0": False,
        },
    }


@pytest.mark.parametrize(
    ("enum_type", "expected"),
    [
        (Region, {"Global", "China"}),
        (SourceType, {"Official", "Person", "Community", "Media"}),
        (SourcePriority, {"P0", "P1", "P2", "P3"}),
        (SourceCredibility, {"High", "Medium", "Low"}),
        (FactCitation, {"Yes", "Conditional", "No"}),
        (
            CollectorType,
            {"Official API", "RSS / Feed", "Web Page Monitor", "Search Discovery"},
        ),
        (
            CollectionStatus,
            {"Collected", "Metadata only", "Unavailable", "Rejected"},
        ),
        (EvidenceRelation, {"Supports", "Contradicts", "Supplements"}),
        (
            InformationStatus,
            {"Confirmed", "High-confidence signal", "Unconfirmed", "Community trend"},
        ),
        (Confidence, {"High", "Medium", "Low"}),
        (Importance, {"Critical", "High", "Medium", "Low"}),
        (
            TechnicalCategory,
            {
                "Model",
                "Agent",
                "AI Coding",
                "Voice / STS",
                "Multimodal",
                "Robotics / Embodied AI",
                "Open Source",
                "Infrastructure",
                "Research",
                "Product",
                "Business / Ecosystem",
            },
        ),
        (
            EternaTag,
            {
                "Digital Resident",
                "Aftelle",
                "Studio Next",
                "Runtime Core",
                "ECCS",
                "Voice / STS",
                "Multimodal",
                "Agent",
                "AI Coding",
                "Business / Ecosystem",
            },
        ),
    ],
)
def test_frozen_enum_values_are_exact(enum_type: type, expected: set[str]) -> None:
    assert {item.value for item in enum_type} == expected


@pytest.mark.parametrize(
    ("model_type", "payload_factory"),
    [
        (CandidateItem, candidate_payload),
        (Evidence, evidence_payload),
        (IntelligenceEvent, event_payload),
        (IntelligenceReport, report_payload),
    ],
)
def test_all_four_models_round_trip_through_dict_and_json(
    model_type: type,
    payload_factory,
) -> None:
    model = from_dict(model_type, payload_factory())

    assert from_dict(model_type, to_dict(model)) == model
    assert from_json(model_type, to_json(model)) == model


def test_optional_source_published_at_round_trip() -> None:
    payload = candidate_payload()
    payload["source_published_at"] = None

    assert to_dict(from_dict(CandidateItem, payload))["source_published_at"] is None


@pytest.mark.parametrize("region", ["Global", "China"])
def test_report_regions_round_trip(region: str) -> None:
    model = from_dict(IntelligenceReport, report_payload(region))

    assert to_dict(model)["region"] == region


def test_unicode_and_deterministic_json_pass() -> None:
    model = from_dict(IntelligenceEvent, event_payload())
    first = to_json(model)
    second = to_json(model)

    assert first == second
    assert "示例模型正式发布" in first
    assert "\\u793a" not in first


def test_json_key_order_is_stable_and_compact() -> None:
    model = from_dict(Evidence, evidence_payload())
    text = to_json(model)

    assert text.startswith('{"candidate_references"')
    assert ": " not in text
    assert ", " not in text


@pytest.mark.parametrize(
    ("model_type", "payload_factory"),
    [
        (CandidateItem, candidate_payload),
        (Evidence, evidence_payload),
        (IntelligenceEvent, event_payload),
        (IntelligenceReport, report_payload),
    ],
)
def test_unknown_and_missing_fields_fail(model_type: type, payload_factory) -> None:
    unknown = payload_factory()
    unknown["future_field"] = True
    missing = payload_factory()
    missing.pop(next(iter(missing)))

    with pytest.raises(SerializationError, match="unknown"):
        from_dict(model_type, unknown)
    with pytest.raises(SerializationError, match="missing"):
        from_dict(model_type, missing)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("region", "GLOBAL"),
        ("collection_status", "collected"),
        ("collector_type", "RSS"),
        ("eterna_tags", ["agent"]),
    ],
)
def test_candidate_enum_typos_fail(field: str, value: object) -> None:
    payload = candidate_payload()
    payload[field] = value

    with pytest.raises(SerializationError):
        from_dict(CandidateItem, payload)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("information_status", "High confidence signal"),
        ("current_confidence", "HIGH"),
        ("importance", "Important"),
        ("technical_categories", ["Voice/STS"]),
        ("eterna_tags", ["RuntimeCore"]),
    ],
)
def test_event_enum_typos_fail(field: str, value: object) -> None:
    payload = event_payload()
    payload[field] = value

    with pytest.raises(SerializationError):
        from_dict(IntelligenceEvent, payload)


@pytest.mark.parametrize(
    ("payload_factory", "field"),
    [
        (candidate_payload, "collected_at"),
        (evidence_payload, "collected_at"),
        (event_payload, "first_seen_at"),
        (report_payload, "report_generated_at"),
    ],
)
def test_naive_datetime_fails(payload_factory, field: str) -> None:
    payload = payload_factory()
    payload[field] = "2026-08-12T08:00:00"
    model_type = {
        candidate_payload: CandidateItem,
        evidence_payload: Evidence,
        event_payload: IntelligenceEvent,
        report_payload: IntelligenceReport,
    }[payload_factory]

    with pytest.raises(SerializationError, match="timezone-aware"):
        from_dict(model_type, payload)


def test_wrong_type_and_invalid_report_date_fail() -> None:
    candidate = candidate_payload()
    candidate["candidate_id"] = 1
    report = report_payload()
    report["report_date"] = "2026-02-30"

    with pytest.raises(SerializationError):
        from_dict(CandidateItem, candidate)
    with pytest.raises(SerializationError, match="calendar date"):
        from_dict(IntelligenceReport, report)


def test_extra_fields_in_strict_nested_values_fail() -> None:
    event = event_payload()
    event["status_history"][0]["reviewer"] = "someone"
    report = report_payload()
    report["importance_order"][0]["score"] = 100

    with pytest.raises(SerializationError, match="unknown"):
        from_dict(IntelligenceEvent, event)
    with pytest.raises(SerializationError, match="unknown"):
        from_dict(IntelligenceReport, report)


def test_reference_and_history_order_survives_round_trip() -> None:
    event = from_dict(IntelligenceEvent, event_payload())
    report = from_dict(IntelligenceReport, report_payload())

    restored_event = from_json(IntelligenceEvent, to_json(event))
    restored_report = from_json(IntelligenceReport, to_json(report))

    assert restored_event.evidence_references == ("evidence-global-2", "evidence-global-1")
    assert restored_event.status_history[0].new_status is InformationStatus.CONFIRMED
    assert restored_event.status_history[1].new_status is InformationStatus.HIGH_CONFIDENCE_SIGNAL
    assert restored_report.event_references == ("event-2", "event-1")


def test_from_json_rejects_duplicate_fields_and_non_finite_values() -> None:
    duplicate = '{"candidate_id":"a","candidate_id":"b"}'
    non_finite_payload = candidate_payload()
    non_finite_payload["source_excerpt"] = float("nan")
    non_finite = json.dumps(non_finite_payload)

    with pytest.raises(SerializationError, match="Duplicate"):
        from_json(CandidateItem, duplicate)
    with pytest.raises(SerializationError, match="NaN"):
        from_json(CandidateItem, non_finite)


def test_serialized_dict_is_detached_from_model() -> None:
    model = from_dict(IntelligenceReport, report_payload())
    serialized = to_dict(model)
    serialized["event_references"].append("event-3")
    serialized["eterna_value_extraction"]["domains"].append("Aftelle")

    assert model.event_references == ("event-2", "event-1")
    assert model.eterna_value_extraction["domains"] == (
        "Studio Next",
        "Agent / Tool Use",
    )


def test_input_payload_is_not_retained_by_model() -> None:
    payload = report_payload()
    original = deepcopy(payload)
    model = from_dict(IntelligenceReport, payload)

    payload["eterna_value_extraction"]["domains"].append("Aftelle")

    assert to_dict(model) == original
