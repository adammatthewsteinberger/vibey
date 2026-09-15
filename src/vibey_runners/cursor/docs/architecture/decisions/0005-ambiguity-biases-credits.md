# Ambiguity resolves toward CreditsExhausted

- Status: Accepted
- Date: 2026-08-13

## Context
Misclassifying credits as a window causes a useless deadline wait.

## Decision
When signals are ambiguous, prefer `CreditsExhausted` over `WindowExhausted`.

## Consequences
Failure mode is a spurious top-up notification, not a hang past a fabricated reset.
