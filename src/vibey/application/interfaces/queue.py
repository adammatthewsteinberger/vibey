"""The durable job queue and the handler seam a worker drives."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Protocol, runtime_checkable
from uuid import UUID

from vibey.application.dto import (
    EnqueueRequest,
    HumanGateRequest,
    JobRecord,
)
from vibey.domain.job import FailureClass, JobState


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


@dataclass(frozen=True, slots=True)
class Defer:
    retry_at: datetime
    detail: str


# What a handler is allowed to say happened. Part of the JobHandler seam's
# vocabulary, so it lives beside the Protocol rather than in the worker that
# interprets it -- otherwise the seam imports its own consumer.
Outcome = Success | Failure | Park | Defer


@runtime_checkable
class JobHandler(Protocol):
    async def handle(self, job: JobRecord) -> Outcome: ...


@runtime_checkable
class JobReadyNotifier(Protocol):
    async def wait_for_job_ready(self, project_id: UUID, *, timeout: timedelta) -> bool:
        """Blocks until a job-ready notification arrives or timeout elapses.
        Returns True if notified, False on timeout (the poll fallback)."""
        ...


@runtime_checkable
class JobRepository(Protocol):
    async def enqueue(self, request: EnqueueRequest) -> JobRecord:
        """Idempotent: a second enqueue with the same (project_id,
        idempotency_key) returns the existing row rather than creating a
        duplicate."""
        ...

    async def claim(self, project_id: UUID, *, owner: str, lease: timedelta) -> JobRecord | None:
        """Claims the highest-priority ready job whose dependencies have all
        succeeded, or None if there is nothing claimable right now."""
        ...

    async def heartbeat(self, job_id: UUID, *, owner: str, lease: timedelta) -> bool: ...

    async def ack(self, job_id: UUID, *, owner: str) -> bool: ...

    async def nack(self, job_id: UUID, *, owner: str, error: Mapping[str, object]) -> bool: ...

    async def defer(
        self,
        job_id: UUID,
        *,
        owner: str,
        retry_at: datetime,
        error: Mapping[str, object],
    ) -> bool:
        """Releases a capacity-blocked lease without consuming a failure attempt."""
        ...

    async def park(self, job_id: UUID, *, owner: str) -> bool:
        """Marks the job awaiting_human and releases its lease immediately,
        without counting as a failure attempt."""
        ...

    async def reap(self) -> int:
        """Reclaims jobs whose lease has expired. Returns the count
        reclaimed."""
        ...

    async def queue_depth(self, project_id: UUID) -> Mapping[JobState, int]:
        """Returns the number of jobs by JobState for the given project."""
        ...

    async def get(self, job_id: UUID) -> JobRecord | None: ...
