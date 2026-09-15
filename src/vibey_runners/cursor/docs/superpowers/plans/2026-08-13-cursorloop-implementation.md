# cursorloop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (or superpowers:executing-plans when working inline). Steps use checkbox (`- [ ]`) syntax for tracking. Every task is TDD: write the failing test first, then the implementation, then run the gate. Do not batch tasks — one task, one green suite, one Conventional Commit.

**Goal:** Ship `cursorloop` — an onion-architected, autonomous Cursor Agent session runner that never blocks on a human and distinguishes a waitable rate-limit window from non-waitable exhausted credits/billing. Composer-first (`composer-2.5`); Grok is a secondary **model profile**, not a separate product. Milestones M1–M3 (pure domain → agent gateway → classification → resilient waiting → `run` CLI) are specified task-by-task below; M4 (Cloud Agents REST surface) and M5 (polish, CLI-fallback adapter, docs) are sketched as later tasks with the same structure.

**Architecture:** Strict onion — `domain → application → infrastructure → cli`, with `bootstrap.py` as the sole composition root, enforced by `import-linter` in CI and pre-commit. `domain/` is pure stdlib: every hard decision (is this limit waitable? how long do we wait? is the work done?) is a pure function over frozen dataclasses. `infrastructure/agent/` is the only place `cursor_sdk` is imported. The runner drives a pure state machine (`domain/loop.py`) over `typing.Protocol` ports (`application/ports.py`). Blueprint: `claudeloop` 0.5.4. Design record: [`../../plans/architecture-and-roadmap.md`](../../plans/architecture-and-roadmap.md). Evidence base: [`../../plans/research-notes.md`](../../plans/research-notes.md).

**Tech Stack:** Python 3.12+, `cursor-sdk`, `typer`, `anyio`, `structlog`, `textual`, `pytest` (+ `pytest-cov`, `pytest-asyncio`, `hypothesis`), `ruff`, `mypy --strict`, `import-linter`, `bandit`, `pip-audit`, `hatchling`, `mkdocs-material`.

## Global Constraints

**The non-negotiables — identical wording across `CURSOR.md`, `AGENTS.md`, and every mirrored skill/rule tree:**

- **Never block on a human.** Every code path must have a way forward that doesn't wait on stdin or a tool call requiring a real person.
- **Credits/billing ≠ rate-limit window.** `CreditsExhausted` has no reset time and can never be treated as waitable-with-a-deadline. Conflating the two reintroduces the exact bug this project replaces.
- **A capacity rejection always outranks a completion claim.**
- **`domain/` stays pure.** Stdlib only, no I/O, no async, no third-party imports — enforced by `import-linter`, not convention.
- **Every commit message follows Conventional Commits**, and the full quality-gate set runs green before any PR.

**Fork-specific:**

- **No Anthropic dependency, ever.** `anthropic` / `claude_agent_sdk` are not dependencies, not extras, not test imports. No `ANTHROPIC_*` env var is read, written, or accepted as a fallback anywhere in `src/`. Enforced by a dedicated `import-linter` forbidden contract.
- **Grok is a model profile, not a product.** One agent adapter, one taxonomy, one CLI. Default model `composer-2.5`.
- **Bias every ambiguous capacity signal toward `CreditsExhausted`.** Misclassifying a window as credits costs a conservative probe cadence; misclassifying credits as a window re-creates the founding bug.

**Naming (fixed, no exceptions):**

| Thing | Value |
|---|---|
| PyPI + import package + console script | `cursorloop` |
| Env prefix | `CURSORLOOP_*` |
| Vendor auth env | `CURSOR_API_KEY` (never `ANTHROPIC_*`) |
| Run state directory | `.cursorloop/` |
| Done marker | `CURSORLOOP_TASK_FULLY_COMPLETE` |
| Verdict fence | ` ```cursorloop-verdict ` |
| Test-agent gate | `CURSORLOOP_ALLOW_TEST_AGENT=1` **and** `CURSORLOOP_TEST_AGENT_SCRIPT=<path>` |
| Default model | `composer-2.5` |

**Quality gates, in CI order — run the full set before opening any PR:**

```bash
ruff check src tests
ruff format --check src tests
mypy src/cursorloop
pytest
lint-imports
bandit -q -r src/cursorloop
pip-audit
```

**Coverage floors:** `domain` 100%, `application` 100%, `infrastructure` 85% (ratcheting), `cli` 85%. Scope and floor are passed **explicitly at each call site**, never in `addopts` — `pytest-cov` unions every `--cov=X` it sees, so a blanket `--cov=cursorloop` in `addopts` would silently widen CI's per-layer gate.

**Testing discipline:** fakes over mocks for every port; `FakeClock`/`FakeSleeper` so a simulated seven-day wait runs in microseconds with zero real sleeping; Hypothesis property tests for every numeric policy field; `# pragma: no cover` only for genuinely unreachable branches, each with a reason.

---

## File map

```
cursorloop/
├── pyproject.toml
├── .pre-commit-config.yaml
├── .gitignore                          # includes .cursorloop/
├── CURSOR.md  AGENTS.md  README.md  LICENSE  SECURITY.md  CONTRIBUTING.md
├── .github/workflows/{ci,docs,publish-to-pypi,release-please}.yml
├── src/cursorloop/
│   ├── __init__.py
│   ├── domain/
│   │   ├── errors.py            capacity.py       faults.py       lexicon.py
│   │   ├── retry_after.py       classify.py       completion.py   waiting.py
│   │   ├── budget.py            plan.py           session.py      autonomy.py
│   │   ├── hooks_policy.py      model_profile.py  model_policy.py control.py
│   │   ├── savepoint.py         snapshot.py       stop_summary.py loop.py
│   ├── application/
│   │   ├── ports.py  dto.py  runner.py
│   │   └── usecases/{run_plan,resume_agent,list_agents,doctor,run_control,invoke_api}.py
│   ├── infrastructure/
│   │   ├── agent/{gateway,options,translate,probe,catalog,models,usage,
│   │   │          watchdog,hooks,scripted,cli_fallback}.py
│   │   ├── api/{spec,binder,gateway,registry}.py
│   │   ├── clock.py  logging.py  redact.py  audit.py  state.py  lock.py
│   │   ├── config.py  rundir.py  notify.py  events.py  state_bus.py
│   │   ├── progress.py  control.py  doctor_env.py  git_savepoints.py
│   │   ├── snapshot.py
│   │   └── stream_ui/app.py
│   ├── cli/
│   │   ├── app.py  asyncio.py  render.py  man_page.py
│   │   └── commands/{run,resume,stop,prompt,status,logs,watch,runs,agents,
│   │                 models,usage,whoami,hooks,tools,dirs,skills,mcp,doctor,
│   │                 model_cmd,effort_cmd,preset_cmd,cwd_cmd,savepoints,
│   │                 unwind,snapshot_cmd,reset,cloud}.py
│   └── bootstrap.py
└── tests/
    ├── domain/         application/     infrastructure/     cli/
    ├── fixtures/       live/            live/system/
    └── conftest.py
```

---

## Task 1: Repository skeleton, packaging, and the CI gate set

**Files:**
- Create: `pyproject.toml`, `.pre-commit-config.yaml`, `.gitignore`, `.editorconfig`
- Create: `src/cursorloop/__init__.py`, `src/cursorloop/domain/__init__.py`, `src/cursorloop/application/__init__.py`
- Create: `tests/conftest.py`, `tests/test_packaging.py`
- Create: `.github/workflows/ci.yml`
- Create: `README.md`, `LICENSE`, `CURSOR.md`, `AGENTS.md`

**Interfaces:**
- Produces: an installable `cursorloop` package exposing `cursorloop.__version__`; a console script entry point registered (stub `main()` returning 0); four `import-linter` contracts.

**Key content — `pyproject.toml` fragments that must be exact:**

```toml
[project]
name = "cursorloop"
requires-python = ">=3.12"
dependencies = [
    "typer>=0.12",
    "structlog>=24.1",
    "cursor-sdk>=0.1",
    "anyio>=4.4",
    "httpx>=0.27",
    "textual>=1.0",
]

[project.scripts]
cursorloop = "cursorloop.cli.app:main"

[tool.pytest.ini_options]
testpaths = ["tests"]
# Deliberately NO --cov=... and NO --cov-fail-under here: pytest-cov UNIONS
# every --cov=X flag it sees, so a blanket --cov=cursorloop would silently
# widen CI's explicitly-scoped per-layer gates. Scope + floor are passed at
# each call site instead.
addopts = "--cov-report=term-missing -m \"not live and not system\""
asyncio_mode = "auto"
markers = [
    "live: exercises a real Cursor account (no token spend). Opt in with -m live.",
    "paid: additionally spends real tokens/turns. Requires --run-paid-live. Always paired with 'live'.",
    "system: deterministic system-live harness (real FS/git/CLI adapters + scripted agent). Opt in with -m system.",
]

[tool.importlinter]
root_package = "cursorloop"

[[tool.importlinter.contracts]]
name = "Onion layering"
type = "layers"
layers = ["cursorloop.cli", "cursorloop.bootstrap", "cursorloop.application", "cursorloop.domain"]

[[tool.importlinter.contracts]]
name = "Infrastructure only reachable from bootstrap"
type = "forbidden"
source_modules = ["cursorloop.domain", "cursorloop.application"]
forbidden_modules = ["cursorloop.infrastructure"]

[[tool.importlinter.contracts]]
name = "No Anthropic anywhere"
type = "forbidden"
source_modules = ["cursorloop"]
forbidden_modules = ["anthropic", "claude_agent_sdk"]

[[tool.importlinter.contracts]]
name = "Domain imports no third party"
type = "forbidden"
source_modules = ["cursorloop.domain"]
forbidden_modules = ["cursor_sdk", "typer", "structlog", "httpx", "anyio", "textual"]
```

**Test snippet:**

```python
# tests/test_packaging.py
from __future__ import annotations

import subprocess  # nosec B404 - fixed argv, no shell, test-only gate check
import sys
from pathlib import Path

import cursorloop

SRC = Path(__file__).resolve().parents[1] / "src" / "cursorloop"


def test_version_is_exposed() -> None:
    assert cursorloop.__version__


def test_no_anthropic_token_anywhere_in_src() -> None:
    """The 'no Anthropic dependency, ever' non-negotiable, checked as text as
    well as by import-linter: a string reference in a comment or an env-var
    lookup would slip past an import contract."""
    offenders: list[str] = []
    for path in SRC.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for needle in ("anthropic", "ANTHROPIC_", "claude_agent_sdk", "CLAUDELOOP_"):
            if needle in text:
                offenders.append(f"{path.relative_to(SRC)}: {needle}")
    assert offenders == [], f"forbidden vendor references in src/: {offenders}"


def test_import_linter_contracts_pass() -> None:
    result = subprocess.run(  # nosec B603 - fixed argv, no shell
        [sys.executable, "-m", "importlinter.cli", "lint-imports"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr
```

- [ ] **Step 1:** Write `tests/test_packaging.py` first. It fails (no package).
- [ ] **Step 2:** Create `pyproject.toml` with the fragments above, plus `[tool.ruff]` (`line-length = 100`, `target-version = "py312"`, `select = ["E","F","I","UP","B","SIM","C4"]`, `flake8-bugbear.extend-immutable-calls = ["typer.Option","typer.Argument"]`), `[tool.mypy]` (`strict = true`, `python_version = "3.12"`, `packages = ["cursorloop"]`, `mypy_path = "src"`), `[tool.coverage.run]` (`branch = true`, `source = ["src/cursorloop"]`).
- [ ] **Step 3:** Create the package skeleton with `__version__ = "0.1.0"` and empty layer packages. Add `.cursorloop/` to `.gitignore`.
- [ ] **Step 4:** Write `.pre-commit-config.yaml` (ruff, ruff-format, mypy, lint-imports, a commit-msg Conventional Commits hook) and `.github/workflows/ci.yml` running the seven gates on 3.12 and 3.13, with per-layer coverage invocations passed explicitly.
- [ ] **Step 5:** Write short `CURSOR.md` and `AGENTS.md` routers containing the five non-negotiables verbatim, the layer map, and a "where to go" table. Facts, not procedures.
- [ ] **Step 6:** `pytest tests/test_packaging.py -v && lint-imports && ruff check src tests && mypy src/cursorloop` all green.
- [ ] **Step 7:** Commit: `chore: scaffold cursorloop package, quality gates, and onion import contracts`

---

## Task 2: `domain/capacity.py` + `domain/faults.py` — the ADTs

