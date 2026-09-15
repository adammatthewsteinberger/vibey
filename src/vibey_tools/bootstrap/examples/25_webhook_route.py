"""Example 25 — Microsoft-Graph-style webhook route.

``install_graph_webhook_route(app, path, ...)`` wires a full FastAPI
route with the right ordering:

    validation token (handshake) → rate limit → JSON parse →
    per-entry clientState → dedup → background dispatch → 202 Accepted

Key invariants:
- Validation handshake MUST short-circuit ≤ 10 s (Graph timeout).
- ``clientState`` is compared constant-time.
- 401 + 429 responses have empty bodies (no info leak).
- Dedup TTL of 600 s covers Graph's documented retry window.

Requires ``pip install vibey-bootstrap[fastapi]``.
"""

from __future__ import annotations

import os

os.environ.setdefault("USE_MOCK_BOOTSTRAP", "true")
os.environ.setdefault("AZURE_BOOTSTRAP_ALLOW_RESET", "1")
os.environ.setdefault("GRAPH_WEBHOOK_CLIENT_STATE", "demo-client-state-secret")

from vibey_bootstrap.auth import (
    WebhookDedup,
    install_graph_webhook_route,
)
from vibey_bootstrap.counters import _reset_counters, counter_snapshot
from vibey_bootstrap.ratelimit import webhook_bucket


def main() -> None:
    _reset_counters()

    try:
        from fastapi import FastAPI
        from fastapi.testclient import TestClient
    except ImportError:
        print("fastapi not installed — run `pip install vibey-bootstrap[fastapi]`")
        return

    delivered: list[str] = []

    def process_message(message_id: str) -> None:
        """Background handler — fetched message body, processed, etc."""
        delivered.append(message_id)

    app = FastAPI()
    bucket = webhook_bucket(name="example_webhook")
    dedup = WebhookDedup(ttl_seconds=600.0)

    install_graph_webhook_route(
        app,
        "/webhooks/email",
        background_handler=process_message,
        rate_limit_bucket=bucket,
        dedup=dedup,
    )

    client = TestClient(app)

    # ── 1. Validation handshake (subscription creation) ─────────────────
    r = client.post("/webhooks/email?validationToken=abc-xyz-123")
    print(f"validation handshake     : status={r.status_code} body={r.text!r}")

    # ── 2. Live notification with correct clientState ───────────────────
    r = client.post(
        "/webhooks/email",
        json={
            "value": [
                {
                    "clientState": "demo-client-state-secret",
                    "subscriptionId": "sub-1",
                    "resourceData": {"id": "msg-AAA"},
                }
            ]
        },
    )
    print(f"valid notification       : status={r.status_code}")

    # ── 3. Replay (same subscription_id + message_id) is deduped ───────
    r = client.post(
        "/webhooks/email",
        json={
            "value": [
                {
                    "clientState": "demo-client-state-secret",
                    "subscriptionId": "sub-1",
                    "resourceData": {"id": "msg-AAA"},
                }
            ]
        },
    )
    print(f"replay (deduped)         : status={r.status_code}")

    # ── 4. Wrong clientState rejected with 401 + empty body ─────────────
    r = client.post(
        "/webhooks/email",
        json={
            "value": [
                {
                    "clientState": "WRONG",
                    "subscriptionId": "sub-1",
                    "resourceData": {"id": "msg-BBB"},
                }
            ]
        },
    )
    print(f"bad clientState          : status={r.status_code} body_empty={r.content == b''}")

    counters = counter_snapshot()

    # ── Verified summary ───────────────────────────────────────────────
    print()
    print("verified:")
    print(f"  background_handler delivered messages : {delivered}")
    print(f"  webhook.received                      : {counters.get('webhook.received', 0)}")
    print(f"  webhook.dedup_skipped                 : {counters.get('webhook.dedup_skipped', 0)}")
    print(
        f"  webhook.client_state_mismatch         : {counters.get('webhook.client_state_mismatch', 0)}"
    )
    print(
        f"  webhook.validation_token_handshake    : {counters.get('webhook.validation_token_handshake', 0)}"
    )


if __name__ == "__main__":
    main()


# ── Expected output ──
# validation handshake     : status=200 body='abc-xyz-123'
# valid notification       : status=202
# replay (deduped)         : status=202
# bad clientState          : status=401 body_empty=True
#
# verified:
#   background_handler delivered messages : ['msg-AAA']
#   webhook.received                      : 1
#   webhook.dedup_skipped                 : 1
#   webhook.client_state_mismatch         : 1
#   webhook.validation_token_handshake    : 1
