"""Tests for ``vibey_bootstrap.audit``."""

from __future__ import annotations

from vibey_bootstrap.audit import (
    AUDIT_MASKED_FIELDS,
    AUDIT_TRUNCATED_FIELDS,
    build_audit_extra,
    truncate_field,
)


def test_inserts_operation_and_timestamp() -> None:
    extra = build_audit_extra("email_audit")
    assert extra["operation"] == "email_audit"
    assert "timestamp" in extra
    assert extra["timestamp"].endswith("Z")


def test_masks_sender_email() -> None:
    extra = build_audit_extra("email_audit", sender="alice@example.com")
    assert "alice" not in extra["sender"]
    assert "@example.com" in extra["sender"]


def test_masks_api_key_field() -> None:
    extra = build_audit_extra("auth_audit", api_key="abcdefghijklmnop")
    assert extra["api_key"] == "***mnop"


def test_truncates_subject() -> None:
    extra = build_audit_extra("email_audit", subject="x" * 500)
    cap = AUDIT_TRUNCATED_FIELDS["subject"]
    assert len(extra["subject"]) <= cap + len("...[truncated]")


def test_passes_through_counts() -> None:
    extra = build_audit_extra("email_audit", attachment_count=5)
    assert extra["attachment_count"] == 5


def test_empty_secret_passes_through() -> None:
    extra = build_audit_extra("auth_audit", api_key="")
    assert extra["api_key"] == ""


def test_truncate_field_helper_no_op_on_non_string() -> None:
    assert truncate_field("subject", 42) == 42
    assert truncate_field("unknown_field", "anything") == "anything"


def test_masked_fields_documented() -> None:
    """Sanity: spec-required fields are in the masked set."""
    for field in ("sender", "recipient", "api_key", "token", "secret"):
        assert field in AUDIT_MASKED_FIELDS
