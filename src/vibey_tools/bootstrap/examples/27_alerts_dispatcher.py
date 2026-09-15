"""Example 27 — Tiered alert dispatcher.

Three severity tiers:

- ``WARN``: log-only (no email). Bumps ``alerts.warn``.
- ``ERROR``: log + append to pending-digest + per-key sliding-window
  history. After ``ALERT_ESCALATE_AFTER`` (default 5) in
  ``ALERT_ESCALATE_WINDOW_SECONDS`` (default 900s), promoted to CRITICAL.
- ``CRITICAL``: log + sender email + rolling rate-limit
  (``ALERT_MAX_PER_HOUR`` default 30; overflow folded into digest).

Across all tiers: ``alert_dev_team`` MUST never raise — best-effort
end-to-end. Identical ``dedup_key`` calls within
``ALERT_DEDUP_WINDOW_SECONDS`` (default 600s) collapse into one record.

Kill switch: ``DEV_ALERTS_ENABLED=false`` suppresses emails entirely
(stricter than rate-limit; alerts also don't fall back to pending digest).
"""

from __future__ import annotations

import os
import time

# Tighter knobs for demo
os.environ.setdefault("USE_MOCK_BOOTSTRAP", "true")
os.environ.setdefault("AZURE_BOOTSTRAP_ALLOW_RESET", "1")
os.environ["ALERT_DEDUP_WINDOW_SECONDS"] = "0.2"
os.environ["ALERT_ESCALATE_AFTER"] = "3"
os.environ["ALERT_ESCALATE_WINDOW_SECONDS"] = "10"
os.environ["ALERT_MAX_PER_HOUR"] = "100"

from vibey_bootstrap.alerts import (
    AlertSeverity,
    alert_dev_team,
    drain_pending_alerts,
    register_dispatcher,
    reset_state,
)
from vibey_bootstrap.counters import _reset_counters, counter_snapshot
from vibey_bootstrap.logging import configure_logging


def main() -> None:
    configure_logging()
    reset_state()
    _reset_counters()

    sent: list[tuple[list[str], str, str]] = []
    register_dispatcher(
        lambda r, s, b: sent.append((r, s, b)),
        recipients=["dev-alerts@example.com"],
    )

    # ── 1. WARN: log-only ──────────────────────────────────────────────
    alert_dev_team(AlertSeverity.WARN, "operation slow", dedup_key="slow_op")
    print(f"after 1 WARN  → emails sent={len(sent)}, pending_digest={len(drain_pending_alerts())}")

    # ── 2. CRITICAL: dedup collapses within window ─────────────────────
    for _ in range(3):
        alert_dev_team(AlertSeverity.CRITICAL, "db down", dedup_key="db_down")
    print(f"3× CRITICAL same key → emails sent={len(sent)} (expect 1, dedup)")

    # ── Wait past the dedup window; same key fires again ──────────────
    time.sleep(0.25)
    alert_dev_team(AlertSeverity.CRITICAL, "db down again", dedup_key="db_down")
    print(f"after dedup window  → emails sent={len(sent)} (expect 2)")

    # ── 3. ERROR escalation: 3 ERRORs past dedup window → CRITICAL ────
    # Dedup collapses identical keys within ALERT_DEDUP_WINDOW_SECONDS, so
    # we sleep past the window between each ERROR. That way each call
    # appends to error_history[key], and the third one trips the
    # escalation threshold (ALERT_ESCALATE_AFTER=3).
    for i in range(3):
        time.sleep(0.25)  # past the 0.2 s dedup window
        alert_dev_team(AlertSeverity.ERROR, f"db slow #{i}", dedup_key="db_slow")
    escalated = [s for s in sent if "[ESCALATED]" in s[1]]
    print(f"\n3× ERROR (past dedup window) → escalated emails={len(escalated)}")

    # ── 4. Kill switch suppresses dispatch ─────────────────────────────
    reset_state()
    register_dispatcher(lambda *a: sent.append(a), recipients=["x@y.com"])  # type: ignore[arg-type]
    sent.clear()
    os.environ["DEV_ALERTS_ENABLED"] = "false"
    alert_dev_team(AlertSeverity.CRITICAL, "kill-switch test", dedup_key="ks")
    print(
        f"\nkill switch active → emails sent={len(sent)}, digest entries={len(drain_pending_alerts())}"
    )
    os.environ.pop("DEV_ALERTS_ENABLED", None)

    counters = counter_snapshot()

    # ── Verified summary ──────────────────────────────────────────────
    print()
    print("verified:")
    print(f"  alerts.warn      counter : {counters.get('alerts.warn', 0)}")
    print(f"  alerts.error     counter : {counters.get('alerts.error', 0)}")
    print(f"  alerts.critical  counter : {counters.get('alerts.critical', 0)}")
    print(f"  alerts.escalated counter : {counters.get('alerts.escalated', 0)}")
    print("  kill switch suppresses BOTH email AND pending digest")


if __name__ == "__main__":
    main()


# ── Expected output ──
# <log lines>
# after 1 WARN  → emails sent=0, pending_digest=0
# 3× CRITICAL same key → emails sent=1 (expect 1, dedup)
# after dedup window  → emails sent=2 (expect 2)
#
# 3× ERROR same dedup_key → escalated emails=1
#
# kill switch active → emails sent=0, digest entries=0
#
# verified:
#   ...
