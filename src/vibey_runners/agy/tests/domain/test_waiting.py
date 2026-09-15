# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from datetime import UTC, datetime, timedelta
from zoneinfo import ZoneInfo

import pytest
from hypothesis import given
from hypothesis import strategies as st

from agyloop.domain.capacity import Available, CreditsExhausted, TransientThrottle, WindowExhausted
from agyloop.domain.quota import next_pt_midnight
from agyloop.domain.waiting import (
    AdaptiveWaitPolicy,
    WaitPolicyConfig,
    next_pacific_midnight,
    next_probe_instant,
    wait_exceeded,
)

PACIFIC = ZoneInfo("America/Los_Angeles")
NOW = datetime(2026, 8, 9, 12, 0, tzinfo=UTC)


def test_next_pacific_midnight_is_alias_of_next_pt_midnight() -> None:
    now = datetime(2026, 8, 13, 18, 0, tzinfo=UTC)
    assert next_pacific_midnight(now) == next_pt_midnight(now)


def test_next_pacific_midnight_from_afternoon_utc() -> None:
    now = datetime(2026, 8, 13, 18, 0, tzinfo=UTC)
    reset = next_pacific_midnight(now)
    pacific = reset.astimezone(PACIFIC)
    assert pacific.hour == 0
    assert pacific.minute == 0
    assert pacific.second == 0
    assert pacific.date().isoformat() == "2026-08-14"


def test_next_pacific_midnight_treats_naive_as_utc() -> None:
    naive = datetime(2026, 8, 13, 18, 0)
    aware = datetime(2026, 8, 13, 18, 0, tzinfo=UTC)
    assert next_pacific_midnight(naive) == next_pacific_midnight(aware)


def test_next_pacific_midnight_across_spring_forward() -> None:
    # US DST 2026 starts 2026-03-08 02:00 PST → 03:00 PDT.
    before = datetime(2026, 3, 7, 23, 30, tzinfo=PACIFIC)
    reset = next_pacific_midnight(before)
    assert reset.astimezone(PACIFIC).isoformat() == "2026-03-08T00:00:00-08:00"

    after = datetime(2026, 3, 8, 12, 0, tzinfo=PACIFIC)
    reset_after = next_pacific_midnight(after)
    assert reset_after.astimezone(PACIFIC).isoformat() == "2026-03-09T00:00:00-07:00"


def test_next_pacific_midnight_across_fall_back() -> None:
    # US DST 2026 ends 2026-11-01 02:00 PDT → 01:00 PST.
    before = datetime(2026, 10, 31, 23, 30, tzinfo=PACIFIC)
    reset = next_pacific_midnight(before)
    assert reset.astimezone(PACIFIC).isoformat() == "2026-11-01T00:00:00-07:00"

    after = datetime(2026, 11, 1, 12, 0, tzinfo=PACIFIC)
    reset_after = next_pacific_midnight(after)
    assert reset_after.astimezone(PACIFIC).isoformat() == "2026-11-02T00:00:00-08:00"


def test_exact_pacific_midnight_advances_to_following_day() -> None:
    midnight = datetime(2026, 8, 13, 0, 0, tzinfo=PACIFIC)
    reset = next_pacific_midnight(midnight)
    assert reset.astimezone(PACIFIC).isoformat() == "2026-08-14T00:00:00-07:00"


# --- AdaptiveWaitPolicy / next_probe_instant ---


def test_config_rejects_nonpositive_credits_interval() -> None:
    with pytest.raises(ValueError):
        WaitPolicyConfig(credits_probe_interval=timedelta(0))


def test_config_rejects_ceiling_below_interval() -> None:
    with pytest.raises(ValueError):
        WaitPolicyConfig(
            credits_probe_interval=timedelta(seconds=100),
            credits_probe_ceiling=timedelta(seconds=50),
        )


def test_config_rejects_backoff_below_one() -> None:
    with pytest.raises(ValueError):
        WaitPolicyConfig(credits_backoff_factor=0.5)


def test_config_rejects_nonpositive_window_interval() -> None:
    with pytest.raises(ValueError):
        WaitPolicyConfig(window_probe_interval=timedelta(0))


