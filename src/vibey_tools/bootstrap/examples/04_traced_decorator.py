"""Example 04 — @traced decorator.

The ``@traced`` decorator records latency on every call (success AND error
paths), auto-detects async, and optionally fires alerts on exceptions or
slow runs. Sensitive argument values are masked before they ever reach a
log line.

Key invariants:
- Latency recorded on BOTH success and exception paths.
- Async detection via ``asyncio.iscoroutinefunction`` — no manual choice.
- When DEBUG is off, ``inspect.signature`` is skipped entirely so the hot
  path stays cheap.
- ``alert_on_error="error"`` lazy-imports ``vibey_bootstrap.alerts`` so
  apps without the alerts extra still get tracing.
"""

from __future__ import annotations

import asyncio
import logging
import os

os.environ.setdefault("USE_MOCK_BOOTSTRAP", "true")
os.environ.setdefault("AZURE_BOOTSTRAP_ALLOW_RESET", "1")

from vibey_bootstrap.alerts import (
    drain_pending_alerts,
    register_dispatcher,
)
from vibey_bootstrap.alerts import reset_state as reset_alerts
from vibey_bootstrap.logging import configure_logging
from vibey_bootstrap.tracing import latency_snapshot, reset_latency_state, traced

logger = logging.getLogger(__name__)


# ── Sync function, no alerting ───────────────────────────────────────────
@traced(operation="example.compute")
def compute(a: int, b: int) -> int:
    return a + b


# ── Async function — auto-detected ──────────────────────────────────────
@traced(operation="example.async_fetch")
async def async_fetch(name: str) -> str:
    await asyncio.sleep(0.01)
    return f"hello-{name}"


# ── Sensitive args + alert on error ─────────────────────────────────────
@traced(
    operation="example.auth",
    sensitive_args=("password", "token"),
    alert_on_error="error",  # fires an ERROR alert when this raises
)
def authenticate(username: str, password: str, token: str | None = None) -> None:
    raise RuntimeError("invalid credentials")


def main() -> None:
    configure_logging()
    reset_latency_state()
    reset_alerts()

    captured: list[tuple[list[str], str, str]] = []
    register_dispatcher(
        lambda r, s, b: captured.append((r, s, b)),
        recipients=["ops@example.com"],
    )

    # ── 1. Sync + async record latency ───────────────────────────────────
    for _ in range(3):
        compute(2, 3)
    asyncio.run(async_fetch("world"))

    # ── 2. Error path still records latency + fires the alert ────────────
    try:
        authenticate("alice", password="hunter2", token="bearer-secret-xyz")
    except RuntimeError:
        pass

    pending = drain_pending_alerts()
    snap = latency_snapshot()

    # ── Verified summary ────────────────────────────────────────────────
    print()
    print("verified:")
    print(f"  example.compute count        : {snap['example.compute']['count']}")
    print(f"  example.async_fetch count    : {snap['example.async_fetch']['count']}")
    print(f"  example.auth errors          : {snap['example.auth']['errors']}")
    print(f"  alerts deferred to digest    : {len(pending)} (ERROR severity)")
    auth_alert = [p for p in pending if "auth" in p.dedup_key]
    if auth_alert:
        print(f"  alert dedup_key              : {auth_alert[0].dedup_key}")
        # 'hunter2' MUST NOT appear in the alert context
        assert "hunter2" not in str(auth_alert[0].context), "sensitive arg leaked!"
        print("  password value leaked in ctx : False (sensitive_args masked)")


if __name__ == "__main__":
    main()


# ── Expected output ──
# <log lines>
#
# verified:
#   example.compute count        : 3
#   example.async_fetch count    : 1
#   example.auth errors          : 1
#   alerts deferred to digest    : 1 (ERROR severity)
#   alert dedup_key              : example.auth:RuntimeError
#   password value leaked in ctx : False (sensitive_args masked)
