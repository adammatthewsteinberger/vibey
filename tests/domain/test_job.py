from datetime import timedelta
from uuid import uuid4

from hypothesis import given
from hypothesis import strategies as st

from vibey.domain.job import FailureClass, JobState, backoff, idempotency_key


def test_job_state_values() -> None:
    assert set(JobState) == {
        JobState.READY,
        JobState.LEASED,
        JobState.SUCCEEDED,
        JobState.FAILED,
        JobState.AWAITING_HUMAN,
        JobState.AWAITING_CAPACITY,
        JobState.CANCELLED,
    }


def test_failure_class_values() -> None:
    assert set(FailureClass) == {
        FailureClass.CAPACITY,
        FailureClass.ENGINE,
        FailureClass.WORK,
        FailureClass.VIBEY,
    }


def test_backoff_grows_exponentially_then_caps() -> None:
    assert backoff(0) == timedelta(seconds=2)
    assert backoff(1) == timedelta(seconds=4)
    assert backoff(2) == timedelta(seconds=8)
    assert backoff(100) == timedelta(minutes=15)


def test_backoff_negative_attempt_treated_as_zero() -> None:
    assert backoff(-5) == backoff(0)


def test_idempotency_key_is_deterministic() -> None:
    project_id = uuid4()
    key1 = idempotency_key(project_id, 1, "build.implement", "item-001")
    key2 = idempotency_key(project_id, 1, "build.implement", "item-001")
    assert key1 == key2


def test_idempotency_key_differs_with_any_component() -> None:
    project_id = uuid4()
    base = idempotency_key(project_id, 1, "build.implement", "item-001")
    assert idempotency_key(project_id, 2, "build.implement", "item-001") != base
    assert idempotency_key(project_id, 1, "build.verify", "item-001") != base
    assert idempotency_key(project_id, 1, "build.implement", "item-002") != base


@given(attempt=st.integers(-100, 1000))
def test_backoff_never_exceeds_cap(attempt: int) -> None:
    assert backoff(attempt) <= timedelta(minutes=15)


@given(attempt=st.integers(-100, 1000))
def test_backoff_never_negative(attempt: int) -> None:
    assert backoff(attempt) >= timedelta(0)
