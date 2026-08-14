"""Offline tests for Region-isolated state, idempotency, and recovery."""

from dataclasses import FrozenInstanceError
from datetime import UTC, date, datetime, timedelta
import json
from pathlib import Path

import pytest

import pipeline.state as state_module
from pipeline.models import InformationStatus, Region, StatusHistoryEntry
from pipeline.state import (
    DeliveryStatus,
    GitCommitStatus,
    RegionState,
    STATE_PATHS,
    StaleStateError,
    StateConflictError,
    StateIOError,
    StateValidationError,
    append_event_evidence,
    append_event_status,
    delivery_idempotency_key,
    empty_region_state,
    format_revision,
    load_region_state,
    register_candidate_observation,
    register_delivery,
    register_event_state,
    register_evidence_reference,
    register_report,
    report_idempotency_key,
    report_path,
    save_region_state,
    set_report_git_result,
    sha256_text,
    state_digest,
    state_from_dict,
    state_from_json,
    state_to_dict,
    state_to_json,
    transition_delivery,
)


REPO_ROOT = Path(__file__).resolve().parents[4]
AUTOMATION_ROOT = Path(__file__).resolve().parents[1]
NOW = datetime(2026, 8, 13, 8, 0, tzinfo=UTC)
REPORT_DATE = date(2026, 8, 13)
SYNTHETIC_FINGERPRINT = sha256_text("synthetic public fixture")
SYNTHETIC_REPORT_HASH = sha256_text("synthetic report body")


def with_candidate(state: RegionState, suffix: str = "1") -> RegionState:
    return register_candidate_observation(
        state,
        observation_key=f"provided-observation-{suffix}",
        candidate_id=f"provided-candidate-{suffix}",
        source_reference="Synthetic Official Source",
        observed_at=NOW,
        canonical_url=f"https://example.invalid/public/{suffix}",
        source_object_id=None,
        content_fingerprint=SYNTHETIC_FINGERPRINT,
    )


def with_evidence(state: RegionState, suffix: str = "1") -> RegionState:
    return register_evidence_reference(
        state,
        evidence_id=f"provided-evidence-{suffix}",
        candidate_references=[f"provided-candidate-{suffix}"],
    )


def with_event(state: RegionState) -> RegionState:
    return register_event_state(
        state,
        event_id="provided-event-1",
        evidence_references=["provided-evidence-1"],
        information_status=InformationStatus.UNCONFIRMED,
    )


def with_report(state: RegionState, revision: int = 1) -> RegionState:
    return register_report(
        state,
        report_date_value=REPORT_DATE,
        revision=revision,
        report_path_value=report_path(state.region, REPORT_DATE),
        content_hash=SYNTHETIC_REPORT_HASH,
    )


def with_pushed_report(state: RegionState) -> RegionState:
    state = with_report(state)
    key = state.reports[0].idempotency_key
    commit_sha = "a" * 40
    state = set_report_git_result(
        state,
        idempotency_key=key,
        status=GitCommitStatus.COMMITTED,
        commit_sha=commit_sha,
    )
    return set_report_git_result(
        state,
        idempotency_key=key,
        status=GitCommitStatus.PUSHED,
        commit_sha=commit_sha,
    )


def populated_state(region: Region = Region.GLOBAL) -> RegionState:
    state = empty_region_state(region)
    state = with_candidate(state)
    state = with_evidence(state)
    state = with_event(state)
    state = with_report(state)
    return register_delivery(state, report_date_value=REPORT_DATE, revision=1)


@pytest.mark.parametrize(
    ("region", "filename"),
    [(Region.GLOBAL, "global.json"), (Region.CHINA, "china.json")],
)
def test_formal_initial_state_loads_and_round_trips(region: Region, filename: str) -> None:
    relative_path = STATE_PATHS[region]
    loaded = load_region_state(
        relative_path,
        expected_region=region,
        repo_root=REPO_ROOT,
    )
    file_text = (AUTOMATION_ROOT / "state" / filename).read_text(encoding="utf-8").strip()

    assert loaded.state == empty_region_state(region)
    assert loaded.state.schema_version == 1
    assert state_to_json(loaded.state) == file_text
    assert loaded.digest == state_digest(loaded.state)


