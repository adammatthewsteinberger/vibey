"""Aggregate library metrics for /api/metrics endpoints.

Soft-imports every contributor so apps without certain extras still get a
useful response — missing modules just don't add their section.
"""

from __future__ import annotations

from typing import Any

from vibey_bootstrap.counters import counter_snapshot
from vibey_bootstrap.tracing.latency import latency_snapshot


def build_metrics_snapshot() -> dict[str, Any]:
    """Aggregate known metrics into a single dict."""
    snap: dict[str, Any] = {
        "latency": latency_snapshot(),
        "alert_counters": counter_snapshot(),
    }
    try:
        from vibey_bootstrap.openai import usage_snapshot

        snap["ai_usage"] = usage_snapshot()
    except Exception:
        pass
    try:
        from vibey_bootstrap.bootstrap import bootstrap_initialized

        snap["bootstrap_initialized"] = bootstrap_initialized()
    except Exception:
        pass
    try:
        from vibey_bootstrap.heartbeat import _last_settle_age_seconds

        snap["last_sb_settle_age_seconds"] = _last_settle_age_seconds()
    except Exception:
        pass
    return snap


__all__ = ["build_metrics_snapshot"]
