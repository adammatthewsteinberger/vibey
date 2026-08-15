# Session Handoff — vibey, after M0–M4

> **You are picking up an in-progress, test-first implementation of vibey**, a
> queue-based six-phase conductor for autonomous software delivery. It has two
> three-phase stage sets: delivery (①–③) and Azure deployment (④–⑥). This
> document is written so you can continue the work with zero prior context.
> Read it fully before touching code. It is long on purpose — the previous
> session spent its entire budget building a foundation that a rushed
> continuation could easily damage.

**Read the design docs first, in this order, before writing any code:**
`README.md` → `docs/plans/architecture-and-roadmap.md` →
`docs/plans/implementation-plan.md` (the milestone table is the spec for
"what to build next") → `docs/plans/domain-model.md` → whichever of
`data-model.md` / `handoff-protocol.md` / `rotation-and-engines.md` /
`phase-protocols.md` covers the milestone you're starting. The 13 ADRs in
`docs/architecture/decisions/` explain *why* the hard calls were made — read
the ones relevant to what you're touching before you touch it.

---

## 1. What state this repo is in right now

Five commits on `main`, all in this session, each a complete milestone with
its own green gate sweep:

```
578421f feat: scaffold M0 repo skeleton, onion contract, CI, and vibey.toml schema
7114e37 feat: implement M1 pure domain (phase machine, rotation, no-loss gate)
6cbff9b feat: implement M2 durable queue and crash-safe workers
0b6c1cc feat: implement M3 engine adapters and conformance suite
df9243f feat: implement M4 ledger and handoff -- the no-loss critical path
```

**Milestones M0 through M4 are done.** That is the foundation layer: pure
domain logic, the Postgres queue, engine adapters, and the ledger/handoff
no-loss gate. Nothing product-shaped exists yet — no phase orchestration, no
CLI beyond `--version`, no TUI, no actual `vibey design|build|review`
commands. That starts at M5.

**Test suite right now:** 436 tests, 98%+ overall coverage, **100% coverage
on `domain/`** (a hard CI gate, not a target). All tests pass repeatably —
several were checked for flakiness by running 3–6 times in a row before being
trusted (see §6, "things that looked like they passed but weren't," for why
this matters).

### 1.1 Directory layout as it exists today

```
vibey/
├── .github/workflows/
│   ├── ci.yml                    # 7-gate CI + Postgres 17 service container
│   └── release-please.yml
├── .importlinter                 # onion contract: domain / application / infrastructure / cli+tui
├── .pre-commit-config.yaml       # ruff, ruff-format, mypy, lint-imports, full test suite, conventional-commit
├── docs/                         # the design docs — READ THESE, do not skim
│   ├── architecture/decisions/   # 13 ADRs, 0001-0013 (0012 superseded)
│   └── plans/                    # architecture-and-roadmap, domain-model, data-model,
│                                 # handoff-protocol, rotation-and-engines, phase-protocols,
│                                 # implementation-plan  <- the milestone table lives here
├── migrations/                   # 0001-0008, forward-only SQL, checksum-guarded
├── pyproject.toml                # deps, ruff/mypy config, pytest markers
├── src/vibey/
│   ├── domain/                   # STDLIB ONLY. 100% coverage floor. See §2.
│   ├── application/               # Protocols (ports), DTOs, use-case orchestration. See §3.
│   ├── infrastructure/
│   │   ├── db/                   # Postgres repositories (asyncpg). See §4.
│   │   ├── engines/               # EngineAdapter implementations, descriptors, classify. See §5.
│   │   ├── ledger/                # redaction, FullLedger writer. See §4.
│   │   └── config_loader.py
│   ├── cli/main.py               # just `vibey --version` so far
│   ├── tui/                      # empty, nothing built yet
│   └── bootstrap.py              # EMPTY — the composition root nothing wires into yet
└── tests/                        # mirrors src/ layout exactly
```

### 1.2 How to verify this all still works before you change anything

