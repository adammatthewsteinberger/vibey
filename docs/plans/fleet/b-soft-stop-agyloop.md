# agyloop — Phase B: soft stop (wind-down) + tri-state sleep

You are working unattended in a disposable git worktree of `agyloop`
(`~/git/agyloop`), on branch `chore/b-soft-stop`. This is a real, mature
codebase — 100% branch-covered on all four architectural layers
(domain/application/infrastructure/cli), CI-gated. Do not weaken any gate,
delete a test, or add a coverage exclusion to get to green.

**Never write outside your worktree.** Pass `--cwd` explicitly to every
`agyloop` subcommand you invoke as a smoke test (it already supports `--cwd`
on essentially everything).

## Context

`claudeloop` (a sibling repo, `~/git/claudeloop`, do not modify it — read
only) already has a working implementation of "soft stop" (wind-down): a
`WindDownCommand` that lets the current turn finish, writes a handoff marker
naming every produced artifact, and exits with a distinct code (75) so a
supervisor can tell "hand off to another runner" from "this failed" or
"the operator hard-stopped it". agyloop has half of this: it can *emit* a
`WindDownAndFinish` domain event and construct a `HandoffMarker`
(`domain/handoff_marker.py`), but nothing writes the marker to disk, nothing
reads it back, and there is no way to *request* a wind-down at all — no
command, no CLI, no exit code.

Read before writing code:
1. `~/git/claudeloop/src/claudeloop/domain/control.py` — `WindDownCommand`,
   how it's added to the `ControlCommand` union, and how `stop_outranks`
   holds a wind-down (not drops it) when a wind-down and a stop race.
2. `~/git/claudeloop/src/claudeloop/infrastructure/control.py` — the inbox
   JSON round-trip (`{"type": "wind_down", ...}` encode/decode).
3. `~/git/claudeloop/src/claudeloop/cli/commands/wind_down_cmd.py` and how
   it's registered in `cli/app.py`.
4. `~/git/claudeloop/src/claudeloop/infrastructure/rundir.py` —
   `write_handoff_marker` (tmp-file + `os.replace`, not a direct write —
   this matters for crash-safety).
5. `~/git/claudeloop/src/claudeloop/domain/handoff_marker.py` —
   `EXIT_WIND_DOWN = 75`, and how `cli/commands/run.py:309` raises it.
6. Now `~/git/agyloop/src/agyloop/domain/handoff_marker.py`,
   `~/git/agyloop/src/agyloop/domain/loop.py` (`WindDownAndFinish`),
   `~/git/agyloop/src/agyloop/application/runner.py` (search for
   `WindDownAndFinish` and `_sleep_interruptible`), and
   `~/git/agyloop/src/agyloop/domain/control.py` (the current
   `ControlCommand` union and `stop_outranks`, if any) to see exactly what's
   missing.

## Deliverables

1. **`WindDownCommand`** in `domain/control.py`: a frozen dataclass with a
   `reason: str` field (non-empty, validated), added to the `ControlCommand`
   union. If a `stop_outranks`-equivalent function exists, extend it so a
   `StopCommand` always wins but a pending `WindDownCommand` is **held**
   (returned, not discarded) when a stop arrives mid-turn — discarding it
   would make correctness depend on poll timing.
2. **Inbox round-trip** for wind-down in `infrastructure/control.py` —
   encode/decode `{"type": "wind_down", "reason": ...}` alongside whatever
   other command kinds already round-trip there.
3. **`agyloop wind-down [--run-id] [--reason] [--cwd]`** CLI command,
   registered in `cli/app.py`, calling a new
   `enqueue_wind_down`/`request_wind_down` use case (wherever agyloop's
   equivalent of claudeloop's `bootstrap_ops` lives — check
   `infrastructure/run_control.py` or similar first; agyloop already has
   `enqueue_*` helpers for other command kinds, follow that pattern exactly).
4. **The marker read/write path**: `rundir.write_handoff_marker` (or
   wherever agyloop's rundir module lives) using tmp-file + `os.replace`,
   and a `handoff_marker_path` property. Wire it into the runner's
   `RunnerContext` (or equivalent) so `_finish_wound_down`-equivalent code
   actually calls it — today the `HandoffMarker` is constructed but never
   written.
5. **`run` exits 75** on wind-down, with the marker path echoed to stdout.
   Find wherever agyloop's exit-code mapping lives (likely near
   `cli/commands/run.py`) and add the wind-down → 75 case; today it falls
   through to a generic failure exit.
6. **Tri-state `_sleep_interruptible`**: change its return type from `bool`
   to `None | Literal["stop"] | Literal["wind_down"]` (or an equivalent
   small enum/union — match agyloop's existing style) so a wind-down
   request can break an in-progress capacity wait, not just a stop. Update
   every call site. This is the single most important piece here: it's what
   lets an operator (or, later, vibey's rotation logic) reclaim an engine
   that's sitting in a long capacity-wait rather than waiting it out.

## Tests

Test-first. No production file gets written before a failing test names it
(this is agyloop's own ground rule — check `AGENTS.md`/`CLAUDE.md` if
present). Cover:
- `WindDownCommand` construction, validation (empty reason rejected),
  round-trip through the inbox.
- `stop_outranks`-equivalent: stop always wins; a held wind-down surfaces
  once the stop is processed, not silently dropped.
- `write_handoff_marker` crash-safety (partial writes never visible —
  temp file + rename, verify via a monkeypatched `os.replace` that raises
  mid-write leaves the old file, if any, intact).
- `run` exit code is exactly 75 on wind-down, and the printed marker path is
  a real file that exists and parses back into the same `HandoffMarker`.
- `_sleep_interruptible` returns `"wind_down"` when a wind-down is enqueued
  mid-sleep, `"stop"` when a stop is, `None` on natural timeout, and that a
  wind-down actually cuts the wait short (assert elapsed time, not just the
  return value).

Every layer must stay at 100% branch coverage. Run the full 7-gate sweep
before considering this done — `ruff check`, `ruff format --check`,
`mypy --strict`, the four per-layer `pytest --cov-fail-under=100` runs,
`lint-imports`, `bandit`, `pip-audit`. Re-run the full suite 3-5 times
(`for i in 1 2 3 4 5; do uv run pytest -q; done`) before trusting a coverage
number that only barely passed — a property test can accidentally be the
only thing covering a branch.

## Smoke test

```bash
agyloop wind-down --run-id smoke-test --reason "manual smoke test" --cwd .
# should fail cleanly if no such run exists; then, with a real scripted run:
agyloop run <some plan> --run-id smoke --cwd $PWD --gateway sdk --scoped &
sleep 2
agyloop wind-down --run-id smoke --cwd $PWD --reason "smoke"
wait $!
echo "exit code: $?"   # must be 75
```

## Done

When the full gate sweep is green, commit with Conventional Commits, and end
your final message with **AGYLOOP_TASK_FULLY_COMPLETE** — only when every
gate above is genuinely green, not aspirationally. If something can't be
made to pass, stop and explain why rather than weakening a gate.
