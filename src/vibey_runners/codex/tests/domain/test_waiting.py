# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Adaptive wait policy: next probe instant per capacity state."""

from __future__ import annotations

import dataclasses
from datetime import UTC, datetime, timedelta

from hypothesis import given
from hypothesis import strategies as st

from codexloop.domain.capacity import (
    AuthFailed,
    Available,
    CapacityState,
    QuotaExhausted,
    ThrottleExhausted,
    TransientBackendError,
    WindowExhausted,
)
from codexloop.domain.waiting import AdaptiveWaitPolicy, WaitConfig

NOW = datetime(2026, 8, 13, 12, 0, tzinfo=UTC)
FAR_DEADLINE = NOW + timedelta(hours=6)
QUOTA = QuotaExhausted(reason="insufficient_quota")
AUTH = AuthFailed(reason="invalid_api_key")

ZERO_JITTER = WaitConfig(jitter_ratio=0.0)
POLICY = AdaptiveWaitPolicy(ZERO_JITTER, rand=lambda: 0.5)


def _next(
    state: CapacityState,
    *,
    now: datetime = NOW,
    attempt: int = 0,
    deadline: datetime = FAR_DEADLINE,
    policy: AdaptiveWaitPolicy = POLICY,
) -> datetime:
    return policy.next_probe_at(state, now, attempt, deadline)


def test_wait_config_defaults_match_waiting_table() -> None:
    config = WaitConfig()
    assert config.throttle_ceiling == timedelta(seconds=60)
    assert config.aggressive_ceiling == timedelta(seconds=300)
    assert config.transient_ceiling == timedelta(seconds=120)
    assert config.quota_probe_base == timedelta(seconds=120)
    assert config.quota_probe_ceiling == timedelta(seconds=600)


def test_throttle_without_retry_after_uses_exponential_backoff_ceiling_60s() -> None:
    state = ThrottleExhausted()
    assert _next(state, attempt=0) == NOW + timedelta(seconds=1)
    assert _next(state, attempt=5) == NOW + timedelta(seconds=32)
    assert _next(state, attempt=6) == NOW + timedelta(seconds=60)
    assert _next(state, attempt=10) == NOW + timedelta(seconds=60)


def test_throttle_retry_after_is_a_minimum_plus_jitter_from_backoff() -> None:
    retry = timedelta(seconds=30)
    state = ThrottleExhausted(retry_after=retry)
    assert _next(state, attempt=0) == NOW + retry
    assert _next(state, attempt=5) == NOW + timedelta(seconds=32)


def test_throttle_binding_retry_after_adds_positive_jitter_above_floor() -> None:
    """When Retry-After binds, wait is strictly above it (R2) unless ceiling equals it."""
    retry = timedelta(seconds=30)
    ceiling = timedelta(seconds=60)
    config = WaitConfig(jitter_ratio=0.1, throttle_ceiling=ceiling)
    # rand=1.0 → spread = retry * jitter_ratio * 1.0 = 3s → delay = 33s
    policy = AdaptiveWaitPolicy(config, rand=lambda: 1.0)
    delay = policy.next_probe_at(ThrottleExhausted(retry_after=retry), NOW, 0, FAR_DEADLINE) - NOW
    assert delay > retry
    assert delay >= retry
    assert delay <= ceiling

    at_ceiling = (
        AdaptiveWaitPolicy(
            WaitConfig(jitter_ratio=0.1, throttle_ceiling=retry),
            rand=lambda: 1.0,
        ).next_probe_at(ThrottleExhausted(retry_after=retry), NOW, 0, FAR_DEADLINE)
        - NOW
    )
    assert at_ceiling == retry


def test_throttle_retry_after_longer_than_ceiling_is_capped_at_60s() -> None:
    state = ThrottleExhausted(retry_after=timedelta(seconds=90))
    assert _next(state, attempt=0) == NOW + timedelta(seconds=60)


