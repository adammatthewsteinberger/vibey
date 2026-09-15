"""Tests for ``vibey_bootstrap.notify``."""

from __future__ import annotations

import time
from dataclasses import dataclass

import pytest

from vibey_bootstrap.counters import _reset_counters, counter_snapshot
from vibey_bootstrap.notify import (
    UnprocessableReason,
    build_failure_alert_body,
    build_unprocessable_notification,
    build_validation_notice_body,
    reset_sender_notification_throttle,
    should_notify_sender,
)


@pytest.fixture(autouse=True)
def _reset() -> None:
    _reset_counters()
    reset_sender_notification_throttle()


# ── Throttle ──────────────────────────────────────────────────────────────


def test_should_notify_admits_below_threshold() -> None:
    addr = "a@b.com"
    for _ in range(3):
        assert should_notify_sender(addr, max_per_hour=3) is True
    assert should_notify_sender(addr, max_per_hour=3) is False


def test_should_notify_window_slides() -> None:
    addr = "a@b.com"
    for _ in range(3):
        assert should_notify_sender(addr, max_per_hour=3, window_seconds=0.1) is True
    time.sleep(0.15)
    assert should_notify_sender(addr, max_per_hour=3, window_seconds=0.1) is True


def test_should_notify_refuses_empty() -> None:
    assert should_notify_sender("") is False
    assert should_notify_sender("   ") is False
    assert counter_snapshot().get("sender.notification.throttled", 0) >= 1


# ── Failure-alert body ─────────────────────────────────────────────────────


def test_sender_body_omits_correlation_id_and_traceback() -> None:
    body = build_failure_alert_body(
        attachment_name="report.pdf",
        correlation_id="SECRET-CID",
        sender="a@b.com",
        error_summary="boom",
        audience="sender",
        product_name="NETA report",
        traceback="SECRET-TRACE-MARKER",
        exception_type="SecretException",
    )
    assert "SECRET-CID" not in body
    assert "SECRET-TRACE-MARKER" not in body
    assert "SecretException" not in body


def test_dev_body_includes_forensics() -> None:
    body = build_failure_alert_body(
        attachment_name="report.pdf",
        correlation_id="DEV-CID",
        sender="a@b.com",
        error_summary="boom",
        audience="dev",
        traceback="DEV-TRACE-MARKER",
    )
    assert "DEV-CID" in body
    assert "DEV-TRACE-MARKER" in body


def test_dev_body_escapes_html() -> None:
    body = build_failure_alert_body(
        attachment_name="<script>alert(1)</script>",
        correlation_id="x",
        sender="a@b.com",
        error_summary="x",
        audience="dev",
    )
    assert "<script>" not in body
    assert "&lt;script&gt;" in body


def test_sender_send_failed_warning_only_in_dev() -> None:
    sender_body = build_failure_alert_body(
        attachment_name="r.pdf",
        correlation_id="x",
        sender="a@b.com",
        error_summary="x",
        audience="sender",
        sender_send_failed=True,
    )
    dev_body = build_failure_alert_body(
        attachment_name="r.pdf",
        correlation_id="x",
        sender="a@b.com",
        error_summary="x",
        audience="dev",
        sender_send_failed=True,
    )
    assert "ALSO failed" not in sender_body
    assert "ALSO failed" in dev_body


# ── Validation notice body ─────────────────────────────────────────────────


@dataclass
class _Issue:
    rule: str
    page_number: int
    equipment_id: str
    message: str


def test_validation_body_renders_issues() -> None:
    issues = [
        _Issue(rule="MSG-1", page_number=3, equipment_id="EQ-A", message="missing value"),
        _Issue(rule="MSG-2", page_number=7, equipment_id="EQ-B", message="format off"),
    ]
    sender_body = build_validation_notice_body(
        attachment_name="r.pdf",
        correlation_id="LEAK-CHECK",
        sender="a@b.com",
        issues=issues,
        audience="sender",
        product_name="NETA report",
    )
    assert "MSG-1" in sender_body
    assert "missing value" in sender_body
    assert "LEAK-CHECK" not in sender_body  # sender body never carries cid


# ── Unprocessable notification ─────────────────────────────────────────────


def test_unprocessable_sender_template_no_jargon() -> None:
    sender_subject, sender_body, dev_subject, dev_body = build_unprocessable_notification(
        failure_reason=UnprocessableReason.TOO_LARGE,
        sender="x@y.com",
        attachment_summary=[{"name": "huge.pdf", "size_bytes": "200MB"}],
        correlation_id="LEAK-CHECK",
        product_name="NETA report",
    )
    assert "too large" in sender_body.lower()
    assert "LEAK-CHECK" not in sender_body
    assert "magic byte" not in sender_body.lower()


def test_unprocessable_dev_body_includes_summary() -> None:
    _, _, _, dev_body = build_unprocessable_notification(
        failure_reason=UnprocessableReason.TYPE_UNSUPPORTED,
        sender="x@y.com",
        attachment_summary=[
            {
                "name": "evil.exe",
                "size_bytes": "100",
                "content_type": "application/pdf",
                "classification": "reject",
                "reject_reason": "unsupported_extension: .exe",
            }
        ],
        correlation_id="CID-XYZ",
    )
    assert "evil.exe" in dev_body
    assert "CID-XYZ" in dev_body
    assert "reject" in dev_body
