# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Adaptive wait policy — decides the next probe instant, never a blind sleep.

This replaces the `time.sleep(wait_seconds)` calls in the legacy script
(legacy/claude_autoresume.py:505,667) with a policy that can notice a mid-wait
credit top-up or an overage lift instead of blocking until a fixed deadline. See
docs/architecture/decisions/0004-adaptive-waiting-with-probes-not-sleep.md.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import datetime, timedelta

from claudeloop.domain.capacity import CapacityState, CreditsExhausted, WindowExhausted


@dataclass(frozen=True, slots=True)
class WaitPolicyConfig:
    credits_probe_interval: timedelta = timedelta(seconds=120)
    credits_probe_ceiling: timedelta = timedelta(seconds=600)
    credits_backoff_factor: float = 1.5
    window_probe_interval: timedelta = timedelta(seconds=600)
    reset_grace: timedelta = timedelta(seconds=60)
    max_wait: timedelta | None = None

    def __post_init__(self) -> None:
        if self.credits_probe_interval <= timedelta(0):
            raise ValueError("credits_probe_interval must be positive")
        if self.credits_probe_ceiling < self.credits_probe_interval:
            raise ValueError("credits_probe_ceiling must be >= credits_probe_interval")
        if self.credits_backoff_factor < 1.0:
            raise ValueError("credits_backoff_factor must be >= 1.0")
        if self.window_probe_interval <= timedelta(0):
            raise ValueError("window_probe_interval must be positive")


DEFAULT_WAIT_POLICY_CONFIG = WaitPolicyConfig()


def next_probe_instant(
    state: CapacityState,
    *,
    now: datetime,
    started_waiting_at: datetime,
    probe_count: int,
    config: WaitPolicyConfig = DEFAULT_WAIT_POLICY_CONFIG,
) -> datetime:
    """Compute the next instant a probe should run. Never returns an instant in the
    past relative to `now`, and — when `config.max_wait` is set — never proposes an
    instant beyond `started_waiting_at + config.max_wait` (callers must treat that as
    "give up", not "wait longer")."""
    if isinstance(state, CreditsExhausted):
        # Compute the exponent in float seconds and clamp to the ceiling *before*
        # constructing a timedelta — an unclamped exponential can overflow
        # timedelta's max magnitude (~2.7e6 years) well within realistic probe counts.
        ceiling_seconds = config.credits_probe_ceiling.total_seconds()
        interval_seconds = config.credits_probe_interval.total_seconds()
        backoff_seconds = min(
            interval_seconds * (config.credits_backoff_factor**probe_count), ceiling_seconds
        )
        candidate = now + timedelta(seconds=backoff_seconds)
    elif isinstance(state, WindowExhausted) and state.resets_at is not None:
        by_reset = state.resets_at + config.reset_grace
        by_interval = now + config.window_probe_interval
        candidate = min(by_reset, by_interval)
    else:
        candidate = now + config.window_probe_interval

    if candidate < now:  # pragma: no cover — unreachable: all config intervals are
        candidate = now  # validated positive in __post_init__, so every branch above
        # already yields candidate >= now. Kept as a defensive invariant guard.

    if config.max_wait is not None:
        deadline = started_waiting_at + config.max_wait
        if candidate > deadline:
            candidate = deadline

    return candidate


def wait_exceeded(*, started_waiting_at: datetime, now: datetime, config: WaitPolicyConfig) -> bool:
    """Whether the configured max_wait budget has been consumed and the run loop
    should give up rather than schedule another probe."""
    if config.max_wait is None:
        return False
    return now - started_waiting_at >= config.max_wait


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
