"""Example 06 — Best-effort counters.

``bump_counter`` is the canonical observability primitive: thread-safe,
never raises, no external dependencies. The library uses it internally to
track alerts, retries, ingress rejections, etc. Apps use the same API for
their own metrics.

Naming convention: ``{namespace}.{event}.{outcome}`` — dotted, lowercase.
Examples:
- ``alerts.{warn,error,critical}``
- ``attachment.rejected.{unsupported_type,mime,size_cap,magic_byte}``
- ``ai.tokens.total``, ``ai.cost_usd_micros``, ``ai.calls``
"""

from __future__ import annotations

import os
import threading

os.environ.setdefault("USE_MOCK_BOOTSTRAP", "true")
os.environ.setdefault("AZURE_BOOTSTRAP_ALLOW_RESET", "1")

from vibey_bootstrap.counters import (
    _reset_counters,
    bump_counter,
    counter_snapshot,
)


def main() -> None:
    _reset_counters()

    # ── 1. Simple sequential counts ────────────────────────────────────
    for _ in range(5):
        bump_counter("example.requests.received")
    bump_counter("example.requests.completed", n=3)
    bump_counter("example.requests.failed", n=2)

    # ── 2. Thread-safe under contention ────────────────────────────────
    def worker() -> None:
        for _ in range(100):
            bump_counter("example.concurrent.shared")

    threads = [threading.Thread(target=worker) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    # ── 3. Never raises on bad input ───────────────────────────────────
    bump_counter("")  # type: ignore[arg-type]   silently no-op
    bump_counter(None)  # type: ignore[arg-type] silently no-op

    snap = counter_snapshot()

    # ── Verified summary ───────────────────────────────────────────────
    print()
    print("verified:")
    print(f"  sequential received           : {snap['example.requests.received']}")
    print(f"  sequential completed (n=3)    : {snap['example.requests.completed']}")
    print(f"  10 threads × 100 increments   : {snap['example.concurrent.shared']} (expect 1000)")
    print(f"  empty / None key ignored      : {'(none)' not in snap}")
    print(f"  total counter names tracked   : {len(snap)}")


if __name__ == "__main__":
    main()


# ── Expected output ──
# verified:
#   sequential received           : 5
#   sequential completed (n=3)    : 3
#   10 threads × 100 increments   : 1000 (expect 1000)
#   empty / None key ignored      : True
#   total counter names tracked   : 4
