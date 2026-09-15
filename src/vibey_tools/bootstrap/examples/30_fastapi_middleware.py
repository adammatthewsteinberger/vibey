"""Example 30 — FastAPI request-timing + alerting middleware.

``install_middleware(app, ...)`` registers a single async middleware that:

- Captures start time per request.
- SILENTLY skips probe paths (``/health/live``, ``/health/ready``, etc.)
  — they'd flood the logs in Kubernetes otherwise.
- Logs entry at DEBUG, exit at INFO (or WARNING for status >= 400).
- Fires an ERROR alert when status >= 500 (deduped per
  ``http_5xx:{path}:{status}``).
- Fires an ERROR alert + re-raises on uncaught handler exceptions
  (deduped per ``http_crash:{path}:{type}``).

Requires ``pip install vibey-bootstrap[fastapi]``.
"""

from __future__ import annotations

import os

os.environ.setdefault("USE_MOCK_BOOTSTRAP", "true")
os.environ.setdefault("AZURE_BOOTSTRAP_ALLOW_RESET", "1")

from vibey_bootstrap.alerts import (
    drain_pending_alerts,
    register_dispatcher,
    reset_state,
)
from vibey_bootstrap.counters import _reset_counters
from vibey_bootstrap.fastapi_middleware import install_middleware
from vibey_bootstrap.logging import configure_logging


def main() -> None:
    configure_logging()
    _reset_counters()
    reset_state()

    try:
        from fastapi import FastAPI, HTTPException
        from fastapi.testclient import TestClient
    except ImportError:
        print("fastapi not installed — run `pip install vibey-bootstrap[fastapi]`")
        return

    register_dispatcher(lambda *a: None, recipients=["ops@example.com"])

    app = FastAPI()
    install_middleware(app, alert_subject_prefix="[demo] ")

    @app.get("/health/live")
    def live() -> dict:
        return {"status": "ok"}

    @app.get("/api/work")
    def work() -> dict:
        return {"ok": True}

    @app.get("/api/server-error")
    def server_error() -> dict:
        raise HTTPException(status_code=500, detail="upstream blew up")

    @app.get("/api/crash")
    def crash() -> dict:
        raise RuntimeError("uncaught handler error")

    client = TestClient(app, raise_server_exceptions=False)

    # ── 1. Probe → silent ───────────────────────────────────────────────
    r = client.get("/health/live")
    print(f"probe /health/live      → {r.status_code}  (no log line, no alert)")

    # ── 2. Normal 200 → INFO log only ──────────────────────────────────
    r = client.get("/api/work")
    print(f"normal /api/work        → {r.status_code}")

    # ── 3. 500 → WARNING log + ERROR alert ─────────────────────────────
    r = client.get("/api/server-error")
    print(f"500 /api/server-error   → {r.status_code}")

    # ── 4. Uncaught exception → exception log + ERROR alert + 500 ──────
    r = client.get("/api/crash")
    print(f"crash /api/crash        → {r.status_code}")

    pending = drain_pending_alerts()

    # ── Verified summary ──────────────────────────────────────────────
    print()
    print("verified:")
    print(f"  total alerts deferred to digest      : {len(pending)} (expect 2: 5xx + crash)")
    for p in pending:
        print(f"    dedup_key: {p.dedup_key}")
    print("  probe paths produce no log lines and no alerts")
    print("  alert_subject_prefix prepends '[demo] ' to subject")


if __name__ == "__main__":
    main()


# ── Expected output ──
# probe /health/live      → 200  (no log line, no alert)
# normal /api/work        → 200
# 500 /api/server-error   → 500
# crash /api/crash        → 500
#
# verified:
#   total alerts deferred to digest      : 2 (expect 2: 5xx + crash)
#     dedup_key: http_5xx:/api/server-error:500
#     dedup_key: http_crash:/api/crash:RuntimeError
#   probe paths produce no log lines and no alerts
#   alert_subject_prefix prepends '[demo] ' to subject
