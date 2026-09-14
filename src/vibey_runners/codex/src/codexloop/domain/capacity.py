# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Capacity value objects and waitability for plan windows / rate limits."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import assert_never


@dataclass(frozen=True, slots=True)
class RateLimitWindow:
    used_percent: float | None
    window_minutes: int
    resets_at: datetime | None

    @property
    def remaining_percent(self) -> float | None:
        if self.used_percent is None:
            return None
        return max(0.0, min(100.0, 100.0 - self.used_percent))


@dataclass(frozen=True, slots=True)
class PlanWindows:
    primary: RateLimitWindow | None
    secondary: RateLimitWindow | None
    plan_type: str | None
    limit_reached: str | None


@dataclass(frozen=True, slots=True)
class Available:
    plan_windows: PlanWindows | None = None


@dataclass(frozen=True, slots=True)
class ThrottleExhausted:
    retry_after: timedelta | None = None
    aggressive: bool = False


@dataclass(frozen=True, slots=True)
class WindowExhausted:
    resets_at: datetime | None = None
    window: str = "unknown"


@dataclass(frozen=True, slots=True)
class QuotaExhausted:
    reason: str


@dataclass(frozen=True, slots=True)
class AuthFailed:
    reason: str


@dataclass(frozen=True, slots=True)
class TransientBackendError:
    retry_after: timedelta | None = None


CapacityState = (
    Available
    | ThrottleExhausted
    | WindowExhausted
    | QuotaExhausted
    | AuthFailed
    | TransientBackendError
)


def is_waitable(state: CapacityState) -> bool:
    """Return False only for billing walls and auth failures."""
    match state:
        case QuotaExhausted() | AuthFailed():
            return False
        case Available() | ThrottleExhausted() | WindowExhausted() | TransientBackendError():
            return True
        case _:  # pragma: no cover — match is exhaustive over CapacityState
            assert_never(state)
