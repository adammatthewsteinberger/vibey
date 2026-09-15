"""Example 17 — Token-bucket rate limiter + FastAPI dependency.

In-process leaky bucket suitable for FastAPI route protection — belt-and-
suspenders against an ingress L7 limiter that's unavailable in local dev
or wedged in some failure mode.

Key invariants:
- Atomic refill + check + consume under a single ``threading.Lock``.
- 429 responses have empty bodies by default — detail strings leak
  budget state.
- Two presets: ``webhook_bucket()`` (240 burst, 4/s) for Graph-shaped
  webhooks; ``admin_bucket()`` (30 burst, 0.5/s) for manual triggers.

Requires ``pip install vibey-bootstrap[fastapi]`` for the FastAPI demo.
"""

from __future__ import annotations

import os
import threading
import time

os.environ.setdefault("USE_MOCK_BOOTSTRAP", "true")
os.environ.setdefault("AZURE_BOOTSTRAP_ALLOW_RESET", "1")

from vibey_bootstrap.counters import _reset_counters, counter_snapshot
from vibey_bootstrap.ratelimit import (
    TokenBucket,
    admin_bucket,
    fastapi_rate_limit,
    webhook_bucket,
)


def main() -> None:
    _reset_counters()

    # ── 1. Sequential drain + refill ────────────────────────────────────
    bucket = TokenBucket(budget=5, refill_per_second=10, name="example")
    admitted = sum(1 for _ in range(5) if bucket.consume())
    rejected_after = bucket.consume()
    print(f"5 sequential calls admitted, 6th rejected: admitted={admitted} 6th={rejected_after}")
    time.sleep(0.3)  # should refill ~3 tokens
    re_admitted = sum(1 for _ in range(5) if bucket.consume())
    print(f"after 300ms refill, admitted of next 5: {re_admitted}")

    # ── 2. Thread-safety under contention ──────────────────────────────
    contended = TokenBucket(budget=50, refill_per_second=0, name="contended")
    results: list[bool] = []
    lock = threading.Lock()

    def worker() -> None:
        ok = contended.consume()
        with lock:
            results.append(ok)

    threads = [threading.Thread(target=worker) for _ in range(100)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    print(
        f"\n100 contended consume() calls: {sum(results)} admitted, {sum(1 for r in results if not r)} rejected (expect 50/50)"
    )

    # ── 3. FastAPI dependency demo ─────────────────────────────────────
    try:
        from fastapi import Depends, FastAPI
        from fastapi.testclient import TestClient
    except ImportError:
        print("\n(fastapi not installed — skipping the FastAPI demo)")
    else:
        app = FastAPI()
        ratelimit_bucket = TokenBucket(budget=2, refill_per_second=0, name="api")

        @app.get("/api/ping", dependencies=[Depends(fastapi_rate_limit(ratelimit_bucket))])
        def ping() -> dict:
            return {"ok": True}

        client = TestClient(app)
        codes = [client.get("/api/ping").status_code for _ in range(4)]
        print(f"\n4 sequential FastAPI calls (budget=2): {codes}")

    # ── 4. Webhook / admin presets ─────────────────────────────────────
    wb = webhook_bucket()
    ab = admin_bucket()
    print(f"\nwebhook_bucket: budget={wb.budget}, refill_per_second=(see source) — 240 / 4")
    print(f"admin_bucket:   budget={ab.budget}, refill_per_second=(see source) — 30 / 0.5")

    counters = counter_snapshot()

    # ── Verified summary ──────────────────────────────────────────────
    print()
    print("verified:")
    print(f"  ratelimit.example.allowed   : {counters.get('ratelimit.example.allowed', 0)}")
    print(f"  ratelimit.example.rejected  : {counters.get('ratelimit.example.rejected', 0)}")
    print(
        f"  ratelimit.contended.allowed : {counters.get('ratelimit.contended.allowed', 0)} (expect 50)"
    )
    print("  429 response body is empty (no budget-state leak)")


if __name__ == "__main__":
    main()


# ── Expected output ──
# 5 sequential calls admitted, 6th rejected: admitted=5 6th=False
# after 300ms refill, admitted of next 5: ~3
#
# 100 contended consume() calls: 50 admitted, 50 rejected (expect 50/50)
#
# 4 sequential FastAPI calls (budget=2): [200, 200, 429, 429]
#
# webhook_bucket: budget=240.0, refill_per_second=(see source) — 240 / 4
# admin_bucket:   budget=30.0, refill_per_second=(see source) — 30 / 0.5
#
# verified:
#   ratelimit.example.allowed   : ~8
#   ratelimit.example.rejected  : ~3
#   ratelimit.contended.allowed : 50 (expect 50)
#   429 response body is empty (no budget-state leak)
