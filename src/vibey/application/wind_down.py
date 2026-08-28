# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://hire.adam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
"""Wind-down orchestration: what happens when a build engine exits with
EXIT_CODE_WIND_DOWN instead of finishing (handoff-protocol.md §3, §6).

The pipeline, in order, is the whole point of the no-loss design:

1. Load this cycle's BUILD ledger range and write it, complete and
   verbatim, to ``<worktree>/.vibey/handoff/ledger.jsonl`` -- the
   incoming engine always gets the full conversation being handed off,
   never just the brief.
2. Produce a brief with the deterministic floor producer (the outgoing
   engine is winding down; asking it for prose is optional quality, the
   floor is guaranteed correctness) and verify it through the gate
   escalation ladder (STRICT x3 -> FULL_TRANSCRIPT -> HUMAN).
3. A gate that ends in HUMAN parks the job -- a handoff that fails the
   no-loss gate is never a silent partial.
4. Bound the livelock (TooManyWindDowns -> park) and select the next
   engine via RotationHandoffService.
5. Persist the HandoffEnvelope, then enqueue the follow-up
   ``build.implement`` whose payload carries the rendered seed prompt and
   whose requirement excludes the engine that wound down.

The winding-down job itself settles Success: wind-down is a graceful
capacity event, not a failure, and must not burn the escalation ladder.
"""

from collections.abc import Callable, Sequence
from pathlib import Path
from uuid import uuid4

from vibey.application.brief_producer import DeterministicBriefProducer
from vibey.application.dto import EnqueueRequest, HumanGateRequest, JobRecord, StopSummary
from vibey.application.handoff_orchestration import produce_and_verify_handoff
from vibey.application.interfaces import HandoffStore, LedgerReader
from vibey.application.ports import Clock, JobRepository
from vibey.application.rotation_handoff import RotationHandoffService, TooManyWindDowns
from vibey.application.seed_prompt import render_seed_prompt
from vibey.application.worker import Outcome, Park, Success
from vibey.domain.effort import Effort
from vibey.domain.engine import EngineId, JobRequirement
from vibey.domain.handoff import (
    BudgetSnapshot,
    HandoffEnvelope,
    HandoffReason,
    LedgerRef,
    RepoState,
)
from vibey.domain.job import idempotency_key
from vibey.domain.ledger import EventKind, LedgerEvent
from vibey.domain.phase import Phase

LedgerWriter = Callable[[Sequence[LedgerEvent], Path], LedgerRef]
"""Writes the full ledger to a file and returns its range reference --
infrastructure's ``write_full_ledger`` satisfies this shape."""


def _budget_from_events(events: Sequence[LedgerEvent]) -> BudgetSnapshot:
    """R8 (budget carry) requires the envelope's snapshot to equal the
    ledger's own BUDGET_SPENT sums, so derive it from the same events the
    gate will check rather than trusting any separate counter."""
    dollars = 0.0
    turns = 0
    for event in events:
        if event.kind is EventKind.BUDGET_SPENT:
            raw_dollars = event.payload.get("dollars", 0.0)
            raw_turns = event.payload.get("turns", 0)
            if isinstance(raw_dollars, int | float):
                dollars += float(raw_dollars)
            if isinstance(raw_turns, int):
                turns += raw_turns
    return BudgetSnapshot(
        turns_spent=turns, dollars_spent=dollars, max_turns=None, max_dollars=None
    )


