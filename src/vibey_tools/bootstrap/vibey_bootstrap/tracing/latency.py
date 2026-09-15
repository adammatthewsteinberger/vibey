"""Per-operation latency histograms.

Simple sorted-sample histograms with a 1024-sample cap per operation.
``bisect.insort`` keeps each list sorted on insertion; downsampling via
``samples[::2]`` preserves the distribution shape without paying the cost of
a full re-sort.
"""

from __future__ import annotations

import bisect
import os
import threading
import time
from dataclasses import dataclass
from typing import Any


@dataclass
class _LatencySamples:
    __slots__ = ("samples", "count", "errors", "slow", "last_seen")
    samples: list[float]
    count: int
    errors: int
    slow: int
    last_seen: float

    def __init__(self) -> None:
        self.samples = []
        self.count = 0
        self.errors = 0
        self.slow = 0
        self.last_seen = 0.0


_HIST_LOCK = threading.Lock()
_HIST: dict[str, _LatencySamples] = {}
_HIST_CAP = 1024


def _record_latency(operation: str, seconds: float, *, error: bool, slow: bool) -> None:
    if not isinstance(operation, str) or not operation:
        return
    try:
        with _HIST_LOCK:
            entry = _HIST.get(operation)
            if entry is None:
                entry = _LatencySamples()
                _HIST[operation] = entry
            entry.count += 1
            if error:
                entry.errors += 1
            if slow:
                entry.slow += 1
            entry.last_seen = time.time()
            bisect.insort(entry.samples, float(seconds))
            if len(entry.samples) > _HIST_CAP:
                entry.samples = entry.samples[::2]
    except Exception:
        pass


def _percentile(sorted_samples: list[float], p: float) -> float:
    n = len(sorted_samples)
    if n == 0:
        return 0.0
    idx = min(n - 1, max(0, int(p * n) - 1))
    return sorted_samples[idx]


def latency_snapshot() -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    with _HIST_LOCK:
        for op, entry in _HIST.items():
            samples = entry.samples
            if not samples:
                continue
            out[op] = {
                "count": entry.count,
                "errors": entry.errors,
                "slow": entry.slow,
                "p50": round(_percentile(samples, 0.50), 4),
                "p95": round(_percentile(samples, 0.95), 4),
                "p99": round(_percentile(samples, 0.99), 4),
                "max": round(samples[-1], 4),
                "last_seen": int(entry.last_seen),
            }
    return out


def reset_latency_state() -> None:
    if os.environ.get("AZURE_BOOTSTRAP_ALLOW_RESET") != "1":
        raise RuntimeError("reset_latency_state is test-only — set AZURE_BOOTSTRAP_ALLOW_RESET=1")
    with _HIST_LOCK:
        _HIST.clear()
