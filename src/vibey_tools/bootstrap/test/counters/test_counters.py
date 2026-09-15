"""Tests for ``vibey_bootstrap.counters``."""

from __future__ import annotations

import threading

import pytest

from vibey_bootstrap.counters import _reset_counters, bump_counter, counter_snapshot


@pytest.fixture(autouse=True)
def _reset() -> None:
    _reset_counters()


def test_thread_safe() -> None:
    n_threads = 10
    bumps_per_thread = 1000
    barrier = threading.Barrier(n_threads)

    def worker() -> None:
        barrier.wait()
        for _ in range(bumps_per_thread):
            bump_counter("shared.counter")

    threads = [threading.Thread(target=worker) for _ in range(n_threads)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert counter_snapshot()["shared.counter"] == n_threads * bumps_per_thread


def test_never_raises_on_bad_input() -> None:
    # Should not raise — counter just no-ops.
    bump_counter("")  # type: ignore[arg-type]
    bump_counter(None)  # type: ignore[arg-type]
    assert "shared.counter" not in counter_snapshot()


def test_reset_refuses_without_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AZURE_BOOTSTRAP_ALLOW_RESET", raising=False)
    with pytest.raises(RuntimeError):
        _reset_counters()
