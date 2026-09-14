# ADR 0004: Quota-aware probe cadence; --no-probe exists

## Status

Accepted (2026-08-13).

## Context

Rejected probes may consume RPD. A naive retry loop eats the quota it waits for.

## Decision

Wait policy is a bounded, quota-aware probe loop. `--no-probe` waits only to computed boundaries. Probes are counted on the budget ledger.

## Consequences

Recorded in architecture §19. Changing this ADR requires a new numbered record, not a silent edit of the classifier or ports.
