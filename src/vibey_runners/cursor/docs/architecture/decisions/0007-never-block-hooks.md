# Never-block via managed hooks and related mechanisms

- Status: Accepted
- Date: 2026-08-13

## Context
Cursor has no `can_use_tool` callback. Autonomy must not wait on a human.

## Decision
Combine managed `.cursor/hooks.json`, an autonomy preamble, `local.force`, and a stall watchdog. `--no-managed-hooks` is the escape hatch.

## Consequences
Runs can mutate hooks.json; hash-verified restore and `cursorloop reset` recover from crashes.
