"""Tests for ``vibey_bootstrap.heartbeat``."""

from __future__ import annotations

import threading
import time

import pytest

from vibey_bootstrap.heartbeat import (
    metrics_snapshot,
    record_consumer_iteration,
    record_message_settled,
    reset_state,
    start_heartbeat,
)


@pytest.fixture(autouse=True)
def _reset() -> None:
    reset_state()


def test_record_iteration_updates_metrics() -> None:
    record_consumer_iteration()
    snap = metrics_snapshot()
    assert snap["last_consumer_iteration_age_seconds"] is not None
    assert snap["last_consumer_iteration_age_seconds"] < 1.0


def test_record_settled_updates_metrics() -> None:
    record_message_settled()
    snap = metrics_snapshot()
    assert snap["last_sb_settle_age_seconds"] is not None


def test_start_heartbeat_emits_tick(caplog: pytest.LogCaptureFixture) -> None:
    stop = threading.Event()
    thread = start_heartbeat(stop, interval_seconds=0.1)
    try:
        with caplog.at_level("INFO", logger="vibey_bootstrap.heartbeat"):
            time.sleep(0.3)
    finally:
        stop.set()
        thread.join(timeout=1.0)
    assert any("heartbeat" in r.message.lower() for r in caplog.records)


def test_start_heartbeat_disabled_when_zero_interval() -> None:
    stop = threading.Event()
    thread = start_heartbeat(stop, interval_seconds=0)
    # Returns an already-joined inert thread
    assert not thread.is_alive()


def test_start_heartbeat_custom_snapshot_fn() -> None:
    captured: list[dict] = []

    def snap_fn() -> dict:
        captured.append({"called": True})
        return {"latency_snapshot": {"op1": {"p95": 1.5, "errors": 2}}, "counters": {"x": 1}}

    stop = threading.Event()
    thread = start_heartbeat(stop, interval_seconds=0.05, snapshot_fn=snap_fn)
    try:
        time.sleep(0.15)
    finally:
        stop.set()
        thread.join(timeout=1.0)
    assert captured


def test_start_consumer_watchdog_fires_after_silence(
    caplog: pytest.LogCaptureFixture,
) -> None:
    from vibey_bootstrap.alerts import (
        drain_pending_alerts,
        register_dispatcher,
    )
    from vibey_bootstrap.alerts import reset_state as reset_alerts
    from vibey_bootstrap.heartbeat import start_consumer_watchdog

    reset_alerts()
    register_dispatcher(lambda *a: None, recipients=["ops@example.com"])
    record_consumer_iteration()
    # Make this iteration appear ancient by clobbering the timestamp
    import vibey_bootstrap.heartbeat as hb

    with hb._state_lock:
        hb._last_consumer_iteration_at = 1.0  # very old monotonic value

    stop = threading.Event()
    thread = start_consumer_watchdog(
        stop,
        interval_seconds=0.05,
        silence_threshold_seconds=0.0,
        resilence_window_seconds=10.0,
    )
    try:
        time.sleep(0.2)
    finally:
        stop.set()
        thread.join(timeout=1.0)
    pending = drain_pending_alerts()
    matched = [p for p in pending if p.dedup_key == "watchdog:consumer_silent"]
    assert matched
    reset_alerts()


def test_start_consumer_watchdog_disabled() -> None:
    from vibey_bootstrap.heartbeat import start_consumer_watchdog

    stop = threading.Event()
    thread = start_consumer_watchdog(stop, interval_seconds=0)
    assert not thread.is_alive()


def test_start_background_monitors(monkeypatch: pytest.MonkeyPatch) -> None:
    from vibey_bootstrap.heartbeat import start_background_monitors

    monkeypatch.setenv("HEARTBEAT_INTERVAL_SECONDS", "0.05")
    monkeypatch.setenv("WATCHDOG_INTERVAL_SECONDS", "0.05")
    stop = threading.Event()
    threads = start_background_monitors(stop)
    try:
        assert len(threads) == 2
        time.sleep(0.1)
    finally:
        stop.set()
        for t in threads:
            t.join(timeout=1.0)


def test_start_background_monitors_disabled(monkeypatch: pytest.MonkeyPatch) -> None:
    from vibey_bootstrap.heartbeat import start_background_monitors

    monkeypatch.setenv("HEARTBEAT_INTERVAL_SECONDS", "0")
    monkeypatch.setenv("WATCHDOG_INTERVAL_SECONDS", "0")
    stop = threading.Event()
    threads = start_background_monitors(stop)
    assert threads == []


def test_reset_state_refuses_without_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AZURE_BOOTSTRAP_ALLOW_RESET", raising=False)
    with pytest.raises(RuntimeError):
        reset_state()
