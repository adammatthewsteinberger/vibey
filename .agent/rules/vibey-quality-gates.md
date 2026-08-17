# vibey-quality-gates (Antigravity mirror of `.claude/skills/vibey-quality-gates/SKILL.md`)

description: The 7-gate CI sweep (ruff check, ruff format, mypy, per-layer coverage × 4, lint-imports, bandit, pip-audit) and what each gate catches.
alwaysApply: false

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

Four separate gates, one per layer. Each must hit **100% branch coverage** or
the build fails.

```bash
uv run pytest -q -p no:cacheprovider --cov=vibey.domain --cov-branch --cov-report=term-missing --cov-fail-under=100
uv run pytest -q -p no:cacheprovider --cov=vibey.application --cov-branch --cov-report=term-missing --cov-fail-under=100
uv run pytest -q -p no:cacheprovider --cov=vibey.infrastructure --cov-branch --cov-report=term-missing --cov-fail-under=100
uv run pytest -q -p no:cacheprovider --cov=vibey.cli --cov-branch --cov-report=term-missing --cov-fail-under=100
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

## Pre-commit hook

All seven gates (plus the Conventional Commits check) run automatically via
pre-commit. Install once:

```bash
pre-commit install
```

The commit-msg hook rejects non-Conventional Commits. The pre-commit hook
runs ruff, mypy, lint-imports, and the full test suite before allowing a
commit.

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
