"""Best-effort process-local counters.

Used by the alerts dispatcher, tracing decorator, OpenAI tracker, etc. to
record observability events without taking a hard dependency on any metrics
backend. The values are surfaced via ``counter_snapshot()`` and the metrics
endpoint in ``vibey_bootstrap.metrics``.
"""

from __future__ import annotations

import os
import threading

_lock = threading.Lock()
_counters: dict[str, int] = {}


def bump_counter(name: str, n: int = 1) -> None:
    """Thread-safe increment. Never raises."""
    if not isinstance(name, str) or not name:
        return
    try:
        with _lock:
            _counters[name] = _counters.get(name, 0) + int(n)
    except Exception:
        pass


def counter_snapshot() -> dict[str, int]:
    """Return a copy of the counter map."""
    with _lock:
        return dict(_counters)


def _reset_counters() -> None:
    """Test-only. Refuses unless AZURE_BOOTSTRAP_ALLOW_RESET=1."""
    if os.environ.get("AZURE_BOOTSTRAP_ALLOW_RESET") != "1":
        raise RuntimeError("_reset_counters is test-only — set AZURE_BOOTSTRAP_ALLOW_RESET=1")
    with _lock:
        _counters.clear()


__all__ = ["bump_counter", "counter_snapshot"]
