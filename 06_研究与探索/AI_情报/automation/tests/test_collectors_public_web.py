"""Offline tests for the limited static public page monitor."""

from datetime import UTC, datetime

import pytest

from collectors.base import CollectionError, CollectionErrorKind
from collectors.dispatch import collect_configured_source
from pipeline.models import CollectorType, Region
from tests.collector_helpers import StaticTransport, configured_source


NOW = datetime(2026, 8, 14, 0, 0, tzinfo=UTC)
PAGE_URL = "https://official.example.invalid/news/"


def source_and_registry():
    return configured_source(
        name="Synthetic Official Page",
        region="Global",
        collector_type="public_web",
        url=PAGE_URL,
    )


def collect(html: str, *, error: Exception | None = None):
    source, registry = source_and_registry()
    transport = StaticTransport(
        html.encode(),
        final_url=PAGE_URL,
        content_type="text/html",
        error=error,
    )
    batch = collect_configured_source(
        source,
        Region.GLOBAL,
        registry,
        transport,
        collected_at=NOW,
    )
    return batch, transport


def test_static_html_extracts_title_text_and_only_same_host_links() -> None:
    html = """<!doctype html><html><head><title>Official Updates</title>
    <style>hidden style</style><script>forbidden()</script></head><body>
    <main><h1>Model release</h1><p>Public static announcement.</p>
    <a href="/news/item-one#details">Item one</a>
    <a href="https://outside.invalid/item">Outside</a>
    <a href="javascript:forbidden()">Script</a></main></body></html>"""

    batch, transport = collect(html)

    record = batch.records[0]
    assert record.collector_type is CollectorType.WEB_PAGE_MONITOR
    assert record.title == "Official Updates"
    assert "Model release" in (record.excerpt or "")
    assert "forbidden()" not in (record.excerpt or "")
    assert record.published_at is None
    assert record.metadata["links"] == ("https://official.example.invalid/news/item-one",)
    assert len(transport.calls) == 1


def test_public_web_does_not_spider_extracted_links() -> None:
    batch, transport = collect(
        "<html><head><title>Updates</title></head><body>News "
        '<a href="/one">One</a><a href="/two">Two</a></body></html>'
    )

    assert len(batch.records) == 1
    assert len(batch.records[0].metadata["links"]) == 2
    assert len(transport.calls) == 1


@pytest.mark.parametrize(
    "html",
    [
        "<html><head><title>Login</title></head><body><input type=password></body></html>",
        "<html><head><title>Checking</title></head><body>Verify you are human</body></html>",
        "<html><head><title>Access</title></head><body>CAPTCHA challenge</body></html>",
    ],
)
def test_login_and_captcha_like_pages_are_rejected(html: str) -> None:
    with pytest.raises(CollectionError) as captured:
        collect(html)
    assert captured.value.kind is CollectionErrorKind.ACCESS_DENIED


def test_oversized_html_failure_is_propagated() -> None:
    too_large = CollectionError(
        CollectionErrorKind.RESPONSE_TOO_LARGE,
        "Synthetic size limit",
    )
    with pytest.raises(CollectionError) as captured:
        collect("", error=too_large)
    assert captured.value is too_large


def test_page_without_title_is_invalid_content() -> None:
    with pytest.raises(CollectionError) as captured:
        collect("<html><body>Visible content only.</body></html>")
    assert captured.value.kind is CollectionErrorKind.INVALID_CONTENT
