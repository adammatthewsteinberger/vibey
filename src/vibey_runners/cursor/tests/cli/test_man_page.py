# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

from typer.testing import CliRunner

from cursorloop.cli.app import app
from cursorloop.cli.man_page import render_man_page

runner = CliRunner()


def test_man_flag_prints_reference() -> None:
    result = runner.invoke(app, ["--man"])
    assert result.exit_code == 0
    assert "CURSORLOOP(1)" in result.stdout
    assert "never blocks" in result.stdout.lower() or "Never blocks" in result.stdout


def test_render_man_page_mentions_exit_codes() -> None:
    text = render_man_page()
    assert "130" in text
    assert "CURSOR_API_KEY" in text
