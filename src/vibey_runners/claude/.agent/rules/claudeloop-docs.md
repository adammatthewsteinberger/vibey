# claudeloop-docs (Antigravity mirror of `.claude/skills/claudeloop-docs/SKILL.md`)


# claudeloop documentation

## Where content belongs

| Content | Goes in |
|---|---|
| Always-true fact, every session needs | `CLAUDE.md` / `AGENTS.md` / `GEMINI.md` — routers, not manuals |
| Procedure for working on specific part | `.claude/skills/` **and** `.cursor/rules/` **and** `.agents/skills/` **and** `.agent/rules/` |
| User-facing "how do I..." | `docs/getting-started/` or `docs/guides/` |
| System design | `docs/architecture/` |
| One specific hard decision | `docs/architecture/decisions/` — an ADR |
| Generated API docs | `docs/reference/api.md` via `mkdocstrings` |
| Contributor process | `docs/contributing/` |
| Historical plans | `docs/plans/` |

**PR checklist**: when procedural guidance changes, update all four trees
(Claude skills, Cursor rules, Codex skills, Antigravity rules) in the same PR.

## Building site

```bash
mkdocs serve              # local preview at http://127.0.0.1:8000
mkdocs build --strict     # what CI runs — fails on ANY warning
```

Run `mkdocs build --strict` before opening PR that touches `docs/`.

See `docs/contributing/documentation.md`.
