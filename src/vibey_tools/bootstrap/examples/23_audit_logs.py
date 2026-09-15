"""Example 23 — Audit-line conventions (build_audit_extra).

Centralizes the "audit log line" pattern so PII/secret leakage at log
call sites is handled consistently:

- Email-shaped values for masked fields → ``mask_email_address``.
- Other secret-named fields → ``mask_api_key``.
- Truncated fields → ``sanitize_for_log(value, max_len=cap)`` so control-
  char injection AND length attacks are both bounded.
- Always inserts ``operation`` and ISO-8601 ``timestamp``.

Apps SHOULD route every ``logger.info("..._AUDIT", extra=...)`` call
through ``build_audit_extra`` so masking is uniform.
"""

from __future__ import annotations

import logging
import os

os.environ.setdefault("USE_MOCK_BOOTSTRAP", "true")
os.environ.setdefault("AZURE_BOOTSTRAP_ALLOW_RESET", "1")

from vibey_bootstrap.audit import (
    AUDIT_LINE_NAMES,
    AUDIT_MASKED_FIELDS,
    AUDIT_TRUNCATED_FIELDS,
    build_audit_extra,
)
from vibey_bootstrap.counters import _reset_counters, counter_snapshot
from vibey_bootstrap.logging import configure_logging


def main() -> None:
    configure_logging()
    _reset_counters()
    logger = logging.getLogger(__name__)

    # ── 1. Email-audit line ─────────────────────────────────────────────
    extra = build_audit_extra(
        "email_audit",
        sender="alice.smith@example.com",
        recipient_count=3,
        subject="Q3 NETA report",
        attachment_count=2,
        attachment_total_bytes=83_412,
    )
    logger.info("EMAIL_AUDIT", extra=extra)
    print(f"sender field rendered as : {extra['sender']!r}  (masked)")
    print(f"recipient_count          : {extra['recipient_count']}  (passed through)")
    print(f"timestamp present        : {'timestamp' in extra}")

    # ── 2. Truncated long subject ──────────────────────────────────────
    long_subject = "x" * 500
    extra2 = build_audit_extra("email_audit", subject=long_subject)
    print(
        f"\nlong subject truncated to: {len(extra2['subject'])} chars (cap is {AUDIT_TRUNCATED_FIELDS['subject']})"
    )
    assert extra2["subject"].endswith("...[truncated]")

    # ── 3. Forensic fields on a failure audit ──────────────────────────
    extra3 = build_audit_extra(
        "report_audit",
        sender="customer@example.com",
        attachment="invoice.pdf",
        outcome="degraded",
        error="upstream timeout",
        traceback="Traceback (most recent):\n  ..." + "x" * 5000,
    )
    logger.warning("REPORT_AUDIT", extra=extra3)
    print(
        f"\ntraceback truncated to   : {len(extra3['traceback'])} chars (cap is {AUDIT_TRUNCATED_FIELDS['traceback']})"
    )

    # ── 4. Empty secret values pass through unchanged ──────────────────
    extra4 = build_audit_extra("auth_audit", api_key="")
    print(f"empty api_key passes through: {extra4['api_key']!r}")

    counters = counter_snapshot()

    # ── Verified summary ──────────────────────────────────────────────
    print()
    print("verified:")
    print(f"  AUDIT_LINE_NAMES (conventions) : {list(AUDIT_LINE_NAMES)}")
    print(f"  masked fields                  : {sorted(AUDIT_MASKED_FIELDS)[:5]}…")
    print(f"  audit.field_masked.sender bumps: {counters.get('audit.field_masked.sender', 0)}")
    print(f"  audit.field_truncated.subject  : {counters.get('audit.field_truncated.subject', 0)}")
    print(
        f"  audit.field_truncated.traceback: {counters.get('audit.field_truncated.traceback', 0)}"
    )


if __name__ == "__main__":
    main()


# ── Expected output ──
# <log lines>
# sender field rendered as : '***th@example.com'  (masked)
# recipient_count          : 3  (passed through)
# timestamp present        : True
#
# long subject truncated to: 114 chars (cap is 100)  [includes "...[truncated]" suffix]
#
# traceback truncated to   : 2014 chars (cap is 2000)
# empty api_key passes through: ''
#
# verified:
#   ...
