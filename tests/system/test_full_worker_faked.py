"""Faked full-worker E2E (worker-orchestration plan, milestone test A).

A real project travels INTAKE -> DESIGN -> BUILD -> REVIEW -> DONE(local)
through `bootstrap.build_full_worker`'s dispatcher against real Postgres and
a real temp git repository -- ScriptedEngine adapters and scripted providers
stand in for models, but every queue transition, gate park/answer/resume,
worktree, merge, subprocess gate, and ledger write is the production code
path `vibey worker` runs.
"""

import asyncio
import os
import re
import subprocess  # nosec B404 - fixed argv, never shell=True
from pathlib import Path
from uuid import UUID

import asyncpg
import pytest

from vibey.application.design_acceptance import DesignAcceptanceService
from vibey.application.dto import EnqueueRequest
from vibey.bootstrap import build_app, build_full_worker, database_url
from vibey.domain.job import JobState, idempotency_key
from vibey.domain.phase import Phase, VisualDecision
from vibey.infrastructure.azure.adapter import InMemoryAzureClientAdapter
from vibey.infrastructure.deploy.state_repository import FileDeploymentStateRepository
from vibey.infrastructure.engines.descriptors import BY_ENGINE_ID
from vibey.infrastructure.engines.scripted import ScriptedEngine
from vibey.infrastructure.engines.scripted_decompose import ScriptedWorkPlanProducer
from vibey.infrastructure.engines.scripted_design import ScriptedDesignProvider
from vibey.infrastructure.engines.scripted_visual import ScriptedVisualProvider

pytestmark = pytest.mark.system


@pytest.fixture(autouse=True)
async def _use_test_database(monkeypatch: pytest.MonkeyPatch) -> None:
    url = os.environ.get(
        "VIBEY_TEST_DATABASE_URL",
        f"postgresql://{os.environ.get('USER', 'postgres')}@localhost:5432/vibey_test",
    )
    monkeypatch.setenv("VIBEY_PG_URL", url)
    conn = await asyncpg.connect(database_url())
    await conn.execute("DROP SCHEMA IF EXISTS public CASCADE")
    await conn.execute("CREATE SCHEMA IF NOT EXISTS public")
    await conn.close()


def _git(repo: Path, *argv: str) -> None:
    subprocess.run(  # nosec B603
        ("git", "-C", str(repo), *argv), check=True, capture_output=True
    )


def _make_repo(root: Path) -> Path:
    """A scratch repo whose contents pass the real automated review commands
    (bandit -q -r src; ruff check .) that review.demo runs."""
    repo = root / "repo"
    (repo / "src").mkdir(parents=True)
    (repo / "src" / "app.py").write_text("def main() -> int:\n    return 0\n")
    subprocess.run(("git", "init", "-q", str(repo)), check=True)  # nosec B603
    _git(repo, "config", "user.email", "e2e@vibey.local")
    _git(repo, "config", "user.name", "vibey e2e")
    _git(repo, "add", ".")
    _git(repo, "commit", "-q", "-m", "init")
    return repo


async def _open_gate(project_id: UUID) -> tuple[UUID, str, str] | None:
    conn = await asyncpg.connect(database_url())
    try:
        row = await conn.fetchrow(
            """
            SELECT gate_id, kind, prompt FROM human_gate
            WHERE project_id = $1 AND answered_at IS NULL
            ORDER BY raised_at LIMIT 1
            """,
            project_id,
        )
    finally:
        await conn.close()
    if row is None:
        return None
    return row["gate_id"], str(row["kind"]), str(row["prompt"])


def _answer_for(kind: str, prompt: str, *, deploy: bool) -> dict[str, object]:
    if kind == "choice":
        return {"choice": "deploy" if deploy else "local_only"}
    if kind == "approval":
        return {"verdict": "accept"}
    if kind == "deploy_interview":
        return {"choice": "accept_defaults"}
    if kind == "deploy_acceptance":
        return {"verdict": "accept", "explicit_mutation_authorized": True}
    if kind == "deploy_demo_review":
        return {"verdict": "approve"}
    question_ids = sorted(set(re.findall(r"\bq-(\d+)\b", prompt)), key=int)
    return {"answers": {f"q-{n}": f"scripted-default-{n}" for n in question_ids}}


