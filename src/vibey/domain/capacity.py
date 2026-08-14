"""Inherited from the *loop family, unchanged in spirit and in the one rule
that matters: a credits balance has no clock."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True, slots=True)
class Available:
    pass


@dataclass(frozen=True, slots=True)
class WindowExhausted:
    resets_at: datetime | None = None
    rate_limit_type: str | None = None


@dataclass(frozen=True, slots=True)
class CreditsExhausted:
    can_purchase: bool = True
    # There is deliberately NO resets_at field here, and there never will be.
    # A credits balance has no clock. Only a human top-up changes it.


@dataclass(frozen=True, slots=True)
class AuthenticationFailed:
    detail: str = ""


CapacityState = Available | WindowExhausted | CreditsExhausted | AuthenticationFailed
