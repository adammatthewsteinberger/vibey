"""Tests for ``vibey_bootstrap.servicebus.dlq_alarm`` and ``.dlq_digest``."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from vibey_bootstrap.alerts import (
    AlertSeverity,
    alert_dev_team,
    register_dispatcher,
)
from vibey_bootstrap.alerts import reset_state as reset_alerts
from vibey_bootstrap.servicebus.dlq_alarm import (
    check_dlq_growth_rate,
)
from vibey_bootstrap.servicebus.dlq_alarm import reset_state as reset_alarm
from vibey_bootstrap.servicebus.dlq_digest import run_dlq_digest


@pytest.fixture
def alert_capture() -> list[tuple[list[str], str, str]]:
    received: list[tuple[list[str], str, str]] = []

    def sender(recipients: list[str], subject: str, body: str) -> None:
        received.append((recipients, subject, body))

    reset_alerts()
    register_dispatcher(sender, recipients=["ops@example.com"])
    yield received
    reset_alerts()


def test_dlq_growth_alarm_fires_critical(
    alert_capture: list[tuple[list[str], str, str]],
) -> None:
    reset_alarm()
    repo = MagicMock()
    # First sample: 0 DLQ messages
    repo.peek_dead_letter_messages = MagicMock(return_value=[])
    result_1 = check_dlq_growth_rate(repo, alert_threshold=5)
    assert result_1["current"] == 0
    # Second sample: 10 DLQ messages — exceeds threshold by far
    repo.peek_dead_letter_messages = MagicMock(return_value=[{}] * 10)
    result_2 = check_dlq_growth_rate(repo, alert_threshold=5)
    assert result_2["current"] == 10
    assert result_2["delta"] == 10
    assert result_2["alerted"] == 1
    matched = [c for c in alert_capture if "growth rate exceeded" in c[1].lower()]
    assert matched


def test_run_dlq_digest_skips_empty(alert_capture: list) -> None:
    sb_repo = MagicMock()
    sb_repo.peek_dead_letter_messages = MagicMock(return_value=[])
    email_repo = MagicMock()
    result = run_dlq_digest(
        sb_repo,
        email_repo,
        dev_recipients=["ops@example.com"],
        api_key="key",
        public_base_url="https://example.com",
    )
    assert result["email_sent"] is False
    assert result["skipped_reason"] == "empty"
    email_repo.send_email.assert_not_called()


def test_run_dlq_digest_folds_pending_alerts(alert_capture: list) -> None:
    """DLQ empty, pending alerts populated → single email with digest section."""
    alert_dev_team(AlertSeverity.ERROR, "thing broke", dedup_key="t1")
    alert_dev_team(AlertSeverity.ERROR, "other thing", dedup_key="t2")
    sb_repo = MagicMock()
    sb_repo.peek_dead_letter_messages = MagicMock(return_value=[])
    email_repo = MagicMock()
    result = run_dlq_digest(
        sb_repo,
        email_repo,
        dev_recipients=["ops@example.com"],
        api_key="key",
        public_base_url="https://example.com",
    )
    assert result["email_sent"] is True
    assert result["pending_alert_count"] == 2
    email_repo.send_email.assert_called_once()
    body = email_repo.send_email.call_args[0][2]
    assert "thing broke" in body
    assert "other thing" in body


def test_run_dlq_digest_with_entries_and_resubmit_link(alert_capture: list) -> None:
    sb_repo = MagicMock()
    sb_repo.peek_dead_letter_messages = MagicMock(
        return_value=[{"attachment_name": "invoice.pdf", "reason": "ParseError"}]
    )
    email_repo = MagicMock()
    result = run_dlq_digest(
        sb_repo,
        email_repo,
        dev_recipients=["ops@example.com"],
        api_key="secret-key",
        public_base_url="https://example.com",
    )
    assert result["email_sent"] is True
    assert result["dlq_count"] == 1
    body = email_repo.send_email.call_args[0][2]
    assert "/dlq/resubmit?token=" in body
    assert "invoice.pdf" in body


def test_run_dlq_digest_no_recipients(alert_capture: list) -> None:
    sb_repo = MagicMock()
    sb_repo.peek_dead_letter_messages = MagicMock(return_value=[{"reason": "x"}])
    email_repo = MagicMock()
    result = run_dlq_digest(
        sb_repo,
        email_repo,
        dev_recipients=[],
        api_key="",
        public_base_url="",
    )
    assert result["email_sent"] is False
    assert result["skipped_reason"] == "no_recipients"