async def test_full_worker_drives_a_project_to_done_local(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)

    async with build_app() as resources:
        project = await resources.projects.create("faked-e2e", repo, max_cycles=3, config={})
        project_id = project.project_id
        await resources.projects.transition(project_id, expected=Phase.INTAKE, to=Phase.DESIGN)
        await resources.jobs.enqueue(
            EnqueueRequest(
                project_id=project_id,
                cycle=project.cycle,
                phase=Phase.DESIGN,
                kind="design.interview",
                idempotency_key=idempotency_key(
                    project_id, project.cycle, "design.interview", "interactive"
                ),
                requirement={"effort": "high"},
            )
        )

        adapters = {
            engine_id: ScriptedEngine(
                descriptor=descriptor, base_dir=tmp_path / "engines" / engine_id.value
            )
            for engine_id, descriptor in BY_ENGINE_ID.items()
        }
        worker = build_full_worker(
            resources=resources,
            project=project,
            design_provider=ScriptedDesignProvider(),
            visual_provider=ScriptedVisualProvider(),
            decomposer=ScriptedWorkPlanProducer(),
            owner="e2e-worker",
            engine_adapters=adapters,
        )

        accepted_design = False
        for _ in range(150):
            if await worker.run_once(project_id):
                continue

            gate = await _open_gate(project_id)
            if gate is not None:
                gate_id, kind, prompt = gate
                await resources.gates.answer(
                    gate_id, answer=_answer_for(kind, prompt, deploy=False), answered_by="e2e"
                )
                continue

            current = await resources.projects.get(project_id)
            assert current is not None
            if current.phase is Phase.DONE:
                break
            if current.phase is Phase.DESIGN and not accepted_design:
                await DesignAcceptanceService(
                    projects=resources.projects,
                    ledger=resources.design_ledger,
                    specs=resources.design_specs,
                    jobs=resources.jobs,
                    clock=resources.clock,
                ).accept(project_id, visual_choice=VisualDecision.DECLINED)
                accepted_design = True
                continue
            # idle but not done: a WORK retry's backoff may be pending
            await asyncio.sleep(0.3)

        final = await resources.projects.get(project_id)
        assert final is not None
        assert final.phase is Phase.DONE, f"ended in {final.phase} (cycle {final.cycle})"

        depth = await resources.jobs.queue_depth(project_id)
        assert depth[JobState.FAILED] == 0
        assert depth[JobState.READY] == 0
        assert depth[JobState.AWAITING_HUMAN] == 0

        conn = await asyncpg.connect(database_url())
        try:
            kinds = {
                (row["kind"], row["state"]): row["count"]
                for row in await conn.fetch(
                    "SELECT kind, state, count(*) AS count FROM job "
                    "WHERE project_id = $1 GROUP BY kind, state",
                    project_id,
                )
            }
            deploy_jobs = await conn.fetchval(
                "SELECT count(*) FROM job WHERE project_id = $1 AND kind LIKE 'deploy.%'",
                project_id,
            )
        finally:
            await conn.close()

        # The scripted spec has one criterion: walking skeleton + one item,
        # each through implement -> verify -> integrate.
        assert kinds[("build.implement", "succeeded")] == 2
        assert kinds[("build.verify", "succeeded")] == 2
        assert kinds[("build.integrate", "succeeded")] == 2
        assert kinds[("review.demo", "succeeded")] == 1
        assert kinds[("review.collect", "succeeded")] == 1
        assert kinds[("review.triage", "succeeded")] == 1
        assert kinds[("review.deployment_choice", "succeeded")] == 1
        # Declining deployment is DONE(local): no deploy job may ever exist.
        assert deploy_jobs == 0

        demo_files = list(repo.glob(".vibey/**/DEMO.md"))
        assert demo_files, "review.demo produced no DEMO.md artifact"


