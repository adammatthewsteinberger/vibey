# ADR 0001: Onion architecture enforced by import-linter

## Status

Accepted (2026-08-13).

## Context

agyloop is a CLI with domain rules that must not leak vendor types.

## Decision

Layers are `cli → bootstrap → application → domain`. Infrastructure is reachable only from bootstrap. import-linter CI enforces the contract. Domain stays stdlib-only.

## Consequences

Recorded in architecture §19. Changing this ADR requires a new numbered record, not a silent edit of the classifier or ports.
