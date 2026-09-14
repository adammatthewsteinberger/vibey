# ADR 0002: Claude Agent SDK over subprocess + regex

## Status

Accepted. Implemented in M1 (domain-level typed signals); adapter
implementation planned for M2.

## Context

`claude_autoresume.py` drives Claude Code by shelling out to
`claude -p --output-format stream-json --verbose` and regex-matching the raw
stream for phrases like `"usage limit"`, `"try again later"`, and
`"rejected"` — explicitly *not* matching the whole stream, because it
routinely contains `allowed_warning` events and repo file contents that
mention "rate limit" in ordinary prose, which would false-positive.

Research during planning established that `claude-agent-sdk` (the Python
package wrapping Claude Code as a library) yields **typed** events instead:
a `RateLimitEvent` with a `status` field (`allowed` / `allowed_warning` /
`rejected`), a `ResultMessage.api_error_status`, and an
`AssistantMessage.error` enum. It also exposes a supported session-discovery
API (`list_sessions()`) replacing a glob over `~/.claude/projects/` that the
Claude Code docs explicitly warn against parsing directly, since the
transcript format changes between releases.

## Decision

Replace subprocess + regex with `claude-agent-sdk`. The domain layer
(`domain/classify.py`) consumes a `TurnSignals` dataclass populated from the
SDK's typed fields rather than parsing text.

## Consequences

- The `allowed_warning` false positive becomes a single `if` branch
  (`status == "allowed_warning"` → not a rejection) instead of a carefully
  scoped regex applied only to "trusted" text surfaces.
- Session discovery moves from a hand-rolled JSONL parser to
  `list_sessions()` / `get_session_info()`, which use cheap stat + head/tail
  reads and are the documented, version-stable way to do this.
- One new risk accepted deliberately: the Claude Code binary contains the
  string `[sdkMessageAdapter] Ignoring rate_limit_event message`, suggesting
  `RateLimitEvent` is dropped on some adapter paths. `classify()` therefore
  never depends on `RateLimitEvent` alone — it also reads
  `ResultMessage.api_error_status` and `AssistantMessage.error` as
  independent corroborating signals. See
  [`../domain-model.md`](../domain-model.md#classifypy-turnsignals-capacitystate).
- `ClaudeSDKClient` (streaming-input mode) stays alive across error results,
  where single-shot `query()` raises a plain `Exception` after yielding the
  error and exits the process. This collapses the legacy respawn-and-resume
  loop into repeated sends on one live process — planned for the M2 agent
  gateway adapter.
