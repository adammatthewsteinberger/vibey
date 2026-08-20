# Runbook: every engine confirmed live

## Goal

All engines — claudeloop, agyloop, codexloop, cursorloop, and (post-02)
copilotloop — hold green 9/9 conformance and at least one paid live work
item each, so rotation runs across the full pool instead of the two
currently proven.

## Current state (verified this week)

| Engine | State |
|---|---|
| claudeloop | Fully live-proven (greeter3/greeter4 runs, dozens of sessions) |
| agyloop | Fully live-proven (implement + verify roles, cross-engine) |
| codexloop | **Broken live**: a real `codexloop run` produced 0 `events.jsonl` lines in ~12 minutes; probe killed; no health row → honestly excluded. Its vocabulary in `LOOP_EVENT_MAP` was source-verified (#34) but never validated against captured runtime output. |
| cursorloop | **Blocked on auth**: `doctor` fails wanting `CURSOR_API_KEY`. Untested beyond that. |

## Plan per engine

### codexloop

1. Reproduce with full stderr capture: `codexloop run <plan> --run-id X
   --cwd <tmp>` on a trivial plan; inspect `.codexloop/runs/X/` for
   meta.json presence vs events absence (is the run alive but silent, or
   dead at spawn?).
2. Root-cause in the codexloop repo (`~/git/codexloop`) — likely suspects:
   event sink never flushed, stdout-vs-file mode flag, or an auth failure
   swallowed before the first event.
3. Fix in codexloop (its own tests), then capture a real run's
   `events.jsonl` and reconcile vibey's `LOOP_EVENT_MAP` +
   `capacity fixtures` against **captured** output (replacing
   source-read-only verification).
4. `vibey doctor --conformance` → 9/9; then one paid greeter work item.

### cursorloop

1. Operator provides `CURSOR_API_KEY` (Cursor dashboard → API keys).
2. `cursorloop doctor` green; capture a real run; reconcile event map
   the same way (its map is also source-verified only).
3. Conformance 9/9 + one paid live item.

### copilotloop

Covered by runbook 02; its acceptance bar lands here: conformance 9/9 +
one live item.

### Pool-level proof

With ≥4 engines healthy: a multi-item BUILD where rotation demonstrably
spreads implements across the pool (selected_count deltas per engine in
`engine_health`), verify always lands on a non-implementer, and one
forced-rotation tier crossing picks a different engine.

## Verification

- `vibey doctor --conformance --record` shows 9/9 for every engine.
- Each engine has ≥1 succeeded paid `build.implement` in a real project
  ledger, with TurnCompleted `cost_usd` recorded (budget brake visibility
  now depends on it — engines whose events omit cost get a runner-side
  work item to emit it).
- Rotation spread proof archived in the validation report.

## Needs from operator

- `CURSOR_API_KEY` exported (or in the env file the worker loads).
- Nothing for codexloop unless root-cause turns out to be its own expired
  auth (`codex login` may need a refresh).
- Copilot needs per runbook 02.

## Risks

- Vendor event vocabularies drift — captured-output reconciliation is the
  bar everywhere now, and workstream 04 watches the changelogs after.
- agyloop emits no `cost_usd` today (36/72 TurnCompleted events in
  greeter4 carried cost — the claudeloop half). Turns still count toward
  turn caps, but dollar caps under-read on agyloop-heavy cycles until its
  runner emits cost.
