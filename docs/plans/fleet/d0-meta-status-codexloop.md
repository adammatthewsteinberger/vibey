# codexloop — Phase D0: write a terminal status to meta.json

You are working unattended in a disposable git worktree of `codexloop`
(`~/git/codexloop`), on branch `chore/d0-meta-status`. `--cwd` doesn't
exist on `codexloop run` yet (a separate known gap — Phase C) so `cd` into
the worktree before invoking `codexloop` rather than passing a flag that
isn't there.

This is a real, mature codebase — 100% branch-covered on all four
architectural layers, CI-gated. Do not weaken any gate, delete a test, or
add a coverage exclusion to get to green.

## Why this task exists

Found 2026-08-19 by vibey (the downstream conductor that drives codexloop
as one of four autonomous engines) while proving out its own
`LoopProcessAdapter`/`vibey worker` machinery end to end against real
installed binaries, not fakes.

`infrastructure/rundir.py`'s `RunDirectory.create()` writes `meta.json`
**exactly once**, at run-directory creation
(`if not self.meta_path.is_file(): self.meta_path.write_text(...)`), and
nothing anywhere else in `src/codexloop/` ever touches it again — confirmed
by `grep -rn "meta_path" src/` (only two hits, both in `rundir.py`, both at
creation) and empirically, by running a full, successful, scripted
`codexloop run` to completion and reading the result:

```json
{"run_id": "test-run-2", "pid": 60448, "started_at": "2026-08-19T01:42:53.644119+00:00"}
```

No `status` field, ever, on any exit path — success, failure, or crash.
codexloop instead records completion in `.codexloop/runs/<id>/state.json`,
which after the same run reads:

```json
{"thread_id": "scripted-done", "turns": 1, "dollars": 0.0, "elapsed_seconds": 0.000555, "remaining_work": [...], "first_turn_done": true, "plan_text": "...", "reason": "done"}
```

Compare this to the other three engines vibey drives — claudeloop,
agyloop, cursorloop — every one of which writes `meta.json`'s `status`
field through a shared vocabulary (`active` → `finished` / `failed` /
`stopped`) at the relevant lifecycle transitions. That vocabulary is not
an arbitrary convention on vibey's side: it's the *only* signal
`LoopProcessAdapter.tail()` (vibey's real, production, engine-agnostic
subprocess adapter — the same code path `vibey worker` and
`vibey doctor --conformance` both use) has for "is this run done yet, and
did it succeed." Without it, vibey can spawn codexloop and stream its raw
`events.jsonl` output just fine, but it can **never** correctly detect
that a codexloop run has finished. In production this would either hang
forever (vibey has its own independent process-exit-based timeout as a
last resort, but that's a safety net, not a substitute for a real signal)
or silently misreport completion.

For reference, claudeloop's own equivalent lifecycle write lives in
`infrastructure/rundir.py:140` (`self.meta_path.write_text(json.dumps(meta.to_dict(), ...))`),
called from multiple points as the run's `RunMeta` object's status
changes — that's the shape to match, not necessarily the exact
implementation.

## Task

Give codexloop's `meta.json` the same living status-field contract the
other three engines already have:

1. Extend whatever `meta.json`-backing dataclass/dict codexloop uses today
   (check `rundir.py`'s current `meta` shape) with a `status` field using
   the shared vocabulary: `active` (written at/soon after run start),
   `finished` (successful completion), `failed` (an unrecoverable error —
   including the "no checkbox items" `ConfigurationError` case and any
   other early-exit validation failure), `stopped` (an operator-requested
   stop). Use the exact same four string values the other engines use —
   don't invent a fifth.
2. Add an update path — a method on `RunDirectory` (mirroring claudeloop's
   pattern) that rewrites `meta.json` with the new status, called at every
   point in the run lifecycle where the outcome becomes known: successful
   completion, any exception/error path (including the plan-parsing
   `ConfigurationError` — confirm exactly where `run_plan.py`'s use case
   catches or lets that propagate, and make sure the status write happens
   before the process actually exits), and the `stop` control-plane path
   if one exists.
3. Use `os.replace`/atomic-write-then-rename for the update, matching how
   `git_savepoints.py` and other codexloop infrastructure already handle
   atomic file writes — a reader mid-write must never see a truncated or
   invalid `meta.json`.

## Tests

Test-first. Unit-level: assert the `RunDirectory` update method writes the
correct status value and that the file round-trips correctly. Integration-
level: extend `tests/live/system/test_subprocess_smoke.py` (or add a
sibling test) to run a real scripted `codexloop run` to completion and
assert `meta.json`'s `status` field is `"finished"` afterward — and a
second test covering the `ConfigurationError`/no-checkbox-items path,
asserting `status` ends up `"failed"`, not left unset. These are the exact
regression tests that would have caught today's gap.

Keep all four layers at 100% branch coverage. Full 7-gate sweep: ruff
check/format, `mypy --strict src/codexloop`, the four
`pytest --cov=<layer> --cov-fail-under=100` runs, `lint-imports`, `bandit`,
`pip-audit`. Re-run the full suite 3-5 times before trusting green.

## Smoke test

After your fix, this must show a `status` field, not just the three
original keys:

```bash
cd /tmp/some-scratch-git-repo
printf -- '- [ ] make a trivial change\n' > plan.md
CODEXLOOP_ALLOW_TEST_AGENT=1 CODEXLOOP_TEST_AGENT_SCRIPT=~/git/codexloop/tests/live/fixtures/agent_scripts/done.json \
  codexloop run plan.md
find .codexloop/runs -name meta.json -exec cat {} \;
# must include "status": "finished"
```

## Done

Full gate sweep green, Conventional Commit, end your final message with
**CODEXLOOP_TASK_FULLY_COMPLETE** — only when genuinely done. If the
cleanest insertion point turns out to be somewhere other than
`RunDirectory` (e.g. a dedicated `MetaStore` port, matching
`FileRunStateStore`'s existing shape), use your judgment and document why
you diverged.
