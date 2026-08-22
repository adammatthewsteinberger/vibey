# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
import hashlib
from dataclasses import dataclass
from datetime import datetime, timedelta
from enum import StrEnum

from vibey.domain.capacity import (
    Available,
    CapacityState,
    CreditsExhausted,
    WindowExhausted,
)


class CircuitState(StrEnum):
    CLOSED = "closed"
    HALF_OPEN = "half_open"
    OPEN = "open"


@dataclass(frozen=True, slots=True)
class DeadlineProbe:
    at: datetime


@dataclass(frozen=True, slots=True)
class BackoffProbe:
    next_at: datetime
    attempt: int


ProbeSchedule = DeadlineProbe | BackoffProbe


@dataclass(frozen=True, slots=True)
class Circuit:
    state: CircuitState
    capacity: CapacityState
    probe: ProbeSchedule | None
    consecutive_failures: int = 0
    ewma_failure: float = 0.0


def _jitter(*, seed: bytes, spread: timedelta = timedelta(seconds=30)) -> timedelta:
    """Deterministic pseudo-jitter derived from the seed bytes, so the same
    inputs always produce the same schedule (rotation.py's determinism
    property depends on functions like this staying pure)."""
    digest = hashlib.sha256(seed).digest()
    fraction = int.from_bytes(digest[:4], "big") / 0xFFFFFFFF
    return timedelta(seconds=spread.total_seconds() * fraction)


def _backoff(
    attempt: int,
    *,
    base: timedelta = timedelta(seconds=2),
    floor: timedelta = timedelta(0),
    cap: timedelta,
) -> timedelta:
    if attempt < 0:
        attempt = 0
    # Cap the exponent itself, not just the result: 2**attempt as a plain int
    # can outgrow timedelta's internal range long before the value is
    # clamped to `cap`, so an unbounded attempt count must never reach the
    # multiplication uncapped.
    capped_attempt = min(attempt, 32)
    multiplier: int = 2**capped_attempt
    delay = base * multiplier
    if delay < floor:
        delay = floor
    if delay > cap:
        delay = cap
    return delay


def schedule_probe(capacity: CapacityState, *, now: datetime, attempt: int) -> ProbeSchedule | None:
    """The type system carries the rule: CreditsExhausted can only ever
    produce a BackoffProbe, never a DeadlineProbe -- because there is no
    deadline."""
    match capacity:
        case Available():
            return None
        case WindowExhausted(resets_at=dt) if dt is not None:
            seed = f"window:{dt.isoformat()}:{attempt}".encode()
            return DeadlineProbe(at=dt + _jitter(seed=seed))
        case WindowExhausted():
            delay = _backoff(attempt, cap=timedelta(minutes=5))
            return BackoffProbe(next_at=now + delay, attempt=attempt)
        case CreditsExhausted():
            delay = _backoff(attempt, floor=timedelta(minutes=5), cap=timedelta(minutes=30))
            return BackoffProbe(next_at=now + delay, attempt=attempt)
        case _:
            return None  # AuthenticationFailed or unknown -- waiting cannot fix credentials
