# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://hire.adam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
import hashlib
from datetime import timedelta
from enum import StrEnum
from uuid import UUID


class JobState(StrEnum):
    READY = "ready"
    LEASED = "leased"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    AWAITING_HUMAN = "awaiting_human"
    AWAITING_CAPACITY = "awaiting_capacity"
    CANCELLED = "cancelled"


class FailureClass(StrEnum):
    CAPACITY = "capacity"  # opens the circuit
    ENGINE = "engine"  # opens after 3
    WORK = "work"  # the code is wrong -- circuit untouched
    VIBEY = "vibey"  # our bug -- circuit untouched


def backoff(
    attempt: int,
    *,
    base: timedelta = timedelta(seconds=2),
    cap: timedelta = timedelta(minutes=15),
) -> timedelta:
    if attempt < 0:
        attempt = 0
    capped_attempt = min(attempt, 32)
    multiplier: int = 2**capped_attempt
    delay = base * multiplier
    return min(delay, cap)


def idempotency_key(project_id: UUID, cycle: int, kind: str, subject: str) -> str:
    raw = f"{project_id}:{cycle}:{kind}:{subject}".encode()
    return hashlib.sha256(raw).hexdigest()
