# codexloop Implementation Plan (M1–M5)

> **For agentic workers:** REQUIRED SUB-SKILL: use `superpowers:executing-plans`
> (inline) or `subagent-driven-development`. Steps use checkbox (`- [ ]`) syntax
> for tracking. Every task is TDD: **write the failing test first**, then the
> implementation, then run the named verification command until green.

**Goal:** Ship `codexloop` — an onion-architected, autonomous OpenAI Codex
session runner that never blocks on a human and never treats a billing wall
(`insufficient_quota`) as a waitable rate-limit window — plus a generated
OpenAI REST CLI surface. M1–M3 are specified task-by-task; M4–M5 are sketched at
task granularity and expanded when M3 lands.

**Architecture:** Strict onion. `domain/` is pure stdlib and holds every
capacity/completion/waiting decision as a total function over value objects.
`application/` declares `Protocol` ports and orchestrates. `infrastructure/`
drives the `codex` binary as a supervised subprocess (`codex exec --json`),
parses its JSONL, and optionally speaks the app-server JSON-RPC protocol.
`cli/` is Typer. `bootstrap.py` is the only module that sees every layer.
Contracts are enforced by `import-linter`, not by review.

**Tech Stack:** Python 3.12+, `openai` SDK (infrastructure only), `codex` CLI
via `anyio` subprocess, `typer`, `anyio`, `structlog`, `textual`, `pytest` +
`pytest-cov` + `pytest-asyncio` + `hypothesis`, `ruff`, `mypy --strict`,
`import-linter`, `bandit`, `pip-audit`, `mkdocs-material`.

**Design inputs (read before starting):**
- [`../../plans/architecture-and-roadmap.md`](../../plans/architecture-and-roadmap.md) — the design of record
- [`../../plans/research-notes.md`](../../plans/research-notes.md) — every vendor fact, with citations and confidence levels

---

## Global Constraints

- **Onion intact.** `domain/` imports stdlib only. `application/` imports
  `domain` only. `infrastructure/` is the only layer importing `openai`,
  `anyio`, `structlog`, `textual`. Only `bootstrap.py` sees every layer.
  `lint-imports` must be green after every task.
- **No `anthropic`, no `claude-agent-sdk`, no `claudeloop`** — anywhere, in any
  form, including in comments-as-copied-code. A CI test enforces this.
- **`QuotaExhausted` has no reset field.** Not "should not be given one" — the
  dataclass has no such field, so no future edit can schedule a wake-up for a
  billing wall.
- **Body first, status second.** Classification branches on `error.code` /
  `error.type` before `http_status`. HTTP 429 alone never decides anything.
- **A capacity rejection outranks a completion claim**, always.
- **TDD, strictly.** Failing test first. No implementation without a test that
  fails for the right reason first.
- **Fakes over mocks** for ports. `FakeClock` / `FakeSleeper` mean no test ever
  sleeps in wall-clock time — a simulated 7-day wait runs in microseconds.
- **Coverage floors:** `domain/` 100%, `application/` 100%, `infrastructure/`
  ≥90%, `cli/` ≥85%. `# pragma: no cover` requires a written reason.
- **Never emit `--full-auto`. Never invoke bare `codex`.** Only
  `codex exec` / `codex exec resume`, with policy via `-c key=value` on both.
- **Default `addopts`:** `-m "not live and not system"`.
- **Conventional Commits**, and only commit when the user asks.
- **No wall-clock `sleep()` in any test.** If a test needs time to pass, it
  advances `FakeClock`.

---

## Milestone M1 — pure core (no vendor dependency)

Nothing in M1 imports `openai` or spawns a process. The whole milestone is
value objects and total functions, which is what makes 100% coverage honest.

### Task 1: Repository skeleton and quality gates

**Files:**
- Create: `pyproject.toml`, `.pre-commit-config.yaml`, `.gitignore`,
  `.editorconfig`, `LICENSE`, `README.md` (already present — extend),
  `src/codexloop/__init__.py`, `src/codexloop/py.typed`,
  `tests/__init__.py`, `.github/workflows/ci.yml`

**Interfaces:**
- Produces: an installable package exposing `codexloop.__version__`; console
  script `codexloop` (stub for now); all quality gates runnable locally.

- [ ] **Step 1:** Write `tests/test_packaging.py` asserting
      `codexloop.__version__` is a PEP 440 string, that `src/codexloop/py.typed`
      exists, and that `importlib.metadata.version("codexloop")` resolves. Run
      it — it fails (no package).
- [ ] **Step 2:** Write `tests/test_no_vendor_leak.py`: no `anthropic`,
      `claude_agent_sdk`, `claude-agent-sdk`, or `claudeloop` appears in (a) any
      `import`/`from` statement under `src/`, (b) `pyproject.toml`
      dependencies, (c) installed distribution metadata. Fails only if someone
      breaks it — write it now so it can never be forgotten later.
- [ ] **Step 3:** Author `pyproject.toml`: `name = "codexloop"`,
      `requires-python = ">=3.12"`, deps `typer`, `structlog`, `anyio`,
      `openai`, `textual`; dev/docs extras; `[project.scripts] codexloop =
      "codexloop.cli.app:main"`; ruff (`line-length = 100`, select
      `E,F,I,UP,B,SIM,C4`, `target-version = "py312"`, bugbear
      `extend-immutable-calls` for Typer); mypy `strict = true`; pytest
      `addopts = '-m "not live and not system"'` and markers `live`, `paid`,
      `system`; coverage `branch = true`.
- [ ] **Step 4:** Add the three `import-linter` contracts — "Onion layering",
      "Infrastructure only reachable from bootstrap", **and "Domain is pure"**
      (forbidding `openai`, `anyio`, `structlog`, `typer`, `textual`, `httpx`
      from `codexloop.domain`).
- [ ] **Step 5:** Wire `.pre-commit-config.yaml` (ruff, ruff-format,
      mypy, lint-imports, Conventional Commits `commit-msg` hook) and
      `ci.yml` running the full gate set on 3.12 and 3.13, macOS and Linux.
