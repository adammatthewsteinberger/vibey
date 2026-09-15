"""Tests for ``vibey_bootstrap.logging.correlation``."""

from __future__ import annotations

import logging

from vibey_bootstrap.logging.correlation import (
    CorrelationFilter,
    correlation_scope,
    get_correlation_id,
)


def test_scope_generates_uuid_when_none() -> None:
    with correlation_scope() as cid:
        assert isinstance(cid, str)
        assert len(cid) == 12
        assert get_correlation_id() == cid


def test_scope_nested_resets_outer_value() -> None:
    with correlation_scope("aaaa-aaaa-aaaa"):
        assert get_correlation_id() == "aaaa-aaaa-aaaa"
        with correlation_scope("bbbb-bbbb-bbbb"):
            assert get_correlation_id() == "bbbb-bbbb-bbbb"
        assert get_correlation_id() == "aaaa-aaaa-aaaa"
    assert get_correlation_id() is None


def test_filter_auto_attaches() -> None:
    filt = CorrelationFilter()
    record = logging.LogRecord(
        name="t",
        level=logging.INFO,
        pathname="t.py",
        lineno=1,
        msg="m",
        args=None,
        exc_info=None,
    )
    with correlation_scope("cid-1", email_id="msg-1"):
        filt.filter(record)
        assert record.correlation_id == "cid-1"  # type: ignore[attr-defined]
        assert record.email_id == "msg-1"  # type: ignore[attr-defined]


def test_arbitrary_fields() -> None:
    filt = CorrelationFilter()
    record = logging.LogRecord(
        name="t",
        level=logging.INFO,
        pathname="t.py",
        lineno=1,
        msg="m",
        args=None,
        exc_info=None,
    )
    with correlation_scope(tenant_id="acme", job_id="42"):
        filt.filter(record)
        assert record.tenant_id == "acme"  # type: ignore[attr-defined]
        assert record.job_id == "42"  # type: ignore[attr-defined]


def test_filter_does_not_override_explicit_extra() -> None:
    filt = CorrelationFilter()
    record = logging.LogRecord(
        name="t",
        level=logging.INFO,
        pathname="t.py",
        lineno=1,
        msg="m",
        args=None,
        exc_info=None,
    )
    record.correlation_id = "explicit"  # type: ignore[attr-defined]
    with correlation_scope("from-scope"):
        filt.filter(record)
        assert record.correlation_id == "explicit"  # type: ignore[attr-defined]
