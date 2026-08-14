"""Native RSS and Atom Adapter using the shared bounded transport."""

from __future__ import annotations

import calendar
from datetime import UTC, datetime
from html.parser import HTMLParser
from time import struct_time

import feedparser

from collectors.base import (
    CollectionBatch,
    CollectionError,
    CollectionErrorKind,
    CollectionItemError,
    MAX_EXCERPT_LENGTH,
    RawCollectorRecord,
)
from collectors.transport import Transport
from pipeline.config import SourceConfigEntry
from pipeline.models import CollectorType, Region


_FEED_CONTENT_TYPES = (
    "application/rss+xml",
    "application/atom+xml",
    "application/xml",
    "text/xml",
)


class _TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self._ignored_depth = 0

    def handle_starttag(self, tag: str, _attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in {"script", "style", "noscript", "svg", "template"}:
            self._ignored_depth += 1

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"script", "style", "noscript", "svg", "template"}:
            self._ignored_depth = max(0, self._ignored_depth - 1)

    def handle_data(self, data: str) -> None:
        if not self._ignored_depth:
            text = " ".join(data.split())
            if text:
                self.parts.append(text)


def _plain_text(value: object, *, limit: int) -> str | None:
    if type(value) is not str or not value.strip():
        return None
    parser = _TextExtractor()
    try:
        parser.feed(value)
        parser.close()
    except (ValueError, AssertionError):
        return None
    text = " ".join(parser.parts)
    if not text:
        text = " ".join(value.split())
    return text[:limit].strip() or None


def _feed_timestamp(entry: object) -> tuple[str | None, datetime | None]:
    published_raw = entry.get("published") or entry.get("updated")
    parsed: struct_time | None = entry.get("published_parsed") or entry.get("updated_parsed")
    raw = published_raw.strip()[:1_024] if type(published_raw) is str else None
    if parsed is None:
        return raw, None
    try:
        timestamp = datetime.fromtimestamp(calendar.timegm(parsed), tz=UTC)
    except (OverflowError, OSError, TypeError, ValueError):
        return raw, None
    return raw, timestamp


def _collect_rss(
    source: SourceConfigEntry,
    transport: Transport,
    *,
    collected_at: datetime,
) -> CollectionBatch:
    response = transport.get(
        source.url,
        accepted_content_types=_FEED_CONTENT_TYPES,
        accept="application/atom+xml, application/rss+xml, application/xml, text/xml",
    )
    parsed = feedparser.parse(response.body)
    if not parsed.get("version"):
        raise CollectionError(
            CollectionErrorKind.INVALID_CONTENT,
            "Response is not a recognized RSS or Atom feed",
        )
    if parsed.get("bozo") and not parsed.entries:
        raise CollectionError(
            CollectionErrorKind.INVALID_CONTENT,
            "RSS or Atom feed is malformed",
        )

    records: list[RawCollectorRecord] = []
    errors: list[CollectionItemError] = []
    if parsed.get("bozo"):
        errors.append(
            CollectionItemError(
                item_index=-1,
                kind=CollectionErrorKind.INVALID_CONTENT,
                message="Feed parser reported malformed source content",
            )
        )
    feed_title = _plain_text(parsed.feed.get("title"), limit=512)
    for index, entry in enumerate(parsed.entries):
        try:
            title = _plain_text(entry.get("title"), limit=4_096)
            link = entry.get("link")
            if title is None or type(link) is not str or not link.strip():
                raise ValueError("entry requires title and public link")
            excerpt = _plain_text(
                entry.get("summary") or entry.get("description"),
                limit=MAX_EXCERPT_LENGTH,
            )
            source_object_id = entry.get("id") or entry.get("guid")
            if source_object_id is not None and type(source_object_id) is not str:
                source_object_id = str(source_object_id)
            published_raw, published_at = _feed_timestamp(entry)
            records.append(
                RawCollectorRecord(
                    source_reference=source.registry_ref,
                    region=Region(source.region),
                    collector_type=CollectorType.RSS_FEED,
                    source_url=link.strip(),
                    source_object_id=source_object_id.strip() if source_object_id else None,
                    title=title,
                    excerpt=excerpt,
                    published_at_raw=published_raw,
                    published_at=published_at,
                    collected_at=collected_at,
                    raw_reference=link.strip(),
                    metadata={
                        "feed_url": response.final_url,
                        "feed_title": feed_title,
                        "entry_index": index,
                    },
                )
            )
        except (TypeError, ValueError) as exc:
            errors.append(
                CollectionItemError(
                    item_index=index,
                    kind=CollectionErrorKind.INVALID_CONTENT,
                    message="Feed entry is missing valid public metadata",
                )
            )

    return CollectionBatch(records=tuple(records), item_errors=tuple(errors))
