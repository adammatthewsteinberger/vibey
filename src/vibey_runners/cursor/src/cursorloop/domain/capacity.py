# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Capacity states returned by classification and probing."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class Available:
    utilization: float | None = None


@dataclass(frozen=True, slots=True)
class WindowExhausted:
    limit_kind: str
    resets_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class CreditsExhausted:
    """Spend cap or included usage exhausted.

    This type deliberately has no ``resets_at`` field. Billing exhaustion is not
    a time-bounded rate-limit window: topping up or raising the cap is the only
    fix, and sleeping to an invented deadline would re-create the founding bug
    this project replaces. Probe-and-notify is the wait policy, never
    sleep-to-deadline.
    """

    can_purchase: bool = True


@dataclass(frozen=True, slots=True)
class AuthenticationFailed:
    detail: str


CapacityState = Available | WindowExhausted | CreditsExhausted | AuthenticationFailed


def is_waitable(state: CapacityState) -> bool:
    """Return whether the runner may wait or probe for this capacity state."""
    return not isinstance(state, AuthenticationFailed)
