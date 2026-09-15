# claudeloop-releasing (Antigravity mirror of `.claude/skills/claudeloop-releasing/SKILL.md`)


# claudeloop releasing

## Branch model

```
main         ← always releasable; release-please opens release PRs here
  ▲ merge commit (preserves commits for release-please)
develop      ← integration; feature branches target this
  ▲ squash-merge (one conventional-commit-titled squash per feature)
feature/*    ← branch from develop, never from main
```

Never branch from `main`. Never target `main` with a feature PR.

## Conventional Commits (required, enforced by hook)

`<type>[optional scope]: <description>`. Hook installed via `pre-commit
install`. Types:

| Type | Use | Bump |
|---|---|---|
| `feat` | new feature | minor |
| `fix` | bug fix | patch |
| `feat!` / `fix!` / `BREAKING CHANGE:` | breaking change | major |
| `docs` `style` `refactor` `test` `build` `ci` `chore` | no functional change | none |
| `perf` | performance improvement | patch |

Scope in parentheses optional but strongly preferred.

## release-please

Fully automated. Opens release PR on `main` from conventional commits.
Merge → tag + GitHub release + PyPI publish via Trusted Publishing (OIDC).

See `docs/contributing/release-process.md`.
