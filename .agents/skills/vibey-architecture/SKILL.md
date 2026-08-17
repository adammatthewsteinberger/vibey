---
name: vibey-architecture
description: Onion layers for vibey (domain, application, infrastructure, cli, tui), import-linter, and where new code belongs. Use before adding a module under src/vibey/.
allowed-tools: Read Grep Glob Bash(lint-imports)
---

# vibey architecture

Dependencies point inward. `import-linter` enforces this in CI via three
contracts: onion-layers, domain-independence, and application-independence.

```
src/vibey/
├── domain/            # PURE. stdlib only. No I/O, no async, no third-party.
├── application/       # Protocol ports + use cases. Imports domain + stdlib.
├── infrastructure/    # Adapters. ONLY layer that may import asyncpg, httpx, etc.
├── cli/               # Typer. Calls application via bootstrap.
├── tui/               # Textual. Calls application via bootstrap.
└── bootstrap.py       # Composition root — the ONE module that sees every layer.
```

## Where does new code go?

1. **Touches FS, network, clock, database, or an SDK?** → `infrastructure/`,
   behind a `Protocol` in `application/ports.py`. Never `import asyncpg` or
   vendor SDKs elsewhere.
2. **Pure decision, zero I/O?** → `domain/`. Examples: `phase.py`,
   `rotation.py`, `noloss.py`, `circuit.py`, `effort.py`.
3. **Orchestration (port → domain → port)?** → `application/`.
4. **Argument parsing / terminal formatting?** → `cli/` or `tui/`.
5. **Wiring concrete implementations to Protocols?** → `bootstrap.py` ONLY.

When in doubt, push logic inward. `lint-imports` names the broken contract
when you violate the onion.

## The forbidden imports

`domain/` must never import:
- Any layer: `vibey.application`, `vibey.infrastructure`, `vibey.cli`, `vibey.tui`
- Third-party: `asyncpg`, `psycopg`, `httpx`, `typer`, `structlog`, `pydantic`, `textual`
- I/O from stdlib: tested by `tests/domain/test_domain_purity.py` (an
  AST-walking test that scans for `open()`, `pathlib`, `subprocess`, `os.environ`,
  `datetime.now()`, `async def`, `await`)

`application/` must never import:
- `vibey.infrastructure`, `vibey.cli`, `vibey.tui`

## Verify before committing

```bash
uv run lint-imports
```

If it fails, the error names the contract and the violating import. Fix it by
moving the offending code to a layer that can legally import the dependency,
or by abstracting the dependency behind a Protocol in `application/ports.py`.

See ADR-0001 (onion architecture).
