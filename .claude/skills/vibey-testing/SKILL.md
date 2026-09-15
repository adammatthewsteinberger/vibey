---
name: vibey-testing
description: The 100% per-layer coverage gates, running tests locally, Postgres integration tests (never mocked), property testing for rotation and no-loss gate, the chaos test, the test tree, and markers.
allowed-tools: Read Bash(pytest)
---

# vibey testing

## Coverage floors — not targets

Every layer carries a **100% branch coverage floor**, enforced in CI as one
test run and four per-layer reports:

```bash
uv run pytest -q -p no:cacheprovider --cov=vibey --cov-branch --cov-report=
uv run coverage report --include='src/vibey/domain/*' --fail-under=100
uv run coverage report --include='src/vibey/application/*' --fail-under=100
uv run coverage report --include='src/vibey/infrastructure/*' --fail-under=100
uv run coverage report --include='src/vibey/cli/*' --fail-under=100
```

The build **fails** if any layer drops below 100%. This is not aspirational
(ADR-0023). `tui/` has tests under `tests/tui/` but no floor of its own.

## Running locally

The default `addopts` are `-m 'not paid' -n auto --maxprocesses=8`: paid tests are
excluded and everything runs under pytest-xdist.

**Every session needs Postgres**, including a run of pure domain tests:
`tests/conftest.py` connects at `pytest_configure`, migrates a
`vibey_test_template` database once, clones it into a database per xdist worker,
and repoints `VIBEY_TEST_DATABASE_URL` at the clone. The role in the DSN must be
able to connect to the `postgres` database and run `CREATE DATABASE`.

```bash
export VIBEY_TEST_DATABASE_URL="postgresql://$(whoami)@localhost:5432/vibey_test"
uv run pytest tests/domain -p no:cacheprovider            # one area, xdist on
uv run pytest tests/domain -o addopts="" -m "not paid"    # serial, for a debugger
```

Overriding `addopts` also drops the paid-test exclusion; keep `-m "not paid"`.
CI uses `postgresql://vibey:vibey@localhost:5432/vibey_test` on a `postgres:17`
service container.

## Test tree

| Path | What lives there |
|---|---|
| `tests/domain/` | Pure unit and Hypothesis property tests, plus `test_domain_purity.py` |
| `tests/application/` | Use cases and handlers against fakes |
| `tests/infrastructure/` | Adapters; `db/` runs against real Postgres, `engines/` holds argv golden files and classifier tests (the fixtures live in `infrastructure/engines/classify.py`) |
| `tests/cli/`, `tests/tui/` | Typer commands; the Textual dashboard |
| `tests/fakes/` | Shared fakes and `test_port_parity.py`, which fails when a fake misses a Protocol method |
| `tests/contracts/` | The same contract run against a fake and the Postgres implementation |
| `tests/live/` | The two-mode live harness (ADR-0030): faked mode (`live`; `ScriptedEngine` and scripted stand-in binaries, no model calls) and paid mode (`paid`; real binaries against real models) |
| `tests/system/` | Delivery-stage-set and full-worker end-to-end tests (`system`) |
| `tests/meta/` | Repository invariants: `test_adr_counts.py`, `test_container_context.py` |
| `tests/test_bootstrap.py` | The composition root |

`tests/meta/test_adr_counts.py` fails when an ADR is added without updating the
"(N ADRs" count in `CLAUDE.md`, `AGENTS.md`, `GEMINI.md`, `README.md` and
`docs/index.md`, when ADR numbering has a gap, or when an ADR is missing from the
`properdocs.yml` nav. `tests/meta/test_container_context.py` fails when
`.dockerignore` excludes a tracked file the Dockerfile copies.

## Tenant suites

The root `pytest` (`testpaths = ["tests"]`) never runs the workspace tenants'
tests. Each has its own suite and configuration: `src/vibey_tools/gh/test/`,
`src/vibey_tools/bootstrap/test/`, `src/vibey_tools/skills/tests/`, and
`src/vibey_runners/<engine>/tests/`. See the `vibey-quality-gates` skill for the
exact commands and which of them CI runs.

## Postgres integration tests — never mocked

All `tests/infrastructure/db/` tests run against a **real ephemeral Postgres**
via the `migrated_pool` and `project_id` fixtures in
`tests/infrastructure/db/conftest.py`. Every test drops and recreates the
`public` schema before running.

**Why real Postgres, never mocked:** because `SELECT ... FOR UPDATE SKIP
LOCKED` semantics are the thing under test. A mock cannot faithfully represent
concurrent worker contention, lease expiry, or the reaper reclaiming expired
leases. See ADR-0002.

Set `VIBEY_TEST_DATABASE_URL` (see "Running locally"); without it the root
conftest falls back to `postgresql://<current user>@localhost:5432/vibey_test`.

## Property tests — the safety-critical invariants

**Rotation fairness** (`tests/domain/test_rotation.py`):
- Over any eligible set and any weight vector, every engine is selected at
  least once per `sum(weights)` selections (no starvation).
- Determinism: identical candidate state produces identical selection.
- Exclusion honored: an engine in `requirement.excluded` is never returned.

**No-loss gate soundness** (`tests/domain/test_noloss.py`):
- For any ledger and any brief that *omits* a closable item, the gate returns
  a violation naming that item. Generated adversarially via Hypothesis.

**Credits-never-have-a-deadline** (`tests/domain/test_circuit.py`):
- `schedule_probe(CreditsExhausted(...), ...)` can only return a `BackoffProbe`,
  never a `DeadlineProbe`. This is the single most important property test in
  the codebase.

**Deterministic brief is provably lossless** (`tests/domain/test_briefing.py`):
- `build_deterministic_brief()` (the floor brief producer) is built from the
  same projections (`domain/projections.py`) that `domain/noloss.py::verify()`
  checks, so it passes the gate by construction. Hypothesis property test
  generates random ledgers and asserts `verify(...).ok`.

## The chaos test

`tests/infrastructure/db/test_chaos.py` runs 8 concurrent asyncio "workers"
against real Postgres, each randomly abandoning a claimed job mid-flight (the
observable effect of a kill: no ack, no nack, lease just expires), with a
concurrent reaper reclaiming expired leases. It proves the property that
matters: **zero double-execution, zero lost jobs** across 500 jobs.

This is a scoped-down substitute for the implementation plan's literal spec
(8 OS processes, `SIGKILL` every 2s via testcontainers) — no Docker daemon
was available in the build environment. If you have Docker available, upgrade
this test to the real testcontainers version.

## The flagship end-to-end test

`tests/infrastructure/db/test_end_to_end_forced_rotation.py` is the **single
most important test in the repo**. It runs `ScriptedEngine` A through a
simulated 40-turn run, hits `CreditsExhausted`, builds the deterministic
floor brief from the real (Postgres-persisted) ledger, runs it through the
actual gate escalation state machine, and proves every closable id open when
A died is verbatim in engine B's first seed prompt — with a negative control
proving the gate would have caught a dropped item.

Read this test before touching `noloss.py`, `briefing.py`, or
`handoff_orchestration.py`.

## Markers

- `@pytest.mark.integration` — requires Postgres (auto-applied to everything
  under `tests/infrastructure/db/` by conftest).
- `@pytest.mark.slow` — takes more than a couple seconds.
- `@pytest.mark.system` — delivery-stage-set end-to-end system test.
- `@pytest.mark.live` — tests against real loop binaries in faked mode (scripted
  agents, no model calls), in `tests/live/`.
- `@pytest.mark.paid` — real models, real API keys, real money. **Excluded by
  default**; opt in with `-m paid`.
