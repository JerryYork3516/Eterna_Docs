"""Strict Global and China source configuration loading."""

from __future__ import annotations

from dataclasses import dataclass
import ipaddress
import json
from pathlib import Path
from types import MappingProxyType
from typing import Mapping
from urllib.parse import urlsplit

from pipeline.errors import AutomationError
from pipeline.registry import RegistryValidationError, SourceRegistry


SUPPORTED_SCHEMA_VERSION = 1
SUPPORTED_REGIONS = frozenset({"Global", "China"})
SUPPORTED_COLLECTOR_TYPES = frozenset({"native_feed", "official_api", "public_web"})

_TOP_LEVEL_KEYS = frozenset({"schema_version", "region", "sources"})
_SOURCE_KEYS = frozenset(
    {"registry_ref", "region", "collector_type", "url", "enabled", "parameters"}
)
_SENSITIVE_KEY_FRAGMENTS = (
    "apikey",
    "token",
    "secret",
    "password",
    "cookie",
    "session",
    "authorization",
    "credential",
    "recipient",
    "email",
)


class ConfigValidationError(AutomationError):
    """Raised when machine-readable source configuration is unsafe or invalid."""


@dataclass(frozen=True, slots=True)
class SourceConfigEntry:
    """Validated runtime source configuration without domain intelligence data."""

    registry_ref: str
    region: str
    collector_type: str
    url: str
    enabled: bool
    parameters: Mapping[str, object]


@dataclass(frozen=True, slots=True)
class SourceConfig:
    """Validated configuration for one isolated Region."""

    schema_version: int
    region: str
    sources: tuple[SourceConfigEntry, ...]


def _normalized_key(key: str) -> str:
    return "".join(character.lower() for character in key if character.isalnum())


def _reject_sensitive_keys(value: object, path: str = "config") -> None:
    if isinstance(value, dict):
        for key, nested_value in value.items():
            if not isinstance(key, str):
                raise ConfigValidationError(f"Configuration key at {path} must be text")
            normalized = _normalized_key(key)
            if any(fragment in normalized for fragment in _SENSITIVE_KEY_FRAGMENTS):
                raise ConfigValidationError(
                    f"Sensitive configuration field is forbidden at {path}.{key}"
                )
            _reject_sensitive_keys(nested_value, f"{path}.{key}")
    elif isinstance(value, list):
        for index, nested_value in enumerate(value):
            _reject_sensitive_keys(nested_value, f"{path}[{index}]")


def _require_exact_keys(
    value: dict[str, object], expected: frozenset[str], path: str
) -> None:
    actual = frozenset(value)
    if actual != expected:
        unknown = sorted(actual - expected)
        missing = sorted(expected - actual)
        raise ConfigValidationError(
            f"{path} keys do not match schema; unknown={unknown}, missing={missing}"
        )


def _validate_public_url(url: object) -> str:
    if not isinstance(url, str) or not url or any(char.isspace() for char in url):
        raise ConfigValidationError("Source URL must be a non-empty URL without whitespace")

    try:
        parsed = urlsplit(url)
        _ = parsed.port
    except ValueError as exc:
        raise ConfigValidationError(f"Source URL is malformed: {url!r}") from exc

    if parsed.scheme not in {"http", "https"}:
        raise ConfigValidationError("Source URL scheme must be http or https")
    if not parsed.netloc or parsed.hostname is None:
        raise ConfigValidationError("Source URL must include a hostname")
    if parsed.username is not None or parsed.password is not None:
        raise ConfigValidationError("Source URL must not contain userinfo credentials")

    hostname = parsed.hostname.lower()
    if hostname == "localhost" or hostname.endswith(".local"):
        raise ConfigValidationError("Source URL must not use a local hostname")
    try:
        address = ipaddress.ip_address(hostname)
    except ValueError:
        pass
    else:
        if not address.is_global:
            raise ConfigValidationError("Source URL must not use a non-public IP address")

    return url


