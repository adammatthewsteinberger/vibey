# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Regression tests for --cwd isolation across all subcommands.

These tests verify that commands respect --cwd and never write to Path.cwd()
when an explicit --cwd is passed. The pattern: create a canary file in the
process cwd, run a command with --cwd pointing elsewhere, and assert the canary
is unchanged.

This prevents the exact incident that prompted this feature: a `resume` from
the wrong directory auto-committed work into the live checkout.
"""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from claudeloop.cli.app import app
from claudeloop.infrastructure.rundir import RunDirectory, runs_root_for

runner = CliRunner()
_ENV = {"NO_COLOR": "1", "TERM": "dumb", "FORCE_COLOR": "0"}


def _setup_run_dir(cwd: Path) -> tuple[RunDirectory, str]:
    """Create a run directory and return it with its run_id."""
    directory = RunDirectory.create(runs_root_for(cwd), cwd=cwd)
    run_id = directory.read_meta().run_id
    return directory, run_id


def test_resume_cwd_isolation(tmp_path: Path, monkeypatch) -> None:
    """resume --cwd never touches the process cwd."""
    # Setup: create a fake worktree with a run
    worktree = tmp_path / "worktree"
    worktree.mkdir()
    directory, run_id = _setup_run_dir(worktree)

    # Canary: a file in the process cwd that should never be touched
    process_cwd = tmp_path / "process_cwd"
    process_cwd.mkdir()
    monkeypatch.chdir(process_cwd)
    canary = process_cwd / ".claudeloop" / "canary.txt"
    canary.parent.mkdir(parents=True, exist_ok=True)
    canary.write_text("untouched", encoding="utf-8")
    canary_mtime = canary.stat().st_mtime

    # Act: resume with explicit --cwd (should fail quickly due to no session, but that's fine)
    runner.invoke(
        app,
        ["resume", "--session-id", run_id, "--cwd", str(worktree), "--max-turns", "0"],
        env=_ENV,
    )
    # The command will likely fail (no active session), but the key assertion is below

    # Assert: canary is unchanged
    assert canary.exists()
    assert canary.read_text(encoding="utf-8") == "untouched"
    assert canary.stat().st_mtime == canary_mtime, "canary file was modified"


def test_stop_cwd_isolation(tmp_path: Path, monkeypatch) -> None:
    """stop --cwd never touches the process cwd."""
    worktree = tmp_path / "worktree"
    worktree.mkdir()
    directory, run_id = _setup_run_dir(worktree)

    process_cwd = tmp_path / "process_cwd"
    process_cwd.mkdir()
    monkeypatch.chdir(process_cwd)
    canary = process_cwd / ".canary"
    canary.write_text("untouched", encoding="utf-8")
    canary_mtime = canary.stat().st_mtime

    # Act: stop with explicit --cwd
    runner.invoke(
        app,
        ["stop", "--run-id", run_id, "--cwd", str(worktree)],
        env=_ENV,
    )
    # Expected to fail (no active run), but we only care about file isolation

    # Assert: canary unchanged
    assert canary.exists()
    assert canary.read_text(encoding="utf-8") == "untouched"
    assert canary.stat().st_mtime == canary_mtime


def test_wind_down_cwd_isolation(tmp_path: Path, monkeypatch) -> None:
    """wind-down --cwd never touches the process cwd."""
    worktree = tmp_path / "worktree"
    worktree.mkdir()
    directory, run_id = _setup_run_dir(worktree)

    process_cwd = tmp_path / "process_cwd"
    process_cwd.mkdir()
    monkeypatch.chdir(process_cwd)
    canary = process_cwd / ".canary"
    canary.write_text("untouched", encoding="utf-8")
    canary_mtime = canary.stat().st_mtime

    runner.invoke(
        app,
        ["wind-down", "--run-id", run_id, "--cwd", str(worktree)],
        env=_ENV,
    )

    assert canary.exists()
    assert canary.read_text(encoding="utf-8") == "untouched"
    assert canary.stat().st_mtime == canary_mtime


def test_status_cwd_isolation(tmp_path: Path, monkeypatch) -> None:
    """status --cwd never touches the process cwd."""
    worktree = tmp_path / "worktree"
    worktree.mkdir()
    directory, run_id = _setup_run_dir(worktree)

    process_cwd = tmp_path / "process_cwd"
    process_cwd.mkdir()
    monkeypatch.chdir(process_cwd)
    canary = process_cwd / ".canary"
    canary.write_text("untouched", encoding="utf-8")
    canary_mtime = canary.stat().st_mtime

    runner.invoke(
        app,
        ["status", "--run-id", run_id, "--cwd", str(worktree)],
        env=_ENV,
    )

    assert canary.exists()
    assert canary.read_text(encoding="utf-8") == "untouched"
    assert canary.stat().st_mtime == canary_mtime


def test_logs_cwd_isolation(tmp_path: Path, monkeypatch) -> None:
    """logs --cwd never touches the process cwd."""
    worktree = tmp_path / "worktree"
    worktree.mkdir()
    directory, run_id = _setup_run_dir(worktree)

    process_cwd = tmp_path / "process_cwd"
    process_cwd.mkdir()
    monkeypatch.chdir(process_cwd)
    canary = process_cwd / ".canary"
    canary.write_text("untouched", encoding="utf-8")
    canary_mtime = canary.stat().st_mtime

    # logs will try to read but should not create anything in process_cwd
    runner.invoke(
        app,
        ["logs", "--run-id", run_id, "--cwd", str(worktree)],
        env=_ENV,
    )

    assert canary.exists()
    assert canary.read_text(encoding="utf-8") == "untouched"
    assert canary.stat().st_mtime == canary_mtime


def test_unwind_cwd_isolation(tmp_path: Path, monkeypatch) -> None:
    """unwind --cwd never touches the process cwd."""
    worktree = tmp_path / "worktree"
    worktree.mkdir()
    directory, run_id = _setup_run_dir(worktree)

    process_cwd = tmp_path / "process_cwd"
    process_cwd.mkdir()
    monkeypatch.chdir(process_cwd)
    canary = process_cwd / ".canary"
    canary.write_text("untouched", encoding="utf-8")
    canary_mtime = canary.stat().st_mtime

    # unwind will fail (no savepoints), but should not touch process_cwd
    runner.invoke(
        app,
        ["unwind", "--to", "1", "--run-id", run_id, "--cwd", str(worktree)],
        env=_ENV,
    )

    assert canary.exists()
    assert canary.read_text(encoding="utf-8") == "untouched"
    assert canary.stat().st_mtime == canary_mtime


def test_watch_cwd_isolation(tmp_path: Path, monkeypatch) -> None:
    """watch --cwd never touches the process cwd."""
    worktree = tmp_path / "worktree"
    worktree.mkdir()
    directory, run_id = _setup_run_dir(worktree)

    process_cwd = tmp_path / "process_cwd"
    process_cwd.mkdir()
    monkeypatch.chdir(process_cwd)
    canary = process_cwd / ".canary"
    canary.write_text("untouched", encoding="utf-8")
    canary_mtime = canary.stat().st_mtime

    # watch with --no-follow exits quickly
    runner.invoke(
        app,
        ["watch", "--run-id", run_id, "--cwd", str(worktree), "--no-follow"],
        env=_ENV,
    )

    assert canary.exists()
    assert canary.read_text(encoding="utf-8") == "untouched"
    assert canary.stat().st_mtime == canary_mtime


def test_prompt_cwd_isolation(tmp_path: Path, monkeypatch) -> None:
    """prompt --cwd never touches the process cwd."""
    worktree = tmp_path / "worktree"
    worktree.mkdir()
    directory, run_id = _setup_run_dir(worktree)

    process_cwd = tmp_path / "process_cwd"
    process_cwd.mkdir()
    monkeypatch.chdir(process_cwd)
    canary = process_cwd / ".canary"
    canary.write_text("untouched", encoding="utf-8")
    canary_mtime = canary.stat().st_mtime

    runner.invoke(
        app,
        ["prompt", "test prompt", "--now", "--run-id", run_id, "--cwd", str(worktree)],
        env=_ENV,
    )

    assert canary.exists()
    assert canary.read_text(encoding="utf-8") == "untouched"
    assert canary.stat().st_mtime == canary_mtime
