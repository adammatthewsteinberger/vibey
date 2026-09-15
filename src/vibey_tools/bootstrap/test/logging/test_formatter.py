"""Tests for ``vibey_bootstrap.logging.formatter``."""

from __future__ import annotations

import logging
import os

import pytest

from vibey_bootstrap.logging.config import configure_logging
from vibey_bootstrap.logging.formatter import (
    ExtraFieldsFormatter,
    LoggingExtraConflictError,
)


def _make_record(**dict_overrides: object) -> logging.LogRecord:
    record = logging.LogRecord(
        name="t",
        level=logging.INFO,
        pathname="t.py",
        lineno=1,
        msg="hello",
        args=None,
        exc_info=None,
    )
    for k, v in dict_overrides.items():
        record.__dict__[k] = v
    return record


def test_renders_extra_fields_as_key_value() -> None:
    fmt = ExtraFieldsFormatter("%(message)s")
    rec = _make_record(op="x", n=42)
    out = fmt.format(rec)
    assert "op='x'" in out
    assert "n=42" in out
    assert "  op=" in out  # two-space gap


def test_drops_stdlib_keys() -> None:
    fmt = ExtraFieldsFormatter("%(message)s")
    rec = _make_record(message="recomputed", asctime="bogus")
    out = fmt.format(rec)
    assert "message=" not in out
    assert "asctime=" not in out


def test_drops_underscore_keys() -> None:
    fmt = ExtraFieldsFormatter("%(message)s")
    rec = _make_record(visible="yes")
    rec.__dict__["_hidden"] = "no"
    out = fmt.format(rec)
    assert "visible='yes'" in out
    assert "_hidden" not in out


def test_no_extras_returns_base_only() -> None:
    fmt = ExtraFieldsFormatter("%(message)s")
    rec = _make_record()
    assert fmt.format(rec) == "hello"


def test_strict_logger_raises_on_reserved_key_in_debug() -> None:
    os.environ["DEBUG_LOGGING_ENABLED"] = "true"
    os.environ["LOG_LEVEL"] = "DEBUG"
    try:
        configure_logging()
        logger = logging.getLogger("t.strict")
        with pytest.raises(LoggingExtraConflictError):
            logger.info("hi", extra={"message": "stomp"})
    finally:
        os.environ.pop("DEBUG_LOGGING_ENABLED", None)
        os.environ.pop("LOG_LEVEL", None)
        # Re-apply defaults so the rest of the suite doesn't see DEBUG.
        logging.setLoggerClass(logging.Logger)
        logging.basicConfig(force=True)