def test_initial_state_is_empty_and_deterministic() -> None:
    state = empty_region_state(Region.GLOBAL)

    assert state.candidates == state.evidences == state.events == ()
    assert state.reports == state.deliveries == ()
    assert state_to_json(state) == state_to_json(state)


def test_cross_region_formal_state_load_fails() -> None:
    with pytest.raises(StateValidationError, match="official Region state path"):
        load_region_state(
            STATE_PATHS[Region.CHINA],
            expected_region=Region.GLOBAL,
            repo_root=REPO_ROOT,
        )


def test_state_round_trip_unicode_and_deterministic_json() -> None:
    state = populated_state()
    text = state_to_json(state)

    assert state_from_dict(state_to_dict(state)) == state
    assert state_from_json(text, expected_region=Region.GLOBAL) == state
    assert state_to_json(state) == text
    assert "Synthetic Official Source" in text
    assert ": " not in text and ", " not in text


@pytest.mark.parametrize("field", ["future", "token"])
def test_unknown_top_level_field_fails(field: str) -> None:
    payload = state_to_dict(empty_region_state(Region.GLOBAL))
    payload[field] = "forbidden"

    with pytest.raises(StateValidationError, match="unknown"):
        state_from_dict(payload)


def test_missing_field_wrong_type_and_unknown_schema_fail() -> None:
    missing = state_to_dict(empty_region_state(Region.GLOBAL))
    missing.pop("events")
    wrong_type = state_to_dict(empty_region_state(Region.GLOBAL))
    wrong_type["reports"] = {}
    future = state_to_dict(empty_region_state(Region.GLOBAL))
    future["schema_version"] = 2

    with pytest.raises(StateValidationError, match="missing"):
        state_from_dict(missing)
    with pytest.raises(StateValidationError, match="array"):
        state_from_dict(wrong_type)
    with pytest.raises(StateValidationError, match="schema_version"):
        state_from_dict(future)


def test_mutable_input_isolation_and_frozen_state() -> None:
    payload = state_to_dict(populated_state())
    state = state_from_dict(payload)
    payload["candidates"].clear()
    payload["events"][0]["evidence_references"].append("other")

    assert len(state.candidates) == 1
    assert state.events[0].evidence_references == ("provided-evidence-1",)
    with pytest.raises(FrozenInstanceError):
        state.region = Region.CHINA  # type: ignore[misc]


def test_first_candidate_observation_uses_caller_provided_id() -> None:
    state = with_candidate(empty_region_state(Region.GLOBAL))
    record = state.candidates[0]

    assert record.candidate_id == "provided-candidate-1"
    assert record.first_seen_at == record.last_seen_at == NOW


def test_repeated_candidate_observation_preserves_first_seen_and_advances_last_seen() -> None:
    state = with_candidate(empty_region_state(Region.GLOBAL))
    later = NOW + timedelta(hours=2)
    state = register_candidate_observation(
        state,
        observation_key="provided-observation-1",
        candidate_id="provided-candidate-1",
        source_reference="Synthetic Official Source",
        observed_at=later,
        canonical_url="https://example.invalid/public/1",
        content_fingerprint=SYNTHETIC_FINGERPRINT,
    )

    assert state.candidates[0].first_seen_at == NOW
    assert state.candidates[0].last_seen_at == later


def test_candidate_last_seen_regression_fails() -> None:
    state = with_candidate(empty_region_state(Region.GLOBAL))

    with pytest.raises(StateConflictError, match="regress"):
        register_candidate_observation(
            state,
            observation_key="provided-observation-1",
            candidate_id="provided-candidate-1",
            source_reference="Synthetic Official Source",
            observed_at=NOW - timedelta(seconds=1),
            canonical_url="https://example.invalid/public/1",
            content_fingerprint=SYNTHETIC_FINGERPRINT,
        )


