# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Capacity state — whether a real turn can be spent, and why not if it cannot.

Five members because Gemini's quota dimensions do not collapse: per-minute
blips, known daily windows, billing walls, auth failures, and ordinary
availability are distinct recovery stories.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import assert_never


@dataclass(frozen=True, slots=True)
class Available:
    """Capacity exists; a real turn may be spent."""

    utilization: float | None = None


@dataclass(frozen=True, slots=True)
class TransientThrottle:
    """Short-horizon overload or per-second/per-minute drain with no known boundary."""

    retry_after: timedelta | None = None
    quota_id: str | None = None


@dataclass(frozen=True, slots=True)
class WindowExhausted:
    """A named quota window (rpm / rpd / tpm / ipm / unknown) has been rejected."""

    rate_limit_type: str
    resets_at: datetime | None = None
    quota_id: str | None = None


@dataclass(frozen=True, slots=True)
class CreditsExhausted:
    """Billing wall — waiting on a clock cannot resolve this.

    There is no ``resets_at`` by construction: a fabricated deadline on a
    credits state would make a billing wall look waitable.
    """

    can_purchase: bool | None = True
    detail: str = ""


@dataclass(frozen=True, slots=True)
class AuthenticationFailed:
    """Terminal — credentials are invalid or revoked. Never retryable."""

    detail: str = ""
    reason: str = ""


CapacityState = (
    Available | TransientThrottle | WindowExhausted | CreditsExhausted | AuthenticationFailed
)


def is_waitable(state: CapacityState) -> bool:
    """Whether the run loop may schedule a wait/probe cycle for this state.

    AuthenticationFailed is the only capacity state that must abort outright.
    CreditsExhausted is still probed (a human may top up) but carries no deadline.
    """
    if isinstance(state, AuthenticationFailed):
        return False
    if isinstance(state, (Available, TransientThrottle, WindowExhausted, CreditsExhausted)):
        return True
    assert_never(state)  # pragma: no cover — CapacityState is a closed union