**Files:**
- Create: `src/cursorloop/domain/capacity.py`, `src/cursorloop/domain/faults.py`, `src/cursorloop/domain/errors.py`
- Create: `tests/domain/test_capacity.py`, `tests/domain/test_faults.py`

**Interfaces:**
- Produces: `CapacityState = Available | WindowExhausted | CreditsExhausted | AuthenticationFailed`, `is_waitable(state) -> bool`, `Fault = TransientFault | Busy | ConfigFault`, `CursorloopError` hierarchy.

**Test snippet:**

```python
# tests/domain/test_capacity.py
from __future__ import annotations

import dataclasses
from datetime import UTC, datetime

import pytest

from cursorloop.domain.capacity import (
    AuthenticationFailed,
    Available,
    CreditsExhausted,
    WindowExhausted,
    is_waitable,
)


def test_credits_exhausted_has_no_reset_field_at_all() -> None:
    """THE load-bearing invariant. Not `resets_at=None` — the type must be
    incapable of expressing a reset instant, so no code path can compute a
    deadline from an empty balance and no future contributor can add one
    'for consistency' without deleting this test."""
    fields = {f.name for f in dataclasses.fields(CreditsExhausted)}
    assert "resets_at" not in fields
    assert "reset_at" not in fields
    assert fields == {"can_purchase"}


def test_window_exhausted_carries_optional_reset() -> None:
    at = datetime(2026, 8, 13, 14, 5, tzinfo=UTC)
    assert WindowExhausted("rate_limit", at).resets_at == at
    assert WindowExhausted("rate_limit").resets_at is None


@pytest.mark.parametrize(
    ("state", "expected"),
    [
        (Available(), True),
        (WindowExhausted("rate_limit"), True),
        (CreditsExhausted(), True),
        (AuthenticationFailed("revoked"), False),
    ],
)
def test_only_authentication_failure_is_unwaitable(state: object, expected: bool) -> None:
    assert is_waitable(state) is expected  # type: ignore[arg-type]


def test_states_are_frozen() -> None:
    with pytest.raises(dataclasses.FrozenInstanceError):
        Available().utilization = 0.5  # type: ignore[misc]
```

- [ ] **Step 1:** Write `tests/domain/test_capacity.py` and `tests/domain/test_faults.py`. Both fail.
- [ ] **Step 2:** Implement `capacity.py` — four `@dataclass(frozen=True, slots=True)` variants, the union alias, and `is_waitable()`. The `CreditsExhausted` docstring states, in prose, why it has no reset field.
- [ ] **Step 3:** Implement `faults.py` — `TransientFault(kind, attempt_hint)`, `Busy(agent_id, active_run_id)`, `ConfigFault(detail, help_url)`, union alias `Fault`. Docstring states these are deliberately *not* capacity states so they can never reach the wait policy.
- [ ] **Step 4:** Implement `errors.py` — `CursorloopError` base plus `PlanParseError`, `StateCorruptError`, `LockHeldError`, `BudgetExhaustedError`.
- [ ] **Step 5:** `pytest tests/domain -v --cov=cursorloop.domain --cov-fail-under=100` green.
- [ ] **Step 6:** Commit: `feat(domain): add CapacityState and Fault algebraic data types`

---

## Task 3: `domain/retry_after.py` and `domain/lexicon.py`

**Files:**
- Create: `src/cursorloop/domain/retry_after.py`, `src/cursorloop/domain/lexicon.py`
- Create: `tests/domain/test_retry_after.py`, `tests/domain/test_lexicon.py`

**Interfaces:**
- Produces: `parse_retry_after(value: str | None, *, now: datetime) -> datetime | None` handling integer-seconds and HTTP-date forms, **never raising**; `BillingLexicon` / `RateLimitLexicon` frozen matchers with `DEFAULT_BILLING_TERMS`, `DEFAULT_RATE_LIMIT_TERMS`, and `matches(*texts) -> str | None` returning the matched term for audit logging.

**Test snippet:**

```python
# tests/domain/test_retry_after.py
from __future__ import annotations

from datetime import UTC, datetime, timedelta

from hypothesis import given
from hypothesis import strategies as st

from cursorloop.domain.retry_after import parse_retry_after

NOW = datetime(2026, 8, 13, 12, 0, 0, tzinfo=UTC)


def test_integer_seconds_form() -> None:
    assert parse_retry_after("120", now=NOW) == NOW + timedelta(seconds=120)


def test_float_seconds_form_is_tolerated() -> None:
    assert parse_retry_after("1.5", now=NOW) == NOW + timedelta(seconds=1.5)


def test_http_date_form() -> None:
    assert parse_retry_after("Wed, 13 Aug 2026 14:05:00 GMT", now=NOW) == datetime(
        2026, 8, 13, 14, 5, 0, tzinfo=UTC
    )


def test_none_and_blank_are_absent_not_errors() -> None:
    assert parse_retry_after(None, now=NOW) is None
    assert parse_retry_after("   ", now=NOW) is None


def test_negative_seconds_clamp_to_now() -> None:
    """A server clock skew must never produce an instant in the past — the
    wait policy would then busy-spin."""
    assert parse_retry_after("-30", now=NOW) == NOW


@given(st.text())
def test_never_raises_on_arbitrary_input(value: str) -> None:
    """A multi-hour unattended run must not die on a malformed header."""
    result = parse_retry_after(value, now=NOW)
    assert result is None or result >= NOW
```

```python
# tests/domain/test_lexicon.py
from cursorloop.domain.lexicon import DEFAULT_BILLING_TERMS, BillingLexicon


def test_matches_are_case_insensitive_and_report_the_term() -> None:
    lex = BillingLexicon(DEFAULT_BILLING_TERMS)
    assert lex.matches("Your USAGE_LIMIT_REACHED for this month") == "usage_limit_reached"


def test_no_match_returns_none() -> None:
    assert BillingLexicon(DEFAULT_BILLING_TERMS).matches("connection reset by peer") is None


def test_none_and_empty_inputs_are_skipped() -> None:
    assert BillingLexicon(DEFAULT_BILLING_TERMS).matches(None, "", "  ") is None


def test_lexicon_is_overridable() -> None:
    assert BillingLexicon(("wallet_empty",)).matches("wallet_empty") == "wallet_empty"
```

- [ ] **Step 1:** Write both test modules. They fail.
- [ ] **Step 2:** Implement `retry_after.py` using `email.utils.parsedate_to_datetime` for the HTTP-date branch (stdlib — domain purity holds), wrapped so every exception path returns `None`. Clamp results to `>= now`.
- [ ] **Step 3:** Implement `lexicon.py` with the default term tuples from the roadmap §4.4 and a `matches(*texts: str | None) -> str | None` that lower-cases once and returns the first matching term.
- [ ] **Step 4:** `pytest tests/domain -v --cov=cursorloop.domain --cov-fail-under=100` green.
- [ ] **Step 5:** Commit: `feat(domain): parse Retry-After and add configurable billing/rate-limit lexicons`

---

## Task 4: `domain/classify.py` — the classifier, ordering and all

**Files:**
- Create: `src/cursorloop/domain/classify.py`
- Create: `tests/domain/test_classify.py`
- Create: `tests/fixtures/signals.py`

**Interfaces:**
- Produces: `TurnSignals` (frozen dataclass) and `classify(signals, *, now, billing=…, rate_limit=…) -> CapacityState | Fault`.

```python
@dataclass(frozen=True, slots=True)
class TurnSignals:
    error_type: str | None = None  # class name, e.g. "RateLimitError"
    error_code: str | None = None  # CursorAgentError.code
    proto_error_code: str | None = None
    error_message: str = ""
    http_status: int | None = None  # status_code
    is_retryable: bool | None = None
    retry_after: str | None = None
    run_status: str | None = None  # "finished"|"error"|"cancelled"|"expired"|"running"
    result_text: str = ""
    request_id: str | None = None
```

**Branch order — encoded in the module and asserted by tests:**
1. auth/permission → `AuthenticationFailed`
2. billing lexicon (code, proto code, message, or `result_text` when status is `"error"`) → `CreditsExhausted`
3. `RateLimitError` with `is_retryable is False` → `CreditsExhausted`
4. `RateLimitError` / HTTP 429 → `WindowExhausted("rate_limit", parse_retry_after(...))`
5. `run_status == "error"` + rate-limit lexicon → `WindowExhausted("rate_limit", None)`
6. `run_status == "expired"` → `WindowExhausted("run_expired", None)`
7. `AgentBusyError` → `Busy`; retryable network/timeout/5xx → `TransientFault`; `ConfigurationError`/`BadRequestError`/`IntegrationNotConnectedError` → `ConfigFault`
8. otherwise → `Available`

**Test snippet:**

```python
# tests/domain/test_classify.py
from __future__ import annotations

from datetime import UTC, datetime, timedelta

from hypothesis import given
from hypothesis import strategies as st

from cursorloop.domain.capacity import (
    AuthenticationFailed,
    Available,
    CreditsExhausted,
    WindowExhausted,
)
from cursorloop.domain.classify import TurnSignals, classify
from cursorloop.domain.faults import Busy, ConfigFault, TransientFault
from cursorloop.domain.lexicon import DEFAULT_BILLING_TERMS

NOW = datetime(2026, 8, 13, 12, 0, 0, tzinfo=UTC)


def test_credits_beat_a_stray_retry_after() -> None:
    """THE adversarial case. A rejection carrying BOTH a retry_after and a
    billing code must classify as CreditsExhausted: a spend cap does not clear
    because a clock advanced, and treating it as a window is exactly the bug
    this project exists to delete."""
    signals = TurnSignals(
        error_type="RateLimitError",
        error_code="usage_limit_reached",
        error_message="You have reached your monthly usage limit.",
        http_status=429,
        is_retryable=True,
        retry_after="60",
    )
    assert classify(signals, now=NOW) == CreditsExhausted(can_purchase=True)


def test_non_retryable_rate_limit_is_credits() -> None:
    """`is_retryable=False` on a RateLimitError means retrying will never clear
    it — that is an exhausted allowance, not a window."""
    signals = TurnSignals(error_type="RateLimitError", is_retryable=False, http_status=429)
    assert classify(signals, now=NOW) == CreditsExhausted(can_purchase=True)


def test_retryable_rate_limit_with_seconds_is_a_window() -> None:
    signals = TurnSignals(
        error_type="RateLimitError", is_retryable=True, retry_after="120", http_status=429
    )
    assert classify(signals, now=NOW) == WindowExhausted("rate_limit", NOW + timedelta(seconds=120))


def test_retryable_rate_limit_without_header_is_an_unscheduled_window() -> None:
    signals = TurnSignals(error_type="RateLimitError", is_retryable=True, http_status=429)
    assert classify(signals, now=NOW) == WindowExhausted("rate_limit", None)


def test_authentication_outranks_everything_including_billing() -> None:
    signals = TurnSignals(
        error_type="AuthenticationError",
        error_message="invalid api key; also out_of_credits",
        http_status=401,
    )
    assert classify(signals, now=NOW) == AuthenticationFailed(
        detail="invalid api key; also out_of_credits"
    )


def test_permission_denied_is_terminal_not_retried() -> None:
    signals = TurnSignals(error_type="PermissionDeniedError", http_status=403)
    assert isinstance(classify(signals, now=NOW), AuthenticationFailed)


def test_errored_run_status_is_read_even_though_nothing_was_thrown() -> None:
    """The second, non-thrown failure channel: run.wait() returns
    status='error' with free text. A classifier that only catches exceptions
    would score this as a successful turn."""
    signals = TurnSignals(run_status="error", result_text="Rate limit exceeded, slow down.")
    assert classify(signals, now=NOW) == WindowExhausted("rate_limit", None)


def test_errored_run_status_with_billing_text_is_credits() -> None:
    signals = TurnSignals(run_status="error", result_text="Payment required: add credits.")
    assert classify(signals, now=NOW) == CreditsExhausted(can_purchase=True)


def test_expired_run_is_a_window() -> None:
    assert classify(TurnSignals(run_status="expired"), now=NOW) == WindowExhausted(
        "run_expired", None
    )


def test_cancelled_run_is_not_a_capacity_problem() -> None:
    """We cancelled it (watchdog or operator). Re-sending is correct."""
    assert classify(TurnSignals(run_status="cancelled"), now=NOW) == Available()


def test_agent_busy_is_a_fault_not_capacity_despite_is_retryable_false() -> None:
    """AgentBusyError documents is_retryable=False, yet the remedy is
    cancel-then-resend. Handling it before the generic is_retryable check is
    what stops a naive `if not is_retryable: raise` aborting a recoverable run."""
    signals = TurnSignals(
        error_type="AgentBusyError", error_code="agent_busy", http_status=409, is_retryable=False
    )
    assert classify(signals, now=NOW) == Busy(agent_id="", active_run_id=None)


def test_transient_network_failure_is_a_fault() -> None:
    signals = TurnSignals(error_type="NetworkError", is_retryable=True)
    assert isinstance(classify(signals, now=NOW), TransientFault)


def test_configuration_error_is_terminal_config_fault() -> None:
    signals = TurnSignals(error_type="ConfigurationError", error_message="unknown model 'nope'")
    assert isinstance(classify(signals, now=NOW), ConfigFault)


def test_finished_run_is_available() -> None:
    assert classify(TurnSignals(run_status="finished", result_text="done"), now=NOW) == Available()


@given(term=st.sampled_from(DEFAULT_BILLING_TERMS), seconds=st.integers(1, 100_000))
def test_a_billing_term_never_produces_a_waitable_window(term: str, seconds: int) -> None:
    """The safety property, stated over the whole lexicon rather than a
    handful of examples: nothing carrying billing language may ever become a
    WindowExhausted with a deadline."""
    signals = TurnSignals(
        error_type="RateLimitError",
        error_message=f"error: {term}",
        is_retryable=True,
        retry_after=str(seconds),
        http_status=429,
    )
    assert classify(signals, now=NOW) == CreditsExhausted(can_purchase=True)
```

