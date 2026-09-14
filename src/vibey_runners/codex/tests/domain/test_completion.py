# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
"""Three-layer completion evaluation: structured → marker → continue."""

from __future__ import annotations

import json

import pytest

from codexloop.domain.capacity import (
    AuthFailed,
    Available,
    QuotaExhausted,
    ThrottleExhausted,
    TransientBackendError,
    WindowExhausted,
)
from codexloop.domain.completion import (
    DEFAULT_DONE_MARKER,
    Blocked,
    CompletionEvaluator,
    Continue,
    Done,
)
from codexloop.domain.signals import TurnSignals

MARKER = DEFAULT_DONE_MARKER


def _eval(
    *,
    structured_output: object | None = None,
    final_message: str | None = None,
    capacity: object | None = None,
    done_marker: str = MARKER,
) -> object:
    evaluator = CompletionEvaluator(done_marker)
    signals = TurnSignals(
        structured_output=structured_output,
        final_message=final_message,
    )
    return evaluator.evaluate(signals, capacity if capacity is not None else Available())


# --- Layer 1: structured output --------------------------------------------


def test_structured_complete_true_empty_remaining_is_done() -> None:
    verdict = _eval(
        structured_output={
            "complete": True,
            "remaining_work": [],
            "blocked_on": None,
            "summary": "all done",
        }
    )
    assert verdict == Done()


def test_structured_complete_false_is_continue_with_remaining() -> None:
    remaining = ["wire evaluator", "add tests"]
    verdict = _eval(
        structured_output={
            "complete": False,
            "remaining_work": remaining,
            "blocked_on": None,
            "summary": "more work",
        }
    )
    assert isinstance(verdict, Continue)
    assert verdict.remaining == remaining


def test_structured_blocked_on_outranks_complete_true() -> None:
    verdict = _eval(
        structured_output={
            "complete": True,
            "remaining_work": [],
            "blocked_on": "needs human approval",
            "summary": "stuck",
        }
    )
    assert verdict == Blocked(reason="needs human approval")


def test_structured_json_string_is_parsed() -> None:
    payload = json.dumps(
        {
            "complete": True,
            "remaining_work": [],
            "blocked_on": None,
            "summary": "done via string",
        }
    )
    assert _eval(structured_output=payload) == Done()


def test_structured_complete_true_with_remaining_is_continue() -> None:
    remaining = ["finish docs"]
    verdict = _eval(
        structured_output={
            "complete": True,
            "remaining_work": remaining,
            "blocked_on": None,
        }
    )
    assert isinstance(verdict, Continue)
    assert verdict.remaining == remaining


# --- Layer 2: done marker on its own line ----------------------------------


def test_marker_on_own_line_is_done() -> None:
    message = f"Implemented the parser.\n{MARKER}\n"
    assert _eval(final_message=message) == Done()


def test_marker_alone_on_stripped_line_is_done() -> None:
    assert _eval(final_message=f"  {MARKER}  ") == Done()


def test_marker_mid_sentence_does_not_complete() -> None:
    message = f"I think {MARKER} applies here but I'm unsure."
    verdict = _eval(final_message=message)
    assert isinstance(verdict, Continue)
    assert verdict.remaining == []


# --- Layer 3: neither → Continue -------------------------------------------


def test_neither_structured_nor_marker_is_continue() -> None:
    verdict = _eval(final_message="still working on it")
    assert isinstance(verdict, Continue)
    assert verdict.remaining == []


def test_empty_signals_is_continue() -> None:
    verdict = _eval()
    assert isinstance(verdict, Continue)
    assert verdict.remaining == []


# --- Precedence: capacity rejection outranks completion --------------------


@pytest.mark.parametrize(
    "capacity",
    [
        ThrottleExhausted(),
        WindowExhausted(),
        QuotaExhausted(reason="insufficient_quota"),
        AuthFailed(reason="invalid_api_key"),
        TransientBackendError(),
    ],
)
def test_non_available_capacity_forces_continue_even_when_complete_true(
    capacity: object,
) -> None:
    verdict = _eval(
        structured_output={
            "complete": True,
            "remaining_work": [],
            "blocked_on": None,
        },
        final_message=MARKER,
        capacity=capacity,
    )
    assert isinstance(verdict, Continue)


def test_capacity_rejection_preserves_remaining_work_when_known() -> None:
    remaining = ["item-a", "item-b"]
    verdict = _eval(
        structured_output={
            "complete": True,
            "remaining_work": remaining,
            "blocked_on": None,
        },
        capacity=ThrottleExhausted(),
    )
    assert isinstance(verdict, Continue)
    assert verdict.remaining == remaining


def test_capacity_rejection_outranks_blocked_on() -> None:
    verdict = _eval(
        structured_output={
            "complete": False,
            "remaining_work": [],
            "blocked_on": "waiting on secrets",
        },
        capacity=QuotaExhausted(reason="insufficient_quota"),
    )
    assert isinstance(verdict, Continue)


def test_capacity_rejection_without_structured_has_empty_remaining() -> None:
    verdict = _eval(
        final_message=MARKER,
        capacity=ThrottleExhausted(),
    )
    assert isinstance(verdict, Continue)
    assert verdict.remaining == []


def test_non_list_remaining_work_treated_as_empty() -> None:
    verdict = _eval(
        structured_output={
            "complete": False,
            "remaining_work": "not-a-list",
            "blocked_on": None,
        }
    )
    assert isinstance(verdict, Continue)
    assert verdict.remaining == []


# --- Malformed structured falls through to marker -------------------------


def test_malformed_json_string_falls_through_to_marker() -> None:
    assert _eval(structured_output="{not-json", final_message=MARKER) == Done()


def test_malformed_json_without_marker_is_continue() -> None:
    verdict = _eval(structured_output="{not-json", final_message="no marker here")
    assert isinstance(verdict, Continue)


def test_non_mapping_structured_falls_through_to_marker() -> None:
    assert _eval(structured_output=["complete", True], final_message=MARKER) == Done()


def test_json_string_array_falls_through_to_marker() -> None:
    assert _eval(structured_output='["not", "a", "mapping"]', final_message=MARKER) == Done()


def test_structured_missing_complete_falls_through_to_marker() -> None:
    assert (
        _eval(
            structured_output={"remaining_work": [], "blocked_on": None},
            final_message=MARKER,
        )
        == Done()
    )


# --- Constructor / defaults ------------------------------------------------


def test_default_done_marker_constant() -> None:
    assert DEFAULT_DONE_MARKER == "CODEXLOOP_TASK_FULLY_COMPLETE"


def test_evaluator_accepts_custom_done_marker() -> None:
    custom = "MY_CUSTOM_DONE"
    evaluator = CompletionEvaluator(custom)
    signals = TurnSignals(final_message=f"ok\n{custom}\n")
    assert evaluator.evaluate(signals, Available()) == Done()
    assert evaluator.evaluate(TurnSignals(final_message=MARKER), Available()) == Continue(
        remaining=[]
    )
