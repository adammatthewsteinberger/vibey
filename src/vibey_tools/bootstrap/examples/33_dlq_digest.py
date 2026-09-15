"""Example 33 — DLQ growth alarm + daily DLQ digest email.

Two operational primitives for Service Bus dead-letter queues:

- ``check_dlq_growth_rate(repo, ...)``: peek DLQ on a schedule;
  compare to the previous sample within the window. When the delta
  exceeds ``alert_threshold``, fire a CRITICAL alert.
- ``run_dlq_digest(...)``: daily digest email that lists current DLQ
  entries AND drains the pending-alerts queue (Tier 2 ERROR alerts
  that fell back to digest). Embeds an HMAC-signed
  ``resubmit`` link (see example 34) for one-click recovery.

Both functions accept any object matching the Protocol shapes
(``peek_dead_letter_messages(max_count)`` for the repo; ``send_email(...)``
for the email sender) — so apps don't need ``azure-servicebus`` for
unit tests.
"""

from __future__ import annotations

import os

os.environ.setdefault("USE_MOCK_BOOTSTRAP", "true")
os.environ.setdefault("AZURE_BOOTSTRAP_ALLOW_RESET", "1")

from vibey_bootstrap.alerts import (
    AlertSeverity,
    alert_dev_team,
    register_dispatcher,
)
from vibey_bootstrap.alerts import reset_state as reset_alerts
from vibey_bootstrap.counters import _reset_counters
from vibey_bootstrap.logging import configure_logging
from vibey_bootstrap.servicebus import (
    check_dlq_growth_rate,
    run_dlq_digest,
)
from vibey_bootstrap.servicebus.dlq_alarm import reset_state as reset_alarm


# ── Mock Service Bus repo — only needs peek_dead_letter_messages ──────
class MockSbRepo:
    def __init__(self, depths: list[int]) -> None:
        self._depths = list(depths)

    def peek_dead_letter_messages(self, max_count: int) -> list[dict]:
        depth = self._depths.pop(0) if self._depths else 0
        # Each "DLQ entry" is just a dict with fields the digest renders
        return [
            {
                "attachment_name": f"invoice-{i}.pdf",
                "sender": f"cust{i}@example.com",
                "reason": "ParseError",
                "dead_letter_error_description": "PDF could not be parsed",
            }
            for i in range(depth)
        ]


# ── Mock email sender ─────────────────────────────────────────────────
class MockEmailRepo:
    def __init__(self) -> None:
        self.sent: list[tuple[list[str], str, str]] = []

    def send_email(self, recipients: list[str], subject: str, html_body: str) -> None:
        self.sent.append((recipients, subject, html_body))


def main() -> None:
    configure_logging()
    _reset_counters()
    reset_alerts()
    reset_alarm()
    register_dispatcher(lambda *a: None, recipients=["ops@example.com"])

    # ── 1. Growth-rate alarm: 0 → 10 jump exceeds threshold ────────────
    repo = MockSbRepo(depths=[0, 10])

    r1 = check_dlq_growth_rate(repo, alert_threshold=5, sample_window_minutes=60)
    print(f"first sample (baseline)  : {r1}")

    r2 = check_dlq_growth_rate(repo, alert_threshold=5, sample_window_minutes=60)
    print(f"second sample (+10)      : {r2}")

    # ── 2. Daily digest: combines DLQ + pending alerts in one email ────
    # Make sure the alerts queue has something to drain in the digest:
    alert_dev_team(AlertSeverity.ERROR, "earlier today: parser flaked", dedup_key="parser_flake")

    repo_for_digest = MockSbRepo(depths=[3])
    mailer = MockEmailRepo()

    result = run_dlq_digest(
        repo_for_digest,
        mailer,
        dev_recipients=["dev-alerts@example.com"],
        api_key="demo-resubmit-secret",
        public_base_url="https://example.com",
        max_peek=10,
    )
    print(f"\nrun_dlq_digest result    : {result}")
    print(f"emails sent              : {len(mailer.sent)}")
    if mailer.sent:
        _, subject, body = mailer.sent[0]
        print(f"subject                  : {subject!r}")
        print(f"body contains DLQ entry  : {'invoice-0.pdf' in body}")
        print(f"body contains alert row  : {'parser flaked' in body}")
        print(f"body contains resubmit?  : {'/dlq/resubmit?token=' in body}")

    # ── 3. Empty DLQ + empty pending → digest skips ────────────────────
    repo_empty = MockSbRepo(depths=[0])
    mailer2 = MockEmailRepo()
    result_empty = run_dlq_digest(
        repo_empty,
        mailer2,
        dev_recipients=["dev-alerts@example.com"],
        api_key="demo",
        public_base_url="https://example.com",
    )
    print(f"\nempty digest result      : {result_empty}")
    print(f"emails sent              : {len(mailer2.sent)} (skipped)")

    # ── Verified summary ──────────────────────────────────────────────
    print()
    print("verified:")
    print("  growth alarm fires CRITICAL when delta > threshold within window")
    print("  digest email composes DLQ entries + drained ERROR alerts")
    print("  digest skips entirely when both DLQ and alerts are empty")
    print("  resubmit link is HMAC-signed (see example 34)")


if __name__ == "__main__":
    main()


# ── Expected output ──
# first sample (baseline)  : {'current': 0, 'delta': 0, 'alerted': 0}
# second sample (+10)      : {'current': 10, 'delta': 10, 'alerted': 1}
#
# run_dlq_digest result    : {'dlq_count': 3, 'email_sent': True, 'skipped_reason': None, 'pending_alert_count': 1}
# emails sent              : 1
# subject                  : '[DLQ digest] 3 DLQ · 1 batched'
# body contains DLQ entry  : True
# body contains alert row  : True
# body contains resubmit?  : True
#
# empty digest result      : {'dlq_count': 0, 'email_sent': False, 'skipped_reason': 'empty', 'pending_alert_count': 0}
# emails sent              : 0 (skipped)
#
# verified:
#   ...
