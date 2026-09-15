# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Stderr notifier must be loud: credits exhaustion is not a quiet log line."""

import pytest

from agyloop.infrastructure.notify import StderrNotifier


def test_stderr_notifier_writes_loud_alert_banner(capsys: pytest.CaptureFixture[str]) -> None:
    StderrNotifier().notify("agyloop: credits exhausted — top up the Google account")
    err = capsys.readouterr().err
    assert "AGYLOOP ALERT" in err
    assert "credits exhausted" in err.lower()
    assert err.count("***") >= 2
