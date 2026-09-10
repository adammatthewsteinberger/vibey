# GEMINI.md

`agyloop`: an onion-architected, autonomous Google Antigravity / Gemini
session runner. Facts only — procedures live in `.agent/rules/` (mirrors of
`.claude/skills/` and `.cursor/rules/`).

## Non-negotiables

- Never block on a human. `ask_question` is denied with guidance.
- Credits ≠ rate-limit window. `CreditsExhausted` has no `resets_at`.
- `domain/` is stdlib only. Vendor types stay in `infrastructure/`.
- Capacity rejection outranks a completion claim.
- Conventional Commits. Never implement on `main`.
- Developer lane: `GOOGLE_API_KEY` (or `GEMINI_API_KEY`). Do not set
  `GOOGLE_GENAI_USE_VERTEXAI` when using the Developer key.
- `--unsafe-skip-permissions` is refused on `--gateway sdk`.

## Layer map

```
domain → application → infrastructure → cli, bootstrap.py is the composition root
```

## Auth

`agyloop doctor` reports the lane. It never guesses Developer vs Vertex
when both look possible.

## Commands

```bash
pytest
pytest -m system
mypy --strict src/agyloop
lint-imports
mkdocs build --strict
```

## Surfaces

| Need | Go to |
|---|---|
| Procedures | `.agent/rules/`, `.claude/skills/`, `.cursor/rules/` |
| ADRs | `docs/architecture/decisions/` |
| Releases | `docs/contributing/release-process.md` |
| Harness patch | `docs/contributing/harness-patch.md` |
