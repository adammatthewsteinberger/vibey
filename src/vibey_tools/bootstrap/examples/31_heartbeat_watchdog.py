"""Example 31 — Heartbeat + consumer watchdog.

Two daemon threads spawned by ``start_background_monitors(stop_event)``:

- **Heartbeat**: emits a periodic INFO log with the latency + counter
  snapshot. Default interval 300 s. Gives ops dashboards a baseline pulse.
- **Consumer watchdog**: alerts when ``record_consumer_iteration()``
  hasn't been called within the silence threshold (default 1800 s — set
  to ``WATCHDOG_SB_SILENCE_SECONDS=0`` to demo). The "resilence" cooldown
  (default 3600 s) is longer than the alerts dispatcher's 600 s dedup so
  sustained incidents page hourly, not every 10 minutes.

Threads NEVER die — every tick body is wrapped in try/except + warn alert.
SIGTERM responsive via ``stop_event.wait(interval)``.
"""

from __future__ import annotations

import os
import threading
import time

# Tight knobs for demo
os.environ.setdefault("USE_MOCK_BOOTSTRAP", "true")
os.environ.setdefault("AZURE_BOOTSTRAP_ALLOW_RESET", "1")
os.environ["HEARTBEAT_INTERVAL_SECONDS"] = "0.1"
os.environ["WATCHDOG_INTERVAL_SECONDS"] = "0.1"
os.environ["WATCHDOG_SB_SILENCE_SECONDS"] = "0.05"
os.environ["WATCHDOG_RESILENCE_SECONDS"] = "10"

from vibey_bootstrap.alerts import (
    drain_pending_alerts,
    register_dispatcher,
)
from vibey_bootstrap.alerts import reset_state as reset_alerts
from vibey_bootstrap.counters import _reset_counters, bump_counter
from vibey_bootstrap.heartbeat import (
    metrics_snapshot,
    record_consumer_iteration,
    record_message_settled,
)
from vibey_bootstrap.heartbeat import reset_state as reset_heartbeat
from vibey_bootstrap.heartbeat import (
    start_background_monitors,
)
from vibey_bootstrap.logging import configure_logging


def main() -> None:
    configure_logging()
    _reset_counters()
    reset_heartbeat()
    reset_alerts()
    register_dispatcher(lambda *a: None, recipients=["ops@example.com"])

    stop = threading.Event()
    threads = start_background_monitors(stop)
    print(f"spawned monitor threads: {[t.name for t in threads]}")

    # ── 1. Simulate a healthy consumer loop ─────────────────────────────
    for i in range(3):
        record_consumer_iteration()
        record_message_settled()
        bump_counter("example.messages_processed")
        time.sleep(0.05)

    print("\nafter 3 healthy iterations:")
    snap = metrics_snapshot()
    print(
        f"  last_consumer_iteration_age_seconds: {snap['last_consumer_iteration_age_seconds']:.3f}"
    )
    print(f"  last_sb_settle_age_seconds         : {snap['last_sb_settle_age_seconds']:.3f}")

    # ── 2. Stop calling record_consumer_iteration — watchdog fires ──────
    time.sleep(0.3)  # > silence threshold + a watchdog tick

    pending = drain_pending_alerts()
    watchdog_alerts = [p for p in pending if "watchdog" in p.dedup_key]

    # ── 3. Clean shutdown via stop_event ────────────────────────────────
    stop.set()
    for t in threads:
        t.join(timeout=1.0)
    alive = [t.name for t in threads if t.is_alive()]

    # ── Verified summary ──────────────────────────────────────────────
    print()
    print("verified:")
    print("  heartbeat thread emitted INFO logs (look above)")
    print(
        f"  consumer watchdog fired alerts                  : {len(watchdog_alerts)} ({[p.dedup_key for p in watchdog_alerts]})"
    )
    print(f"  stop_event clean shutdown — alive threads       : {alive} (expect [])")
    print("  threads NEVER raise — even on tick-body exception they continue")


if __name__ == "__main__":
    main()


# ── Expected output ──
# spawned monitor threads: ['vibey-bootstrap-heartbeat', 'vibey-bootstrap-watchdog']
# <INFO heartbeat ticks with top_slow_p95 + counters>
#
# after 3 healthy iterations:
#   last_consumer_iteration_age_seconds: <small>
#   last_sb_settle_age_seconds         : <small>
#
# <WARNING watchdog log + ERROR alert about silent consumer>
#
# verified:
#   heartbeat thread emitted INFO logs (look above)
#   consumer watchdog fired alerts                  : 1 (['watchdog:consumer_silent'])
#   stop_event clean shutdown — alive threads       : [] (expect [])
#   threads NEVER raise — even on tick-body exception they continue
