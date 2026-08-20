# Non-functional requirements

## NFR-01: Full local suite wall time

Scale: Seconds of wall-clock time for `uv run pytest -q -p no:cacheprovider -n auto` on the developer's machine (the one used to record the ~6m20s baseline), including session setup and teardown, measured with `time`

Meter: Median of 3 consecutive runs after a warm template database, recorded in the evidence file

Must: <= 120 s (worst acceptable)

Wish: <= 90 s (target); <= 60 s (ideal)

Fit criterion: Median of 3 runs at or under 120 s is required to merge; at or under 90 s satisfies the runbook target and is the goal

## NFR-02: Pre-commit hook total time

Scale: Seconds of wall-clock time from `git commit` invocation to commit creation with a single staged Python change, including changed-file lints and the single parallel suite run

Meter: Median of 3 measured commits on the developer's machine, recorded in the evidence file

Must: <= 180 s (worst acceptable)

Wish: <= 120 s (target); <= 90 s (ideal)

Fit criterion: Median at or under 180 s is required; at or under 120 s satisfies the runbook target; 2–3 minutes is explicitly acceptable if it keeps the full suite in the hook

## NFR-03: Coverage gate cost

Scale: Number of full test-suite executions required to evaluate all four per-layer 100% branch floors

Meter: Count of pytest invocations in CI workflow and in local gate instructions

Must: Exactly 1 suite execution feeds all four floors

Wish: Same (1)

Fit criterion: CI log and local commands show a single pytest run followed by four `coverage report` calls

## NFR-04: Determinism under parallelism

Scale: Number of test-outcome differences across N consecutive full -n auto runs

Meter: Compare pass/fail/skip/deselect counts and failing-test IDs across 3 consecutive runs locally plus the CI run

Must: 0 differences across 3 local runs and CI

Wish: 0 differences across 10 runs

Fit criterion: Zero flakes observed; any observed flake blocks merge until fixed via isolation

## NFR-05: Database isolation

Scale: Number of test databases shared by more than one concurrent xdist worker

Meter: Inspect `pg_stat_activity` / database names during a -n auto run

Must: 0 shared databases; one vibey_test_<worker_id> per worker

Wish: Same

Fit criterion: No DROP SCHEMA deadlock or 'database is being accessed by other users' errors in any run

## NFR-06: Connection footprint

Scale: Peak PostgreSQL connections opened by the test run

Meter: `SELECT count(*) FROM pg_stat_activity WHERE datname LIKE 'vibey_test%'` sampled during the run

Must: Peak stays below the server's max_connections minus 10 with 8 workers on default Postgres settings (100)

Wish: <= 4 connections per worker

Fit criterion: No 'too many clients' errors across 3 runs at the 8-worker cap

## NFR-07: Session startup overhead

Scale: Seconds from pytest start to first test execution with a warm template

Meter: pytest `--durations` / timestamps in evidence

Must: <= 10 s

Wish: <= 3 s

Fit criterion: Template clone per worker completes in well under a second; migrations are not re-applied on warm runs

## NFR-08: Gate preservation

Scale: Number of quality gates relaxed, removed, or renamed

Meter: Diff review of pyproject.toml, .pre-commit-config.yaml, ci.yml against develop

Must: 0 relaxed/removed/renamed

Wish: Same

Fit criterion: All four floors still `--fail-under=100` with branch coverage; mypy --strict, lint-imports, bandit, pip-audit unchanged; CI step names unchanged

## NFR-09: Clean-up hygiene

Scale: Number of leftover vibey_test_gw* databases and .coverage.* fragments after a normal run

Meter: `psql -lqt` and `ls -a .coverage*` after the run

Must: 0 worker databases, exactly one .coverage file

Wish: Same

Fit criterion: Verified after each of the 3 consistency runs
