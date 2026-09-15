# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Tests for ``vibey_bootstrap.tokens``."""

from __future__ import annotations

from pathlib import Path

import pytest

from vibey_bootstrap.tokens import (
    InvalidActionToken,
    issue_action_token,
    verify_action_token,
)


def test_round_trip() -> None:
    token = issue_action_token("sec", action="resubmit_dlq")
    body = verify_action_token("sec", token, expected_action="resubmit_dlq")
    assert body["act"] == "resubmit_dlq"
    assert "exp" in body


def test_payload_extras_round_trip() -> None:
    token = issue_action_token("sec", action="x", payload={"user": "alice", "n": 7})
    body = verify_action_token("sec", token, expected_action="x")
    assert body["user"] == "alice"
    assert body["n"] == 7


def test_rejects_tampered_payload() -> None:
    token = issue_action_token("sec", action="x")
    payload, sig = token.split(".")
    # Flip a single character in the payload section
    altered_payload = "A" + payload[1:] if payload[0] != "A" else "B" + payload[1:]
    tampered = f"{altered_payload}.{sig}"
    with pytest.raises(InvalidActionToken):
        verify_action_token("sec", tampered, expected_action="x")


def test_rejects_expired() -> None:
    token = issue_action_token("sec", action="x", ttl_seconds=-1)
    with pytest.raises(InvalidActionToken, match="expired"):
        verify_action_token("sec", token, expected_action="x")


def test_rejects_wrong_action() -> None:
    token = issue_action_token("sec", action="a")
    with pytest.raises(InvalidActionToken, match="not scoped"):
        verify_action_token("sec", token, expected_action="b")


def test_empty_secret_rejected() -> None:
    with pytest.raises(ValueError):
        issue_action_token("", action="x")
    with pytest.raises(InvalidActionToken):
        verify_action_token("", "anything", expected_action="x")


def test_malformed_token() -> None:
    with pytest.raises(InvalidActionToken):
        verify_action_token("sec", "not-a-token", expected_action="x")
    with pytest.raises(InvalidActionToken):
        verify_action_token("sec", "a.b.c", expected_action="x")


def test_uses_constant_time_compare() -> None:
    """The signature comparison must use ``hmac.compare_digest``."""
    from vibey_bootstrap.tokens import __file__ as tokens_path

    source = Path(tokens_path).read_text()
    assert "hmac.compare_digest" in source, "verify_action_token must not compare with =="
