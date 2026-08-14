"""Offline tests for the bounded, no-auth shared HTTP Transport."""

import httpx
import pytest

from collectors.base import CollectionError, CollectionErrorKind
from collectors.transport import HttpTransport, TransportSettings


def transport_for(handler, **settings: object) -> HttpTransport:
    return HttpTransport(
        TransportSettings(**settings),
        transport=httpx.MockTransport(handler),
    )


def test_transport_sets_explicit_user_agent_and_reads_supported_content() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.headers["user-agent"].startswith("Eterna-AI-Intelligence/")
        assert "authorization" not in request.headers
        return httpx.Response(200, headers={"content-type": "application/json"}, json={})

    with transport_for(handler) as transport:
        response = transport.get(
            "https://api.example.invalid/data",
            accepted_content_types=("application/json",),
            accept="application/json",
        )

    assert response.body == b"{}"
    assert transport.request_count == 1


def test_timeout_is_classified_without_retry() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        raise httpx.ReadTimeout("synthetic timeout", request=request)

    with transport_for(handler) as transport:
        with pytest.raises(CollectionError) as captured:
            transport.get(
                "https://api.example.invalid/data",
                accepted_content_types=("application/json",),
                accept="application/json",
            )

    assert captured.value.kind is CollectionErrorKind.TIMEOUT
    assert calls == 1


def test_network_error_is_classified_without_retry() -> None:
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        raise httpx.ConnectError("synthetic network failure", request=request)

    with transport_for(handler) as transport:
        with pytest.raises(CollectionError) as captured:
            transport.get(
                "https://api.example.invalid/data",
                accepted_content_types=("application/json",),
                accept="application/json",
            )

    assert captured.value.kind is CollectionErrorKind.NETWORK_ERROR
    assert calls == 1


@pytest.mark.parametrize(
    ("status_code", "kind"),
    [
        (403, CollectionErrorKind.ACCESS_DENIED),
        (429, CollectionErrorKind.RATE_LIMITED),
        (500, CollectionErrorKind.HTTP_ERROR),
    ],
)
def test_http_status_is_classified_without_bypass(
    status_code: int,
    kind: CollectionErrorKind,
) -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(status_code, headers={"content-type": "application/json"})

    with transport_for(handler) as transport:
        with pytest.raises(CollectionError) as captured:
            transport.get(
                "https://api.example.invalid/data",
                accepted_content_types=("application/json",),
                accept="application/json",
            )

    assert captured.value.kind is kind
    assert captured.value.status_code == status_code
    assert transport.request_count == 1


def test_declared_and_streamed_oversized_responses_fail() -> None:
    def declared(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers={"content-type": "text/html", "content-length": "11"},
            content=b"small",
        )

    with transport_for(declared, max_response_bytes=10) as transport:
        with pytest.raises(CollectionError) as captured:
            transport.get(
                "https://example.invalid/",
                accepted_content_types=("text/html",),
                accept="text/html",
            )
    assert captured.value.kind is CollectionErrorKind.RESPONSE_TOO_LARGE

    def streamed(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers={"content-type": "text/html"},
            content=b"01234567890",
        )

    with transport_for(streamed, max_response_bytes=10) as transport:
        with pytest.raises(CollectionError) as captured:
            transport.get(
                "https://example.invalid/",
                accepted_content_types=("text/html",),
                accept="text/html",
            )
    assert captured.value.kind is CollectionErrorKind.RESPONSE_TOO_LARGE


def test_malformed_content_type_is_rejected() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            headers={"content-type": "application/octet-stream"},
            content=b"{}",
        )

    with transport_for(handler) as transport:
        with pytest.raises(CollectionError) as captured:
            transport.get(
                "https://api.example.invalid/data",
                accepted_content_types=("application/json",),
                accept="application/json",
            )
    assert captured.value.kind is CollectionErrorKind.UNSUPPORTED_CONTENT


def test_redirect_limit_and_cross_host_boundary_fail_closed() -> None:
    def loop(request: httpx.Request) -> httpx.Response:
        return httpx.Response(302, headers={"location": "/next"}, request=request)

    with transport_for(loop, max_redirects=1) as transport:
        with pytest.raises(CollectionError) as captured:
            transport.get(
                "https://example.invalid/start",
                accepted_content_types=("text/html",),
                accept="text/html",
            )
    assert captured.value.kind is CollectionErrorKind.REDIRECT_LIMIT
    assert transport.request_count == 2

    def cross_host(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            302,
            headers={"location": "https://other.invalid/next"},
            request=request,
        )

    with transport_for(cross_host) as transport:
        with pytest.raises(CollectionError) as captured:
            transport.get(
                "https://example.invalid/start",
                accepted_content_types=("text/html",),
                accept="text/html",
            )
    assert captured.value.kind is CollectionErrorKind.ACCESS_DENIED


def test_redirect_does_not_replay_set_cookie() -> None:
    seen_cookie_headers: list[str | None] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_cookie_headers.append(request.headers.get("cookie"))
        if request.url.path == "/start":
            return httpx.Response(
                302,
                headers={"location": "/final", "set-cookie": "session=forbidden"},
                request=request,
            )
        return httpx.Response(
            200,
            headers={"content-type": "text/html"},
            content=b"<html></html>",
            request=request,
        )

    with transport_for(handler) as transport:
        transport.get(
            "https://example.invalid/start",
            accepted_content_types=("text/html",),
            accept="text/html",
        )

    assert seen_cookie_headers == [None, None]


def test_transport_request_budget_is_finite() -> None:
    def handler(_request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, headers={"content-type": "application/json"}, json={})

    with transport_for(handler, max_requests=1) as transport:
        transport.get(
            "https://api.example.invalid/one",
            accepted_content_types=("application/json",),
            accept="application/json",
        )
        with pytest.raises(CollectionError, match="budget") as captured:
            transport.get(
                "https://api.example.invalid/two",
                accepted_content_types=("application/json",),
                accept="application/json",
            )
    assert captured.value.kind is CollectionErrorKind.HTTP_ERROR
