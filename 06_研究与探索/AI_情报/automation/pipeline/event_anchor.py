"""Deterministic event-instance anchors for the Personal MVP route."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date
import hashlib
import json
import re
import unicodedata

from pipeline.errors import AutomationError
from pipeline.models import Region


class EventAnchorError(AutomationError):
    """Raised when an event anchor cannot be created without guessing."""


_SPACE_PATTERN = re.compile(r"\s+")
_ANCHOR_NAMESPACE = "eterna-ai-intelligence-event-anchor-v1"


def _normalized_identity_text(value: object, field_name: str) -> str:
    if type(value) is not str:
        raise EventAnchorError(f"{field_name} must be text")
    normalized = _SPACE_PATTERN.sub(
        " ",
        unicodedata.normalize("NFKC", value),
    ).strip().casefold()
    if not normalized:
        raise EventAnchorError(f"{field_name} must not be empty")
    if len(normalized) > 4096:
        raise EventAnchorError(f"{field_name} exceeds the supported length")
    return normalized


@dataclass(frozen=True, slots=True)
class EventAnchorInput:
    """Auditable identity material supplied from traceable Event Evidence."""

    region: Region
    subject: str
    action: str
    object_name: str
    event_date: date
    version: str | None = None

    def __post_init__(self) -> None:
        if type(self.region) is not Region:
            raise EventAnchorError("region must be a Region")
        _normalized_identity_text(self.subject, "subject")
        _normalized_identity_text(self.action, "action")
        _normalized_identity_text(self.object_name, "object_name")
        if self.version is not None:
            _normalized_identity_text(self.version, "version")
        # datetime is a date subclass, so the exact-type check also rejects
        # naive or timezone-derived runtime timestamps passed by mistake.
        if type(self.event_date) is not date:
            raise EventAnchorError("event_date must be an explicit calendar date")


def deterministic_event_anchor(value: EventAnchorInput) -> str:
    """Return a stable SHA-256 identity without source or runtime material."""

    if type(value) is not EventAnchorInput:
        raise EventAnchorError("value must be an EventAnchorInput")
    material = {
        "action": _normalized_identity_text(value.action, "action"),
        "event_date": value.event_date.isoformat(),
        "namespace": _ANCHOR_NAMESPACE,
        "object_name": _normalized_identity_text(value.object_name, "object_name"),
        "region": value.region.value,
        "subject": _normalized_identity_text(value.subject, "subject"),
        "version": (
            _normalized_identity_text(value.version, "version")
            if value.version is not None
            else None
        ),
    }
    encoded = json.dumps(
        material,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return f"event_anchor_{hashlib.sha256(encoded).hexdigest()}"


__all__ = [
    "EventAnchorError",
    "EventAnchorInput",
    "deterministic_event_anchor",
]