def test_throttle_aggressive_uses_longer_capped_backoff_ceiling_300s() -> None:
    state = ThrottleExhausted(aggressive=True)
    assert _next(state, attempt=8) == NOW + timedelta(seconds=256)
    assert _next(state, attempt=9) == NOW + timedelta(seconds=300)


def test_throttle_aggressive_without_retry_after_still_exponential() -> None:
    state = ThrottleExhausted(aggressive=True)
    assert _next(state, attempt=0) == NOW + timedelta(seconds=1)


def test_throttle_aggressive_retry_after_is_minimum_with_300s_ceiling() -> None:
    state = ThrottleExhausted(retry_after=timedelta(seconds=90), aggressive=True)
    assert _next(state, attempt=0) == NOW + timedelta(seconds=90)
    huge = ThrottleExhausted(retry_after=timedelta(seconds=400), aggressive=True)
    assert _next(huge, attempt=0) == NOW + timedelta(seconds=300)


def test_transient_backend_error_short_capped_backoff_ceiling_120s() -> None:
    state = TransientBackendError()
    assert _next(state, attempt=0) == NOW + timedelta(seconds=1)
    assert _next(state, attempt=6) == NOW + timedelta(seconds=64)
    assert _next(state, attempt=7) == NOW + timedelta(seconds=120)


def test_transient_retry_after_does_not_extend_past_backoff_cadence() -> None:
    """Transient waits are short capped backoff, not a header-sourced sleep."""
    state = TransientBackendError(retry_after=timedelta(hours=5))
    assert _next(state, attempt=0) == NOW + timedelta(seconds=1)


def test_window_exhausted_with_resets_at_wakes_at_min_reset_plus_grace_or_interval() -> None:
    config = WaitConfig(
        grace=timedelta(seconds=2),
        window_probe_interval=timedelta(seconds=60),
        jitter_ratio=0.0,
    )
    policy = AdaptiveWaitPolicy(config, rand=lambda: 0.5)
    far_reset = NOW + timedelta(hours=5)
    near_reset = NOW + timedelta(seconds=10)
    assert _next(
        WindowExhausted(resets_at=far_reset),
        policy=policy,
    ) == NOW + timedelta(seconds=60)
    assert _next(
        WindowExhausted(resets_at=near_reset),
        policy=policy,
    ) == NOW + timedelta(seconds=12)


def test_window_exhausted_past_reset_keeps_probing_on_interval() -> None:
    config = WaitConfig(
        grace=timedelta(seconds=2),
        window_probe_interval=timedelta(seconds=60),
        jitter_ratio=0.0,
    )
    policy = AdaptiveWaitPolicy(config, rand=lambda: 0.5)
    past = NOW - timedelta(hours=1)
    assert _next(WindowExhausted(resets_at=past), policy=policy) == NOW + timedelta(seconds=60)


def test_window_exhausted_without_resets_at_uses_bounded_cadence_120s_to_600s() -> None:
    state = WindowExhausted(resets_at=None)
    assert _next(state, attempt=0) == NOW + timedelta(seconds=120)
    assert _next(state, attempt=1) == NOW + timedelta(seconds=240)
    assert _next(state, attempt=2) == NOW + timedelta(seconds=480)
    assert _next(state, attempt=3) == NOW + timedelta(seconds=600)


def test_quota_exhausted_uses_same_bounded_cadence_and_has_no_reset_field() -> None:
    names = {f.name for f in dataclasses.fields(QuotaExhausted)}
    assert "resets_at" not in names
    assert "retry_after" not in names
    assert _next(QUOTA, attempt=0) == NOW + timedelta(seconds=120)
    assert _next(QUOTA, attempt=3) == NOW + timedelta(seconds=600)


def test_quota_exhausted_clamps_to_caller_deadline_not_a_billing_reset() -> None:
    deadline = NOW + timedelta(seconds=30)
    assert _next(QUOTA, attempt=0, deadline=deadline) == deadline


