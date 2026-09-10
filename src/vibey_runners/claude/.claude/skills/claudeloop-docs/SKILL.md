---
name: claudeloop-docs
description: Explains where different kinds of content belong in this repo (CLAUDE.md vs .claude/skills/ vs docs/), how to build and strict-check the MkDocs Material site, and the writing conventions used throughout (Roadmap admonitions, relative links, ADR format). Use this whenever writing or editing any file under docs/, whenever deciding whether new content belongs in CLAUDE.md, a skill, or docs/, whenever the user asks about documentation structure, or before adding a page to mkdocs.yml's nav. Make sure to consult this before adding procedural, multi-step content to CLAUDE.md directly — CLAUDE.md is deliberately kept short and holds only facts; procedures belong in a skill instead, and getting this wrong bloats the context every single session pays for.
allowed-tools: Read Grep Glob Bash(mkdocs *)
---

# claudeloop documentation

## Where content belongs — the decision table

| Content | Goes in |
|---|---|
| An always-true fact, cheap to state, every session needs | `CLAUDE.md` **and** `AGENTS.md` — kept deliberately SHORT, routers not manuals |
| A procedure for working on a specific part of this codebase | `.claude/skills/<name>/SKILL.md` **and** mirrored to `.cursor/rules/<name>.mdc` **and** `.agents/skills/<name>/SKILL.md` |
| User-facing "how do I..." | `docs/getting-started/` or `docs/guides/` |
| System design — what exists, how pieces fit | `docs/architecture/` |
| The reasoning behind ONE specific hard decision | `docs/architecture/decisions/` — an ADR |
| Generated API docs | `docs/reference/api.md` via `mkdocstrings` — never hand-write signatures that already exist as docstrings |
| Contributor process | `docs/contributing/` |
| Historical plans, preserved verbatim once superseded | `docs/plans/` |

**The CLAUDE.md / AGENTS.md / skill dividing line:** routers hold facts;
skills/rules hold procedures. If you're about to add a multi-step "when
doing X, do Y then Z" instruction to `CLAUDE.md` or `AGENTS.md`, it belongs
in a skill instead — skills load into context only when relevant.

### Three agent surfaces (must stay in sync)

| Surface | Paths |
|---|---|
| Claude Code | `CLAUDE.md` + `.claude/skills/*/SKILL.md` |
| Cursor | `.cursor/rules/claudeloop-router.mdc` (always) + `.cursor/rules/claudeloop-*.mdc` |
| Codex | `AGENTS.md` + `.agents/skills/*/SKILL.md` |

**PR checklist:** when procedural guidance changes, update all three trees
in the same PR. No codegen in v1 — manual mirror.

## Building and checking the site

```bash
pip install -e ".[docs]"
mkdocs serve      # local preview at http://127.0.0.1:8000, live-reloads
mkdocs build --strict   # what CI runs — fails on ANY warning, most commonly a broken link
```

Run `mkdocs build --strict` before opening a PR that touches `docs/` — it's
exactly what `docs.yml` runs in CI.

## Writing conventions

- **Plain markdown only** — the extensions enabled in `mkdocs.yml`
  (admonitions, code fences, tables) and nothing docs-only-syntax beyond
  that, because every page must read correctly as plain text on GitHub
  (`CLAUDE.md` and the skills link straight to file paths, not built-site
  URLs).
- **Relative links, not absolute site URLs** — so links work both on GitHub
  and in the built MkDocs site.
- **Explain "why," not just "what."** A page restating a function signature
  the code already shows isn't earning its place — put reasoning a stranger
  can't get from the code alone into the page. This is exactly the ADRs'
  purpose.
- **Mark roadmap content with `!!! note "Roadmap"`** at the top of any page
  describing a not-yet-built milestone, so a reader never mistakes a design
  intention for current behavior. `grep -rl '!!! note "Roadmap"' docs/`
  finds every page that needs revisiting as a milestone lands.
- **New page → add it to `mkdocs.yml`'s `nav:`** or `mkdocs build --strict`
  will not error (an orphaned page is not itself a strict-mode failure) but
  the page becomes unreachable from the site nav — always add it.

## ADR format

Follow the existing files in `docs/architecture/decisions/` exactly:
`NNNN-kebab-case-title.md`, sections `## Status` / `## Context` / `##
Decision` / `## Consequences`, four-digit zero-padded sequential numbering.
Add a new ADR when a PR makes a hard, non-obvious design call worth
preserving the reasoning for — not for routine changes.

## Full reference

`docs/contributing/documentation.md`.
