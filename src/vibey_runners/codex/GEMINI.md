# GEMINI.md

`codexloop`: an onion-architected, autonomous OpenAI Codex session runner.
Facts only — procedures live in `.agent/rules/` (mirrors of
`.claude/skills/` and `.cursor/rules/`).

## Non-negotiables

- Never block on a human. `ask_question` is denied with guidance.
- Quota ≠ rate-limit window. `QuotaExhausted` has no `resets_at`.
- `domain/` is stdlib only. Vendor types stay in `infrastructure/`.
- Capacity rejection outranks a completion claim.
- Body-first classification. HTTP status after `error.code` / `error.type`.
- Conventional Commits. Never implement on `main`.
- Never `--full-auto`. Never bare `codex`.
- App-server transport is optional and falls back to exec.

## Layer map

```
domain → application → infrastructure → cli, bootstrap.py is the composition root
```

## Commands

```bash
pytest
pytest -m system
pytest -m live  # needs OPENAI_API_KEY
mypy --strict src/codexloop
lint-imports
bandit -q -r src/codexloop
pip-audit
```

## Surfaces

| Need | Go to |
|---|---|
| Procedures | `.agent/rules/`, `.claude/skills/`, `.cursor/rules/` |
| ADRs | `docs/architecture/decisions/` |
| Releases | `docs/contributing/release-process.md` |
