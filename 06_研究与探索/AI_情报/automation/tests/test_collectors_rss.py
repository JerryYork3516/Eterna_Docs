"""Offline RSS and Atom Adapter tests."""

from datetime import UTC, datetime

import pytest

from collectors.base import CollectionError, CollectionErrorKind
from collectors.dispatch import collect_configured_source
from pipeline.models import CollectorType, Region
from tests.collector_helpers import StaticTransport, configured_source


NOW = datetime(2026, 8, 14, 0, 0, tzinfo=UTC)
FEED_URL = "https://feeds.example.invalid/news.xml"


def collect(body: bytes, content_type: str = "application/rss+xml"):
    source, registry = configured_source(
        name="Synthetic Feed",
        region="Global",
        collector_type="native_feed",
        url=FEED_URL,
        source_type="Media",
    )
    transport = StaticTransport(
        body,
        final_url=FEED_URL,
        content_type=content_type,
    )
    return collect_configured_source(
        source,
        Region.GLOBAL,
        registry,
        transport,
        collected_at=NOW,
    )


def test_valid_rss_preserves_guid_link_and_published_time() -> None:
    body = b"""<?xml version="1.0"?><rss version="2.0"><channel>
    <title>Synthetic News</title><link>https://feeds.example.invalid/</link>
    <description>Test</description><item><title>Release One</title>
    <link>https://feeds.example.invalid/release-one</link><guid>item-1</guid>
    <pubDate>Thu, 14 Aug 2026 01:02:03 GMT</pubDate>
    <description><![CDATA[<p>Public <b>summary</b>.</p>]]></description></item>
    </channel></rss>"""

    batch = collect(body)

    assert len(batch.records) == 1
    record = batch.records[0]
    assert record.collector_type is CollectorType.RSS_FEED
    assert record.source_object_id == "item-1"
    assert record.source_url.endswith("/release-one")
    assert record.published_at_raw == "Thu, 14 Aug 2026 01:02:03 GMT"
    assert record.published_at == datetime(2026, 8, 14, 1, 2, 3, tzinfo=UTC)
    assert record.excerpt == "Public summary ."


def test_valid_atom_preserves_entry_identity() -> None:
    body = b"""<?xml version="1.0" encoding="utf-8"?>
    <feed xmlns="http://www.w3.org/2005/Atom"><title>Synthetic Atom</title>
    <id>urn:feed</id><updated>2026-08-14T01:00:00Z</updated><entry>
    <title>Atom Release</title><id>urn:item:2</id>
    <link href="https://feeds.example.invalid/atom-release"/>
    <updated>2026-08-14T02:00:00Z</updated><summary>Atom summary.</summary>
    </entry></feed>"""

    batch = collect(body, "application/atom+xml")

    assert batch.records[0].source_object_id == "urn:item:2"
    assert batch.records[0].published_at == datetime(2026, 8, 14, 2, 0, tzinfo=UTC)


def test_missing_published_time_remains_unknown() -> None:
    body = b"""<rss version="2.0"><channel><title>Feed</title><link>https://feeds.example.invalid/</link>
    <description>Test</description><item><title>No Time</title>
    <link>https://feeds.example.invalid/no-time</link></item></channel></rss>"""

    record = collect(body).records[0]

    assert record.published_at_raw is None
    assert record.published_at is None
    assert record.collected_at == NOW


def test_malformed_feed_is_explicit_failure() -> None:
    with pytest.raises(CollectionError) as captured:
        collect(b"<html><title>Not a feed</title></html>", "application/xml")

    assert captured.value.kind is CollectionErrorKind.INVALID_CONTENT


def test_malformed_entry_does_not_drop_valid_sibling() -> None:
    body = b"""<rss version="2.0"><channel><title>Feed</title><link>https://feeds.example.invalid/</link>
    <description>Test</description><item><title>Missing Link</title></item><item>
    <title>Valid</title><link>https://feeds.example.invalid/valid</link></item></channel></rss>"""

    batch = collect(body)

    assert [record.title for record in batch.records] == ["Valid"]
    assert len(batch.item_errors) == 1
    assert batch.item_errors[0].item_index == 0
