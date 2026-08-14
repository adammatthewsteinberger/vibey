from collections.abc import Mapping
from enum import IntEnum

from vibey.domain.errors import EscalationExhausted
from vibey.domain.phase import Phase


class Effort(IntEnum):
    TRIVIAL = 0
    LOW = 1
    STANDARD = 2
    HIGH = 3
    MAX = 4


PHASE_BASE_EFFORT: Mapping[Phase, Effort] = {
    Phase.DESIGN: Effort.HIGH,
    Phase.BUILD: Effort.LOW,
    Phase.REVIEW: Effort.HIGH,
    Phase.DEPLOY: Effort.LOW,
}

# attempt -> effort, for Phase 2's per-item escalation ladder (1-based attempts)
BUILD_LADDER: tuple[Effort, ...] = (
    Effort.LOW,
    Effort.LOW,
    Effort.STANDARD,
    Effort.STANDARD,
    Effort.HIGH,
    Effort.HIGH,
)
BUILD_LADDER_EXHAUSTED = len(BUILD_LADDER)  # attempt 7 -> human gate


def effort_for_attempt(base: Effort, attempt: int) -> Effort:
    """Phase 2 escalation. Never lowers below base; saturates at HIGH."""
    if attempt <= 0:
        raise ValueError("attempt is 1-based")
    if attempt > BUILD_LADDER_EXHAUSTED:
        raise EscalationExhausted(attempt)
    return max(base, BUILD_LADDER[attempt - 1])


def forces_rotation(previous: Effort, current: Effort) -> bool:
    return current > previous
