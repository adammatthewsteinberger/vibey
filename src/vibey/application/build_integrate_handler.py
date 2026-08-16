"""Durable ``build.integrate`` handler (M6 task 6.8): merges one verified
work item's branch into the shared integration branch, runs the full gate
suite against the merged result, and never rolls back the whole phase for
one bad item -- a merge conflict or a post-merge gate failure produces a
``FindingRaised`` event and a targeted repair ``build.implement`` job based
on the integration branch's current head, not a rollback of everything
(phase-protocols.md section 2.4).

Concurrency note: this handler does not serialize concurrent
``build.integrate`` jobs for the same (project, cycle) against each other --
a real lock (e.g. a Postgres advisory lock scoped to project_id/cycle) is
needed before multiple workers can safely integrate into the same branch at
once. Safe today because nothing in this codebase runs more than one worker
against a project concurrently yet; flagged here so it isn't forgotten when
that changes.
"""

import shlex
from collections.abc import Mapping
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
from uuid import uuid4

from vibey.application.build_engine_run import BuildLedger
from vibey.application.build_verify_handler import GateRunner
from vibey.application.dto import EngineEvent, EnqueueRequest, JobRecord
from vibey.application.ports import Clock, JobRepository
from vibey.application.worker import Failure, Outcome, Success
from vibey.domain.effort import Effort
from vibey.domain.job import FailureClass, idempotency_key
from vibey.domain.ledger import EventKind
from vibey.domain.phase import Phase
from vibey.domain.review import Severity
from vibey.domain.worktree import branch_name


@dataclass(frozen=True, slots=True)
class MergeOutcome:
    ok: bool
    detail: str


class IntegrationBranch(Protocol):
    async def ensure(self) -> Path: ...

    async def merge_item(self, item_id: str) -> MergeOutcome: ...


class BuildIntegrateHandler:
    def __init__(
        self,
        *,
        integration: IntegrationBranch,
        gates: GateRunner,
        ledger: BuildLedger,
        jobs: JobRepository,
        clock: Clock,
    ) -> None:
        self._integration = integration
        self._gates = gates
        self._ledger = ledger
        self._jobs = jobs
        self._clock = clock

    async def handle(self, job: JobRecord) -> Outcome:
        if job.kind != "build.integrate":
            return Failure(FailureClass.VIBEY, "expected build.integrate job")
        if job.work_item_id is None:
            return Failure(FailureClass.VIBEY, "build.integrate job is missing work_item_id")

        merge = await self._integration.merge_item(job.work_item_id)
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

        return Success({"work_item_id": job.work_item_id})

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
