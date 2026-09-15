# GEMINI.md

`claudeloop`: an onion-architected, autonomous Claude Code session runner
and full Anthropic SDK CLI. Facts only — procedures live in `.agent/rules/`
(mirrors of `.claude/skills/` and `.cursor/rules/`).

## Non-negotiables

- Never block on a human. Every code path has a way forward.
- Credits ≠ rate-limit window. `CreditsExhausted` has no `resets_at`.
- `domain/` is stdlib only. Vendor types stay in `infrastructure/`.
- Capacity rejection outranks a completion claim.
- Conventional Commits. Never implement on `main`.
- SDK path (`--gateway sdk`) is `ClaudeSDKClient`, not `query()`.
- Structured output (`output_format`) is primary, `CLAUDELOOP_TASK_FULLY_COMPLETE` substring is fallback.
- `CLAUDE_CODE_RETRY_WATCHDOG` off by default — opt-in `--retry-watchdog` only.

## Layer map

```
domain → application → infrastructure → cli, bootstrap.py is the composition root
```

## Auth

API key via `ANTHROPIC_API_KEY`. Run `claudeloop doctor` to verify setup.
Supports Anthropic API, AWS Bedrock, Google Cloud Vertex AI, Foundry.

## Commands

```bash
pytest
pytest -m system
mypy --strict src/claudeloop
lint-imports
mkdocs build --strict
```

## Surfaces

| Need | Go to |
|---|---|
| Procedures | `.agent/rules/`, `.claude/skills/`, `.cursor/rules/` |
| ADRs | `docs/architecture/decisions/` |
| Releases | `docs/contributing/release-process.md` |
| Security | `SECURITY.md` |
