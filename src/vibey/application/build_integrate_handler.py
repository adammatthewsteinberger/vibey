"""Durable ``build.integrate`` handler (M6 task 6.8): merges one verified
work item's branch into the shared integration branch, runs the full gate
suite against the merged result, and never rolls back the whole phase for
one bad item -- a merge conflict or a post-merge gate failure produces a
``FindingRaised`` event and a targeted repair ``build.implement`` job based
on the integration branch's current head, not a rollback of everything
(phase-protocols.md section 2.4).

Concurrency: concurrent ``build.integrate`` jobs for the same
(project, cycle) are serialized through the optional ``lock``
(IntegrationLock -- a Postgres advisory lock in production). Contention
defers the job for a short retry instead of blocking the worker; the lock
is released in a ``finally`` so a crashed merge can never wedge the
branch for every other worker.
"""

import contextlib
import shlex
from collections.abc import Mapping
from datetime import timedelta
from uuid import uuid4

from vibey.application.build_engine_run import BuildLedger
from vibey.application.build_verify_handler import GateRunner
from vibey.application.dto import EngineEvent, EnqueueRequest, JobRecord
from vibey.application.interfaces import (
    IntegrationBranch,
    IntegrationLock,
    MergeOutcome,
    ProjectTransitioner,
)
from vibey.application.ports import Clock, JobRepository
from vibey.application.worker import Defer, Failure, Outcome, Success
from vibey.domain.effort import Effort
from vibey.domain.job import FailureClass, idempotency_key
from vibey.domain.ledger import EventKind
from vibey.domain.phase import Phase
from vibey.domain.review import Severity
from vibey.domain.worktree import branch_name


class BuildIntegrateHandler:
    def __init__(
        self,
        *,
        integration: IntegrationBranch,
        gates: GateRunner,
        ledger: BuildLedger,
        jobs: JobRepository,
        clock: Clock,
        projects: ProjectTransitioner | None = None,
        lock: IntegrationLock | None = None,
        lock_backoff: timedelta = timedelta(seconds=30),
    ) -> None:
        self._integration = integration
        self._gates = gates
        self._ledger = ledger
        self._jobs = jobs
        self._clock = clock
        self._projects = projects
        self._lock = lock
        self._lock_backoff = lock_backoff

    async def handle(self, job: JobRecord) -> Outcome:
        if job.kind != "build.integrate":
            return Failure(FailureClass.VIBEY, "expected build.integrate job")
        if job.work_item_id is None:
            return Failure(FailureClass.VIBEY, "build.integrate job is missing work_item_id")

        if self._lock is None:
            return await self._integrate(job, job.work_item_id)
        if not await self._lock.try_acquire(job.project_id, job.cycle):
            return Defer(
                retry_at=self._clock.now() + self._lock_backoff,
                detail=(f"integration branch for cycle {job.cycle} is held by another worker"),
            )
        try:
            return await self._integrate(job, job.work_item_id)
        finally:
            await self._lock.release(job.project_id, job.cycle)

    async def _integrate(self, job: JobRecord, work_item_id: str) -> Outcome:
        merge = await self._integration.merge_item(work_item_id)
        if not merge.ok:
            detail = f"merge conflict integrating {job.work_item_id!r}: {merge.detail}"
            await self._isolate_and_repair(job, detail)
            return Failure(FailureClass.WORK, detail)

        integration_path = await self._integration.ensure()
        verification = job.payload.get("verification", {})
        commands = verification.get("commands", ()) if isinstance(verification, Mapping) else ()
        for command in commands:
            result = await self._gates.run(tuple(shlex.split(str(command))), cwd=integration_path)
            if result.returncode != 0:
                detail = (
                    f"gate failed after merging {job.work_item_id!r}: {command}: "
                    f"{result.stderr.strip()}"
                )
                await self._isolate_and_repair(job, detail)
                return Failure(FailureClass.WORK, detail)

        await self._maybe_enter_review(job)
        return Success({"work_item_id": job.work_item_id})

    async def _maybe_enter_review(self, job: JobRecord) -> None:
        """The BUILD -> REVIEW bridge: when this integrate is the cycle's
        last unsettled BUILD job, transition the phase and enqueue the
        review.demo entry. Both operations tolerate replay: the enqueue is
        idempotent by key, and a CAS miss on the transition means another
        worker (or a replayed self) already won -- that is success, not an
        error, or replays would poison the job."""
        if self._projects is None:
            return
        remaining = await self._jobs.count_unsettled(
            job.project_id, cycle=job.cycle, phase=Phase.BUILD, exclude=job.id
        )
        if remaining != 0:
            return
        # A CAS miss (ValueError) means a replay or another worker already
        # moved the phase on -- swallowing it keeps replays idempotent.
        with contextlib.suppress(ValueError):
            await self._projects.transition(job.project_id, expected=Phase.BUILD, to=Phase.REVIEW)
        await self._jobs.enqueue(
            EnqueueRequest(
                project_id=job.project_id,
                cycle=job.cycle,
                phase=Phase.REVIEW,
                kind="review.demo",
                idempotency_key=idempotency_key(job.project_id, job.cycle, "review.demo", "entry"),
                requirement={"effort": Effort.HIGH.name.lower()},
            )
        )

    async def _isolate_and_repair(self, job: JobRecord, detail: str) -> None:
        """The item is isolated (a finding + a repair job against it), but
        nothing about the rest of the phase is touched -- other items'
        build.integrate jobs proceed independently."""
        finding_id = f"f_integrate_{job.work_item_id}_{uuid4().hex[:8]}"
        now = self._clock.now()
        await self._ledger.record(
            project_id=job.project_id,
            cycle=job.cycle,
            job_id=job.id,
            engine_id=None,
            correlation_id=uuid4(),
            event=EngineEvent(
                kind=EventKind.FINDING_RAISED.value,
                at=now,
                payload={
                    "finding_id": finding_id,
                    "severity": Severity.HIGH.value,
                    "text": detail,
                },
            ),
        )
        await self._jobs.enqueue(
            EnqueueRequest(
                project_id=job.project_id,
                cycle=job.cycle,
                phase=Phase.BUILD,
                kind="build.implement",
                idempotency_key=idempotency_key(
                    job.project_id, job.cycle, "build.implement", f"repair-{finding_id}"
                ),
                work_item_id=job.work_item_id,
                payload={**dict(job.payload), "base_ref": branch_name(job.cycle, "integration")},
                requirement={"effort": Effort.LOW.name.lower()},
            )
        )


# Re-exported for the same reason `application/ports.py` re-exports the
# interfaces package: the seam moved, the import path should not break.
__all__ = [
    "MergeOutcome",
    "IntegrationBranch",
]
