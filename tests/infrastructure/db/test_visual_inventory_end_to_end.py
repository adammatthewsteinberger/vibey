from datetime import UTC, datetime

import asyncpg

from vibey.application.dto import EnqueueRequest
from vibey.application.job_dispatcher import JobDispatcher
from vibey.application.visual_handler import VisualInventoryHandler, VisualPlanHandler
from vibey.application.worker import WorkerLoop
from vibey.domain.job import JobState, idempotency_key
from vibey.domain.phase import Phase
from vibey.infrastructure.db.design_ledger import PostgresDesignLedger
from vibey.infrastructure.db.human_gate_repository import PostgresHumanGateRepository
from vibey.infrastructure.db.job_repository import PostgresJobRepository
from vibey.infrastructure.db.ledger_repository import PostgresLedgerRepository
from vibey.infrastructure.db.project_repository import PostgresProjectRepository
from vibey.infrastructure.db.visual_inventory_repository import FileVisualInventoryRepository
from vibey.infrastructure.engines.scripted_visual import ScriptedVisualProvider


class FixedClock:
    def now(self) -> datetime:
        return datetime(2026, 8, 14, tzinfo=UTC)


async def test_scripted_visual_inventory_and_plan_run_end_to_end(
    migrated_pool: asyncpg.Pool, tmp_path
) -> None:
    projects = PostgresProjectRepository(migrated_pool)
    project = await projects.create("scripted-visual", tmp_path, max_cycles=10, config={})
    project_id = project.project_id
    jobs = PostgresJobRepository(migrated_pool)
    gates = PostgresHumanGateRepository(migrated_pool)
    ledger = PostgresDesignLedger(PostgresLedgerRepository(migrated_pool))
    inventories = FileVisualInventoryRepository(projects)
    provider = ScriptedVisualProvider()

    inventory_job = await jobs.enqueue(
        EnqueueRequest(
            project_id=project_id,
            cycle=1,
            phase=Phase.VISUAL_DESIGN,
            kind="visual.inventory",
            idempotency_key=idempotency_key(project_id, 1, "visual.inventory", "integration"),
        )
    )

    dispatcher = JobDispatcher(
        {
            "visual.inventory": VisualInventoryHandler(
                ledger=ledger, producer=provider, inventories=inventories, jobs=jobs
            ),
            "visual.plan": VisualPlanHandler(inventories=inventories),
        }
    )
    worker = WorkerLoop(jobs=jobs, gates=gates, handler=dispatcher, owner="visual-worker")

    # visual.inventory runs and enqueues visual.plan; then visual.plan runs.
    assert await worker.run_once(project_id)
    assert await worker.run_once(project_id)
    assert not await worker.run_once(project_id)

    async with migrated_pool.acquire() as conn:
        kinds = await conn.fetch("SELECT kind, state FROM job WHERE project_id = $1", project_id)
    assert {row["kind"]: row["state"] for row in kinds} == {
        "visual.inventory": JobState.SUCCEEDED.value,
        "visual.plan": JobState.SUCCEEDED.value,
    }
    assert (await jobs.get(inventory_job.id)).state is JobState.SUCCEEDED  # type: ignore[union-attr]
    assert (tmp_path / ".vibey/context/visual/screen-inventory.md").exists()
    saved = await inventories.load(project_id, 1)
    assert saved is not None
    assert saved.surfaces[0].screen_id == "home"
