# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
"""Composition root: the only module that wires concrete adapters to ports."""

import asyncio
import os
from collections.abc import AsyncIterator, Awaitable, Callable, Mapping
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path
from uuid import UUID

import asyncpg

from vibey.application.budget_source import LedgerBudgetSource
from vibey.application.build_decompose_handler import BuildDecomposeHandler
from vibey.application.build_implement_handler import BuildImplementHandler
from vibey.application.build_integrate_handler import BuildIntegrateHandler
from vibey.application.build_verify_handler import BuildVerifyHandler, VerifyRepairPolicy
from vibey.application.deploy_acceptance_handler import DeployAcceptanceHandler
from vibey.application.deploy_design_bridge import DeployDesignBridgeHandler
from vibey.application.deploy_design_handler import (
    DeployInterviewHandler,
    DeploySynthesizeHandler,
)
from vibey.application.deploy_execute_handler import DeployExecuteHandler
from vibey.application.deploy_review_handler import (
    DeployReviewDemoHandler,
    DeployReviewTriageHandler,
)
from vibey.application.deploy_review_routing import DeployReviewRoutingHandler
from vibey.application.design_handler import DesignInterviewHandler
from vibey.application.design_research_handler import DesignResearchHandler
from vibey.application.design_synthesis_handler import DesignSpecHandler, DesignSynthesizeHandler
from vibey.application.dto import JobRecord, ProjectRecord
from vibey.application.engine_health_service import EngineHealthService
from vibey.application.engine_selection import RotationRecordingHandler, SelectingEngineProvider
from vibey.application.engine_selector import EngineSelector
from vibey.application.interfaces import (
    AzureClientPort,
    Clock,
    DesignProvider,
    EngineAdapter,
    JobHandler,
    VisualInventoryProducer,
    WorkPlanProducer,
)
from vibey.application.job_dispatcher import JobDispatcher
from vibey.application.review_collect_handler import ReviewCollectHandler
from vibey.application.review_demo_handler import ReviewDemoHandler
from vibey.application.review_deployment_choice_handler import ReviewDeploymentChoiceHandler
from vibey.application.review_triage_handler import ReviewTriageHandler
from vibey.application.rotation_handoff import RotationHandoffService
from vibey.application.visual_handler import VisualInventoryHandler, VisualPlanHandler
from vibey.application.wind_down import WindDownOrchestrator
from vibey.application.worker import WorkerLoop
from vibey.domain.engine import EngineId
from vibey.domain.errors import VibeyError
from vibey.domain.phase import Phase
from vibey.infrastructure.azure.adapter import InMemoryAzureClientAdapter
from vibey.infrastructure.build.automated_review_runner import SubprocessAutomatedReviewRunner
from vibey.infrastructure.build.gate_runner import SubprocessGateRunner
from vibey.infrastructure.db.advisory_lock import PostgresAdvisoryLock
from vibey.infrastructure.db.build_ledger import PostgresBuildLedger
from vibey.infrastructure.db.design_ledger import PostgresDesignLedger
from vibey.infrastructure.db.design_spec_repository import FileDesignSpecRepository
from vibey.infrastructure.db.engine_health_repository import PostgresEngineHealthRepository
from vibey.infrastructure.db.handoff_repository import PostgresHandoffRepository
from vibey.infrastructure.db.human_gate_repository import PostgresHumanGateRepository
from vibey.infrastructure.db.job_repository import PostgresJobRepository
from vibey.infrastructure.db.ledger_repository import PostgresLedgerRepository
from vibey.infrastructure.db.migrator import apply_migrations, discover_migrations
from vibey.infrastructure.db.project_repository import PostgresProjectRepository
from vibey.infrastructure.db.review_ledger import PostgresReviewLedger
from vibey.infrastructure.db.rotation_cursor_repository import PostgresRotationCursorRepository
from vibey.infrastructure.db.visual_inventory_repository import FileVisualInventoryRepository
from vibey.infrastructure.deploy.state_repository import FileDeploymentStateRepository
from vibey.infrastructure.engines.descriptors import BY_ENGINE_ID, DEFAULT_DESCRIPTORS, QWENLOOP
from vibey.infrastructure.engines.loop_process_adapter import LoopProcessAdapter
from vibey.infrastructure.git.integration_branch import IntegrationBranch
from vibey.infrastructure.git.worktree_manager import GitWorktreeManager
from vibey.infrastructure.ledger.full_ledger_writer import write_full_ledger
from vibey.infrastructure.provision.agent_surface import AgentSurfaceProvisioner
from vibey.infrastructure.review_artifact_writer import FileReviewArtifactWriter
from vibey.infrastructure.skills_context import compiler_from_config


