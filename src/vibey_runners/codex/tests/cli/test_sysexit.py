# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Exit code translation for RunResult outcomes."""

from __future__ import annotations

from codexloop.application.dto import RunResult
from codexloop.cli.asyncio import sysexit_for


def test_sysexit_for_success() -> None:
    """Successful run returns 0."""
    result = RunResult(success=True, reason="done", turns=3, thread_id="t1")
    assert sysexit_for(result) == 0


def test_sysexit_for_stop() -> None:
    """Operator stop returns 130 (SIGINT-like)."""
    result = RunResult(success=False, reason="stop", turns=2, thread_id="t2")
    assert sysexit_for(result) == 130


def test_sysexit_for_wind_down() -> None:
    """Wind-down returns 75 (EX_TEMPFAIL) to signal handoff."""
    result = RunResult(success=False, reason="wind-down: capacity", turns=5, thread_id="t3")
    assert sysexit_for(result) == 75


def test_sysexit_for_generic_failure() -> None:
    """Any other failure returns 1."""
    result = RunResult(success=False, reason="error", turns=1, thread_id="t4")
    assert sysexit_for(result) == 1
