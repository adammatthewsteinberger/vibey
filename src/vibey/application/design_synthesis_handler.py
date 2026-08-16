"""Synthesis and final publication handlers for DESIGN."""

from collections.abc import Sequence
from typing import Protocol
from uuid import UUID

from vibey.application.design import DesignEvent
from vibey.application.design_handler import DesignLedger
from vibey.application.dto import JobRecord
from vibey.application.worker import Failure, Outcome, Success
from vibey.domain.job import FailureClass
from vibey.domain.spec import DesignSpec


class SpecSynthesizer(Protocol):
    async def synthesize(self, events: Sequence[DesignEvent]) -> DesignSpec: ...


class DesignSpecRepository(Protocol):
    async def save(self, project_id: UUID, cycle: int, spec: DesignSpec) -> None: ...

    async def load(self, project_id: UUID, cycle: int) -> DesignSpec | None: ...

    async def publish(self, project_id: UUID, cycle: int, spec: DesignSpec) -> None: ...


class DesignSynthesizeHandler:
    def __init__(
        self,
        *,
        ledger: DesignLedger,
        synthesizer: SpecSynthesizer,
        specs: DesignSpecRepository,
    ) -> None:
        self._ledger = ledger
        self._synthesizer = synthesizer
        self._specs = specs

    async def handle(self, job: JobRecord) -> Outcome:
        if job.kind != "design.synthesize":
            return Failure(FailureClass.VIBEY, "expected design.synthesize job")
        events = await self._ledger.all_for_project(job.project_id)
        spec = await self._synthesizer.synthesize(events)
        violations = spec.is_buildable()
        if violations:
            return Failure(FailureClass.WORK, "; ".join(violations))
        await self._specs.save(job.project_id, job.cycle, spec)
        return Success({"acceptance_criteria": len(spec.criteria)})


class DesignSpecHandler:
    def __init__(self, *, specs: DesignSpecRepository) -> None:
        self._specs = specs

    async def handle(self, job: JobRecord) -> Outcome:
        if job.kind != "design.spec":
            return Failure(FailureClass.VIBEY, "expected design.spec job")
        spec = await self._specs.load(job.project_id, job.cycle)
        if spec is None:
            return Failure(FailureClass.WORK, "no synthesized design spec exists")
        await self._specs.publish(job.project_id, job.cycle, spec)
        return Success({"acceptance_criteria": len(spec.criteria)})
