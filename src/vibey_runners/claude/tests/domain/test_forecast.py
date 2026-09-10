# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""The five forecast laws. Identical in every runner, because a wind-down that
means something different per vendor is worse than none at all."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

from claudeloop.domain.capacity import Available
from claudeloop.domain.forecast import (
    BurnRate,
    CapacityForecast,
    Headroom,
    WindDownPolicy,
    forecast,
    should_wind_down,
)

AVAILABLE_UNKNOWN = Available()


def available_at(used: float) -> Available:
    """`used` is utilization: 0.99 means 99% consumed, 1% headroom."""
    return Available(utilization=used)


NOW = datetime(2026, 8, 15, 12, 0, tzinfo=timezone.utc)
ON = WindDownPolicy(enabled=True)


def _forecast(**kwargs: object) -> CapacityForecast:
    params: dict[str, object] = {
        "available": AVAILABLE_UNKNOWN,
        "turns_spent": 5,
        "now": NOW,
        "policy": ON,
    }
    params.update(kwargs)
    available = params.pop("available")
    return forecast(available, **params)  # type: ignore[arg-type]


# --- F1: unknown is never exhausted -----------------------------------------


def test_f1_unknown_vendor_headroom_never_winds_down() -> None:
    """A missing vendor field must not stop a run. Conflating "cannot see it"
    with "none left" is how a healthy run gets killed for no reason."""
    projection = _forecast(available=AVAILABLE_UNKNOWN)
    assert projection.known is False
    assert should_wind_down(projection, ON, turns_spent=5) is None


def test_f1_unknown_is_not_zero() -> None:
    assert Headroom(None, "x").known is False
    assert Headroom(0.0, "x").known is True


# --- F2: stale degrades to unknown ------------------------------------------


def test_f2_a_stale_reading_becomes_unknown_not_stale() -> None:
    fresh = Headroom(0.05, "utilization", NOW - timedelta(minutes=1))
    stale = Headroom(0.05, "utilization", NOW - timedelta(hours=2))
    policy = timedelta(minutes=15)
    assert fresh.staled(now=NOW, max_staleness=policy).known is True
    assert stale.staled(now=NOW, max_staleness=policy).known is False


def test_f2_a_stale_vendor_reading_cannot_trigger_a_wind_down() -> None:
    projection = _forecast(
        available=available_at(0.99),
        capacity_as_of=NOW - timedelta(hours=2),
    )
    assert should_wind_down(projection, ON, turns_spent=5) is None


# --- F3: never before the first completed turn ------------------------------


def test_f3_no_wind_down_before_any_turn_has_completed() -> None:
    """Otherwise a run starting at 90% utilization hands off an empty brief and
    engines pass nothing to each other forever."""
    projection = _forecast(available=available_at(0.99), turns_spent=0, capacity_as_of=NOW)
    assert should_wind_down(projection, ON, turns_spent=0) is None


def test_f3_the_same_forecast_does_wind_down_after_one_turn() -> None:
    projection = _forecast(available=available_at(0.99), turns_spent=1, capacity_as_of=NOW)
    assert should_wind_down(projection, ON, turns_spent=1) is not None


# --- F4: monotone ------------------------------------------------------------


@settings(max_examples=200)
@given(
    high=st.floats(min_value=0.0, max_value=1.0),
    drop=st.floats(min_value=0.0, max_value=1.0),
)
def test_f4_lowering_headroom_never_switches_a_wind_down_back_off(high: float, drop: float) -> None:
    low = max(0.0, high - drop)
    # utilization is "used", so a *higher* utilization is *lower* headroom.
    looser = _forecast(available=available_at(low), capacity_as_of=NOW)
    tighter = _forecast(available=available_at(high), capacity_as_of=NOW)
    if should_wind_down(looser, ON, turns_spent=5) is not None:
        assert should_wind_down(tighter, ON, turns_spent=5) is not None


# --- F5: binding is the minimum KNOWN dimension ------------------------------


def test_f5_binding_ignores_unknown_dimensions() -> None:
    projection = _forecast(
        available=available_at(0.20),  # 0.80 headroom, known
        capacity_as_of=NOW,
        max_turns=10,
        turns_spent=9,  # 0.10 headroom, known and tighter
    )
    assert projection.binding.known is True
    assert projection.binding.source == "turns"
    assert projection.binding.fraction == pytest.approx(0.1)


def test_f5_all_unknown_yields_an_unknown_binding() -> None:
    projection = _forecast(available=AVAILABLE_UNKNOWN)
    assert projection.known is False


# --- the policy switch -------------------------------------------------------


def test_the_policy_is_off_by_default() -> None:
    """A predictive stop shipped without data to tune it is a guess applied to
    every run. The first release only measures."""
    assert WindDownPolicy().enabled is False
    projection = _forecast(available=available_at(0.99), capacity_as_of=NOW)
    assert should_wind_down(projection, WindDownPolicy(), turns_spent=5) is None


def test_a_dollar_budget_running_out_winds_down_on_the_turn_reserve() -> None:
    projection = _forecast(
        available=AVAILABLE_UNKNOWN,
        max_dollars=10.0,
        dollars_spent=9.5,
        observed=BurnRate(turns=10, elapsed_seconds=600.0, dollars=9.5),
    )
    assert projection.turns_until_exhaustion is not None
    assert projection.turns_until_exhaustion < 1.0
    assert should_wind_down(projection, ON, turns_spent=10) is not None


def test_plenty_of_headroom_does_not_wind_down() -> None:
    projection = _forecast(
        available=available_at(0.10),
        capacity_as_of=NOW,
        max_turns=100,
        turns_spent=5,
    )
    assert should_wind_down(projection, ON, turns_spent=5) is None


# --- remaining branches ------------------------------------------------------


def test_burn_rate_with_no_turns_yet_reports_unknown_cost_per_turn() -> None:
    """Dividing by zero turns would be a fabricated number, not a projection."""
    assert BurnRate(turns=0, elapsed_seconds=0.0, dollars=0.0).dollars_per_turn is None
    assert BurnRate(turns=4, elapsed_seconds=40.0, dollars=2.0).dollars_per_turn == 0.5


def test_a_vendor_reset_instant_becomes_seconds_until_reset() -> None:
    """The vendor reports resets_at while still allowing traffic; before this it
    was captured and never consumed."""
    projection = _forecast(
        available=available_at(0.20),
        capacity_as_of=NOW,
        capacity_resets_at=NOW + timedelta(minutes=30),
    )
    assert projection.seconds_until_reset == pytest.approx(1800.0)


def test_no_reset_instant_leaves_seconds_until_reset_unknown() -> None:
    projection = _forecast(available=available_at(0.20), capacity_as_of=NOW)
    assert projection.seconds_until_reset is None


def test_the_turn_reserve_fires_when_headroom_alone_would_not() -> None:
    """Two turns left is a wind-down even at 80% headroom: the reserve exists so
    the handoff artifacts can still be produced."""
    projection = _forecast(
        available=available_at(0.20),
        capacity_as_of=NOW,
        max_turns=10,
        turns_spent=8,
    )
    wind_down = should_wind_down(projection, ON, turns_spent=8)
    assert wind_down is not None
    assert wind_down.reason == "turn_reserve"
