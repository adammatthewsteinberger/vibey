"""Durable ``visual.inventory`` / ``visual.plan`` handlers.

Task 5.7/5.8 scaffolding: an inventory producer fills the screen/state matrix
from the accepted DESIGN spec, and the plan stage publishes it as a reviewable
artifact. Media generation, the design-system contract, and the review gate
(tasks 5.8's remaining artifacts, 5.9-5.13) are not built yet -- this only
covers the inventory itself, mirroring how design/spec.py started in M1
before anything consumed it.
"""

from vibey.application.design_handler import DesignLedger
from vibey.application.dto import EnqueueRequest, JobRecord
from vibey.application.interfaces import (
    VisualInventoryProducer,
    VisualInventoryRepository,
)
from vibey.application.ports import JobRepository
from vibey.application.worker import Failure, Outcome, Success
from vibey.domain.effort import Effort
from vibey.domain.job import FailureClass, idempotency_key
from vibey.domain.phase import Phase


class VisualInventoryHandler:
    def __init__(
        self,
        *,
        ledger: DesignLedger,
        producer: VisualInventoryProducer,
        inventories: VisualInventoryRepository,
        jobs: JobRepository,
    ) -> None:
        self._ledger = ledger
        self._producer = producer
        self._inventories = inventories
        self._jobs = jobs

    async def handle(self, job: JobRecord) -> Outcome:
        if job.kind != "visual.inventory":
            return Failure(FailureClass.VIBEY, "expected visual.inventory job")
        events = await self._ledger.all_for_project(job.project_id)
        inventory = await self._producer.inventory(events)
        violations = inventory.is_complete()
        if violations:
            return Failure(FailureClass.WORK, "; ".join(violations))
        await self._inventories.save(job.project_id, job.cycle, inventory)
        await self._jobs.enqueue(
            EnqueueRequest(
                project_id=job.project_id,
                cycle=job.cycle,
                phase=Phase.VISUAL_DESIGN,
                kind="visual.plan",
                idempotency_key=idempotency_key(job.project_id, job.cycle, "visual.plan", "plan"),
                requirement={"effort": Effort.HIGH.name.lower()},
            )
        )
        return Success({"surfaces": len(inventory.surfaces)})


class VisualPlanHandler:
    def __init__(self, *, inventories: VisualInventoryRepository) -> None:
        self._inventories = inventories

    async def handle(self, job: JobRecord) -> Outcome:
        if job.kind != "visual.plan":
            return Failure(FailureClass.VIBEY, "expected visual.plan job")
        inventory = await self._inventories.load(job.project_id, job.cycle)
        if inventory is None:
            return Failure(FailureClass.WORK, "no visual inventory exists")
        await self._inventories.publish(job.project_id, job.cycle, inventory)
        return Success({"surfaces": len(inventory.surfaces)})


# Re-exported for the same reason `application/ports.py` re-exports the
# interfaces package: the seam moved, the import path should not break.
__all__ = [
    "VisualInventoryProducer",
    "VisualInventoryRepository",
]
