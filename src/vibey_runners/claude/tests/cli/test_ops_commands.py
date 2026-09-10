# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from claudeloop.cli.app import app
from claudeloop.infrastructure.rundir import RunDirectory, runs_root_for

runner = CliRunner()
_ENV = {"NO_COLOR": "1", "TERM": "dumb", "FORCE_COLOR": "0"}


def _run_dir(tmp_path: Path) -> RunDirectory:
    return RunDirectory.create(runs_root_for(tmp_path), cwd=tmp_path)


def test_ops_command_help_smoke() -> None:
    for args in (
        ["permission-mode", "--help"],
        ["cwd", "--help"],
        ["slash", "--help"],
        ["tool", "--help"],
        ["attach", "--help"],
        ["folder", "--help"],
        ["skill", "--help"],
        ["plugin", "--help"],
        ["connector", "--help"],
        ["github", "--help"],
        ["memory", "--help"],
        ["artifact", "--help"],
        ["chat", "--help"],
        ["response", "--help"],
        ["research", "--help"],
        ["web-search", "--help"],
        ["voice", "--help"],
        ["speak", "--help"],
        ["snapshot", "--help"],
    ):
        result = runner.invoke(app, args, env=_ENV)
        assert result.exit_code == 0, args
        assert "Usage" in result.output or "help" in result.output.lower()


def test_snapshot_cli(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    directory = _run_dir(tmp_path)
    run_id = directory.read_meta().run_id
    out = tmp_path / "handoff.json"
    result = runner.invoke(
        app,
        ["snapshot", "--run-id", run_id, "--out", str(out), "--bundle"],
        env=_ENV,
    )
    assert result.exit_code == 0, result.output
    assert "snapshot_path:" in result.output
    assert "snapshot_digest:" in result.output
    assert (directory.snapshots_root / "latest.json").is_file()
    assert out.is_file()
    assert list(directory.snapshots_root.glob("*-manual.json"))


def test_snapshot_cli_no_run(tmp_path: Path, monkeypatch) -> None:
    """No matching run directory raises FileNotFoundError -> exit 1."""
    monkeypatch.chdir(tmp_path)
    result = runner.invoke(app, ["snapshot", "--run-id", "nope"], env=_ENV)
    assert result.exit_code == 1


def test_snapshot_cli_no_bundle_no_out(tmp_path: Path, monkeypatch) -> None:
    """--no-bundle and no --out skip the bundle_path/copied_to lines."""
    monkeypatch.chdir(tmp_path)
    directory = _run_dir(tmp_path)
    run_id = directory.read_meta().run_id
    result = runner.invoke(
        app,
        ["snapshot", "--run-id", run_id, "--no-bundle"],
        env=_ENV,
    )
    assert result.exit_code == 0, result.output
    assert "snapshot_path:" in result.output
    assert "bundle_path:" not in result.output
    assert "copied_to:" not in result.output


def test_permission_mode_and_resource_enqueue(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    directory = _run_dir(tmp_path)
    run_id = directory.read_meta().run_id
    result = runner.invoke(app, ["permission-mode", "plan", "--run-id", run_id], env=_ENV)
    assert result.exit_code == 0, result.output
    assert list(directory.inbox.glob("*.cmd.json"))
    note = tmp_path / "n.txt"
    note.write_text("hi", encoding="utf-8")
    result = runner.invoke(app, ["attach", str(note), "--run-id", run_id], env=_ENV)
    assert result.exit_code == 0, result.output
    result = runner.invoke(
        app, ["memory", "set", "prefs", "be concise", "--run-id", run_id], env=_ENV
    )
    assert result.exit_code == 0, result.output
    result = runner.invoke(app, ["memory", "list", "--run-id", run_id], env=_ENV)
    assert result.exit_code == 0
    assert "prefs" in result.output
    result = runner.invoke(app, ["chat", "pin", "sess-x"], env=_ENV)
    assert result.exit_code == 0
    result = runner.invoke(app, ["chat", "share", "sess-x"], env=_ENV)
    assert result.exit_code == 0
    assert "bundle" in result.output.lower() or "Share" in result.output
