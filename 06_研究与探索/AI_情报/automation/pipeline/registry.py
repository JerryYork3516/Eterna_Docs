"""Strict, read-only access to the frozen Source Registry tables."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from types import MappingProxyType
from typing import Mapping

from pipeline.errors import AutomationError


_REQUIRED_HEADERS = (
    "Source",
    "Type",
    "Region",
    "Platform / URL",
    "Priority",
    "Credibility",
    "Fact Citation",
    "Eterna Tags",
)
_SUPPORTED_REGIONS = frozenset({"Global", "China"})
_SUPPORTED_SOURCE_TYPES = frozenset({"Official", "Person", "Community", "Media"})
_SUPPORTED_PRIORITIES = frozenset({"P0", "P1", "P2", "P3"})
_SUPPORTED_CREDIBILITY = frozenset({"High", "Medium", "Low"})
_SUPPORTED_FACT_CITATION = frozenset({"Yes", "Conditional", "No"})
_KNOWN_ETERNA_TAGS = (
    "Business / Ecosystem",
    "Digital Resident",
    "Voice / STS",
    "Studio Next",
    "Runtime Core",
    "Multimodal",
    "AI Coding",
    "Aftelle",
    "ECCS",
    "Agent",
)
_MARKDOWN_LINK = re.compile(r"\[[^\]]+\]\((https?://[^)]+)\)")
_SEPARATOR_CELL = re.compile(r":?-{3,}:?")


class RegistryValidationError(AutomationError):
    """Raised when the frozen Registry cannot be parsed deterministically."""


@dataclass(frozen=True, slots=True)
class RegistryEntry:
    """Runtime projection of the frozen Source Registry fields."""

    name: str
    source_type: str
    region: str
    platform: str
    urls: tuple[str, ...]
    priority: str
    credibility: str
    fact_citation: str
    eterna_tags: tuple[str, ...]


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


def _parse_eterna_tags(value: str) -> tuple[str, ...]:
    """Split the Registry cell while preserving tags that contain `` / ``."""

    protected = value
    placeholders: dict[str, str] = {}
    for index, tag in enumerate(_KNOWN_ETERNA_TAGS):
        placeholder = f"__ETERNA_TAG_{index}__"
        protected = protected.replace(tag, placeholder)
        placeholders[placeholder] = tag
    tags = tuple(
        placeholders.get(item.strip(), item.strip())
        for item in protected.split(" / ")
        if item.strip()
    )
    if not tags or len(set(tags)) != len(tags):
        raise RegistryValidationError("Source Registry row has invalid Eterna Tags")
    return tags


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
        priority = row["Priority"]
        credibility = row["Credibility"]
        fact_citation = row["Fact Citation"]
        eterna_tags = _parse_eterna_tags(row["Eterna Tags"])

        if not name or not source_type or not platform:
            raise RegistryValidationError("Source Registry row has empty required fields")
        if source_type not in _SUPPORTED_SOURCE_TYPES:
            raise RegistryValidationError(
                f"Source Registry row has unsupported Type: {source_type!r}"
            )
        if region not in _SUPPORTED_REGIONS:
            raise RegistryValidationError(
                f"Source Registry row has unsupported Region: {region!r}"
            )
        if priority not in _SUPPORTED_PRIORITIES:
            raise RegistryValidationError(
                f"Source Registry row has unsupported Priority: {priority!r}"
            )
        if credibility not in _SUPPORTED_CREDIBILITY:
            raise RegistryValidationError(
                f"Source Registry row has unsupported Credibility: {credibility!r}"
            )
        if fact_citation not in _SUPPORTED_FACT_CITATION:
            raise RegistryValidationError(
                f"Source Registry row has unsupported Fact Citation: {fact_citation!r}"
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
            priority=priority,
            credibility=credibility,
            fact_citation=fact_citation,
            eterna_tags=eterna_tags,
        )

    if not entries:
        raise RegistryValidationError("No Source Registry entries were parsed")

    return SourceRegistry(entries=MappingProxyType(entries))
