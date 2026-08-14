import pytest
from hypothesis import given
from hypothesis import strategies as st

from vibey.domain.effort import (
    BUILD_LADDER,
    BUILD_LADDER_EXHAUSTED,
    PHASE_BASE_EFFORT,
    Effort,
    effort_for_attempt,
    forces_rotation,
)
from vibey.domain.errors import EscalationExhausted
from vibey.domain.phase import Phase


def test_phase_base_effort_matches_the_users_requirement() -> None:
    assert PHASE_BASE_EFFORT[Phase.DESIGN] is Effort.HIGH
    assert PHASE_BASE_EFFORT[Phase.BUILD] is Effort.LOW
    assert PHASE_BASE_EFFORT[Phase.REVIEW] is Effort.HIGH
    assert PHASE_BASE_EFFORT[Phase.DEPLOY] is Effort.LOW


@pytest.mark.parametrize(
    ("attempt", "expected"),
    [
        (1, Effort.LOW),
        (2, Effort.LOW),
        (3, Effort.STANDARD),
        (4, Effort.STANDARD),
        (5, Effort.HIGH),
        (6, Effort.HIGH),
    ],
)
def test_effort_for_attempt_follows_the_ladder(attempt: int, expected: Effort) -> None:
    assert effort_for_attempt(Effort.LOW, attempt) is expected


def test_effort_for_attempt_never_lowers_below_base() -> None:
    assert effort_for_attempt(Effort.HIGH, 1) is Effort.HIGH


def test_attempt_seven_raises_escalation_exhausted() -> None:
    with pytest.raises(EscalationExhausted) as exc_info:
        effort_for_attempt(Effort.LOW, BUILD_LADDER_EXHAUSTED + 1)

    assert exc_info.value.attempt == BUILD_LADDER_EXHAUSTED + 1


def test_attempt_zero_or_negative_is_rejected() -> None:
    with pytest.raises(ValueError, match="1-based"):
        effort_for_attempt(Effort.LOW, 0)


def test_forces_rotation_only_on_increase() -> None:
    assert forces_rotation(Effort.LOW, Effort.STANDARD) is True
    assert forces_rotation(Effort.STANDARD, Effort.STANDARD) is False
    assert forces_rotation(Effort.HIGH, Effort.LOW) is False


@given(base=st.sampled_from(list(Effort)), attempt=st.integers(1, BUILD_LADDER_EXHAUSTED))
def test_effort_for_attempt_table_test_over_all_attempts(base: Effort, attempt: int) -> None:
    result = effort_for_attempt(base, attempt)
    assert result >= base
    assert result >= BUILD_LADDER[attempt - 1]


@given(attempt=st.integers(BUILD_LADDER_EXHAUSTED + 1, BUILD_LADDER_EXHAUSTED + 100))
def test_every_attempt_past_the_ladder_raises(attempt: int) -> None:
    with pytest.raises(EscalationExhausted):
        effort_for_attempt(Effort.LOW, attempt)
