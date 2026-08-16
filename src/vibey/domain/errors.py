from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from vibey.domain.handoff import GateResult


class VibeyError(Exception):
    """Base class for all vibey domain errors."""


class InvalidPhaseError(VibeyError):
    """A PhaseState was constructed with invalid fields."""


class IllegalTransitionError(VibeyError):
    """A phase transition was attempted that evaluate_transition denies."""


class NoEligibleEngine(VibeyError):
    """Rotation was asked to select from a candidate set with no positive weight."""


class EscalationExhausted(VibeyError):
    """The build escalation ladder has no rung left for this attempt."""

    def __init__(self, attempt: int) -> None:
        self.attempt = attempt
        super().__init__(f"escalation ladder exhausted at attempt {attempt}")


class HandoffRejected(VibeyError):
    """The no-loss gate denied a handoff after exhausting its escalation path."""

    def __init__(self, result: "GateResult") -> None:
        self.result = result
        super().__init__(f"handoff rejected: {len(result.violations)} violation(s)")


class InvalidSpecError(VibeyError):
    """A DesignSpec failed its buildability checks."""


class BudgetExceeded(VibeyError):
    """A spend would exceed the project's budget caps."""
