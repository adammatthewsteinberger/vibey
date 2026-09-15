# Development setup

## Clone and install

```bash
git clone https://github.com/adammatthewsteinberger/agyloop.git
cd agyloop
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,docs]"
pre-commit install
```

Requires Python 3.12+. `pre-commit install` wires both lint/format hooks and
Conventional Commits enforcement (`default_install_hook_types`).

Editable with uv:

```bash
uv sync --extra dev --extra docs
uv run agyloop --help
```

## The branch model (gitflow)

```
main         ← always releasable; release-please opens PRs against this
  ▲ merge commit
develop      ← integration branch; default GitHub branch
  ▲ squash-merge
feature/*    ← your work — branch from develop, never from main
```

1. `git checkout -b feature/short-description develop`
2. Conventional Commits — the `commit-msg` hook rejects anything else.
3. PR into `develop`. CI (`ci.yml`) runs Python 3.12–3.13.
4. Squash-merge into `develop` with a conventional title.
5. `develop` → `main` is a **merge commit**, not a squash.
6. After the first public `v0.1.0`, release-please maintains a standing
   release PR on `main`. See [release-process.md](release-process.md).

## Conventional Commits

| Type | Use for | Triggers |
|---|---|---|
| `feat` | A new feature | minor bump |
| `fix` | A bug fix | patch bump |
| `feat!` / `fix!` / `BREAKING CHANGE:` | Breaking | major bump |
| `docs` `style` `refactor` `test` `build` `ci` `chore` | no bump | none |
| `perf` | performance | patch bump |
| `revert` | reverts a prior commit | depends |

## Quality gates

```bash
ruff check src tests
ruff format --check src tests
mypy --strict src/agyloop
pytest
pytest -m system
lint-imports
bandit -q -r src/agyloop
pip-audit
mkdocs build --strict
```

`pre-commit run --all-files` runs the hook subset.

## Where new code belongs

See [ADR 0001](../architecture/decisions/0001-onion-architecture.md) and the
`agyloop-architecture` skill. Short test:

1. Touches FS, network, clock, or `google.antigravity`? → `infrastructure/`
2. Pure decision, zero I/O? → `domain/`
3. Orchestration of ports? → `application/`
4. Argument parsing / human output? → `cli/`
5. Wiring adapters into ports? → `bootstrap.py` only

## Harness input-detection

See [harness-patch.md](harness-patch.md) if you are changing the Antigravity
`localharness` retarget.
