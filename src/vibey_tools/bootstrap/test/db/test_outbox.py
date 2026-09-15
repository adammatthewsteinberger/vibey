"""Outbox tests."""

from __future__ import annotations

import pytest

pytest.importorskip("sqlalchemy")

from unittest.mock import MagicMock

from vibey_bootstrap.db.outbox import Outbox, drain_outbox


def test_drain_outbox_sends_and_marks_sent() -> None:
    session = MagicMock()
    session.execute.return_value.fetchall.return_value = [
        ("id-1", '{"to": ["a@b.com"], "subject": "hi", "html_body": "x"}'),
    ]
    session.execute.return_value.rowcount = 1
    sent_payloads: list[dict] = []

    def sender(payload: dict) -> None:
        sent_payloads.append(payload)

    count = drain_outbox(session, sender, batch_size=5)
    assert count == 1
    assert sent_payloads[0]["subject"] == "hi"


def test_outbox_enqueue_bumps_counter() -> None:
    session = MagicMock()
    outbox = Outbox(session)
    outbox.enqueue(idempotency_key="k1", payload={"x": 1})
    session.execute.assert_called()
