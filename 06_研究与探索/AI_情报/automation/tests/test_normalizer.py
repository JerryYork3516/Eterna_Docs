"""Offline tests for A6 Candidate normalization and State continuity."""

from dataclasses import fields, replace
from datetime import UTC, datetime, timedelta
from pathlib import Path
from types import MappingProxyType

import pytest

from collectors.base import RawCollectorRecord
from pipeline.models import (
    CandidateItem,
    CollectionStatus,
    CollectorType,
    EternaTag,
    FactCitation,
    Region,
    SourceCredibility,
    SourcePriority,
    SourceType,
)
from pipeline.normalizer import (
    NormalizationError,
    candidate_identity,
    canonicalize_public_url,
    content_fingerprint,
    normalize_batch,
    normalize_record,
)
from pipeline.registry import RegistryEntry, SourceRegistry, load_source_registry
from pipeline.state import (
    StateConflictError,
    empty_region_state,
    register_candidate_observation,
)


NOW = datetime(2026, 8, 14, 8, 0, tzinfo=UTC)
REGISTRY_PATH = Path(__file__).resolve().parents[2] / "Stage1" / "Source_Registry_v0.1.md"


def registry_entry(
    *,
    name: str = "Synthetic Official",
    region: str = "Global",
    urls: tuple[str, ...] = ("https://official.example.invalid/",),
    source_type: str = "Official",
    priority: str = "P0",
    credibility: str = "High",
    fact_citation: str = "Yes",
    eterna_tags: tuple[str, ...] = ("Agent", "AI Coding"),
) -> RegistryEntry:
    return RegistryEntry(
        name=name,
        source_type=source_type,
        region=region,
        platform="Synthetic public source",
        urls=urls,
        priority=priority,
        credibility=credibility,
        fact_citation=fact_citation,
        eterna_tags=eterna_tags,
    )


def registry(*entries: RegistryEntry) -> SourceRegistry:
    selected = entries or (registry_entry(),)
    return SourceRegistry(
        entries=MappingProxyType({entry.name: entry for entry in selected})
    )


def raw_record(**overrides: object) -> RawCollectorRecord:
    values: dict[str, object] = {
        "source_reference": "Synthetic Official",
        "region": Region.GLOBAL,
        "collector_type": CollectorType.WEB_PAGE_MONITOR,
        "source_url": "https://official.example.invalid/news/item#details",
        "source_object_id": None,
        "title": "Public model update",
        "excerpt": "Minimal public excerpt.",
        "published_at_raw": "2026-08-14T07:00:00Z",
        "published_at": NOW - timedelta(hours=1),
        "collected_at": NOW,
        "raw_reference": "https://official.example.invalid/news/item#details",
        "metadata": {"synthetic": True},
    }
    values.update(overrides)
    return RawCollectorRecord(**values)  # type: ignore[arg-type]


def test_registry_projection_parses_frozen_fields_exactly() -> None:
    source_registry = load_source_registry(REGISTRY_PATH)
    openai = source_registry.get("OpenAI")

    assert openai.source_type == "Official"
    assert openai.priority == "P0"
    assert openai.credibility == "High"
    assert openai.fact_citation == "Yes"
    assert openai.eterna_tags == (
        "Agent",
        "AI Coding",
        "Voice / STS",
        "Multimodal",
        "Business / Ecosystem",
    )


def test_candidate_maps_registry_and_raw_fields_exactly() -> None:
    candidate, state = normalize_record(
        raw_record(), registry(), empty_region_state(Region.GLOBAL)
    )

    assert type(candidate) is CandidateItem
    assert candidate.region is Region.GLOBAL
    assert candidate.source_reference == "Synthetic Official"
    assert candidate.source_type is SourceType.OFFICIAL
    assert candidate.source_priority is SourcePriority.P0
    assert candidate.source_credibility is SourceCredibility.HIGH
    assert candidate.source_fact_citation is FactCitation.YES
    assert candidate.eterna_tags == (EternaTag.AGENT, EternaTag.AI_CODING)
    assert candidate.source_url == "https://official.example.invalid/news/item"
    assert candidate.raw_evidence_reference.endswith("#details")
    assert candidate.first_seen_at == candidate.last_seen_at == NOW
    assert state.candidates[0].candidate_id == candidate.candidate_id