def test_credits_exhausted_probes_soon_first_time() -> None:
    config = WaitPolicyConfig(credits_probe_interval=timedelta(seconds=120))
    at = next_probe_instant(
        CreditsExhausted(), now=NOW, started_waiting_at=NOW, probe_count=0, config=config
    )
    assert at == NOW + timedelta(seconds=120)


def test_credits_exhausted_backs_off_but_caps_at_ceiling() -> None:
    config = WaitPolicyConfig(
        credits_probe_interval=timedelta(seconds=120),
        credits_probe_ceiling=timedelta(seconds=600),
        credits_backoff_factor=2.0,
    )
    at = next_probe_instant(
        CreditsExhausted(), now=NOW, started_waiting_at=NOW, probe_count=10, config=config
    )
    assert at == NOW + timedelta(seconds=600)


def test_credits_exhausted_never_sleeps_to_pacific_midnight() -> None:
    midnight = next_pacific_midnight(NOW)
    at = next_probe_instant(CreditsExhausted(), now=NOW, started_waiting_at=NOW, probe_count=0)
    assert at < midnight
    assert at <= NOW + timedelta(seconds=600)


def test_window_exhausted_with_resets_at_uses_reset_plus_grace_when_sooner() -> None:
    config = WaitPolicyConfig(
        reset_grace=timedelta(seconds=60), window_probe_interval=timedelta(hours=1)
    )
    resets_at = NOW + timedelta(minutes=5)
    at = next_probe_instant(
        WindowExhausted(rate_limit_type="unknown", resets_at=resets_at),
        now=NOW,
        started_waiting_at=NOW,
        probe_count=0,
        config=config,
    )
    assert at == resets_at + timedelta(seconds=60)


def test_window_exhausted_uses_interval_bound_when_reset_is_far_away() -> None:
    """Catches a mid-window top-up: don't sleep blindly to a far-future reset."""
    config = WaitPolicyConfig(window_probe_interval=timedelta(minutes=10))
    resets_at = NOW + timedelta(days=7)
    at = next_probe_instant(
        WindowExhausted(rate_limit_type="unknown", resets_at=resets_at),
        now=NOW,
        started_waiting_at=NOW,
        probe_count=0,
        config=config,
    )
    assert at == NOW + timedelta(minutes=10)


def test_window_exhausted_without_resets_at_falls_back_to_interval() -> None:
    config = WaitPolicyConfig(window_probe_interval=timedelta(minutes=15))
    at = next_probe_instant(
        WindowExhausted(rate_limit_type="unknown", resets_at=None),
        now=NOW,
        started_waiting_at=NOW,
        probe_count=0,
        config=config,
    )
    assert at == NOW + timedelta(minutes=15)


def test_rpd_window_uses_reset_plus_grace_when_sooner_than_interval() -> None:
    config = WaitPolicyConfig(
        reset_grace=timedelta(seconds=60), rpd_probe_interval=timedelta(minutes=15)
    )
    resets_at = NOW + timedelta(minutes=5)
    at = next_probe_instant(
        WindowExhausted(rate_limit_type="rpd", resets_at=resets_at),
        now=NOW,
        started_waiting_at=NOW,
        probe_count=0,
        config=config,
    )
    assert at == resets_at + timedelta(seconds=60)


def test_rpd_window_probes_on_interval_when_midnight_is_far() -> None:
    config = WaitPolicyConfig(rpd_probe_interval=timedelta(minutes=15))
    resets_at = NOW + timedelta(hours=20)
    at = next_probe_instant(
        WindowExhausted(rate_limit_type="rpd", resets_at=resets_at),
        now=NOW,
        started_waiting_at=NOW,
        probe_count=0,
        config=config,
    )
    assert at == NOW + timedelta(minutes=15)


def test_rpd_default_interval_is_fifteen_minutes() -> None:
    resets_at = NOW + timedelta(hours=20)
    at = next_probe_instant(
        WindowExhausted(rate_limit_type="rpd", resets_at=resets_at),
        now=NOW,
        started_waiting_at=NOW,
        probe_count=0,
    )
    assert at == NOW + timedelta(minutes=15)


