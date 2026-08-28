# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://hire.adam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
# Made with love by Vibey, the auto-vibecoding machine by Adam Matthew Steinberger.
"""Tests for loop_events.py event type mapping."""

from vibey.domain.engine import EngineId
from vibey.domain.ledger import EventKind
from vibey.infrastructure.engines.loop_events import LOOP_EVENT_MAP, translate_event_type


def test_agyloop_event_mapping_coverage() -> None:
    """Verify all real agyloop event types from a captured run are mapped."""
    # These event types were captured from a real agyloop 0.1.0 run
    real_agyloop_events = [
        "run.started",
        "preflight",
        "turn.starting",
        "chatter.prompt",
        "sdk.event",
        "chatter.assistant",
        "turn.completed",
        "savepoint.skipped",
        "capacity.forecast",
        "finished",
    ]

    agyloop_map = LOOP_EVENT_MAP[EngineId.AGYLOOP]

    for event_type in real_agyloop_events:
        assert event_type in agyloop_map, f"Real agyloop event '{event_type}' not mapped"


def test_agyloop_finished_maps_to_verdict_rendered() -> None:
    """The 'finished' event must map to VerdictRendered for structured_verdict check."""
    result = translate_event_type(EngineId.AGYLOOP, "finished")
    assert result == EventKind.VERDICT_RENDERED, (
        f"'finished' must map to VerdictRendered, got {result}"
    )


def test_agyloop_turn_events() -> None:
    """Verify turn-related events map correctly."""
    assert translate_event_type(EngineId.AGYLOOP, "chatter.prompt") == EventKind.TURN_REQUESTED
    assert translate_event_type(EngineId.AGYLOOP, "turn.starting") == EventKind.TURN_REQUESTED
    assert translate_event_type(EngineId.AGYLOOP, "chatter.assistant") == EventKind.TURN_COMPLETED
    assert translate_event_type(EngineId.AGYLOOP, "turn.completed") == EventKind.TURN_COMPLETED


def test_agyloop_session_events() -> None:
    """Verify session initialization events map to SESSION_SEEDED."""
    assert translate_event_type(EngineId.AGYLOOP, "run.started") == EventKind.SESSION_SEEDED
    assert translate_event_type(EngineId.AGYLOOP, "preflight") == EventKind.SESSION_SEEDED


def test_agyloop_savepoint_events() -> None:
    """Verify savepoint events map correctly."""
    assert translate_event_type(EngineId.AGYLOOP, "savepoint") == EventKind.SAVEPOINT_CREATED
    assert (
        translate_event_type(EngineId.AGYLOOP, "savepoint.created") == EventKind.SAVEPOINT_CREATED
    )
    assert (
        translate_event_type(EngineId.AGYLOOP, "savepoint.skipped") == EventKind.SAVEPOINT_CREATED
    )


def test_agyloop_unknown_event_returns_none() -> None:
    """Unknown event types return None and are gracefully skipped."""
    result = translate_event_type(EngineId.AGYLOOP, "unknown.event.type")
    assert result is None


def test_all_engines_have_mappings() -> None:
    """All four engine IDs have event mappings."""
    for engine_id in [
        EngineId.CLAUDELOOP,
        EngineId.CODEXLOOP,
        EngineId.CURSORLOOP,
        EngineId.AGYLOOP,
    ]:
        assert engine_id in LOOP_EVENT_MAP, f"{engine_id} missing from LOOP_EVENT_MAP"
        assert len(LOOP_EVENT_MAP[engine_id]) > 0, f"{engine_id} map is empty"


def test_agyloop_capacity_event() -> None:
    """capacity.forecast is proactive headroom telemetry emitted only while
    capacity IS available (see runner.py::_project_capacity) -- it must not
    map to CAPACITY_REJECTED, or every normal successful run would look
    capacity-constrained."""
    assert translate_event_type(EngineId.AGYLOOP, "capacity.forecast") == EventKind.BUDGET_SPENT


def test_agyloop_tool_invocation() -> None:
    """Verify sdk.event maps to TOOL_INVOKED."""
    assert translate_event_type(EngineId.AGYLOOP, "sdk.event") == EventKind.TOOL_INVOKED


