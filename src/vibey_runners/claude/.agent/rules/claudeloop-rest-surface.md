# claudeloop-rest-surface (Antigravity mirror of `.claude/skills/claudeloop-rest-surface/SKILL.md`)


# claudeloop REST surface (generated)

`claudeloop api ...` covers all `anthropic` SDK endpoints, generated from
SDK introspection. No hand-written commands in this namespace — the drift
gate enforces 1:1 parity.

## Discovery (zero credentials)

Walk class tree under `anthropic.resources` via `cached_property`
descriptors. Works with no API key configured.

## Command binding

- Path/scalar params → Typer options
- Request body → `--json <inline>` / `--json-file <path>` with `@path`
  inlining
- `--raw` → `with_raw_response`
- `--stream` → `with_streaming_response`
- `--max-items N` → auto-pagination bound
- `--provider` → alternate SDK client (`AnthropicAWS`, `AnthropicGoogleCloud`,
  `AnthropicFoundry`, etc.). Only `AnthropicAWS`, `AnthropicGoogleCloud`,
  `AnthropicFoundry` carry full resource tree.

## Drift gate (CI test)

Enumerates every endpoint-backed method in installed `anthropic` SDK,
asserts each has a registered command. Also asserts discovered method count
vs committed baseline — catches disappearing methods too.

Six local helpers with no HTTP endpoint (`messages.stream`,
`messages.parse`, `beta.messages.stream`, `beta.messages.parse`,
`beta.messages.tool_runner`, `beta.webhooks.unwrap`) must be explicitly
enumerated in drift test.

See ADR 0006.
