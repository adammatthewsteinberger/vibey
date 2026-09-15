"""Email sender tests."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest


def test_acs_email_sender_send(monkeypatch) -> None:
    pytest.importorskip("azure.communication.email")
    monkeypatch.setenv("ACS_CONNECTION_STRING", "endpoint=https://x/;accesskey=y")
    monkeypatch.setenv("ACS_SENDER_ADDRESS", "sender@example.com")
    from vibey_bootstrap.email import AcsEmailSender

    poller = MagicMock()
    poller.result.return_value = MagicMock(id="msg-1")
    client = MagicMock()
    client.begin_send.return_value = poller
    with patch.object(AcsEmailSender, "_get_client", return_value=client):
        sender = AcsEmailSender()
        msg_id = sender.send(to=["a@b.com"], subject="hi", html_body="<p>x</p>")
    assert msg_id == "msg-1"
