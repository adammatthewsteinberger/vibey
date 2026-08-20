# codexloop — Phase C4: wire the (already-built) event sink into a real run

You are working unattended in a disposable git worktree of `codexloop`
(`~/git/codexloop`), on branch `chore/c4-wire-events-sink`. `--cwd` doesn't
exist on `codexloop run` yet (a separate known gap — Phase C) so `cd` into
the worktree before invoking `codexloop` rather than passing a flag that
isn't there.

This is a real, mature codebase — 100% branch-covered on all four
architectural layers, CI-gated. Do not weaken any gate, delete a test, or
add a coverage exclusion to get to green.

## Why this task exists

Found 2026-08-18 while vibey (the downstream conductor that drives
`codexloop` as one of four autonomous engines) was correcting its own
`LOOP_EVENT_MAP` — the table that translates `codexloop`'s real
`events.jsonl` line-by-line `event_type` strings into vibey's internal
event vocabulary. That correction needed a real, captured `events.jsonl`
to verify against, the same way it was done for `claudeloop` and `agyloop`
earlier. There wasn't one to capture.

`src/codexloop/infrastructure/events.py::JsonlRunEventSink` is fully
implemented and has its own passing unit tests
(`tests/infrastructure/test_rundir_state.py::test_event_sink_creates_missing_file`,
`::test_event_sink_appends_redacted_jsonl`) — but it is **never
constructed anywhere outside those tests.** `grep -rn "JsonlRunEventSink("
src/` turns up nothing. `bootstrap.py` never imports it. Confirmed
empirically too, not just by reading the source: running

```bash
CODEXLOOP_ALLOW_TEST_AGENT=1 CODEXLOOP_TEST_AGENT_SCRIPT=tests/live/fixtures/agent_scripts/done.json \
  codexloop run plan.md
```

to a real, successful completion (`done  turns=1  thread=scripted-done`) in
a scratch git worktree leaves `.codexloop/runs/<id>/events.jsonl` at **0
bytes**. The file is touched by `RunDirectory.ensure_layout()` and never
written again by anything.

This means:
- `codexloop watch` / `run --stream-ui` (`run_stream_ui_for_events`) has
  nothing to tail — the Textual live view is watching a file that never
  gets a line written to it.
- vibey's downstream ledger gets zero mid-run visibility into a real
  `codexloop` run: no turn boundaries, no tool activity, no rate-limit
  telemetry — only the coarse `meta.json` status flips at the very start
  and very end.
- The real event vocabulary *does* exist and *is* fully parsed in memory
  already — `infrastructure/agent/events.py::JsonlParser` recognizes
  `thread.started`, `turn.started`, `turn.completed`, `turn.failed`,
  `item.started`, `item.completed`, `rate_limits.updated`, `event_msg`,
  `error` from the wrapped `codex exec --json` subprocess's own stdout —
  it just gets discarded after `CodexExecGateway.send_turn()` folds it
  into one `TurnSignals` summary via `to_turn_signals()`. The raw,
  per-event detail behind that summary is thrown away instead of
  persisted.

## Task

Wire real events onto disk during a run, using the vocabulary that's
already parsed. The natural insertion point is `CodexExecGateway`
(`infrastructure/agent/gateway.py`): it already has `self._parse_lines()`
producing a `list[CodexEvent | None]` from `result.stdout_lines` before
folding it into signals. Thread an optional event sink through:

1. `CodexExecGateway.__init__` — accept something sink-shaped (reuse
   `JsonlRunEventSink`, or define a small `Protocol` in `application/ports.py`
   if the layering rules require it — check how `RunEventSink` is done in
   `cursorloop` for a parity reference, but don't assume cursorloop's
   design is bug-free; see the companion cursorloop task, which has its own
   wiring gap).
2. `bootstrap.py::build_runner` — construct `JsonlRunEventSink(run_dir.events_path)`
   (mirroring the existing dead-but-tested class) and pass it to
   `CodexExecGateway`.
3. In `send_turn()`, after parsing events, emit each non-`None` `CodexEvent`
   to the sink using its **real** type string — the same literals
   `JsonlParser` already recognizes, not new ones you invent. Decide a
   reasonable payload per event kind (e.g. `thread_id` for
   `ThreadStarted`, `usage` fields for `TurnCompleted`, the error fields
   for `TurnFailed`/`ErrorEvent`, the raw `item` mapping for
   `ItemStarted`/`ItemCompleted`, the `plan_windows` fields for
   `RateLimitsUpdated`). `UnknownEvent` instances carry their own `.type`
   string already — emit those too, unmodified, rather than dropping them;
   that's exactly the forward-compatible behavior vibey's own
   `translate_event_type()` already assumes (skip gracefully, don't
   crash).

Also decide, and document your decision either way: should
`AutonomousRunner`/`run_plan.py` additionally emit codexloop-authored
wrapper-level boundary events (a `run.started` at the top of a run, a
`finished` at the end) analogous to what `claudeloop` and `agyloop` already
write into their own `events.jsonl`? Right now codexloop has no such
markers at all — only the raw `codex exec --json` passthrough vocabulary,
once wired. Adding them would bring codexloop's `events.jsonl` shape in
line with the other two live-verified engines and let vibey detect
`VerdictRendered`-equivalent moments from the event stream instead of
`meta.json` alone. Not adding them is also acceptable, but say why.

## Tests

Test-first. Unit-level: assert `CodexExecGateway.send_turn()` calls the
sink with the correct type strings and payload shape for a scripted
`ProcessResult` fixture covering at least one of each `CodexEvent` variant.
Integration-level: extend
`tests/live/system/test_subprocess_smoke.py::test_subprocess_done_exits_0`
(or add a sibling test right next to it, same file) to additionally assert
the run's `events.jsonl` is non-empty and every line parses as JSON with a
recognized `event_type` — this is the regression test that would have
caught today's gap; a green `codexloop run` that leaves the file empty
must fail this test.

Keep all four layers at 100% branch coverage. Full 7-gate sweep: ruff
check/format, `mypy --strict src/codexloop`, the four
`pytest --cov=<layer> --cov-fail-under=100` runs, `lint-imports`, `bandit`,
`pip-audit`. Re-run the full suite 3-5 times before trusting green.

## Smoke test

After your fix, this must produce a populated file, not an empty one:

```bash
cd /tmp/some-scratch-git-repo
CODEXLOOP_ALLOW_TEST_AGENT=1 CODEXLOOP_TEST_AGENT_SCRIPT=~/git/codexloop/tests/live/fixtures/agent_scripts/done.json \
  codexloop run plan.md
find .codexloop -name events.jsonl -exec wc -l {} \;
# must be > 0 lines, each valid JSON, each with a recognized event_type
```

## Done

Full gate sweep green, Conventional Commit, end your final message with
**CODEXLOOP_TASK_FULLY_COMPLETE** — only when genuinely done. If something
in this plan turns out to be wrong once you're in the code (e.g. a cleaner
insertion point than `CodexExecGateway`), use your judgment and document
why you diverged.
