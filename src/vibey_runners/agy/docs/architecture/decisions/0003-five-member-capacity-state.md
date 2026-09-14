# ADR 0003: Five-member CapacityState; CreditsExhausted cannot carry a reset

## Status

Accepted (2026-08-13).

## Context

Gemini 429 RESOURCE_EXHAUSTED spans RPM, RPD, and spend. A billing wall must never look waitable.

## Decision

`CapacityState` is Available | WindowExhausted | TransientThrottle | CreditsExhausted | AuthenticationFailed. `CreditsExhausted` has no `resets_at` field. Ambiguous 429 is an unknown window, never Available.

## Consequences

Recorded in architecture §19. Changing this ADR requires a new numbered record, not a silent edit of the classifier or ports.
