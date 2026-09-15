---
name: claudeloop-rest-surface
description: Explains the design of the generated `claudeloop api ...` command tree — introspecting the anthropic SDK's resource class tree, binding methods to Typer commands, the --raw/--stream/--provider modifiers, and the CI drift gate that enforces 1:1 parity with the SDK. Use this whenever building or modifying src/claudeloop/infrastructure/api/ (introspect.py, binder, gateway, providers) or the generated CLI sub-app, whenever the user asks about the REST API surface, the anthropic SDK's endpoints, or "1:1 parity" / "drift gate" / "no gaps". Make sure to consult this before hand-writing any command under claudeloop api — every command in that namespace must be generated from SDK introspection, never hand-written one at a time, or the drift gate becomes meaningless and the "no gaps" claim becomes false.
---

# claudeloop REST surface (generated, not hand-written)


> **Codex skill mirror** of `.claude/skills/claudeloop-rest-surface/SKILL.md`. When this guidance changes, update Claude skill, Cursor rule, and `.agents/skills/` in the same PR.

`claudeloop api ...` covers all of the `anthropic` Python SDK's endpoint
methods without a single one being hand-written. This is the load-bearing
constraint of the whole subsystem — see ADR 0006 for why (short version:
Anthropic's own `ant` CLI already exists and covers this surface from the
same OpenAPI spec; a hand-written duplicate would silently rot the moment
anyone stopped tracking upstream SDK changes by hand).

## How discovery works — no live client needed

Walk the **class tree** under `anthropic.resources` via its
`cached_property` descriptors, not an instantiated `anthropic.Anthropic()`
client. This means discovery works with zero credentials configured — the
drift-gate CI test can run without any API key secret. Each leaf yields a
resource path, a method name, and its `inspect.signature`.

## Command binding rules

- **Path/scalar parameters** → real, typed Typer options.
- **Request body** → `--json <inline>` / `--json-file <path>` with `@path`
  file inlining, matching `ant`'s own approach — do not flatten every
  nested `TypedDict` field into individual flags; `ant` independently
  reached the same conclusion for the same reason (the request shapes are
  too deeply nested for that to stay usable).
- **`--raw`** selects the SDK's `with_raw_response` variant.
- **`--stream`** selects `with_streaming_response` where the method
  supports it.
- **`--max-items N`** bounds auto-pagination on list endpoints.
- **`--provider`** selects an alternate SDK client
  (`AnthropicAWS`/`AnthropicVertex`/`AnthropicBedrock`/
  `AnthropicBedrockMantle`/`AnthropicGoogleCloud`/`AnthropicFoundry`).
  **Only `AnthropicAWS`, `AnthropicGoogleCloud`, and `AnthropicFoundry`
  carry the SDK's full resource tree** — the others expose Messages and
  Beta only. The binder must reflect this per-provider difference; do not
  generate a command for a provider that would simply fail at runtime.

## The drift gate — what makes "no gaps" a real claim

A CI test enumerates every endpoint-backed method the installed `anthropic`
SDK exposes and asserts each has a registered `claudeloop api` command.
It also asserts the discovered method **count** against a committed
baseline, so a method disappearing from a newer SDK release is caught too,
not just additions. If you add a new hand-bound command (for one of the six
local helpers below), update the baseline deliberately — don't let the test
silently pass with a stale count.

## The six local helpers with no HTTP endpoint

`messages.stream`, `messages.parse`, `beta.messages.stream`,
`beta.messages.parse`, `beta.messages.tool_runner`, `beta.webhooks.unwrap`
— none of these map to a discoverable `cached_property` endpoint, so
introspection alone won't find them. Each must be **explicitly enumerated**
in the drift test as either hand-bound to a command or deliberately
exempted with a stated reason — never silently forgotten. If you're adding
support for one of these, add it to that explicit list, not just a new
Typer command.

## Full reference

`docs/architecture/decisions/0006-generated-rest-surface-not-hand-written.md`,
`docs/guides/rest-api-surface.md`.