def test_available_is_not_a_wait_state_and_returns_now() -> None:
    assert _next(Available()) == NOW


def test_auth_failed_is_terminal_and_returns_deadline() -> None:
    assert _next(AUTH) == FAR_DEADLINE


def test_probe_at_deadline_boundary_returns_exactly_deadline() -> None:
    assert _next(ThrottleExhausted(), deadline=NOW) == NOW
    assert _next(QUOTA, deadline=NOW) == NOW
    assert _next(AUTH, deadline=NOW) == NOW


def test_quota_exhausted_instant_shifts_exactly_with_now_no_hidden_reset() -> None:
    """Guard: QuotaExhausted waits are cadence-only — no hidden reset clock."""
    delta = timedelta(days=365)
    later = NOW + delta
    deadline_a = NOW + timedelta(days=1_000)
    deadline_b = later + timedelta(days=1_000)
    for attempt in (0, 1, 3, 10):
        first = _next(QUOTA, now=NOW, attempt=attempt, deadline=deadline_a)
        second = _next(QUOTA, now=later, attempt=attempt, deadline=deadline_b)
        assert second - first == delta


AWARE = st.datetimes(
    min_value=datetime(2024, 1, 1),
    max_value=datetime(2028, 12, 31),
    timezones=st.just(UTC),
)
ATTEMPTS = st.integers(min_value=0, max_value=20)
HORIZONS = st.timedeltas(min_value=timedelta(0), max_value=timedelta(days=2))
RETRY_AFTERS = st.none() | st.timedeltas(min_value=timedelta(0), max_value=timedelta(seconds=600))
RESETS = st.none() | AWARE

WaitCase = tuple[CapacityState, datetime, int, datetime]


@st.composite
def wait_inputs(draw: st.DrawFn) -> WaitCase:
    now = draw(AWARE)
    deadline = now + draw(HORIZONS)
    attempt = draw(ATTEMPTS)
    kind = draw(
        st.sampled_from(
            (
                "available",
                "throttle",
                "throttle_aggressive",
                "transient",
                "window",
                "quota",
                "auth",
            )
        )
    )
    state: CapacityState
    match kind:
        case "available":
            state = Available()
        case "throttle":
            state = ThrottleExhausted(retry_after=draw(RETRY_AFTERS), aggressive=False)
        case "throttle_aggressive":
            state = ThrottleExhausted(retry_after=draw(RETRY_AFTERS), aggressive=True)
        case "transient":
            state = TransientBackendError(retry_after=draw(RETRY_AFTERS))
        case "window":
            state = WindowExhausted(resets_at=draw(RESETS), window="unknown")
        case "quota":
            state = QUOTA
        case "auth":
            state = AUTH
        case unreachable:
            raise AssertionError(unreachable)
    return state, now, attempt, deadline


@given(wait_inputs())
def test_next_probe_at_never_returns_an_instant_in_the_past(bundle: WaitCase) -> None:
    state, now, attempt, deadline = bundle
    instant = POLICY.next_probe_at(state, now, attempt, deadline)
    assert instant >= now or instant == deadline


@given(wait_inputs())
def test_next_probe_at_never_returns_beyond_deadline(bundle: WaitCase) -> None:
    state, now, attempt, deadline = bundle
    instant = POLICY.next_probe_at(state, now, attempt, deadline)
    assert instant <= deadline
    if now >= deadline:
        assert instant == deadline


@given(wait_inputs().filter(lambda bundle: not isinstance(bundle[0], Available)))
def test_next_probe_at_always_converges_to_deadline(bundle: WaitCase) -> None:
    state, now, attempt, deadline = bundle
    cursor = now
    for step in range(10_000):
        instant = POLICY.next_probe_at(state, cursor, attempt + step, deadline)
        assert cursor <= instant <= deadline or instant == deadline
        if instant >= deadline:
            return
        assert instant > cursor
        cursor = instant
    raise AssertionError("wait policy did not reach deadline in 10000 steps")
