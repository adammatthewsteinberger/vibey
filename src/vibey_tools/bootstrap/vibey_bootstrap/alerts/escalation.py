"""Sliding-window error history for the ERROR→CRITICAL escalation ladder."""

from __future__ import annotations

import time
from collections import deque


def should_escalate(
    history: deque[float],
    *,
    threshold: int,
    window_seconds: float,
) -> bool:
    """Return True when the deque holds ``>= threshold`` events inside the
    sliding ``window_seconds``. Prunes stale entries in-place.
    """
    if threshold <= 0:
        return False
    now = time.monotonic()
    cutoff = now - window_seconds
    while history and history[0] < cutoff:
        history.popleft()
    history.append(now)
    return len(history) >= threshold
