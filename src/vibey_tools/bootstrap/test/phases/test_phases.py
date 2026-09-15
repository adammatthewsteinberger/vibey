"""Tests for ``vibey_bootstrap.phases``."""

from __future__ import annotations

import pytest

from vibey_bootstrap.alerts import (
    drain_pending_alerts,
    register_dispatcher,
)
from vibey_bootstrap.alerts import reset_state as reset_alerts
from vibey_bootstrap.counters import _reset_counters, counter_snapshot
from vibey_bootstrap.phases import run_phase, run_phases


@pytest.fixture(autouse=True)
def _reset() -> None:
    _reset_counters()
    reset_alerts()
    register_dispatcher(lambda *a: None, recipients=["ops@example.com"])


def test_run_phase_returns_result_on_success() -> None:
    pr = run_phase(
        "collect",
        lambda: [1, 2, 3],
        namespace="t",
        aggregate_counter="findings",
        alert_severity=None,
    )
    assert pr.ok is True
    assert pr.value == [1, 2, 3]
    snap = counter_snapshot()
    assert snap.get("t.collect.ok", 0) == 1
    assert snap.get("t.collect.findings", 0) == 3


def test_run_phase_never_re_raises_on_failure() -> None:
    def bad() -> None:
        raise RuntimeError("explode")

    # Must not raise:
    pr = run_phase("bad", bad, namespace="t", alert_severity=None)
    assert pr.ok is False
    assert isinstance(pr.exception, RuntimeError)
    assert pr.value is None
    assert counter_snapshot().get("t.bad.failed", 0) == 1


def test_run_phases_continues_after_failure() -> None:
    def fail_phase() -> None:
        raise ValueError("x")

    results = run_phases(
        [("a", fail_phase), ("b", lambda: 42)],
        namespace="t",
        alert_severity=None,
    )
    assert len(results) == 2
    assert results[0].ok is False
    assert results[1].ok is True
    assert results[1].value == 42


def test_run_phase_alerts_with_dedup_per_phase() -> None:
    def bad() -> None:
        raise ValueError("x")

    run_phase("dup", bad, namespace="t")
    run_phase("dup", bad, namespace="t")
    pending = drain_pending_alerts()
    keys = [p.dedup_key for p in pending if p.dedup_key.startswith("t.phase.dup")]
    # dedup window should suppress the second one
    assert len(set(keys)) == 1


def test_run_phase_aggregate_counter_only_when_sized() -> None:
    # When the value is unsized (e.g. an int), aggregate_counter must not crash
    pr = run_phase(
        "scalar", lambda: 42, namespace="t", aggregate_counter="findings", alert_severity=None
    )
    assert pr.ok is True
    assert counter_snapshot().get("t.scalar.findings") is None
