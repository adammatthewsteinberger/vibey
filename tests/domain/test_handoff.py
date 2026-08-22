# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
import dataclasses
from datetime import UTC, datetime
from uuid import uuid4

from vibey.domain.engine import EngineId
from vibey.domain.handoff import (
    ArtifactRef,
    AssumptionRef,
    BudgetSnapshot,
    DecisionRef,
    GateMode,
    GateResult,
    GateRule,
    HandoffBrief,
    HandoffEnvelope,
    HandoffReason,
    LedgerRef,
    QuestionRef,
    RemainingItem,
    RepoState,
    Violation,
)
from vibey.domain.phase import Phase
from vibey.domain.review import Ambiguity, FindingRef, Severity

NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _empty_brief(**overrides: object) -> HandoffBrief:
    defaults: dict[str, object] = {
        "objective": "build the thing",
        "constraints": (),
        "decisions": (),
        "assumptions": (),
        "done": (),
        "remaining": (),
        "open_questions": (),
        "open_findings": (),
        "artifacts": (),
        "invariants": (),
        "style_rules": (),
        "next_action": "keep going",
    }
    defaults.update(overrides)
    return HandoffBrief(**defaults)  # type: ignore[arg-type]


def test_handoff_brief_constructs_with_populated_refs() -> None:
    brief = _empty_brief(
        constraints=("must work offline",),
        decisions=(DecisionRef("d1", "outbox over 2PC"),),
        assumptions=(AssumptionRef("a1", "postgres is the only write db"),),
        remaining=(RemainingItem("wire retry policy", item_id="r1"),),
        open_questions=(QuestionRef("q1", "capped or unbounded?", blocking=False),),
        open_findings=(FindingRef("f1", Severity.HIGH, Ambiguity.NEEDS_CLARIFICATION),),
        artifacts=(ArtifactRef("art1", "migrations/007_outbox.sql"),),
    )

    assert brief.constraints == ("must work offline",)
    assert brief.decisions[0].decision_id == "d1"
    assert brief.open_findings[0].severity is Severity.HIGH


def test_gate_result_ok_true_has_no_violations_by_convention() -> None:
    result = GateResult(
        ok=True,
        mode=GateMode.STRICT,
        attempts=1,
        violations=(),
        rules_run=tuple(GateRule),
    )
    assert result.ok is True
    assert result.violations == ()


def test_gate_result_violation_carries_rule_and_item() -> None:
    violation = Violation(rule=GateRule.R2_QUESTIONS, item_id="q1", detail="missing")
    result = GateResult(
        ok=False,
        mode=GateMode.STRICT,
        attempts=1,
        violations=(violation,),
        rules_run=(GateRule.R2_QUESTIONS,),
    )
    assert result.violations[0].item_id == "q1"


def test_full_envelope_constructs_and_round_trips_via_replace() -> None:
    budget = BudgetSnapshot(turns_spent=5, dollars_spent=1.5, max_turns=60, max_dollars=40.0)
    envelope = HandoffEnvelope(
        schema_version=1,
        handoff_id=uuid4(),
        project_id=uuid4(),
        cycle=1,
        phase=Phase.BUILD,
        from_engine=EngineId.CLAUDELOOP,
        to_engine=EngineId.CODEXLOOP,
        reason=HandoffReason.CAPACITY,
        produced_at=NOW,
        brief=_empty_brief(),
        repo_state=RepoState(
            branch="vibey/c1/item-001",
            head_sha="deadbeef",
            worktree_path=".vibey/worktrees/c1-item-001",
            dirty_paths=(),
            last_savepoint="deadbeef",
            integration_branch="vibey/c1/integration",
        ),
        ledger_ref=LedgerRef(
            uri="handoff/ledger.jsonl", from_seq=1, to_seq=10, event_count=10, digest="abc"
        ),
        budget=budget,
        gate=GateResult(ok=True, mode=GateMode.STRICT, attempts=1, violations=(), rules_run=()),
    )

    rotated = dataclasses.replace(envelope, to_engine=EngineId.CURSORLOOP)

    assert envelope.to_engine is EngineId.CODEXLOOP
    assert rotated.to_engine is EngineId.CURSORLOOP
    assert rotated.brief == envelope.brief  # unaffected fields survive the replace


def test_envelope_from_engine_none_when_synthesized() -> None:
    budget = BudgetSnapshot(turns_spent=0, dollars_spent=0.0, max_turns=None, max_dollars=None)
    envelope = HandoffEnvelope(
        schema_version=1,
        handoff_id=uuid4(),
        project_id=uuid4(),
        cycle=1,
        phase=Phase.BUILD,
        from_engine=None,
        to_engine=EngineId.CODEXLOOP,
        reason=HandoffReason.FAILURE,
        produced_at=NOW,
        brief=_empty_brief(),
        repo_state=RepoState(
            branch="b",
            head_sha="h",
            worktree_path="w",
            dirty_paths=(),
            last_savepoint=None,
            integration_branch=None,
        ),
        ledger_ref=LedgerRef(uri="u", from_seq=1, to_seq=1, event_count=1, digest="d"),
        budget=budget,
        gate=GateResult(ok=True, mode=GateMode.FORCED, attempts=1, violations=(), rules_run=()),
    )

    assert envelope.from_engine is None
