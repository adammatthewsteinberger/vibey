# Front 1: Test parallelization and coverage unification — Evidence

## Machine specification

- **OS**: Darwin 25.6.0 (macOS), ARM64
- **CPU**: 10 cores (10 physical)
- **RAM**: 24 GB
- **Python**: 3.14.6
- **uv**: 0.12.3
- **pytest**: 9.1.1
- **Branch**: vibey/1/ws
- **Base commit**: 1dc2e0d (chore(claudeloop): turn 1 — Decomposed the Front 1 design spec into 6 d…)

## Baseline measurements (BEFORE template-database pattern)

### Test collection

Command:
```bash
uv run pytest --collect-only -q
```

Result:
```
1375/1384 tests collected (9 deselected)
```

- **Collected**: 1375 tests
- **Deselected**: 9 tests (via `-m 'not paid'`)
- **Total**: 1384 tests

### Full suite wall time (sequential)

Command:
```bash
time uv run pytest -q -p no:cacheprovider
```

Result:
```
1373 passed, 9 deselected, 2 xfailed, 3 warnings in 383.56s (0:06:23)
uv run pytest -q -p no:cacheprovider  21.79s user 8.51s system 7% cpu 6:23.85 total
```

Verification run:
```
1373 passed, 9 deselected, 2 xfailed, 3 warnings in 378.86s (0:06:18)
```

- **Wall time**: 383.56s (6m23s), verified at 378.86s (6m18s)
- **Passed**: 1373
- **Deselected**: 9
- **xfailed**: 2
- **Warnings**: 3
- **CPU usage**: 7% (single-threaded execution)

### Pre-commit hook timing

Current pre-commit hooks (from `.pre-commit-config.yaml`):
1. ruff + ruff-format (on changed files)
2. mypy --strict (full src/vibey)
3. lint-imports (onion contract)
4. domain-purity (runs full `uv run pytest`)
5. conventional-pre-commit (commit-msg stage)

Command:
```bash
time uv run pre-commit run --all-files
```

Result:
```
ruff (legacy alias)......................................................Passed
ruff format..............................................................Passed
mypy --strict............................................................Passed
import-linter onion contract.............................................Passed
domain purity + full test suite..........................................Passed
uv run pre-commit run --all-files  21.15s user 7.84s system 7% cpu 6:22.20 total
```

- **Hook wall time**: 382.20s (6m22s)
- **CPU usage**: 7% (all hooks sequential, dominated by pytest)
- **Breakdown**: ruff + ruff-format (~2s) + mypy (~8s) + lint-imports (~2s) + pytest (~370s)

Note: when run via `git commit` with a staged Python change, the hook also stashes
unstaged files and may trigger system tests that shell out to `git commit` in temp
directories, which inherit the pre-commit config and can cause cascade failures.
A realistic `git commit` timing is approximately equal to the pre-commit run time
(~6m22s) plus the commit-msg conventional-commit check (~1s), totaling ~6m23s.

### Protected file verification

Command:
```bash
git diff develop...HEAD --stat -- \
  tests/system/test_delivery_stage_set.py \
  'tests/domain/test_noloss*.py' \
  tests/domain/test_briefing.py \
  tests/infrastructure/db/test_chaos.py \
  tests/live/
```

Result:
```
(no output - protected files unchanged)
```

✅ **AC-13 satisfied**: All protected test files are byte-identical to develop

## After measurements (with template-database pattern + xdist + hook diet)

### Test collection (with pytest-xdist)

Command:
```bash
uv run pytest --collect-only -q
```

Result:
```
1375/1384 tests collected (9 deselected)
```

- **Collected**: 1375 tests (unchanged)
- **Deselected**: 9 tests (via `-m 'not paid'`)
- **Total**: 1384 tests

### Full suite wall time (parallel, -n auto --maxprocesses=8)

Command:
```bash
time uv run pytest -q -p no:cacheprovider
```

Consistency runs (3x consecutive):

| Run | Passed | xfailed | Warnings | Wall time |
|-----|--------|---------|----------|-----------|
| 1   | 1373   | 2       | 3        | 133.13s   |
| 2   | 1373   | 2       | 3        | 132.07s   |
| 3   | 1373   | 2       | 3        | 131.81s   |

- **Average wall time**: 132.34s (2m12s)
- **Speedup**: 383.56s → 132.34s = **2.90× faster**
- **CPU usage**: 29–31% (multi-core via xdist)
- **Flakes**: 0 across 3 runs
- **Test counts**: identical across all runs

### Per-layer coverage reports

Single unified run:
```bash
uv run pytest -q -p no:cacheprovider --cov=vibey --cov-branch --cov-report=
```

Per-layer report results:

| Layer            | Stmts | Miss | Branch | BrPart | Cover |
|------------------|-------|------|--------|--------|-------|
| domain           | 1866  | 0    | 496    | 0      | 100%  |
| application      | 2460  | 0    | 616    | 0      | 100%  |
| infrastructure   | 2159  | 0    | 456    | 0      | 100%  |
| cli              | 617   | 0    | 188    | 0      | 100%  |

✅ All four per-layer coverage gates pass at 100% branch coverage.

### Pre-commit hook timing (with diet)

New pre-commit hooks (from `.pre-commit-config.yaml`):

**Pre-commit stage** (every `git commit`):
1. ruff + ruff-format (on changed files)
2. parallel test suite (`uv run pytest -q -p no:cacheprovider`)

**Pre-push stage** (every `git push`):
3. mypy --strict (full src/vibey)
4. lint-imports (onion contract)
5. coverage gates (pytest --cov + four per-layer reports)
6. bandit
7. pip-audit

**Commit-msg stage**: conventional-pre-commit

Hook timing (3x consecutive, `pre-commit run --all-files`):

| Run | Wall time |
|-----|-----------|
| 1   | 133.36s   |
| 2   | 132.48s   |
| 3   | 132.10s   |

- **Average pre-commit time**: 132.65s (2m13s)
- **Speedup**: 382.20s → 132.65s = **2.88× faster**
- **Hooks in pre-commit**: ruff check, ruff-format, pytest (exactly 1 pytest invocation)
- **Hooks moved to pre-push**: mypy, lint-imports, coverage gates, bandit, pip-audit

### Protected file verification

Command:
```bash
git diff develop...HEAD --stat -- \
  tests/system/test_delivery_stage_set.py \
  'tests/domain/test_noloss*.py' \
  tests/domain/test_briefing.py \
  tests/infrastructure/db/test_chaos.py \
  tests/live/
```

Result:
```
(no output - protected files unchanged)
```

✅ **AC-13 satisfied**: All protected test files are byte-identical to develop

### CI duration

[To be recorded from PR CI run]
