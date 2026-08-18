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
