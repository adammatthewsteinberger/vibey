"""Tests for ``timed_operation`` and ``log_exception_context``."""

from __future__ import annotations

import logging

import pytest

from vibey_bootstrap.tracing.log_exception_context import log_exception_context
from vibey_bootstrap.tracing.timed_operation import timed_operation


def test_timed_operation_emits_on_debug(caplog: pytest.LogCaptureFixture) -> None:
    logger = logging.getLogger("t.timed.debug")
    logger.setLevel(logging.DEBUG)
    with caplog.at_level(logging.DEBUG, logger="t.timed.debug"):
        with timed_operation(logger, "op.x", phase="setup") as fields:
            fields["count"] = 5
    assert any("op.x" in r.message for r in caplog.records)


def test_timed_operation_silent_when_info(caplog: pytest.LogCaptureFixture) -> None:
    logger = logging.getLogger("t.timed.info")
    logger.setLevel(logging.INFO)
    with caplog.at_level(logging.INFO, logger="t.timed.info"):
        with timed_operation(logger, "op.x"):
            pass
    assert caplog.records == []


def test_log_exception_context(caplog: pytest.LogCaptureFixture) -> None:
    logger = logging.getLogger("t.exc_ctx")
    with caplog.at_level(logging.ERROR, logger="t.exc_ctx"):
        try:
            raise ValueError("oops")
        except ValueError as exc:
            log_exception_context(logger, exc, operation="t.exc_ctx", input_id=42)
    assert any("ValueError" in r.message or r.exc_info for r in caplog.records)
