import json
from pathlib import Path
from uuid import uuid4

from typer.testing import CliRunner

from vibey import __version__
from vibey.cli import main as cli_main
from vibey.cli.main import app

runner = CliRunner()


def test_version_flag_prints_version_and_exits() -> None:
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert __version__ in result.stdout


def test_no_args_shows_help() -> None:
    result = runner.invoke(app, [])

    assert "vibey" in result.stdout


def test_m5_commands_are_exposed() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "new" in result.stdout
    assert "design" in result.stdout
    assert "answer" in result.stdout
    assert "work" in result.stdout


def test_design_command_enqueues_interview(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    project_id = uuid4()

    async def fake_enqueue(received):  # type: ignore[no-untyped-def]
        assert received == project_id
        return "job-1"

    monkeypatch.setattr(cli_main, "_enqueue_design", fake_enqueue)
    result = runner.invoke(app, ["design", str(project_id)])
    assert result.exit_code == 0
    assert "design job job-1" in result.stdout


def test_work_command_runs_one_queue_item(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    project_id = uuid4()

    async def fake_work(received, provider, max_turns, max_dollars):  # type: ignore[no-untyped-def]
        assert received == project_id
        assert provider == "scripted"
        assert max_turns == 1
        assert max_dollars == 0.25
        return True

    monkeypatch.setattr(cli_main, "_work_once", fake_work)
    result = runner.invoke(app, ["work", str(project_id)])
    assert result.exit_code == 0
    assert "processed one job" in result.stdout


def test_load_spec_json(tmp_path: Path) -> None:
    path = tmp_path / "spec.json"
    path.write_text(
        json.dumps(
            {
                "objective": "Ship",
                "constraints": [{"text": "Offline", "kind": "hard"}],
                "non_goals": ["Cloud"],
                "criteria": [
                    {
                        "criterion_id": "AC-1",
                        "given": "input",
                        "when": "run",
                        "then": "output",
                        "fit": "test passes",
                    }
                ],
                "nfrs": [],
                "walking_skeleton": "one path",
            }
        )
    )
    spec = cli_main._load_spec(path)
    assert spec.is_buildable() == ()
    assert spec.hard_constraints() == ("Offline",)


def test_parse_question_answers_builds_the_handler_payload() -> None:
    assert cli_main._parse_question_answers(("q-1=Ship it", "q-2=default=allowed")) == {
        "answers": {"q-1": "Ship it", "q-2": "default=allowed"}
    }


def test_parse_question_answers_rejects_unkeyed_text() -> None:
    try:
        cli_main._parse_question_answers(("Ship it",))
    except ValueError as exc:
        assert "QUESTION_ID=ANSWER" in str(exc)
    else:
        raise AssertionError("unkeyed answers must be rejected")
