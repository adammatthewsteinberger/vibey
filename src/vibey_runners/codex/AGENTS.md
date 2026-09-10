# AGENTS.md

`codexloop`: an onion-architected, autonomous OpenAI Codex session runner.
It never blocks on a human, and it distinguishes an exhausted rate-limit
window (waitable) from exhausted quota (never waitable — needs a human to
top up). Pre-1.0. Python 3.12+.

**This file is deliberately short — it holds facts, not procedures.** Every
"how do I..." lives in a skill below; every "why was it built this way"
lives in `docs/architecture/decisions/`.

## Non-negotiables

- **Never block on a human.** Every code path must have a way forward that
  doesn't wait on stdin or a tool call requiring a real person.
- **Quota ≠ rate limit.** `QuotaExhausted` has no reset time and can never
  be treated as waitable-with-a-deadline.
- **`domain/` stays pure.** Stdlib only, no I/O, no async, no third-party
  imports — enforced by `import-linter`, not convention.
- **A capacity rejection always outranks a completion claim.**
- **Body-first classification.** HTTP status is consulted only after
  `error.code` / `error.type`.
- **Every commit message follows Conventional Commits** — a git hook
  rejects anything else.
- **Never implement on `main`.** Feature PRs squash into `develop`;
  `develop` merge-commits into `main`.
- **Never `--full-auto`.** Never bare `codex`.

## Layer map

```
domain → application → infrastructure → cli, with bootstrap.py as the sole composition root
```

Dependencies point inward only, enforced by `import-linter` in CI. See the
`codexloop-architecture` skill before adding any new file.

## Commands worth memorizing

```bash
pre-commit install
pytest
pytest -m system
pytest -m live  # needs OPENAI_API_KEY
ruff check --fix src tests && ruff format src tests
mypy --strict src/codexloop
lint-imports
bandit -q -r src/codexloop
pip-audit
```

## Where to go for everything else

| Need | Go to |
|---|---|
| How to work on any specific part of this codebase | `.agents/skills/`, `.claude/skills/`, `.cursor/rules/`, `.agent/rules/` |
| System design and why each hard call was made | `docs/architecture/decisions/` |
| User-facing docs | `docs/getting-started/`, `docs/guides/` |
| Contributor workflow, gitflow, releases | `CONTRIBUTING.md`, `docs/contributing/` |
| Security policy | `SECURITY.md` |

**Maintenance:** when procedural guidance changes, update Claude skills,
Cursor rules, Codex skills, and Antigravity rules in the **same PR**.
