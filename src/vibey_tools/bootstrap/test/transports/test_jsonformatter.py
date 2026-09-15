"""JsonLogFormatter: fields, correlation, masking, robustness."""

from __future__ import annotations

import json
import logging

from vibey_bootstrap.logging import JsonLogFormatter, correlation_scope
from vibey_bootstrap.logging.correlation import CorrelationFilter


def _record(msg: str = "hello", **extra: object) -> logging.LogRecord:
    rec = logging.LogRecord("svc", logging.INFO, __file__, 1, msg, None, None)
    for k, v in extra.items():
        setattr(rec, k, v)
    return rec


def test_required_fields() -> None:
    out = json.loads(JsonLogFormatter().format(_record()))
    assert out["level"] == "INFO"
    assert out["logger"] == "svc"
    assert out["message"] == "hello"
    assert "timestamp" in out and out["timestamp"].endswith("+00:00")


def test_extra_fields_serialized() -> None:
    out = json.loads(JsonLogFormatter().format(_record(user_id="u1", count=3)))
    assert out["user_id"] == "u1"
    assert out["count"] == 3


def test_secret_extras_masked() -> None:
    out = json.loads(JsonLogFormatter().format(_record(api_key="supersecret", password="pw")))
    assert out["api_key"] == "***"
    assert out["password"] == "***"


def test_reserved_and_private_keys_excluded() -> None:
    out = json.loads(JsonLogFormatter().format(_record(_internal="x")))
    assert "_internal" not in out
    # stdlib reserved keys like 'levelname' are not duplicated as extras
    assert list(out).count("level") == 1


def test_correlation_fields_present_in_scope() -> None:
    fmt = JsonLogFormatter()
    filt = CorrelationFilter()
    with correlation_scope(correlation_id="abc123", request_id="r1"):
        rec = _record()
        filt.filter(rec)
        out = json.loads(fmt.format(rec))
    assert out["correlation_id"] == "abc123"
    assert out["request_id"] == "r1"


def test_unserializable_extra_falls_back_to_repr() -> None:
    class Weird:
        def __repr__(self) -> str:
            return "<weird>"

    out = json.loads(JsonLogFormatter().format(_record(obj=Weird())))
    assert out["obj"] == "<weird>"


def test_exception_field_rendered() -> None:
    try:
        raise ValueError("boom")
    except ValueError:
        import sys

        rec = logging.LogRecord("svc", logging.ERROR, __file__, 1, "fail", None, sys.exc_info())
    out = json.loads(JsonLogFormatter().format(rec))
    assert "ValueError: boom" in out["exception"]


def test_format_never_raises_on_bad_message() -> None:
    rec = logging.LogRecord("svc", logging.INFO, __file__, 1, "%d", ("notanint",), None)
    # getMessage() would raise; formatter must still return a string.
    result = JsonLogFormatter().format(rec)
    assert isinstance(result, str)
    assert "level" in result
