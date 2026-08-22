# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
"""The handoff envelope: the record that a conversation moved from one
engine to another, carrying proof it was verified (handoff-protocol.md)."""

from dataclasses import dataclass
from datetime import datetime
from enum import StrEnum
from uuid import UUID

from vibey.domain.budget import BudgetLedger as BudgetSnapshot
from vibey.domain.engine import EngineId
from vibey.domain.phase import Phase
from vibey.domain.review import FindingRef

__all__ = [
    "ArtifactRef",
    "AssumptionRef",
    "BudgetSnapshot",
    "DecisionRef",
    "GateMode",
    "GateResult",
    "GateRule",
    "HandoffBrief",
    "HandoffEnvelope",
    "HandoffReason",
    "LedgerRef",
    "QuestionRef",
    "RemainingItem",
    "RepoState",
    "Violation",
]


class HandoffReason(StrEnum):
    ROTATION = "rotation"
    CAPACITY = "capacity"
    ESCALATION = "escalation"
    FAILURE = "failure"
    PHASE_TRANSITION = "phase_transition"
    OPERATOR = "operator"


class GateMode(StrEnum):
    STRICT = "strict"
    FULL_TRANSCRIPT = "full_transcript"
    HUMAN = "human"
    FORCED = "forced"


class GateRule(StrEnum):
    R1_REMAINING = "R1"
    R2_QUESTIONS = "R2"
    R3_DECISIONS = "R3"
    R4_ASSUMPTIONS = "R4"
    R5_FINDINGS = "R5"
    R6_RANGE = "R6"
    R7_ARTIFACTS = "R7"
    R8_BUDGET = "R8"
    R9_CONSTRAINTS = "R9"
    R10_CONTAINMENT = "R10"


@dataclass(frozen=True, slots=True)
class Violation:
    rule: GateRule
    item_id: str | None
    detail: str


@dataclass(frozen=True, slots=True)
class GateResult:
    ok: bool
    mode: GateMode
    attempts: int
    violations: tuple[Violation, ...]
    rules_run: tuple[GateRule, ...]


@dataclass(frozen=True, slots=True)
class DecisionRef:
    decision_id: str
    restatement: str


@dataclass(frozen=True, slots=True)
class AssumptionRef:
    assumption_id: str
    restatement: str


@dataclass(frozen=True, slots=True)
class QuestionRef:
    question_id: str
    text: str
    blocking: bool


@dataclass(frozen=True, slots=True)
class RemainingItem:
    text: str
    item_id: str | None = None


@dataclass(frozen=True, slots=True)
class ArtifactRef:
    artifact_id: str
    path: str


@dataclass(frozen=True, slots=True)
class HandoffBrief:
    objective: str
    constraints: tuple[str, ...]
    decisions: tuple[DecisionRef, ...]
    assumptions: tuple[AssumptionRef, ...]
    done: tuple[str, ...]
    remaining: tuple[RemainingItem, ...]
    open_questions: tuple[QuestionRef, ...]
    open_findings: tuple[FindingRef, ...]
    artifacts: tuple[ArtifactRef, ...]
    invariants: tuple[str, ...]
    style_rules: tuple[str, ...]
    next_action: str


@dataclass(frozen=True, slots=True)
class LedgerRef:
    uri: str
    from_seq: int
    to_seq: int
    event_count: int
    digest: str


@dataclass(frozen=True, slots=True)
class RepoState:
    branch: str
    head_sha: str
    worktree_path: str
    dirty_paths: tuple[str, ...]
    last_savepoint: str | None
    integration_branch: str | None


@dataclass(frozen=True, slots=True)
class HandoffEnvelope:
    schema_version: int
    handoff_id: UUID
    project_id: UUID
    cycle: int
    phase: Phase
    from_engine: EngineId | None
    to_engine: EngineId
    reason: HandoffReason
    produced_at: datetime
    brief: HandoffBrief
    repo_state: RepoState
    ledger_ref: LedgerRef
    budget: BudgetSnapshot
    gate: GateResult
