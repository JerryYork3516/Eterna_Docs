"""Bounded public HTTP transport shared by all MVP Collectors."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol
from urllib.parse import urljoin, urlsplit

import httpx

from collectors.base import CollectionError, CollectionErrorKind


DEFAULT_USER_AGENT = "Eterna-AI-Intelligence/0.1 (+public-research-collector)"
_REDIRECT_STATUSES = frozenset({301, 302, 303, 307, 308})


@dataclass(frozen=True, slots=True)
class TransportSettings:
    connect_timeout: float = 5.0
    read_timeout: float = 10.0
    write_timeout: float = 10.0
    pool_timeout: float = 5.0
    max_response_bytes: int = 1_000_000
    max_redirects: int = 3
    max_requests: int = 8
    user_agent: str = DEFAULT_USER_AGENT

    def __post_init__(self) -> None:
        for field_name in (
            "connect_timeout",
            "read_timeout",
            "write_timeout",
            "pool_timeout",
        ):
            value = getattr(self, field_name)
            if type(value) not in {int, float} or value <= 0:
                raise ValueError(f"{field_name} must be positive")
        if type(self.max_response_bytes) is not int or self.max_response_bytes < 1:
            raise ValueError("max_response_bytes must be positive")
        if type(self.max_redirects) is not int or self.max_redirects < 0:
            raise ValueError("max_redirects must be non-negative")
        if type(self.max_requests) is not int or self.max_requests < 1:
            raise ValueError("max_requests must be positive")
        if type(self.user_agent) is not str or not self.user_agent.strip():
            raise ValueError("user_agent must be explicit")


@dataclass(frozen=True, slots=True)
class TransportResponse:
    body: bytes
    final_url: str
    status_code: int
    content_type: str


class Transport(Protocol):
    def get(
        self,
        url: str,
        *,
        accepted_content_types: tuple[str, ...],
        accept: str,
    ) -> TransportResponse: ...


def _base_content_type(value: str) -> str:
    return value.split(";", 1)[0].strip().lower()


def _content_type_matches(actual: str, accepted: tuple[str, ...]) -> bool:
    if actual in accepted:
        return True
    if actual.endswith("+json") and "application/json" in accepted:
        return True
    if actual.endswith("+xml") and "application/xml" in accepted:
        return True
    return False


def _safe_redirect(current_url: str, location: str) -> str:
    try:
        target = urljoin(current_url, location)
        current = urlsplit(current_url)
        parsed = urlsplit(target)
        _ = parsed.port
    except ValueError as exc:
        raise CollectionError(
            CollectionErrorKind.UNSUPPORTED_CONTENT,
            "Redirect target is malformed",
        ) from exc
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise CollectionError(
            CollectionErrorKind.UNSUPPORTED_CONTENT,
            "Redirect target is not HTTP(S)",
        )
    if parsed.username is not None or parsed.password is not None:
        raise CollectionError(
            CollectionErrorKind.ACCESS_DENIED,
            "Redirect target contains forbidden credentials",
        )
    if parsed.hostname.lower() != (current.hostname or "").lower():
        raise CollectionError(
            CollectionErrorKind.ACCESS_DENIED,
            "Cross-host redirects require separate source approval",
        )
    if current.scheme == "https" and parsed.scheme != "https":
        raise CollectionError(
            CollectionErrorKind.ACCESS_DENIED,
            "HTTPS downgrade redirects are forbidden",
        )
    return target


class HttpTransport:
    """A no-retry, no-auth, no-cookie transport with explicit resource limits."""

    def __init__(
        self,
        settings: TransportSettings | None = None,
        *,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self.settings = settings or TransportSettings()
        timeout = httpx.Timeout(
            connect=self.settings.connect_timeout,
            read=self.settings.read_timeout,
            write=self.settings.write_timeout,
            pool=self.settings.pool_timeout,
        )
        self._client = httpx.Client(
            timeout=timeout,
            follow_redirects=False,
            transport=transport,
            trust_env=False,
            headers={"User-Agent": self.settings.user_agent},
        )
        self._request_count = 0

    @property
    def request_count(self) -> int:
        return self._request_count

    def close(self) -> None:
        self._client.cookies.clear()
        self._client.close()

    def __enter__(self) -> "HttpTransport":
        return self

    def __exit__(self, *_args: object) -> None:
        self.close()

    def get(
        self,
        url: str,
        *,
        accepted_content_types: tuple[str, ...],
        accept: str,
    ) -> TransportResponse:
        if not accepted_content_types:
            raise ValueError("accepted_content_types must not be empty")
        current_url = url
        redirects = 0

        while True:
            if self._request_count >= self.settings.max_requests:
                raise CollectionError(
                    CollectionErrorKind.HTTP_ERROR,
                    "Transport request budget exhausted",
                )
            self._request_count += 1
            self._client.cookies.clear()
            try:
                with self._client.stream(
                    "GET",
                    current_url,
                    headers={"Accept": accept},
                ) as response:
                    self._client.cookies.clear()
                    if response.status_code in _REDIRECT_STATUSES:
                        location = response.headers.get("location")
                        if not location:
                            raise CollectionError(
                                CollectionErrorKind.HTTP_ERROR,
                                "Redirect response has no Location",
                                status_code=response.status_code,
                            )
                        if redirects >= self.settings.max_redirects:
                            raise CollectionError(
                                CollectionErrorKind.REDIRECT_LIMIT,
                                "Redirect limit exceeded",
                                status_code=response.status_code,
                            )
                        current_url = _safe_redirect(current_url, location)
                        redirects += 1
                        continue

                    self._raise_for_status(response.status_code)
                    content_type = _base_content_type(
                        response.headers.get("content-type", "")
                    )
                    accepted = tuple(item.lower() for item in accepted_content_types)
                    if not content_type or not _content_type_matches(content_type, accepted):
                        raise CollectionError(
                            CollectionErrorKind.UNSUPPORTED_CONTENT,
                            "Response Content-Type is unsupported",
                            status_code=response.status_code,
                        )
                    content_length = response.headers.get("content-length")
                    if content_length is not None:
                        try:
                            declared_length = int(content_length)
                        except ValueError:
                            declared_length = -1
                        if declared_length > self.settings.max_response_bytes:
                            raise CollectionError(
                                CollectionErrorKind.RESPONSE_TOO_LARGE,
                                "Response exceeds the configured size limit",
                                status_code=response.status_code,
                            )

                    body = bytearray()
                    for chunk in response.iter_bytes():
                        body.extend(chunk)
                        if len(body) > self.settings.max_response_bytes:
                            raise CollectionError(
                                CollectionErrorKind.RESPONSE_TOO_LARGE,
                                "Response exceeds the configured size limit",
                                status_code=response.status_code,
                            )
                    return TransportResponse(
                        body=bytes(body),
                        final_url=str(response.url),
                        status_code=response.status_code,
                        content_type=content_type,
                    )
            except CollectionError:
                raise
            except httpx.TimeoutException as exc:
                raise CollectionError(
                    CollectionErrorKind.TIMEOUT,
                    "Public source request timed out",
                ) from exc
            except httpx.RequestError as exc:
                raise CollectionError(
                    CollectionErrorKind.NETWORK_ERROR,
                    "Public source request failed",
                ) from exc
            finally:
                self._client.cookies.clear()

    @staticmethod
    def _raise_for_status(status_code: int) -> None:
        if status_code in {401, 403}:
            raise CollectionError(
                CollectionErrorKind.ACCESS_DENIED,
                "Public source denied access",
                status_code=status_code,
            )
        if status_code == 429:
            raise CollectionError(
                CollectionErrorKind.RATE_LIMITED,
                "Public source rate limit reached",
                status_code=status_code,
            )
        if status_code >= 400:
            raise CollectionError(
                CollectionErrorKind.HTTP_ERROR,
                "Public source returned an HTTP error",
                status_code=status_code,
            )
