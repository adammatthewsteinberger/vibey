from dataclasses import replace
from datetime import timedelta
from uuid import UUID, uuid4

from tests.application.fakes import FakeJobRepository, make_job
from vibey.application.design import DesignEvent
from vibey.application.visual_handler import VisualInventoryHandler, VisualPlanHandler
from vibey.application.worker import Failure, Success
from vibey.domain.job import FailureClass
from vibey.domain.visual import (
    MediaManifestEntry,
    MediaModality,
    ScreenSurface,
    SurfaceAction,
    VisualInventory,
)


def inventory() -> VisualInventory:
    return VisualInventory(
        surfaces=(
            ScreenSurface(
                screen_id="home",
                name="Home",
                action=SurfaceAction.CREATE,
                responsive_states=("mobile",),
                accessibility_requirements=("keyboard navigable",),
                media_manifest=(MediaManifestEntry("hero", MediaModality.IMAGE, "a hero image"),),
            ),
        )
    )


class FakeLedger:
    async def append(self, *args):  # type: ignore[no-untyped-def]
        return None

    async def all_for_project(self, project_id: UUID) -> tuple[DesignEvent, ...]:
        return ()


class FakeProducer:
    def __init__(self, result: VisualInventory) -> None:
        self.result = result

    async def inventory(self, events):  # type: ignore[no-untyped-def]
        return self.result


class FakeInventories:
    def __init__(self) -> None:
        self.value: VisualInventory | None = None
        self.published = False

    async def save(self, project_id: UUID, cycle: int, value: VisualInventory) -> None:
        self.value = value

    async def load(self, project_id: UUID, cycle: int) -> VisualInventory | None:
        return self.value

    async def publish(self, project_id: UUID, cycle: int, value: VisualInventory) -> None:
        self.published = True


async def test_inventory_handler_saves_a_complete_inventory_and_enqueues_the_plan() -> None:
    job = replace(make_job(uuid4()), kind="visual.inventory")
    inventories = FakeInventories()
    jobs = FakeJobRepository()
    outcome = await VisualInventoryHandler(
        ledger=FakeLedger(), producer=FakeProducer(inventory()), inventories=inventories, jobs=jobs
    ).handle(job)
    assert isinstance(outcome, Success)
    assert inventories.value == inventory()
    claimed = await jobs.claim(job.project_id, owner="test", lease=timedelta(seconds=5))
    assert claimed is not None
    assert claimed.kind == "visual.plan"


async def test_inventory_handler_rejects_wrong_kind_and_incomplete_result() -> None:
    inventories = FakeInventories()
    handler = VisualInventoryHandler(
        ledger=FakeLedger(),
        producer=FakeProducer(VisualInventory(())),
        inventories=inventories,
        jobs=FakeJobRepository(),
    )
    assert await handler.handle(make_job(uuid4())) == Failure(
        FailureClass.VIBEY, "expected visual.inventory job"
    )
    outcome = await handler.handle(replace(make_job(uuid4()), kind="visual.inventory"))
    assert isinstance(outcome, Failure)
    assert outcome.failure_class is FailureClass.WORK


async def test_plan_handler_publishes_saved_inventory() -> None:
    job = replace(make_job(uuid4()), kind="visual.plan")
    inventories = FakeInventories()
    inventories.value = inventory()
    outcome = await VisualPlanHandler(inventories=inventories).handle(job)
    assert isinstance(outcome, Success)
    assert inventories.published


async def test_plan_handler_rejects_wrong_kind_and_missing_inventory() -> None:
    handler = VisualPlanHandler(inventories=FakeInventories())
    assert await handler.handle(make_job(uuid4())) == Failure(
        FailureClass.VIBEY, "expected visual.plan job"
    )
    missing = await handler.handle(replace(make_job(uuid4()), kind="visual.plan"))
    assert missing == Failure(FailureClass.WORK, "no visual inventory exists")
