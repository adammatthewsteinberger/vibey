# cursorloop — Phase D0: don't crash on the continuation prompt after a scripted "done" turn

You are working unattended in a disposable git worktree of `cursorloop`
(`~/git/cursorloop`), on branch `chore/d0-completion-detection`.
`cursorloop` has good `--cwd` coverage — use it explicitly on every
subcommand that supports it.

This is a real, mature codebase — 100% branch-covered on all four
architectural layers, CI-gated. Do not weaken any gate, delete a test, or
add a coverage exclusion to get to green.

## Why this task exists

Found 2026-08-19 by vibey (the downstream conductor that drives cursorloop
as one of four autonomous engines) while proving out its own
`LoopProcessAdapter`/`vibey worker` machinery end to end against real
installed binaries — same investigation that found codexloop's
`d0-meta-status-codexloop.md` gap, and closely related to the
`c4-wire-events-sink-cursorloop.md` fix that already landed (#27): that
plan's own aside flagged this exact crash as "a different bug in
completion detection, not part of this task's scope" — this is that task.

Reproduced directly, twice, independently (once during the c4 wiring
work, once again during this investigation): a real scripted
`cursorloop run --plan <plan> --cwd <dir>` against the `done.json` fixture
(one scripted turn, verdict `{"complete": true, ...}`,
`CURSORLOOP_TASK_FULLY_COMPLETE` in the output text) crashes instead of
exiting 0:

```
IndexError: ScriptedAgentGateway: no turns left in script (prompt='Continue
exactly where you left off.')
```

`application/runner.py`'s `AutonomousRunner` sends a second turn — the
`_CONTINUE_PROMPT` follow-up — after the scripted agent's first (and only)
turn, instead of recognizing the turn's verdict as complete and finishing.
`infrastructure/agent/scripted.py::ScriptedAgentGateway.send_turn` then has
no more turns queued for that second call and raises, which is a real,
if slightly different, way this same scripted turn's `verdict` never gets
treated as a stopping condition — whatever `evaluate`/`reconcile`
(`domain/completion.py`) is supposed to do with `TurnOutcome.verdict` isn't
short-circuiting the next-turn decision here.

This matters beyond the crash itself: `LoopProcessAdapter.tail()` (vibey's
real subprocess adapter) detects completion by watching `meta.json`'s
`status` field — a crashed cursorloop process may never get the chance to
write a terminal status either, which is the exact failure mode
`d0-meta-status-codexloop.md`'s sibling investigation is about. Fixing the
root cause here (recognizing a complete verdict without sending a
needless continuation turn) is more valuable than just handling the
crash gracefully.

## Task

1. Find where `AutonomousRunner` decides whether to send `_CONTINUE_PROMPT`
   after a turn (`application/runner.py` — likely `_do_send` or the
   `decide_after_turn` call in `domain/loop.py`) and confirm whether a
   `TurnOutcome.verdict.complete == True` is actually being checked there,
   or whether something upstream of that decision (e.g. how
   `ScriptedAgentGateway` reports `TurnOutcome` vs. how the live
   `CursorAgentGateway` path does, via `parse_verdict_block` in
   `infrastructure/agent/translate.py`) causes the scripted path
   specifically to fall through this check when the live path wouldn't.
2. Fix so a scripted turn's verdict is honored exactly like a live turn's
   verdict — the runner must not ask for a continuation when the agent
   already said it's done. Do not fix this by making
   `ScriptedAgentGateway.send_turn` merely more tolerant of extra calls
   (e.g. returning some placeholder instead of raising) — that would paper
   over the real bug (an unwanted continuation turn happening at all) with
   a quieter failure instead of fixing the decision logic that requests
   it.

## Tests

Test-first. Add a test — likely alongside
`tests/live/system/test_matrix_inprocess.py`'s existing `done.json`-based
tests, or `application/test_runner.py` if there's a more direct unit-level
seam — asserting that a single-turn scripted script with a complete
verdict results in exactly one `send_turn` call, not two, and the run
exits successfully. This is the regression test that would have caught
today's bug: a green run that quietly sends 2+ turns for a 1-turn script
must fail it.

Keep all four layers at 100% branch coverage. Full 7-gate sweep: ruff
check/format, `mypy --strict src/cursorloop`, the four
`pytest --cov=<layer> --cov-fail-under=100` runs, `lint-imports`, `bandit`,
`pip-audit`. Re-run the full suite 3-5 times before trusting green.

## Smoke test

After your fix, this must exit 0 without the IndexError, and
`sent_prompts` (if you can observe it, e.g. via a slightly more
instrumented reproduction) must show exactly one call:

```bash
cd /tmp/some-scratch-git-repo
printf -- '- [ ] x\n' > plan.md
CURSORLOOP_ALLOW_TEST_AGENT=1 CURSORLOOP_TEST_AGENT_SCRIPT=~/git/cursorloop/tests/live/fixtures/agent_scripts/done.json \
  cursorloop run --plan plan.md --cwd .
echo "exit: $?"
# must be 0, no IndexError traceback
```

## Done

Full gate sweep green, Conventional Commit, end your final message with
**CURSORLOOP_TASK_FULLY_COMPLETE** — only when genuinely done. If the
root cause turns out to be somewhere other than the two files named above,
that's fine — just make sure the fix addresses why the runner asks for a
continuation after a complete verdict, not just where the crash happens
to surface.
