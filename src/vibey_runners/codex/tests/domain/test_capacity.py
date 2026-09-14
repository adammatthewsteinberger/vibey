# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Capacity value objects: RateLimitWindow, PlanWindows, CapacityState, is_waitable."""

from __future__ import annotations

import dataclasses
from datetime import UTC, datetime, timedelta

import pytest

from codexloop.domain.capacity import (
    AuthFailed,
    Available,
    CapacityState,
    PlanWindows,
    QuotaExhausted,
    RateLimitWindow,
    ThrottleExhausted,
    TransientBackendError,
    WindowExhausted,
    is_waitable,
)

RESET_FIELD_NAMES = frozenset({"resets_at", "retry_after"})

CAPACITY_MEMBERS: tuple[type[CapacityState], ...] = (
    Available,
    ThrottleExhausted,
    WindowExhausted,
    QuotaExhausted,
    AuthFailed,
    TransientBackendError,
)


def _minimal(member: type[CapacityState]) -> CapacityState:
    if member is Available:
        return Available()
    if member is ThrottleExhausted:
        return ThrottleExhausted()
    if member is WindowExhausted:
        return WindowExhausted()
    if member is QuotaExhausted:
        return QuotaExhausted(reason="insufficient_quota")
    if member is AuthFailed:
        return AuthFailed(reason="invalid_api_key")
    if member is TransientBackendError:
        return TransientBackendError()
    raise AssertionError(f"unhandled member {member!r}")


@pytest.mark.parametrize("member", CAPACITY_MEMBERS)
def test_capacity_members_are_frozen_slots_and_hashable(member: type[CapacityState]) -> None:
    params = member.__dataclass_params__
    assert params.frozen is True
    assert params.slots is True
    instance = _minimal(member)
    assert hash(instance) == hash(instance)
    fields = dataclasses.fields(member)
    if not fields:
        return
    name = fields[0].name
    with pytest.raises(dataclasses.FrozenInstanceError):
        setattr(instance, name, getattr(instance, name))


def test_quota_exhausted_has_no_reset_or_retry_field() -> None:
    names = {f.name for f in dataclasses.fields(QuotaExhausted)}
    assert names.isdisjoint(RESET_FIELD_NAMES)


def test_auth_failed_has_no_reset_or_retry_field() -> None:
    names = {f.name for f in dataclasses.fields(AuthFailed)}
    assert names.isdisjoint(RESET_FIELD_NAMES)


def test_rate_limit_window_remaining_percent_none_when_used_unknown() -> None:
    window = RateLimitWindow(used_percent=None, window_minutes=300, resets_at=None)
    assert window.remaining_percent is None


@pytest.mark.parametrize(
    ("used", "expected"),
    [
        (0.0, 100.0),
        (25.0, 75.0),
        (100.0, 0.0),
        (-10.0, 100.0),  # clamps high
        (150.0, 0.0),  # clamps low
    ],
)
def test_rate_limit_window_remaining_percent_clamps(used: float, expected: float) -> None:
    window = RateLimitWindow(
        used_percent=used,
        window_minutes=300,
        resets_at=datetime(2026, 8, 13, tzinfo=UTC),
    )
    assert window.remaining_percent == expected


def test_plan_windows_and_available_carry_snapshot() -> None:
    primary = RateLimitWindow(used_percent=13.0, window_minutes=300, resets_at=None)
    secondary = RateLimitWindow(used_percent=93.0, window_minutes=10080, resets_at=None)
    plan = PlanWindows(
        primary=primary,
        secondary=secondary,
        plan_type="plus",
        limit_reached=None,
    )
    assert Available(plan_windows=plan).plan_windows is plan
    assert hash(plan) == hash(plan)


def test_waitable_states_may_carry_timing_hints() -> None:
    retry = timedelta(seconds=30)
    resets = datetime(2026, 8, 13, 12, 0, tzinfo=UTC)
    assert ThrottleExhausted(retry_after=retry, aggressive=True).retry_after == retry
    assert WindowExhausted(resets_at=resets, window="five_hour").resets_at == resets
    assert TransientBackendError(retry_after=retry).retry_after == retry


@pytest.mark.parametrize(
    ("state", "expected"),
    [
        (Available(), True),
        (ThrottleExhausted(), True),
        (WindowExhausted(), True),
        (TransientBackendError(), True),
        (QuotaExhausted(reason="insufficient_quota"), False),
        (AuthFailed(reason="invalid_api_key"), False),
    ],
)
def test_is_waitable_false_exactly_for_quota_and_auth(state: CapacityState, expected: bool) -> None:
    assert is_waitable(state) is expected
