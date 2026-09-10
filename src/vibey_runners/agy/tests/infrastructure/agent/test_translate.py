# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Exception and chunk translation into TurnSignals / TurnOutcome."""

from __future__ import annotations

from datetime import timedelta

from google.antigravity.types import (
    AntigravityCancelledError,
    AntigravityConnectionError,
    AntigravityExecutionError,
    AntigravityValidationError,
    Text,
    Thought,
)

from agyloop.application.dto import TurnOutcome
from agyloop.domain.capacity import Available, WindowExhausted
from agyloop.domain.classify import classify
from agyloop.domain.completion import Blocked, Continue, Done, evaluate
from agyloop.domain.errors import AgentConfigError
from agyloop.infrastructure.agent.translate import (
    outcome_from_chunks,
    outcome_from_exception,
    signals_from_exception,
    verdict_from_structured,
)


def test_execution_error_429_maps_to_turn_signals() -> None:
    exc = AntigravityExecutionError(
        "429 RESOURCE_EXHAUSTED: Resource has been exhausted (e.g. check quota)."
    )
    signals = signals_from_exception(exc)
    assert signals.exception_type == "AntigravityExecutionError"
    assert signals.http_status == 429
    assert signals.status == "RESOURCE_EXHAUSTED" or signals.google_status == "RESOURCE_EXHAUSTED"
    state = classify(signals)
    assert isinstance(state, WindowExhausted)


def test_cancelled_error_is_not_a_capacity_signal() -> None:
    exc = AntigravityCancelledError("operator stop")
    signals = signals_from_exception(exc)
    assert signals.exception_type == "AntigravityCancelledError"
    assert "cancelled" in (signals.exception_type or "").casefold()
    state = classify(signals)
    assert isinstance(state, Available)


def test_validation_error_is_our_bug() -> None:
    exc = AntigravityValidationError("bad LocalAgentConfig")
    try:
        outcome_from_exception(exc)
    except AgentConfigError as wrapped:
        assert "bad LocalAgentConfig" in str(wrapped)
        assert wrapped.__cause__ is exc
    else:
        raise AssertionError("AntigravityValidationError must not become TurnSignals")


def test_connection_error_401_maps_auth_status() -> None:
    exc = AntigravityConnectionError("401 UNAUTHENTICATED: invalid API key")
    signals = signals_from_exception(exc)
    assert signals.http_status == 401
    assert (signals.status or signals.google_status) == "UNAUTHENTICATED"


def test_retry_info_delay_is_recovered_from_message() -> None:
    exc = AntigravityExecutionError('429 RESOURCE_EXHAUSTED retryDelay: "27s" rate_limit_exceeded')
    signals = signals_from_exception(exc)
    assert signals.retry_info_delay == timedelta(seconds=27)
    assert signals.error_code == "rate_limit_exceeded"


def test_chunks_preserve_partial_text_and_thoughts() -> None:
    outcome = outcome_from_chunks(
        [Thought(step_index=0, text="planning"), Text(step_index=1, text="hello")],
        session_id="abc",
    )
    assert isinstance(outcome, TurnOutcome)
    assert outcome.output_text == "hello"
    assert outcome.session_id == "abc"
    assert outcome.signals.exception_type is None


def _evaluate_structured(blob: object, output_text: str = "") -> Done | Continue | Blocked:
    return evaluate(structured=verdict_from_structured(blob), output_text=output_text)


def test_structured_output_complete_maps_to_done() -> None:
    blob = {
        "complete": True,
        "remaining_work": [],
        "blocked_on": None,
        "summary": "Implemented and tested the parser; all gates green.",
    }
    result = _evaluate_structured(blob)
    assert result == Done(summary="Implemented and tested the parser; all gates green.")


def test_structured_output_incomplete_maps_to_continue() -> None:
    blob = {
        "complete": False,
        "remaining_work": ["write tests", "open PR"],
        "blocked_on": None,
        "summary": "parser drafted",
    }
    result = _evaluate_structured(blob)
    assert result == Continue(remaining_work=("write tests", "open PR"))
    assert not isinstance(result, Done)


