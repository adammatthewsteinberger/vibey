# claudeloop — Phase C: autonomy guardrails

You are working unattended in a disposable git worktree of `claudeloop`
(`~/git/claudeloop`), on branch `chore/c-guardrails`. Pass `--cwd`
explicitly wherever it exists (currently only `run` and `sessions`
support it — fixing that gap is part of this task).

This is a real, mature codebase — 100% branch-covered on all four
architectural layers, CI-gated. Do not weaken any gate, delete a test, or
add a coverage exclusion to get to green.

## Context: why this matters

claudeloop is meant to be the safe reference implementation other repos in
this fleet copy from for worktree isolation. In practice it currently has a
real gap: **`--cwd` exists on only two of its ~20 subcommands** (`run` and
`sessions`). Every other command — `resume, stop, wind-down, status, watch,
prompt, logs, unwind` — silently defaults to `Path.cwd()`. This is *exactly*
the incident class the whole worktree-isolation discipline exists to
prevent: an earlier real session ran `claudeloop resume` from the live
checkout (because `resume` has no `--cwd`) and it auto-committed uncommitted
work into the wrong place. `resume` still has this exact bug today.

Separately: claudeloop's `develop` CI is currently **red** on py3.10 only —
three TUI tests fail intermittently (`tests/infrastructure/test_stream_app.py::
TestStreamAppActions::test_prev_turn_replay`,
`test_next_turn_replay`, `TestStreamAppPartialBranches::
test_prev_turn_all_starts_before_current`), with
`textual.css.query.NoMatches: No nodes match '#assistant' on Screen(id='_default')`
— the same commit passes on 3.11/3.12/3.13 and passed on its own PR branch,
so this is a genuine py3.10-only flake, not a logic bug per se: the test is
almost certainly racing the widget mount rather than awaiting it properly.

Finally, `--wind-down-at` is referenced in
`~/git/vibey/docs/plans/fleet-program-runbook.md` as a guardrail that's
supposedly "enabled" — it does not exist anywhere in claudeloop today. It's
needed so an unattended run can hand off gracefully at a deadline instead of
being killed mid-turn.

## Deliverables

1. **`--cwd` on every subcommand that currently lacks it**: `resume, stop,
   wind-down, status, watch, prompt, logs, unwind` (check `cli/app.py` for
   the complete current list and don't miss any). Each of these currently
   resolves a working directory via `Path.cwd()` somewhere in its
   implementation — find that call, thread a `--cwd: Path = typer.Option(...)`
   parameter through instead, defaulting to `Path.cwd()` only when the flag
   is omitted (so existing invocations without `--cwd` keep working).
   **`resume` is the priority** — it's the one with the documented incident.
   Add a regression test that constructs a runner from a `--cwd` other than
   the process's actual working directory and asserts no file is touched
   outside it (a temp dir sentinel file check is a good pattern — write a
   canary file in the *process* cwd before the call, and assert it's
   unchanged afterward).

2. **`--wind-down-at <ISO8601 | +duration>`** on `run` and `resume`. Parse
   an absolute ISO-8601 timestamp or a relative duration (`+2h`, `+90m`,
   whatever suffix convention matches claudeloop's existing time-parsing
   idioms — check for one before inventing a new format). When the deadline
   arrives, emit the same `WindDownAndFinish` outcome a manually-requested
   wind-down produces (reuse `domain/forecast.py`'s `should_wind_down` or a
   sibling helper — check what's already there for capacity-forecast-driven
   wind-down and follow the same shape for a deadline-driven one). This
   should compose cleanly with the tri-state `_sleep_interruptible` you may
   see other fleet runs adding in parallel — if it's not landed yet when you
   start, implement the deadline check as its own interruption path and
   note in your final summary that it should be unified once tri-state
   sleep lands (don't block on another run finishing).

3. **Fix the py3.10 `test_stream_app.py` flake**. Read the three failing
   tests and the `StreamApp`/`TestStreamAppActions`/
   `TestStreamAppPartialBranches` fixtures. The likely cause is a Textual
   `app.run_test()` pilot proceeding before the initial mount/compose has
   settled — Textual's own guidance is to `await pilot.pause()` (or
   equivalent) after any action that changes mounted widgets before querying
   for them. Reproduce locally first if you can pin py3.10 (check what
   Python versions are available in this environment — if only newer ones
   are installed, reason carefully about the race from the stack trace and
   Textual's test-pilot docs rather than guessing blind). Make the fix
   deterministic — no `sleep()`-based patches; use the pilot's own
   synchronization primitives.

## Tests

Test-first, as always. For (1): a `--cwd`-isolation test per fixed command,
verifying no writes escape the passed worktree. For (2): a
`--wind-down-at` parsing test (both ISO and relative-duration forms,
including invalid input) and a scheduling test that a deadline in the very
near future actually triggers a wind-down outcome without waiting for the
full window (fake/injectable clock, not real sleeps). For (3): whatever test
change resolves the flake should be proven non-flaky by running it
repeatedly, not just once — `for i in $(seq 1 20); do uv run pytest
tests/infrastructure/test_stream_app.py -q || break; done` should be clean
20/20 before you trust the fix.

Keep all four layers at 100% branch coverage. Full 7-gate sweep: ruff
check/format, `mypy --strict src/claudeloop`, the four
`pytest --cov=<layer> --cov-fail-under=100 --cov-branch` runs, `lint-imports`,
`bandit`, `pip-audit`. Then `for i in 1 2 3 4 5; do uv run pytest -q; done`
to catch any newly-introduced flakiness before you trust green.

## Smoke test

```bash
mkdir -p /tmp/cwd-smoke && cd /tmp/other-dir-that-must-not-be-touched 2>/dev/null || mkdir -p /tmp/other-dir-that-must-not-be-touched
claudeloop resume --run-id some-existing-run --cwd /tmp/cwd-smoke
# confirm nothing was written under /tmp/other-dir-that-must-not-be-touched

claudeloop run <plan> --run-id wd-smoke --cwd /tmp/cwd-smoke --wind-down-at +30s --max-wait 3600 &
sleep 35
wait $!; echo "exit code: $?"   # should be 75 once the deadline fires
```

## Done

Full gate sweep green (including CI green on all four Python versions, not
just the ones you can run locally — check the workflow matrix and reason
about py3.10 specifically even if you can't execute it directly),
Conventional Commit, end your final message with
**CLAUDELOOP_TASK_FULLY_COMPLETE** — only when genuinely done. If a gate
can't be made to pass, stop and explain why instead of weakening it.
