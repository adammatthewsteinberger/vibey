# Fleet program — dogfooding mechanics

This directory holds the per-run plan files that drive the fleet program
(`docs/plans/fleet-program-runbook.md`) autonomously, one *loop runner at a
time, in disposable worktrees. See
`/Users/adam/.claude/plans/can-youy-please-deep-transient-kettle.md` for the
overall program plan this implements (sequencing, verified current state,
and the phase-by-phase breakdown).

## Launching a run

```bash
scripts/fleet/run.sh REPO PHASE [DRIVER]
# e.g.
scripts/fleet/run.sh agyloop b-soft-stop agyloop
scripts/fleet/run.sh vibey e1-live-engines claudeloop
```

This creates (or reuses) `~/.cache/fleet-worktrees/<repo>-<phase>` on branch
`chore/<phase>` off `origin/develop`, and hands the plan file
`docs/plans/fleet/<phase>-<repo>.md` to the chosen driver with the agreed
caps (`--max-turns 800 --max-dollars 80 --max-wait 21600`), `--cwd` pinned to
the worktree on every subcommand that supports it, and a system-prompt note
listing protected paths.

## Landing a run

```bash
scripts/fleet/land.sh REPO PHASE
```

Pushes the branch, opens (or reuses) a PR against `develop`, watches checks,
and squash-merges **only if every check is green and the diff does not touch
a protected path**. A protected-path diff or a red PR is left open with an
explanation — never silently merged.

## Protected paths

A run must not modify these without explicit human review (enforced by
`land.sh`'s refusal, not just convention):

- `tests/infrastructure/db/test_chaos.py` — the chaos test
- `tests/domain/test_noloss*.py`, `tests/domain/test_briefing.py` — the
  no-loss property suite
- `tests/system/test_delivery_stage_set.py` — the full-cycle system test
- `tests/live/**` — the two-mode harness, once it exists (Phase E1)

## Known gaps that shape the launcher today

- **codexloop's `run` has no `--cwd`** (Phase C fixes this). `run.sh` works
  around it by `cd`-ing into the worktree before invoking codexloop — this
  is exactly the class of incident `--cwd` normally prevents, so codexloop
  runs need extra care until Phase C lands.
- **codex and cursor-agent are not installed** as of this writing — only
  `claude` (backing claudeloop) and `GOOGLE_API_KEY`/`GEMINI_API_KEY`
  (backing agyloop) are live-capable. codexloop/cursorloop plan files assume
  a driver of `claudeloop` (cross-repo dogfooding: claudeloop's own agent
  does the work on the codexloop/cursorloop checkouts) until the user
  installs `codex`/`cursor-agent`.
- `scripts/fleet/status.sh` tabulates every worktree under
  `~/.cache/fleet-worktrees/` with its PR and check state — run it any time
  to see what's in flight.

## Concurrency

At most 5 runs in flight at once (agreed budget). Each run gets its own
worktree and PR; they don't interact except by landing onto the same
`develop` branch, so land in whatever order goes green first.
