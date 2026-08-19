# The greeter live demo: a real project, real engines, one forced rotation

This runbook drives one small project ("a CLI greeter") end to end on real
`*loop` binaries: DESIGN through the interactive interview, BUILD on
engine-selected sessions, REVIEW with real automated gates, and DONE(local).
Along the way it demonstrates the two behaviors the whole design exists
for: **per-job engine rotation** and **the no-loss wind-down handoff**.

It costs real money (live claudeloop/agyloop sessions). Budget caps are
enforced per run (`--max-turns`, `--max-dollars`), but expect a few dollars
across the whole demo.

## Prerequisites

- PostgreSQL running locally, and `VIBEY_PG_URL` pointing at a database you
  own (never SQLite; see ADR-0002).
- At least two engines installed and authenticated — this runbook uses
  `claudeloop` and `agyloop`. `vibey doctor` will tell you which are ready.
- A clean working directory for the project repo.

## 1. Record engine health

Selection is driven by the `engine_health` table. An engine with no
recorded conformance is **ineligible** — the worker will warn and never
select it. Record both:

```bash
vibey doctor --conformance --record
```

This runs the 9-check conformance suite against every installed engine and
persists preflight + conformance for the latest project (use `--project` to
target another). Re-run it whenever an engine is updated.

## 2. Create the project

```bash
mkdir ~/demos/greeter && cd ~/demos/greeter && git init
vibey new greeter --repo . --max-cycles 3
```

`vibey new` enqueues the first `design.interview` job. Nothing runs yet —
jobs run only inside a worker.

## 3. Start the worker

```bash
vibey worker --provider claudeloop --engines claudeloop,agyloop
```

- `--provider claudeloop` makes the DESIGN interview and the BUILD
  decomposition use live ClaudeLoop calls (the default `scripted` provider
  is for tests).
- `--engines claudeloop,agyloop` is the allow-list: BUILD jobs select
  between exactly these two via smooth-weighted round-robin, per job.

The worker LISTENs on `vibey_job_ready`, so answers you give in another
terminal wake it immediately.

## 4. Answer the DESIGN gates

The interview parks on human gates. In a second terminal:

```bash
vibey status            # shows the parked gate and its questions
vibey answer <gate-id> q-1="a CLI that greets the user by name" q-2="..."
```

Repeat until the interview completes and the design is accepted (decline
the visual-design interstitial when offered — the greeter has no UI).
`vibey watch` gives a live dashboard of the queue, circuits, and ledger
tail while you go.

## 5. Watch BUILD rotate

After acceptance, BUILD decomposes the spec into work items and runs
`build.implement` / `build.verify` jobs on engine-selected sessions:

- every job's selected engine is durable (`job.assigned_engine`);
- each item's **verifier is never its implementer**;
- `vibey engines` shows the selection counts and circuit states live.

## 6. Force a rotation (the E1 milestone)

While a `build.implement` session is running on claudeloop, ask it to wind
down (or wait for a real window exhaustion). The engine exits with code 75;
vibey then:

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
burns the escalation ladder. Three wind-downs on one item park it for you
(`TooManyWindDowns`).

## 7. REVIEW and completion

REVIEW runs the automated review (bandit, ruff) against the integrated
result, then parks the deployment choice. Decline it:

```bash
vibey answer <gate-id> --choice local_only
```

The project records DONE(local). `vibey cost` shows what the demo spent;
`vibey status` should show an empty queue with zero failed jobs.

## If something goes wrong

- **"no recorded conformance" warning at worker startup** — step 1 was
  skipped or failed; engine-driven jobs will sit ready but unselected.
- **A job keeps deferring** — `vibey engines` will show an open circuit
  (capacity) or `vibey status` a pending backoff; both clear on their own.
- **A gate you don't recognize** — `vibey answer --raw '{"...": ...}'`
  covers any shape the typed flags don't.
- Workers are disposable: kill the worker any time; leases expire and the
  next worker replays idempotently.
