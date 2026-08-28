# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://hire.adam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
"""Real-Postgres integration tests for the CLI's async command bodies.

``tests/cli/test_main.py`` monkeypatches ``_enqueue_design``/``_work_once`` and
therefore never exercises the code that actually calls ``build_app()`` --
``new``, ``design``, ``answer``, ``work`` (scripted provider), and
``design accept``. These tests drive the real Typer commands end to end
against a real database, per the project's own rule of never mocking
Postgres.
"""

import asyncio
import os
from pathlib import Path
from uuid import UUID

import asyncpg
import pytest
from typer.testing import CliRunner

from vibey.bootstrap import build_app, database_url
from vibey.cli.main import app

pytestmark = pytest.mark.integration

# Typer force-enables rich ANSI styling whenever GITHUB_ACTIONS is set
# (typer/rich_utils.py), which CI always has and a local shell never does.
# That embeds escape codes inside option names, breaking plain substring
# checks against --help output -- disable it the way Typer itself exposes.
runner = CliRunner(env={"_TYPER_FORCE_DISABLE_TERMINAL": "1"})


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


async def _latest_gate_id(job_id: UUID) -> UUID:
    async with build_app() as resources:
        gate = await resources.gates.latest_for_job(job_id)
        assert gate is not None
        return gate.gate_id


def test_new_project_creates_and_enqueues_design(tmp_path: Path) -> None:
    result = runner.invoke(app, ["new", "widget", "--repo", str(tmp_path)])

    assert result.exit_code == 0, result.output
    lines = result.output.strip().splitlines()
    assert lines[0].startswith("project ")
    assert lines[1].startswith("design job ")


def test_full_design_flow_through_the_real_cli(tmp_path: Path) -> None:
    created = runner.invoke(app, ["new", "widget", "--repo", str(tmp_path)])
    assert created.exit_code == 0, created.output
    project_line, job_line = created.output.strip().splitlines()
    project_id = UUID(project_line.removeprefix("project "))
    interview_job_id = UUID(job_line.removeprefix("design job "))

    for number in range(1, 8):
        worked = runner.invoke(app, ["work", str(project_id)])
        assert worked.exit_code == 0, worked.output
        assert "processed one job" in worked.output

        gate_id = asyncio.run(_latest_gate_id(interview_job_id))
        answered = runner.invoke(app, ["answer", str(gate_id), f"q-{number}=answer-{number}"])
        assert answered.exit_code == 0, answered.output
        assert f"answered {gate_id}" in answered.output

    # Interview finalizes and enqueues research/synthesize/spec (5 more jobs).
    for _ in range(6):
        worked = runner.invoke(app, ["work", str(project_id)])
        assert worked.exit_code == 0, worked.output

    idle = runner.invoke(app, ["work", str(project_id)])
    assert idle.exit_code == 0, idle.output
    assert "no ready job" in idle.output

    accepted = runner.invoke(app, ["design", "accept", str(project_id)])
    assert accepted.exit_code == 0, accepted.output
    assert f"accepted design for {project_id}" in accepted.output
    assert (tmp_path / ".vibey/context/spec.md").exists()


def test_answer_rejects_unkeyed_text(tmp_path: Path) -> None:
    created = runner.invoke(app, ["new", "widget", "--repo", str(tmp_path)])
    assert created.exit_code == 0, created.output

    result = runner.invoke(app, ["answer", str(UUID(int=0)), "not-keyed"])

    assert result.exit_code != 0


def test_design_resume_reenqueues_the_interview(tmp_path: Path) -> None:
    created = runner.invoke(app, ["new", "widget", "--repo", str(tmp_path)])
    assert created.exit_code == 0, created.output
    project_line, _ = created.output.strip().splitlines()
    project_id = UUID(project_line.removeprefix("project "))

    result = runner.invoke(app, ["design", "resume", str(project_id)])

    assert result.exit_code == 0, result.output
    assert "design job " in result.output


def test_design_with_no_subcommand_shows_help() -> None:
    result = runner.invoke(app, ["design"])

    assert result.exit_code == 0, result.output
    assert "resume" in result.output.lower() or "accept" in result.output.lower()


