# codexloop-docs (Antigravity mirror of `.claude/skills/codexloop-docs/SKILL.md`)


# codexloop docs

User-facing documentation lives in `docs/` and is built with
mkdocs-material.

## Structure

```
docs/
├── index.md                      # landing page
├── getting-started.md
├── guides/                       # how-to guides
│   └── rest-api-surface.md
├── architecture/
│   ├── index.md
│   └── adr/                      # Architecture Decision Records
│       ├── index.md
│       ├── 0001-onion-import-linter.md
│       └── 0002-subprocess-codex-exec.md
├── contributing.md
└── publishing.md
```

## Commands

```bash
mkdocs serve          # live preview at http://127.0.0.1:8000
mkdocs build --strict # fail on warnings
```

`--strict` runs in CI via `.github/workflows/docs.yml`.

## ADRs

Architecture Decision Records follow the Nygard format. Each ADR gets a
number (0001, 0002, ...) and a kebab-case title. Add new ADRs to
`docs/architecture/adr/index.md`.

## Excluded paths

`mkdocs.yml` excludes `plans/**` and `superpowers/**` from the built
site. These are workspace-specific and not user-facing.

## Before pushing doc changes

Run `mkdocs build --strict` to catch broken links, missing pages, and
markdown errors.
