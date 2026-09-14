# The generated REST API surface

`claudeloop api ...` covers the `anthropic` Python SDK's endpoint-backed
methods without hand-writing each command. Discovery walks the SDK resource
class tree at build time; a CI drift gate asserts 1:1 parity with the
installed SDK. See [ADR 0006](../architecture/decisions/0006-generated-rest-surface-not-hand-written.md).

## Why this exists alongside `ant`

Anthropic's own `ant` CLI already covers the full 131-endpoint REST surface
of the `anthropic` Python SDK — generated from the same OpenAPI spec.
`claudeloop api ...` is not trying to replace it; it exists so the same
binary that drives autonomous Claude Code sessions can also reach any
Anthropic API endpoint directly, without a second tool install, for
workflows that mix both (e.g. an autonomous run that also needs to check
`claudeloop api messages count-tokens` before kicking off a large plan).

## How it's generated

At import time, `infrastructure/api/introspect.py` walks the *class* tree
under `anthropic.resources` — via the `cached_property` descriptors, not a
live client instance, so this works with zero credentials configured. Every
discovered method becomes a Typer command under `claudeloop api`, following
the SDK's own nesting (`claudeloop api beta sessions events send`, mirroring
`client.beta.sessions.events.send(...)`).

## Command shape

```bash
claudeloop api messages create \
  --model claude-opus-5 \
  --max-tokens 1024 \
  --json '{"messages": [{"role": "user", "content": "hello"}]}'

claudeloop api messages create --json-file request.json --stream

claudeloop api beta:sessions list --max-items 20 --raw
```

- **Path and scalar parameters** become real, typed Typer options.
- **The request body** is `--json <inline>` or `--json-file <path>`
  (supporting `@path` inlining the same way Anthropic's own `ant` CLI does)
  rather than flattening every nested `TypedDict` field into individual
  flags — not worth the complexity for deeply nested request shapes.
- **`--raw`** selects the SDK's `with_raw_response` variant (headers, status
  code, unparsed body).
- **`--stream`** selects `with_streaming_response` where the method supports
  it.
- **`--max-items N`** bounds auto-pagination on list endpoints, mirroring
  `ant`'s `--max-items`.
- **`--provider`** selects among `AnthropicAWS`, `AnthropicVertex`,
  `AnthropicBedrock`, `AnthropicBedrockMantle`, `AnthropicGoogleCloud`, and
  `AnthropicFoundry` in place of the default first-party client. Only
  `AnthropicAWS`, `AnthropicGoogleCloud`, and `AnthropicFoundry` expose the
  SDK's full resource tree; the generated command set for the other
  providers is correspondingly narrower (Messages and Beta only), by
  design — see ADR 0006.

## The drift gate

A CI test enumerates every endpoint-backed method the installed `anthropic`
SDK exposes and asserts each one has a registered `claudeloop api` command.
The test also checks the discovered method count against a committed
baseline, so a method *disappearing* from a newer SDK version is caught,
not just one appearing. This is what makes "1:1 parity" a claim CI enforces
rather than a claim that quietly rots the next time `anthropic` ships a
minor release.
