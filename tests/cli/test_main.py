# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
import json
from pathlib import Path
from uuid import uuid4

import pytest
from typer.testing import CliRunner

from vibey import __version__
from vibey.cli import main as cli_main
from vibey.cli.main import app
from vibey.domain.errors import InvalidAnswer

# Typer force-enables rich ANSI styling whenever GITHUB_ACTIONS is set
# (typer/rich_utils.py), which CI always has and a local shell never does.
# That embeds escape codes inside option names, breaking plain substring
# checks against --help output -- disable it the way Typer itself exposes.
runner = CliRunner(env={"_TYPER_FORCE_DISABLE_TERMINAL": "1"})


def test_version_flag_prints_version_and_exits() -> None:
    result = runner.invoke(app, ["--version"])

    assert result.exit_code == 0
    assert __version__ in result.stdout


def test_no_args_shows_help() -> None:
    result = runner.invoke(app, [])

    assert "vibey" in result.stdout


def test_cli_commands_are_exposed() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "new" in result.stdout
    assert "design" in result.stdout
    assert "answer" in result.stdout
    assert "work" in result.stdout
    assert "watch" in result.stdout
    assert "status" in result.stdout
    assert "engines" in result.stdout
    assert "cost" in result.stdout
    assert "ledger" in result.stdout
    assert "deploy" in result.stdout


def test_design_command_enqueues_interview(monkeypatch) -> None:  # type: ignore[no-untyped-def]
    project_id = uuid4()

    async def fake_enqueue(received):  # type: ignore[no-untyped-def]
        assert received == project_id
        return "job-1"

    monkeypatch.setattr(cli_main, "_enqueue_design", fake_enqueue)
    result = runner.invoke(app, ["design", "resume", str(project_id)])
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
    """A VibeyError, not a bare ValueError, so the CLI guard can render it as
    a sentence instead of an asyncio traceback."""
    with pytest.raises(InvalidAnswer, match="QUESTION_ID=ANSWER"):
        cli_main._parse_question_answers(("Ship it",))