- [ ] **Step 1:** Write `tests/domain/test_classify.py` in full (all 15 cases above). All fail.
- [ ] **Step 2:** Create `tests/fixtures/signals.py` with synthetic `TurnSignals` builders. Each fixture carries a header comment stating it is **synthetic**, derived from documented `CursorAgentError` field shapes, and must be replaced by a real captured payload the first time one is observed.
- [ ] **Step 3:** Implement `classify.py` with the eight branches in order. Add a module-level comment stating that the order is load-bearing and naming the two tests that enforce it.
- [ ] **Step 4:** Add an `unclassified_terminal_error` sentinel: when `run_status == "error"` and no lexicon matches, return `Available` **and** set `signals`-derived detail on a returned marker the audit layer can log verbatim (via a module-level `UNCLASSIFIED_REASON` constant and a `classification_reason(signals) -> str` helper, kept pure).
- [ ] **Step 5:** `pytest tests/domain/test_classify.py -v` green; `--cov=cursorloop.domain --cov-fail-under=100` green.
- [ ] **Step 6:** Commit: `feat(domain): classify Cursor turn signals into capacity states and faults`

---

## Task 5: `domain/waiting.py` — probe scheduling

**Files:**
- Create: `src/cursorloop/domain/waiting.py`
- Create: `tests/domain/test_waiting.py`

**Interfaces:**
- Produces: `WaitPolicyConfig` (with `__post_init__` validation), `DEFAULT_WAIT_POLICY_CONFIG`, `next_probe_instant(state, *, now, started_waiting_at, probe_count, config) -> datetime`, `wait_exceeded(*, started_waiting_at, now, config) -> bool`, `ProgressWaitConfig` + `next_progress_wait_instant()`, `is_wait_only_remaining_work(items) -> bool`.

**Config defaults:** `credits_probe_interval=120s`, `credits_probe_ceiling=600s`, `credits_backoff_factor=1.5`, `window_probe_interval=300s`, `reset_grace=15s`, `max_wait=None`.

**Test snippet:**

```python
# tests/domain/test_waiting.py
from __future__ import annotations

from datetime import UTC, datetime, timedelta

from hypothesis import given, settings
from hypothesis import strategies as st

from cursorloop.domain.capacity import CreditsExhausted, WindowExhausted
from cursorloop.domain.waiting import (
    DEFAULT_WAIT_POLICY_CONFIG as CFG,
)
from cursorloop.domain.waiting import (
    next_probe_instant,
    wait_exceeded,
)

NOW = datetime(2026, 8, 13, 12, 0, 0, tzinfo=UTC)


def test_credits_probe_uses_the_bounded_cadence_not_a_deadline() -> None:
    at = next_probe_instant(
        CreditsExhausted(), now=NOW, started_waiting_at=NOW, probe_count=0, config=CFG
    )
    assert at == NOW + timedelta(seconds=CFG.credits_probe_interval)


def test_credits_backoff_is_clamped_to_the_ceiling() -> None:
    at = next_probe_instant(
        CreditsExhausted(), now=NOW, started_waiting_at=NOW, probe_count=50, config=CFG
    )
    assert at == NOW + timedelta(seconds=CFG.credits_probe_ceiling)


@settings(max_examples=300)
@given(probe_count=st.integers(min_value=0, max_value=10_000))
def test_credits_backoff_never_overflows_timedelta(probe_count: int) -> None:
    """Regression property inherited from the blueprint: computing
    interval * factor**probe_count and only THEN clamping overflows
    timedelta's magnitude limit at realistic probe counts. Clamp in float
    seconds BEFORE constructing the timedelta."""
    at = next_probe_instant(
        CreditsExhausted(), now=NOW, started_waiting_at=NOW, probe_count=probe_count, config=CFG
    )
    assert NOW < at <= NOW + timedelta(seconds=CFG.credits_probe_ceiling)


def test_window_probe_is_bounded_by_the_interval_even_for_a_far_reset() -> None:
    """A far-future resets_at must not become a blind sleep: the interval bound
    is what notices an early lift (a spend-cap raise, an admin unblock)."""
    far = NOW + timedelta(days=7)
    at = next_probe_instant(
        WindowExhausted("rate_limit", far),
        now=NOW,
        started_waiting_at=NOW,
        probe_count=0,
        config=CFG,
    )
    assert at == NOW + timedelta(seconds=CFG.window_probe_interval)


def test_window_probe_uses_reset_plus_grace_when_it_is_nearer() -> None:
    soon = NOW + timedelta(seconds=30)
    at = next_probe_instant(
        WindowExhausted("rate_limit", soon),
        now=NOW,
        started_waiting_at=NOW,
        probe_count=0,
        config=CFG,
    )
    assert at == soon + timedelta(seconds=CFG.reset_grace)


@given(
    elapsed=st.integers(min_value=0, max_value=1_000_000),
    probe_count=st.integers(min_value=0, max_value=500),
)
def test_probe_instant_is_never_in_the_past_and_never_exceeds_max_wait(
    elapsed: int, probe_count: int
) -> None:
    config = CFG.with_max_wait(timedelta(hours=6))
    started = NOW
    now = NOW + timedelta(seconds=elapsed)
    for state in (CreditsExhausted(), WindowExhausted("rate_limit", None)):
        at = next_probe_instant(
            state, now=now, started_waiting_at=started, probe_count=probe_count, config=config
        )
        assert at >= now
        assert at <= started + config.max_wait  # type: ignore[operator]


def test_wait_exceeded_is_the_paired_give_up_check() -> None:
    config = CFG.with_max_wait(timedelta(minutes=10))
    assert not wait_exceeded(started_waiting_at=NOW, now=NOW + timedelta(minutes=9), config=config)
    assert wait_exceeded(started_waiting_at=NOW, now=NOW + timedelta(minutes=11), config=config)
```

- [ ] **Step 1:** Write `tests/domain/test_waiting.py`. All fail.
- [ ] **Step 2:** Implement `WaitPolicyConfig` as a frozen dataclass with `__post_init__` rejecting non-positive intervals, a ceiling below the interval, and a factor `< 1.0`. Add `with_max_wait()` returning a new config.
- [ ] **Step 3:** Implement `next_probe_instant()`. **Compute the credits backoff in float seconds and clamp to the ceiling before constructing any `timedelta`.** Clamp every branch's candidate to `started_waiting_at + max_wait` when set, and to `>= now` always.
- [ ] **Step 4:** Implement `wait_exceeded()`, `ProgressWaitConfig`, `next_progress_wait_instant()`, `is_wait_only_remaining_work()`.
- [ ] **Step 5:** `pytest tests/domain/test_waiting.py -v` green including all Hypothesis properties.
- [ ] **Step 6:** Commit: `feat(domain): add adaptive probe scheduling with credits backoff and window bounds`

---

## Task 6: `domain/completion.py` — verdict block, marker, empty-turn

**Files:**
- Create: `src/cursorloop/domain/completion.py`, `src/cursorloop/domain/autonomy.py`, `src/cursorloop/domain/plan.py`
- Create: `tests/domain/test_completion.py`, `tests/domain/test_plan.py`

**Interfaces:**
- Produces: `CompletionVerdict = Done | Continue | Blocked`; `StructuredVerdict(complete, remaining_work, blocked_on, summary)`; `parse_verdict_block(text) -> StructuredVerdict | None`; `evaluate(*, structured, output_text, done_marker, tokens, empty_turn_streak, empty_turn_limit) -> CompletionVerdict`; `DEFAULT_DONE_MARKER = "CURSORLOOP_TASK_FULLY_COMPLETE"`; `VERDICT_FENCE = "cursorloop-verdict"`; `autonomy_preamble(...) -> str`; `WorkPlan.parse()` / `with_items_marked_done()`.

**Test snippet:**

```python
# tests/domain/test_completion.py
from __future__ import annotations

import textwrap

from cursorloop.domain.completion import (
    DEFAULT_DONE_MARKER,
    Blocked,
    Continue,
    Done,
    StructuredVerdict,
    evaluate,
    parse_verdict_block,
)


def _fenced(payload: str) -> str:
    return textwrap.dedent(f"""\
        Some assistant prose about the work.

        ```cursorloop-verdict
        {payload}
        ```
        """)


def test_parses_a_well_formed_verdict_block() -> None:
    text = _fenced('{"complete": false, "remaining_work": ["wire the gateway"], '
                   '"blocked_on": null, "summary": "made progress"}')
    assert parse_verdict_block(text) == StructuredVerdict(
        complete=False,
        remaining_work=("wire the gateway",),
        blocked_on=None,
        summary="made progress",
    )


def test_last_fence_wins() -> None:
    """A model quoting the instruction earlier in its own reasoning must not be
    mistaken for the actual verdict."""
    text = (
        _fenced('{"complete": true, "remaining_work": [], "blocked_on": null, "summary": "quoted"}')
        + _fenced('{"complete": false, "remaining_work": ["real"], '
                  '"blocked_on": null, "summary": "actual"}')
    )
    verdict = parse_verdict_block(text)
    assert verdict is not None and verdict.summary == "actual"


def test_malformed_json_is_absent_not_fatal() -> None:
    """A multi-hour run must never die on a stray brace."""
    assert parse_verdict_block(_fenced("{not json at all,,,}")) is None


def test_wrong_types_are_absent() -> None:
    assert parse_verdict_block(_fenced('{"complete": "yes"}')) is None


def test_no_fence_is_absent() -> None:
    assert parse_verdict_block("just prose, no fence here") is None


def test_blocked_on_outranks_complete_and_is_terminal() -> None:
    """A turn must never be allowed to claim both. blocked_on is reserved for
    true external/human blockers; waitable self-started work belongs in
    remaining_work with blocked_on null."""
    structured = StructuredVerdict(complete=True, blocked_on="needs prod DB credentials")
    assert evaluate(structured=structured, output_text="") == Blocked(
        reason="needs prod DB credentials"
    )


def test_structured_verdict_beats_the_marker() -> None:
    structured = StructuredVerdict(complete=False, remaining_work=("more",))
    assert evaluate(
        structured=structured, output_text=f"blah {DEFAULT_DONE_MARKER} blah"
    ) == Continue(remaining_work=("more",))


def test_marker_is_the_fallback_only_when_structured_is_absent() -> None:
    assert evaluate(structured=None, output_text=f"all set {DEFAULT_DONE_MARKER}") == Done()


def test_empty_zero_token_turn_becomes_a_wait_only_continue() -> None:
    assert evaluate(structured=None, output_text="   ", tokens=0, empty_turn_streak=0) == Continue(
        remaining_work=("Waiting for a non-empty model response",)
    )


def test_repeated_empty_turns_become_blocked() -> None:
    assert evaluate(
        structured=None, output_text="", tokens=0, empty_turn_streak=2, empty_turn_limit=3
    ) == Blocked(reason="repeated empty model responses")


def test_ordinary_text_with_no_signal_is_a_plain_continue() -> None:
    assert evaluate(structured=None, output_text="I refactored two files.") == Continue()
```

