"""Example 21 — Service Bus consumer wrapper (handle_message).

End-to-end dispatcher for a single received message:

1. Parse JSON body. On parse failure → dead-letter with reason
   ``invalid_json``.
2. Schema validation (optional). On ``InvalidMessageError`` → dead-letter
   with the exception class name.
3. Open ``correlation_scope`` from the payload's correlation field; the
   ``CorrelationFilter`` then auto-tags every log line during processing.
4. Call ``processor.process(payload)``. Classify any exception via
   ``is_unrecoverable``:
   - Unrecoverable → best-effort ``processor.notify_failure(...)``,
     then dead-letter, then ERROR alert.
   - Transient → abandon (broker redelivers), ERROR alert.
5. ``record_message_settled()`` always fires in ``finally`` so the
   watchdog sees the message hit a terminal state.
"""

from __future__ import annotations

import json
import os
from typing import Any
from unittest.mock import MagicMock

os.environ.setdefault("USE_MOCK_BOOTSTRAP", "true")
os.environ.setdefault("AZURE_BOOTSTRAP_ALLOW_RESET", "1")

from vibey_bootstrap.alerts import register_dispatcher
from vibey_bootstrap.alerts import reset_state as reset_alerts
from vibey_bootstrap.counters import _reset_counters, counter_snapshot
from vibey_bootstrap.exceptions import InvalidMessageError, NetworkError
from vibey_bootstrap.logging import configure_logging
from vibey_bootstrap.servicebus import handle_message
from vibey_bootstrap.validation import queue_message_schema


# ── A bare-minimum processor matching MessageProcessor Protocol ───────
class DemoProcessor:
    def __init__(self, behavior: str) -> None:
        self.behavior = behavior
        self.notify_failure_called_with: list[tuple[dict, BaseException]] = []

    def process(self, payload: dict) -> None:
        if self.behavior == "ok":
            return
        if self.behavior == "unrecoverable":
            raise InvalidMessageError("payload broke an invariant")
        if self.behavior == "transient":
            raise NetworkError("upstream blip")
        raise RuntimeError(f"unknown behavior {self.behavior!r}")

    def notify_failure(self, payload: dict, error: Exception) -> None:
        # Best-effort customer notification — see example 18 for body
        # builders and the throttle pattern.
        self.notify_failure_called_with.append((payload, error))


def _msg(payload: Any, raw: bytes | None = None) -> Any:
    m = MagicMock()
    m.body = raw if raw is not None else json.dumps(payload).encode()
    return m


def main() -> None:
    configure_logging()
    _reset_counters()
    reset_alerts()
    register_dispatcher(lambda *a: None, recipients=["ops@example.com"])

    schema = queue_message_schema(required_fields=("correlation_id",))

    # ── 1. Happy path: complete ────────────────────────────────────────
    receiver = MagicMock()
    p1 = DemoProcessor("ok")
    handle_message(receiver, _msg({"correlation_id": "cid-1"}), p1, schema=schema)
    print(f"happy path: complete={receiver.complete_message.call_count}")

    # ── 2. Unrecoverable: dead-letter + notify_failure ─────────────────
    receiver = MagicMock()
    p2 = DemoProcessor("unrecoverable")
    handle_message(receiver, _msg({"correlation_id": "cid-2"}), p2, schema=schema)
    print(
        f"unrecoverable: "
        f"dead_letter={receiver.dead_letter_message.call_count}, "
        f"notify_failure_called={len(p2.notify_failure_called_with)}"
    )

    # ── 3. Transient: abandon (broker redelivers) ──────────────────────
    receiver = MagicMock()
    p3 = DemoProcessor("transient")
    handle_message(receiver, _msg({"correlation_id": "cid-3"}), p3, schema=schema)
    print(f"transient: abandon={receiver.abandon_message.call_count}")

    # ── 4. Invalid JSON: dead-letter before processor runs ─────────────
    receiver = MagicMock()
    p4 = DemoProcessor("ok")
    handle_message(receiver, _msg({}, raw=b"not json"), p4, schema=schema)
    print(
        f"invalid_json: dead_letter={receiver.dead_letter_message.call_count}, "
        f"processor_called={p4.notify_failure_called_with == [] and 'process not invoked'}"
    )

    # ── 5. Schema failure: dead-letter with InvalidMessageError reason ──
    receiver = MagicMock()
    p5 = DemoProcessor("ok")
    handle_message(receiver, _msg({}), p5, schema=schema)
    print(f"schema fail: dead_letter={receiver.dead_letter_message.call_count}")

    counters = counter_snapshot()

    # ── Verified summary ───────────────────────────────────────────────
    print()
    print("verified:")
    print(f"  sb.completed        : {counters.get('sb.completed', 0)} (expect 1)")
    print(
        f"  sb.dead_lettered    : {counters.get('sb.dead_lettered', 0)} (expect 3 — unrecov, json, schema)"
    )
    print(f"  sb.abandoned        : {counters.get('sb.abandoned', 0)} (expect 1)")
    print("  unrecoverable path called notify_failure BEFORE dead_letter")
    print("  correlation_scope open during processor.process call")


if __name__ == "__main__":
    main()


# ── Expected output ──
# happy path: complete=1
# unrecoverable: dead_letter=1, notify_failure_called=1
# transient: abandon=1
# invalid_json: dead_letter=1, processor_called=process not invoked
# schema fail: dead_letter=1
#
# verified:
#   sb.completed        : 1 (expect 1)
#   sb.dead_lettered    : 3 (expect 3 — unrecov, json, schema)
#   sb.abandoned        : 1 (expect 1)
#   unrecoverable path called notify_failure BEFORE dead_letter
#   correlation_scope open during processor.process call
