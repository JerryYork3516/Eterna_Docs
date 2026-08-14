"""Config and Registry gated dispatch for one enabled MVP source."""

from __future__ import annotations

from datetime import datetime
from urllib.parse import urlsplit

from collectors.base import CollectionBatch, CollectionError, CollectionErrorKind
from collectors.github import _collect_github
from collectors.huggingface import _collect_huggingface
from collectors.public_web import _collect_public_web
from collectors.rss import _collect_rss
from collectors.transport import Transport
from pipeline.config import (
    ConfigValidationError,
    SourceConfigEntry,
    validate_source_config,
)
from pipeline.models import Region
from pipeline.registry import SourceRegistry


def _validated_enabled_source(
    source: SourceConfigEntry,
    expected_region: Region,
    registry: SourceRegistry,
) -> SourceConfigEntry:
    if type(source) is not SourceConfigEntry or type(expected_region) is not Region:
        raise CollectionError(
            CollectionErrorKind.SOURCE_REJECTED,
            "Collector requires a typed source and Region",
        )
    payload = {
        "schema_version": 1,
        "region": expected_region.value,
        "sources": [
            {
                "registry_ref": source.registry_ref,
                "region": source.region,
                "collector_type": source.collector_type,
                "url": source.url,
                "enabled": source.enabled,
                "parameters": dict(source.parameters),
            }
        ],
    }
    try:
        validated = validate_source_config(payload, expected_region.value, registry).sources[0]
    except ConfigValidationError as exc:
        raise CollectionError(
            CollectionErrorKind.SOURCE_REJECTED,
            "Source did not pass Config and Registry validation",
        ) from exc
    if not validated.enabled:
        raise CollectionError(
            CollectionErrorKind.SOURCE_DISABLED,
            "Disabled sources are not collected",
        )
    return validated


def collect_configured_source(
    source: SourceConfigEntry,
    expected_region: Region,
    registry: SourceRegistry,
    transport: Transport,
    *,
    collected_at: datetime,
) -> CollectionBatch:
    """Collect exactly one pre-validated source without Normalization."""

    if type(collected_at) is not datetime:
        raise CollectionError(
            CollectionErrorKind.SOURCE_REJECTED,
            "collected_at must be a timezone-aware datetime",
        )
    try:
        offset = collected_at.utcoffset()
    except (OverflowError, ValueError) as exc:
        raise CollectionError(
            CollectionErrorKind.SOURCE_REJECTED,
            "collected_at has an invalid timezone",
        ) from exc
    if collected_at.tzinfo is None or offset is None:
        raise CollectionError(
            CollectionErrorKind.SOURCE_REJECTED,
            "collected_at must be timezone-aware",
        )
    validated = _validated_enabled_source(source, expected_region, registry)
    registry_entry = registry.get(validated.registry_ref)
    if validated.collector_type in {"official_api", "public_web"} and (
        registry_entry.source_type != "Official"
    ):
        raise CollectionError(
            CollectionErrorKind.SOURCE_REJECTED,
            "Official API and public web MVP sources must be Official Registry entries",
        )

    if validated.collector_type == "native_feed":
        return _collect_rss(validated, transport, collected_at=collected_at)
    if validated.collector_type == "public_web":
        return _collect_public_web(validated, transport, collected_at=collected_at)
    if validated.collector_type == "official_api":
        hostname = (urlsplit(validated.url).hostname or "").lower()
        if hostname == "github.com":
            return _collect_github(validated, transport, collected_at=collected_at)
        if hostname == "huggingface.co":
            return _collect_huggingface(validated, transport, collected_at=collected_at)
    raise CollectionError(
        CollectionErrorKind.UNSUPPORTED_CONTENT,
        "Configured Collector source has no approved MVP Adapter",
    )
