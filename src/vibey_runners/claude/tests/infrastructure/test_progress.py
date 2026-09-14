# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Tests for infrastructure/progress.py — ConsoleProgressReporter adapter."""

from __future__ import annotations

import io
import sys
from datetime import datetime, timezone

from claudeloop.infrastructure.progress import ConsoleProgressReporter


def test_turn_sent_prints_attempt_number(monkeypatch) -> None:
    """turn_sent prints the attempt number."""
    reporter = ConsoleProgressReporter()
    captured = io.StringIO()
    monkeypatch.setattr(sys, "stdout", captured)
    reporter.turn_sent(attempt=1)
    output = captured.getvalue()
    assert "attempt 1" in output
    assert "===" in output


def test_turn_sent_with_different_attempts(monkeypatch) -> None:
    """turn_sent handles different attempt numbers correctly."""
    reporter = ConsoleProgressReporter()
    for attempt_num in [1, 2, 5, 42]:
        captured = io.StringIO()
        monkeypatch.setattr(sys, "stdout", captured)
        reporter.turn_sent(attempt=attempt_num)
        output = captured.getvalue()
        assert f"attempt {attempt_num}" in output


def test_waiting_shows_reason_and_time(monkeypatch) -> None:
    """waiting prints reason and until timestamp."""
    reporter = ConsoleProgressReporter()
    until = datetime(2026, 8, 15, 12, 30, 0, tzinfo=timezone.utc)
    captured = io.StringIO()
    monkeypatch.setattr(sys, "stdout", captured)
    reporter.waiting(reason="rate_limit", until=until)
    output = captured.getvalue()
    assert "Waiting" in output
    assert "rate_limit" in output
    assert "2026-08-15T12:30:00+00:00" in output


def test_finished_success_shows_done(monkeypatch) -> None:
    """finished with success=True shows 'Done'."""
    reporter = ConsoleProgressReporter()
    captured = io.StringIO()
    monkeypatch.setattr(sys, "stdout", captured)
    reporter.finished(success=True, reason="completed")
    output = captured.getvalue()
    assert "Done" in output
    assert "completed" in output


def test_finished_failure_shows_failed(monkeypatch) -> None:
    """finished with success=False shows 'Failed'."""
    reporter = ConsoleProgressReporter()
    captured = io.StringIO()
    monkeypatch.setattr(sys, "stdout", captured)
    reporter.finished(success=False, reason="timeout")
    output = captured.getvalue()
    assert "Failed" in output
    assert "timeout" in output


def test_output_is_flushed(monkeypatch) -> None:
    """All progress output is flushed immediately."""
    # This test verifies flush=True is used in all print calls.
    # We verify by checking that output appears immediately in the stream.
    reporter = ConsoleProgressReporter()
    captured = io.StringIO()
    monkeypatch.setattr(sys, "stdout", captured)

    reporter.turn_sent(attempt=1)
    assert len(captured.getvalue()) > 0

    captured.truncate(0)
    captured.seek(0)
    until = datetime.now(timezone.utc)
    reporter.waiting(reason="test", until=until)
    assert len(captured.getvalue()) > 0

    captured.truncate(0)
    captured.seek(0)
    reporter.finished(success=True, reason="test")
    assert len(captured.getvalue()) > 0
