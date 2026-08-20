"""Durable ``build.implement`` handler (M6 task 6.4): engine selection
(single injected adapter for now -- full rotation wiring is a later task,
same position design.interview's "interviewer" was in after M5), worktree
creation, agent-surface provisioning, run, tail, and ledger persistence.

Effort escalates by attempt using the same pure ladder domain/effort.py
built in M1 -- an exhausted ladder parks for a human gate rather than
failing outright, since attempt 7 means autonomous escalation has nothing
left to try.

Forced rotation (task 6.6): when an attempt's effort crosses a tier
boundary (attempts 3 and 5 per BUILD_LADDER), ``forces_rotation`` returns
True and the handler enforces that the injected engine differs from the
previous attempt's engine.  The constraint is checked, not performed --
``BuildImplementHandler`` receives a single ``EngineAdapter``, so real
rotation (selecting from a pool) is a caller responsibility not yet built
in BUILD.  This is the same "documented, not faked" approach
``build.verify``'s must-differ-from-implementer constraint uses.

On success, enqueues build.verify (task 6.5) against the same worktree, so
implement never leaves a completed item with no next step queued -- the same
pattern design_handler.py's follow-up enqueue and visual_handler.py's
inventory->plan chaining use.
"""

from collections.abc import Mapping
from dataclasses import replace
from datetime import timedelta
from uuid import uuid4

from vibey.application.build_engine_run import BuildLedger, run_and_record
from vibey.application.build_verify_handler import granted_amount, granted_limit
from vibey.application.dto import EnqueueRequest, HumanGateRequest, JobRecord, RunSpec
from vibey.application.interfaces import (
    BudgetSource,
    BuildProvisioner,
    BuildWorktrees,
)
from vibey.application.ports import Clock, EngineAdapter, HumanGateRepository, JobRepository
from vibey.application.wind_down import WindDownOrchestrator
from vibey.application.worker import Defer, Failure, Outcome, Park, Success
from vibey.domain.effort import (
    BUILD_LADDER_EXHAUSTED,
    PHASE_BASE_EFFORT,
    effort_for_attempt,
    forces_rotation,
)
from vibey.domain.engine import EXIT_CODE_WIND_DOWN, IsolationLevel
from vibey.domain.errors import EscalationExhausted
from vibey.domain.job import FailureClass, idempotency_key
from vibey.domain.phase import Phase
from vibey.domain.provision import ProvisionSpec

_EMPTY_PROVISION_SPEC = ProvisionSpec((), ())