@dataclass(frozen=True, slots=True)
class AppResources:
    projects: PostgresProjectRepository
    jobs: PostgresJobRepository
    gates: PostgresHumanGateRepository
    ledger: PostgresLedgerRepository
    design_ledger: PostgresDesignLedger
    design_specs: FileDesignSpecRepository
    visual_inventories: FileVisualInventoryRepository
    # Phase-specific ledger adapters over the one append-only event log.
    build_ledger: PostgresBuildLedger
    review_ledger: PostgresReviewLedger
    deploy_review_ledger: PostgresReviewLedger
    # Rotation infrastructure (Phase E1)
    engine_health_repo: PostgresEngineHealthRepository
    rotation_cursors: PostgresRotationCursorRepository
    engine_health_service: EngineHealthService
    engine_selector: EngineSelector
    rotation_handoff: RotationHandoffService
    engine_adapters: Mapping[EngineId, EngineAdapter]
    handoffs: PostgresHandoffRepository
    clock: Clock
    integration_lock: PostgresAdvisoryLock | None = None


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
    *, resources: AppResources, provider: VisualInventoryProducer, owner: str
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


@dataclass(frozen=True, slots=True)
class _ClosureFactory:
    """JobHandlerFactory over a construction closure. The closures are
    defined inside build_full_worker, the only place allowed to see every
    concrete class -- keeping per-job construction (and per-job engine
    selection) in the composition root."""

    build: Callable[[JobRecord], Awaitable[JobHandler]]

    async def create(self, job: JobRecord) -> JobHandler:
        return await self.build(job)


_KIND_LEASES: Mapping[str, timedelta] = {
    # Engine-driven jobs run for hours; control-plane jobs for minutes.
    # Everything unlisted gets a 2-minute lease (still >> the heartbeat
    # interval of lease/3, so a healthy worker never loses one).
    "build.implement": timedelta(hours=2),
    "build.verify": timedelta(hours=2),
    "build.decompose": timedelta(minutes=15),
    "build.plan": timedelta(minutes=15),
    "build.integrate": timedelta(minutes=15),
}


def lease_for_kind(kind: str) -> timedelta:
    return _KIND_LEASES.get(kind, timedelta(minutes=2))


async def preflight_sweep(
    *,
    resources: AppResources,
    project_id: UUID,
    adapters: Mapping[EngineId, EngineAdapter],
) -> tuple[EngineId, ...]:
    """Refresh installed/version/auth for every configured engine, then
    return the engines still ineligible for engine-driven jobs (no recorded
    conformance) so the caller can warn -- conformance itself is granted
    only by `vibey doctor --conformance --record`.

    Preflights run concurrently: each engine's doctor does real network
    auth verification (~60s for claudeloop), and running them in sequence
    made worker startup scale linearly with engine count."""
    engine_ids = tuple(adapters)
    preflights = await asyncio.gather(
        *(adapters[engine_id].preflight() for engine_id in engine_ids)
    )
    for engine_id, preflight in zip(engine_ids, preflights, strict=True):
        await resources.engine_health_service.record_preflight(project_id, engine_id, preflight)
    records = await resources.engine_health_service.list_for_project(project_id)
    by_id = {record.engine_id: record for record in records}
    return tuple(
        engine_id
        for engine_id in adapters
        if engine_id not in by_id or not by_id[engine_id].conformance_ok
    )


def _qwenloop_enabled(config: Mapping[str, object]) -> bool:
    override = os.environ.get("VIBEY_FEATURE_QWENLOOP")
    if override is not None:
        return override.strip().lower() in {"1", "true", "yes", "on"}
    features = config.get("features")
    return isinstance(features, Mapping) and features.get("qwenloop") is True


