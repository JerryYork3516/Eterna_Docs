"""Offline, default-deny validation for future automation write paths."""

from __future__ import annotations

from datetime import date
from pathlib import Path, PurePosixPath
import re
from typing import Iterable

from pipeline.errors import AutomationError


_SUPPORTED_REGIONS = frozenset({"Global", "China"})
_DEFAULT_REPO_ROOT = Path(__file__).resolve().parents[4]
_STATE_PATHS = {
    "Global": "06_研究与探索/AI_情报/automation/state/global.json",
    "China": "06_研究与探索/AI_情报/automation/state/china.json",
}
_REPORT_PATTERNS = {
    "Global": re.compile(
        r"^06_研究与探索/AI_情报/reports/global/"
        r"(?P<year>[0-9]{4})/(?P<month>[0-9]{2})/"
        r"(?P<report_date>[0-9]{4}-[0-9]{2}-[0-9]{2})"
        r"_Global_AI_Intelligence\.md$"
    ),
    "China": re.compile(
        r"^06_研究与探索/AI_情报/reports/china/"
        r"(?P<year>[0-9]{4})/(?P<month>[0-9]{2})/"
        r"(?P<report_date>[0-9]{4}-[0-9]{2}-[0-9]{2})"
        r"_China_AI_Intelligence\.md$"
    ),
}


class PathPolicyError(AutomationError):
    """Raised when a proposed automation write path is outside the allowlist."""


def _validate_repo_relative_path(repo_relative_path: str) -> PurePosixPath:
    if not isinstance(repo_relative_path, str) or not repo_relative_path:
        raise PathPolicyError("Write path must be a non-empty repo-relative string")
    if "\\" in repo_relative_path:
        raise PathPolicyError("Write path must use POSIX separators")

    path = PurePosixPath(repo_relative_path)
    raw_parts = repo_relative_path.split("/")
    if path.is_absolute() or any(part in {"", ".", ".."} for part in raw_parts):
        raise PathPolicyError("Absolute paths and path traversal are forbidden")
    return path


def _reject_symlink_escape(path: PurePosixPath, repo_root: Path) -> None:
    try:
        root = repo_root.resolve()
        candidate = root.joinpath(*path.parts).resolve(strict=False)
    except (OSError, RuntimeError, ValueError) as exc:
        raise PathPolicyError("Write path cannot be resolved safely") from exc
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise PathPolicyError(
            "Write path escapes the repository through a symlink"
        ) from exc


def _validate_report_path(region: str, path_text: str) -> None:
    match = _REPORT_PATTERNS[region].fullmatch(path_text)
    if match is None:
        raise PathPolicyError(f"Path is not an allowed {region} report path")

    report_date_text = match.group("report_date")
    try:
        report_date = date.fromisoformat(report_date_text)
    except ValueError as exc:
        raise PathPolicyError("Report path contains an invalid calendar date") from exc

    if match.group("year") != f"{report_date.year:04d}":
        raise PathPolicyError("Report year directory does not match report_date")
    if match.group("month") != f"{report_date.month:02d}":
        raise PathPolicyError("Report month directory does not match report_date")


def validate_write_path(
    region: str,
    repo_relative_path: str,
    *,
    repo_root: Path | None = None,
) -> PurePosixPath:
    """Validate one future write target without creating or writing it."""

    if not isinstance(region, str) or region not in _SUPPORTED_REGIONS:
        raise PathPolicyError(f"Unsupported Region: {region!r}")

    path = _validate_repo_relative_path(repo_relative_path)
    _reject_symlink_escape(path, repo_root or _DEFAULT_REPO_ROOT)
    path_text = path.as_posix()

    if path_text == _STATE_PATHS[region]:
        return path

    _validate_report_path(region, path_text)
    return path


def validate_write_paths(
    region: str,
    paths: Iterable[str],
    *,
    repo_root: Path | None = None,
) -> tuple[PurePosixPath, ...]:
    """Validate multiple targets under the same Region-specific policy."""

    return tuple(
        validate_write_path(region, path, repo_root=repo_root) for path in paths
    )
