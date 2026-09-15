"""Example 05 — Slow-budget alerts.

Demonstrates how ``@traced`` fires a WARN-severity alert when an operation
exceeds its slow threshold. Thresholds can be:
1. Hardcoded per-call via ``slow_threshold_seconds=`` on the decorator.
2. Looked up from a project-wide registry via ``register_slow_threshold``.
3. Inherited from the library's default Azure-SDK threshold table.

Resolution priority: caller arg > registered override > library default.
"""

from __future__ import annotations

import logging
import os
import time

os.environ.setdefault("USE_MOCK_BOOTSTRAP", "true")
os.environ.setdefault("AZURE_BOOTSTRAP_ALLOW_RESET", "1")

from vibey_bootstrap.alerts import (
    register_dispatcher,
)
from vibey_bootstrap.alerts import reset_state as reset_alerts
from vibey_bootstrap.counters import _reset_counters, counter_snapshot
from vibey_bootstrap.logging import configure_logging
from vibey_bootstrap.tracing import (
    default_slow_threshold,
    latency_snapshot,
    register_slow_threshold,
    reset_latency_state,
    reset_slow_thresholds,
    traced,
)

logger = logging.getLogger(__name__)


# ── Hardcoded per-call threshold ─────────────────────────────────────────
@traced(operation="example.long_op", slow_threshold_seconds=0.01)
def long_op() -> None:
    time.sleep(0.05)  # 5× the budget — will fire WARN


# ── Threshold looked up from registry ────────────────────────────────────
@traced(operation="example.indexed_op")
def indexed_op() -> None:
    time.sleep(0.02)


def main() -> None:
    configure_logging()
    reset_latency_state()
    reset_slow_thresholds()
    reset_alerts()
    _reset_counters()
    register_dispatcher(lambda *a: None, recipients=["ops@example.com"])

    # ── Register a project-wide threshold (overrides library default) ──
    register_slow_threshold("example.indexed_op", 0.001)

    # ── Library default (for documented operations) ────────────────────
    pipeline_default = default_slow_threshold("pipeline.process")

    # ── Trigger both operations ────────────────────────────────────────
    long_op()
    indexed_op()

    snap = latency_snapshot()
    counters = counter_snapshot()

    # ── Verified summary ───────────────────────────────────────────────
    print()
    print("verified:")
    print(f"  long_op slow count           : {snap['example.long_op']['slow']}")
    print(f"  indexed_op slow count        : {snap['example.indexed_op']['slow']}")
    print(f"  registered threshold lookup  : {default_slow_threshold('example.indexed_op')}")
    print(f"  library default pipeline.process: {pipeline_default}s")
    print(f"  alerts.warn counter bumps    : {counters.get('alerts.warn', 0)}")


if __name__ == "__main__":
    main()


# ── Expected output ──
# <log lines, including a WARN about the slow operation>
#
# verified:
#   long_op slow count           : 1
#   indexed_op slow count        : 1
#   registered threshold lookup  : 0.001
#   library default pipeline.process: 180.0s
#   alerts.warn counter bumps    : 2
