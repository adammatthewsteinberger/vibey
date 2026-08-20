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


def _clean_git_env() -> dict[str, str]:
    return {
        k: v
        for k, v in os.environ.items()
        if not k.startswith(("GIT_", "PRE_COMMIT"))
    }


def _git(repo: Path, *argv: str) -> None:
    subprocess.run(  # nosec B603
        ("git", "-C", str(repo), *argv),
        check=True,
        capture_output=True,
        env=_clean_git_env(),
    )


def _make_repo(root: Path) -> Path:
    """A scratch repo whose contents pass the real automated review commands
    (bandit -q -r src; ruff check .) that review.demo runs."""
    repo = root / "repo"
    (repo / "src").mkdir(parents=True)
    (repo / "src" / "app.py").write_text("def main() -> int:\n    return 0\n")
    subprocess.run(  # nosec B603
        ("git", "init", "-q", str(repo)),
        check=True,
        env=_clean_git_env(),
    )
    _git(repo, "config", "user.email", "e2e@vibey.local")
    _git(repo, "config", "user.name", "vibey e2e")
    _git(repo, "config", "core.hooksPath", "/dev/null")
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
        # Engine-driven jobs now select via the real rotation stack, which
        # requires populated health records -- the faked-harness equivalent
        # of `vibey doctor --conformance --record` + the startup sweep.
        for engine_id, adapter in adapters.items():
            await resources.engine_health_service.update_from_preflight(
                project_id, engine_id, await adapter.preflight(), conformance_ok=True
            )
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

        # Real per-job rotation: every engine-driven job durably recorded
        # its selected engine, and each verify's reviewer differs from its
        # item's implementer.
        conn = await asyncpg.connect(database_url())
        try:
            engine_rows = await conn.fetch(
                "SELECT kind, work_item_id, assigned_engine, requirement FROM job "
                "WHERE project_id = $1 AND kind IN ('build.implement', 'build.verify')",
                project_id,
            )
        finally:
            await conn.close()
        assert all(row["assigned_engine"] for row in engine_rows)
        import json as _json

        for row in engine_rows:
            if row["kind"] == "build.verify":
                implementer = _json.loads(row["requirement"]).get("implementer_engine_id")
                assert implementer is not None
                assert row["assigned_engine"] != implementer
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
        # Engine-driven jobs now select via the real rotation stack, which
        # requires populated health records -- the faked-harness equivalent
        # of `vibey doctor --conformance --record` + the startup sweep.
        for engine_id, adapter in adapters.items():
            await resources.engine_health_service.update_from_preflight(
                project_id, engine_id, await adapter.preflight(), conformance_ok=True
            )
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


class _WindsDownOnSkeleton:
    """Wraps a ScriptedEngine so its first REGULAR skeleton implement run
    winds down (exit 75, closable events, no verdict). The follow-up run
    is seeded from the brief -- its prompt never matches the prefix -- so
    exactly one wind-down happens per project, on whichever engine the
    rotor selects first."""

    def __init__(self, inner: ScriptedEngine) -> None:
        self._inner = inner

    def __getattr__(self, name: str) -> object:
        return getattr(self._inner, name)

    async def start(self, spec):  # type: ignore[no-untyped-def]
        if spec.prompt.startswith("Implement work item ws"):
            now = "2026-08-19T00:00:00+00:00"
            self._inner.scripts = [
                [
                    {"kind": "SessionSeeded", "at": now, "payload": {"seed_digest": "wd"}},
                    {
                        "kind": "QuestionAsked",
                        "at": now,
                        "payload": {
                            "question_id": "q_wind_1",
                            "text": "Should the skeleton expose a health endpoint?",
                            "blocking": False,
                        },
                    },
                    {
                        "kind": "DecisionRecorded",
                        "at": now,
                        "payload": {
                            "decision_id": "d_wind_1",
                            "title": "Single module layout",
                            "choice": "single module",
                        },
                    },
                    {
                        "kind": "AssumptionStated",
                        "at": now,
                        "payload": {
                            "assumption_id": "a_wind_1",
                            "text": "stdout logging suffices for the skeleton",
                        },
                    },
                ]
            ]
            self._inner.exit_code_script = [75]
        return await self._inner.start(spec)


