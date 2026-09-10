# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

from typer.testing import CliRunner

from cursorloop.cli.app import app

runner = CliRunner()


def test_root_help_lists_core_commands() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    for name in ("run", "resume", "doctor", "hooks", "models"):
        assert name in result.stdout


def test_models_lists_shipped_presets() -> None:
    result = runner.invoke(app, ["models"])
    assert result.exit_code == 0
    assert "composer" in result.stdout
