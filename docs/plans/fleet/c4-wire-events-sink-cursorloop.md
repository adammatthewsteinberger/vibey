# cursorloop — Phase C4: wire the event sink into scripted (offline) runs too

You are working unattended in a disposable git worktree of `cursorloop`
(`~/git/cursorloop`), on branch `chore/c4-wire-events-sink`. `cursorloop`
has good `--cwd` coverage — use it explicitly on every subcommand that
supports it.

This is a real, mature codebase — 100% branch-covered on all four
architectural layers, CI-gated. Do not weaken any gate, delete a test, or
add a coverage exclusion to get to green.

## Why this task exists

Found 2026-08-18 alongside the identical-shaped codexloop gap
(`c4-wire-events-sink-codexloop.md`), while vibey (the downstream conductor
that drives `cursorloop` as one of four autonomous engines) was correcting
its own `LOOP_EVENT_MAP` for `cursorloop` and needed a real, captured
`events.jsonl` to verify against.

Unlike codexloop, cursorloop's event sink **is** wired for real use —
`bootstrap.py::build_runner` constructs
`event_sink = JsonlRunEventSink(run_dir.events_path, run_id=run_id, trace_id=trace_id)`
and passes it into `CursorAgentGateway(..., event_sink=event_sink)`, which
hands it to `infrastructure/agent/translate.py::TeeStream`. `TeeStream`
really does call `self._sink.emit("tool_call", ...)` /
`self._sink.emit("status", ...)` / `self._sink.emit("usage", ...)` while
draining a live Cursor Agent SDK run — those three string literals are
hardcoded verbatim in `_on_tool_call`/`_on_status`/`_on_usage`, so they're
genuine, not guessed.

But `build_runner` has two branches:

```python
scripted = resolve_test_agent_from_env()
if scripted is not None:
    gateway, probe = scripted          # <-- event_sink never reaches here
else:
    ...
    gateway = CursorAgentGateway(..., event_sink=event_sink)
```

The scripted/offline branch — the *only* branch reachable in this
environment (no `CURSOR_API_KEY`, and presumably in most CI too) — throws
the constructed `event_sink` away entirely.
`infrastructure/agent/scripted.py::resolve_test_agent_from_env` already
accepts an `on_event: Callable[[dict[str, object]], None] | None` parameter
that `ScriptedAgentGateway` will call for each `ScriptedTurn.raw_events`
entry — `build_runner` just never passes one.

Confirmed empirically, not just by reading the source: a full scripted
`cursorloop run --plan plan.md` against
`tests/live/fixtures/agent_scripts/done.json` in a scratch git worktree
left `.cursorloop/runs/<id>/events.jsonl` at **0 bytes**. (Separately, that
same run also hit `ScriptedAgentGateway: no turns left in script` on a
second, unexpected `send_turn` call — the runner sent a continuation
prompt after the scripted "done" turn instead of recognizing completion.
That's a different bug in completion detection, not part of this task's
scope, but worth a one-line mention in your PR description so it's not
lost — don't fix it here unless it's trivially in the way.)

This means the entire two-mode (faked/live) harness strategy that
`cursorloop` and vibey both rely on for testing event-stream behavior
without live credentials is currently blind in offline mode: the only path
that ever populates `events.jsonl` needs a real `CURSOR_API_KEY` and a real
SDK session, which most CI and most local dogfooding runs don't have.

## Task

1. Pass an `on_event` callback into `resolve_test_agent_from_env()` in the
   `scripted is not None` branch of `build_runner`, forwarding into the
   already-constructed `event_sink` — match `RunEventSink.emit(event_type,
   payload)`'s two-argument shape against `on_event`'s
   single-dict-argument shape (check
   `application/interfaces/observability.py::RunEventSink`'s exact
   Protocol signature and `ScriptedAgentGateway.send_turn`'s call site in
   `scripted.py` for the dict shape it actually passes — likely something
   like `{"type": ..., **rest}` — before deciding how to split it).
2. Give at least one of the fixture agent scripts under
   `tests/live/fixtures/agent_scripts/` (or a new one added alongside them)
   a `raw_events` list on its turn(s) so the wiring has something real to
   carry end-to-end, and so the regression test below has fixture data to
   assert against.
3. Document, in the same place you found this gap, that (once wired)
   cursorloop's `events.jsonl` still has **no wrapper-level session/turn/
   verdict boundary marker** at all — only in-turn SDK message types
   (`tool_call`/`status`/`usage`). Decide whether `AutonomousRunner`
   (`application/runner.py`) should additionally emit its own
   `run.started`/`finished`-shaped events into the sink for parity with
   claudeloop/agyloop (recommended — `self._log.info("run.started", ...)`
   and the `"finished"` `run_status` value already exist at
   `application/runner.py:152` and `:521`, but those go to the structured
   `Logger`, not `RunEventSink` — this task doesn't require making that
   change, but say clearly in your PR whether you did or didn't and why).

## Tests

Test-first. Unit-level: assert `build_runner`'s scripted branch actually
forwards `on_event` and that it reaches the constructed sink (a fake sink
double, or reading the real file back, either is fine — match the existing
test style in `tests/bootstrap/test_build_runner_bridge.py`). Integration-
level: a scripted `cursorloop run` end-to-end (same shape as
`tests/live/system/test_subprocess_smoke.py`, or extend
`tests/live/system/test_matrix_inprocess.py` if that's the more idiomatic
in-process harness for this repo) asserting the run's `events.jsonl` is
non-empty and every line parses as JSON with one of the three real
`event_type` values. A green run that leaves the file empty must fail this
test — that's exactly the regression this task exists to close.

Keep all four layers at 100% branch coverage. Full 7-gate sweep: ruff
check/format, `mypy --strict src/cursorloop`, the four
`pytest --cov=<layer> --cov-fail-under=100` runs, `lint-imports`, `bandit`,
`pip-audit`. Re-run the full suite 3-5 times before trusting green.

## Smoke test

After your fix, this must produce a populated file, not an empty one:

```bash
cd /tmp/some-scratch-git-repo
CURSORLOOP_ALLOW_TEST_AGENT=1 CURSORLOOP_TEST_AGENT_SCRIPT=~/git/cursorloop/tests/live/fixtures/agent_scripts/done.json \
  cursorloop run --plan plan.md --cwd .
find .cursorloop -name events.jsonl -exec wc -l {} \;
# must be > 0 lines once the fixture script carries raw_events
```

## Done

Full gate sweep green, Conventional Commit, end your final message with
**CURSORLOOP_TASK_FULLY_COMPLETE** — only when genuinely done. If the
`on_event`/`RunEventSink` signature mismatch turns out to need a small
adapter shim rather than a direct pass-through, that's fine — just keep it
in `infrastructure/`, not leaking into `application/`.
