# Contributing

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,docs]"
pre-commit install
```

## Tests

```bash
pytest                         # default: not live and not system
pytest -m system               # scripted system harness
pytest -m live                 # real Codex account (opt-in)
```

Coverage floors: whole package 100% (`pytest --cov=codexloop --cov-fail-under=100`).

## Commits

Conventional Commits (`feat:`, `fix:`, `test:`, `chore:`, `docs:`).

## Publishing

See [Publishing](publishing.md) for TestPyPI → PyPI Trusted Publishing and the
release-please flow.
