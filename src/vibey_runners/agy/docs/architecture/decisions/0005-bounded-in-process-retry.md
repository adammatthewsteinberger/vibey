# ADR 0005: Bounded in-process retry with jitter

## Status

Accepted (2026-08-13).

## Context

The SDK/harness may already retry transient errors. Unbounded outer retry compounds backoff.

## Decision

In-process retry is bounded with jitter. Hard limits (credits, auth, RPD) still surface to the outer loop. The outer loop never hides a billing wall as a blip.

## Consequences

Recorded in architecture §19. Changing this ADR requires a new numbered record, not a silent edit of the classifier or ports.
