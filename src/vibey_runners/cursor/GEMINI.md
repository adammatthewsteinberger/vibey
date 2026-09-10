# GEMINI.md

`cursorloop`: an onion-architected, autonomous Cursor Agent session runner.
Facts only — procedures live in `.agent/rules/` (mirrors of `.claude/skills/`
and `.cursor/rules/`).

## Non-negotiables

- Never block on a human. Every path has a non-waiting forward.
- Credits ≠ rate-limit window. `CreditsExhausted` has no `resets_at`.
- `domain/` is stdlib only. Vendor types stay in `infrastructure/`.
- Capacity rejection outranks a completion claim.
- Conventional Commits. No Anthropic dependency, ever.
- Default model: `composer-2.5` (Cursor). Grok is a `ModelProfile` only.
- Bias ambiguous capacity signals → `CreditsExhausted`.

## Layer map

```
domain → application → infrastructure → cli, bootstrap.py is the composition root
```

## Auth

`CURSOR_API_KEY` (never `ANTHROPIC_*`). `cursorloop doctor` reports config.

## Commands

```bash
pytest
pytest -m system
ruff check --fix src tests && ruff format src tests
mypy --strict src/cursorloop
lint-imports
```

## Surfaces

| Need | Go to |
|---|---|
| Procedures | `.agent/rules/`, `.claude/skills/`, `.cursor/rules/` |
| Design record | `docs/plans/architecture-and-roadmap.md` |
| Implementation plan | `docs/superpowers/plans/2026-08-13-cursorloop-implementation.md` |
| Research notes | `docs/plans/research-notes.md` |
