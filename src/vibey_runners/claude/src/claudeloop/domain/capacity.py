# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Capacity state — whether the account can currently spend a real turn, and why not
if it can't. This is the typed replacement for regex-scraping stream-json for limit
language."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class Available:
    """Capacity exists; a real turn may be spent. `utilization` is informational —
    it reflects an `allowed_warning` signal and must never itself block a turn."""

    utilization: float | None = None


@dataclass(frozen=True, slots=True)
class WindowExhausted:
    """A rate-limit window (five_hour / seven_day / seven_day_opus / seven_day_sonnet /
    overage) has been rejected. `resets_at` is the trusted reset instant when known;
    when None, the caller must fall back to a configured wait interval rather than
    assuming any particular reset time."""

    rate_limit_type: str
    resets_at: datetime | None = None


@dataclass(frozen=True, slots=True)
class CreditsExhausted:
    """No token/time budget will fix this — the account is out of usage credits and
    requires a human to purchase more. There is no reset time by construction: waiting
    for a clock to advance can never resolve this state, only a probe that notices a
    top-up can."""

    can_purchase: bool = True


@dataclass(frozen=True, slots=True)
class AuthenticationFailed:
    """Terminal — credentials are invalid or revoked. Never retryable."""

    detail: str = ""


CapacityState = Available | WindowExhausted | CreditsExhausted | AuthenticationFailed


def is_waitable(state: CapacityState) -> bool:
    """Whether the run loop should ever schedule a wait/probe cycle for this state.
    AuthenticationFailed is the only capacity state that must abort outright."""
    return not isinstance(state, AuthenticationFailed)
