# codexloop — vendor research notes

> **Status.** Pre-implementation research, captured 2026-08-13. This document
> exists to justify every non-obvious design decision in
> [`architecture-and-roadmap.md`](architecture-and-roadmap.md). Nothing here is
> product code and nothing here is settled by assertion: each finding carries a
> citation and a confidence level, and the findings that are *not* firmly
> documented by OpenAI are called out explicitly so they become ADRs with a
> stated risk rather than silent assumptions.
>
> **Blueprint.** `codexloop` forks the design (not the code) of
> [`claudeloop` 0.5.4](https://github.com/adammatthewsteinberger/claudeloop) —
> an onion-architected autonomous Claude Code session runner whose two
> non-negotiables are (1) never block on a human and (2) never conflate an
> exhausted *rate-limit window* (waitable, has a reset time) with exhausted
> *credits/quota* (not waitable, needs a human to pay). Everything below asks
> the same two questions of the OpenAI / Codex stack.

---

## Contents

1. [Method and confidence scale](#1-method-and-confidence-scale)
2. [R1 — HTTP 429 is two different failures sharing one status code](#r1--http-429-is-two-different-failures-sharing-one-status-code)
3. [R2 — Rate-limit headers and `Retry-After` on the API path](#r2--rate-limit-headers-and-retry-after-on-the-api-path)
4. [R3 — Codex ChatGPT-plan windows: 5-hour primary, weekly secondary](#r3--codex-chatgpt-plan-windows-5-hour-primary-weekly-secondary)
5. [R4 — `codex exec --json`: the event stream we can actually parse](#r4--codex-exec---json-the-event-stream-we-can-actually-parse)
6. [R5 — Session continuity: `codex exec resume`, rollout files, `CODEX_HOME`](#r5--session-continuity-codex-exec-resume-rollout-files-codex_home)
7. [R6 — There is no stable `codex status --json`; three probe strategies](#r6--there-is-no-stable-codex-status---json-three-probe-strategies)
8. [R7 — Authentication: API key vs ChatGPT login](#r7--authentication-api-key-vs-chatgpt-login)
9. [R8 — Approval modes and sandboxing: how to never block](#r8--approval-modes-and-sandboxing-how-to-never-block)
10. [R9 — Codex SDK availability: TypeScript yes, Python no](#r9--codex-sdk-availability-typescript-yes-python-no)
11. [R10 — The app-server JSON-RPC surface](#r10--the-app-server-json-rpc-surface)
12. [R11 — The OpenAI Python SDK as the M4 REST surface](#r11--the-openai-python-sdk-as-the-m4-rest-surface)
13. [R12 — Structured completion output](#r12--structured-completion-output)
14. [Findings that become ADRs](#findings-that-become-adrs)
15. [Open questions to resolve empirically](#open-questions-to-resolve-empirically)
16. [Citation index](#citation-index)

---

## 1. Method and confidence scale

Sources were gathered from OpenAI's published developer documentation, the
`openai/codex` repository and its issue tracker, and — where OpenAI has
published nothing — from third-party integrations that ship code against the
same surfaces. Third-party evidence is *not* treated as equivalent to a spec;
it is treated as a hypothesis that the implementation must verify at runtime
and degrade gracefully when it fails.

| Confidence | Meaning | How codexloop is allowed to use it |
|---|---|---|
| **A — documented** | Stated in OpenAI's own docs or the `openai/codex` repository docs. | May be relied on in a hot path. Still guarded by a parse-failure fallback. |
| **B — corroborated** | Observed in `openai/codex` source/issues *and* independently in at least one third-party integration. | May be relied on **only** as an optimisation, never as the sole input to a capacity decision. |
| **C — single-source / community** | One blog, one issue comment, one third-party repo. | Informs design; must be probed at runtime and must have a documented fallback. Requires an ADR naming the risk. |

The rule that falls out of this table, and the single most important design
constraint in the project:

> **A capacity decision is never allowed to depend on a confidence-C signal
> alone.** Every classification path must terminate in a defensible answer even
> if every optional telemetry source returns nothing.

---

## R1 — HTTP 429 is two different failures sharing one status code

**Confidence: A.**

This is the finding the entire product is built around, and it is the exact
same shape as the `credits_required` finding that reshaped `claudeloop`.

OpenAI's error-codes guide documents 429 for *both* transient throttling and
billing exhaustion, and instructs callers to read the response body rather than
the status:

> For billing-related errors, inspect `error.code` to identify the specific
> cause. The broader `error.type` can still be `insufficient_quota`.
> — [Error codes | OpenAI API][c-errors]

The rate-limits guide is even more explicit that a `Retry-After` on a 429 does
not license retrying every 429:

> `Retry-After` may be present on `429` responses caused by a temporary rate
> limit. It does not mean that quota, billing, or other errors that require
> user action can be resolved by retrying. […] Don't retry quota, billing, or
> other errors that require you to take action.
> — [Rate limits | OpenAI API][c-ratelimits]

### The two bodies, side by side

Throttling — **waitable**, clears on its own, typically within seconds:

```json
{
  "error": {
    "message": "Rate limit reached for gpt-5.6 in organization org-… on requests per min. Limit: 500 / min.",
    "type": "rate_limit_error",
    "code": "rate_limit_exceeded",
    "param": null
  }
}
```

Billing — **not waitable**, no reset exists, only a human with a credit card
clears it:

```json
{
  "error": {
    "message": "You exceeded your current quota, please check your plan and billing details.",
    "type": "insufficient_quota",
    "param": null,
    "code": "insufficient_quota"
  }
}
```

That second body is quoted verbatim in OpenAI's own cookbook
([How to handle rate limits][c-cookbook]), so it is not a reconstruction.

### The wider code space

The error-codes guide additionally documents `credit_balance_exhausted`
("Your organization has no prepaid credits remaining. Add credits to continue
using the API") as a distinct 429 code, with `error.type` still potentially
reading `insufficient_quota` ([Error codes][c-errors]). Separately, the
Codex/ChatGPT-plan path surfaces `usage_limit_reached` — the plan-window wall
rather than a per-minute throttle. Third-party integrations that classify Codex
errors treat the space like this ([`llm/packages/core/src/providers/codex/errors.ts`][c-codexerrors],
confidence B):

```ts
const NON_RETRYABLE_CODES = new Set([
  'context_length_exceeded', 'insufficient_quota', 'usage_not_included',
  'invalid_prompt', 'usage_limit_reached', 'server_is_overloaded', 'slow_down',
  'token_expired', 'refresh_token_expired', 'refresh_token_reused',
  'refresh_token_invalidated',
]);
const NON_RETRYABLE_TYPES = new Set([
  'usage_limit_reached', 'usage_not_included', 'invalid_request_error',
]);
const RETRYABLE_CODES = new Set([
  'rate_limit_exceeded', 'websocket_connection_limit_reached',
]);
```

Note the asymmetry that matters: `usage_limit_reached` is listed as
non-retryable *there* because that integration wants immediate credential
rotation. For codexloop it is **retryable-with-a-deadline** — it is precisely
the waitable window — provided we can obtain a reset instant (see
[R3](#r3--codex-chatgpt-plan-windows-5-hour-primary-weekly-secondary)). If we
cannot obtain one, it degrades to a bounded probe loop, never a blind sleep.

### The classification table codexloop will implement

| `error.code` / `error.type` | HTTP | Domain state | Waitable? | Reset source |
|---|---|---|---|---|
| `rate_limit_exceeded` | 429 | `ThrottleExhausted` | yes | `Retry-After`, else `x-ratelimit-reset-*`, else backoff |
| `usage_limit_reached` | 429 | `WindowExhausted` | yes | plan-window `resets_at` if obtainable, else bounded probe |
| `insufficient_quota` | 429 | `QuotaExhausted` | **no** | none — notify a human |
| `credit_balance_exhausted` | 429 | `QuotaExhausted` | **no** | none — notify a human |
| `usage_not_included` | 429/403 | `QuotaExhausted(plan_gap)` | **no** | none — plan does not cover this model |
| `server_is_overloaded` | 503 | `TransientBackendError` | yes | short capped backoff |
| `slow_down` | 429 | `ThrottleExhausted(aggressive)` | yes | longer capped backoff |
| `context_length_exceeded` | 400 | `TurnFailedFatally` | n/a | prompt/compaction problem, not capacity |
| `invalid_api_key`, `token_expired`, `refresh_token_*` | 401 | `AuthFailed` | **no** | terminal — never retry |
| any 5xx not listed | 5xx | `TransientBackendError` | yes | capped backoff |
| **unrecognised 429** | 429 | `WindowExhausted(reset=None)` | yes, **bounded** | bounded probe under `--max-wait` |

The last row is the safety default and deserves its own note. When a *new* 429
code appears that codexloop has never seen, the conservative choice is a
bounded probe loop — not an unbounded sleep (which would hang for hours on a
billing failure) and not an abort (which would end a legitimate run on an
unknown-but-transient throttle). The bound is `--max-wait`, so the worst case
is a clean, explained failure at a time the operator chose.

**Design consequence.** `domain/classify.py` branches on the parsed error body
first and on HTTP status only as a fallback. A property test asserts the
invariant directly: *no input whose code or type is in the non-waitable set can
ever produce a waitable `CapacityState`.*

---

## R2 — Rate-limit headers and `Retry-After` on the API path

**Confidence: A.**

For direct API calls (the M4 REST surface, and any future direct-Responses
transport), OpenAI documents these response headers
([Rate limits][c-ratelimits]):

| Header | Sample | Meaning |
|---|---|---|
| `Retry-After` | `56` | Minimum seconds to wait before retrying a *temporary* rate-limit error, when present |
| `x-ratelimit-limit-requests` | `60` | Max requests permitted before exhausting the limit |
| `x-ratelimit-limit-tokens` | `150000` | Max tokens permitted before exhausting the limit |
| `x-ratelimit-remaining-requests` | `59` | Requests remaining |
| `x-ratelimit-remaining-tokens` | `149984` | Tokens remaining |
| `x-ratelimit-reset-requests` | — | Time until the request limit resets |
| `x-ratelimit-reset-tokens` | — | Time until the token limit resets |

Two operational notes from the same page, both of which change the design:

1. **Treat `Retry-After` as a minimum and add jitter.** "Treat this value as a
   minimum: wait at least that long and add a small random delay so multiple
   clients don't retry at the same time."
2. **The official SDKs already retry.** "Each official OpenAI SDK
   automatically retries eligible rate-limit errors and honors `Retry-After`
   when it's present. You don't need to parse the header or add another retry
   loop for standard API calls. […] If you add application-level retries,
   account for the retries your SDK already performs."

Point 2 is the OpenAI-side analogue of claudeloop's `CLAUDE_CODE_RETRY_WATCHDOG`
decision. The SDK's built-in retry is *good* for absorbing sub-minute blips and
*bad* as the outer loop, because it is invisible: no progress reporting, no
audit trail, no `--max-wait`, and — critically — no
window-vs-billing discrimination. codexloop therefore configures the SDK with a
small, explicit `max_retries` so short throttles are absorbed in-process, while
anything that survives that budget surfaces to the runner as a first-class
`CapacityState`.

`x-ratelimit-remaining-*` is a genuine improvement over anything claudeloop
had: it enables *pre-emptive* capacity awareness. The runner can log "72% of
the token window consumed" and, at operator option, pause before a turn rather
than after a rejection. That is a nice-to-have and is scheduled for M3, behind
a flag, never as a hard gate.

---

## R3 — Codex ChatGPT-plan windows: 5-hour primary, weekly secondary

**Confidence: B (mechanism), C (exact field names across versions).**

When Codex is authenticated with a ChatGPT plan rather than an API key, the
relevant limit is not RPM/TPM at all — it is a pair of rolling plan windows.
The Codex CLI receives these from OpenAI as `x-codex-*` response headers and
parses them into a `RateLimitSnapshot`
([`openai/codex` issue #14728][c-issue14728]):

> 1. **HTTP headers parsed** — `codex-rs/codex-api/src/rate_limits.rs` parses
>    `x-codex-primary-used-percent`, `x-codex-secondary-used-percent`, etc. into
>    `RateLimitSnapshot`
> 2. **Event emitted** — `ResponseEvent::RateLimits(snapshot)` is sent to the
>    event stream
> 3. **State stored** — `SessionState.latest_rate_limits` is set via
>    `set_rate_limits()`
> 4. **TokenCountEvent created** — `send_token_count_event()` reads
>    `state.token_info_and_rate_limits()` and populates
>    `TokenCountEvent { info, rate_limits }`

The snapshot shape, as observed in the VS Code path in that same issue:

```json
{
  "type": "event_msg",
  "payload": {
    "type": "token_count",
    "info": null,
    "rate_limits": {
      "primary":   { "used_percent": 0.0, "window_minutes": 299,   "resets_in_seconds": 17940 },
      "secondary": { "used_percent": 6.0, "window_minutes": 10079, "resets_in_seconds": 275281 }
    }
  }
}
```

A third-party spec that read the same data out of persisted rollout files
reports a richer variant with absolute epoch resets and plan metadata
([CODEX-USAGE-VISIBILITY-SPEC.md][c-usagespec], confidence C):

```json
{ "type": "event_msg",
  "payload": {
    "type": "token_count",
    "rate_limits": {
      "limit_id": "codex",
      "primary":   { "used_percent": 13, "window_minutes": 300,   "resets_at": 1780171524 },
      "secondary": { "used_percent": 93, "window_minutes": 10080, "resets_at": 1780174809 },
      "plan_type": "plus",
      "rate_limit_reached_type": null } } }
```

Interpretation, which the same spec reports as verified against a live session:

- `primary` ≈ the **5-hour rolling window** (`window_minutes` 299–300).
- `secondary` ≈ the **weekly window** (`window_minutes` 10079–10080 = 7 days).
- `used_percent` is consumption, so remaining is `100 − used_percent`.
- `plan_type` names the ChatGPT plan (`plus`, `pro`, …).
- `rate_limit_reached_type` is `null` until a window is actually hit — this is
  the field that most directly names *which* window rejected a turn.

### The trap: the field names differ between versions

`resets_in_seconds` (relative) and `resets_at` (absolute epoch) both appear in
the wild. codexloop must parse **both** and normalise to an absolute
`datetime` in the domain:

```
resets_at        -> datetime.fromtimestamp(value, tz=UTC)
resets_in_seconds-> clock.now() + timedelta(seconds=value)
neither present  -> None  (falls through to bounded probing)
```

The relative form is strictly worse for a long-lived runner because it is only
meaningful at the instant it was read; converting it against the injected
`Clock` immediately, at the adapter boundary, is what keeps the domain layer
pure and testable.

### The bigger trap: it is `null` in `codex exec`

> `codex exec` mode always yields `rate_limits: null` in rollout JSONL and in
> `TokenCount` events, making it impossible to display real-time usage
> percentages in tooling. […] However, `ev.rate_limits` is always `None` at
> runtime in exec mode.
> — [`openai/codex` issue #14728][c-issue14728]

The exec-mode JSONL writer *already handles* `RateLimitsUpdated` correctly; the
data simply never arrives, reportedly because the API does not return the
`x-codex-*` headers for non-interactive requests. Since `codex exec --json` is
codexloop's primary transport, **the richest capacity signal is exactly the one
we cannot count on.** This single fact is what forces the layered probe design
in [R6](#r6--there-is-no-stable-codex-status---json-three-probe-strategies).

**Design consequence.** The `rate_limits` payload is modelled as an
*opportunistic enrichment*, never a requirement. The parser is written so that
`null`, a missing key, an unknown extra window, or a renamed field all degrade
to `None` for that window only — and never raise.

---

## R4 — `codex exec --json`: the event stream we can actually parse

**Confidence: A.**

`codex exec` (short form `codex e`) is the documented non-interactive entry
point, purpose-built for "scripted or CI-style runs that should finish without
human interaction" ([Developer commands][c-clireference]). With `--json`,
stdout becomes newline-delimited JSON, one object per state change
([Non-interactive mode][c-noninteractive]):

> When you enable `--json`, `stdout` becomes a JSON Lines (JSONL) stream so you
> can capture every event Codex emits while it's running. Event types include
> `thread.started`, `turn.started`, `turn.completed`, `turn.failed`, `item.*`,
> and `error`.

A documented sample stream:

```json
{"type":"thread.started","thread_id":"0199a213-81c0-7800-8aa1-bbab2a035a53"}
{"type":"turn.started"}
{"type":"item.started","item":{"id":"item_1","type":"command_execution","command":"bash -lc ls","status":"in_progress"}}
{"type":"item.completed","item":{"id":"item_3","type":"agent_message","text":"Repo contains docs, sdk, and examples directories."}}
{"type":"turn.completed","usage":{"input_tokens":24763,"cached_input_tokens":24448,"output_tokens":122,"reasoning_output_tokens":0}}
```

Item types cover agent messages, reasoning, command executions, file changes,
MCP tool calls, web searches, and plan updates.

### Flags that matter to codexloop

| Flag | Why codexloop cares |
|---|---|
| `--json` | The whole machine-readable contract. Non-negotiable. |
| `--output-last-message PATH` / `-o` | Final assistant message to a file — a robust completion-marker source that does not require scraping the stream. |
| `--output-schema PATH` | JSON Schema constraining the model's response shape — the basis of typed completion verdicts (see [R12](#r12--structured-completion-output)). |
| `--ephemeral` | Do not persist the session to disk. Exactly right for capacity probes: a probe must not pollute the working session. |
| `--skip-git-repo-check` | Allow running outside a git repo. codexloop refuses non-git working directories by default anyway, so this is opt-in only. |
| `--model` | Model override per invocation. |
| `-i` / `--image` | Image attachments; irrelevant to M1–M3, mapped in the CLI matrix for completeness. |
| `-c key=value` | Arbitrary config override. The universal escape hatch — see [R8](#r8--approval-modes-and-sandboxing-how-to-never-block). |

The reference guide explicitly recommends the combination codexloop uses:
"Pair `--json` with `--output-last-message` in CI to capture machine-readable
progress and a final natural-language summary."

### Where the failures show up

`turn.failed` and `error` are the two event types that carry capacity
information. A `turn.failed` payload carries an error object whose `code` /
`type` feed the [R1](#r1--http-429-is-two-different-failures-sharing-one-status-code)
table directly. Because the exact nesting has varied across CLI versions, the
translation adapter searches a small set of candidate paths
(`error`, `payload.error`, `item.error`, `turn.error`) and treats *any* of them
as a hit — a deliberately forgiving parser at the edge, feeding a strict
domain type.

**Also non-negotiable:** the process exit code is a second, independent
capacity signal, and stderr carries human-formatted diagnostics. codexloop
captures all three (stdout JSONL, stderr text, exit code) into every
`TurnOutcome`, because relying on the JSONL alone means a malformed stream
becomes an unexplained failure.

---

## R5 — Session continuity: `codex exec resume`, rollout files, `CODEX_HOME`

**Confidence: A (commands), B (rollout layout).**

The documented continuation path ([Developer commands][c-clireference]):

> The optional `resume` subcommand lets you continue non-interactive tasks. Use
> `--last` to pick the most recent session from the current working directory,
> or add `--all` to search across all sessions.

So:

```bash
codex exec --json "…"                 # first turn, prints thread.started with thread_id
codex exec resume --last --json "…"   # continue most recent session for this cwd
codex exec resume <THREAD_ID> --json "…"   # continue an explicit session
```

**Prefer the explicit `thread_id`.** `--last` is convenient and is exactly the
fragile "most recent session for this cwd" heuristic claudeloop replaced with a
supported API. Because `thread.started` gives us the id on the very first turn,
codexloop records it immediately and resumes by id for the rest of the run;
`--last` remains only as the `resume` command's convenience path when no
explicit id is supplied.

### The `--sandbox`-on-resume gotcha

This one is a real, reported production break
([cc-connect PR #1360][c-ccconnect], confidence B, manually verified there
against codex-cli 0.137):

> `codex exec resume` does NOT accept the `--sandbox <mode>` flag (only
> `codex exec` does). […] Fix: on resume, express sandbox via
> `-c sandbox_mode="…"` config override instead of the `--sandbox` flag. Both
> `codex exec` and `codex exec resume` accept `-c`, so this is the canonical
> fix that doesn't regress the first-turn path.

**Design consequence, and it is a strong one:** codexloop expresses *every*
policy setting through `-c key=value` overrides on *both* the first turn and
resumes, rather than mixing flag styles between the two paths. One argv builder,
one code path, one set of tests — and the class of bug where turn 1 is
sandboxed correctly and turn 2 silently fails cannot occur. A unit test asserts
that the resume argv never contains a bare `--sandbox`.

### Rollout files

Codex persists per-session rollout JSONL under `$CODEX_HOME` (default
`~/.codex/`), and those files carry the `token_count` events described in
[R3](#r3--codex-chatgpt-plan-windows-5-hour-primary-weekly-secondary). The
third-party usage spec reads them by tailing the newest rollout and taking the
most recent `token_count` ([CODEX-USAGE-VISIBILITY-SPEC.md][c-usagespec]).

codexloop treats rollout parsing as a **confidence-C, best-effort telemetry
source only** — never as session state, never as the source of truth for
completion, never as a required input to a capacity decision. This mirrors the
claudeloop lesson that globbing `~/.claude/projects/` was the single most
fragile thing in the legacy script. Reading someone else's on-disk format that
they explicitly do not document as an API is borrowing against a future break.

---

## R6 — There is no stable `codex status --json`; three probe strategies

**Confidence: A (that it is absent), C (each workaround).**

The interactive TUI has `/status`, which shows plan and usage. There is no
documented, stable, machine-readable equivalent. A community write-up building
exactly this tool states the position plainly:

> Important caveat: Codex app-server is documented, but it is also described as
> experimental and may change. So this is still not a supported
> `codex status --json`. It is just a more sensible workaround than screen
> scraping.
> — [Nelson Chen's blog][c-mindflakes]

claudeloop had a clean answer here: a cheap throwaway turn against the Agent
SDK with `no-session-persistence`. codexloop needs an equivalent, and has three
candidate mechanisms. **The design takes all three, in a strict preference
order, with a guaranteed-available floor.**

### Strategy A — exec probe (floor; always available)

A minimal `codex exec` invocation:

```bash
codex exec --json --ephemeral \
  -c approval_policy="never" -c sandbox_mode="read-only" \
  "reply with the single word OK"
```

- `--ephemeral` means no session file is written, so the probe leaves no trace
  in the working session — the direct analogue of claudeloop's
  `no-session-persistence`.
- `sandbox_mode=read-only` means a probe can never mutate the workspace even if
  the model misbehaves.
- The signal is **binary but sufficient**: it either completes (capacity
  available) or fails with a classifiable error body (still exhausted). That is
  the only fact the wait loop actually needs.
- Cost: one very small turn. A *rejected* probe consumes no model tokens, which
  is what makes a repeated cadence affordable — the same reasoning claudeloop
  used. When capacity *is* available, the probe costs a handful of tokens, so
  the cadence must be bounded (it is: minimum interval, exponential backoff, and
  `--max-wait`).

**Confidence A that this works, because it uses only documented flags.** This
is the floor: if every richer source fails, this one still answers the question.

### Strategy B — app-server `account/rateLimits/read` (preferred enrichment)

The app-server exposes a JSON-RPC method that returns the rate-limit snapshot
without spending a turn ([codex_mcp_interface.md][c-mcpiface],
[Codex App Server][c-appserver], [zenn write-up][c-zenn]):

```
codex app-server --stdio        # or: codex app-server --listen stdio://
```

```json
{"id":1,"method":"initialize","params":{"clientInfo":{"name":"codexloop","title":"codexloop","version":"0.1.0"},"capabilities":{"experimentalApi":true}}}
{"method":"initialized","params":{}}
{"id":2,"method":"account/rateLimits/read"}
```

Notes that matter for the adapter:

- Transport is newline-delimited JSON-RPC 2.0 with `"jsonrpc":"2.0"` **omitted
  on the wire** ([Codex App Server][c-appserver]).
- The `initialize` → `initialized` → call handshake is mandatory.
- `account/rateLimits/read` is **experimental** and requires
  `capabilities.experimentalApi: true` during `initialize`, otherwise the
  server rejects it with "… requires experimentalApi capability".
- The v2 RPC list also includes `account/read`, `config/read`, `thread/start`,
  `thread/resume`, `thread/read`, `turn/start`, `turn/steer`,
  `turn/interrupt`, `model/list` — which makes the app-server a plausible
  *primary* transport in a later milestone, not just a probe.
- A related `account/rateLimitResetCredit/consume` exists for "banked resets"
  ([zenn][c-zenn]). codexloop explicitly does **not** consume banked resets:
  spending a user's banked credit as a side effect of a capacity probe would be
  a surprising, irreversible act. It is noted here so a future feature is a
  deliberate opt-in flag, never an accident.

**Risk, stated plainly:** the interface documents itself as "experimental and
subject to change without notice". Therefore this strategy is (a) always behind
a capability probe at startup, (b) never on the critical path, (c) covered by a
contract test that asserts codexloop still functions correctly when the method
is absent, errors, or returns an unparseable shape.

### Strategy C — rollout tail (last-resort enrichment)

Tail the newest rollout JSONL under `$CODEX_HOME` and read the most recent
`token_count.rate_limits` ([R3](#r3--codex-chatgpt-plan-windows-5-hour-primary-weekly-secondary),
[R5](#r5--session-continuity-codex-exec-resume-rollout-files-codex_home)).
Cheapest of the three, and the most fragile: it is a private on-disk format,
the data may be stale, and in exec-only sessions it is reportedly `null`
anyway. Included because it costs nothing to try and because when it *does*
produce a `resets_at`, that instant converts a bounded probe loop into a
precisely scheduled wake-up.

### The composite probe

```
CapacityProbe.probe():
    snapshot = app_server_rate_limits()      # B — skipped if unavailable
    if snapshot is None:
        snapshot = rollout_tail_rate_limits()  # C — skipped if unavailable/stale
    outcome  = exec_probe()                   # A — always runs; authoritative
    return ProbeResult(outcome=outcome, snapshot=snapshot)
```

`outcome` answers *"can we work right now?"* and is always present.
`snapshot` answers *"when will we be able to?"* and is always optional. The
domain's `AdaptiveWaitPolicy` takes both and degrades to a bounded cadence
whenever `snapshot` is `None`. Strategies B and C can be individually disabled
by flag/env, and a `doctor` subcommand reports which ones are live on this
machine — so an operator can see the degradation instead of guessing at it.

---

## R7 — Authentication: API key vs ChatGPT login

**Confidence: A.**

Two authentication modes, with materially different capacity semantics:

| Mode | How | Capacity model | Failure when exhausted |
|---|---|---|---|
| **API key** | `OPENAI_API_KEY` env (the SDK's standard); the Codex CLI receives it as `CODEX_API_KEY` | RPM/TPM tiers + prepaid credit balance | `rate_limit_exceeded` (waitable) or `insufficient_quota` / `credit_balance_exhausted` (**not** waitable) |
| **ChatGPT plan** | `codex login` → browser OAuth → credentials in `$CODEX_HOME/auth.json` | 5-hour primary + weekly secondary plan windows | `usage_limit_reached` (waitable, if a reset can be obtained) |

`codex login` "authenticates the CLI with a ChatGPT account, API key, or access
token. With no flags, Codex opens a browser for the ChatGPT OAuth flow", and
critically for automation:

> `codex login status` exits with `0` when credentials are present, which is
> helpful in automation scripts.
> — [Developer commands][c-clireference]

That is the `doctor` check: a cheap, documented, non-interactive way to verify
credentials exist *before* a long unattended run starts, rather than
discovering the problem three hours in.

**A trap worth recording:** an OAuth access token from the ChatGPT login flow
is *not* a valid API key. An OpenAI maintainer response on
[`openai/codex` issue #7144][c-issue7144]:

> The SDK expects an OpenAI API key (e.g., `sk-…`) and simply passes it to the
> CLI as `CODEX_API_KEY`; it does not exchange OAuth access tokens from
> `auth.openai.com/oauth/token`. That OAuth access token isn't valid for the
> Responses API, so the request returns 401. Please use a real API key or run
> `codex login` and let the CLI use `auth.json`.

So the two credential paths must never be crossed. codexloop's `doctor`
therefore reports *which* mode is active and refuses to guess, because the
capacity classification table differs between them — a `usage_limit_reached`
means "wait for the window" on a plan and would be nonsensical on a raw API
key, while `insufficient_quota` means "a human must pay" on a key and would
indicate something else entirely on a plan.

**Never blocking, credential edition.** The browser OAuth flow cannot complete
unattended, so it is only ever *reported*, never *triggered*, by a running
loop. Authentication failure mid-run is a terminal state (exit 1) with a
notification — never a retry loop, which would spin uselessly forever.

---

## R8 — Approval modes and sandboxing: how to never block

**Confidence: A.**

Codex governs autonomy with two orthogonal settings ([sandbox docs][c-sandbox],
[Agent approvals & security][c-approvals]):

| Setting | Values |
|---|---|
| `sandbox_mode` | `read-only` \| `workspace-write` \| `danger-full-access` |
| `approval_policy` | `untrusted` \| `on-request` \| `never` |

Documented presets:

| Preset | Flags | Behaviour |
|---|---|---|
| Read only | `--sandbox read-only` | Read and reason; escalates for writes |
| Auto (trusted repos) | `--sandbox workspace-write --ask-for-approval on-request` | Writes inside the workspace without prompting; escalates to leave the sandbox |
| YOLO (not recommended) | `--dangerously-bypass-approvals-and-sandbox` (alias `--yolo`) | No sandbox, no prompts |

**The never-block setting is `approval_policy = never`**, and the docs endorse
it directly: "you can disable all approval prompts with `--ask-for-approval
never`. This option works [with all] sandbox modes." Crucially, that is
*orthogonal* to the sandbox — which means codexloop can be simultaneously
non-blocking **and** sandboxed. This is strictly better than claudeloop's
position, where autonomy required `permission_mode="bypassPermissions"`
wholesale. codexloop's default is therefore:

```
approval_policy = "never"        # never wait for a human
sandbox_mode    = "workspace-write"   # but stay inside the workspace
```

`danger-full-access` / `--yolo` remains available behind an explicit,
loudly-logged opt-in, for use inside a container or dedicated VM — the case the
docs themselves carve out: "configure the container to provide the isolation
you need and run Codex with `--sandbox danger-full-access`".

For extra directories the docs are explicit that `--add-dir` is the right tool:
"When you need to grant Codex write access to more directories, prefer
`--add-dir` rather than forcing `--sandbox danger-full-access`." codexloop
exposes this as `--add-folder`, keeping name parity with claudeloop's flag.

### `--full-auto` is deprecated/removed

Community reporting states `codex exec --full-auto` was deprecated at v0.128
and **removed in CLI v0.147.0** (August 2026), with scripts that still pass it
now erroring ([Codex CLI Guide 2026][c-crosley], confidence C on the exact
version numbers; the deprecation itself is corroborated by the approvals docs,
which describe `--full-auto` as "a deprecated compatibility path" that "prints
a warning"). Either way the conclusion is the same and is version-independent:

> **codexloop never emits `--full-auto`.** It emits `-c approval_policy=…` and
> `-c sandbox_mode=…`, which work on both `codex exec` and `codex exec resume`.

### Version drift is a first-class hazard

The CLI is moving fast: flags are added, deprecated, and removed within
months. codexloop therefore:

1. Records `codex --version` at run start into the audit log, so any postmortem
   starts with the exact binary.
2. Pins a **minimum supported version** and warns (not fails) above a known-good
   ceiling.
3. Keeps all argv construction in a single, heavily-tested `argv builder`
   module, so a flag change is a one-file diff plus a table-driven test update.
4. Ships a `doctor` check that runs the real binary with `--help` and asserts
   the flags codexloop depends on are present, converting a mid-run surprise
   into a pre-run failure.

---

## R9 — Codex SDK availability: TypeScript yes, Python no

**Confidence: A.**

The official Codex SDK is `@openai/codex-sdk`, a TypeScript/Node package. Its
shape ([`openai/codex` issue #7144][c-issue7144]):

```ts
interface CodexClient {
  startThread(options?: ThreadOptions): CodexThread;
  resumeThread(id: string, options?: ThreadOptions): CodexThread;
}
interface CodexThread {
  id: string | null;
  run(input: Input, options?: TurnOptions): Promise<RunResult>;
  runStreamed(input: Input, options?: TurnOptions): Promise<RunStreamedResult>;
}
```

Note that the SDK is itself a wrapper: it "simply passes [the API key] to the
CLI as `CODEX_API_KEY`" — i.e. the SDK drives the same `codex` binary
codexloop would drive directly.

**There is no official Python Codex SDK.** The PyPI name `codex-sdk` is taken
by an unrelated project (an internal SDK for `cleanlab-codex`) — checked
2026-08-13. Anyone reaching for `pip install codex-sdk` gets something else
entirely, which is worth writing down before someone adds it to a requirements
file.

**Design consequence — this is the decisive transport finding.** Since (a)
codexloop is Python, (b) there is no Python Codex SDK, and (c) the TypeScript
SDK is itself a CLI wrapper, driving the `codex` binary as a subprocess is not
a workaround — it is the *same* integration the official SDK performs, minus a
Node runtime dependency. The port stays abstract (`AgentGateway`) so an
app-server transport, or a future Python SDK, drops in without touching
`domain/` or `application/`.

This inverts claudeloop's ADR-0002 ("Agent SDK over subprocess") for a
well-understood reason, and that inversion earns its own ADR in codexloop
rather than being a silent divergence.

---

## R10 — The app-server JSON-RPC surface

**Confidence: A (existence and shape), with an explicit experimental caveat.**

Beyond the rate-limit probe of [R6](#r6--there-is-no-stable-codex-status---json-three-probe-strategies),
`codex app-server` is a full bidirectional control protocol
([Codex App Server][c-appserver], [codex_mcp_interface.md][c-mcpiface]):

- **Transports:** `stdio` (default, newline-delimited JSON), Unix socket, and
  an experimental/unsupported WebSocket listener.
- **v2 RPCs:** `thread/start`, `thread/resume`, `thread/fork`, `thread/read`,
  `thread/list`; `turn/start`, `turn/steer`, `turn/interrupt`;
  `account/read`, `account/login/start`, `account/login/cancel`,
  `account/logout`, `account/rateLimits/read`; `config/read`,
  `config/value/write`, `config/batchWrite`; `model/list`, `app/list`,
  `collaborationMode/list`.
- **Experimental gating:** `capabilities.experimentalApi: true` at
  `initialize`, else experimental methods are rejected.
- **Self-described stability:** "Status: experimental and subject to change
  without notice."

Two RPCs are strategically interesting far beyond probing:

- **`turn/interrupt`** would give codexloop a *real* mid-turn stop, rather than
  the "finish the in-flight turn, then stop" drain that a subprocess transport
  implies.
- **`turn/steer`** would allow injecting an operator prompt *into a running
  turn*, which is a strictly better `prompt --now`.

A third-party evaluation harness already ships both a Codex SDK provider and an
app-server provider and characterises the trade-off exactly as codexloop sees
it ([Promptfoo][c-promptfoo]):

> For CI and straightforward automation, prefer the … [SDK]; [the app-server]
> protocol is experimental, broader than the SDK, and designed for rich product
> integrations.

**Decision.** The subprocess/exec transport is the M2 default because it is
documented and stable. The app-server transport is scoped as an **optional
second adapter** behind the same `AgentGateway` port, targeted at M5, gated by
a capability probe, and never required for a correct run. Its rate-limit RPC is
used from M3 as enrichment only.

---

## R11 — The OpenAI Python SDK as the M4 REST surface

**Confidence: A.**

claudeloop ships a *generated* CLI over the entire Anthropic SDK
(131 endpoints) with a drift gate that fails CI when an SDK upgrade adds a
method. codexloop reaches parity by doing the same thing against the `openai`
Python SDK.

The mechanism transplants almost unchanged, because it depends on generic
Python introspection rather than anything Anthropic-specific:

- **Discovery** walks the *class* tree under `openai.resources` via the
  `cached_property` descriptors — the class tree, not a live client, so **no
  credentials are needed at import time.** Each leaf yields a resource path, a
  method name, and an `inspect.signature`.
- **Binding** maps path and scalar parameters to typed Typer options; request
  bodies go to `--json` / `--json-file` with `@path` inlining. Mapping every
  nested TypedDict to individual flags is explicitly not worth it.
- **Modifiers:** `--raw` / `--stream` select the `with_raw_response` /
  `with_streaming_response` variants; list methods auto-paginate with
  `--max-items`.
- **Providers:** the analogue of claudeloop's `--provider` (Bedrock/Vertex) is
  `AzureOpenAI` and any other alternate client class. Because those clients do
  **not** expose the full resource tree, the binder must reflect the actual
  surface of the selected client rather than offering commands that will fail
  at call time.
- **The drift gate** is what makes "no gaps" enforceable rather than aspirational:
  a test enumerates the SDK surface and asserts every endpoint method has a
  registered command, and asserts the discovered count against a committed
  baseline so *removals* are caught too. Local helpers (e.g. streaming and
  parsing helpers) are individually enumerated as bound-or-exempt — no silent
  omissions.

Surfaces to cover: `responses`, `chat.completions`, `embeddings`, `images`,
`audio`, `files`, `batches`, `fine_tuning`, `vector_stores`, `moderations`,
`models`, `uploads`, `containers`, `evals`, `webhooks`, and the beta namespaces
present at pin time. The exact count is deliberately **not** hardcoded in this
document — it is discovered by the introspector and frozen into a baseline file
at M4, which is the only number that can't rot.

**Dependency note.** `openai` is the only vendor SDK codexloop depends on, and
it lives exclusively in `infrastructure/`. **No `anthropic` and no
`claude-agent-sdk` anywhere in the tree** — enforced by `import-linter` plus a
grep-based test, so a copy-paste from the blueprint cannot smuggle one in.

---

## R12 — Structured completion output

**Confidence: A (the flag), B (end-to-end behaviour under exec).**

`codex exec --output-schema <path>` accepts a JSON Schema for the model's
response shape ([DeepWiki on headless exec][c-deepwiki], corroborated by the
CLI reference). That is the direct analogue of the
`ClaudeAgentOptions.output_format` schema claudeloop uses for typed completion
verdicts, and it lets codexloop ask each turn to answer:

```json
{
  "complete": true,
  "remaining_work": [],
  "blocked_on": null,
  "summary": "Implemented and tested the parser; all gates green."
}
```

`domain/completion.py` maps that to `Done` / `Continue(remaining)` /
`Blocked(reason)`.

**Three-layer fallback**, because a schema is a request and not a guarantee:

1. **Structured output** — parse the schema-shaped object from the final
   message (`--output-last-message` gives a clean file to read rather than
   scraping stdout).
2. **Done marker** — `CODEXLOOP_TASK_FULLY_COMPLETE`, appended as an
   instruction to the prompt, matched in the final message. Inherited from
   claudeloop and kept for exactly the case where the model ignores the schema.
3. **No signal** — treat as `Continue`. A missing verdict is *never* read as
   completion; the run continues until a budget or an explicit verdict stops it.

And the inviolable ordering rule, transplanted verbatim from claudeloop because
it was learned the hard way:

> **A capacity rejection always outranks a completion claim.** If a turn both
> claims completion and was rejected for capacity, it is a rejection. Otherwise
> a truncated limit message that happens to contain marker-like text ends the
> run early with work unfinished.

---

## Findings that become ADRs

| # | Decision | Driven by | Risk if wrong |
|---|---|---|---|
| 0001 | Onion architecture enforced by `import-linter` | claudeloop blueprint | Low — proven |
| 0002 | **Subprocess `codex exec --json` over an SDK** | [R9](#r9--codex-sdk-availability-typescript-yes-python-no) | Medium — inverts claudeloop ADR-0002; mitigated by the abstract `AgentGateway` port |
| 0003 | **`QuotaExhausted` is a distinct, non-waitable state from `WindowExhausted`** | [R1](#r1--http-429-is-two-different-failures-sharing-one-status-code) | **Critical** — the whole product |
| 0004 | Adaptive probe loop, never a blind sleep | [R3](#r3--codex-chatgpt-plan-windows-5-hour-primary-weekly-secondary), [R6](#r6--there-is-no-stable-codex-status---json-three-probe-strategies) | High — a blind sleep misses a credit top-up |
| 0005 | Layered capacity probe with a guaranteed exec floor | [R6](#r6--there-is-no-stable-codex-status---json-three-probe-strategies) | Medium — experimental sources may vanish |
| 0006 | Generated OpenAI REST surface, never hand-written | [R11](#r11--the-openai-python-sdk-as-the-m4-rest-surface) | Low — drift gate enforces it |
| 0007 | `approval_policy=never` + `sandbox_mode=workspace-write` as the default | [R8](#r8--approval-modes-and-sandboxing-how-to-never-block) | Medium — a sandbox escape is a real risk if defaults slip to full-access |
| 0008 | All policy via `-c key=value` on both exec and resume | [R5](#r5--session-continuity-codex-exec-resume-rollout-files-codex_home) | Medium — the exact bug this prevents is reported in the wild |
| 0009 | App-server as an optional second transport, never required | [R10](#r10--the-app-server-json-rpc-surface) | Low — additive |
| 0010 | Rollout-file parsing is best-effort telemetry only | [R5](#r5--session-continuity-codex-exec-resume-rollout-files-codex_home) | Low — bounded blast radius by construction |
| 0011 | Never auto-consume banked rate-limit reset credits | [R6](#r6--there-is-no-stable-codex-status---json-three-probe-strategies) | Low — but irreversible if wrong, hence explicit |
| 0012 | Minimum-supported `codex` version, asserted by `doctor` | [R8](#r8--approval-modes-and-sandboxing-how-to-never-block) | Medium — the CLI moves fast |

---

## Open questions to resolve empirically

These are written as executable experiments, not as musings. Each has a
deterministic outcome that changes the implementation, and each has a defined
fallback so the project is never blocked waiting on an answer.

| # | Question | Experiment | If the answer is "no" |
|---|---|---|---|
| Q1 | Does `turn.failed` carry a machine-readable `error.code` / `error.type`? | Force a 429 (tiny quota key), capture the JSONL | Fall back to matching the message text and stderr; keep the parser forgiving |
| Q2 | Does `rate_limits` ever populate under `codex exec` on the current CLI? | Long ChatGPT-plan run; grep the JSONL for `token_count` | Rely on strategies B and C; the bounded probe cadence is the floor |
| Q3 | Is `resets_at` epoch-seconds or ISO-8601 on this CLI version? | Inspect one live `token_count` payload | Parser accepts both plus `resets_in_seconds`; unknown shape → `None` |
| Q4 | Does `account/rateLimits/read` work on a plain ChatGPT-plan login? | Run the `initialize` handshake with `experimentalApi: true` | Disable strategy B via capability probe; `doctor` reports it as unavailable |
| Q5 | What is the exit code for a capacity rejection vs a genuine failure? | Table-driven capture across forced failure modes | Classify on the body only; exit code becomes advisory |
| Q6 | Does `--output-schema` reliably constrain the final message under exec? | Run a schema'd plan 20× and measure conformance | Lean on the `CODEXLOOP_TASK_FULLY_COMPLETE` marker as primary |
| Q7 | Does `--ephemeral` truly leave no rollout file behind? | Probe, then diff `$CODEX_HOME` | Probe against a temp `CODEX_HOME`, then delete it |
| Q8 | Do `usage_limit_reached` responses carry a reset instant anywhere? | Capture one real window exhaustion end-to-end | Bounded probe cadence under `--max-wait`; log the degradation explicitly |
| Q9 | Does `codex exec resume` accept every `-c` key the first turn does? | Table-driven argv test against the real binary | Narrow the resume override set; document the difference |
| Q10 | Minimum `codex` version supporting `--json` + `--output-schema` + `-c`? | Bisect across installed versions in CI | Raise the documented floor; `doctor` fails fast below it |

**Until Q1–Q10 are answered, the implementation assumes the pessimistic branch
of each.** That is why the wait policy is a bounded probe loop rather than a
scheduled wake-up: the schedule is an optimisation applied when a reset instant
happens to be available, not a precondition for correctness.

---

## Citation index

| Key | Source |
|---|---|
| [c-errors] | Error codes — OpenAI API. https://developers.openai.com/api/docs/guides/error-codes |
| [c-ratelimits] | Rate limits — OpenAI API. https://developers.openai.com/api/docs/guides/rate-limits |
| [c-cookbook] | How to handle rate limits — OpenAI Cookbook. https://developers.openai.com/cookbook/examples/how_to_handle_rate_limits |
| [c-clireference] | Developer commands (Codex CLI reference). https://developers.openai.com/codex/cli/reference |
| [c-noninteractive] | Non-interactive mode (`codex exec`, `--json` JSONL events). https://learn.chatgpt.com/docs/non-interactive-mode |
| [c-deepwiki] | Headless Execution Mode (`codex exec`) — DeepWiki on `openai/codex`. https://deepwiki.com/openai/codex/4.2-headless-execution-mode-(codex-exec) |
| [c-sandbox] | `docs/sandbox.md` — sandbox modes and approval policies. https://github.com/openai/codex/blob/main/docs/sandbox.md |
| [c-approvals] | Agent approvals & security. https://learn.chatgpt.com/docs/agent-approvals-security |
| [c-appserver] | Codex App Server (JSON-RPC, transports, `experimentalApi`). https://learn.chatgpt.com/docs/app-server |
| [c-mcpiface] | `codex-rs/docs/codex_mcp_interface.md` (v2 RPC list). https://github.com/openai/codex/blob/main/codex-rs/docs/codex_mcp_interface.md |
| [c-issue14728] | `openai/codex` #14728 — "emit rate_limits in exec mode JSONL output". https://github.com/openai/codex/issues/14728 |
| [c-issue7144] | `openai/codex` #7144 — TypeScript SDK auth / `CODEX_API_KEY`. https://github.com/openai/codex/issues/7144 |
| [c-usagespec] | `CODEX-USAGE-VISIBILITY-SPEC.md` — rollout `token_count.rate_limits` field survey (third-party, confidence C). https://github.com/JKHeadley/instar/blob/main/docs/specs/CODEX-USAGE-VISIBILITY-SPEC.md |
| [c-codexerrors] | `providers/codex/errors.ts` — retryable/non-retryable code sets (third-party, confidence B). https://github.com/ank1015/llm/blob/main/packages/core/src/providers/codex/errors.ts |
| [c-ccconnect] | cc-connect PR #1360 — `codex exec resume` rejects `--sandbox`; use `-c sandbox_mode=…` (third-party, confidence B). https://github.com/chenhg5/cc-connect/pull/1360 |
| [c-mindflakes] | "Codex" — app-server as a `codex status --json` substitute (community, confidence C). http://mindflakes.com/tags/codex/ |
| [c-zenn] | Consuming banked resets via `account/rateLimits/read` (community, confidence C). https://zenn.dev/tdksk/articles/7cc5a278f59ad7?locale=en |
| [c-promptfoo] | Promptfoo — OpenAI Codex App Server provider (third-party, confidence B). https://www.promptfoo.dev/docs/providers/openai-codex-app-server/ |
| [c-crosley] | Codex CLI Guide 2026 — version history, `--full-auto` removal (community, confidence C). https://blakecrosley.com/guides/codex |
| [c-claudeloop] | claudeloop 0.5.4 — the blueprint. https://github.com/adammatthewsteinberger/claudeloop |