@pytest.mark.parametrize(
    ("candidate_id", "source_reference"),
    [("different-candidate", "Synthetic Official Source"), ("provided-candidate-1", "Other Source")],
)
def test_candidate_id_or_source_rebinding_fails(
    candidate_id: str,
    source_reference: str,
) -> None:
    state = with_candidate(empty_region_state(Region.GLOBAL))

    with pytest.raises(StateConflictError, match="rebind"):
        register_candidate_observation(
            state,
            observation_key="provided-observation-1",
            candidate_id=candidate_id,
            source_reference=source_reference,
            observed_at=NOW,
            canonical_url="https://example.invalid/public/1",
            content_fingerprint=SYNTHETIC_FINGERPRINT,
        )


def test_candidate_requires_identity_material_and_explicit_id() -> None:
    with pytest.raises(StateValidationError, match="stable observation"):
        register_candidate_observation(
            empty_region_state(Region.GLOBAL),
            observation_key="provided-observation",
            candidate_id="provided-candidate",
            source_reference="Synthetic Source",
            observed_at=NOW,
        )
    with pytest.raises(TypeError):
        register_candidate_observation(  # type: ignore[call-arg]
            empty_region_state(Region.GLOBAL),
            observation_key="provided-observation",
            source_reference="Synthetic Source",
            observed_at=NOW,
            source_object_id="object-1",
        )


def test_evidence_registration_is_idempotent_but_conflicting_binding_fails() -> None:
    state = with_candidate(empty_region_state(Region.GLOBAL))
    state = with_evidence(state)
    same = with_evidence(state)

    assert same is state
    with pytest.raises((StateConflictError, StateValidationError)):
        register_evidence_reference(
            state,
            evidence_id="provided-evidence-1",
            candidate_references=["other-candidate"],
        )
    with pytest.raises(StateValidationError, match="list or tuple"):
        register_evidence_reference(
            state,
            evidence_id="provided-evidence-2",
            candidate_references="provided-candidate-1",
        )


def test_event_registration_preserves_caller_id_and_is_idempotent() -> None:
    state = with_evidence(with_candidate(empty_region_state(Region.GLOBAL)))
    state = with_event(state)
    same = with_event(state)

    assert state.events[0].event_id == "provided-event-1"
    assert same is state


def test_event_evidence_is_append_only_and_ordered() -> None:
    state = with_candidate(empty_region_state(Region.GLOBAL))
    state = with_evidence(state)
    state = with_candidate(state, "2")
    state = with_evidence(state, "2")
    state = with_event(state)
    updated = append_event_evidence(
        state,
        event_id="provided-event-1",
        evidence_references=["provided-evidence-2"],
    )

    assert updated.events[0].evidence_references == (
        "provided-evidence-1",
        "provided-evidence-2",
    )
    assert state.events[0].evidence_references == ("provided-evidence-1",)


def test_status_history_append_and_immutability() -> None:
    state = with_event(with_evidence(with_candidate(empty_region_state(Region.GLOBAL))))
    entry = StatusHistoryEntry(
        changed_at=NOW + timedelta(minutes=1),
        previous_status=InformationStatus.UNCONFIRMED,
        new_status=InformationStatus.CONFIRMED,
        evidence_references=["provided-evidence-1"],
        reason="Synthetic official confirmation.",
    )
    updated = append_event_status(state, event_id="provided-event-1", entry=entry)

    assert updated.events[0].information_status is InformationStatus.CONFIRMED
    assert updated.events[0].status_history == (entry,)
    assert state.events[0].status_history == ()
    with pytest.raises(FrozenInstanceError):
        entry.reason = "changed"  # type: ignore[misc]


def test_status_history_previous_status_mismatch_fails() -> None:
    state = with_event(with_evidence(with_candidate(empty_region_state(Region.GLOBAL))))
    entry = StatusHistoryEntry(
        changed_at=NOW,
        previous_status=InformationStatus.CONFIRMED,
        new_status=InformationStatus.COMMUNITY_TREND,
        evidence_references=["provided-evidence-1"],
        reason="Synthetic change.",
    )

    with pytest.raises(StateConflictError, match="previous_status"):
        append_event_status(state, event_id="provided-event-1", entry=entry)


