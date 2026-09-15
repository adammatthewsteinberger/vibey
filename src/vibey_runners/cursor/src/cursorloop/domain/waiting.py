# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Adaptive wait policy — the next instant to probe, never a duration to sleep.

Credits exhaustion has no reset time, so the policy probes on a bounded
exponential cadence. A window with ``resets_at`` wakes at
``min(resets_at + grace, now + interval)`` so an early lift is noticed.
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, replace
from datetime import datetime, timedelta

from cursorloop.domain.capacity import CapacityState, CreditsExhausted, WindowExhausted


def _capped_exponential_seconds(initial: float, factor: float, count: int, ceiling: float) -> float:
    """Return ``min(initial * factor**count, ceiling)`` without overflowing.

    Computing the power first and clamping after raises ``OverflowError`` (or
    yields ``inf``) at realistic probe counts; compare in log space so the
    ceiling is applied before any ``timedelta`` is constructed.
    """
    if count <= 0 or factor == 1.0:
        return initial
    limit = math.log(ceiling / initial) / math.log(factor)
    if count >= limit:
        return ceiling
    return initial * (factor**count)


@dataclass(frozen=True, slots=True)
class WaitPolicyConfig:
    credits_probe_interval: timedelta = timedelta(seconds=120)
    credits_probe_ceiling: timedelta = timedelta(seconds=600)
    credits_backoff_factor: float = 1.5
    window_probe_interval: timedelta = timedelta(seconds=300)
    reset_grace: timedelta = timedelta(seconds=15)
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

    def with_max_wait(self, max_wait: timedelta) -> WaitPolicyConfig:
        return replace(self, max_wait=max_wait)


DEFAULT_WAIT_POLICY_CONFIG = WaitPolicyConfig()


def next_probe_instant(
    state: CapacityState,
    *,
    now: datetime,
    started_waiting_at: datetime,
    probe_count: int,
    config: WaitPolicyConfig = DEFAULT_WAIT_POLICY_CONFIG,
) -> datetime:
    """Return the next instant a probe should run.

    Never returns an instant in the past relative to ``now``. When
    ``config.max_wait`` is set, never proposes an instant beyond
    ``started_waiting_at + config.max_wait``, except that a deadline already
    in the past is raised to ``now`` so the caller cannot busy-spin.
    """
    if isinstance(state, CreditsExhausted):
        backoff_seconds = _capped_exponential_seconds(
            config.credits_probe_interval.total_seconds(),
            config.credits_backoff_factor,
            probe_count,
            config.credits_probe_ceiling.total_seconds(),
        )
        candidate = now + timedelta(seconds=backoff_seconds)
    elif isinstance(state, WindowExhausted) and state.resets_at is not None:
        by_reset = state.resets_at + config.reset_grace
        by_interval = now + config.window_probe_interval
        candidate = min(by_reset, by_interval)
    else:
        candidate = now + config.window_probe_interval

    if config.max_wait is not None:
        deadline = started_waiting_at + config.max_wait
        if candidate > deadline:
            candidate = deadline

    if candidate < now:
        candidate = now

    return candidate


def wait_exceeded(*, started_waiting_at: datetime, now: datetime, config: WaitPolicyConfig) -> bool:
    """Whether the configured max_wait budget has been consumed."""
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


def is_wait_only_remaining_work(items: tuple[str, ...]) -> bool:
    """True when every remaining-work item looks like wait/poll language (or empty)."""
    if not items:
        return True
    return all(_WAIT_ONLY_RE.search(item) is not None for item in items)


def next_progress_wait_instant(
    *,
    now: datetime,
    streak: int,
    config: ProgressWaitConfig = DEFAULT_PROGRESS_WAIT_CONFIG,
) -> datetime:
    """Exponential backoff between wait-only Continues with an unchanged tree."""
    if streak < 0:
        raise ValueError("streak must be >= 0")
    seconds = _capped_exponential_seconds(
        config.initial_seconds, config.factor, streak, config.ceiling_seconds
    )
    return now + timedelta(seconds=seconds)
