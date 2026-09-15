# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Hypothesis strategies for TurnSignals and related domain values."""

from __future__ import annotations

import dataclasses

from hypothesis import strategies as st

from codexloop.domain.capacity import PlanWindows, RateLimitWindow
from codexloop.domain.error_codes import (
    AUTH_CODES,
    FATAL_CODES,
    QUOTA_CODES,
    THROTTLE_CODES,
    TRANSIENT_CODES,
    WINDOW_CODES,
)
from codexloop.domain.signals import TurnSignals

KNOWN_CODES: frozenset[str] = (
    QUOTA_CODES | AUTH_CODES | WINDOW_CODES | THROTTLE_CODES | TRANSIENT_CODES | FATAL_CODES
)

NON_WAITABLE_CODES: tuple[str, ...] = tuple(sorted(QUOTA_CODES | AUTH_CODES))


def unknown_error_tokens() -> st.SearchStrategy[str | None]:
    """Tokens that are not in the known error-code taxonomy (plus None)."""
    return st.none() | st.text(max_size=64).filter(lambda token: token not in KNOWN_CODES)


def rate_limit_windows() -> st.SearchStrategy[RateLimitWindow]:
    return st.builds(
        RateLimitWindow,
        used_percent=st.none()
        | st.floats(min_value=0.0, max_value=100.0, allow_nan=False, allow_infinity=False),
        window_minutes=st.integers(min_value=1, max_value=20_000),
        resets_at=st.none() | st.datetimes(),
    )


def optional_plan_windows() -> st.SearchStrategy[PlanWindows | None]:
    return st.none() | st.builds(
        PlanWindows,
        primary=st.none() | rate_limit_windows(),
        secondary=st.none() | rate_limit_windows(),
        plan_type=st.none() | st.text(max_size=32),
        limit_reached=st.none() | st.text(max_size=32),
    )


@st.composite
def any_turn_signals(draw: st.DrawFn) -> TurnSignals:
    """Arbitrary TurnSignals, including completion claims and window snapshots."""
    return TurnSignals(
        error_code=draw(st.none() | st.text(max_size=64)),
        error_type=draw(st.none() | st.text(max_size=64)),
        http_status=draw(st.none() | st.integers(min_value=100, max_value=599)),
        retry_after_s=draw(
            st.none()
            | st.floats(min_value=0.0, max_value=86_400.0, allow_nan=False, allow_infinity=False)
        ),
        plan_windows=draw(optional_plan_windows()),
        completed=draw(st.booleans()),
        failed=draw(st.booleans()),
        final_message=draw(st.none() | st.text(max_size=64)),
        structured_output=None,
        usage=None,
        exit_code=draw(st.none() | st.integers(min_value=-255, max_value=255)),
        stderr_tail=draw(st.none() | st.text(max_size=64)),
    )


@st.composite
def quota_or_auth_turn_signals(draw: st.DrawFn) -> TurnSignals:
    """TurnSignals whose error.code and/or error.type is a QUOTA or AUTH token.

    The other field may be anything — including a waitable taxonomy code — so
    the property actually enforces that a billing/auth marker cannot be
    classified as waitable.
    """
    token = draw(st.sampled_from(NON_WAITABLE_CODES))
    place = draw(st.sampled_from(("code", "type", "both")))
    other = draw(st.none() | st.sampled_from(sorted(KNOWN_CODES)) | st.text(max_size=32))
    base = draw(any_turn_signals())
    return dataclasses.replace(
        base,
        error_code=token if place in ("code", "both") else other,
        error_type=token if place in ("type", "both") else other,
    )


@st.composite
def unrecognised_429_turn_signals(draw: st.DrawFn) -> TurnSignals:
    """HTTP 429 with a code/type outside the known taxonomy."""
    base = draw(any_turn_signals())
    return dataclasses.replace(
        base,
        http_status=429,
        error_code=draw(unknown_error_tokens()),
        error_type=draw(unknown_error_tokens()),
    )
