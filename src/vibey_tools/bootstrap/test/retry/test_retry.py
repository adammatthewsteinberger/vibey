"""Tests for ``vibey_bootstrap.retry``."""

from __future__ import annotations

import pytest

tenacity = pytest.importorskip("tenacity")

from vibey_bootstrap.counters import _reset_counters, counter_snapshot
from vibey_bootstrap.exceptions import NetworkError, RateLimitError
from vibey_bootstrap.retry import build_retry, retry_ai_transient, retry_azure_transient


@pytest.fixture(autouse=True)
def _reset() -> None:
    _reset_counters()


def test_bumps_runs_counter_per_call() -> None:
    @build_retry(
        operation="t.r1",
        retry_on=NetworkError,
        max_attempts=2,
        wait_min_seconds=0.01,
        wait_max_seconds=0.01,
        counter_namespace="t.r1",
    )
    def ok() -> int:
        return 1

    ok()
    ok()
    ok()
    assert counter_snapshot().get("t.r1.runs", 0) == 3
    assert counter_snapshot().get("t.r1.calls.ok", 0) == 3


def test_bumps_ok_on_success_after_transient_retry() -> None:
    state = {"n": 0}

    @build_retry(
        operation="t.r2",
        retry_on=NetworkError,
        max_attempts=5,
        wait_min_seconds=0.001,
        wait_max_seconds=0.005,
        counter_namespace="t.r2",
    )
    def flaky() -> int:
        state["n"] += 1
        if state["n"] < 3:
            raise NetworkError("temp")
        return 42

    assert flaky() == 42
    assert state["n"] == 3
    assert counter_snapshot().get("t.r2.calls.ok", 0) == 1


def test_bumps_rate_limit_on_429() -> None:
    @build_retry(
        operation="t.r3",
        retry_on=RateLimitError,
        max_attempts=2,
        wait_min_seconds=0.001,
        wait_max_seconds=0.005,
        counter_namespace="t.r3",
    )
    def always_429() -> None:
        raise RateLimitError("429")

    with pytest.raises(RateLimitError):
        always_429()
    assert counter_snapshot().get("t.r3.calls.rate_limit_or_http_error", 0) == 1


def test_does_not_retry_unmatched() -> None:
    @build_retry(
        operation="t.r4",
        retry_on=RateLimitError,
        max_attempts=5,
        wait_min_seconds=0.001,
        wait_max_seconds=0.005,
        counter_namespace="t.r4",
    )
    def always_value_error() -> None:
        raise ValueError("nope")

    with pytest.raises(ValueError):
        always_value_error()
    # Must not have retried
    assert counter_snapshot().get("t.r4.runs", 0) == 1


def test_invokes_rate_limit_callback() -> None:
    captured: list[BaseException] = []

    @build_retry(
        operation="t.r5",
        retry_on=RateLimitError,
        max_attempts=3,
        wait_min_seconds=0.001,
        wait_max_seconds=0.005,
        counter_namespace="t.r5",
        rate_limit_callback=captured.append,
    )
    def flaky() -> str:
        if not captured:
            raise RateLimitError("first")
        return "ok"

    assert flaky() == "ok"
    assert len(captured) == 1
    assert isinstance(captured[0], RateLimitError)


def test_retry_azure_transient_preset() -> None:
    """Just verify the preset constructs and runs."""

    @retry_azure_transient(operation="t.r6", counter_namespace="t.r6")
    def ok() -> int:
        return 7

    assert ok() == 7


def test_retry_ai_transient_preset() -> None:
    @retry_ai_transient(operation="t.r7", counter_namespace="t.r7")
    def ok() -> int:
        return 9

    assert ok() == 9
