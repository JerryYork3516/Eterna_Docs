"""Unit and offline tests for Registry-backed source configuration."""

from __future__ import annotations

from copy import deepcopy
import hashlib
import json
from pathlib import Path

import pytest

from pipeline.config import (
    ConfigValidationError,
    load_source_config,
    validate_source_config,
)
from pipeline.registry import load_source_registry


AUTOMATION_ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = AUTOMATION_ROOT.parent / "Stage1" / "Source_Registry_v0.1.md"
GLOBAL_CONFIG_PATH = AUTOMATION_ROOT / "config" / "global_sources.json"
CHINA_CONFIG_PATH = AUTOMATION_ROOT / "config" / "china_sources.json"


@pytest.fixture(scope="module")
def registry():
    return load_source_registry(REGISTRY_PATH)


def _payload(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def test_current_global_config_resolves_to_registry(registry) -> None:
    config = load_source_config(GLOBAL_CONFIG_PATH, "Global", registry)

    assert config.region == "Global"
    assert len(config.sources) == 3
    assert all(
        registry.get(source.registry_ref).region == "Global"
        for source in config.sources
    )


def test_current_china_config_resolves_to_registry(registry) -> None:
    config = load_source_config(CHINA_CONFIG_PATH, "China", registry)

    assert config.region == "China"
    assert len(config.sources) == 3
    assert all(
        registry.get(source.registry_ref).region == "China"
        for source in config.sources
    )


def test_registry_is_not_modified_by_validation(registry) -> None:
    before = hashlib.sha256(REGISTRY_PATH.read_bytes()).hexdigest()

    load_source_config(GLOBAL_CONFIG_PATH, "Global", registry)
    load_source_config(CHINA_CONFIG_PATH, "China", registry)

    assert hashlib.sha256(REGISTRY_PATH.read_bytes()).hexdigest() == before


def test_invalid_json_fails(tmp_path: Path, registry) -> None:
    path = tmp_path / "invalid.json"
    path.write_text("{", encoding="utf-8")

    with pytest.raises(ConfigValidationError):
        load_source_config(path, "Global", registry)


def test_wrong_schema_version_fails(registry) -> None:
    payload = _payload(GLOBAL_CONFIG_PATH)
    payload["schema_version"] = 2

    with pytest.raises(ConfigValidationError):
        validate_source_config(payload, "Global", registry)


def test_config_region_mismatch_fails(registry) -> None:
    payload = _payload(GLOBAL_CONFIG_PATH)

    with pytest.raises(ConfigValidationError):
        validate_source_config(payload, "China", registry)


def test_unsupported_region_fails(registry) -> None:
    payload = _payload(GLOBAL_CONFIG_PATH)
    payload["region"] = "Combined"

    with pytest.raises(ConfigValidationError):
        validate_source_config(payload, "Global", registry)


def test_unknown_collector_type_fails(registry) -> None:
    payload = _payload(GLOBAL_CONFIG_PATH)
    payload["sources"][0]["collector_type"] = "search"

    with pytest.raises(ConfigValidationError):
        validate_source_config(payload, "Global", registry)


@pytest.mark.parametrize(
    "url", ["file:///tmp/source", "ftp://example.com/feed", "data:text/plain,x"]
)
def test_invalid_url_scheme_fails(url: str, registry) -> None:
    payload = _payload(GLOBAL_CONFIG_PATH)
    payload["sources"][0]["url"] = url

    with pytest.raises(ConfigValidationError):
        validate_source_config(payload, "Global", registry)


def test_url_userinfo_fails(registry) -> None:
    payload = _payload(GLOBAL_CONFIG_PATH)
    payload["sources"][0]["url"] = "https://" + "user" + "@" + "openai.com/news/"

    with pytest.raises(ConfigValidationError):
        validate_source_config(payload, "Global", registry)


def test_secret_like_parameter_fails_recursively(registry) -> None:
    payload = _payload(GLOBAL_CONFIG_PATH)
    payload["sources"][0]["parameters"] = {
        "headers": {"Authorization": "forbidden"}
    }

    with pytest.raises(ConfigValidationError):
        validate_source_config(payload, "Global", registry)


def test_unknown_top_level_field_fails(registry) -> None:
    payload = _payload(GLOBAL_CONFIG_PATH)
    payload["future"] = False

    with pytest.raises(ConfigValidationError):
        validate_source_config(payload, "Global", registry)


def test_registry_reference_missing_fails(registry) -> None:
    payload = _payload(GLOBAL_CONFIG_PATH)
    payload["sources"][0]["registry_ref"] = "Not Registered"

    with pytest.raises(ConfigValidationError):
        validate_source_config(payload, "Global", registry)


def test_registry_url_mismatch_fails(registry) -> None:
    payload = _payload(GLOBAL_CONFIG_PATH)
    payload["sources"][0]["url"] = "https://example.com/not-registered"

    with pytest.raises(ConfigValidationError):
        validate_source_config(payload, "Global", registry)


def test_china_source_in_global_config_fails(registry) -> None:
    payload = _payload(GLOBAL_CONFIG_PATH)
    china_source = deepcopy(_payload(CHINA_CONFIG_PATH)["sources"][0])
    china_source["region"] = "Global"
    payload["sources"][0] = china_source

    with pytest.raises(ConfigValidationError):
        validate_source_config(payload, "Global", registry)


def test_global_source_in_china_config_fails(registry) -> None:
    payload = _payload(CHINA_CONFIG_PATH)
    global_source = deepcopy(_payload(GLOBAL_CONFIG_PATH)["sources"][0])
    global_source["region"] = "China"
    payload["sources"][0] = global_source

    with pytest.raises(ConfigValidationError):
        validate_source_config(payload, "China", registry)