def test_status_history_timestamp_regression_fails() -> None:
    state = with_event(with_evidence(with_candidate(empty_region_state(Region.GLOBAL))))
    first = StatusHistoryEntry(
        changed_at=NOW + timedelta(minutes=2),
        previous_status=InformationStatus.UNCONFIRMED,
        new_status=InformationStatus.CONFIRMED,
        evidence_references=["provided-evidence-1"],
        reason="Synthetic confirmation.",
    )
    state = append_event_status(state, event_id="provided-event-1", entry=first)
    regressed = StatusHistoryEntry(
        changed_at=NOW + timedelta(minutes=1),
        previous_status=InformationStatus.CONFIRMED,
        new_status=InformationStatus.HIGH_CONFIDENCE_SIGNAL,
        evidence_references=["provided-evidence-1"],
        reason="Synthetic correction.",
    )

    with pytest.raises(StateConflictError, match="timestamp"):
        append_event_status(state, event_id="provided-event-1", entry=regressed)


@pytest.mark.parametrize("revision", [1, 2, 99])
def test_revision_format_is_deterministic(revision: int) -> None:
    assert format_revision(revision) == f"r{revision}"


@pytest.mark.parametrize("revision", [0, -1, 1.0, "1", True])
def test_invalid_revision_fails(revision: object) -> None:
    with pytest.raises(StateValidationError, match="positive integer"):
        format_revision(revision)  # type: ignore[arg-type]


def test_report_idempotency_keys_are_deterministic_and_region_separated() -> None:
    global_key = report_idempotency_key(Region.GLOBAL, REPORT_DATE, 1)
    china_key = report_idempotency_key(Region.CHINA, REPORT_DATE, 1)

    assert global_key == "report|Global|2026-08-13|r1"
    assert china_key == "report|China|2026-08-13|r1"
    assert global_key != china_key
    assert global_key != report_idempotency_key(Region.GLOBAL, REPORT_DATE, 2)


def test_same_report_key_and_hash_is_idempotent() -> None:
    state = with_report(empty_region_state(Region.GLOBAL))
    same = with_report(state)

    assert same is state
    assert len(state.reports) == 1


def test_same_report_key_with_different_hash_fails() -> None:
    state = with_report(empty_region_state(Region.GLOBAL))

    with pytest.raises(StateConflictError, match="content_hash"):
        register_report(
            state,
            report_date_value=REPORT_DATE,
            revision=1,
            report_path_value=report_path(Region.GLOBAL, REPORT_DATE),
            content_hash=sha256_text("different synthetic report"),
        )


def test_cross_region_report_path_fails() -> None:
    with pytest.raises(StateValidationError, match="allowlist"):
        register_report(
            empty_region_state(Region.GLOBAL),
            report_date_value=REPORT_DATE,
            revision=1,
            report_path_value=report_path(Region.CHINA, REPORT_DATE),
            content_hash=SYNTHETIC_REPORT_HASH,
        )


def test_report_content_hash_is_lowercase_sha256() -> None:
    digest = sha256_text("中文 synthetic content")

    assert len(digest) == 64
    assert digest == digest.lower()
    with pytest.raises(StateValidationError, match="SHA-256"):
        register_report(
            empty_region_state(Region.GLOBAL),
            report_date_value=REPORT_DATE,
            revision=1,
            report_path_value=report_path(Region.GLOBAL, REPORT_DATE),
            content_hash="bad-hash",
        )


def test_git_result_is_state_only_and_push_requires_commit() -> None:
    state = with_report(empty_region_state(Region.GLOBAL))
    key = state.reports[0].idempotency_key
    commit_sha = "a" * 40

    with pytest.raises(StateConflictError, match="committed"):
        set_report_git_result(
            state,
            idempotency_key=key,
            status=GitCommitStatus.PUSHED,
            commit_sha=commit_sha,
        )
    state = set_report_git_result(
        state,
        idempotency_key=key,
        status=GitCommitStatus.COMMITTED,
        commit_sha=commit_sha,
    )
    state = set_report_git_result(
        state,
        idempotency_key=key,
        status=GitCommitStatus.PUSHED,
        commit_sha=commit_sha,
    )

    assert state.reports[0].git_status is GitCommitStatus.PUSHED
    with pytest.raises(StateConflictError, match="terminal|illegal"):
        set_report_git_result(
            state,
            idempotency_key=key,
            status=GitCommitStatus.COMMITTED,
            commit_sha=commit_sha,
        )


