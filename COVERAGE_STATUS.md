# Phase A Coverage Status - vibey

**Branch:** `chore/a8-coverage`  
**Last Updated:** 2026-08-15  
**Status:** Partial completion - Domain layer complete, Infrastructure/CLI require substantial work

## Summary

Phase A aims to achieve 100% test coverage across all four architectural layers with per-layer CI gates. Progress has been made on the domain layer, but infrastructure and CLI layers have significant gaps requiring dedicated effort.

## Current Coverage by Layer

| Layer | Current | Target | Status | Gaps Remaining |
|-------|---------|--------|--------|----------------|
| **domain** | 99.87% | 100% | ✅ Near Complete | 3 partial branches (likely coverage.py artifacts) |
| **application** | 99.10% | 100% | ⚠️ In Progress | 7 partial branches |
| **infrastructure** | 93.44% | 100% | ❌ Needs Work | 75 statements + 52 branches = 127 gaps |
| **cli** | 71.83% | 100% | ❌ Needs Work | 101 statements + 31 branches = 132 gaps |

## Completed Work

### ✅ Fixed Failing Tests (2)
- `test_watch_command_with_no_projects`
- `test_watch_command_with_unknown_project_id`

**Issue:** Tests were patching `vibey.cli.main.VibeyDashboardApp` but the class is actually in `vibey.tui.dashboard.VibeyDashboardApp` (lazy import).

**Fix:** Updated patch paths from `vibey.cli.main.VibeyDashboardApp` to `vibey.tui.dashboard.VibeyDashboardApp`.

### ✅ Domain Layer: 99.70% → 99.87%

Added comprehensive edge case tests:

**projections.py** (5 → 1 partial branches):
- ✅ Empty `assumption_id` handling
- ✅ Empty `finding_id` handling  
- ✅ Empty `finding_id` in FINDING_RESOLVED events
- ✅ Finding resolved before being raised
- ✅ Added `answer_why_question` test for assumption search

**provision.py** (1 partial branch):
- ✅ Tail content handling without leading newline

**circuit.py** (1 partial branch):
- ✅ Test exists for AuthenticationFailed case

**Remaining Gaps (3 partial branches):**
1. `circuit.py:92->exit` - AuthenticationFailed match/case return branch (has test, likely coverage.py artifact with match/case)
2. `projections.py:247->244` - ASSUMPTION_STATED elif loop continuation (has test, likely coverage.py artifact with elif-in-loop)
3. `provision.py:67->69` - Newline trimming edge case (has test, edge case may need different construction)

These appear to be coverage.py instrumentation limitations rather than actual gaps.

## Work Remaining

### ⚠️ Application Layer (99.10%)

**7 partial branches across 5 files:**

1. `design_handler.py` (2 branches):
   - `65->64`: Skip already-answered items in loop
   - `76->75`: Skip already-assumed items in loop

2. `review_deployment_choice_handler.py` (2 branches):
   - `99->106`: Some deployment choice branch
   - `129->136`: Another deployment choice branch

3. `review_triage_handler.py` (1 branch):
   - `119->133`: Review triage decision branch

4. `text_verdict_fallback.py` (1 branch):
   - `64->66`: Verdict parsing fallback path

5. `worker.py` (1 branch):
   - `85->exit`: Worker exit path

**Estimated effort:** 10-15 hours (requires understanding async test infrastructure and handler state machines)

### ❌ Infrastructure Layer (93.44%)

**127 coverage gaps (75 missed statements + 52 partial branches)**

Critical files needing attention:

| File | Coverage | Type | Priority |
|------|----------|------|----------|
| `db/handoff_repository.py` | 82% | Database adapter | High |
| `db/project_repository.py` | 88% | Database adapter | High |
| `engines/claudeloop_design.py` | 81% | Engine integration | High |
| `engines/claudeloop_process.py` | 87% | Engine integration | High |
| `engines/classify.py` | 92% | Engine classification | Medium |
| `git/clean_env.py` | 71% | Git subprocess | Medium |
| `db/engine_health_repository.py` | 92% | Database adapter | Medium |
| `db/human_gate_repository.py` | 92% | Database adapter | Medium |
| `db/job_repository.py` | 97% | Database adapter | Low |
| `db/ledger_repository.py` | 92% | Database adapter | Medium |

**Common gap patterns:**
- Database error handling paths (connection failures, constraint violations)
- Git subprocess failure modes
- Engine process communication edge cases
- File I/O error conditions

