# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
"""4.11: the milestone this whole design exists for, demonstrated rather
than asserted. A mid-item CapacityRejected kills engine A; work continues
on engine B; every closable id open when A died is present, verbatim, in
B's first prompt, and the no-loss gate proves zero items were dropped."""

from datetime import UTC, datetime
from pathlib import Path
from uuid import UUID, uuid4

import asyncpg

from vibey.application.dto import RunSpec
from vibey.application.handoff_orchestration import produce_and_verify_handoff
from vibey.application.ports import BriefProducer
from vibey.application.seed_prompt import closable_ids_in_brief, render_seed_prompt
from vibey.domain.briefing import build_deterministic_brief
from vibey.domain.capacity import CreditsExhausted
from vibey.domain.effort import Effort
from vibey.domain.engine import IsolationLevel
from vibey.domain.handoff import BudgetSnapshot, GateMode, HandoffBrief, Violation
from vibey.domain.phase import Phase
from vibey.infrastructure.db.ledger_repository import PostgresLedgerRepository
from vibey.infrastructure.engines.descriptors import CLAUDELOOP, CODEXLOOP
from vibey.infrastructure.engines.scripted import ScriptedEngine
from vibey.infrastructure.engines.tailer import translate_run_iter
from vibey.infrastructure.ledger.full_ledger_writer import write_full_ledger

NOW = datetime(2026, 1, 1, tzinfo=UTC)


class _DeterministicFloorProducer:
    """Stands in for handoff.produce when the outgoing engine is dead: no
    engine can be asked for a brief, so vibey falls back to its own
    template, generated directly from the same projections the gate
    checks (handoff-protocol.md §6.5, option 4 -- "the floor")."""

    def __init__(self, brief: HandoffBrief) -> None:
        self._brief = brief

    async def produce(
        self, *, attempt: int, mode: GateMode, violations: tuple[Violation, ...]
    ) -> HandoffBrief:
        return self._brief


async def test_forced_rotation_after_engine_a_dies_carries_every_open_item_to_b(
    migrated_pool: asyncpg.Pool, project_id: UUID, tmp_path: Path
) -> None:
    ledger_repo = PostgresLedgerRepository(migrated_pool)

    # --- Engine A: 40 turns into an outbox relay, then credits run out ----
    engine_a = ScriptedEngine(
        descriptor=CLAUDELOOP,
        base_dir=tmp_path / "engine-a",
        script=[
            {"kind": "SessionSeeded", "at": NOW.isoformat(), "payload": {"seed_digest": "d1"}},
            {
                "kind": "QuestionAsked",
                "at": NOW.isoformat(),
                "payload": {
                    "question_id": "q_7f3a",
                    "text": "Should retries be capped or unbounded?",
                    "blocking": False,
                },
            },
            {
                "kind": "DecisionRecorded",
                "at": NOW.isoformat(),
                "payload": {
                    "decision_id": "d_44a1",
                    "title": "Outbox over 2PC",
                    "choice": "transactional outbox",
                    "rationale": "single local transaction; no XA coordinator",
                    "alternatives": ["two-phase commit"],
                },
            },
            {
                "kind": "AssumptionStated",
                "at": NOW.isoformat(),
                "payload": {
                    "assumption_id": "a_0c2f",
                    "text": "Postgres is the only write DB",
                    "confidence": "high",
                },
            },
            {
                "kind": "FindingRaised",
                "at": NOW.isoformat(),
                "payload": {
                    "finding_id": "f_21c9",
                    "severity": "medium",
                    "text": "relay integration test flakes on CI",
                },
            },
            {
                "kind": "CapacityRejected",
                "at": NOW.isoformat(),
                "payload": {"capacity_state": "CreditsExhausted", "can_purchase": True},
            },
        ],
    )
    handle_a = await engine_a.start(
        RunSpec(
            run_id=uuid4(),
            worktree_path=tmp_path / "worktree-a",
            prompt="implement the outbox relay",
            effort=Effort.LOW,
            isolation=IsolationLevel.WORKTREE,
        )
    )

    # Engine A is now dead: credits exhausted, cannot be asked for a brief.
    assert isinstance(
        engine_a.classify({"capacity": {"state": "credits_exhausted"}}), CreditsExhausted
    )

    correlation_id = uuid4()
    drafts = [
        d
        async for d in translate_run_iter(
            engine_a.tail(handle_a),
            project_id=project_id,
            cycle=1,
            phase=Phase.BUILD,
            engine_id=CLAUDELOOP.engine_id,
            job_id=None,
            correlation_id=correlation_id,
        )
    ]
    appended = [await ledger_repo.append(d) for d in drafts]
    assert len(appended) == len(drafts)

    ledger_events = await ledger_repo.all_for_project(project_id)
    assert len(ledger_events) == len(drafts)

    # --- The floor: vibey produces a brief itself, no model involved ------
    floor_brief = build_deterministic_brief(ledger_events)
    ledger_ref = write_full_ledger(
        ledger_events, tmp_path / "worktree-b" / ".vibey" / "handoff" / "ledger.jsonl"
    )
    zero_budget = BudgetSnapshot(turns_spent=0, dollars_spent=0.0, max_turns=None, max_dollars=None)

    producer: BriefProducer = _DeterministicFloorProducer(floor_brief)
    outcome = await produce_and_verify_handoff(
        producer=producer,
        ledger=ledger_events,
        ref=ledger_ref,
        budget=zero_budget,
    )

    # The requirement, demonstrated: the gate passed on the first attempt,
    # because the floor brief is lossless by construction.
    assert outcome.result.ok, outcome.result.violations
    assert outcome.result.mode is GateMode.STRICT
    assert outcome.result.attempts == 1

    # --- Work continues on engine B ----------------------------------------
    seed_prompt = render_seed_prompt(outcome.brief)
    expected_ids = {"q_7f3a", "d_44a1", "a_0c2f", "f_21c9"}
    assert expected_ids <= closable_ids_in_brief(outcome.brief)
    for item_id in expected_ids:
        assert item_id in seed_prompt, f"{item_id} missing from B's first prompt"

    engine_b = ScriptedEngine(descriptor=CODEXLOOP, base_dir=tmp_path / "engine-b")
    handle_b = await engine_b.start(
        RunSpec(
            run_id=uuid4(),
            worktree_path=tmp_path / "worktree-b",
            prompt=seed_prompt,
            effort=Effort.LOW,
            isolation=IsolationLevel.WORKTREE,
        )
    )
    assert handle_b.run_dir.exists()

    # --- Zero dropped items, checked independently of the gate's own ok ---
    from vibey.domain.projections import build_open_items

    open_before = build_open_items(ledger_events)
    still_carried = closable_ids_in_brief(outcome.brief)
    for qid in open_before.questions:
        assert qid in still_carried
    for did in open_before.decisions:
        assert did in still_carried
    for aid in open_before.assumptions:
        assert aid in still_carried
    for fid in open_before.findings:
        assert fid in still_carried


