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

## After measurements (with template-database pattern)

[To be filled in after implementation]

### Test collection (with pytest-xdist)

[PENDING]

### Full suite wall time (parallel, -n auto)

[PENDING - target: ≤120s worst acceptable, ≤90s target, ≤60s ideal]

### Consistency runs (3x consecutive)

[PENDING - must show 0 flakes, identical counts]

### Per-layer coverage reports

[PENDING - single run, four reports]

### Pre-commit hook timing (with diet)

[PENDING - target: ≤180s worst acceptable, ≤120s target]

### CI duration

[PENDING - to be recorded from PR]
