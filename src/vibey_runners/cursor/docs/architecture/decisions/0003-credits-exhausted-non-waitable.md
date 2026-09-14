# CreditsExhausted is distinct and non-waitable

- Status: Accepted
- Date: 2026-08-13

## Context
Conflating billing exhaustion with a rate-limit window caused the bug this project replaces.

## Decision
`CreditsExhausted` has no reset time and must never be treated as waitable-with-a-deadline. Waiting uses a bounded probe cadence, not a blind sleep until a fabricated reset.

## Consequences
Operators get a notification on entry; `--max-wait` still bounds the probe loop.
