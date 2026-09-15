"""End-to-end Azure Function app skeleton — v2.

v2 successor to ``function_app_example.py`` (the v1 demo). Wires together
the idioms from the numbered examples into a runnable HTTP-triggered
Azure Function.

Composed primitives:
- ``ensure_bootstrap()`` lazy init (see 01_quickstart.py)
- ``configure_logging()`` with v2 ExtraFieldsFormatter (see 02)
- ``correlation_scope()`` per request (see 03)
- ``@traced`` on handlers (see 04)
- ``build_audit_extra`` for audit lines (see 23)
- ``bump_counter`` for observability (see 06)
- Alerts dispatcher + global exception hooks (see 27, 28)
- Health probes for /health/live + /health/ready (see 29)

Run locally:
    USE_MOCK_BOOTSTRAP=true python examples/e2e_azure_function.py --dry-run
Deploy: drop the FunctionApp / routes into your function_app.py.
"""

from __future__ import annotations

import argparse
import logging
import os
import sys
import uuid
from typing import Any

# In a real Azure Function the env is provided by the host; for the dry-run
# demo we short-circuit Azure calls.
if "--dry-run" in sys.argv:
    os.environ.setdefault("USE_MOCK_BOOTSTRAP", "true")
    os.environ.setdefault("AZURE_BOOTSTRAP_ALLOW_RESET", "1")

from vibey_bootstrap.alerts import (
    install_global_exception_hooks,
    register_dispatcher,
)
from vibey_bootstrap.audit import build_audit_extra
from vibey_bootstrap.bootstrap import ensure_bootstrap
from vibey_bootstrap.counters import bump_counter, counter_snapshot
from vibey_bootstrap.health import check_app_config_health, check_app_insights_health
from vibey_bootstrap.logging import configure_logging, correlation_scope
from vibey_bootstrap.tracing import traced

logger = logging.getLogger(__name__)


# ── 1. Lazy idempotent startup (Azure Functions worker doesn't run
#       module-level code during indexing — wrap once per cold start) ──
_started = False


def _email_sender(recipients: list[str], subject: str, html_body: str) -> None:
    """Replace with Graph / SendGrid / Microsoft Mail send."""
    logger.info("alert_email_sent", extra={"recipients": len(recipients), "subject": subject[:80]})


def _startup() -> None:
    """Run once. Called from every route handler before any work."""
    global _started
    if _started:
        return
    configure_logging()
    install_global_exception_hooks()
    ensure_bootstrap()
    register_dispatcher(_email_sender, recipients=["dev-alerts@example.com"])
    _started = True


# ── 2. Business logic — fully traced, alert on error ─────────────────────
@traced(operation="example.handle_request", alert_on_error="error")
def handle_request(payload: dict[str, Any]) -> dict[str, Any]:
    """Project's real business logic goes here."""
    if payload.get("raise"):
        raise RuntimeError("simulated handler failure")
    bump_counter("example.requests.processed")
    return {"ok": True, "processed": payload.get("name", "anon")}


# ── 3. Route handlers (each opens a correlation_scope) ──────────────────
def http_handler(request_id: str | None, body: dict[str, Any]) -> dict[str, Any]:
    """In a real Azure Function this is wrapped in @app.route(route="hello")."""
    _startup()
    cid = request_id or uuid.uuid4().hex[:12]
    with correlation_scope(cid, request_id=cid):
        logger.info(
            "REPORT_AUDIT",
            extra=build_audit_extra(
                "http_request",
                method="POST",
                path="/api/hello",
                # NOTE: stdlib LogRecord reserves the key `name`. Use a
                # different field name when forwarding caller payload values.
                payload_name=body.get("name", ""),
            ),
        )
        return handle_request(body)


def health_live() -> dict[str, str]:
    """GET /api/health/live — fast, no external calls."""
    _startup()
    return {"status": "ok"}


def health_ready() -> dict[str, Any]:
    """GET /api/health/ready — checks dependencies."""
    _startup()
    return {
        "status": "ok",
        "app_config": check_app_config_health(),
        "app_insights": check_app_insights_health(),
    }


# ── 4. Dry-run driver — exercises every route in-process ───────────────
def main_dry_run() -> None:
    """Simulate three requests + one error path."""
    print("=== /api/health/live ===")
    print(health_live())

    print("\n=== /api/health/ready ===")
    print(health_ready())

    print("\n=== /api/hello (success) ===")
    print(http_handler(request_id="req-001", body={"name": "world"}))

    print("\n=== /api/hello (raises, alert fires) ===")
    try:
        # Anything that throws inside @traced(alert_on_error=...) will
        # appear in the alerts queue.
        http_handler(
            request_id="req-002",
            body={"name": "raise-me", "raise": True},
        )
    except Exception as exc:
        print(f"  caller saw: {type(exc).__name__}: {exc}")

    print("\n=== counters ===")
    for k, v in sorted(counter_snapshot().items()):
        print(f"  {k:40} {v}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--dry-run", action="store_true", help="Run the dry-run driver (no Azure connections)"
    )
    args = parser.parse_args()

    if args.dry_run:
        main_dry_run()
    else:
        print("This file is meant to be deployed as part of an Azure FunctionApp.")
        print("For a live demo, run with --dry-run.")


# ── In a real function_app.py the route declarations look like this: ───
# import azure.functions as func
# app = func.FunctionApp()
#
# @app.route(route="hello", auth_level=func.AuthLevel.FUNCTION)
# def hello(req: func.HttpRequest) -> func.HttpResponse:
#     body = req.get_json()
#     request_id = req.headers.get("X-Request-Id")
#     result = http_handler(request_id, body)
#     return func.HttpResponse(json.dumps(result), mimetype="application/json")
