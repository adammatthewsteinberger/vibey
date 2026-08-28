# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Operator handlers against a real database.

The handlers are thin, but the things they must get right -- creating a
project exactly once, answering through the shared service, staying a
no-op on unchanged input -- are all statements about persisted state, so
they are checked against Postgres rather than a mock.
"""

import os
from pathlib import Path
from unittest.mock import patch
from uuid import uuid4

import asyncpg
import kopf
import pytest

from vibey.application.dto import HumanGateRequest
from vibey.bootstrap import build_app, database_url
from vibey.infrastructure.operator import handlers

pytestmark = pytest.mark.integration


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


async def test_ensure_project_creates_once_and_is_a_no_op_thereafter(tmp_path: Path) -> None:
    """A reconcile loop calls this every interval. Without the status guard
    each pass would start another project against the same repository."""
    async with build_app() as resources:
        spec = {"repo": str(tmp_path), "maxCycles": 2}
        first = await handlers.ensure_project(
            resources, name="demo", spec=spec, known_project_id=None
        )
        second = await handlers.ensure_project(
            resources, name="demo", spec=spec, known_project_id=str(first.project_id)
        )
    assert second.project_id == first.project_id


async def test_ensure_project_recreates_when_status_names_a_missing_project(
    tmp_path: Path,
) -> None:
    """A stale id -- a database restored from before the project existed --
    must not wedge the operator into never creating anything again."""
    async with build_app() as resources:
        project = await handlers.ensure_project(
            resources,
            name="demo",
            spec={"repo": str(tmp_path)},
            known_project_id=str(uuid4()),
        )
    assert project.name == "demo"


async def test_creating_a_project_enqueues_its_design_interview(tmp_path: Path) -> None:
    async with build_app() as resources:
        project = await handlers.ensure_project(
            resources, name="demo", spec={"repo": str(tmp_path)}, known_project_id=None
        )
        depth = await resources.jobs.queue_depth(project.project_id)
    assert sum(depth.values()) == 1


async def test_spec_carries_budget_caps_into_project_config(tmp_path: Path) -> None:
    async with build_app() as resources:
        project = await handlers.ensure_project(
            resources,
            name="demo",
            spec={
                "repo": str(tmp_path),
                "maxCycleDollars": 5.0,
                "maxCycleTurns": 40,
                "engines": ["claudeloop"],
                "skillsContext": {"mode": "shadow", "budget": 4000},
            },
            known_project_id=None,
        )
        stored = await resources.projects.get(project.project_id)
    assert stored is not None
    assert stored.config["max_cycle_dollars"] == 5.0
    assert stored.config["max_cycle_turns"] == 40
    assert stored.config["engines"] == ["claudeloop"]
    assert stored.config["skills_context"] == {"mode": "shadow", "budget": 4000}
    with pytest.raises(ValueError, match="skillsContext must be an object"):
        handlers._project_config("demo", {"skillsContext": "shadow"})


async def test_answers_from_the_cr_go_through_the_shared_gate_service(tmp_path: Path) -> None:
    """The CR is a second entry point and must never become a second code
    path: the gate is answered by the same service `vibey answer` calls,
    and the answer is attributed to the operator."""
    async with build_app() as resources:
        project = await handlers.ensure_project(
            resources, name="demo", spec={"repo": str(tmp_path)}, known_project_id=None
        )
        gate = await resources.gates.raise_gate(
            project.project_id,
            None,
            HumanGateRequest(kind="question", prompt="which shape?", options=("a", "b")),
        )
        plan = await handlers.apply_answers(
            resources,
            project_id=project.project_id,
            spec_answers={str(gate.gate_id): {"choice": "a"}},
        )
        answered = await resources.gates.get(gate.gate_id)

    assert plan.apply == ((gate.gate_id, {"choice": "a"}),)
    assert answered is not None
    assert answered.answer == {"choice": "a"}
    assert answered.answered_by == "operator"


async def test_reapplying_an_unchanged_cr_answers_nothing_twice(tmp_path: Path) -> None:
    async with build_app() as resources:
        project = await handlers.ensure_project(
            resources, name="demo", spec={"repo": str(tmp_path)}, known_project_id=None
        )
        gate = await resources.gates.raise_gate(
            project.project_id,
            None,
            HumanGateRequest(kind="question", prompt="q", options=()),
        )
        answers = {str(gate.gate_id): {"choice": "a"}}
        await handlers.apply_answers(resources, project_id=project.project_id, spec_answers=answers)
        second = await handlers.apply_answers(
            resources, project_id=project.project_id, spec_answers=answers
        )

    assert second.apply == ()
    assert second.ignored == ((str(gate.gate_id), "no open gate with that id"),)


async def test_open_gates_are_listed_oldest_first_and_exclude_answered(tmp_path: Path) -> None:
    async with build_app() as resources:
        project = await handlers.ensure_project(
            resources, name="demo", spec={"repo": str(tmp_path)}, known_project_id=None
        )
        first = await resources.gates.raise_gate(
            project.project_id, None, HumanGateRequest(kind="question", prompt="1", options=())
        )
        second = await resources.gates.raise_gate(
            project.project_id, None, HumanGateRequest(kind="approval", prompt="2", options=())
        )
        await resources.gates.answer(first.gate_id, answer={"choice": "x"}, answered_by="test")
        still_open = await resources.gates.open_for_project(project.project_id)

    assert [g.gate_id for g in still_open] == [second.gate_id]


async def test_status_reports_the_park_a_human_has_to_answer(tmp_path: Path) -> None:
    async with build_app() as resources:
        project = await handlers.ensure_project(
            resources, name="demo", spec={"repo": str(tmp_path)}, known_project_id=None
        )
        await resources.gates.raise_gate(
            project.project_id,
            None,
            HumanGateRequest(kind="budget_exhausted", prompt="grant more?", options=()),
        )
        status = await handlers.build_status(resources, project_id=project.project_id)

    parked = next(c for c in status["conditions"] if c["type"] == "Parked")  # type: ignore[index,union-attr]
    assert parked["status"] == "True"
    assert parked["reason"] == "BudgetExhausted"


async def test_status_for_a_vanished_project_is_unknown_not_a_crash() -> None:
    """The operator must keep reconciling other resources when one CR's
    project has been deleted out from under it."""
    async with build_app() as resources:
        status = await handlers.build_status(resources, project_id=uuid4())
    assert status["phase"] == "unknown"
    assert status["conditions"][0]["status"] == "Unknown"  # type: ignore[index]


async def test_on_create_patches_status_with_the_new_project(tmp_path: Path) -> None:
    patch_obj = kopf.Patch()
    await handlers.on_create(spec={"repo": str(tmp_path)}, name="demo", patch=patch_obj)
    assert patch_obj["status"]["phase"] == "design"
    assert patch_obj["status"]["projectId"]


async def test_reconcile_applies_answers_and_reports_the_ones_it_ignored(
    tmp_path: Path,
) -> None:
    create_patch = kopf.Patch()
    await handlers.on_create(spec={"repo": str(tmp_path)}, name="demo", patch=create_patch)
    project_id = create_patch["status"]["projectId"]

    async with build_app() as resources:
        from uuid import UUID

        gate = await resources.gates.raise_gate(
            UUID(project_id),
            None,
            HumanGateRequest(kind="question", prompt="q", options=()),
        )

    patch_obj = kopf.Patch()
    await handlers.reconcile(
        spec={
            "repo": str(tmp_path),
            "answers": {str(gate.gate_id): {"choice": "a"}, "bogus": {}},
        },
        status={"projectId": project_id},
        name="demo",
        patch=patch_obj,
    )

    assert patch_obj["status"]["ignoredAnswers"] == [{"key": "bogus", "reason": "not a gate id"}]
    parked = next(c for c in patch_obj["status"]["conditions"] if c["type"] == "Parked")
    assert parked["status"] == "False"


async def test_reconcile_without_answers_leaves_no_ignored_key(tmp_path: Path) -> None:
    create_patch = kopf.Patch()
    await handlers.on_create(spec={"repo": str(tmp_path)}, name="demo", patch=create_patch)

    patch_obj = kopf.Patch()
    await handlers.reconcile(
        spec={"repo": str(tmp_path)},
        status={"projectId": create_patch["status"]["projectId"]},
        name="demo",
        patch=patch_obj,
    )
    assert "ignoredAnswers" not in patch_obj["status"]


def test_run_delegates_to_kopf_cluster_wide_by_default() -> None:
    with patch.object(kopf, "run") as kopf_run:
        handlers.run()
    kopf_run.assert_called_once_with(namespace=None, clusterwide=True)


def test_run_scoped_to_one_namespace_is_not_cluster_wide() -> None:
    with patch.object(kopf, "run") as kopf_run:
        handlers.run(namespace="vibey")
    kopf_run.assert_called_once_with(namespace="vibey", clusterwide=False)
