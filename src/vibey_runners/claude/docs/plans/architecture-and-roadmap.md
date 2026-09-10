# Plan: claudeloop — autonomous Claude session runner + full Anthropic SDK CLI

> **Status.** This is the original approved architecture plan (milestone M1–M5). **M1 is complete** — the pure domain core described below exists at `src/claudeloop/domain/`, fully tested. M2–M5 are roadmap, not yet built. This document is preserved verbatim as the design record; see [`../architecture/overview.md`](../architecture/overview.md) for the living description of what's actually implemented, and [`decisions/`](../architecture/decisions/) for individual ADRs distilled from the reasoning below.

## Context

`claude_autoresume.py` (now [`legacy/claude_autoresume.py`](https://github.com/adammatthewsteinberger/claudeloop/blob/main/legacy/claude_autoresume.py)) is a 663-line single-file script that drives a Claude Code session to completion unattended. It shells out to `claude -p --dangerously-skip-permissions --output-format stream-json --verbose`, scrapes the stream for usage-limit signals with regexes, sleeps until a parsed reset time, and re-invokes with `--continue`/`--resume` until a done-marker string appears. It works, but it is a script: no package, no tests, no types, hand-rolled string matching against an undocumented stream format, and session discovery by globbing `~/.claude/projects/` — a path the docs explicitly warn against parsing because the format changes between releases.

The goal is to turn it into a proper pip-installable library and CLI: onion architecture, OOP, Typer, near-total coverage, extensive debug logging, security controls, and CI quality gates — covering both the **Claude Agent SDK** (the autonomous session runner) and the **Anthropic REST SDK** (full 1:1 command parity).

Four research findings reshape the design, and each removes or replaces something the current script hand-rolls:

1. **Structured rate-limit data replaces regex scraping.** The Agent SDK yields a typed `RateLimitEvent` carrying `status` (`allowed` / `allowed_warning` / `rejected`), `resets_at`, `rate_limit_type` (`five_hour` / `seven_day` / `seven_day_opus` / `seven_day_sonnet` / `overage`), `utilization`, and separate `overage_status` / `overage_resets_at` / `overage_disabled_reason`. The `allowed_warning` false positive documented at `legacy/claude_autoresume.py:89-104` becomes a field comparison instead of a heuristic.

2. **Not every 429 is waitable, and the current script cannot tell.** A real transcript captured during development contains a real rejection with `error_code: "credits_required"`, `disabled_reason: "out_of_credits"`, `can_user_purchase_credits: true` — and **no reset time**. Only a human adding credits clears it. Today the script sleeps an hour and retries forever. Because a credit top-up can also arrive *during* an ordinary window wait, blind sleeping to a far-future `resets_at` is wrong in both cases: waiting must become a **probe loop** that notices returning capacity early.

3. **Session discovery has a supported API.** `list_sessions()` / `get_session_info()` return `SDKSessionInfo` (session_id, summary, last_modified, custom_title, first_prompt, git_branch, cwd, tag, created_at) using cheap stat + head/tail reads. This replaces the fragile glob and the hand-rolled JSONL parse at `legacy/claude_autoresume.py:133-192`.

4. **`ClaudeSDKClient` survives errors; `query()` does not.** Single-shot `query()` raises a bare `Exception` *after* yielding the error result and the process exits non-zero. A streaming-input `ClaudeSDKClient` stays alive across error results, so the outer respawn-and-resume loop collapses into repeated sends on one live process.

One deliberate non-finding: the official `ant` CLI already covers all 131 REST endpoints from the same Stainless spec hash as the Python SDK. The project chose to include the REST surface anyway, so it is scoped below as a **generated** namespace with a drift gate — never hand-written, because a hand-written snapshot is silently incomplete after the next SDK release.

## Architecture

Onion, four layers, dependencies strictly inward. The point is not ceremony: it is that every hard decision (is this limit waitable? how long do we wait? is the work done?) becomes a pure function over value objects, which is what makes near-100% coverage honest rather than a mocking exercise.

```
src/claudeloop/
├── domain/              # pure. no I/O, no third-party imports, no async
│   ├── errors.py        # AutoclaudeError hierarchy
│   ├── plan.py          # WorkPlan, PlanItem  (parsed from the md handoff)
│   ├── session.py       # SessionRef, SessionSelector = PlanFile | MostRecent | Explicit
│   ├── capacity.py      # CapacityState ADT, RateLimitWindow, CreditState
│   ├── classify.py      # TurnSignals -> CapacityState
│   ├── completion.py    # CompletionVerdict ADT, CompletionEvaluator
│   ├── waiting.py       # AdaptiveWaitPolicy -> next probe instant
│   ├── budget.py        # Budget, BudgetLedger (turns, dollars, wall clock)
│   └── loop.py          # RunLoopStateMachine: (RunState, TurnOutcome, now) -> Decision
├── application/         # ports + use cases; depends only on domain
│   ├── ports.py         # Protocols: AgentGateway, CapacityProbe, SessionCatalog,
│   │                    #   ApiGateway, Clock, Sleeper, ProgressReporter,
│   │                    #   AuditLog, Notifier, RunStateStore, SessionLock
│   ├── dto.py           # TurnOutcome, ProbeResult, ApiInvocation
│   ├── runner.py        # AutonomousRunner — drives the state machine over the ports
│   └── usecases/        # RunFromPlanFile, ResumeMostRecent, ResumeSession,
│                        #   Preflight, ListSessions, InvokeApiMethod
├── infrastructure/      # adapters; the only layer importing anthropic / claude_agent_sdk
│   ├── agent/           # gateway, options builder, message translation, probe,
│   │                    #   autonomy (can_use_tool + hooks), session catalog
│   ├── api/             # introspect, binder, gateway, providers
│   ├── clock.py  logging.py  audit.py  state.py  lock.py  notify.py  config.py
├── cli/                 # Typer; hand-written core commands + generated `api` sub-app
└── bootstrap.py         # composition root — the one module that knows every layer
```

The dependency rule is enforced in CI by `import-linter` (layered contract: `cli` → `bootstrap` → `application` → `domain`, with `infrastructure` importable only by `bootstrap`), not by convention.

**Async bridge.** The Agent SDK is `anyio`-based and Typer is sync. Wrap async commands in a single `@async_command` decorator in `cli/asyncio.py` that calls `anyio.run()`, installs SIGINT/SIGTERM handlers that request graceful drain (finish the in-flight turn, persist state, disconnect the client), and translates `ClaudeSDKError` subclasses into Typer exit codes. One bridge point, not one per command.

## The autonomous run loop

`domain/loop.py` is a pure state machine; `application/runner.py` executes its decisions against the ports. States and the decisions that move between them:

| State | Entered when | Decision produced |
|---|---|---|
| `Preflight` | run starts | probe capacity before spending a real turn |
| `Running` | capacity available | send plan text (first turn) or continuation prompt |
| `Evaluating` | a turn ended | classify signals, evaluate completion |
| `Waiting` | capacity exhausted | compute next probe instant |
| `Probing` | wake from wait | cheap throwaway turn; re-classify |
| `Complete` / `Failed` | terminal | exit 0 / non-zero |

Classification (`domain/classify.py`) maps turn signals to a `CapacityState`, and the ordering matters:

- `RateLimitEvent.status == "allowed_warning"` is **not** a limit — record `utilization` and keep going. This is the exact false positive that caused multi-day cooldowns before.
- `status == "rejected"`, or `ResultMessage.api_error_status == 429`, or `AssistantMessage.error == "rate_limit"` → exhausted. Then discriminate:
  - `error_code == "credits_required"` / `disabled_reason == "out_of_credits"` / `overage_disabled_reason` set → **`CreditsExhausted(can_purchase)`** — no reset exists.
  - `resets_at` present → **`WindowExhausted(resets_at, rate_limit_type)`**.
  - neither → `WindowExhausted(None, unknown)`, fall back to the configured wait.
- `AssistantMessage.error == "authentication_failed"` → terminal abort, never retry.
- `subtype in {"error_max_turns", "error_max_budget_usd"}` → policy-controlled: raise the cap and continue, or abort.

Because the SDK's typed `RateLimitEvent` is reportedly dropped on some adapter paths (the binary contains `[sdkMessageAdapter] Ignoring rate_limit_event message`), classification reads **all three** signals and never depends on `RateLimitEvent` alone.

### Waiting that notices a credit top-up

This is the part that replaces `time.sleep(wait_seconds)` at `legacy/claude_autoresume.py:655`. `AdaptiveWaitPolicy` returns *the next instant to probe*, never a single long sleep:

- **`CreditsExhausted`** — no reset time exists, so the only thing that can change is a human buying credits. Probe on a bounded cadence (default 120s, backing off to a 600s ceiling) for as long as `--max-wait` allows. Fire the `Notifier` on entry so the human actually learns they need to act.
- **`WindowExhausted(resets_at)`** — probe at `min(resets_at + grace, now + window_probe_interval)`. The `resets_at` bound is the expected path; the interval bound is what catches a top-up that lifts an overage-driven rejection *before* the window rolls over.
- Each probe result is compared against the previous `CapacityState`. A transition to available is logged explicitly — "capacity restored at probe #7, 26m into a 5h window; cause: overage_status allowed → resuming" — so the recovery is visible in the audit log rather than inferred.

The probe itself (`infrastructure/agent/probe.py`) runs a minimal throwaway turn: one-token prompt, `max_turns=1`, no tools, `setting_sources=None` so no CLAUDE.md is loaded, and `extra_args={"no-session-persistence": None}` so it leaves no transcript. Two improvements over today's `preflight_wait()`: it costs less, and it stops polluting the working session with "OK" turns. A rejected probe is not billed, so the cadence is safe.

**`CLAUDE_CODE_RETRY_WATCHDOG` is deliberately left off** for the outer loop. It would retry 429s in-process indefinitely, which sounds attractive but blocks silently for hours: no progress reporting, no credit-vs-window discrimination, no `--max-wait`, nothing in the audit log. Instead set a modest `CLAUDE_CODE_MAX_RETRIES` so transient 5xx/529 blips are absorbed in-process while hard limits surface to the runner. Expose `--retry-watchdog` for anyone who prefers the built-in behavior.

## Never blocking on a human

The hard requirement is that the run never stalls waiting for an answer. Notifying the human is fine; *waiting* on them is not. Every stall path gets a mitigation:

- **Permission prompts** — `permission_mode="bypassPermissions"`. Note the Python SDK has no `dangerously_skip_permissions` field; this is the equivalent.
- **Defense in depth** — a `can_use_tool` callback that returns `PermissionResultAllow` without ever awaiting input, so an unexpected permission path still cannot block.
- **`AskUserQuestion`** — intercepted in `can_use_tool` and *denied with guidance* rather than auto-answered: returning a fabricated choice silently invents a decision the user never made, whereas a deny message ("running autonomously, no user available — choose the option you would recommend, note the assumption, and proceed") hands the decision back to the model with the constraint stated. The chosen assumption then lands in the transcript where it can be reviewed.
- **`ExitPlanMode`** — auto-approved, so a plan-mode turn cannot park.
- **Hooks** — `PermissionRequest` auto-allows; `Notification` logs only.
- **The model simply asking "Shall I proceed?"** — no tool call, so no interception point. Handled by an appended system-prompt fragment establishing autonomous operation, and by the completion evaluator treating a turn with `complete: false` and no progress as a continuation rather than a stop.
- **stdin** — never inherit a TTY; the runner is safe under `nohup` and systemd.
- **MCP OAuth** — cannot complete unattended. `doctor` checks configured MCP servers up front and fails fast with the servers named, rather than discovering it mid-run.

## Completion detection

`ClaudeAgentOptions.output_format` carries a JSON schema so each turn returns a typed verdict in `ResultMessage.structured_output`:

```json
{"complete": bool, "remaining_work": [str], "blocked_on": str | null, "summary": str}
```

`domain/completion.py` maps that to `Done` / `Continue(remaining)` / `Blocked(reason)`. This kills both current failure modes: a marker colliding with the user's own prompt text, and a truncated limit message coincidentally containing marker-like text — the guard in `legacy/claude_autoresume.py` (the `if not limited and done:` check near the end of the retry loop) becomes unnecessary because completion is a typed field, not a substring.

The existing `CLAUDELOOP_TASK_FULLY_COMPLETE` marker is retained as a fallback for when `structured_output` is absent, with the instruction-appending logic ported from `with_done_marker_instruction()` in the legacy script. A limit always outranks a completion claim, as today.

When the input is an md plan, `WorkPlan` parses it into items and `remaining_work` is tracked per item, so the log shows what is actually left rather than one boolean.

## The generated REST surface

`claudeloop api …` covers all 131 endpoints without hand-writing any of them.

- **Discovery** walks the *class* tree under `anthropic.resources` via the `cached_property` descriptors, not a live client — so no credentials are needed at import time. Each leaf yields resource path, method name, and `inspect.signature`.
- **Binding** maps path and scalar params to real typed Typer options; the request body goes to `--json` / `--json-file` with `@path` inlining. Mapping every nested TypedDict to flags is not worth it — `ant` reaches the same conclusion with relaxed-YAML structured flags.
- **Modifiers**: `--raw` / `--stream` select the `with_raw_response` / `with_streaming_response` variants; list methods auto-paginate with `--max-items`; `--provider` selects the alternate clients (only `AnthropicAWS`, `AnthropicGoogleCloud`, `AnthropicFoundry` carry the full tree — Bedrock/Mantle/Vertex expose Messages and Beta only, and the binder must reflect that rather than offering commands that will fail).
- **The drift gate** is the deliverable that makes "no gaps" real: a test enumerates the SDK surface and asserts every endpoint method has a registered command, failing CI when an SDK upgrade adds one. It also asserts the discovered count against a committed baseline so *removals* are caught too. The six local helpers (`messages.stream`/`parse`, `beta.messages.stream`/`parse`/`tool_runner`, `beta.webhooks.unwrap`) are explicitly enumerated as either bound or exempted — no silent omissions.

## Logging, security, quality gates

**Logging.** `structlog` with a JSON renderer to file and a human renderer to console. Every record carries `run_id`, `attempt_no`, `session_id`, `event_type`. The full raw event stream is preserved to a per-run JSONL audit file, keeping today's "nothing is lost" property from `run_once()` in the legacy script. `-v/-vv`, `--log-level`, `--log-file`.

**Security.**
- A redaction processor in the structlog pipeline scrubs `api_key`, `authorization_token`, `access_token`, `refresh_token`, `client_secret`, `secret_value`, and `Authorization` headers. This matters more than usual because the REST surface includes vaults and credentials, and because debug logging is a stated requirement.
- Bypassing permissions is required for autonomy but must be *chosen*: explicit opt-in, refuse to run as root, and refuse outside a git repository or an allowlisted directory unless overridden. Support `add_dirs` allowlisting and the SDK's `SandboxSettings`.
- Budget guardrails are a safety control, not a nicety, for an unattended multi-hour loop: `max_budget_usd`, `task_budget`, `max_turns`, `--max-wait`, `--max-attempts`.
- No `shell=True` anywhere; moving off subprocess removes the surface entirely. Plan-file and log paths are resolved and confined.
- A per-session advisory file lock prevents two runners from driving one session concurrently.

**Quality gates** (pre-commit + GitHub Actions): `ruff` lint and format, `mypy --strict`, `pytest` with `--cov-fail-under` set per-package (100% domain and application, high floor for infrastructure), `import-linter` for the onion contract, the API drift test, `bandit`, and `pip-audit`.

## Testing to ~100%

- **Domain** — pure unit tests, plus Hypothesis property tests for `AdaptiveWaitPolicy` (never returns a past instant, never exceeds `--max-wait`, always converges) and `LimitClassifier` (a credits rejection never classifies as waitable).
- **Application** — fakes for every port. `FakeAgentGateway` replays scripted event sequences; `FakeClock`/`FakeSleeper` make a simulated 7-day wait run in microseconds with zero real sleeping. The credit-top-up path is tested by scripting a probe sequence that returns `CreditsExhausted` five times then `Available`, and asserting the runner resumes on probe six.
- **Contract tests** run the same suite against both fake and real adapters where feasible.
- **Fixtures** — a real transcript captured during development already contains a genuine `credits_required` 429; capture it as a golden fixture rather than inventing one.
- **CLI** — Typer's `CliRunner`.
- `# pragma: no cover` is reserved for genuinely unreachable branches (signal handlers, `TYPE_CHECKING` blocks) and each use carries a reason.

## Build order

Each milestone leaves the tree working, and M2 already replaces the current script.

1. **M1 — pure core.** Package skeleton, `pyproject.toml`, domain layer, ports, full unit suite, CI with all gates. No SDK dependency yet. **✅ Complete.**
2. **M2 — runner parity.** Agent gateway, options builder, message translation, session catalog, `run`/`resume`/`sessions` commands. Reaches feature parity with `claude_autoresume.py`.
3. **M3 — resilient waiting.** Capacity probe, adaptive wait policy, credit-top-up detection, notifier, resumable run state.
4. **M4 — REST surface.** Introspection, binder, `api` sub-app, drift gate.
5. **M5 — polish.** Docs, `doctor`, packaging verification, security review.

## Verification

- **Unit and property suites** — `pytest --cov`, gates green, including the simulated multi-day wait with no wall-clock sleep.
- **Drift gate** — deliberately hide one SDK method from discovery and confirm CI fails; that proves the "no gaps" claim is enforced rather than asserted.
- **Onion contract** — add an import from `domain` to `infrastructure` and confirm `import-linter` rejects it.
- **End-to-end, plan-file mode** — run against a small md plan in a scratch git repo and confirm it completes, exits 0, and the audit log shows the structured completion verdict.
- **Never-block** — run a plan that explicitly instructs the model to ask a clarifying question, and confirm the runner denies `AskUserQuestion` with guidance and continues instead of hanging.
- **Limit handling without waiting for a real limit** — a fake gateway scripted to emit a `rejected` `RateLimitEvent` with a `resets_at`, then a `credits_required` rejection, asserting the first schedules a bounded probe and the second never schedules a blind sleep.
- **Credit top-up, live** — the honest test is opportunistic: when a real `credits_required` rejection occurs, add credits mid-wait and confirm the runner resumes on the next probe rather than at the window boundary. Until then the scripted probe sequence in M3 covers the logic.
- **Install check** — `pipx install .` on macOS and Linux, confirm the `claudeloop` entry point resolves and `--help` renders.
