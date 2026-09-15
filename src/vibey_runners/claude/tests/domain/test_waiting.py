# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from datetime import datetime, timedelta, timezone

import pytest
from hypothesis import given
from hypothesis import strategies as st

from claudeloop.domain.capacity import Available, CreditsExhausted, WindowExhausted
from claudeloop.domain.waiting import WaitPolicyConfig, next_probe_instant, wait_exceeded

NOW = datetime(2026, 8, 9, 12, 0, tzinfo=timezone.utc)


def test_config_rejects_nonpositive_credits_interval():
    with pytest.raises(ValueError):
        WaitPolicyConfig(credits_probe_interval=timedelta(0))


def test_config_rejects_ceiling_below_interval():
    with pytest.raises(ValueError):
        WaitPolicyConfig(
            credits_probe_interval=timedelta(seconds=100),
            credits_probe_ceiling=timedelta(seconds=50),
        )


def test_config_rejects_backoff_below_one():
    with pytest.raises(ValueError):
        WaitPolicyConfig(credits_backoff_factor=0.5)


def test_config_rejects_nonpositive_window_interval():
    with pytest.raises(ValueError):
        WaitPolicyConfig(window_probe_interval=timedelta(0))


def test_credits_exhausted_probes_soon_first_time():
    config = WaitPolicyConfig(credits_probe_interval=timedelta(seconds=120))
    at = next_probe_instant(
        CreditsExhausted(), now=NOW, started_waiting_at=NOW, probe_count=0, config=config
    )
    assert at == NOW + timedelta(seconds=120)


def test_credits_exhausted_backs_off_but_caps_at_ceiling():
    config = WaitPolicyConfig(
        credits_probe_interval=timedelta(seconds=120),
        credits_probe_ceiling=timedelta(seconds=600),
        credits_backoff_factor=2.0,
    )
    # after several probes, backoff would exceed ceiling
    at = next_probe_instant(
        CreditsExhausted(), now=NOW, started_waiting_at=NOW, probe_count=10, config=config
    )
    assert at == NOW + timedelta(seconds=600)


def test_window_exhausted_with_resets_at_uses_reset_plus_grace_when_sooner():
    config = WaitPolicyConfig(
        reset_grace=timedelta(seconds=60), window_probe_interval=timedelta(hours=1)
    )
    resets_at = NOW + timedelta(minutes=5)
    at = next_probe_instant(
        WindowExhausted(rate_limit_type="five_hour", resets_at=resets_at),
        now=NOW,
        started_waiting_at=NOW,
        probe_count=0,
        config=config,
    )
    assert at == resets_at + timedelta(seconds=60)


def test_window_exhausted_uses_interval_bound_when_reset_is_far_away():
    """Catches a mid-window top-up: don't sleep blindly to a far-future reset."""
    config = WaitPolicyConfig(window_probe_interval=timedelta(minutes=10))
    resets_at = NOW + timedelta(days=7)
    at = next_probe_instant(
        WindowExhausted(rate_limit_type="seven_day", resets_at=resets_at),
        now=NOW,
        started_waiting_at=NOW,
        probe_count=0,
        config=config,
    )
    assert at == NOW + timedelta(minutes=10)


def test_window_exhausted_without_resets_at_falls_back_to_interval():
    config = WaitPolicyConfig(window_probe_interval=timedelta(minutes=15))
    at = next_probe_instant(
        WindowExhausted(rate_limit_type="unknown", resets_at=None),
        now=NOW,
        started_waiting_at=NOW,
        probe_count=0,
        config=config,
    )
    assert at == NOW + timedelta(minutes=15)


def test_available_state_still_produces_an_instant_not_in_the_past():
    # classify() should never hand Available to the waiting policy in practice, but
    # the function must still behave safely (no crash, no past instant) if it does.
    at = next_probe_instant(Available(), now=NOW, started_waiting_at=NOW, probe_count=0)
    assert at >= NOW


def test_max_wait_clamps_candidate_to_deadline():
    config = WaitPolicyConfig(
        window_probe_interval=timedelta(hours=1), max_wait=timedelta(minutes=5)
    )
    at = next_probe_instant(
        WindowExhausted(rate_limit_type="unknown"),
        now=NOW,
        started_waiting_at=NOW,
        probe_count=0,
        config=config,
    )
    assert at == NOW + timedelta(minutes=5)


def test_max_wait_set_but_candidate_already_within_it_is_unclamped():
    """The complementary case to test_max_wait_clamps_candidate_to_deadline:
    max_wait is configured, but the computed candidate already falls inside
    it, so the clamp's `if candidate > deadline` branch must NOT fire."""
    config = WaitPolicyConfig(
        window_probe_interval=timedelta(minutes=5), max_wait=timedelta(hours=1)
    )
    at = next_probe_instant(
        WindowExhausted(rate_limit_type="unknown"),
        now=NOW,
        started_waiting_at=NOW,
        probe_count=0,
        config=config,
    )
    assert at == NOW + timedelta(minutes=5)


def test_wait_exceeded_false_when_max_wait_unset():
    config = WaitPolicyConfig(max_wait=None)
    assert (
        wait_exceeded(started_waiting_at=NOW, now=NOW + timedelta(days=999), config=config) is False
    )


def test_wait_exceeded_true_past_deadline():
    config = WaitPolicyConfig(max_wait=timedelta(hours=1))
    assert (
        wait_exceeded(started_waiting_at=NOW, now=NOW + timedelta(hours=2), config=config) is True
    )


def test_wait_exceeded_false_before_deadline():
    config = WaitPolicyConfig(max_wait=timedelta(hours=1))
    assert (
        wait_exceeded(started_waiting_at=NOW, now=NOW + timedelta(minutes=30), config=config)
        is False
    )


@given(
    probe_count=st.integers(min_value=0, max_value=50),
    interval_s=st.integers(min_value=1, max_value=3600),
    ceiling_s=st.integers(min_value=1, max_value=36000),
    factor=st.floats(min_value=1.0, max_value=3.0, allow_nan=False, allow_infinity=False),
)
def test_property_credits_probe_never_in_the_past_and_never_exceeds_ceiling(
    probe_count, interval_s, ceiling_s, factor
):
    interval = timedelta(seconds=interval_s)
    ceiling = timedelta(seconds=max(interval_s, ceiling_s))
    config = WaitPolicyConfig(
        credits_probe_interval=interval,
        credits_probe_ceiling=ceiling,
        credits_backoff_factor=factor,
    )
    at = next_probe_instant(
        CreditsExhausted(), now=NOW, started_waiting_at=NOW, probe_count=probe_count, config=config
    )
    assert at >= NOW
    assert at <= NOW + ceiling


@given(max_wait_s=st.integers(min_value=1, max_value=86400))
def test_property_never_proposes_instant_beyond_max_wait(max_wait_s):
    config = WaitPolicyConfig(
        max_wait=timedelta(seconds=max_wait_s), window_probe_interval=timedelta(days=30)
    )
    at = next_probe_instant(
        WindowExhausted(rate_limit_type="unknown"),
        now=NOW,
        started_waiting_at=NOW,
        probe_count=0,
        config=config,
    )
    assert at <= NOW + timedelta(seconds=max_wait_s)