```bash
# Postgres 17+ must be running locally and reachable. This session used
# Homebrew's postgresql@18 with peer/trust auth (no password needed for the
# local user). Confirm with:
psql -U "$(whoami)" -d postgres -c "select version();"

# Create the test database once (idempotent to re-run, it'll just error harmlessly
# if it exists):
psql -U "$(whoami)" -d postgres -c "CREATE DATABASE vibey_test;"

# Then run the exact gate sequence CI runs:
cd vibey
export VIBEY_TEST_DATABASE_URL="postgresql://$(whoami)@localhost:5432/vibey_test"
uv run ruff check .
uv run ruff format --check .
uv run mypy --strict src/vibey
uv run pytest tests/domain --cov=vibey.domain --cov-report=term-missing --cov-fail-under=100
uv run pytest --cov=vibey --cov-report=term-missing --cov-fail-under=90
uv run lint-imports
uv run bandit -q -r src/vibey
uv run pip-audit
```

All seven gates must be green before you commit anything. `pre-commit run
--all-files` (with `VIBEY_TEST_DATABASE_URL` exported) runs the equivalent
local subset and is faster to iterate with.

If you don't have Postgres available in your environment: the domain-only
gate (`pytest tests/domain`) and most of `application/` tests run without a
database. Tests requiring Postgres are marked `@pytest.mark.integration`
(applied automatically to everything under `tests/infrastructure/db/` by
`tests/infrastructure/db/conftest.py`'s `pytest_collection_modifyitems`) —
you can exclude them with `-m "not integration"`, but you will not be able to
validate M2/M3/M4 repository code without a real Postgres. **Do not mock
Postgres to work around this** — every prior session deliberately tested
against a real database per the project's own ground rules
(`docs/plans/implementation-plan.md` — "testcontainers Postgres, never
mocked"). If you truly cannot get Postgres, say so explicitly rather than
weakening the tests.

---

## 2. `domain/` — the pure core (100% coverage, stdlib only)

This is the layer where being wrong is silent, per its own docstring
philosophy in `docs/plans/domain-model.md`. Every file here:

- imports nothing but the Python standard library and other `domain/` modules
  (enforced by `.importlinter`'s `domain-independence` contract, which
  explicitly forbids `asyncpg`, `psycopg`, `httpx`, `typer`, `structlog`,
  `pydantic`, `textual`, and cross-layer imports)
- contains no `async def`, no `await`, no `open()`, no `pathlib`, no
  `subprocess`, no `os.environ`, no ambient `datetime.now()` (time is always
  a parameter) — enforced by an AST-walking test,
  `tests/domain/test_domain_purity.py`, which is itself tested against a
  planted violation
- is frozen, slotted dataclasses and pure functions
- carries a **100% branch coverage floor** in CI (`pytest tests/domain
  --cov-fail-under=100`) — this is not aspirational, the build fails under it

### 2.1 What's implemented in `domain/`

| File | What it is | Why it matters |
|---|---|---|
| `errors.py` | `VibeyError` hierarchy | base for every domain exception |
| `phase.py` | `Phase` enum, `PhaseState`, `evaluate_transition()`, `next_phase_after_review()` (ADR-0010's routing logic) | the phase machine's legality rules |
| `effort.py` | `Effort` 5-level ladder, `effort_for_attempt()` (the BUILD escalation ladder), `forces_rotation()` | ADR-0006 |
| `capacity.py` | `Available \| WindowExhausted \| CreditsExhausted \| AuthenticationFailed` | `CreditsExhausted` **deliberately has no `resets_at` field** — this is the single most important invariant in the whole codebase, see §2.2 |
| `circuit.py` | `CircuitState`, `schedule_probe()` | the property test `test_credits_never_produce_a_deadline` lives here |
| `engine.py` | `EngineId`, `Capability`, `EngineDescriptor`, `EngineInvocation`, `IsolationLevel` | descriptor shape; `saturates_at()` |
| `rotation.py` | `Candidate`, `select()` (nginx-style Smooth Weighted Round Robin), `eligible()`, the four weight factors | ADR-0005; properties: no-starvation, weight-fidelity, determinism, exclusion-honored |
| `ledger.py` | `EventKind` (19 kinds), `LedgerEvent`, `digest_event`/`digest_range`, `open_items()` | ADR-0003; the event vocabulary everything else translates into |
| `handoff.py` | `HandoffEnvelope`, `HandoffBrief`, `GateResult`, `GateRule` (R1–R10), `Violation`, `LedgerRef`, `RepoState` | the shapes the no-loss gate operates on |
| `noloss.py` | `verify()` — **the 10-rule no-loss gate** | ADR-0004; this function is why rotation is safe. Read it before touching anything that produces a `HandoffBrief` |
| `briefing.py` | `build_deterministic_brief()` — the "floor" brief producer | proven lossless by a Hypothesis property test, not just asserted (see §2.3) |
| `projections.py` | `build_open_items`, `build_decision_log`, `build_cost_report`, `build_work_ledger` | pure replay-based projections over `Sequence[LedgerEvent]` |
| `job.py` | `JobState`, `FailureClass`, `backoff()`, `idempotency_key()` | queue semantics shared by domain and infra |
| `spec.py` | `DesignSpec`, `AcceptanceCriterion`, `NonFunctionalRequirement` (Planguage-shaped), `is_buildable()` | **not yet used by anything** — built in M1, will be consumed starting M5 (DESIGN phase) |
| `review.py` | `Severity`, `Ambiguity`, `UserVerdict`, `FindingRef` | **not yet used by anything** except `phase.py`'s signature — will be consumed starting M7 (REVIEW phase) |
| `budget.py` | `BudgetLedger`, `would_exceed()` (checked before escalation, not after) | **not yet wired into the escalation ladder** — `effort_for_attempt()` in `effort.py` does not currently consult a budget; M6 needs to wire this in |
| `config.py` | `vibey.toml` schema, `parse_config()` | round-trips every field in the architecture doc's example config |

### 2.2 The one invariant you must never violate

`CreditsExhausted` (in `capacity.py`) has no `resets_at` field, full stop.
This is enforced at **three independent layers**, and if you ever find
yourself wanting to add a "just this once" deadline to it, stop and re-read
`docs/architecture/decisions/0002-postgres-not-sqlite.md`'s sibling ADRs and
`rotation-and-engines.md` §6.2:

1. **Type-level**: `domain/capacity.py`'s `CreditsExhausted` dataclass
   literally has no such attribute.
2. **Property-tested**: `domain/circuit.py::schedule_probe()` can only
   return a `BackoffProbe` (no deadline) for `CreditsExhausted`, never a
   `DeadlineProbe`. Hypothesis-tested in `tests/domain/test_circuit.py`.
3. **Database-level**: the `engine_health` table
   (`migrations/0007_engine_health_rotation.sql`) has a `CHECK` constraint,
   `credits_never_have_a_deadline`, that makes it **physically impossible**
   to store a `CreditsExhausted` row with a non-null `resets_at` — Postgres
   itself will reject the `INSERT`/`UPDATE`. This is tested directly in
   `tests/infrastructure/db/test_engine_health_repository.py::
   test_credits_exhausted_with_a_resets_at_violates_the_db_check_constraint`,
   which asserts `asyncpg.exceptions.CheckViolationError` is raised.

### 2.3 The other invariant that matters: the floor brief is *provably* lossless

`domain/briefing.py::build_deterministic_brief()` is vibey's brief producer
of last resort — used when no engine can be asked (dead, out of credits,
whatever). It is built directly from the same projections
(`domain/projections.py`) that `domain/noloss.py::verify()` checks, so it
passes the gate by construction. This isn't just asserted in a docstring —
`tests/domain/test_briefing.py::test_deterministic_brief_always_passes_the_gate`
is a Hypothesis property test that generates random combinations of open
questions/decisions/assumptions/findings (with realistic answered/superseded/
resolved variants) and asserts `verify(...).ok` for every generated ledger.
If you ever change `briefing.py` or `noloss.py`, rerun this test with a high
example count before trusting the change.

---

## 3. `application/` — Protocols, DTOs, and orchestration

Imports `domain/` freely; **must never import `infrastructure/`, `cli/`, or
`tui/`** (enforced by `.importlinter`'s `application-independence`
contract). Concrete implementations of every Protocol here live in
`infrastructure/` and get wired together in `bootstrap.py` — which is
**currently empty**. Nothing is wired into a running CLI command yet; every
piece built so far is exercised directly by tests, not by `vibey` subcommands.

| File | Contents |
|---|---|
| `ports.py` | Every Protocol: `Clock`, `JobRepository`, `HumanGateRepository`, `JobReadyNotifier`, `EngineAdapter`, `BriefProducer`, `EngineHealthRepository` |
| `dto.py` | Every cross-boundary shape: `EnqueueRequest`, `JobRecord`, `HumanGateRequest/Record`, `RunSpec`, `RunHandle`, `PreflightResult`, `StopSummary`, `SnapshotRef`, `EngineEvent`, `ConformanceCheckResult/Report`, `EngineHealthRecord`, `FailureAttribution` |
| `worker.py` | `WorkerLoop` — lease→execute→settle, `Success \| Failure \| Park` outcome ADT, background heartbeat task. 100% covered with **fake ports**, no database (see `tests/application/fakes.py`) |
| `conformance.py` | `run_conformance()` — the 9-check suite from `rotation-and-engines.md` §8.2 |
| `verdict_extraction.py` | `extract_events()` — structured-verdict JSON → closable `ExtractedEvent`s, with vibey-minted ids and normalized-text dedup |
| `text_verdict_fallback.py` | `extract_verdict_from_text()` — heuristic (not LLM) fallback for engines without structured output; **documented stand-in**, see §6 |
| `handoff_orchestration.py` | `produce_and_verify_handoff()` — the STRICT×3→FULL_TRANSCRIPT→HUMAN escalation state machine |
| `seed_prompt.py` | `render_seed_prompt()` — brief → the text handed to an incoming engine's first turn; `closable_ids_in_brief()` |

`tests/application/fakes.py` has `FakeJobRepository` and
`FakeHumanGateRepository` — in-memory Protocol implementations used to unit
test `worker.py` without a database. If you need to test more
Protocol-consuming application code without Postgres, extend these fakes
rather than reaching for a mocking library.

---

## 4. `infrastructure/` — Postgres, engines, ledger mechanics

### 4.1 `infrastructure/db/` — every repository is real-Postgres-tested, never mocked

| File | Backs | Key gotchas |
|---|---|---|
| `migrator.py` | `schema_migration` checksum guard | forward-only; editing an applied migration raises `MigrationChecksumError` |
| `job_repository.py` | `PostgresJobRepository` | `enqueue/claim/heartbeat/ack/nack/park/reap`; `NOTIFY`'s payload **cannot be a bind parameter** — it's f-string interpolated from a `UUID` (safe: UUIDs have no injection surface, but don't copy this pattern for anything user-supplied) |
| `human_gate_repository.py` | `PostgresHumanGateRepository` | park/answer round trip |
| `engine_health_repository.py` | `PostgresEngineHealthRepository` | see §2.2 — this is where the CHECK constraint lives |
| `ledger_repository.py` | `PostgresLedgerRepository` | wraps the `append_event()` SQL function (in `migrations/0002_event.sql`); **redacts the payload and recomputes the digest before persisting** — see §4.3 |
| `handoff_repository.py` | `PostgresHandoffRepository` | persists every attempt's violations as jsonb; `envelope_to_json()` uses `dataclasses.asdict()` + a custom JSON default for UUID/datetime/enum |
| `notifier.py` | `PostgresJobReadyNotifier` | real `LISTEN`/`NOTIFY` with a timeout-based poll fallback |

All of these are tested in `tests/infrastructure/db/` against a real local
Postgres via the `migrated_pool` and `project_id` fixtures in
`tests/infrastructure/db/conftest.py` (which drops and recreates the
`public` schema before every test — **do not point
`VIBEY_TEST_DATABASE_URL` at a database you care about**).

**The chaos test** (`tests/infrastructure/db/test_chaos.py`) is a scoped-down
substitute for the milestone's literal spec (8 OS processes, `SIGKILL` every
2s via testcontainers) — no docker daemon was available in the build
environment. It instead runs 8 concurrent `asyncio` "workers" against real
Postgres, each of which randomly abandons a claimed job mid-flight (the
observable effect of a kill: no ack, no nack, lease just expires), with a
concurrent reaper reclaiming expired leases. It proves the property that
matters — zero double-execution, zero lost jobs across 500 jobs — but it is
**not** literal OS-process chaos testing. If you have docker available, this
is a good candidate to upgrade to the real testcontainers version the plan
originally specified.

**The flagship end-to-end test**
(`tests/infrastructure/db/test_end_to_end_forced_rotation.py`) is the single
most important test in the repo. It runs `ScriptedEngine` A through a
simulated 40-turn run, hits `CreditsExhausted`, builds the deterministic
floor brief from the real (Postgres-persisted) ledger, runs it through the
actual gate escalation state machine, and proves every closable id open when
A died is verbatim in engine B's first seed prompt — with a negative control
proving the gate would have caught a dropped item. Read this test before you
touch `noloss.py`, `briefing.py`, or `handoff_orchestration.py`.

### 4.2 `infrastructure/engines/` — engine adapters

| File | Contents |
|---|---|
| `descriptors.py` | `CLAUDELOOP`, `CODEXLOOP`, `CURSORLOOP`, `AGYLOOP` — verified effort projections transcribed from `rotation-and-engines.md` §3, **except agyloop's, which is a documented reinterpretation** (see §6) |
| `argv.py` | `build_argv()` — descriptor + `RunSpec` → command line; 20 golden files under `tests/infrastructure/engines/golden/` (4 engines × 5 efforts) |
| `scripted.py` | `ScriptedEngine` — the fake runner **everything downstream depends on**. Writes the real `.{engine}loop/runs/<id>/` directory shape (`meta.json`, `events.jsonl`, `audit.jsonl`, `bus.jsonl`, `status.json`, `savepoints.jsonl`, `stop-summary.md`, `inbox/`, `snapshots/latest.json`) to real disk, offline, deterministic. Accepts a `script:` override to control exactly what events a run produces. `help_text` defaults to advertising every flag the descriptor claims (so conformance passes by construction) but can be overridden to a broken string to prove conformance *catches* a gap |
| `classify.py` | `classify_capacity()` (vendor error → `CapacityState`, per-engine) and `attribute_failure()` (exit code + tail → `FailureClass`) — **synthesized fixture payloads, not captured real ones**, see §6. Also exports `CREDITS_FIXTURES`/`WINDOW_FIXTURES`/`AUTH_FIXTURES`/`AVAILABLE_FIXTURES` as public constants shared between the classifier's own tests and the conformance suite |
| `tailer.py` | `translate_event()`/`translate_run_iter()` — `EngineEvent` → `LedgerEventDraft` (everything a `LedgerEvent` needs except `event_id`/`seq`/`digest`, which are minted at append time) |

### 4.3 `infrastructure/ledger/`

| File | Contents |
|---|---|
| `redact.py` | `redact_payload()` — regex-based secret scrubbing (OpenAI/Anthropic-style `sk-`, AWS `AKIA`, GitHub `ghp_`, Slack `xox[baprs]-`, Google `AIza`, JWTs, `Bearer` headers) plus sensitive-key-name matching (`api_key`, `secret`, `password`, `token`, etc.), applied recursively through nested dicts/lists. **Called by `PostgresLedgerRepository.append()` before every write** — the digest is recomputed post-redaction, not pre-redaction, so R6 range integrity reflects what's actually in the column |
| `full_ledger_writer.py` | `write_full_ledger()` — writes `<worktree>/.vibey/handoff/ledger.jsonl`, one JSON line per event ordered by seq, returns a `LedgerRef` whose digest is exactly `domain.ledger.digest_range()` |

---

## 5. Honest scope deviations — read before assuming something is "real"

The previous session was explicit about every place it substituted a
documented stand-in for something the plan called for that wasn't available
in the build environment (no docker daemon, no live provider accounts, no
real `claudeloop`/`codexloop`/`cursorloop`/`agyloop` binaries). These are not
hidden — each is called out in its module's docstring and in the relevant
commit message — but they're collected here so you don't rediscover them the
hard way:

1. **No real vendor binaries or captured error payloads.**
   `infrastructure/engines/classify.py`'s per-engine `CapacityState`
   classifiers are plausible, clearly-documented *reconstructions* of what
   each vendor's error shape might look like, not payloads harvested from
   real incidents. The property that's actually load-bearing and *is*
   rigorously tested — credits and window exhaustion are never confused,
   regardless of engine — holds regardless of whether the exact field names
   match a real vendor's JSON. If you get access to real `*loop` binaries or
   real captured error payloads, this is the first thing to replace.

2. **agyloop's effort descriptor is a reinterpretation, not a transcription.**
   `rotation-and-engines.md` §3 says agyloop has "the same shape as
   claudeloop" (5-level range) but §1's own capability matrix says agyloop
   has **no top-level `--effort` command**, only `--preset`. Since there's no
   `--effort` flag to combine with `--preset`, `descriptors.py` treats
   agyloop as preset-only, saturating at HIGH (the same pattern verified for
   codexloop) rather than inventing two more preset tiers the source table
   never names. This is flagged in the module docstring. Verify against the
   real `agyloop --help` if you ever get access to it.

3. **3.5's "replay a captured real run dir from each engine"** is satisfied
   by replaying a `ScriptedEngine`-produced run directory through the tailer
   instead of a real captured one (`tests/infrastructure/engines/
   test_scripted.py::test_replaying_a_scripted_run_directory_through_the_tailer_produces_ledger_drafts`).

4. **The M2 chaos test is asyncio-level, not OS-process-level.** See §4.1.

5. **`text_verdict_fallback.py`'s extraction is a heuristic line-prefix
   parser** (`Question:`, `Decision:`, `Assumption:`, `Remaining:`,
   `Blocked:`), not the real cheap-model extraction call the design
   describes ("a `TRIVIAL`-effort extraction call parses the free-text turn
   into the same schema"). It produces the identical output schema so
   `extract_events()` downstream never needs to know which path a turn came
   from — that seam is real and correctly placed — but the actual model call
   is not implemented because there's no live model access from within this
   build environment. **When you have model access, replace the body of
   `extract_verdict_from_text()`, not its signature or callers.**

6. **`vibey up`'s Postgres auto-provisioning (task 2.3: BYO → Compose →
   `pg_ctl`) was never built.** It's orthogonal to queue correctness, which
   is what M2 actually needed to prove. If you're building the CLI in M5+
   and need `vibey up` to work end to end, you'll need to write this.

None of these deviations touch the parts of the system that are actually
safety-critical (the no-loss gate, the credits/window distinction, the
queue's crash-safety). They're all in the "talk to a vendor CLI" seam, which
was always going to need real access to finish properly.

---

## 6. Things that looked like they passed but weren't (learn from these)

Two real bugs were caught during M1 by running property tests repeatedly
rather than trusting a single green run — worth internalizing before you
write more Hypothesis tests:

1. **A duplicate-`engine_id` precondition violation in
   `domain/rotation.py::select()`.** A Hypothesis test generated candidate
   lists with repeated `engine_id`s (an unrealistic input — there are only 4
   known engines and a real caller never offers the same one twice), and
   `select()`'s dict-keyed-by-`engine_id` construction silently dropped one
   candidate's weight, occasionally producing `NoEligibleEngine` when a
   valid candidate existed. Fixed by making `select()` explicitly validate
   uniqueness and raise `ValueError` rather than silently misbehave — a real
   hardening, not just a test fix. See `test_select_rejects_duplicate_engine_ids`.

2. **A coverage flake in `domain/phase.py`.** A branch
   (`_guard_review_to_done`'s "not accepted" path) was only ever covered by
   Hypothesis's randomized fuzz test, not by a deterministic unit test — so
   the 100%-coverage gate passed or failed depending on the random seed.
   Fixed by adding an explicit deterministic test for that exact branch.
   **Lesson: if `pytest --cov-fail-under=100` passes, rerun it 3–5 times
   before trusting it — a property test can accidentally be the only thing
   covering a branch, which means coverage becomes seed-dependent.** This
   was caught by literally doing that (`for i in 1 2 3 4 5 6; do uv run
   pytest ...; done`) — it's a cheap habit, keep doing it after any change
   touching `domain/`.

---

## 7. What to build next — M5 onward

Per `docs/plans/implementation-plan.md`, in order:

- **M5 — Phase ① DESIGN.** The 7-stage structured interview protocol
  (`docs/plans/phase-protocols.md`), consuming `domain/spec.py` (currently
  unused) and producing an accepted `DesignSpec`. This is also where a real
  CLI command (`vibey design`) and the first actual use of `bootstrap.py`
  (wiring `PostgresJobRepository` etc. into a running process) needs to
  happen — nothing has been wired into an executable command yet.
- **M6 — Phase ② BUILD.** Parallel worktrees, the escalation ladder (needs
  `domain/budget.py`'s `would_exceed()` wired into `effort_for_attempt()`,
  which isn't connected yet), integration.
- **M7 — Phase ③ REVIEW and the loop-backs.** Consumes `domain/review.py`
  (currently only referenced by `phase.py`'s type signature, not
  substantively used). Full `③→①→②→③` cycle test.
- **M8 — Operability.** TUI (`vibey/tui/` is currently empty), cost
  reporting, OTel, notifications.
- **M9 — Isolation and security.** Container/VM isolation levels beyond the
  `worktree` default; threat-model review.
- **M10 — Phases ④–⑥, the Azure deployment stage set.** Phase ④ interactively
  establishes an accepted deployment contract, Phase ⑤ deploys autonomously
  until verified success or a failure needs user input, and Phase ⑥ demos the
  result or routes the failure back to ④, ⑤, or the appropriate delivery phase.
  ADR-0013 supersedes ADR-0012's separate-CLI lifecycle decision.

The implementation plan explicitly notes M5 onward is "the bootstrap: the
tool builds its own remaining phases" — i.e., once DESIGN/BUILD/REVIEW work
end to end, vibey is meant to start building itself. That's a milestone
worth pointing out to whoever picks this up, since it changes the character
of the work from "build the orchestrator" to "use enough of the orchestrator
to have it help build the rest."

### Before starting M5, specifically:

1. Read `docs/plans/phase-protocols.md` §1 (DESIGN) in full.
2. Look at `application/ports.py` and decide what new Protocols DESIGN needs
   (a `SpecRepository`? A way to persist/query the interview's question/
   answer history against the `event` ledger via `EventKind.QUESTION_ASKED`/
   `ANSWER_GIVEN`, which already exist and are already tested in
   `domain/ledger.py`).
3. `bootstrap.py` is empty. M5 is likely the first milestone that actually
   needs it populated — decide the wiring pattern (a single `build_app()`
   function returning a struct of concrete Protocol implementations is a
   reasonable default, but there's no existing precedent in this repo to
   follow, so use your judgment and keep it out of `domain/`/`application/`).
4. The onion contract (`.importlinter`) will immediately catch you if
   `cli/` or a new phase-orchestration module accidentally imports something
   it shouldn't. Run `uv run lint-imports` early and often while wiring.

---

## 8. Working agreements this session followed (keep following them)

From `docs/plans/implementation-plan.md`'s own "Ground rules," which are not
optional:

1. **Test first.** No production file gets written before a failing test
   names it.
2. **`domain/` and `application/` carry hard coverage floors** — `domain/`
   at 100%, enforced in CI. Not "aim for."
3. **Every commit-worthy change runs the full 7-gate sweep**: `ruff check`,
   `ruff format --check`, `mypy --strict`, `pytest` (both the domain-only
   100% run and the full-suite 90% run), `lint-imports`, `bandit`,
   `pip-audit`.
4. **Conventional Commits**, enforced by the installed commit-msg hook — a
   non-conventional message is physically rejected, not just discouraged.
5. Real Postgres for anything touching `infrastructure/db/`, never mocked.
6. When something can't be built faithfully (no docker, no live model
   access, no real vendor binary), **build the closest faithful substitute,
   document the deviation loudly in the module docstring and the commit
   message, and make sure the substitute doesn't compromise whatever
   property is actually safety-critical.** Don't skip the task; don't fake
   the property that matters.

---

## 9. Quick reference: commands you'll run constantly

```bash
# Full domain-only loop (fast, no DB needed)
uv run pytest tests/domain --cov=vibey.domain --cov-report=term-missing --cov-fail-under=100

# Full suite (needs Postgres + VIBEY_TEST_DATABASE_URL exported)
uv run pytest --cov=vibey --cov-report=term-missing --cov-fail-under=90

# Onion architecture check
uv run lint-imports

# Everything pre-commit runs
uv run pre-commit run --all-files

# Reset the test database by hand if a test leaves it in a weird state
psql -U "$(whoami)" -d vibey_test -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
```

Good luck. The foundation is solid — 436 tests, every safety-critical
invariant enforced at more than one layer, nothing mocked that shouldn't be.
Build on it carefully.
