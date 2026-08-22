# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
"""The append-only, vendor-neutral event ledger (ADR-0003). This module is
pure projection logic over an in-memory event sequence -- persistence lives
in infrastructure/."""

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from vibey.domain.engine import EngineId
from vibey.domain.phase import Phase


class EventKind(StrEnum):
    SESSION_SEEDED = "SessionSeeded"
    TURN_REQUESTED = "TurnRequested"
    TURN_COMPLETED = "TurnCompleted"
    TOOL_INVOKED = "ToolInvoked"
    FILE_EDITED = "FileEdited"
    VERDICT_RENDERED = "VerdictRendered"
    CAPACITY_REJECTED = "CapacityRejected"
    QUESTION_ASKED = "QuestionAsked"
    ANSWER_GIVEN = "AnswerGiven"
    DECISION_RECORDED = "DecisionRecorded"
    ASSUMPTION_STATED = "AssumptionStated"
    FINDING_RAISED = "FindingRaised"
    FINDING_RESOLVED = "FindingResolved"
    ARTIFACT_PRODUCED = "ArtifactProduced"
    SAVEPOINT_CREATED = "SavePointCreated"
    HANDOFF_INITIATED = "HandoffInitiated"
    HANDOFF_ACCEPTED = "HandoffAccepted"
    PHASE_TRANSITIONED = "PhaseTransitioned"
    BUDGET_SPENT = "BudgetSpent"
    VISUAL_DESIGN_OPTED_IN = "VisualDesignOptedIn"
    VISUAL_DESIGN_DECLINED = "VisualDesignDeclined"
    VISUAL_DESIGN_ACCEPTED = "VisualDesignAccepted"
    VISUAL_DESIGN_WAIVED = "VisualDesignWaived"
    DEPLOYMENT_OPTED_IN = "DeploymentOptedIn"
    DEPLOYMENT_DECLINED = "DeploymentDeclined"


CLOSABLE: frozenset[EventKind] = frozenset(
    {
        EventKind.QUESTION_ASKED,
        EventKind.DECISION_RECORDED,
        EventKind.ASSUMPTION_STATED,
        EventKind.FINDING_RAISED,
    }
)

CLOSES: Mapping[EventKind, EventKind] = {
    EventKind.ANSWER_GIVEN: EventKind.QUESTION_ASKED,
    EventKind.FINDING_RESOLVED: EventKind.FINDING_RAISED,
}

# The payload field carrying the id minted for each closable/closing kind.
_ID_FIELD: Mapping[EventKind, str] = {
    EventKind.QUESTION_ASKED: "question_id",
    EventKind.ANSWER_GIVEN: "question_id",
    EventKind.DECISION_RECORDED: "decision_id",
    EventKind.ASSUMPTION_STATED: "assumption_id",
    EventKind.FINDING_RAISED: "finding_id",
    EventKind.FINDING_RESOLVED: "finding_id",
}


class Provenance(StrEnum):
    TRUSTED = "trusted"
    AGENT = "agent"
    UNTRUSTED = "untrusted"


@dataclass(frozen=True, slots=True)
class LedgerEvent:
    event_id: UUID
    project_id: UUID
    cycle: int
    phase: Phase
    seq: int
    kind: EventKind
    engine_id: EngineId | None
    job_id: UUID | None
    causation_id: UUID | None
    correlation_id: UUID
    provenance: Provenance
    produced_at: datetime
    payload: Mapping[str, object]
    digest: str


def canonical_bytes(payload: Mapping[str, object]) -> bytes:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str).encode()


def digest_event(payload: Mapping[str, object]) -> str:
    return hashlib.sha256(canonical_bytes(payload)).hexdigest()


def digest_range(events: Sequence[LedgerEvent]) -> str:
    """Order-sensitive Merkle-ish fold. Rule R6 depends on this."""
    h = hashlib.sha256()
    for e in sorted(events, key=lambda x: x.seq):
        h.update(str(e.seq).encode())
        h.update(b"\x00")
        h.update(e.digest.encode())
    return h.hexdigest()


def open_items(events: Sequence[LedgerEvent], kind: EventKind) -> tuple[str, ...]:
    """Ids opened by `kind` and not yet closed or superseded. The gate's
    primitive."""
    if kind not in CLOSABLE:
        raise ValueError(f"{kind} is not a closable event kind")

    closing_kind = next((k for k, closes in CLOSES.items() if closes is kind), None)
    id_field = _ID_FIELD[kind]

    opened: dict[str, int] = {}
    for e in sorted(events, key=lambda x: x.seq):
        if e.kind is kind:
            item_id = str(e.payload[id_field])
            opened[item_id] = e.seq
            if kind is EventKind.DECISION_RECORDED:
                superseded = e.payload.get("supersedes")
                if superseded is not None:
                    opened.pop(str(superseded), None)
        elif closing_kind is not None and e.kind is closing_kind:
            item_id = str(e.payload[id_field])
            opened.pop(item_id, None)

    return tuple(sorted(opened, key=lambda item_id: opened[item_id]))
