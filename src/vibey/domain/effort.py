# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://hire.adam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
from collections.abc import Mapping, Sequence
from enum import IntEnum

from vibey.domain.errors import EscalationExhausted
from vibey.domain.phase import Phase
from vibey.domain.review import FindingRef, Severity


class Effort(IntEnum):
    TRIVIAL = 0
    LOW = 1
    STANDARD = 2
    HIGH = 3
    MAX = 4


PHASE_BASE_EFFORT: Mapping[Phase, Effort] = {
    Phase.DESIGN: Effort.HIGH,
    Phase.VISUAL_DESIGN: Effort.HIGH,
    Phase.BUILD: Effort.LOW,
    Phase.REVIEW: Effort.HIGH,
    Phase.DEPLOY_DESIGN: Effort.HIGH,
    Phase.DEPLOY_EXECUTE: Effort.LOW,
    Phase.DEPLOY_REVIEW: Effort.HIGH,
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


def triage_required_effort(findings: Sequence[FindingRef]) -> Effort:
    """Calculates required execution effort for a set of triaged findings.

    Critical findings unconditionally demand MAX effort.
    """
    if any(f.severity is Severity.CRITICAL for f in findings):
        return Effort.MAX
    if any(f.severity is Severity.HIGH for f in findings):
        return Effort.HIGH
    if any(f.severity is Severity.MEDIUM for f in findings):
        return Effort.STANDARD
    return Effort.LOW
