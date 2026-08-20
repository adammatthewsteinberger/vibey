# Acceptance criteria

## AC-01

Given a clean checkout on the feature branch with a reachable PostgreSQL server and no pre-existing vibey_test_template or vibey_test_gw* databases

When the full suite is run sequentially (no -n flag) via `uv run pytest -q -p no:cacheprovider`

Then the session creates vibey_test_template by applying migrations once, clones it into a single worker database, every test passes, and the worker database is dropped at session end while the template persists for reuse

Fit criterion: pass/fail: exit code 0, `psql -lqt` shows vibey_test_template present and no vibey_test_gw* database present after the run

## AC-02

Given the template database already exists from a prior session

When the suite is run again

Then the template is reused without re-migrating unless the migration set has changed (or it is rebuilt cheaply and idempotently), and session startup overhead is bounded

Fit criterion: pass/fail: second-run session setup (time to first test) is under 5 seconds; re-running twice back-to-back yields identical pass counts

## AC-03

Given pytest-xdist is installed and the template fixture is in place

When the full suite is run with `uv run pytest -q -p no:cacheprovider -n auto`

Then each xdist worker gets its own cloned database named vibey_test_<worker_id>, no two workers share a database, and all tests pass

Fit criterion: pass/fail: exit code 0; during the run `psql -lqt` shows one vibey_test_gwN database per active worker; post-run none remain

## AC-04

Given the full suite runs under -n auto

When it is executed 3 consecutive times

Then every run passes with identical collected, passed, skipped, and deselected counts, demonstrating no order- or timing-dependent failures

Fit criterion: pass/fail: 3/3 green runs with byte-identical `pytest -q` summary lines for counts

## AC-05

Given the suite's baseline collected/skipped/deselected counts on develop before this change are recorded

When the suite runs under -n auto after this change

Then the collected count is equal or greater, and the skipped and deselected counts are exactly equal to baseline (no test was skipped, xfailed, or deselected to achieve parallelism)

Fit criterion: pass/fail: before/after counts committed in the evidence file match on skipped and deselected; `git grep -n 'skip\|xfail' tests/` shows no new occurrences vs develop

## AC-06

Given the suite is run once with `--cov=vibey --cov-branch -n auto` producing a single combined .coverage file

When `coverage report --include='src/vibey/domain/*' --fail-under=100` (and likewise for application, infrastructure, cli) is executed against that file

Then each of the four invocations reports exactly 100% branch coverage and exits 0, without re-running the suite

Fit criterion: pass/fail: four exit-0 reports from one .coverage file; each report's TOTAL line shows 100%

## AC-07

Given the xdist workers each write a .coverage.<host>.<pid> fragment

When the run completes

Then fragments are combined into one .coverage (via pytest-cov's built-in combine or an explicit `coverage combine` step) before any per-layer report is evaluated, and stale fragments from a prior run cannot contaminate the result

Fit criterion: pass/fail: post-run only one .coverage file exists; deleting all .coverage* and re-running produces the same four 100% results

## AC-08

Given a line of source in any layer is deliberately left uncovered in a scratch branch (e.g. a temporary unreachable branch)

When the unified coverage gates run

Then only that layer's gate fails and the others pass, proving per-layer granularity survives the single-run merge

Fit criterion: pass/fail: demonstrated once during development and noted in the evidence file; the scratch change is not committed

## AC-09

Given .github/workflows/ci.yml is updated

When the workflow is diffed against develop

Then every pre-existing job and step `name:` value still exists verbatim; the Gate 4a–4d steps now execute per-layer `coverage report` commands against the shared .coverage produced by a single preceding `pytest -n auto --cov=vibey --cov-branch` step

Fit criterion: pass/fail: `grep -c 'name:' ci.yml` retains all original names; a script comparing the set of `name:` values before/after reports no removals

## AC-10

Given the feature branch is pushed and a PR is opened against develop

When GitHub Actions runs

Then all gates (uv.lock sync, Gates 1–7 including 4a–4d) are green and CI reports its suite wall time, which is recorded in the evidence file as documentation (not authoritative)

Fit criterion: pass/fail: PR checks all green; CI duration captured

## AC-11

Given .pre-commit-config.yaml after the hook diet

When `git commit` is run with a staged change to a Python file

Then the pre-commit stage runs ruff check and ruff format on changed files only, runs the full parallel suite exactly once, and the commit-msg stage still enforces Conventional Commits; no hook invokes pytest a second time

Fit criterion: pass/fail: `pre-commit run --all-files --verbose` log shows exactly one pytest invocation; conventional-pre-commit still rejects a non-conforming message

## AC-12

Given the full sweep (mypy --strict, lint-imports, bandit, pip-audit, four coverage floors) is removed from the commit stage

When a developer runs `git push` or CI runs

Then the full 7-gate sweep is still executed at the pre-push stage and/or CI, so no gate is lost, only relocated

Fit criterion: pass/fail: pre-push hook config or CI contains every gate; documented mapping of gate → stage in the PR description

## AC-13

Given the protected test files list

When `git diff develop...HEAD --stat -- tests/system/test_delivery_stage_set.py 'tests/domain/test_noloss*.py' tests/domain/test_briefing.py tests/infrastructure/db/test_chaos.py tests/live/` is run

Then the output is empty

Fit criterion: pass/fail: empty diff

## AC-14

Given a worker process is killed mid-run (simulating a crash) leaving vibey_test_gw3 behind

When the suite is run again

Then session setup drops and recreates any pre-existing worker database rather than failing with 'database already exists'

Fit criterion: pass/fail: manually verified once; documented in evidence

## AC-15

Given the change is complete

When the evidence file (e.g. docs/runbooks/expansion/evidence/13-front1-before-after.md or a section appended to the runbook) is reviewed

Then it contains machine description, before timings (full suite ~6m20s, hook ~13m as baseline, re-measured on this machine at start of work), after timings for full suite and commit hook, the 3x consistency runs, the four per-layer coverage report outputs, collected/skipped/deselected counts before and after, and the CI duration

Fit criterion: pass/fail: every listed datum present with the exact command used to produce it
