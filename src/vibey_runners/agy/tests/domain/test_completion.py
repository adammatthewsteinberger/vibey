# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
from agyloop.domain.completion import (
    COMPLETION_RESPONSE_SCHEMA,
    DEFAULT_DONE_MARKER,
    DONE_MARKER_INSTRUCTION,
    Blocked,
    Continue,
    Done,
    StructuredVerdict,
    evaluate,
)


def test_done_marker_is_agyloop_branded() -> None:
    assert DEFAULT_DONE_MARKER == "AGYLOOP_TASK_FULLY_COMPLETE"


def test_completion_schema_names_verdict_fields() -> None:
    properties = COMPLETION_RESPONSE_SCHEMA["properties"]
    assert isinstance(properties, dict)
    assert set(properties) == {"complete", "remaining_work", "blocked_on", "summary"}
    assert DEFAULT_DONE_MARKER in DONE_MARKER_INSTRUCTION


def test_structured_complete_is_done() -> None:
    v = StructuredVerdict(complete=True, summary="all done")
    assert evaluate(structured=v, output_text="") == Done(summary="all done")


def test_structured_incomplete_is_continue_with_remaining_work() -> None:
    v = StructuredVerdict(complete=False, remaining_work=("thing a", "thing b"))
    assert evaluate(structured=v, output_text="") == Continue(remaining_work=("thing a", "thing b"))


def test_structured_blocked_outranks_complete_flag() -> None:
    v = StructuredVerdict(complete=True, blocked_on="waiting on MCP auth")
    assert evaluate(structured=v, output_text="") == Blocked(reason="waiting on MCP auth")


def test_structured_empty_blocked_on_outranks_complete_flag() -> None:
    v = StructuredVerdict(complete=True, blocked_on="")
    assert evaluate(structured=v, output_text="") == Blocked(reason="")


def test_structured_incomplete_outranks_marker_in_text() -> None:
    v = StructuredVerdict(complete=False, remaining_work=("still going",))
    result = evaluate(structured=v, output_text="AGYLOOP_TASK_FULLY_COMPLETE")
    assert result == Continue(remaining_work=("still going",))


def test_invalid_structured_plus_marker_is_continue_never_done() -> None:
    """Malformed payloads must be passed as present incomplete structured output.

    Passing None would fall through to the marker and yield Done.
    """
    result = evaluate(
        structured=StructuredVerdict(complete=False),
        output_text=DEFAULT_DONE_MARKER,
    )
    assert isinstance(result, Continue)
    assert not isinstance(result, Done)


def test_fallback_marker_present_is_done() -> None:
    result = evaluate(structured=None, output_text="...\nAGYLOOP_TASK_FULLY_COMPLETE\n")
    assert result == Done(summary="")


def test_absent_structured_plus_marker_is_done() -> None:
    result = evaluate(structured=None, output_text=DEFAULT_DONE_MARKER)
    assert result == Done(summary="")


def test_fallback_marker_absent_is_continue_never_done() -> None:
    result = evaluate(structured=None, output_text="still working on it")
    assert result == Continue(remaining_work=())
    assert not isinstance(result, Done)


def test_missing_verdict_is_continue_never_done() -> None:
    result = evaluate(structured=None, output_text="")
    assert isinstance(result, Continue)
    assert not isinstance(result, Done)


def test_fallback_uses_custom_marker() -> None:
    result = evaluate(structured=None, output_text="XYZ_DONE", done_marker="XYZ_DONE")
    assert result == Done(summary="")


def test_empty_turn_soft_continue_then_blocked() -> None:
    first = evaluate(structured=None, output_text="", cost_usd=0.0, empty_turn_streak=0)
    assert isinstance(first, Continue)
    third = evaluate(structured=None, output_text="", cost_usd=0.0, empty_turn_streak=2)
    assert isinstance(third, Blocked)


def test_permission_denial_only_turn_is_blocked() -> None:
    """A turn that only contains permission-denial messages is not progress."""
    denial_text = (
        'jetski: no output produced — a tool required the "command" permission that '
        "headless mode cannot prompt for, so it was auto-denied. Add an allow-rule "
        "under permissions.allow in settings.json"
    )
    result = evaluate(structured=None, output_text=denial_text)
    assert isinstance(result, Blocked)
    assert "permission" in result.reason.lower() or "denied" in result.reason.lower()


def test_permission_denial_with_marker_is_still_blocked() -> None:
    """Permission denial outranks a completion marker — cannot be done if nothing ran."""
    denial_text = (
        "no output produced — a tool required permission that cannot be granted.\n"
        f"{DEFAULT_DONE_MARKER}"
    )
    result = evaluate(structured=None, output_text=denial_text)
    assert isinstance(result, Blocked)
    assert not isinstance(result, Done)


def test_permission_denial_pattern_variants() -> None:
    """Detect multiple permission-denial phrasing variations."""
    patterns = [
        "tool required permission",
        "auto-denied",
        "permission that headless mode cannot",
        "dangerously-skip-permissions",
        "unsafe-skip-permissions to auto-approve",
    ]
    for pattern in patterns:
        result = evaluate(structured=None, output_text=pattern)
        assert isinstance(result, Blocked), f"Pattern '{pattern}' should block"