class BuildImplementHandler:
    def __init__(
        self,
        *,
        worktrees: BuildWorktrees,
        provisioner: BuildProvisioner,
        engine: EngineAdapter,
        ledger: BuildLedger,
        jobs: JobRepository,
        clock: Clock,
        provision_spec: ProvisionSpec = _EMPTY_PROVISION_SPEC,
        capacity_backoff: timedelta = timedelta(minutes=5),
        budget_source: BudgetSource | None = None,
        wind_down: WindDownOrchestrator | None = None,
        human_gates: HumanGateRepository | None = None,
    ) -> None:
        self._worktrees = worktrees
        self._provisioner = provisioner
        self._engine = engine
        self._ledger = ledger
        self._jobs = jobs
        self._clock = clock
        self._provision_spec = provision_spec
        self._capacity_backoff = capacity_backoff
        self._budget_source = budget_source
        self._wind_down = wind_down
        self._human_gates = human_gates

    async def handle(self, job: JobRecord) -> Outcome:
        if job.kind != "build.implement":
            return Failure(FailureClass.VIBEY, "expected build.implement job")
        if job.work_item_id is None:
            return Failure(FailureClass.VIBEY, "build.implement job is missing work_item_id")

        base_effort = PHASE_BASE_EFFORT[Phase.BUILD]
        try:
            effort = effort_for_attempt(base_effort, job.attempts)
        except EscalationExhausted:
            # An answered gate can extend the ladder: further attempts run
            # at the ladder's top effort until the granted bound. Without
            # this contract the park was a dead end -- answering un-parked
            # the job, attempts were still past the ladder, and it parked
            # again forever.
            granted = None
            if self._human_gates is not None:
                gate = await self._human_gates.latest_for_job(job.id)
                if gate is not None and gate.answer is not None:
                    granted = granted_limit(gate.answer, "max_attempts")
            if granted is None or job.attempts > granted:
                return Park(
                    HumanGateRequest(
                        kind="escalation_exhausted",
                        prompt=(
                            f"work item {job.work_item_id!r} exhausted the escalation "
                            f"ladder after {job.attempts} attempts. Grant more by "
                            f"answering --raw '{{\"max_attempts\": {job.attempts + 3}}}' "
                            "(they run at the ladder's top effort), or fix the item by "
                            "hand and answer anything to let the next verify pass."
                        ),
                    )
                )
            effort = effort_for_attempt(base_effort, BUILD_LADDER_EXHAUSTED)

        if self._budget_source is not None:
            budget = await self._budget_source.current(job.project_id, job.cycle)
            if budget.any_exhausted and self._human_gates is not None:
                # An answered budget gate can raise the caps -- otherwise
                # the park is a dead end (retrying re-trips it forever).
                gate = await self._human_gates.latest_for_job(job.id)
                if gate is not None and gate.answer is not None:
                    dollars = granted_amount(gate.answer, "max_dollars")
                    turns = granted_limit(gate.answer, "max_turns")
                    budget = replace(
                        budget,
                        max_dollars=dollars if dollars is not None else budget.max_dollars,
                        max_turns=turns if turns is not None else budget.max_turns,
                    )
            if budget.any_exhausted:
                # The runaway brake: no engine session starts once the
                # cycle's ledger-recorded spend crosses its cap. The repair
                # storms burned real money because this check didn't exist.
                cap = f"${budget.max_dollars:.2f}" if budget.max_dollars is not None else "-"
                return Park(
                    HumanGateRequest(
                        kind="budget_exhausted",
                        prompt=(
                            f"cycle budget exhausted: ${budget.dollars_spent:.2f} spent "
                            f"of {cap} cap ({budget.turns_spent} turns). Raise the cap "
                            'by answering --raw \'{"max_dollars": '
                            f"{budget.dollars_spent + 10:.0f}}}', or stop here."
                        ),
                    )
                )
            if job.attempts > 1:
                projected = job.payload.get("projected_cost_per_attempt")
                if isinstance(projected, int | float) and budget.would_exceed(float(projected)):
                    cap = f"${budget.max_dollars:.2f}" if budget.max_dollars is not None else "?"
                    return Park(
                        HumanGateRequest(
                            kind="budget_exhausted",
                            prompt=(
                                f"work item {job.work_item_id!r} would exceed the cycle "
                                f"budget (${budget.dollars_spent:.2f} spent of "
                                f"{cap} cap) with projected cost "
                                f"${float(projected):.2f} for attempt {job.attempts}"
                            ),
                        )
                    )

        previous_engine_id = job.payload.get("previous_engine_id")
        if previous_engine_id is not None and job.attempts > 1:
            # Clamp: granted attempts past the ladder all sit at its top.
            previous_effort = effort_for_attempt(
                base_effort, min(job.attempts - 1, BUILD_LADDER_EXHAUSTED)
            )
            if forces_rotation(previous_effort, effort):
                current_id = self._engine.descriptor.engine_id.value
                if current_id == previous_engine_id:
                    return Failure(
                        FailureClass.VIBEY,
                        f"forced rotation required at attempt {job.attempts} "
                        f"but engine {current_id!r} matches the previous attempt",
                    )

        base_ref = str(job.payload.get("base_ref", "HEAD"))
        worktree_path = await self._worktrees.create(job.work_item_id, base_ref=base_ref)
        await self._provisioner.provision(worktree_path, self._provision_spec)

        run_id = uuid4()
        handle = await self._engine.start(
            RunSpec(
                run_id=run_id,
                worktree_path=worktree_path,
                prompt=_render_prompt(job.work_item_id, job.payload),
                effort=effort,
                isolation=IsolationLevel.WORKTREE,
            )
        )
        run_outcome = await run_and_record(self._engine, self._ledger, job=job, handle=handle)

        if run_outcome.capacity_rejected:
            engine_id = self._engine.descriptor.engine_id.value
            return Defer(
                retry_at=self._clock.now() + self._capacity_backoff,
                detail=f"engine {engine_id} reported capacity rejection",
                capacity=True,
            )
        if self._wind_down is not None and run_outcome.exit_code == EXIT_CODE_WIND_DOWN:
            # Graceful wind-down: stop() first so the outgoing engine's
            # final snapshot (StopSummary.remaining_work) can feed the
            # brief, then hand the whole no-loss pipeline to the
            # orchestrator. This settles Success -- wind-down must never
            # burn the escalation ladder.
            stop = await self._engine.stop(handle)
            return await self._wind_down.execute(
                job=job,
                worktree_path=worktree_path,
                engine_id=self._engine.descriptor.engine_id,
                effort=effort,
                stop=stop,
            )
        if not run_outcome.complete:
            return Failure(FailureClass.WORK, "engine run did not report completion")

        await self._jobs.enqueue(
            EnqueueRequest(
                project_id=job.project_id,
                cycle=job.cycle,
                phase=Phase.BUILD,
                kind="build.verify",
                idempotency_key=idempotency_key(
                    job.project_id, job.cycle, "build.verify", str(job.id)
                ),
                work_item_id=job.work_item_id,
                payload=job.payload,
                requirement={"implementer_engine_id": self._engine.descriptor.engine_id.value},
                depends_on=(job.id,),
            )
        )
        return Success({"work_item_id": job.work_item_id, "run_id": str(run_id)})


