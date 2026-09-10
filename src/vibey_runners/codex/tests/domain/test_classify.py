# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Classify TurnSignals into CapacityState — ladder, tie-breakers, R1 properties."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from hypothesis import given

from codexloop.domain.capacity import (
    AuthFailed,
    Available,
    PlanWindows,
    QuotaExhausted,
    RateLimitWindow,
    ThrottleExhausted,
    TransientBackendError,
    WindowExhausted,
    is_waitable,
)
from codexloop.domain.classify import classify
from codexloop.domain.error_codes import FATAL_CODES
from codexloop.domain.signals import TurnSignals
from tests.domain.strategies import quota_or_auth_turn_signals, unrecognised_429_turn_signals

RESET = datetime(2026, 8, 13, 12, 0, tzinfo=UTC)


# --- Ladder (strict order) -------------------------------------------------


def test_auth_error_code_returns_auth_failed() -> None:
    state = classify(TurnSignals(error_code="invalid_api_key", http_status=401))
    assert isinstance(state, AuthFailed)
    assert state.reason == "invalid_api_key"
    assert is_waitable(state) is False
    assert not hasattr(state, "resets_at")
    assert not hasattr(state, "retry_after")


def test_http_401_without_code_returns_auth_failed() -> None:
    state = classify(TurnSignals(http_status=401))
    assert isinstance(state, AuthFailed)
    assert state.reason == "unauthorized"
    assert is_waitable(state) is False


def test_http_401_with_unrelated_code_still_auth_failed() -> None:
    state = classify(TurnSignals(http_status=401, error_code="not_an_auth_code"))
    assert isinstance(state, AuthFailed)
    assert state.reason == "not_an_auth_code"


def test_http_401_with_unrelated_type_still_auth_failed() -> None:
    state = classify(TurnSignals(http_status=401, error_type="not_an_auth_type"))
    assert isinstance(state, AuthFailed)
    assert state.reason == "not_an_auth_type"


def test_quota_error_code_returns_quota_exhausted() -> None:
    state = classify(TurnSignals(error_code="insufficient_quota", http_status=429))
    assert isinstance(state, QuotaExhausted)
    assert state.reason == "insufficient_quota"
    assert is_waitable(state) is False
    assert not hasattr(state, "resets_at")
    assert not hasattr(state, "retry_after")


def test_quota_error_type_used_when_code_absent() -> None:
    state = classify(TurnSignals(error_type="credit_balance_exhausted", http_status=429))
    assert isinstance(state, QuotaExhausted)
    assert state.reason == "credit_balance_exhausted"


def test_window_error_code_returns_window_exhausted_without_snapshot() -> None:
    state = classify(TurnSignals(error_code="usage_limit_reached", http_status=429))
    assert state == WindowExhausted(resets_at=None, window="unknown")
    assert is_waitable(state) is True


def test_window_error_uses_primary_plan_window_resets_at() -> None:
    plan = PlanWindows(
        primary=RateLimitWindow(used_percent=100.0, window_minutes=300, resets_at=RESET),
        secondary=None,
        plan_type="plus",
        limit_reached=None,
    )
    state = classify(TurnSignals(error_code="usage_limit_reached", plan_windows=plan))
    assert state == WindowExhausted(resets_at=RESET, window="five_hour")


def test_window_with_plan_windows_but_no_resets_at_stays_unknown() -> None:
    plan = PlanWindows(
        primary=RateLimitWindow(used_percent=80.0, window_minutes=300, resets_at=None),
        secondary=RateLimitWindow(used_percent=10.0, window_minutes=10_080, resets_at=None),
        plan_type=None,
        limit_reached=None,
    )
    state = classify(TurnSignals(error_code="usage_limit_reached", plan_windows=plan))
    assert state == WindowExhausted(resets_at=None, window="unknown")


def test_window_error_falls_back_to_secondary_plan_window_resets_at() -> None:
    plan = PlanWindows(
        primary=None,
        secondary=RateLimitWindow(used_percent=100.0, window_minutes=10_080, resets_at=RESET),
        plan_type=None,
        limit_reached=None,
    )
    state = classify(TurnSignals(error_type="usage_limit_reached", plan_windows=plan))
    assert state == WindowExhausted(resets_at=RESET, window="weekly")


