# vibey-quality-gates (Antigravity mirror of `.claude/skills/vibey-quality-gates/SKILL.md`)

# vibey quality gates

CI runs a 7-gate sweep over the root `vibey` package, as the `gates` job in
`.github/workflows/ci.yml`. **All seven must pass** — together with the other CI
jobs below — before a PR can merge. Run them locally with
`pre-commit run --all-files --hook-stage pre-push` (a plain
`pre-commit run --all-files` runs only the ruff hooks) or individually:

## Gate 1: ruff check

Linter. Catches unused imports, undefined names, syntax errors, and common
anti-patterns.

```bash
uv run ruff check .
```

Root ruff covers `src/**/*.py` and `tests/**/*.py`, so it also lints the
workspace tenants under `src/vibey_runners/` and `src/vibey_tools/`.

## Gate 2: ruff format --check

Formatter. Ensures consistent code style across the repo. Fails if any file
would be reformatted.

```bash
uv run ruff format --check .
```

To fix: `uv run ruff format .`

## Gate 3: mypy --strict

Type checker. Enforces `--strict` mode across `src/vibey/`. Catches type
errors, missing type annotations, and `Any` usage.

```bash
uv run mypy --strict src/vibey
```

## Gate 4: pytest per-layer coverage (100%)

One test run produces a combined `.coverage` file; four per-layer reports
enforce 100% branch coverage. Each must pass or the build fails.

```bash
uv run pytest -q -p no:cacheprovider --cov=vibey --cov-branch --cov-report=
uv run coverage report --include='src/vibey/domain/*' --fail-under=100
uv run coverage report --include='src/vibey/application/*' --fail-under=100
uv run coverage report --include='src/vibey/infrastructure/*' --fail-under=100
uv run coverage report --include='src/vibey/cli/*' --fail-under=100
```

**Why per-layer, not aggregate?** Because `domain/` is the safety-critical
layer and must never drop below 100%. An aggregate gate would allow a 95%
domain to hide behind a 100% infrastructure. See ADR-0023.

The test run needs a reachable Postgres even for a subset: `tests/conftest.py`
clones a migrated template database per xdist worker at session start. See the
`vibey-testing` skill.

## Gate 5: lint-imports

Onion architecture enforcer. Verifies dependencies point inward only, and
that `domain/` imports nothing but stdlib.

```bash
uv run lint-imports
```

If it fails, the error names the contract and the violating import. See
`.importlinter` for the four contracts: `onion-layers`,
`domain-independence`, `application-independence`, and `interfaces-declare-only`
— the last of which today covers `application/interfaces` only, although the
declare-only rule applies to every `interfaces/` package. See ADR-0016.

See the `vibey-architecture` skill before fixing a violation.

## Gate 6: bandit

Security linter. Scans for common security issues: hardcoded passwords, SQL
injection, insecure temp files, weak crypto, shell=True, etc.

```bash
uv run bandit -q -r src/vibey
```

## Gate 7: pip-audit

Dependency vulnerability scanner. Checks for known CVEs in pinned
dependencies.

```bash
uv run pip-audit
```

## Hook diet

The seven gates are split across git hook stages so commits stay fast
(`.pre-commit-config.yaml`):

**Pre-commit stage** (runs on every `git commit`):
- ruff (`--fix`) + ruff format, on changed files

**Pre-push stage** (runs on every `git push`):
- The plain parallel test suite (`uv run pytest -q -p no:cacheprovider`) — kept
  so a test failure reports as itself rather than as a coverage-gate failure
- mypy --strict
- lint-imports
- Per-layer 100% coverage gates (pytest --cov + four reports)
- bandit
- pip-audit

**Commit-msg stage**: Conventional Commits enforcement.

Install all three hook types once:

```bash
pre-commit install && pre-commit install --hook-type pre-push && pre-commit install --hook-type commit-msg
```

## The other CI jobs

`ci.yml` runs six jobs on every push and PR to `develop`/`main`:

| Job | What it checks |
|---|---|
| `uv-lock` | `uv lock --check`. `gates`, `tools` and `tools-lint` depend on it. The lock carries vibey's own version, so a version bump without `uv lock` fails here first. |
| `gates` | The seven gates above, against a `postgres:17` service. |
| `tools` | Each absorbed tool's own suite on its own Python floors (ADR-0022). |
| `tools-lint` | vibey-gh's own linters and its managed-automation drift check. |
| `image` | Builds `deploy/docker/Dockerfile` for amd64 and arm64 and asserts four image contracts: the entrypoint runs, it runs as non-root uid 10001, it has no compiler/uv/pip, and migrations ship in the image. |
| `cluster-smoke` | Helm install of `deploy/helm/vibey` on minikube and four cluster contracts: a projectless worker parks instead of crash-looping, the worker picks up a project created in-cluster, the KEDA ScaledObject reconciles against real Postgres, and a worker drains promptly on SIGTERM (ADR-0025, ADR-0026). |

Other workflows also gate a merge: `provenance.yml` (runs on every push and PR),
and `pr-automation.yml`, which re-evaluates a PR each time `CI` or `Provenance`
completes (`[pr_automation] scan_workflows` in `.vibey-gh.toml`) and hands ready
PRs to `merge-train.yml` (see the `vibey-releasing` skill).

## Workspace tenants: their own checks

The tenants under `src/vibey_runners/` and `src/vibey_tools/` keep the gates they
arrived with (ADR-0021, ADR-0022). The root `mypy`, `bandit` and coverage gates
cover `src/vibey` only. Run a tenant's checks from its own directory, with plain
pip and a Python at its floor — the workspace lock resolves at 3.12, so a uv
environment cannot exercise the 3.10 and 3.11 floors. These are the `tools` and
`tools-lint` commands, verbatim:

```bash
# vibey-gh (CI: Python 3.11, 3.12, 3.13; 100% branch floor in its own addopts)
cd src/vibey_tools/gh
pip install -e ".[dev]"
python -m pytest -q
python -m black --check vibey_gh test
isort --check-only vibey_gh test
python -m mypy vibey_gh

# vibey-skills (CI: Python 3.10, 3.12)
cd src/vibey_tools/skills
pip install -e .
python3 tools/validate_manifests.py && python3 tools/check_links.py \
  && PYTHONPATH=src python3 -m unittest discover -s tests

# vibey-bootstrap (CI: Python 3.11, 3.12)
cd src/vibey_tools/bootstrap
pip install -e ".[test,all]"
pytest test/ -m "not integration" --cov=vibey_bootstrap --cov-report=term
```

vibey-gh's suite shells out to `uv` and drives real git history, so it needs
`uv` on `PATH` and a full clone.

The runners (`src/vibey_runners/{claude,codex,cursor,agy,qwen}`) carry their own
`tests/`, ruff, mypy and import-linter configuration in their `pyproject.toml`,
but **no CI job runs them as of 2026-09-15**. When you change a runner, run its
suite yourself from its directory (`pip install -e ".[dev]" && python -m pytest`)
and read its `[tool.pytest.ini_options]` first: agyloop's and cursorloop's addopts
exclude `live` and `system` tests, and qwenloop's enforce a 100% branch floor.

## What each gate catches

| Gate | Catches |
|---|---|
| ruff check | Unused imports, undefined names, syntax errors, anti-patterns |
| ruff format | Inconsistent code style |
| mypy --strict | Type errors, missing annotations, `Any` usage |
| pytest (per-layer 100%) | Untested branches, logic errors, regressions |
| lint-imports | Onion violations, forbidden imports |
| bandit | Security issues, hardcoded secrets, insecure patterns |
| pip-audit | Dependency CVEs |
