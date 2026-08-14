"""Protocols application/ depends on. Concrete implementations live in
infrastructure/ and are wired together only in bootstrap.py."""

from collections.abc import AsyncIterator, Mapping
from datetime import datetime, timedelta
from typing import Protocol, runtime_checkable
from uuid import UUID

from vibey.application.dto import (
    EngineEvent,
    EngineHealthRecord,
    EnqueueRequest,
    HumanGateRecord,
    HumanGateRequest,
    JobRecord,
    PreflightResult,
    RunHandle,
    RunSpec,
    SnapshotRef,
    StopSummary,
)
from vibey.domain.capacity import CapacityState
from vibey.domain.engine import EngineDescriptor
from vibey.domain.job import FailureClass


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


@runtime_checkable
class EngineAdapter(Protocol):
    """infrastructure/engines/ -- the only place vendor CLI shapes exist."""

    @property
    def descriptor(self) -> EngineDescriptor: ...

    async def preflight(self) -> PreflightResult:
        """Runs `<engine> doctor`; classifies auth + availability."""
        ...

    async def start(self, spec: RunSpec) -> RunHandle:
        """Builds argv from descriptor.effort_projection + isolation flags,
        spawns the runner, returns a handle over its run directory."""
        ...

    def tail(self, handle: RunHandle) -> AsyncIterator[EngineEvent]:
        """Streams the runner's events.jsonl, translated into vibey's own
        event vocabulary."""
        ...

    async def send_prompt(self, handle: RunHandle, text: str, *, now: bool) -> None:
        """Writes the runner's control-plane inbox (prompt --now / --at-break)."""
        ...

    async def stop(self, handle: RunHandle) -> StopSummary:
        """Soft-stops the run; collects stop-summary.md and the final
        snapshot."""
        ...

    async def snapshot(self, handle: RunHandle) -> SnapshotRef | None: ...

    def classify(self, raw: Mapping[str, object]) -> CapacityState:
        """Vendor error shape -> vibey's capacity ADT."""
        ...

    def attribute(self, exit_code: int, tail: str) -> FailureClass: ...


@runtime_checkable
class EngineHealthRepository(Protocol):
    async def get(self, project_id: UUID, engine_id: str) -> EngineHealthRecord | None: ...

    async def upsert(self, record: EngineHealthRecord) -> EngineHealthRecord: ...

    async def list_for_project(self, project_id: UUID) -> tuple[EngineHealthRecord, ...]: ...
