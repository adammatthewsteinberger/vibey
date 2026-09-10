# ADR 0009: Budgets are token/turn-denominated; dollars are labeled estimates

## Status

Accepted (2026-08-13).

## Context

Gemini usage metadata has no billed cost field. Silent fake dollars erode trust.

## Decision

`--max-turns` / `--max-tokens` are first-class. `--max-dollars` uses an explicit price table in `domain/pricing.py` and is always labeled `estimate`.

## Consequences

Recorded in architecture §19. Changing this ADR requires a new numbered record, not a silent edit of the classifier or ports.
