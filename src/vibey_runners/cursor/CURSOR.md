# CURSOR.md

`cursorloop`: an onion-architected, autonomous Cursor Agent session runner.
Composer-first (`composer-2.5`); Grok is a secondary model profile, not a
product. It never blocks on a human, and it distinguishes an exhausted
rate-limit window (waitable) from exhausted credits (never waitable).

**This file is deliberately short — it holds facts, not procedures.**

## Non-negotiables

- **Never block on a human.** Every code path must have a way forward that doesn't wait on stdin or a tool call requiring a real person.
- **Credits/billing ≠ rate-limit window.** `CreditsExhausted` has no reset time and can never be treated as waitable-with-a-deadline. Conflating the two reintroduces the exact bug this project replaces.
- **A capacity rejection always outranks a completion claim.**
- **`domain/` stays pure.** Stdlib only, no I/O, no async, no third-party imports — enforced by `import-linter`, not convention.
- **Every commit message follows Conventional Commits**, and the full quality-gate set runs green before any PR.

## Fork-specific

- **No Anthropic dependency, ever.** `anthropic` / `claude_agent_sdk` are not dependencies, not extras, not test imports. No `ANTHROPIC_*` env var is read, written, or accepted as a fallback anywhere in `src/`.
- **Grok is a model profile, not a product.** One agent adapter, one taxonomy, one CLI. Default model `composer-2.5`.
- **Bias every ambiguous capacity signal toward `CreditsExhausted`.**

## Naming

| Thing | Value |
|---|---|
| PyPI + import package + console script | `cursorloop` |
| Env prefix | `CURSORLOOP_*` |
| Vendor auth env | `CURSOR_API_KEY` (never `ANTHROPIC_*`) |
| Run state directory | `.cursorloop/` |
| Done marker | `CURSORLOOP_TASK_FULLY_COMPLETE` |
| Verdict fence | ` ```cursorloop-verdict ` |
| Test-agent gate | `CURSORLOOP_ALLOW_TEST_AGENT=1` **and** `CURSORLOOP_TEST_AGENT_SCRIPT=<path>` |
| Default model | `composer-2.5` |

## Layer map

```
domain → application → infrastructure → cli, with bootstrap.py as the sole composition root
```

Dependencies point inward only, enforced by `import-linter` in CI.

## Where to go for everything else

| Need | Go to |
|---|---|
| Design record and transplant plan | `docs/plans/architecture-and-roadmap.md` |
| Implementation plan (task-by-task) | `docs/superpowers/plans/2026-08-13-cursorloop-implementation.md` |
| Research evidence and citations | `docs/plans/research-notes.md` |
| Cross-product keep/swap outline | `docs/plans/_shared-transplant-outline.md` |
| Agent-facing facts (same non-negotiables) | `AGENTS.md` |