def test_collection_status_uses_only_available_public_content() -> None:
    collected, _ = normalize_record(
        raw_record(excerpt="Public body."),
        registry(),
        empty_region_state(Region.GLOBAL),
    )
    metadata_only, _ = normalize_record(
        raw_record(excerpt=None),
        registry(),
        empty_region_state(Region.GLOBAL),
    )

    assert collected.collection_status is CollectionStatus.COLLECTED
    assert metadata_only.collection_status is CollectionStatus.METADATA_ONLY


def test_unknown_source_published_time_remains_unknown() -> None:
    candidate, _ = normalize_record(
        raw_record(published_at=None, published_at_raw=None),
        registry(),
        empty_region_state(Region.GLOBAL),
    )

    assert candidate.source_published_at is None
    assert candidate.collected_at == NOW


def test_canonical_url_normalizes_only_safe_syntax() -> None:
    value = canonicalize_public_url(
        "HTTPS://Example.Invalid:443/a/%7Eitem?b=2&a=1#fragment"
    )

    assert value == "https://example.invalid/a/%7Eitem?b=2&a=1"
    assert canonicalize_public_url("http://example.invalid:80") == "http://example.invalid/"


@pytest.mark.parametrize(
    "value",
    [
        "file:///tmp/item",
        "https://user@example.invalid/item",
        "https://127.0.0.1/item",
        "https://localhost/item",
        "https://example.invalid/a b",
    ],
)
def test_canonical_url_rejects_unsafe_or_non_public_values(value: str) -> None:
    with pytest.raises(NormalizationError):
        canonicalize_public_url(value)


def test_candidate_identity_is_stable_and_ignores_observation_content() -> None:
    first = raw_record(source_object_id="object-101")
    changed = replace(
        first,
        title="Changed title",
        excerpt="Changed public excerpt.",
        published_at=NOW,
        collected_at=NOW + timedelta(hours=1),
    )
    canonical = canonicalize_public_url(first.source_url)

    assert candidate_identity(first, canonical) == candidate_identity(changed, canonical)
    observation_key, candidate_id = candidate_identity(first, canonical)
    assert observation_key.startswith("observation_")
    assert candidate_id.startswith("candidate_")
    assert len(candidate_id) == len("candidate_") + 64


def test_identity_prefers_source_object_id_over_url() -> None:
    first = raw_record(source_object_id="stable-object")
    moved = replace(first, source_url="https://official.example.invalid/new-path")

    assert candidate_identity(
        first, canonicalize_public_url(first.source_url)
    ) == candidate_identity(moved, canonicalize_public_url(moved.source_url))


def test_url_fallback_identity_canonicalizes_equivalent_urls() -> None:
    first = raw_record(source_url="HTTPS://OFFICIAL.EXAMPLE.INVALID:443/item#a")
    second = replace(
        first,
        source_url="https://official.example.invalid/item#b",
        raw_reference="https://official.example.invalid/item#b",
    )

    assert candidate_identity(
        first, canonicalize_public_url(first.source_url)
    ) == candidate_identity(second, canonicalize_public_url(second.source_url))


def test_region_and_source_reference_isolate_candidate_identity() -> None:
    base = raw_record(source_object_id="object-1")
    china = replace(base, region=Region.CHINA)
    other_source = replace(base, source_reference="Other Official")
    canonical = canonicalize_public_url(base.source_url)

    assert candidate_identity(base, canonical) != candidate_identity(china, canonical)
    assert candidate_identity(base, canonical) != candidate_identity(other_source, canonical)


