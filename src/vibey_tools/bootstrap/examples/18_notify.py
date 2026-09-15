"""Example 18 — Sender / dev notification builders + per-sender throttle.

Two-tier email bodies. The library enforces a hard contract at build time:
``audience='sender'`` bodies OMIT correlation IDs, blob paths, exception
types, and tracebacks. Senders can be attackers; they get a generic
acknowledgement, not internal forensics. ``audience='dev'`` bodies
include the full triage context.

``should_notify_sender`` is a per-sender sliding-window throttle that
defends against reflection amplification (attacker spoofs ``From:``
headers; pipeline bounces unbounded notifications). Dev-team alerts are
NEVER throttled — they're a separate path.
"""

from __future__ import annotations

import os

os.environ.setdefault("USE_MOCK_BOOTSTRAP", "true")
os.environ.setdefault("AZURE_BOOTSTRAP_ALLOW_RESET", "1")

from vibey_bootstrap.counters import _reset_counters, counter_snapshot
from vibey_bootstrap.notify import (
    UnprocessableReason,
    build_failure_alert_body,
    build_unprocessable_notification,
    reset_sender_notification_throttle,
    should_notify_sender,
)


def main() -> None:
    _reset_counters()
    reset_sender_notification_throttle()

    SECRET_CID = "LEAK-CHECK-CORRELATION-ID"
    SECRET_TRACE = "LEAK-CHECK-TRACEBACK"

    # ── 1. Sender vs dev failure-alert body ────────────────────────────
    sender_body = build_failure_alert_body(
        attachment_name="report.pdf",
        correlation_id=SECRET_CID,
        sender="customer@example.com",
        error_summary="upstream timeout",
        audience="sender",
        product_name="NETA report",
        traceback=SECRET_TRACE,
        exception_type="UpstreamError",
        blob_path="reports/Q3/report.pdf",
    )

    dev_body = build_failure_alert_body(
        attachment_name="report.pdf",
        correlation_id=SECRET_CID,
        sender="customer@example.com",
        error_summary="upstream timeout",
        audience="dev",
        traceback=SECRET_TRACE,
        exception_type="UpstreamError",
        blob_path="reports/Q3/report.pdf",
    )

    leaks_in_sender = [
        m for m in (SECRET_CID, SECRET_TRACE, "UpstreamError", "reports/Q3") if m in sender_body
    ]
    leaks_in_dev = [m for m in (SECRET_CID, SECRET_TRACE) if m in dev_body]

    print(f"sender body length            : {len(sender_body)} chars")
    print(f"sender body leaks (must be 0) : {len(leaks_in_sender)} {leaks_in_sender}")
    print(f"dev body length               : {len(dev_body)} chars")
    print(f"dev body forensic markers     : {len(leaks_in_dev)} {leaks_in_dev}")

    # ── 2. Unprocessable notification (sender + dev variants) ──────────
    s_subj, s_body, d_subj, d_body = build_unprocessable_notification(
        failure_reason=UnprocessableReason.TOO_LARGE,
        sender="customer@example.com",
        attachment_summary=[
            {"name": "huge.pdf", "size_bytes": 200_000_000, "reject_reason": "size_cap"},
        ],
        correlation_id="CID-UNPROC-1",
        product_name="NETA report",
    )
    print(f"\nsender subject : {s_subj!r}")
    print(f"dev subject    : {d_subj!r}")
    print(f"sender body has correlation id  : {'CID-UNPROC-1' in s_body}")
    print(f"dev body has correlation id     : {'CID-UNPROC-1' in d_body}")
    print(f"sender body has 'too large' copy: {'too large' in s_body.lower()}")
    print(f"dev body has reject_reason col  : {'reject reason' in d_body.lower()}")

    # ── 3. Per-sender throttle ─────────────────────────────────────────
    addr = "alice@example.com"
    admits = [should_notify_sender(addr, max_per_hour=3) for _ in range(5)]
    print(f"\nthrottle admits (max 3/hr): {admits}")
    empty = should_notify_sender("")
    print(f"empty sender admits: {empty} (must be False — defense against spoofed From:)")

    counters = counter_snapshot()

    # ── Verified summary ──────────────────────────────────────────────
    print()
    print("verified:")
    print(f"  sender body OMITS cid/traceback/exception/blob_path : {len(leaks_in_sender) == 0}")
    print(f"  dev body INCLUDES cid + traceback                   : {len(leaks_in_dev) == 2}")
    print(
        f"  sender.notified counter                             : {counters.get('sender.notified', 0)}"
    )
    print(
        f"  sender.notification.throttled                       : {counters.get('sender.notification.throttled', 0)}"
    )


if __name__ == "__main__":
    main()


# ── Expected output ──
# sender body length            : <some length>
# sender body leaks (must be 0) : 0 []
# dev body length               : <larger length>
# dev body forensic markers     : 2 ['LEAK-CHECK-CORRELATION-ID', 'LEAK-CHECK-TRACEBACK']
#
# sender subject : 'Unable to process your NETA report submission'
# dev subject    : '[NETA report] Unprocessable submission: too_large'
# sender body has correlation id  : False
# dev body has correlation id     : True
# sender body has 'too large' copy: True
# dev body has reject_reason col  : True
#
# throttle admits (max 3/hr): [True, True, True, False, False]
# empty sender admits: False (must be False — defense against spoofed From:)
#
# verified:
#   sender body OMITS cid/traceback/exception/blob_path : True
#   dev body INCLUDES cid + traceback                   : True
#   sender.notified counter                             : 3
#   sender.notification.throttled                       : 3
