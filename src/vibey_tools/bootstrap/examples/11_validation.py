"""Example 11 — Queue-message schema validation.

Validate untrusted queue payloads cheaply at the consumer entry point,
BEFORE downloading any blobs or doing any work. The ``queue_message_schema``
helper builds a sensible default schema that rejects ``..`` (path-traversal)
and ``://`` (URL scheme injection) in path-shaped fields.

Key invariants:
- Schema failures raise ``InvalidMessageError`` (a subclass of
  ``UnrecoverableError``) — so the Service Bus consumer wrapper
  dead-letters them.
- The validator MUST run before any external content download.
"""

from __future__ import annotations

import os

os.environ.setdefault("USE_MOCK_BOOTSTRAP", "true")
os.environ.setdefault("AZURE_BOOTSTRAP_ALLOW_RESET", "1")

from vibey_bootstrap.counters import _reset_counters, counter_snapshot
from vibey_bootstrap.exceptions import InvalidMessageError
from vibey_bootstrap.validation import (
    FieldRule,
    MessageSchema,
    queue_message_schema,
    validate_message,
)


def main() -> None:
    _reset_counters()

    # ── 1. Default-shaped consumer schema ──────────────────────────────
    schema = queue_message_schema(
        required_fields=("correlation_id",),
        path_field="blob_path",
        path_required_prefix="reports/",
        counter_namespace="example_queue",
    )

    # ── Happy path ──
    payload = validate_message(
        {"correlation_id": "abc-123", "blob_path": "reports/Q3/x.pdf"},
        schema,
    )
    print(f"happy path: {payload}")

    # ── Path-traversal rejected ──
    try:
        validate_message(
            {"correlation_id": "abc", "blob_path": "reports/../etc/passwd"},
            schema,
        )
    except InvalidMessageError as exc:
        print(f"\nrejected '..': {exc}")

    # ── URL-scheme injection rejected ──
    try:
        validate_message(
            {"correlation_id": "abc", "blob_path": "https://evil.example.com/x"},
            schema,
        )
    except InvalidMessageError as exc:
        print(f"rejected '://': {exc}")

    # ── Prefix enforcement ──
    try:
        validate_message(
            {"correlation_id": "abc", "blob_path": "other-tenant/x.pdf"},
            schema,
        )
    except InvalidMessageError as exc:
        print(f"rejected prefix: {exc}")

    # ── Missing field ──
    try:
        validate_message({"blob_path": "reports/x.pdf"}, schema)
    except InvalidMessageError as exc:
        print(f"rejected missing: {exc}")

    # ── 2. Custom schema with explicit FieldRule ───────────────────────
    custom = MessageSchema(
        fields=(
            FieldRule(name="message_id", required=True, type=str, non_empty=True),
            FieldRule(name="retry_count", required=False, type=int),
            FieldRule(
                name="sender_email",
                required=True,
                type=str,
                pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$",
            ),
        ),
        counter_namespace="custom_queue",
    )

    out = validate_message(
        {"message_id": "msg-1", "retry_count": 3, "sender_email": "alice@example.com"},
        custom,
    )
    print(f"\ncustom schema accepted: {out}")

    counters = counter_snapshot()

    # ── Verified summary ──────────────────────────────────────────────
    print()
    print("verified:")
    print(
        f"  example_queue.rejected.schema : {counters.get('example_queue.rejected.schema', 0)} (expect 4)"
    )
    print(
        f"  custom_queue.rejected.schema  : {counters.get('custom_queue.rejected.schema', 0)} (expect 0)"
    )
    print("  InvalidMessageError is unrecoverable → consumer dead-letters")


if __name__ == "__main__":
    main()


# ── Expected output ──
# happy path: {'correlation_id': 'abc-123', 'blob_path': 'reports/Q3/x.pdf'}
#
# rejected '..': field 'blob_path' contains forbidden substring '..'
# rejected '://': field 'blob_path' contains forbidden substring '://'
# rejected prefix: field 'blob_path' must start with 'reports/'
# rejected missing: missing required field 'correlation_id'
#
# custom schema accepted: {'message_id': 'msg-1', 'retry_count': 3, 'sender_email': 'alice@example.com'}
#
# verified:
#   example_queue.rejected.schema : 4 (expect 4)
#   custom_queue.rejected.schema  : 0 (expect 0)
#   InvalidMessageError is unrecoverable → consumer dead-letters