- [ ] **Step 6:** `pip install -e ".[dev]" && pytest && ruff check src tests &&
      mypy src/codexloop && lint-imports && bandit -q -r src/codexloop &&
      pip-audit` — all green.

### Task 2: Error hierarchy and the OpenAI error-code taxonomy

**Files:**
- Create: `src/codexloop/domain/__init__.py`, `src/codexloop/domain/errors.py`,
  `src/codexloop/domain/error_codes.py`
- Create: `tests/domain/__init__.py`, `tests/domain/test_error_codes.py`

**Interfaces:**
- Produces: `CodexloopError` and subclasses `ConfigurationError`,
  `CapacityError`, `AuthError`, `CodexBinaryError`, `CodexProtocolError`,
  `BudgetExceeded`, `WaitDeadlineExceeded`
- Produces: `ErrorClass` enum (`AUTH`, `QUOTA`, `WINDOW`, `THROTTLE`,
  `TRANSIENT`, `FATAL`, `UNKNOWN`) and `classify_code(code, type_) -> ErrorClass`
- Source of truth: [research-notes R1](../../plans/research-notes.md#r1--http-429-is-two-different-failures-sharing-one-status-code)

- [ ] **Step 1:** Write `test_error_codes.py` as a table test over every code in
      R1's table: `insufficient_quota`, `credit_balance_exhausted`,
      `usage_not_included` → `QUOTA`; `usage_limit_reached` → `WINDOW`;
      `rate_limit_exceeded`, `slow_down` → `THROTTLE`; `server_is_overloaded`
      → `TRANSIENT`; `invalid_api_key`, `token_expired`, `refresh_token_expired`,
      `refresh_token_reused`, `refresh_token_invalidated` → `AUTH`;
      `context_length_exceeded`, `invalid_prompt` → `FATAL`; anything else →
      `UNKNOWN`. Assert `type_` is consulted when `code` is absent, and that
      **`QUOTA` and `AUTH` sets are disjoint from every retryable set**.
- [ ] **Step 2:** Implement `errors.py` and `error_codes.py` with frozen sets.
- [ ] **Step 3:** `pytest tests/domain/test_error_codes.py -v` green; 100%
      coverage on both modules.

### Task 3: Capacity value objects

**Files:**
- Create: `src/codexloop/domain/capacity.py`
- Create: `tests/domain/test_capacity.py`

**Interfaces:**
- Produces: `RateLimitWindow(used_percent, window_minutes, resets_at)` with
  `remaining_percent`; `PlanWindows(primary, secondary, plan_type, limit_reached)`;
  the `CapacityState` union `Available | ThrottleExhausted | WindowExhausted |
  QuotaExhausted | AuthFailed | TransientBackendError`
- All members `@dataclass(frozen=True, slots=True)`

- [ ] **Step 1:** Write `test_capacity.py`. The load-bearing assertions:
      `QuotaExhausted` has **no** `resets_at` / `retry_after` field (assert via
      `dataclasses.fields`); `AuthFailed` likewise; every member is frozen and
      hashable; `remaining_percent` is `None` when `used_percent` is `None` and
      clamps to `[0, 100]` otherwise.
- [ ] **Step 2:** Implement `capacity.py`. Add `is_waitable(state) -> bool` and
      a test asserting it is `False` for exactly `QuotaExhausted` and
      `AuthFailed`.
- [ ] **Step 3:** `pytest tests/domain/test_capacity.py -v` green, 100%.

### Task 4: `TurnSignals` and classification

**Files:**
- Create: `src/codexloop/application/__init__.py`,
  `src/codexloop/application/dto.py`
- Create: `src/codexloop/domain/classify.py`
- Create: `tests/domain/test_classify.py`,
  `tests/domain/strategies.py` (Hypothesis strategies)

**Interfaces:**
- Produces: `TurnSignals` (error_code, error_type, http_status, retry_after_s,
  plan_windows, completed, failed, final_message, structured_output, usage,
  exit_code, stderr_tail), `TurnOutcome`, `ProbeResult`, `TokenUsage`
- Produces: `classify(signals: TurnSignals) -> CapacityState`
- **Note:** `TurnSignals` lives in `application/dto.py` but `classify` takes it
  as a structural argument — if that trips the "domain imports application"
  contract, move the dataclass into `domain/signals.py` and re-export from
  `dto.py`. Resolve this in Step 1, not later.

- [ ] **Step 1:** Write `test_classify.py` covering the full decision flow of
      [architecture §7](../../plans/architecture-and-roadmap.md#7-capacity-classification),
      one test per branch, in the documented order.
- [ ] **Step 2:** Write the three tie-breaker tests explicitly, because these are
      the ones a naive implementation gets wrong:
      (a) `Retry-After` present **and** `insufficient_quota` → `QuotaExhausted`
      (the header is ignored);
      (b) `completed=True` **and** a 429 error present → the capacity state wins;
      (c) `used_percent=97.0` with no error → `Available`, **not** exhausted.
- [ ] **Step 3:** Write the Hypothesis property:
      `@given(any TurnSignals whose code/type is in the QUOTA or AUTH sets)` →
      `classify()` returns a state for which `is_waitable()` is `False` and
      which exposes no reset instant. This is the single most important test in
      the repository; name it accordingly.
- [ ] **Step 4:** Write the unknown-429 property: any `http_status == 429` with
      an unrecognised code → `WindowExhausted(resets_at=None)`, never
      `QuotaExhausted`, never a terminal state.
- [ ] **Step 5:** Implement `dto.py` and `classify.py`.
- [ ] **Step 6:** `pytest tests/domain -v --cov=codexloop.domain
      --cov-fail-under=100` green.

### Task 5: Backoff and the adaptive wait policy

**Files:**
- Create: `src/codexloop/domain/backoff.py`, `src/codexloop/domain/waiting.py`
- Create: `tests/domain/test_backoff.py`, `tests/domain/test_waiting.py`

**Interfaces:**
- Produces: `backoff(attempt, *, base, ceiling, jitter_ratio, rand) -> timedelta`
  — pure, with injected randomness so it is deterministic under test
- Produces: `AdaptiveWaitPolicy(config).next_probe_at(state, now, attempt,
  deadline) -> datetime` implementing the table in
  [architecture §8](../../plans/architecture-and-roadmap.md#8-waiting-that-notices-a-top-up)

- [ ] **Step 1:** Write `test_backoff.py` with Hypothesis: monotonic
      non-decreasing in `attempt`; never exceeds `ceiling`; never negative;
      deterministic for a fixed `rand`.
- [ ] **Step 2:** Write `test_waiting.py` per state — `ThrottleExhausted` with
      and without `retry_after`, `WindowExhausted` with and without `resets_at`,
      `QuotaExhausted`, `TransientBackendError` — asserting the documented
      instant for each.
- [ ] **Step 3:** Write the three Hypothesis properties: never returns an
      instant in the past; never returns an instant beyond `deadline` (it
      returns exactly `deadline` at the boundary); always converges.
- [ ] **Step 4:** Write the guard test: for `QuotaExhausted`, the returned
      instant is derived **only** from the probe cadence — feeding a
      wildly-different `now` shifts the result by exactly that delta, proving no
      hidden reset time is in play.
- [ ] **Step 5:** Implement `backoff.py` and `waiting.py`.
- [ ] **Step 6:** `pytest tests/domain/test_backoff.py tests/domain/test_waiting.py -v` green.

### Task 6: Completion evaluation

**Files:**
- Create: `src/codexloop/domain/completion.py`
- Create: `tests/domain/test_completion.py`

**Interfaces:**
- Produces: `CompletionVerdict = Done | Continue(remaining) | Blocked(reason)`;
  `CompletionEvaluator(done_marker).evaluate(signals, capacity) -> CompletionVerdict`

- [ ] **Step 1:** Write tests for the three layers: structured output parsed →
      `Done` / `Continue` / `Blocked`; marker on its own line in the final
      message → `Done`; neither → `Continue`.
- [ ] **Step 2:** Write the precedence tests: a non-`Available` capacity state
      forces `Continue` **even when** `complete: true` is present; a marker
      appearing mid-sentence (not on its own line) does **not** complete;
      malformed structured output falls through to the marker layer rather than
      raising.
- [ ] **Step 3:** Implement `completion.py`.
- [ ] **Step 4:** `pytest tests/domain/test_completion.py -v` green.

### Task 7: Plan parsing, budgets, threads, model profiles, approval policy

**Files:**
- Create: `src/codexloop/domain/{plan,budget,session,model_profile,approval,control}.py`
- Create: `tests/domain/test_{plan,budget,session,model_profile,approval,control}.py`

**Interfaces:**
- `WorkPlan.parse(text) -> WorkPlan`, `PlanItem`
- `Budget(max_turns, max_dollars, max_wall_clock)`, `BudgetLedger.record(...)`,
  `.exceeded() -> str | None`
- `ThreadRef(thread_id, cwd, started_at, model)`,
  `SessionSelector = PlanFile | MostRecent | Explicit(thread_id)`
- `ModelEffortProfile(model, effort)` with presets `low|medium|high`
- `ApprovalPolicy` × `SandboxMode` enums + `validate(policy, sandbox) -> None`
- `ControlCommand` ADT: `Stop | Prompt(text, timing) | SetModel | SetEffort |
  SetApproval | SetSandbox | SetCwd | Snapshot | ResourceMutate`

- [ ] **Step 1:** Tests for markdown plan parsing: headings/checkboxes become
      `PlanItem`s; an empty plan raises `ConfigurationError`; round-trip of
      `remaining_work` names is stable.
- [ ] **Step 2:** Tests for budget: each cap trips independently; `exceeded()`
      names the offending budget; a ledger never goes backwards.
- [ ] **Step 3:** Tests for the approval matrix: `never` + `workspace-write` is
      the default and is valid; `danger-full-access` is valid only with an
      explicit `allow_dangerous=True`, otherwise `validate` raises. **Add a test
      asserting the default pair is exactly `(never, workspace-write)`** — this
      is the security-drift guard from risk #12.
- [ ] **Step 4:** Tests for `ControlCommand` round-tripping through a JSON dict
      (the inbox format), including an unknown command kind being rejected, not
      ignored.
- [ ] **Step 5:** Implement all six modules.
- [ ] **Step 6:** `pytest tests/domain -v` green.

### Task 8: The run-loop state machine

**Files:**
- Create: `src/codexloop/domain/loop.py`
- Create: `tests/domain/test_loop.py`

**Interfaces:**
- Produces: `RunState` enum (`Preflight`, `Running`, `Evaluating`,
  `ThrottleBackoff`, `Waiting`, `Probing`, `Stopping`, `Complete`, `Failed`)
- Produces: `Decision` ADT (`SendTurn`, `Probe`, `WaitUntil`, `BackoffUntil`,
  `Finish(success, reason)`, `Drain`)
- Produces: `RunLoopStateMachine.advance(state, outcome, now, ledger, controls)
  -> tuple[RunState, Decision]` — a **total** function

- [ ] **Step 1:** Write a transition table test covering every arrow in the
      state diagram of
      [architecture §9](../../plans/architecture-and-roadmap.md#9-the-autonomous-run-loop),
      as `(state, outcome) -> (next_state, decision)` rows.
- [ ] **Step 2:** Write the exhaustiveness test: every `(RunState,
      CapacityState)` pair produces a decision, none raise. Use Hypothesis to
      enumerate the product.
- [ ] **Step 3:** Write the terminal-state tests: `AuthFailed` from any state →
      `Failed`; `--max-wait` exceeded → `Failed` with reason `max_wait`; a
      `Stop` control from any non-terminal state → `Stopping` → exit 130;
      budget exceeded → `Failed` with the budget named.
- [ ] **Step 4:** Implement `loop.py`. Use a closed-union exhaustiveness
      `assert` in the fall-through, with the `# nosec B101` justification
      pattern (a precondition on a closed union, not a security gate).
- [ ] **Step 5:** `pytest tests/domain/test_loop.py -v` green.

### Task 9: Application ports

**Files:**
- Create: `src/codexloop/application/ports.py`
- Create: `tests/application/__init__.py`, `tests/application/fakes.py`,
  `tests/application/test_ports.py`

**Interfaces:**
- Produces `Protocol`s: `Clock`, `Sleeper`, `AgentGateway`, `CapacityProbe`,
  `ThreadCatalog`, `ProgressReporter`, `AuditLog`, `Notifier`, `Logger`,
  `RunStateStore`, `SessionLock`, `RunControl`, `RunEventSink`, `StateBus`,
  `SavePointStore`, `RunSnapshotSink`, `ApiGateway`, `RunResources`
- Produces fakes for every one of them in `tests/application/fakes.py`,
  including `FakeClock` (advanceable) and `FakeSleeper` (records requested
  instants, advances `FakeClock`, **never sleeps**)

- [ ] **Step 1:** Write `test_ports.py` asserting each fake structurally
      satisfies its `Protocol` (`isinstance` against `runtime_checkable`, or a
      `mypy`-checked assignment in a `TYPE_CHECKING` block).
- [ ] **Step 2:** Write the `FakeSleeper` test: sleeping until `T` advances
      `FakeClock` to exactly `T` and records the request; a simulated 7-day wait
      completes in a single test with zero real elapsed time.
- [ ] **Step 3:** Implement `ports.py` and `fakes.py`.
- [ ] **Step 4:** `pytest tests/application -v && lint-imports` green.

### M1 exit gate

- [ ] `pytest --cov=codexloop.domain --cov=codexloop.application --cov-fail-under=100`
- [ ] `ruff check src tests && ruff format --check src tests`
- [ ] `mypy src/codexloop` — zero errors, zero suppressions in domain/application
- [ ] `lint-imports` — all three contracts green
- [ ] `bandit -q -r src/codexloop && pip-audit`
- [ ] `pip install -e . && codexloop --version` prints
- [ ] Manual negative check: add `import openai` to a `domain/` module, confirm
      `lint-imports` fails, then revert

---

## Milestone M2 — runner parity (subprocess transport + core CLI)

### Task 10: Argv builder

**Files:**
- Create: `src/codexloop/infrastructure/__init__.py`,
  `src/codexloop/infrastructure/agent/__init__.py`,
  `src/codexloop/infrastructure/agent/argv.py`
- Create: `tests/infrastructure/__init__.py`,
  `tests/infrastructure/test_argv.py`

**Interfaces:**
- Produces: `build_exec_argv(opts) -> list[str]`,
  `build_resume_argv(thread_id | None, opts) -> list[str]`,
  `build_probe_argv(opts) -> list[str]`

- [ ] **Step 1:** Write the regression-guard tests **first**, because they are
      the reason this module exists as its own file:
      (a) resume argv **never** contains a bare `--sandbox`
      ([R5](../../plans/research-notes.md#r5--session-continuity-codex-exec-resume-rollout-files-codex_home));
      (b) exec and resume express **identical** policy via `-c key=value`;
      (c) `--full-auto` never appears in any argv;
      (d) argv[1] is always `exec` — never a bare `codex` invocation;
      (e) the prompt always follows a `--` separator;
      (f) probe argv always contains `--ephemeral` and
      `-c sandbox_mode="read-only"`.
- [ ] **Step 2:** Write a table test over the full option matrix (model, effort,
      approval, sandbox, add-dirs, output-schema, output-last-message,
      skip-git-repo-check) asserting exact argv for each.
- [ ] **Step 3:** Implement `argv.py`. Values are shell-quoted into
      `-c key="value"` form; no `shell=True` anywhere; the function returns a
      list, never a string.
- [ ] **Step 4:** `pytest tests/infrastructure/test_argv.py -v` green.

### Task 11: Fake `codex` shim (test infrastructure)

**Files:**
- Create: `tests/shim/fake_codex.py`, `tests/shim/__init__.py`
- Create: `tests/conftest.py` (fixture putting the shim first on `PATH`)
- Create: `tests/fixtures/jsonl/{clean_completion,tool_heavy,turn_failed_429_window,turn_failed_429_quota,malformed_line,huge_line,truncated_stream}.jsonl`

**Interfaces:**
- Produces: an executable shim reading `FAKE_CODEX_SCRIPT` (a fixture path) and
  `FAKE_CODEX_MODE` (`stream` | `hang` | `exit_nonzero` | `orphan_child` |
  `huge_line`), emitting the fixture to stdout and diagnostics to stderr

- [ ] **Step 1:** Author the seven JSONL fixtures by hand from the documented
      event shapes in
      [R4](../../plans/research-notes.md#r4--codex-exec---json-the-event-stream-we-can-actually-parse)
      — `thread.started`, `turn.started`, `item.*`, `turn.completed` with
      `usage`, `turn.failed` with a 429 body. Mark them as **synthetic** in a
      `README.md` beside them, and add a TODO to replace each with a real
      capture once a `codex` binary is available.
- [ ] **Step 2:** Implement the shim and the `PATH` fixture.
- [ ] **Step 3:** Write a meta-test asserting the shim itself behaves: each mode
      produces the expected stdout/stderr/exit-code shape. A broken shim
      produces confusing failures everywhere else, so it gets its own test.
- [ ] **Step 4:** `pytest tests/shim -v` green.

### Task 12: JSONL event parsing

**Files:**
- Create: `src/codexloop/infrastructure/agent/events.py`
- Create: `tests/infrastructure/test_events.py`

**Interfaces:**
- Produces: `CodexEvent` union (`ThreadStarted`, `TurnStarted`, `TurnCompleted`,
  `TurnFailed`, `ItemStarted`, `ItemCompleted`, `RateLimitsUpdated`,
  `ErrorEvent`, `UnknownEvent`) and `parse_line(str) -> CodexEvent | None`

- [ ] **Step 1:** Write tests over every fixture: the clean stream yields the
      documented event sequence; `thread.started` surfaces `thread_id`;
      `turn.completed` surfaces `usage`.
- [ ] **Step 2:** Write the forgiving-parser tests, which are the point of the
      module: an unknown `type` becomes `UnknownEvent` (never raises); a
      malformed line returns `None` and increments a counter; a line missing
      `type` returns `None`; a `turn.failed` with the error nested at any of
      `error`, `payload.error`, `item.error`, `turn.error` is found in all four
      shapes.
- [ ] **Step 3:** Write the `rate_limits` tests: `null` → `None`;
      `resets_in_seconds` → converted against an injected `now`; `resets_at`
      epoch → converted; unknown/renamed keys → `None` for that window only,
      never an exception
      ([R3](../../plans/research-notes.md#r3--codex-chatgpt-plan-windows-5-hour-primary-weekly-secondary)).
- [ ] **Step 4:** Implement `events.py`.
- [ ] **Step 5:** `pytest tests/infrastructure/test_events.py -v` green.

### Task 13: Process supervision

**Files:**
- Create: `src/codexloop/infrastructure/agent/process.py`
- Create: `tests/infrastructure/test_process.py`

**Interfaces:**
- Produces: `async run_codex(argv, *, cwd, env, timeout, max_line_bytes) ->
  ProcessResult(stdout_lines, stderr_tail, exit_code, truncated_lines)`

- [ ] **Step 1:** Write the concurrency test first: a shim that writes a large
      volume to **both** stdout and stderr completes without deadlocking. A
      sequential reader hangs here, which is exactly the bug this test exists to
      prevent.
- [ ] **Step 2:** Write the line-ceiling test: a line beyond `max_line_bytes` is
      truncated, counted, and flagged — memory does not balloon and nothing
      raises.
- [ ] **Step 3:** Write the timeout test: `FAKE_CODEX_MODE=hang` with a short
      timeout raises `CodexBinaryError` with the timeout named.
- [ ] **Step 4:** Write the orphan test: `FAKE_CODEX_MODE=orphan_child` spawns a
      grandchild; on cancellation, assert **neither** child nor grandchild
      survives (poll the process table with a bounded retry).
- [ ] **Step 5:** Write the stdin test: the child's stdin is not a TTY and reads
      return EOF immediately.
- [ ] **Step 6:** Implement `process.py` with `anyio`: concurrent stream pumps
      in a task group, `start_new_session=True` for a dedicated process group,
      `SIGTERM` → grace → `SIGKILL` on the group.
- [ ] **Step 7:** `pytest tests/infrastructure/test_process.py -v` green.

### Task 14: Translation and the exec gateway

**Files:**
- Create: `src/codexloop/infrastructure/agent/translate.py`,
  `src/codexloop/infrastructure/agent/schema.py`,
  `src/codexloop/infrastructure/agent/gateway.py`
- Create: `tests/infrastructure/test_translate.py`,
  `tests/infrastructure/test_gateway.py`

**Interfaces:**
- Produces: `to_turn_signals(events, *, exit_code, stderr_tail, now) -> TurnSignals`
- Produces: `write_output_schema(path) -> Path` emitting the completion JSON Schema
- Produces: `CodexExecGateway` implementing `AgentGateway`, recording
  `thread_id` from the first `thread.started` and resuming **by id** thereafter

- [ ] **Step 1:** Write translation tests over all seven fixtures, asserting the
      resulting `TurnSignals` for each — including that `exit_code` and
      `stderr_tail` are always populated, so a malformed stream still yields a
      classifiable outcome rather than an unexplained failure.
- [ ] **Step 2:** Write the end-to-end classification test: fixture → parse →
      translate → `classify()` → expected `CapacityState`, one row per fixture.
      This is the seam where a vendor change actually bites, so it gets an
      explicit test rather than being implied by unit coverage.
- [ ] **Step 3:** Write gateway tests against the shim: first turn uses
      `codex exec`; second turn uses `codex exec resume <thread_id>` with the
      **captured id, not `--last`**; `close()` is idempotent; a failed turn
      still returns a `TurnOutcome` rather than raising.
- [ ] **Step 4:** Write the schema test: the emitted JSON Schema validates a
      conforming verdict object and rejects a non-conforming one.
- [ ] **Step 5:** Implement `translate.py`, `schema.py`, `gateway.py`.
- [ ] **Step 6:** `pytest tests/infrastructure -v` green.

### Task 15: Generic infrastructure adapters

**Files:**
- Create: `src/codexloop/infrastructure/{clock,logging,redact,audit,config,rundir,state,lock,notify,progress,events}.py`
- Create: `tests/infrastructure/test_{logging_redact,config,rundir_state,lock}.py`

**Interfaces:**
- `SystemClock`, `AnyioSleeper`; `configure_logging(...)` → structlog with dual
  console (human + JSON) and optional file; `RedactionProcessor`;
  `JsonlAuditLog`; `load_config(...)` merging `codexloop.toml` → `CODEXLOOP_*`
  → flags; `RunDirectory` owning `.codexloop/runs/<run_id>/`;
  `FileRunStateStore`; `AdvisoryFileLock`; `CommandNotifier`

- [ ] **Step 1:** Write the redaction tests **first** and make them mean
      something: `OPENAI_API_KEY`, `CODEX_API_KEY`, `authorization`,
      `access_token`, `refresh_token`, `client_secret` are scrubbed by key; any
      value matching `sk-[A-Za-z0-9_-]{16,}` is scrubbed by pattern **even under
      an innocuous key**; scrubbing survives nesting inside dicts and lists.
- [ ] **Step 2:** Write config-precedence tests: flag beats env beats project
      toml beats user toml beats default, for one representative setting of each
      type (str, int, bool, duration, list).
- [ ] **Step 3:** Write `RunDirectory` tests: layout matches
      [architecture §13](../../plans/architecture-and-roadmap.md#13-mid-run-operator-control);
      creation is idempotent; a run id is never reused.
- [ ] **Step 4:** Write lock tests: a second acquire on the same thread id
      fails; release allows re-acquire; a stale lock from a dead pid is broken
      with a logged reason.
- [ ] **Step 5:** Implement all modules.
- [ ] **Step 6:** `pytest tests/infrastructure -v` green.

### Task 16: The autonomous runner

**Files:**
- Create: `src/codexloop/application/runner.py`,
  `src/codexloop/application/usecases/{__init__,run_plan,resume_thread,preflight,list_threads}.py`
- Create: `tests/application/test_runner.py`, `tests/application/test_usecases.py`

**Interfaces:**
- Produces: `AutonomousRunner(ctx).run(selector, plan) -> RunResult(success, reason, turns, thread_id)`

- [ ] **Step 1:** Write the happy-path test with fakes: preflight → turn → `Done`
      → exit 0, asserting the exact sequence of port calls.
- [ ] **Step 2:** Write the continuation test: `Continue` × 3 then `Done`;
      assert the continuation prompt is used from turn 2 and that
      `remaining_work` is threaded into it.
- [ ] **Step 3:** Write the budget tests: each of turns / dollars / wall-clock
      trips independently and produces `Failed` with the budget named.
- [ ] **Step 4:** Write the state-persistence test: state is written after every
      turn and a fresh runner can resume from it.
- [ ] **Step 5:** Write the drain test: a `Stop` control mid-run finishes the
      in-flight turn, writes `stop-summary.md`, and returns exit 130.
- [ ] **Step 6:** Implement `runner.py` and the use cases.
- [ ] **Step 7:** `pytest tests/application -v --cov=codexloop.application
      --cov-fail-under=100` green.

### Task 17: Bootstrap and the core CLI

**Files:**
- Create: `src/codexloop/bootstrap.py`, `src/codexloop/cli/{__init__,app,asyncio,render}.py`,
  `src/codexloop/cli/commands/{__init__,run,resume,threads,status,logs,runs}.py`
- Create: `tests/cli/__init__.py`, `tests/cli/test_app.py`

**Interfaces:**
- Produces: `build_runner(config) -> RunnerContext`; the Typer root app;
  `@async_command` bridging `anyio.run()` + signal handling + exit-code
  translation

- [ ] **Step 1:** Write CLI tests with Typer's `CliRunner`: `--version`,
      `--help`, every command's `--help` renders; `prompt` without exactly one
      timing flag exits 2.
- [ ] **Step 2:** Write the exit-code mapping test: `Done` → 0; `Failed` → 1;
      usage error → 2; soft stop → 130.
- [ ] **Step 3:** Write the bootstrap test: `build_runner` returns a context
      whose gateway satisfies `AgentGateway`, and **`--transport` selects
      between adapters without any `cli/` module importing `infrastructure/`**
      (asserted by `lint-imports`, not by inspection).
- [ ] **Step 4:** Implement `bootstrap.py`, the CLI app, the async bridge with
      SIGINT/SIGTERM → graceful drain, and the six commands.
- [ ] **Step 5:** `pytest tests/cli -v && lint-imports` green.

### M2 exit gate

- [ ] End-to-end against the shim: a markdown plan drives to `Done`, exit 0
- [ ] End-to-end with `FAKE_CODEX_MODE=orphan_child` + SIGINT: no surviving
      processes
- [ ] A plan instructing the model to ask a clarifying question still completes
      (scripted shim response)
- [ ] All gates green; coverage floors met

---

## Milestone M3 — resilient waiting

### Task 18: The exec capacity probe

**Files:**
- Create: `src/codexloop/infrastructure/agent/probe.py`
- Create: `tests/infrastructure/test_probe.py`

- [ ] **Step 1:** Write tests asserting probe argv contains `--ephemeral` and
      `sandbox_mode="read-only"`, and that a probe **never** writes to the run's
      thread (no `resume`, no thread id).
- [ ] **Step 2:** Write the outcome tests: a successful probe yields
      `Available`; a rejected probe yields the classified state; a probe that
      fails to spawn yields `TransientBackendError` rather than raising.
- [ ] **Step 3:** Implement `probe.py`.
- [ ] **Step 4:** `pytest tests/infrastructure/test_probe.py -v` green.

### Task 19: App-server rate-limit probe (optional enrichment)

**Files:**
- Create: `src/codexloop/infrastructure/appserver/{__init__,client,ratelimits}.py`
- Create: `tests/infrastructure/test_appserver.py`

**Interfaces:**
- Produces: `AppServerClient` (stdio JSON-RPC, `initialize` with
  `capabilities.experimentalApi: true` → `initialized` → call, **no
  `"jsonrpc"` key on the wire**), `read_rate_limits() -> PlanWindows | None`

- [ ] **Step 1:** Write the handshake test against a fake app-server shim,
      asserting the exact three-message sequence and the `experimentalApi`
      capability
      ([R6](../../plans/research-notes.md#r6--there-is-no-stable-codex-status---json-three-probe-strategies)).
- [ ] **Step 2:** Write the graceful-degradation tests, which matter more than
      the happy path because this surface is experimental: method-not-found →
      `None`; missing capability error → `None` + one warning log; malformed
      response → `None`; process fails to spawn → `None`; **no path raises**.
- [ ] **Step 3:** Write the guard test: `account/rateLimitResetCredit/consume`
      is **never** called by any code path (assert on the recorded method list).
- [ ] **Step 4:** Implement the client and the rate-limit reader with a bounded
      per-request timeout.
- [ ] **Step 5:** `pytest tests/infrastructure/test_appserver.py -v` green.

### Task 20: Rollout tail (last-resort enrichment)

**Files:**
- Create: `src/codexloop/infrastructure/rollout.py`
- Create: `tests/infrastructure/test_rollout.py`

- [ ] **Step 1:** Write tests over synthetic rollout files: newest
      `token_count.rate_limits` wins; malformed lines are skipped; a missing
      window degrades to `None` for that window only; no rollout → `None`.
- [ ] **Step 2:** Write the staleness test: a snapshot older than a configured
      max age is discarded rather than trusted.
- [ ] **Step 3:** Write the containment test: reading is strictly read-only and
      confined to `$CODEX_HOME`; a symlink escaping it is refused.
- [ ] **Step 4:** Implement `rollout.py`.
- [ ] **Step 5:** `pytest tests/infrastructure/test_rollout.py -v` green.

### Task 21: The composite probe and the wait loop

**Files:**
- Create: `src/codexloop/infrastructure/capacity_probe.py`
- Modify: `src/codexloop/application/runner.py`, `src/codexloop/bootstrap.py`
- Create: `tests/application/test_waiting_runner.py`

- [ ] **Step 1:** Write the composite-probe tests: app-server tried first,
      rollout second, exec always; when both enrichment sources return `None`,
      the exec result alone still produces a correct decision.
- [ ] **Step 2:** Write **the** scenario test —
      `test_resumes_when_a_human_tops_up_credit_mid_wait`: `QuotaExhausted` ×5
      then `Available`; assert the runner resumes on probe 6, that
      `FakeSleeper` was never asked to sleep past the probe cadence, and that
      the notifier fired exactly once on entry.
- [ ] **Step 3:** Write the window test: `WindowExhausted(resets_at=T)`
      schedules a probe at `min(T + grace, now + interval)`, and a simulated
      5-hour wait completes in microseconds under `FakeClock`.
- [ ] **Step 4:** Write the deadline test: `--max-wait` exceeded → exit 1 with
      reason `max_wait`, and **the run state on disk reflects the reason** so a
      later `status` explains it.
- [ ] **Step 5:** Write the unknown-code test: a scripted
      `{"code": "some_future_code", "status": 429}` produces a bounded wait and
      emits a `capacity.unknown_code` event.
- [ ] **Step 6:** Implement the composite probe and wire the wait loop.
- [ ] **Step 7:** `pytest tests/application -v` green, 100% coverage.

### Task 22: Control plane, savepoints, and the remaining CLI

**Files:**
- Create: `src/codexloop/infrastructure/{control,state_bus,git_savepoints,snapshot,doctor_env}.py`
- Create: `src/codexloop/application/usecases/{run_control,doctor}.py`
- Create: `src/codexloop/cli/commands/{stop,prompt,capacity,doctor,watch,savepoints,unwind,reset,snapshot,model_cmd,effort_cmd,approval_cmd,sandbox_cmd,cwd_cmd}.py`
- Create: `tests/infrastructure/test_control_and_savepoints.py`,
  `tests/cli/test_ops_commands.py`

- [ ] **Step 1:** Write inbox tests: a command file is picked up at the next
      boundary, applied exactly once, then archived; a malformed file is
      quarantined with a log line rather than crashing the run.
- [ ] **Step 2:** Write savepoint tests: a commit is created only when the tree
      changed after excluding `.codexloop/`; an unchanged tree is ref-tagged
      only; subjects read `chore(codexloop): turn N — …`; `unwind` refuses while
      a run is live.
- [ ] **Step 3:** Write `doctor` tests: `codex` on `PATH`; `codex --version`
      above the minimum floor; `codex login status` exit 0; required flags
      present in `codex exec --help`; which probe strategies are live; the
      active auth mode (API key vs ChatGPT plan) reported explicitly; MCP
      servers requiring OAuth named and failed fast.
- [ ] **Step 4:** Write `capacity` command tests: prints plan windows when
      available, and says so **honestly** — not silently — when unavailable.
- [ ] **Step 5:** Implement the modules and commands.
- [ ] **Step 6:** `pytest -v` full suite green.

### Task 23: System harness

**Files:**
- Create: `src/codexloop/infrastructure/agent/scripted.py`
- Modify: `src/codexloop/bootstrap.py` (test-agent gate)
- Create: `tests/live/system/{conftest,test_matrix_inprocess,test_subprocess_smoke}.py`
- Create: `tests/live/fixtures/agent_scripts/{done,window_then_done,quota_then_topup,unknown_429}.json`

- [ ] **Step 1:** Implement `ScriptedAgentGateway` / `ScriptedCapacityProbe`
      reading a JSON script, plus `resolve_test_agent_from_env()`. The gate
      requires **both** `CODEXLOOP_ALLOW_TEST_AGENT=1` **and**
      `CODEXLOOP_TEST_AGENT_SCRIPT=<path>`; a script without the allow flag is a
      hard error, never a silent fallback.
- [ ] **Step 2:** Write the in-process matrix (`-m system`) with real
      FS/git/control/events adapters + scripted agent + `FakeClock`/`FakeSleeper`.
- [ ] **Step 3:** Write the subprocess smoke test: the real `codexloop` binary
      with the scripted agent; complete → 0; stop mid-wait → 130; `--help`
      lists every ops command.
- [ ] **Step 4:** `pytest -m system -v` green; default `pytest` still skips it.

### M3 exit gate

- [ ] Simulated 7-day wait runs in microseconds, zero real sleeping
- [ ] Credit-top-up scenario resumes on the scripted probe
- [ ] `--max-wait` exits 1 with a named reason recorded on disk
- [ ] `codexloop doctor` reports auth mode and live probe strategies
- [ ] All gates green; `-m system` green

---

## Milestone M4 — generated OpenAI REST surface *(sketch)*

Expanded into full steps when M3 lands. Design:
[architecture §15](../../plans/architecture-and-roadmap.md#15-the-generated-rest-surface-m4),
[R11](../../plans/research-notes.md#r11--the-openai-python-sdk-as-the-m4-rest-surface).

### Task 24: SDK introspection
- [ ] Walk the **class** tree under `openai.resources` via `cached_property`
      descriptors — no live client, so no credentials at import time
- [ ] Emit `EndpointSpec(resource_path, method_name, signature, is_list, is_streaming)`
- [ ] Test: discovery works with `OPENAI_API_KEY` unset

### Task 25: Typer binding
- [ ] Map path + scalar params to typed options; body → `--json` / `--json-file`
      with `@path` inlining
- [ ] `--raw` / `--stream` select the raw/streaming response variants
- [ ] List methods auto-paginate with `--max-items`

### Task 26: Providers
- [ ] `--provider openai|azure|custom` with `--base-url`
- [ ] The binder reflects the **actual** surface of the selected client, rather
      than offering commands that will fail at call time

### Task 27: The drift gate
- [ ] Test asserting every discovered endpoint has a registered command
- [ ] `api_baseline.json` committed; count asserted both ways so removals are
      caught too
- [ ] Local helpers individually enumerated as bound-or-exempt
- [ ] **Verify by breaking it:** hide one SDK method from discovery, confirm CI
      fails, restore

### Task 28: `codexloop api` sub-app
- [ ] Generated sub-app mounted on the root; `--help` renders with no
      credentials present
- [ ] `docs/guides/rest-api-surface.md`

---

## Milestone M5 — app-server transport, docs, release *(sketch)*

### Task 29: App-server gateway
- [ ] `thread/start`, `thread/resume`, `turn/start` as a full `AgentGateway`
- [ ] `turn/interrupt` → true mid-turn stop; `turn/steer` → true mid-turn prompt
- [ ] Approval requests auto-answered at the protocol level (the interception
      point the exec transport does not have)
- [ ] Capability probe at startup; falls back to exec with a logged reason
- [ ] Passes the **same** system matrix as exec, or is documented as unavailable

### Task 30: Stream UI
- [ ] Textual live token view behind `--stream-ui`; `watch --replay`

### Task 31: Docs site
- [ ] `mkdocs.yml`; `docs/{index,getting-started,guides,architecture,reference,contributing}`
- [ ] ADRs 0001–0012 from
      [the seed list](../../plans/architecture-and-roadmap.md#22-adr-seed-list)
- [ ] `mkdocs build --strict` green (fails on any warning, most commonly a
      broken link)
- [ ] Roadmap pages marked with `!!! note "Roadmap"` so a reader never mistakes
      an intention for current behaviour

### Task 32: Agent surfaces
- [ ] `AGENTS.md` + `CLAUDE.md` routers (short — facts, not procedures)
- [ ] `.agents/skills/`, `.claude/skills/`, `.cursor/rules/` — the same
      procedures mirrored across all three, changed in the same PR

### Task 33: Release
- [ ] `SECURITY.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`
- [ ] release-please + Conventional Commits
- [ ] `pipx install .` verified on macOS and Linux
- [ ] PyPI publish via trusted publishing

---

## Spec coverage

| Design item | Source | Task |
|---|---|---|
| Onion layers + three import contracts | arch §3 | 1 |
| No-vendor-leak guard | arch §5 | 1 |
| OpenAI error taxonomy | R1 | 2 |
| `QuotaExhausted` has no reset field | arch §6 | 3 |
| Body-first classification | R1, arch §7 | 4 |
| Unknown-429 → bounded wait | arch §7 | 4, 21 |
| Adaptive wait, never a blind sleep | arch §8 | 5, 21 |
| Three-layer completion detection | R12, arch §12 | 6 |
| Approval × sandbox matrix + default guard | R8 | 7 |
| Run-loop state machine incl. `ThrottleBackoff` | arch §9 | 8 |
| Port list + fakes | arch §3 | 9 |
| One argv builder, `-c` on both paths | R5, arch §10 | 10 |
| Golden JSONL fixtures + fake `codex` shim | arch §20 | 11 |
| Forgiving JSONL parser | R4 | 12 |
| Plan-window normalisation (both reset forms) | R3 | 12 |
| Process supervision (deadlock, orphans, ceiling) | arch §10 | 13 |
| Resume by captured `thread_id`, not `--last` | R5 | 14 |
| Redaction + config precedence + run dir + lock | arch §17, §18 | 15 |
| Autonomous runner + budgets + drain | arch §9 | 16 |
| CLI + async bridge + exit codes | arch §14 | 17 |
| Ephemeral read-only exec probe | R6 | 18 |
| App-server rate-limit probe + never-consume guard | R6, R10 | 19 |
| Rollout tail as best-effort only | R5 | 20 |
| Composite probe + credit-top-up scenario | arch §8 | 21 |
| Control plane, savepoints, doctor, capacity | arch §13 | 22 |
| System harness with a double-gated test agent | arch §20 | 23 |
| Generated REST surface + drift gate | R11, arch §15 | 24–28 |
| App-server transport with real interrupt/steer | R10 | 29 |
| Docs, ADRs, agent surfaces, release | arch §21 | 31–33 |

---

## Definition of done (whole project)

- [ ] `pytest` green with per-layer coverage floors met
- [ ] `ruff`, `mypy --strict`, `lint-imports`, `bandit`, `pip-audit` green
- [ ] `pytest -m system` green
- [ ] The drift gate **proven** by deliberately breaking it and watching CI fail
- [ ] The onion contract proven the same way (a `domain → infrastructure` import
      is rejected; `import openai` in `domain/` is rejected)
- [ ] No `anthropic` / `claude-agent-sdk` / `claudeloop` anywhere
- [ ] `pipx install .` works on macOS and Linux; `codexloop --help` renders
- [ ] `mkdocs build --strict` green
- [ ] A real markdown plan drives a real `codex` session to completion,
      unattended, exiting 0 — and a real capacity rejection is classified
      correctly in the audit log
