# Shared transplant outline (claudeloop 0.5.4 → *loop forks)

This outline is identical across cursorloop / codexloop / agyloop. Product-specific architecture docs adapt section 2–8; they must not weaken the Global Constraints.

## Global Constraints (verbatim in every plan)

1. Never block on a human.
2. Credits/billing ≠ rate-limit window (`CreditsExhausted` has no waitable deadline).
3. A capacity rejection always outranks a completion claim.
4. `domain/` stays pure: stdlib only, no I/O, no async, no third-party imports (import-linter).
5. Every commit follows Conventional Commits.
6. Quality gates match claudeloop: `ruff check`, `ruff format --check`, `mypy --strict`, `pytest` (domain+application 100% coverage floors), `lint-imports`, `bandit`, `pip-audit`.
7. No `anthropic` / `claude_agent_sdk` runtime dependencies (historical citations of claudeloop only).

## Keep (copy + rename package)

| Source (`claudeloop`) | Notes |
|---|---|
| `domain/loop.py`, `waiting.py`, `budget.py`, `capacity.py`, `control.py`, `plan.py`, `session.py`, `savepoint*.py`, `snapshot.py`, `stop_summary.py`, `errors.py`, `chatter.py`, `model_policy.py` | Remap error class names (`AutoclaudeError` → product Error) |
| `domain/classify.py`, `completion.py`, `model_profile.py`, `permission.py`, `slash.py` | **Pure but vendor-shaped** — rewrite signal fields / aliases / modes |
| `application/ports.py`, `dto.py`, `runner.py`, `usecases/*` | Keep Protocols; rewrite AgentGateway docstring |
| `infrastructure/` minus `agent/` and `api/` | Control plane, rundir, state, lock, audit, logging, notify, clock, resources, stream_ui, git_savepoints |
| Operator CLI: stop/prompt/logs/status/watch/runs/savepoints/snapshot/unwind/reset/attach/… | Remap branding |
| Tests for domain loop/waiting/budget + application runner fakes | Port then retarget classify fixtures |
| CI / pre-commit / import-linter / CODEOWNERS pattern | Rename package paths |

## Replace (rewrite)

| Source | Why |
|---|---|
| `infrastructure/agent/*` | New SDK/CLI gateway, options, translate, autonomy, catalog, probe |
| `infrastructure/api/*` | Provider REST or omit with ADR |
| `infrastructure/doctor_env.py`, snapshot paths under `~/.claude` | New auth/doctor/session roots |
| Packaging: `pyproject.toml`, entrypoint, env prefix, `.claudeloop/` | Full rename |
| Docs, skills, `.claude`/`.cursor`/`.agents` trees | Product-specific |
| Generated Anthropic `cli api` | Drop; replace per REST decision |

## Application ports to preserve (signatures)

From `claudeloop.application.ports`: `Clock`, `Sleeper`, `AgentGateway` (`send_turn`, `close`, `set_profile`, `set_permission_mode`, `set_cwd`, `set_session_resources`, `resolve_tool_approval`), `RunResources`, `CapacityProbe`, `SessionCatalog`, `ProgressReporter`, `AuditLog`, `Notifier`, `Logger`, `RunStateStore`, `SessionLock`, `ApiGateway`, `RunControl`, `RunEventSink`, `StreamUi`, `SavePointStore`, `StateBus`, `RunSnapshotSink`.

## Milestone mirror

| Milestone | Deliverable |
|---|---|
| M1 | Package skeleton + pure domain + ports + unit tests + CI gates (no vendor SDK required to import domain) |
| M2 | Agent gateway + translate + catalog + `run`/`resume`/`sessions`/`doctor` |
| M3 | Capacity probe + adaptive wait + credit/billing probe cadence + notifier + resumable run state |
| M4 | Provider REST surface **or** documented deferral ADR + mid-run ops polish |
| M5 | Docs, packaging verification, security review, live/system harness |

## Capacity ADT (shared shapes)

**Required core members** (never remove): `Available`, `WindowExhausted(resets_at, rate_limit_type)`, `CreditsExhausted(can_purchase)`, `AuthenticationFailed`.

**Hard rule:** `CreditsExhausted` must **never** gain a `resets_at` / waitable deadline field. Billing is probe+notify, not sleep-to-deadline.

**Allowed vendor extensions** (document in that product’s architecture ADR): short-horizon members such as `TransientThrottle` / `ThrottleExhausted` for RPM-class or 503 backoff — only if the waiting policy treats them as short bounded backoff and never conflates them with credits. Cursorloop may keep the four-member ADT if Cursor errors fold cleanly into window vs credits.

Only the **classifier inputs** (`TurnSignals`) and any documented extensions change per vendor.

## Packaging rename matrix (fill per product)

| Item | claudeloop | cursorloop | codexloop | agyloop |
|---|---|---|---|---|
| PyPI / CLI | `claudeloop` | `cursorloop` | `codexloop` | `agyloop` |
| Env prefix | `CLAUDELOOP_` | `CURSORLOOP_` | `CODEXLOOP_` | `AGYLOOP_` |
| State dir | `.claudeloop/` | `.cursorloop/` | `.codexloop/` | `.agyloop/` |
| Config files | `claudeloop.toml` | `cursorloop.toml` | `codexloop.toml` | `agyloop.toml` |
| Done marker | `CLAUDELOOP_TASK_FULLY_COMPLETE` | `CURSORLOOP_TASK_FULLY_COMPLETE` | `CODEXLOOP_TASK_FULLY_COMPLETE` | `AGYLOOP_TASK_FULLY_COMPLETE` |
| Auth env | `ANTHROPIC_*` | `CURSOR_API_KEY` | `OPENAI_API_KEY` / Codex login | `GOOGLE_API_KEY` / ADC |
| Primary SDK | `claude-agent-sdk` | `cursor-sdk` | Codex CLI/SDK + `openai` | `google-antigravity` |
