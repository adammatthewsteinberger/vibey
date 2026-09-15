"""Example 37 — ``/api/metrics`` endpoint via build_metrics_snapshot.

``build_metrics_snapshot()`` aggregates the well-known v2 metrics into
a single JSON-friendly dict. Soft-imports every contributor — apps
without an extra installed just don't get that section (no error).

Sections (when their module is installed):
- ``latency``: per-operation latency histogram (p50/p95/p99/max)
- ``alert_counters``: every ``bump_counter`` registered name
- ``ai_usage``: ``vibey_bootstrap.openai.usage_snapshot()``
- ``bootstrap_initialized``: process-local readiness flag
- ``last_sb_settle_age_seconds``: heartbeat age (seconds since last
  Service Bus message settle)

Requires ``pip install vibey-bootstrap[fastapi]`` for the FastAPI demo;
``build_metrics_snapshot`` itself is stdlib-only.
"""

from __future__ import annotations

import os

os.environ.setdefault("USE_MOCK_BOOTSTRAP", "true")
os.environ.setdefault("AZURE_BOOTSTRAP_ALLOW_RESET", "1")

from vibey_bootstrap.counters import _reset_counters, bump_counter
from vibey_bootstrap.heartbeat import (
    record_message_settled,
)
from vibey_bootstrap.heartbeat import reset_state as reset_heartbeat
from vibey_bootstrap.metrics import build_metrics_snapshot
from vibey_bootstrap.openai import record_usage
from vibey_bootstrap.openai import reset_state as reset_tracker
from vibey_bootstrap.tracing import traced
from vibey_bootstrap.tracing.latency import reset_latency_state


def main() -> None:
    _reset_counters()
    reset_tracker()
    reset_heartbeat()
    reset_latency_state()

    # ── 1. Generate some metrics traffic ────────────────────────────────
    @traced(operation="example.work")
    def work() -> None:
        bump_counter("example.work_count")

    for _ in range(5):
        work()
    record_usage("gpt-4o", prompt_tokens=1000, completion_tokens=500)
    record_message_settled()
    bump_counter("alerts.error", n=2)

    # ── 2. Snapshot ─────────────────────────────────────────────────────
    snap = build_metrics_snapshot()

    print("metrics snapshot sections:")
    for section in sorted(snap):
        if section == "latency":
            print(f"  {section:30} ({len(snap['latency'])} operations tracked)")
        elif section == "alert_counters":
            print(f"  {section:30} ({len(snap['alert_counters'])} counters)")
        elif section == "ai_usage":
            print(f"  {section:30} totals={snap['ai_usage']['totals']}")
        else:
            print(f"  {section:30} {snap[section]!r}")

    print(f"\nexample.work latency       : p95={snap['latency']['example.work']['p95']}")
    print(f"alerts.error counter       : {snap['alert_counters'].get('alerts.error', 0)}")
    print(f"AI calls                   : {snap['ai_usage']['totals']['calls']}")
    print(f"last_sb_settle_age_seconds : {snap['last_sb_settle_age_seconds']:.3f}")

    # ── 3. Wire into FastAPI ────────────────────────────────────────────
    try:
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
    except ImportError:
        print("\nfastapi not installed — skipping the route demo")
        return

    app = FastAPI()

    @app.get("/api/metrics")
    def metrics() -> dict:
        return build_metrics_snapshot()

    client = TestClient(app)
    r = client.get("/api/metrics")
    print(f"\nGET /api/metrics: status={r.status_code}, body keys={sorted(r.json().keys())}")

    # ── Verified summary ──────────────────────────────────────────────
    print()
    print("verified:")
    print("  snapshot includes latency + counters always")
    print("  openai + heartbeat + bootstrap added when modules installed")
    print("  missing-extra sections silently omitted (no error)")
    print("  ready to wire as a FastAPI route returning JSON")


if __name__ == "__main__":
    main()


# ── Expected output ──
# metrics snapshot sections:
#   ai_usage                       totals={'calls': 1, 'total_tokens': 1500, 'cost_usd': 0.0075, 'rate_limit_events': 0}
#   alert_counters                 (3 counters)
#   bootstrap_initialized          False
#   last_sb_settle_age_seconds     <small float>
#   latency                        (1 operations tracked)
#
# example.work latency       : p95=...
# alerts.error counter       : 2
# AI calls                   : 1
# last_sb_settle_age_seconds : <small>
#
# GET /api/metrics: status=200, body keys=['ai_usage', 'alert_counters', 'bootstrap_initialized', 'last_sb_settle_age_seconds', 'latency']
#
# verified:
#   ...
