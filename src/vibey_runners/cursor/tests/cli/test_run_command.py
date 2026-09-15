# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

import json
import re
from pathlib import Path

from typer.testing import CliRunner

from cursorloop.cli.app import app

runner = CliRunner()


def _strip_ansi(text: str) -> str:
    return re.sub(r"\x1b\[[0-9;]*m", "", text)


def _auth_failure_script(tmp_path: Path) -> Path:
    script = tmp_path / "auth.json"
    script.write_text(
        json.dumps(
            {
                "probes": [{"signals": {}}],
                "turns": [
                    {
                        "signals": {
                            "error_type": "AuthenticationError",
                            "error_message": "bad key",
                        },
                        "output_text": "",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    return script


def test_run_help_documents_the_never_block_flags(monkeypatch) -> None:
    # CI runners default to a narrow COLUMNS; Rich also injects ANSI between
    # dashes (``\x1b…m-\x1b…m-turn-timeout``), which breaks a raw substring
    # check for ``--turn-timeout``. Force a wide, colorless dump and strip
    # any residual SGR sequences before asserting.
    monkeypatch.setenv("COLUMNS", "200")
    monkeypatch.setenv("NO_COLOR", "1")
    monkeypatch.setenv("TERM", "dumb")
    result = runner.invoke(
        app,
        ["run", "--help"],
        env={"COLUMNS": "200", "NO_COLOR": "1", "TERM": "dumb"},
    )
    assert result.exit_code == 0
    help_text = _strip_ansi(result.stdout)
    for flag in ("--turn-timeout", "--stall-timeout", "--max-wait", "--managed-hooks"):
        assert flag in help_text, help_text


def test_test_agent_gate_requires_both_env_vars(monkeypatch, tmp_path: Path) -> None:
    """A scripted agent must never be reachable by setting one variable —
    especially not by an env var leaking into a real user's shell."""
    script = tmp_path / "script.json"
    script.write_text('{"probes": [], "turns": []}')
    monkeypatch.setenv("CURSORLOOP_TEST_AGENT_SCRIPT", str(script))
    monkeypatch.delenv("CURSORLOOP_ALLOW_TEST_AGENT", raising=False)

    plan = tmp_path / "plan.md"
    plan.write_text("- [ ] do a thing\n")
    result = runner.invoke(app, ["run", "--plan", str(plan)])
    assert result.exit_code != 0
    assert "CURSORLOOP_ALLOW_TEST_AGENT" in result.stdout


def test_version_flag() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "cursorloop" in result.stdout


def test_authentication_failure_exits_3(monkeypatch, tmp_path: Path) -> None:
    plan = tmp_path / "plan.md"
    plan.write_text("- [ ] do a thing\n")
    monkeypatch.setenv("CURSORLOOP_ALLOW_TEST_AGENT", "1")
    monkeypatch.setenv("CURSORLOOP_TEST_AGENT_SCRIPT", str(_auth_failure_script(tmp_path)))
    result = runner.invoke(
        app, ["run", "--plan", str(plan), "--cwd", str(tmp_path), "--no-managed-hooks"]
    )
    assert result.exit_code == 3


def test_run_rejects_invalid_plan(tmp_path: Path) -> None:
    plan = tmp_path / "empty.md"
    plan.write_text("   \n")
    result = runner.invoke(app, ["run", "--plan", str(plan), "--cwd", str(tmp_path)])
    assert result.exit_code == 1
    combined = (result.stdout or "") + (result.stderr or "")
    assert "Invalid plan" in combined or "blank" in combined.lower()


def test_run_success_with_scripted_agent(monkeypatch, tmp_path: Path) -> None:
    plan = tmp_path / "plan.md"
    plan.write_text("Say hi and finish.\n", encoding="utf-8")
    script = tmp_path / "done.json"
    script.write_text(
        json.dumps(
            {
                "probes": [{"signals": {}}],
                "turns": [
                    {
                        "signals": {},
                        "verdict": {
                            "complete": True,
                            "remaining_work": [],
                            "blocked_on": None,
                            "summary": "ok",
                        },
                        "output_text": "CURSORLOOP_TASK_FULLY_COMPLETE",
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("CURSORLOOP_ALLOW_TEST_AGENT", "1")
    monkeypatch.setenv("CURSORLOOP_TEST_AGENT_SCRIPT", str(script))
    result = runner.invoke(
        app,
        [
            "run",
            "--plan",
            str(plan),
            "--cwd",
            str(tmp_path),
            "--no-managed-hooks",
            "--max-turns",
            "2",
            "--model",
            "composer",
        ],
    )
    assert result.exit_code == 0
    combined = (result.stdout or "") + (result.stderr or "")
    assert "Done:" in combined


def test_run_build_runner_runtime_error_exits_one(monkeypatch, tmp_path: Path) -> None:
    plan = tmp_path / "plan.md"
    plan.write_text("work\n", encoding="utf-8")
    monkeypatch.delenv("CURSORLOOP_ALLOW_TEST_AGENT", raising=False)
    monkeypatch.delenv("CURSORLOOP_TEST_AGENT_SCRIPT", raising=False)
    monkeypatch.delenv("CURSOR_API_KEY", raising=False)

    def boom(**kwargs: object) -> object:
        del kwargs
        raise RuntimeError("CURSORLOOP_ALLOW_TEST_AGENT missing")

    from unittest.mock import patch

    with patch("cursorloop.cli.commands.run.bootstrap.build_runner", side_effect=boom):
        result = runner.invoke(app, ["run", "--plan", str(plan), "--cwd", str(tmp_path)])
    assert result.exit_code == 1


def test_run_failed_turn_prints_reason(monkeypatch, tmp_path: Path) -> None:
    plan = tmp_path / "plan.md"
    plan.write_text("work\n", encoding="utf-8")
    monkeypatch.setenv("CURSORLOOP_ALLOW_TEST_AGENT", "1")
    monkeypatch.setenv("CURSORLOOP_TEST_AGENT_SCRIPT", str(_auth_failure_script(tmp_path)))
    result = runner.invoke(
        app,
        [
            "run",
            "--plan",
            str(plan),
            "--cwd",
            str(tmp_path),
            "--no-managed-hooks",
            "--max-turns",
            "2",
        ],
    )
    assert result.exit_code == 3
    combined = (result.stdout or "") + (result.stderr or "")
    assert "Run failed" in combined or "authentication" in combined.lower()


def test_run_rejects_a_run_id_that_would_escape_the_runs_root(tmp_path: Path) -> None:
    """A run id becomes a path segment, so traversal has to be refused before
    anything is created -- and refused with a message, not a traceback."""
    plan = tmp_path / "plan.md"
    plan.write_text("# Plan\n\nDo the thing.\n")
    result = runner.invoke(
        app,
        ["run", "--plan", str(plan), "--cwd", str(tmp_path), "--run-id", "../escape"],
    )
    assert result.exit_code == 2
    combined = (result.stdout or "") + (result.stderr or "")
    assert "invalid run id" in combined
    assert not (tmp_path.parent / "escape").exists()


def test_run_refuses_to_reuse_an_existing_run_id(tmp_path: Path) -> None:
    """Silently reopening someone else's run directory would interleave two
    runs' events in one log."""
    from cursorloop.infrastructure.rundir import RunDirectory, runs_root_for

    plan = tmp_path / "plan.md"
    plan.write_text("# Plan\n\nDo the thing.\n")
    RunDirectory.create(runs_root_for(tmp_path), cwd=tmp_path, run_id="taken")

    result = runner.invoke(
        app, ["run", "--plan", str(plan), "--cwd", str(tmp_path), "--run-id", "taken"]
    )
    assert result.exit_code == 2
    combined = (result.stdout or "") + (result.stderr or "")
    assert "already exists" in combined