def test_push_failure_preserves_commit_sha_and_retry_only_pushes() -> None:
    state = with_report(empty_region_state(Region.GLOBAL))
    key = state.reports[0].idempotency_key
    commit_sha = "b" * 40

    state = set_report_git_result(
        state,
        idempotency_key=key,
        status=GitCommitStatus.COMMITTED,
        commit_sha=commit_sha,
    )
    state = set_report_git_result(
        state,
        idempotency_key=key,
        status=GitCommitStatus.PUSH_FAILED,
        commit_sha=commit_sha,
    )

    assert state.reports[0].git_status is GitCommitStatus.PUSH_FAILED
    assert state.reports[0].commit_sha == commit_sha
    persisted = state_from_json(state_to_json(state), expected_region=Region.GLOBAL)
    assert persisted.reports[0].git_status is GitCommitStatus.PUSH_FAILED
    assert persisted.reports[0].commit_sha == commit_sha
    with pytest.raises(StateConflictError, match="illegal"):
        set_report_git_result(
            state,
            idempotency_key=key,
            status=GitCommitStatus.COMMITTED,
            commit_sha=commit_sha,
        )
    with pytest.raises(StateConflictError, match="preserve"):
        set_report_git_result(
            state,
            idempotency_key=key,
            status=GitCommitStatus.PUSHED,
            commit_sha="c" * 40,
        )

    state = set_report_git_result(
        state,
        idempotency_key=key,
        status=GitCommitStatus.PUSHED,
        commit_sha=commit_sha,
    )

    assert state.reports[0].git_status is GitCommitStatus.PUSHED
    assert state.reports[0].commit_sha == commit_sha
    with pytest.raises(StateConflictError, match="terminal|illegal"):
        set_report_git_result(
            state,
            idempotency_key=key,
            status=GitCommitStatus.PUSH_FAILED,
            commit_sha=commit_sha,
        )


def test_commit_failure_can_retry_commit_without_sha() -> None:
    state = with_report(empty_region_state(Region.GLOBAL))
    key = state.reports[0].idempotency_key

    state = set_report_git_result(
        state,
        idempotency_key=key,
        status=GitCommitStatus.COMMIT_FAILED,
        commit_sha=None,
    )
    assert state.reports[0].commit_sha is None

    state = set_report_git_result(
        state,
        idempotency_key=key,
        status=GitCommitStatus.COMMITTED,
        commit_sha="d" * 40,
    )
    assert state.reports[0].git_status is GitCommitStatus.COMMITTED


@pytest.mark.parametrize(
    ("status", "commit_sha", "match"),
    [
        (GitCommitStatus.PUSH_FAILED, None, "require commit_sha"),
        (GitCommitStatus.COMMIT_FAILED, "e" * 40, "must not carry commit_sha"),
    ],
)
def test_git_failure_status_enforces_commit_sha_contract(
    status: GitCommitStatus,
    commit_sha: str | None,
    match: str,
) -> None:
    payload = state_to_dict(with_report(empty_region_state(Region.GLOBAL)))
    payload["reports"][0]["git_status"] = status.value
    payload["reports"][0]["commit_sha"] = commit_sha

    with pytest.raises(StateValidationError, match=match):
        state_from_dict(payload)


def test_delivery_key_is_deterministic_and_distinct_from_report_key() -> None:
    delivery_key = delivery_idempotency_key(Region.GLOBAL, REPORT_DATE, 1)

    assert delivery_key == "delivery|Global|2026-08-13|r1"
    assert delivery_key != report_idempotency_key(Region.GLOBAL, REPORT_DATE, 1)


def test_delivery_cannot_start_before_report_is_pushed() -> None:
    state = register_delivery(
        with_report(empty_region_state(Region.GLOBAL)),
        report_date_value=REPORT_DATE,
        revision=1,
    )

    with pytest.raises(StateConflictError, match="pushed"):
        transition_delivery(
            state,
            idempotency_key=state.deliveries[0].idempotency_key,
            new_status=DeliveryStatus.IN_PROGRESS,
        )


