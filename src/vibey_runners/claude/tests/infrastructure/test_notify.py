# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Tests for infrastructure/notify.py — StderrNotifier adapter."""

from __future__ import annotations

import io
import sys
from contextlib import redirect_stderr

from claudeloop.infrastructure.notify import StderrNotifier


def test_notify_prints_banner_message_to_stderr() -> None:
    """StderrNotifier writes message wrapped in banner to stderr."""
    notifier = StderrNotifier()
    captured = io.StringIO()
    with redirect_stderr(captured):
        notifier.notify("Test message")
    output = captured.getvalue()
    assert "Test message" in output
    assert "!" in output  # Banner should contain exclamation marks


def test_notify_banner_length_scales_with_message() -> None:
    """Banner length adapts to message length within min/max bounds."""
    notifier = StderrNotifier()

    # Short message should get min banner length (20)
    captured_short = io.StringIO()
    with redirect_stderr(captured_short):
        notifier.notify("Hi")
    short_output = captured_short.getvalue()
    short_banner_line = [line for line in short_output.split("\n") if line and set(line) == {"!"}][
        0
    ]
    assert len(short_banner_line) >= 20

    # Long message should get capped banner length (max 78)
    long_message = "A" * 100
    captured_long = io.StringIO()
    with redirect_stderr(captured_long):
        notifier.notify(long_message)
    long_output = captured_long.getvalue()
    long_banner_line = [line for line in long_output.split("\n") if line and set(line) == {"!"}][0]
    assert len(long_banner_line) <= 78

    # Medium message should get banner matching its length
    medium_message = "A" * 50
    captured_medium = io.StringIO()
    with redirect_stderr(captured_medium):
        notifier.notify(medium_message)
    medium_output = captured_medium.getvalue()
    medium_banner_line = [
        line for line in medium_output.split("\n") if line and set(line) == {"!"}
    ][0]
    assert len(medium_banner_line) == 50


def test_notify_writes_to_stderr_not_stdout(monkeypatch) -> None:
    """Notification goes to stderr, not stdout."""
    notifier = StderrNotifier()
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()
    monkeypatch.setattr(sys, "stdout", stdout_capture)
    monkeypatch.setattr(sys, "stderr", stderr_capture)
    notifier.notify("Alert")
    assert "Alert" in stderr_capture.getvalue()
    assert stdout_capture.getvalue() == ""


def test_notify_banner_appears_before_and_after_message() -> None:
    """Message is sandwiched between two identical banner lines."""
    notifier = StderrNotifier()
    captured = io.StringIO()
    with redirect_stderr(captured):
        notifier.notify("Middle")
    lines = [line for line in captured.getvalue().split("\n") if line]
    assert len(lines) == 3
    assert lines[0] == lines[2]  # First and last lines are identical banners
    assert "Middle" in lines[1]
    assert set(lines[0]) == {"!"}  # First line is all exclamation marks
