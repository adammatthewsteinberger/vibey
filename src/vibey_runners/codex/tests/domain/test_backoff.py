# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Backoff: classic exponential with injected jitter."""

from __future__ import annotations

from datetime import timedelta

from hypothesis import given
from hypothesis import strategies as st

from codexloop.domain.backoff import backoff

POSITIVE_SECONDS = st.floats(
    min_value=0.0, max_value=3_600.0, allow_nan=False, allow_infinity=False
)
JITTER = st.floats(min_value=0.0, max_value=2.0, allow_nan=False, allow_infinity=False)
ATTEMPTS = st.integers(min_value=0, max_value=30)
UNIT = st.floats(min_value=0.0, max_value=1.0, allow_nan=False, allow_infinity=False)
BACKOFF_GIVEN = given(
    attempt=ATTEMPTS,
    base_s=POSITIVE_SECONDS,
    ceiling_s=POSITIVE_SECONDS,
    jitter_ratio=JITTER,
    r=UNIT,
)


def _td(seconds: float) -> timedelta:
    return timedelta(seconds=seconds)


def _delay(
    attempt: int, base_s: float, ceiling_s: float, jitter_ratio: float, r: float
) -> timedelta:
    return backoff(
        attempt,
        base=_td(base_s),
        ceiling=_td(ceiling_s),
        jitter_ratio=jitter_ratio,
        rand=lambda: r,
    )


@BACKOFF_GIVEN
def test_backoff_never_exceeds_ceiling(
    attempt: int, base_s: float, ceiling_s: float, jitter_ratio: float, r: float
) -> None:
    assert _delay(attempt, base_s, ceiling_s, jitter_ratio, r) <= _td(ceiling_s)


@BACKOFF_GIVEN
def test_backoff_never_negative(
    attempt: int, base_s: float, ceiling_s: float, jitter_ratio: float, r: float
) -> None:
    assert _delay(attempt, base_s, ceiling_s, jitter_ratio, r) >= timedelta(0)


@BACKOFF_GIVEN
def test_backoff_monotonic_non_decreasing_in_attempt_for_fixed_rand(
    attempt: int, base_s: float, ceiling_s: float, jitter_ratio: float, r: float
) -> None:
    earlier = _delay(attempt, base_s, ceiling_s, jitter_ratio, r)
    later = _delay(attempt + 1, base_s, ceiling_s, jitter_ratio, r)
    assert later >= earlier


@BACKOFF_GIVEN
def test_backoff_deterministic_for_a_fixed_rand(
    attempt: int, base_s: float, ceiling_s: float, jitter_ratio: float, r: float
) -> None:
    first = _delay(attempt, base_s, ceiling_s, jitter_ratio, r)
    second = _delay(attempt, base_s, ceiling_s, jitter_ratio, r)
    assert first == second


def test_backoff_attempt_zero_without_jitter_equals_base() -> None:
    delay = backoff(
        0,
        base=_td(1.5),
        ceiling=_td(60.0),
        jitter_ratio=0.0,
        rand=lambda: 0.5,
    )
    assert delay == _td(1.5)


def test_backoff_doubles_each_attempt_until_ceiling() -> None:
    assert _delay(0, 1.0, 60.0, 0.0, 0.5) == _td(1.0)
    assert _delay(1, 1.0, 60.0, 0.0, 0.5) == _td(2.0)
    assert _delay(5, 1.0, 60.0, 0.0, 0.5) == _td(32.0)
    assert _delay(6, 1.0, 60.0, 0.0, 0.5) == _td(60.0)
    assert _delay(20, 1.0, 60.0, 0.0, 0.5) == _td(60.0)


def test_backoff_jitter_maps_rand_zero_to_low_factor() -> None:
    delay = backoff(
        0,
        base=_td(10.0),
        ceiling=_td(60.0),
        jitter_ratio=0.1,
        rand=lambda: 0.0,
    )
    assert delay == _td(9.0)


def test_backoff_jitter_maps_rand_one_to_high_factor_then_clamps_to_ceiling() -> None:
    delay = backoff(
        0,
        base=_td(10.0),
        ceiling=_td(10.0),
        jitter_ratio=0.5,
        rand=lambda: 1.0,
    )
    assert delay == _td(10.0)


def test_backoff_clamps_negative_jitter_to_zero() -> None:
    delay = backoff(
        0,
        base=_td(10.0),
        ceiling=_td(60.0),
        jitter_ratio=2.0,
        rand=lambda: 0.0,
    )
    assert delay == timedelta(0)


def test_backoff_huge_attempt_still_respects_ceiling() -> None:
    delay = backoff(
        10_000,
        base=_td(1.0),
        ceiling=_td(60.0),
        jitter_ratio=0.0,
        rand=lambda: 0.5,
    )
    assert delay == _td(60.0)
