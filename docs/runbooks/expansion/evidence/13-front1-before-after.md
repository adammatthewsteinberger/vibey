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

Started: Thu Aug 20 16:54:00 EDT 2026 (approx)
Expected duration: ~6m20s (~380s)

Status: Running in background (task ID: bsap0y8u2)

Result: [PENDING - test run in progress, will update upon completion]

### Pre-commit hook timing

Current pre-commit hooks (from `.pre-commit-config.yaml`):
1. ruff + ruff-format (on changed files)
2. mypy --strict (full src/vibey)
3. lint-imports (onion contract)
4. domain-purity (runs full `uv run pytest`)
5. conventional-pre-commit (commit-msg stage)

Command:
```bash
# Create trivial change and time commit
echo "# test" >> /tmp/test_commit.py
git add /tmp/test_commit.py
time git commit -m "test: timing baseline"
git reset HEAD~1
```

Expected duration: ~13 minutes (per spec, includes full test suite run)

Result: [PENDING - will measure after test suite completes to avoid parallel runs]

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
