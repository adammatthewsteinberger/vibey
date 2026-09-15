"""Tests for ``vibey_bootstrap.alerts.render``."""

from __future__ import annotations

import time

from vibey_bootstrap.alerts.dispatcher import AlertRecord, AlertSeverity
from vibey_bootstrap.alerts.render import (
    _redact,
    _render_alert_html,
    render_pending_alerts_html,
)


def _make_record(**ctx: object) -> AlertRecord:
    now = time.monotonic()
    return AlertRecord(
        severity=AlertSeverity.CRITICAL,
        subject="<script>x</script>",
        context=dict(ctx),
        dedup_key="k",
        first_seen=now,
        last_seen=now,
    )


def test_redact_strips_secret_keys() -> None:
    out = _redact({"password": "live", "user_id": "alice", "API_KEY": "abc"})
    assert out["password"] == "***"
    assert out["API_KEY"] == "***"
    assert out["user_id"] == "alice"


def test_html_escapes_user_input() -> None:
    rec = _make_record()
    body = _render_alert_html(rec)
    assert "<script>" not in body
    assert "&lt;script&gt;" in body


def test_digest_fragment_empty() -> None:
    assert render_pending_alerts_html([]) == ""


def test_digest_fragment_contains_rows() -> None:
    body = render_pending_alerts_html(
        [_make_record(account="acct1"), _make_record(account="acct2")]
    )
    assert "acct1" in body
    assert "acct2" in body
