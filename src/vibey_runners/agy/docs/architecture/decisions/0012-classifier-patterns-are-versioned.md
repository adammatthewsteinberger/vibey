# ADR 0012: Classifier string patterns are versioned, fixture-backed, and counted

## Status

Accepted (2026-08-13).

## Context

A billing wall misread as RPM is the highest-cost classification bug.

## Decision

Spend markers live in `_SPEND_MARKERS`. Golden fixtures under `tests/fixtures/errors/` lock the ladder. `classify_explained` names the rung. Ambiguity defaults to a bounded unknown window.

## Consequences

Recorded in architecture §19. Changing this ADR requires a new numbered record, not a silent edit of the classifier or ports.
