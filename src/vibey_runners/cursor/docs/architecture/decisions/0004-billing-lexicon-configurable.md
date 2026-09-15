# Billing lexicon is configurable and harvested

- Status: Accepted
- Date: 2026-08-13

## Context
Cursor does not publish a stable credits discriminator on RateLimitError.

## Decision
Maintain a configurable billing lexicon; capture unmatched terminal errors into the audit log; expose `doctor --explain-error`.

## Consequences
Wrong strings waste a window bounded by max-wait — not an infinite hang.
