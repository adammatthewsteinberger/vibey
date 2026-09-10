# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from __future__ import annotations

import textwrap

from cursorloop.domain.autonomy import VERDICT_SCHEMA_DESCRIPTION, autonomy_preamble
from cursorloop.domain.completion import (
    DEFAULT_DONE_MARKER,
    VERDICT_FENCE,
    Blocked,
    Continue,
    Done,
    StructuredVerdict,
    evaluate,
    parse_verdict_block,
)


def _fenced(payload: str) -> str:
    return textwrap.dedent(f"""\
        Some assistant prose about the work.

        ```cursorloop-verdict
        {payload}
        ```
        """)


def test_parses_a_well_formed_verdict_block() -> None:
    text = _fenced(
        '{"complete": false, "remaining_work": ["wire the gateway"], '
        '"blocked_on": null, "summary": "made progress"}'
    )
    assert parse_verdict_block(text) == StructuredVerdict(
        complete=False,
        remaining_work=("wire the gateway",),
        blocked_on=None,
        summary="made progress",
    )


def test_last_fence_wins() -> None:
    """A model quoting the instruction earlier in its own reasoning must not be
    mistaken for the actual verdict."""
    text = _fenced(
        '{"complete": true, "remaining_work": [], "blocked_on": null, "summary": "quoted"}'
    ) + _fenced(
        '{"complete": false, "remaining_work": ["real"], "blocked_on": null, "summary": "actual"}'
    )
    verdict = parse_verdict_block(text)
    assert verdict is not None and verdict.summary == "actual"


def test_malformed_json_is_absent_not_fatal() -> None:
    """A multi-hour run must never die on a stray brace."""
    assert parse_verdict_block(_fenced("{not json at all,,,}")) is None


def test_wrong_types_are_absent() -> None:
    assert parse_verdict_block(_fenced('{"complete": "yes"}')) is None


def test_no_fence_is_absent() -> None:
    assert parse_verdict_block("just prose, no fence here") is None


def test_blocked_on_outranks_complete_and_is_terminal() -> None:
    """A turn must never be allowed to claim both. blocked_on is reserved for
    true external/human blockers; waitable self-started work belongs in
    remaining_work with blocked_on null."""
    structured = StructuredVerdict(complete=True, blocked_on="needs prod DB credentials")
    assert evaluate(structured=structured, output_text="") == Blocked(
        reason="needs prod DB credentials"
    )


def test_structured_verdict_beats_the_marker() -> None:
    structured = StructuredVerdict(complete=False, remaining_work=("more",))
    assert evaluate(
        structured=structured, output_text=f"blah {DEFAULT_DONE_MARKER} blah"
    ) == Continue(remaining_work=("more",))


def test_marker_is_the_fallback_only_when_structured_is_absent() -> None:
    assert evaluate(structured=None, output_text=f"all set {DEFAULT_DONE_MARKER}") == Done()


def test_empty_zero_token_turn_becomes_a_wait_only_continue() -> None:
    assert evaluate(structured=None, output_text="   ", tokens=0, empty_turn_streak=0) == Continue(
        remaining_work=("Waiting for a non-empty model response",)
    )


def test_repeated_empty_turns_become_blocked() -> None:
    assert evaluate(
        structured=None, output_text="", tokens=0, empty_turn_streak=2, empty_turn_limit=3
    ) == Blocked(reason="repeated empty model responses")


def test_ordinary_text_with_no_signal_is_a_plain_continue() -> None:
    assert evaluate(structured=None, output_text="I refactored two files.") == Continue()


def test_last_malformed_fence_is_absent_even_if_an_earlier_one_was_valid() -> None:
    text = _fenced(
        '{"complete": true, "remaining_work": [], "blocked_on": null, "summary": "ok"}'
    ) + _fenced("{not json}")
    assert parse_verdict_block(text) is None


def test_missing_complete_is_absent() -> None:
    assert parse_verdict_block(_fenced('{"remaining_work": [], "summary": "x"}')) is None


def test_non_object_json_is_absent() -> None:
    assert parse_verdict_block(_fenced("[1, 2, 3]")) is None


def test_wrong_remaining_work_type_is_absent() -> None:
    assert parse_verdict_block(_fenced('{"complete": false, "remaining_work": "later"}')) is None


def test_non_string_remaining_work_item_is_absent() -> None:
    assert parse_verdict_block(_fenced('{"complete": false, "remaining_work": [1]}')) is None


def test_wrong_blocked_on_type_is_absent() -> None:
    assert parse_verdict_block(_fenced('{"complete": false, "blocked_on": 12}')) is None


def test_wrong_summary_type_is_absent() -> None:
    assert parse_verdict_block(_fenced('{"complete": true, "summary": false}')) is None


def test_omitted_optional_fields_default() -> None:
    assert parse_verdict_block(_fenced('{"complete": true}')) == StructuredVerdict(complete=True)


def test_structured_complete_is_done_with_summary() -> None:
    structured = StructuredVerdict(complete=True, summary="shipped")
    assert evaluate(structured=structured, output_text="") == Done(summary="shipped")


def test_fallback_uses_custom_marker() -> None:
    assert evaluate(structured=None, output_text="XYZ_DONE", done_marker="XYZ_DONE") == Done()


def test_empty_text_with_tokens_is_a_plain_continue() -> None:
    """A billed empty body is not the empty-turn soft-fail; tokens prove a turn ran."""
    assert evaluate(structured=None, output_text="", tokens=12) == Continue()


def test_verdict_fence_constant_matches_the_convention() -> None:
    assert VERDICT_FENCE == "cursorloop-verdict"
    assert DEFAULT_DONE_MARKER == "CURSORLOOP_TASK_FULLY_COMPLETE"


def test_autonomy_preamble_never_blocks_on_a_human() -> None:
    text = autonomy_preamble(DEFAULT_DONE_MARKER, require_verdict=False)
    lowered = text.lower()
    assert "human" in lowered
    assert "assumption" in lowered
    assert "clarifying" in lowered
    assert "blocked_on" in lowered
    assert "external" in lowered
    assert VERDICT_FENCE in text
    assert DEFAULT_DONE_MARKER in text
    assert VERDICT_SCHEMA_DESCRIPTION in text


def test_autonomy_preamble_require_verdict_makes_the_fence_mandatory() -> None:
    optional = autonomy_preamble(DEFAULT_DONE_MARKER, require_verdict=False)
    required = autonomy_preamble(DEFAULT_DONE_MARKER, require_verdict=True)
    assert "required on every turn" in required.lower()
    assert "required on every turn" not in optional.lower()


def test_verdict_schema_description_steers_blocked_on() -> None:
    lowered = VERDICT_SCHEMA_DESCRIPTION.lower()
    assert "complete" in lowered
    assert "remaining_work" in lowered
    assert "blocked_on" in lowered
    assert "null" in lowered
    assert "waitable" in lowered or "background" in lowered
