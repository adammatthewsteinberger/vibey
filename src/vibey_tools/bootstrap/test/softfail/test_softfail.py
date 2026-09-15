"""Tests for ``vibey_bootstrap.softfail``."""

from __future__ import annotations

import pytest

from vibey_bootstrap.alerts import (
    drain_pending_alerts,
    register_dispatcher,
)
from vibey_bootstrap.alerts import reset_state as reset_alerts
from vibey_bootstrap.counters import _reset_counters, counter_snapshot
from vibey_bootstrap.exceptions import InvalidMessageError
from vibey_bootstrap.softfail import soft_fail, soft_fail_with


@pytest.fixture(autouse=True)
def _reset() -> None:
    _reset_counters()
    reset_alerts()
    register_dispatcher(lambda *a: None, recipients=["ops@example.com"])


def test_returns_fallback_on_caught() -> None:
    def fn() -> int:
        raise ValueError("boom")

    result = soft_fail_with(
        fn,
        fallback=42,
        operation="t.x",
        alert_severity=None,
    )
    assert result.degraded is True
    assert result.value == 42
    assert result.reason == "ValueError"


def test_returns_value_on_success() -> None:
    def fn() -> int:
        return 7

    result = soft_fail_with(fn, fallback=42, operation="t.x", alert_severity=None)
    assert result.degraded is False
    assert result.value == 7
    assert result.exception is None


def test_re_raises_unrecoverable_by_default() -> None:
    def fn() -> None:
        raise InvalidMessageError("poison")

    with pytest.raises(InvalidMessageError):
        soft_fail_with(fn, fallback=42, operation="t.x", alert_severity=None)


def test_unrecoverable_swallowed_when_opted_out() -> None:
    def fn() -> None:
        raise InvalidMessageError("poison")

    result = soft_fail_with(
        fn,
        fallback=99,
        operation="t.x",
        alert_severity=None,
        re_raise_unrecoverable=False,
    )
    assert result.degraded is True
    assert result.value == 99


def test_fallback_fn_receives_exception() -> None:
    captured: list[BaseException] = []

    def fallback(exc: BaseException) -> str:
        captured.append(exc)
        return "from-fn"

    def fn() -> str:
        raise RuntimeError("x")

    result = soft_fail_with(
        fn,
        fallback="default",
        fallback_fn=fallback,
        operation="t.x",
        alert_severity=None,
    )
    assert result.value == "from-fn"
    assert len(captured) == 1
    assert isinstance(captured[0], RuntimeError)


def test_bumps_counter() -> None:
    def fn() -> None:
        raise ValueError("x")

    soft_fail_with(fn, fallback=None, operation="t.x", counter_name="t.failed", alert_severity=None)
    assert counter_snapshot().get("t.failed", 0) == 1


def test_fires_alert() -> None:
    def fn() -> None:
        raise ValueError("x")

    soft_fail_with(fn, fallback=None, operation="t.alert", alert_severity="error")
    pending = drain_pending_alerts()
    matched = [p for p in pending if "soft_fail" in p.dedup_key]
    assert matched


def test_ctx_marks_degraded() -> None:
    with soft_fail(operation="t.ctx", alert_severity=None) as ctx:
        raise ValueError("oops")
    assert ctx["degraded"] is True
    assert ctx["reason"] == "ValueError"


def test_ctx_passes_through_when_no_exception() -> None:
    with soft_fail(operation="t.ctx", alert_severity=None) as ctx:
        ctx["whatever"] = "yes"
    assert ctx["degraded"] is False
    assert ctx["whatever"] == "yes"


def test_ctx_re_raises_unrecoverable() -> None:
    with pytest.raises(InvalidMessageError):
        with soft_fail(operation="t.ctx", alert_severity=None):
            raise InvalidMessageError("poison")