def test_claudeloop_event_mapping_coverage() -> None:
    """Verify all real claudeloop event types from a captured run are mapped."""
    # Captured from a real, authenticated `vibey doctor --conformance
    # --engine claudeloop` run's events.jsonl.
    real_claudeloop_events = [
        "run.started",
        "preflight",
        "chatter.prompt",
        "turn.starting",
        "chatter.assistant",
        "turn.completed",
        "chatter.tool",
        "savepoint",
        "capacity.forecast",
        "finished",
    ]

    claudeloop_map = LOOP_EVENT_MAP[EngineId.CLAUDELOOP]

    for event_type in real_claudeloop_events:
        assert event_type in claudeloop_map, f"Real claudeloop event '{event_type}' not mapped"


def test_claudeloop_finished_maps_to_verdict_rendered() -> None:
    """The 'finished' event must map to VerdictRendered for structured_verdict check."""
    result = translate_event_type(EngineId.CLAUDELOOP, "finished")
    assert result == EventKind.VERDICT_RENDERED, (
        f"'finished' must map to VerdictRendered, got {result}"
    )


def test_claudeloop_turn_events() -> None:
    """Verify turn-related events map correctly."""
    assert translate_event_type(EngineId.CLAUDELOOP, "chatter.prompt") == EventKind.TURN_REQUESTED
    assert translate_event_type(EngineId.CLAUDELOOP, "turn.starting") == EventKind.TURN_REQUESTED
    assert (
        translate_event_type(EngineId.CLAUDELOOP, "chatter.assistant") == EventKind.TURN_COMPLETED
    )
    assert translate_event_type(EngineId.CLAUDELOOP, "turn.completed") == EventKind.TURN_COMPLETED


def test_claudeloop_session_events() -> None:
    """Verify session initialization events map to SESSION_SEEDED."""
    assert translate_event_type(EngineId.CLAUDELOOP, "run.started") == EventKind.SESSION_SEEDED
    assert translate_event_type(EngineId.CLAUDELOOP, "preflight") == EventKind.SESSION_SEEDED


def test_claudeloop_savepoint_event() -> None:
    """Verify the savepoint event maps correctly."""
    assert translate_event_type(EngineId.CLAUDELOOP, "savepoint") == EventKind.SAVEPOINT_CREATED


def test_claudeloop_capacity_event() -> None:
    """capacity.forecast is proactive headroom telemetry emitted only while
    capacity IS available (see runner.py::_project_capacity, word-for-word
    identical to agyloop's own) -- it must not map to CAPACITY_REJECTED, or
    every normal successful run would look capacity-constrained."""
    assert translate_event_type(EngineId.CLAUDELOOP, "capacity.forecast") == EventKind.BUDGET_SPENT


def test_claudeloop_tool_invocation() -> None:
    """Verify chatter.tool maps to TOOL_INVOKED."""
    assert translate_event_type(EngineId.CLAUDELOOP, "chatter.tool") == EventKind.TOOL_INVOKED


def test_claudeloop_unknown_event_returns_none() -> None:
    """Unknown event types (including the old fabricated mapping's own
    entries, now removed) return None and are gracefully skipped."""
    assert translate_event_type(EngineId.CLAUDELOOP, "unknown.event.type") is None
    assert translate_event_type(EngineId.CLAUDELOOP, "session.started") is None


def test_codexloop_event_mapping_coverage() -> None:
    """Verify the real `codex exec --json` vocabulary is mapped.

    Sourced from codexloop's own infrastructure/agent/events.py::JsonlParser
    -- the exact type strings it recognizes -- not a live capture, since
    codexloop's own event sink isn't wired to events.jsonl yet (see
    docs/plans/fleet/c4-wire-events-sink-codexloop.md).
    """
    real_codexloop_events = [
        "thread.started",
        "turn.started",
        "turn.completed",
        "turn.failed",
        "item.started",
        "item.completed",
        "rate_limits.updated",
    ]

    codexloop_map = LOOP_EVENT_MAP[EngineId.CODEXLOOP]

    for event_type in real_codexloop_events:
        assert event_type in codexloop_map, f"Real codexloop event '{event_type}' not mapped"