class WindDownOrchestrator:
    def __init__(
        self,
        *,
        ledger: LedgerReader,
        handoff_service: RotationHandoffService,
        handoffs: HandoffStore,
        jobs: JobRepository,
        clock: Clock,
        write_ledger: LedgerWriter,
        objective: str = "See the accepted spec in .vibey/context/spec.md.",
        spec_constraints: Sequence[str] = (),
    ) -> None:
        self._ledger = ledger
        self._handoff_service = handoff_service
        self._handoffs = handoffs
        self._jobs = jobs
        self._clock = clock
        self._write_ledger = write_ledger
        self._objective = objective
        self._spec_constraints = tuple(spec_constraints)

    async def execute(
        self,
        *,
        job: JobRecord,
        worktree_path: Path,
        engine_id: EngineId,
        effort: Effort,
        stop: StopSummary,
    ) -> Outcome:
        raw_count = job.payload.get("wind_down_count", 0)
        wind_down_count = raw_count if isinstance(raw_count, int) else 0
        work_item_id = job.work_item_id or ""

        # The handoff hands off THIS cycle's BUILD conversation. Other
        # phases speak their own payload dialects (design's QuestionAsked
        # carries item_id/stage, closed by human gates, not by handoff
        # closables), and earlier cycles were sealed by their own reviews
        # -- mixing them into the gate would check the wrong closures.
        events = tuple(
            event
            for event in await self._ledger.all_for_project(job.project_id)
            if event.cycle == job.cycle and event.phase is Phase.BUILD
        )
        budget = _budget_from_events(events)
        ref = self._write_ledger(events, worktree_path / ".vibey" / "handoff" / "ledger.jsonl")

        producer = DeterministicBriefProducer(
            events=events,
            objective=self._objective,
            spec_constraints=self._spec_constraints,
            extra_remaining=stop.remaining_work,
        )
        outcome = await produce_and_verify_handoff(
            producer=producer,
            ledger=events,
            ref=ref,
            budget=budget,
            spec_constraints=self._spec_constraints,
        )
        if not outcome.result.ok:
            violations = "; ".join(v.detail for v in outcome.result.violations) or "unknown"
            return Park(
                HumanGateRequest(
                    kind="handoff_gate_failed",
                    prompt=(
                        f"work item {work_item_id!r} wound down on {engine_id.value} but the "
                        f"no-loss gate failed even in full-transcript mode: {violations}. "
                        "How should the handoff proceed?"
                    ),
                )
            )

        try:
            decision = await self._handoff_service.handle_wind_down(
                project_id=job.project_id,
                work_item_id=work_item_id,
                current_engine=engine_id,
                requirement=JobRequirement(effort=effort),
                wind_down_count=wind_down_count,
                ledger_snapshot={"remaining_work": [item.text for item in outcome.brief.remaining]},
                brief=outcome.brief,
            )
        except TooManyWindDowns as exc:
            return Park(HumanGateRequest(kind="too_many_wind_downs", prompt=str(exc)))

        envelope = HandoffEnvelope(
            schema_version=1,
            handoff_id=uuid4(),
            project_id=job.project_id,
            cycle=job.cycle,
            phase=Phase.BUILD,
            from_engine=engine_id,
            to_engine=decision.next_engine,
            reason=HandoffReason.ROTATION,
            produced_at=self._clock.now(),
            brief=outcome.brief,
            repo_state=RepoState(
                branch="",
                head_sha="",
                worktree_path=str(worktree_path),
                dirty_paths=(),
                last_savepoint=None,
                integration_branch=None,
            ),
            ledger_ref=ref,
            budget=budget,
            gate=outcome.result,
        )
        await self._handoffs.record(envelope)

        seed_prompt = render_seed_prompt(outcome.brief)
        await self._jobs.enqueue(
            EnqueueRequest(
                project_id=job.project_id,
                cycle=job.cycle,
                phase=Phase.BUILD,
                kind="build.implement",
                idempotency_key=idempotency_key(
                    job.project_id,
                    job.cycle,
                    "build.implement",
                    f"{work_item_id}:wind-down:{decision.wind_down_count}",
                ),
                work_item_id=job.work_item_id,
                payload={
                    **job.payload,
                    "seed_prompt": seed_prompt,
                    "wind_down_count": decision.wind_down_count,
                    "previous_engine_id": engine_id.value,
                },
                requirement={"excluded_engine_ids": (engine_id.value,)},
            )
        )
        return Success(
            {
                "work_item_id": work_item_id,
                "wind_down": True,
                "handoff_id": str(envelope.handoff_id),
                "next_engine": decision.next_engine.value,
            }
        )