- [ ] **Step 1:** Write `tests/domain/test_completion.py` and `tests/domain/test_plan.py`. All fail.
- [ ] **Step 2:** Implement `completion.py`. `parse_verdict_block` scans for all ` ```cursorloop-verdict ` fences with a compiled `re` pattern (stdlib), takes the last, `json.loads` inside a `try`, and validates each field's type — returning `None` on any failure.
- [ ] **Step 3:** Implement `evaluate()` with precedence: structured (`blocked_on` → `complete` → `Continue`), then marker, then empty-turn soft-fail, then plain `Continue`.
- [ ] **Step 4:** Implement `autonomy.py` — `autonomy_preamble(done_marker, require_verdict)` returning the constant text: no human is available; choose the option you would recommend, state the assumption inline, and proceed; never ask a clarifying question; end every turn with the verdict fence; `blocked_on` is only for true external blockers. Plus `VERDICT_SCHEMA_DESCRIPTION`.
- [ ] **Step 5:** Implement `plan.py` — `WorkPlan.parse(markdown)` extracting `- [ ]`/`- [x]`/`* [ ]` items (either case) and `with_items_marked_done(frozenset)`.
- [ ] **Step 6:** Add `reconcile(verdict, plan) -> CompletionVerdict` that downgrades `Done` to `Continue` when unchecked plan items remain, and test it.
- [ ] **Step 7:** `pytest tests/domain -v --cov=cursorloop.domain --cov-fail-under=100` green.
- [ ] **Step 8:** Commit: `feat(domain): detect completion via verdict block, marker fallback, and plan reconciliation`

---

## Task 7: `domain/budget.py`, `model_profile.py`, `model_policy.py`, `session.py`

**Files:**
- Create: `src/cursorloop/domain/budget.py`, `model_profile.py`, `model_policy.py`, `session.py`, `hooks_policy.py`
- Create: `tests/domain/test_budget.py`, `test_model_profile.py`, `test_session.py`, `test_hooks_policy.py`

**Interfaces:**
- `Budget(max_turns, max_tokens, max_cost_usd, max_attempts, max_wall_clock)`; `BudgetLedger` immutable, `spend_turn(tokens, dollars_or_none)` returning a **new** ledger, `any_exhausted`, and a `cost_pending: bool` flag.
- `ModelProfile(model_id, params, effort, fast)` + `SHIPPED_PRESETS` (`composer`, `composer-fast`, `grok`, `grok-xhigh`, `grok-4.5`, `router-cost`, `router-balanced`, `router-intelligence`).
- `AgentRef(agent_id, runtime, cwd, name, summary, last_modified, status)` with `runtime_from_id(agent_id)`; `AgentSelector = PlanFileSelector | ExplicitAgentSelector | MostRecentAgentSelector`.
- `hooks_policy.MANAGED_EVENTS` and `allow_payload(event) -> dict[str, str]`.

**Test snippet:**

```python
# tests/domain/test_budget.py
from cursorloop.domain.budget import Budget, BudgetLedger


def test_unknown_cost_is_never_treated_as_zero() -> None:
    """agent.get_usage().cost is None until billing settles, and
    charged_cents is 0.0 for plan-included/BYOK usage. A ledger that reads a
    settling None as $0.00 will blow straight through --max-cost."""
    ledger = BudgetLedger(budget=Budget(max_cost_usd=1.0)).spend_turn(tokens=500, dollars=None)
    assert ledger.cost_pending is True
    assert ledger.dollars_spent == 0.0
    assert ledger.dollars_exhausted is False


def test_tokens_are_the_enforceable_hard_cap() -> None:
    ledger = BudgetLedger(budget=Budget(max_tokens=1000)).spend_turn(tokens=1200, dollars=None)
    assert ledger.tokens_exhausted is True
    assert ledger.any_exhausted is True


def test_ledger_is_immutable() -> None:
    first = BudgetLedger(budget=Budget(max_turns=5))
    second = first.spend_turn(tokens=10, dollars=0.01)
    assert first.turns_spent == 0
    assert second.turns_spent == 1


def test_unset_caps_are_never_exhausted() -> None:
    ledger = BudgetLedger(budget=Budget()).spend_turn(tokens=10**9, dollars=10**6)
    assert ledger.any_exhausted is False
```

```python
# tests/domain/test_model_profile.py
from cursorloop.domain.model_profile import SHIPPED_PRESETS, ModelProfile


def test_default_preset_is_composer() -> None:
    assert SHIPPED_PRESETS["composer"].model_id == "composer-2.5"


def test_grok_is_a_profile_not_a_product() -> None:
    """Grok is one entry in the profile table, reachable through the same
    gateway and the same taxonomy as Composer. There is no separate adapter."""
    grok = SHIPPED_PRESETS["grok"]
    assert grok.model_id == "cursor-grok-4.6"
    assert grok.effort == "high"


def test_fast_variants_are_expressed_as_params_not_ids() -> None:
    profile = SHIPPED_PRESETS["composer-fast"]
    assert profile.model_id == "composer-2.5"
    assert ("fast", "true") in profile.params


def test_router_presets_always_pass_optimize_for_explicitly() -> None:
    """Omitting optimize_for, or sending a legacy 'default', is not a supported
    Router contract."""
    for name in ("router-cost", "router-balanced", "router-intelligence"):
        profile = SHIPPED_PRESETS[name]
        assert profile.model_id == "auto-smart"
        assert any(pid == "optimize_for" for pid, _ in profile.params)


def test_profile_to_selection_payload_is_serialisable() -> None:
    payload = ModelProfile("composer-2.5", params=(("fast", "true"),)).to_selection_payload()
    assert payload == {"id": "composer-2.5", "params": [{"id": "fast", "value": "true"}]}
```

- [ ] **Step 1:** Write the four test modules. All fail.
- [ ] **Step 2:** Implement `budget.py` with the `cost_pending` distinction and a `Budget.max_tokens` cap.
- [ ] **Step 3:** Implement `model_profile.py` with `SHIPPED_PRESETS` and `to_selection_payload()` producing the wire shape the gateway will feed to `ModelSelection` (kept as plain dicts so `domain/` never imports `cursor_sdk`).
- [ ] **Step 4:** Implement `model_policy.py` — escalation rules **and** the mandatory de-escalation emission, because per-run model overrides are sticky and a one-off escalation would otherwise bill every later turn at the higher rate. Test: `test_escalation_emits_a_matching_de_escalation`.
- [ ] **Step 5:** Implement `session.py` with `runtime_from_id` (`bc-` → `"cloud"`, else `"local"`) and the three-shape selector union.
- [ ] **Step 6:** Implement `hooks_policy.py` — `MANAGED_EVENTS = ("preToolUse", "beforeShellExecution", "beforeMCPExecution", "beforeReadFile", "beforeSubmitPrompt", "stop")` and pure `allow_payload()` / `preamble_injection_payload()` builders.
- [ ] **Step 7:** `pytest tests/domain -v --cov=cursorloop.domain --cov-fail-under=100` green.
- [ ] **Step 8:** Commit: `feat(domain): add budget ledger, model profiles, agent selectors, and hook policy`

---

## Task 8: `domain/loop.py` — the run-loop state machine

**Files:**
- Create: `src/cursorloop/domain/loop.py`, `src/cursorloop/domain/control.py`
- Create: `tests/domain/test_loop.py`

**Interfaces:**
- `Phase = PREFLIGHT | RUNNING | WAITING | PROBING | COMPLETE | FAILED`; `RunState(phase, ledger, started_waiting_at, probe_count, failure_reason)`; `Decision = SendTurn | RunProbe | ScheduleProbe | DelayThenSend | Finish`; `start()`, `decide_preflight()`, `decide_after_turn()`, `decide_after_probe()`, `decide_progress_delay()`.

**Test snippet:**

```python
# tests/domain/test_loop.py
from __future__ import annotations

from datetime import UTC, datetime, timedelta

from cursorloop.domain.budget import Budget, BudgetLedger
from cursorloop.domain.capacity import (
    AuthenticationFailed,
    Available,
    CreditsExhausted,
    WindowExhausted,
)
from cursorloop.domain.completion import Blocked, Continue, Done
from cursorloop.domain.loop import (
    Finish,
    Phase,
    ScheduleProbe,
    SendTurn,
    decide_after_probe,
    decide_after_turn,
    decide_preflight,
    start,
)

NOW = datetime(2026, 8, 13, 12, 0, 0, tzinfo=UTC)
LEDGER = BudgetLedger(budget=Budget(max_turns=100))


def test_after_turn_limit_outranks_completion_claim() -> None:
    """THE single most important invariant in the codebase: capacity is
    checked BEFORE the verdict, always. A Done verdict on a turn that also hit
    a rejection is discarded — a truncated limit message can coincidentally
    contain marker-like text, and hitting a real limit is never 'done'.
    NEVER reorder this check."""
    state, decision = decide_after_turn(
        start(LEDGER),
        capacity=CreditsExhausted(),
        verdict=Done(summary="all finished!"),
        now=NOW,
    )
    assert state.phase is Phase.WAITING
    assert isinstance(decision, ScheduleProbe)


def test_credits_exhaustion_schedules_a_probe_never_a_deadline_sleep() -> None:
    _, decision = decide_after_turn(
        start(LEDGER), capacity=CreditsExhausted(), verdict=Continue(), now=NOW
    )
    assert isinstance(decision, ScheduleProbe)
    assert NOW < decision.at <= NOW + timedelta(seconds=600)


def test_authentication_failure_is_terminal_from_every_phase() -> None:
    for decide in (
        lambda: decide_preflight(start(LEDGER), AuthenticationFailed("bad key"), now=NOW),
        lambda: decide_after_turn(
            start(LEDGER), capacity=AuthenticationFailed("bad key"), verdict=Continue(), now=NOW
        ),
        lambda: decide_after_probe(start(LEDGER), AuthenticationFailed("bad key"), now=NOW),
    ):
        state, decision = decide()
        assert state.phase is Phase.FAILED
        assert decision == Finish(success=False, reason="authentication failed")


def test_preflight_probes_before_spending_a_real_turn_when_exhausted() -> None:
    state, decision = decide_preflight(
        start(LEDGER), WindowExhausted("rate_limit", NOW + timedelta(minutes=5)), now=NOW
    )
    assert state.phase is Phase.WAITING
    assert isinstance(decision, ScheduleProbe)


def test_probe_finding_capacity_resumes_the_run() -> None:
    waiting, _ = decide_after_turn(
        start(LEDGER), capacity=CreditsExhausted(), verdict=Continue(), now=NOW
    )
    state, decision = decide_after_probe(waiting, Available(), now=NOW + timedelta(minutes=2))
    assert state.phase is Phase.RUNNING
    assert decision == SendTurn()


def test_repeated_probes_increment_the_count_and_keep_the_original_start() -> None:
    state, _ = decide_after_turn(
        start(LEDGER), capacity=CreditsExhausted(), verdict=Continue(), now=NOW
    )
    for i in range(1, 4):
        state, _ = decide_after_probe(state, CreditsExhausted(), now=NOW + timedelta(minutes=2 * i))
        assert state.probe_count == i
        assert state.started_waiting_at == NOW


def test_blocked_verdict_terminates_the_run() -> None:
    state, decision = decide_after_turn(
        start(LEDGER),
        capacity=Available(),
        verdict=Blocked(reason="needs prod credentials"),
        now=NOW,
    )
    assert state.phase is Phase.FAILED
    assert decision == Finish(success=False, reason="needs prod credentials")


def test_budget_exhaustion_stops_the_loop() -> None:
    tight = BudgetLedger(budget=Budget(max_turns=1))
    state, decision = decide_after_turn(
        start(tight), capacity=Available(), verdict=Continue(), now=NOW, tokens=10
    )
    assert state.phase is Phase.FAILED
    assert decision == Finish(success=False, reason="budget exhausted")
```

- [ ] **Step 1:** Write `tests/domain/test_loop.py`. All fail.
- [ ] **Step 2:** Implement `loop.py`, porting the blueprint's structure. In `decide_after_turn`, the capacity check comes **before** the verdict check, with a comment naming `test_after_turn_limit_outranks_completion_claim` and stating never to reorder.
- [ ] **Step 3:** Use exhaustiveness `assert isinstance(...)` guards on the closed unions with `# nosec B101` and a comment matching the blueprint's justification style (precondition, not a security gate; fails loudly if a future union variant is added without a branch).
- [ ] **Step 4:** Implement `control.py` — `ControlCommand = Stop | Prompt | SetModel | SetEffort | SetCwd | Snapshot | SavePoint`.
- [ ] **Step 5:** `pytest tests/domain -v --cov=cursorloop.domain --cov-fail-under=100` green; `bandit -q -r src/cursorloop` clean.
- [ ] **Step 6:** Commit: `feat(domain): add the pure run-loop state machine with capacity-outranks-verdict ordering`

---

## Task 9: `application/ports.py`, `dto.py`, and the fakes

