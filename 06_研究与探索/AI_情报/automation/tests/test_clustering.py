"""Offline tests for A7 Evidence, duplicate, and EventDraft rules."""

from dataclasses import replace
from datetime import UTC, datetime, timedelta

import pytest

from pipeline.clustering import (
    ClusterInput,
    ClusteringError,
    EventDescriptor,
    cluster_candidates,
    near_duplicate_signature,
    stable_event_id,
)
from pipeline.models import (
    CandidateItem,
    CollectionStatus,
    CollectorType,
    EternaTag,
    EvidenceRelation,
    FactCitation,
    Region,
    SourceCredibility,
    SourcePriority,
    SourceType,
    StatusHistoryEntry,
    TechnicalCategory,
    InformationStatus,
)
from pipeline.state import (
    StateConflictError,
    append_event_status,
    empty_region_state,
    register_candidate_observation,
    register_event_state,
    register_evidence_reference,
    sha256_text,
    state_from_json,
    state_to_json,
)


NOW = datetime(2026, 8, 14, 8, 0, tzinfo=UTC)


def candidate(suffix: str = "1", **overrides: object) -> CandidateItem:
    values: dict[str, object] = {
        "candidate_id": f"candidate-{suffix}",
        "region": Region.GLOBAL,
        "source_reference": "Synthetic Official",
        "source_type": SourceType.OFFICIAL,
        "source_priority": SourcePriority.P0,
        "source_credibility": SourceCredibility.HIGH,
        "source_fact_citation": FactCitation.YES,
        "collector_type": CollectorType.RSS_FEED,
        "source_url": f"https://example.invalid/public/{suffix}",
        "title": "Synthetic model release",
        "source_excerpt": "The public model is now available.",
        "source_published_at": NOW - timedelta(hours=1),
        "collected_at": NOW,
        "first_seen_at": NOW,
        "last_seen_at": NOW,
        "eterna_tags": (EternaTag.AGENT,),
        "raw_evidence_reference": f"https://example.invalid/feed#{suffix}",
        "collection_status": CollectionStatus.COLLECTED,
    }
    values.update(overrides)
    return CandidateItem(**values)  # type: ignore[arg-type]


def state_with(*candidates: CandidateItem):
    if not candidates:
        raise AssertionError("fixture requires at least one Candidate")
    state = empty_region_state(candidates[0].region)
    for item in candidates:
        state = register_candidate_observation(
            state,
            observation_key=f"observation-{item.candidate_id}",
            candidate_id=item.candidate_id,
            source_reference=item.source_reference,
            observed_at=item.last_seen_at,
            canonical_url=item.source_url,
            source_object_id=item.candidate_id,
            content_fingerprint=sha256_text(
                f"{item.title}|{item.source_excerpt}|{item.source_url}"
            ),
        )
    return state


def descriptor(**overrides: object) -> EventDescriptor:
    values: dict[str, object] = {
        "subject": "Synthetic Official",
        "action": "released",
        "object_name": "Synthetic Model",
        "version": "v1",
        "technical_categories": (TechnicalCategory.MODEL,),
    }
    values.update(overrides)
    return EventDescriptor(**values)  # type: ignore[arg-type]


def test_evidence_is_complete_deterministic_and_traceable() -> None:
    item = candidate()
    first = cluster_candidates(
        [ClusterInput(item, descriptor())],
        state=state_with(item),
    )
    second = cluster_candidates(
        [ClusterInput(item, descriptor())],
        state=state_with(item),
    )

    assert first.evidences == second.evidences
    evidence = first.evidences[0]
    assert evidence.evidence_id.startswith("evidence_")
    assert evidence.candidate_references == (item.candidate_id,)
    assert evidence.source_reference == item.source_reference
    assert evidence.source_url == item.source_url
    assert evidence.source_published_at == item.source_published_at
    assert evidence.collected_at == item.collected_at
    assert evidence.source_priority is SourcePriority.P0
    assert evidence.source_credibility is SourceCredibility.HIGH
    assert evidence.is_primary_source is True
    assert evidence.relation is EvidenceRelation.SUPPORTS
    assert dict(evidence.traceability) == {
        "candidate_id": item.candidate_id,
        "source_reference": item.source_reference,
        "source_url": item.source_url,
        "raw_evidence_reference": item.raw_evidence_reference,
    }
    assert "final information status" in evidence.evidence_note


