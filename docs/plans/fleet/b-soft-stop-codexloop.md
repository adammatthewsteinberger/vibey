# codexloop — Phase B: soft stop (wind-down) + tri-state sleep

You are working unattended in a disposable git worktree of `codexloop`
(`~/git/codexloop`), on branch `chore/b-soft-stop`. **Important operational
note:** codexloop's `run` command does not currently accept `--cwd` — you
were launched with your shell's working directory already set to this
worktree. Stay there; never `cd` out of it, and never assume `--cwd` exists
on codexloop commands (it doesn't, yet — that's tracked separately, don't
add it here unless it's trivially in scope).

This is a real, mature codebase — 100% branch-covered on all four
architectural layers (domain/application/infrastructure/cli), CI-gated
(`ubuntu-latest`+`macos-latest` × py3.12/3.13, 4 pytest invocations per
cell). Do not weaken any gate, delete a test, or add a coverage exclusion.

## Context

`claudeloop` (a sibling repo, `~/git/claudeloop`, read-only reference — do
not modify it) has a working "soft stop" (wind-down) implementation: a
`WindDownCommand` that lets the current turn finish, writes a handoff marker
naming every artifact produced, and exits with a distinct code (75) so a
supervisor can tell "hand this run off elsewhere" from "it failed" or "the
operator hard-stopped it". codexloop currently has **none** of this: no
`WindDownCommand`, no `stop_outranks`, no wind-down CLI command, no
`enqueue_wind_down`, no marker writer, no exit-75 path, and `_sleep_interruptible`
doesn't exist at all — the sleep in `application/runner.py` (around line
241) is a bare `await self._sleeper.sleep_until(until)` with no interrupt
path whatsoever.

Also: codexloop has a real inline `case WindDownAndFinish() as wound_down:`
block in `application/runner.py` around line 250-265, and a `_write_handoff_marker`
helper at roughly line 495-517 that's already correctly extracted and wired
through `RunnerContext.handoff_marker_writer` — but `bootstrap.py` never
supplies that writer, so it's `None` in production and the marker is never
actually written to disk today. Fix that wiring as part of this work.

Read before writing code:
1. `~/git/claudeloop/src/claudeloop/domain/control.py` — `WindDownCommand`
   shape, its place in the `ControlCommand` union, `stop_outranks` holding
   (not dropping) a pending wind-down when a stop races it.
2. `~/git/claudeloop/src/claudeloop/infrastructure/control.py` — inbox JSON
   round-trip.
3. `~/git/claudeloop/src/claudeloop/cli/commands/wind_down_cmd.py` +
   registration in `cli/app.py`.
4. `~/git/claudeloop/src/claudeloop/infrastructure/rundir.py` —
   `write_handoff_marker` (tmp-file + `os.replace`).
5. `~/git/claudeloop/src/claudeloop/domain/handoff_marker.py` —
   `EXIT_WIND_DOWN = 75`; `cli/commands/run.py:309` raising it.
6. In codexloop itself: `src/codexloop/domain/control.py` (current union +
   `_BUILDERS`), `src/codexloop/infrastructure/control.py` (current inbox
   round-trip, 9 kinds), `src/codexloop/domain/handoff_marker.py`
   (`EXIT_WIND_DOWN` already defined, only referenced from a unit test —
   confirm), `src/codexloop/application/runner.py` (the inline wind-down
   case, `_write_handoff_marker`, `RunnerContext.handoff_marker_writer`),
   `src/codexloop/cli/asyncio.py` (`sysexit_for` — success→0, stop→130,
   **everything else→1**, including a wind-down today), and `bootstrap.py`
   (grep for every `Path.cwd()` call — codexloop hardcodes cwd in ~8 places;
   leave those alone unless they're directly in the wind-down path).

## Deliverables

1. **`WindDownCommand`** in `domain/control.py`: frozen dataclass,
   `reason: str` (validated non-empty), added to the `ControlCommand` union
   and to `_BUILDERS`. Add (or extend) a `stop_outranks`-equivalent — it
   does not exist anywhere in codexloop today, so this is new: stop always
   wins, but a pending wind-down is **held**, not dropped, when a stop
   arrives first.
2. **Inbox round-trip** for wind-down in `infrastructure/control.py`,
   following the existing 9-kind pattern exactly.
3. **`codexloop wind-down [--run-id] [--reason]`** CLI command, registered
   alongside the other 20 top-level commands in `cli/app.py`, calling a new
   enqueue use case (codexloop has no `bootstrap_ops` module — put it
   wherever the other control-enqueue logic lives, likely `bootstrap.py`
   itself; follow the existing pattern for prompt/stop/etc.).
4. **`rundir.write_handoff_marker`** (tmp-file + `os.replace`) in
   `infrastructure/rundir.py`, alongside the existing `validate_run_id` /
   `RunDirectory.{create,ensure_layout}` API. Wire `bootstrap.py` to pass
   this as `handoff_marker_writer` into `RunnerContext` — this is the fix
   that makes the already-extracted `_write_handoff_marker` actually run in
   production.
5. **Exit 75 on wind-down**: fix `cli/asyncio.py::sysexit_for` to map a
   wind-down outcome to 75, distinct from the generic failure `1`. Echo the
   marker path to stdout when it happens.
6. **Tri-state `_sleep_interruptible`**: this function does not exist in
   codexloop today. Add it around `application/runner.py:241`, replacing the
   bare `await self._sleeper.sleep_until(until)` — return
   `None | Literal["stop"] | Literal["wind_down"]`, polling the control
   inbox during the wait, cutting it short on either signal. Update the
   caller(s) accordingly.

## Tests

Test-first (codexloop's own ground rules — check `AGENTS.md`/`CLAUDE.md`).
Cover: `WindDownCommand` validation + round-trip; `stop_outranks`-equivalent
holding behavior; `write_handoff_marker` crash-safety (temp+rename, verify a
mid-write failure leaves any prior file intact); `sysexit_for` returns 75
exactly for wind-down and the printed marker path parses back to the same
`HandoffMarker`; `_sleep_interruptible` returns `"wind_down"`/`"stop"`/`None`
correctly and actually shortens the wait (assert elapsed time).

Keep all four layers at 100% branch coverage. Full 7-gate sweep: ruff
check/format, `mypy --strict src/codexloop`, the four
`pytest --cov=<layer> --cov-fail-under=100` runs, `lint-imports`, `bandit`,
`pip-audit`. **codexloop's CI runs pytest 4× per matrix cell** (one per
layer) across 4 cells — run the full suite at least 3 times locally before
trusting green; a previous intermittent failure here
(`tests/infrastructure/test_coverage_boost.py::test_git_savepoints_list_unwind_and_errors`)
was a real SHA-collision flake, already fixed on develop — don't reintroduce
anything like it (avoid short numeric-only savepoint targets in new tests).

## Smoke test

```bash
# from inside the worktree (no --cwd support yet)
codexloop run <some plan> --run-id smoke &
sleep 2
codexloop wind-down --run-id smoke --reason "smoke test"
wait $!; echo "exit code: $?"   # must be 75
```

## Done

Full gate sweep green, Conventional Commit, end your final message with
**CODEXLOOP_TASK_FULLY_COMPLETE** — only when genuinely done. If a gate
can't be made to pass, stop and explain why instead of weakening it.
