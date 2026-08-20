# vibey — real engines never complete a conformance run within the poll window

You are working in a fresh worktree off `origin/develop` on branch
`chore/e1-conformance-timeout`. Two real, confirmed bugs in this area were
already found and fixed by dogfooding (both merged to `develop`, do not
redo this part):

1. `LoopProcessAdapter.start()` used to root `run_dir` under a fixed
   `base_dir` instead of `spec.worktree_path` — fixed (PR #21, commit
   `48fd270`). `base_dir` no longer exists on `LoopProcessAdapter` at all.
2. `run_conformance()`'s scratch worktree used to be a bare (non-git)
   directory — fixed (same PR): it's now `git init`'d (with an empty
   commit) before a real adapter's `start()` is invoked.

## The remaining problem (not yet root-caused)

Even after both fixes, running `vibey doctor --conformance --engine agyloop`
against a fresh scratch dir — agyloop is the one engine authenticated in
this environment (`GOOGLE_API_KEY`/`GEMINI_API_KEY` set), so this is a real,
non-hypothetical failure, not an auth artifact — still fails four of the
nine conformance checks:

```
PASS binary
FAIL flags — adapter exposes no help text
PASS state_dir
FAIL run_dir_shape — missing: ['meta.json', 'events.jsonl', 'snapshots/latest.json']
FAIL snapshot_schema — no snapshot
PASS capacity_map
FAIL done_marker — expected 'AGYLOOP_TASK_FULLY_COMPLETE' in a verdict event
PASS control_plane
FAIL structured_verdict — no VerdictRendered event in scripted run
```

The adapter's own log shows it correctly polling
`<scratch>/.agyloop/runs/<run_id>/events.jsonl` (the path-mismatch bug is
confirmed fixed) for the full `run_dir_poll_seconds` budget (30s in
`run_conformance()`, plus up to another 10s inside `LoopProcessAdapter.tail()`
itself) — the file simply never appears there in that window, for a REAL,
authenticated agyloop process actually running.

A similar-looking but distinct earlier finding (from a previous session,
possibly now explained by one of the two fixes above, possibly not):
a real claudeloop conformance turn was observed completing successfully at
the SDK event-log level (`verdict: Done`, real token cost charged, a
`StructuredOutput` tool call reporting `{"complete":true,...}`) yet
claudeloop's own `meta.json` on disk still showed `"status": "failed"`.
Don't assume this is the same bug as the agyloop timeout above — verify
independently; it may already be fixed, or may be a second, distinct issue.

## What `run_conformance()` actually sends the engine

Read `src/vibey/application/conformance.py` in full — the relevant part is
around line ~85: it starts a run with `prompt="conformance check"` and
`effort=Effort.TRIVIAL`, in a scratch directory containing nothing but an
empty git repo and a one-line plan file at
`.vibey/plans/<run_id>.md` containing that same text.

## Your job: root-cause this properly, then fix it

Do not guess-and-patch. Investigate for real:

1. **Reproduce it directly, bypassing vibey.** Create a scratch dir, `git
   init` it, write a plan file with literally the text `conformance check`,
   and run `agyloop run <plan> --cwd <dir> --run-id <uuid> --preset low
   --effort low` yourself from the shell. Watch what it actually does:
   does it produce output at all? How long does it take? Does it ever
   write `events.jsonl`/`meta.json`/`snapshots/latest.json` under
   `<dir>/.agyloop/runs/<uuid>/`, and if so, where exactly, and after how
   long? If it never does, does the process hang forever, or does it exit
   (check the exit code and any stderr)?
2. **Form a real hypothesis before touching code.** Plausible candidates,
   in rough likelihood order — confirm or rule out each with actual
   evidence from step 1, don't just pick one:
   - The prompt `"conformance check"` is too vague for a real autonomous
     coding agent to act on. It has no concrete deliverable and nothing to
     verify against, so the agent may explore indefinitely, ask a
     clarifying question it never gets an answer to (this harness is
     non-interactive), or simply never reach a state where it emits a
     `done_marker`/renders a verdict. If so, the fix is almost certainly
     in `run_conformance()`: send a closed-ended, trivially-completable
     prompt instead (e.g. one that asks the agent to create one specific
     file with specific content and then declare the task complete) — not
     a change to any engine.
   - 30-40 seconds genuinely isn't enough wall-clock time for even a
     "low effort" real API turn plus whatever the engine does on startup
     (git status, session init, etc.) before its first write. If
     confirmed by direct measurement in step 1, the fix is likely to widen
     `run_dir_poll_seconds` for real (non-scripted) runs specifically —
     don't blindly increase it for the scripted/faked path too, since
     that would slow down every test that intentionally checks the
     negative case (see `test_run_dir_shape_waits_for_a_slow_real_engine_instead_of_racing_it`
     and the "negative case" test in `tests/application/test_conformance.py`
     for how the timeout is already exercised there).
   - agyloop writes real output somewhere other than
     `<cwd>/.agyloop/runs/<run_id>/` when given `--cwd` explicitly (an
     agyloop-side bug, not a vibey-side one). Rule this in or out by
     checking the full scratch directory tree after your direct-CLI repro
     in step 1, not just the one path vibey happens to poll.
3. **Fix the actual root cause**, wherever it lives (vibey's
   `conformance.py`, or a real agyloop bug if that's what you find —
   in which case fix it in `~/git/agyloop`, not by working around it in
   vibey). Add a regression test that would have caught this. If the fix
   is a longer poll budget, justify the specific number with what you
   measured in step 1, don't guess a round number.
4. **Verify for real**, not just via the unit suite: re-run
   `vibey doctor --conformance --engine agyloop` from a **fresh** scratch
   directory (delete `/tmp/vibey-conformance` first — it accumulates state
   across runs and that's a separate, lower-priority hygiene issue, not
   yours to fix here unless it's actually interfering with your
   verification) and confirm `run_dir_shape`, `snapshot_schema`,
   `done_marker`, and `structured_verdict` all pass. `flags` failing is a
   separate, known, unrelated gap (the adapter doesn't currently expose
   `--help` text at all — out of scope here, don't fix it as a drive-by).

## Budget discipline

This is real, metered API spend (Gemini calls via agyloop). Don't loop
blindly re-running the full conformance suite hoping something changes —
every run costs money and ~40+ real seconds. Reproduce once carefully with
maximum logging/observation, form a hypothesis, fix, verify once. If after
a genuinely careful investigation the root cause still isn't clear, stop,
write up exactly what you observed and ruled out, and leave it for a human
rather than continuing to spend down the budget on speculative fixes.

## Protected paths — do not merge without human review

`tests/live/**` is a protected path (per `docs/plans/fleet/README.md` and
`scripts/fleet/land.sh`'s own refusal check). If your fix touches anything
under `tests/live/`, `land.sh` will correctly refuse to auto-merge — leave
the PR open with a clear description of what changed and why; a human
will review and merge it.

## Gates

Standard 7-gate sweep, all four layers at 100% branch coverage:

```bash
uv run ruff check src tests && uv run ruff format --check src tests
uv run mypy --strict src/vibey
uv run lint-imports
uv run bandit -q -r src/vibey
uv run pip-audit
for L in domain application infrastructure cli; do
  uv run pytest -q -p no:cacheprovider --cov=vibey.$L --cov-branch --cov-fail-under=100
done
```

Mark the task complete only after the real (non-scripted, non-faked)
`vibey doctor --conformance --engine agyloop` verification in step 4 above
actually passes the four checks named there — not merely after the gates
above pass. A green gate sweep with the underlying real-engine bug still
unfixed is not done.
