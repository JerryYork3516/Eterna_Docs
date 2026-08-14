"""Deterministic Evidence construction and conservative pre-analysis clustering."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
import hashlib
import json
import re
import unicodedata
from typing import Sequence

from pipeline.errors import AutomationError
from pipeline.models import (
    CandidateItem,
    EternaTag,
    Evidence,
    EvidenceRelation,
    FactCitation,
    Region,
    SourceType,
    TechnicalCategory,
)
from pipeline.state import (
    RegionState,
    StateConflictError,
    append_event_evidence,
    register_event_state,
    register_evidence_reference,
)


class ClusteringError(AutomationError):
    """Raised when A7 cannot cluster without guessing or breaking provenance."""


_SPACE_PATTERN = re.compile(r"\s+")


def _text(value: object, field_name: str, *, maximum: int = 4096) -> str:
    if type(value) is not str or not value or value != value.strip():
        raise ClusteringError(f"{field_name} must be non-empty trimmed text")
    if len(value) > maximum:
        raise ClusteringError(f"{field_name} exceeds the supported length")
    return value


def _normalized_text(value: str) -> str:
    return _SPACE_PATTERN.sub(" ", unicodedata.normalize("NFKC", value)).strip().casefold()


def _digest(material: object) -> str:
    encoded = json.dumps(
        material,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


@dataclass(frozen=True, slots=True)
class EventDescriptor:
    """Explicit same-event identity material supplied by a deterministic upstream rule."""

    subject: str
    action: str
    object_name: str
    event_anchor: str
    version: str | None = None
    technical_categories: tuple[TechnicalCategory, ...] = ()

    def __post_init__(self) -> None:
        _text(self.subject, "subject")
        _text(self.action, "action")
        _text(self.object_name, "object_name")
        _text(self.event_anchor, "event_anchor", maximum=512)
        if self.version is not None:
            _text(self.version, "version")
        if type(self.technical_categories) is not tuple or any(
            type(item) is not TechnicalCategory for item in self.technical_categories
        ):
            raise ClusteringError(
                "technical_categories must be a tuple of TechnicalCategory values"
            )
        if len(set(self.technical_categories)) != len(self.technical_categories):
            raise ClusteringError("technical_categories must not contain duplicates")


@dataclass(frozen=True, slots=True)
class ClusterInput:
    candidate: CandidateItem
    descriptor: EventDescriptor | None = None
    relation: EvidenceRelation = EvidenceRelation.SUPPORTS

    def __post_init__(self) -> None:
        if type(self.candidate) is not CandidateItem:
            raise ClusteringError("candidate must be a CandidateItem")
        if self.descriptor is not None and type(self.descriptor) is not EventDescriptor:
            raise ClusteringError("descriptor must be an EventDescriptor when provided")
        if type(self.relation) is not EvidenceRelation:
            raise ClusteringError("relation must be an EvidenceRelation")


@dataclass(frozen=True, slots=True)
class NearDuplicateLink:
    primary_evidence_id: str
    duplicate_evidence_id: str
    candidate_references: tuple[str, str]
    counts_as_independent_confirmation: bool = False
    reason: str = (
        "Normalized title, non-empty excerpt, and UTC observation day are exact matches."
    )

    def __post_init__(self) -> None:
        _text(self.primary_evidence_id, "primary_evidence_id", maximum=512)
        _text(self.duplicate_evidence_id, "duplicate_evidence_id", maximum=512)
        if self.primary_evidence_id == self.duplicate_evidence_id:
            raise ClusteringError("Near Duplicate Evidence identities must differ")
        if (
            type(self.candidate_references) is not tuple
            or len(self.candidate_references) != 2
        ):
            raise ClusteringError("candidate_references must contain exactly two candidates")
        for reference in self.candidate_references:
            _text(reference, "candidate_reference", maximum=512)
        if self.counts_as_independent_confirmation is not False:
            raise ClusteringError("Near Duplicate must not be independent confirmation")
        _text(self.reason, "reason")


@dataclass(frozen=True, slots=True)
class EventDraft:
    """Pre-analysis Event aggregate; intentionally has no A8/A9 judgment fields."""

    event_id: str
    canonical_title: str
    region: Region
    event_anchor: str | None
    technical_categories: tuple[TechnicalCategory, ...]
    first_seen_at: datetime
    last_seen_at: datetime
    evidence_references: tuple[str, ...]
    independent_evidence_references: tuple[str, ...]
    eterna_tags: tuple[EternaTag, ...]

    def __post_init__(self) -> None:
        _text(self.event_id, "event_id", maximum=512)
        _text(self.canonical_title, "canonical_title")
        if type(self.region) is not Region:
            raise ClusteringError("region must be a Region")
        if self.event_anchor is not None:
            _text(self.event_anchor, "event_anchor", maximum=512)
        if type(self.technical_categories) is not tuple or any(
            type(item) is not TechnicalCategory for item in self.technical_categories
        ):
            raise ClusteringError("technical_categories contains an invalid value")
        if type(self.eterna_tags) is not tuple or any(
            type(item) is not EternaTag for item in self.eterna_tags
        ):
            raise ClusteringError("eterna_tags contains an invalid value")
        if not self.evidence_references or len(set(self.evidence_references)) != len(
            self.evidence_references
        ):
            raise ClusteringError("evidence_references must be non-empty and unique")
        if any(
            reference not in self.evidence_references
            for reference in self.independent_evidence_references
        ):
            raise ClusteringError("independent Evidence must belong to this EventDraft")
        try:
            first_offset = self.first_seen_at.utcoffset()
            last_offset = self.last_seen_at.utcoffset()
        except (AttributeError, OverflowError, ValueError) as exc:
            raise ClusteringError("EventDraft times must be timezone-aware datetimes") from exc
        if first_offset is None or last_offset is None:
            raise ClusteringError("EventDraft times must be timezone-aware datetimes")
        if self.last_seen_at < self.first_seen_at:
            raise ClusteringError("last_seen_at must not precede first_seen_at")


@dataclass(frozen=True, slots=True)
class ClusteringResult:
    evidences: tuple[Evidence, ...]
    event_drafts: tuple[EventDraft, ...]
    near_duplicates: tuple[NearDuplicateLink, ...]
    state: RegionState


def near_duplicate_signature(candidate: CandidateItem) -> str | None:
    """Return an exact normalized-content signature, never a fuzzy similarity score."""

    if candidate.source_excerpt is None:
        return None
    normalized_excerpt = _normalized_text(candidate.source_excerpt)
    if not normalized_excerpt:
        return None
    if candidate.source_published_at is not None:
        temporal_kind = "source_published_day"
        temporal_value = candidate.source_published_at.astimezone(UTC).date().isoformat()
    else:
        temporal_kind = "first_seen_day"
        temporal_value = candidate.first_seen_at.astimezone(UTC).date().isoformat()
    return _digest(
        {
            "namespace": "near-duplicate-v1",
            "title": _normalized_text(candidate.title),
            "excerpt": normalized_excerpt,
            "temporal_kind": temporal_kind,
            "temporal_value": temporal_value,
        }
    )


def _event_material(
    candidate: CandidateItem,
    descriptor: EventDescriptor | None,
) -> dict[str, object]:
    if descriptor is not None:
        return {
            "kind": "structured-event",
            "region": candidate.region.value,
            "subject": _normalized_text(descriptor.subject),
            "action": _normalized_text(descriptor.action),
            "object": _normalized_text(descriptor.object_name),
            "version": (
                _normalized_text(descriptor.version) if descriptor.version is not None else None
            ),
            "event_anchor": descriptor.event_anchor,
        }
    signature = near_duplicate_signature(candidate)
    if signature is not None:
        return {
            "kind": "exact-normalized-content",
            "region": candidate.region.value,
            "content_signature": signature,
        }
    return {
        "kind": "candidate-fallback",
        "region": candidate.region.value,
        "candidate_id": candidate.candidate_id,
    }


def stable_event_id(candidate: CandidateItem, descriptor: EventDescriptor | None = None) -> str:
    """Create a deterministic Region-isolated Event identity without Eterna relevance."""

    if type(candidate) is not CandidateItem:
        raise ClusteringError("candidate must be a CandidateItem")
    if descriptor is not None and type(descriptor) is not EventDescriptor:
        raise ClusteringError("descriptor must be an EventDescriptor when provided")
    return f"event_{_digest({'namespace': 'event-v1', **_event_material(candidate, descriptor)})}"


def stable_evidence_id(
    candidate: CandidateItem,
    *,
    event_id: str,
    relation: EvidenceRelation = EvidenceRelation.SUPPORTS,
) -> str:
    """Create a deterministic Evidence identity bound to Candidate, Event, and relation."""

    if type(candidate) is not CandidateItem:
        raise ClusteringError("candidate must be a CandidateItem")
    _text(event_id, "event_id", maximum=512)
    if type(relation) is not EvidenceRelation:
        raise ClusteringError("relation must be an EvidenceRelation")
    material = {
        "namespace": "evidence-v1",
        "region": candidate.region.value,
        "candidate_id": candidate.candidate_id,
        "event_id": event_id,
        "relation": relation.value,
        "source_reference": candidate.source_reference,
    }
    return f"evidence_{_digest(material)}"


def _is_primary_source(candidate: CandidateItem, descriptor: EventDescriptor | None) -> bool:
    if descriptor is None:
        return False
    return (
        candidate.source_type is SourceType.OFFICIAL
        and candidate.source_fact_citation is FactCitation.YES
        and _normalized_text(candidate.source_reference) == _normalized_text(descriptor.subject)
    )


def _evidence_note(relation: EvidenceRelation) -> str:
    if relation is EvidenceRelation.CONTRADICTS:
        return "Explicit conflict relation only; final Status and Confidence are deferred."
    if relation is EvidenceRelation.SUPPLEMENTS:
        return "Supplemental relation only; no final information status is implied."
    return "Supporting relation only; no final information status is implied."


def _candidate_is_registered(state: RegionState, candidate: CandidateItem) -> bool:
    return any(item.candidate_id == candidate.candidate_id for item in state.candidates)


def build_evidence(
    candidate: CandidateItem,
    *,
    event_id: str,
    state: RegionState,
    descriptor: EventDescriptor | None = None,
    relation: EvidenceRelation = EvidenceRelation.SUPPORTS,
    independent_confirmation: bool = True,
    duplicate_of_evidence_id: str | None = None,
) -> tuple[Evidence, RegionState]:
    """Build one immutable Evidence and register its stable reference in Region state."""

    if type(candidate) is not CandidateItem or type(state) is not RegionState:
        raise ClusteringError("candidate and state must use their strict model types")
    if candidate.region is not state.region:
        raise ClusteringError("Candidate Region does not match Region state")
    if not _candidate_is_registered(state, candidate):
        raise ClusteringError("Candidate must be registered in Region state before Evidence")
    evidence_id = stable_evidence_id(candidate, event_id=event_id, relation=relation)
    evidence = Evidence(
        evidence_id=evidence_id,
        candidate_references=(candidate.candidate_id,),
        source_reference=candidate.source_reference,
        source_url=candidate.source_url,
        source_published_at=candidate.source_published_at,
        collected_at=candidate.collected_at,
        source_priority=candidate.source_priority,
        source_credibility=candidate.source_credibility,
        is_primary_source=_is_primary_source(candidate, descriptor),
        relation=relation,
        traceability={
            "candidate_id": candidate.candidate_id,
            "source_reference": candidate.source_reference,
            "source_url": candidate.source_url,
            "raw_evidence_reference": candidate.raw_evidence_reference,
        },
        evidence_note=_evidence_note(relation),
    )
    existing = next(
        (item for item in state.evidences if item.evidence_id == evidence_id),
        None,
    )
    if existing is not None:
        independent_confirmation = existing.independent_confirmation
        duplicate_of_evidence_id = existing.duplicate_of_evidence_id
        content_signature = existing.content_signature
    else:
        content_signature = near_duplicate_signature(candidate)
    try:
        updated_state = register_evidence_reference(
            state,
            evidence_id=evidence_id,
            candidate_references=evidence.candidate_references,
            relation=relation,
            independent_confirmation=independent_confirmation,
            duplicate_of_evidence_id=duplicate_of_evidence_id,
            content_signature=content_signature,
        )
    except StateConflictError as exc:
        raise ClusteringError("stable Evidence state conflicts with the new observation") from exc
    return evidence, updated_state


def _existing_event_for_candidate(state: RegionState, candidate_id: str) -> str | None:
    evidence_ids = {
        item.evidence_id
        for item in state.evidences
        if candidate_id in item.candidate_references
    }
    event_ids = {
        event.event_id
        for event in state.events
        if any(reference in evidence_ids for reference in event.evidence_references)
    }
    if len(event_ids) == 1:
        return next(iter(event_ids))
    return None


def _primary_for_signature(
    state: RegionState,
    *,
    event_id: str,
    signature: str | None,
) -> str | None:
    if signature is None:
        return None
    event = next((item for item in state.events if item.event_id == event_id), None)
    event_evidence = set(event.evidence_references) if event is not None else set()
    matches = sorted(
        item.evidence_id
        for item in state.evidences
        if item.evidence_id in event_evidence
        and item.content_signature == signature
        and item.independent_confirmation
    )
    return matches[0] if matches else None


def cluster_candidates(
    inputs: Sequence[ClusterInput],
    *,
    state: RegionState,
) -> ClusteringResult:
    """Create Evidence and EventDraft values using deterministic, conservative rules."""

    if type(state) is not RegionState:
        raise ClusteringError("state must be a RegionState")
    if type(inputs) not in {tuple, list}:
        raise ClusteringError("inputs must be a list or tuple of ClusterInput values")
    if any(type(item) is not ClusterInput for item in inputs):
        raise ClusteringError("inputs contains a non-ClusterInput value")

    for item in inputs:
        if item.candidate.region is not state.region:
            raise ClusteringError(
                "Region boundary forbids Global and China Candidates in one clustering run"
            )
        if not _candidate_is_registered(state, item.candidate):
            raise ClusteringError(
                "all Candidates must be registered in Region state before clustering"
            )

    priority_rank = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    source_type_rank = {"Official": 0, "Person": 1, "Media": 2, "Community": 3}
    credibility_rank = {"High": 0, "Medium": 1, "Low": 2}
    ordered_inputs = sorted(
        inputs,
        key=lambda item: (
            priority_rank[item.candidate.source_priority.value],
            source_type_rank[item.candidate.source_type.value],
            credibility_rank[item.candidate.source_credibility.value],
            item.candidate.candidate_id,
            item.relation.value,
        ),
    )

    current_state = state
    evidences: dict[str, Evidence] = {}
    near_links: dict[tuple[str, str], NearDuplicateLink] = {}
    event_candidates: dict[str, list[CandidateItem]] = {}
    event_descriptors: dict[str, list[EventDescriptor]] = {}

    for item in ordered_inputs:
        candidate = item.candidate
        event_id = stable_event_id(candidate, item.descriptor)
        if item.descriptor is None:
            existing_event_id = _existing_event_for_candidate(
                current_state,
                candidate.candidate_id,
            )
            event_id = existing_event_id or event_id

        evidence_id = stable_evidence_id(candidate, event_id=event_id, relation=item.relation)
        existing_evidence = next(
            (entry for entry in current_state.evidences if entry.evidence_id == evidence_id),
            None,
        )
        if existing_evidence is not None:
            evidence, current_state = build_evidence(
                candidate,
                event_id=event_id,
                state=current_state,
                descriptor=item.descriptor,
                relation=item.relation,
                independent_confirmation=existing_evidence.independent_confirmation,
                duplicate_of_evidence_id=existing_evidence.duplicate_of_evidence_id,
            )
        else:
            signature = near_duplicate_signature(candidate)
            duplicate_of = _primary_for_signature(
                current_state,
                event_id=event_id,
                signature=signature,
            )
            evidence, current_state = build_evidence(
                candidate,
                event_id=event_id,
                state=current_state,
                descriptor=item.descriptor,
                relation=item.relation,
                independent_confirmation=duplicate_of is None,
                duplicate_of_evidence_id=duplicate_of,
            )
        evidence_record = next(
            entry
            for entry in current_state.evidences
            if entry.evidence_id == evidence.evidence_id
        )
        if evidence_record.duplicate_of_evidence_id is not None:
            primary_state = next(
                entry
                for entry in current_state.evidences
                if entry.evidence_id == evidence_record.duplicate_of_evidence_id
            )
            link = NearDuplicateLink(
                primary_evidence_id=evidence_record.duplicate_of_evidence_id,
                duplicate_evidence_id=evidence.evidence_id,
                candidate_references=(
                    primary_state.candidate_references[0],
                    candidate.candidate_id,
                ),
            )
            near_links[(link.primary_evidence_id, link.duplicate_evidence_id)] = link

        evidences[evidence.evidence_id] = evidence
        existing_event = next(
            (entry for entry in current_state.events if entry.event_id == event_id),
            None,
        )
        if existing_event is None:
            current_state = register_event_state(
                current_state,
                event_id=event_id,
                evidence_references=(evidence.evidence_id,),
            )
        else:
            current_state = append_event_evidence(
                current_state,
                event_id=event_id,
                evidence_references=(evidence.evidence_id,),
            )
        event_candidates.setdefault(event_id, []).append(candidate)
        if item.descriptor is not None:
            event_descriptors.setdefault(event_id, []).append(item.descriptor)

    event_drafts = []
    for event_id in sorted(event_candidates):
        candidates = event_candidates[event_id]
        event_state = next(item for item in current_state.events if item.event_id == event_id)
        evidence_state = {
            item.evidence_id: item
            for item in current_state.evidences
            if item.evidence_id in event_state.evidence_references
        }
        categories = sorted(
            {
                category
                for descriptor in event_descriptors.get(event_id, [])
                for category in descriptor.technical_categories
            },
            key=lambda item: item.value,
        )
        tags = sorted(
            {tag for candidate in candidates for tag in candidate.eterna_tags},
            key=lambda item: item.value,
        )
        canonical_title = min(
            (candidate.title for candidate in candidates),
            key=lambda value: (_normalized_text(value), value),
        )
        event_drafts.append(
            EventDraft(
                event_id=event_id,
                canonical_title=canonical_title,
                region=state.region,
                event_anchor=(
                    event_descriptors[event_id][0].event_anchor
                    if event_descriptors.get(event_id)
                    else None
                ),
                technical_categories=tuple(categories),
                first_seen_at=min(candidate.first_seen_at for candidate in candidates),
                last_seen_at=max(candidate.last_seen_at for candidate in candidates),
                evidence_references=event_state.evidence_references,
                independent_evidence_references=tuple(
                    reference
                    for reference in event_state.evidence_references
                    if evidence_state[reference].independent_confirmation
                ),
                eterna_tags=tuple(tags),
            )
        )

    return ClusteringResult(
        evidences=tuple(evidences[key] for key in sorted(evidences)),
        event_drafts=tuple(event_drafts),
        near_duplicates=tuple(near_links[key] for key in sorted(near_links)),
        state=current_state,
    )


__all__ = [
    "ClusterInput",
    "ClusteringError",
    "ClusteringResult",
    "EventDescriptor",
    "EventDraft",
    "NearDuplicateLink",
    "build_evidence",
    "cluster_candidates",
    "near_duplicate_signature",
    "stable_event_id",
    "stable_evidence_id",
]
