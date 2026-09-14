# claudeloop-quality-gates (Antigravity mirror of `.claude/skills/claudeloop-quality-gates/SKILL.md`)


# claudeloop quality gates

## Full set (CI order)

```bash
ruff check src tests
ruff format --check src tests
mypy src/claudeloop
pytest
lint-imports
bandit -q -r src/claudeloop
pip-audit
```

Or via pre-commit:

```bash
pre-commit run --all-files
```

## Fixing each gate

| Gate | Fix |
|---|---|
| `ruff check` | `ruff check --fix src tests` |
| `ruff format --check` | `ruff format src tests` |
| `mypy` | Add/correct annotations. `strict = true` repo-wide |
| `pytest` | See `claudeloop-testing` — add test or justified `# pragma: no cover` |
| `lint-imports` | See `claudeloop-architecture` — move code to correct layer |
| `bandit` | Fix issue or `# nosec B1xx` with inline justification (see existing examples in `domain/loop.py`) |
| `pip-audit` | Bump dependency. No fix? Surface explicitly in PR/issue — this project handles credentials |

## Bandit nosec bar

Only for verified false positive. Comment must explain the specific reason
the pattern is safe here. See existing examples in `src/claudeloop/domain/loop.py`.
