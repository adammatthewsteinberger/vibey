---
name: agyloop-router
description: agyloop always-on router — non-negotiables, onion layers, and where Claude/Cursor/Codex/Antigravity procedures live
alwaysApply: true
allowed-tools: Read
---

# agyloop (Codex router)

`agyloop`: an onion-architected, autonomous Google Antigravity / Gemini
session runner. It never blocks on a human, and it distinguishes an
exhausted rate-limit window (waitable) from exhausted credits (never
waitable — needs a human to top up). Python 3.12+.

**This skill is deliberately short — facts, not procedures.** Procedural
guidance lives in the other `.agents/skills/agyloop-*` files.

## Non-negotiables

- **Never block on a human.**
- **Credits ≠ rate limit.** `CreditsExhausted` has no reset time.
- **`domain/` stays pure.** Stdlib only — enforced by `import-linter`.
- **A capacity rejection always outranks a completion claim.**
- **Every commit message follows Conventional Commits.**
- **Never implement on `main`.** Feature PRs squash into `develop`.

## Layer map

```
domain → application → infrastructure → cli, with bootstrap.py as the sole composition root
```

## Commands worth memorizing

```bash
pre-commit install
pytest
pytest -m system
ruff check --fix src tests && ruff format src tests
mypy --strict src/agyloop
lint-imports
mkdocs serve
mkdocs build --strict
```

## Where to go

| Need | Go to |
|---|---|
| Architecture | skill `agyloop-architecture` |
| Domain model | `agyloop-domain-model` |
| Testing | `agyloop-testing` |
| Quality gates | `agyloop-quality-gates` |
| Docs / PyPI link rules | `agyloop-docs` |
| Antigravity SDK | `agyloop-agent-sdk` |
| REST surface | `agyloop-rest-surface` |
| Releases | `agyloop-releasing` |
| Security | `SECURITY.md` |

When a skill/procedure changes, update Claude + Cursor + Codex + Antigravity in the same PR.
