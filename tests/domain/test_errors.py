# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://hire.adam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
from vibey.domain.errors import (
    BudgetExceeded,
    EscalationExhausted,
    HandoffRejected,
    IllegalTransitionError,
    InvalidPhaseError,
    InvalidSpecError,
    NoEligibleEngine,
    VibeyError,
)


def test_vibey_error_is_an_exception() -> None:
    assert issubclass(VibeyError, Exception)


def test_error_hierarchy_all_descend_from_vibey_error() -> None:
    for exc_type in (
        InvalidPhaseError,
        IllegalTransitionError,
        NoEligibleEngine,
        EscalationExhausted,
        HandoffRejected,
        InvalidSpecError,
        BudgetExceeded,
    ):
        assert issubclass(exc_type, VibeyError)


def test_escalation_exhausted_carries_the_attempt_number() -> None:
    error = EscalationExhausted(7)

    assert error.attempt == 7
    assert "7" in str(error)


def test_handoff_rejected_carries_the_gate_result() -> None:
    class _FakeGateResult:
        violations = ("v1", "v2")

    result = _FakeGateResult()
    error = HandoffRejected(result)  # type: ignore[arg-type]

    assert error.result is result
    assert "2 violation" in str(error)
