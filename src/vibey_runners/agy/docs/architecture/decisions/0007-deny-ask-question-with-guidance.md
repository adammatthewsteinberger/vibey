# ADR 0007: ask_question is denied with guidance, never auto-answered

## Status

Accepted (2026-08-13).

## Context

HITL `questions_request` would block an unattended run. Fabricating a choice is unreviewable.

## Decision

OnInteractionHook returns F5 deny-with-guidance text. `--strict-autonomy` also disables ASK_QUESTION. Interactive hooks are never registered.

## Consequences

Recorded in architecture §19. Changing this ADR requires a new numbered record, not a silent edit of the classifier or ports.
