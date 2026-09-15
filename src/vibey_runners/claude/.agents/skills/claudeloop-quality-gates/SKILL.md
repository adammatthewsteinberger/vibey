---
name: claudeloop-quality-gates
description: Covers how to run and FIX every quality gate in this repo — ruff (lint + format), mypy --strict, pytest with per-layer coverage, import-linter (lint-imports), bandit, and pip-audit. Use this whenever a quality gate fails locally or in CI, whenever the user asks how to lint, format, type-check, or run security scans on this codebase, or before opening a PR to run the full gate set proactively. Make sure to consult this whenever a ruff, mypy, lint-imports, or bandit error appears in tool output — it gives the exact fix command for each gate rather than requiring you to guess at generic remediation.
---

# claudeloop quality gates — run and fix


> **Codex skill mirror** of `.claude/skills/claudeloop-quality-gates/SKILL.md`. When this guidance changes, update Claude skill, Cursor rule, and `.agents/skills/` in the same PR.

## The full set, in the order CI runs them

```bash
ruff check src tests
ruff format --check src tests
mypy src/claudeloop
pytest
lint-imports
bandit -q -r src/claudeloop
pip-audit
```

Or the pre-commit-wired subset against your working tree:

```bash
pre-commit run --all-files
```

## Fixing each gate

| Gate | Symptom | Fix |
|---|---|---|
| `ruff check` | Lint error | `ruff check --fix src tests` for auto-fixable rules; hand-edit the rest. Rule set: `E, F, I, UP, B, SIM, C4` (see `[tool.ruff.lint]` in `pyproject.toml`). |
| `ruff format --check` | Formatting diff | `ruff format src tests` |
| `mypy` | Type error | Add/correct annotations. `strict = true` repo-wide — no bare `Any` without a documented reason. `domain/` and `application/` in particular must type-check cleanly with zero suppressions. |
| `pytest` | Test failure or coverage below the per-layer floor | See the `claudeloop-testing` skill — check whether a branch is genuinely untested (add a test) vs. genuinely unreachable (a justified `# pragma: no cover`) |
| `lint-imports` | Onion-layering violation | See the `claudeloop-architecture` skill — the fix is almost always moving the offending code to the correct layer, not suppressing the contract |
| `bandit` | Flagged security pattern | Either fix the underlying issue, or — for a genuine false positive like an exhaustiveness `assert` on a closed union — add `# nosec B1xx` with an inline comment stating *why* it's safe. Two real examples exist in `src/claudeloop/domain/loop.py`; match that level of justification, don't just silence the warning. |
| `pip-audit` | Known CVE in a dependency | Bump the dependency. If no fix is available yet, this needs to be surfaced explicitly (in the PR description or an issue), not silently ignored — this project handles API credentials and bypasses permission prompts by design, so dependency CVEs are higher-stakes than usual. See `SECURITY.md`. |

## Bandit `# nosec` — the bar for using it

Only for a verified false positive, never to silence a real finding faster.
The comment must explain the specific reason the pattern is safe *here*,
matching this repo's existing style:

```python
# Precondition, not a security gate: CompletionVerdict is the closed union
# {Done, Blocked, Continue} and both other members are handled above, so this
# is exhaustive by construction — asserted here to fail loudly if a future
# variant is added to the union without a matching branch here.
assert isinstance(verdict, Continue)  # nosec B101
```

## Before opening a PR

Run the full gate set (not just the pre-commit subset — `pytest` with
coverage and `pip-audit` aren't pre-commit hooks) once locally. A PR that
fails CI on a gate that would have caught locally wastes a review round.

## Full reference

`docs/contributing/development.md#running-the-quality-gates-locally`,
`CONTRIBUTING.md#quality-gates`.
