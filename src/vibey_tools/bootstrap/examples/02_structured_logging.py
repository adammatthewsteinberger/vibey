"""Example 02 — Structured logging + masking.

Demonstrates the v2 formatter that renders ``extra={...}`` fields as
greppable ``key=repr(value)`` pairs after a two-space gap, plus the
masking helpers that prevent secrets / emails / control-chars from
leaking into log lines.

Key invariants:
- Control chars (``\x00-\x1f``, ``\x7f``) are stripped at the CALL SITE
  via ``sanitize_for_log`` — they enable log-line injection if they reach
  the formatter intact.
- Secrets are masked at the call site via ``mask_secrets_in_dict`` /
  ``mask_api_key``. The formatter is NOT a safety net.
"""

from __future__ import annotations

import logging
import os

os.environ.setdefault("USE_MOCK_BOOTSTRAP", "true")

from vibey_bootstrap.logging import (
    configure_logging,
    mask_api_key,
    mask_email_address,
    mask_secrets_in_dict,
    sanitize_for_log,
)


def main() -> None:
    configure_logging()
    logger = logging.getLogger(__name__)

    # ── Happy path: structured extras render as `key=repr` pairs ──
    logger.info(
        "Processed payload",
        extra={"correlation_id": "abc-123", "record_count": 7, "duration_ms": 42},
    )

    # ── Mask secrets BEFORE they enter extra={} ──
    config = {
        "user_id": "alice",
        "api_key": "super-secret-key-xyz",
        "connection_string": "Endpoint=sb://...;SharedAccessKey=hidden",
        "endpoint": "https://example.com",  # not secret-flagged
    }
    safe_config = mask_secrets_in_dict(config)
    logger.info("Connecting to backend", extra=safe_config)

    # ── Mask individual values ──
    token = "abc-DEFG-1234-secret-xyz"
    user_email = "alice.smith@example.com"
    logger.info(
        "Auth event",
        extra={
            "token": mask_api_key(token),
            "user_email": mask_email_address(user_email),
        },
    )

    # ── Strip control chars from attacker-controlled input ──
    untrusted_subject = "Important\nFAKE LOG LINE\rinjected by attacker"
    logger.info(
        "Inbound email",
        extra={"subject": sanitize_for_log(untrusted_subject)},
    )

    # ── Verified summary ──
    print()
    print("verified:")
    print(f"  mask_api_key('{token}')         → {mask_api_key(token)!r}")
    print(f"  mask_email_address('{user_email}') → {mask_email_address(user_email)!r}")
    print(f"  sanitize_for_log strips \\n\\r    → {sanitize_for_log(untrusted_subject)!r}")
    print(f"  api_key in masked dict        → {safe_config['api_key']!r}")


if __name__ == "__main__":
    main()


# ── Expected output ──
# <log lines with key='value' pairs after a two-space gap>
#
# verified:
#   mask_api_key('abc-DEFG-1234-secret-xyz')         → '***-xyz'
#   mask_email_address('alice.smith@example.com') → '***th@example.com'
#   sanitize_for_log strips \n\r    → 'Important?FAKE LOG LINE?injected by attacker'
#   api_key in masked dict        → '***'