def test_codexloop_session_and_turn_events() -> None:
    """Verify session/turn events map correctly."""
    assert translate_event_type(EngineId.CODEXLOOP, "thread.started") == EventKind.SESSION_SEEDED
    assert translate_event_type(EngineId.CODEXLOOP, "turn.started") == EventKind.TURN_REQUESTED
    assert translate_event_type(EngineId.CODEXLOOP, "turn.completed") == EventKind.TURN_COMPLETED
    assert translate_event_type(EngineId.CODEXLOOP, "turn.failed") == EventKind.TURN_COMPLETED


def test_codexloop_item_events_map_to_tool_invoked() -> None:
    """Verify item.started/item.completed map to TOOL_INVOKED."""
    assert translate_event_type(EngineId.CODEXLOOP, "item.started") == EventKind.TOOL_INVOKED
    assert translate_event_type(EngineId.CODEXLOOP, "item.completed") == EventKind.TOOL_INVOKED


def test_codexloop_rate_limits_event() -> None:
    """rate_limits.updated is proactive plan/window telemetry folded into
    TurnSignals for classification (domain/classify.py) -- it is never
    itself a rejection, so it must not map to CAPACITY_REJECTED."""
    assert translate_event_type(EngineId.CODEXLOOP, "rate_limits.updated") == EventKind.BUDGET_SPENT


def test_codexloop_ambiguous_events_are_unmapped() -> None:
    """ "error" and "event_msg" carry payload-dependent meaning this
    string-keyed map can't resolve -- they must be skipped, not guessed."""
    assert translate_event_type(EngineId.CODEXLOOP, "error") is None
    assert translate_event_type(EngineId.CODEXLOOP, "event_msg") is None


def test_codexloop_unknown_event_returns_none() -> None:
    """Unknown event types (including the old fabricated mapping's own
    entries, now removed) return None and are gracefully skipped."""
    assert translate_event_type(EngineId.CODEXLOOP, "unknown.event.type") is None
    assert translate_event_type(EngineId.CODEXLOOP, "thread.message.user") is None
    assert translate_event_type(EngineId.CODEXLOOP, "output.verdict") is None


def test_cursorloop_event_mapping_coverage() -> None:
    """Verify the real Cursor Agent SDK vocabulary is mapped.

    Sourced from cursorloop's own infrastructure/agent/translate.py::
    TeeStream -- string literals hardcoded verbatim in
    _on_tool_call/_on_status/_on_usage -- not a live capture, since the
    scripted (offline) path never reaches the sink (see
    docs/plans/fleet/c4-wire-events-sink-cursorloop.md).
    """
    real_cursorloop_events = ["tool_call", "usage"]

    cursorloop_map = LOOP_EVENT_MAP[EngineId.CURSORLOOP]

    for event_type in real_cursorloop_events:
        assert event_type in cursorloop_map, f"Real cursorloop event '{event_type}' not mapped"


def test_cursorloop_tool_invocation() -> None:
    """Verify tool_call maps to TOOL_INVOKED."""
    assert translate_event_type(EngineId.CURSORLOOP, "tool_call") == EventKind.TOOL_INVOKED


def test_cursorloop_usage_event() -> None:
    """Verify usage maps to BUDGET_SPENT."""
    assert translate_event_type(EngineId.CURSORLOOP, "usage") == EventKind.BUDGET_SPENT


def test_cursorloop_status_is_unmapped() -> None:
    """ "status" is a free-text SDK message, not a fixed vocabulary -- no
    single EventKind fits every value it can carry, so it's skipped."""
    assert translate_event_type(EngineId.CURSORLOOP, "status") is None


def test_cursorloop_has_no_session_or_verdict_events() -> None:
    """Unlike the other three engines, cursorloop's events.jsonl carries no
    wrapper-level session/turn/verdict boundary marker at all -- only
    in-turn SDK message types. These must stay unmapped, not guessed."""
    assert translate_event_type(EngineId.CURSORLOOP, "agent.started") is None
    assert translate_event_type(EngineId.CURSORLOOP, "finished") is None
    assert translate_event_type(EngineId.CURSORLOOP, "agent.savepoint") is None


def test_cursorloop_unknown_event_returns_none() -> None:
    """Unknown event types (including the old fabricated mapping's own
    entries, now removed) return None and are gracefully skipped."""
    assert translate_event_type(EngineId.CURSORLOOP, "unknown.event.type") is None
    assert translate_event_type(EngineId.CURSORLOOP, "capacity.limited") is None
