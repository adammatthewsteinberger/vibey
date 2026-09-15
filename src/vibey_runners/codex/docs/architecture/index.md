# Architecture

Strict onion:

- `domain/` — pure stdlib value objects and total functions
- `application/` — ports + runner orchestration
- `infrastructure/` — `codex` subprocess, app-server, OpenAI REST surface
- `cli/` — Typer
- `bootstrap.py` — only module that sees every layer

Contracts are enforced by `import-linter`. See ADRs in this section for
accepted decisions.
