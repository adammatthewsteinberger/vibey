# vibey — loop_events.py doesn't recognize agyloop's real event_type strings

Not yet launched. Written up for queueing after landing
`e1-loopadapter-conformance-hang-vibey.md`'s fix (the tail() infinite-hang
bug and the run_dir/GC/DEVNULL/scratch-dir fixes) — that fix got
`run_dir_shape` and `snapshot_schema` passing against a real, healthy
agyloop for the first time. This is the next, narrower, already-diagnosed
gap it uncovered.

## The problem, already confirmed

`vibey doctor --conformance --engine agyloop` now runs a real turn to
completion and reads its `events.jsonl` correctly (confirmed: `PASS
run_dir_shape`, `PASS snapshot_schema`), but every single event in it logs
as `unknown_event_type` and gets silently skipped:

```
chatter.prompt, sdk.event, chatter.assistant, turn.completed, savepoint,
capacity.forecast, finished, run.started, preflight, turn.starting
```

None of these `event_type` strings has an entry in
`src/vibey/infrastructure/engines/loop_events.py`'s `LOOP_EVENT_MAP` for
`EngineId.AGYLOOP`. `translate_event_type()` returns `None` for every one,
so `LoopProcessAdapter.tail()` never yields a single `EngineEvent` for a
real agyloop run — which is why `done_marker` (`expected
'AGYLOOP_TASK_FULLY_COMPLETE' in a verdict event`) and `structured_verdict`
(`no VerdictRendered event in scripted run`) both fail: the code they
check (`for event in events: ...`) is iterating an empty list every time,
regardless of what agyloop actually did.

## What to do

1. Read `src/vibey/infrastructure/engines/loop_events.py` in full — see
   what event_type → EventKind mapping already exists for the other three
   engines (claudeloop/codexloop/cursorloop) as the pattern to follow.
2. Capture a real agyloop `events.jsonl` from a real run (e.g. `agyloop run
   <plan> --cwd <dir> --run-id <id> --preset low --effort low` against a
   trivially-completable prompt, then read the resulting
   `.agyloop/runs/<id>/events.jsonl`) and read every distinct `event_type`
   value plus its `payload` shape directly, rather than guessing from the
   list above alone — there may be more event types than what one short
   conformance run happened to produce.
3. Add entries to `LOOP_EVENT_MAP` for `EngineId.AGYLOOP` mapping each real
   event_type to the correct `domain.ledger.EventKind`. In particular:
   `finished` (or whatever event carries the actual completion payload —
   read the real payload shape, don't assume) needs to map to something
   `structured_verdict`'s check will recognize (`EventKind.VerdictRendered`
   equivalent), and its payload needs to actually carry
   `descriptor.done_marker` (`AGYLOOP_TASK_FULLY_COMPLETE`) somewhere
   `conformance.py`'s `done_marker` check reads it
   (`event.payload.get("done_marker")`) — trace exactly how agyloop's own
   `AGYLOOP_TASK_FULLY_COMPLETE` marker text ends up (or doesn't) in the
   `finished` event's payload; it may need a payload-shape fix here too,
   not just a mapping addition, if agyloop doesn't put the marker text
   anywhere `events.jsonl` captures.
4. Add regression tests in `tests/infrastructure/engines/test_loop_events.py`
   (or wherever the existing per-engine mapping tests live) using real
   captured event shapes, not synthetic ones.
5. `flags` (`adapter exposes no help text`) is a separate, known,
   pre-existing gap — don't fix it here as a drive-by.

## Verify for real

`vibey doctor --conformance --engine agyloop` should go from 6/9 to 8/9
passing (only `flags` still failing, tracked separately). Don't declare
done from the gate sweep alone — confirm `done_marker` and
`structured_verdict` actually flip to PASS in a real run.

## Budget discipline

Same as the other harness/adapter plans in this directory: read real
captured data before writing the mapping, don't guess payload shapes,
verify with one real end-to-end run rather than repeated live-cost
iteration.

## Gates

Standard vibey 7-gate sweep, all four layers at 100% branch coverage (see
`docs/plans/fleet/e1-conformance-timeout-vibey.md` for the exact
commands).
