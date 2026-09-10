# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

from datetime import UTC, datetime, timedelta

import pytest
from hypothesis import assume, given, settings
from hypothesis import strategies as st

from cursorloop.domain.capacity import Available, CreditsExhausted, WindowExhausted
from cursorloop.domain.waiting import (
    DEFAULT_PROGRESS_WAIT_CONFIG,
    ProgressWaitConfig,
    WaitPolicyConfig,
    is_wait_only_remaining_work,
    next_probe_instant,
    next_progress_wait_instant,
    wait_exceeded,
)
from cursorloop.domain.waiting import (
    DEFAULT_WAIT_POLICY_CONFIG as CFG,
)

NOW = datetime(2026, 8, 13, 12, 0, 0, tzinfo=UTC)


def test_credits_probe_uses_the_bounded_cadence_not_a_deadline() -> None:
    at = next_probe_instant(
        CreditsExhausted(), now=NOW, started_waiting_at=NOW, probe_count=0, config=CFG
    )
    assert at == NOW + CFG.credits_probe_interval


def test_credits_backoff_is_clamped_to_the_ceiling() -> None:
    at = next_probe_instant(
        CreditsExhausted(), now=NOW, started_waiting_at=NOW, probe_count=50, config=CFG
    )
    assert at == NOW + CFG.credits_probe_ceiling


@settings(max_examples=300)
@given(probe_count=st.integers(min_value=0, max_value=10_000))
def test_credits_backoff_never_overflows_timedelta(probe_count: int) -> None:
    """Regression property inherited from the blueprint: computing
    interval * factor**probe_count and only THEN clamping overflows
    timedelta's magnitude limit at realistic probe counts. Clamp in float
    seconds BEFORE constructing the timedelta."""
    at = next_probe_instant(
        CreditsExhausted(), now=NOW, started_waiting_at=NOW, probe_count=probe_count, config=CFG
    )
    assert NOW < at <= NOW + CFG.credits_probe_ceiling


def test_window_probe_is_bounded_by_the_interval_even_for_a_far_reset() -> None:
    """A far-future resets_at must not become a blind sleep: the interval bound
    is what notices an early lift (a spend-cap raise, an admin unblock)."""
    far = NOW + timedelta(days=7)
    at = next_probe_instant(
        WindowExhausted("rate_limit", far),
        now=NOW,
        started_waiting_at=NOW,
        probe_count=0,
        config=CFG,
    )
    assert at == NOW + CFG.window_probe_interval


def test_window_probe_uses_reset_plus_grace_when_it_is_nearer() -> None:
    soon = NOW + timedelta(seconds=30)
    at = next_probe_instant(
        WindowExhausted("rate_limit", soon),
        now=NOW,
        started_waiting_at=NOW,
        probe_count=0,
        config=CFG,
    )
    assert at == soon + CFG.reset_grace


@given(
    elapsed=st.integers(min_value=0, max_value=1_000_000),
    probe_count=st.integers(min_value=0, max_value=500),
)
def test_probe_instant_is_never_in_the_past_and_never_exceeds_max_wait(
    elapsed: int, probe_count: int
) -> None:
    config = CFG.with_max_wait(timedelta(hours=6))
    started = NOW
    now = NOW + timedelta(seconds=elapsed)
    # Once elapsed exceeds max_wait the two clamps conflict; wait_exceeded is the
    # paired give-up check for that region, so this property holds only while the
    # wait budget remains.
    assume(config.max_wait is not None and now <= started + config.max_wait)
    for state in (CreditsExhausted(), WindowExhausted("rate_limit", None)):
        at = next_probe_instant(
            state, now=now, started_waiting_at=started, probe_count=probe_count, config=config
        )
        assert at >= now
        assert at <= started + config.max_wait  # type: ignore[operator]


def test_wait_exceeded_is_the_paired_give_up_check() -> None:
    config = CFG.with_max_wait(timedelta(minutes=10))
    assert not wait_exceeded(started_waiting_at=NOW, now=NOW + timedelta(minutes=9), config=config)
    assert wait_exceeded(started_waiting_at=NOW, now=NOW + timedelta(minutes=11), config=config)


def test_config_defaults_match_the_policy_table() -> None:
    assert CFG.credits_probe_interval == timedelta(seconds=120)
    assert CFG.credits_probe_ceiling == timedelta(seconds=600)
    assert CFG.credits_backoff_factor == 1.5
    assert CFG.window_probe_interval == timedelta(seconds=300)
    assert CFG.reset_grace == timedelta(seconds=15)
    assert CFG.max_wait is None


def test_config_rejects_nonpositive_credits_interval() -> None:
    with pytest.raises(ValueError, match="credits_probe_interval"):
        WaitPolicyConfig(credits_probe_interval=timedelta(0))


def test_config_rejects_ceiling_below_interval() -> None:
    with pytest.raises(ValueError, match="credits_probe_ceiling"):
        WaitPolicyConfig(
            credits_probe_interval=timedelta(seconds=100),
            credits_probe_ceiling=timedelta(seconds=50),
        )


def test_config_rejects_backoff_below_one() -> None:
    with pytest.raises(ValueError, match="credits_backoff_factor"):
        WaitPolicyConfig(credits_backoff_factor=0.5)


def test_config_rejects_nonpositive_window_interval() -> None:
    with pytest.raises(ValueError, match="window_probe_interval"):
        WaitPolicyConfig(window_probe_interval=timedelta(0))


