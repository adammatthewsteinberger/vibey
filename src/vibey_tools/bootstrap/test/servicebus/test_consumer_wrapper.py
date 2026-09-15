# Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Tests for ``vibey_bootstrap.servicebus.consumer_wrapper.handle_message``."""

from __future__ import annotations

import json
import logging
from typing import Any
from unittest.mock import MagicMock, patch

import pytest

from vibey_bootstrap.alerts import (
    register_dispatcher,
)
from vibey_bootstrap.alerts import reset_state as reset_alerts
from vibey_bootstrap.counters import _reset_counters, counter_snapshot
from vibey_bootstrap.exceptions import (
    InvalidMessageError,
    NetworkError,
)
from vibey_bootstrap.servicebus.consumer_wrapper import handle_message
from vibey_bootstrap.validation import queue_message_schema


def _make_msg(body: Any) -> Any:
    msg = MagicMock()
    if isinstance(body, (bytes, str)):
        msg.body = body
    else:
        msg.body = json.dumps(body).encode("utf-8")
    return msg


@pytest.fixture(autouse=True)
def _reset() -> None:
    _reset_counters()
    reset_alerts()
    register_dispatcher(lambda *a: None, recipients=["ops@example.com"])


def test_completes_on_success() -> None:
    receiver = MagicMock()
    processor = MagicMock()
    msg = _make_msg({"correlation_id": "x"})

    processed, failed = handle_message(receiver, msg, processor)
    assert processed is True and failed is False
    receiver.complete_message.assert_called_once_with(msg)
    receiver.abandon_message.assert_not_called()
    receiver.dead_letter_message.assert_not_called()
    assert counter_snapshot().get("sb.completed", 0) == 1


def test_dead_letters_unrecoverable() -> None:
    receiver = MagicMock()
    processor = MagicMock()
    processor.process.side_effect = InvalidMessageError("poison")
    msg = _make_msg({"correlation_id": "x"})

    processed, failed = handle_message(receiver, msg, processor)
    assert processed is False and failed is True
    receiver.dead_letter_message.assert_called_once()
    kwargs = receiver.dead_letter_message.call_args.kwargs
    assert kwargs["reason"] == "InvalidMessageError"
    processor.notify_failure.assert_called_once()
    assert counter_snapshot().get("sb.dead_lettered", 0) == 1


def test_abandons_transient() -> None:
    receiver = MagicMock()
    processor = MagicMock()
    processor.process.side_effect = NetworkError("temp")
    msg = _make_msg({"correlation_id": "x"})

    processed, failed = handle_message(receiver, msg, processor)
    assert processed is False and failed is True
    receiver.abandon_message.assert_called_once()
    receiver.dead_letter_message.assert_not_called()
    assert counter_snapshot().get("sb.abandoned", 0) == 1


def test_notify_failure_called_before_dead_letter() -> None:
    receiver = MagicMock()
    processor = MagicMock()
    processor.process.side_effect = InvalidMessageError("poison")
    msg = _make_msg({"correlation_id": "x"})

    call_order: list[str] = []
    processor.notify_failure.side_effect = lambda *a, **k: call_order.append("notify")
    receiver.dead_letter_message.side_effect = lambda *a, **k: call_order.append("dl")

    handle_message(receiver, msg, processor)
    assert call_order == ["notify", "dl"]


def test_notify_failure_swallows_exception() -> None:
    receiver = MagicMock()
    processor = MagicMock()
    processor.process.side_effect = InvalidMessageError("poison")
    processor.notify_failure.side_effect = RuntimeError("notify_failure broke")
    msg = _make_msg({"correlation_id": "x"})

    # Must NOT raise; dead_letter MUST still happen
    handle_message(receiver, msg, processor)
    receiver.dead_letter_message.assert_called_once()


def test_invalid_json_dead_letters() -> None:
    receiver = MagicMock()
    processor = MagicMock()
    msg = MagicMock()
    msg.body = b"not json"

    processed, failed = handle_message(receiver, msg, processor)
    assert processed is False and failed is True
    receiver.dead_letter_message.assert_called_once()
    kwargs = receiver.dead_letter_message.call_args.kwargs
    assert kwargs["reason"] == "invalid_json"
    processor.process.assert_not_called()


def test_validates_schema_before_processing() -> None:
    receiver = MagicMock()
    processor = MagicMock()
    schema = queue_message_schema(required_fields=("correlation_id",), path_field="blob_path")
    msg = _make_msg({"blob_path": "foo"})  # missing correlation_id

    processed, failed = handle_message(receiver, msg, processor, schema=schema)
    assert processed is False and failed is True
    processor.process.assert_not_called()
    receiver.dead_letter_message.assert_called_once()


def test_opens_correlation_scope_around_process(caplog: pytest.LogCaptureFixture) -> None:
    from vibey_bootstrap.logging.correlation import CorrelationFilter

    receiver = MagicMock()
    processor = MagicMock()
    test_logger = logging.getLogger("t.sbtest")
    filt = CorrelationFilter()
    test_logger.addFilter(filt)
    try:

        def process(payload: Any) -> None:
            test_logger.info("inside process")

        processor.process.side_effect = process
        msg = _make_msg({"correlation_id": "MY-CID-1234"})

        with caplog.at_level(logging.INFO, logger="t.sbtest"):
            handle_message(receiver, msg, processor)
        matched = [r for r in caplog.records if r.msg == "inside process"]
        seen = [r.msg for r in caplog.records]
        assert matched, f"expected 'inside process' log; got msgs: {seen}"
        assert getattr(matched[0], "correlation_id", None) == "MY-CID-1234"
    finally:
        test_logger.removeFilter(filt)


def test_records_settle_on_all_paths() -> None:
    """``record_message_settled`` must fire in every finally — success, unrecoverable, transient."""

    for case_exc in (None, InvalidMessageError("x"), NetworkError("x")):
        receiver = MagicMock()
        processor = MagicMock()
        if case_exc is not None:
            processor.process.side_effect = case_exc
        msg = _make_msg({"correlation_id": "x"})

        with patch(
            "vibey_bootstrap.servicebus.consumer_wrapper.record_message_settled"
        ) as fake_settle:
            handle_message(receiver, msg, processor)
            fake_settle.assert_called_once()