def validate_source_config(
    payload: object,
    expected_region: str,
    registry: SourceRegistry,
) -> SourceConfig:
    """Validate one JSON-compatible source configuration object."""

    if (
        not isinstance(expected_region, str)
        or expected_region not in SUPPORTED_REGIONS
    ):
        raise ConfigValidationError(f"Unsupported expected Region: {expected_region!r}")
    if not isinstance(payload, dict):
        raise ConfigValidationError("Source config root must be an object")

    _reject_sensitive_keys(payload)
    _require_exact_keys(payload, _TOP_LEVEL_KEYS, "config")

    schema_version = payload["schema_version"]
    region = payload["region"]
    raw_sources = payload["sources"]

    if type(schema_version) is not int or schema_version != SUPPORTED_SCHEMA_VERSION:
        raise ConfigValidationError(
            f"Unsupported schema_version: {schema_version!r}"
        )
    if not isinstance(region, str) or region not in SUPPORTED_REGIONS:
        raise ConfigValidationError(f"Unsupported config Region: {region!r}")
    if region != expected_region:
        raise ConfigValidationError(
            f"Config Region {region!r} does not match expected Region {expected_region!r}"
        )
    if not isinstance(raw_sources, list) or not raw_sources:
        raise ConfigValidationError("sources must be a non-empty array")

    sources: list[SourceConfigEntry] = []
    identities: set[tuple[str, str]] = set()
    for index, raw_source in enumerate(raw_sources):
        item_path = f"config.sources[{index}]"
        if not isinstance(raw_source, dict):
            raise ConfigValidationError(f"{item_path} must be an object")
        _require_exact_keys(raw_source, _SOURCE_KEYS, item_path)

        registry_ref = raw_source["registry_ref"]
        source_region = raw_source["region"]
        collector_type = raw_source["collector_type"]
        enabled = raw_source["enabled"]
        parameters = raw_source["parameters"]

        if not isinstance(registry_ref, str) or not registry_ref:
            raise ConfigValidationError(f"{item_path}.registry_ref must be non-empty")
        if (
            not isinstance(source_region, str)
            or source_region not in SUPPORTED_REGIONS
        ):
            raise ConfigValidationError(
                f"{item_path}.region is unsupported: {source_region!r}"
            )
        if source_region != region:
            raise ConfigValidationError(
                f"{item_path}.region does not match config Region {region!r}"
            )
        if (
            not isinstance(collector_type, str)
            or collector_type not in SUPPORTED_COLLECTOR_TYPES
        ):
            raise ConfigValidationError(
                f"{item_path}.collector_type is unsupported: {collector_type!r}"
            )
        if type(enabled) is not bool:
            raise ConfigValidationError(f"{item_path}.enabled must be boolean")
        if not isinstance(parameters, dict):
            raise ConfigValidationError(f"{item_path}.parameters must be an object")

        url = _validate_public_url(raw_source["url"])
        try:
            registry_entry = registry.get(registry_ref)
        except RegistryValidationError as exc:
            raise ConfigValidationError(
                f"{item_path}.registry_ref does not exist: {registry_ref!r}"
            ) from exc
        if registry_entry.region != source_region:
            raise ConfigValidationError(
                f"{registry_ref!r} is {registry_entry.region}, not {source_region}"
            )
        if url not in registry_entry.urls:
            raise ConfigValidationError(
                f"URL is not registered for {registry_ref!r}: {url!r}"
            )

        identity = (registry_ref, url)
        if identity in identities:
            raise ConfigValidationError(f"Duplicate configured source: {identity!r}")
        identities.add(identity)

        sources.append(
            SourceConfigEntry(
                registry_ref=registry_ref,
                region=source_region,
                collector_type=collector_type,
                url=url,
                enabled=enabled,
                parameters=MappingProxyType(dict(parameters)),
            )
        )

    return SourceConfig(
        schema_version=schema_version,
        region=region,
        sources=tuple(sources),
    )


def load_source_config(
    path: Path,
    expected_region: str,
    registry: SourceRegistry,
) -> SourceConfig:
    """Load and strictly validate one UTF-8 JSON source configuration file."""

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise ConfigValidationError(f"Cannot load source config: {path}") from exc

    return validate_source_config(payload, expected_region, registry)
