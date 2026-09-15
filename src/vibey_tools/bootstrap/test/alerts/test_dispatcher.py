"""Tests for ``vibey_bootstrap.alerts.dispatcher``."""

from __future__ import annotations

import sys
import time
from typing import Any

import pytest

from vibey_bootstrap.alerts import (
    AlertSeverity,
    alert_dev_team,
    drain_pending_alerts,
    install_global_exception_hooks,
    register_dispatcher,
    reset_state,
)


@pytest.fixture
def calls() -> list[tuple[list[str], str, str]]:
    received: list[tuple[list[str], str, str]] = []

    def sender(recipients: list[str], subject: str, body: str) -> None:
        received.append((recipients, subject, body))

    reset_state()
    register_dispatcher(sender, recipients=["ops@example.com"])
    yield received
    reset_state()


def test_dedup_within_window(calls: list[tuple[list[str], str, str]]) -> None:
    for _ in range(3):
        alert_dev_team(AlertSeverity.CRITICAL, "db down", dedup_key="dbd")
    assert len(calls) == 1


def test_dedup_releases_after_window(
    calls: list[tuple[list[str], str, str]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ALERT_DEDUP_WINDOW_SECONDS", "0.1")
    alert_dev_team(AlertSeverity.CRITICAL, "subj1", dedup_key="k1")
    time.sleep(0.2)
    alert_dev_team(AlertSeverity.CRITICAL, "subj1", dedup_key="k1")
    assert len(calls) == 2


def test_rate_limit_folds_into_digest(
    calls: list[tuple[list[str], str, str]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ALERT_MAX_PER_HOUR", "2")
    for i in range(5):
        alert_dev_team(AlertSeverity.CRITICAL, f"distinct subject {i}", dedup_key=f"k{i}")
    assert len(calls) == 2
    pending = drain_pending_alerts()
    assert len(pending) == 3


def test_escalation_promotes_after_threshold(
    calls: list[tuple[list[str], str, str]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("ALERT_ESCALATE_AFTER", "3")
    monkeypatch.setenv("ALERT_ESCALATE_WINDOW_SECONDS", "30")
    monkeypatch.setenv("ALERT_DEDUP_WINDOW_SECONDS", "0.001")
    # Fire three distinct dedup keys to bypass dedup, but with same escalation key
    for i in range(3):
        time.sleep(0.005)
        alert_dev_team(
            AlertSeverity.ERROR,
            f"db slow #{i}",
            dedup_key="db_slow",
        )
    # Expect one CRITICAL email from escalation
    escalated = [c for c in calls if "[ESCALATED]" in c[1]]
    assert escalated, f"expected an [ESCALATED] email, got {calls}"


def test_kill_switch(monkeypatch: pytest.MonkeyPatch) -> None:
    received: list[Any] = []

    def sender(*args: Any) -> None:
        received.append(args)

    reset_state()
    register_dispatcher(sender, recipients=["ops@example.com"])
    monkeypatch.setenv("DEV_ALERTS_ENABLED", "false")
    alert_dev_team(AlertSeverity.CRITICAL, "subj", dedup_key="k")
    assert received == []
    # Kill switch should NOT add to pending digest either.
    assert drain_pending_alerts() == []
    reset_state()


def test_swallows_dispatcher_exception() -> None:
    reset_state()

    def bad_sender(*args: Any) -> None:
        raise RuntimeError("network down")

    register_dispatcher(bad_sender, recipients=["ops@example.com"])
    # Should not raise.
    alert_dev_team(AlertSeverity.CRITICAL, "subj", dedup_key="k")
    pending = drain_pending_alerts()
    assert any(p.dedup_key == "k" for p in pending)
    reset_state()


def test_global_exception_hook_fires_critical() -> None:
    reset_state()
    received: list[tuple[list[str], str, str]] = []

    def sender(recipients: list[str], subject: str, body: str) -> None:
        received.append((recipients, subject, body))

    register_dispatcher(sender, recipients=["ops@example.com"])
    install_global_exception_hooks()
    try:
        sys.excepthook(ValueError, ValueError("hook test"), None)  # type: ignore[misc]
    except Exception:  # noqa: BLE001
        pass
    matched = [r for r in received if "ValueError" in r[1]]
    assert matched
    reset_state()
