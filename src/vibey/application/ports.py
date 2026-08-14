"""Protocols application/ depends on. Concrete implementations live in
infrastructure/ and are wired together only in bootstrap.py."""

from collections.abc import Mapping
from datetime import datetime, timedelta
from typing import Protocol, runtime_checkable
from uuid import UUID

from vibey.application.dto import EnqueueRequest, HumanGateRecord, HumanGateRequest, JobRecord


@runtime_checkable
class Clock(Protocol):
    def now(self) -> datetime: ...


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

    async def park(self, job_id: UUID, *, owner: str) -> bool:
        """Marks the job awaiting_human and releases its lease immediately,
        without counting as a failure attempt."""
        ...

    async def reap(self) -> int:
        """Reclaims jobs whose lease has expired. Returns the count
        reclaimed."""
        ...

    async def get(self, job_id: UUID) -> JobRecord | None: ...


@runtime_checkable
class HumanGateRepository(Protocol):
    async def raise_gate(
        self, project_id: UUID, job_id: UUID | None, request: HumanGateRequest
    ) -> HumanGateRecord: ...

    async def answer(
        self, gate_id: UUID, *, answer: Mapping[str, object], answered_by: str
    ) -> HumanGateRecord: ...


@runtime_checkable
class JobReadyNotifier(Protocol):
    async def wait_for_job_ready(self, project_id: UUID, *, timeout: timedelta) -> bool:
        """Blocks until a job-ready notification arrives or timeout elapses.
        Returns True if notified, False on timeout (the poll fallback)."""
        ...