def test_content_fingerprint_excludes_collected_at_but_tracks_content() -> None:
    first = raw_record()
    later = replace(first, collected_at=NOW + timedelta(hours=2))
    changed = replace(first, excerpt="Changed public excerpt.")
    canonical = canonicalize_public_url(first.source_url)

    assert content_fingerprint(first, canonical) == content_fingerprint(later, canonical)
    assert content_fingerprint(first, canonical) != content_fingerprint(changed, canonical)


def test_repeat_observation_preserves_identity_and_advances_state() -> None:
    first = raw_record(source_object_id="object-1")
    candidate, state = normalize_record(
        first, registry(), empty_region_state(Region.GLOBAL)
    )
    later_record = replace(
        first,
        excerpt="Updated public excerpt.",
        collected_at=NOW + timedelta(hours=2),
    )
    later_candidate, state = normalize_record(later_record, registry(), state)

    assert later_candidate.candidate_id == candidate.candidate_id
    assert later_candidate.first_seen_at == NOW
    assert later_candidate.last_seen_at == NOW + timedelta(hours=2)
    assert len(state.candidates) == 1
    assert state.candidates[0].content_fingerprint == content_fingerprint(
        later_record, canonicalize_public_url(later_record.source_url)
    )


def test_object_identity_survives_public_url_change() -> None:
    first = raw_record(source_object_id="object-1")
    candidate, state = normalize_record(
        first, registry(), empty_region_state(Region.GLOBAL)
    )
    moved = replace(
        first,
        source_url="https://official.example.invalid/news/renamed-item",
        raw_reference="https://official.example.invalid/news/renamed-item",
        collected_at=NOW + timedelta(minutes=5),
    )
    moved_candidate, state = normalize_record(moved, registry(), state)

    assert moved_candidate.candidate_id == candidate.candidate_id
    assert state.candidates[0].canonical_url.endswith("/renamed-item")


def test_object_identity_does_not_merge_across_source_hosts() -> None:
    first = raw_record(source_object_id="object-1")
    _candidate, state = normalize_record(
        first, registry(), empty_region_state(Region.GLOBAL)
    )
    cross_host = replace(
        first,
        source_url="https://other.example.invalid/news/item",
        raw_reference="https://other.example.invalid/news/item",
        collected_at=NOW + timedelta(minutes=5),
    )

    with pytest.raises(NormalizationError):
        normalize_record(cross_host, registry(), state)


def test_repeat_observation_time_regression_fails_closed() -> None:
    candidate, state = normalize_record(
        raw_record(), registry(), empty_region_state(Region.GLOBAL)
    )

    with pytest.raises(NormalizationError):
        normalize_record(
            raw_record(collected_at=NOW - timedelta(seconds=1)),
            registry(),
            state,
        )
    assert candidate.first_seen_at == NOW


def test_existing_identity_rebinding_fails_closed() -> None:
    record = raw_record(source_object_id="object-1")
    canonical = canonicalize_public_url(record.source_url)
    observation_key, _candidate_id = candidate_identity(record, canonical)
    state = register_candidate_observation(
        empty_region_state(Region.GLOBAL),
        observation_key=observation_key,
        candidate_id="candidate_" + "0" * 64,
        source_reference=record.source_reference,
        observed_at=NOW,
        canonical_url=canonical,
        source_object_id=record.source_object_id,
        content_fingerprint="0" * 64,
    )

    with pytest.raises(NormalizationError):
        normalize_record(record, registry(), state)


@pytest.mark.parametrize(
    ("entry", "record"),
    [
        (
            registry_entry(
                urls=("https://github.com/approved-org",),
            ),
            raw_record(
                collector_type=CollectorType.OFFICIAL_API,
                source_url="https://github.com/other-org/repository",
                source_object_id="1",
            ),
        ),
        (
            registry_entry(
                urls=("https://huggingface.co/approved-org",),
            ),
            raw_record(
                collector_type=CollectorType.OFFICIAL_API,
                source_url="https://huggingface.co/other-org/model",
                source_object_id="2",
            ),
        ),
    ],
)
def test_official_api_cross_organization_url_fails(
    entry: RegistryEntry,
    record: RawCollectorRecord,
) -> None:
    with pytest.raises(NormalizationError, match="registered organization"):
        normalize_record(record, registry(entry), empty_region_state(Region.GLOBAL))