def test_p0_is_not_unconditionally_primary_for_an_unrelated_subject() -> None:
    item = candidate()
    result = cluster_candidates(
        [ClusterInput(item, descriptor(subject="Different Company"))],
        state=state_with(item),
    )

    assert result.evidences[0].is_primary_source is False


def test_exact_duplicate_returns_one_evidence_and_one_event() -> None:
    item = candidate()
    result = cluster_candidates(
        [ClusterInput(item, descriptor()), ClusterInput(item, descriptor())],
        state=state_with(item),
    )

    assert len(result.evidences) == 1
    assert len(result.event_drafts) == 1
    assert len(result.state.evidences) == 1
    assert len(result.state.events) == 1
    assert result.near_duplicates == ()


def test_exact_duplicate_is_idempotent_across_state_round_trip() -> None:
    item = candidate()
    first = cluster_candidates(
        [ClusterInput(item, descriptor())],
        state=state_with(item),
    )
    restored = state_from_json(
        state_to_json(first.state),
        expected_region=Region.GLOBAL,
    )
    second = cluster_candidates(
        [ClusterInput(item, descriptor())],
        state=restored,
    )

    assert second.state == restored
    assert second.evidences == first.evidences
    assert second.event_drafts[0].event_id == first.event_drafts[0].event_id


def test_near_duplicate_keeps_provenance_but_not_independent_confirmation() -> None:
    original = candidate("original")
    repost = candidate(
        "repost",
        source_reference="Synthetic Media",
        source_type=SourceType.MEDIA,
        source_priority=SourcePriority.P2,
        source_credibility=SourceCredibility.MEDIUM,
        source_fact_citation=FactCitation.CONDITIONAL,
    )
    result = cluster_candidates(
        [ClusterInput(original), ClusterInput(repost)],
        state=state_with(original, repost),
    )

    assert near_duplicate_signature(original) == near_duplicate_signature(repost)
    assert len(result.evidences) == 2
    assert len(result.event_drafts) == 1
    assert len(result.near_duplicates) == 1
    link = result.near_duplicates[0]
    assert link.counts_as_independent_confirmation is False
    assert link.candidate_references == (original.candidate_id, repost.candidate_id)
    draft = result.event_drafts[0]
    assert set(draft.evidence_references) == {
        evidence.evidence_id for evidence in result.evidences
    }
    assert draft.independent_evidence_references == (link.primary_evidence_id,)
    duplicate_state = next(
        item
        for item in result.state.evidences
        if item.evidence_id == link.duplicate_evidence_id
    )
    assert duplicate_state.independent_confirmation is False
    assert duplicate_state.duplicate_of_evidence_id == link.primary_evidence_id


def test_near_duplicate_marking_survives_repeat_run() -> None:
    original = candidate("original")
    repost = candidate("repost", source_reference="Synthetic Media")
    first = cluster_candidates(
        [ClusterInput(original), ClusterInput(repost)],
        state=state_with(original, repost),
    )
    second = cluster_candidates(
        [ClusterInput(repost)],
        state=state_from_json(state_to_json(first.state)),
    )

    assert second.state == first.state
    assert len(second.near_duplicates) == 1
    assert second.event_drafts[0].independent_evidence_references == (
        first.near_duplicates[0].primary_evidence_id,
    )


def test_near_duplicate_primary_is_deterministic_across_input_order() -> None:
    official = candidate("official")
    repost = candidate(
        "repost",
        source_reference="Synthetic Media",
        source_type=SourceType.MEDIA,
        source_priority=SourcePriority.P2,
        source_credibility=SourceCredibility.MEDIUM,
        source_fact_citation=FactCitation.CONDITIONAL,
    )
    initial = state_with(official, repost)

    forward = cluster_candidates(
        [ClusterInput(official), ClusterInput(repost)],
        state=initial,
    )
    reverse = cluster_candidates(
        [ClusterInput(repost), ClusterInput(official)],
        state=initial,
    )

    assert forward.state == reverse.state
    assert forward.near_duplicates == reverse.near_duplicates


