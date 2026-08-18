"""Event type translation: loop event_type vocabulary → vibey EventKind.

Real loop events.jsonl files use dotted event_type strings ("chatter.assistant",
"sdk.message", "RateLimitEvent") rather than vibey's EventKind vocabulary.
This module maps the observed real event types to EventKind, engine by engine.

CLAUDELOOP and AGYLOOP's mappings are built from real events.jsonl captured
by real, authenticated, live runs (see docs/plans/fleet/
e1-loop-event-map-vibey.md and the conformance investigation it closed
out) -- an earlier version of this file claimed the same for every engine
while actually containing fabricated event_type strings for all four
(session.user_turn, function.call, thread.message.user, agent.savepoint,
...: none of these are real). CODEXLOOP and CURSORLOOP still carry that
earlier, unverified guesswork -- their CLIs aren't authenticated in this
environment, so their mappings haven't been corrected the same way yet.
Don't trust them without the same live-capture verification.
"""

from vibey.domain.engine import EngineId
from vibey.domain.ledger import EventKind

# Mapping from real loop event_type strings to vibey's EventKind vocabulary.
# Unmapped types are logged and skipped gracefully rather than crashing.

LOOP_EVENT_MAP: dict[EngineId, dict[str, EventKind]] = {
    EngineId.CLAUDELOOP: {
        # Claudeloop events (captured from a real events.jsonl, same
        # conformance run that fixed agyloop's mapping -- claudeloop shares
        # the identical event/payload vocabulary, down to word-for-word
        # matching docstrings on _project_capacity in both runner.py files).
        "run.started": EventKind.SESSION_SEEDED,
        "preflight": EventKind.SESSION_SEEDED,
        "chatter.prompt": EventKind.TURN_REQUESTED,
        "turn.starting": EventKind.TURN_REQUESTED,
        "chatter.assistant": EventKind.TURN_COMPLETED,
        "turn.completed": EventKind.TURN_COMPLETED,
        "chatter.tool": EventKind.TOOL_INVOKED,
        "savepoint": EventKind.SAVEPOINT_CREATED,
        # capacity.forecast is proactive headroom telemetry emitted only
        # while capacity IS available (see runner.py::_project_capacity's
        # own docstring) -- never an actual rejection. See the identical
        # reasoning on EngineId.AGYLOOP's own capacity.forecast below.
        "capacity.forecast": EventKind.BUDGET_SPENT,
        "finished": EventKind.VERDICT_RENDERED,
    },
    EngineId.CODEXLOOP: {
        # Codex uses similar but not identical event names
        "thread.message.user": EventKind.TURN_REQUESTED,
        "thread.message.assistant": EventKind.TURN_COMPLETED,
        "tool.call": EventKind.TOOL_INVOKED,
        "rate_limit.hit": EventKind.CAPACITY_REJECTED,
        "credits.exhausted": EventKind.CAPACITY_REJECTED,
        "thread.started": EventKind.SESSION_SEEDED,
        "file.modified": EventKind.FILE_EDITED,
        # Codex-specific structured output events
        "output.verdict": EventKind.VERDICT_RENDERED,
        "output.question": EventKind.QUESTION_ASKED,
        "output.decision": EventKind.DECISION_RECORDED,
    },
    EngineId.CURSORLOOP: {
        # Cursor/Composer events
        "agent.message.user": EventKind.TURN_REQUESTED,
        "agent.message.assistant": EventKind.TURN_COMPLETED,
        "composer.tool_use": EventKind.TOOL_INVOKED,
        "agent.started": EventKind.SESSION_SEEDED,
        "agent.savepoint": EventKind.SAVEPOINT_CREATED,
        "file.change": EventKind.FILE_EDITED,
        "capacity.limited": EventKind.CAPACITY_REJECTED,
    },
    EngineId.AGYLOOP: {
        # Agyloop events (captured from real agyloop 0.1.0 events.jsonl)
        "run.started": EventKind.SESSION_SEEDED,
        "preflight": EventKind.SESSION_SEEDED,
        "chatter.prompt": EventKind.TURN_REQUESTED,
        "turn.starting": EventKind.TURN_REQUESTED,
        "chatter.assistant": EventKind.TURN_COMPLETED,
        "turn.completed": EventKind.TURN_COMPLETED,
        "sdk.event": EventKind.TOOL_INVOKED,
        "savepoint": EventKind.SAVEPOINT_CREATED,
        "savepoint.created": EventKind.SAVEPOINT_CREATED,
        "savepoint.skipped": EventKind.SAVEPOINT_CREATED,
        # capacity.forecast is emitted only while capacity IS available (see
        # runner.py::_project_capacity's own docstring: "only while the
        # vendor says we are not already blocked" -- it's proactive headroom
        # telemetry, never a rejection). Mapping it to CAPACITY_REJECTED
        # would make every normal, successful run look capacity-constrained.
        # BUDGET_SPENT matches its actual payload (headroom,
        # turns_until_exhaustion, seconds_until_reset).
        "capacity.forecast": EventKind.BUDGET_SPENT,
        "finished": EventKind.VERDICT_RENDERED,
    },
}


def translate_event_type(engine_id: EngineId, event_type: str) -> EventKind | None:
    """Map a loop's event_type to vibey's EventKind, or None if unrecognized.

    Unrecognized types should be logged and skipped, not raise - a new loop
    version emitting a new event type must not crash vibey.
    """
    engine_map = LOOP_EVENT_MAP.get(engine_id, {})
    return engine_map.get(event_type)


__all__ = ["LOOP_EVENT_MAP", "translate_event_type"]
