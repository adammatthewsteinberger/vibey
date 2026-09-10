# codexloop-releasing (Antigravity mirror of `.claude/skills/codexloop-releasing/SKILL.md`)


# codexloop releasing

## Gitflow

```
develop (default branch) → main (releases)
```

1. Feature PRs squash into `develop`.
2. `develop` merge-commits into `main` when ready to release.
3. release-please opens a PR on `main` when it detects conventional
   commits since the last tag.
4. Merging the release PR publishes to PyPI.

## Workflows

- **`ci.yml`**: runs on every push. Tests, linting, type checks, per-layer
  coverage, import-linter, bandit, pip-audit.
- **`publish-testpypi.yml`**: publishes to TestPyPI on every `develop`
  push. **Known gap: no test gate.** This workflow builds and publishes
  without running tests first. It trusts that CI passed.
- **`release-please.yml`**: opens a release PR on `main` when conventional
  commits land. Merging that PR publishes to PyPI (via GitHub Actions +
  PyPI trusted publishing).

## release-please

Configured in `release-please-config.json`:

```json
{
  "packages": {
    ".": {
      "release-type": "python",
      "package-name": "codexloop",
      "changelog-path": "CHANGELOG.md"
    }
  }
}
```

It maintains `CHANGELOG.md` automatically from conventional commits.

## Before merging develop → main

1. All CI gates green on `develop`.
2. TestPyPI publish succeeded (workflow run shows no errors).
3. CHANGELOG.md reflects all user-facing changes since last release.
