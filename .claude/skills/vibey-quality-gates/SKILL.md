---
name: vibey-quality-gates
description: The 7-gate CI sweep (ruff check, ruff format, mypy, per-layer coverage × 4, lint-imports, bandit, pip-audit) and what each gate catches.
allowed-tools: Bash
---

# vibey quality gates

CI runs a 7-gate sweep. **All seven must pass** before a PR can merge. Run
locally with `pre-commit run --all-files` or individually:

## Gate 1: ruff check

Linter. Catches unused imports, undefined names, syntax errors, and common
anti-patterns.

```bash
uv run ruff check .
```

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
domain to hide behind a 100% infrastructure.

## Gate 5: lint-imports

Onion architecture enforcer. Verifies dependencies point inward only, and
that `domain/` imports nothing but stdlib.

```bash
uv run lint-imports
```

If it fails, the error names the contract and the violating import. See
`.importlinter` for the three contracts: `onion-layers`,
`domain-independence`, `application-independence`.

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

The seven gates are split across two git hook stages for fast commits:

**Pre-commit stage** (runs on every `git commit`):
- ruff check + ruff format (changed files only)
- Full parallel test suite (`uv run pytest`)

**Pre-push stage** (runs on every `git push`):
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
