# Cloud Agents REST surface — documented deferral with a live partial subset

- Status: Accepted (amended)
- Date: 2026-08-13
- Deciders: cursorloop maintainers

## Context

The Cloud Agents API v1 is beta and warned to change. Generating a full
`cursorloop cloud …` surface from an unstable published OpenAPI document would
either break between releases or ship a silent partial CLI.

M1–M3 (local autonomous runner) do not depend on Cloud Agents REST. Operators
still need `me` / `models` / agent create-get-cancel for ops.

## Decision

**Defer full OpenAPI → CLI generation.** Keep a digest-pinned *sketch* document
covering the runner-needed subset. CI pins the digest and asserts every
`operationId` is registered.

**Ship the partial subset as live HTTP** (`cursorloop cloud me|models|create|get|cancel`)
via `CloudAgentsGateway` (Bearer + redaction). Help text and `cloud status`
still label the surface **PARTIAL** and point at this ADR — completeness is
not claimed.

## Consequences

- Operators get working REST for the handful of endpoints the runner needs.
- Expanding to a generated full surface remains a deliberate digest bump + ADR
  amendment, not a silent expansion.
- Local autonomous runs remain unaffected.
