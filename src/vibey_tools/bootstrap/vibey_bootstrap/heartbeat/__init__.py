"""Background heartbeat + worker-progress watchdog.

The heartbeat thread emits a periodic INFO log with the latency + counter
snapshot so ops dashboards have a baseline pulse. The watchdog fires an
ERROR alert when ``record_consumer_iteration()`` hasn't been called within
the silence threshold — useful for any worker loop (Service Bus consumer,
Kafka consumer, polling job).
"""

from __future__ import annotations

import logging
import os
import threading
import time
from collections.abc import Callable
from typing import Any

from vibey_bootstrap.counters import counter_snapshot
from vibey_bootstrap.tracing.latency import latency_snapshot

_state_lock = threading.Lock()
_last_message_settled_at: float = 0.0
_last_consumer_iteration_at: float = 0.0
_last_watchdog_alert_at: float = 0.0

_logger = logging.getLogger(__name__)


def _env_float(name: str, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None or raw == "":
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def record_message_settled() -> None:
    """Stamp the last-settled time. Best-effort, never raises."""
    global _last_message_settled_at
    try:
        with _state_lock:
            _last_message_settled_at = time.monotonic()
    except Exception:
        pass


def record_consumer_iteration() -> None:
    """Stamp the last-iteration time. Best-effort, never raises."""
    global _last_consumer_iteration_at
    try:
        with _state_lock:
            _last_consumer_iteration_at = time.monotonic()
        if _logger.isEnabledFor(logging.DEBUG):
            _logger.debug("consumer_iteration recorded")
    except Exception:
        pass


def _last_settle_age_seconds() -> float | None:
    with _state_lock:
        if _last_message_settled_at == 0.0:
            return None
        return time.monotonic() - _last_message_settled_at


def _last_iteration_age_seconds() -> float | None:
    with _state_lock:
        if _last_consumer_iteration_at == 0.0:
            return None
        return time.monotonic() - _last_consumer_iteration_at


def _default_snapshot() -> dict[str, Any]:
    return {
        "latency_snapshot": latency_snapshot(),
        "counters": counter_snapshot(),
    }


def metrics_snapshot() -> dict[str, Any]:
    """For /api/metrics endpoints."""
    return {
        "last_sb_settle_age_seconds": _last_settle_age_seconds(),
        "last_consumer_iteration_age_seconds": _last_iteration_age_seconds(),
    }


def _make_inert_thread(name: str) -> threading.Thread:
    """Return a thread that has finished. Useful when an interval is disabled."""
    t = threading.Thread(target=lambda: None, name=name, daemon=True)
    t.start()
    t.join()
    return t


def start_heartbeat(
    stop_event: threading.Event,
    *,
    interval_seconds: float | None = None,
    snapshot_fn: Callable[[], dict[str, Any]] | None = None,
) -> threading.Thread:
    """Spawn a daemon thread emitting periodic heartbeat logs.

    Returns the thread (or an already-finished placeholder when disabled).
    """
    if interval_seconds is None:
        interval_seconds = _env_float("HEARTBEAT_INTERVAL_SECONDS", 300.0)
    if interval_seconds <= 0:
        return _make_inert_thread("vibey-bootstrap-heartbeat-disabled")

    started = time.monotonic()
    snap_fn = snapshot_fn or _default_snapshot

    def _loop() -> None:
        while not stop_event.wait(interval_seconds):
            try:
                snap = snap_fn()
                latency = snap.get("latency_snapshot", {}) or {}
                counters = snap.get("counters", {}) or {}
                top_slow = sorted(
                    latency.items(),
                    key=lambda kv: kv[1].get("p95", 0.0),
                    reverse=True,
                )[:5]
                top_errors = sorted(
                    latency.items(),
                    key=lambda kv: kv[1].get("errors", 0),
                    reverse=True,
                )[:5]
                _logger.info(
                    "Pipeline heartbeat",
                    extra={
                        "operation": "heartbeat_tick",
                        "uptime_seconds": int(time.monotonic() - started),
                        "operation_count": len(latency),
                        "top_slow_p95": {k: v.get("p95", 0.0) for k, v in top_slow},
                        "top_error_ops": {k: v.get("errors", 0) for k, v in top_errors},
                        "alert_counters": counters,
                        "last_sb_settle_age_seconds": _last_settle_age_seconds(),
                    },
                )
            except Exception as exc:  # noqa: BLE001
                _logger.exception("heartbeat tick failed")
                try:
                    from vibey_bootstrap.alerts import AlertSeverity, alert_dev_team

                    alert_dev_team(
                        AlertSeverity.WARN,
                        subject=f"Heartbeat tick failed: {type(exc).__name__}",
                        context={"error": str(exc)[:500]},
                        dedup_key=f"heartbeat_tick:{type(exc).__name__}",
                    )
                except Exception:
                    pass

    t = threading.Thread(target=_loop, name="vibey-bootstrap-heartbeat", daemon=True)
    t.start()
    return t


def start_consumer_watchdog(
    stop_event: threading.Event,
    *,
    interval_seconds: float | None = None,
    silence_threshold_seconds: float | None = None,
    resilence_window_seconds: float | None = None,
) -> threading.Thread:
    """Spawn a daemon thread that alerts when consumer iteration stalls.

    The default ``resilence_window`` (1 hour) is intentionally longer than
    the alerts dispatcher's 10-min dedup so sustained incidents page hourly,
    not every 10 minutes.
    """
    if interval_seconds is None:
        interval_seconds = _env_float("WATCHDOG_INTERVAL_SECONDS", 60.0)
    if silence_threshold_seconds is None:
        silence_threshold_seconds = _env_float("WATCHDOG_SB_SILENCE_SECONDS", 1800.0)
    if resilence_window_seconds is None:
        resilence_window_seconds = _env_float("WATCHDOG_RESILENCE_SECONDS", 3600.0)
    if interval_seconds <= 0:
        return _make_inert_thread("vibey-bootstrap-watchdog-disabled")

    def _loop() -> None:
        global _last_watchdog_alert_at
        while not stop_event.wait(interval_seconds):
            try:
                age = _last_iteration_age_seconds()
                if age is None or age <= silence_threshold_seconds:
                    continue
                now = time.monotonic()
                with _state_lock:
                    last_alert = _last_watchdog_alert_at
                if last_alert != 0.0 and (now - last_alert) < resilence_window_seconds:
                    continue
                _logger.warning(
                    "SB consumer loop has not progressed",
                    extra={
                        "operation": "watchdog_tick",
                        "silence_seconds": int(age),
                        "threshold_seconds": silence_threshold_seconds,
                    },
                )
                try:
                    from vibey_bootstrap.alerts import AlertSeverity, alert_dev_team

                    alert_dev_team(
                        AlertSeverity.ERROR,
                        subject="SB consumer silent — consumer loop is not progressing",
                        context={
                            "silence_seconds": int(age),
                            "threshold_seconds": silence_threshold_seconds,
                            "last_sb_settle_age_seconds": _last_settle_age_seconds(),
                        },
                        dedup_key="watchdog:consumer_silent",
                    )
                except Exception:
                    pass
                with _state_lock:
                    _last_watchdog_alert_at = now
            except Exception:
                _logger.exception("watchdog tick failed")

    t = threading.Thread(target=_loop, name="vibey-bootstrap-watchdog", daemon=True)
    t.start()
    return t


def start_background_monitors(stop_event: threading.Event) -> list[threading.Thread]:
    """Spawn both heartbeat + watchdog with env defaults."""
    threads: list[threading.Thread] = []
    if _env_float("HEARTBEAT_INTERVAL_SECONDS", 300.0) > 0:
        threads.append(start_heartbeat(stop_event))
    if _env_float("WATCHDOG_INTERVAL_SECONDS", 60.0) > 0:
        threads.append(start_consumer_watchdog(stop_event))
    return threads


def reset_state() -> None:
    """Test-only. Refuses unless AZURE_BOOTSTRAP_ALLOW_RESET=1."""
    if os.environ.get("AZURE_BOOTSTRAP_ALLOW_RESET") != "1":
        raise RuntimeError("reset_state is test-only — set AZURE_BOOTSTRAP_ALLOW_RESET=1")
    global _last_message_settled_at, _last_consumer_iteration_at, _last_watchdog_alert_at
    with _state_lock:
        _last_message_settled_at = 0.0
        _last_consumer_iteration_at = 0.0
        _last_watchdog_alert_at = 0.0


__all__ = [
    "metrics_snapshot",
    "record_consumer_iteration",
    "record_message_settled",
    "reset_state",
    "start_background_monitors",
    "start_consumer_watchdog",
    "start_heartbeat",
]
