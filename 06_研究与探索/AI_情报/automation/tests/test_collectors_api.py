"""Offline GitHub and Hugging Face official public API Adapter tests."""

from datetime import UTC, datetime
import json

import pytest

from collectors.base import CollectionError, CollectionErrorKind
from collectors.dispatch import collect_configured_source
from collectors.github import github_organization_from_url
from collectors.huggingface import huggingface_organization_from_url
from pipeline.models import CollectorType, Region
from tests.collector_helpers import StaticTransport, configured_source


NOW = datetime(2026, 8, 14, 0, 0, tzinfo=UTC)


def test_github_organization_url_mapping_is_exact() -> None:
    assert github_organization_from_url("https://github.com/openai") == "openai"
    for invalid in (
        "http://github.com/openai",
        "https://github.com/openai/repository",
        "https://github.com/openai?tab=repositories",
        "https://example.invalid/openai",
    ):
        with pytest.raises(CollectionError):
            github_organization_from_url(invalid)


def test_github_valid_response_preserves_object_url_and_times() -> None:
    source, registry = configured_source(
        name="Synthetic GitHub Org",
        region="Global",
        collector_type="official_api",
        url="https://github.com/synthetic-org",
    )
    payload = [
        {
            "id": 101,
            "full_name": "synthetic-org/repository",
            "html_url": "https://github.com/synthetic-org/repository",
            "description": "Public repository metadata.",
            "owner": {"login": "synthetic-org"},
            "created_at": "2026-08-10T01:02:03Z",
            "updated_at": "2026-08-13T01:02:03Z",
            "pushed_at": "2026-08-14T01:02:03Z",
            "archived": False,
        }
    ]
    transport = StaticTransport(
        json.dumps(payload).encode(),
        final_url="https://api.github.com/orgs/synthetic-org/repos?per_page=30",
        content_type="application/json",
    )

    batch = collect_configured_source(
        source,
        Region.GLOBAL,
        registry,
        transport,
        collected_at=NOW,
    )

    record = batch.records[0]
    assert record.collector_type is CollectorType.OFFICIAL_API
    assert record.source_object_id == "101"
    assert record.source_url == "https://github.com/synthetic-org/repository"
    assert record.published_at == datetime(2026, 8, 10, 1, 2, 3, tzinfo=UTC)
    assert record.metadata["pushed_at"] == "2026-08-14T01:02:03Z"
    assert len(transport.calls) == 1
    assert transport.calls[0][0].startswith("https://api.github.com/orgs/synthetic-org/repos?")


def test_github_malformed_response_is_explicit_failure() -> None:
    source, registry = configured_source(
        name="Synthetic GitHub Org",
        region="Global",
        collector_type="official_api",
        url="https://github.com/synthetic-org",
    )
    transport = StaticTransport(
        b'{"message":"unexpected"}',
        final_url="https://api.github.com/orgs/synthetic-org/repos",
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
    assert captured.value.kind is CollectionErrorKind.INVALID_CONTENT


def test_github_rate_limit_is_propagated_without_fallback() -> None:
    source, registry = configured_source(
        name="Synthetic GitHub Org",
        region="Global",
        collector_type="official_api",
        url="https://github.com/synthetic-org",
    )
    rate_limit = CollectionError(CollectionErrorKind.RATE_LIMITED, "Synthetic rate limit")
    transport = StaticTransport(
        final_url="https://api.github.com/",
        content_type="application/json",
        error=rate_limit,
    )

    with pytest.raises(CollectionError) as captured:
        collect_configured_source(
            source,
            Region.GLOBAL,
            registry,
            transport,
            collected_at=NOW,
        )
    assert captured.value is rate_limit
    assert len(transport.calls) == 1


def test_huggingface_organization_url_mapping_is_exact() -> None:
    assert huggingface_organization_from_url("https://huggingface.co/openai") == "openai"
    with pytest.raises(CollectionError):
        huggingface_organization_from_url("https://huggingface.co/models/openai")


@pytest.mark.parametrize(
    ("object_kind", "object_name", "expected_url"),
    [
        ("models", "synthetic-org/model-one", "https://huggingface.co/synthetic-org/model-one"),
        (
            "datasets",
            "synthetic-org/data-one",
            "https://huggingface.co/datasets/synthetic-org/data-one",
        ),
        (
            "spaces",
            "synthetic-org/space-one",
            "https://huggingface.co/spaces/synthetic-org/space-one",
        ),
    ],
)
def test_huggingface_public_metadata_without_file_download(
    object_kind: str,
    object_name: str,
    expected_url: str,
) -> None:
    source, registry = configured_source(
        name="Synthetic Hugging Face Org",
        region="Global",
        collector_type="official_api",
        url="https://huggingface.co/synthetic-org",
        parameters={"object_kind": object_kind},
    )
    payload = [
        {
            "_id": "object-202",
            "id": object_name,
            "createdAt": "2026-08-11T03:04:05Z",
            "lastModified": "2026-08-14T03:04:05Z",
            "downloads": 12,
            "likes": 3,
            "tags": ["public", "synthetic"],
            "siblings": [{"rfilename": "large-weights.bin"}],
        }
    ]
    transport = StaticTransport(
        json.dumps(payload).encode(),
        final_url=f"https://huggingface.co/api/{object_kind}?author=synthetic-org",
        content_type="application/json",
    )

    batch = collect_configured_source(
        source,
        Region.GLOBAL,
        registry,
        transport,
        collected_at=NOW,
    )

    record = batch.records[0]
    assert record.source_object_id == "object-202"
    assert record.source_url == expected_url
    assert record.published_at == datetime(2026, 8, 11, 3, 4, 5, tzinfo=UTC)
    assert len(transport.calls) == 1
    assert transport.calls[0][0].startswith(f"https://huggingface.co/api/{object_kind}?")
    assert "large-weights.bin" not in repr(record.metadata)


def test_huggingface_malformed_or_cross_org_entries_are_item_failures() -> None:
    source, registry = configured_source(
        name="Synthetic Hugging Face Org",
        region="Global",
        collector_type="official_api",
        url="https://huggingface.co/synthetic-org",
    )
    transport = StaticTransport(
        b'[{"id":"other-org/model"},{"id":"synthetic-org/valid","_id":"2"}]',
        final_url="https://huggingface.co/api/models?author=synthetic-org",
        content_type="application/json",
    )

    batch = collect_configured_source(
        source,
        Region.GLOBAL,
        registry,
        transport,
        collected_at=NOW,
    )

    assert [record.title for record in batch.records] == ["synthetic-org/valid"]
    assert len(batch.item_errors) == 1


def test_huggingface_invalid_root_response_fails() -> None:
    source, registry = configured_source(
        name="Synthetic Hugging Face Org",
        region="Global",
        collector_type="official_api",
        url="https://huggingface.co/synthetic-org",
    )
    transport = StaticTransport(
        b'"unexpected"',
        final_url="https://huggingface.co/api/models?author=synthetic-org",
        content_type="application/json",
    )

    with pytest.raises(CollectionError, match="array"):
        collect_configured_source(
            source,
            Region.GLOBAL,
            registry,
            transport,
            collected_at=NOW,
        )
