# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""The wind-down exit code, and the command that requests one."""

from __future__ import annotations

from pathlib import Path

from typer.testing import CliRunner

from claudeloop.bootstrap_ops import enqueue_wind_down
from claudeloop.cli.app import app
from claudeloop.domain.control import WindDownCommand
from claudeloop.domain.handoff_marker import EXIT_WIND_DOWN
from claudeloop.infrastructure.control import FileRunControl
from claudeloop.infrastructure.rundir import RunDirectory, runs_root_for

runner = CliRunner()


def test_the_command_is_advertised_and_explains_the_difference_from_stop() -> None:
    result = runner.invoke(app, ["wind-down", "--help"])
    assert result.exit_code == 0
    assert "natural break" in result.output
    assert "75" in result.output


def test_enqueue_writes_a_command_the_runner_will_actually_pick_up(tmp_path: Path) -> None:
    """The inbox only reads *.cmd.json, so a correctly-shaped payload under the
    wrong name is silently ignored -- worth pinning."""
    RunDirectory.create(runs_root_for(tmp_path), cwd=tmp_path, run_id="r1")

    result = enqueue_wind_down(tmp_path, "r1", reason="rotate")

    assert result.run_id == "r1"
    assert result.command_type == "wind_down"
    inbox = runs_root_for(tmp_path) / "r1" / "inbox"
    assert list(inbox.glob("*.cmd.json")), "runner polls *.cmd.json only"
    assert FileRunControl(inbox).poll() == [WindDownCommand(reason="rotate")]


def test_the_exit_code_is_not_one_of_the_taken_ones() -> None:
    """0 success, 1 failure, 2 usage, 130 operator stop. A supervisor needs to
    tell "resume me elsewhere" from all of those."""
    assert EXIT_WIND_DOWN == 75
    assert EXIT_WIND_DOWN not in {0, 1, 2, 130}
