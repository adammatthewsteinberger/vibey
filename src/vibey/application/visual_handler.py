"""Durable ``visual.inventory`` / ``visual.plan`` handlers.

Task 5.7/5.8 scaffolding: an inventory producer fills the screen/state matrix
from the accepted DESIGN spec, and the plan stage publishes it as a reviewable
artifact. Media generation, the design-system contract, and the review gate
(tasks 5.8's remaining artifacts, 5.9-5.13) are not built yet -- this only
covers the inventory itself, mirroring how design/spec.py started in M1
before anything consumed it.
"""

from collections.abc import Sequence
from typing import Protocol
from uuid import UUID

from vibey.application.design import DesignEvent
from vibey.application.design_handler import DesignLedger
from vibey.application.dto import JobRecord
from vibey.application.worker import Failure, Outcome, Success
from vibey.domain.job import FailureClass
from vibey.domain.visual import VisualInventory


class VisualInventoryProducer(Protocol):
    async def inventory(self, events: Sequence[DesignEvent]) -> VisualInventory: ...


class VisualInventoryRepository(Protocol):
    async def save(self, project_id: UUID, cycle: int, inventory: VisualInventory) -> None: ...

    async def load(self, project_id: UUID, cycle: int) -> VisualInventory | None: ...

    async def publish(self, project_id: UUID, cycle: int, inventory: VisualInventory) -> None: ...


class VisualInventoryHandler:
    def __init__(
        self,
        *,
        ledger: DesignLedger,
        producer: VisualInventoryProducer,
        inventories: VisualInventoryRepository,
    ) -> None:
        self._ledger = ledger
        self._producer = producer
        self._inventories = inventories

    async def handle(self, job: JobRecord) -> Outcome:
        if job.kind != "visual.inventory":
            return Failure(FailureClass.VIBEY, "expected visual.inventory job")
        events = await self._ledger.all_for_project(job.project_id)
        inventory = await self._producer.inventory(events)
        violations = inventory.is_complete()
        if violations:
            return Failure(FailureClass.WORK, "; ".join(violations))
        await self._inventories.save(job.project_id, job.cycle, inventory)
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
