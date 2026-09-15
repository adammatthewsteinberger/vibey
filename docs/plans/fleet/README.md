# Fleet program — dogfooding mechanics

> **Status as of 2026-09-15: dormant.** These scripts drove the August 2026
> dogfooding runs (ADR-0017). Every plan file in this directory has landed
> except `b-soft-stop-agyloop.md` (agyloop still has no `wind-down`) and two
> `d0-*` items whose landing is unverified — see [Plan-file status](#plan-file-status).
> The scripts assume separate checkouts at `~/git/<runner>` with GitHub remotes
> under `adammatthewsteinberger/<runner>`. Those GitHub repositories no longer exist:
> the runners live in this repository under `src/vibey_runners/` (ADR-0021), and
> the only remote is `the-vibey-project/vibey`. As written, `run.sh`, `land.sh`
> and `status.sh` fail at `git fetch` or `gh pr` for any runner repository, and `smoke.sh --live` passes a
> `--max-dollars` option that pytest does not define. Kept as a record; re-point
> the scripts at the monorepo before reusing them.

This directory holds the per-run plan files that drive the fleet program
(`docs/plans/fleet-program-runbook.md`) autonomously, one *loop runner at a
time, in disposable worktrees. The overall program plan (sequencing, verified
state, phase breakdown) is [`docs/plans/fleet-program-runbook.md`](../fleet-program-runbook.md).

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
the worktree on every subcommand that supports it. `run.sh` injects no
system-prompt note: protected paths are named in each plan file and enforced by
`land.sh`. (claudeloop has since gained `--append-system-prompt`, from
`c2-append-system-prompt-claudeloop.md`, but `run.sh` does not use it.)

## Landing a run

```bash
scripts/fleet/land.sh REPO PHASE
```

Pushes the branch, opens (or reuses) a PR against `develop`, watches checks,
and squash-merges **only if every check is green and the diff does not touch
a protected path**. A protected-path diff or a red PR is left open with an
explanation — never silently merged.

## Smoke-testing the fleet

```bash
scripts/fleet/smoke.sh [--repo NAME]... [--live] [--skip-conformance]
```

The fleet-wide gate: the same 7-gate sweep every PR is judged on (4x
100%-branch coverage layers, ruff check/format, mypy --strict, lint-imports,
bandit, pip-audit), run against each repo's actual primary checkout on its
current branch — plus, for vibey, the two-mode `tests/live/` harness
(ADR-0030) and `vibey doctor --conformance` across every installed engine
binary. Defaults to all 5 repos; pass `--repo NAME` (repeatable) to scope it.
Meant to be green before any TestPyPI/PyPI publish (Phase F's `harness` gate).

The harness has two markers in `pyproject.toml`: `live` (faked mode — real
loop binaries driven by scripted agents) and `paid` (real models; needs API
keys and costs money). The default `addopts` exclude only `paid`. Real-model
tests are selected with `pytest -m paid`. `smoke.sh --live` still runs
`pytest -m live --max-dollars 5` with `VIBEY_LIVE_ENGINES` set; pytest defines
no `--max-dollars` option, so that invocation aborts with an
unrecognized-argument error.

## Protected paths

A run must not modify these without explicit human review (enforced by
`land.sh`'s refusal, not just convention):

- `tests/infrastructure/db/test_chaos.py` — the chaos test
- `tests/domain/test_noloss*.py`, `tests/domain/test_briefing.py` — the
  no-loss property suite
- `tests/system/test_delivery_stage_set.py` — the full-cycle system test
- `tests/live/**` — the two-mode harness (`-m live` faked, `-m paid` real),
  landed with vibey PR #17

No CI job or CODEOWNERS rule enforces these paths; `land.sh` is the only guard,
and it is dormant.

## Known gaps that shape the launcher today

- **codexloop's `run` has no `--cwd`** — still true at codexloop 0.4.0. The
  c-guardrails phase added `--cwd` across claudeloop only, not to `codexloop run`.
  `run.sh` works around it by `cd`-ing into the worktree before invoking
  codexloop — this is exactly the class of incident `--cwd` normally
  prevents, so codexloop runs need extra care.
- **`cursor-agent` is not installed** on the development machine (checked
  2026-09-15; `codex` now is). cursorloop plan files therefore assume a driver
  of `claudeloop` (cross-repo dogfooding: claudeloop's own agent does the work
  on the cursorloop code) until `cursor-agent` is installed. When this was
  written (2026-08-17) `codex` was missing too.
- `scripts/fleet/status.sh` tabulates every worktree under
  `~/.cache/fleet-worktrees/` with its PR and check state — run it any time
  to see what's in flight.

## Plan-file status

Checked against `src/vibey_runners/` and `src/vibey/` on 2026-09-15.

| Status | Plan files | Evidence |
|---|---|---|
| Landed | `agent-docs-{agyloop,claudeloop,codexloop,cursorloop,vibey}` | each runner directory carries `AGENTS.md`/`CLAUDE.md`/`GEMINI.md` and the agent-surface trees |
| Landed | `b-soft-stop-codexloop` (+ `-fixup`, `-fixup2`), `b-soft-stop-cursorloop` | `WindDownCommand` in `codexloop/domain/control.py`, `WindDown` in `cursorloop/domain/control.py`; `wind-down` CLI; exit 75 |
| Landed | `c-guardrails-claudeloop` (+ `-fixup`), `c2-append-system-prompt-claudeloop` | `--cwd` across claudeloop's CLI; `--append-system-prompt` on `claudeloop run` |
| Landed | `c2-harness-fix-agyloop` (+ `-fixup`), `c3-harness-handshake-agyloop` | CLI-gateway capacity probe, `--no-probe`, codesigned harness in `agyloop` |
| Landed | `c4-wire-events-sink-codexloop`, `c4-wire-events-sink-cursorloop` | `JsonlRunEventSink` constructed in each runner's `bootstrap.py` |
| Landed | `e1-live-engines-vibey` (+ `-fixup-runid`), `e1-loop-event-map-vibey`, `e1-loopadapter-conformance-hang-vibey`, `e1-conformance-timeout-vibey` | `LoopProcessAdapter`, `loop_events.LOOP_EVENT_MAP`, `--run-id` in `infrastructure/engines/argv.py`, `tests/live/` |
| Open | `b-soft-stop-agyloop` | agyloop has no `WindDownCommand`, no `wind-down` command (only the unrelated `unwind`), and no `write_handoff_marker` |
| Unverified | `d0-completion-detection-cursorloop`, `d0-meta-status-codexloop` | not checked against the runner code |

`patches/cursorloop-wind-down-draft.patch` is superseded by the landed
cursorloop wind-down.

## Concurrency

At most 5 runs in flight at once (agreed budget). Each run gets its own
worktree and PR; they don't interact except by landing onto the same
`develop` branch, so land in whatever order goes green first.
