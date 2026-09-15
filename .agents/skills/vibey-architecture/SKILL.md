---
name: vibey-architecture
description: Onion layers for vibey (domain, application, infrastructure, cli, tui), import-linter, and where new code belongs. Use before adding a module under src/vibey/.
allowed-tools: Read Grep Glob Bash(lint-imports)
---

# vibey architecture

Dependencies point inward. `import-linter` enforces this in CI via four
contracts: onion-layers, domain-independence, application-independence, and
interfaces-declare-only.

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

## Shape: classes, behind interfaces

Code lives in **class objects**. A module-level function is the method of last
resort — a package's `__all__` façade, a `__main__` entry point, a bare function
some library contract requires — and where you use one, write the reason at the
definition. "It is only a few lines" is not a reason.

**Every class has an interface beside it**, in a mirrored `interfaces/` directory:

```
src/vibey/services/github_service.py
src/vibey/services/interfaces/github_service_interface.py
```

The mapping is mechanical: the directory gains an `interfaces/` child, the module
gains an `_interface` suffix. Interfaces **declare**; they never consume — an
interface module imports the standard library and other interfaces, nothing else
from its own tree. That is the `interfaces-declare-only` contract, and it applies
to every `interfaces/` package, not just `application/interfaces`.

Why: a class behind an interface is substituted at its seam. The caller takes the
interface, the test passes a double, and nothing is patched — so the test depends
on the contract, which is meant to be stable, rather than on the import graph,
which is not. With a 100% branch floor that is not a style preference: a branch
reachable only by `monkeypatch.setattr` is a branch whose test breaks for reasons
unrelated to its subject.

This applies to **new and changed code**. The existing tree (289 module-level
functions, 288 unfaced classes, measured 2026-09-15) converges module by module,
and the absorbed subtrees under `src/vibey_runners/` and `src/vibey_tools/`
converge as they are touched — rewriting them on import would destroy the
property their import exists to create. `domain/` gets no exemption: a pure
function becomes a method on a stateless class, and purity is preserved, because
purity was never about the absence of a class.

See ADR-0016.

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
