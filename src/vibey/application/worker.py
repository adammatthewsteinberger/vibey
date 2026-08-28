# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""The lease -> execute -> ack loop. Workers are stateless: all durable
state lives in JobRepository, so a worker can die at any point and a reaped
job is simply claimed by someone else (non-negotiable #6: every handler must
be idempotent under replay)."""

import asyncio
import contextlib
from collections.abc import Callable
from datetime import datetime, timedelta
from uuid import UUID

from vibey.application.dto import JobRecord
from vibey.application.interfaces import (
    Defer,
    Failure,
    JobHandler,
    Outcome,
    Park,
    Success,
)
from vibey.application.ports import HumanGateRepository, JobRepository
from vibey.domain.job import FailureClass


class CapacityDeferred(Exception):
    def __init__(self, retry_at: datetime, detail: str) -> None:
        super().__init__(detail)
        self.retry_at = retry_at
        self.detail = detail


class WorkerLoop:
    def __init__(
        self,
        *,
        jobs: JobRepository,
        gates: HumanGateRepository,
        handler: JobHandler,
        owner: str,
        lease: timedelta = timedelta(seconds=30),
        lease_for_kind: Callable[[str], timedelta] | None = None,
    ) -> None:
        self._jobs = jobs
        self._gates = gates
        self._handler = handler
        self._owner = owner
        self._lease = lease
        self._lease_for_kind = lease_for_kind

    async def run_once(self, project_id: UUID) -> bool:
        """Claims and executes at most one job. Returns False if there was
        nothing claimable."""
        job = await self._jobs.claim(project_id, owner=self._owner, lease=self._lease)
        if job is None:
            return False

        # Lease duration is per-kind (a build.implement run takes hours; a
        # triage takes minutes). The kind isn't known until after the claim,
        # so claim at the short default and immediately extend once resolved.
        lease = self._lease
        if self._lease_for_kind is not None:
            resolved = self._lease_for_kind(job.kind)
            if resolved != self._lease:
                await self._jobs.heartbeat(job.id, owner=self._owner, lease=resolved)
                lease = resolved

        heartbeat_task = asyncio.ensure_future(self._heartbeat_forever(job.id, lease=lease))
        try:
            try:
                outcome: Outcome = await self._handler.handle(job)
            except CapacityDeferred as exc:
                outcome = Defer(exc.retry_at, exc.detail, capacity=True)
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
            #
            # Some handlers (review.collect, the deploy gates) raise their
            # gate themselves before returning Park; raising here again
            # would leave a duplicate unanswered gate that latest_for_job
            # returns forever, re-parking the job no matter what the human
            # answered. Only raise when this job has no open gate already.
            existing = await self._gates.latest_for_job(job.id)
            if existing is None or existing.answer is not None:
                await self._gates.raise_gate(job.project_id, job.id, outcome.request)
            await self._jobs.park(job.id, owner=self._owner)
        elif isinstance(outcome, Defer):
            await self._jobs.defer(
                job.id,
                owner=self._owner,
                retry_at=outcome.retry_at,
                error={"class": FailureClass.CAPACITY.value, "detail": outcome.detail},
            )

    async def _heartbeat_forever(self, job_id: UUID, *, lease: timedelta) -> None:
        interval = lease.total_seconds() / 3
        try:
            while True:
                await asyncio.sleep(interval)
                await self._jobs.heartbeat(job_id, owner=self._owner, lease=lease)
        except asyncio.CancelledError:
            pass


# Re-exported for the same reason `application/ports.py` re-exports the
# interfaces package: the seam moved, the import path should not break.
__all__ = [
    "Defer",
    "Failure",
    "JobHandler",
    "Outcome",
    "Park",
    "Success",
]