async def test_full_worker_survives_a_forced_wind_down_rotation(tmp_path: Path) -> None:
    """Milestone test C: the skeleton's first implement run winds down mid-
    item. The no-loss pipeline must persist a verified handoff envelope,
    seed a follow-up on a DIFFERENT engine whose prompt carries every
    closable id verbatim, and the project must still reach DONE(local)."""
    repo = _make_repo(tmp_path)

    async with build_app() as resources:
        project = await resources.projects.create("faked-e2e-wind", repo, max_cycles=3, config={})
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
            engine_id: _WindsDownOnSkeleton(
                ScriptedEngine(
                    descriptor=descriptor,
                    base_dir=tmp_path / "engines" / engine_id.value,
                    stop_remaining=("carry the skeleton forward from the snapshot",),
                )
            )
            for engine_id, descriptor in BY_ENGINE_ID.items()
        }
        for engine_id, adapter in adapters.items():
            await resources.engine_health_service.update_from_preflight(
                project_id, engine_id, await adapter.preflight(), conformance_ok=True
            )
        worker = build_full_worker(
            resources=resources,
            project=project,
            design_provider=ScriptedDesignProvider(),
            visual_provider=ScriptedVisualProvider(),
            decomposer=ScriptedWorkPlanProducer(),
            owner="e2e-wind-worker",
            engine_adapters=adapters,  # type: ignore[arg-type]
        )

        accepted_design = False
        for _ in range(200):
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
            await asyncio.sleep(0.3)

        final = await resources.projects.get(project_id)
        assert final is not None
        assert final.phase is Phase.DONE, f"ended in {final.phase} (cycle {final.cycle})"

        import json as _json

        conn = await asyncpg.connect(database_url())
        try:
            handoffs = await conn.fetch(
                "SELECT from_engine, to_engine, reason, accepted, gate_mode, envelope "
                "FROM handoff WHERE project_id = $1",
                project_id,
            )
            implements = await conn.fetch(
                "SELECT id, state, assigned_engine, payload, requirement FROM job "
                "WHERE project_id = $1 AND kind = 'build.implement' ORDER BY created_at",
                project_id,
            )
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

        # Exactly one verified handoff, accepted by the no-loss gate.
        (handoff,) = handoffs
        assert handoff["accepted"] is True
        assert handoff["reason"] == "rotation"
        assert handoff["from_engine"] != handoff["to_engine"]

        # Three implements: the wind-down (Success), its seeded follow-up,
        # and item-001; each verified item still integrated exactly once.
        assert kinds[("build.implement", "succeeded")] == 3
        assert kinds[("build.verify", "succeeded")] == 2
        assert kinds[("build.integrate", "succeeded")] == 2

        by_payload = {job_row["id"]: _json.loads(job_row["payload"]) for job_row in implements}
        follow_ups = [
            job_row for job_row in implements if "seed_prompt" in by_payload[job_row["id"]]
        ]
        (follow_up,) = follow_ups
        seed = by_payload[follow_up["id"]]["seed_prompt"]

        # Every closable id the winding-down engine raised appears verbatim.
        for closable in ("q_wind_1", "d_wind_1", "a_wind_1"):
            assert closable in seed, f"{closable} missing from seed prompt"
        assert "carry the skeleton forward from the snapshot" in seed

        # The follow-up rotated: different engine, with the wound-down
        # engine durably excluded in its requirement.
        assert follow_up["assigned_engine"] != handoff["from_engine"]
        excluded = _json.loads(follow_up["requirement"])["excluded_engine_ids"]
        assert excluded == [handoff["from_engine"]]
