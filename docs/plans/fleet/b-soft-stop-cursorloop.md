# cursorloop — Phase B: soft stop (wind-down) + tri-state sleep

You are working unattended in a disposable git worktree of `cursorloop`
(`~/git/cursorloop`), on branch `chore/b-soft-stop`. Pass `--cwd` explicitly
to every subcommand that supports it (cursorloop already has good `--cwd`
coverage — `stop, prompt, status, logs, watch, runs, savepoints, unwind,
doctor, resume, agents, hooks` — use it everywhere you can).

This is a real, mature codebase — 100% branch-covered on all four
architectural layers (domain/application/infrastructure/cli), CI-gated
(5 pytest invocations per cell: 4 per-layer floors + a full-suite run). Do
not weaken any gate, delete a test, or add a coverage exclusion.

## A previous attempt exists — read it, don't just reimplement blind

A prior autonomous run already made a first pass at this exact task, but it
stalled and was never landed: it's behind `origin/develop` by several
commits, fails `ruff` (two lines over the 100-char limit), fails
`mypy --strict` (an unimported `HandoffMarker` annotation), never wired the
exit-75 path, never touched `_sleep_interruptible`, and added zero tests —
so it cannot pass CI as-is. Its *ideas* are sound and worth reusing. The
diff has been salvaged for you at
`docs/plans/fleet/patches/cursorloop-wind-down-draft.patch` (source-only,
with the CI/version-bump reverts stripped out). **Read the patch first.**
Do not apply it with `git apply` blindly — it's stale (predates several
develop commits) and incomplete. Use it as a reference for the intended
shape of `WindDownCommand`, the CLI command, and the inbox wiring, then
write it properly against current `develop`, complete the missing pieces,
and add real tests.

## Context

`claudeloop` (a sibling repo, `~/git/claudeloop`, read-only reference) has
the complete, working version of this feature: a `WindDownCommand` that
lets the current turn finish, writes a handoff marker naming every artifact
produced, and exits with a distinct code (75) so a supervisor can tell
"hand this off elsewhere" from "it failed" or "operator hard-stopped it".

Read before writing code:
1. `~/git/claudeloop/src/claudeloop/domain/control.py` — `WindDownCommand`
   shape + `stop_outranks` **held-not-dropped** semantics.
2. `~/git/claudeloop/src/claudeloop/infrastructure/control.py` — inbox
   round-trip.
3. `~/git/claudeloop/src/claudeloop/cli/commands/wind_down_cmd.py` +
   registration.
4. `~/git/claudeloop/src/claudeloop/infrastructure/rundir.py` —
   `write_handoff_marker` (tmp-file + `os.replace`).
5. `~/git/claudeloop/src/claudeloop/domain/handoff_marker.py` —
   `EXIT_WIND_DOWN = 75`.
6. In cursorloop itself: `src/cursorloop/domain/control.py` (current union:
   Stop|Prompt|SetModel|SetEffort|SetCwd|Snapshot|SavePoint — no
   WindDown), `src/cursorloop/infrastructure/control.py` (`_stop_outranks`
   lives here in **infrastructure**, not domain — move the outranking logic
   to `domain/control.py` as part of this work, matching claudeloop's
   layering, and keep the infra module as a thin caller), `src/cursorloop/
   infrastructure/run_control.py` (the `enqueue_{stop,prompt,model,effort,
   cwd,snapshot,savepoint}` family — add `enqueue_wind_down` here),
   `src/cursorloop/infrastructure/rundir.py` (has `write_meta`,
   `update_meta`, `write_stop_summary` but no `write_handoff_marker`),
   `src/cursorloop/domain/handoff_marker.py` (`EXIT_WIND_DOWN = 75` already
   defined, referenced only from a unit test), `src/cursorloop/cli/render.py`
   (`exit_code_for`: success→0, auth→3, max-wait→4, stopped→130, else→1 —
   add the wind-down case), and `src/cursorloop/application/runner.py`
   (`_finish_wound_down` **already exists** here at roughly lines 468-500,
   correctly extracted and wired — reuse it, don't rewrite it; you mainly
   need to make sure the marker actually gets written and the exit code is
   right).

## Deliverables

1. **`WindDownCommand`** in `domain/control.py` — frozen dataclass,
   `reason: str = "operator wind-down"` with a non-empty guard, added to the
   `ControlCommand` union.
2. **`stop_outranks` moved to `domain/control.py`** (currently
   `_stop_outranks` in `infrastructure/control.py`, handling `Stop` only) —
   extend it to handle wind-down: stop always wins, a pending wind-down is
   held (not dropped) if a stop arrives first. Update the infra caller.
3. **Inbox round-trip** for `{"type": "wind_down", "reason": ...}` in
   `infrastructure/control.py`, alongside the existing 7-kind mapping.
4. **`enqueue_wind_down(cwd, reason, run_id)`** in
   `infrastructure/run_control.py`, matching the existing family's
   signature shape exactly.
5. **`cursorloop wind-down [--reason] [--run-id] [--cwd]`** CLI command in
   `cli/commands/control_cmds.py`, registered in `cli/app.py` next to
   `stop`/`prompt`/etc.
6. **`rundir.write_handoff_marker(marker)`** — tmp-file + `os.replace`,
   plus a `handoff_marker_path` property, in `infrastructure/rundir.py`.
   Fix the missing `HandoffMarker` import (this broke `mypy --strict` in
   the prior attempt — the annotation was used without the class being
   imported). Wire `bootstrap.py` to pass
   `handoff_marker_writer=run_dir.write_handoff_marker` into the runner
   context, and confirm `_finish_wound_down` (already at
   `application/runner.py:468-500`) actually calls it.
7. **Exit 75 on wind-down**: extend `cli/render.py::exit_code_for` with the
   wind-down case, distinct from the generic `else→1`. Echo the marker path.
8. **Tri-state `_sleep_interruptible`**: currently at
   `application/runner.py:426-434`, returns `bool` and only recognizes
   `Stop` (`isinstance(command, Stop)`). Change its return type to
   `None | Literal["stop"] | Literal["wind_down"]` so a wind-down can also
   break the wait. Update both call sites (`:178`, `:189`).

## Tests

Test-first. Cover: `WindDownCommand` validation + round-trip; the moved
`stop_outranks` held-not-dropped behavior (add a domain-layer test now that
it lives in `domain/`); `write_handoff_marker` crash-safety; `exit_code_for`
returns exactly 75 for wind-down; `_sleep_interruptible` returns
`"wind_down"`/`"stop"`/`None` correctly and genuinely shortens the wait.

All four layers stay at 100% branch coverage — including the **full-suite**
5th CI step (`ci.yml` runs `pytest tests --cov=cursorloop.<layer>
--cov-fail-under=100` ×4 plus one plain full-suite run). Full gate sweep:
ruff check/format, `mypy --strict`, `lint-imports`, `bandit`, `pip-audit`,
plus the 5 pytest invocations. Fix both pre-existing lint issues from the
prior attempt if you end up touching those same lines again (a 103-char
line in `domain/control.py` and a 113-char line in
`infrastructure/run_control.py` were the specific failures — don't
reproduce them; cursorloop's line limit is 100).

## Smoke test

```bash
cursorloop run --plan <some plan> --run-id smoke --cwd . &
sleep 2
cursorloop wind-down --run-id smoke --cwd . --reason "smoke test"
wait $!; echo "exit code: $?"   # must be 75
```

## Done

Full gate sweep green, Conventional Commit, end your final message with
**CURSORLOOP_TASK_FULLY_COMPLETE** — only when genuinely done. If a gate
can't be made to pass, stop and explain why instead of weakening it.
