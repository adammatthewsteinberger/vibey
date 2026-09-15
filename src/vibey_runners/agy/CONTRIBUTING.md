# Contributing to agyloop

Thank you for considering a contribution. This document is meant to be
command-level and specific — if something here is unclear or you hit a
situation it doesn't cover, that's a bug in this document; please open an
issue or a PR fixing it.

## Table of contents

1. [Environment setup](#environment-setup)
2. [The branch model](#the-branch-model-gitflow)
3. [Conventional Commits](#conventional-commits)
4. [Git hooks](#git-hooks)
5. [Quality gates](#quality-gates)
6. [Testing philosophy](#testing-philosophy)
7. [The onion architecture import rule](#the-onion-architecture-import-rule)
8. [PR checklist](#pr-checklist)
9. [Getting help](#getting-help)
10. [Code of Conduct](#code-of-conduct)
11. [License of contributions](#license-of-contributions)

## Environment setup

```bash
git clone https://github.com/the-vibey-project/vibey.git
cd vibey/src/vibey_runners/agy   # agyloop lives here in the vibey monorepo
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,docs]"
pre-commit install
```

Requires **Python 3.12+** on **macOS or Linux**. Windows is not a supported
target. Live runs need `GOOGLE_API_KEY` or Application Default Credentials;
the default test suite and `pytest -m system` need no Google account. See
[`docs/contributing/development.md`](docs/contributing/development.md).

## The branch model (gitflow)

```
main         ← the vibey monorepo's release branch
  ▲ rebase merge — promotion PRs opened by `vibey-gh promote`
develop      ← the monorepo's integration branch; feature branches target this
  ▲ squash merge — one conventional-commit-titled squash per feature
feature/*    ← your work
```

This package is developed inside the [vibey monorepo](https://github.com/the-vibey-project/vibey)
(`src/vibey_runners/agy`), and its branch model, merge train and release automation are the
monorepo's: see vibey's [CONTRIBUTING](https://github.com/the-vibey-project/vibey/blob/develop/CONTRIBUTING.md)
and [ADR-0028](https://github.com/the-vibey-project/vibey/blob/develop/docs/architecture/decisions/0028-vibey-gh-owns-release-and-provenance.md).
release-please was retired; `vibey-gh` derives versions and publishes.

1. `git checkout -b feature/short-description develop` in the vibey repository.
2. Commit using [Conventional Commits](#conventional-commits).
3. Open a PR **into `develop`**, not `main`. This package's own quality gates
   still apply and run in vibey's CI.
4. The merge train squash-merges the PR once its checks and review pass.
5. `vibey-gh promote` opens the promotion PR into `main`; it is rebase-merged
   and the release workflow publishes.

Never implement on `main`.

## Conventional Commits

Every commit message must follow
[Conventional Commits](https://www.conventionalcommits.org/):

```
<type>[optional scope]: <description>
```

Allowed types (enforced by the `commit-msg` hook in `--strict` mode):

| Type | Use for | Version bump |
|---|---|---|
| `feat` | A new feature | minor |
| `fix` | A bug fix | patch |
| `feat!` / `fix!` / a `BREAKING CHANGE:` footer | A breaking change | major |
| `docs` | Documentation only | none |
| `style` | Formatting, no logic change | none |
| `refactor` | Neither a fix nor a feature | none |
| `perf` | A performance improvement | patch |
| `test` | Adding or correcting tests | none |
| `build` | Build system or dependencies | none |
| `ci` | CI configuration | none |
| `chore` | Anything else | none |
| `revert` | Reverting a previous commit | depends |

```
feat(domain): add CreditsExhausted as a distinct capacity state
fix(agent): retarget withdrawn flash-lite input detection
docs(architecture): add ADR for five-member CapacityState
```

## Git hooks

```bash
pre-commit install
```

This wires **both** `pre-commit` and `commit-msg` because
`.pre-commit-config.yaml` declares `default_install_hook_types: [pre-commit,
commit-msg]`.

**Troubleshooting:**

- Conventional Commits rejection — fix the first line to
  `<type>[scope]: <description>` and commit again.
- A hook rewrote files — `git add` the fixes and commit again.
- Emergency bypass: `git commit --no-verify`. CI still enforces the gates.

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

Or:

```bash
pre-commit run --all-files
```

## Testing philosophy

- **Fakes over mocks.** Ports get real classes implementing the same
  `Protocol`, checked by `mypy --strict`.
- **No real sleeping in a test.** `FakeClock` / `FakeSleeper`.
- **Hypothesis** for numeric or time-based invariants.
- `# pragma: no cover` must carry a reason.

## The onion architecture import rule

`domain/` imports nothing but the standard library. `application/` imports
`domain/` and defines ports as `Protocol`. `infrastructure/` is the *only*
place `google.antigravity` may appear in an `import` statement. `cli/` talks
to `application/` via `bootstrap.py`, never to `infrastructure/` directly.

Enforced by `import-linter`. See
[ADR 0001](docs/architecture/decisions/0001-onion-architecture.md).

## PR checklist

- [ ] Branch created from `develop`, named `feature/<short-description>`
- [ ] Commits (or the squash-merge title) follow Conventional Commits
- [ ] `pre-commit run --all-files` passes
- [ ] `pytest` and `pytest -m system` pass
- [ ] No new cross-layer imports that `lint-imports` would reject
- [ ] Docs updated if behavior changed
- [ ] Agent surfaces kept in sync (Claude / Cursor / Codex / Antigravity)
- [ ] A new ADR if this PR makes a hard, non-obvious design call
- [ ] You agree to the [Code of Conduct](CODE_OF_CONDUCT.md) and to license
      this contribution under the MIT License

## Getting help

| I want to... | Go here |
|---|---|
| User/operator docs | [`docs/index.md`](https://github.com/the-vibey-project/vibey/blob/develop/src/vibey_runners/agy/docs/index.md) |
| Ask a question or discuss design | [GitHub Discussions](https://github.com/the-vibey-project/vibey/discussions) |
| Report a bug | [Bug report form](https://github.com/the-vibey-project/vibey/issues/new?template=bug_report.yml) |
| Propose a feature | [Feature request form](https://github.com/the-vibey-project/vibey/issues/new?template=feature_request.yml) |
| Report a vulnerability | [SECURITY.md](SECURITY.md) — privately |
| Same map, shorter | [SUPPORT.md](SUPPORT.md) |

Blank issues are disabled on purpose. If none of the forms fit, open a
Discussion instead of a free-form issue.

## Code of Conduct

Participation in this project is governed by the
[Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). Report
unacceptable behavior to adam@matthewsteinberger.com.

## License of contributions

This repository is MIT-licensed ([LICENSE](LICENSE)). By opening a pull
request you agree that your contribution is provided under the same MIT
License (inbound = outbound). There is no CLA.
