"""Daily DLQ digest emails with embedded resubmit link + pending-alert summary."""

from __future__ import annotations

import logging
from collections.abc import Iterable
from html import escape
from typing import Any, Protocol

from vibey_bootstrap.tokens import (
    InvalidActionToken,
    issue_action_token,
    verify_action_token,
)
from vibey_bootstrap.tracing.decorators import traced

_logger = logging.getLogger(__name__)
_DLQ_RESUBMIT_ACTION = "resubmit_dlq"


class InvalidResubmitToken(InvalidActionToken):
    """Resubmit token is invalid (alias of ``InvalidActionToken``)."""


def issue_resubmit_token(secret: str, *, ttl_seconds: int = 24 * 60 * 60) -> str:
    return issue_action_token(secret, action=_DLQ_RESUBMIT_ACTION, ttl_seconds=ttl_seconds)


def verify_resubmit_token(secret: str, token: str) -> None:
    try:
        verify_action_token(secret, token, expected_action=_DLQ_RESUBMIT_ACTION)
    except InvalidActionToken as exc:
        raise InvalidResubmitToken(str(exc)) from exc


class EmailRepoProtocol(Protocol):
    def send_email(self, recipients: list[str], subject: str, html_body: str) -> None: ...


def build_dlq_digest_body(
    entries: list[dict[str, Any]],
    resubmit_url: str | None,
) -> str:
    """5-column escaped HTML table: attachment, sender, dlq_time, reason, detail.

    Includes a "Resubmit all" button when ``resubmit_url`` is provided, else a
    CLI hint.
    """
    rows: list[str] = []
    for e in entries:
        attachment = escape(str(e.get("attachment_name") or e.get("subject") or ""))
        sender = escape(str(e.get("sender") or ""))
        ts = escape(str(e.get("dlq_time") or e.get("enqueued_time_utc") or ""))
        reason = escape(str(e.get("dead_letter_reason") or e.get("reason") or ""))
        detail = escape(str(e.get("dead_letter_error_description") or e.get("detail") or "")[:200])
        rows.append(
            "<tr>"
            f'<td style="padding:4px 8px;border:1px solid #ddd;">{attachment}</td>'
            f'<td style="padding:4px 8px;border:1px solid #ddd;">{sender}</td>'
            f'<td style="padding:4px 8px;border:1px solid #ddd;">{ts}</td>'
            f'<td style="padding:4px 8px;border:1px solid #ddd;">{reason}</td>'
            f'<td style="padding:4px 8px;border:1px solid #ddd;">{detail}</td>'
            "</tr>"
        )
    table_body = "".join(rows) or (
        '<tr><td colspan="5" style="padding:8px;text-align:center;color:#888;">'
        "No dead-letter messages.</td></tr>"
    )
    if resubmit_url:
        action_block = (
            '<p style="margin-top:16px;">'
            f'<a href="{escape(resubmit_url)}" '
            'style="background:#0078d4;color:#fff;padding:10px 16px;'
            'text-decoration:none;border-radius:4px;">Resubmit all</a></p>'
        )
    else:
        action_block = (
            '<p style="margin-top:16px;color:#888;font-size:12px;">'
            "To resubmit, run the DLQ resubmit CLI with a valid API key.</p>"
        )
    return (
        '<html><body style="font-family:Helvetica,Arial,sans-serif;color:#333;">'
        f"<h2>Dead-letter queue digest ({len(entries)} messages)</h2>"
        '<table style="border-collapse:collapse;border:1px solid #ddd;width:100%;">'
        "<thead><tr>"
        '<th style="padding:4px 8px;border:1px solid #ddd;">Attachment</th>'
        '<th style="padding:4px 8px;border:1px solid #ddd;">Sender</th>'
        '<th style="padding:4px 8px;border:1px solid #ddd;">DLQ&rsquo;d at</th>'
        '<th style="padding:4px 8px;border:1px solid #ddd;">Reason</th>'
        '<th style="padding:4px 8px;border:1px solid #ddd;">Detail</th>'
        "</tr></thead><tbody>" + table_body + "</tbody></table>" + action_block + "</body></html>"
    )


@traced(operation="dlq_digest.run", alert_on_error="error")
def run_dlq_digest(
    service_bus_repo: Any,
    email_repo: EmailRepoProtocol,
    *,
    dev_recipients: Iterable[str],
    api_key: str,
    public_base_url: str,
    max_peek: int = 50,
    subject_prefix: str = "[DLQ digest]",
) -> dict[str, Any]:
    """Daily DLQ digest + pending-alerts summary email."""
    from vibey_bootstrap.alerts import (
        drain_pending_alerts,
        render_pending_alerts_html,
    )

    try:
        entries = service_bus_repo.peek_dead_letter_messages(max_count=max_peek) or []
    except Exception:
        _logger.exception("dlq_digest: peek failed")
        entries = []

    pending_alerts = drain_pending_alerts()
    recipients = [r.strip() for r in dev_recipients if r and r.strip()]

    if not entries and not pending_alerts:
        return {
            "dlq_count": 0,
            "email_sent": False,
            "skipped_reason": "empty",
            "pending_alert_count": 0,
        }
    if not recipients:
        _logger.warning("dlq_digest: no recipients, skipping")
        return {
            "dlq_count": len(entries),
            "email_sent": False,
            "skipped_reason": "no_recipients",
            "pending_alert_count": len(pending_alerts),
        }

    resubmit_url: str | None = None
    if api_key and public_base_url:
        token = issue_resubmit_token(api_key)
        resubmit_url = f"{public_base_url.rstrip('/')}/dlq/resubmit?token={token}"
    body = build_dlq_digest_body(entries, resubmit_url)
    if pending_alerts:
        body += render_pending_alerts_html(pending_alerts)

    subject = f"{subject_prefix} {len(entries)} DLQ · {len(pending_alerts)} batched"
    email_repo.send_email(recipients, subject, body)
    return {
        "dlq_count": len(entries),
        "email_sent": True,
        "skipped_reason": None,
        "pending_alert_count": len(pending_alerts),
    }


__all__ = [
    "EmailRepoProtocol",
    "InvalidResubmitToken",
    "build_dlq_digest_body",
    "issue_resubmit_token",
    "run_dlq_digest",
    "verify_resubmit_token",
]
