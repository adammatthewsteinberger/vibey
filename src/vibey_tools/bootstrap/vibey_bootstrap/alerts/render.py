"""HTML rendering for alert emails and digest fragments."""

from __future__ import annotations

from html import escape
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from vibey_bootstrap.alerts.dispatcher import AlertRecord

_REDACT_KEYS: set[str] = {
    "password",
    "secret",
    "token",
    "authorization",
    "client_secret",
    "api_key",
    "apikey",
    "connection_string",
}


def _redact(ctx: dict[str, Any]) -> dict[str, Any]:
    """Shallow-copy redactor — any key whose lowercase form contains a
    substring from ``_REDACT_KEYS`` has its value replaced with ``***``."""
    out: dict[str, Any] = {}
    for key, value in ctx.items():
        if isinstance(key, str) and any(s in key.lower() for s in _REDACT_KEYS) and value:
            out[key] = "***"
        else:
            out[key] = value
    return out


def _row(label: str, value: str) -> str:
    return (
        f'<tr><td style="padding:4px 8px;border:1px solid #ddd;font-weight:bold;">{escape(label)}</td>'
        f'<td style="padding:4px 8px;border:1px solid #ddd;">{escape(value)}</td></tr>'
    )


def _render_alert_html(rec: AlertRecord) -> str:
    """Render a single alert as a self-contained HTML table."""
    redacted = _redact(rec.context)
    rows = [
        _row("Severity", rec.severity.value.upper()),
        _row("Subject", rec.subject),
        _row("Dedup key", rec.dedup_key),
        _row("Occurrences", str(rec.count)),
    ]
    for key, value in redacted.items():
        rows.append(_row(key, str(value)))
    return (
        '<html><body style="font-family:Helvetica,Arial,sans-serif;color:#333;">'
        f"<h2 style='margin-bottom:0;'>{escape(rec.subject)}</h2>"
        f"<p style='color:#888;margin-top:4px;'>Severity: <b>{escape(rec.severity.value.upper())}</b></p>"
        '<table style="border-collapse:collapse;border:1px solid #ddd;">'
        + "".join(rows)
        + "</table>"
        '<p style="font-size:11px;color:#888;margin-top:16px;">'
        "This alert is rate-limited and deduped. Sustained occurrences will be escalated."
        "</p></body></html>"
    )


def _render_alert_row(r: AlertRecord) -> str:
    """Render one row of a digest table (5 columns)."""
    ctx_html = "<br/>".join(
        f"{escape(str(k))}: {escape(str(v))}" for k, v in _redact(r.context).items()
    )
    return (
        "<tr>"
        f'<td style="padding:4px 8px;border:1px solid #ddd;">{escape(r.severity.value.upper())}</td>'
        f'<td style="padding:4px 8px;border:1px solid #ddd;">{r.count}</td>'
        f'<td style="padding:4px 8px;border:1px solid #ddd;">{escape(r.subject)}</td>'
        f'<td style="padding:4px 8px;border:1px solid #ddd;">{escape(r.dedup_key)}</td>'
        f'<td style="padding:4px 8px;border:1px solid #ddd;">{ctx_html}</td>'
        "</tr>"
    )


def render_pending_alerts_html(records: list[AlertRecord]) -> str:
    """Render the pending-alerts digest fragment for inclusion in a daily email."""
    if not records:
        return ""
    rows = "".join(_render_alert_row(r) for r in records)
    return (
        "<h3>Batched alerts since last digest</h3>"
        '<table style="border-collapse:collapse;border:1px solid #ddd;width:100%;">'
        "<thead><tr>"
        '<th style="padding:4px 8px;border:1px solid #ddd;">Severity</th>'
        '<th style="padding:4px 8px;border:1px solid #ddd;">Count</th>'
        '<th style="padding:4px 8px;border:1px solid #ddd;">Subject</th>'
        '<th style="padding:4px 8px;border:1px solid #ddd;">Dedup key</th>'
        '<th style="padding:4px 8px;border:1px solid #ddd;">Context</th>'
        "</tr></thead><tbody>" + rows + "</tbody></table>"
    )
