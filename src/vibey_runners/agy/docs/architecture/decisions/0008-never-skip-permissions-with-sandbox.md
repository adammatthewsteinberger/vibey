# ADR 0008: Never combine skip-permissions with --sandbox

## Status

Accepted (2026-08-13).

## Context

antigravity-cli#36: `--dangerously-skip-permissions` defeats `--sandbox`.

## Decision

SDK `run` refuse-closes `--unsafe-skip-permissions`. CLI gateway emits skip-permissions only after root/git/sandbox gates, never with `--sandbox`. All refusals include the #36 warning.

## Consequences

Recorded in architecture §19. Changing this ADR requires a new numbered record, not a silent edit of the classifier or ports.