def test_with_max_wait_returns_a_new_config_leaving_the_original_untouched() -> None:
    updated = CFG.with_max_wait(timedelta(hours=6))
    assert CFG.max_wait is None
    assert updated.max_wait == timedelta(hours=6)
    assert updated.credits_probe_interval == CFG.credits_probe_interval


def test_window_without_resets_at_uses_the_interval() -> None:
    at = next_probe_instant(
        WindowExhausted("rate_limit", None),
        now=NOW,
        started_waiting_at=NOW,
        probe_count=0,
        config=CFG,
    )
    assert at == NOW + CFG.window_probe_interval


def test_available_state_still_produces_an_instant_not_in_the_past() -> None:
    at = next_probe_instant(Available(), now=NOW, started_waiting_at=NOW, probe_count=0)
    assert at >= NOW


def test_past_reset_is_clamped_to_now_not_a_busy_spin() -> None:
    past = NOW - timedelta(seconds=60)
    at = next_probe_instant(
        WindowExhausted("rate_limit", past),
        now=NOW,
        started_waiting_at=NOW,
        probe_count=0,
        config=CFG,
    )
    assert at >= NOW


def test_max_wait_clamps_a_far_candidate_to_the_deadline() -> None:
    config = CFG.with_max_wait(timedelta(minutes=5))
    at = next_probe_instant(
        WindowExhausted("rate_limit", None),
        now=NOW,
        started_waiting_at=NOW,
        probe_count=0,
        config=config,
    )
    assert at == NOW + timedelta(minutes=5)


def test_max_wait_does_not_clamp_a_candidate_already_inside_the_budget() -> None:
    config = CFG.with_max_wait(timedelta(hours=1))
    at = next_probe_instant(
        WindowExhausted("rate_limit", None),
        now=NOW,
        started_waiting_at=NOW,
        probe_count=0,
        config=config,
    )
    assert at == NOW + CFG.window_probe_interval


def test_wait_exceeded_is_false_when_max_wait_is_unset() -> None:
    assert wait_exceeded(started_waiting_at=NOW, now=NOW + timedelta(days=999), config=CFG) is False


def test_wait_exceeded_is_true_at_the_exact_deadline() -> None:
    config = CFG.with_max_wait(timedelta(minutes=10))
    assert wait_exceeded(started_waiting_at=NOW, now=NOW + timedelta(minutes=10), config=config)


def test_credits_backoff_grows_before_the_ceiling() -> None:
    at = next_probe_instant(
        CreditsExhausted(), now=NOW, started_waiting_at=NOW, probe_count=1, config=CFG
    )
    expected = CFG.credits_probe_interval.total_seconds() * CFG.credits_backoff_factor
    assert at == NOW + timedelta(seconds=expected)


def test_credits_backoff_with_factor_one_stays_at_the_interval() -> None:
    config = WaitPolicyConfig(credits_backoff_factor=1.0)
    at = next_probe_instant(
        CreditsExhausted(), now=NOW, started_waiting_at=NOW, probe_count=10, config=config
    )
    assert at == NOW + config.credits_probe_interval


def test_probe_instant_is_never_in_the_past_once_max_wait_has_elapsed() -> None:
    config = CFG.with_max_wait(timedelta(minutes=1))
    started = NOW - timedelta(hours=1)
    at = next_probe_instant(
        CreditsExhausted(), now=NOW, started_waiting_at=started, probe_count=0, config=config
    )
    assert at >= NOW


def test_wait_only_heuristic_treats_empty_and_wait_language_as_wait_only() -> None:
    assert is_wait_only_remaining_work(())
    assert is_wait_only_remaining_work(("Wait for E2E suite", "still running flow 1"))
    assert is_wait_only_remaining_work(("pending review", "poll the queue"))
    assert is_wait_only_remaining_work(("sleep until green", "in-progress deploy"))
    assert is_wait_only_remaining_work(("in progress build",))
    assert not is_wait_only_remaining_work(("Fix the login button",))
    assert not is_wait_only_remaining_work(("Wait for suite", "Fix the login button"))


def test_progress_wait_backoff_clamps_to_the_ceiling() -> None:
    cfg = ProgressWaitConfig(initial_seconds=30, factor=2.0, ceiling_seconds=300)
    at0 = next_progress_wait_instant(now=NOW, streak=0, config=cfg)
    at10 = next_progress_wait_instant(now=NOW, streak=10, config=cfg)
    assert (at0 - NOW).total_seconds() == 30
    assert (at10 - NOW).total_seconds() == 300


def test_progress_wait_default_config_starts_at_thirty_seconds() -> None:
    at = next_progress_wait_instant(now=NOW, streak=0)
    assert at == NOW + timedelta(seconds=DEFAULT_PROGRESS_WAIT_CONFIG.initial_seconds)


@pytest.mark.parametrize(
    ("kwargs", "match"),
    [
        ({"initial_seconds": 0}, "initial_seconds"),
        ({"factor": 0.5}, "factor"),
        ({"initial_seconds": 60, "ceiling_seconds": 30}, "ceiling_seconds"),
    ],
)
def test_progress_wait_config_rejects_invalid(kwargs: dict[str, float], match: str) -> None:
    with pytest.raises(ValueError, match=match):
        ProgressWaitConfig(**kwargs)


def test_next_progress_wait_rejects_negative_streak() -> None:
    with pytest.raises(ValueError, match="streak"):
        next_progress_wait_instant(now=NOW, streak=-1)
