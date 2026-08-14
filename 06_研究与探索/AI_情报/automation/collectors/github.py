"""Minimal GitHub official public REST API Adapter."""

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


_ORG_NAME = re.compile(r"[A-Za-z0-9](?:[A-Za-z0-9-]{0,37}[A-Za-z0-9])?")


def github_organization_from_url(url: str) -> str:
    parsed = urlsplit(url)
    parts = tuple(part for part in parsed.path.split("/") if part)
    if (
        parsed.scheme != "https"
        or (parsed.hostname or "").lower() != "github.com"
        or len(parts) != 1
        or parsed.query
        or parsed.fragment
        or _ORG_NAME.fullmatch(parts[0]) is None
    ):
        raise CollectionError(
            CollectionErrorKind.SOURCE_REJECTED,
            "Configured GitHub URL is not an exact public organization URL",
        )
    return parts[0]


def _repository_endpoint(organization: str) -> str:
    encoded = quote(organization, safe="")
    return (
        f"https://api.github.com/orgs/{encoded}/repos"
        "?type=public&sort=pushed&direction=desc&per_page=30"
    )


def _collect_github(
    source: SourceConfigEntry,
    transport: Transport,
    *,
    collected_at: datetime,
) -> CollectionBatch:
    organization = github_organization_from_url(source.url)
    response = transport.get(
        _repository_endpoint(organization),
        accepted_content_types=("application/json",),
        accept="application/vnd.github+json",
    )
    payload = parse_json_bytes(response.body)
    if type(payload) is not list:
        raise CollectionError(
            CollectionErrorKind.INVALID_CONTENT,
            "GitHub repositories response must be an array",
        )

    records: list[RawCollectorRecord] = []
    errors: list[CollectionItemError] = []
    for index, item in enumerate(payload):
        try:
            if type(item) is not dict:
                raise ValueError("repository entry must be an object")
            object_id = item.get("id")
            full_name = item.get("full_name")
            html_url = item.get("html_url")
            owner = item.get("owner")
            if (
                type(object_id) not in {int, str}
                or type(full_name) is not str
                or type(html_url) is not str
                or type(owner) is not dict
                or type(owner.get("login")) is not str
                or owner["login"].lower() != organization.lower()
                or not full_name.lower().startswith(organization.lower() + "/")
            ):
                raise ValueError("repository identity is inconsistent")
            created_raw = item.get("created_at")
            created_at = parse_source_datetime(created_raw)
            description = item.get("description")
            if description is not None and type(description) is not str:
                description = None
            records.append(
                RawCollectorRecord(
                    source_reference=source.registry_ref,
                    region=Region(source.region),
                    collector_type=CollectorType.OFFICIAL_API,
                    source_url=html_url,
                    source_object_id=str(object_id),
                    title=full_name,
                    excerpt=description[:16_384].strip() if description else None,
                    published_at_raw=created_raw if type(created_raw) is str else None,
                    published_at=created_at,
                    collected_at=collected_at,
                    raw_reference=html_url,
                    metadata={
                        "api_url": response.final_url,
                        "created_at": created_raw if type(created_raw) is str else None,
                        "updated_at": item.get("updated_at")
                        if type(item.get("updated_at")) is str
                        else None,
                        "pushed_at": item.get("pushed_at")
                        if type(item.get("pushed_at")) is str
                        else None,
                        "archived": item.get("archived")
                        if type(item.get("archived")) is bool
                        else None,
                    },
                )
            )
        except (TypeError, ValueError):
            errors.append(
                CollectionItemError(
                    item_index=index,
                    kind=CollectionErrorKind.INVALID_CONTENT,
                    message="GitHub repository entry is malformed",
                )
            )

    return CollectionBatch(records=tuple(records), item_errors=tuple(errors))