def build_full_worker(
    *,
    resources: AppResources,
    project: ProjectRecord,
    design_provider: DesignProvider,
    visual_provider: VisualInventoryProducer,
    decomposer: WorkPlanProducer,
    owner: str,
    engine_adapters: Mapping[EngineId, EngineAdapter] | None = None,
    allow_list: frozenset[EngineId] | None = None,
    azure_client: AzureClientPort | None = None,
) -> WorkerLoop:
    """The full-phase dispatcher: every job kind vibey enqueues, routed.

    `engine_adapters` overrides resources.engine_adapters -- the faked
    harness injects ScriptedEngines here instead of patching. Engine-driven
    BUILD jobs select their engine per job via the rotation stack
    (SelectingEngineProvider -> EngineSelector SWRR), honoring the
    `allow_list`; selection requires populated engine_health records
    (`vibey doctor --conformance --record` + the worker's startup preflight
    sweep). `azure_client` defaults to the in-memory adapter -- real `az`
    wiring is an explicit later decision, never an accidental default.
    """
    adapters = dict(engine_adapters if engine_adapters is not None else resources.engine_adapters)
    qwenloop_enabled = _qwenloop_enabled(project.config)
    if qwenloop_enabled and EngineId.QWENLOOP not in adapters:
        adapters[EngineId.QWENLOOP] = LoopProcessAdapter(descriptor=QWENLOOP)
    azure = azure_client if azure_client is not None else InMemoryAzureClientAdapter()
    clock = resources.clock
    repo_root = Path(project.repo_path)
    deploy_state = FileDeploymentStateRepository(repo_root)
    deploy_design_ledger = PostgresReviewLedger(resources.ledger, phase=Phase.DEPLOY_DESIGN)
    deploy_execute_ledger = PostgresReviewLedger(resources.ledger, phase=Phase.DEPLOY_EXECUTE)
    engine_provider = SelectingEngineProvider(
        selector=resources.engine_selector,
        health=resources.engine_health_service,
        adapters=adapters,
        jobs=resources.jobs,
        clock=clock,
        owner=owner,
        allow_list=allow_list,
        standby_engine=EngineId.QWENLOOP if qwenloop_enabled else None,
    )
    # The runaway brake: caps come from the project's own config
    # (max_cycle_dollars / max_cycle_turns, set at `vibey new`). Without
    # either, spend stays uncapped -- opting in is explicit, never a
    # silent default that would surprise existing projects.
    raw_dollars = project.config.get("max_cycle_dollars")
    raw_turns = project.config.get("max_cycle_turns")
    budget_source: LedgerBudgetSource | None = None
    if isinstance(raw_dollars, int | float) or isinstance(raw_turns, int):
        budget_source = LedgerBudgetSource(
            resources.ledger,
            max_dollars=float(raw_dollars) if isinstance(raw_dollars, int | float) else None,
            max_turns=raw_turns if isinstance(raw_turns, int) else None,
        )
    wind_down = WindDownOrchestrator(
        ledger=resources.ledger,
        handoff_service=RotationHandoffService(resources.engine_selector, allow_list=allow_list),
        handoffs=resources.handoffs,
        jobs=resources.jobs,
        clock=clock,
        write_ledger=write_full_ledger,
    )
    skills_context = compiler_from_config(project.config, repo_path=repo_root)

    def _recording(handler: JobHandler, adapter: EngineAdapter) -> JobHandler:
        return RotationRecordingHandler(
            inner=handler,
            health=resources.engine_health_service,
            project_id=project.project_id,
            engine_id=adapter.descriptor.engine_id,
        )

    async def _implement(job: JobRecord) -> JobHandler:
        adapter = await engine_provider.select_for(job)
        handler = BuildImplementHandler(
            worktrees=GitWorktreeManager(repo_root, cycle=job.cycle),
            provisioner=AgentSurfaceProvisioner(),
            engine=adapter,
            ledger=resources.build_ledger,
            jobs=resources.jobs,
            clock=clock,
            wind_down=wind_down,
            human_gates=resources.gates,
            budget_source=budget_source,
            skills_context=skills_context,
        )
        return _recording(handler, adapter)

    async def _verify(job: JobRecord) -> JobHandler:
        adapter = await engine_provider.select_for(job)
        handler = BuildVerifyHandler(
            worktrees=GitWorktreeManager(repo_root, cycle=job.cycle),
            gates=SubprocessGateRunner(),
            reviewer=adapter,
            ledger=resources.build_ledger,
            jobs=resources.jobs,
            repair=VerifyRepairPolicy(
                ledger_reader=resources.ledger, clock=clock, gates=resources.gates
            ),
        )
        return _recording(handler, adapter)

    async def _integrate(job: JobRecord) -> JobHandler:
        return BuildIntegrateHandler(
            integration=IntegrationBranch(repo_root, cycle=job.cycle),
            gates=SubprocessGateRunner(),
            ledger=resources.build_ledger,
            jobs=resources.jobs,
            clock=clock,
            projects=resources.projects,
            lock=resources.integration_lock,
            ledger_reader=resources.ledger,
            human_gates=resources.gates,
        )

    handlers: dict[str, JobHandler] = {
        "design.interview": DesignInterviewHandler(
            ledger=resources.design_ledger,
            jobs=resources.jobs,
            gates=resources.gates,
            questions=design_provider,
            clock=clock,
            interviewer=EngineId.CLAUDELOOP,
        ),
        "design.research": DesignResearchHandler(
            ledger=resources.design_ledger,
            researcher=design_provider,
            clock=clock,
            engine_id=EngineId.CLAUDELOOP,
        ),
        "design.synthesize": DesignSynthesizeHandler(
            ledger=resources.design_ledger,
            synthesizer=design_provider,
            specs=resources.design_specs,
        ),
        "design.spec": DesignSpecHandler(specs=resources.design_specs),
        "visual.inventory": VisualInventoryHandler(
            ledger=resources.design_ledger,
            producer=visual_provider,
            inventories=resources.visual_inventories,
            jobs=resources.jobs,
        ),
        "visual.plan": VisualPlanHandler(inventories=resources.visual_inventories),
        "build.decompose": BuildDecomposeHandler(
            specs=resources.design_specs,
            decomposer=decomposer,
            jobs=resources.jobs,
        ),
        "review.demo": ReviewDemoHandler(
            specs=resources.design_specs,
            ledger=resources.review_ledger,
            artifacts=FileReviewArtifactWriter(resources.projects),
            jobs=resources.jobs,
            clock=clock,
            automated_reviewer=SubprocessAutomatedReviewRunner(
                projects=resources.projects,
                gates=SubprocessGateRunner(),
            ),
        ),
        "review.collect": ReviewCollectHandler(
            ledger=resources.review_ledger,
            gates=resources.gates,
            jobs=resources.jobs,
            clock=clock,
        ),
        "review.triage": ReviewTriageHandler(
            ledger=resources.review_ledger,
            specs=resources.design_specs,
            jobs=resources.jobs,
            clock=clock,
            projects=resources.projects,
            spec_store=resources.design_specs,
        ),
        "review.deployment_choice": ReviewDeploymentChoiceHandler(
            ledger=resources.review_ledger,
            gates=resources.gates,
            jobs=resources.jobs,
            projects=resources.projects,
            clock=clock,
        ),
        "deploy.design": DeployDesignBridgeHandler(
            jobs=resources.jobs,
            projects=resources.projects,
        ),
        "deploy.interview": DeployInterviewHandler(
            ledger=deploy_design_ledger,
            gates=resources.gates,
            clock=clock,
            jobs=resources.jobs,
        ),
        "deploy.synthesize": DeploySynthesizeHandler(
            ledger=deploy_design_ledger,
            clock=clock,
            jobs=resources.jobs,
            spec_store=deploy_state,
        ),
        "deploy.spec": DeployAcceptanceHandler(
            ledger=deploy_design_ledger,
            gates=resources.gates,
            jobs=resources.jobs,
            projects=resources.projects,
            clock=clock,
            spec_provider=deploy_state.load_spec,
            consent_store=deploy_state,
        ),
        "deploy.execute": DeployExecuteHandler(
            ledger=deploy_execute_ledger,
            jobs=resources.jobs,
            projects=resources.projects,
            azure_client=azure,
            clock=clock,
            spec_provider=deploy_state.load_spec,
            consent_provider=deploy_state.load_consent,
        ),
        "deploy.demo": DeployReviewDemoHandler(
            ledger=resources.deploy_review_ledger,
            human_gates=resources.gates,
            jobs=resources.jobs,
            spec_provider=deploy_state.load_spec,
        ),
        "deploy.triage": DeployReviewTriageHandler(
            ledger=resources.deploy_review_ledger,
            human_gates=resources.gates,
            jobs=resources.jobs,
            spec_provider=deploy_state.load_spec,
        ),
        "deploy.route": DeployReviewRoutingHandler(
            ledger=resources.deploy_review_ledger,
            jobs=resources.jobs,
            projects=resources.projects,
            azure_client=azure,
            spec_provider=deploy_state.load_spec,
            consent_provider=deploy_state.load_consent,
        ),
    }
    # Alias kinds sharing a handler (the handlers themselves guard on both).
    handlers["build.plan"] = handlers["build.decompose"]
    handlers["deploy.accept"] = handlers["deploy.spec"]
    handlers["deploy.graph"] = handlers["deploy.execute"]

    dispatcher = JobDispatcher(
        handlers,
        factories={
            "build.implement": _ClosureFactory(_implement),
            "build.verify": _ClosureFactory(_verify),
            "build.integrate": _ClosureFactory(_integrate),
        },
    )
    return WorkerLoop(
        jobs=resources.jobs,
        gates=resources.gates,
        handler=dispatcher,
        owner=owner,
        lease_for_kind=lease_for_kind,
    )


