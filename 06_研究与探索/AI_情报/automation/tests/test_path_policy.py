"""Unit tests for default-deny, Region-specific write paths."""

from pathlib import Path

import pytest

from pipeline.path_policy import (
    PathPolicyError,
    validate_automation_git_target,
    validate_legacy_state_path,
    validate_write_path,
    validate_write_paths,
)


GLOBAL_REPORT = "06_研究与探索/每日AI资讯/2026-08-12_Global_AI_News.md"
CHINA_REPORT = "06_研究与探索/每日AI资讯/2026-08-12_China_AI_News.md"
GLOBAL_STATE = "06_研究与探索/AI_情报/automation/state/global.json"
CHINA_STATE = "06_研究与探索/AI_情报/automation/state/china.json"


@pytest.mark.parametrize(
    ("region", "path"),
    [
        ("Global", GLOBAL_REPORT),
        ("China", CHINA_REPORT),
    ],
)
def test_allowed_write_paths_pass(region: str, path: str) -> None:
    assert validate_write_path(region, path).as_posix() == path


def test_single_path_batch_passes() -> None:
    paths = validate_write_paths("Global", [GLOBAL_REPORT])

    assert tuple(path.as_posix() for path in paths) == (GLOBAL_REPORT,)


@pytest.mark.parametrize("paths", [[], [GLOBAL_REPORT, GLOBAL_REPORT]])
def test_unattended_write_requires_exactly_one_report(paths: list[str]) -> None:
    with pytest.raises(PathPolicyError):
        validate_write_paths("Global", paths)


def test_approved_automation_git_target_passes() -> None:
    assert validate_automation_git_target("AI_News", "origin/AI_News") == (
        "AI_News",
        "origin/AI_News",
    )


@pytest.mark.parametrize(
    ("branch", "upstream"),
    [
        ("main", "origin/main"),
        ("AI-News", "origin/AI-News"),
        ("AI_News", "origin/main"),
        ("other", "origin/AI_News"),
    ],
)
def test_unapproved_automation_git_targets_fail(branch: str, upstream: str) -> None:
    with pytest.raises(PathPolicyError):
        validate_automation_git_target(branch, upstream)


def test_unsupported_region_fails() -> None:
    with pytest.raises(PathPolicyError):
        validate_write_path("Combined", GLOBAL_REPORT)


@pytest.mark.parametrize(
    ("region", "path"),
    [
        ("Global", CHINA_REPORT),
        ("China", GLOBAL_REPORT),
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
        GLOBAL_STATE,
        CHINA_STATE,
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
        "06_研究与探索/AI_情报/reports/global/2026/08/2026-08-12_Global_AI_Intelligence.md",
        "06_研究与探索/AI_情报/reports/china/2026/08/2026-08-12_China_AI_Intelligence.md",
        "06_研究与探索/每日AI资讯/2026-08-12_China_AI_News.md",
        "06_研究与探索/每日AI资讯/2026-08-12_Global_AI_News_r2.md",
        "06_研究与探索/每日AI资讯/2026-8-12_Global_AI_News.md",
        "06_研究与探索/每日AI资讯/2026-08-12_global_AI_News.md",
        "06_研究与探索/每日AI资讯/random.md",
        "06_研究与探索/每日AI资讯/2026-02-30_Global_AI_News.md",
    ],
)
def test_invalid_report_paths_fail(path: str) -> None:
    with pytest.raises(PathPolicyError):
        validate_write_path("Global", path)


def test_symlink_escape_fails(tmp_path: Path) -> None:
    repo_root = tmp_path / "repo"
    research_root = repo_root / "06_研究与探索"
    research_root.mkdir(parents=True)
    outside = tmp_path / "outside"
    outside.mkdir()
    (research_root / "每日AI资讯").symlink_to(outside, target_is_directory=True)

    with pytest.raises(PathPolicyError):
        validate_write_path("Global", GLOBAL_REPORT, repo_root=repo_root)


def test_legacy_state_path_is_separate_from_unattended_write_policy() -> None:
    with pytest.raises(PathPolicyError):
        validate_write_path("Global", GLOBAL_STATE)

    assert validate_legacy_state_path("Global", GLOBAL_STATE).as_posix() == GLOBAL_STATE