def test_design_accept_visual_opts_into_visual_design(tmp_path: Path) -> None:
    created = runner.invoke(app, ["new", "widget", "--repo", str(tmp_path)])
    assert created.exit_code == 0, created.output
    project_line, job_line = created.output.strip().splitlines()
    project_id = UUID(project_line.removeprefix("project "))
    interview_job_id = UUID(job_line.removeprefix("design job "))

    for number in range(1, 8):
        worked = runner.invoke(app, ["work", str(project_id)])
        assert worked.exit_code == 0, worked.output
        gate_id = asyncio.run(_latest_gate_id(interview_job_id))
        answered = runner.invoke(app, ["answer", str(gate_id), f"q-{number}=answer-{number}"])
        assert answered.exit_code == 0, answered.output

    for _ in range(6):
        worked = runner.invoke(app, ["work", str(project_id)])
        assert worked.exit_code == 0, worked.output

    accepted = runner.invoke(app, ["design", "accept", str(project_id), "--visual"])
    assert accepted.exit_code == 0, accepted.output
    assert "entered visual_design" in accepted.output


def test_full_visual_design_flow_through_the_real_cli(tmp_path: Path) -> None:
    created = runner.invoke(app, ["new", "widget", "--repo", str(tmp_path)])
    assert created.exit_code == 0, created.output
    project_line, job_line = created.output.strip().splitlines()
    project_id = UUID(project_line.removeprefix("project "))
    interview_job_id = UUID(job_line.removeprefix("design job "))

    for number in range(1, 8):
        worked = runner.invoke(app, ["work", str(project_id)])
        assert worked.exit_code == 0, worked.output
        gate_id = asyncio.run(_latest_gate_id(interview_job_id))
        answered = runner.invoke(app, ["answer", str(gate_id), f"q-{number}=answer-{number}"])
        assert answered.exit_code == 0, answered.output

    for _ in range(6):
        worked = runner.invoke(app, ["work", str(project_id)])
        assert worked.exit_code == 0, worked.output

    accepted = runner.invoke(app, ["design", "accept", str(project_id), "--visual"])
    assert accepted.exit_code == 0, accepted.output
    assert "entered visual_design" in accepted.output

    # visual.inventory, then visual.plan
    for _ in range(2):
        worked = runner.invoke(app, ["work", str(project_id)])
        assert worked.exit_code == 0, worked.output
        assert "processed one job" in worked.output

    idle = runner.invoke(app, ["work", str(project_id)])
    assert idle.exit_code == 0, idle.output
    assert "no ready job" in idle.output
    assert (tmp_path / ".vibey/context/visual/screen-inventory.md").exists()

    settled = runner.invoke(app, ["visual", "accept", str(project_id)])
    assert settled.exit_code == 0, settled.output
    assert "entered build" in settled.output


def test_visual_waive_also_reaches_build(tmp_path: Path) -> None:
    created = runner.invoke(app, ["new", "widget", "--repo", str(tmp_path)])
    assert created.exit_code == 0, created.output
    project_line, job_line = created.output.strip().splitlines()
    project_id = UUID(project_line.removeprefix("project "))
    interview_job_id = UUID(job_line.removeprefix("design job "))

    for number in range(1, 8):
        runner.invoke(app, ["work", str(project_id)])
        gate_id = asyncio.run(_latest_gate_id(interview_job_id))
        runner.invoke(app, ["answer", str(gate_id), f"q-{number}=answer-{number}"])
    for _ in range(6):
        runner.invoke(app, ["work", str(project_id)])
    runner.invoke(app, ["design", "accept", str(project_id), "--visual"])
    for _ in range(2):
        runner.invoke(app, ["work", str(project_id)])

    settled = runner.invoke(app, ["visual", "waive", str(project_id)])
    assert settled.exit_code == 0, settled.output
    assert "entered build" in settled.output


def test_visual_with_no_subcommand_shows_help() -> None:
    result = runner.invoke(app, ["visual"])

    assert result.exit_code == 0, result.output
    assert "accept" in result.output.lower() or "waive" in result.output.lower()


def _raise_test_gate(tmp_path: Path, name: str) -> UUID:
    async def seed() -> UUID:
        from vibey.application.dto import HumanGateRequest

        async with build_app() as resources:
            project = await resources.projects.create(name, tmp_path, max_cycles=1, config={})
            gate = await resources.gates.raise_gate(
                project.project_id,
                None,
                HumanGateRequest(
                    kind="review_verdict",
                    prompt="Accept?",
                    options=("accept", "changes"),
                    default_answer="accept",
                ),
            )
            return gate.gate_id

    return asyncio.run(seed())


def _gate_answer(gate_id: UUID) -> dict[str, object]:
    async def load() -> dict[str, object]:
        async with build_app() as resources:
            gate = await resources.gates.get(gate_id)
            assert gate is not None and gate.answer is not None
            return dict(gate.answer)

    return asyncio.run(load())