def test_delivery_status_success_path_and_terminal_guard() -> None:
    state = register_delivery(with_pushed_report(empty_region_state(Region.GLOBAL)), report_date_value=REPORT_DATE, revision=1)
    key = state.deliveries[0].idempotency_key
    state = transition_delivery(state, idempotency_key=key, new_status=DeliveryStatus.IN_PROGRESS)
    state = transition_delivery(state, idempotency_key=key, new_status=DeliveryStatus.DELIVERED)

    assert state.deliveries[0].status is DeliveryStatus.DELIVERED
    for next_status in DeliveryStatus:
        with pytest.raises(StateConflictError):
            transition_delivery(state, idempotency_key=key, new_status=next_status)


def test_delivery_failure_and_retry_path() -> None:
    state = register_delivery(with_pushed_report(empty_region_state(Region.CHINA)), report_date_value=REPORT_DATE, revision=1)
    key = state.deliveries[0].idempotency_key
    state = transition_delivery(state, idempotency_key=key, new_status=DeliveryStatus.IN_PROGRESS)
    state = transition_delivery(state, idempotency_key=key, new_status=DeliveryStatus.DELIVERY_FAILED)
    state = transition_delivery(state, idempotency_key=key, new_status=DeliveryStatus.IN_PROGRESS)
    state = transition_delivery(state, idempotency_key=key, new_status=DeliveryStatus.DELIVERED)

    assert state.deliveries[0].status is DeliveryStatus.DELIVERED


@pytest.mark.parametrize(
    ("region", "relative_path"),
    [(Region.GLOBAL, STATE_PATHS[Region.GLOBAL]), (Region.CHINA, STATE_PATHS[Region.CHINA])],
)
def test_official_state_paths_save_in_isolated_repo(
    tmp_path: Path,
    region: Region,
    relative_path: str,
) -> None:
    digest = save_region_state(
        empty_region_state(region),
        relative_path,
        repo_root=tmp_path,
        expected_previous_digest=None,
        create_new=True,
    )

    assert digest == state_digest(empty_region_state(region))
    assert load_region_state(relative_path, expected_region=region, repo_root=tmp_path).state == empty_region_state(region)


@pytest.mark.parametrize(
    "relative_path",
    [
        STATE_PATHS[Region.CHINA],
        "06_研究与探索/AI_情报/automation/state/other.json",
        "06_研究与探索/AI_情报/reports/global/2026/08/state.json",
        "/tmp/global.json",
    ],
)
def test_wrong_or_arbitrary_state_path_fails(tmp_path: Path, relative_path: str) -> None:
    with pytest.raises(StateValidationError):
        save_region_state(
            empty_region_state(Region.GLOBAL),
            relative_path,
            repo_root=tmp_path,
            expected_previous_digest=None,
            create_new=True,
        )


def test_atomic_save_produces_valid_json_and_no_temp_file(tmp_path: Path) -> None:
    relative_path = STATE_PATHS[Region.GLOBAL]
    save_region_state(
        empty_region_state(Region.GLOBAL),
        relative_path,
        repo_root=tmp_path,
        expected_previous_digest=None,
        create_new=True,
    )
    target = tmp_path / relative_path

    assert state_from_json(target.read_text(encoding="utf-8"), expected_region=Region.GLOBAL) == empty_region_state(Region.GLOBAL)
    assert list(target.parent.glob(".global.json.*.tmp")) == []


def test_atomic_replace_failure_retains_old_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    relative_path = STATE_PATHS[Region.GLOBAL]
    save_region_state(
        empty_region_state(Region.GLOBAL),
        relative_path,
        repo_root=tmp_path,
        expected_previous_digest=None,
        create_new=True,
    )
    loaded = load_region_state(relative_path, expected_region=Region.GLOBAL, repo_root=tmp_path)
    updated = with_candidate(loaded.state)
    target = tmp_path / relative_path
    before = target.read_bytes()

    def fail_replace(_source: object, _target: object) -> None:
        raise OSError("synthetic pre-replace failure")

    monkeypatch.setattr(state_module.os, "replace", fail_replace)
    with pytest.raises(StateIOError, match="Atomic"):
        save_region_state(
            updated,
            relative_path,
            repo_root=tmp_path,
            expected_previous_digest=loaded.digest,
        )

    assert target.read_bytes() == before
    assert list(target.parent.glob(".global.json.*.tmp")) == []


