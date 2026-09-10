---
name: agyloop-docs
description: Where content belongs (routers vs skills vs docs), MkDocs strict build, PyPI-safe absolute README links.
allowed-tools: Read Grep Glob Bash(mkdocs *)
---

# agyloop documentation

| Content | Goes in |
|---|---|
| Always-true facts | `CLAUDE.md`, `AGENTS.md`, `GEMINI.md` (short routers) |
| Procedures | `.claude/skills/`, `.cursor/rules/`, `.agents/skills/`, `.agent/rules/` |
| User how-to | `docs/getting-started/`, `docs/guides/` |
| One hard decision | `docs/architecture/decisions/` |
| Contributor process | `docs/contributing/` |

README is what PyPI renders: **absolute** URLs only for docs, repo,
security, contributing, changelog. Relative `docs/*.md` links break on PyPI.

```bash
pip install -e ".[docs]"
mkdocs serve
mkdocs build --strict
```

`edit_uri` stays `edit/main/docs/` — the published site tracks `main`.

When a procedure changes, update Claude + Cursor + Codex + Antigravity in
the same PR.
