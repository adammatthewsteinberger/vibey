"""Event type translation: loop event_type vocabulary → vibey EventKind.

Real loop events.jsonl files use dotted event_type strings ("chatter.assistant",
"sdk.message", "RateLimitEvent") rather than vibey's EventKind vocabulary.
This module maps the observed real event types to EventKind, engine by engine.

Event shapes discovered by running each loop in scripted mode (CLAUDELOOP_ALLOW_TEST_AGENT=1)
and inspecting the resulting events.jsonl files.
"""

from vibey.domain.engine import EngineId
from vibey.domain.ledger import EventKind

# Mapping from real loop event_type strings to vibey's EventKind vocabulary.
# Built from actual events.jsonl inspection, not documentation.
# Unmapped types are logged and skipped gracefully rather than crashing.

LOOP_EVENT_MAP: dict[EngineId, dict[str, EventKind]] = {
    EngineId.CLAUDELOOP: {
        # Chatter events (conversational turns)
        "chatter.user": EventKind.TURN_REQUESTED,
        "chatter.assistant": EventKind.TURN_COMPLETED,
        # SDK events (tool use)
        "sdk.tool_use": EventKind.TOOL_INVOKED,
        "sdk.text_created": EventKind.TURN_COMPLETED,
        # Capacity events
        "capacity.rate_limit": EventKind.CAPACITY_REJECTED,
        "capacity.credits_exhausted": EventKind.CAPACITY_REJECTED,
        "capacity.auth_failed": EventKind.CAPACITY_REJECTED,
        # Session lifecycle
        "session.started": EventKind.SESSION_SEEDED,
        "session.savepoint": EventKind.SAVEPOINT_CREATED,
        # File operations
        "file.edit": EventKind.FILE_EDITED,
        "file.write": EventKind.FILE_EDITED,
        # Structured outputs (when using output_format=json)
        "verdict.rendered": EventKind.VERDICT_RENDERED,
        "question.asked": EventKind.QUESTION_ASKED,
        "decision.recorded": EventKind.DECISION_RECORDED,
        "assumption.stated": EventKind.ASSUMPTION_STATED,
        "finding.raised": EventKind.FINDING_RAISED,
        "artifact.produced": EventKind.ARTIFACT_PRODUCED,
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
        # Gemini/Agy events
        "session.user_turn": EventKind.TURN_REQUESTED,
        "session.model_turn": EventKind.TURN_COMPLETED,
        "function.call": EventKind.TOOL_INVOKED,
        "session.init": EventKind.SESSION_SEEDED,
        "quota.exceeded": EventKind.CAPACITY_REJECTED,
        "resource.exhausted": EventKind.CAPACITY_REJECTED,
        "file.updated": EventKind.FILE_EDITED,
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
