---
name: claudeloop-architecture
description: Explains claudeloop's onion architecture — the four layers (domain, application, infrastructure, cli), the import-linter contract enforcing them, and exactly where new code belongs. Use this whenever adding a new file, class, or function to src/claudeloop/, whenever unsure which layer something belongs in, whenever import-linter or lint-imports fails, or when the user mentions "onion architecture", "layers", "ports and adapters", "bootstrap.py", "composition root", or asks "where should this go". Make sure to consult this before writing any new module under src/claudeloop/ — placing code in the wrong layer is the most common mistake in this codebase and import-linter will reject it in CI regardless.
allowed-tools: Read Grep Glob Bash(lint-imports)
---

# claudeloop architecture

`claudeloop` is a strict onion / ports-and-adapters design. Dependencies
point inward only. This is enforced in CI and pre-commit by `import-linter`,
not by convention — a violation fails with a named contract error, not a
review comment.

## The four layers, innermost first

```
src/claudeloop/
├── domain/           # PURE. stdlib only. No I/O, no async, no third-party imports.
├── application/       # Protocol-based ports + use cases. Imports domain + stdlib only.
├── infrastructure/    # Adapters. The ONLY layer allowed to import anthropic /
│                       #   claude_agent_sdk / structlog / httpx / any third-party SDK.
├── cli/                # Typer commands. Calls application use cases via bootstrap.
└── bootstrap.py         # Composition root — the ONE module allowed to see every layer.
```

## The decision test — where does new code go?

Ask in this order:

1. **Does it touch the filesystem, network, clock, or an SDK?**
   → `infrastructure/`, behind a `Protocol` port defined in
   `application/ports.py`. Never call `anthropic.*` or `claude_agent_sdk.*`
   from anywhere else.

2. **Is it a decision — a branch determining what happens next — with zero
   I/O of its own?**
   → `domain/`. Test: can you write its test as
   `assert some_function(SomeDataclass(...)) == ExpectedResult(...)` with no
   mocking, no fixtures beyond dataclass literals? If yes, it's domain.
   Existing examples: `domain/classify.py` (turn signals → capacity state),
   `domain/waiting.py` (capacity state → next probe instant),
   `domain/completion.py` (structured output → completion verdict),
   `domain/loop.py` (the run-loop state machine itself).

3. **Is it orchestration — call a port, feed the result to a domain
   function, call another port?**
   → `application/`, as a use case in `application/usecases/` or inside
   `application/runner.py`.

4. **Is it argument parsing or terminal output formatting for a human?**
   → `cli/`.

**When in doubt, push logic inward.** A `cli/` command containing an
`if/elif` deciding what a rate-limit response *means* is a bug: that
decision belongs in `domain/classify.py`, testable with zero CLI process
spun up.

## The enforced import rules

From `pyproject.toml`:

```toml
[[tool.importlinter.contracts]]
name = "Onion layering"
type = "layers"
layers = ["claudeloop.cli", "claudeloop.bootstrap", "claudeloop.application", "claudeloop.domain"]

[[tool.importlinter.contracts]]
name = "Infrastructure only reachable from bootstrap"
type = "forbidden"
source_modules = ["claudeloop.domain", "claudeloop.application"]
forbidden_modules = ["claudeloop.infrastructure"]
```

Concretely:

- `domain/*.py` may `import` from stdlib and other `domain/*` modules ONLY.
  No `typing.Protocol`-based ports either — those live one layer out.
- `application/*.py` may import `domain` and stdlib. Ports are
  `typing.Protocol`, never an ABC a concrete adapter must inherit from —
  this is what keeps `application/` from ever needing to import
  `infrastructure/` just to name a type.
- `infrastructure/*.py` may import `domain`, `application`, and any
  third-party package. This is the ONLY place `anthropic` or
  `claude_agent_sdk` appears in an `import` statement anywhere in
  `src/claudeloop/`.
- `cli/*.py` calls into `application/` use cases obtained from
  `bootstrap.build_runner(...)` (or equivalent) — never constructs an
  `infrastructure/` adapter directly.
- `bootstrap.py` is the single seam permitted to import from every layer —
  it's where a concrete adapter (e.g.
  `infrastructure.agent.gateway.ClaudeAgentGateway`) gets wired into the
  `Protocol` port `application/ports.py` declares (e.g. `AgentGateway`).

## Verifying your change respects the contract

```bash
lint-imports
```

Run this before committing any new module. It's also a `pre-commit` hook and
runs in CI (`ci.yml`). A violation names the exact contract broken —
"Onion layering" or "Infrastructure only reachable from bootstrap" — and the
offending import chain.

## Full reference

See `docs/architecture/overview.md` for the complete layer table and
`docs/architecture/decisions/0001-onion-architecture-with-import-linter.md`
for why this was chosen over convention-only layering. See
`docs/architecture/ports-and-adapters.md` for the planned port list
(M2+) and why ports are `Protocol` rather than ABC.
