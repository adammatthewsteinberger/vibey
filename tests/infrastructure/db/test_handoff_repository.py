from datetime import UTC, datetime
from uuid import UUID, uuid4

import asyncpg

from vibey.domain.engine import EngineId
from vibey.domain.handoff import (
    BudgetSnapshot,
    GateMode,
    GateResult,
    GateRule,
    HandoffBrief,
    HandoffEnvelope,
    HandoffReason,
    LedgerRef,
    RepoState,
    Violation,
)
from vibey.domain.phase import Phase
from vibey.infrastructure.db.handoff_repository import PostgresHandoffRepository

NOW = datetime(2026, 1, 1, tzinfo=UTC)


def _empty_brief() -> HandoffBrief:
    return HandoffBrief(
        objective="o",
        constraints=(),
        decisions=(),
        assumptions=(),
        done=(),
        remaining=(),
        open_questions=(),
        open_findings=(),
        artifacts=(),
        invariants=(),
        style_rules=(),
        next_action="continue",
    )


def _envelope(
    project_id: UUID,
    *,
    gate: GateResult | None = None,
    reason: HandoffReason = HandoffReason.CAPACITY,
) -> HandoffEnvelope:
    gate = gate or GateResult(
        ok=True, mode=GateMode.STRICT, attempts=1, violations=(), rules_run=tuple(GateRule)
    )
    return HandoffEnvelope(
        schema_version=1,
        handoff_id=uuid4(),
        project_id=project_id,
        cycle=1,
        phase=Phase.BUILD,
        from_engine=EngineId.CLAUDELOOP,
        to_engine=EngineId.CODEXLOOP,
        reason=reason,
        produced_at=NOW,
        brief=_empty_brief(),
        repo_state=RepoState(
            branch="vibey/c1/item-001",
            head_sha="deadbeef",
            worktree_path=".vibey/worktrees/c1-item-001",
            dirty_paths=(),
            last_savepoint="deadbeef",
            integration_branch=None,
        ),
        ledger_ref=LedgerRef(
            uri="handoff/ledger.jsonl", from_seq=1, to_seq=10, event_count=10, digest="abc"
        ),
        budget=BudgetSnapshot(turns_spent=5, dollars_spent=1.5, max_turns=60, max_dollars=40.0),
        gate=gate,
    )


async def test_record_and_get_round_trips(migrated_pool: asyncpg.Pool, project_id: UUID) -> None:
    repo = PostgresHandoffRepository(migrated_pool)
    envelope = _envelope(project_id)

    handoff_id = await repo.record(envelope)
    fetched = await repo.get(handoff_id)

    assert fetched is not None
    assert fetched["from_engine"] == "claudeloop"
    assert fetched["to_engine"] == "codexloop"
    assert fetched["gate_mode"] == "strict"
    assert fetched["accepted"] is True
    assert fetched["envelope"]["schema_version"] == 1
    assert fetched["envelope"]["reason"] == "capacity"


async def test_every_attempts_violations_are_recorded(
    migrated_pool: asyncpg.Pool, project_id: UUID
) -> None:
    repo = PostgresHandoffRepository(migrated_pool)
    violations = (
        Violation(rule=GateRule.R2_QUESTIONS, item_id="q1", detail="missing"),
        Violation(rule=GateRule.R7_ARTIFACTS, item_id="art1", detail="missing"),
    )
    failed_gate = GateResult(
        ok=False,
        mode=GateMode.FULL_TRANSCRIPT,
        attempts=4,
        violations=violations,
        rules_run=tuple(GateRule),
    )
    envelope = _envelope(project_id, gate=failed_gate)

    handoff_id = await repo.record(envelope)
    fetched = await repo.get(handoff_id)

    assert fetched is not None
    assert fetched["accepted"] is False
    assert fetched["gate_attempts"] == 4
    assert len(fetched["gate_violations"]) == 2
    assert {v["item_id"] for v in fetched["gate_violations"]} == {"q1", "art1"}


async def test_list_for_pair_is_queryable_and_ordered(
    migrated_pool: asyncpg.Pool, project_id: UUID
) -> None:
    repo = PostgresHandoffRepository(migrated_pool)
    await repo.record(_envelope(project_id, reason=HandoffReason.ROTATION))
    await repo.record(_envelope(project_id, reason=HandoffReason.ESCALATION))

    records = await repo.list_for_pair(project_id, from_engine="claudeloop", to_engine="codexloop")

    assert len(records) == 2
    assert [r["envelope"]["reason"] for r in records] == ["rotation", "escalation"]


async def test_list_for_pair_handles_synthesized_from_engine_none(
    migrated_pool: asyncpg.Pool, project_id: UUID
) -> None:
    repo = PostgresHandoffRepository(migrated_pool)
    envelope = _envelope(project_id)
    envelope = HandoffEnvelope(
        schema_version=envelope.schema_version,
        handoff_id=uuid4(),
        project_id=envelope.project_id,
        cycle=envelope.cycle,
        phase=envelope.phase,
        from_engine=None,
        to_engine=envelope.to_engine,
        reason=HandoffReason.FAILURE,
        produced_at=envelope.produced_at,
        brief=envelope.brief,
        repo_state=envelope.repo_state,
        ledger_ref=envelope.ledger_ref,
        budget=envelope.budget,
        gate=envelope.gate,
    )
    await repo.record(envelope)

    records = await repo.list_for_pair(project_id, from_engine=None, to_engine="codexloop")

    assert len(records) == 1
    assert records[0]["from_engine"] is None
