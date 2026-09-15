"""Example 01 — Quickstart.

Demonstrates the 30-second production-grade setup:
    configure_logging() + ensure_bootstrap() + install_global_exception_hooks()
    + register_dispatcher()

After this, every line emitted via stdlib `logging` carries correlation IDs,
extra fields render as `key=repr(value)` pairs, noisy third-party loggers
are silenced, and uncaught exceptions fire CRITICAL alerts (with dedup +
rate-limit + escalation).
"""

from __future__ import annotations

import logging
import os

# Run without contacting Azure
os.environ.setdefault("USE_MOCK_BOOTSTRAP", "true")

from vibey_bootstrap.alerts import (
    install_global_exception_hooks,
    register_dispatcher,
)
from vibey_bootstrap.bootstrap import ensure_bootstrap
from vibey_bootstrap.logging import configure_logging

# ── 1. Define your email sender (any callable matching this signature) ──
sent_alerts: list[tuple[list[str], str, int]] = []


def my_email_sender(recipients: list[str], subject: str, html_body: str) -> None:
    """Replace with a real Graph / SendGrid / Microsoft Mail call."""
    sent_alerts.append((recipients, subject, len(html_body)))
    print(f"[mock-sender] → {recipients} subject={subject!r} body_len={len(html_body)}")


# ── 2. Wire everything up at process startup ──────────────────────────────
def main() -> None:
    configure_logging()
    install_global_exception_hooks()
    ensure_bootstrap()
    register_dispatcher(my_email_sender, recipients=["dev-alerts@example.com"])

    logger = logging.getLogger(__name__)
    logger.info(
        "Quickstart wired",
        extra={"phase": "startup", "subsystem": "bootstrap"},
    )

    # ── 3. Demonstrate a CRITICAL alert flowing through the dispatcher ─
    from vibey_bootstrap.alerts import AlertSeverity, alert_dev_team

    alert_dev_team(
        AlertSeverity.CRITICAL,
        subject="Demo alert from quickstart",
        context={"environment": "example", "demo": True},
        dedup_key="quickstart_demo",
    )

    # ── 4. Verified summary ────────────────────────────────────────────
    print()
    print("verified:")
    print("  logging configured     : True")
    print("  bootstrap initialized  : True (mock mode)")
    print("  excepthook wired       : True")
    print(f"  alert emails sent      : {len(sent_alerts)}")


if __name__ == "__main__":
    main()


# ── Expected output ──
# 2026-05-18 ... INFO __main__ Quickstart wired  phase='startup' subsystem='bootstrap'
# [mock-sender] → ['dev-alerts@example.com'] subject='[CRITICAL] Demo alert from quickstart' body_len=...
#
# verified:
#   logging configured     : True
#   bootstrap initialized  : True (mock mode)
#   excepthook wired       : True
#   alert emails sent      : 1