def test_same_structured_event_clusters_different_evidence() -> None:
    official = candidate("official")
    engineer = candidate(
        "engineer",
        source_reference="Synthetic Engineer",
        source_type=SourceType.PERSON,
        source_priority=SourcePriority.P1,
        source_fact_citation=FactCitation.CONDITIONAL,
        title="Engineer explains the model release",
        source_excerpt="A public explanation of the release capabilities.",
        eterna_tags=(EternaTag.AI_CODING,),
        first_seen_at=NOW + timedelta(minutes=2),
        last_seen_at=NOW + timedelta(minutes=2),
    )
    result = cluster_candidates(
        [ClusterInput(official, descriptor()), ClusterInput(engineer, descriptor())],
        state=state_with(official, engineer),
    )

    assert len(result.event_drafts) == 1
    assert len(result.event_drafts[0].evidence_references) == 2
    assert len(result.event_drafts[0].independent_evidence_references) == 2
    assert result.event_drafts[0].technical_categories == (TechnicalCategory.MODEL,)
    assert set(result.event_drafts[0].eterna_tags) == {
        EternaTag.AGENT,
        EternaTag.AI_CODING,
    }


@pytest.mark.parametrize(
    ("left", "right"),
    [
        (descriptor(version="v1"), descriptor(version="v2")),
        (descriptor(action="released"), descriptor(action="updated pricing")),
        (descriptor(object_name="Model A"), descriptor(object_name="Product UI")),
        (descriptor(subject="Company A"), descriptor(subject="Company B")),
    ],
)
def test_distinct_subject_action_object_or_version_never_merge(
    left: EventDescriptor,
    right: EventDescriptor,
) -> None:
    first = candidate("1")
    second = candidate(
        "2",
        title="A superficially similar title",
        source_excerpt="Different public evidence.",
    )
    result = cluster_candidates(
        [ClusterInput(first, left), ClusterInput(second, right)],
        state=state_with(first, second),
    )

    assert len(result.event_drafts) == 2
    assert stable_event_id(first, left) != stable_event_id(second, right)


def test_title_similarity_alone_does_not_merge_uncertain_items() -> None:
    first = candidate("1", title="Model update", source_excerpt="Capability A.")
    second = candidate("2", title="Model update", source_excerpt="Capability B.")
    result = cluster_candidates(
        [ClusterInput(first), ClusterInput(second)],
        state=state_with(first, second),
    )

    assert len(result.event_drafts) == 2
    assert result.near_duplicates == ()


def test_matching_content_on_a_distant_published_day_does_not_near_merge() -> None:
    first = candidate("1")
    second = candidate(
        "2",
        source_published_at=NOW + timedelta(days=30),
        collected_at=NOW + timedelta(days=30),
        first_seen_at=NOW + timedelta(days=30),
        last_seen_at=NOW + timedelta(days=30),
    )
    result = cluster_candidates(
        [ClusterInput(first), ClusterInput(second)],
        state=state_with(first, second),
    )

    assert near_duplicate_signature(first) != near_duplicate_signature(second)
    assert len(result.event_drafts) == 2
    assert result.near_duplicates == ()


def test_eterna_tags_do_not_participate_in_event_identity() -> None:
    first = candidate("1", eterna_tags=(EternaTag.AFTELLE,))
    second = candidate(
        "2",
        title="Independent source confirms release",
        source_excerpt="Independent release evidence.",
        eterna_tags=(EternaTag.RUNTIME_CORE,),
    )

    assert stable_event_id(first, descriptor()) == stable_event_id(second, descriptor())


