# Contributing

Qwenloop uses `develop` as its integration branch and `main` as its release
branch. Open feature and fix pull requests against `develop`.

Before submitting a change:

```bash
uv sync --extra dev
uv run ruff check .
uv run ruff format --check .
uv run mypy --strict src/qwenloop
uv run lint-imports
uv run pytest -q
uv run bandit -q -r src/qwenloop
```

Keep domain code stdlib-only and free of I/O and async behavior. Never commit
model weights, local caches, credentials, run artifacts, or evaluation results
containing private repository data.

All commits use Conventional Commits. `vibey-gh` installs the provenance hooks:

```bash
uvx vibey-gh install
uvx vibey-gh check
```
