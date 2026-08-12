"""Strict, read-only access to the frozen Source Registry tables."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from types import MappingProxyType
from typing import Mapping

from pipeline.errors import AutomationError


_REQUIRED_HEADERS = ("Source", "Type", "Region", "Platform / URL")
_SUPPORTED_REGIONS = frozenset({"Global", "China"})
_MARKDOWN_LINK = re.compile(r"\[[^\]]+\]\((https?://[^)]+)\)")
_SEPARATOR_CELL = re.compile(r":?-{3,}:?")


class RegistryValidationError(AutomationError):
    """Raised when the frozen Registry cannot be parsed deterministically."""


@dataclass(frozen=True, slots=True)
class RegistryEntry:
    """Minimum Source Registry fields needed by runtime config validation."""

    name: str
    source_type: str
    region: str
    platform: str
    urls: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SourceRegistry:
    """Immutable exact-name index of parsed Registry entries."""

    entries: Mapping[str, RegistryEntry]

    def get(self, registry_ref: str) -> RegistryEntry:
        try:
            return self.entries[registry_ref]
        except KeyError as exc:
            raise RegistryValidationError(
                f"Source Registry reference does not exist: {registry_ref!r}"
            ) from exc


def _split_table_row(line: str) -> tuple[str, ...]:
    return tuple(cell.strip() for cell in line.strip().strip("|").split("|"))


def _is_separator_row(cells: tuple[str, ...]) -> bool:
    return bool(cells) and all(_SEPARATOR_CELL.fullmatch(cell) for cell in cells)


def load_source_registry(path: Path) -> SourceRegistry:
    """Parse only the current Registry's source tables without modifying them."""

    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise RegistryValidationError(f"Cannot read Source Registry: {path}") from exc

    if "状态：`FROZEN`" not in text:
        raise RegistryValidationError("Source Registry is not marked FROZEN")

    entries: dict[str, RegistryEntry] = {}
    headers: tuple[str, ...] | None = None

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if not line.startswith("|"):
            headers = None
            continue

        cells = _split_table_row(line)
        if headers is None:
            if all(header in cells for header in _REQUIRED_HEADERS):
                headers = cells
            continue

        if _is_separator_row(cells):
            continue
        if len(cells) != len(headers):
            raise RegistryValidationError("Malformed Source Registry table row")

        row = dict(zip(headers, cells, strict=True))
        name = row["Source"]
        source_type = row["Type"]
        region = row["Region"]
        platform = row["Platform / URL"]

        if not name or not source_type or not platform:
            raise RegistryValidationError("Source Registry row has empty required fields")
        if region not in _SUPPORTED_REGIONS:
            raise RegistryValidationError(
                f"Source Registry row has unsupported Region: {region!r}"
            )
        if name in entries:
            raise RegistryValidationError(
                f"Source Registry Source name is not unique: {name!r}"
            )

        entries[name] = RegistryEntry(
            name=name,
            source_type=source_type,
            region=region,
            platform=platform,
            urls=tuple(_MARKDOWN_LINK.findall(platform)),
        )

    if not entries:
        raise RegistryValidationError("No Source Registry entries were parsed")

    return SourceRegistry(entries=MappingProxyType(entries))
