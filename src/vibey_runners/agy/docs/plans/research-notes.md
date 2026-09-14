# agyloop — vendor research notes: the Google Antigravity SDK, the `agy` CLI, and Gemini capacity semantics

> **Status.** Pre-implementation research record, compiled 2026-08-13. This
> document exists to make the design decisions in
> [`architecture-and-roadmap.md`](architecture-and-roadmap.md) *auditable*: every
> non-obvious call there traces back to a numbered finding here, and every
> finding here carries the source it came from and a confidence marker. Nothing
> in this file is product code and nothing here is a promise about vendor
> behavior — it is a snapshot of what the vendor documented on the retrieval
> date, plus explicit flags on the parts that are still unverified.
>
> **Blueprint.** `agyloop` forks the design (not the code) of
> [`claudeloop` 0.5.4](https://github.com/adammatthewsteinberger/claudeloop) —
> an onion-architected autonomous Claude Code session runner whose two
> non-negotiables are (1) **never block on a human** and (2) **never conflate an
> exhausted rate-limit window (waitable, has a reset instant) with exhausted
> credits/billing (not waitable, needs a human to pay)**. Everything below asks
> the same two questions of the Google Antigravity / Gemini stack, and the
> answers are materially harder than they were for Anthropic.

## Contents

0. [Why this document exists](#0-why-this-document-exists)
1. [Method, confidence scale, and the gating rule](#1-method-confidence-scale-and-the-gating-rule)
2. [Source inventory](#2-source-inventory)
3. [F1 — The SDK's shape: `Agent` + `LocalAgentConfig`](#f1--the-sdks-shape-agent--localagentconfig)
4. [F2 — Policies: `allow_all()` is the autonomy switch](#f2--policies-allow_all-is-the-autonomy-switch)
5. [F3 — Hooks: nine lifecycle points, three categories](#f3--hooks-nine-lifecycle-points-three-categories)
6. [F4 — Structured output: the completion verdict](#f4--structured-output-the-completion-verdict)
7. [F5 — `ask_question` and the never-block rule](#f5--ask_question-and-the-never-block-rule)
8. [F6 — Session persistence via `conversation_id`](#f6--session-persistence-via-conversation_id)
9. [F7 — Errors: four exception types, no typed rate-limit event](#f7--errors-four-exception-types-no-typed-rate-limit-event)
10. [F8 — Gemini capacity: four independent dimensions](#f8--gemini-capacity-four-independent-dimensions)
11. [F9 — `RESOURCE_EXHAUSTED` is ambiguous; classify with details](#f9--resource_exhausted-is-ambiguous-classify-with-details)
12. [F10 — `UsageMetadata`: the budget ledger's input](#f10--usagemetadata-the-budget-ledgers-input)
13. [F11 — The `agy` CLI, and the sandbox trap](#f11--the-agy-cli-and-the-sandbox-trap)
14. [F12 — The capacity probe, and why probing is not free](#f12--the-capacity-probe-and-why-probing-is-not-free)
15. [F13 — Auth: two lanes, ADC by default](#f13--auth-two-lanes-adc-by-default)
16. [F14 — REST surface feasibility for M4](#f14--rest-surface-feasibility-for-m4)
17. [Consolidated implications — findings → design decisions](#17-consolidated-implications--findings--design-decisions)
18. [Findings that become ADRs](#18-findings-that-become-adrs)
19. [Open questions to resolve empirically](#19-open-questions-to-resolve-empirically)
20. [Non-goals of this research](#20-non-goals-of-this-research)
21. [Citation index](#21-citation-index)

---

## 0. Why this document exists

claudeloop got its second non-negotiable almost for free, because the Claude
Agent SDK surfaces a *typed* `RateLimitEvent` carrying `status`, `resets_at`,
`rate_limit_type`, and separate overage fields — so "is this waitable?" is a
field comparison.

**The single most consequential research finding for agyloop is that the Google
stack does not hand us that.** Google's rejection signal is an HTTP `429` with
`status: RESOURCE_EXHAUSTED` and a human-readable message, and the
discriminating information — *which* quota, *how long*, *is it spend-based* —
lives in *optional* error `details` and in the message text. Classification is
therefore a real inference problem here, not a field read, which is exactly why
it must live in a pure, exhaustively-tested `domain/classify.py` rather than
being smeared across adapters.

The second most consequential finding is that Gemini's capacity model has **four
independent dimensions** (RPM, TPM, RPD, spend) where Claude had essentially
two, and they have wildly different recovery characteristics — seconds, minutes,
up to 24 hours, and *never*. Collapsing them, in either direction, produces a
runner that is either uselessly slow or catastrophically stuck.

Everything below is organized to support those two conclusions and their
consequences.

---

## 1. Method, confidence scale, and the gating rule

Sources were gathered from Google's published Antigravity SDK documentation and
its Python repository source, Google's Gemini API documentation (rate limits,
troubleshooting, API errors), the Antigravity CLI documentation and issue
tracker, and — where Google has published nothing — from third-party
integrations and community reports that ship code against the same surfaces.
Third-party evidence is *not* treated as equivalent to a spec; it is treated as
a hypothesis the implementation must verify at runtime and degrade gracefully
when it fails.

| Marker | Meaning | How agyloop is allowed to use it |
|---|---|---|
| **[V] — verified** | Stated in primary vendor documentation or visible in the published SDK source. | May be relied on in a hot path. Still guarded by a parse-failure fallback. |
| **[S] — secondary** | Community guide, developer-forum thread, third-party cheat sheet, or an independent project shipping code against the same surface. | May inform design and may be used as an *optimisation*, never as the sole input to a capacity decision. Must be re-verified before code depends on it. |
| **[U] — unverified** | An open question. Nothing published either way. | A design must not *require* this to be true; it may only *opportunistically* exploit it behind a feature check, with a documented fallback. |

The rule that falls out of this table, and the single most important design
constraint in the project:

> **A capacity decision is never allowed to depend on an [S] or [U] signal
> alone.** Every classification path must terminate in a defensible answer even
> if every optional telemetry source returns nothing, every `details[]` entry is
> stripped, and every message pattern fails to match.

The practical consequence is the *ambiguity default*: when the ladder in
[F9](#f9--resource_exhausted-is-ambiguous-classify-with-details) runs out of
rungs, the answer is **bounded probing under `--max-wait`** — never an unbounded
sleep (which would hang for a day on a billing wall) and never an optimistic
tight retry (which would burn RPD chasing a quota that will not return today).

---

## 2. Source inventory

Primary sources, all retrieved 2026-08-13:

| # | Source | URL |
|---|---|---|
| S1 | Google Antigravity blog — *Introducing the Google Antigravity SDK* | <https://antigravity.google/blog/introducing-google-antigravity-sdk> |
| S2 | Antigravity SDK docs — Overview + Quick Start | <https://antigravity.google/docs/sdk/overview> |
| S3 | `google-antigravity/antigravity-sdk-python` — repository README | <https://github.com/google-antigravity/antigravity-sdk-python> |
| S4 | SDK source — `google/antigravity/types.py` | <https://github.com/google-antigravity/antigravity-sdk-python/blob/main/google/antigravity/types.py> |
| S5 | SDK source — `google/antigravity/agent.py` | <https://github.com/google-antigravity/antigravity-sdk-python/blob/main/google/antigravity/agent.py> |
| S6 | SDK source — `google/antigravity/hooks/README.md` | <https://github.com/google-antigravity/antigravity-sdk-python/blob/main/google/antigravity/hooks/README.md> |
| S7 | SDK source — `google/antigravity/conversation/README.md` | <https://github.com/google-antigravity/antigravity-sdk-python/blob/main/google/antigravity/conversation/README.md> |
| S8 | Gemini API — **Rate limits** | <https://ai.google.dev/gemini-api/docs/rate-limits> |
| S9 | Gemini API — **Troubleshooting guide** | <https://ai.google.dev/gemini-api/docs/troubleshooting> |
| S10 | Gemini API — **API errors** | <https://ai.google.dev/gemini-api/docs/api-errors> |
| S11 | Antigravity CLI docs — **Permissions** | <https://antigravity.google/docs/cli/permissions> |
| S12 | `antigravity-cli` issue #36 — *Agent can bypass sandbox when combining `--sandbox` with `--dangerously-skip-permissions`* | <https://github.com/google-antigravity/antigravity-cli/issues/36> |
| S13 | Gemini API — Generating content (REST reference) | <https://ai.google.dev/api/generate-content> |
| S14 | Google Gen AI SDK (`google-genai`) reference | <https://googleapis.github.io/python-genai/> |
| S15 | Gemini API discovery / OpenAPI availability (cookbook issue #261) | <https://github.com/google-gemini/cookbook/issues/261> |
| S16 | Gemini Enterprise Agent Platform — Error code 429 | <https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/deploy/error-code-429> |

Secondary / corroborating (treated as **[S]** throughout):

| # | Source | URL |
|---|---|---|
| X1 | Antigravity CLI tutorial (Google Cloud Medium) — full `agy --help` capture | <https://medium.com/google-cloud/antigravity-cli-tutorial-series-12b46cfe3bf2> |
| X2 | Antigravity CLI cheat sheet — permission presets | <https://toolsbase.dev/en/reference/antigravity-cli-commands> |
| X3 | `imbue-ai/catalyst` commit — *Run agy sandboxed; auto-approve via permissions policy (not skip-permissions)* | <https://github.com/imbue-ai/catalyst/commit/430f31fd82182881c5e13c47593847d512457c5c> |
| X4 | Gemini API developer forum — *Handling 429 / 503 errors* | <https://discuss.ai.google.dev/t/handling-429-503-errors-from-the-gemini-api/124640> |
| X5 | Gemini API developer forum — *RPD is not being reset* | <https://discuss.ai.google.dev/t/rpd-is-not-being-reset/145704> |
| X6 | claudeloop 0.5.4 — the blueprint being forked | <https://github.com/adammatthewsteinberger/claudeloop> |

---

## F1 — The SDK's shape: `Agent` + `LocalAgentConfig`

**Confidence: [V].**

The package is `google-antigravity` on PyPI (S2). The high-level surface is
deliberately tiny — an async context manager wrapping a persistent session:

```python
import asyncio
from google.antigravity import Agent, LocalAgentConfig


async def main() -> None:
    config = LocalAgentConfig()
    async with Agent(config) as agent:
        response = await agent.chat("What files are in the current directory?")
        print(await response.text())


asyncio.run(main())
```

(S1, S2, and S3 all publish this same fifteen-line quick start, which is a
useful corroboration signal in itself: three vendor surfaces agreeing on one
entry point means the entry point is unlikely to move soon.)

The SDK describes itself as "the same agent runtime that powers Antigravity 2.0
and the Antigravity CLI" (S1) — i.e. the SDK and the `agy` binary are two front
doors onto one harness. That matters for agyloop: **a single `AgentGateway` port
can plausibly have both an SDK adapter and a CLI adapter with equivalent
semantics**, which is exactly the hedge we want while the SDK is in preview.

Layering, per S1/S7:

| Layer | Object | What it's for |
|---|---|---|
| L1 | `Agent` | Lifecycle: binary discovery, tool wiring, hook registration, policy defaults. Most code only needs this. |
| L2 | `Conversation` (`agent.conversation`) | Stateful session: `history`, `total_usage`, `send()` + `receive_steps()`, `connection`. |
| L3 | `Connection` | Transport / backend abstraction. |

**Implication for agyloop.** `infrastructure/agent/gateway_sdk.py` binds L1 for
the normal path and reaches into L2 for usage accounting and step-level
streaming. It must never leak either type past the infrastructure boundary — the
port returns our own `TurnOutcome` DTO.

### F1.1 `Agent.chat()` and `ChatResponse` **[V]**

From S5 and S4:

- `async def chat(self, prompt: types.Content) -> types.ChatResponse` — raises
  `ValueError` for `None`, empty, or whitespace-only prompts, and for empty
  sequences. **agyloop must never send an empty continuation prompt**; the
  continuation-prompt builder needs a non-empty guarantee at the domain level,
  enforced by a type invariant rather than by an adapter-level check, because
  the adapter is the wrong place to discover a domain bug.
- `ChatResponse` is an async stream of semantic chunks with lazy buffering.
  Every iterator (`.chunks`, `.thoughts`, `.tool_calls`, and
  `async for delta in response`) returns an **independent cursor** over a shared
  buffer; cursors are safe to consume sequentially *or* concurrently via
  `asyncio.gather`. If the upstream stream raises, the error is stored and
  **re-raised to every cursor that reaches the end of the buffer**.
- `await response.text()` drains and aggregates all `Text` chunks.
- `await response.structured_output()` drains, then returns the parsed
  structured payload or `None`.
- `response.usage_metadata` exposes accumulated `UsageMetadata` for the turn.

**Implication, and it is load-bearing.** The "error is stored and re-raised to
every cursor" behavior means a capacity rejection mid-stream surfaces as an
*exception at drain time*, not as a tidy typed event. Our gateway must wrap the
whole drain in a `try/except` and translate exceptions into `TurnSignals` — see
[F7](#f7--errors-four-exception-types-no-typed-rate-limit-event). It also means
partial output is potentially available *before* the exception: any text the
model emitted before the rejection is in the buffer, and the chatter log should
preserve it rather than discarding the turn wholesale.

### F1.2 `StreamChunk` taxonomy **[V]**

`StreamChunk` base with `Thought` and `Text` subclasses (S4); `ToolCall` and
`ToolResult` are interleaved into the same chunk stream. Multimodal content
types exist: `Image`, `Document`, `Audio`, `Video`.

**Implication.** agyloop's chatter log (the human-readable narration stream
claudeloop writes to `chatter.jsonl`) maps cleanly: `Thought` → thinking lines,
`Text` → assistant lines, `ToolCall`/`ToolResult` → tool lines. The multimodal
types are irrelevant to M1–M3 and are recorded here only so the translator's
`match` statement is exhaustive from day one rather than growing an
`UNKNOWN`-shaped hole later.

### F1.3 `Step` / `StepType` **[V]**

`StepType ∈ {TEXT_RESPONSE, TOOL_CALL, SYSTEM_MESSAGE, COMPACTION, FINISH,
UNKNOWN}`; `StepSource ∈ {SYSTEM, USER, MODEL, UNKNOWN}`; plus `StepTarget`,
`StepStatus`. Each `Step` may carry `usage_metadata` (S4).

Two of these are directly useful to us:

- **`FINISH`** is where structured output lands (see
  [F4](#f4--structured-output-the-completion-verdict)).
- **`COMPACTION`** tells us the harness compacted context. claudeloop had no
  equivalent signal; agyloop should log it as a first-class event, because a
  compaction mid-run is a strong hint that the "remaining work" list is at risk
  of drifting and the plan reconciliation should be re-anchored.

The presence of `UNKNOWN` in *both* enums is itself a design instruction from
the vendor: the step vocabulary is expected to grow. Our translator must handle
`UNKNOWN` as "log it and continue," never as an error.

---

## F2 — Policies: `allow_all()` is the autonomy switch

**Confidence: [V].**

Out of the box, `LocalAgentConfig` **enables all builtin tools but applies a
`confirm_run_command()` policy — most tools work without friction, but shell
access is denied by default** (S1). The documented way to get full autonomy:

```python
from google.antigravity import Agent, LocalAgentConfig
from google.antigravity.hooks import policy

config = LocalAgentConfig(policies=[policy.allow_all()])
```

The general policy vocabulary (S1, S2, S6):

```python
from google.antigravity.hooks.policy import deny, allow, ask_user, enforce

policies = [
    deny("*"),  # block everything by default
    allow("view_file"),  # except reading files
    deny("run_command", when=lambda args: "rm" in args.get("CommandLine", "")),
    ask_user("run_command", handler=my_approval_fn),
]
hook = policy.enforce(policies)  # -> a PreToolCallDecideHook
```

Key properties from S6:

- Evaluation is **declarative and priority-based**, top-down; `policy.enforce()`
  compiles a policy list into a single `PreToolCallDecideHook`.
- `ask_user` policies **require a handler that receives the full `ToolCall` and
  returns `True` (approve) or `False` (deny)**. Note that the handler is *our*
  code — which is what makes a synchronous, non-blocking denial possible.
- There is a documented `policy.workspace_only()` helper that scopes
  file-operation tools to specific workspace directories (referenced from
  `BuiltinTools.file_tools()` in S4).

### F2.1 Disabling ≠ denying **[V]**

S4/S6 draw this distinction sharply, and it is the single most useful piece of
policy guidance for us:

| Mechanism | Effect | Token cost | Model awareness |
|---|---|---|---|
| `CapabilitiesConfig.disabled_tools` | Tool's schema is **stripped from the model's context entirely** | Saves tokens | Model never sees it, never tries |
| `policy.deny(...)` | Tool stays visible; call is **rejected at runtime** with a denial message | Costs tokens, may cause retries | Model learns *why* and can adapt |

Vendor guideline (S4): prefer `disabled_tools`/`enabled_tools` for tools the
agent should *never* use; use `policy.deny()` for conditional restrictions that
depend on arguments or context.

**Implication for agyloop's never-block rule.** This gives us a principled
choice for `ask_question`, and it is *not* "disable it." See
[F5](#f5--ask_question-and-the-never-block-rule).

### F2.2 `BuiltinTools` enum **[V]**

Full membership, from S4:

```
list_directory, search_directory, find_file, view_file, create_file,
edit_file, run_command, ask_question, start_subagent, generate_image,
search_web, finish
```

With classmethod groupings: `read_only()` (`list_directory`,
`search_directory`, `find_file`, `view_file`, `finish`), `nondestructive()`
(everything except `run_command`), `file_tools()` (`view_file`, `create_file`,
`edit_file`), `all_tools()`, `none()`.

**Implication.** `BuiltinTools.read_only()` (or `none()`) is exactly the right
tool set for the **capacity probe**
([F12](#f12--the-capacity-probe-and-why-probing-is-not-free)) — a throwaway turn
that must cost as little as possible and must not mutate the workspace. And
`nondestructive()` is a good default for a `--safe` run mode we should expose.

Two members are worth flagging as autonomy hazards in their own right:
`start_subagent` (a subagent inherits the parent's policies per S6, so an
autonomy hole is inherited too) and `generate_image` (an unexpected cost and, on
some tiers, a separate IPM quota dimension — see
[F8](#f8--gemini-capacity-four-independent-dimensions)).

### F2.3 `CapabilitiesConfig` **[V]**

```python
class CapabilitiesConfig(pydantic.BaseModel):
    enable_subagents: bool = True
    enabled_tools: list[BuiltinTools] | None = None  # mutually exclusive
    disabled_tools: list[BuiltinTools] | None = None  # with enabled_tools
    compaction_threshold: int | None = None
    finish_tool_schema_json: str | None = None
```

A model validator raises if both `enabled_tools` and `disabled_tools` are set.

Two fields matter disproportionately:

- **`finish_tool_schema_json`** — a JSON-schema *string* for the `finish` tool.
  This is the structured-completion-verdict hook
  ([F4](#f4--structured-output-the-completion-verdict)).
- **`compaction_threshold`** — lets us tune how aggressively long autonomous
  runs compact. claudeloop had nothing comparable; long unattended runs are
  precisely where this bites.

---

## F3 — Hooks: nine lifecycle points, three categories

**Confidence: [V].**

S1/S2 describe three hook categories:

| Category | Blocking? | Mutating? | Use |
|---|---|---|---|
| **Inspect** | No | No | Logging, metrics, audit trails |
| **Decide** | Yes | No | Approve/deny (policies are built on this) |
| **Transform** | Yes | Yes | Sanitize data in transit, recover from tool errors |

Nine concrete hook points are advertised (S1): session start, session end,
pre-turn, post-turn, pre-tool-call, post-tool-call, tool error recovery, user
interaction handling, and context compaction — each with a decorator shortcut.

S6 adds behavioral detail for `LocalConnection`:

- For **built-in** tools, `PreToolCallDecideHook` runs and can approve or deny;
  `PostToolCallHook` fires on completion; `OnToolErrorHook` fires on failure.
- For **host-side** (custom Python and MCP) tools the *full* pipeline runs:
  Decide → Execute → PostToolCall / OnToolError.
- **Subagent hooks** fire when a subagent starts, when its trajectory goes idle,
  and per tool call within it.
- `hook_runner.py` implements strict execution-order dispatch.
- `utils/interactive.py` ships concrete interactive implementations —
  `ToolConfirmationHook`, `AskQuestionHook` — which are precisely the ones a
  headless runner must **not** use.

**Implications for agyloop, in priority order:**

1. **`OnToolErrorHook` is a capacity-signal source.** A `run_command` that fails
   because the model call behind it 429'd is observable here *before* it becomes
   a turn-level exception. Feed it into the same `TurnSignals` accumulator; it
   may be the only place a structured error survives.
2. **Inspect hooks are our audit log.** Every tool call/result goes to
   `audit.jsonl` from an inspect hook, not from parsing text. This is a genuine
   upgrade on claudeloop, which reconstructed the audit trail from a message
   stream.
3. **Session start/end hooks** are where we bind `run_id` / `conversation_id`
   into the structured-logging context.
4. **Compaction hook** → emit a `context_compacted` event (see F1.3).
5. **We must positively ensure `ToolConfirmationHook` and `AskQuestionHook` from
   `utils.interactive` are never registered.** A `doctor` check should assert
   this, because a stray interactive hook is precisely a "blocks on a human"
   regression and it would be invisible until a run hangs at 3am. The assertion
   is cheap (inspect the registered hook set by type) and the failure mode it
   prevents is the worst one the product has.

**[U]** Hook *ordering* between multiple registered decide hooks is documented
as "strict execution order" but the tie-breaking rule when two policies match
the same tool call is not spelled out beyond "priority-based, top-down." agyloop
should therefore compile exactly **one** `enforce()` hook from a single ordered
policy list rather than registering several, so ordering is ours to reason about
rather than the runtime's.

---

## F4 — Structured output: the completion verdict

**Confidence: [V] for the mechanisms, [U] for reliability under real runs.**

Two independent mechanisms exist, and agyloop should use both:

**(a) Response schema on the config.** S1: "Define a response schema (as a JSON
schema, dict, or Pydantic model) and the agent returns validated, typed data via
`response.structured_output()`."

**(b) The `finish` tool's schema.** `CapabilitiesConfig.finish_tool_schema_json`
(S4) plus `StepType.FINISH` — "Finish the conversation and return structured
output" is the documented purpose of the `finish` builtin (S4). The
`Conversation` exposes `get_last_structured_output()`, which is what
`ChatResponse.structured_output()` delegates to (S4).

The verdict schema agyloop will impose (design decision, recorded here because
it depends on this finding):

```json
{
  "complete": true,
  "remaining_work": ["..."],
  "blocked_on": null,
  "summary": "..."
}
```

**Implication.** This is a near-exact carryover of claudeloop's
`domain/completion.py`, including its two hard rules: `blocked_on` outranks
`complete`, and **a capacity rejection outranks *any* completion claim**. The
only delta is the plumbing: `ClaudeAgentOptions.output_format` becomes
`finish_tool_schema_json` (and/or the config-level response schema).

**Caveat [U], and it is the reason the marker survives.** `structured_output()`
returns `None` when no structured payload exists — and we have not verified how
often the harness ends a turn without emitting a `FINISH` step (e.g. when the
turn ends due to an error, a cancel, or a compaction boundary). The
`AGYLOOP_TASK_FULLY_COMPLETE` marker fallback is therefore **not optional**; it
is the load-bearing backstop for every turn that returns `None`.

The three-layer ladder, stated once so the implementation has no room to
improvise:

1. **Structured output** — parse the schema-shaped object from
   `structured_output()`.
2. **Done marker** — `AGYLOOP_TASK_FULLY_COMPLETE`, appended as a prompt
   instruction, matched in the final aggregated text.
3. **No signal** — treat as `Continue`. A missing verdict is **never** read as
   completion. The run continues until a budget, an explicit verdict, or an
   operator stop ends it.

---

## F5 — `ask_question` and the never-block rule

**Confidence: [V].**

The harness has a first-class human-in-the-loop path. S1 lists it as a headline
feature: "The agent pauses mid-task to ask structured questions with predefined
options and branches on the response." The types (S4):

```python
class AskQuestionOption(BaseModel):  # frozen
    id: str
    text: str


class AskQuestionEntry(BaseModel):  # frozen
    question: str
    options: list[AskQuestionOption]
    is_multi_select: bool = False


class AskQuestionInteractionSpec(BaseModel):  # frozen
    questions: list[AskQuestionEntry]


class QuestionResponse(BaseModel):
    selected_option_ids: list[str] | None = None
    freeform_response: str = ""
    skipped: bool = False


class QuestionHookResult(BaseModel):
    responses: list[QuestionResponse]
    cancelled: bool = False
```

And the generic decide-hook result:

```python
class HookResult(BaseModel):
    allow: bool = True
    message: str = ""
```

### F5.1 The three candidate strategies, and why we pick the third

| Strategy | Mechanism | Verdict |
|---|---|---|
| **Auto-answer** | Return a `QuestionHookResult` selecting some option | **Rejected.** Fabricates a decision the human never made and buries it — the exact failure claudeloop's ADR 0007 rejected. |
| **Disable the tool** | `CapabilitiesConfig(disabled_tools=[BuiltinTools.ASK_QUESTION])` | **Rejected as the sole mechanism.** The model never sees the tool, so it can't ask — but it also gets no guidance about *why*, and it may fall back to asking in plain prose (which has no interception point at all). Cheap, though, so we use it as belt-and-braces under `--strict-autonomy`. |
| **Deny with guidance** | `HookResult(allow=False, message=...)` from a decide hook, or an `ask_user` policy handler that returns `False` synchronously | **Chosen.** S6 states explicitly that a denied tool "lets the model understand why it was refused," and the model "may then retry or choose a different approach." That is precisely the behavior we want: hand the decision back with the constraint stated. |

The denial message agyloop will send (design decision, recorded here):

> Running autonomously — no human is available to answer. Choose the option you
> would recommend, state the assumption you are making in your next message, and
> proceed. Do not call `ask_question` again for this decision.

Because the assumption then lands in the transcript, it is reviewable after the
fact — the property claudeloop's ADR 0007 was protecting. Note also that the
denial handler must return **synchronously**; an `ask_user` handler that awaits
anything reintroduces exactly the blocking behavior we are eliminating, and a
lint rule / review checklist item should say so.

### F5.2 The remaining hole, unchanged from claudeloop **[V]**

A model that simply *writes* "Shall I proceed?" as prose makes no tool call, so
there is no interception point. Mitigations carry over verbatim: an autonomy
fragment in `system_instructions`, and a completion evaluator that treats
`complete: false` with no `blocked_on` as a **continuation**, never a stop.

`LocalAgentConfig` accepts `system_instructions` as a `str` or a list of
`SystemInstructionSection`, with `CustomSystemInstructions` documented as "full
replacement (advanced usage)" and carrying an explicit warning that it replaces
*all* default instructions (S4). **agyloop must use the additive form, never
`CustomSystemInstructions`** — replacing the harness's operational guidelines
wholesale would silently discard the tool-usage protocols the runtime depends
on, and the resulting failure would look like model incompetence rather than a
configuration bug.

---

## F6 — Session persistence via `conversation_id`

**Confidence: [V] for the mechanism, [U] for durability.**

From S5, verbatim in substance:

```python
@property
def conversation_id(self) -> str | None:
    """Returns the conversation identifier assigned by the runtime.

    Available after the session has started and at least one message has
    been exchanged. Pass this value back via SessionConfig.conversation_id
    to resume from a saved session. Returns None before the session starts.
    """
```

S1 confirms: "Session persistence: Resume conversations from saved session IDs
by passing `conversation_id` back to the agent config."

**This is a straight upgrade over claudeloop's session story.** claudeloop had
to discover sessions by globbing `~/.claude/projects/` before the SDK grew
`list_sessions()`. Here, the id is handed to us and we own persistence — which
means we are never parsing a vendor's private on-disk format, the single most
fragile thing in the legacy script this whole family of projects replaces.

**Implications:**

- `.agyloop/runs/<run_id>/meta.json` stores `conversation_id` the moment it
  becomes non-`None` — i.e. **after the first successful turn**, which means
  there is a window where a crash loses the session. Mitigation: persist
  immediately in a post-turn inspect hook, before any other post-turn work, and
  `fsync`.
- `agyloop resume` is `LocalAgentConfig(conversation_id=...)` plus a
  continuation prompt. No filesystem archaeology.
- `agyloop sessions` lists **our own** run registry, not a vendor directory.
  This is a deliberate scope reduction from claudeloop's `sessions` command and
  should be documented as such in the CLI help — we cannot enumerate
  conversations we did not create, and pretending otherwise would be a support
  burden.
- **[U]** Whether a `conversation_id` survives a runtime/CLI upgrade, and how
  long the backend retains it, is not documented. `resume` must degrade
  gracefully: if resumption fails, start a fresh conversation seeded with the
  persisted plan state and say so loudly in the log, rather than aborting. A
  run that silently restarts its context is bad; a run that aborts three hours
  in because a session expired is worse.

`Conversation` (S7) additionally exposes `history`, `total_usage`, turn count,
compaction indices, and `send()` / `receive_steps()` for step-level streaming —
so a `--stream` UI mode and an accurate per-run token ledger are both available
without extra vendor calls.

---

## F7 — Errors: four exception types, no typed rate-limit event

**Confidence: [V] for the taxonomy, [U] for what a 429 actually looks like at
the call site.**

From S4, the complete public error taxonomy:

```python
class AntigravityConnectionError(Exception):
    ...
    # connection cannot be established, or fatal protocol-level error


class AntigravityCancelledError(asyncio.CancelledError):
    ...
    # active turn cancelled programmatically


class AntigravityExecutionError(Exception):
    ...
    # agent loop terminated on a fatal error (e.g. model call failure,
    # system constraint violation) and cannot continue


class AntigravityValidationError(Exception):
    ...
    # wraps pydantic.ValidationError at the SDK boundary; carries .message
    # and .errors
```

**This is the crux of the whole fork.** There is **no** `RateLimitEvent`
analogue, no `resets_at` field, no `rate_limit_type`, no
`can_user_purchase_credits`. A quota rejection from the model backend will most
plausibly surface as an `AntigravityExecutionError` whose message embeds the
underlying `429` — "model call failure" is literally the documented example of
what that exception means.

**Consequences, and these drive the architecture:**

1. **`domain/classify.py` becomes the highest-risk module in the codebase**, not
   a thin field mapper. It must parse a `TurnSignals` bundle assembled from an
   exception type, an exception message, and whatever structured `details` the
   adapter can recover, and it must be defensive about all three being thin.
2. **The adapter must try hard to recover structure before falling back to
   string matching.** Where the underlying error is a `google.api_core` /
   `google.genai` error object, the `429` body carries `error.status`,
   `error.code`, `error.message`, and `error.details[]` — the standard Google
   error envelope (S10, S13). See
   [F9](#f9--resource_exhausted-is-ambiguous-classify-with-details) for the
   specific detail types.
3. **String matching is a *fallback*, is versioned, and is tested against golden
   fixtures.** Every message pattern we match gets a captured fixture in
   `tests/fixtures/errors/` with a provenance comment naming where it came from
   and when. A pattern that stops matching must fail a test, not silently
   reclassify a billing wall as a waitable blip.
4. **The ambiguity default must be safe.** When we cannot tell, the answer is
   *bounded probing with a hard `--max-wait`*, never an unbounded sleep and
   never an optimistic tight retry loop.
5. **`AntigravityCancelledError` is not a capacity signal.** It means *we*
   cancelled — operator stop, budget trip, signal handler. Conflating it with a
   rejection would make an operator stop look like a rate limit and schedule a
   pointless wait.
6. **`AntigravityValidationError` is a bug in our own config**, not a vendor
   problem. It should fail fast and loudly at startup rather than mid-run, which
   argues for validating the whole `LocalAgentConfig` in `Preflight`.

**[U]** Whether the Antigravity harness performs its own internal retry/backoff
on `429` before surfacing an error to the SDK caller is undocumented. If it
does, our observed inter-turn latency will already include vendor backoff, and
our own retry budget must be tuned down to avoid compounding. **This is the
single highest-value thing to measure in the M2 live-harness spike**: run a
free-tier account into an RPM wall and record (a) wall-clock time to the
exception, (b) the exception type, (c) the exact message text, (d) any
recoverable `details`.

---

## F8 — Gemini capacity: four independent dimensions

**Confidence: [V].**

From S8 (Gemini API rate limits), all verified:

- Limits are measured across **RPM** (requests per minute), **TPM** (input
  tokens per minute), and **RPD** (requests per day).
- "Your usage is evaluated against each limit, and exceeding **any** of them
  will trigger a rate limit error" — e.g. 21 requests against an RPM limit of 20
  errors even with TPM headroom.
- **"Rate limits are applied per project, not per API key. Requests per day
  (RPD) quotas reset at midnight Pacific time."**
- Separately: **spend-based rate limits** exist "to protect against unexpected
  charges," and whether they apply depends on billing history and tier:

| Usage tier | Spend rate limit (per 10 minutes) | Billing tier cap |
|---|---|---|
| Free | N/A | N/A |
| Tier 1 | $10 | $250 |
| Tier 2 | $200 | $2,000 |
| Tier 3 | $200 | $20,000 – $100,000+ |

- Tier qualification: Tier 1 = active linked billing account; Tier 2 = $100 paid
  + 3 days from first successful payment; Tier 3 = $1,000 paid + 30 days.
  Upgrades take effect within ~10 minutes; live limits are visible in AI Studio.
- Limits vary per model and change with tier/account status; S8 explicitly says
  to view them in AI Studio rather than assume.

Corroborating **[S]** detail: an **IPM** (images per minute) dimension exists
for multimodal/image work; RPD midnight PT is 08:00 UTC during PST and 07:00 UTC
during PDT.

### F8.1 The four-way split agyloop must make

This is the direct translation of the capacity requirement into vendor-grounded
terms:

| Dimension | Time to recovery | Boundary known? | agyloop `CapacityState` |
|---|---|---|---|
| **RPM / TPM / IPM** | Seconds to ~1 minute | No fixed instant; recovery is continuous as the sliding window drains | `TransientThrottle(retry_after)` — retry with exponential backoff + jitter |
| **RPD** | Up to 24h | **Yes** — next midnight America/Los_Angeles | `WindowExhausted(quota_id, resets_at=next_pt_midnight())` — wait to boundary, but keep probing |
| **Spend-based (10-min rolling)** | ~10 minutes | Approximately | `WindowExhausted(quota_id="spend_10m", resets_at=now+10m)` — bounded, but treat the estimate as soft |
| **Billing cap / no balance / hard daily exhaustion** | **Never, without a human** | N/A — there is no reset | `CreditsExhausted(can_purchase=...)` — probe cadence + notify, never a deadline |

**This table is the entire reason agyloop exists as a separate project rather
than a claudeloop config flag.** claudeloop's two-state model
(`WindowExhausted` | `CreditsExhausted`) is insufficient here: collapsing RPM
into `WindowExhausted` would make the runner wait minutes for something that
clears in seconds, and collapsing a billing cap into `WindowExhausted` would
make it wait forever for something that never clears.

### F8.2 Why "per project, not per key" changes the data model **[V]**

S8 is explicit that limits are per *project*. Two consequences that are easy to
get wrong:

1. **Cached capacity state must be keyed by project id, not API key.** A user
   who rotates keys expecting fresh quota will be disappointed, and a UI that
   implies otherwise is actively misleading.
2. **Concurrent agyloop runs in the same project share one quota pool.** The
   per-session advisory lock prevents two runners on one *conversation*; it does
   nothing about two runners on one *project*. That is a documentation item and,
   optionally, a `--project-concurrency-warning` in `doctor`.

---

## F9 — `RESOURCE_EXHAUSTED` is ambiguous; classify with details

**Confidence: [V] for the ambiguity and the envelope, [U] for what survives to
us.**

S9's troubleshooting table is unambiguous about the ambiguity:

> **429 / RESOURCE_EXHAUSTED** — "You've exceeded one of the API's rate limits
> (**RPM, TPM, RPD, spend**, etc.)." Cause: "You are sending too many requests,
> using too many tokens, **or exceeding spend-based limits for your account's
> billing history and tier**."

So the status code alone spans *both* sides of the waitable/non-waitable line.
**A bare `429 RESOURCE_EXHAUSTED` must never be classified.** It must be routed
through the discriminator ladder.

S10 gives a finer-grained code vocabulary that *is* discriminating when present:

| Error code | HTTP | Meaning | Documented remedy |
|---|---|---|---|
| `rate_limit_exceeded` | 429 | Exceeded per-minute or per-second request/token limit | Wait and retry with exponential backoff |
| `quota_exceeded` | 429 | **Exceeded your daily quota** | Wait until the quota resets, or request an increase |

That maps directly onto our `TransientThrottle` vs `WindowExhausted(daily)`
split. When `error_code` is present, it is the strongest single signal we get —
and the whole point of the adapter working hard to recover structure is to reach
this rung rather than the text-matching rungs below it.

### F9.1 The Google error envelope and its `details[]`

Standard Google API error shape (S10, S13):

```json
{
  "error": {
    "code": 429,
    "message": "Resource has been exhausted (e.g. check quota).",
    "status": "RESOURCE_EXHAUSTED",
    "details": [ /* typed detail messages */ ]
  }
}
```

Two `details[]` entry types matter enormously when present:

- **`google.rpc.RetryInfo`** — carries `retryDelay` (e.g. `"27s"`). Community
  and vendor guidance alike say to **prefer this over your own backoff
  computation** when it is supplied. Its presence is itself evidence of
  transience: a service that tells you when to come back believes you should
  come back.
- **`google.rpc.QuotaFailure`** — carries `violations[]` with `quotaMetric`,
  `quotaId`, `quotaDimensions`, and often `quotaValue`. The `quotaId` string is
  where "per minute" vs "per day" is spelled out, and it is the second-strongest
  signal after `error_code`.

**[U]** Whether the Antigravity harness preserves these `details` all the way
through to the message/exception the SDK raises is **unverified and is the
second-highest-value M2 spike measurement**. Design accordingly: the extractor
tries structured `details` first, then a `retry-after`-ish numeric in the
message, then quota-name substrings, then gives up into the ambiguous branch.

### F9.2 Retry guidance we are expected to follow **[V]**

From S9:

- Implement **exponential backoff** — e.g. 1s, 2s, 4s, 8s.
- **Add jitter** so clients don't synchronize.
- **Retry only on transient errors** (429, 408, 5xx). **Do not retry 400/403** —
  those are invalid keys or bad syntax.
- **Set a maximum number of retries** to prevent infinite loops.
- The official `google-genai` Python SDK already "automatically retries
  transient errors up to four times with an initial delay of approximately 1
  second and a maximum delay of 60 seconds."

That last bullet is the Google analogue of claudeloop's ADR 0005
(`CLAUDE_CODE_RETRY_WATCHDOG` left off): **in-process retry is fine for
absorbing blips, but it must be bounded and it must not hide a hard limit from
the outer loop.** If the Antigravity harness embeds `google-genai`'s default
retry, then by the time we see an error we have *already* burned ~4 retries and
up to ~60s — and the fact that it still failed is meaningful evidence that this
is not a one-second blip. Our own budget must be tuned down accordingly rather
than compounding.

S16 (Gemini Enterprise / Vertex path) adds two more mechanisms worth knowing
about because they change what a `429` means on that lane:

- **Provisioned Throughput** — under-quota capacity errors are returned as
  `5XX` rather than `429`. So on the Enterprise lane, a `503` may carry
  capacity meaning that it does not carry on the Developer API lane.
- **Acceleration limits** — a sharp usage ramp can 429 you *even within quota*;
  the documented remedy is to ramp gradually.

For an autonomous runner that sends one turn at a time this is mostly
informational, but it justifies a `--ramp` option that paces the first N turns
of a run, and it is a reason `doctor` must report which lane is active.

### F9.3 Practical operator notes **[S]**

From X4/X5, useful for the `doctor` command and for our docs:

- AI Studio's rate-limit page shows **peak usage per model over the last 90
  days** by default, which is why RPD "looks like" it never resets. The
  real-time number is on the dedicated usage page. Usage data lags ~15 minutes.
- **`503 UNAVAILABLE` is *not* a quota signal** (model overloaded) — it must be
  retried, not waited-out, and must never classify as `CreditsExhausted`. This
  is a mistake community threads show people making repeatedly.
- Billing-account linkage problems can produce quota behavior that looks like
  exhaustion while you are nominally within tier limits.

**Implication.** `agyloop doctor` should print the project id, the resolved auth
mode, and a clear "we cannot read your live quota — check AI Studio" pointer,
rather than pretending to know limits it cannot query. Honesty about what the
tool cannot see is worth more than a confident wrong number.

---

## F10 — `UsageMetadata`: the budget ledger's input

**Confidence: [V].**

From S4:

```python
class UsageMetadata(pydantic.BaseModel):
    prompt_token_count: int | None = None
    cached_content_token_count: int | None = None  # subset of prompt tokens
    candidates_token_count: int | None = None  # excludes thinking
    thoughts_token_count: int | None = None
    total_token_count: int | None = None  # prompt + candidates + thoughts
```

`None` means "not available" (e.g. the step involved no model call); `0` means
the model explicitly reported zero.

**Implications:**

1. **There is no dollar figure.** claudeloop's `max_budget_usd` was fed by an
   SDK-reported cost. agyloop must either (a) express budgets in **tokens and
   turns** — the honest option — or (b) apply a user-supplied price table per
   model. Decision for the roadmap: **tokens/turns are first-class;
   `--max-dollars` exists only with an explicit `--price-per-mtok-in/out`
   pairing, and is documented as an estimate.**
2. `cached_content_token_count` being a *subset* of prompt tokens means naive
   summation double-counts. The ledger must model it as such, and a unit test
   should assert that a turn with cached content does not inflate the total.
3. `thoughts_token_count` is separately billable-ish and separately
   interesting — a run whose thinking tokens dominate is a run worth flagging in
   the summary, because it usually means the plan is under-specified.
4. **`None` must not be coerced to `0` in the ledger.** "Unknown" and "zero" are
   different, and conflating them would let a budget silently never trigger. The
   ledger therefore tracks a separate `unknown_steps` counter and the stop
   summary reports it, so an operator can see that the number they are looking
   at is incomplete.

---

## F11 — The `agy` CLI, and the sandbox trap

**Confidence: [V] for the permissions model and the bug, [S] for the flag
capture and preset names.**

### F11.1 Flag surface **[S]** (X1, a captured `agy --help`)

```
--add-dir                       Add a directory to the workspace (repeatable)
-c, --continue                  Continue the most recent conversation
--conversation                  Resume a previous conversation by ID
--dangerously-skip-permissions  Auto-approve all tool permission requests without prompting
-i, --prompt-interactive        Run an initial prompt interactively and continue the session
--log-file                      Override CLI log file path
--model                         Model for the current CLI session
-p, --print, --prompt           Run a single prompt non-interactively and print the response
--print-timeout                 Timeout for print mode wait (default 5m0s)
--sandbox                       Run in a sandbox with terminal restrictions enabled
subcommands: changelog, help, install, models, plugin(s), update
```

`--conversation <ID>` mirrors the SDK's `conversation_id`, and `-p` gives a
non-interactive one-shot — so a CLI-backed `AgentGateway` is feasible. But note
`--print-timeout` defaults to **5 minutes**, which is far too short for a
substantive autonomous turn; a CLI adapter must raise it explicitly, and a unit
test should assert the argv builder never omits it.

Note also that `-c/--continue` is the same "most recent conversation for this
directory" heuristic that claudeloop deliberately replaced with an explicit id.
The CLI adapter should always pass `--conversation <ID>`, never `-c`.

### F11.2 Permission presets **[V]/[S]**

S11 documents a fine-grained permissions engine with `action(target)` grammar,
allow/deny/ask lists, and secure defaults:

- Workspace file reads/writes are auto-allowed in standard operation.
- `read_url` / `execute_url` default to **Ask**.
- All other unconfigured actions (`command`, `mcp`, `execute_url`, non-workspace
  files) default to **Ask**.
- **`unsandboxed(prefix)` / `unsandboxed(*)`** is a distinct permission action:
  "commands matching this grant will be executed **outside of container
  isolation** (only applicable when terminal sandboxing is enabled)." Default:
  **Ask**.

X2 (**[S]**) names four presets: `request-review` (default),
`proceed-in-sandbox`, `always-proceed`, `strict`, switchable via `/permissions`.

The existence of `unsandboxed` as a *named, denyable action* is the key fact —
it is what makes the safe configuration in F11.4 expressible at all.

### F11.3 The trap: `--dangerously-skip-permissions` defeats `--sandbox` **[V]**

S12 (upstream issue #36) is unambiguous and reproducible:

```bash
mkdir /tmp/workspace && cd /tmp/workspace
agy --sandbox --dangerously-skip-permissions -p "Run 'echo test > /tmp/outside_workspace.txt'"
cat /tmp/outside_workspace.txt     # the file exists
```

What happens: the initial tool call fails, **but the failure hint tells the
model to pass `bypassSandbox: true`** — and because
`--dangerously-skip-permissions` auto-approves *the sandbox-bypass prompt too*,
the retry succeeds and writes outside the workspace. The issue's own summary:
"With Antigravity CLI, `--dangerously-skip-permissions` appears to make
`--sandbox` completely ineffective." The proposed upstream fix is to disallow
`bypassSandbox` without explicit confirmation, and to never allow it in headless
(`-p`) mode.

X3 (**[S]**) is an independent third-party project hitting exactly this and
publishing a validated workaround: stop passing
`--dangerously-skip-permissions`; instead run `--sandbox` with settings
`toolPermission = "proceed-in-sandbox"` and `permissions.deny = ["unsandboxed"]`
— "allow everything except evading the sandbox," with `deny` outranking
everything. They report validating both the positive case (shell auto-proceeds,
no dialog) and the negative control (an out-of-workspace write is blocked, and
lands again when the old config is restored). An independently-validated
negative control is the strongest form of [S] evidence available here, and it is
why this workaround is adopted rather than merely noted.

### F11.4 What agyloop must do about it

This is a **security requirement**, and it will be an ADR:

1. **The SDK path is the default and the recommended path.** `policy.allow_all()`
   grants tool autonomy without touching the CLI's sandbox-bypass approval flow
   at all — the CLI bug is a CLI bug.
2. **When the CLI adapter is used, agyloop never passes
   `--dangerously-skip-permissions` by default.** It uses `--sandbox` +
   `proceed-in-sandbox` + `deny: ["unsandboxed"]`.
3. `--dangerously-skip-permissions` is available only behind an explicit
   `--unsafe-skip-permissions` opt-in that (a) **refuses to combine with
   `--sandbox`** rather than silently neutering it, (b) refuses to run as root,
   (c) refuses outside a git repository or allowlisted directory, and (d) emits
   a `WARNING`-level audit record naming the risk and citing issue #36.
4. **`doctor` checks the installed `agy` version** and warns when it is one
   known to exhibit #36 with the requested flag combination.
5. Even on the SDK path, autonomy must be *scoped*: `policy.allow_all()` should
   be paired with `policy.workspace_only()` for file tools and an explicit
   `deny` for destructive command patterns in the default profile, with `--yolo`
   required to drop those.

**[U] and important:** whether the SDK path has its *own* sandbox-bypass
equivalent that `allow_all()` also auto-approves is unverified. **Treat the SDK
path as unsafe until proven otherwise** — point 5 exists precisely because we
cannot yet claim the SDK is safer, only that it does not go through the *known*
broken flow.

---

## F12 — The capacity probe, and why probing is not free

**Confidence: [design, grounded in V], with one [U] that changes the design.**

claudeloop's probe was a one-token, no-tools, no-persistence throwaway turn. The
Antigravity equivalents:

| claudeloop probe property | agyloop mechanism |
|---|---|
| `max_turns=1` | Single `chat()` on a probe agent |
| no tools | `CapabilitiesConfig(enabled_tools=BuiltinTools.read_only())`, or `BuiltinTools.none()` |
| `setting_sources=None` (no CLAUDE.md) | Minimal additive `system_instructions`; no plugins/MCP servers configured on the probe config |
| `no-session-persistence` | **Do not pass `conversation_id`** — the probe gets its own throwaway conversation and never touches the working session |
| "a rejected probe is not billed" | **[U] — must be verified.** If a rejected Gemini request still counts against RPD, an aggressive probe cadence could *consume the very quota it is waiting for*. |

**That last row is a genuine hazard unique to this fork** and it changes the
design: because RPD is a *request* count, probing is not free the way it was
against Claude's window model. Therefore:

- **Probe cadence must be quota-aware.** While in `WindowExhausted(daily)`, the
  probe interval floor is much larger (default 15 minutes, backing off), and the
  primary wake-up is the known midnight-PT boundary. Probing exists to catch an
  *early* recovery (a tier upgrade, a quota grant, a billing fix), not to poll a
  24h clock.
- **A `--no-probe` mode** must exist that waits purely to the computed boundary
  and issues zero probe requests. This is the correct default for anyone on a
  tight RPD, and it must be documented as such rather than buried.
- **The probe must be counted in the budget ledger** like any other request, so
  a probe storm shows up in the numbers instead of hiding in them.
- **The probe must be classifiable.** A probe that fails must produce the same
  `TurnSignals` shape as a real turn, so the classifier is exercised identically
  in both paths and cannot develop a probe-only bug.

### F12.1 Boundary arithmetic is its own risk

`domain/quota.py::next_pt_midnight(now)` is a pure function using `zoneinfo`
with `America/Los_Angeles`. It must be tested across both DST transitions,
including the ambiguous local hour in autumn and the non-existent local hour in
spring. Getting it wrong means waking an hour early into a still-exhausted quota
(harmless, costs one probe) or an hour late (costs an hour of a multi-hour run).
Both are cheap to avoid and expensive to diagnose after the fact, which is
exactly the profile of a bug that should be closed by a table-driven test rather
than by care.

---

## F13 — Auth: two lanes, ADC by default

**Confidence: [V].**

From S3 (repository README), verbatim in substance:

- **Gemini Developer API lane.** `LocalAgentConfig(api_key="...")`, or leave it
  unset and let the environment supply it. The Google Gen AI convention (S14) is
  **`GOOGLE_API_KEY`**.
- **Gemini Enterprise Agent Platform (formerly Vertex AI) lane.**
  ```python
  config = LocalAgentConfig(vertex=True, project="your-gcp-project", location="us-central1")
  ```
  or via environment:
  ```sh
  # Either GOOGLE_GENAI_USE_VERTEXAI or GOOGLE_GENAI_USE_ENTERPRISE enable Vertex.
  export GOOGLE_GENAI_USE_VERTEXAI=True
  export GOOGLE_CLOUD_PROJECT="your-gcp-project"
  export GOOGLE_CLOUD_LOCATION="us-central1"
  ```
- **"Explicit kwargs always take precedence over env vars."**
- **"By default, the SDK uses Application Default Credentials (ADC) for
  authentication,"** with `gcloud auth application-default login` as the
  documented local setup step.

**Implications:**

1. **`doctor` must resolve and report the effective lane** — Developer API vs
   Enterprise/Vertex — and the *source* of each setting (explicit flag,
   `AGYLOOP_*`, `GOOGLE_*`, or ADC). Silent lane selection is a support
   nightmare, and the two lanes have *different quota semantics* (S16): a `503`
   means something different on each, and `details[]` availability may differ.
2. **ADC expiry is a never-block hazard.** An expired ADC refresh token will
   surface as an auth error mid-run; `gcloud auth application-default login` is
   interactive and therefore forbidden mid-run. Classification must map auth
   failures to `AuthenticationFailed` → **terminal abort with a notifier fire**,
   never a retry loop. This is claudeloop's rule and it carries over unchanged.
3. **Redaction must cover more surface than claudeloop's.** In addition to
   `api_key` / `authorization`, we must scrub `GOOGLE_API_KEY`, bearer tokens
   minted from ADC, `client_secret`, `refresh_token`, and the contents of
   `application_default_credentials.json` if it is ever read into a log.
4. Since **rate limits are per project, not per key** (S8), the *project id* is
   the correct cardinality for any capacity state we cache or report — not the
   key. A user rotating keys does not get fresh quota, and our UI must not imply
   otherwise.
5. **[S]** As of mid-2026 Google restricts unrestricted API keys for the Gemini
   API (keys should be restricted to `generativelanguage.googleapis.com`).
   `doctor` should mention this in its auth guidance.

---

## F14 — REST surface feasibility for M4

**Confidence: [V] for the substrates, [design] for the recommendation.**

claudeloop's M4 generated a 1:1 CLI over all 131 Anthropic REST endpoints by
introspecting the SDK's `cached_property` resource tree. The Google equivalent
has **three** candidate substrates:

| Option | Substrate | Pros | Cons |
|---|---|---|---|
| **A. Discovery document** | `https://generativelanguage.googleapis.com/$discovery/rest?version=v1beta` | Canonical, machine-readable, no key required to fetch (per S15), the vendor's own "source of truth for API definitions" | Discovery format, not OpenAPI; needs its own binder |
| **B. Published OpenAPI 3.0** | `https://generativelanguage.googleapis.com/$discovery/OPENAPI3_0?version=v1beta` | Standard format, tooling-rich | S15 shows it was added later and is derived; needs a drift check against A |
| **C. `google-genai` SDK introspection** | `client.models`, `client.files`, `client.caches`, `client.batches`, `client.tunings`, `client.aio.*` | Mirrors claudeloop's exact technique; typed; handles auth/paging | Adds a second SDK dependency; the SDK surface is narrower than the raw API |

Relevant facts: the official Python SDK is `google-genai`, `client.models`
exposes inferencing, and `client.aio` mirrors every module asynchronously (S14).
The Gemini REST reference (S13) confirms the endpoint shape
`POST /v1beta/{model=models/*}:generateContent`.

**Recommendation for the roadmap:** prefer **A with B as a cross-check**, and
gate the whole milestone on a stability criterion. If, at M4 planning time, the
discovery document's endpoint inventory has been stable across two consecutive
minor Gemini API releases *and* the Antigravity SDK has left preview, build it.
Otherwise **defer with an ADR** rather than shipping a surface that will be
wrong within a month. Either way the deliverable that makes "no gaps" real is
the same as claudeloop's: **a drift gate test** that enumerates the upstream
surface and fails CI when a command is missing, plus a committed baseline count
so *removals* are caught too.

Note also that a REST surface here spans **two** API families (Gemini Developer
API and the Vertex/Enterprise lane, which have partially disjoint operations —
S14 warns that some services exist only on one backend). Any generated surface
must model the backend split the way claudeloop's `--provider` modeled
Bedrock/Vertex/Foundry's partial trees, rather than offering commands that will
fail at call time.

**Deliberate contrast with the sibling fork.** codexloop locks its M4 in,
because `openai.resources` is the same `cached_property` class-tree shape
claudeloop already introspects — a confidence-A transplant. Here the substrate
is a *discovery document*, not a Python class tree, so the binder is new code
rather than retargeted code. That difference in transplant cost, not any
difference in ambition, is why this milestone is conditional and codexloop's is
not.

---

## 17. Consolidated implications — findings → design decisions

| # | Finding | agyloop design consequence | Where it lands |
|---|---|---|---|
| F1 | `Agent`/`LocalAgentConfig`, async CM | `AgentGateway` port wraps a live `Agent`; one async bridge in `cli/asyncio.py` | ADR 0002 |
| F1.1 | Errors re-raised at drain | Gateway drains inside `try/except` and builds `TurnSignals`; partial text preserved | `infrastructure/agent/translate.py` |
| F1.2 | `Thought` / `Text` / `ToolCall` chunks | Chatter log maps 1:1; `match` is exhaustive including multimodal | `infrastructure/agent/translate.py` |
| F1.3 | `COMPACTION` step type | First-class `context_compacted` event; re-anchor plan reconciliation | `domain/plan.py`, `hooks.py` |
| F2 | `policy.allow_all()` | Autonomy switch; paired with scoping policies by default | `infrastructure/agent/autonomy.py` |
| F2.1 | Disable ≠ deny | `ask_question` **denied with guidance**, optionally also disabled under `--strict-autonomy` | ADR 0007 |
| F2.2 | `BuiltinTools.read_only()` / `none()` | The probe's tool set; `nondestructive()` backs a `--safe` mode | `infrastructure/agent/probe.py` |
| F2.3 | `finish_tool_schema_json`, `compaction_threshold` | Structured verdict hook; tunable compaction for long runs | `domain/completion.py`, `options.py` |
| F3 | Nine lifecycle hooks | Audit log, chatter log, usage accounting, compaction events all hook-sourced | `infrastructure/agent/hooks.py` |
| F3 | `utils.interactive` hooks exist | Doctor asserts they are never registered | `application/usecases/doctor.py` |
| F3 | Hook ordering under-specified | Compile exactly one `enforce()` hook from one ordered list | `infrastructure/agent/autonomy.py` |
| F4 | `finish_tool_schema_json` + `structured_output()` | Typed completion verdict; `AGYLOOP_TASK_FULLY_COMPLETE` fallback stays mandatory | `domain/completion.py` |
| F5 | `AskQuestion*` types | Deny-with-guidance message text; never fabricate a `QuestionResponse`; handler must be synchronous | ADR 0007 |
| F5.2 | Additive `system_instructions` only | Never `CustomSystemInstructions` — it discards operational protocols | `infrastructure/agent/options.py` |
| F6 | `conversation_id` | Persist post-turn + `fsync`; `resume` degrades to fresh-conversation-with-plan-state | `infrastructure/state.py` |
| F7 | **No typed rate-limit event** | `classify.py` is an inference module with golden fixtures; ambiguity ⇒ bounded probe | ADR 0003 |
| F7 | `AntigravityCancelledError` ≠ capacity | Operator stop must never schedule a wait | `domain/classify.py` |
| F7 | `AntigravityValidationError` = our bug | Validate the whole config in `Preflight`, fail fast | `application/usecases/preflight.py` |
| F8 | Four quota dimensions | **Five-member `CapacityState`** incl. `TransientThrottle` | ADR 0003 |
| F8 | RPD resets midnight PT | `domain/quota.py::next_pt_midnight()` with `zoneinfo` + DST tests | `domain/quota.py` |
| F8.2 | Limits are per project | Cache capacity state by project id, never by key; document shared-pool concurrency | `infrastructure/state.py` |
| F9 | `RetryInfo` / `QuotaFailure` | Prefer server-supplied `retryDelay` over local backoff; `quotaId` drives the daily/minute split | `domain/waiting.py`, `domain/quota.py` |
| F9.2 | Vendor retry guidance + embedded SDK retry | Bounded in-process retries + jitter; outer loop still sees hard limits | ADR 0005 |
| F9.2 | Enterprise acceleration limits | `--ramp N` paces the first N turns | `application/runner.py` |
| F9.3 | `503` is not a quota signal | `TransientThrottle`, never `CreditsExhausted` | `domain/classify.py` |
| F10 | `UsageMetadata`, no dollars | Budgets in tokens/turns; `--max-dollars` requires a price table and is labeled an estimate; `None` ≠ `0` | `domain/budget.py` |
| F11 | CLI sandbox bypass (#36) | Never combine the dangerous flag with `--sandbox`; prefer `proceed-in-sandbox` + `deny: unsandboxed` | ADR 0008 |
| F11.1 | `--print-timeout` default 5m | CLI adapter always raises it explicitly | `infrastructure/agent/gateway_cli.py` |
| F12 | Probes may consume RPD | Quota-aware probe cadence; `--no-probe`; probes counted in the ledger | ADR 0004 |
| F13 | Two auth lanes, ADC | Doctor reports the resolved lane and source; auth failure is terminal | `infrastructure/doctor_env.py` |
| F14 | Discovery/OpenAPI available | M4 gated on a stability criterion; otherwise deferred by ADR | ADR 0006 |

---

## 18. Findings that become ADRs

| # | Decision | Driven by | Confidence of the evidence | Risk if wrong |
|---|---|---|---|---|
| 0001 | Onion architecture enforced by `import-linter` | claudeloop blueprint (X6) | [V] | Low — proven in the blueprint |
| 0002 | `google-antigravity` SDK is the primary gateway; the `agy` CLI is a secondary adapter behind the same port | F1 | [V] | Medium — the SDK is in preview and may churn |
| 0003 | **Five-member `CapacityState`; `CreditsExhausted` structurally cannot carry a reset instant** | F7, F8 | [V] | **Critical** — this is the whole product |
| 0004 | Quota-aware probe cadence; probes counted in the ledger; `--no-probe` exists | F12 | [V] mechanism, [U] on billing | High — a naive cadence consumes the quota it is waiting for |
| 0005 | Bounded in-process retry with jitter; the outer loop still sees hard limits | F9.2 | [V] | Medium — double backoff if the harness also retries |
| 0006 | Gemini REST surface gated on a stability criterion, else deferred by ADR | F14 | [V] substrates | Low — deferral is a legitimate outcome |
| 0007 | `ask_question` is **denied with guidance**, never auto-answered or silently disabled | F5 | [V] | Medium — a fabricated decision is invisible and unreviewable |
| 0008 | Never combine `--dangerously-skip-permissions` with `--sandbox`; prefer `proceed-in-sandbox` + `deny: unsandboxed` | F11 | [V] bug, [S] workaround | **High** — a real, reproduced sandbox escape |
| 0009 | Budgets are token/turn-denominated; dollars require an explicit price table and are labeled estimates | F10 | [V] | Low — but silently wrong dollars erode trust fast |
| 0010 | `conversation_id` persisted from a post-turn inspect hook with `fsync`; resume degrades to a fresh conversation seeded with plan state | F6 | [V] mechanism, [U] durability | Medium — a crash window exists either way |
| 0011 | Auth lane is resolved and reported by `doctor`, never guessed; auth failure is terminal | F13 | [V] | Medium — the two lanes have different quota semantics |
| 0012 | Classifier string patterns are versioned, fixture-backed, and counted; ambiguity defaults to a bounded probe | F7, F9 | [V] need, [U] shapes | **High** — this is precisely where a billing wall gets misread as a blip |
| 0013 | Compile exactly one `enforce()` decide hook from one ordered policy list | F3 | [U] ordering | Low — but it makes ordering ours to reason about |
| 0014 | `503 UNAVAILABLE` is a transient throttle, never a credits state | F9.3 | [V] | Medium — a common community mistake |

---

## 19. Open questions to resolve empirically

These are written as executable experiments, not as musings. Each has a
deterministic outcome that changes the implementation, and each has a defined
fallback so the project is never blocked waiting on an answer. Ordered by how
much design risk they carry; each becomes a checklist item in the implementation
plan's M2 live-spike task.

| # | Question | Experiment | If the answer is bad |
|---|---|---|---|
| Q1 | What exactly does a Gemini `429` look like by the time it reaches the SDK caller — exception type, full message text, and do any structured `details` survive? | Drive a free-tier account into an RPM wall; capture type, `repr`, `str`, and `__dict__` of the raised exception | Text matching becomes the primary discriminator; every pattern gets a versioned golden fixture and `doctor --explain-classify` reports which rung fired |
| Q2 | Does the harness retry internally before raising, and with what budget? | Time the wall-clock gap between the rejected request and the raised exception across 10 forced rejections | Tune our own retry budget down to near-zero; document that observed latency is vendor-owned |
| Q3 | Do rejected requests count against RPD? | Read AI Studio's usage page before and after a batch of 20 deliberately rejected probes (allowing for the ~15-minute lag) | Probe cadence floor rises sharply; `--no-probe` becomes the documented default for RPD waits |
| Q4 | Does an RPD rejection differ textually from an RPM rejection? | Force both on the same project and diff the captured messages | Infer from *timing* (elapsed since the last successful turn) — a much weaker signal that needs its own domain rule and its own test matrix |
| Q5 | What does a billing-cap / spend-limit rejection look like, as distinct from RPD? | Drive a Tier-1 account into its $10/10-min spend cap and capture the body | The `CreditsExhausted` discriminator falls back to a conservative rule: any rejection we cannot positively classify as time-windowed gets a bounded probe **and** a notifier fire |
| Q6 | Does `structured_output()` reliably return non-`None` on a normally completed turn with `finish_tool_schema_json` set? | Run 20 schema'd turns and measure conformance | Promote `AGYLOOP_TASK_FULLY_COMPLETE` to the primary completion signal and demote the schema to enrichment |
| Q7 | Is `conversation_id` durable across process restarts, harness upgrades, and multi-hour gaps? | Resume after 1 min, 1 h, 12 h; resume across an SDK upgrade | `resume` starts a fresh conversation seeded with persisted plan state and logs the degradation loudly |
| Q8 | Does the harness surface a distinguishable compaction signal we can hook, versus only observing a `COMPACTION` step after the fact? | Force a long context and watch both the hook stream and the step stream | Detect compaction from the step stream only; re-anchor plan reconciliation one turn late |
| Q9 | Does `policy.allow_all()` also auto-approve a sandbox-bypass equivalent on the SDK path, the way `--dangerously-skip-permissions` does on the CLI path (S12)? | Reproduce the #36 scenario through the SDK adapter | **Treat as unsafe until proven otherwise.** Default profile keeps `workspace_only()` + destructive-command denies regardless of the answer |
| Q10 | Are `RetryInfo` / `QuotaFailure` details present on the Enterprise/Vertex lane too, or only the Developer API lane? | Run the same forced rejection on both lanes | Lane-specific extractor branches, with the weaker lane falling through to text matching sooner |
| Q11 | Do Enterprise-lane acceleration limits reject a cold run inside quota, and does pacing fix it? | Start a fresh project and compare rejection rates with and without `--ramp 5` | `--ramp` becomes a default on the Enterprise lane rather than an opt-in |
| Q12 | Does a subagent inherit the parent's policies, including the `ask_question` denial? | Run a plan that spawns a subagent and instruct the subagent to ask a question | Register the denial hook explicitly at the subagent hook points too |

**Until Q1–Q12 are answered, the implementation assumes the pessimistic branch
of each.** That is why the wait policy is a bounded, quota-aware probe loop
rather than a scheduled wake-up: the schedule is an optimisation applied when a
boundary happens to be knowable, not a precondition for correctness.

---

## 20. Non-goals of this research

- We did not benchmark model quality, cost, or latency across Gemini variants.
  Model selection is a user decision; agyloop only needs to pass the id through
  and record it.
- We did not evaluate the Antigravity IDE / 2.0 product surface — only the SDK
  and the CLI, since those are the two programmable front doors.
- We did not investigate MCP server configuration in depth beyond noting that
  `McpStdioServer` / `McpStreamableHttpServer` configs exist (S4). MCP OAuth is
  a known never-block hazard inherited from claudeloop and gets a `doctor` check
  regardless.
- We did not price out or design the notifier transport (email, webhook, desktop
  notification). That is an infrastructure choice with no vendor coupling.
- We did not research Antigravity's plugin system, beyond noting that the probe
  config must not load plugins (F12).

---

## 21. Citation index

| Key | Source | Confidence class |
|---|---|---|
| S1 | *Introducing the Google Antigravity SDK* — vendor blog. <https://antigravity.google/blog/introducing-google-antigravity-sdk> | [V] |
| S2 | Antigravity SDK docs — Overview + Quick Start. <https://antigravity.google/docs/sdk/overview> | [V] |
| S3 | `antigravity-sdk-python` README — auth lanes, ADC default. <https://github.com/google-antigravity/antigravity-sdk-python> | [V] |
| S4 | SDK source `types.py` — error taxonomy, `BuiltinTools`, `CapabilitiesConfig`, `UsageMetadata`, `AskQuestion*`, `Step`/`StepType`. <https://github.com/google-antigravity/antigravity-sdk-python/blob/main/google/antigravity/types.py> | [V] |
| S5 | SDK source `agent.py` — `chat()`, `ChatResponse`, `conversation_id`. <https://github.com/google-antigravity/antigravity-sdk-python/blob/main/google/antigravity/agent.py> | [V] |
| S6 | SDK source `hooks/README.md` — policy semantics, hook pipeline, `utils.interactive`. <https://github.com/google-antigravity/antigravity-sdk-python/blob/main/google/antigravity/hooks/README.md> | [V] |
| S7 | SDK source `conversation/README.md` — L2 surface, history, usage. <https://github.com/google-antigravity/antigravity-sdk-python/blob/main/google/antigravity/conversation/README.md> | [V] |
| S8 | Gemini API — Rate limits (RPM/TPM/RPD, per-project, midnight PT, spend tiers). <https://ai.google.dev/gemini-api/docs/rate-limits> | [V] |
| S9 | Gemini API — Troubleshooting (429 ambiguity, retry guidance, SDK built-in retry). <https://ai.google.dev/gemini-api/docs/troubleshooting> | [V] |
| S10 | Gemini API — API errors (`rate_limit_exceeded` vs `quota_exceeded`, error envelope). <https://ai.google.dev/gemini-api/docs/api-errors> | [V] |
| S11 | Antigravity CLI — Permissions (action grammar, `unsandboxed`, secure defaults). <https://antigravity.google/docs/cli/permissions> | [V] |
| S12 | `antigravity-cli` #36 — `--dangerously-skip-permissions` defeats `--sandbox`. <https://github.com/google-antigravity/antigravity-cli/issues/36> | [V] |
| S13 | Gemini API — Generating content REST reference, error envelope shape. <https://ai.google.dev/api/generate-content> | [V] |
| S14 | `google-genai` SDK reference — client tree, `client.aio`, backend split. <https://googleapis.github.io/python-genai/> | [V] |
| S15 | Gemini cookbook #261 — discovery document and OpenAPI 3.0 availability. <https://github.com/google-gemini/cookbook/issues/261> | [V] |
| S16 | Gemini Enterprise Agent Platform — 429, Provisioned Throughput, acceleration limits. <https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/deploy/error-code-429> | [V] |
| X1 | Antigravity CLI tutorial — captured `agy --help`. <https://medium.com/google-cloud/antigravity-cli-tutorial-series-12b46cfe3bf2> | [S] |
| X2 | Antigravity CLI cheat sheet — permission presets. <https://toolsbase.dev/en/reference/antigravity-cli-commands> | [S] |
| X3 | `imbue-ai/catalyst` — validated sandbox-safe configuration with a negative control. <https://github.com/imbue-ai/catalyst/commit/430f31fd82182881c5e13c47593847d512457c5c> | [S] |
| X4 | Gemini developer forum — handling 429 / 503. <https://discuss.ai.google.dev/t/handling-429-503-errors-from-the-gemini-api/124640> | [S] |
| X5 | Gemini developer forum — RPD reset confusion and the AI Studio 90-day peak view. <https://discuss.ai.google.dev/t/rpd-is-not-being-reset/145704> | [S] |
| X6 | claudeloop 0.5.4 — the blueprint. <https://github.com/adammatthewsteinberger/claudeloop> | [V] |
