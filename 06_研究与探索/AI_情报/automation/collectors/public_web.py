"""Limited static public page monitor without browser execution or recursion."""

from __future__ import annotations

from datetime import datetime
from html.parser import HTMLParser
from urllib.parse import urldefrag, urljoin, urlsplit

from collectors.base import (
    CollectionBatch,
    CollectionError,
    CollectionErrorKind,
    MAX_EXCERPT_LENGTH,
    RawCollectorRecord,
)
from collectors.transport import Transport
from pipeline.config import SourceConfigEntry
from pipeline.models import CollectorType, Region


_HTML_CONTENT_TYPES = ("text/html", "application/xhtml+xml")
_STRONG_CHALLENGE_MARKERS = (
    "captcha",
    "verify you are human",
    "checking your browser",
    "challenge-platform",
    "cf-chl-",
    "验证码",
)
_LOGIN_TITLES = ("sign in", "log in", "login", "登录")
_MAX_LINKS = 20


class _PageParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.title_parts: list[str] = []
        self.text_parts: list[str] = []
        self.links: list[str] = []
        self.has_password_input = False
        self._ignored_depth = 0
        self._title_depth = 0

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        normalized = tag.lower()
        attributes = {key.lower(): value for key, value in attrs}
        if normalized in {"script", "style", "noscript", "svg", "template"}:
            self._ignored_depth += 1
        if normalized == "title":
            self._title_depth += 1
        if normalized == "input" and (attributes.get("type") or "").lower() == "password":
            self.has_password_input = True
        if normalized == "a" and attributes.get("href") and len(self.links) < _MAX_LINKS * 4:
            self.links.append(attributes["href"] or "")

    def handle_endtag(self, tag: str) -> None:
        normalized = tag.lower()
        if normalized in {"script", "style", "noscript", "svg", "template"}:
            self._ignored_depth = max(0, self._ignored_depth - 1)
        if normalized == "title":
            self._title_depth = max(0, self._title_depth - 1)

    def handle_data(self, data: str) -> None:
        text = " ".join(data.split())
        if not text:
            return
        if self._title_depth:
            self.title_parts.append(text)
        if not self._ignored_depth:
            self.text_parts.append(text)


def _same_host_links(base_url: str, raw_links: list[str]) -> tuple[str, ...]:
    base = urlsplit(base_url)
    links: list[str] = []
    for raw in raw_links:
        try:
            candidate, _fragment = urldefrag(urljoin(base_url, raw))
            parsed = urlsplit(candidate)
            _ = parsed.port
        except ValueError:
            continue
        if (
            parsed.scheme not in {"http", "https"}
            or not parsed.hostname
            or parsed.hostname.lower() != (base.hostname or "").lower()
            or parsed.username is not None
            or parsed.password is not None
        ):
            continue
        if candidate not in links:
            links.append(candidate)
        if len(links) == _MAX_LINKS:
            break
    return tuple(links)


def _collect_public_web(
    source: SourceConfigEntry,
    transport: Transport,
    *,
    collected_at: datetime,
) -> CollectionBatch:
    response = transport.get(
        source.url,
        accepted_content_types=_HTML_CONTENT_TYPES,
        accept="text/html, application/xhtml+xml",
    )
    try:
        html = response.body.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise CollectionError(
            CollectionErrorKind.INVALID_CONTENT,
            "Public page is not valid UTF-8 HTML",
        ) from exc

    parser = _PageParser()
    try:
        parser.feed(html)
        parser.close()
    except (AssertionError, ValueError) as exc:
        raise CollectionError(
            CollectionErrorKind.INVALID_CONTENT,
            "Public page HTML is malformed",
        ) from exc

    title = " ".join(parser.title_parts).strip()
    text = " ".join(parser.text_parts).strip()
    lowered_title = title.casefold()
    lowered_text = text.casefold()
    if parser.has_password_input or any(
        lowered_title == marker or lowered_title.startswith(marker + " ")
        for marker in _LOGIN_TITLES
    ):
        raise CollectionError(
            CollectionErrorKind.ACCESS_DENIED,
            "Login pages are outside the public web monitor boundary",
        )
    if any(marker in lowered_text for marker in _STRONG_CHALLENGE_MARKERS):
        raise CollectionError(
            CollectionErrorKind.ACCESS_DENIED,
            "Challenge or CAPTCHA pages are outside the public web monitor boundary",
        )
    if not title or not text:
        raise CollectionError(
            CollectionErrorKind.INVALID_CONTENT,
            "Public page requires a title and visible static text",
        )

    final_host = (urlsplit(response.final_url).hostname or "").lower()
    configured_host = (urlsplit(source.url).hostname or "").lower()
    if final_host != configured_host:
        raise CollectionError(
            CollectionErrorKind.ACCESS_DENIED,
            "Public page resolved outside the configured source host",
        )
    links = _same_host_links(response.final_url, parser.links)
    record = RawCollectorRecord(
        source_reference=source.registry_ref,
        region=Region(source.region),
        collector_type=CollectorType.WEB_PAGE_MONITOR,
        source_url=response.final_url,
        source_object_id=None,
        title=title[:4_096].strip(),
        excerpt=text[:MAX_EXCERPT_LENGTH].strip(),
        published_at_raw=None,
        published_at=None,
        collected_at=collected_at,
        raw_reference=response.final_url,
        metadata={"links": links, "link_count": len(links)},
    )
    return CollectionBatch(records=(record,))
