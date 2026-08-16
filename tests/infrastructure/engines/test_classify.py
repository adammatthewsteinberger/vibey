import pytest

from vibey.domain.capacity import (
    AuthenticationFailed,
    Available,
    CreditsExhausted,
    WindowExhausted,
)
from vibey.domain.engine import EngineId
from vibey.domain.job import FailureClass
from vibey.infrastructure.engines.classify import (
    AUTH_FIXTURES,
    AVAILABLE_FIXTURES,
    CREDITS_FIXTURES,
    WINDOW_FIXTURES,
    attribute_failure,
    classify_capacity,
)


@pytest.mark.parametrize("engine_id", list(EngineId))
def test_credits_fixture_classifies_as_credits_exhausted(engine_id: EngineId) -> None:
    result = classify_capacity(engine_id, CREDITS_FIXTURES[engine_id])
    assert isinstance(result, CreditsExhausted)


@pytest.mark.parametrize("engine_id", list(EngineId))
def test_window_fixture_classifies_as_window_exhausted(engine_id: EngineId) -> None:
    result = classify_capacity(engine_id, WINDOW_FIXTURES[engine_id])
    assert isinstance(result, WindowExhausted)


@pytest.mark.parametrize("engine_id", list(EngineId))
def test_auth_fixture_classifies_as_authentication_failed(engine_id: EngineId) -> None:
    result = classify_capacity(engine_id, AUTH_FIXTURES[engine_id])
    assert isinstance(result, AuthenticationFailed)


@pytest.mark.parametrize("engine_id", list(EngineId))
def test_available_fixture_classifies_as_available(engine_id: EngineId) -> None:
    result = classify_capacity(engine_id, AVAILABLE_FIXTURES[engine_id])
    assert isinstance(result, Available)


@pytest.mark.parametrize("engine_id", list(EngineId))
def test_credits_never_carries_a_resets_at(engine_id: EngineId) -> None:
    result = classify_capacity(engine_id, CREDITS_FIXTURES[engine_id])
    assert not hasattr(result, "resets_at")


@pytest.mark.parametrize("engine_id", list(EngineId))
def test_credits_and_window_are_never_confused(engine_id: EngineId) -> None:
    credits_result = classify_capacity(engine_id, CREDITS_FIXTURES[engine_id])
    window_result = classify_capacity(engine_id, WINDOW_FIXTURES[engine_id])

    assert not isinstance(credits_result, WindowExhausted)
    assert not isinstance(window_result, CreditsExhausted)


# --- FailureClass attribution fixture corpus --------------------------------

PYTEST_FAILURE_TAIL = """
======= FAILURES =======
______ test_outbox_relay_retries ______
    assert relay.attempts == 3
AssertionError: assert 1 == 3
FAILED tests/test_relay.py::test_outbox_relay_retries - AssertionError
"""

ENGINE_CRASH_TAIL = """
Traceback (most recent call last):
  File "runner.py", line 42, in main
    raise RuntimeError("runner crashed")
RuntimeError: runner crashed
"""

VIBEY_BUG_TAIL = "VibeyInternalError: unexpected None in handoff.produce"


def test_failing_pytest_never_opens_the_circuit() -> None:
    """The single property called out by the milestone: a project test
    failure must classify WORK, never ENGINE, regardless of exit code."""
    result = attribute_failure(1, PYTEST_FAILURE_TAIL)
    assert result is FailureClass.WORK


def test_failing_pytest_is_work_even_with_a_nonstandard_exit_code() -> None:
    result = attribute_failure(2, PYTEST_FAILURE_TAIL)
    assert result is FailureClass.WORK


def test_work_marker_wins_even_alongside_an_incidental_traceback() -> None:
    mixed_tail = ENGINE_CRASH_TAIL + "\n" + PYTEST_FAILURE_TAIL
    assert attribute_failure(1, mixed_tail) is FailureClass.WORK


def test_engine_crash_classifies_as_engine() -> None:
    assert attribute_failure(1, ENGINE_CRASH_TAIL) is FailureClass.ENGINE


def test_timeout_exit_code_classifies_as_engine() -> None:
    assert attribute_failure(124, "process timed out") is FailureClass.ENGINE


def test_sigkill_exit_code_classifies_as_engine() -> None:
    assert attribute_failure(137, "killed") is FailureClass.ENGINE


def test_vibey_internal_error_classifies_as_vibey() -> None:
    assert attribute_failure(1, VIBEY_BUG_TAIL) is FailureClass.VIBEY


def test_clean_exit_classifies_as_work() -> None:
    assert attribute_failure(0, "") is FailureClass.WORK


def test_unrecognized_nonzero_exit_defaults_to_work() -> None:
    assert attribute_failure(1, "something odd happened") is FailureClass.WORK