def test_optimistic_concurrency_rejects_stale_save(tmp_path: Path) -> None:
    relative_path = STATE_PATHS[Region.GLOBAL]
    save_region_state(
        empty_region_state(Region.GLOBAL),
        relative_path,
        repo_root=tmp_path,
        expected_previous_digest=None,
        create_new=True,
    )
    run_a = load_region_state(relative_path, expected_region=Region.GLOBAL, repo_root=tmp_path)
    run_b = load_region_state(relative_path, expected_region=Region.GLOBAL, repo_root=tmp_path)
    newer = with_candidate(run_b.state)
    newer_digest = save_region_state(
        newer,
        relative_path,
        repo_root=tmp_path,
        expected_previous_digest=run_b.digest,
    )

    with pytest.raises(StaleStateError):
        save_region_state(
            run_a.state,
            relative_path,
            repo_root=tmp_path,
            expected_previous_digest=run_a.digest,
        )

    assert load_region_state(relative_path, expected_region=Region.GLOBAL, repo_root=tmp_path).digest == newer_digest


def test_corrupt_state_fails_closed(tmp_path: Path) -> None:
    relative_path = STATE_PATHS[Region.GLOBAL]
    target = tmp_path / relative_path
    target.parent.mkdir(parents=True)
    target.write_text("{", encoding="utf-8")

    with pytest.raises(StateValidationError):
        load_region_state(relative_path, expected_region=Region.GLOBAL, repo_root=tmp_path)
    assert target.read_text(encoding="utf-8") == "{"


@pytest.mark.parametrize(
    ("mutator", "match"),
    [
        (lambda payload: payload.__setitem__("region", "China"), "expected Region"),
        (lambda payload: payload["reports"][0].__setitem__("content_hash", "bad"), "SHA-256"),
        (lambda payload: payload["deliveries"][0].__setitem__("status", "Sent"), "unsupported"),
        (lambda payload: payload["candidates"][0].__setitem__("first_seen_at", "2026-08-13T08:00:00"), "timezone-aware"),
    ],
)
def test_corrupt_fields_fail_closed(mutator, match: str) -> None:
    payload = state_to_dict(populated_state())
    mutator(payload)

    with pytest.raises(StateValidationError, match=match):
        state_from_dict(payload, expected_region=Region.GLOBAL)


def test_history_inconsistency_fails_closed() -> None:
    state = with_event(with_evidence(with_candidate(empty_region_state(Region.GLOBAL))))
    entry = StatusHistoryEntry(
        changed_at=NOW,
        previous_status=InformationStatus.UNCONFIRMED,
        new_status=InformationStatus.CONFIRMED,
        evidence_references=["provided-evidence-1"],
        reason="Synthetic confirmation.",
    )
    payload = state_to_dict(append_event_status(state, event_id="provided-event-1", entry=entry))
    payload["events"][0]["information_status"] = "Community trend"

    with pytest.raises(StateValidationError, match="final history"):
        state_from_dict(payload)

    payload = state_to_dict(append_event_status(state, event_id="provided-event-1", entry=entry))
    payload["events"][0]["status_history"][0]["previous_status"] = "Community trend"
    with pytest.raises(StateValidationError, match="initial status"):
        state_from_dict(payload)


def test_sensitive_content_is_rejected() -> None:
    state = with_event(with_evidence(with_candidate(empty_region_state(Region.GLOBAL))))
    entry = StatusHistoryEntry(
        changed_at=NOW,
        previous_status=InformationStatus.UNCONFIRMED,
        new_status=InformationStatus.CONFIRMED,
        evidence_references=["provided-evidence-1"],
        reason="Send details to " + "person" + "@" + "example.invalid",
    )

    with pytest.raises(StateValidationError, match="sensitive"):
        append_event_status(state, event_id="provided-event-1", entry=entry)


def test_duplicate_json_keys_and_invalid_region_fail() -> None:
    with pytest.raises(StateValidationError, match="duplicate"):
        state_from_json('{"schema_version":1,"schema_version":1}')
    payload = state_to_dict(empty_region_state(Region.GLOBAL))
    payload["region"] = "GLOBAL"
    with pytest.raises(StateValidationError, match="unsupported"):
        state_from_dict(payload)
