# The greeter live demo: a real project, real engines, one forced rotation

This runbook drives one small project ("a CLI greeter") end to end on real
`*loop` binaries: DESIGN through the interactive interview, BUILD on
engine-selected sessions, REVIEW with real automated gates, and DONE(local).
Along the way it demonstrates the two behaviors the whole design exists
for: **per-job engine rotation** and **the no-loss wind-down handoff**.

It costs real money (live claudeloop/agyloop sessions). The BUILD-phase
brake is the per-cycle cap you set at `vibey new` (`--max-cycle-dollars`,
enforced from the ledger's recorded `cost_usd`); without it BUILD spend is
uncapped. The worker's `--max-turns` / `--max-dollars` cap only the
ClaudeLoop process that runs the DESIGN interview and the BUILD
decomposition, not the BUILD engine sessions. Expect a few dollars across
the whole demo.

## Prerequisites

- PostgreSQL running locally, and `VIBEY_PG_URL` pointing at a database you
  own (never SQLite; see ADR-0002).
- At least two engines installed and authenticated — this runbook uses
  `claudeloop` and `agyloop`. `vibey doctor` will tell you which are ready.
- A clean working directory for the project repo.

## 1. Create the project

```bash
mkdir -p ~/demos/greeter && cd ~/demos/greeter && git init
vibey new greeter --repo . --max-cycles 3 --max-cycle-dollars 15
```

`vibey new` prints the project id and enqueues the first
`design.interview` job. Keep the project id: `vibey design accept` needs it
in step 4. Nothing runs yet — jobs run only inside a worker.

## 2. Record engine health

Selection is driven by the `engine_health` table. An engine with no
recorded conformance is **ineligible** — the worker will warn and never
select it. Record both:

```bash
vibey doctor --conformance --record
```

This runs the 9-check conformance suite against every installed engine and
persists preflight + conformance for the latest project — so it needs
`vibey new` to have run first; without a project it exits with "no
projects found" (use `--project` to target another project). Re-run it
whenever an engine is updated.

## 3. Start the worker

```bash
uv run --project <vibey-checkout> vibey worker --provider claudeloop --engines claudeloop,agyloop
```

- `--provider claudeloop` makes the DESIGN interview and the BUILD
  decomposition use live ClaudeLoop calls (the default `scripted` provider
  is for tests).
- `--provider qwenloop` is the sovereign alternative to the paid DESIGN
  provider (ADR-0027). It runs the interview on a local model
  (`QwenloopDesignProvider`: Ollama at `http://127.0.0.1:11434` with
  `qwen2.5-coder:14b`). A local model has no web access, so research reads
  operator-supplied evidence: set `VIBEY_EVIDENCE_DIR` to a directory holding
  one `<topic>.md` per research topic (`prior-art.md`, `libraries.md`,
  `api-docs.md`) whose first line is `source: <where it came from>`. A missing file makes the research job
  refuse rather than invent a source, and synthesis waits on every research
  job. In this mode the BUILD decomposition uses the scripted producer, not a
  live model. This demo uses claudeloop because it exercises paid-pool
  rotation.

  ```bash
  export VIBEY_EVIDENCE_DIR=~/demos/greeter-evidence
  uv run --project <vibey-checkout> vibey worker --provider qwenloop --engines claudeloop,agyloop
  ```

- `--engines claudeloop,agyloop` is the allow-list: BUILD jobs select
  between exactly these two via smooth-weighted round-robin, per job.
- To add qwenloop to the pool as a local standby engine (ADR-0015), export
  `VIBEY_FEATURE_QWENLOOP=1` before both `vibey doctor` and `vibey worker`.
  `[features] qwenloop = true` in `vibey.toml` is honored by `vibey doctor`
  but not by the worker, which reads the project's stored config.
- Launch the worker with `uv run` from the vibey checkout (`--project`), not a
  bare `.venv/bin/vibey`. Verify
  and integrate gate commands run with the worker's own environment, so
  `uv run` is what puts the venv's `bin` on `PATH` for gate binaries such
  as `python`.

The worker LISTENs on `vibey_job_ready`, so answers you give in another
terminal wake it immediately.

## 4. Answer the DESIGN gates and accept the design

The interview parks on human gates. In a second terminal:

```bash
vibey status               # AWAITING_HUMAN: 1 under Queue Depth means a gate is parked
psql "$VIBEY_PG_URL" -c "SELECT gate_id, kind, prompt FROM human_gate WHERE answered_at IS NULL ORDER BY raised_at DESC LIMIT 1;"
vibey answer <gate-id> system_description="a CLI that greets the user by name" --defaults
vibey answer <gate-id> --defaults          # later stages: take every default
```

`vibey status` shows only queue depth per job state, never a gate id or its
questions. The parked gate's id and prompt live in the `human_gate` table
(`answered_at IS NULL`); no CLI command lists them yet, so read them with
`psql`.

Question keys are minted by the model and vary per run — read them from the
gate prompt when you want to answer one explicitly. `--defaults` accepts
every default (blocking questions included) and combines with explicit
pairs, which win; it is the zero-touch path, so an unattended driver never
needs to parse anything.

Repeat until the interview completes. The worker then runs
`design.research` (three topics), `design.synthesize`, and `design.spec` on
its own. When `vibey status` shows no `AWAITING_HUMAN` jobs and those have
succeeded, accept the design. Acceptance is an explicit command, not a
gate:

```bash
vibey design accept <project-id> --no-visual
```

`--no-visual` (the default) declines the VISUAL_DESIGN interstitial and
enters BUILD directly — the greeter has no UI. `vibey watch` gives a live
dashboard of the queue, circuits, and ledger tail while you go.

## 5. Watch BUILD rotate

After acceptance, BUILD decomposes the spec into work items and runs
`build.implement` / `build.verify` jobs on engine-selected sessions:

- every job's selected engine is durable (`job.assigned_engine`);
- each item's **verifier is never its implementer**;
- `vibey engines` prints a snapshot of selection counts and circuit states;
  `vibey watch` keeps them live.

## 6. Force a rotation (the E1 milestone)

While a `build.implement` session is running on claudeloop, ask it to wind
down from another terminal:

```bash
claudeloop wind-down --cwd <repo>/.vibey/worktrees/<cycle>/<item-id> --reason demo
```

(or wait for a real window exhaustion). claudeloop honors the request at
its next natural break, after the turn in flight finishes, so a short
greeter session may complete before the request lands — trigger it early in
a session. The engine exits with code 75; vibey then:

1. writes this cycle's full BUILD ledger to
   `<worktree>/.vibey/handoff/ledger.jsonl`;
2. produces a handoff brief and verifies it against the no-loss gate
   (STRICT, escalating to FULL_TRANSCRIPT, parking for you only if even
   that fails);
3. persists the verified `HandoffEnvelope` (query the `handoff` table:
   `accepted` must be true);
4. enqueues a follow-up `build.implement` whose prompt is the rendered
   brief — every open question, decision, assumption, and finding id
   verbatim — with claudeloop durably excluded, so agyloop picks it up.

The wind-down job settles **Success**: rotation is not a failure and never
burns the escalation ladder. An item may rotate three times; a fourth
wind-down on the same item parks it for you as a `too_many_wind_downs`
gate.

## 7. REVIEW and completion

REVIEW produces the demo artifacts under `.vibey/runs/<cycle>/review/` and
runs the automated review (`ruff check .`, `bandit -q -r src`) against the
integrated result, then parks two gates in turn. Answer the review verdict
first, then decline deployment:

```bash
vibey answer <gate-id> --verdict accept       # review.collect approval gate
vibey answer <gate-id> --choice local_only    # review.deployment_choice gate
```

The project records DONE(local). `vibey cost` shows per-engine spend for
the cycle (ignore its `Cycle Budget Cap` and `Total Budget Cap` lines — they read an
unset `budget` key and print $40.00 and $250.00 regardless of
`--max-cycle-dollars` — and its
per-engine "turns" figure is the selection count, not turns);
`vibey status` should show an empty queue with zero failed jobs.

## If something goes wrong

- **"no projects found" from `vibey doctor --record`** — the project does
  not exist yet; run step 1 first.
- **"no recorded conformance" warning at worker startup** — step 2 was
  skipped or failed; engine-driven jobs will sit ready but unselected. A
  timing-flaky conformance FAIL is possible on a loaded machine: re-run
  `vibey doctor --conformance --record --engine <name>` once.
- **A job keeps deferring** — three causes, none of which `vibey status`
  names (it shows queue depth only): an open circuit (`vibey engines`), a
  capacity backoff, or a verify/integrate repair round in flight (a
  `build.implement` repair job for the same item is queued or running; the
  verify job re-checks every 10 minutes). The reason is stored on the job
  row:
  `psql "$VIBEY_PG_URL" -c "SELECT kind, work_item_id, run_after, last_error->>'detail' FROM job WHERE state='ready' AND run_after > now();"`.
  Watch `vibey ledger show --kind FindingRaised` and `--kind FindingResolved`
  for the repair round to close. Circuits and backoffs clear on their own;
  an open circuit past its reset deadline half-opens automatically at the
  next selection and closes itself on the first success.
- **A `verify_repair_exhausted` / `integrate_repair_exhausted` gate** —
  the item burned its bounded repair rounds. Grant more with
  `vibey answer <gate-id> --raw '{"max_rounds": 6}'` (the prompt suggests
  a value), or fix the branch by hand and answer anything to retry. Bounded
  ladders park with grants rather than failing (ADR-0024).
- **A `budget_exhausted` gate** — the cycle's ledger-recorded spend crossed
  `--max-cycle-dollars` (or `--max-cycle-turns`), or the next attempt's
  projected cost would. No further engine session starts until you raise
  the cap: `vibey answer <gate-id> --raw '{"max_dollars": 25}'` (add
  `"max_turns": N` to raise the turn cap too; the prompt suggests a value),
  or leave it parked to stop here.
- **An `escalation_exhausted` gate** — the item burned the six-rung effort
  ladder (the seventh attempt parks). Grant more with
  `vibey answer <gate-id> --raw '{"max_attempts": 10}'` (they run at the
  ladder's top effort), or fix the item by hand and answer anything to let
  the next verify pass.
- **A verify gate fails with `gate command could not start` (exit 127)** —
  the engine wrote a gate command (often `python`) whose binary is not on
  the worker's `PATH`. That is a failing gate the repair loop fixes, not a
  vibey failure, but launch the worker with `uv run` (step 3) so the
  venv's `bin` is on `PATH` for gate commands. Known open issue: engine
  sessions have been observed installing packages into vibey's own venv;
  if `vibey doctor` starts failing after a run, `uv sync` restores it.
- **A gate you don't recognize** — `vibey answer --raw '{"...": ...}'`
  covers any shape the typed flags don't.
- Workers are disposable: kill the worker any time; leases expire and the
  next worker replays idempotently.
