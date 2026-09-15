# Onion architecture enforced by import-linter

- Status: Accepted
- Date: 2026-08-13

## Context
cursorloop must keep capacity, waiting, and completion decisions pure so they can be tested without I/O.

## Decision
Four layers — domain → application → infrastructure → cli — with bootstrap as the sole composition root. `import-linter` enforces the onion in CI.

## Consequences
Application never imports infrastructure. Domain stays stdlib-only.