async def test_full_worker_drives_the_deploy_stage_set_to_done_deployed(tmp_path: Path) -> None:
    """Milestone test B: the same flow, opting INTO deployment -- the bridge,
    the deploy design chain, spec+consent persistence, execute against the
    in-memory Azure adapter, demo approval, and routing to DONE."""
    repo = _make_repo(tmp_path)
    azure = InMemoryAzureClientAdapter()

    async with build_app() as resources:
        project = await resources.projects.create("faked-e2e-deploy", repo, max_cycles=3, config={})
        project_id = project.project_id
        await resources.projects.transition(project_id, expected=Phase.INTAKE, to=Phase.DESIGN)
        await resources.jobs.enqueue(
            EnqueueRequest(
                project_id=project_id,
                cycle=project.cycle,
                phase=Phase.DESIGN,
                kind="design.interview",
                idempotency_key=idempotency_key(
                    project_id, project.cycle, "design.interview", "interactive"
                ),
                requirement={"effort": "high"},
            )
        )

        adapters = {
            engine_id: ScriptedEngine(
                descriptor=descriptor, base_dir=tmp_path / "engines" / engine_id.value
            )
            for engine_id, descriptor in BY_ENGINE_ID.items()
        }
        worker = build_full_worker(
            resources=resources,
            project=project,
            design_provider=ScriptedDesignProvider(),
            visual_provider=ScriptedVisualProvider(),
            decomposer=ScriptedWorkPlanProducer(),
            owner="e2e-deploy-worker",
            engine_adapters=adapters,
            azure_client=azure,
        )

        accepted_design = False
        for _ in range(200):
            if await worker.run_once(project_id):
                continue
            gate = await _open_gate(project_id)
            if gate is not None:
                gate_id, kind, prompt = gate
                await resources.gates.answer(
                    gate_id, answer=_answer_for(kind, prompt, deploy=True), answered_by="e2e"
                )
                continue
            current = await resources.projects.get(project_id)
            assert current is not None
            if current.phase is Phase.DONE:
                break
            if current.phase is Phase.DESIGN and not accepted_design:
                await DesignAcceptanceService(
                    projects=resources.projects,
                    ledger=resources.design_ledger,
                    specs=resources.design_specs,
                    jobs=resources.jobs,
                    clock=resources.clock,
                ).accept(project_id, visual_choice=VisualDecision.DECLINED)
                accepted_design = True
                continue
            await asyncio.sleep(0.3)

        final = await resources.projects.get(project_id)
        assert final is not None
        assert final.phase is Phase.DONE, f"ended in {final.phase} (cycle {final.cycle})"

        conn = await asyncpg.connect(database_url())
        try:
            kinds = {
                (row["kind"], row["state"]): row["count"]
                for row in await conn.fetch(
                    "SELECT kind, state, count(*) AS count FROM job "
                    "WHERE project_id = $1 GROUP BY kind, state",
                    project_id,
                )
            }
        finally:
            await conn.close()

        for deploy_kind in (
            "deploy.design",
            "deploy.interview",
            "deploy.synthesize",
            "deploy.spec",
            "deploy.execute",
            "deploy.demo",
            "deploy.route",
        ):
            assert kinds.get((deploy_kind, "succeeded")) == 1, f"{deploy_kind}: {kinds}"

        # The in-memory Azure adapter executed exactly one consented plan.
        assert len(azure.deployments) == 1
        assert azure.deployments[0].provisioning_state == "Succeeded"

        # Spec and consent were persisted, and the consent is digest-bound.
        state = FileDeploymentStateRepository(repo)
        spec = state.load_spec(project_id)
        consent = state.load_consent(project_id)
        assert spec is not None and consent is not None
        assert consent.matches_spec(spec) is True