def test_rate_limit_exceeded_returns_throttle_exhausted() -> None:
    state = classify(
        TurnSignals(error_code="rate_limit_exceeded", http_status=429, retry_after_s=7.5)
    )
    assert state == ThrottleExhausted(retry_after=timedelta(seconds=7.5), aggressive=False)
    assert is_waitable(state) is True


def test_slow_down_returns_aggressive_throttle() -> None:
    state = classify(TurnSignals(error_code="slow_down", http_status=429, retry_after_s=12.0))
    assert state == ThrottleExhausted(retry_after=timedelta(seconds=12.0), aggressive=True)


def test_server_is_overloaded_returns_transient_backend_error() -> None:
    state = classify(
        TurnSignals(error_code="server_is_overloaded", http_status=503, retry_after_s=2.0)
    )
    assert state == TransientBackendError(retry_after=timedelta(seconds=2.0))
    assert is_waitable(state) is True


def test_unlisted_5xx_returns_transient_backend_error() -> None:
    state = classify(TurnSignals(http_status=503, error_code="totally_new_backend_blip"))
    assert isinstance(state, TransientBackendError)
    assert is_waitable(state) is True


@pytest.mark.parametrize("code", sorted(FATAL_CODES))
def test_fatal_codes_are_not_capacity_rejections(code: str) -> None:
    state = classify(TurnSignals(error_code=code, http_status=400))
    assert state == Available()
    assert is_waitable(state) is True


def test_unrecognised_429_returns_window_exhausted_without_reset() -> None:
    state = classify(TurnSignals(http_status=429, error_code="brand_new_vendor_code"))
    assert state == WindowExhausted(resets_at=None, window="unknown")
    assert not isinstance(state, QuotaExhausted)
    assert not isinstance(state, AuthFailed)


def test_absence_of_capacity_signal_returns_available() -> None:
    assert classify(TurnSignals()) == Available()


# --- Tie-breakers (naive implementations get these wrong) -------------------


def test_retry_after_with_insufficient_quota_is_quota_exhausted() -> None:
    """Retry-After is ignored when the body is a billing wall."""
    state = classify(
        TurnSignals(
            error_code="insufficient_quota",
            http_status=429,
            retry_after_s=30.0,
        )
    )
    assert isinstance(state, QuotaExhausted)
    assert is_waitable(state) is False
    assert not hasattr(state, "retry_after")
    assert not hasattr(state, "resets_at")


def test_completed_true_with_429_capacity_state_wins() -> None:
    """A capacity rejection always outranks a completion claim."""
    state = classify(
        TurnSignals(
            error_code="rate_limit_exceeded",
            http_status=429,
            completed=True,
            final_message="CODEXLOOP_TASK_FULLY_COMPLETE",
        )
    )
    assert isinstance(state, ThrottleExhausted)
    assert not isinstance(state, Available)


def test_used_percent_97_with_no_error_is_available() -> None:
    """High window utilisation is not itself a capacity rejection."""
    plan = PlanWindows(
        primary=RateLimitWindow(used_percent=97.0, window_minutes=300, resets_at=RESET),
        secondary=None,
        plan_type=None,
        limit_reached=None,
    )
    state = classify(TurnSignals(plan_windows=plan, completed=True))
    assert isinstance(state, Available)
    assert not isinstance(state, WindowExhausted)
    assert not isinstance(state, QuotaExhausted)


# --- Hypothesis properties -------------------------------------------------


@given(quota_or_auth_turn_signals())
def test_quota_or_auth_signals_never_classify_as_waitable_or_with_a_reset_instant(
    signals: TurnSignals,
) -> None:
    """R1 invariant — the single most important test in the repository.

    No TurnSignals whose error.code or error.type is in the QUOTA or AUTH
    sets may produce a waitable CapacityState or one that exposes a reset
    instant. A billing wall and an auth failure have no deadline.
    """
    state = classify(signals)
    assert is_waitable(state) is False
    assert not hasattr(state, "resets_at")
    assert not hasattr(state, "retry_after")
    assert isinstance(state, (QuotaExhausted, AuthFailed))


@given(unrecognised_429_turn_signals())
def test_unrecognised_429_is_bounded_window_never_quota_or_terminal(
    signals: TurnSignals,
) -> None:
    state = classify(signals)
    assert isinstance(state, WindowExhausted)
    assert state.resets_at is None
    assert not isinstance(state, QuotaExhausted)
    assert not isinstance(state, AuthFailed)
    assert is_waitable(state) is True
