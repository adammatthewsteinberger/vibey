# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Paid-mode worker BUILD path: one real claudeloop session through the
production dispatch stack -- rotation-selected engine, real worktree, real
subprocess, durable assigned_engine, and the verify follow-up enqueued
with the must-differ constraint.

This is the live counterpart of the faked E2Es in
tests/system/test_full_worker_faked.py, scoped to a single trivial work
item so the spend stays bounded (one LOW-effort session). DESIGN and
decompose are skipped by enqueueing the build.implement job directly.

Run with: pytest -m paid tests/live/test_paid_worker_build.py
Requires: the claudeloop binary on PATH with working auth, and Postgres
reachable via VIBEY_TEST_DATABASE_URL (defaults to a local vibey_test).
"""

import os
import shutil
import subprocess  # nosec B404 - fixed argv, never shell=True
from pathlib import Path

import asyncpg
import pytest

from vibey.application.dto import EnqueueRequest
from vibey.bootstrap import build_app, build_full_worker, database_url
from vibey.domain.engine import EngineId
from vibey.domain.job import JobState, idempotency_key
from vibey.domain.phase import Phase
from vibey.infrastructure.engines.descriptors import CLAUDELOOP
from vibey.infrastructure.engines.loop_process_adapter import LoopProcessAdapter
from vibey.infrastructure.engines.scripted_decompose import ScriptedWorkPlanProducer
from vibey.infrastructure.engines.scripted_design import ScriptedDesignProvider
from vibey.infrastructure.engines.scripted_visual import ScriptedVisualProvider


@pytest.fixture()
async def _paid_test_database(monkeypatch: pytest.MonkeyPatch) -> None:
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


@pytest.mark.paid
@pytest.mark.slow
@pytest.mark.usefixtures("_paid_test_database")
async def test_one_live_build_implement_runs_on_a_selected_engine(tmp_path: Path) -> None:
    if shutil.which(CLAUDELOOP.binary) is None:
        pytest.skip(f"{CLAUDELOOP.binary} not installed")

    repo = tmp_path / "repo"
    repo.mkdir()
    (repo / "README.md").write_text("live worker demo\n")
    subprocess.run(("git", "init", "-q", str(repo)), check=True)  # nosec B603
    _git(repo, "config", "user.email", "live@vibey.local")
    _git(repo, "config", "user.name", "vibey live")
    _git(repo, "add", ".")
    _git(repo, "commit", "-q", "-m", "init")

    async with build_app() as resources:
        project = await resources.projects.create("paid-build", repo, max_cycles=1, config={})
        project_id = project.project_id
        await resources.projects.transition(project_id, expected=Phase.INTAKE, to=Phase.DESIGN)
        await resources.projects.transition(project_id, expected=Phase.DESIGN, to=Phase.BUILD)

        adapter = LoopProcessAdapter(descriptor=CLAUDELOOP)
        preflight = await adapter.preflight()
        if not preflight.auth_ok:
            pytest.skip("claudeloop is installed but not authenticated")
        # The doctor --conformance --record equivalent: grant eligibility
        # directly -- conformance itself is covered elsewhere, and running
        # it here would spend a second session.
        await resources.engine_health_service.update_from_preflight(
            project_id, EngineId.CLAUDELOOP, preflight, conformance_ok=True
        )

        await resources.jobs.enqueue(
            EnqueueRequest(
                project_id=project_id,
                cycle=project.cycle,
                phase=Phase.BUILD,
                kind="build.implement",
                idempotency_key=idempotency_key(
                    project_id, project.cycle, "build.implement", "hello"
                ),
                work_item_id="hello",
                payload={
                    "title": "create hello.txt containing exactly 'hello from vibey'",
                    "verification": {
                        "commands": ["cat hello.txt"],
                        "criteria_checked": ["AC-1"],
                    },
                },
            )
        )

        worker = build_full_worker(
            resources=resources,
            project=project,
            design_provider=ScriptedDesignProvider(),
            visual_provider=ScriptedVisualProvider(),
            decomposer=ScriptedWorkPlanProducer(),
            owner="paid-live-worker",
            engine_adapters={EngineId.CLAUDELOOP: adapter},
            allow_list=frozenset({EngineId.CLAUDELOOP}),
        )

        # One pass runs the whole live session inside run_once; the second
        # pass claims the verify follow-up, whose must-differ constraint
        # has no eligible engine here and settles as a Defer -- proving
        # the constraint holds without spending another session.
        for _ in range(4):
            if not await worker.run_once(project_id):
                break

        conn = await asyncpg.connect(database_url())
        try:
            implement = await conn.fetchrow(
                "SELECT state, assigned_engine FROM job "
                "WHERE project_id = $1 AND kind = 'build.implement'",
                project_id,
            )
            verify = await conn.fetchrow(
                "SELECT state, requirement FROM job "
                "WHERE project_id = $1 AND kind = 'build.verify'",
                project_id,
            )
            build_events = await conn.fetchval(
                "SELECT count(*) FROM event WHERE project_id = $1 AND phase = 'build'",
                project_id,
            )
        finally:
            await conn.close()

        assert implement is not None
        assert implement["state"] == JobState.SUCCEEDED.value
        assert implement["assigned_engine"] == "claudeloop"
        assert build_events > 0, "the live session recorded no ledger events"

        assert verify is not None
        assert '"implementer_engine_id": "claudeloop"' in verify["requirement"]
        # Sole-engine worker: the verifier must differ, so the job waits.
        assert verify["state"] in (
            JobState.AWAITING_CAPACITY.value,
            JobState.READY.value,
        )