def test_technical_categories_aggregate_but_do_not_change_event_identity() -> None:
    first = candidate("1")
    second = candidate(
        "2",
        title="Independent release detail",
        source_excerpt="A distinct detail for the same release.",
    )
    model_descriptor = descriptor(technical_categories=(TechnicalCategory.MODEL,))
    product_descriptor = descriptor(technical_categories=(TechnicalCategory.PRODUCT,))
    result = cluster_candidates(
        [
            ClusterInput(first, model_descriptor),
            ClusterInput(second, product_descriptor),
        ],
        state=state_with(first, second),
    )

    assert stable_event_id(first, model_descriptor) == stable_event_id(
        second, product_descriptor
    )
    assert result.event_drafts[0].technical_categories == (
        TechnicalCategory.MODEL,
        TechnicalCategory.PRODUCT,
    )


def test_supporting_and_contradicting_evidence_coexist_without_final_status() -> None:
    support = candidate("support")
    contradiction = candidate(
        "contradiction",
        title="Release timing disputed",
        source_excerpt="A public source disputes the announced timing.",
    )
    result = cluster_candidates(
        [
            ClusterInput(support, descriptor(), EvidenceRelation.SUPPORTS),
            ClusterInput(
                contradiction,
                descriptor(),
                EvidenceRelation.CONTRADICTS,
            ),
        ],
        state=state_with(support, contradiction),
    )

    assert {item.relation for item in result.evidences} == {
        EvidenceRelation.SUPPORTS,
        EvidenceRelation.CONTRADICTS,
    }
    draft = result.event_drafts[0]
    assert not hasattr(draft, "information_status")
    assert not hasattr(draft, "current_confidence")
    assert not hasattr(draft, "importance")
    event_state = result.state.events[0]
    assert event_state.initial_status is None
    assert event_state.information_status is None
    assert event_state.status_history == ()


def test_preanalysis_event_rejects_status_transition() -> None:
    item = candidate()
    result = cluster_candidates(
        [ClusterInput(item, descriptor())],
        state=state_with(item),
    )
    entry = StatusHistoryEntry(
        changed_at=NOW + timedelta(hours=1),
        previous_status=InformationStatus.UNCONFIRMED,
        new_status=InformationStatus.CONFIRMED,
        evidence_references=(result.evidences[0].evidence_id,),
        reason="Synthetic transition that belongs to A9.",
    )

    with pytest.raises(StateConflictError, match="pre-analysis"):
        append_event_status(result.state, event_id=result.event_drafts[0].event_id, entry=entry)


def test_stable_evidence_id_cannot_be_rebound() -> None:
    first = candidate("1")
    second = candidate("2")
    result = cluster_candidates(
        [ClusterInput(first, descriptor())],
        state=state_with(first, second),
    )

    with pytest.raises(StateConflictError, match="rebound"):
        register_evidence_reference(
            result.state,
            evidence_id=result.evidences[0].evidence_id,
            candidate_references=(second.candidate_id,),
        )


def test_stable_event_id_cannot_be_rebound_to_different_evidence() -> None:
    first = candidate("1")
    second = candidate("2", source_excerpt="Distinct second Evidence.")
    result = cluster_candidates(
        [ClusterInput(first, descriptor())],
        state=state_with(first, second),
    )
    state = register_evidence_reference(
        result.state,
        evidence_id="evidence-manual-second",
        candidate_references=(second.candidate_id,),
    )

    with pytest.raises(StateConflictError, match="different state"):
        register_event_state(
            state,
            event_id=result.event_drafts[0].event_id,
            evidence_references=("evidence-manual-second",),
        )


def test_global_and_china_are_isolated() -> None:
    global_item = candidate("global")
    china_item = candidate(
        "china",
        region=Region.CHINA,
        source_url="https://example.cn/public/china",
        raw_evidence_reference="https://example.cn/feed#china",
    )

    assert stable_event_id(global_item, descriptor()) != stable_event_id(
        china_item, descriptor()
    )
    with pytest.raises(ClusteringError, match="Region"):
        cluster_candidates(
            [ClusterInput(global_item), ClusterInput(china_item)],
            state=state_with(global_item),
        )


def test_candidate_must_be_registered_before_clustering() -> None:
    item = candidate()

    with pytest.raises(ClusteringError, match="registered"):
        cluster_candidates(
            [ClusterInput(item)],
            state=empty_region_state(Region.GLOBAL),
        )
