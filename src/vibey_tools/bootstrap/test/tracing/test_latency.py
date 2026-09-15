"""Tests for ``vibey_bootstrap.tracing.latency``."""

from __future__ import annotations

import pytest

from vibey_bootstrap.tracing.latency import (
    _HIST,
    _HIST_CAP,
    _record_latency,
    latency_snapshot,
    reset_latency_state,
)


@pytest.fixture(autouse=True)
def _reset() -> None:
    reset_latency_state()


def test_downsample_at_cap() -> None:
    for i in range(2000):
        _record_latency("downsample_op", float(i) / 100, error=False, slow=False)
    assert len(_HIST["downsample_op"].samples) <= _HIST_CAP


def test_percentiles_monotonic() -> None:
    for i in range(1, 1001):
        _record_latency("percentiles_op", float(i) / 1000.0, error=False, slow=False)
    snap = latency_snapshot()["percentiles_op"]
    assert snap["p50"] <= snap["p95"] <= snap["p99"] <= snap["max"]


def test_error_counter_increments() -> None:
    _record_latency("err_op", 0.1, error=True, slow=False)
    _record_latency("err_op", 0.2, error=True, slow=False)
    _record_latency("err_op", 0.3, error=False, slow=False)
    snap = latency_snapshot()["err_op"]
    assert snap["count"] == 3
    assert snap["errors"] == 2


def test_reset_refuses_without_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AZURE_BOOTSTRAP_ALLOW_RESET", raising=False)
    with pytest.raises(RuntimeError):
        reset_latency_state()
