"""Stage 1.12 A9 deterministic event-anchor tests."""

from datetime import date, datetime
import re

import pytest

from pipeline.event_anchor import (
    EventAnchorError,
    EventAnchorInput,
    deterministic_event_anchor,
)
from pipeline.models import Region


EVENT_DATE = date(2026, 8, 14)


def anchor_input(**overrides: object) -> EventAnchorInput:
    values: dict[str, object] = {
        "region": Region.GLOBAL,
        "subject": "GitHub",
        "action": "Announces rollout",
        "object_name": "Grok 4.6 in GitHub Copilot",
        "version": "4.6",
        "event_date": EVENT_DATE,
    }
    values.update(overrides)
    return EventAnchorInput(**values)  # type: ignore[arg-type]


def test_anchor_is_deterministic_and_has_strict_format() -> None:
    first = deterministic_event_anchor(anchor_input())
    second = deterministic_event_anchor(anchor_input())

    assert first == second
    assert re.fullmatch(r"event_anchor_[0-9a-f]{64}", first)


def test_anchor_normalizes_case_whitespace_and_unicode() -> None:
    canonical = anchor_input(
        subject="GitHub",
        action="Announces rollout",
        object_name="Grok 4.6 in GitHub Copilot",
        version="v4.6",
    )
    equivalent = anchor_input(
        subject="  GITHUB\n",
        action="announces\trollout",
        object_name="Ｇｒｏｋ  4.6 IN github copilot",
        version=" V4.6 ",
    )

    assert deterministic_event_anchor(canonical) == deterministic_event_anchor(equivalent)


@pytest.mark.parametrize(
    "overrides",
    [
        {"region": Region.CHINA},
        {"subject": "Anthropic"},
        {"action": "Publishes"},
        {"object_name": "Claude watermark specification"},
        {"version": "4.7"},
        {"event_date": date(2026, 8, 15)},
    ],
)
def test_identity_field_changes_isolate_event(overrides: dict[str, object]) -> None:
    assert deterministic_event_anchor(anchor_input()) != deterministic_event_anchor(
        anchor_input(**overrides)
    )


def test_runtime_and_provenance_fields_are_not_accepted_identity_material() -> None:
    fields = EventAnchorInput.__dataclass_fields__

    assert set(fields) == {
        "region",
        "subject",
        "action",
        "object_name",
        "event_date",
        "version",
    }
    assert not {
        "collected_at",
        "report_date",
        "current_time",
        "candidate_id",
        "source_reference",
        "source_url",
        "eterna_tags",
        "technical_categories",
    } & set(fields)


@pytest.mark.parametrize("field_name", ["subject", "action", "object_name"])
def test_empty_identity_text_fails_closed(field_name: str) -> None:
    with pytest.raises(EventAnchorError, match=field_name):
        anchor_input(**{field_name: " \n\t "})


@pytest.mark.parametrize(
    "invalid_date",
    [None, "2026-08-14", datetime(2026, 8, 14, 12, 0)],
)
def test_missing_or_invalid_event_date_fails_closed(invalid_date: object) -> None:
    with pytest.raises(EventAnchorError, match="event_date"):
        anchor_input(event_date=invalid_date)


def test_invalid_region_and_empty_version_fail_closed() -> None:
    with pytest.raises(EventAnchorError, match="region"):
        anchor_input(region="Global")
    with pytest.raises(EventAnchorError, match="version"):
        anchor_input(version="  ")
