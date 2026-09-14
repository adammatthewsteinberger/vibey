# Hash-verified merge and restore of hooks.json

- Status: Accepted
- Date: 2026-08-13

## Context
A crashed run must not leave a permanently mutated user hooks file.

## Decision
Snapshot prior bytes + hash; on restore, only rewrite if the on-disk file still matches the managed merge (preserve user edits mid-run).

## Consequences
`cursorloop reset` is the operator recovery path when restore cannot run automatically.
