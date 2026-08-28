# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://hire.adam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
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
from vibey.application.build_verify_handler import GateRunner, gate_output_tail, granted_max_rounds
from vibey.application.dto import EngineEvent, EnqueueRequest, HumanGateRequest, JobRecord
from vibey.application.interfaces import (
    IntegrationBranch,
    IntegrationLock,
    LedgerReader,
    MergeOutcome,
    ProjectTransitioner,
)
from vibey.application.ports import Clock, HumanGateRepository, JobRepository
from vibey.application.worker import Defer, Failure, Outcome, Park, Success
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
        ledger_reader: LedgerReader | None = None,
        max_repair_rounds: int = 3,
        repair_backoff: timedelta = timedelta(minutes=10),
        human_gates: HumanGateRepository | None = None,
    ) -> None:
        self._integration = integration
        self._gates = gates
        self._ledger = ledger
        self._jobs = jobs
        self._clock = clock
        self._projects = projects
        self._lock = lock
        self._lock_backoff = lock_backoff
        self._ledger_reader = ledger_reader
        self._max_repair_rounds = max_repair_rounds
        self._repair_backoff = repair_backoff
        self._human_gates = human_gates

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
            return await self._fail_or_repair(job, work_item_id, detail, merge_conflict=True)

        integration_path = await self._integration.ensure()
        verification = job.payload.get("verification", {})
        commands = verification.get("commands", ()) if isinstance(verification, Mapping) else ()
        for command in commands:
            result = await self._gates.run(tuple(shlex.split(str(command))), cwd=integration_path)
            if result.returncode != 0:
                detail = (
                    f"gate failed after merging {job.work_item_id!r}: {command}: "
                    f"{gate_output_tail(result)}"
                )
                return await self._fail_or_repair(job, work_item_id, detail, merge_conflict=False)

        if self._ledger_reader is not None:
            # A successful integrate closes its own earlier merge/gate
            # findings, or they stay open in the ledger and poison
            # review.triage into a needless loop-back long after the
            # conflict was repaired -- caught live: 39 stale conflict
            # findings sent an accepted review straight back to BUILD.
            await self._resolve_own_findings(job, work_item_id, self._ledger_reader)

        await self._maybe_enter_review(job)
        return Success({"work_item_id": job.work_item_id})

    async def _resolve_own_findings(
        self, job: JobRecord, work_item_id: str, reader: LedgerReader
    ) -> None:
        prefix = f"f_integrate_{work_item_id}_"
        raised: list[str] = []
        resolved: set[str] = set()
        for event in await reader.all_for_project(job.project_id):
            if event.cycle != job.cycle:
                continue
            finding_id = str(event.payload.get("finding_id", ""))
            if not finding_id.startswith(prefix):
                continue
            if event.kind is EventKind.FINDING_RAISED:
                raised.append(finding_id)
            elif event.kind is EventKind.FINDING_RESOLVED:
                resolved.add(finding_id)
        for finding_id in raised:
            if finding_id in resolved:
                continue
            await self._ledger.record(
                project_id=job.project_id,
                cycle=job.cycle,
                job_id=job.id,
                engine_id=None,
                correlation_id=uuid4(),
                event=EngineEvent(
                    kind=EventKind.FINDING_RESOLVED.value,
                    at=self._clock.now(),
                    payload={
                        "finding_id": finding_id,
                        "resolution": "the work item now integrates cleanly",
                    },
                ),
            )

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

    async def _fail_or_repair(
        self, job: JobRecord, work_item_id: str, detail: str, *, merge_conflict: bool
    ) -> Outcome:
        """Without a ledger reader: the original raise-and-fail behavior.
        With one: the bounded repair loop -- dedupe against an in-flight
        repair, park after max rounds, and give the repair session
        instructions it can actually act on. Caught live: every failed
        integrate attempt spawned a fresh repair, and a merge-conflict
        repair without merge instructions worked on the item branch where
        nothing looked wrong -- an unbounded storm of paid sessions."""
        if self._ledger_reader is None:
            await self._isolate_and_repair(job, detail)
            return Failure(FailureClass.WORK, detail)

        prefix = f"f_integrate_{work_item_id}_"
        raised: list[str] = []
        resolved: set[str] = set()
        for event in await self._ledger_reader.all_for_project(job.project_id):
            if event.cycle != job.cycle:
                continue
            finding_id = str(event.payload.get("finding_id", ""))
            if not finding_id.startswith(prefix):
                continue
            if event.kind is EventKind.FINDING_RAISED:
                raised.append(finding_id)
            elif event.kind is EventKind.FINDING_RESOLVED:
                resolved.add(finding_id)
        retry_at = self._clock.now() + self._repair_backoff

        if any(finding_id not in resolved for finding_id in raised):
            return Defer(
                retry_at=retry_at,
                detail=f"integration of {work_item_id!r} failing; repair in flight",
            )
        allowed = self._max_repair_rounds
        if self._human_gates is not None:
            gate = await self._human_gates.latest_for_job(job.id)
            if gate is not None and gate.answer is not None:
                granted = granted_max_rounds(gate.answer)
                if granted is not None and granted > allowed:
                    allowed = granted
        if len(raised) >= allowed:
            return Park(
                HumanGateRequest(
                    kind="integrate_repair_exhausted",
                    prompt=(
                        f"work item {work_item_id!r} failed integration after "
                        f"{len(raised)} repair rounds; latest: {detail[:500]}. "
                        "Grant more repair rounds by answering "
                        f"--raw '{{\"max_rounds\": {len(raised) + 3}}}', or fix the "
                        "branch by hand and answer anything to retry."
                    ),
                )
            )

        integration_branch = branch_name(job.cycle, "integration")
        if merge_conflict:
            instructions = (
                f"This branch could not be merged into the shared integration branch "
                f"{integration_branch}. In this worktree run `git merge {integration_branch}`, "
                "resolve every conflict so both the integrated code's behavior and this "
                "item's changes survive, commit the merge, then re-run the verification "
                "commands."
            )
        else:
            instructions = (
                f"The merged result on {integration_branch} fails the checks below. Fix the "
                "cause on this branch without weakening the checks, then re-run the "
                "verification commands."
            )
        await self._isolate_and_repair(job, detail, repair_instructions=instructions)
        return Defer(
            retry_at=retry_at,
            detail=f"integration of {work_item_id!r} failed; repair enqueued",
        )

    async def _isolate_and_repair(
        self, job: JobRecord, detail: str, *, repair_instructions: str | None = None
    ) -> None:
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
        payload: dict[str, object] = {
            **dict(job.payload),
            "base_ref": branch_name(job.cycle, "integration"),
        }
        if repair_instructions is not None:
            payload["repair_finding_id"] = finding_id
            payload["repair_detail"] = f"{detail[:1500]}\n\n{repair_instructions}"
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
                payload=payload,
                requirement={"effort": Effort.LOW.name.lower()},
            )
        )


# Re-exported for the same reason `application/ports.py` re-exports the
# interfaces package: the seam moved, the import path should not break.
__all__ = [
    "MergeOutcome",
    "IntegrationBranch",
]
