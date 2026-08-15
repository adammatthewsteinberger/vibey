"""Composition root: the only module that wires concrete adapters to ports."""

import getpass
import os
from collections.abc import AsyncIterator, Sequence
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Protocol

import asyncpg

from vibey.application.design import DesignEvent, DesignStage, QuestionBatch, ResearchResult
from vibey.application.design_handler import DesignInterviewHandler
from vibey.application.design_research_handler import DesignResearchHandler
from vibey.application.design_synthesis_handler import DesignSpecHandler, DesignSynthesizeHandler
from vibey.application.dto import ProjectRecord
from vibey.application.job_dispatcher import JobDispatcher
from vibey.application.visual_handler import VisualInventoryHandler, VisualPlanHandler
from vibey.application.worker import WorkerLoop
from vibey.domain.engine import EngineId
from vibey.domain.spec import DesignSpec
from vibey.domain.visual import VisualInventory
from vibey.infrastructure.db.design_ledger import PostgresDesignLedger
from vibey.infrastructure.db.design_spec_repository import FileDesignSpecRepository
from vibey.infrastructure.db.human_gate_repository import PostgresHumanGateRepository
from vibey.infrastructure.db.job_repository import PostgresJobRepository
from vibey.infrastructure.db.ledger_repository import PostgresLedgerRepository
from vibey.infrastructure.db.migrator import apply_migrations, discover_migrations
from vibey.infrastructure.db.project_repository import PostgresProjectRepository
from vibey.infrastructure.db.visual_inventory_repository import FileVisualInventoryRepository


@dataclass(frozen=True, slots=True)
class AppResources:
    projects: PostgresProjectRepository
    jobs: PostgresJobRepository
    gates: PostgresHumanGateRepository
    ledger: PostgresLedgerRepository
    design_ledger: PostgresDesignLedger
    design_specs: FileDesignSpecRepository
    visual_inventories: FileVisualInventoryRepository


class DesignProvider(Protocol):
    async def batch(
        self, stage: DesignStage, prior_events: Sequence[DesignEvent]
    ) -> QuestionBatch: ...

    async def research(self, topic: str) -> ResearchResult: ...

    async def synthesize(self, events: Sequence[DesignEvent]) -> DesignSpec: ...


class VisualProvider(Protocol):
    async def inventory(self, events: Sequence[DesignEvent]) -> VisualInventory: ...


class SystemClock:
    def now(self) -> datetime:
        return datetime.now(UTC)


def build_design_worker(
    *, resources: AppResources, project: ProjectRecord, provider: DesignProvider, owner: str
) -> WorkerLoop:
    clock = SystemClock()
    dispatcher = JobDispatcher(
        {
            "design.interview": DesignInterviewHandler(
                ledger=resources.design_ledger,
                jobs=resources.jobs,
                gates=resources.gates,
                questions=provider,
                clock=clock,
                interviewer=EngineId.CLAUDELOOP,
            ),
            "design.research": DesignResearchHandler(
                ledger=resources.design_ledger,
                researcher=provider,
                clock=clock,
                engine_id=EngineId.CLAUDELOOP,
            ),
            "design.synthesize": DesignSynthesizeHandler(
                ledger=resources.design_ledger,
                synthesizer=provider,
                specs=resources.design_specs,
            ),
            "design.spec": DesignSpecHandler(specs=resources.design_specs),
        }
    )
    return WorkerLoop(
        jobs=resources.jobs,
        gates=resources.gates,
        handler=dispatcher,
        owner=owner,
    )


def build_visual_worker(
    *, resources: AppResources, provider: VisualProvider, owner: str
) -> WorkerLoop:
    dispatcher = JobDispatcher(
        {
            "visual.inventory": VisualInventoryHandler(
                ledger=resources.design_ledger,
                producer=provider,
                inventories=resources.visual_inventories,
                jobs=resources.jobs,
            ),
            "visual.plan": VisualPlanHandler(inventories=resources.visual_inventories),
        }
    )
    return WorkerLoop(
        jobs=resources.jobs,
        gates=resources.gates,
        handler=dispatcher,
        owner=owner,
    )


def database_url() -> str:
    return os.environ.get("VIBEY_PG_URL", f"postgresql://{getpass.getuser()}@localhost:5432/vibey")


@asynccontextmanager
async def build_app(*, url: str | None = None) -> AsyncIterator[AppResources]:
    pool = await asyncpg.create_pool(url or database_url(), min_size=1, max_size=10)
    if pool is None:
        raise RuntimeError("asyncpg did not create a pool")
    try:
        migrations_dir = Path(__file__).resolve().parents[2] / "migrations"
        async with pool.acquire() as conn:
            await apply_migrations(conn, discover_migrations(migrations_dir))
        projects = PostgresProjectRepository(pool)
        ledger = PostgresLedgerRepository(pool)
        yield AppResources(
            projects=projects,
            jobs=PostgresJobRepository(pool),
            gates=PostgresHumanGateRepository(pool),
            ledger=ledger,
            design_ledger=PostgresDesignLedger(ledger),
            design_specs=FileDesignSpecRepository(projects),
            visual_inventories=FileVisualInventoryRepository(projects),
        )
    finally:
        await pool.close()
