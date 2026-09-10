# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""The root -v / -q / --log-level / --log-file surface, and what it configures."""

from __future__ import annotations

import logging
from pathlib import Path

from typer.testing import CliRunner

from claudeloop.bootstrap import configure_cli_logging
from claudeloop.cli.app import app
from claudeloop.domain.verbosity import resolve_log_plan

runner = CliRunner()


def test_quiet_and_verbose_together_are_refused_before_anything_runs() -> None:
    result = runner.invoke(app, ["-q", "-v", "status", "--help"])
    assert result.exit_code == 2
    assert "mutually exclusive" in result.output


def test_an_invalid_log_level_is_refused_with_a_message() -> None:
    result = runner.invoke(app, ["--log-level", "LOUD", "status", "--help"])
    assert result.exit_code == 2
    assert "invalid log level" in result.output


def test_third_party_loggers_stay_quiet_until_the_net_is_widened(tmp_path: Path) -> None:
    """asyncio and the vendor SDK are noise at -v; -vv is the explicit ask."""
    try:
        configure_cli_logging(plan=resolve_log_plan(verbose=1), log_file=tmp_path / "a.jsonl")
        assert logging.getLogger("httpx").level == logging.WARNING

        configure_cli_logging(plan=resolve_log_plan(verbose=2), log_file=tmp_path / "b.jsonl")
        assert logging.getLogger("httpx").level == logging.DEBUG
    finally:
        logging.getLogger().handlers.clear()


def test_log_file_is_written(tmp_path: Path) -> None:
    log_file = tmp_path / "out.jsonl"
    try:
        configure_cli_logging(plan=resolve_log_plan(verbose=1), log_file=log_file)
        logging.getLogger("claudeloop.test").info("hello")
    finally:
        logging.getLogger().handlers.clear()
    assert log_file.exists()