**Files:**
- Create: `src/cursorloop/application/ports.py`, `src/cursorloop/application/dto.py`
- Create: `tests/application/fakes.py`, `tests/application/test_fakes_satisfy_ports.py`

**Interfaces:**
- Ports (all `typing.Protocol`, never ABC): `Clock`, `Sleeper`, `AgentGateway`, `CapacityProbe`, `AgentCatalog`, `ModelCatalog`, `UsageReader`, `HookManager`, `ProgressReporter`, `AuditLog`, `Notifier`, `Logger`, `RunStateStore`, `AgentLock`, `RunControl`, `RunEventSink`, `StreamUi`, `SavePointStore`, `StateBus`, `RunSnapshotSink`, `ApiGateway`.
- DTOs: `TurnOutcome(signals, verdict, output_text, agent_id, run_id, tokens, cost_usd, cost_pending, raw_events)`, `ProbeResult(signals, at)`, `RunResult(success, reason, agent_id, turns_spent, tokens_spent, dollars_spent, cost_pending)`.

**Key port shapes:**

```python
class AgentGateway(Protocol):
    """Wraps a durable cursor_sdk Agent. Each send_turn() maps to one
    agent.send() → Run. An errored Run does NOT invalidate the agent, so the
    outer loop is repeated sends on one handle, never respawn-and-reattach."""

    async def send_turn(self, prompt_text: str, *, force: bool = False) -> TurnOutcome: ...
    async def close(self) -> None: ...
    async def set_profile(self, profile: ModelProfile) -> None: ...
    async def set_cwd(self, cwd: str) -> None: ...
    async def cancel_active_run(self) -> bool: ...
    def agent_id(self) -> str: ...


class HookManager(Protocol):
    """Autonomy policy lives in .cursor/hooks.json because Cursor hooks are
    file-based only — there is no programmatic permission callback."""

    def install(self) -> None: ...
    def restore(self) -> bool: ...
    def is_installed(self) -> bool: ...


class UsageReader(Protocol):
    async def turn_tokens(self, run_id: str) -> int: ...
    async def billed_cost_usd(self) -> float | None: ...  # None means UNKNOWN, never zero
```

**Test snippet:**

```python
# tests/application/test_fakes_satisfy_ports.py
from cursorloop.application import ports
from tests.application import fakes


def test_every_fake_structurally_satisfies_its_protocol() -> None:
    """Protocol conformance is structural, so a drifted fake fails silently at
    runtime and only shows up as a confusing test failure later. Assert it."""
    assert isinstance(fakes.FakeClock(), ports.Clock)
    assert isinstance(fakes.FakeSleeper(fakes.FakeClock()), ports.Sleeper)
    assert isinstance(fakes.FakeAgentGateway([]), ports.AgentGateway)
    assert isinstance(fakes.FakeCapacityProbe([]), ports.CapacityProbe)
    assert isinstance(fakes.FakeHookManager(), ports.HookManager)
    assert isinstance(fakes.FakeNotifier(), ports.Notifier)
    assert isinstance(fakes.FakeAuditLog(), ports.AuditLog)


def test_fake_sleeper_advances_the_fake_clock_without_real_sleeping() -> None:
    """This is what makes a simulated seven-day wait run in microseconds."""
    clock = fakes.FakeClock()
    sleeper = fakes.FakeSleeper(clock)
    target = clock.now().replace(year=clock.now().year + 1)
    import anyio

    anyio.run(sleeper.sleep_until, target)
    assert clock.now() == target
    assert sleeper.total_simulated_seconds > 0
```

- [ ] **Step 1:** Write `tests/application/test_fakes_satisfy_ports.py`. It fails.
- [ ] **Step 2:** Implement `ports.py`. Mark every protocol `@runtime_checkable` so the conformance test is possible. Each port's docstring states the *shape* contract, never a concrete type.
- [ ] **Step 3:** Implement `dto.py` with `cost_pending` propagated from the usage reader.
- [ ] **Step 4:** Implement `tests/application/fakes.py`: `FakeClock` (settable, monotonic), `FakeSleeper` (advances the clock, records total simulated seconds, never sleeps), `FakeAgentGateway` (replays a scripted list of `TurnOutcome`), `FakeCapacityProbe` (replays a scripted list of `TurnSignals`), `FakeHookManager`, `FakeNotifier`, `FakeAuditLog`, `FakeRunStateStore`, `FakeAgentLock`, `FakeUsageReader`.
- [ ] **Step 5:** `pytest tests/application -v --cov=cursorloop.application --cov-fail-under=100` green; `lint-imports` green.
- [ ] **Step 6:** Commit: `feat(application): declare protocol ports, DTOs, and the port fakes`

---

## Task 10: `application/runner.py` — the executor

**Files:**
- Create: `src/cursorloop/application/runner.py`
- Create: `src/cursorloop/application/usecases/run_plan.py`
- Create: `tests/application/test_runner.py`

**Interfaces:**
- `RunnerContext` (all ports + config), `AutonomousRunner.run(initial_prompt) -> RunResult`.

The runner pattern-matches `Decision` **exhaustively**: `SendTurn` → `gateway.send_turn`, `RunProbe` → `probe.probe`, `ScheduleProbe` → `reporter.waiting` + `sleeper.sleep_until` + `RunProbe`, `DelayThenSend` → interruptible sleep then send, `Finish` → terminal. `Fault` values are handled before the state machine sees anything: `TransientFault` → jittered bounded retry; `Busy` → `cancel_active_run()` then re-send with `force=True`; `ConfigFault` → terminal.

**Test snippet:**

```python
# tests/application/test_runner.py
from __future__ import annotations

import anyio

from cursorloop.domain.capacity import Available, CreditsExhausted
from tests.application import fakes


def test_runner_resumes_on_the_probe_that_finds_a_credit_top_up() -> None:
    """The scenario the whole project exists for: five probes still exhausted,
    the sixth finds capacity, and the run resumes THERE — not at some invented
    deadline, because CreditsExhausted has no deadline to invent."""
    probe = fakes.FakeCapacityProbe([CreditsExhausted()] * 5 + [Available()])
    gateway = fakes.FakeAgentGateway(
        [fakes.turn(capacity=CreditsExhausted()), fakes.turn(done=True, summary="finished")]
    )
    clock, sleeper = fakes.FakeClock(), None
    sleeper = fakes.FakeSleeper(clock)
    runner = fakes.build_runner(gateway=gateway, probe=probe, clock=clock, sleeper=sleeper)

    result = anyio.run(runner.run, "do the work")

    assert result.success is True
    assert probe.calls == 6
    assert sleeper.real_sleep_calls == 0  # a multi-hour wait, zero wall-clock seconds


def test_notifier_fires_on_entry_to_credits_exhaustion() -> None:
    """A human has to act, so a human has to be told — immediately, not after
    the run eventually gives up."""
    notifier = fakes.FakeNotifier()
    runner = fakes.build_runner(
        gateway=fakes.FakeAgentGateway([fakes.turn(capacity=CreditsExhausted())]),
        probe=fakes.FakeCapacityProbe([CreditsExhausted(), Available()]),
        notifier=notifier,
    )
    anyio.run(runner.run, "do the work")
    assert any("credit" in message.lower() for message in notifier.messages)


def test_busy_error_cancels_the_active_run_then_re_sends_with_force() -> None:
    gateway = fakes.FakeAgentGateway([fakes.busy_turn(), fakes.turn(done=True)])
    runner = fakes.build_runner(gateway=gateway)
    result = anyio.run(runner.run, "do the work")
    assert result.success is True
    assert gateway.cancel_calls == 1
    assert gateway.force_flags == [False, True]


def test_transient_fault_retries_then_gives_up_at_the_cap() -> None:
    gateway = fakes.FakeAgentGateway([fakes.transient_turn()] * 10)
    runner = fakes.build_runner(gateway=gateway, max_transient_retries=3)
    result = anyio.run(runner.run, "do the work")
    assert result.success is False
    assert gateway.send_calls == 4  # initial + 3 retries


def test_hooks_are_restored_even_when_the_run_fails() -> None:
    hooks = fakes.FakeHookManager()
    runner = fakes.build_runner(
        gateway=fakes.FakeAgentGateway([fakes.blocked_turn("needs prod creds")]), hooks=hooks
    )
    anyio.run(runner.run, "do the work")
    assert hooks.installed_then_restored is True
```

- [ ] **Step 1:** Write `tests/application/test_runner.py`. All fail.
- [ ] **Step 2:** Implement `runner.py`. Wrap the whole run in a `try/finally` that restores hooks, releases the agent lock, persists state, and closes the gateway — so `test_hooks_are_restored_even_when_the_run_fails` passes for the right reason.
- [ ] **Step 3:** On entry to `CreditsExhausted`, fire `notifier.notify(...)` exactly once per waiting episode (not once per probe) and record an `entered_credits_exhausted` audit event.
- [ ] **Step 4:** On every probe, diff against the previous `CapacityState` and, on restoration, emit an explicit audit line naming the probe number and elapsed wait.
- [ ] **Step 5:** Implement `usecases/run_plan.py` — read the plan file, parse a `WorkPlan`, build the first prompt as `autonomy_preamble() + plan_text`, and reconcile each turn's `remaining_work` back against the plan.
- [ ] **Step 6:** `pytest tests/application -v --cov=cursorloop.application --cov-fail-under=100` green.
- [ ] **Step 7:** Commit: `feat(application): add the autonomous runner with probe-based recovery and fault handling`

---

## Task 11: `infrastructure/agent/options.py` — one builder for create and resume

**Files:**
- Create: `src/cursorloop/infrastructure/agent/options.py`
- Create: `tests/infrastructure/test_agent_options.py`

**Interfaces:**
- `build_agent_options(*, profile, cwd, dirs, setting_sources, tools, disallowed_tools, sandbox, mcp_servers, subagents, mode, name, auto_review) -> AgentOptions`.

**Why one builder:** nothing persists across `Agent.resume()` — not the model, not inline MCP servers, not `tools`/`disallowed_tools`, not `custom_tools`. A resume path that rebuilds options by hand silently loses safety restrictions. One builder, called by both paths, plus a test that proves it.

**Test snippet:**

```python
# tests/infrastructure/test_agent_options.py
from cursorloop.domain.model_profile import SHIPPED_PRESETS
from cursorloop.infrastructure.agent.options import build_agent_options


def test_auto_review_is_always_off_for_autonomous_runs() -> None:
    """Auto-review routes local tool calls through an interactive gate. An
    unattended run that enables it will park."""
    options = build_agent_options(profile=SHIPPED_PRESETS["composer"], cwd="/repo")
    assert options.local is not None
    assert options.local.auto_review is False


def test_mode_is_explicitly_agent_never_plan() -> None:
    options = build_agent_options(profile=SHIPPED_PRESETS["composer"], cwd="/repo")
    assert options.mode == "agent"


def test_hermetic_by_default_no_setting_sources() -> None:
    """Without setting_sources, only inline MCP servers load — and the same
    switch gates project skills. Hermetic is the reproducible default;
    --setting-sources project is an opt-in that also enables project MCP."""
    options = build_agent_options(profile=SHIPPED_PRESETS["composer"], cwd="/repo")
    assert options.local is not None
    assert options.local.setting_sources is None


def test_model_selection_carries_profile_params() -> None:
    options = build_agent_options(profile=SHIPPED_PRESETS["composer-fast"], cwd="/repo")
    assert options.model.id == "composer-2.5"
    assert [(p.id, p.value) for p in options.model.params] == [("fast", "true")]


def test_multi_root_goes_to_dirs_not_cwd() -> None:
    """LocalAgentOptions rejects multi-entry cwd; extra roots belong in dirs."""
    options = build_agent_options(
        profile=SHIPPED_PRESETS["composer"], cwd="/repo", dirs=("/repo/pkg-a", "/repo/pkg-b")
    )
    assert options.local is not None
    assert options.local.cwd == "/repo"
    assert list(options.local.dirs) == ["/repo/pkg-a", "/repo/pkg-b"]


def test_resume_uses_the_same_builder_and_loses_nothing() -> None:
    """Nothing persists across Agent.resume(): not the model, not inline MCP,
    not tools/disallowed_tools. Both paths must produce identical options."""
    kwargs = {
        "profile": SHIPPED_PRESETS["grok"],
        "cwd": "/repo",
        "disallowed_tools": ("shell",),
        "tools": ("read", "edit", "grep"),
    }
    assert build_agent_options(**kwargs) == build_agent_options(**kwargs)
```