def test_structured_output_blocked_on_outranks_complete() -> None:
    blob = {
        "complete": True,
        "remaining_work": [],
        "blocked_on": "waiting on MCP OAuth",
        "summary": "looks done",
    }
    result = _evaluate_structured(blob)
    assert result == Blocked(reason="waiting on MCP OAuth")


def test_malformed_complete_string_is_continue_never_done() -> None:
    blob = {
        "complete": "false",
        "remaining_work": [],
        "blocked_on": None,
        "summary": "not actually complete",
    }
    assert verdict_from_structured(blob) is not None
    result = _evaluate_structured(blob)
    assert isinstance(result, Continue)
    assert not isinstance(result, Done)


def test_invalid_structured_blob_plus_marker_is_continue_never_done() -> None:
    blob = {
        "complete": "false",
        "remaining_work": [],
        "blocked_on": None,
        "summary": "not actually complete",
    }
    result = _evaluate_structured(blob, output_text="AGYLOOP_TASK_FULLY_COMPLETE")
    assert verdict_from_structured(blob) is not None
    assert isinstance(result, Continue)
    assert not isinstance(result, Done)


def test_structured_output_none_plus_marker_is_done() -> None:
    result = _evaluate_structured(None, output_text="wrapping up\nAGYLOOP_TASK_FULLY_COMPLETE\n")
    assert result == Done(summary="")


def test_structured_output_none_without_marker_is_continue_never_done() -> None:
    result = _evaluate_structured(None, output_text="still working on the parser")
    assert isinstance(result, Continue)
    assert not isinstance(result, Done)


def test_404_not_found_is_agent_config_error() -> None:
    exc = AntigravityExecutionError(
        "404 NOT_FOUND: gemini-2.5-flash-lite is no longer available to new users"
    )
    try:
        outcome_from_exception(exc)
    except AgentConfigError as wrapped:
        assert "404" in str(wrapped) or "NOT_FOUND" in str(wrapped)
        assert wrapped.__cause__ is exc
    else:
        raise AssertionError("withdrawn-model 404 must not become TurnSignals")


def test_signals_from_exception_recover_404_and_not_found() -> None:
    exc = AntigravityExecutionError("404 NOT_FOUND models/gemini-2.5-flash-lite")
    signals = signals_from_exception(exc)
    assert signals.http_status == 404
    assert (signals.status or signals.google_status) == "NOT_FOUND"


def test_chunks_with_structured_complete_evaluate_to_done() -> None:
    outcome = outcome_from_chunks(
        [Text(step_index=1, text="shipped")],
        structured={
            "complete": True,
            "remaining_work": [],
            "blocked_on": None,
            "summary": "all green",
        },
    )
    result = evaluate(structured=outcome.verdict, output_text=outcome.output_text)
    assert result == Done(summary="all green")
    assert "antigravity" not in type(outcome.verdict).__module__


def test_verdict_from_structured_non_dict_and_wrong_keys() -> None:
    from unittest.mock import MagicMock

    from agyloop.infrastructure.agent.translate import partial_text_from_response

    # Non-dict
    v1 = verdict_from_structured(["not", "a", "dict"])
    assert v1 is not None
    assert v1.complete is False

    # Dict with wrong keys
    v2 = verdict_from_structured({"complete": True})
    assert v2 is not None
    assert v2.complete is False

    # partial_text_from_response with text chunks
    chunk1 = MagicMock()
    chunk1.__class__.__name__ = "Text"
    chunk1.text = "partial "
    chunk2 = MagicMock()
    chunk2.__class__.__name__ = "Other"
    chunk3 = MagicMock()
    chunk3.__class__.__name__ = "Text"
    chunk3.text = "output"

    resp = MagicMock()
    resp._buffered_chunks = [chunk1, chunk2, chunk3]
    assert partial_text_from_response(resp) == "partial output"
