# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Adaptive wait policy — next probe instant, never a blind sleep.

Quota-aware: RPM/TPM (and TransientThrottle) use a short bounded backoff;
RPD waits toward Pacific midnight with a 15-minute probe floor (or straight
to the midnight boundary when ``no_probe``); credits use a bounded probe
cadence with no deadline.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta

from agyloop.domain.capacity import (
    CapacityState,
    CreditsExhausted,
    TransientThrottle,
    WindowExhausted,
)
from agyloop.domain.quota import next_pt_midnight

_SHORT_WINDOW_TYPES = frozenset({"rpm", "tpm", "ipm"})


def next_pacific_midnight(now: datetime) -> datetime:
    """Return the next midnight in America/Los_Angeles after ``now``."""
    return next_pt_midnight(now)


@dataclass(frozen=True, slots=True)
class WaitPolicyConfig:
    credits_probe_interval: timedelta = timedelta(seconds=120)
    credits_probe_ceiling: timedelta = timedelta(seconds=600)
    credits_backoff_factor: float = 1.5
    window_probe_interval: timedelta = timedelta(seconds=600)
    rpd_probe_interval: timedelta = timedelta(minutes=15)
    throttle_probe_interval: timedelta = timedelta(seconds=1)
    throttle_probe_ceiling: timedelta = timedelta(seconds=60)
    throttle_backoff_factor: float = 2.0
    reset_grace: timedelta = timedelta(seconds=60)
    max_wait: timedelta | None = None
    no_probe: bool = False

    def __post_init__(self) -> None:
        if self.credits_probe_interval <= timedelta(0):
            raise ValueError("credits_probe_interval must be positive")
        if self.credits_probe_ceiling < self.credits_probe_interval:
            raise ValueError("credits_probe_ceiling must be >= credits_probe_interval")
        if self.credits_backoff_factor < 1.0:
            raise ValueError("credits_backoff_factor must be >= 1.0")
        if self.window_probe_interval <= timedelta(0):
            raise ValueError("window_probe_interval must be positive")
        if self.rpd_probe_interval <= timedelta(0):
            raise ValueError("rpd_probe_interval must be positive")
        if self.throttle_probe_interval <= timedelta(0):
            raise ValueError("throttle_probe_interval must be positive")
        if self.throttle_probe_ceiling < self.throttle_probe_interval:
            raise ValueError("throttle_probe_ceiling must be >= throttle_probe_interval")
        if self.throttle_backoff_factor < 1.0:
            raise ValueError("throttle_backoff_factor must be >= 1.0")


DEFAULT_WAIT_POLICY_CONFIG = WaitPolicyConfig()


def _backoff_from(
    *,
    now: datetime,
    probe_count: int,
    interval: timedelta,
    ceiling: timedelta,
    factor: float,
) -> datetime:
    # Clamp in float seconds before constructing a timedelta — an unclamped
    # exponential can overflow timedelta's max magnitude at high probe counts.
    ceiling_seconds = ceiling.total_seconds()
    interval_seconds = interval.total_seconds()
    backoff_seconds = min(interval_seconds * (factor**probe_count), ceiling_seconds)
    return now + timedelta(seconds=backoff_seconds)


def _throttle_candidate(
    *,
    now: datetime,
    probe_count: int,
    config: WaitPolicyConfig,
    retry_after: timedelta | None = None,
) -> datetime:
    if retry_after is not None:
        ceiling = config.throttle_probe_ceiling
        delay = retry_after if retry_after < ceiling else ceiling
        return now + delay
    return _backoff_from(
        now=now,
        probe_count=probe_count,
        interval=config.throttle_probe_interval,
        ceiling=config.throttle_probe_ceiling,
        factor=config.throttle_backoff_factor,
    )


def _window_candidate(
    state: WindowExhausted,
    *,
    now: datetime,
    probe_count: int,
    config: WaitPolicyConfig,
) -> datetime:
    if state.rate_limit_type in _SHORT_WINDOW_TYPES:
        return _throttle_candidate(now=now, probe_count=probe_count, config=config)
    if state.rate_limit_type == "rpd":
        if config.no_probe and state.resets_at is not None:
            return state.resets_at + config.reset_grace
        by_interval = now + config.rpd_probe_interval
        if state.resets_at is None:
            return by_interval
        return min(state.resets_at + config.reset_grace, by_interval)
    if state.resets_at is not None:
        by_reset = state.resets_at + config.reset_grace
        by_interval = now + config.window_probe_interval
        return min(by_reset, by_interval)
    return now + config.window_probe_interval


