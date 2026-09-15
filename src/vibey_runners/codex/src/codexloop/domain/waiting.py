# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Adaptive wait policy: the next instant to probe, never a blind sleep."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from random import random
from typing import assert_never

from codexloop.domain.backoff import backoff
from codexloop.domain.capacity import (
    AuthFailed,
    Available,
    CapacityState,
    QuotaExhausted,
    ThrottleExhausted,
    TransientBackendError,
    WindowExhausted,
)


@dataclass(frozen=True, slots=True)
class WaitConfig:
    """Cadence knobs for :class:`AdaptiveWaitPolicy`.

    Defaults match the waiting table: throttle 60s, aggressive 300s, transient
    120s, unknown-window / quota probe 120s → 600s.
    """

    grace: timedelta = timedelta(seconds=2)
    window_probe_interval: timedelta = timedelta(seconds=60)
    quota_probe_base: timedelta = timedelta(seconds=120)
    quota_probe_ceiling: timedelta = timedelta(seconds=600)
    throttle_ceiling: timedelta = timedelta(seconds=60)
    aggressive_ceiling: timedelta = timedelta(seconds=300)
    transient_ceiling: timedelta = timedelta(seconds=120)
    jitter_ratio: float = 0.1
    backoff_base: timedelta = timedelta(seconds=1)


class AdaptiveWaitPolicy:
    """Map a capacity state to the next probe instant."""

    def __init__(self, config: WaitConfig, *, rand: Callable[[], float] = random) -> None:
        self._config = config
        self._rand = rand

    def next_probe_at(
        self,
        state: CapacityState,
        now: datetime,
        attempt: int,
        deadline: datetime,
    ) -> datetime:
        match state:
            case Available():
                return now
            case AuthFailed():
                return deadline
            case ThrottleExhausted() as throttle:
                return _clamp(now + self._throttle_delay(throttle, attempt), now, deadline)
            case TransientBackendError():
                delay = self._capped_backoff(attempt, self._config.transient_ceiling)
                return _clamp(now + delay, now, deadline)
            case WindowExhausted() as window:
                return _clamp(self._window_instant(window, now, attempt), now, deadline)
            case QuotaExhausted():
                delay = self._quota_delay(attempt)
                return _clamp(now + delay, now, deadline)
            case _:  # pragma: no cover — match is exhaustive over CapacityState
                assert_never(state)

    def _throttle_delay(self, state: ThrottleExhausted, attempt: int) -> timedelta:
        ceiling = (
            self._config.aggressive_ceiling if state.aggressive else self._config.throttle_ceiling
        )
        delay = self._capped_backoff(attempt, ceiling)
        if state.retry_after is not None:
            # Retry-After is a minimum; add a small random delay so clients do not
            # wake together when the header is the binding wait (R2).
            retry_s = max(state.retry_after.total_seconds(), 0.0)
            spread_s = retry_s * self._config.jitter_ratio * self._rand()
            delay = max(delay, timedelta(seconds=retry_s + spread_s))
        return min(delay, ceiling)

    def _window_instant(self, state: WindowExhausted, now: datetime, attempt: int) -> datetime:
        if state.resets_at is None:
            return now + self._quota_delay(attempt)
        target = state.resets_at + self._config.grace
        interval_wake = now + self._config.window_probe_interval
        if target <= now:
            return interval_wake
        return min(target, interval_wake)

    def _quota_delay(self, attempt: int) -> timedelta:
        return self._capped_backoff(
            attempt,
            self._config.quota_probe_ceiling,
            base=self._config.quota_probe_base,
        )

    def _capped_backoff(
        self,
        attempt: int,
        ceiling: timedelta,
        *,
        base: timedelta | None = None,
    ) -> timedelta:
        return backoff(
            attempt,
            base=self._config.backoff_base if base is None else base,
            ceiling=ceiling,
            jitter_ratio=self._config.jitter_ratio,
            rand=self._rand,
        )


def _clamp(instant: datetime, now: datetime, deadline: datetime) -> datetime:
    return min(deadline, max(now, instant))
