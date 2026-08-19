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
...: none of these are real).

CODEXLOOP and CURSORLOOP previously carried that same unverified guesswork.
It has been replaced (2026-08-18) with vocabulary read directly from each
engine's own source -- real string literals their own code already
recognizes or emits, not fabrications -- but it is **not** live-capture
verified the way CLAUDELOOP/AGYLOOP's is, because neither engine currently
writes anything into events.jsonl in this environment:

- CODEXLOOP: `infrastructure/events.py::JsonlRunEventSink` is fully
  implemented and unit-tested but never constructed anywhere in
  codexloop's own `src/` outside its tests -- confirmed by source grep and
  empirically, by running `codexloop run` to a real successful completion
  in scripted mode and finding events.jsonl at 0 bytes. The vocabulary
  below is what `infrastructure/agent/events.py::JsonlParser` recognizes
  from the wrapped `codex exec --json` subprocess's own stdout -- genuine,
  but currently unreachable until the sink gets wired. See
  docs/plans/fleet/c4-wire-events-sink-codexloop.md.
- CURSORLOOP: the sink is wired, but only for the live Cursor Agent SDK
  path (`bootstrap.py::build_runner`'s non-scripted branch); the
  scripted/test-agent branch discards it. Confirmed empirically the same
  way: a full scripted `cursorloop run` left events.jsonl at 0 bytes. The
  vocabulary below is hardcoded verbatim in
  `infrastructure/agent/translate.py::TeeStream`'s
  `_on_tool_call`/`_on_status`/`_on_usage` methods -- genuine, reachable
  only in live mode (untested here -- no CURSOR_API_KEY). Cursorloop also
  has no wrapper-level session/turn/verdict boundary event in
  events.jsonl at all, unlike the other three engines -- only in-turn SDK
  message types. See docs/plans/fleet/c4-wire-events-sink-cursorloop.md.

Both gaps are real bugs in codexloop/cursorloop themselves, not vibey
guesses papering over them -- queued as separate fleet plan files rather
than fixed inline here, since each involves wiring/design decisions in
that engine's own codebase.
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
        # Real `codex exec --json` vocabulary, sourced directly from
        # codexloop's own infrastructure/agent/events.py::JsonlParser --
        # the exact type strings it parses from the wrapped codex CLI's
        # own event stream. See the module docstring: this is genuine,
        # source-verified vocabulary, not a live capture (the sink that
        # would write it to events.jsonl isn't wired yet).
        "thread.started": EventKind.SESSION_SEEDED,
        "turn.started": EventKind.TURN_REQUESTED,
        "turn.completed": EventKind.TURN_COMPLETED,
        # turn.failed is still a turn boundary -- success/failure lives in
        # the payload, mirroring how VERDICT_RENDERED enrichment elsewhere
        # checks payload fields rather than encoding it into the kind.
        "turn.failed": EventKind.TURN_COMPLETED,
        # "item" is codex's generic envelope for a discrete unit of agent
        # work -- command execution, patch application, MCP tool calls,
        # reasoning, AND plain agent messages all arrive as item.started/
        # item.completed with the real distinction only in a payload
        # ``type`` field this string-keyed map can't see. Approximated as
        # TOOL_INVOKED, the closest existing EventKind, same coarseness
        # claudeloop/agyloop already accept for their own tool events.
        "item.started": EventKind.TOOL_INVOKED,
        "item.completed": EventKind.TOOL_INVOKED,
        # rate_limits.updated is proactive plan/window telemetry folded
        # into TurnSignals for classification -- it is not itself a
        # rejection (see domain/classify.py: rejection comes from
        # error_code/error_type/http_status, never straight from this
        # event), so it gets the same BUDGET_SPENT treatment as
        # claudeloop/agyloop's capacity.forecast.
        "rate_limits.updated": EventKind.BUDGET_SPENT,
        # "error" and "event_msg" deliberately left unmapped: both are
        # generic wrapper types whose real meaning depends on payload
        # contents this string-keyed map can't see (event_msg mostly
        # carries unrelated telemetry and only rarely means rate-limit
        # data; "error" spans everything from a transient tool hiccup to
        # a fatal auth failure). translate_event_type() already treats an
        # unmapped type as "log and skip" -- the honest choice here.
    },
    EngineId.CURSORLOOP: {
        # Real Cursor Agent SDK vocabulary, hardcoded verbatim in
        # cursorloop's own infrastructure/agent/translate.py::TeeStream
        # (_on_tool_call/_on_status/_on_usage). See the module docstring:
        # genuine, source-verified, but only reachable via the live SDK
        # path in cursorloop today (untested here -- no CURSOR_API_KEY),
        # and cursorloop's events.jsonl never carries a session/turn/
        # verdict boundary marker at all, only these in-turn types.
        "tool_call": EventKind.TOOL_INVOKED,
        "usage": EventKind.BUDGET_SPENT,
        # "status" deliberately left unmapped: it's a free-text SDK
        # status message (whatever text the Cursor Agent SDK sends), not
        # a fixed vocabulary -- no single EventKind fits every value it
        # can carry.
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
