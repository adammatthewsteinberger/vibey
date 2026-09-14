# Completion via verdict fence, marker, empty-turn, plan reconciliation

- Status: Accepted
- Date: 2026-08-13

## Context
Cursor has no structured output_format for agents.

## Decision
Four-tier completion: `cursorloop-verdict` fence, done marker, empty-turn soft-fail, WorkPlan checkbox reconciliation. Capacity rejection outranks any completion claim.

## Consequences
Non-compliant models run to a budget cap; `--require-verdict` can tighten the gate.
