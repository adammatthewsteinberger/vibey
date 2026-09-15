"""`handle_message` under adverse conditions: odd bodies, lost locks, broken alerting.

Every branch here ends the same way — the message is settled exactly once and
``record_message_settled`` runs — because a consumer that stops settling stalls the
queue, which is worse than any single bad message.
"""

from __future__ import annotations

import json
import logging
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

import vibey_bootstrap.alerts as alerts
from vibey_bootstrap.alerts import register_dispatcher
from vibey_bootstrap.alerts import reset_state as reset_alerts
from vibey_bootstrap.counters import _reset_counters, counter_snapshot
from vibey_bootstrap.exceptions import InvalidMessageError, NetworkError
from vibey_bootstrap.servicebus import consumer_wrapper as cw
from vibey_bootstrap.servicebus.consumer_wrapper import _msg_body, _settle, handle_message


@pytest.fixture(autouse=True)
def reset():
    _reset_counters()
    reset_alerts()
    register_dispatcher(lambda *a: None, recipients=["ops@example.com"])
    yield
    reset_alerts()


def message(body: Any) -> Any:
    msg = MagicMock()
    msg.body = body
    return msg


# ── body extraction ────────────────────────────────────────────────────────


def test_a_body_property_that_raises_yields_no_body():
    msg = MagicMock()
    msg.body = MagicMock(side_effect=RuntimeError("AMQP frame is gone"))
    assert _msg_body(msg) is None


def test_a_generator_body_is_joined_into_bytes():
    assert _msg_body(message(iter([b"{", b'"a":1', b"}"]))) == b'{"a":1}'


def test_a_generator_body_that_fails_mid_iteration_yields_no_body():
    def explode():
        yield b"{"
        raise RuntimeError("connection dropped mid-frame")

    assert _msg_body(message(explode())) is None


def test_a_string_body_is_parsed_as_json():
    receiver, processor = MagicMock(), MagicMock()
    assert handle_message(receiver, message('{"correlation_id": "x"}'), processor) == (True, False)
    processor.process.assert_called_once_with({"correlation_id": "x"})


def test_a_body_of_an_unusable_type_is_dead_lettered():
    receiver, processor = MagicMock(), MagicMock()
    assert handle_message(receiver, message(None), processor) == (False, True)
    assert receiver.dead_letter_message.call_args.kwargs["reason"] == "invalid_json"
    assert counter_snapshot()["sb.dead_lettered"] == 1


# ── settling ───────────────────────────────────────────────────────────────


def test_an_unknown_settle_action_is_logged_rather_than_raised(caplog):
    with caplog.at_level(logging.WARNING):
        _settle(MagicMock(), MagicMock(), action="teleport")
    assert "lock likely lost" in caplog.text


def test_a_settle_failure_survives_alerting_that_is_also_broken(monkeypatch, caplog):
    monkeypatch.setattr(
        alerts, "alert_dev_team", MagicMock(side_effect=RuntimeError("alerting is down"))
    )
    receiver = MagicMock()
    receiver.complete_message.side_effect = RuntimeError("message lock lost")
    with caplog.at_level(logging.WARNING):
        _settle(receiver, MagicMock(), action="complete")  # must not raise
    assert "lock likely lost" in caplog.text


# ── lock renewal ───────────────────────────────────────────────────────────


def test_a_lock_renewer_that_will_not_register_does_not_stop_processing(caplog):
    renewer = MagicMock()
    renewer.register_message.side_effect = RuntimeError("receiver already closed")
    receiver, processor = MagicMock(), MagicMock()

    with caplog.at_level(logging.WARNING):
        result = handle_message(
            receiver, message(b'{"correlation_id": "x"}'), processor, lock_renewer=renewer
        )
    assert result == (True, False)
    assert "lock_renewer registration failed" in caplog.text


def test_the_lock_renewer_is_closed_even_when_closing_it_fails():
    renewer = MagicMock()
    renewer.close.side_effect = RuntimeError("already closed")
    receiver, processor = MagicMock(), MagicMock()

    assert handle_message(receiver, message(b"{}"), processor, lock_renewer=renewer) == (
        True,
        False,
    )
    renewer.close.assert_called_once()


def test_a_registered_lock_renewer_gets_a_long_renewal_window():
    renewer = MagicMock()
    receiver, processor = MagicMock(), MagicMock()
    handle_message(receiver, message(b"{}"), processor, lock_renewer=renewer)
    assert renewer.register_message.call_args.kwargs["max_lock_renewal_duration"] == 3600


# ── correlation ────────────────────────────────────────────────────────────


def test_extra_correlation_fields_are_bound_only_when_they_are_non_empty_strings():
    seen: dict[str, Any] = {}

    def capture(payload):
        from vibey_bootstrap.logging.correlation import get_correlation_id

        seen["cid"] = get_correlation_id()

    processor = MagicMock()
    processor.process.side_effect = capture
    body = json.dumps(
        {"correlation_id": "cid-1", "tenant": "acme", "empty": "", "numeric": 7}
    ).encode()

    with patch.object(cw, "correlation_scope", wraps=cw.correlation_scope) as scope:
        handle_message(
            MagicMock(),
            message(body),
            processor,
            extra_correlation_fields=("tenant", "empty", "numeric", "absent"),
        )

    assert scope.call_args.kwargs == {"tenant": "acme"}
    assert seen["cid"] == "cid-1"


# ── failure paths with broken alerting ─────────────────────────────────────


def test_a_dead_letter_still_happens_when_alerting_is_broken(monkeypatch):
    monkeypatch.setattr(
        alerts, "alert_dev_team", MagicMock(side_effect=RuntimeError("alerting is down"))
    )
    receiver, processor = MagicMock(), MagicMock()
    processor.process.side_effect = InvalidMessageError("permanently bad payload")

    assert handle_message(receiver, message(b"{}"), processor) == (False, True)
    receiver.dead_letter_message.assert_called_once()
    assert counter_snapshot()["sb.dead_lettered"] == 1


def test_an_abandon_still_happens_when_alerting_is_broken(monkeypatch):
    monkeypatch.setattr(
        alerts, "alert_dev_team", MagicMock(side_effect=RuntimeError("alerting is down"))
    )
    receiver, processor = MagicMock(), MagicMock()
    processor.process.side_effect = NetworkError("the database blinked")

    assert handle_message(receiver, message(b"{}"), processor) == (False, True)
    receiver.abandon_message.assert_called_once()
    assert counter_snapshot()["sb.abandoned"] == 1
