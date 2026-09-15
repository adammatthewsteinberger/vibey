# Hybrid Live Harness + Docs Deep-Scan Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans (inline) or subagent-driven-development. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Ship a hybrid system/free/paid live harness (Approach 1 + Both injection styles) and then make FOSS docs/man/README exhaustively current.

**Architecture:** Test-only env gate in `bootstrap.build_runner` swaps Claude for a JSON-scripted agent. System tests use real FS/git/control adapters; in-process matrix is exhaustive; subprocess smoke proves CLI wiring. Docs milestone follows a green harness.

**Tech Stack:** pytest markers, Typer CLI, real infra adapters, JSON agent scripts, mkdocs, man_page.py

## Global Constraints

- Onion intact: test-agent selection only in composition root
- Default `addopts`: `-m "not live and not system"`
- Test agent requires BOTH `CLAUDELOOP_ALLOW_TEST_AGENT=1` and `CLAUDELOOP_TEST_AGENT_SCRIPT=<path>`
- No paid tokens without `--run-paid-live`
- Conventional Commits only when user asks to commit
- Fakes over mocks for ports; FakeClock/FakeSleeper for wait edges in-process

---

### Task 1: Scripted agent + bootstrap gate

**Files:**
- Create: `src/claudeloop/infrastructure/agent/scripted.py`
- Modify: `src/claudeloop/bootstrap.py`
- Create: `tests/infrastructure/test_scripted_agent.py`

**Interfaces:**
- Produces: `load_agent_script(path) -> AgentScript`, `ScriptedAgentGateway`, `ScriptedCapacityProbe`, `resolve_test_agent_from_env() -> tuple[gateway, probe] | None`
- JSON schema: `{ "probes": [TurnSignalsDict...], "turns": [TurnDict...] }` with optional ISO `resets_at`

- [ ] **Step 1:** Implement `scripted.py` + bootstrap gate; fail if script set without allow
- [ ] **Step 2:** Unit tests for load/replay/gate refuse; widen `RunnerContext.gateway` type to `AgentGateway`
- [ ] **Step 3:** `pytest tests/infrastructure/test_scripted_agent.py -v` green

### Task 2: System in-process matrix

**Files:**
- Create: `tests/live/system/conftest.py`
- Create: `tests/live/system/test_matrix_inprocess.py`
- Modify: `pyproject.toml` markers + addopts

- [ ] **Step 1:** Helper composing real RunDirectory/control/events/audit/git/bus + FakeAgent + FakeClock/Sleeper
- [ ] **Step 2:** Tests covering happy/control/edge cases from the design spec
- [ ] **Step 3:** `pytest -m system tests/live/system/test_matrix_inprocess.py -v` green

### Task 3: Subprocess smoke + fixtures

**Files:**
- Create: `tests/live/fixtures/agent_scripts/*.json`
- Create: `tests/live/system/test_subprocess_smoke.py`

- [ ] **Step 1:** Scripts: `done.json`, `wait_then_need_stop.json` (window exhausted far future)
- [ ] **Step 2:** Subprocess tests with allow+script env; stop mid-wait → 130; complete → 0; ops help
- [ ] **Step 3:** `pytest -m system tests/live/system/test_subprocess_smoke.py -v` green

### Task 4: Free + paid extensions + Milestone A docs

**Files:**
- Modify: `tests/live/test_free_tier.py`, `tests/live/test_paid_tier.py`, `tests/live/conftest.py`
- Modify: `docs/guides/live-testing.md`, `docs/contributing/testing.md`

- [ ] **Step 1:** Free: ops in help, `--max-buffer-size` on run --help
- [ ] **Step 2:** Paid: one mid-run status/logs/stop-or-prompt smoke
- [ ] **Step 3:** Document markers; `pytest` default still skips live/system

### Task 5: Milestone B — docs + man deep-scan

**Files:**
- Modify: `src/claudeloop/cli/man_page.py`, `docs/reference/cli.md`, `README.md`, guides, configuration, SECURITY.md, mkdocs.yml as needed, skills

- [ ] **Step 1:** Grep stale content; rewrite CLI reference + exhaust man page
- [ ] **Step 2:** Update all FOSS surfaces; `mkdocs build --strict`
- [ ] **Step 3:** Update `claudeloop-testing` skill for system marker

## Spec coverage

| Spec item | Task |
|---|---|
| Test-agent gate | 1 |
| In-process matrix | 2 |
| Subprocess smoke | 3 |
| Free/paid + A docs | 4 |
| Docs deep-scan B | 5 |
