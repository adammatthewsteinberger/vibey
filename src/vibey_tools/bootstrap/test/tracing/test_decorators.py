"""Tests for ``vibey_bootstrap.tracing.decorators``."""

from __future__ import annotations

import asyncio
import logging
import time

import pytest

from vibey_bootstrap.alerts import (
    register_dispatcher,
    reset_state,
)
from vibey_bootstrap.counters import _reset_counters, counter_snapshot
from vibey_bootstrap.tracing.decorators import traced
from vibey_bootstrap.tracing.latency import latency_snapshot, reset_latency_state


@pytest.fixture(autouse=True)
def _reset() -> None:
    reset_latency_state()
    reset_state()
    _reset_counters()


def test_sync_records_latency() -> None:
    @traced(operation="t.sync_records")
    def f() -> int:
        return 1

    f()
    snap = latency_snapshot()
    assert snap["t.sync_records"]["count"] == 1
    assert snap["t.sync_records"]["errors"] == 0


def test_async_records_latency() -> None:
    @traced(operation="t.async_records")
    async def f() -> int:
        return 1

    asyncio.run(f())
    snap = latency_snapshot()
    assert snap["t.async_records"]["count"] == 1


def test_records_error_path() -> None:
    @traced(operation="t.error_path")
    def f() -> None:
        raise ValueError("boom")

    with pytest.raises(ValueError):
        f()
    snap = latency_snapshot()
    assert snap["t.error_path"]["count"] == 1
    assert snap["t.error_path"]["errors"] == 1


def test_skips_arg_serialization_when_debug_off(caplog: pytest.LogCaptureFixture) -> None:
    """When DEBUG is off, the decorator must NOT invoke heavy ``__repr__``."""
    seen_repr_calls: list[str] = []

    class Heavy:
        def __repr__(self) -> str:
            seen_repr_calls.append("touched")
            return "<heavy>"

    @traced(operation="t.no_arg_render")
    def f(obj: Heavy) -> int:
        return 1

    # logger.isEnabledFor(DEBUG) must be False — set caller logger to INFO.
    logging.getLogger(f.__module__).setLevel(logging.INFO)
    f(Heavy())
    assert seen_repr_calls == []


def test_sensitive_args_masked(caplog: pytest.LogCaptureFixture) -> None:
    @traced(operation="t.masking", sensitive_args=("password",))
    def f(user: str, password: str) -> int:
        return 1

    logger = logging.getLogger(f.__module__)
    logger.setLevel(logging.DEBUG)
    with caplog.at_level(logging.DEBUG, logger=f.__module__):
        f("alice", password="hunter2")
    assert "hunter2" not in caplog.text


def test_alert_on_error_fires() -> None:
    received: list[tuple[list[str], str, str]] = []

    def sender(recipients: list[str], subject: str, body: str) -> None:
        received.append((recipients, subject, body))

    register_dispatcher(sender, recipients=["ops@example.com"])

    @traced(operation="t.alert_on_err", alert_on_error="critical")
    def f() -> None:
        raise RuntimeError("nope")

    with pytest.raises(RuntimeError):
        f()
    assert len(received) == 1
    assert "t.alert_on_err failed: RuntimeError" in received[0][1]


def test_slow_threshold_fires_warn(caplog: pytest.LogCaptureFixture) -> None:
    """WARN-severity alerts are log-only by spec; verify via counter + log."""

    @traced(operation="t.slow_warn", slow_threshold_seconds=0.001)
    def f() -> None:
        time.sleep(0.02)

    with caplog.at_level(logging.WARNING, logger="vibey_bootstrap.alerts.dispatcher"):
        f()
    # Latency was still recorded with slow=True
    snap = latency_snapshot()
    assert snap["t.slow_warn"]["slow"] == 1
    # WARN counter ticked
    assert counter_snapshot().get("alerts.warn", 0) >= 1
    # The slow-budget log line fired
    assert any("slow:" in r.message or "slow: " in r.message for r in caplog.records)