def test_no_probe_rpd_waits_to_pacific_midnight_not_interval() -> None:
    """--no-probe must sleep to the computed RPD boundary, not poll every 15 min."""
    config = WaitPolicyConfig(no_probe=True, rpd_probe_interval=timedelta(minutes=15))
    resets_at = next_pacific_midnight(NOW)
    at = next_probe_instant(
        WindowExhausted(rate_limit_type="rpd", resets_at=resets_at),
        now=NOW,
        started_waiting_at=NOW,
        probe_count=0,
        config=config,
    )
    assert at == resets_at + config.reset_grace
    assert at - NOW > timedelta(hours=1)


def test_no_probe_credits_still_uses_cadence_not_midnight() -> None:
    config = WaitPolicyConfig(no_probe=True, credits_probe_interval=timedelta(seconds=120))
    midnight = next_pacific_midnight(NOW)
    at = next_probe_instant(
        CreditsExhausted(), now=NOW, started_waiting_at=NOW, probe_count=0, config=config
    )
    assert at == NOW + timedelta(seconds=120)
    assert at < midnight


def test_no_probe_rpm_stays_short_window_not_rpd_midnight() -> None:
    config = WaitPolicyConfig(no_probe=True)
    midnight = next_pacific_midnight(NOW)
    at = next_probe_instant(
        WindowExhausted(rate_limit_type="rpm", resets_at=midnight),
        now=NOW,
        started_waiting_at=NOW,
        probe_count=0,
        config=config,
    )
    assert at <= NOW + timedelta(seconds=60)
    assert at < midnight


def test_rpm_window_uses_short_throttle_cadence_not_rpd_midnight() -> None:
    midnight = next_pacific_midnight(NOW)
    at = next_probe_instant(
        WindowExhausted(rate_limit_type="rpm", resets_at=midnight),
        now=NOW,
        started_waiting_at=NOW,
        probe_count=0,
    )
    assert at <= NOW + timedelta(seconds=60)
    assert at < midnight


def test_tpm_window_uses_short_throttle_cadence_not_rpd_midnight() -> None:
    midnight = next_pacific_midnight(NOW)
    at = next_probe_instant(
        WindowExhausted(rate_limit_type="tpm", resets_at=midnight),
        now=NOW,
        started_waiting_at=NOW,
        probe_count=0,
    )
    assert at <= NOW + timedelta(seconds=60)
    assert at < midnight


def test_transient_throttle_uses_retry_after_when_supplied() -> None:
    at = next_probe_instant(
        TransientThrottle(retry_after=timedelta(seconds=8)),
        now=NOW,
        started_waiting_at=NOW,
        probe_count=0,
    )
    assert at == NOW + timedelta(seconds=8)


def test_transient_throttle_retry_after_clamps_to_ceiling() -> None:
    at = next_probe_instant(
        TransientThrottle(retry_after=timedelta(minutes=5)),
        now=NOW,
        started_waiting_at=NOW,
        probe_count=0,
    )
    assert at == NOW + timedelta(seconds=60)


def test_transient_throttle_exponential_backoff_caps_at_ceiling() -> None:
    at = next_probe_instant(TransientThrottle(), now=NOW, started_waiting_at=NOW, probe_count=10)
    assert at == NOW + timedelta(seconds=60)


def test_adaptive_wait_policy_delegates_to_next_probe_instant() -> None:
    policy = AdaptiveWaitPolicy()
    state = CreditsExhausted()
    assert policy.next_probe_instant(
        state, now=NOW, started_waiting_at=NOW, probe_count=0
    ) == next_probe_instant(state, now=NOW, started_waiting_at=NOW, probe_count=0)
    config = WaitPolicyConfig(max_wait=timedelta(hours=1))
    bounded = AdaptiveWaitPolicy(config)
    assert bounded.wait_exceeded(started_waiting_at=NOW, now=NOW) is False
    assert bounded.wait_exceeded(started_waiting_at=NOW, now=NOW + timedelta(hours=1)) is True


