# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Operator-facing failure output, and the logging the flags configure."""

from __future__ import annotations

import json
import logging
from pathlib import Path

import pytest
import typer
from typer.testing import CliRunner

from vibey.cli.errors import EXIT_BLOCKED, guard, render
from vibey.cli.main import app
from vibey.domain.errors import (
    BudgetExceeded,
    InvalidPhaseError,
    NoEligibleEngine,
    UnknownProject,
)
from vibey.domain.verbosity import resolve_log_plan
from vibey.infrastructure.logging import (
    NullAppLogger,
    StructlogAppLogger,
    configure_logging,
    get_logger,
)

# Typer force-enables rich ANSI styling whenever GITHUB_ACTIONS is set
# (typer/rich_utils.py), which CI always has and a local shell never does.
# That embeds escape codes inside option names, breaking plain substring
# checks against --help output -- disable it the way Typer itself exposes.
runner = CliRunner(env={"_TYPER_FORCE_DISABLE_TERMINAL": "1"})


def test_known_error_renders_as_a_sentence_not_a_traceback() -> None:
    message = render(UnknownProject("unknown project 123"))
    assert message.startswith("Error: unknown project 123")
    assert "Traceback" not in message


def test_errors_with_a_known_remedy_say_what_to_try_next() -> None:
    assert "vibey engines" in render(NoEligibleEngine("nothing eligible"))
    assert "[budget]" in render(BudgetExceeded("over cap"))


def test_errors_without_an_honest_remedy_suggest_nothing() -> None:
    """Inventing a remedy that does not work is worse than staying quiet."""
    message = render(InvalidPhaseError("bad state"))
    assert message.splitlines()[0] == "Error: bad state"


def test_guard_converts_a_vibey_error_into_an_exit_code() -> None:
    with pytest.raises(typer.Exit) as excinfo, guard():
        raise UnknownProject("nope")
    assert excinfo.value.exit_code == EXIT_BLOCKED


def test_guard_lets_unknown_errors_keep_their_traceback() -> None:
    """Swallowing an error we do not understand trades a confusing message for
    a silent one."""
    with pytest.raises(RuntimeError, match="something else"), guard():
        raise RuntimeError("something else")


def test_guard_treats_ctrl_c_as_a_decision_not_a_failure() -> None:
    with pytest.raises(typer.Exit) as excinfo, guard():
        raise KeyboardInterrupt
    assert excinfo.value.exit_code == 130


# --- flags -------------------------------------------------------------------


def test_verbosity_flags_are_advertised() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    for flag in ("-v", "--verbose", "--quiet", "--log-level", "--log-file"):
        assert flag in result.output


def test_quiet_and_verbose_together_exit_with_a_usage_error() -> None:
    result = runner.invoke(app, ["-q", "-v", "status", "--help"])
    assert result.exit_code == 2
    assert "mutually exclusive" in result.output


def test_invalid_log_level_is_refused_with_a_message() -> None:
    result = runner.invoke(app, ["--log-level", "LOUD", "status", "--help"])
    assert result.exit_code == 2
    assert "invalid log level" in result.output


# --- transports --------------------------------------------------------------


def test_log_file_receives_redacted_json_lines(tmp_path: Path) -> None:
    log_file = tmp_path / "vibey.jsonl"
    configure_logging(resolve_log_plan(verbose=1), log_file=log_file, human_console=False)
    try:
        get_logger().info("probe.done", api_key="sk-should-not-appear", engine="claudeloop")
    finally:
        logging.getLogger().handlers.clear()

    records = [json.loads(line) for line in log_file.read_text().splitlines() if line.strip()]
    assert records, "expected at least one JSON line"
    record = records[-1]
    assert record["event"] == "probe.done"
    assert record["transport"] == "file"
    assert record["engine"] == "claudeloop"
    # The same redactor the event ledger uses: a secret must not be safe in one
    # sink and leaked in another.
    assert "sk-should-not-appear" not in log_file.read_text()


def test_third_party_loggers_stay_quiet_until_the_net_is_widened(tmp_path: Path) -> None:
    configure_logging(resolve_log_plan(verbose=1), log_file=tmp_path / "a.jsonl")
    assert logging.getLogger("asyncpg").level == logging.WARNING

    configure_logging(resolve_log_plan(verbose=2), log_file=tmp_path / "b.jsonl")
    assert logging.getLogger("asyncpg").level == logging.DEBUG
    logging.getLogger().handlers.clear()


def test_guard_treats_a_closed_pipe_as_success() -> None:
    """`vibey ledger | head` closes the pipe early. That is the reader being
    done, not the command failing."""
    with pytest.raises(typer.Exit) as excinfo, guard():
        raise BrokenPipeError
    assert excinfo.value.exit_code == 0


def test_the_structlog_adapter_forwards_every_level(tmp_path: Path) -> None:
    log_file = tmp_path / "levels.jsonl"
    configure_logging(resolve_log_plan(verbose=1), log_file=log_file, human_console=False)
    try:
        logger = StructlogAppLogger(component="unit")
        bound = logger.bind(run_id="r1")
        logger.debug("d.event")
        logger.info("i.event")
        logger.warning("w.event")
        logger.error("e.event")
        bound.info("bound.event")
    finally:
        logging.getLogger().handlers.clear()

    text = log_file.read_text()
    for event in ("d.event", "i.event", "w.event", "e.event", "bound.event"):
        assert event in text
    assert '"run_id": "r1"' in text


def test_the_null_logger_absorbs_everything() -> None:
    """The default, so nothing is obliged to configure logging in order to run
    -- and so a library consumer never gets output it did not ask for."""
    null = NullAppLogger()
    assert null.bind(run_id="r1") is null
    for level in ("debug", "info", "warning", "error"):
        getattr(null, level)("event", key="value")
