# Runbook: cost & performance — insanely optimized, tests and runtime

## Goal

Drive both dollars-per-delivered-work-item and seconds-per-feedback-loop
as low as they can go without sacrificing a single gate. Two fronts: the
test/CI loop (developer + dogfooding velocity) and the runtime (engine
spend + orchestration efficiency).

## Front 1: the test/CI loop

Current pain (measured this week): the full suite is ~6:20, the commit
hook runs it **twice** (~13 min per commit), CI repeats it, and the four
per-layer coverage gates re-run the whole suite four more times
sequentially (~25 min locally). Concurrent suites deadlock on the shared
`vibey_test` database (observed: DROP SCHEMA deadlock), forcing
serialization.

Work items, in expected-impact order:

1. **Per-worker test databases** — template-database pattern: migrate
   once into `vibey_test_template`, each xdist worker clones it
   (`CREATE DATABASE ... TEMPLATE`) in milliseconds. Kills the
   deadlock class entirely and unlocks parallelism.
2. **pytest-xdist** across the suite (`-n auto`): with per-worker DBs,
   target ≤90s for the full suite on this machine.
3. **One coverage run, four gates**: run the suite once with
   `--cov=vibey`, then enforce the four per-layer floors from the single
   `.coverage` file (`coverage report --include=... --fail-under=100` ×4).
   ~25 min → one suite run.
4. **Commit hook diet**: hook runs changed-file lints + the single
   parallel suite once (not twice); the pre-push/CI stage owns the full
   sweep. Target: commit ≤2 min.
5. **CI caching**: uv cache + hypothesis DB cache keyed on lockfile;
   fail-fast lint stage before the test stage.
6. **Perf regression guard**: CI records suite duration; a PR that slows
   the suite >20% gets a visible warning label.

## Front 2: runtime cost & performance

Engine spend (the real money):

1. **Effort right-sizing audit**: greeter4 ran implements at LOW→
   `--preset low --effort medium`; measure verdict-quality-per-dollar per
   tier per engine from ledger data (`cost_usd` by effort by outcome —
   the data already exists) and tune `PHASE_BASE_EFFORT` + projections
   empirically.
2. **Cost-aware rotation**: extend SWRR effective weight with a cost
   penalty (cheaper engine wins ties at equal health/fidelity; ADR-0005
   compatible — it's just weight shaping). `cost_usd_cycle` column
   already exists in engine_health.
3. **Prompt budget**: seed prompts + house rules are resent every
   session; measure and trim rendered prompt sizes; cache-stable prefix
   ordering for engines whose APIs support prompt caching.
4. **Repair-loop economics**: rounds are bounded (PR #59); add
   ledger-derived per-round cost reporting so parks show "3 rounds,
   $4.10" — operators grant with eyes open.

Orchestration hot paths (correctness-preserving):

5. **Ledger scan elimination**: `LedgerBudgetSource`, finding scans, and
   round counters all do `all_for_project()` full scans per claim. Add
   filtered reader queries (kind + cycle + finding-prefix pushed to SQL,
   indexed) — O(events) → O(relevant). Indexes:
   `(project_id, cycle, kind)`, plus a partial index on
   `payload->>'finding_id'`.
6. **Claim batching**: workers claim one job per wake; add
   claim-up-to-K for cheap kinds (verify gates, integrates) while engine
   kinds stay 1-per-worker.
7. **Event tail latency**: loop_process_adapter re-tails on a poll
   interval; switch to fs-event-driven tailing (watchfiles) with poll
   fallback.
8. **Connection discipline**: one shared pool sized to worker
   parallelism; advisory-lock connections accounted; pool metrics into
   the observability layer.

## Verification

- Measured before/after table committed with each item (suite wall time,
  commit hook time, CI wall time, $/greeter-item, claims/sec on a
  20-job queue, p95 event-tail latency).
- Hard targets: full suite ≤90s; commit ≤2 min; per-layer gates from one
  run; greeter-class item median engine cost down ≥25% at equal verify
  pass rate (measured across ≥10 items before/after effort retuning).
- Zero gate relaxation: 100% branch floors, protected tests, chaos and
  property tests all unchanged.

### Front 1 delivery status (PR #70, validated 2026-08-21)

Items 1–4 are **delivered and independently validated** — see
`evidence/13-front1-validation.md`. Suite 383s → 135s (2.8×); the four
per-layer floors now cost one instrumented run plus four
`coverage report` calls, 136s against ~1530s before (**11.3×**), with
every layer still at exactly 100% branch coverage.

**Accepted deviation**: the suite lands at a 135s median against the
≤120s "must" (and the ≤90s target above). Operator-accepted as a speed
shortfall rather than a correctness one — determinism, per-layer
granularity, crash recovery, and protected-file integrity all pass.
**Closing this gap is the job of items 5 and 6 below**, which remain
open; do not treat the ≤90s target as abandoned, only as deferred to
them.

## Needs from operator

Nothing.

## Risks

- Parallel tests expose hidden shared state — fix the tests (isolation
  is a correctness win), never mark-and-skip.
- Effort down-tuning can raise repair rounds — the $/delivered-item
  metric (not $/session) is the optimization target, and the ledger
  provides it.
