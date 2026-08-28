# Made with ❤️ by [Vibey](https://adammatthewsteinberger.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
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
It was replaced (2026-08-18) with vocabulary read directly from each
engine's own source -- real string literals their own code already
recognizes or emits, not fabrications. At the time, neither engine wrote
anything into events.jsonl in this environment at all (both sinks were
fully implemented but not wired into the real run path -- see
docs/plans/fleet/c4-wire-events-sink-{codexloop,cursorloop}.md); both gaps
were fixed and landed the same day (codexloop#30, cursorloop#27). Current
verification status per engine:

- CODEXLOOP: `infrastructure/events.py::JsonlRunEventSink` is now
  constructed in `bootstrap.py` and wired into `CodexExecGateway`, which
  emits the vocabulary below (sourced from
  `infrastructure/agent/events.py::JsonlParser`, the exact type strings it
  parses from the wrapped `codex exec --json` subprocess's own stdout) to
  the sink after every turn. Verified end to end with a real subprocess
  smoke test -- a fake `codex` binary on PATH (codexloop's own
  `tests/shim/fake_codex.py` harness) driving the real, unmodified
  `CodexExecGateway.send_turn` code path -- confirming events.jsonl is
  genuinely populated with this vocabulary. Not yet observed against a
  live, authenticated `codex` CLI session, since `codex` isn't installed
  in this environment.
- CURSORLOOP: the sink is now wired into the scripted/test-agent path too
  (previously live-SDK-only), confirmed by a real scripted `cursorloop
  run` populating events.jsonl. That confirms the forwarding mechanism,
  not the vocabulary itself: the actual event types
  (`tool_call`/`status`/`usage`) still come only from
  `infrastructure/agent/translate.py::TeeStream`'s
  `_on_tool_call`/`_on_status`/`_on_usage`, which only executes in the
  live Cursor Agent SDK path -- those three string literals are hardcoded
  verbatim in that source (reading them is equivalent to observing them),
  but still unconfirmed against a real live SDK session, since no
  CURSOR_API_KEY is available here. Cursorloop also has no wrapper-level
  session/turn/verdict boundary event in events.jsonl at all, unlike the
  other three engines -- only in-turn SDK message types.
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
        # own event stream. See the module docstring: now wired end to end
        # and verified with a real subprocess smoke test (fake codex
        # binary, real CodexExecGateway code path), though not yet against
        # a live, authenticated codex CLI session.
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
        # codexloop's own wrapper-level terminal verdict (codexloop#35),
        # the one event in its stream that is not raw codex vocabulary. It
        # carries success/complete/reason and, on success only, the done
        # marker -- previously nothing published the marker at all, so a
        # finished codexloop run was indistinguishable from an abandoned
        # one to any reader of events.jsonl.
        "run.verdict": EventKind.VERDICT_RENDERED,
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
        # the sink is wired for both scripted and live runs now, but this
        # specific vocabulary only ever flows from TeeStream, which only
        # runs in the live SDK path -- still unobserved live here (no
        # CURSOR_API_KEY). Cursorloop's events.jsonl never carries a
        # session/turn/verdict boundary marker at all, only these in-turn
        # types.
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
    EngineId.QWENLOOP: {
        "run.started": EventKind.SESSION_SEEDED,
        "text_delta": EventKind.TURN_COMPLETED,
        "tool_result": EventKind.TOOL_INVOKED,
        "completed": EventKind.VERDICT_RENDERED,
        "failed": EventKind.VERDICT_RENDERED,
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