async def test_forced_rotation_asserts_result_would_fail_if_an_item_were_dropped(
    migrated_pool: asyncpg.Pool, project_id: UUID, tmp_path: Path
) -> None:
    """Negative control: a hand-broken brief that drops the finding is
    caught by the gate rather than silently accepted -- proof the passing
    result above is a real property, not an artifact of a gate that always
    says yes."""
    from vibey.domain.handoff import LedgerRef
    from vibey.domain.ledger import digest_range

    ledger_repo = PostgresLedgerRepository(migrated_pool)
    engine_a = ScriptedEngine(
        descriptor=CLAUDELOOP,
        base_dir=tmp_path / "engine-a",
        script=[
            {
                "kind": "FindingRaised",
                "at": NOW.isoformat(),
                "payload": {"finding_id": "f_drop_me", "severity": "high", "text": "flaky test"},
            },
        ],
    )
    handle_a = await engine_a.start(
        RunSpec(
            run_id=uuid4(),
            worktree_path=tmp_path / "worktree-a",
            prompt="x",
            effort=Effort.LOW,
            isolation=IsolationLevel.WORKTREE,
        )
    )
    correlation_id = uuid4()
    drafts = [
        d
        async for d in translate_run_iter(
            engine_a.tail(handle_a),
            project_id=project_id,
            cycle=1,
            phase=Phase.BUILD,
            engine_id=CLAUDELOOP.engine_id,
            job_id=None,
            correlation_id=correlation_id,
        )
    ]
    for d in drafts:
        await ledger_repo.append(d)
    ledger_events = await ledger_repo.all_for_project(project_id)

    broken_brief = build_deterministic_brief([])  # built from an empty range -- drops the finding
    ref = LedgerRef(
        uri="u",
        from_seq=ledger_events[0].seq,
        to_seq=ledger_events[-1].seq,
        event_count=len(ledger_events),
        digest=digest_range(ledger_events),
    )

    producer: BriefProducer = _DeterministicFloorProducer(broken_brief)
    outcome = await produce_and_verify_handoff(
        producer=producer,
        ledger=ledger_events,
        ref=ref,
        budget=BudgetSnapshot(turns_spent=0, dollars_spent=0.0, max_turns=None, max_dollars=None),
    )

    assert not outcome.result.ok or outcome.result.mode is GateMode.FULL_TRANSCRIPT
    if outcome.result.mode is GateMode.STRICT:
        assert any(v.item_id == "f_drop_me" for v in outcome.result.violations)
