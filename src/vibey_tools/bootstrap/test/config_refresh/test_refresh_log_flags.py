"""Tests for ``vibey_bootstrap.config_refresh.refresh_log_flags``."""

from __future__ import annotations

import logging

import pytest

from vibey_bootstrap.config_refresh import refresh_log_flags
from vibey_bootstrap.counters import _reset_counters, counter_snapshot


@pytest.fixture(autouse=True)
def _reset(monkeypatch: pytest.MonkeyPatch) -> None:
    _reset_counters()
    for k in ("LOG_LEVEL", "DEBUG_LOGGING_ENABLED", "USE_MOCK_BOOTSTRAP"):
        monkeypatch.delenv(k, raising=False)


def test_mock_short_circuits(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("USE_MOCK_BOOTSTRAP", "true")
    # No counter bumps — pure no-op.
    refresh_log_flags()
    assert counter_snapshot() == {}


def test_missing_refresh_setting_is_ok(monkeypatch: pytest.MonkeyPatch) -> None:
    """When refresh_setting isn't registered, the flow logs DEBUG and continues."""
    import vibey_bootstrap

    saved = getattr(vibey_bootstrap, "refresh_setting", None)
    try:
        # Remove the attribute temporarily
        if hasattr(vibey_bootstrap, "refresh_setting"):
            delattr(vibey_bootstrap, "refresh_setting")
        refresh_log_flags()
    finally:
        if saved is not None:
            vibey_bootstrap.refresh_setting = saved  # type: ignore[attr-defined]


def test_level_change_triggers_reconfigure(monkeypatch: pytest.MonkeyPatch) -> None:
    # Start at INFO
    monkeypatch.setenv("LOG_LEVEL", "INFO")
    from vibey_bootstrap.logging.config import configure_logging

    configure_logging()
    assert logging.getLogger().getEffectiveLevel() == logging.INFO
    # Flip to WARNING and trigger refresh
    monkeypatch.setenv("LOG_LEVEL", "WARNING")
    refresh_log_flags()
    assert logging.getLogger().getEffectiveLevel() == logging.WARNING
    assert counter_snapshot().get("log_flag_refresh.level_changed", 0) >= 1


def test_remote_read_exception_bumps_counter(monkeypatch: pytest.MonkeyPatch) -> None:
    import vibey_bootstrap

    def raising_refresh(*names: str) -> None:
        raise RuntimeError("network down")

    saved = getattr(vibey_bootstrap, "refresh_setting", None)
    try:
        vibey_bootstrap.refresh_setting = raising_refresh  # type: ignore[attr-defined]
        refresh_log_flags()
        assert counter_snapshot().get("log_flag_refresh.remote_read_failed", 0) >= 1
    finally:
        if saved is not None:
            vibey_bootstrap.refresh_setting = saved  # type: ignore[attr-defined]