class DatabaseNotConfigured(VibeyError):
    """VIBEY_PG_URL is unset and there is no safe default to invent."""

    def __init__(self) -> None:
        super().__init__(
            "VIBEY_PG_URL is not set. vibey will not guess a database.\n"
            "  export VIBEY_PG_URL=postgresql://user@localhost:5432/vibey"
        )


def database_url() -> str:
    """The DSN, or an error -- never a guess.

    This used to fall back to postgresql://<user>@localhost:5432/vibey. That
    is not the resolution order the architecture describes (an explicit DSN,
    then a Compose service, then a managed cluster under .vibey/pgdata); it
    was an undocumented shortcut that resolved to whatever database happened
    to be named `vibey` on the machine.

    It cost real data integrity. Eight autonomous BUILD jobs ran the test
    suite in their worktrees with VIBEY_PG_URL unset; every test that called
    build_app() without an explicit url took this fallback and wrote to the
    PRODUCTION database, creating 78 projects in eleven minutes. Nothing
    failed, because a silent default cannot fail -- that is the whole
    problem with it. Refusing is the fix: a tool that writes to a database
    should be told which one.
    """
    url = os.environ.get("VIBEY_PG_URL")
    if not url:
        raise DatabaseNotConfigured
    return url


def migrations_dir() -> Path:
    """Resolved relative to this file so it works from a source checkout and
    from the image alike (/app/src/vibey/bootstrap.py -> /app/migrations).
    Derived in one place because two copies of this arithmetic would drift
    silently -- the image's layout depends on it."""
    return Path(__file__).resolve().parents[2] / "migrations"


