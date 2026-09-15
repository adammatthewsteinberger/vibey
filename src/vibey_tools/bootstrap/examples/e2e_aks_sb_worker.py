"""End-to-end AKS Service Bus consumer skeleton — v2.

Pod main loop:
1. ``build_credential()`` picks WorkloadIdentityCredential in cluster
   (no client secrets in pod env).
2. ``ensure_bootstrap()`` loads App Config + Key Vault.
3. ``start_background_monitors(stop_event)`` spawns heartbeat + consumer
   watchdog daemons.
4. Main loop receives Service Bus messages, wraps each in
   ``lock_for_process`` (so the broker doesn't redeliver mid-process)
   and ``handle_message`` (which dead-letter-vs-abandon-classifies
   failures and opens correlation_scope around processing).
5. SIGTERM is caught and ``stop_event.set()`` is called so all daemon
   threads exit cleanly within the Kubernetes 30-second grace period.

Run:
    USE_MOCK_BOOTSTRAP=true python examples/e2e_aks_sb_worker.py --dry-run
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import sys
import threading
import time
from typing import Any
from unittest.mock import MagicMock

if "--dry-run" in sys.argv:
    os.environ.setdefault("USE_MOCK_BOOTSTRAP", "true")
    os.environ.setdefault("AZURE_BOOTSTRAP_ALLOW_RESET", "1")

from vibey_bootstrap.alerts import (
    install_global_exception_hooks,
    register_dispatcher,
)
from vibey_bootstrap.bootstrap import ensure_bootstrap
from vibey_bootstrap.counters import counter_snapshot
from vibey_bootstrap.heartbeat import (
    record_consumer_iteration,
    start_background_monitors,
)
from vibey_bootstrap.identity import build_credential, credential_kind
from vibey_bootstrap.logging import configure_logging
from vibey_bootstrap.sb_lock import lock_for_process
from vibey_bootstrap.servicebus import handle_message
from vibey_bootstrap.validation import queue_message_schema


# ── Project's MessageProcessor ───────────────────────────────────────────
class ReportProcessor:
    """Business-logic handler — wired into handle_message."""

    def __init__(self) -> None:
        self.processed: list[str] = []

    def process(self, payload: dict[str, Any]) -> None:
        # Real project: download blob, run pipeline, upload result, etc.
        # See examples 09 / 10 / 14 / 15 for fault-tolerance idioms.
        self.processed.append(payload["correlation_id"])

    def notify_failure(self, payload: dict[str, Any], error: Exception) -> None:
        # Best-effort sender notification — see example 18 for body builders
        # and example 27 for the alerts dispatcher.
        pass


# ── Mock Service Bus receiver — only needs the three settle methods ─────
class MockReceiver:
    def __init__(self, messages: list[dict[str, Any]]) -> None:
        self._messages = list(messages)
        self.actions: list[tuple[str, dict]] = []

    def receive(self) -> Any | None:
        if not self._messages:
            return None
        payload = self._messages.pop(0)
        msg = MagicMock()
        msg.body = json.dumps(payload).encode("utf-8")
        return msg

    def complete_message(self, msg: Any) -> None:
        self.actions.append(("complete", json.loads(msg.body)))

    def abandon_message(self, msg: Any) -> None:
        self.actions.append(("abandon", json.loads(msg.body)))

    def dead_letter_message(self, msg: Any, *, reason: str, error_description: str) -> None:
        self.actions.append((f"dead_letter({reason})", json.loads(msg.body)))


# ── Main loop ────────────────────────────────────────────────────────────
def main_loop(receiver: Any, processor: Any, stop_event: threading.Event) -> None:
    schema = queue_message_schema(
        required_fields=("correlation_id",),
        path_field="blob_path",
        path_required_prefix="reports/",
    )

    while not stop_event.is_set():
        record_consumer_iteration()  # feeds the watchdog

        msg = receiver.receive()
        if msg is None:
            # No message — sleep a beat to avoid hot-looping; respect stop.
            if stop_event.wait(0.1):
                break
            continue

        with lock_for_process(receiver, msg, max_lock_renewal_seconds=3600):
            handle_message(
                receiver,
                msg,
                processor,
                schema=schema,
                correlation_field="correlation_id",
                extra_correlation_fields=("email_id",),
                source="consumer",
                counter_namespace="sb",
            )


# ── Dry-run driver ──────────────────────────────────────────────────────
def main_dry_run() -> None:
    configure_logging()
    install_global_exception_hooks()
    ensure_bootstrap()
    register_dispatcher(lambda *a: None, recipients=["ops@example.com"])

    print(f"credential kind preferred: {credential_kind().value}")
    print("(in cluster: WorkloadIdentity; locally: CLIENT_SECRET or DEFAULT)")
    # We don't actually call build_credential() in dry-run — no network.

    # Five mock messages: 3 valid, 1 invalid JSON, 1 schema violation
    receiver = MockReceiver(
        messages=[
            {"correlation_id": "cid-1", "blob_path": "reports/Q3/a.pdf"},
            {"correlation_id": "cid-2", "blob_path": "reports/Q3/b.pdf"},
            {"correlation_id": "cid-3", "blob_path": "reports/Q3/c.pdf"},
            {"blob_path": "reports/Q3/no-cid.pdf"},  # missing correlation_id
            {"correlation_id": "cid-5", "blob_path": "../etc/passwd"},  # traversal
        ]
    )
    processor = ReportProcessor()

    stop_event = threading.Event()
    monitors = start_background_monitors(stop_event)
    print(f"\nspawned monitor threads: {[t.name for t in monitors if t.is_alive()]}")

    # Run the loop until the receiver drains
    loop = threading.Thread(
        target=main_loop,
        args=(receiver, processor, stop_event),
        daemon=True,
    )
    loop.start()

    # Wait for all messages to be consumed (in dry-run; real apps wait on signals)
    deadline = time.monotonic() + 2.0
    while loop.is_alive() and time.monotonic() < deadline:
        time.sleep(0.05)
        if not receiver._messages and len(receiver.actions) >= 5:
            break

    # Clean shutdown
    stop_event.set()
    loop.join(timeout=1.0)
    for t in monitors:
        t.join(timeout=1.0)

    print("\n=== receiver actions (settle terminus per message) ===")
    for action, body in receiver.actions:
        print(f"  {action:30} payload={body}")

    print(f"\nsuccessfully processed correlation IDs: {processor.processed}")

    print("\n=== sb counters ===")
    for k, v in sorted(counter_snapshot().items()):
        if k.startswith("sb"):
            print(f"  {k:25} {v}")


def main_pod() -> None:
    """The real entry-point for a Kubernetes deployment."""
    configure_logging()
    install_global_exception_hooks()
    ensure_bootstrap()
    register_dispatcher(
        ...,  # type: ignore[arg-type]  # your project's email sender
        recipients=["dev-alerts@example.com"],
    )

    credential = build_credential()  # WorkloadIdentity in cluster
    # ... use credential to create your azure.servicebus.ServiceBusClient
    # ... then iterate receiver.receive_messages() inside main_loop(...)

    stop_event = threading.Event()
    signal.signal(signal.SIGTERM, lambda *_: stop_event.set())
    signal.signal(signal.SIGINT, lambda *_: stop_event.set())
    monitors = start_background_monitors(stop_event)

    try:
        # main_loop(real_receiver, real_processor, stop_event)
        pass
    finally:
        stop_event.set()
        for t in monitors:
            t.join(timeout=5)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if args.dry_run:
        main_dry_run()
    else:
        print("Run with --dry-run to exercise the in-process driver.")
        print("Production: wire `main_pod()` into your container ENTRYPOINT.")
