# vibey — E1 fixup: `build_argv` never passes `--run-id`, so the adapter can never find its own runs

You are continuing work on branch `chore/e1-live-engines` (this worktree).
All four layers are genuinely at 100% branch coverage and all 7 gates pass
— that work is real and should not be redone. But **the coverage floor
does not catch this bug**, because it's a real-subprocess integration gap
that only shows up when `LoopProcessAdapter` drives an actual installed
binary, not a mock. It was found by literally running
`vibey doctor --conformance` against real `claudeloop`/`codexloop`/
`cursorloop`/`agyloop` installs and reading the real run directories those
processes created.

## The bug, confirmed

`src/vibey/infrastructure/engines/loop_process_adapter.py:127`
pre-computes the run directory the adapter will look for:

```python
run_dir = self.base_dir / self.descriptor.state_dir / "runs" / str(spec.run_id)
```

But `src/vibey/infrastructure/engines/argv.py::build_argv()` never passes
`--run-id` to the spawned process — read the whole function, it's short.
Every one of the four loop CLIs supports `--run-id <str>` on `run`
(confirmed in each repo's own `run --help`), but nothing in `build_argv`
uses `spec.run_id` for anything except the plan-file path
(`argv.py:16`). So the spawned process falls back to generating **its
own** run-id (each loop's own scheme — e.g. claudeloop's is a
timestamp-based `20260817T194343Z-3c715e6a`, not vibey's UUID), and
writes its real `meta.json`/`events.jsonl`/`snapshots/latest.json` into
`.{engine}loop/runs/<the-loop's-own-id>/` — a directory `LoopProcessAdapter`
never looks in, because it's holding `spec.run_id` (vibey's UUID) instead.

**This is the single root cause of four of the nine conformance checks
failing identically across all four engines**: `run_dir_shape` (missing
meta.json/events.jsonl/snapshots/latest.json), `snapshot_schema` (no
snapshot found — it's looking in the wrong directory), `done_marker`
(same reason), `structured_verdict` (same reason). Confirmed by direct
inspection: a real conformance run against claudeloop produced a genuine,
complete run directory with all expected files at
`.claudeloop/runs/20260817T194343Z-3c715e6a/` — the adapter just never
found it because it was looking for `.claudeloop/runs/8934e8b0-.../`
(vibey's run_id) instead.

## The fix

Add `--run-id <spec.run_id>` to the argv `build_argv` constructs, for the
`run` verb (new sessions) — not `resume`, which takes the loop's own
session/run identifier differently per engine (check each descriptor;
don't assume `resume` needs the same treatment without verifying against
each loop's actual `resume --help`). Insert it in a sensible, consistent
position relative to the plan path and the other flags — look at how the
fleet runbook's own documented invocations order flags
(`run <plan> --run-id <id> --cwd <dir> ...`) for a reasonable default, but
what matters is correctness and golden-file consistency, not exact
position.

**This will break the golden argv fixture tests on purpose** —
`tests/infrastructure/engines/golden/*.txt` (20 files: 4 engines × 5
efforts) are byte-for-byte expected argv strings that predate this fix and
don't have `--run-id` in them. Regenerate all 20 to include the new flag in
whatever position you chose, and confirm the golden test
(`tests/infrastructure/engines/test_argv.py` or wherever it lives) still
asserts byte-for-byte equality — don't loosen the assertion to work around
the diff, fix the fixtures.

## Verification — do this for real, don't estimate

1. Full 4-layer coverage + 7-gate sweep, same as before (you already know
   the commands — `pyproject.toml`/`ci.yml` are the source of truth).
2. **Re-run the actual scenario that found this bug**, cheaply — one real
   engine is enough to confirm the fix, not all four (conserve API spend):
   ```bash
   uv run vibey doctor --conformance --engine claudeloop
   ```
   Confirm `run_dir_shape`, `snapshot_schema`, `done_marker`, and
   `structured_verdict` genuinely pass now (or at minimum that the adapter
   is now looking in — and finding — the same directory the real process
   wrote to; if `done_marker`/`structured_verdict` still fail for a
   *different* reason now that the path is right, that's useful new
   information, report it precisely rather than declaring done).
3. Inspect the real run directory this produces
   (`.claudeloop/runs/<the-uuid-you-passed>/`) and confirm it exists and
   is named after the run_id vibey actually asked for, not the loop's own
   generated fallback.

**Before you report done:** this task exists specifically because a
previous "all gates green" claim on unrelated work was contradicted by
directly inspecting real output — do the same discipline here. A green
coverage run does not prove this specific bug is fixed, since none of the
existing tests exercised a real subprocess against this exact path
(they use `ScriptedEngine`, which is why this got past every fake). Only
the real `doctor --conformance` invocation above proves it.

Commit on the same branch (`chore/e1-live-engines`), don't open a new one.

Done: **CLAUDELOOP_TASK_FULLY_COMPLETE** — only after you've personally
run the real conformance check and seen the specific four checks that were
failing now pass (or precisely diagnosed what's left, if anything is).
