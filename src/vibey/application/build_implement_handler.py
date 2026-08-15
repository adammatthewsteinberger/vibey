"""Durable ``build.implement`` handler (M6 task 6.4): engine selection
(single injected adapter for now -- full rotation wiring is a later task,
same position design.interview's "interviewer" was in after M5), worktree
creation, agent-surface provisioning, run, tail, and ledger persistence.

Effort escalates by attempt using the same pure ladder domain/effort.py
built in M1 (task 6.6's mechanism, wired in now because it was already
sitting there unused) -- an exhausted ladder parks for a human gate rather
than failing outright, since attempt 7 means autonomous escalation has
nothing left to try.

Translating an EngineAdapter's raw ``EngineEvent`` stream into a
``LedgerEvent`` is infrastructure/engines/tailer.py's job, which application/
must not import (the onion contract forbids it). ``BuildLedger.record``
takes the raw event and does that translation on the infrastructure side --
the same shape design_handler.py's ``DesignLedger`` port uses.
"""

from collections.abc import AsyncIterator, Mapping
from datetime import timedelta
from pathlib import Path
from typing import Protocol
from uuid import UUID, uuid4

from vibey.application.dto import EngineEvent, HumanGateRequest, JobRecord, RunSpec
from vibey.application.ports import Clock, EngineAdapter
from vibey.application.worker import Defer, Failure, Outcome, Park, Success
from vibey.domain.effort import PHASE_BASE_EFFORT, effort_for_attempt
from vibey.domain.engine import EngineId, IsolationLevel
from vibey.domain.errors import EscalationExhausted
from vibey.domain.job import FailureClass
from vibey.domain.ledger import EventKind
from vibey.domain.phase import Phase
from vibey.domain.provision import ProvisionSpec

_EMPTY_PROVISION_SPEC = ProvisionSpec((), ())


class BuildLedger(Protocol):
    async def record(
        self,
        *,
        project_id: UUID,
        cycle: int,
        job_id: UUID,
        engine_id: EngineId,
        correlation_id: UUID,
        event: EngineEvent,
    ) -> None: ...


class BuildWorktrees(Protocol):
    async def create(self, item_id: str, *, base_ref: str = "HEAD") -> Path: ...


class BuildProvisioner(Protocol):
    async def provision(self, worktree_path: Path, spec: ProvisionSpec) -> tuple[Path, ...]: ...


class BuildImplementHandler:
    def __init__(
        self,
        *,
        worktrees: BuildWorktrees,
        provisioner: BuildProvisioner,
        engine: EngineAdapter,
        ledger: BuildLedger,
        clock: Clock,
        provision_spec: ProvisionSpec = _EMPTY_PROVISION_SPEC,
        capacity_backoff: timedelta = timedelta(minutes=5),
    ) -> None:
        self._worktrees = worktrees
        self._provisioner = provisioner
        self._engine = engine
        self._ledger = ledger
        self._clock = clock
        self._provision_spec = provision_spec
        self._capacity_backoff = capacity_backoff

    async def handle(self, job: JobRecord) -> Outcome:
        if job.kind != "build.implement":
            return Failure(FailureClass.VIBEY, "expected build.implement job")
        if job.work_item_id is None:
            return Failure(FailureClass.VIBEY, "build.implement job is missing work_item_id")

        try:
            effort = effort_for_attempt(PHASE_BASE_EFFORT[Phase.BUILD], job.attempts)
        except EscalationExhausted:
            return Park(
                HumanGateRequest(
                    kind="escalation_exhausted",
                    prompt=(
                        f"work item {job.work_item_id!r} exhausted the escalation ladder "
                        f"after {job.attempts} attempts; how should it proceed?"
                    ),
                )
            )

        worktree_path = await self._worktrees.create(job.work_item_id)
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

        complete, capacity_rejected = await self._record_run(
            job, handle_events=self._engine.tail(handle)
        )

        if capacity_rejected:
            engine_id = self._engine.descriptor.engine_id.value
            return Defer(
                retry_at=self._clock.now() + self._capacity_backoff,
                detail=f"engine {engine_id} reported capacity rejection",
            )
        if not complete:
            return Failure(FailureClass.WORK, "engine run did not report completion")
        return Success({"work_item_id": job.work_item_id, "run_id": str(run_id)})

    async def _record_run(
        self, job: JobRecord, *, handle_events: AsyncIterator[EngineEvent]
    ) -> tuple[bool, bool]:
        complete = False
        capacity_rejected = False
        correlation_id = uuid4()
        async for event in handle_events:
            await self._ledger.record(
                project_id=job.project_id,
                cycle=job.cycle,
                job_id=job.id,
                engine_id=self._engine.descriptor.engine_id,
                correlation_id=correlation_id,
                event=event,
            )
            if event.kind == EventKind.VERDICT_RENDERED.value and bool(
                event.payload.get("complete")
            ):
                complete = True
            if event.kind == EventKind.CAPACITY_REJECTED.value:
                capacity_rejected = True
        return complete, capacity_rejected


def _render_prompt(item_id: str, payload: Mapping[str, object]) -> str:
    title = str(payload.get("title", item_id))
    verification = payload.get("verification", {})
    commands = verification.get("commands", ()) if isinstance(verification, Mapping) else ()
    checklist = "\n".join(f"- {command}" for command in commands) or "- (none specified)"
    return f"Implement work item {item_id}: {title}\n\nVerify your work with:\n{checklist}\n"