- [ ] **Step 1:** Write `tests/infrastructure/test_agent_options.py`. All fail.
- [ ] **Step 2:** Implement `options.py`. `auto_review=False` and `mode="agent"` are hard defaults, not caller choices, and each carries a comment explaining the stall path it closes.
- [ ] **Step 3:** Convert `ModelProfile.to_selection_payload()` into a real `ModelSelection` here — this is the only place the domain's plain dict meets `cursor_sdk`.
- [ ] **Step 4:** `pytest tests/infrastructure/test_agent_options.py -v` green; `lint-imports` green (this is the first module importing `cursor_sdk`, so the contract is genuinely exercised).
- [ ] **Step 5:** Commit: `feat(infra): build Cursor agent options from a single create/resume builder`

---

## Task 12: `infrastructure/agent/translate.py` — SDK → `TurnOutcome`

**Files:**
- Create: `src/cursorloop/infrastructure/agent/translate.py`
- Create: `tests/infrastructure/test_translate.py`, `tests/fixtures/sdk_payloads.py`

**Interfaces:**
- `signals_from_exception(exc) -> TurnSignals`, `signals_from_run(run) -> TurnSignals`, `outcome_from_run(run, buffered_text, tokens, cost) -> TurnOutcome`, `TeeStream` (consumes `run.messages()` exactly once, buffering text and forwarding deltas to a `StreamUi`).

**Test snippet:**

```python
# tests/infrastructure/test_translate.py
from cursorloop.infrastructure.agent.translate import signals_from_exception, signals_from_run
from tests.fixtures import sdk_payloads


def test_exception_fields_are_captured_verbatim_for_classification() -> None:
    exc = sdk_payloads.fake_rate_limit_error(
        code="usage_limit_reached", is_retryable=False, retry_after=None, request_id="req_123"
    )
    signals = signals_from_exception(exc)
    assert signals.error_type == "RateLimitError"
    assert signals.error_code == "usage_limit_reached"
    assert signals.is_retryable is False
    assert signals.request_id == "req_123"


def test_errored_run_without_an_exception_still_produces_signals() -> None:
    """The non-thrown channel. run.wait() returning status='error' is a real,
    first-class outcome — not an absence of failure."""
    run = sdk_payloads.fake_run(status="error", result="Usage limit reached for this month.")
    signals = signals_from_run(run)
    assert signals.run_status == "error"
    assert "usage limit" in signals.result_text.lower()


def test_request_id_is_always_carried_for_support_escalation() -> None:
    exc = sdk_payloads.fake_network_error(request_id="req_abc")
    assert signals_from_exception(exc).request_id == "req_abc"


def test_stream_is_consumed_exactly_once() -> None:
    """messages(), events(), and iter_text() all advance the same underlying
    stream. Any adapter that both streams for the UI and re-reads for
    classification gets an empty second pass — so we tee on a single pass."""
    run = sdk_payloads.fake_streaming_run(["hello ", "world"])
    from cursorloop.infrastructure.agent.translate import TeeStream

    tee = TeeStream(run)
    text = tee.drain()
    assert text == "hello world"
    assert run.consume_count == 1
```

- [ ] **Step 1:** Write `tests/infrastructure/test_translate.py` and `tests/fixtures/sdk_payloads.py`. All fail. Each fixture builder carries a header comment stating it is **synthetic**, derived from the documented dataclass shapes, and must be replaced by a real captured payload the first time one is observed in the wild.
- [ ] **Step 2:** Implement `signals_from_exception` reading `type(exc).__name__`, `code`, `proto_error_code`, `str(exc)`/`message`, `status_code`, `is_retryable`, `retry_after`, `request_id` — every attribute accessed with `getattr(exc, name, None)` so an SDK version lacking one does not crash the run.
- [ ] **Step 3:** Implement `signals_from_run` and `outcome_from_run`, propagating `run.usage.total_tokens` when present and `None` cost when unsettled.
- [ ] **Step 4:** Implement `TeeStream`: one pass over `run.messages()`, buffering assistant text, forwarding `tool_call`/`status`/`usage` to the event sink and `on_delta` text to the `StreamUi`, then `run.wait()` for the terminal result.
- [ ] **Step 5:** `pytest tests/infrastructure -v` green.
- [ ] **Step 6:** Commit: `feat(infra): translate Cursor SDK runs and errors into turn signals`

---

## Task 13: `infrastructure/agent/gateway.py`, `probe.py`, `watchdog.py`, `catalog.py`, `models.py`, `usage.py`

**Files:**
- Create: those six modules under `src/cursorloop/infrastructure/agent/`
- Create: `tests/infrastructure/test_gateway.py`, `test_probe.py`, `test_watchdog.py`, `test_models.py`

**Interfaces:**
- `CursorAgentGateway(client, agent, profile, watchdog, event_sink)` implementing `AgentGateway`.
- `CursorCapacityProbe(cwd, profile)` implementing `CapacityProbe` via `Agent.prompt(tools=[])`.
- `TurnWatchdog(turn_timeout, stall_timeout, clock)` — cancels a stalled run.
- `CursorAgentCatalog(client)` implementing `AgentCatalog` over `client.agents.list/get/list_runs`.
- `CursorModelCatalog(client)` implementing `ModelCatalog` over `client.models.list()`.
- `CursorUsageReader(agent)` implementing `UsageReader`.

**Test snippet:**

```python
# tests/infrastructure/test_probe.py
from cursorloop.infrastructure.agent.probe import build_probe_options


def test_probe_offers_no_tools_at_all() -> None:
    """tools=[] is documented as offering no built-in tools: the model can only
    respond with text. Cheapest possible capacity check, zero blast radius."""
    options = build_probe_options(cwd="/repo")
    assert list(options.tools) == []


def test_probe_is_hermetic_and_leaves_no_transcript() -> None:
    """Agent.prompt() creates, sends, waits, and disposes, so the throwaway
    turn never pollutes the working agent's conversation."""
    options = build_probe_options(cwd="/repo")
    assert options.local is not None
    assert options.local.setting_sources is None
    assert options.name == "cursorloop-probe"
```

```python
# tests/infrastructure/test_watchdog.py
from datetime import timedelta

import anyio

from cursorloop.infrastructure.agent.watchdog import TurnWatchdog
from tests.application import fakes


def test_no_delta_for_the_stall_timeout_cancels_the_run() -> None:
    """A model that stops emitting and never terminates is the stall path with
    no interception point — Cursor exposes no ask-user tool to intercept. The
    watchdog is what makes it survivable."""
    clock = fakes.FakeClock()
    run = fakes.FakeRun(status="running")
    watchdog = TurnWatchdog(
        turn_timeout=timedelta(minutes=30), stall_timeout=timedelta(minutes=10), clock=clock
    )
    watchdog.turn_started(run)
    clock.advance(timedelta(minutes=11))
    anyio.run(watchdog.tick)
    assert run.cancel_calls == 1


def test_a_terminal_run_is_never_cancelled() -> None:
    """run.cancel() on an already-terminal run raises
    UnsupportedRunOperationError. Guard on run.status."""
    clock = fakes.FakeClock()
    run = fakes.FakeRun(status="finished")
    watchdog = TurnWatchdog(
        turn_timeout=timedelta(minutes=1), stall_timeout=timedelta(minutes=1), clock=clock
    )
    watchdog.turn_started(run)
    clock.advance(timedelta(minutes=5))
    anyio.run(watchdog.tick)
    assert run.cancel_calls == 0


def test_a_delta_resets_the_stall_clock() -> None:
    clock = fakes.FakeClock()
    run = fakes.FakeRun(status="running")
    watchdog = TurnWatchdog(
        turn_timeout=timedelta(hours=2), stall_timeout=timedelta(minutes=10), clock=clock
    )
    watchdog.turn_started(run)
    clock.advance(timedelta(minutes=9))
    watchdog.saw_delta()
    clock.advance(timedelta(minutes=9))
    anyio.run(watchdog.tick)
    assert run.cancel_calls == 0
```

```python
# tests/infrastructure/test_models.py
import pytest

from cursorloop.infrastructure.agent.models import resolve_profile
from tests.fixtures import sdk_payloads


def test_unknown_model_is_rejected_against_the_live_catalog_not_a_constant() -> None:
    """Cursor ships models faster than we ship releases, so the catalog is the
    source of truth and the error lists what IS available."""
    catalog = sdk_payloads.fake_model_catalog(["composer-2.5", "cursor-grok-4.6"])
    with pytest.raises(ValueError, match="composer-2.5"):
        resolve_profile("gpt-9-turbo", catalog=catalog)


def test_router_requires_optimize_for_to_be_available_in_the_catalog() -> None:
    catalog = sdk_payloads.fake_model_catalog(["composer-2.5"])  # no auto-smart
    with pytest.raises(ValueError, match="Router"):
        resolve_profile("router-balanced", catalog=catalog)
```

- [ ] **Step 1:** Write the four test modules. All fail.
- [ ] **Step 2:** Implement `watchdog.py` first — it is a dependency of the gateway and the least entangled.
- [ ] **Step 3:** Implement `probe.py` with `build_probe_options()` split out as a pure-ish function so it is testable without a live client.
- [ ] **Step 4:** Implement `gateway.py`. `send_turn(prompt, force=False)` builds `SendOptions(local=LocalSendOptions(force=force))` when local, catches `CursorAgentError` into `signals_from_exception`, tees the stream, and always re-asserts the active profile after any one-off override (the sticky-override problem). Add `test_profile_is_reasserted_after_a_one_off_escalation`.
- [ ] **Step 5:** Implement `catalog.py`, always passing `cwd=` on local list/get and `workspace=` on the bridge launch, and refusing to resume from a mismatched cwd without `allow_cwd_change`.
- [ ] **Step 6:** Implement `models.py` and `usage.py`, with `billed_cost_usd()` returning `None` (never `0.0`) when `AgentUsage.cost is None`.
- [ ] **Step 7:** `pytest tests/infrastructure -v --cov=cursorloop.infrastructure --cov-fail-under=85` green.
- [ ] **Step 8:** Commit: `feat(infra): add the Cursor agent gateway, capacity probe, stall watchdog, and catalogs`

---

## Task 14: `infrastructure/agent/hooks.py` — managed autonomy hooks

**Files:**
- Create: `src/cursorloop/infrastructure/agent/hooks.py`
- Create: `tests/infrastructure/test_hooks_manager.py`

**Interfaces:**
- `ManagedHooks(workspace, state_dir)` implementing `HookManager`: `install()`, `restore() -> bool`, `is_installed()`, plus `diff()` for the CLI.

**Mechanism:** write scripts to `.cursorloop/hooks/`; deep-merge cursorloop's entries by **appending** to each event array in `.cursor/hooks.json`; record SHA-256 of the original bytes and the merged bytes in `.cursorloop/state.json`; restore only if the on-disk hash still matches what we wrote.

**Test snippet:**

```python
# tests/infrastructure/test_hooks_manager.py
import json
from pathlib import Path

from cursorloop.infrastructure.agent.hooks import ManagedHooks


def test_install_appends_and_never_replaces_existing_entries(tmp_path: Path) -> None:
    hooks_file = tmp_path / ".cursor" / "hooks.json"
    hooks_file.parent.mkdir(parents=True)
    hooks_file.write_text(
        json.dumps({"version": 1, "hooks": {"afterFileEdit": [{"command": "./fmt.sh"}]}})
    )

    ManagedHooks(workspace=tmp_path, state_dir=tmp_path / ".cursorloop").install()

    merged = json.loads(hooks_file.read_text())
    assert {"command": "./fmt.sh"} in merged["hooks"]["afterFileEdit"]
    assert merged["hooks"]["preToolUse"]


def test_restore_returns_the_original_bytes_exactly(tmp_path: Path) -> None:
    hooks_file = tmp_path / ".cursor" / "hooks.json"
    hooks_file.parent.mkdir(parents=True)
    original = json.dumps({"version": 1, "hooks": {"afterFileEdit": [{"command": "./fmt.sh"}]}})
    hooks_file.write_text(original)

    manager = ManagedHooks(workspace=tmp_path, state_dir=tmp_path / ".cursorloop")
    manager.install()
    assert manager.restore() is True
    assert hooks_file.read_text() == original


def test_a_user_edit_during_the_run_wins_and_restore_declines(tmp_path: Path) -> None:
    """We hash what we wrote. If the on-disk bytes changed, the user edited the
    file mid-run — their edit wins, we log loudly and leave it alone."""
    hooks_file = tmp_path / ".cursor" / "hooks.json"
    hooks_file.parent.mkdir(parents=True)
    hooks_file.write_text(json.dumps({"version": 1, "hooks": {}}))

    manager = ManagedHooks(workspace=tmp_path, state_dir=tmp_path / ".cursorloop")
    manager.install()
    hooks_file.write_text(json.dumps({"version": 1, "hooks": {"stop": [{"command": "./mine.sh"}]}}))

    assert manager.restore() is False
    assert "mine.sh" in hooks_file.read_text()


def test_install_when_no_hooks_file_exists_creates_one_and_removes_it_on_restore(
    tmp_path: Path,
) -> None:
    manager = ManagedHooks(workspace=tmp_path, state_dir=tmp_path / ".cursorloop")
    manager.install()
    assert (tmp_path / ".cursor" / "hooks.json").exists()
    assert manager.restore() is True
    assert not (tmp_path / ".cursor" / "hooks.json").exists()


def test_generated_scripts_never_exit_2(tmp_path: Path) -> None:
    """Exit 2 blocks the action. cursorloop's hooks exist to ALLOW, so none of
    our scripts may ever use it — and any other non-zero exit fails open,
    which is the correct failure direction for autonomy."""
    manager = ManagedHooks(workspace=tmp_path, state_dir=tmp_path / ".cursorloop")
    manager.install()
    for script in (tmp_path / ".cursorloop" / "hooks").glob("*.sh"):
        assert "exit 2" not in script.read_text()
```

