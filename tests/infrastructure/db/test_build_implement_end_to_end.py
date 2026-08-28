# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Real-Postgres, real-git, real-worktree end-to-end covering M6's whole
implement->verify->integrate loop: decompose -> worktree -> provision ->
implement -> gates -> diff review -> merge into the integration branch ->
post-merge gates -> ledger, driven entirely through the actual queue
(WorkerLoop), same shape as test_design_interview_end_to_end.py."""

from datetime import UTC, datetime
from pathlib import Path

import asyncpg

from vibey.application.build_decompose_handler import BuildDecomposeHandler
from vibey.application.build_implement_handler import BuildImplementHandler
from vibey.application.build_integrate_handler import BuildIntegrateHandler
from vibey.application.build_verify_handler import BuildVerifyHandler
from vibey.application.dto import EnqueueRequest
from vibey.application.job_dispatcher import JobDispatcher
from vibey.application.worker import WorkerLoop
from vibey.domain.effort import Effort
from vibey.domain.job import JobState, idempotency_key
from vibey.domain.phase import Phase
from vibey.domain.plan import VerificationSpec, WorkItem
from vibey.domain.spec import AcceptanceCriterion, DesignSpec
from vibey.infrastructure.build.gate_runner import SubprocessGateRunner
from vibey.infrastructure.db.build_ledger import PostgresBuildLedger
from vibey.infrastructure.db.design_spec_repository import FileDesignSpecRepository
from vibey.infrastructure.db.human_gate_repository import PostgresHumanGateRepository
from vibey.infrastructure.db.job_repository import PostgresJobRepository
from vibey.infrastructure.db.ledger_repository import PostgresLedgerRepository
from vibey.infrastructure.db.project_repository import PostgresProjectRepository
from vibey.infrastructure.engines.descriptors import CLAUDELOOP, CODEXLOOP
from vibey.infrastructure.engines.scripted import ScriptedEngine
from vibey.infrastructure.git.clean_env import CleanGitEnvSubprocessExecutor
from vibey.infrastructure.git.integration_branch import IntegrationBranch
from vibey.infrastructure.git.worktree_manager import GitWorktreeManager
from vibey.infrastructure.provision.agent_surface import AgentSurfaceProvisioner


class FixedClock:
    def now(self) -> datetime:
        return datetime(2026, 8, 14, tzinfo=UTC)


class Decomposer:
    async def decompose(self, spec: DesignSpec) -> tuple[WorkItem, ...]:
        return (
            WorkItem(
                item_id="skeleton",
                title="walking skeleton",
                acceptance_ids=("AC-1",),
                depends_on=(),
                est_effort=Effort.LOW,
                files_touched_hint=(),
                verification=VerificationSpec(commands=("true",), criteria_checked=("AC-1",)),
            ),
        )


async def _run(*argv: str) -> None:
    result = await CleanGitEnvSubprocessExecutor().execute(argv)
    assert result.returncode == 0, result.stderr


async def test_decompose_implement_verify_integrate_run_end_to_end_through_the_queue(
    migrated_pool: asyncpg.Pool, tmp_path: Path
) -> None:
    repo_path = tmp_path / "repo"
    repo_path.mkdir()
    await _run("git", "-C", str(repo_path), "init", "-q", "-b", "main")
    await _run("git", "-C", str(repo_path), "config", "user.email", "test@example.com")
    await _run("git", "-C", str(repo_path), "config", "user.name", "Test")
    (repo_path / "README.md").write_text("hello\n")
    await _run("git", "-C", str(repo_path), "add", "README.md")
    await _run("git", "-C", str(repo_path), "commit", "-q", "-m", "initial")

    projects = PostgresProjectRepository(migrated_pool)
    project = await projects.create("scripted-build", repo_path, max_cycles=10, config={})
    project_id = project.project_id
    jobs = PostgresJobRepository(migrated_pool)
    gates = PostgresHumanGateRepository(migrated_pool)
    ledger_repo = PostgresLedgerRepository(migrated_pool)
    specs = FileDesignSpecRepository(projects)

    spec = DesignSpec(
        "Ship",
        (),
        (),
        (AcceptanceCriterion("AC-1", "given", "when", "then", "fit"),),
        (),
        "walking skeleton",
    )
    await specs.save(project_id, 1, spec)

    decompose_job = await jobs.enqueue(
        EnqueueRequest(
            project_id=project_id,
            cycle=1,
            phase=Phase.BUILD,
            kind="build.decompose",
            idempotency_key=idempotency_key(project_id, 1, "build.decompose", "entry"),
        )
    )

    dispatcher = JobDispatcher(
        {
            "build.decompose": BuildDecomposeHandler(
                specs=specs, decomposer=Decomposer(), jobs=jobs
            ),
            "build.implement": BuildImplementHandler(
                worktrees=GitWorktreeManager(repo_path, cycle=1),
                provisioner=AgentSurfaceProvisioner(),
                engine=ScriptedEngine(descriptor=CLAUDELOOP, base_dir=tmp_path / "engine"),
                ledger=PostgresBuildLedger(ledger_repo),
                jobs=jobs,
                clock=FixedClock(),
            ),
            "build.verify": BuildVerifyHandler(
                worktrees=GitWorktreeManager(repo_path, cycle=1),
                gates=SubprocessGateRunner(),
                reviewer=ScriptedEngine(descriptor=CODEXLOOP, base_dir=tmp_path / "engine"),
                ledger=PostgresBuildLedger(ledger_repo),
                jobs=jobs,
            ),
            "build.integrate": BuildIntegrateHandler(
                integration=IntegrationBranch(repo_path, cycle=1),
                gates=SubprocessGateRunner(),
                ledger=PostgresBuildLedger(ledger_repo),
                jobs=jobs,
                clock=FixedClock(),
            ),
        }
    )
    worker = WorkerLoop(jobs=jobs, gates=gates, handler=dispatcher, owner="build-worker")

    assert await worker.run_once(project_id)  # build.decompose
    assert await worker.run_once(project_id)  # build.implement
    assert await worker.run_once(project_id)  # build.verify
    assert await worker.run_once(project_id)  # build.integrate

    async with migrated_pool.acquire() as conn:
        rows = await conn.fetch("SELECT kind, state FROM job WHERE project_id = $1", project_id)
    states = {row["kind"]: row["state"] for row in rows}
    assert states == {
        "build.decompose": JobState.SUCCEEDED.value,
        "build.implement": JobState.SUCCEEDED.value,
        "build.verify": JobState.SUCCEEDED.value,
        "build.integrate": JobState.SUCCEEDED.value,
    }

    integration_path = repo_path / ".vibey" / "worktrees" / "1" / "integration"
    assert integration_path.exists()

    worktree = repo_path / ".vibey" / "worktrees" / "1" / "skeleton"
    assert worktree.exists()
    assert (worktree / "CLAUDE.md").exists()
    assert (worktree / "AGENTS.md").exists()

    ledger_events = await ledger_repo.all_for_project(project_id)
    build_events = [e for e in ledger_events if e.phase is Phase.BUILD]
    assert build_events
    assert any(e.kind.value == "VerdictRendered" for e in build_events)

    decompose_record = await jobs.get(decompose_job.id)
    assert decompose_record is not None
    assert decompose_record.state is JobState.SUCCEEDED