def test_answer_verdict_flag_sends_verdict_shape(tmp_path: Path) -> None:
    gate_id = _raise_test_gate(tmp_path, "verdict-proj")

    result = runner.invoke(app, ["answer", str(gate_id), "--verdict", "accept"])

    assert result.exit_code == 0, result.output
    assert _gate_answer(gate_id) == {"verdict": "accept"}


def test_answer_choice_flag_sends_choice_shape(tmp_path: Path) -> None:
    gate_id = _raise_test_gate(tmp_path, "choice-proj")

    result = runner.invoke(app, ["answer", str(gate_id), "--choice", "local_only"])

    assert result.exit_code == 0, result.output
    assert _gate_answer(gate_id) == {"choice": "local_only"}


def test_answer_raw_flag_sends_arbitrary_object(tmp_path: Path) -> None:
    gate_id = _raise_test_gate(tmp_path, "raw-proj")

    result = runner.invoke(
        app, ["answer", str(gate_id), "--raw", '{"verdict": "accept", "note": "ship it"}']
    )

    assert result.exit_code == 0, result.output
    assert _gate_answer(gate_id) == {"verdict": "accept", "note": "ship it"}


def test_answer_requires_exactly_one_mode() -> None:
    none_given = runner.invoke(app, ["answer", str(UUID(int=1))])
    assert none_given.exit_code == 2
    assert "exactly one" in none_given.output

    two_given = runner.invoke(app, ["answer", str(UUID(int=1)), "--choice", "x", "--verdict", "y"])
    assert two_given.exit_code == 2
    assert "exactly one" in two_given.output

    pairs_plus_flag = runner.invoke(app, ["answer", str(UUID(int=1)), "q-1=a", "--choice", "x"])
    assert pairs_plus_flag.exit_code == 2


def test_answer_raw_rejects_invalid_json_and_non_objects() -> None:
    bad_json = runner.invoke(app, ["answer", str(UUID(int=1)), "--raw", "{nope"])
    assert bad_json.exit_code == 2
    assert "valid JSON" in bad_json.output

    non_object = runner.invoke(app, ["answer", str(UUID(int=1)), "--raw", '["a"]'])
    assert non_object.exit_code == 2
    assert "JSON object" in non_object.output


def test_answer_defaults_flag_sends_accept_defaults(tmp_path: Path) -> None:
    gate_id = _raise_test_gate(tmp_path, "defaults-proj")

    result = runner.invoke(app, ["answer", str(gate_id), "--defaults"])

    assert result.exit_code == 0, result.output
    assert _gate_answer(gate_id) == {"answers": {}, "accept_defaults": True}


def test_answer_defaults_combines_with_pairs_but_not_other_modes(tmp_path: Path) -> None:
    gate_id = _raise_test_gate(tmp_path, "defaults-pairs-proj")

    result = runner.invoke(app, ["answer", str(gate_id), "q-1=explicit", "--defaults"])

    assert result.exit_code == 0, result.output
    assert _gate_answer(gate_id) == {
        "answers": {"q-1": "explicit"},
        "accept_defaults": True,
    }

    with_choice = runner.invoke(app, ["answer", str(UUID(int=1)), "--defaults", "--choice", "x"])
    assert with_choice.exit_code == 2
    assert "only combines" in with_choice.output


def test_new_project_stores_cycle_budget_caps_in_config(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "new",
            "budgeted-proj",
            "--repo",
            str(tmp_path),
            "--max-cycle-dollars",
            "15.5",
            "--max-cycle-turns",
            "200",
            "--skills-context-mode",
            "shadow",
            "--skills-context-budget",
            "4000",
        ],
    )
    assert result.exit_code == 0, result.output

    async def load():  # type: ignore[no-untyped-def]
        async with build_app() as resources:
            project = await resources.projects.get_latest()
            assert project is not None
            return project.config

    config = asyncio.run(load())
    assert config["max_cycle_dollars"] == 15.5
    assert config["max_cycle_turns"] == 200
    assert config["skills_context"] == {"mode": "shadow", "budget": 4000}


def test_new_project_rejects_unknown_skills_context_mode(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        [
            "new",
            "bad-context-mode",
            "--repo",
            str(tmp_path),
            "--skills-context-mode",
            "surprise",
        ],
    )
    assert result.exit_code != 0
    assert "off, shadow, or inject" in result.output