- [ ] **Step 1:** Write `tests/infrastructure/test_hooks_manager.py`. All fail.
- [ ] **Step 2:** Implement `ManagedHooks`, generating one small POSIX shell script per managed event that reads stdin, emits `{"permission":"allow"}` (or the preamble injection for `beforeSubmitPrompt`, or the final-text capture for `stop`), and exits `0`.
- [ ] **Step 3:** Store `{"hooks_original_sha256", "hooks_merged_sha256", "hooks_original_path", "hooks_existed"}` in the state store.
- [ ] **Step 4:** Add `mode=0o700` on generated scripts and `bandit` clean (no `shell=True`, no world-writable files).
- [ ] **Step 5:** `pytest tests/infrastructure/test_hooks_manager.py -v` green; `bandit -q -r src/cursorloop` clean.
- [ ] **Step 6:** Commit: `feat(infra): manage .cursor/hooks.json autonomy fragment with hash-verified restore`

---

## Task 15: Supporting infrastructure — logging, redaction, state, lock, audit, config, rundir, notify

**Files:**
- Create: `src/cursorloop/infrastructure/{clock,logging,redact,audit,state,lock,config,rundir,notify,events,progress,state_bus,control}.py`
- Create: `tests/infrastructure/test_redact.py`, `test_state.py`, `test_lock.py`, `test_config.py`

**Test snippet:**

```python
# tests/infrastructure/test_redact.py
from cursorloop.infrastructure.redact import redact_event


def test_cursor_api_keys_are_scrubbed_by_pattern_not_just_by_key_name() -> None:
    """Cursor's fixed crsr_ prefix makes a pattern scrub genuinely effective —
    which matters because debug logging is a stated requirement and this tool
    handles credentials by design."""
    event = {"message": "auth failed for crsr_abcdefghijklmnopqrstuvwxyz012345"}
    assert "crsr_abcdefghij" not in redact_event(None, "info", event)["message"]


def test_known_secret_keys_are_scrubbed() -> None:
    event = {
        "api_key": "crsr_x",
        "CURSOR_API_KEY": "crsr_y",
        "Authorization": "Bearer crsr_z",
        "client_secret": "s",
        "safe": "keep me",
    }
    scrubbed = redact_event(None, "info", event)
    assert scrubbed["safe"] == "keep me"
    for key in ("api_key", "CURSOR_API_KEY", "Authorization", "client_secret"):
        assert scrubbed[key] == "***"


def test_no_anthropic_key_patterns_are_referenced() -> None:
    import inspect

    from cursorloop.infrastructure import redact

    assert "sk-ant" not in inspect.getsource(redact)
```

```python
# tests/infrastructure/test_config.py
from cursorloop.infrastructure.config import load_config


def test_only_cursorloop_and_cursor_env_vars_are_read(monkeypatch) -> None:
    monkeypatch.setenv("ANTHROPIC_API_KEY", "should-be-ignored")
    monkeypatch.setenv("CURSOR_API_KEY", "crsr_real")
    monkeypatch.setenv("CURSORLOOP_MAX_WAIT", "3600")
    config = load_config()
    assert config.api_key == "crsr_real"
    assert config.max_wait_seconds == 3600
    assert "ANTHROPIC_API_KEY" not in config.observed_env


def test_billing_lexicon_is_overridable_from_the_environment(monkeypatch) -> None:
    monkeypatch.setenv("CURSORLOOP_BILLING_LEXICON", "wallet_empty,no_funds")
    assert load_config().billing_terms == ("wallet_empty", "no_funds")
```

- [ ] **Step 1:** Write the four test modules. All fail.
- [ ] **Step 2:** Implement `redact.py` (structlog processor: key-name set + `crsr_[A-Za-z0-9]{16,}` pattern), `logging.py` (JSON to file, human to console, bound `run_id`/`agent_id`/`phase`/`event_type`, redaction processor installed first).
- [ ] **Step 3:** Implement `state.py` (`.cursorloop/state.json` with atomic write-then-rename), `rundir.py` (`.cursorloop/runs/<run_id>/`), `audit.py` (JSONL append, nothing lost), `lock.py` (per-agent advisory lock under `.cursorloop/locks/`).
- [ ] **Step 4:** Implement `config.py` reading `CURSORLOOP_*` and `CURSOR_API_KEY` only, with `tomllib` for the config file (3.12 stdlib — no `tomli` dependency).
- [ ] **Step 5:** Implement `clock.py`, `notify.py`, `events.py`, `progress.py`, `state_bus.py`, `control.py`.
- [ ] **Step 6:** `pytest tests/infrastructure -v --cov=cursorloop.infrastructure --cov-fail-under=85` green.
- [ ] **Step 7:** Commit: `feat(infra): add logging, redaction, run state, locking, audit, and config adapters`

---

## Task 16: `bootstrap.py` and the `run` / `resume` CLI

**Files:**
- Create: `src/cursorloop/bootstrap.py`
- Create: `src/cursorloop/cli/{app,asyncio,render}.py`
- Create: `src/cursorloop/cli/commands/{run,resume,agents,models,usage,whoami,hooks,doctor}.py`
- Create: `tests/cli/test_run_command.py`, `tests/cli/test_app.py`

**Interfaces:**
- `bootstrap.build_runner(config) -> AutonomousRunner`; `bootstrap.build_catalog(config)`; the test-agent gate.
- `cli/asyncio.py`'s `@async_command`: single `anyio.run()` bridge, SIGINT/SIGTERM → graceful drain, `CursorAgentError` → stable exit codes.

**Exit codes:** `0` complete; `1` failed (blocked / budget / config fault); `2` usage error (Typer); `3` authentication failed; `4` max wait exceeded; `130` interrupted with graceful drain.

**Test snippet:**

```python
# tests/cli/test_run_command.py
from typer.testing import CliRunner

from cursorloop.cli.app import app

runner = CliRunner()


def test_run_help_documents_the_never_block_flags() -> None:
    result = runner.invoke(app, ["run", "--help"])
    assert result.exit_code == 0
    for flag in ("--turn-timeout", "--stall-timeout", "--max-wait", "--managed-hooks"):
        assert flag in result.stdout


def test_test_agent_gate_requires_both_env_vars(monkeypatch, tmp_path) -> None:
    """A scripted agent must never be reachable by setting one variable —
    especially not by an env var leaking into a real user's shell."""
    script = tmp_path / "script.json"
    script.write_text('{"probes": [], "turns": []}')
    monkeypatch.setenv("CURSORLOOP_TEST_AGENT_SCRIPT", str(script))
    monkeypatch.delenv("CURSORLOOP_ALLOW_TEST_AGENT", raising=False)

    result = runner.invoke(app, ["run", "--plan", str(tmp_path / "plan.md")])
    assert result.exit_code != 0
    assert "CURSORLOOP_ALLOW_TEST_AGENT" in result.stdout


def test_version_flag() -> None:
    result = runner.invoke(app, ["--version"])
    assert result.exit_code == 0
    assert "cursorloop" in result.stdout


def test_authentication_failure_exits_3(monkeypatch, tmp_path) -> None:
    plan = tmp_path / "plan.md"
    plan.write_text("- [ ] do a thing\n")
    monkeypatch.setenv("CURSORLOOP_ALLOW_TEST_AGENT", "1")
    monkeypatch.setenv("CURSORLOOP_TEST_AGENT_SCRIPT", str(_auth_failure_script(tmp_path)))
    result = runner.invoke(app, ["run", "--plan", str(plan)])
    assert result.exit_code == 3
```

- [ ] **Step 1:** Write `tests/cli/test_run_command.py` and `tests/cli/test_app.py`. All fail.
- [ ] **Step 2:** Implement `cli/asyncio.py` — the single `@async_command` bridge with signal handlers requesting graceful drain (finish the in-flight turn, persist state, restore hooks, close the agent and client) and `CursorAgentError` → exit-code translation.
- [ ] **Step 3:** Implement `bootstrap.py`, wiring every adapter into its port, owning the `AsyncClient.launch_bridge(workspace=...)` lifetime, and gating the scripted test agent on **both** env vars (fail loudly if the script is set without the allow flag).
- [ ] **Step 4:** Implement `infrastructure/agent/scripted.py` — `load_agent_script(path) -> AgentScript`, `ScriptedAgentGateway`, `ScriptedCapacityProbe`, JSON schema `{"probes": [TurnSignalsDict...], "turns": [TurnDict...]}` with optional ISO `resets_at`.
- [ ] **Step 5:** Implement `cli/app.py` and the eight commands, each thin: parse, call a use case, render. Any `if/elif` deciding what a rate-limit response *means* in a CLI module is a bug — that belongs in `domain/classify.py`.
- [ ] **Step 6:** `pytest tests/cli -v --cov=cursorloop.cli --cov-fail-under=85` green; `pytest` (full suite) green; `lint-imports` green.
- [ ] **Step 7:** Commit: `feat(cli): wire the composition root and ship run, resume, agents, models, and hooks commands`

---

## Task 17: `doctor` — fail fast before a multi-hour run

**Files:**
- Create: `src/cursorloop/infrastructure/doctor_env.py`
- Create: `src/cursorloop/application/usecases/doctor.py`
- Create: `src/cursorloop/cli/commands/doctor.py`
- Create: `tests/infrastructure/test_doctor_env.py`

**Checks, each pass/warn/fail with a remedy line:**

| Check | Fails when |
|---|---|
| `CURSOR_API_KEY` present | unset |
| `Cursor.me()` succeeds | key invalid or revoked |
| `cursor-sdk-bridge --help` runs | the bundled bridge binary is missing or blocked |
| `Cursor.models.list()` contains the selected model | the profile's id is not in the account's catalog |
| Router availability when a `router-*` preset is selected | `auto-smart` absent or `optimize_for` value not allowed |
| MCP OAuth readiness | a configured server has no saved login (**fatal for an unattended run**) |
| Service-account key + MCP OAuth | such keys cannot fall back to user auth |
| `setting_sources` implications | reports exactly what `project`/`user` would load — skills **and** MCP together |
| Git repository + not root | autonomy guardrails |
| Managed hooks state | a stale merged `hooks.json` from a crashed run |
| Cloud run + uncommitted `.cursor/hooks.json` | cloud agents read hooks from the repo |
| `.cursorloop/` git-ignored | run state contains prompts and transcripts |

**Test snippet:**

