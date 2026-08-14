"""Minimal Hugging Face official public API Adapter."""

from __future__ import annotations

from datetime import datetime
import re
from urllib.parse import quote, urlsplit

from collectors.base import (
    CollectionBatch,
    CollectionError,
    CollectionErrorKind,
    CollectionItemError,
    RawCollectorRecord,
    parse_json_bytes,
    parse_source_datetime,
)
from collectors.transport import Transport
from pipeline.config import SourceConfigEntry
from pipeline.models import CollectorType, Region


_ORGANIZATION = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9._-]{0,94}[A-Za-z0-9])?")
_OBJECT_KINDS = frozenset({"models", "datasets", "spaces"})


def huggingface_organization_from_url(url: str) -> str:
    parsed = urlsplit(url)
    parts = tuple(part for part in parsed.path.split("/") if part)
    if (
        parsed.scheme != "https"
        or (parsed.hostname or "").lower() != "huggingface.co"
        or len(parts) != 1
        or parsed.query
        or parsed.fragment
        or _ORGANIZATION.fullmatch(parts[0]) is None
    ):
        raise CollectionError(
            CollectionErrorKind.SOURCE_REJECTED,
            "Configured Hugging Face URL is not an exact public organization URL",
        )
    return parts[0]


def _object_kind(source: SourceConfigEntry) -> str:
    value = source.parameters.get("object_kind", "models")
    if type(value) is not str or value not in _OBJECT_KINDS:
        raise CollectionError(
            CollectionErrorKind.SOURCE_REJECTED,
            "Hugging Face object_kind is unsupported",
        )
    return value


def _api_endpoint(organization: str, object_kind: str) -> str:
    return (
        f"https://huggingface.co/api/{object_kind}"
        f"?author={quote(organization, safe='')}&limit=30&sort=lastModified&direction=-1"
    )


def _public_object_url(object_kind: str, object_name: str) -> str:
    if object_kind == "models":
        return f"https://huggingface.co/{object_name}"
    return f"https://huggingface.co/{object_kind}/{object_name}"


def _collect_huggingface(
    source: SourceConfigEntry,
    transport: Transport,
    *,
    collected_at: datetime,
) -> CollectionBatch:
    organization = huggingface_organization_from_url(source.url)
    object_kind = _object_kind(source)
    response = transport.get(
        _api_endpoint(organization, object_kind),
        accepted_content_types=("application/json",),
        accept="application/json",
    )
    payload = parse_json_bytes(response.body)
    if type(payload) is not list:
        raise CollectionError(
            CollectionErrorKind.INVALID_CONTENT,
            "Hugging Face response must be an array",
        )

    records: list[RawCollectorRecord] = []
    errors: list[CollectionItemError] = []
    for index, item in enumerate(payload):
        try:
            if type(item) is not dict:
                raise ValueError("object entry must be an object")
            object_name = item.get("id") or item.get("modelId")
            if (
                type(object_name) is not str
                or not object_name.lower().startswith(organization.lower() + "/")
            ):
                raise ValueError("object is outside the configured organization")
            object_id = item.get("_id") or object_name
            if type(object_id) not in {str, int}:
                raise ValueError("object ID is missing")
            created_raw = item.get("createdAt")
            created_at = parse_source_datetime(created_raw)
            public_url = _public_object_url(object_kind, object_name)
            tags = item.get("tags")
            safe_tags = (
                [tag for tag in tags[:20] if type(tag) is str and len(tag) <= 128]
                if type(tags) is list
                else []
            )
            records.append(
                RawCollectorRecord(
                    source_reference=source.registry_ref,
                    region=Region(source.region),
                    collector_type=CollectorType.OFFICIAL_API,
                    source_url=public_url,
                    source_object_id=str(object_id),
                    title=object_name,
                    excerpt=None,
                    published_at_raw=created_raw if type(created_raw) is str else None,
                    published_at=created_at,
                    collected_at=collected_at,
                    raw_reference=public_url,
                    metadata={
                        "api_url": response.final_url,
                        "object_kind": object_kind,
                        "last_modified": item.get("lastModified")
                        if type(item.get("lastModified")) is str
                        else None,
                        "downloads": item.get("downloads")
                        if type(item.get("downloads")) is int
                        else None,
                        "likes": item.get("likes") if type(item.get("likes")) is int else None,
                        "tags": safe_tags,
                    },
                )
            )
        except (TypeError, ValueError):
            errors.append(
                CollectionItemError(
                    item_index=index,
                    kind=CollectionErrorKind.INVALID_CONTENT,
                    message="Hugging Face public object entry is malformed",
                )
            )

    return CollectionBatch(records=tuple(records), item_errors=tuple(errors))