@pytest.mark.parametrize(
    ("registered_url", "source_url"),
    [
        (
            "https://github.com/approved-org",
            "https://github.com/approved-org/repository/releases/tag/v1",
        ),
        (
            "https://huggingface.co/approved-org",
            "https://huggingface.co/datasets/approved-org/public-data",
        ),
        (
            "https://huggingface.co/approved-org",
            "https://huggingface.co/spaces/approved-org/public-space",
        ),
    ],
)
def test_official_api_registered_organization_url_passes(
    registered_url: str,
    source_url: str,
) -> None:
    entry = registry_entry(urls=(registered_url,))
    candidate, _ = normalize_record(
        raw_record(
            collector_type=CollectorType.OFFICIAL_API,
            source_url=source_url,
            source_object_id="public-object",
        ),
        registry(entry),
        empty_region_state(Region.GLOBAL),
    )

    assert candidate.source_url == source_url


def test_official_api_unknown_host_is_default_denied() -> None:
    with pytest.raises(NormalizationError, match="unsupported public host"):
        normalize_record(
            raw_record(
                collector_type=CollectorType.OFFICIAL_API,
                source_object_id="object-1",
            ),
            registry(),
            empty_region_state(Region.GLOBAL),
        )


def test_region_and_registry_mismatches_fail() -> None:
    with pytest.raises(NormalizationError, match="RegionState"):
        normalize_record(
            raw_record(), registry(), empty_region_state(Region.CHINA)
        )
    with pytest.raises(NormalizationError, match="Source Registry"):
        normalize_record(
            raw_record(),
            registry(registry_entry(region="China")),
            empty_region_state(Region.GLOBAL),
        )


def test_unknown_registry_enum_or_tag_fails_without_guessing() -> None:
    bad_tag = registry_entry(eterna_tags=("Ecosystem",))

    with pytest.raises(NormalizationError, match="without guessing"):
        normalize_record(
            raw_record(), registry(bad_tag), empty_region_state(Region.GLOBAL)
        )


def test_batch_preserves_valid_order_and_exposes_item_error() -> None:
    valid_one = raw_record(source_object_id="one", title="One")
    invalid = replace(valid_one, source_reference="Missing Source", source_object_id="bad")
    valid_two = replace(valid_one, source_object_id="two", title="Two")

    result = normalize_batch(
        (valid_one, invalid, valid_two),
        registry(),
        empty_region_state(Region.GLOBAL),
    )

    assert [candidate.title for candidate in result.candidates] == ["One", "Two"]
    assert len(result.item_errors) == 1
    assert result.item_errors[0].item_index == 1
    assert len(result.state.candidates) == 2


def test_candidate_has_no_a7_or_analysis_fields() -> None:
    candidate, _ = normalize_record(
        raw_record(), registry(), empty_region_state(Region.GLOBAL)
    )
    names = {field.name for field in fields(candidate)}

    assert names.isdisjoint(
        {
            "evidence_id",
            "event_id",
            "information_status",
            "current_confidence",
            "importance",
            "why_it_matters",
        }
    )


def test_state_still_rejects_stable_object_identity_rebinding() -> None:
    state = empty_region_state(Region.GLOBAL)
    state = register_candidate_observation(
        state,
        observation_key="observation-stable",
        candidate_id="candidate-stable",
        source_reference="Synthetic Official",
        observed_at=NOW,
        canonical_url="https://official.example.invalid/item",
        source_object_id="object-1",
        content_fingerprint="a" * 64,
    )

    with pytest.raises(StateConflictError, match="rebind"):
        register_candidate_observation(
            state,
            observation_key="observation-stable",
            candidate_id="candidate-stable",
            source_reference="Synthetic Official",
            observed_at=NOW + timedelta(minutes=1),
            canonical_url="https://official.example.invalid/item",
            source_object_id="object-2",
            content_fingerprint="b" * 64,
        )
