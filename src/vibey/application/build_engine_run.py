"""Shared "run an EngineAdapter, tail its events, record them to the BUILD
ledger" logic used by both build.implement and build.verify -- they differ
in what they ask an engine to do and what a completing verdict means, not
in how a run is driven or persisted."""

from dataclasses import dataclass
from typing import Protocol
from uuid import UUID, uuid4

from vibey.application.dto import EngineEvent, JobRecord, RunHandle
from vibey.application.ports import EngineAdapter
from vibey.domain.engine import EngineId
from vibey.domain.ledger import EventKind


class BuildLedger(Protocol):
    async def record(
        self,
        *,
        project_id: UUID,
        cycle: int,
        job_id: UUID,
        engine_id: EngineId | None,
        correlation_id: UUID,
        event: EngineEvent,
    ) -> None: ...


@dataclass(frozen=True, slots=True)
class RunOutcome:
    complete: bool
    capacity_rejected: bool


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
    return RunOutcome(complete=complete, capacity_rejected=capacity_rejected)