def test_available_state_still_produces_an_instant_not_in_the_past() -> None:
    at = next_probe_instant(Available(), now=NOW, started_waiting_at=NOW, probe_count=0)
    assert at >= NOW


def test_max_wait_clamps_candidate_to_deadline() -> None:
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


def test_max_wait_set_but_candidate_already_within_it_is_unclamped() -> None:
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


def test_wait_exceeded_false_when_max_wait_unset() -> None:
    config = WaitPolicyConfig(max_wait=None)
    assert (
        wait_exceeded(started_waiting_at=NOW, now=NOW + timedelta(days=999), config=config) is False
    )


def test_wait_exceeded_true_past_deadline() -> None:
    config = WaitPolicyConfig(max_wait=timedelta(hours=1))
    assert (
        wait_exceeded(started_waiting_at=NOW, now=NOW + timedelta(hours=2), config=config) is True
    )


def test_wait_exceeded_false_before_deadline() -> None:
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
    probe_count: int, interval_s: int, ceiling_s: int, factor: float
) -> None:
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
def test_property_never_proposes_instant_beyond_max_wait(max_wait_s: int) -> None:
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


def test_config_rejects_nonpositive_rpd_and_throttle() -> None:
    with pytest.raises(ValueError, match="rpd_probe_interval"):
        WaitPolicyConfig(rpd_probe_interval=timedelta(0))
    with pytest.raises(ValueError, match="throttle_probe_interval"):
        WaitPolicyConfig(throttle_probe_interval=timedelta(0))
    with pytest.raises(ValueError, match="throttle_probe_ceiling"):
        WaitPolicyConfig(
            throttle_probe_interval=timedelta(seconds=10),
            throttle_probe_ceiling=timedelta(seconds=1),
        )
    with pytest.raises(ValueError, match="throttle_backoff_factor"):
        WaitPolicyConfig(throttle_backoff_factor=0.5)


def test_rpd_without_resets_at_uses_interval() -> None:
    config = WaitPolicyConfig(rpd_probe_interval=timedelta(minutes=15))
    at = next_probe_instant(
        WindowExhausted(rate_limit_type="rpd", resets_at=None),
        now=NOW,
        started_waiting_at=NOW,
        probe_count=0,
        config=config,
    )
    assert at == NOW + timedelta(minutes=15)


def test_progress_wait_backoff_and_validation() -> None:
    from agyloop.domain.completion import Continue
    from agyloop.domain.loop import decide_progress_delay
    from agyloop.domain.waiting import (
        ProgressWaitConfig,
        is_wait_only_remaining_work,
        next_progress_wait_instant,
    )

    assert is_wait_only_remaining_work(())
    assert is_wait_only_remaining_work(("Wait for E2E suite", "still running flow 1"))
    assert not is_wait_only_remaining_work(("Fix the login button",))

    cfg = ProgressWaitConfig(initial_seconds=30, factor=2.0, ceiling_seconds=300)
    assert (next_progress_wait_instant(now=NOW, streak=0, config=cfg) - NOW).total_seconds() == 30
    assert (next_progress_wait_instant(now=NOW, streak=10, config=cfg) - NOW).total_seconds() == 300
    with pytest.raises(ValueError, match="initial_seconds"):
        ProgressWaitConfig(initial_seconds=0)
    with pytest.raises(ValueError, match="factor"):
        ProgressWaitConfig(factor=0.5)
    with pytest.raises(ValueError, match="ceiling_seconds"):
        ProgressWaitConfig(initial_seconds=60, ceiling_seconds=30)
    with pytest.raises(ValueError, match="streak"):
        next_progress_wait_instant(now=NOW, streak=-1)
    assert (
        decide_progress_delay(
            verdict=Continue(remaining_work=("Waiting for suite",)),
            tree_changed=True,
            now=NOW,
            streak=0,
        )
        is None
    )
    delay = decide_progress_delay(
        verdict=Continue(remaining_work=("Waiting for suite",)),
        tree_changed=False,
        now=NOW,
        streak=0,
    )
    assert delay is not None
    assert (delay.at - NOW).total_seconds() == 30
