# Architecture overview

An unattended agent loop has one structural enemy: I/O and vendor quirks
leaking into the logic that decides when to run, wait, or stop. cursorloop
keeps that decision logic pure by building as an onion:

```
domain  ←  application  ←  infrastructure  ←  cli
              ↑ composition root: bootstrap.py
```

- **domain** — pure decision logic: the run-loop state machine, the capacity
  ADT, the budget ledger, completion verdicts. No I/O, no SDK imports, fully
  unit-testable.
- **application** — use cases and ports: the orchestration that a CLI or any
  other driver calls, expressed against `Protocol` interfaces in
  `application/ports.py`.
- **infrastructure** — the adapters: Cursor agent transport, the generated
  Cloud Agents REST client, git savepoints, config, logging/audit, the state
  bus and stream UI.
- **cli** — Typer commands that translate flags into use-case calls; nothing
  else lives there.
- **bootstrap.py** — the only place concrete adapters meet ports.

An import-linter contract enforces the onion in CI: domain imports nothing
above it, and only bootstrap wires the layers together.
