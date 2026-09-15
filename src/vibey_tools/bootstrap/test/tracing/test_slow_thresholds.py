"""Tests for ``vibey_bootstrap.tracing.slow_thresholds``."""

from __future__ import annotations

import pytest

from vibey_bootstrap.tracing.slow_thresholds import (
    default_slow_threshold,
    register_slow_threshold,
    reset_slow_thresholds,
)


@pytest.fixture(autouse=True)
def _reset() -> None:
    reset_slow_thresholds()


def test_default_returns_known_op() -> None:
    assert default_slow_threshold("pipeline.process") == 180.0


def test_default_returns_none_for_unknown() -> None:
    assert default_slow_threshold("nonexistent.op") is None


def test_register_overrides_default() -> None:
    register_slow_threshold("pipeline.process", 30.0)
    assert default_slow_threshold("pipeline.process") == 30.0


def test_register_extends_with_new_op() -> None:
    register_slow_threshold("custom.op", 5.5)
    assert default_slow_threshold("custom.op") == 5.5


def test_reset_refuses_without_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("AZURE_BOOTSTRAP_ALLOW_RESET", raising=False)
    with pytest.raises(RuntimeError):
        reset_slow_thresholds()
