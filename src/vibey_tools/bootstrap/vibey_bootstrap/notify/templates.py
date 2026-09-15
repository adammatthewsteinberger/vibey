# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Two-tier (sender / dev) notification body builders.

Sender bodies are abuse-safe by construction — they OMIT correlation ids,
blob paths, exception types, and tracebacks. Senders are potentially
attackers; they get a generic acknowledgement, not forensic detail.

Dev bodies include the full forensic context (HTML-escaped) so on-call has
everything needed to triage.
"""

from __future__ import annotations

from enum import Enum
from html import escape
from typing import Any

_DEFAULT_SENDER_ACTION_STEPS: tuple[str, ...] = (
    "Verify the attachment opens in a recent PDF reader.",
    "Try resending the email with the attachment re-saved as a PDF.",
    "If the problem persists, reply to this email — our team has been notified.",
)


class UnprocessableReason(str, Enum):
    UNREADABLE = "unreadable"
    NO_PDF_FOUND = "no_pdf_found"
    TOO_LARGE = "too_large"
    TYPE_UNSUPPORTED = "type_unsupported"


_UNPROCESSABLE_TEMPLATES: dict[UnprocessableReason, str] = {
    UnprocessableReason.UNREADABLE: (
        "We couldn't read your attachment. The file may be corrupt, "
        "password-protected, or in an unexpected format."
    ),
    UnprocessableReason.NO_PDF_FOUND: (
        "We didn't find a PDF in your message. Please attach the report as a PDF and resend."
    ),
    UnprocessableReason.TOO_LARGE: (
        "Your attachment was too large to process. Please try splitting the report and resending."
    ),
    UnprocessableReason.TYPE_UNSUPPORTED: (
        "Your attachment type isn't supported. Please send a PDF or a ZIP containing PDFs."
    ),
}


def _row(label: str, value: str) -> str:
    return (
        f'<tr><td style="padding:4px 8px;border:1px solid #ddd;font-weight:bold;">'
        f"{escape(label)}</td>"
        f'<td style="padding:4px 8px;border:1px solid #ddd;">{escape(value)}</td></tr>'
    )


def _table(rows: list[str]) -> str:
    if not rows:
        return ""
    return (
        '<table style="border-collapse:collapse;border:1px solid #ddd;margin-top:8px;">'
        + "".join(rows)
        + "</table>"
    )


def build_failure_alert_body(
    *,
    attachment_name: str,
    correlation_id: str,
    sender: str,
    error_summary: str,
    audience: str,
    product_name: str = "",
    sender_send_failed: bool = False,
    action_steps: tuple[str, ...] | None = None,
    **extra_context: Any,
) -> str:
    """Build an HTML body for a pipeline-failure notification.

    Sender audience: generic acknowledgement, no forensic leakage.
    Dev audience: full traceback / blob path / exception type rendered.
    """
    if audience == "sender":
        steps = action_steps or _DEFAULT_SENDER_ACTION_STEPS
        steps_html = "<ul>" + "".join(f"<li>{escape(s)}</li>" for s in steps) + "</ul>"
        product_clause = (
            f"the {escape(product_name)} you submitted" if product_name else "your submission"
        )
        rows = [
            _row("Attachment", attachment_name),
        ]
        return (
            '<html><body style="font-family:Helvetica,Arial,sans-serif;color:#333;">'
            f"<p>We hit a problem processing {product_clause}. "
            "Our team has been notified and is looking into it.</p>"
            + _table(rows)
            + "<h3 style='margin-top:16px;'>What you can do</h3>"
            + steps_html
            + "</body></html>"
        )

    # dev audience — full forensic detail
    warning = ""
    if sender_send_failed:
        warning = (
            '<p style="background:#fee;padding:8px;border:1px solid #c00;color:#c00;">'
            "⚠ Sender-facing notification ALSO failed to send — manual follow-up needed."
            "</p>"
        )
    product_clause = f"a {escape(product_name)} submission" if product_name else "a submission"
    rows = [
        _row("Attachment", attachment_name),
        _row("Sender", sender),
        _row("Correlation ID", correlation_id),
        _row("Error", error_summary),
    ]
    for key, value in extra_context.items():
        rows.append(_row(key, str(value)))
    return (
        '<html><body style="font-family:Helvetica,Arial,sans-serif;color:#333;">'
        + warning
        + f"<p>Pipeline failure: {product_clause} could not be processed "
        "and has been dead-lettered.</p>" + _table(rows) + "</body></html>"
    )


def build_validation_notice_body(
    *,
    attachment_name: str,
    correlation_id: str,
    sender: str,
    issues: list[Any],
    audience: str,
    product_name: str = "",
    sender_send_failed: bool = False,
    **extra_context: Any,
) -> str:
    """Soft-fail observation body. Report generated; these are advisory."""
    issue_rows = []
    for issue in issues:
        rule = escape(str(getattr(issue, "rule", "") or ""))
        page = escape(str(getattr(issue, "page_number", "") or ""))
        equipment = escape(str(getattr(issue, "equipment_id", "") or ""))
        message = escape(str(getattr(issue, "message", "") or ""))
        issue_rows.append(
            "<tr>"
            f'<td style="padding:4px 8px;border:1px solid #ddd;">{rule}</td>'
            f'<td style="padding:4px 8px;border:1px solid #ddd;">{page}</td>'
            f'<td style="padding:4px 8px;border:1px solid #ddd;">{equipment}</td>'
            f'<td style="padding:4px 8px;border:1px solid #ddd;">{message}</td>'
            "</tr>"
        )
    issue_table = (
        '<table style="border-collapse:collapse;border:1px solid #ddd;margin-top:8px;width:100%;">'
        "<thead><tr>"
        '<th style="padding:4px 8px;border:1px solid #ddd;">Rule</th>'
        '<th style="padding:4px 8px;border:1px solid #ddd;">Page</th>'
        '<th style="padding:4px 8px;border:1px solid #ddd;">Equipment</th>'
        '<th style="padding:4px 8px;border:1px solid #ddd;">Message</th>'
        "</tr></thead><tbody>" + "".join(issue_rows) + "</tbody></table>"
    )

    product_clause = product_name or "report"
    if audience == "sender":
        return (
            '<html><body style="font-family:Helvetica,Arial,sans-serif;color:#333;">'
            f"<p>Your {escape(product_clause)} has been generated and uploaded. "
            "Data quality observations were noted; please review at your "
            "convenience.</p>" + issue_table + "</body></html>"
        )

    warning = ""
    if sender_send_failed:
        warning = (
            '<p style="background:#fee;padding:8px;border:1px solid #c00;color:#c00;">'
            "⚠ Sender-facing notice ALSO failed to send."
            "</p>"
        )
    triage_rows = [_row(k, str(v)) for k, v in extra_context.items()]
    return (
        '<html><body style="font-family:Helvetica,Arial,sans-serif;color:#333;">'
        + warning
        + f"<p>Validation observations: {escape(product_clause)} generated and "
        "uploaded successfully. Listed rules are advisory.</p>"
        + issue_table
        + _table(
            [
                _row("Sender", sender),
                _row("Correlation ID", correlation_id),
                _row("Attachment", attachment_name),
                *triage_rows,
            ]
        )
        + "</body></html>"
    )


def build_unprocessable_notification(
    *,
    failure_reason: UnprocessableReason,
    sender: str,
    attachment_summary: list[dict[str, Any]],
    correlation_id: str,
    product_name: str = "",
    email_subject: str | None = None,
    email_id: str | None = None,
) -> tuple[str, str, str, str]:
    """Returns ``(sender_subject, sender_body, dev_subject, dev_body)``.

    Sender body is template-driven, no internal jargon, no correlation id.
    Dev body has the full forensic table.
    """
    product = product_name or "submission"
    sender_subject = f"Unable to process your {product} submission"
    dev_subject = (
        f"[{product_name}] Unprocessable submission: {failure_reason.value}"
        if product_name
        else f"Unprocessable submission: {failure_reason.value}"
    )

    body_copy = _UNPROCESSABLE_TEMPLATES[failure_reason]
    sender_body = (
        '<html><body style="font-family:Helvetica,Arial,sans-serif;color:#333;">'
        f"<p>{escape(body_copy)}</p>"
        "</body></html>"
    )

    summary_rows = []
    for item in attachment_summary:
        name = escape(str(item.get("name", "")))
        size = escape(str(item.get("size_bytes", "")))
        mime = escape(str(item.get("content_type", "")))
        classification = escape(str(item.get("classification", "")))
        reject = escape(str(item.get("reject_reason", "")))
        summary_rows.append(
            "<tr>"
            f'<td style="padding:4px 8px;border:1px solid #ddd;">{name}</td>'
            f'<td style="padding:4px 8px;border:1px solid #ddd;">{size}</td>'
            f'<td style="padding:4px 8px;border:1px solid #ddd;">{mime}</td>'
            f'<td style="padding:4px 8px;border:1px solid #ddd;">{classification}</td>'
            f'<td style="padding:4px 8px;border:1px solid #ddd;">{reject}</td>'
            "</tr>"
        )
    summary_table = (
        '<table style="border-collapse:collapse;border:1px solid #ddd;width:100%;">'
        "<thead><tr>"
        '<th style="padding:4px 8px;border:1px solid #ddd;">Name</th>'
        '<th style="padding:4px 8px;border:1px solid #ddd;">Size</th>'
        '<th style="padding:4px 8px;border:1px solid #ddd;">MIME</th>'
        '<th style="padding:4px 8px;border:1px solid #ddd;">Classified</th>'
        '<th style="padding:4px 8px;border:1px solid #ddd;">Reject reason</th>'
        "</tr></thead><tbody>" + "".join(summary_rows) + "</tbody></table>"
    )
    dev_rows = [
        _row("Failure reason", failure_reason.value),
        _row("Sender", sender),
        _row("Correlation ID", correlation_id),
    ]
    if email_subject:
        dev_rows.append(_row("Email subject", email_subject))
    if email_id:
        dev_rows.append(_row("Email ID", email_id))

    dev_body = (
        '<html><body style="font-family:Helvetica,Arial,sans-serif;color:#333;">'
        "<p>Inbound submission rejected by the ingress gates.</p>"
        + _table(dev_rows)
        + "<h3>Attachments seen</h3>"
        + summary_table
        + "</body></html>"
    )
    return sender_subject, sender_body, dev_subject, dev_body


__all__ = [
    "UnprocessableReason",
    "build_failure_alert_body",
    "build_unprocessable_notification",
    "build_validation_notice_body",
]