def next_probe_instant(
    state: CapacityState,
    *,
    now: datetime,
    started_waiting_at: datetime,
    probe_count: int,
    config: WaitPolicyConfig = DEFAULT_WAIT_POLICY_CONFIG,
) -> datetime:
    """Compute the next instant a probe should run.

    Never returns an instant in the past relative to ``now``. When
    ``config.max_wait`` is set, never proposes an instant beyond
    ``started_waiting_at + config.max_wait``.
    """
    if isinstance(state, CreditsExhausted):
        candidate = _backoff_from(
            now=now,
            probe_count=probe_count,
            interval=config.credits_probe_interval,
            ceiling=config.credits_probe_ceiling,
            factor=config.credits_backoff_factor,
        )
    elif isinstance(state, TransientThrottle):
        candidate = _throttle_candidate(
            now=now,
            probe_count=probe_count,
            config=config,
            retry_after=state.retry_after,
        )
    elif isinstance(state, WindowExhausted):
        candidate = _window_candidate(state, now=now, probe_count=probe_count, config=config)
    else:
        candidate = now + config.window_probe_interval

    if candidate < now:  # pragma: no cover — defensive invariant
        candidate = now

    if config.max_wait is not None:
        deadline = started_waiting_at + config.max_wait
        if candidate > deadline:
            candidate = deadline

    return candidate


def wait_exceeded(*, started_waiting_at: datetime, now: datetime, config: WaitPolicyConfig) -> bool:
    """Whether the configured max_wait budget has been consumed."""
    if config.max_wait is None:
        return False
    return now - started_waiting_at >= config.max_wait


class AdaptiveWaitPolicy:
    """Quota-aware policy: next probe instant, never a single long sleep."""

    def __init__(self, config: WaitPolicyConfig = DEFAULT_WAIT_POLICY_CONFIG) -> None:
        self._config = config

    def next_probe_instant(
        self,
        state: CapacityState,
        *,
        now: datetime,
        started_waiting_at: datetime,
        probe_count: int,
    ) -> datetime:
        return next_probe_instant(
            state,
            now=now,
            started_waiting_at=started_waiting_at,
            probe_count=probe_count,
            config=self._config,
        )

    def wait_exceeded(self, *, started_waiting_at: datetime, now: datetime) -> bool:
        return wait_exceeded(started_waiting_at=started_waiting_at, now=now, config=self._config)


_WAIT_ONLY_RE = re.compile(
    r"(?i)\b(wait|waiting|pending|poll|sleep|in[- ]progress|still running)\b"
)


@dataclass(frozen=True, slots=True)
class ProgressWaitConfig:
    initial_seconds: float = 30.0
    factor: float = 2.0
    ceiling_seconds: float = 300.0

    def __post_init__(self) -> None:
        if self.initial_seconds <= 0:
            raise ValueError("initial_seconds must be positive")
        if self.factor < 1.0:
            raise ValueError("factor must be >= 1.0")
        if self.ceiling_seconds < self.initial_seconds:
            raise ValueError("ceiling_seconds must be >= initial_seconds")


DEFAULT_PROGRESS_WAIT_CONFIG = ProgressWaitConfig()


def is_wait_only_remaining_work(remaining_work: tuple[str, ...]) -> bool:
    """True when every remaining_work item looks like wait/poll language (or empty)."""
    if not remaining_work:
        return True
    return all(_WAIT_ONLY_RE.search(item) is not None for item in remaining_work)


def next_progress_wait_instant(
    *,
    now: datetime,
    streak: int,
    config: ProgressWaitConfig = DEFAULT_PROGRESS_WAIT_CONFIG,
) -> datetime:
    """Exponential backoff between wait-only Continues with an unchanged tree."""
    if streak < 0:
        raise ValueError("streak must be >= 0")
    ceiling = config.ceiling_seconds
    initial = config.initial_seconds
    seconds = min(initial * (config.factor**streak), ceiling)
    return now + timedelta(seconds=seconds)
