# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Sliding-window per-sender notification throttle.

Defends against reflection amplification: an attacker forging ``From:``
addresses to bounce unbounded notifications off the pipeline. Dev-team
alerts are NEVER routed through this throttle — they're separate.

Process-local; pod restarts allow a brief burst. That's the right trade —
sender notification is best-effort, not a delivery cap.
"""

from __future__ import annotations

import os
import threading
import time
from collections import deque

from vibey_bootstrap.counters import bump_counter

NOTIFY_SENDER_MAX_PER_HOUR_DEFAULT = 3
NOTIFY_SENDER_WINDOW_SECONDS_DEFAULT = 3600

_throttle_state: dict[str, deque[float]] = {}
_throttle_lock = threading.Lock()


def should_notify_sender(
    sender_email: str,
    *,
    max_per_hour: int = NOTIFY_SENDER_MAX_PER_HOUR_DEFAULT,
    window_seconds: float = NOTIFY_SENDER_WINDOW_SECONDS_DEFAULT,
    counter_namespace: str = "sender",
) -> bool:
    """Return True when the sender is allowed another notification."""
    key = (sender_email or "").strip().lower()
    if not key:
        bump_counter(f"{counter_namespace}.notification.throttled")
        return False
    now = time.monotonic()
    cutoff = now - window_seconds
    with _throttle_lock:
        bucket = _throttle_state.setdefault(key, deque())
        while bucket and bucket[0] < cutoff:
            bucket.popleft()
        if len(bucket) >= max_per_hour:
            bump_counter(f"{counter_namespace}.notification.throttled")
            return False
        bucket.append(now)
    bump_counter(f"{counter_namespace}.notified")
    return True


def reset_sender_notification_throttle() -> None:
    """Test-only. Refuses unless AZURE_BOOTSTRAP_ALLOW_RESET=1."""
    if os.environ.get("AZURE_BOOTSTRAP_ALLOW_RESET") != "1":
        raise RuntimeError(
            "reset_sender_notification_throttle is test-only — set AZURE_BOOTSTRAP_ALLOW_RESET=1"
        )
    with _throttle_lock:
        _throttle_state.clear()


__all__ = [
    "NOTIFY_SENDER_MAX_PER_HOUR_DEFAULT",
    "NOTIFY_SENDER_WINDOW_SECONDS_DEFAULT",
    "reset_sender_notification_throttle",
    "should_notify_sender",
]
