"""The lease -> execute -> ack loop. Workers are stateless: all durable
state lives in JobRepository, so a worker can die at any point and a reaped
job is simply claimed by someone else (non-negotiable #6: every handler must
be idempotent under replay)."""

import asyncio
import contextlib
from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import timedelta
from typing import Protocol, runtime_checkable
from uuid import UUID

from vibey.application.dto import HumanGateRequest, JobRecord
from vibey.application.ports import HumanGateRepository, JobRepository
from vibey.domain.job import FailureClass


@dataclass(frozen=True, slots=True)
class Success:
    result: Mapping[str, object] = field(default_factory=dict)


@dataclass(frozen=True, slots=True)
class Failure:
    failure_class: FailureClass
    detail: str


@dataclass(frozen=True, slots=True)
class Park:
    request: HumanGateRequest


Outcome = Success | Failure | Park


@runtime_checkable
class JobHandler(Protocol):
    async def handle(self, job: JobRecord) -> Outcome: ...


class WorkerLoop:
    def __init__(
        self,
        *,
        jobs: JobRepository,
        gates: HumanGateRepository,
        handler: JobHandler,
        owner: str,
        lease: timedelta = timedelta(seconds=30),
    ) -> None:
        self._jobs = jobs
        self._gates = gates
        self._handler = handler
        self._owner = owner
        self._lease = lease

    async def run_once(self, project_id: UUID) -> bool:
        """Claims and executes at most one job. Returns False if there was
        nothing claimable."""
        job = await self._jobs.claim(project_id, owner=self._owner, lease=self._lease)
        if job is None:
            return False

        heartbeat_task = asyncio.ensure_future(self._heartbeat_forever(job.id))
        try:
            try:
                outcome: Outcome = await self._handler.handle(job)
            except Exception as exc:  # noqa: BLE001 - any handler bug becomes a VIBEY-class nack
                outcome = Failure(FailureClass.VIBEY, str(exc))
        finally:
            heartbeat_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await heartbeat_task

        await self._settle(job, outcome)
        return True

    async def _settle(self, job: JobRecord, outcome: Outcome) -> None:
        if isinstance(outcome, Success):
            await self._jobs.ack(job.id, owner=self._owner)
        elif isinstance(outcome, Failure):
            await self._jobs.nack(
                job.id,
                owner=self._owner,
                error={"class": outcome.failure_class.value, "detail": outcome.detail},
            )
        elif isinstance(outcome, Park):
            # The gate is raised before the lease is released, so there is
            # never a window where the job looks claimable again before the
            # human_gate row exists to explain why it is parked.
            await self._gates.raise_gate(job.project_id, job.id, outcome.request)
            await self._jobs.park(job.id, owner=self._owner)

    async def _heartbeat_forever(self, job_id: UUID) -> None:
        interval = self._lease.total_seconds() / 3
        try:
            while True:
                await asyncio.sleep(interval)
                await self._jobs.heartbeat(job_id, owner=self._owner, lease=self._lease)
        except asyncio.CancelledError:
            pass
