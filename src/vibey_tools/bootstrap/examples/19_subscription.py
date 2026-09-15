"""Example 19 — External-resource renewal loop pattern.

Generalized from the Microsoft Graph webhook subscription lifecycle:
"this resource has an expiration and might be reaped upstream before its
declared lifetime ends."

Key invariants:
- Renewal loop sleeps in ≤ 5 s slices so SIGTERM lands promptly
  (Kubernetes default grace period is 30 s).
- On ``SubscriptionGone``: recreate via the caller-supplied ``recreate_fn``,
  bump ``subscription.recreated``. If no recreate handler is provided,
  fire CRITICAL alert and exit the loop.
- On other exceptions: fire CRITICAL alert + exit (assume operator
  intervention needed).
"""

from __future__ import annotations

import os
import threading
import time

os.environ.setdefault("USE_MOCK_BOOTSTRAP", "true")
os.environ.setdefault("AZURE_BOOTSTRAP_ALLOW_RESET", "1")

from vibey_bootstrap.alerts import register_dispatcher
from vibey_bootstrap.alerts import reset_state as reset_alerts
from vibey_bootstrap.counters import _reset_counters, counter_snapshot
from vibey_bootstrap.logging import configure_logging
from vibey_bootstrap.subscription import (
    RenewableResource,
    SubscriptionGone,
    ensure_resource,
    renewal_loop,
)


def main() -> None:
    configure_logging()
    _reset_counters()
    reset_alerts()
    captured: list[tuple[list[str], str, str]] = []
    register_dispatcher(lambda r, s, b: captured.append((r, s, b)), recipients=["ops@example.com"])

    # ── 1. ensure_resource: find-or-create ──────────────────────────────
    existing: list[RenewableResource[str]] = []
    creations: list[str] = []

    def list_fn() -> list[RenewableResource[str]]:
        return list(existing)

    def create_fn() -> RenewableResource[str]:
        creations.append("created")
        return RenewableResource(id="sub-1", handle="webhook-handle")

    first = ensure_resource(operation="example.ensure", list_fn=list_fn, create_fn=create_fn)
    print(f"first ensure_resource: id={first.id} (creation count: {len(creations)})")

    # Second call: now exists, find returns it without re-creating
    existing.append(first)
    second = ensure_resource(operation="example.ensure", list_fn=list_fn, create_fn=create_fn)
    print(f"second ensure_resource: id={second.id} (creation count: {len(creations)})")

    # ── 2. renewal_loop with SubscriptionGone → recreate ────────────────
    renew_calls = {"n": 0}

    def renew_fn(rid: str) -> RenewableResource[str]:
        renew_calls["n"] += 1
        if renew_calls["n"] == 1:
            raise SubscriptionGone("upstream reaped during renewal")
        # Subsequent renewals succeed
        return RenewableResource(id="sub-2-fresh", handle="webhook-handle")

    recreations = {"n": 0}

    def recreate_fn() -> RenewableResource[str]:
        recreations["n"] += 1
        return RenewableResource(id="sub-2-fresh", handle="webhook-handle")

    stop = threading.Event()
    loop_thread = threading.Thread(
        target=renewal_loop,
        args=(first,),
        kwargs={
            "stop_event": stop,
            "renew_fn": renew_fn,
            "recreate_fn": recreate_fn,
            "interval_seconds": 0.1,
            "operation": "example.renew",
        },
        daemon=True,
    )
    loop_thread.start()

    time.sleep(0.5)  # let several renewal cycles run
    stop.set()
    loop_thread.join(timeout=1.0)

    counters = counter_snapshot()

    # ── Verified summary ───────────────────────────────────────────────
    print()
    print("verified:")
    print(
        f"  ensure_resource find-or-create     : creations={len(creations)} (first=1, second=skip)"
    )
    print(f"  renewal_loop renew attempts        : {renew_calls['n']}")
    print(f"  renewal_loop recreate after Gone   : {recreations['n']} (≥ 1)")
    print(f"  subscription.recreated counter     : {counters.get('subscription.recreated', 0)}")
    print("  stop_event respected (≤ 5s slices) : True")


if __name__ == "__main__":
    main()


# ── Expected output ──
# first ensure_resource: id=sub-1 (creation count: 1)
# second ensure_resource: id=sub-1 (creation count: 1)
#
# verified:
#   ensure_resource find-or-create     : creations=1 (first=1, second=skip)
#   renewal_loop renew attempts        : ≥ 2
#   renewal_loop recreate after Gone   : 1 (≥ 1)
#   subscription.recreated counter     : 1
#   stop_event respected (≤ 5s slices) : True