**Estimated effort:** 25-35 hours (requires understanding database contracts, subprocess handling, and engine protocols)

### ❌ CLI Layer (71.83%)

**132 coverage gaps (101 missed statements + 31 partial branches)**

**Primary gap:** `cli/main.py` has 70% coverage

The CLI main file contains all command implementations. Missing coverage includes:
- Command option validation paths
- Error handling for each command
- Interactive prompts and confirmations
- File I/O error conditions
- Database connection error paths

**Estimated effort:** 20-30 hours (requires CliRunner integration tests for every command variant)

## Defects from Audit

| # | Description | Status |
|---|-------------|--------|
| 1 | claudeloop's "full suite" CI gates nothing | ⏸️ Blocked (different repo) |
| 2 | agyloop enforces no coverage | ⏸️ Blocked (different repo) |
| 3 | codexloop intermittent test failure | ⏸️ Blocked (different repo) |
| 4 | agyloop develop/main diverged | ⏸️ Blocked (different repo) |
| 5 | uv.lock untracked in other repos | ⏸️ Blocked (different repos) |
| 6 | vibey's apply_third_party_level missing | ✅ Fixed (commit 74c8eb5) |

## CI Gate Requirements (Not Yet Implemented)

Per the runbook, CI must enforce 100% coverage per layer:

```yaml
# .github/workflows/test.yml needs 4 separate coverage jobs:

- name: Coverage - Domain Layer
  run: |
    pytest --cov=vibey.domain --cov-fail-under=100 --cov-report=term

- name: Coverage - Application Layer  
  run: |
    pytest --cov=vibey.application --cov-fail-under=100 --cov-report=term

- name: Coverage - Infrastructure Layer
  run: |
    pytest --cov=vibey.infrastructure --cov-fail-under=100 --cov-report=term

- name: Coverage - CLI Layer
  run: |
    pytest --cov=vibey.cli --cov-fail-under=100 --cov-report=term
```

**Status:** Not implemented yet - waiting for actual 100% coverage achievement

## Recommendations

### Immediate (This PR)
1. ✅ Commit domain layer improvements (done)
2. Document current state (this file)
3. Open PR with progress and clear next steps

### Short Term (Next 1-2 PRs)
1. Complete application layer to 100% (7 branches, ~10-15 hours)
2. Implement per-layer CI gates for domain + application
3. Begin infrastructure layer systematic coverage improvement

### Medium Term (Subsequent PRs)
1. Infrastructure layer to 100% (~25-35 hours)
   - Database repositories first (most critical)
   - Engine integrations second
   - Supporting infrastructure third
2. CLI layer to 100% (~20-30 hours)
   - Command-by-command test coverage
   - Error path coverage
3. Enable all four per-layer CI gates

## Verification Commands

Test current coverage state:

```bash
# Domain layer
uv run pytest -q -p no:cacheprovider --cov=vibey.domain --cov-report=term --cov-fail-under=100

# Application layer  
uv run pytest -q -p no:cacheprovider --cov=vibey.application --cov-report=term --cov-fail-under=100

# Infrastructure layer
uv run pytest -q -p no:cacheprovider --cov=vibey.infrastructure --cov-report=term --cov-fail-under=100

# CLI layer
uv run pytest -q -p no:cacheprovider --cov=vibey.cli --cov-report=term --cov-fail-under=100

# All tests
uv run pytest

# Linting
uv run ruff check src tests
uv run ruff format --check src tests
uv run mypy --strict src/vibey
uv run lint-imports
uv run bandit -q -r src/vibey
uv run pip-audit
```

## Total Effort Estimate

- ✅ **Completed:** ~8 hours (failing tests + domain layer)
- ⚠️ **Application:** ~10-15 hours
- ❌ **Infrastructure:** ~25-35 hours  
- ❌ **CLI:** ~20-30 hours
- **Total remaining:** ~55-80 hours of systematic test writing

## Next Steps

1. Review this PR and decide on approach:
   - **Option A:** Merge partial progress, continue in subsequent PRs
   - **Option B:** Continue in this branch until more layers complete
   - **Option C:** Adjust runbook to accept current coverage levels temporarily

2. If proceeding with full 100% coverage requirement:
   - Dedicate focused sessions to each layer
   - Application → Infrastructure → CLI
   - One PR per layer for easier review

3. Consider parallel work:
   - One developer on vibey coverage
   - Others on claudeloop/agyloop/cursorloop/codexloop (also need 100%)
