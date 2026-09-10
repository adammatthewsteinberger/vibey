# cursorloop — vendor research notes

> **Status.** Pre-implementation research, captured before any `src/cursorloop/`
> code exists. This document is the evidence base for
> [`architecture-and-roadmap.md`](./architecture-and-roadmap.md); the roadmap
> states *what we are building*, this file states *what we verified, where we
> verified it, and how much weight the design is allowed to put on it*. Every
> design invention below is explicitly labelled as an invention so a future
> reader never mistakes our taxonomy for a vendor guarantee.

**Research date:** 2026-08-13.
**Blueprint:** `claudeloop` 0.5.4 (`/Users/adam/git/claudeloop`) — an
onion-architected autonomous Claude Code session runner that never blocks on a
human and distinguishes a waitable rate-limit window from non-waitable
exhausted credits.
**Target:** `cursorloop` — the same architecture, the same non-negotiables,
retargeted onto the **Cursor Agent SDK** (`cursor-sdk`, Python) with
**Composer** as the default model family.

---

## Contents

1. [Method and confidence scale](#1-method-and-confidence-scale)
2. [Scope, naming, and what is deliberately *not* here](#2-scope-naming-and-what-is-deliberately-not-here)
3. [Cursor Python SDK — the primitives we build on](#3-cursor-python-sdk--the-primitives-we-build-on)
4. [Authentication](#4-authentication)
5. [CLI fallback: `agent -p`](#5-cli-fallback-agent--p)
6. [Capacity taxonomy — an invention, and why](#6-capacity-taxonomy--an-invention-and-why)
7. [Waiting that notices a top-up](#7-waiting-that-notices-a-top-up)
8. [Never blocking on a human](#8-never-blocking-on-a-human)
9. [Completion detection — no `output_format`, so build one](#9-completion-detection--no-output_format-so-build-one)
10. [Composer, Grok, and model profiles](#10-composer-grok-and-model-profiles)
11. [The REST surface: Cloud Agents API v1](#11-the-rest-surface-cloud-agents-api-v1)
12. [Security notes](#12-security-notes)
13. [Findings that become ADRs](#13-findings-that-become-adrs)
14. [Open questions to resolve empirically](#14-open-questions-to-resolve-empirically)
15. [Open risks](#15-open-risks)
16. [Divergences from the claudeloop blueprint](#16-divergences-from-the-claudeloop-blueprint)
17. [Citation index](#17-citation-index)

---

## 1. Method and confidence scale

Sources were gathered from Cursor's own published documentation at
`cursor.com/docs` (fetched 2026-08-13), cross-checked between the SDK
reference, the API reference, and the product/pricing pages; and, where Cursor
publishes nothing, from the blueprint's hard-won behaviour plus generic HTTP
semantics. Anything in the second category is treated as a **hypothesis the
implementation must verify at runtime and degrade gracefully when it fails** —
never as a spec.

| Confidence | Meaning | How cursorloop is allowed to use it |
|---|---|---|
| **A — documented** | Stated in Cursor's own docs, in a form specific enough to code against (a named field, a documented exit code, a listed enum value). | May be relied on in a hot path. Still guarded by a parse-failure fallback. |
| **B — corroborated inference** | Not stated as such by Cursor, but forced by two or more documented facts, or corroborated by the blueprint hitting the identical shape on another vendor. | May inform a decision, but never as the *sole* input to a capacity classification. Must have a fallback. |
| **C — invention / single-source** | cursorloop's own taxonomy, or a single doc sentence read tendentiously. | Must be configurable, must be probed against reality, must be captured into fixtures, and must have an ADR naming the risk. |

The rule that falls out of this table, and the single most important design
constraint in the project:

> **A capacity decision is never allowed to depend on a confidence-C signal
> alone in a way that can produce an *unbounded* wait.** Every classification
> path must terminate in a defensible answer — and every waiting path must be
> clamped by `--max-wait` — even if every optional signal returns nothing.

Confidence is marked at the head of each section below and inline on individual
claims where it differs from the section default.

---

## 2. Scope, naming, and what is deliberately *not* here

**Confidence: A** (these are our own decisions, not vendor claims).

| Dimension | claudeloop (blueprint) | cursorloop (this project) |
|---|---|---|
| Vendor SDK | `claude-agent-sdk` + `anthropic` | `cursor-sdk` **only** |
| Default model | Claude (Sonnet/Opus family) | `composer-2.5` |
| Secondary model | n/a | Grok, as a **model profile**, not a product |
| Distribution name | `claudeloop` (PyPI + console script) | `cursorloop` (PyPI + console script) |
| Env prefix | `CLAUDELOOP_*`, `ANTHROPIC_*` | `CURSORLOOP_*`, `CURSOR_API_KEY` |
| Run state dir | `.claudeloop/` | `.cursorloop/` |
| Completion marker | `CLAUDELOOP_TASK_FULLY_COMPLETE` | `CURSORLOOP_TASK_FULLY_COMPLETE` |
| Verdict fence | `ClaudeAgentOptions.output_format` (vendor-enforced) | ` ```cursorloop-verdict ` (convention) — see §9 |
| REST surface | Generated from the Anthropic Python SDK (131 endpoints) | Cursor **Cloud Agents API v1** (public beta) — see §11 |

**Explicitly out of scope, permanently:**

- No dependency on `anthropic`, `claude-agent-sdk`, or any Anthropic package.
- No `ANTHROPIC_API_KEY` / `ANTHROPIC_*` environment variable is read, written,
  documented as supported, or accepted as a fallback. The only place the string
  `ANTHROPIC_` may appear in this repository is inside a historical citation of
  claudeloop's design (as in this very table), never in `src/`. A grep-based
  test enforces this so a copy-paste from the blueprint cannot smuggle one in.
- No `CLAUDE.md`-reading behaviour, no `~/.claude/projects/` scraping, no
  `claude` CLI subprocess.
- **Grok is not a separate product.** There is no `grokloop`, no `--grok` mode,
  no parallel adapter. Grok is one entry in a model-profile table (§10).
- No xAI-direct transport. See §10 for why that would be a second vendor, a
  second auth story, and a second capacity taxonomy for a model already
  reachable through the Cursor catalog on the same key.

---

## 3. Cursor Python SDK — the primitives we build on

**Section confidence: A.** Source: <https://cursor.com/docs/sdk/python> (fetched
2026-08-13) [[c-sdkpython]], cross-checked against <https://cursor.com/docs/api>
[[c-api]] and <https://cursor.com/docs/cloud-agent/api/endpoints>
[[c-cloudapi]].

### 3.1 Package, runtime, and installation

```bash
pip install cursor-sdk
```

- Requires **Python 3.10 or later**. cursorloop will require **3.12+** anyway
  (see roadmap, packaging matrix), which is comfortably inside the supported
  range.
- The wheel ships a bridge binary installed on `PATH` as `cursor-sdk-bridge`.
  `cursor-sdk-bridge --help` is a legitimate `doctor` preflight check: it proves
  the native bridge shipped with the installed wheel and is executable. This is
  a genuine new failure mode relative to the blueprint — a pure-Python SDK
  cannot fail to have a platform binary — and it is why the `agent -p` fallback
  adapter (§5) earns its place in the plan.
- Debug logging is opt-in via `CURSOR_SDK_LOG=debug|info`, and the docs state
  the SDK only configures its own `cursor_sdk` logger — so it will not fight
  cursorloop's `structlog` configuration. `doctor` should surface this variable
  as the supported way to get vendor-side traces.

### 3.2 The three-object model: Agent → Run → SDKMessage

| Concept | Meaning (verbatim from the docs, condensed) |
|---|---|
| `Agent` | Durable handle holding conversation state, workspace config, model selection, settings. **Survives across multiple prompts.** |
| `Run` | **One prompt submission.** Owns its own stream, status, result, conversation, and cancellation. |
| `SDKMessage` | Typed stream message yielded during a run; same shape across local and cloud. |
| `CursorClient` / `Client` | Explicit client for lifecycle control, custom HTTP options, or multiple workspaces in one process. |
| `AsyncClient` | Async mirror. **Required for all async operations.** |

This maps onto claudeloop's design remarkably cleanly, and it maps onto the
*good* half of it. claudeloop's ADR-0002
(`docs/architecture/decisions/0002-agent-sdk-over-subprocess.md`) exists because
`claude_agent_sdk.query()` raises after yielding an error result and kills the
process, whereas `ClaudeSDKClient` survives errors and can be re-sent to. The
Cursor SDK gives us the surviving-handle shape *by default*: `Agent` is the
durable object and each `agent.send()` produces a fresh `Run`. **An error on one
run does not invalidate the agent.** The outer respawn-and-resume loop that the
legacy `claude_autoresume.py` needed collapses to repeated `agent.send()` calls
on one live `Agent`, exactly as claudeloop achieves with `ClaudeSDKClient`.

So the transport argument that ADR-0002 had to *win* on Anthropic is simply the
default on Cursor. cursorloop inherits the conclusion without inheriting the
fight, and the CLI-subprocess path is demoted from "the thing we replaced" to
"a documented fallback adapter" (§5).

### 3.3 `Agent.create()`

```python
from cursor_sdk import Agent, AgentOptions, CloudAgentOptions, CloudRepository, LocalAgentOptions

agent = Agent.create(
    model="composer-2.5",
    local=LocalAgentOptions(cwd="."),
)

cloud_agent = Agent.create(
    model="composer-2.5",
    cloud=CloudAgentOptions(
        repos=[CloudRepository(url="https://github.com/your-org/your-repo", starting_ref="main")],
        auto_create_pr=True,
    ),
)
```

Verified facts:

- `Agent.create()` **validates options and returns a handle immediately**;
  `agent.agent_id` is populated straight away.
- ID prefixes are a reliable runtime discriminator: **`agent-` for local,
  `bc-` for cloud**. This is documented twice (creation and resume).
- Passing `local=` selects the local runtime; passing `cloud=` selects the cloud
  runtime; **omitting `cloud` selects local**.
- `agent.model` is a typed `ModelSelection`, so `agent.model.id` and
  `agent.model.params` are directly readable — useful for audit-logging exactly
  which model a turn was billed against.
- Raw snake-cased dicts are accepted anywhere a dataclass is. cursorloop will
  use the dataclasses exclusively (mypy strict, and dicts defeat that).
- Cloud agents created by the SDK are filtered out of the default agent list in
  the Cursor UI; they appear under **Filter → Source → SDK**. Worth stating in
  user docs so an operator can find their runs, and worth setting
  `AgentOptions.name = "cursorloop/<run_id>"` so they are individually
  identifiable there.

### 3.4 `AgentOptions` — the full documented option surface

| Property | Type | Default | Notes for cursorloop |
|---|---|---|---|
| `model` | `str \| ModelSelection \| Mapping` | required for local; cloud falls back to a server-resolved default | Always set explicitly. Never rely on the server default — reproducibility. |
| `api_key` | `str` | `CURSOR_API_KEY` env | Never pass from a CLI flag; env or keyring only (§12). |
| `name` | `str` | auto-generated | Set to `cursorloop/<run_id>` so runs are identifiable in the dashboard. |
| `local` | `LocalAgentOptions` | `None` | Primary runtime for M1–M3. |
| `cloud` | `CloudAgentOptions` | `None` | M4+. |
| `mcp_servers` | `Mapping[str, McpServerConfig]` | `None` | Inline definitions; **not persisted across resume** (§3.10). |
| `agents` | `Mapping[str, AgentDefinition]` | `None` | Subagent definitions. |
| `tools` | `Sequence[str]` | default toolset | **Local only.** Allowlist. `[]` = text-only model. |
| `disallowed_tools` | `Sequence[str]` | `None` | **Local only.** Deny wins over `tools`. |
| `agent_id` | `str` | auto | Durable ID across invocations — a natural resume key for `.cursorloop/state.json`. |
| `idempotency_key` | `str` | auto for cloud | Cloud only. |
| `mode` | `"agent" \| "plan"` | server default = agent | Seeds the first run; per-send override available. cursorloop sets it explicitly rather than inheriting a server default. |

`LocalAgentOptions`:

| Property | Type | Notes |
|---|---|---|
| `cwd` | `str \| PathLike` | Primary working directory. **Multi-entry lists are rejected** — use `dirs`. |
| `dirs` | `Sequence[str \| PathLike]` | Additional workspace folders; merged with `cwd` so rules/skills/context load from every path. This is the `add_dirs` allowlist analogue. |
| `setting_sources` | `Sequence[SettingSource]` | `"project"`, `"user"`, `"team"`, `"mdm"`, `"plugins"`, `"all"`. **Gates whether `.cursor/` on disk is read at all.** |
| `sandbox_options` | `SandboxOptions` | Local sandbox. |
| `store` | `LocalAgentStoreConfig` | Bridge-side local store config. |
| `auto_review` | `bool` | Route local tool calls through Auto-review when the backend supports it. **Must be left off/false for autonomy** — see §8. |
| `custom_tools` | `Mapping[str, CustomTool]` | Python functions exposed to a local agent, no MCP server needed. Local only. |

`CloudAgentOptions`: `env`, `repos`, `work_on_current_branch`, `auto_create_pr`,
`open_as_cursor_github_app`, `skip_reviewer_request`, `env_vars`, `metadata`
(≤50 pairs, keys ≤255 chars, values ≤4096 bytes; `403 feature_unavailable` if
metadata isn't enabled for the account). `env_vars` names **cannot start with
`CURSOR_`** and cannot be combined with a caller-supplied `agent_id`.

### 3.5 `Agent.resume()`

```python
Agent.resume(
    agent_id: str,
    options: AgentOptions | Mapping[str, Any] | None = None,
    *,
    client: CursorClient | None = None,
) -> Agent
```

Verified facts, all of which have direct consequences:

1. **Runtime is auto-detected from the ID prefix** (`bc-` → cloud, anything else
   → local). cursorloop persists `agent_id` and never needs to persist the
   runtime separately — though it will anyway, for audit clarity.
2. **`agent.model` is `None` on resume unless you pass `model` again.** A resume
   path that forgets this silently loses the model selection. cursorloop's
   resume use case must re-send the full resolved `ModelSelection`.
3. **Inline MCP servers are not persisted across resume** — the docs say they
   often carry secrets and live in memory only. Same for `tools` /
   `disallowed_tools` / `custom_tools`. Every one of these must be re-applied on
   every resume. This is a checklist, and a checklist is a bug waiting to
   happen, so it belongs in one `options.py` builder called by both create and
   resume — never duplicated.
4. **Local persistence is workspace-scoped.** The bridge keeps state under a
   per-workspace state root. When the bridge runs as a long-lived sidecar, it
   must be given the *same* workspace as the agent, and `cwd` must be passed to
   local `list`/`get` calls:

   ```python
   with CursorClient.launch_bridge(workspace="/path/to/repo") as client:
       agents = client.agents.list(runtime="local", cwd="/path/to/repo")
       info = client.agents.get(agents.items[0].agent_id, cwd="/path/to/repo")
   ```

   This is the supported session-discovery API — the direct analogue of
   claudeloop's `list_sessions()` / `get_session_info()`, and the reason
   cursorloop will never glob a state directory. Getting a *supported* discovery
   API is one of the two places (with the durable `Agent` handle) where Cursor
   is straightforwardly better than the legacy Anthropic path, which forced a
   `~/.claude/projects/` glob the vendor docs explicitly warned against.

### 3.6 `Agent.prompt()` — one-shot

```python
Agent.prompt(
    message, options=None, *, client=None
) -> RunResult
```

Creates an agent, sends one prompt, waits, disposes. **This is the wrong
primitive for the run loop** (it throws away the durable handle that makes
resume cheap), but it is exactly right for two narrow uses:

- the **capacity probe** (§7) — a throwaway one-token turn that must leave no
  conversational residue on the working agent;
- `cursorloop doctor` connectivity checks.

Note the docs' own retry example uses `Agent.prompt` inside a
`RateLimitError` / `CursorAgentError` retry loop — see §6. That example is also
where the `AgentBusyError` trap lives (§3.12, risk R10): the docs' own pattern
would abort on a recoverable condition.

### 3.7 `agent.send()` and `SendOptions`

Each `agent.send()` returns a `Run`; conversation context is retained on the
`Agent` across runs. `SendOptions`:

| Property | Notes |
|---|---|
| `model` | Per-send override. **Sticky** — later sends without an override keep the new selection. |
| `mode` | `"agent"` or `"plan"` per send. |
| `mcp_servers` | **Fully replaces** creation-time servers for this run (not merged). |
| `cloud.env_vars` | Cloud only; run-scoped, removed when the run finishes; overrides agent-scoped by name. |
| **`local.force`** | **Local only. `True` expires a stuck active run before starting this message.** |
| `idempotency_key` | Client-generated key for the send. |
| `on_step` | Callback per completed conversation step (text / thinking / tool batch). |
| `on_delta` | Callback per raw `InteractionUpdate`. |

**`local.force` is the single most important never-block primitive in the whole
SDK for cursorloop.** The documented failure mode it addresses — a local run
stuck in an active state — is precisely the shape of stall that would otherwise
park an unattended loop forever. See §8.

`on_delta` / `on_step` give us the live-progress feed that claudeloop's
`infrastructure/stream_ui/` consumes; the update subclasses live in
`cursor_sdk.events` (`TextDeltaUpdate`, `ToolCallStartedUpdate`, …). They also
provide the timestamps that drive the stall watchdog's no-delta deadline.

### 3.8 `Run` — status, result, and the error/exception split

```python
class Run:
    id: str
    agent_id: str
    status: str  # "running" | "finished" | "error" | "cancelled" | "expired"
    result: str
    model: ModelSelection | None
    duration_ms: int
    git: RunGitInfo | None
    created_at: str | None
    usage: TokenUsage | None

    def stream(self) -> Iterator[SDKMessage]: ...
    def messages(self) -> Iterator[SDKMessage]: ...
    def events(self) -> Iterator[RunStreamEvent]: ...
    def iter_text(self) -> Iterator[str]: ...
    def text(self) -> str: ...
    def wait(self) -> RunResult: ...
    def cancel(self) -> None: ...
    def conversation(self) -> list[ConversationTurn]: ...
    def observe(self, *, after_offset: str | None = None) -> Iterator[RunStreamEvent]: ...
    def supports(self, operation: str) -> bool: ...
    def unsupported_reason(self, operation: str) -> str | None: ...
    def on_did_change_status(self, listener) -> Callable[[], None]: ...
```

**This is the finding that most shapes the classifier.** There are *two
independent* channels by which a Cursor run can fail, and a correct
implementation must read both:

1. **A thrown exception** — `CursorAgentError` and its subclasses (§3.12), raised
   out of `send()` / `wait()` / iteration.
2. **A non-thrown terminal status** — `run.status ∈ {"error", "cancelled",
   "expired"}` with human-readable text in `run.result`.

claudeloop hit the same duality from a different direction: its ADR notes that
the typed `RateLimitEvent` "is reportedly dropped on some adapter paths", so
`domain/classify.py` reads three signals and never trusts one. cursorloop
inherits that discipline for a *documented* reason rather than an observed bug:
`status == "error"` is a real, first-class outcome of `run.wait()`, not an
exception. **A classifier that only catches exceptions will silently treat an
errored run as a completed one** — which, combined with a completion evaluator
that falls back to substring matching, is exactly how a run could end early with
work unfinished.

Other verified `Run` facts:

- **A run stream is consumable once.** `messages()`, `events()`, and
  `iter_text()` all draw from the same underlying stream and advance it. Call
  `wait()` to drain remaining events and get the typed `RunResult`. Any adapter
  that both streams for the UI and re-reads for classification must therefore
  tee once into its own buffer, not iterate twice.
- `run.cancel()` on an already-terminal run raises `UnsupportedRunOperationError`
  — guard with `run.status == "running"`.
- `run.supports(op)` / `run.unsupported_reason(op)` report SDK capability for
  `"stream"`, `"wait"`, `"cancel"`, `"conversation"` and **do not check run
  state**. State guards still need `run.status`.
- `on_did_change_status(listener) -> unsubscribe` gives a push-based status
  feed, useful for the stall watchdog in §8.

### 3.9 Token usage, `get_usage()`, and cost

Two distinct views, and conflating them would produce a wrong budget ledger:

**Live token counts** — `run.usage` / `result.usage`, a cumulative `TokenUsage`
across turns; `None` when nothing reported (cancelled run, runtime that doesn't
surface usage, unreconciled cloud snapshot).

```python
@dataclass(frozen=True)
class TokenUsage:
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    cache_write_tokens: int
    total_tokens: int
    reasoning_tokens: int | None = None
```

`total_tokens = input + output + cache_read + cache_write` and **excludes**
`reasoning_tokens`, which are already a subset of `output_tokens`. Per-turn
numbers arrive as an `SDKUsageMessage` (`type == "usage"`) once at the end of
each turn that reported usage.

**Billed cost** — `agent.get_usage(run_id=None)`:

```python
@dataclass(frozen=True)
class AgentUsage:
    usage: TokenUsage
    runs: Sequence[RunUsage] = ()
    cost: UsageCost | None = None


@dataclass(frozen=True)
class UsageCost:
    raw_cost_cents: float  # undiscounted model token cost; 0 for request-priced usage
    charged_cents: float  # amount charged, discounts + Cursor Token Rate included
```

Cloud agents return a per-run breakdown; local agents return a per-turn
breakdown. **`cost` is `None` until billing settles**, and `charged_cents` is
`0.0` for plan-included, BYOK, and credit-grant usage.

Consequences for cursorloop's `domain/budget.py` port:

- A dollar budget must treat `cost is None` as *unknown*, never as *zero*. An
  unattended loop that reads a settling `None` as `$0.00` will happily run
  forever under a `--max-cost` cap it has already blown through.
- `charged_cents == 0.0` is genuinely ambiguous (plan-included vs. not yet
  settled vs. BYOK). The ledger therefore tracks **tokens as the authoritative
  hard cap** and dollars as a best-effort secondary cap, inverting claudeloop's
  emphasis (Anthropic's `ResultMessage.total_cost_usd` is immediate and exact).
- `get_usage()` is an extra network call. It must be rate-limited to at most
  once per N turns (configurable, default every turn is fine for a
  multi-minute turn, but the config must exist).

**Worth stating for what it is not:** `get_usage()` is a *billing* view, not a
capacity view. There is no Cursor analogue of Codex's `x-codex-*` window headers
or Anthropic's `RateLimitEvent.utilization` — nothing tells cursorloop "you are
72% through your window" before a rejection. Capacity is therefore learned
**only** by attempting a turn or a probe. That absence is what makes the probe
loop (§7) load-bearing rather than an optimisation, and it is worth re-checking
at every SDK bump (Q6, §14).

### 3.10 MCP, skills, hooks, subagents — the `.cursor/` filesystem contract

**MCP loading order for local agents** (first match wins on conflicting names):

1. `mcp_servers` on `agent.send()` — **fully replaces** creation-time servers for
   that run.
2. `mcp_servers` on `Agent.create()`.
3. Plugin servers, if `local.setting_sources` includes `"plugins"`.
4. Project servers from **`.cursor/mcp.json`**, if `setting_sources` includes
   `"project"`.
5. User servers from **`~/.cursor/mcp.json`**, if `setting_sources` includes
   `"user"`.

**Without `local.setting_sources`, only inline servers are loaded.** That single
sentence is load-bearing: a cursorloop run that wants the repo's own MCP
configuration must opt in explicitly. It also means cursorloop can run in a
*hermetic* mode (no ambient config) simply by omitting `setting_sources` — which
is the correct default for reproducible CI usage, with `--setting-sources` to
widen it.

**MCP OAuth is the one true unattended blocker.** The docs are explicit: "If a
local MCP server requires OAuth login, the SDK can reuse a saved login from the
Cursor app, but it cannot open a browser to sign you in." Cloud runs
authenticated with a personal API token can reuse OAuth previously authorized at
cursor.com/agents; **service account API keys cannot fall back to user auth.**
This is exactly claudeloop's "MCP OAuth cannot complete unattended" finding, and
gets the same treatment: `doctor` checks configured MCP servers up front and
fails fast, naming the servers, rather than discovering it mid-run.

**Skills** (<https://cursor.com/docs/skills> [[c-skills]]) load automatically from:

| Location | Scope |
|---|---|
| `.cursor/skills/` | project |
| `.agents/skills/` | project |
| `~/.cursor/skills/` | user |
| `~/.agents/skills/` | user |

plus compatibility paths `.claude/skills/`, `.codex/skills/`, and their `~`
variants. Each skill is a folder containing `SKILL.md` with YAML frontmatter
(`name`, `description`, optional `paths`, `disable-model-invocation`,
`metadata`), optionally with `scripts/`, `references/`, `assets/`. Nested
`.cursor/skills/` directories anywhere in the repo are discovered and are
automatically scoped to files under that directory. Skills are gated by the same
`setting_sources` project/user layers as MCP.

This matters for cursorloop in two directions. **Inbound:** an autonomous run
should usually load project skills, so `--setting-sources project` is the
sensible run default even though the hermetic default is none. **Outbound:**
cursorloop ships its *own* agent-surface skills under `.cursor/skills/`,
`.claude/skills/`, and `.agents/skills/` exactly as claudeloop does, and the
Cursor compatibility paths mean the three mirrored trees are all discoverable by
Cursor itself.

**Subagents**: inline via `AgentOptions.agents={name: AgentDefinition(...)}`, or
committed at `.cursor/agents/*.md` with `name` / `description` / optional
`model` frontmatter. Inline overrides file-based on name collision. Nesting is
allowed one level deep from the top-level agent (a subagent launched by a
subagent cannot launch further ones).

**Hooks** (<https://cursor.com/docs/hooks> [[c-hooks]]) — the critical structural
finding:

> **Hooks are file-based only. There is no programmatic hook callback. Hooks are
> a project policy boundary, not a per-run knob.**

- Local: `.cursor/hooks.json` in `local.cwd`, or `~/.cursor/hooks.json`.
- Cloud: commit `.cursor/hooks.json` + scripts to the repo in `cloud.repos`.
  SDK-created cloud agents load project hooks automatically.
- Hook processes communicate over stdio with JSON in both directions.
- Exit codes: `0` = succeeded, use the JSON output; **`2` = block the action**
  (equivalent to `permission: "deny"`); any other code = hook failed and **the
  action proceeds (fail-open by default)**.
- Two execution types: command-based (default) and prompt-based (LLM-evaluated,
  returns `{ok: boolean, reason?: string}`). **Cloud agents run command-based
  hooks only.**

Agent hook events: `sessionStart` / `sessionEnd`, `preToolUse` / `postToolUse` /
`postToolUseFailure`, `subagentStart` / `subagentStop`, `beforeShellExecution` /
`afterShellExecution`, `beforeMCPExecution` / `afterMCPExecution`,
`beforeReadFile` / `afterFileEdit`, `beforeSubmitPrompt`, `preCompact`, `stop`,
`afterAgentResponse` / `afterAgentThought`. Cloud supports all of those except
`sessionStart`, `sessionEnd`, `beforeMCPExecution`, `afterMCPExecution`, plus
the Tab and `workspaceOpen` hooks which are IDE-only.

**This is the single largest architectural delta from claudeloop.** claudeloop's
never-block story leans on `can_use_tool` — an in-process Python callback that
returns `PermissionResultAllow` and, critically, intercepts `AskUserQuestion` to
deny-with-guidance (ADR-0007). **The Cursor SDK has no equivalent callback.** The
replacement is a cursorloop-authored `hooks.json` fragment, materialised into
the workspace before the run and removed after. See §8 and the roadmap's
never-block table.

The fail-open exit-code semantics deserve a note, because they cut in our
favour exactly once: if cursorloop's hook script crashes, the action *proceeds*
rather than blocking. For an autonomous runner that is the correct failure
direction — a broken autonomy hook degrades to "no policy" rather than to "the
run hangs". It is also, obviously, the wrong failure direction for anyone using
hooks as a security boundary, which is why the docs say so and why cursorloop
pairs auto-allow with `disallowed_tools` and the sandbox rather than relying on
hooks alone.

### 3.11 Restricting the toolset

`tools` allowlists; `disallowed_tools` removes and keeps the rest, **including
tools added to the platform after your SDK version shipped** — which makes
`disallowed_tools` the safer of the two for a long-lived unattended process.
Both are **local only** and **neither persists on the agent**; re-pass on
resume. Names accept public tool names (`"read"`, `"edit"`, `"task"`,
`"webSearch"`, …) plus capability groups `"shell"` and `"mcp"`. **Deny wins.**
Unknown names raise `BadRequestError` at creation. Disallowing `"mcp"` also
removes custom tools; disallowing `"task"` disables subagents.

The "tools added after your SDK version shipped" clause is the whole argument
for preferring deny-lists in a security-sensitive posture, and it is the same
argument as pinning a dependency floor: an allowlist silently narrows over time
as the platform grows, while a deny-list silently *widens*. For a runner whose
autonomy posture is "allow everything the hooks see", widening is the honest
default and narrowing would be a false sense of safety.

### 3.12 Errors — the full documented hierarchy

```python
class CursorAgentError(Exception):
    message: str
    code: str | None
    status: int | None
    status_code: int | None
    details: list[Mapping[str, Any]]
    is_retryable: bool
    cause: BaseException | None
    proto_error_code: str | None
    request_id: str | None
    headers: Mapping[str, str]
    retry_after: str | None
```

`CursorSDKError` is a backward-compatible alias root.

| Error | Documented trigger |
|---|---|
| `AuthenticationError` | Invalid API key or not logged in. |
| `PermissionDeniedError` | Authenticated caller lacks permission for the operation. |
| `RateLimitError` | **Too many requests *or usage limits exceeded*.** |
| `ConfigurationError` | Invalid model, missing required configuration, bad request params. |
| `AgentBusyError` | Follow-up sent while a run is `CREATING`/`RUNNING` (HTTP 409, code `agent_busy`). |
| `BadRequestError` | Malformed request. |
| `IntegrationNotConnectedError` | Cloud agent for a repo whose SCM provider isn't connected. Carries `provider` and `help_url`. |
| `NetworkError` | Service unavailable / network failure. |
| `APITimeoutError` | Request timed out. |
| `InternalServerError` | Cursor service returned a server error. |
| `NotFoundError` | Resource not found. |
| `AgentNotFoundError` | Agent doesn't exist or isn't visible under the current cwd. |
| `UnsupportedRunOperationError` | Run operation not supported for the current run state. Carries `operation`. |

`retry_after` is documented as **"an HTTP-style string (seconds, or an HTTP
date) supplied by the server when it's set"** — so a parser must handle both
`"120"` and `"Wed, 13 Aug 2026 09:00:00 GMT"`, and must tolerate `None`.

`AgentBusyError` deserves its own note: **`is_retryable` is `False`** and
retrying immediately keeps failing. The documented remedies are to wait for the
active run to reach a terminal status, `run.cancel()` it, or poll
`Agent.list_runs()`. **For local agents `AgentBusyError` is not raised at all** —
instead you pass `local={"force": True}` on `send()` to expire a stuck local run.

**The single most consequential sentence in this whole section** is
`RateLimitError`'s: *"Too many requests **or usage limits exceeded**."* That one
error class covers both halves of the distinction the entire product is built
around, with no documented field to tell them apart. Everything in §6 exists
because of that sentence.

---

## 4. Authentication

**Section confidence: A.** Source: [[c-api]], [[c-sdkpython]].

- `CURSOR_API_KEY` is the environment variable. `AgentOptions.api_key` overrides
  it per agent.
- Accepted key types for the SDK: **user API keys** (Cursor Dashboard → API
  Keys) and **service account API keys** (Team settings). **Team Admin API keys
  are not yet supported by the SDK.**
- Key format is `crsr_…`.
- The Cloud Agents REST API accepts both Basic (key as username, empty password)
  and Bearer.
- SDK runs follow the same pricing, request pools, and Privacy Mode rules as IDE
  and Cloud Agent runs, and appear in the team usage dashboard **under the SDK
  tag**.

cursorloop consequences:

- One env var to document: `CURSOR_API_KEY`. No `ANTHROPIC_*` anything.
- `doctor` verifies a key is present and *works* by calling `Cursor.me()` —
  which returns an `SDKUser` (`api_key_name`, `created_at`, optional
  `user_id`/`user_email`/…) — rather than by regex-matching the `crsr_` prefix.
  A key that parses and does not authenticate is the failure mode that matters.
- The redaction processor ported from `claudeloop/infrastructure/redact.py` must
  scrub `api_key`, `CURSOR_API_KEY`, `Authorization`, and any value matching
  `crsr_[A-Za-z0-9]+`.
- Repository-scoped API keys **cannot create no-repo cloud agents**; service
  account keys **cannot fall back to user OAuth for MCP**. Both are `doctor`
  checks, not runtime surprises.

**Never blocking, credential edition.** Unlike Codex there is no browser OAuth
step inside the SDK's own auth path — a key is a key. But MCP OAuth (§3.10) is
exactly that blocker one level down, and the same rule applies: a login flow is
only ever *reported* by a running loop, never *triggered*. Authentication
failure mid-run is terminal (exit non-zero) with a notification, never a retry
loop, which would spin uselessly forever.

---

## 5. CLI fallback: `agent -p`

**Section confidence: A** (the flags), **B** (the design position). Source:
<https://cursor.com/docs/cli/reference/parameters> [[c-cliparams]].

The Cursor CLI (`agent`) is a viable degraded-mode backend if the SDK bridge
cannot start (no wheel-bundled binary for the platform, a corporate policy
blocking the bridge, an SDK version regression). The relevant global options:

| Option | Meaning |
|---|---|
| `-p, --print` | Print responses to console, for scripts / non-interactive use. **Has access to all tools, including write and shell.** |
| `--output-format <fmt>` | `text` \| `json` \| `stream-json` (only with `--print`) |
| `--stream-partial-output` | Text deltas, with `--print` + `stream-json` |
| `--resume [chatId]` / `--continue` | Resume a chat / previous session |
| `--model <id>` | Model selection |
| `--mode <mode>` | `plan` or `ask`; agent is the default |
| `-f, --force` / `--yolo` | **Force allow commands unless explicitly denied** |
| `--sandbox <mode>` | `enabled` \| `disabled` |
| `--approve-mcps` | **Automatically approve all MCP servers** |
| `--trust` | **Trust the workspace without prompting (headless mode only)** |
| `--workspace <dir>` | Workspace directory |
| `--api-key <key>` | Also `CURSOR_API_KEY` |
| `-w, --worktree [name]` | Run in a new git worktree under `~/.cursor/worktrees/` |

Commands include `agent login|logout|status|whoami|about|models|mcp|sandbox|
worker|update|ls|resume|create-chat`.

The unattended invocation is therefore:

```bash
agent -p --force --trust --approve-mcps \
      --output-format stream-json --stream-partial-output \
      --model composer-2.5 --workspace "$PWD" "<prompt>"
```

**Design position:** this is a *fallback adapter behind the same
`AgentGateway` port*, not the primary path, and it is **M5, not M1**. Reasons:

- `--force`/`--yolo` and `--trust` are exactly the "bypass permissions" posture
  claudeloop demands an explicit opt-in for; a subprocess path re-introduces the
  stream-scraping fragility the whole project exists to delete.
- `stream-json`'s schema is not versioned in the docs the way the SDK
  dataclasses are.
- It is nevertheless worth having, because a runner that dies when one transport
  breaks is not an autonomous runner. Shipping it as a second adapter also
  proves the port abstraction is real, which is the same argument claudeloop
  makes for contract tests against fake and real adapters.

Note the contrast with codexloop, where the subprocess path is the *primary*
transport because no Python SDK exists at all. Here a first-party Python SDK
exists and is the better integration, so the same mechanism sits at the opposite
end of the preference order. Two forks of one blueprint reaching opposite
transport conclusions from the same reasoning is a sign the reasoning is doing
real work rather than being restated.

`agent worker start` (private cloud workers, `--pool`, `--label`,
`--management-addr` exposing `/healthz`, `/readyz`, `/metrics`) is noted here
only as future ops surface; it is out of scope for M1–M5.

---

## 6. Capacity taxonomy — **an invention**, and why

**Section confidence: C for the taxonomy, A for the inputs it consumes.**

> **This section defines vocabulary Cursor does not publish.** The Cursor SDK
> exposes `RateLimitError` with `is_retryable` / `retry_after` and a documented
> sentence that it covers *"Too many requests **or usage limits exceeded**"*.
> It does **not** publish a machine-readable discriminator between "your
> five-hour burst window is full, come back at 14:05" and "your plan's included
> usage is spent and your spend limit is capped, a human must act". cursorloop
> invents that discriminator, because the entire reason this project exists is
> that treating the second as the first produces an infinite sleep loop.

### 6.1 The two-axis model

Every terminal signal from a turn is reduced to exactly one `CapacityState`:

| `CapacityState` | Semantics | Waitable? | Has a reset instant? |
|---|---|---|---|
| `Available(utilization)` | A real turn may be spent. | — | — |
| `WindowExhausted(limit_kind, resets_at)` | A time-bounded window is full. Waiting *alone* fixes it. | **Yes** | Sometimes (`retry_after`), else `None` |
| `CreditsExhausted(can_purchase)` | Included usage / credits / spend cap exhausted. **Only a human topping up or raising the cap fixes it.** | Yes, but **only by probing** — never by sleeping to a deadline | **Never — the type does not carry the field** |
| `AuthenticationFailed(detail)` | Credentials invalid, revoked, or insufficient. | **No — terminal** | — |

`CreditsExhausted` deliberately has **no `resets_at` field at all** — not
`None`, the type literally cannot express one. This is copied verbatim from
claudeloop's domain model, where the skill file calls it "the single most
important fact in this codebase". Making it unrepresentable rather than
merely-`None` means the class of bug where someone writes
`sleep_until(state.resets_at or default)` cannot be typed.

### 6.2 The mapping table (vendor signal → invented state)

| Observed signal | Mapped `CapacityState` | Rationale |
|---|---|---|
| `RateLimitError`, `is_retryable=True`, `retry_after="120"` | `WindowExhausted("rate_limit", now+120s)` | Server told us when. Trust it, bounded (§7). |
| `RateLimitError`, `is_retryable=True`, `retry_after=<HTTP-date>` | `WindowExhausted("rate_limit", parsed_date)` | Same, absolute form. |
| `RateLimitError`, `is_retryable=True`, `retry_after=None` | `WindowExhausted("rate_limit", None)` | Waitable but unscheduled → configured interval. |
| `RateLimitError`, `is_retryable=False` | `CreditsExhausted(can_purchase=True)` | **The key inference.** A rate limit the server says will *never* clear by retrying is not a window — it is an exhausted allowance. |
| `RateLimitError` whose `code` / `proto_error_code` / `message` matches the billing lexicon (§6.3) | `CreditsExhausted` | **Checked before `retry_after`** so a stray Retry-After header can never make a spend cap look waitable. |
| HTTP `402 Payment Required`, or `403` with a billing-lexicon body | `CreditsExhausted` | Billing semantics regardless of exception class. |
| `AuthenticationError` | `AuthenticationFailed` | Terminal. Never retried. |
| `PermissionDeniedError` | `AuthenticationFailed` | Terminal. Retrying an authorization failure is a spin loop. |
| `run.status == "error"` + billing lexicon in `run.result` | `CreditsExhausted` | Non-thrown channel (§3.8). |
| `run.status == "error"` + rate-limit lexicon in `run.result` | `WindowExhausted("rate_limit", None)` | Non-thrown channel. |
| `run.status == "expired"` | `WindowExhausted("run_expired", None)` | Cloud-side expiry; re-send is legitimate. |
| `run.status == "cancelled"` | not a capacity state → `Available`; the run loop treats it as an operator/watchdog event | Cancellation is our own doing (§8). |
| `AgentBusyError` (cloud) | not a capacity state → `Busy` transient | Documented `is_retryable=False`, but the remedy is cancel-or-wait-for-terminal, not a capacity wait. |
| `NetworkError`, `APITimeoutError`, `InternalServerError` with `is_retryable=True` | not a capacity state → `TransientFault` | Bounded in-process retry with jittered backoff. Escalates to `Failed` after `--max-transient-retries`. |
| `ConfigurationError`, `BadRequestError` | terminal config failure, exit non-zero | Never retried; the request will never become valid. |
| `IntegrationNotConnectedError` | terminal config failure, message includes `provider` + `help_url` | A human must connect the SCM. Notify, do not loop. |
| `NotFoundError` / `AgentNotFoundError` on resume | terminal for that selector; `run` may start a fresh agent if `--allow-new-agent` | A vanished agent is not a capacity problem. |
| **Unrecognised `RateLimitError` shape** | `CreditsExhausted(can_purchase=True)` | **The safety default.** See below. |
| Nothing above; `run.status == "finished"` | `Available(utilization=None)` | The normal path. |

The unrecognised-shape row is the deliberate inversion of codexloop's equivalent
default, and the difference is instructive. codexloop defaults an unknown 429 to
`WindowExhausted(reset=None)` (bounded probing) because OpenAI's error space is
documented well enough that an unknown code is probably a *new throttle*.
Cursor's error space has exactly one rate-limit class covering both meanings, so
an unrecognised shape is equally likely to be billing — and since
`CreditsExhausted` also probes (it just probes on a slower cadence and notifies
a human), defaulting to it is strictly safer: the worst case is one spurious
notification and a slightly slower recovery, versus a silent multi-hour wait.

### 6.3 The billing lexicon

An ordered, **case-insensitive, configurable** list of substrings matched
against `error.code`, `error.proto_error_code`, and `error.message`, and against
`run.result` when the status is `"error"`.

**Tier 1 — credits and balance:**

```
out_of_credits, credits_required, insufficient_credits, no_credits,
credit_balance, credit_balance_exhausted, add_credits, purchase_credits,
top_up, topup_required
```

**Tier 2 — usage allowance and plan quota:**

```
usage_limit, usage_limit_reached, usage_limit_exceeded, usage_exceeded,
included_usage, plan_limit, plan_quota, plan_exhausted, quota_exceeded,
monthly_limit, monthly_quota, request_limit_reached, usage_not_included
```

**Tier 3 — spend caps set by the user or an admin:**

```
spend_limit, spending_limit, hard_limit, budget_exceeded, cap_reached,
spend_cap, admin_limit, team_limit
```

**Tier 4 — billing and subscription state:**

```
payment_required, payment_failed, billing, billing_error, upgrade_required,
subscription_expired, subscription_inactive, trial_expired, trial_ended
```

And the **counter-lexicon** — substrings that, absent any tier hit, positively
indicate a *waitable window* rather than an exhausted allowance:

```
too_many_requests, rate_limit_exceeded, rate_limited, slow_down,
concurrent_limit, requests_per, try_again_in, temporarily
```

Three honest caveats, recorded here so nobody later mistakes this for a
contract:

1. **These strings are inferred, not documented.** They are drawn from the
   product vocabulary Cursor uses across usage/pricing docs, the generic HTTP
   semantics of 402, and the codes OpenAI and Anthropic publish for the same
   concepts (on the reasonable assumption that billing vocabulary converges
   across vendors). They will drift.
2. **The lexicon must be user-overridable** via
   `CURSORLOOP_BILLING_LEXICON` / a config key, because a caught-late
   misclassification costs an operator hours of silent sleeping. The
   counter-lexicon is separately overridable via
   `CURSORLOOP_WINDOW_LEXICON`.
3. **Misclassification is asymmetric, and the code must be biased
   accordingly.** Classifying a *window* as *credits* costs at most a slightly
   more conservative probe cadence and a spurious notification. Classifying
   *credits* as a *window* re-creates the exact bug this project exists to
   delete. Therefore: **when a signal is ambiguous, prefer `CreditsExhausted`**,
   because `CreditsExhausted` never sleeps blind — it probes and notifies.

**Harvesting.** Every terminal error that matches nothing is written verbatim
(after redaction) to the run's audit log under an `unclassified_terminal_error`
event, and `cursorloop doctor --explain-error <file>` re-runs the classifier
offline against a captured payload. That turns lexicon maintenance from
guesswork into a data-collection loop, and it is the mechanism by which
confidence-C moves toward confidence-A over releases.

### 6.4 Ordering is load-bearing

The classifier's branch order, which must never be shuffled:

1. Auth / permission → `AuthenticationFailed`. Checked **first**; outranks all.
2. Billing lexicon hit (any channel, any tier) → `CreditsExhausted`.
3. `RateLimitError` with `is_retryable=False` → `CreditsExhausted`.
4. `RateLimitError` / HTTP 429 → `WindowExhausted(resets_at=parse(retry_after))`.
5. `run.status == "error"` with counter-lexicon hit → `WindowExhausted(None)`.
6. `run.status == "expired"` → `WindowExhausted("run_expired", None)`.
7. Transient network/5xx → `TransientFault` (gateway-local, not a capacity state).
8. Terminal config errors → `Failed`.
9. Everything else → `Available`.

The adversarial test that must exist from day one: **a `RateLimitError` carrying
both `retry_after="60"` and `code="usage_limit_reached"` must classify as
`CreditsExhausted`.** claudeloop has the exact analogue
(`tests/domain/test_classify.py`, credits-wins-over-`resets_at`).

A Hypothesis property test states the invariant directly rather than by example:
*no `TurnSignals` whose any-channel text contains a tier-1..4 lexicon entry can
produce a `CapacityState` carrying a `resets_at`.*

---

## 7. Waiting that notices a top-up

**Section confidence: A** (the policy is ours and is pure arithmetic; only the
probe mechanism depends on vendor behaviour).

Ported wholesale from claudeloop `domain/waiting.py`; the vendor changes but the
policy does not, because the policy is pure arithmetic over the ADT.

`next_probe_instant(state, *, now, started_waiting_at, probe_count, config) ->
datetime` — **always returns the next instant to probe, never a duration to
sleep.**

- **`CreditsExhausted`** — no reset exists by construction, so the only thing
  that can change is a human acting. Exponential backoff from
  `credits_probe_interval` (default 120 s) to `credits_probe_ceiling` (default
  600 s). Fire the `Notifier` **on entry**, so the human learns they need to act
  instead of discovering a stalled terminal tomorrow.
  *Implementation hazard inherited from claudeloop:* compute the backoff in
  float seconds and clamp to the ceiling **before** constructing a `timedelta` —
  `interval * factor**probe_count` unclamped overflows `timedelta`'s magnitude
  limit at realistic probe counts. A Hypothesis property test caught this in
  claudeloop; the same property test ships in cursorloop from day one.
- **`WindowExhausted(resets_at=X)`** — `min(X + reset_grace, now +
  window_probe_interval)`. The `resets_at` bound is the expected path; the
  interval bound is what catches an *early* lift (a plan upgrade, a spend-cap
  raise, an admin unblocking the team) before the nominal boundary.
- **`WindowExhausted(resets_at=None)`** — the configured
  `window_probe_interval`.
- `config.max_wait` clamps every candidate to `started_waiting_at + max_wait`;
  `wait_exceeded()` is the paired give-up check.

**The probe itself.** claudeloop's probe runs a one-token turn with
`max_turns=1`, no tools, `setting_sources=None`, and
`extra_args={"no-session-persistence": None}` so it leaves no transcript. Cursor
has no `no-session-persistence` flag, so cursorloop's probe is:

```python
Agent.prompt(
    "ok",
    AgentOptions(
        model=<probe model>,
        tools=[],                       # no built-in tools at all → text-only
        local=LocalAgentOptions(cwd=<cwd>),   # no setting_sources → hermetic
        name="cursorloop-probe",
    ),
)
```

`Agent.prompt()` creates, sends, waits, and **disposes** — so the throwaway
agent never pollutes the working agent's conversation, which is a cleaner
guarantee than claudeloop's flag-based approach. `tools=[]` is documented as
"no built-in tools; the model can only respond with text", which minimises both
cost and blast radius. A rejected probe is not billed for output.

**Probe cost accounting.** A *rejected* probe costs nothing, which is what makes
a repeated cadence affordable — but the probe that *succeeds* costs a handful of
tokens and, more importantly, is the probe that ends the wait. So the cadence is
bounded on both ends: a minimum interval so a fast-clearing throttle cannot turn
into a tight loop, and `--max-wait` so an indefinite exhaustion ends as a clean
failure at an operator-chosen time rather than as a process that is still
running next week. Probe tokens are charged against the same budget ledger as
work turns, and counted separately in the run summary so an operator can see
what the waiting cost.

Every probe result is diffed against the previous `CapacityState` and the
transition is logged explicitly — *"capacity restored at probe #7, 26m into the
wait; cause: RateLimitError no longer raised → resuming"* — so recovery is
visible in the audit log rather than inferred from a resumed turn.

---

## 8. Never blocking on a human

**Section confidence: A** (every mechanism is documented), **C** (that the
combination is *sufficient* — that is what the verification checklist tests).

The hard requirement: **the run never stalls waiting for an answer.** Notifying
a human is fine; *waiting* on one is not. Cursor removes claudeloop's primary
mechanism (`can_use_tool`) and supplies different ones. Every stall path and its
mitigation:

| Stall path | claudeloop mechanism | cursorloop mechanism |
|---|---|---|
| Tool permission prompt | `permission_mode="bypassPermissions"` | `.cursor/hooks.json` fragment: `beforeShellExecution`, `preToolUse`, `beforeMCPExecution`, `beforeReadFile` all return `{"permission": "allow"}` with exit 0. Hooks are **fail-open by default** on non-0/2 exits, which is the right failure direction here. |
| Belt-and-braces permission | `can_use_tool` callback returning `PermissionResultAllow` | No programmatic equivalent exists. Substitute: `local.auto_review=False` (never route tool calls through Auto-review, which is an interactive gate), plus a **toolset allowlist** so no un-allowlisted tool can even be offered. |
| The model asks a clarifying question mid-turn | intercept `AskUserQuestion`, deny with guidance | Cursor exposes no ask-user tool interception point. Substitute (three layers): (a) an **autonomy preamble** appended to every prompt stating no human is available and instructing the model to choose the option it would recommend, record the assumption inline, and proceed; (b) a `beforeSubmitPrompt` hook that re-injects the preamble if it is missing; (c) the **stall watchdog** below. |
| The model ends a turn with a question and stops | completion evaluator treats `complete: false` + no progress as continuation | Identical: the completion evaluator (§9) maps a non-`Done` turn to `Continue`, and the runner sends the next continuation prompt. A question is just a turn that isn't done. |
| Plan mode parks | `ExitPlanMode` auto-approved | Never create the agent in `mode="plan"` for autonomous runs; `mode="agent"` is the default and cursorloop sets it explicitly. `--plan-first` exists but always issues an explicit `SendOptions(mode="agent")` follow-up. |
| A local run gets wedged in an active state | n/a | **`SendOptions(local=LocalSendOptions(force=True))`** — documented as expiring a stuck active run before starting the message. cursorloop sets `force=True` on every retry send after a `Busy`/timeout, and exposes `--force-stuck-runs/--no-force-stuck-runs`. |
| Cloud agent busy | n/a | `AgentBusyError` → poll `Agent.list_runs()`, `run.cancel()` the active run if it is `"running"`, re-send. Documented remedy, implemented as a bounded loop, not a retry spin. |
| A turn produces no output and never terminates | budget caps + max_turns | **Stall watchdog:** a per-turn wall-clock deadline (`--turn-timeout`, default 30 min) and a no-delta deadline (`--stall-timeout`, default 10 min) driven by `on_delta` timestamps and `on_did_change_status`. On breach: `run.cancel()` (guarded by `run.status == "running"`), record a `turn_stalled` audit event, re-send with `local.force=True`. This is the mechanism that makes "no interception point for a question" survivable. |
| MCP OAuth login required | `doctor` fails fast, naming servers | Identical, and now documented by the vendor: the SDK "cannot open a browser to sign you in". `doctor` enumerates servers from `.cursor/mcp.json` + `~/.cursor/mcp.json` and reports which have no saved login. Service-account keys are additionally flagged, since they cannot fall back to user auth. |
| stdin / TTY | never inherit a TTY | Identical. The runner is safe under `nohup`, `systemd`, and CI. No code path reads stdin. The CLI-fallback adapter (§5) always passes `--print`, `--force`, and `--trust`, all of which are explicitly the non-interactive forms. |
| Workspace trust prompt (CLI fallback only) | n/a | `--trust` (documented: "Trust the workspace without prompting (headless mode only)"). |
| MCP approval prompt (CLI fallback only) | n/a | `--approve-mcps`. |

### 8.1 The managed hooks fragment — design sketch

cursorloop **must not silently overwrite a user's `.cursor/hooks.json`.** The
mechanism:

1. Write cursorloop's hook scripts under `.cursorloop/hooks/` (git-ignorable,
   inside the run state dir, never inside `.cursor/`).
2. On run start, read any existing `.cursor/hooks.json`, deep-merge cursorloop's
   entries *by appending* to each event's array, write the merged file, and
   record a SHA-256 of both the original and merged forms in
   `.cursorloop/state.json`.
3. On run end (including crash recovery via `cursorloop reset`), restore the
   original file iff the on-disk hash still matches what we wrote. If it does
   not match, leave the file alone and log loudly — the user edited it mid-run
   and their edit wins.
4. `--no-managed-hooks` disables the whole mechanism for operators whose repos
   already encode the right policy.

Since hooks are watched and reloaded automatically by Cursor, and since cloud
agents read hooks **from the repository**, cloud runs need the hook fragment
*committed* — which cursorloop will surface as a `doctor` warning rather than
attempting to commit on the user's behalf.

### 8.2 The autonomy preamble — content requirements

The preamble is the only mechanism standing between a clarifying question and a
parked run, so its text is a design artifact, not boilerplate. It must state, at
minimum: that no human is available for the duration of the run; that the model
should choose the option it would recommend rather than asking; that the chosen
assumption must be recorded inline in the response so it lands in the transcript
and can be reviewed; that `blocked_on` in the verdict block is reserved for
*genuine external* blockers (a missing credential, a third-party outage) and not
for "I would like guidance"; and the exact verdict-block format from §9.

It is appended to every prompt, not just the first, because context compaction
can drop it — and the `beforeSubmitPrompt` hook re-injects it if it is missing,
which covers the case where a prompt reaches the model by a path cursorloop did
not construct.

---

## 9. Completion detection — no `output_format`, so build one

**Section confidence: A** (that the vendor feature is absent), **C** (that our
convention is reliable enough — this is the weakest load-bearing part of the
design and is labelled as such in user docs).

**The finding:** claudeloop's completion story rests on
`ClaudeAgentOptions.output_format`, which hands the model a JSON schema and
returns a typed `ResultMessage.structured_output`:

```json
{"complete": bool, "remaining_work": [str], "blocked_on": str | null, "summary": str}
```

**The Cursor Python SDK has no equivalent.** There is no `output_format`, no
`response_format`, no structured-output schema anywhere in `AgentOptions`,
`LocalAgentOptions`, `CloudAgentOptions`, or `SendOptions`. `RunResult` carries
`status`, `result` (free text), `model`, `duration_ms`, `usage`, `git` — and
nothing schema-shaped.

**The replacement is a two-tier convention**, both tiers parsed from
`run.result` / `run.text()`:

**Tier 1 — a fenced verdict block.** The autonomy preamble instructs the model
to end every turn with exactly:

~~~text
```cursorloop-verdict
{"complete": false, "remaining_work": ["..."], "blocked_on": null, "summary": "..."}
```
~~~

The parser extracts the **last** ` ```cursorloop-verdict ` fence in the output,
`json.loads` it, and validates it into the same `StructuredVerdict` dataclass
claudeloop uses. Rules:

- **Last fence wins** — a model quoting the instruction earlier in its own
  output must not be mistaken for the verdict.
- Malformed JSON, a missing `complete` key, or a wrong type → treat as **absent**
  and fall through to tier 2. Never crash a multi-hour run on a bad brace.
- The block is stripped from any text shown to the user.
- A `stop` hook (`.cursor/hooks.json`) can additionally capture the final
  assistant text to a file under `.cursorloop/`, giving a second, out-of-band
  copy of the verdict in case stream consumption raced.

**Tier 2 — the sentinel marker.** When no valid verdict block is present, fall
back to substring-matching **`CURSORLOOP_TASK_FULLY_COMPLETE`** in the raw
output — the direct analogue of claudeloop's `CLAUDELOOP_TASK_FULLY_COMPLETE`
fallback, with the same two documented failure modes (collision with the user's
own prompt text; truncation inside a limit message coincidentally producing
marker-like text) and the same mitigation: **a capacity rejection is evaluated
first and always outranks a completion claim.**

**Tier 3 — the empty-turn soft failure**, ported verbatim: an empty, zero-cost
turn with no verdict becomes `Continue(("Waiting for a non-empty model
response",))`, and after `empty_turn_limit` consecutive empties becomes
`Blocked("repeated empty model responses")`. Without this, a model that returns
nothing forever is indistinguishable from progress.

**Tier 4 — plan reconciliation.** When the input is a markdown plan with
checkboxes, unchecked items are authoritative evidence that work remains,
regardless of what a turn claims. This is the only tier that can *contradict* a
`complete: true` verdict, and it is deliberately conservative: it downgrades
`Done` to `Continue`, never the reverse.

`blocked_on` remains terminal and outranks `complete`; it is reserved for true
external/human blockers, while waitable self-started work belongs in
`remaining_work` with `blocked_on: null`. That distinction is reinforced in both
the preamble text and the verdict-block schema description.

**Consequence for reliability:** cursorloop's completion detection is
*strictly weaker* than claudeloop's, because it depends on model compliance with
a text convention rather than a vendor-enforced schema. This must be stated
plainly in user docs, and it justifies two extra safeguards claudeloop does not
need: (a) a `--require-verdict` mode that treats N consecutive verdict-less
turns as `Blocked`; (b) the `WorkPlan` reconciliation of tier 4.

**Measure it before trusting it.** Q7 in §14 is an explicit conformance
experiment: run a schema'd plan twenty times and count verdict-block
conformance. If it is below roughly 90%, the marker becomes the primary
mechanism and the fence becomes the enrichment, inverting tiers 1 and 2.

---

## 10. Composer, Grok, and model profiles

**Section confidence: A.** Sources: <https://cursor.com/docs/models-and-pricing>
[[c-models]], <https://cursor.com/docs/models/cursor-composer-2-5> [[c-composer]],
<https://cursor.com/docs/models/grok-4-6> [[c-grok46]] (all fetched 2026-08-13).

**Composer ≠ Grok, and cursorloop is Composer-first.**

The **Cursor Models pool** contains three first-party models — **Composer 2.5**,
**Cursor Grok 4.6**, and **Cursor Grok 4.5** — all exempt from the Cursor Token
Rate and available on individual and team plans.

| Model | Identity | Effort levels | Fast variant |
|---|---|---|---|
| Composer 2.5 | Cursor's own agentic model, RL-trained on long-horizon coding tasks; tuned for tool use, file edits, terminal ops inside Cursor | — (effort calibration is internal) | yes |
| Cursor Grok 4.6 | Jointly trained by Cursor and SpaceXAI; frontier model for complex coding, improved instruction-following and long-horizon agentic work over 4.5 | `xhigh`, `high` (default), `medium`, `low` | yes |
| Cursor Grok 4.5 | Jointly trained by Cursor and SpaceXAI | `xhigh`, `high`, `medium`, `low` | yes |

The SDK-visible surface for all of this is `ModelSelection`:

```python
@dataclass(frozen=True)
class ModelSelection:
    id: str
    params: Sequence[ModelParameterValue] = ()


@dataclass(frozen=True)
class ModelParameterValue:
    id: str
    value: str
```

with `Cursor.models.list()` as the **source of truth** for valid ids, parameter
definitions, and preset variants for the calling account/team. The docs' worked
example shows `composer-2.5` exposing a `fast` parameter with values
`"false"`/`"true"`.

**The design position:**

- cursorloop's default is `composer-2.5`, chosen because it is Cursor's own
  agentic model, is cheapest in the pool, and is explicitly tuned for
  long-horizon tool-using work — which is exactly what an unattended runner does
  for hours.
- **Grok is a model profile, nothing more.** `domain/model_profile.py` (ported
  from claudeloop) carries `(model_id, params, effort, fast)` and the CLI
  exposes `cursorloop model <id>` / `cursorloop effort <level>` /
  `cursorloop preset <name>`. Shipping presets: `composer` (default),
  `composer-fast`, `grok` (→ `cursor-grok-4.6`, effort `high`),
  `grok-xhigh`, `grok-4.5`, `router-balanced`.
- **Model ids are never hard-coded as a closed set.** `Cursor.models.list()` is
  called by `doctor` and by `cursorloop model --list`, and an unknown id is
  rejected against the live catalog with a helpful message rather than against
  a stale constant. Cursor ships models faster than we ship releases.
- **Effort is model-conditional.** Composer's effort calibration is internal, so
  `cursorloop effort` against a Composer profile reports that rather than
  silently accepting a no-op that an operator would reasonably believe took
  effect.
- **Cursor Router** (`auto-smart` + `optimize_for ∈ {cost, balanced,
  intelligence}`) is supported as a profile, with the documented caveats: it is
  Teams/Enterprise, admins must enable it, `optimize_for` must always be passed
  explicitly (never omitted, never `default`), and the underlying model can
  change between requests — so the docs will steer anyone doing reproducible
  comparisons to a fixed model id.
- **An xAI-direct path is documented as out of scope.** Talking to xAI's API
  directly would be a second vendor, a second auth story, and a second capacity
  taxonomy, for a model that is already available through the Cursor catalog
  under the same key and the same pool. If it is ever wanted, it belongs behind
  the *existing* `AgentGateway` port as a third adapter, and it needs its own
  ADR. It is not part of M1–M5.

Per-run overrides are **sticky** (`SendOptions.model` changes the agent's
selection for subsequent sends), which the runner must account for: after a
one-off escalation to a higher-effort profile, it must explicitly send the base
profile back, or every remaining turn silently bills at the escalated rate. The
gateway therefore re-asserts the active profile on every send rather than
tracking whether it needs to, because "track whether it needs to" is the version
of this that has a bug in it.

---

## 11. The REST surface: Cloud Agents API v1

**Section confidence: A** (the endpoints and the beta warning), **B** (the
generate-from-OpenAPI recommendation). Sources: [[c-cloudapi]], [[c-api]].

**Status: public beta.** The docs state plainly: *"The Cloud Agents API v1 is in
public beta. APIs may change before general availability."* There is a full
**OpenAPI specification** published at `/docs-static/cloud-agents-openapi.yaml`.
Auth accepts Basic and Bearer. Base host is `api.cursor.com`.

Documented endpoint groups:

| Group | Endpoints |
|---|---|
| Agents | Create An Agent (`POST /v1/agents`), List Agents, Get An Agent |
| Runs | Create A Run, List Runs, Get A Run, **Stream A Run**, Cancel A Run |
| Usage | Get Agent Usage |
| Artifacts | List Artifacts, Download An Artifact |
| Lifecycle | Archive, Unarchive, Delete Permanently |
| Worker tokens | Create A User-Scoped Worker Token |
| Fleet management | List Workers, Get Fleet Summary, Get Worker By ID, List Pending Pool Requests |
| Metadata | API Key Info (`GET /v1/me`), List Models (`GET /v1/models`), List GitHub Repositories |

Webhooks are "coming soon" for v1; the legacy v0 API still supports them.

**The comparison that decides the design.** claudeloop's REST surface is
*generated* — it walks `anthropic.resources` class trees via `cached_property`
descriptors, binds 131 endpoints to Typer commands, and enforces a **drift gate**
test that fails CI when an SDK upgrade adds or removes an endpoint (ADR-0006:
never hand-write a snapshot that is silently incomplete after the next release).

Cursor's surface is different in three ways that matter:

1. **It is ~20 endpoints, not 131.** The economic argument for generation is
   much weaker.
2. **There is no Python client package whose class tree we can introspect.** The
   `cursor-sdk` package is an *agent* SDK, not a generated REST client; it
   exposes `client.agents`, `client.models`, `client.repositories` and nothing
   resembling a full endpoint tree. Generation would have to come from the
   OpenAPI YAML, not from Python introspection.
3. **It is beta and explicitly warned to change.** Generating a CLI from a
   moving spec is *better* than hand-writing one against it — but only if the
   generation source is stable enough to pin.

**Recommendation, to be recorded as an ADR:** generate the `cursorloop api`
sub-app **from the published OpenAPI document**, vendored into the repo at a
pinned digest, with a CI job that re-fetches the spec and fails on drift. This
preserves claudeloop's "no silent gaps" property with a different mechanism
suited to the different source. If the spec proves too unstable during M4
implementation, the fallback is to **defer the REST surface to post-1.0** and
ship only the handful of endpoints the runner itself needs
(`/v1/me`, `/v1/models`, agent create/get/cancel) as hand-written, explicitly
partial commands clearly labelled as such. Either way, the decision gets an ADR,
because "we shipped a partial CLI" must be a recorded choice, not an accident.

Note also that most of what an operator would want from the REST API is already
on the SDK client (`client.agents.list/get/list_runs/get_run/cancel_run`,
`client.models.list`, `client.repositories.list`, `Cursor.me()`) — so M4's user
value is mostly in the *fleet/worker/artifact* endpoints the SDK does not wrap.

---

## 12. Security notes

**Section confidence: A.**

Carried over from claudeloop's threat model, adjusted for Cursor:

- **Redaction.** The structlog processor must scrub `api_key`, `CURSOR_API_KEY`,
  `Authorization`, `authorization_token`, `access_token`, `refresh_token`,
  `client_secret`, and any `crsr_[A-Za-z0-9]{16,}` literal. Cursor's key format
  makes a regex scrub genuinely effective here — a small but real improvement on
  the blueprint, where Anthropic keys had no equally distinctive shape.
- **Secrets in MCP config.** `StdioMcpServerConfig.env` values are documented as
  passed *into the cloud VM*. `HttpMcpServerConfig.headers`/`auth` are handled by
  Cursor's backend and redacted before the VM sees them. cursorloop must never
  log a resolved MCP config, and its `doctor` output must print server *names*
  and transports, never env or headers.
- **Cloud `env_vars`.** Encrypted at rest, injected into the agent's shell,
  deleted with the agent; names cannot start with `CURSOR_`. cursorloop passes
  them through but never persists them in `.cursorloop/state.json`.
- **Autonomy is a chosen posture.** Auto-allowing every tool via hooks is the
  functional equivalent of claudeloop's `bypassPermissions`, and gets the same
  guardrails: explicit opt-in flag, refuse to run as root, refuse outside a git
  repository or an allowlisted directory unless overridden, and prefer
  `disallowed_tools` (which also blocks tools added after our SDK version) over
  a positive allowlist for anything security-sensitive.
- **Sandbox.** `LocalAgentOptions.sandbox_options` and the CLI's
  `--sandbox enabled` exist; cursorloop surfaces both and documents that
  sandboxing plus auto-allow is a materially safer combination than auto-allow
  alone. This is closer to codexloop's position (where `approval_policy=never`
  is orthogonal to `sandbox_mode`) than to claudeloop's, where autonomy required
  bypassing permissions wholesale.
- **The workspace-mutation risk is new.** claudeloop's autonomy lived entirely
  in process memory. cursorloop's writes a file into the user's repo. That is a
  genuinely worse security and safety posture, and the hash-verified
  merge/restore protocol (§8.1) plus `--no-managed-hooks` is the whole
  mitigation. It is called out in the threat model rather than buried in an
  implementation note.
- **Budget guardrails are a safety control**, not a nicety, for an unattended
  multi-hour loop: `--max-turns`, `--max-tokens`, `--max-cost`, `--max-wait`,
  `--max-attempts`, `--turn-timeout`. With `cost` sometimes `None` (§3.9),
  tokens are the enforceable cap.
- **No `shell=True` anywhere.** The CLI-fallback adapter builds an argv list.
  Plan-file and log paths are resolved and confined.
- **A per-agent advisory file lock** under `.cursorloop/locks/` prevents two
  runners from driving one agent concurrently — which on Cursor would surface as
  `AgentBusyError` storms rather than silent interleaving.
- **`.cursorloop/` must be git-ignored by default**, and `cursorloop init`
  should offer to add it, because run state contains prompts, transcripts, and
  potentially secrets echoed by tools.

---

## 13. Findings that become ADRs

| # | Decision | Driven by | Confidence | Risk if wrong |
|---|---|---|---|---|
| 0001 | Onion architecture enforced by `import-linter` | claudeloop blueprint | A | Low — proven |
| 0002 | **Cursor Python SDK over the `agent -p` subprocess** | [§3.2](#32-the-three-object-model-agent--run--sdkmessage), [§5](#5-cli-fallback-agent--p) | A | Low — upholds claudeloop ADR-0002; the SDK gives the durable-handle shape by default |
| 0003 | **`CreditsExhausted` is a distinct, non-waitable state with no reset field** | [§6](#6-capacity-taxonomy--an-invention-and-why) | A (principle) / C (the discriminator) | **Critical** — the whole product |
| 0004 | **The billing lexicon is an invention, configurable, and harvested from live errors** | [§6.3](#63-the-billing-lexicon) | C | High — wrong strings mean a wasted window, bounded by `--max-wait` |
| 0005 | Ambiguity resolves toward `CreditsExhausted`, not `WindowExhausted` | [§6.2](#62-the-mapping-table-vendor-signal--invented-state) | C | Low — the failure mode is a spurious notification, not a hang |
| 0006 | Adaptive probe loop, never a blind sleep | [§7](#7-waiting-that-notices-a-top-up) | A | High — a blind sleep misses a credit top-up |
| 0007 | **Never-block via managed `hooks.json` + preamble + `local.force` + stall watchdog**, since `can_use_tool` has no analogue | [§3.10](#310-mcp-skills-hooks-subagents--the-cursor-filesystem-contract), [§8](#8-never-blocking-on-a-human) | A (mechanisms) / C (sufficiency) | **Critical** — this is the other non-negotiable |
| 0008 | Hash-verified merge/restore of the user's `.cursor/hooks.json` | [§8.1](#81-the-managed-hooks-fragment--design-sketch) | A | Medium — a crashed run must never leave a mutated repo |
| 0009 | **Completion via a `cursorloop-verdict` fence + marker + empty-turn + plan reconciliation**, since there is no `output_format` | [§9](#9-completion-detection--no-output_format-so-build-one) | A (absence) / C (reliability) | High — a non-compliant model runs to a budget cap |
| 0010 | Composer-first; Grok is a model profile, never a product | [§10](#10-composer-grok-and-model-profiles) | A | Low — but scope creep here dilutes the taxonomy |
| 0011 | Model ids validated against `Cursor.models.list()`, never a constant | [§10](#10-composer-grok-and-model-profiles) | A | Low — additive |
| 0012 | Tokens are the hard budget cap; dollars best-effort, `None` ≠ `0` | [§3.9](#39-token-usage-get_usage-and-cost) | A | Medium — inverts claudeloop's emphasis |
| 0013 | **Generate the REST surface from a vendored, pinned OpenAPI doc — or defer with an ADR** | [§11](#11-the-rest-surface-cloud-agents-api-v1) | B | Low — bounded to M4 |
| 0014 | One `build_agent_options()` shared by create and resume | [§3.5](#35-agentresume) | A | Medium — the exact bug it prevents (silent loss of tools/model/MCP on resume) is documented behaviour |
| 0015 | Single-pass stream tee in `translate.py` | [§3.8](#38-run--status-result-and-the-errorexception-split) | A | Medium — a second read returns nothing |
| 0016 | `agent -p` as an optional second `AgentGateway` adapter at M5 | [§5](#5-cli-fallback-agent--p) | B | Low — additive, and it proves the port |
| 0017 | No `anthropic` / `claude_agent_sdk` anywhere, enforced by a grep test | [§2](#2-scope-naming-and-what-is-deliberately-not-here) | A | Low — but a copy-paste from the blueprint would otherwise be silent |

---

## 14. Open questions to resolve empirically

These are written as executable experiments, not as musings. Each has a
deterministic outcome that changes the implementation, and each has a defined
fallback so the project is never blocked waiting on an answer.

| # | Question | Experiment | If the answer is "no" / unfavourable |
|---|---|---|---|
| Q1 | Does a real usage-limit `RateLimitError` carry a distinguishing `code` or `proto_error_code`, or only prose in `message`? | Exhaust a test account's included usage; capture the exception's full field set | Lexicon matches `message` only; keep the parser forgiving and widen tiers from the captured wording |
| Q2 | Is `is_retryable=False` actually set on a billing exhaustion, or is it `True` with a far-future `retry_after`? | Same capture as Q1 | The lexicon becomes the *primary* discriminator and `is_retryable` demotes to a tiebreak; §6.4 ordering already puts the lexicon first, so this is a confidence change, not a code change |
| Q3 | Which `retry_after` form does Cursor actually emit — integer seconds or HTTP-date? | Force a burst throttle; log the raw string | Parser handles both plus `None`; on an unparseable value log verbatim and degrade to `WindowExhausted(None)`, never raise |
| Q4 | Does an errored run reliably put a classifiable string in `run.result`, or is it sometimes empty? | Table-driven capture across forced failure modes | Treat an empty `run.result` with `status=="error"` as an unrecognised shape → `CreditsExhausted` safety default, and notify |
| Q5 | Does `Agent.prompt(tools=[])` actually avoid creating a durable agent record visible to `client.agents.list()`? | Probe, then list agents before/after and diff | Probe against a temp workspace and prune, or accept the records and filter them by the `cursorloop-probe` name |
| Q6 | Does any SDK surface expose pre-rejection utilization (a "you are 80% through your window" signal)? | Inspect `run.usage`, `get_usage()`, and response `headers` on a near-limit account | None expected. Capacity stays probe-learned; revisit at every SDK bump |
| Q7 | Do Composer and Grok reliably emit the `cursorloop-verdict` fence? | Run a schema'd plan 20× per model; count conformance | Below ~90%: invert tiers — marker primary, fence enrichment — and make `--require-verdict` the default |
| Q8 | Are hooks re-read per-run, or cached for the life of the bridge? | Mutate `hooks.json` mid-run; observe whether the new policy takes effect | Materialise hooks *before* `launch_bridge` and treat them as immutable for the run; document that `permission-mode` changes take effect on the next run |
| Q9 | Does `local.force=True` reliably clear a wedged run, and what does it cost? | Wedge a local run (kill the bridge mid-turn), then send with `force=True` | Add a bounded cancel-then-recreate-agent escalation path behind the watchdog |
| Q10 | Does `AgentBusyError` ever surface for *local* agents despite the docs saying it does not? | Concurrent sends to one local agent | Handle it on both paths; the lock (§12) should make it unreachable anyway |
| Q11 | Do `tools` / `disallowed_tools` silently no-op on cloud agents, or raise? | Create a cloud agent with a deny-list and attempt a denied tool | If silent, `doctor` warns that toolset restrictions are local-only and the security posture for cloud runs rests on hooks + sandbox |
| Q12 | Is the Cloud Agents OpenAPI document stable enough to pin across a release cycle? | Fetch weekly for the M4 window; diff | Take the deferral branch of ADR 0013 and ship the four endpoints the runner needs |
| Q13 | What is the minimum `cursor-sdk` version exposing `local.force`, `on_delta`, `Agent.resume`, and `tools=[]`? | Bisect across published versions in CI | Raise the documented floor; `doctor` fails fast below it |
| Q14 | Does `setting_sources` allow loading project *skills* without project *MCP*? | Try each `SettingSource` value and enumerate what loads | Documented as coupled (risk R6); `doctor` reports what each choice would load, before the run |

**Until Q1–Q14 are answered, the implementation assumes the pessimistic branch
of each.** That is why the wait policy is a bounded probe loop rather than a
scheduled wake-up, why the classifier reads four channels rather than one, and
why completion has four tiers instead of a schema: the optimistic path is an
optimisation applied when a signal happens to be available, never a
precondition for correctness.

---

## 15. Open risks

| # | Risk | Impact | Mitigation / trigger to revisit |
|---|---|---|---|
| R1 | **The billing lexicon (§6.3) is inferred, not documented.** Cursor may use wording we don't match. | A credits exhaustion misclassified as a window → a bounded-but-wrong wait, then a `max_wait` failure. Not an infinite loop (the `max_wait` clamp saves us) but a wasted window. | Bias ambiguity toward `CreditsExhausted`; make the lexicon configurable; capture every unmatched terminal error verbatim into the audit log so real-world wording can be harvested; add a `cursorloop doctor --explain-error <file>` to classify a captured payload offline. |
| R2 | **`retry_after` semantics are only "HTTP-style"**; we have not observed a real one. | A parse failure could produce a `None` reset and a slower-than-necessary recovery. | Parse both integer-seconds and HTTP-date; on failure log the raw string and degrade to `WindowExhausted(None)`, never crash. Property-test the parser. |
| R3 | **No structured output** (§9). Completion depends on model text compliance. | A model that ignores the verdict convention runs until a budget cap. | Marker fallback + `WorkPlan` checkbox reconciliation + `--require-verdict` + empty-turn soft-fail. Revisit immediately if Cursor ships structured output. |
| R4 | **Hooks are file-based only**, so autonomy policy mutates the user's workspace. | A crashed run could leave a modified `.cursor/hooks.json`. | Hash-verified merge/restore (§8.1), `cursorloop reset` recovery command, `--no-managed-hooks` escape hatch, and never write inside `.cursor/` except the single merged `hooks.json`. |
| R5 | **Cloud Agents API v1 is beta and warned to change** (§11). | An M4 REST surface could break between releases. | Vendored pinned OpenAPI + drift CI job; ADR recording the defer-vs-generate decision; keep M1–M3 free of any REST dependency. |
| R6 | **`local.setting_sources` gates skills *and* MCP together.** There is no documented way to load project skills without also loading project MCP. | A hermetic run that wants repo skills may pull in repo MCP servers, one of which needs OAuth. | `doctor` enumerates what each `setting_sources` choice would load, before the run. Default to no setting sources; `--setting-sources project` is opt-in and documented as also enabling project MCP. |
| R7 | **Sticky per-run model overrides** (§10). | A one-off escalation silently persists and bills every later turn at the higher rate. | The gateway always re-asserts the active profile on the next send; an audit event records the effective `run.model` per turn; a test asserts the profile is restored. |
| R8 | **Streams are consumable once** (§3.8). | An adapter that streams to the UI and then re-reads for classification gets an empty second pass. | One canonical consumption path in `infrastructure/agent/translate.py` that tees into a buffer; a contract test asserts a run can be both UI-streamed and classified from a single pass. |
| R9 | **`get_usage()` cost settles late** (§3.9). | A dollar budget cap silently under-counts. | Tokens are the hard cap; `cost is None` is *unknown*, never `0`; the ledger records `cost_pending` and the final summary reconciles once more after the run. |
| R10 | **`AgentBusyError` has `is_retryable=False`** but the correct action is still to retry after cancelling. | A naive `if not is_retryable: raise` (the pattern in Cursor's own docs example) would abort a recoverable run. | `AgentBusyError` is handled *before* the generic `is_retryable` check, with the documented cancel-then-resend remedy and a bounded attempt count. |
| R11 | **Bridge binary availability.** The SDK ships a `cursor-sdk-bridge` binary per wheel. | An unsupported platform/architecture, or a policy that blocks unsigned binaries, kills the primary adapter. | `doctor` runs `cursor-sdk-bridge --help`; the CLI-fallback adapter (§5) exists precisely for this; both are behind the same port. |
| R12 | **Local persistence is workspace-scoped** and bridge-managed. | Resuming from a different cwd silently finds no agents (`AgentNotFoundError`). | Always pass `workspace=` on `launch_bridge` and `cwd=` on local list/get; persist the absolute workspace path in `.cursorloop/state.json` and refuse to resume from a mismatched cwd without `--allow-cwd-change`. |
| R13 | **`tools`/`disallowed_tools`/`custom_tools`/inline MCP do not persist across resume.** | A resumed run silently loses its safety restrictions. | A single `build_agent_options()` used by both create and resume; a test that resumes and asserts the full option set was re-applied. |
| R14 | **Grok scope creep.** Pressure to make Grok "its own thing". | Two products, two adapters, a diluted taxonomy. | Written into the non-negotiables: Grok is a model profile. Any change requires an ADR that first explains why a profile is insufficient. |
| R15 | **No pre-rejection capacity telemetry** (§3.9, Q6). | cursorloop cannot warn "you are about to hit a limit"; it can only react. | Accepted. The probe loop is the whole answer, and it is bounded. Re-check at every SDK bump; if utilization ever appears, it becomes an `Available(utilization)` payload and an optional pre-emptive pause. |
| R16 | **`cursor-sdk` is young and moving.** Field names and defaults may shift between minor versions. | A silent behaviour change mid-release-cycle. | Pin a tested range (floor + known-good ceiling); record the resolved version in the audit log at run start; keep every SDK touchpoint inside `infrastructure/agent/` so a break is a one-directory diff. |

---

## 16. Divergences from the claudeloop blueprint

Recorded explicitly so a reader familiar with the blueprint can find the seams
fast, and so each divergence is a decision rather than a drift.

| Area | claudeloop | cursorloop | Why |
|---|---|---|---|
| Durable session | `ClaudeSDKClient`, argued for in ADR-0002 | `Agent`, the SDK default | Cursor gives the good shape for free |
| Session discovery | `list_sessions()` API replacing a `~/.claude/projects/` glob | `client.agents.list(runtime="local", cwd=…)` | Both supported; Cursor's is workspace-scoped, which adds risk R12 |
| Permission bypass | `permission_mode="bypassPermissions"` + `can_use_tool` | Managed `hooks.json` + `disallowed_tools` + `auto_review=False` | No programmatic callback exists |
| Ask-user interception | `AskUserQuestion` denied with guidance | Autonomy preamble + `beforeSubmitPrompt` re-injection + stall watchdog | No interception point exists |
| Completion | Vendor-enforced `output_format` schema | Four-tier convention | No structured output exists |
| Capacity discriminator | Documented `credits_required` / `out_of_credits` fields | Inferred billing lexicon over four text channels | Cursor publishes one error class for both meanings |
| Reset instant | `RateLimitEvent.resets_at`, typed | `retry_after`, HTTP-style string | Weaker, hence the both-forms parser |
| Pre-rejection telemetry | `RateLimitEvent.utilization` | None | Probe-only capacity awareness |
| Budget hard cap | Dollars (`total_cost_usd`, exact and immediate) | Tokens (`cost` settles late and can be `None`) | Inverted emphasis, §3.9 |
| REST surface | Generated from a Python class tree, 131 endpoints, drift gate | Generated from a vendored OpenAPI doc, ~20 endpoints — or deferred | No Python REST client to introspect |
| Sandbox vs autonomy | Coupled — autonomy meant bypassing permissions | Orthogonal — `sandbox_options` composes with auto-allow hooks | Strictly better posture, closer to codexloop's |
| Workspace mutation | None; autonomy lived in memory | Writes a merged `.cursor/hooks.json` | Strictly worse posture; mitigated by §8.1 |

---

## 17. Citation index

| Key | Source | Fetched |
|---|---|---|
| [c-sdkpython] | Cursor Python SDK reference — `Agent`, `Run`, `AgentOptions`, errors, usage, MCP/skills/hooks/subagents. <https://cursor.com/docs/sdk/python> | 2026-08-13 |
| [c-api] | APIs overview — authentication, key types, rate limits, error codes. <https://cursor.com/docs/api> | 2026-08-13 |
| [c-cloudapi] | Cloud Agents API v1 endpoints + OpenAPI link + beta warning. <https://cursor.com/docs/cloud-agent/api/endpoints> | 2026-08-13 |
| [c-hooks] | Hooks — events, exit-code semantics, cloud support, config sources. <https://cursor.com/docs/hooks> | 2026-08-13 |
| [c-skills] | Agent Skills — directories, `SKILL.md`, frontmatter, nesting, compatibility paths. <https://cursor.com/docs/skills> | 2026-08-13 |
| [c-cliparams] | CLI parameters — `agent -p`, `--force`, `--trust`, `--approve-mcps`, `--output-format`. <https://cursor.com/docs/cli/reference/parameters> | 2026-08-13 |
| [c-models] | Models & pricing — the Cursor Models pool, Token Rate exemption. <https://cursor.com/docs/models-and-pricing> | 2026-08-13 |
| [c-composer] | Composer 2.5 — identity, agentic tuning, `fast` parameter. <https://cursor.com/docs/models/cursor-composer-2-5> | 2026-08-13 |
| [c-grok46] | Cursor Grok 4.6 — effort levels, fast variant, joint training. <https://cursor.com/docs/models/grok-4-6> | 2026-08-13 |
| [c-claudeloop] | claudeloop 0.5.4 — the blueprint. `docs/plans/architecture-and-roadmap.md`, `src/claudeloop/domain/`, ADRs 0001–0007. <https://github.com/adammatthewsteinberger/claudeloop> | local |
| [c-outline] | Shared transplant outline across the `*loop` forks. [`_shared-transplant-outline.md`](_shared-transplant-outline.md) | local |
| [c-roadmap] | cursorloop architecture and roadmap — the design this document justifies. [`architecture-and-roadmap.md`](architecture-and-roadmap.md) | local |
