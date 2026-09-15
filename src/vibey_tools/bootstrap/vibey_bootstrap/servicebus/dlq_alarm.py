# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Dead-letter queue growth-rate alarm.

Samples DLQ depth on each call; compares to the previous sample within the
window. When the delta exceeds the threshold, fires a CRITICAL alert.
"""

from __future__ import annotations

import logging
import os
import threading
import time
from typing import Any, Protocol

_logger = logging.getLogger(__name__)


class SbRepoProtocol(Protocol):
    def peek_dead_letter_messages(self, max_count: int) -> list[dict[str, Any]]: ...


_lock = threading.Lock()
_last_sample_ts: float | None = None
_last_sample_count: int | None = None


def reset_state() -> None:
    """Test-only. Refuses unless AZURE_BOOTSTRAP_ALLOW_RESET=1."""
    if os.environ.get("AZURE_BOOTSTRAP_ALLOW_RESET") != "1":
        raise RuntimeError("reset_state is test-only — set AZURE_BOOTSTRAP_ALLOW_RESET=1")
    global _last_sample_ts, _last_sample_count
    with _lock:
        _last_sample_ts = None
        _last_sample_count = None


def check_dlq_growth_rate(
    service_bus_repo: SbRepoProtocol,
    *,
    alert_threshold: int = 5,
    sample_window_minutes: int = 60,
) -> dict[str, int]:
    """Peek the DLQ, compare to the previous sample, alert on excessive growth.

    Returns ``{'current': N, 'delta': N, 'alerted': 0 or 1}``.
    """
    global _last_sample_ts, _last_sample_count
    try:
        messages = service_bus_repo.peek_dead_letter_messages(max_count=500)
        current = len(messages)
    except Exception:
        _logger.exception("dlq_alarm: peek failed")
        return {"current": 0, "delta": 0, "alerted": 0}

    now = time.monotonic()
    window_seconds = sample_window_minutes * 60
    delta = 0
    with _lock:
        if _last_sample_ts is not None and (now - _last_sample_ts) <= window_seconds:
            delta = current - (_last_sample_count or 0)
        _last_sample_ts = now
        _last_sample_count = current

    alerted = 0
    if delta > alert_threshold:
        try:
            from vibey_bootstrap.alerts import AlertSeverity, alert_dev_team

            alert_dev_team(
                AlertSeverity.CRITICAL,
                subject=(
                    f"DLQ growth rate exceeded threshold (+{delta} in {sample_window_minutes}m)"
                ),
                context={
                    "current_depth": current,
                    "delta": delta,
                    "window_minutes": sample_window_minutes,
                    "threshold": alert_threshold,
                },
                dedup_key="dlq_alarm.growth_rate_exceeded",
            )
            alerted = 1
        except Exception:
            pass
    return {"current": current, "delta": delta, "alerted": alerted}
