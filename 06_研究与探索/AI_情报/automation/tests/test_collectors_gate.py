"""Offline tests for Config, Registry, Region, and A6 boundary gates."""

from dataclasses import FrozenInstanceError, fields
from datetime import UTC, datetime
from pathlib import Path
from types import MappingProxyType

import pytest

from collectors.base import CollectionError, CollectionErrorKind, RawCollectorRecord
from collectors.dispatch import collect_configured_source
from pipeline.config import SourceConfigEntry, load_source_config
from pipeline.models import CandidateItem, Region
from pipeline.registry import load_source_registry
from tests.collector_helpers import StaticTransport, configured_source


NOW = datetime(2026, 8, 14, 0, 0, tzinfo=UTC)
AUTOMATION_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = AUTOMATION_ROOT.parent / "Stage1" / "Source_Registry_v0.1.md"


def test_disabled_source_is_rejected_before_transport() -> None:
    source, registry = configured_source(
        name="Disabled Official",
        region="Global",
        collector_type="public_web",
        url="https://disabled.example.invalid/",
        enabled=False,
    )
    transport = StaticTransport(
        b"<html></html>",
        final_url=source.url,
        content_type="text/html",
    )

    with pytest.raises(CollectionError) as captured:
        collect_configured_source(
            source,
            Region.GLOBAL,
            registry,
            transport,
            collected_at=NOW,
        )

    assert captured.value.kind is CollectionErrorKind.SOURCE_DISABLED
    assert transport.calls == []


def test_region_mismatch_is_rejected_before_transport() -> None:
    source, registry = configured_source(
        name="China Official",
        region="China",
        collector_type="public_web",
        url="https://china.example.invalid/",
    )
    transport = StaticTransport(
        b"<html></html>",
        final_url=source.url,
        content_type="text/html",
    )

    with pytest.raises(CollectionError) as captured:
        collect_configured_source(
            source,
            Region.GLOBAL,
            registry,
            transport,
            collected_at=NOW,
        )

    assert captured.value.kind is CollectionErrorKind.SOURCE_REJECTED
    assert transport.calls == []


def test_naive_collected_at_is_rejected_before_transport() -> None:
    source, registry = configured_source(
        name="Official",
        region="Global",
        collector_type="public_web",
        url="https://official.example.invalid/",
    )
    transport = StaticTransport(
        b"<html></html>",
        final_url=source.url,
        content_type="text/html",
    )

    with pytest.raises(CollectionError, match="timezone-aware"):
        collect_configured_source(
            source,
            Region.GLOBAL,
            registry,
            transport,
            collected_at=datetime(2026, 8, 14, 0, 0),
        )
    assert transport.calls == []


def test_forged_registry_url_is_revalidated_before_transport() -> None:
    source, registry = configured_source(
        name="Official",
        region="Global",
        collector_type="public_web",
        url="https://official.example.invalid/",
    )
    forged = SourceConfigEntry(
        registry_ref=source.registry_ref,
        region=source.region,
        collector_type=source.collector_type,
        url="https://forged.example.invalid/",
        enabled=True,
        parameters=MappingProxyType({}),
    )
    transport = StaticTransport(
        b"<html></html>",
        final_url=forged.url,
        content_type="text/html",
    )

    with pytest.raises(CollectionError) as captured:
        collect_configured_source(
            forged,
            Region.GLOBAL,
            registry,
            transport,
            collected_at=NOW,
        )

    assert captured.value.kind is CollectionErrorKind.SOURCE_REJECTED
    assert transport.calls == []


@pytest.mark.parametrize(
    ("region", "config_name"),
    [(Region.GLOBAL, "global_sources.json"), (Region.CHINA, "china_sources.json")],
)
def test_current_a2_sources_all_resolve_to_an_a5_adapter(
    region: Region,
    config_name: str,
) -> None:
    registry = load_source_registry(REGISTRY_PATH)
    config = load_source_config(
        AUTOMATION_ROOT / "config" / config_name,
        region.value,
        registry,
    )

    for source in config.sources:
        if source.collector_type == "official_api":
            transport = StaticTransport(
                b"[]",
                final_url="https://api.github.com/synthetic",
                content_type="application/json",
            )
        else:
            transport = StaticTransport(
                b"<html><head><title>Updates</title></head><body>Public update.</body></html>",
                final_url=source.url,
                content_type="text/html",
            )
        collect_configured_source(
            source,
            region,
            registry,
            transport,
            collected_at=NOW,
        )
        assert len(transport.calls) == 1


def test_unknown_official_api_adapter_is_default_denied() -> None:
    source, registry = configured_source(
        name="Unsupported Official API",
        region="Global",
        collector_type="official_api",
        url="https://api.example.invalid/",
    )
    transport = StaticTransport(
        b"{}",
        final_url=source.url,
        content_type="application/json",
    )

    with pytest.raises(CollectionError) as captured:
        collect_configured_source(
            source,
            Region.GLOBAL,
            registry,
            transport,
            collected_at=NOW,
        )

    assert captured.value.kind is CollectionErrorKind.UNSUPPORTED_CONTENT
    assert transport.calls == []


def test_raw_record_is_immutable_and_has_no_a6_or_analysis_fields() -> None:
    source, registry = configured_source(
        name="Official Page",
        region="Global",
        collector_type="public_web",
        url="https://official.example.invalid/",
    )
    transport = StaticTransport(
        b"<html><head><title>Updates</title></head><body>Public update.</body></html>",
        final_url=source.url,
        content_type="text/html",
    )

    batch = collect_configured_source(
        source,
        Region.GLOBAL,
        registry,
        transport,
        collected_at=NOW,
    )
    record = batch.records[0]
    field_names = {field.name for field in fields(RawCollectorRecord)}

    assert type(record) is RawCollectorRecord
    assert not isinstance(record, CandidateItem)
    assert field_names.isdisjoint(
        {
            "candidate_id",
            "first_seen_at",
            "last_seen_at",
            "information_status",
            "current_confidence",
            "importance",
            "eterna_tags",
        }
    )
    with pytest.raises(FrozenInstanceError):
        record.title = "Changed"  # type: ignore[misc]


def test_no_secret_is_required_for_public_collection(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in ("GITHUB_TOKEN", "HF_TOKEN", "HUGGING_FACE_HUB_TOKEN"):
        monkeypatch.delenv(name, raising=False)
    source, registry = configured_source(
        name="Official Page",
        region="Global",
        collector_type="public_web",
        url="https://official.example.invalid/",
    )
    transport = StaticTransport(
        b"<html><head><title>Updates</title></head><body>Public update.</body></html>",
        final_url=source.url,
        content_type="text/html",
    )

    assert collect_configured_source(
        source,
        Region.GLOBAL,
        registry,
        transport,
        collected_at=NOW,
    ).records