@asynccontextmanager
async def build_app(*, url: str | None = None) -> AsyncIterator[AppResources]:
    pool = await asyncpg.create_pool(url or database_url(), min_size=1, max_size=10)
    if pool is None:
        raise RuntimeError("asyncpg did not create a pool")
    try:
        async with pool.acquire() as conn:
            await apply_migrations(conn, discover_migrations(migrations_dir()))

        projects = PostgresProjectRepository(pool)
        ledger = PostgresLedgerRepository(pool)

        # Build rotation infrastructure (Phase E1)
        engine_health_repo = PostgresEngineHealthRepository(pool)
        rotation_cursors = PostgresRotationCursorRepository(pool)
        engine_health_service = EngineHealthService(engine_health_repo)
        engine_selector = EngineSelector(
            health_service=engine_health_service,
            cursor_repository=rotation_cursors,
            descriptors=BY_ENGINE_ID,
        )
        rotation_handoff = RotationHandoffService(engine_selector)

        # Build engine adapters
        engine_adapters = {
            desc.engine_id: LoopProcessAdapter(descriptor=desc) for desc in DEFAULT_DESCRIPTORS
        }

        yield AppResources(
            projects=projects,
            jobs=PostgresJobRepository(pool),
            gates=PostgresHumanGateRepository(pool),
            ledger=ledger,
            design_ledger=PostgresDesignLedger(ledger),
            design_specs=FileDesignSpecRepository(projects),
            visual_inventories=FileVisualInventoryRepository(projects),
            build_ledger=PostgresBuildLedger(ledger),
            review_ledger=PostgresReviewLedger(ledger),
            deploy_review_ledger=PostgresReviewLedger(ledger, phase=Phase.DEPLOY_REVIEW),
            engine_health_repo=engine_health_repo,
            rotation_cursors=rotation_cursors,
            engine_health_service=engine_health_service,
            engine_selector=engine_selector,
            rotation_handoff=rotation_handoff,
            engine_adapters=engine_adapters,
            handoffs=PostgresHandoffRepository(pool),
            clock=SystemClock(),
            integration_lock=PostgresAdvisoryLock(pool),
        )
    finally:
        await pool.close()


# Re-exported for the same reason `application/ports.py` re-exports the
# interfaces package: the seam moved, the import path should not break.
__all__ = [
    "DesignProvider",
    "VisualInventoryProducer",
]
