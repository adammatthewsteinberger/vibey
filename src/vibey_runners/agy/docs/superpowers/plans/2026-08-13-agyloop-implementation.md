# agyloop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `agyloop`, an onion-architected autonomous Antigravity/Gemini runner that never blocks on a human and distinguishes waitable RPM/TPM/RPD windows from non-waitable spend/billing exhaustion.

**Architecture:** Full fork of claudeloop 0.5.4; `infrastructure/agent` uses `google.antigravity.Agent` + `LocalAgentConfig(policies=[allow_all])`; structured completion via SDK; state under `.agyloop/`.

**Tech Stack:** Python 3.12+, `google-antigravity`, Typer, anyio, structlog, textual, pytest, Hypothesis, ruff, mypy strict, import-linter, bandit, pip-audit.

## Global Constraints

- Never block on a human.
- Credits/billing ≠ rate-limit window.
- Capacity rejection outranks completion.
- `domain/` stdlib only.
- Conventional Commits + claudeloop quality gates.
- Prefer SDK policies over `agy --dangerously-skip-permissions` + sandbox combos.
- No `anthropic` / `claude_agent_sdk`.
- Naming: `agyloop`, `AGYLOOP_*`, `.agyloop/`, `AGYLOOP_TASK_FULLY_COMPLETE`.

---

## File map (create)

```
pyproject.toml
src/agyloop/__init__.py
src/agyloop/bootstrap.py
src/agyloop/domain/*.py
src/agyloop/application/{ports,dto,runner}.py
src/agyloop/infrastructure/agent/{gateway,options,translate,autonomy,catalog,probe,policies}.py
src/agyloop/cli/app.py
tests/...
```

---

### Task 1: Package skeleton + CI

- [ ] **Step 1:**

```python
import agyloop


def test_version_is_string():
    assert isinstance(agyloop.__version__, str)
```

- [ ] **Step 2: FAIL**

- [ ] **Step 3: Scaffold; dep `google-antigravity`; entry `agyloop`**

- [ ] **Step 4: Pass**

- [ ] **Step 5: Commit** `chore: scaffold agyloop package skeleton`

---

### Task 2: Classify Gemini RESOURCE_EXHAUSTED variants

**Files:** `domain/capacity.py`, `classify.py`, `waiting.py` helper for next midnight PT

- [ ] **Step 1: Failing tests**

```python
from agyloop.domain.classify import TurnSignals, classify
from agyloop.domain.capacity import WindowExhausted, CreditsExhausted, AuthenticationFailed
from agyloop.domain.waiting import next_pacific_midnight


def test_rpm_resource_exhausted_is_window():
    state = classify(
        TurnSignals(
            http_status=429,
            status="RESOURCE_EXHAUSTED",
            message="Resource exhausted: RPM",
            quota_metric="rpm",
        )
    )
    assert isinstance(state, WindowExhausted)
    assert state.rate_limit_type == "rpm"


def test_spend_limit_is_credits():
    state = classify(
        TurnSignals(
            http_status=429,
            status="RESOURCE_EXHAUSTED",
            message="spend-based rate limit",
        )
    )
    assert isinstance(state, CreditsExhausted)


def test_rpd_uses_pacific_midnight(fake_now):
    state = classify(
        TurnSignals(
            http_status=429,
            status="RESOURCE_EXHAUSTED",
            message="requests per day",
            quota_metric="rpd",
        )
    )
    assert isinstance(state, WindowExhausted)
    assert state.rate_limit_type == "rpd"
```

- [ ] **Step 2: FAIL**

- [ ] **Step 3: Implement classifier + `next_pacific_midnight(now) -> datetime` pure helper**

- [ ] **Step 4: Pass**

- [ ] **Step 5: Commit** `feat: classify gemini resource exhausted variants`

---

### Task 3: Port domain loop/waiting/budget/completion

- [ ] **Step 1: Port tests; marker `AGYLOOP_TASK_FULLY_COMPLETE`; prefer structured verdict fields**

- [ ] **Step 2–4: Port modules**

- [ ] **Step 5: Commit** `feat: port domain run loop and waiting`

---

### Task 4: Application runner + fakes

- [ ] **Step 1: Script RPM window then Available; script CreditsExhausted probe cadence**

- [ ] **Step 2–4: Port runner/ports**

- [ ] **Step 5: Commit** `feat: port autonomous runner`

---

### Task 5: Antigravity SDK gateway (M2)

**Files:** `gateway.py`, `options.py`, `policies.py`, `translate.py`, `autonomy.py`

- [ ] **Step 1: Test options always attach allow_all (or explicit allowlist) and never ask_user blocking handler**

```python
def test_local_config_is_autonomous():
    cfg = build_local_config(cwd=".")
    assert config_has_allow_all(cfg) or config_has_nonblocking_policies(cfg)
```

- [ ] **Step 2: FAIL**

- [ ] **Step 3: Implement async gateway `Agent(config)`; map exceptions → TurnSignals; HITL hook → deny-with-guidance**

- [ ] **Step 4: Pass with mocks**

- [ ] **Step 5: Commit** `feat: add antigravity sdk agent gateway`

---

### Task 6: Structured completion path

- [ ] **Step 1: Test translate structured_output JSON → Done/Continue/Blocked**

- [ ] **Step 2–4: Wire schema in options; marker fallback**

- [ ] **Step 5: Commit** `feat: structured completion via antigravity`

---

### Task 7: Catalog, probe, doctor, CLI

- [ ] **Step 1: CliRunner help; doctor checks GOOGLE_API_KEY/ADC**

- [ ] **Step 2–4: `.agyloop/` rundir; run/resume/sessions**

- [ ] **Step 5: Commit** `feat: add run resume doctor CLI`

---

### Task 8: M3 waiting + notifier

- [ ] **Step 1: RPD wait uses next_pacific_midnight; credits uses cadence**

- [ ] **Step 2–4: Implement probe via cheap chat turn**

- [ ] **Step 5: Commit** `feat: wire adaptive waiting for gemini quotas`

---

### Task 9: M4 REST or ADR

- [ ] **Step 1: Spike GenAI/Vertex introspection**

- [ ] **Step 2: Implement api CLI + drift gate OR `docs/architecture/decisions/0006-defer-genai-rest.md`**

- [ ] **Step 3: Commit accordingly**

---

### Task 10: Security note + system harness + M5 docs

- [ ] **Step 1: SECURITY.md documents sandbox + skip-permissions footgun; refuse root**

- [ ] **Step 2: `pytest -m system` scripted**

- [ ] **Step 3: User docs**

- [ ] **Step 4: Commit** `docs: security and polish agyloop`

---

## Self-review

- [ ] RPM/TPM/RPD/spend all tested
- [ ] No anthropic deps
- [ ] Autonomy via SDK policies
- [ ] Structured completion task present
