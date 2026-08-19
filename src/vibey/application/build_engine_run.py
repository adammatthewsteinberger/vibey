"""Shared "run an EngineAdapter, tail its events, record them to the BUILD
ledger" logic used by both build.implement and build.verify -- they differ
in what they ask an engine to do and what a completing verdict means, not
in how a run is driven or persisted."""

from dataclasses import dataclass
from uuid import uuid4

from vibey.application.dto import JobRecord, RunHandle
from vibey.application.interfaces import (
    BuildLedger,
)
from vibey.application.ports import EngineAdapter
from vibey.domain.ledger import EventKind


@dataclass(frozen=True, slots=True)
class RunOutcome:
    complete: bool
    capacity_rejected: bool
    exit_code: int | None = None
    """The engine process's exit code, when the adapter exposes the
    optional ``run_exit_code`` capability -- EXIT_CODE_WIND_DOWN here is
    the graceful-handoff signal. None for adapters without the capability
    or while the process is still running."""


async def run_and_record(
    engine: EngineAdapter, ledger: BuildLedger, *, job: JobRecord, handle: RunHandle
) -> RunOutcome:
    complete = False
    capacity_rejected = False
    correlation_id = uuid4()
    async for event in engine.tail(handle):
        await ledger.record(
            project_id=job.project_id,
            cycle=job.cycle,
            job_id=job.id,
            engine_id=engine.descriptor.engine_id,
            correlation_id=correlation_id,
            event=event,
        )
        if event.kind == EventKind.VERDICT_RENDERED.value and bool(event.payload.get("complete")):
            complete = True
        if event.kind == EventKind.CAPACITY_REJECTED.value:
            capacity_rejected = True

    # Read the exit code only after the tail drains: the adapter's process
    # reference stays alive until stop() releases it, and a pre-drain read
    # would race the process's own shutdown.
    exit_code: int | None = None
    read_exit_code = getattr(engine, "run_exit_code", None)
    if callable(read_exit_code):
        raw = read_exit_code(handle)
        if isinstance(raw, int):
            exit_code = raw
    return RunOutcome(complete=complete, capacity_rejected=capacity_rejected, exit_code=exit_code)


# Re-exported for the same reason `application/ports.py` re-exports the
# interfaces package: the seam moved, the import path should not break.
__all__ = [
    "BuildLedger",
]
