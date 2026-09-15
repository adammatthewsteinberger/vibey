"""End-to-end FastAPI application skeleton — v2.

Wires together the v2 idioms into a runnable FastAPI app:
- Bootstrap + logging + alerts (see 01_quickstart.py)
- Request-timing + 5xx-alert middleware (see 30)
- Graph-style webhook with validation handshake + clientState + dedup
  + rate limit (see 25)
- Three health probes — live, ready, app-insights logging (see 29)
- API-key-protected admin endpoint (see 13)
- ``/api/metrics`` returning the aggregated metrics snapshot (see 37)

Run:
    USE_MOCK_BOOTSTRAP=true python examples/e2e_fastapi_pipeline.py --dry-run
"""

from __future__ import annotations

import argparse
import os
import sys

if "--dry-run" in sys.argv:
    os.environ.setdefault("USE_MOCK_BOOTSTRAP", "true")
    os.environ.setdefault("AZURE_BOOTSTRAP_ALLOW_RESET", "1")
    os.environ.setdefault("API_KEY", "demo-api-key")
    os.environ.setdefault("GRAPH_WEBHOOK_CLIENT_STATE", "demo-client-state")

from vibey_bootstrap.alerts import (
    install_global_exception_hooks,
    register_dispatcher,
)
from vibey_bootstrap.auth import (
    WebhookDedup,
    install_graph_webhook_route,
    verify_api_key_header,
)
from vibey_bootstrap.bootstrap import ensure_bootstrap
from vibey_bootstrap.fastapi_middleware import install_middleware
from vibey_bootstrap.health import (
    check_app_config_health,
    check_app_insights_health,
    check_app_insights_logging,
)
from vibey_bootstrap.logging import configure_logging
from vibey_bootstrap.metrics import build_metrics_snapshot
from vibey_bootstrap.ratelimit import admin_bucket, fastapi_rate_limit, webhook_bucket


def build_app():  # type: ignore[no-untyped-def]
    from fastapi import Depends, FastAPI, Header

    # ── 1. Startup — call BEFORE creating routes ────────────────────────
    configure_logging()
    install_global_exception_hooks()
    ensure_bootstrap()

    sent_alerts: list[tuple[list[str], str, int]] = []

    def email_sender(recipients: list[str], subject: str, body: str) -> None:
        # Replace with Graph / SendGrid / Microsoft Mail send.
        sent_alerts.append((recipients, subject, len(body)))

    register_dispatcher(email_sender, recipients=["dev-alerts@example.com"])

    # ── 2. FastAPI app + middleware ────────────────────────────────────
    app = FastAPI(title="vibey-bootstrap v2 e2e")
    install_middleware(
        app,
        probe_paths=("/health/live", "/health/ready", "/api/health/live", "/api/health/ready"),
        alert_subject_prefix="[e2e] ",
    )

    # ── 3. Webhook route (no API-key check; clientState is the auth) ────
    delivered: list[str] = []

    def background_handler(message_id: str) -> None:
        # In production this would queue a Service Bus message or kick
        # off the per-message processing pipeline.
        delivered.append(message_id)

    install_graph_webhook_route(
        app,
        "/api/webhooks/email",
        background_handler=background_handler,
        rate_limit_bucket=webhook_bucket(name="email_webhook"),
        dedup=WebhookDedup(ttl_seconds=600),
    )

    # ── 4. Health probes (silent in middleware) ─────────────────────────
    @app.get("/health/live")
    def live() -> dict:
        return {"status": "ok"}

    @app.get("/health/ready")
    def ready() -> dict:
        return {
            "status": "ok",
            "app_config": check_app_config_health(),
            "app_insights": check_app_insights_health(),
            "app_insights_logging": check_app_insights_logging(),
        }

    # ── 5. API-key-protected admin endpoint with rate limit ────────────
    admin_bkt = admin_bucket(name="admin_actions")

    @app.post(
        "/api/admin/reload",
        dependencies=[Depends(fastapi_rate_limit(admin_bkt))],
    )
    async def admin_reload(x_api_key: str = Header(default=None)) -> dict:
        await verify_api_key_header(x_api_key)
        # ... project-specific reload logic ...
        return {"reloaded": True}

    # ── 6. /api/metrics for ops dashboards ──────────────────────────────
    @app.get("/api/metrics")
    def metrics() -> dict:
        return build_metrics_snapshot()

    return app, delivered, sent_alerts


def main_dry_run() -> None:
    try:
        from fastapi.testclient import TestClient
    except ImportError:
        print("fastapi not installed — run `pip install vibey-bootstrap[fastapi]`")
        return

    app, delivered, sent_alerts = build_app()
    client = TestClient(app, raise_server_exceptions=False)

    print("=== GET /health/live ===")
    print(client.get("/health/live").json())

    print("\n=== GET /health/ready ===")
    print(client.get("/health/ready").json())

    print("\n=== POST /api/webhooks/email (validation handshake) ===")
    r = client.post("/api/webhooks/email?validationToken=abc-xyz")
    print(f"  status={r.status_code} body={r.text!r}")

    print("\n=== POST /api/webhooks/email (live notification) ===")
    r = client.post(
        "/api/webhooks/email",
        json={
            "value": [
                {
                    "clientState": "demo-client-state",
                    "subscriptionId": "sub-1",
                    "resourceData": {"id": "msg-AAA"},
                }
            ]
        },
    )
    print(f"  status={r.status_code} delivered={delivered}")

    print("\n=== POST /api/admin/reload (no key → 401) ===")
    r = client.post("/api/admin/reload")
    print(f"  status={r.status_code}")

    print("\n=== POST /api/admin/reload (correct key) ===")
    r = client.post("/api/admin/reload", headers={"x-api-key": "demo-api-key"})
    print(f"  status={r.status_code} body={r.json()}")

    print("\n=== GET /api/metrics ===")
    snap = client.get("/api/metrics").json()
    print(f"  sections={sorted(snap.keys())}")

    print(f"\ndev alerts dispatched (cumulative): {len(sent_alerts)}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.dry_run:
        main_dry_run()
    else:
        print("Run with --dry-run to exercise the in-process test client,")
        print("or wire `build_app()` into your uvicorn/gunicorn entry-point.")
