# ADR 0011: Auth lane is resolved and reported by doctor, never guessed

## Status

Accepted (2026-08-13).

## Context

Developer API and Vertex/Enterprise have different quota semantics. Guessing the lane misclassifies limits.

## Decision

`agyloop doctor` reports lane+source. Conflict (GOOGLE_API_KEY + Vertex flag) is unresolved and fails the auth check. Auth failure is terminal in the run loop.

## Consequences

Recorded in architecture §19. Changing this ADR requires a new numbered record, not a silent edit of the classifier or ports.
