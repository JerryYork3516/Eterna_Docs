"""Unit tests for default-deny, Region-specific write paths."""

from pathlib import Path

import pytest

from pipeline.path_policy import (
    PathPolicyError,
    validate_write_path,
    validate_write_paths,
)


GLOBAL_REPORT = (
    "06_研究与探索/AI_情报/reports/global/2026/08/"
    "2026-08-12_Global_AI_Intelligence.md"
)
CHINA_REPORT = (
    "06_研究与探索/AI_情报/reports/china/2026/08/"
    "2026-08-12_China_AI_Intelligence.md"
)
GLOBAL_STATE = "06_研究与探索/AI_情报/automation/state/global.json"
CHINA_STATE = "06_研究与探索/AI_情报/automation/state/china.json"


@pytest.mark.parametrize(
    ("region", "path"),
    [
        ("Global", GLOBAL_REPORT),
        ("China", CHINA_REPORT),
        ("Global", GLOBAL_STATE),
        ("China", CHINA_STATE),
    ],
)
def test_allowed_write_paths_pass(region: str, path: str) -> None:
    assert validate_write_path(region, path).as_posix() == path


def test_multiple_paths_for_one_region_pass() -> None:
    paths = validate_write_paths("Global", [GLOBAL_REPORT, GLOBAL_STATE])

    assert tuple(path.as_posix() for path in paths) == (GLOBAL_REPORT, GLOBAL_STATE)


def test_unsupported_region_fails() -> None:
    with pytest.raises(PathPolicyError):
        validate_write_path("Combined", GLOBAL_REPORT)


@pytest.mark.parametrize(
    ("region", "path"),
    [
        ("Global", CHINA_REPORT),
        ("Global", CHINA_STATE),
        ("China", GLOBAL_REPORT),
        ("China", GLOBAL_STATE),
    ],
)
def test_cross_region_paths_fail(region: str, path: str) -> None:
    with pytest.raises(PathPolicyError):
        validate_write_path(region, path)


@pytest.mark.parametrize(
    "path",
    [
        "INDEX.md",
        "CHANGELOG.md",
        "AGENTS.md",
        "06_研究与探索/INDEX.md",
        "06_研究与探索/AI_情报/Stage1/Source_Registry_v0.1.md",
        "06_研究与探索/AI_情报/automation/config/global_sources.json",
        "06_研究与探索/AI_情报/automation/pipeline/config.py",
        ".github/workflows/ai-intelligence.yml",
        "../CHANGELOG.md",
        "../../something",
        "/absolute/path",
    ],
)
def test_forbidden_paths_fail(path: str) -> None:
    with pytest.raises(PathPolicyError):
        validate_write_path("Global", path)


@pytest.mark.parametrize(
    "path",
    [
        "06_研究与探索/AI_情报/reports/global/2026/07/2026-08-12_Global_AI_Intelligence.md",
        "06_研究与探索/AI_情报/reports/global/2025/08/2026-08-12_Global_AI_Intelligence.md",
        "06_研究与探索/AI_情报/reports/global/2026/08/2026-08-12_China_AI_Intelligence.md",
        "06_研究与探索/AI_情报/reports/global/2026/08/2026-08-12_Global_AI_Intelligence_r2.md",
        "06_研究与探索/AI_情报/reports/global/2026/08/random.md",
        "06_研究与探索/AI_情报/reports/global/2026/02/2026-02-30_Global_AI_Intelligence.md",
    ],
)
def test_invalid_report_paths_fail(path: str) -> None:
    with pytest.raises(PathPolicyError):
        validate_write_path("Global", path)


def test_symlink_escape_fails(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    intelligence_root = repo_root / "06_研究与探索" / "AI_情报"
    intelligence_root.mkdir(parents=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    (intelligence_root / "reports").symlink_to(outside, target_is_directory=True)

    with pytest.raises(PathPolicyError):
        validate_write_path("Global", GLOBAL_REPORT, repo_root=repo_root)