```python
# tests/infrastructure/test_doctor_env.py
from cursorloop.infrastructure.doctor_env import check_mcp_oauth_readiness


def test_an_mcp_server_needing_oauth_is_a_fatal_finding(tmp_path) -> None:
    """The SDK can reuse a login saved by the Cursor app but cannot open a
    browser to sign you in. Discovering this mid-run is how an unattended run
    dies at 3am; discovering it in doctor is how it doesn't."""
    (tmp_path / ".cursor").mkdir()
    (tmp_path / ".cursor" / "mcp.json").write_text(
        '{"mcpServers": {"linear": {"url": "https://mcp.linear.app/mcp"}}}'
    )
    findings = check_mcp_oauth_readiness(workspace=tmp_path, saved_logins=frozenset())
    assert [f.name for f in findings if f.level == "fail"] == ["mcp-oauth:linear"]


def test_a_saved_login_clears_the_finding(tmp_path) -> None:
    (tmp_path / ".cursor").mkdir()
    (tmp_path / ".cursor" / "mcp.json").write_text(
        '{"mcpServers": {"linear": {"url": "https://mcp.linear.app/mcp"}}}'
    )
    findings = check_mcp_oauth_readiness(workspace=tmp_path, saved_logins=frozenset({"linear"}))
    assert all(f.level != "fail" for f in findings)


def test_service_account_keys_cannot_fall_back_to_user_auth(tmp_path) -> None:
    (tmp_path / ".cursor").mkdir()
    (tmp_path / ".cursor" / "mcp.json").write_text(
        '{"mcpServers": {"linear": {"url": "https://mcp.linear.app/mcp"}}}'
    )
    findings = check_mcp_oauth_readiness(
        workspace=tmp_path, saved_logins=frozenset({"linear"}), is_service_account=True
    )
    assert any(f.level == "fail" for f in findings)


def test_doctor_never_prints_mcp_env_or_headers(tmp_path) -> None:
    (tmp_path / ".cursor").mkdir()
    (tmp_path / ".cursor" / "mcp.json").write_text(
        '{"mcpServers": {"gh": {"command": "npx", "env": {"GITHUB_TOKEN": "ghp_secret"}}}}'
    )
    rendered = "\n".join(
        f.detail for f in check_mcp_oauth_readiness(workspace=tmp_path, saved_logins=frozenset())
    )
    assert "ghp_secret" not in rendered
```

- [ ] **Step 1:** Write `tests/infrastructure/test_doctor_env.py`. All fail.
- [ ] **Step 2:** Implement `doctor_env.py` with a `Finding(name, level, detail, remedy)` value object and one function per check.
- [ ] **Step 3:** Implement the use case and the CLI command, with `--json` output and a non-zero exit when any finding is `fail`.
- [ ] **Step 4:** Add `cursorloop doctor --explain-error <payload.json>` re-running `classify()` offline against a captured payload, so a misclassification report is reproducible without a live account.
- [ ] **Step 5:** `pytest tests/infrastructure/test_doctor_env.py tests/cli -v` green.
- [ ] **Step 6:** Commit: `feat(cli): add doctor preflight checks including MCP OAuth readiness`

---

## Task 18: M3 completion — control, waiting UX, and the system harness

**Files:**
- Create: `src/cursorloop/cli/commands/{stop,prompt,status,logs,watch,runs,savepoints,unwind,snapshot_cmd,reset}.py`
- Create: `src/cursorloop/infrastructure/{git_savepoints,snapshot}.py`
- Create: `tests/live/system/{conftest.py,test_matrix_inprocess.py,test_subprocess_smoke.py}`
- Create: `tests/live/fixtures/agent_scripts/{done.json,credits_then_available.json,window_far_future.json,stall_then_recover.json}.json`

**Test snippet:**

```python
# tests/live/system/test_matrix_inprocess.py
import pytest

pytestmark = pytest.mark.system


def test_credits_exhaustion_then_top_up_resumes_with_real_adapters(system_env) -> None:
    """Real FS/git/control/audit adapters + a scripted agent + FakeClock. This
    is the end-to-end proof of the founding invariant, with no tokens spent and
    no wall-clock seconds burned."""
    result = system_env.run(script="credits_then_available.json")
    assert result.exit_code == 0
    events = system_env.audit_events()
    assert any(e["event_type"] == "entered_credits_exhausted" for e in events)
    assert any(e["event_type"] == "capacity_restored" for e in events)
    assert system_env.sleeper.real_sleep_calls == 0


def test_stop_mid_wait_drains_gracefully_and_exits_130(system_env) -> None:
    result = system_env.run(script="window_far_future.json", stop_after_seconds=1)
    assert result.exit_code == 130
    assert system_env.state()["phase"] == "WAITING"
    assert system_env.hooks_restored() is True


def test_max_wait_exceeded_exits_4_with_a_named_reason(system_env) -> None:
    result = system_env.run(script="window_far_future.json", max_wait="60s")
    assert result.exit_code == 4
    assert "max wait exceeded" in result.stdout
```

- [ ] **Step 1:** Write `tests/live/system/conftest.py` composing real `RunDirectory`/control/events/audit/git/bus adapters with the scripted gateway and `FakeClock`/`FakeSleeper`.
- [ ] **Step 2:** Write the agent script fixtures and `test_matrix_inprocess.py`. All fail.
- [ ] **Step 3:** Implement the ten control commands, each backed by `usecases/run_control.py` and the file-based control channel under `.cursorloop/runs/<run_id>/control/`.
- [ ] **Step 4:** Implement `git_savepoints.py` and `snapshot.py` (ported from the blueprint — vendor-independent).
- [ ] **Step 5:** Write `test_subprocess_smoke.py` proving CLI wiring end-to-end with the allow+script env pair set: complete → 0, stop mid-wait → 130, ops in `--help`.
- [ ] **Step 6:** `pytest -m system -v` green; `pytest` (default, which skips `live` and `system`) still green.
- [ ] **Step 7:** Commit: `feat(cli): add mid-run control commands and the deterministic system-live harness`

---

## Task 19 *(M4 sketch)*: Cloud Agents REST surface

**Files:**
- Create: `src/cursorloop/infrastructure/api/{spec,binder,gateway,registry}.py`
- Create: `src/cursorloop/infrastructure/api/cloud-agents-openapi.yaml` (vendored, digest-pinned)
- Create: `src/cursorloop/cli/commands/cloud.py`
- Create: `tests/infrastructure/test_api_drift.py`, `tests/cli/test_api_commands.py`
- Create: `.github/workflows/api-drift.yml`
- Create: `docs/architecture/decisions/0006-cloud-agents-rest-surface.md`

- [ ] **Step 1:** Vendor the published OpenAPI document, record its SHA-256 in `registry.py`, and write `test_vendored_spec_digest_matches`.
- [ ] **Step 2:** Implement `spec.py` (load + digest assert) and `binder.py` (operation → Click command; path/scalar params become typed options; bodies go to `--json` / `--json-file` with `@path` inlining).
- [ ] **Step 3:** Implement `gateway.py` — `httpx` with Bearer auth, the shared redaction processor, and `respx`-backed tests.
- [ ] **Step 4:** Write the drift gate: every operation in the vendored spec has a registered command, and the operation count matches a committed baseline so **removals** are caught too. Verify it by deliberately hiding one operation and confirming CI fails.
- [ ] **Step 5:** Add `.github/workflows/api-drift.yml` — a scheduled job re-fetching the published spec and failing on a digest difference.
- [ ] **Step 6:** Implement `cloud.py` (`cloud run`, plus archive/unarchive/delete/artifacts) over the SDK client where it already wraps the endpoint, and over the generated surface where it does not.
- [ ] **Step 7:** Write ADR-0006 recording either the generated surface **or** the documented deferral (only `GET /v1/me`, `GET /v1/models`, agent create/get/cancel, explicitly labelled partial), whichever the milestone concludes and why.
- [ ] **Step 8:** Commit: `feat(api): generate the Cloud Agents REST surface from a pinned OpenAPI spec`

---

## Task 20 *(M5 sketch)*: CLI-fallback adapter, stream UI, docs, agent surfaces

**Files:**
- Create: `src/cursorloop/infrastructure/agent/cli_fallback.py`
- Create: `src/cursorloop/infrastructure/stream_ui/app.py`
- Create: `src/cursorloop/cli/man_page.py`
- Create: `docs/{index,getting-started/*,guides/*,architecture/*,reference/*,contributing/*}.md`, `mkdocs.yml`
- Create: `.cursor/skills/cursorloop-*/SKILL.md` (8), `.cursor/rules/cursorloop-*.mdc` (8), `.claude/skills/cursorloop-*/SKILL.md` (8), `.agents/skills/cursorloop-*/SKILL.md` (8)
- Create: `docs/architecture/decisions/0001…0010`

- [ ] **Step 1:** Implement `cli_fallback.py` building an argv list (never `shell=True`) for `agent -p --force --trust --approve-mcps --output-format stream-json --stream-partial-output --model <id> --workspace <cwd>`, parsing `stream-json` into the same `TurnSignals`/`TurnOutcome` shapes.
- [ ] **Step 2:** Run the **contract suite** against all three `AgentGateway` implementations — scripted, SDK, CLI-fallback — proving the port abstraction rather than asserting it.
- [ ] **Step 3:** Implement the Textual stream UI fed from `on_delta`/`on_step`, and `cursorloop watch`.
- [ ] **Step 4:** Write the eight ADRs listed in the roadmap (§15), following the `NNNN-kebab-case-title.md` / Status / Context / Decision / Consequences format exactly.
- [ ] **Step 5:** Write the docs site: getting-started (installation, quickstart, configuration), guides (autonomous runs, rate limits and credits, never-blocking, completion detection, model profiles, logging and observability, live testing, cloud agents), architecture (overview, domain model, ports and adapters, run-loop state machine), reference (CLI, generated API via `mkdocstrings`), contributing (development, testing, documentation, release process).
- [ ] **Step 6:** Write the four mirrored agent surfaces. **When procedural guidance changes, all four trees change in the same PR** — Cursor loads `.cursor/skills/` natively and also reads `.claude/skills/` and `.agents/skills/` for compatibility, so drift is user-visible.
- [ ] **Step 7:** Implement `man_page.py` and `cursorloop --man`.
- [ ] **Step 8:** `mkdocs build --strict` green; `pipx install .` resolves the `cursorloop` entry point on macOS and Linux; `--help` and `--man` render; `bandit` and `pip-audit` clean.
- [ ] **Step 9:** Commit (one per step group): `feat(infra): add the agent CLI fallback gateway`, `feat(cli): add the Textual stream UI and watch command`, `docs: publish the cursorloop documentation site and ADRs`, `docs: mirror agent skills across Cursor, Claude, and Codex trees`

---

## Verification checklist

Run before declaring any milestone done.

- [ ] Unit + property suites green, with the simulated multi-day wait doing **zero** wall-clock sleeping.
- [ ] Add a `domain → infrastructure` import; confirm `lint-imports` rejects it. Add `import anthropic`; confirm the no-Anthropic contract rejects it. Revert both.
- [ ] End-to-end plan-file run in a scratch git repo: completes, exits 0, audit log shows the parsed verdict and the effective `run.model` per turn.
- [ ] Never-block: a plan explicitly instructing the model to ask a clarifying question **completes instead of hanging**.
- [ ] Never-block: a synthetic wedged local run is cleared by `local.force=True` after the watchdog cancels it.
- [ ] Limits without a real limit: a scripted gateway emits a retryable `RateLimitError` with `retry_after`, then a non-retryable one with a billing code; the first schedules a bounded probe, the second **never** schedules a deadline-based sleep.
- [ ] Resume: kill the process mid-wait, re-run, confirm the same agent resumes from `.cursorloop/state.json` with the **full** option set re-applied.
- [ ] Hooks: crash mid-run, then `cursorloop reset`; confirm `.cursor/hooks.json` is restored byte-for-byte, and that a user edit during the run is preserved instead.
- [ ] Credit top-up, live (opportunistic): when a real exhaustion occurs, top up mid-wait and confirm resumption on the next probe rather than at a window boundary. Capture the real payload as a golden fixture and retire the synthetic one.
- [ ] Drift gate (M4): hide one operation from discovery; confirm CI fails.
- [ ] `pipx install .` on macOS and Linux; `cursorloop --help` renders.

## Spec coverage

| Roadmap section | Tasks |
|---|---|
| Onion architecture + import contracts | 1 |
| Capacity ADT + fault union | 2 |
| `Retry-After` parsing + billing lexicon | 3 |
| Classifier ordering + the adversarial credits case | 4 |
| Adaptive waiting + probe scheduling | 5 |
| Completion: verdict block, marker, empty-turn, plan reconciliation | 6 |
| Budget (tokens-hard / dollars-best-effort), model profiles, Grok-as-profile | 7 |
| Run-loop state machine + capacity-outranks-verdict | 8 |
| Ports, DTOs, fakes | 9 |
| Runner, credit-top-up recovery, notification on entry | 10 |
| One options builder for create + resume | 11 |
| SDK translation, both failure channels, single-pass tee | 12 |
| Gateway, probe, stall watchdog, catalogs, usage | 13 |
| Managed `.cursor/hooks.json` never-block policy | 14 |
| Logging, redaction, state, lock, audit, config | 15 |
| Composition root, `run`/`resume` CLI, exit codes, test-agent gate | 16 |
| `doctor`, MCP OAuth fail-fast, `--explain-error` | 17 |
| Mid-run control + system-live harness | 18 |
| Cloud Agents REST surface + drift gate (M4) | 19 |
| CLI fallback, stream UI, docs, ADRs, agent surfaces (M5) | 20 |
