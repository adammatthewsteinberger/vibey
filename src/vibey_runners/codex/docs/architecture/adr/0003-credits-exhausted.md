# ADR 0003 — CreditsExhausted is structurally non-waitable

## Status

Accepted

## Context

Recorded from the architecture seed list.

## Decision

`QuotaExhausted` has no reset field so billing walls cannot be scheduled.

## Consequences

Documented in the architecture roadmap; CI enforces the load-bearing ones.
