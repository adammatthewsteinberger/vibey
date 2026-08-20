# Design spec

## Objective

Execute Front 1 (items 1-4 of the test/CI loop) of docs/runbooks/expansion/13-cost-performance.md: (1) per-worker test databases via the PostgreSQL template-database pattern (migrate once into a template, each pytest-xdist worker clones it with CREATE DATABASE ... TEMPLATE) so suites never contend on or deadlock over a shared vibey_test; (2) pytest-xdist parallelism (-n auto, capped at 8 workers) across the whole suite; (3) a single full-coverage run (--cov=vibey --cov-branch) that enforces all four per-layer 100% branch floors from one combined .coverage file via four `coverage report --include=... --fail-under=100` invocations, replacing four sequential full-suite runs; (4) a commit-hook diet so the pre-commit hook runs changed-file lints plus the single parallel suite exactly once (not twice), while pre-push/CI owns the full 7-gate sweep. Deliver with measured before/after evidence committed alongside the change.

## Constraints

- [hard] Scope is Front 1 items 1-4 only. Do not start Front 2 (runtime cost work), nor Front 1 items 5 (CI caching) or 6 (perf regression guard), in this cycle.
- [hard] Changes are minimal and surgical, confined to: tests/conftest.py and test fixtures/helpers, pyproject.toml, .pre-commit-config.yaml, and .github/workflows/ci.yml. No changes under src/vibey/ are expected; if one proves necessary it must be justified in the PR and must not touch domain/ purity.
- [hard] Never relax any gate: the four 100% branch-coverage floors (domain, application, infrastructure, cli), mypy --strict, import-linter onion contracts, bandit, pip-audit, ruff check, ruff format --check all remain enforced at their current strictness.
- [hard] Protected test files must remain byte-untouched: tests/system/test_delivery_stage_set.py, tests/domain/test_noloss*.py, tests/domain/test_briefing.py, tests/infrastructure/db/test_chaos.py, tests/live/**. Verify with `git diff --stat` against develop before merge.
- [hard] Tests that fail under parallelism are fixed by improving their isolation (fixtures, per-worker resources, unique names), never by marking, skipping, deselecting, serializing via xdist groups as a workaround, or adding retries. Zero tolerance for non-deterministic behavior under -n auto.
- [hard] CI workflow changes must preserve every existing job and step name exactly (e.g. 'Gate 1 - ruff check', 'Gate 4a - pytest domain layer (100% coverage)', 'Gate 4b - pytest application layer (100% coverage)', 'Gate 4c - pytest infrastructure layer (100% coverage)', 'Gate 4d - pytest CLI layer (100% coverage)', 'Gate 5 - lint-imports (onion contract)', 'Gate 6 - bandit', 'Gate 7 - pip-audit', 'uv.lock is in sync with pyproject.toml') so branch protections keep matching. The single suite run may be a new step; the four Gate 4x steps become `coverage report` invocations against the shared .coverage file.
- [hard] domain/ stays pure stdlib; no fixture or plugin change may introduce an import into src/vibey/domain.
- [hard] PostgreSQL remains the only test database backend (never SQLite); Postgres integration tests stay real, never mocked.
- [hard] Template strategy: one shared template database (vibey_test_template, per the runbook) is migrated once per session by a single coordinator (or under an advisory lock so concurrent workers cannot race), then cloned once per xdist worker at session start into vibey_test_<worker_id> (e.g. vibey_test_gw0); the non-xdist case (no worker id) still works with a single clone so plain `pytest path/to/test.py` keeps functioning.
- [hard] Worker-specific databases are created at session start and dropped at session end; a crashed run must not leave the next run unable to start (drop-if-exists before create).
- [soft] Worker count policy: -n auto capped at 8 (e.g. via --maxprocesses=8 or equivalent) to avoid connection exhaustion and diminishing returns; the cap must be respected on both local machines and CI runners.
- [hard] Existing pytest addopts marker filter (-m 'not paid') must be preserved; tests/live/** and paid tests remain excluded exactly as today.
- [hard] Fixture migration scope: introduce a new worker-aware database fixture that wraps/replaces the existing db fixture and migrate all tests to it in one change for consistency, without editing protected files (they must continue to work via conftest-level fixture names they already consume).
- [soft] Conservative risk posture: prioritize test stability and zero regressions over maximum speed; worst-acceptable timings are still hard evidence requirements but the stability checkpoint comes before tuning.
- [soft] Optimization priority when trade-offs arise: 1) commit-hook speed, 2) full local suite speed, 3) CI pipeline speed.
- [hard] Every commit follows Conventional Commits; work happens on a feature branch off develop and squashes into develop via PR; never on main.
- [hard] New dev dependencies (pytest-xdist) go in the dev dependency group in pyproject.toml with uv.lock regenerated; pip-audit must stay green.
- [soft] Regression prevention: document the per-worker database convention and the -n auto expectation for new tests in the testing skill/contributing docs, and update the Claude, Cursor, Codex, and Antigravity agent-surface trees in the same PR if the testing procedure changes.

## Non-goals

- Front 2 of the runbook (effort right-sizing audit, cost-aware rotation, cost_usd_cycle, or any runtime/engine-spend work).
- Front 1 item 5 (uv/hypothesis CI caching, fail-fast lint stage) and item 6 (suite-duration perf regression guard or PR warning labels).
- Renaming, reordering, or consolidating CI gate names or jobs beyond what is strictly needed to run the suite once.
- Editing any protected test file, adding skip/xfail markers, deselecting tests, or introducing flaky-test retry plugins.
- Changing production code under src/vibey/ (repositories, migrations, bootstrap) to accommodate testing.
- Switching the test database engine, mocking PostgreSQL, or introducing an in-memory queue backend for tests.
- Splitting the suite into tiers (smoke vs full) for the commit hook; the hook runs the full parallel suite once, per the user's explicit decision.
- Portable/normalized cross-machine benchmarks; CI timings are recorded for documentation only and are not authoritative.
- Reworking the `-m 'not paid'` marker policy or tests/live exclusion.
- Performance tuning of individual slow tests beyond what isolation fixes require, unless needed to reach the worst-acceptable wall-time floor.

## Walking skeleton

Step 0 — Baseline: on develop, record this machine's numbers before touching anything: `time uv run pytest -q -p no:cacheprovider` (expect ~6m20s), a timed `git commit` with a trivial staged change (expect ~13m), and the collected/passed/skipped/deselected counts. Commit these into the evidence file first so 'before' is real, not quoted.

Step 1 — Template database pattern, sequential: in tests/conftest.py add a session-scoped fixture chain: (a) resolve a base DSN from the existing env/config the db fixture already uses; (b) ensure `vibey_test_template` exists and is migrated, guarded by a pg_advisory_lock so only one process builds it; (c) derive worker id from PYTEST_XDIST_WORKER (default 'main' when absent), `DROP DATABASE IF EXISTS vibey_test_<wid>` then `CREATE DATABASE vibey_test_<wid> TEMPLATE vibey_test_template`; (d) point the existing db/connection fixtures at that per-worker DSN so protected tests keep consuming the same fixture names; (e) drop the worker DB at session end. Run the full suite sequentially; it must be green with unchanged counts (AC-01, AC-02, AC-13). This is the core risk and is validated alone.

Step 2 — Add pytest-xdist: add `pytest-xdist` to dev deps, `uv lock`, run `uv run pytest -q -p no:cacheprovider -n auto --maxprocesses=8`. Fix any isolation failures by improving fixtures (unique temp dirs, per-worker ports/names, no module-level shared state), never by skipping. Repeat 3x for determinism (AC-03, AC-04, AC-05, NFR-04/05/06). Record wall time; if under 120 s proceed, else profile with `--durations=25` and fix the largest offenders via isolation, not deselection. Then bake `-n auto` (capped at 8) into pyproject addopts alongside the preserved `-m 'not paid'`, only if plain `pytest path::test` still works for single-file runs.

Step 3 — Unified coverage: configure `[tool.coverage.run] parallel = true` (and `source`), run once with `--cov=vibey --cov-branch -n auto`, confirm fragments combine into one .coverage, then run `coverage report --include='src/vibey/domain/*' --fail-under=100` and the three siblings. Prove per-layer granularity with a throwaway uncovered branch (AC-06/07/08). Update ci.yml: one new step runs the suite with coverage; the four existing 'Gate 4x' steps keep their exact names but run the per-layer `coverage report` commands (AC-09). Update the CLAUDE.md 'Commands worth memorizing' block and the testing/quality-gates skills across all four agent-surface trees to the new one-run-four-reports form.

Step 4 — Hook diet: restructure .pre-commit-config.yaml so the pre-commit stage runs ruff check/format on changed files plus one `uv run pytest -q -p no:cacheprovider -n auto` invocation; move mypy --strict, lint-imports, bandit, pip-audit, and the four coverage reports to a pre-push stage (and they remain in CI). Keep conventional-pre-commit on commit-msg. Measure 3 commits (AC-11, AC-12, NFR-02).

Step 5 — Evidence and PR: finalize the before/after evidence file with every command and output, open the PR against develop, confirm all CI gates green and record CI duration (AC-10, AC-15). Merge order of risk: Step 1 alone must be green before Step 2 begins; Step 2 must be deterministic before Step 3; Step 4 is last because it depends on the suite being fast enough to sit in the hook.
