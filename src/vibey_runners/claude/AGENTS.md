# AGENTS.md

`claudeloop`: an onion-architected, autonomous Claude Code session runner
and full Anthropic SDK CLI. It never blocks on a human, and it distinguishes
an exhausted rate-limit window (waitable) from exhausted credits (never
waitable — needs a human to top up). Pre-1.0; milestones M1–M5 are complete.
Operator mid-run control (stop/prompt/logs/savepoints, plus resources,
permissions/cwd, chat ops, and response actions) ships on top of that core.

**This file is deliberately short — it holds facts, not procedures.** Every
"how do I..." lives in a skill below; every "why was it built this way"
lives in `docs/architecture/decisions/`.

## Non-negotiables

- **Never block on a human.** Every code path must have a way forward that
  doesn't wait on stdin or a tool call requiring a real person.
- **Credits ≠ rate limit.** `CreditsExhausted` has no reset time and can
  never be treated as waitable-with-a-deadline. Conflating the two
  reintroduces the exact bug this project replaces.
- **`domain/` stays pure.** Stdlib only, no I/O, no async, no third-party
  imports — enforced by `import-linter`, not convention.
- **A capacity rejection always outranks a completion claim.**
- **Every commit message follows Conventional Commits** — a git hook
  rejects anything else.

## Layer map

```
domain → application → infrastructure → cli, with bootstrap.py as the sole composition root
```

Dependencies point inward only, enforced by `import-linter` in CI. See the
`claudeloop-architecture` skill before adding any new file.

## Commands worth memorizing

```bash
pre-commit install                 # one-time: wires up lint + commit-msg hooks
pytest                              # run the test suite (skips live + system)
pytest -m system                    # deterministic system-live harness (no tokens)
ruff check --fix src tests && ruff format src tests
mypy src/claudeloop
lint-imports                        # verify the onion contract
mkdocs serve                        # preview docs locally
mkdocs build --strict
```

## Where to go for everything else

| Need | Go to |
|---|---|
| How to work on any specific part of this codebase | `.agents/skills/` (Codex), `.claude/skills/` (Claude Code), `.cursor/rules/` (Cursor) — same eight procedures, mirrored |
| System design and why each hard call was made | `docs/architecture/` and `docs/architecture/decisions/` |
| User-facing docs | `docs/getting-started/`, `docs/guides/` |
| Contributor workflow, gitflow, releases | `CONTRIBUTING.md`, `docs/contributing/` |
| The original approved plans | `docs/plans/` |
| The behavior being replaced, and why | `legacy/claude_autoresume.py` |
| Security policy / threat model | `SECURITY.md` |

**Maintenance:** when procedural guidance changes, update Claude skills,
Cursor rules, and `.agents/skills/` in the **same PR**.