# Standing constraints for every engine session. Each line traces to a
# real failure from the live runs: root-level test stubs broke the shared
# suite, `pip install` mutated environments, generated files caused binary
# merge conflicts, and scratch files polluted review scans.
_HOUSE_RULES = (
    "House rules:\n"
    "- Keep every test under tests/; never create test files at the repo root.\n"
    "- Verification must pass in a clean checkout of this branch with nothing "
    "installed: no pip install, no network, no reliance on your own environment.\n"
    "- Never commit generated files (caches, coverage data, egg-info, build "
    "artifacts) or scratch notes; the deliverable files only.\n"
)


def _render_prompt(item_id: str, payload: Mapping[str, object]) -> str:
    seed = payload.get("seed_prompt")
    if isinstance(seed, str) and seed:
        # A wind-down follow-up: the seed prompt was rendered from the
        # gate-verified brief and must reach the incoming engine verbatim
        # (every closable id appears in it by construction).
        return seed
    title = str(payload.get("title", item_id))
    verification = payload.get("verification", {})
    commands = verification.get("commands", ()) if isinstance(verification, Mapping) else ()
    checklist = "\n".join(f"- {command}" for command in commands) or "- (none specified)"
    repair_detail = payload.get("repair_detail")
    repair_note = (
        f"This item's verification is FAILING. Fix the failure below, on this "
        f"branch, without weakening the checks themselves:\n{repair_detail}\n\n"
        if isinstance(repair_detail, str) and repair_detail
        else ""
    )
    return (
        f"Implement work item {item_id}: {title}\n\n"
        f"{repair_note}{_HOUSE_RULES}\nVerify your work with:\n{checklist}\n"
    )


# Re-exported for the same reason `application/ports.py` re-exports the
# interfaces package: the seam moved, the import path should not break.
__all__ = [
    "BudgetSource",
    "BuildProvisioner",
    "BuildWorktrees",
]
