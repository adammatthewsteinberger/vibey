# Contributing to vibey

Thank you for considering a contribution. This document is meant to be
command-level and specific — if something here is unclear or you hit a
situation it doesn't cover, that's a bug in this document; please open an
issue or a PR fixing it.

## Table of contents

1. [Environment setup](#environment-setup)
2. [The branch model](#the-branch-model-gitflow)
3. [Conventional Commits](#conventional-commits)
4. [Quality gates](#quality-gates)
5. [The onion architecture import rule](#the-onion-architecture-import-rule)
6. [Protected tests](#protected-tests)
7. [Agent surfaces](#agent-surfaces)
8. [PR checklist](#pr-checklist)
9. [Getting help](#getting-help)
10. [Code of Conduct](#code-of-conduct)
11. [License of contributions](#license-of-contributions)

## Environment setup

```bash
git clone https://github.com/adammatthewsteinberger/vibey.git
cd vibey
uv sync --extra dev
pre-commit install
```

Requires **Python 3.12+**, **PostgreSQL** (the test suite uses a
`vibey_test` database), and **macOS or Linux**. Windows is not a supported
target. The default suite needs no engine binaries and no paid accounts;
live tests under `tests/live/` are opt-in and gated on environment
variables.

## The branch model (gitflow)

```
main         ← always releasable; release-please opens release PRs against this
  ▲ (merge commit — preserves individual conventional commits)
develop      ← integration branch; feature branches target this
  ▲ (squash-merge — one conventional-commit-titled squash per feature)
feature/*    ← your work
```

1. `git checkout -b feature/short-description develop`
2. Commit using [Conventional Commits](#conventional-commits).
3. Open a PR **into `develop`**, not `main`.
4. Your feature branch is **squash-merged** into `develop`.
5. Periodically, `develop` is merged into `main` as a **merge commit**.

Never implement on `main`.

## Conventional Commits

Every commit message must follow
[Conventional Commits](https://www.conventionalcommits.org/), enforced by a
`commit-msg` hook: `feat`, `fix`, `docs`, `style`, `refactor`, `perf`,
`test`, `build`, `chore`, `ci`, `revert` — with `feat`/`fix`/breaking
changes driving release-please's version bumps.

## Quality gates

The pre-commit hook runs the full suite; CI enforces the same seven gates
plus four per-layer coverage floors:

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy --strict src/vibey
uv run lint-imports
uv run bandit -q -r src/vibey
uv run pip-audit

# Per-layer 100% branch coverage — each one fails the build under 100%:
uv run pytest -q -p no:cacheprovider --cov=vibey.domain --cov-branch --cov-fail-under=100
uv run pytest -q -p no:cacheprovider --cov=vibey.application --cov-branch --cov-fail-under=100
uv run pytest -q -p no:cacheprovider --cov=vibey.infrastructure --cov-branch --cov-fail-under=100
uv run pytest -q -p no:cacheprovider --cov=vibey.cli --cov-branch --cov-fail-under=100
```

There is no "coverage debt" mechanism: a PR that drops any layer below 100%
branch coverage does not merge. Every `None`-default keyword argument needs
both-sides tests.

## The onion architecture import rule

```
domain → application → infrastructure → cli, tui
                                  ▲
                          bootstrap.py (the sole composition root)
```

Dependencies point inward only, enforced by `import-linter` in CI — not by
convention. `domain/` is stdlib-pure: no I/O, no async, no third-party
imports, verified by an AST-walking purity test. New I/O goes in
`infrastructure/` behind a `Protocol` declared in
`application/interfaces/`; wiring happens only in `bootstrap.py`.

## Protected tests

A small set of test files encode contracts that must not drift
(`tests/system/test_delivery_stage_set.py`, `tests/domain/test_noloss*.py`,
`tests/domain/test_briefing.py`, `tests/infrastructure/db/test_chaos.py`,
and everything under `tests/live/`). Do not modify them without explicit
maintainer sign-off in the PR description; changes to them are reviewed as
contract changes, not test edits.

## Agent surfaces

When a skill or procedure changes, update all four agent-surface trees in
the same PR: `.claude/skills/`, `.cursor/rules/`, `.agents/skills/`, and
`.agent/rules/`. CLAUDE.md holds facts, not procedures — every "how do I"
belongs in a skill.

## PR checklist

- [ ] Branched from `develop`; targets `develop` (not `main`)
- [ ] Commits (or the squash-merge title) follow Conventional Commits
- [ ] `pre-commit run --all-files` passes
- [ ] All four 100% branch-coverage gates pass
- [ ] Protected tests untouched (or sign-off obtained and noted)
- [ ] Agent-surface trees updated if a procedure changed
- [ ] Docs updated if behavior changed
- [ ] I agree to the [Code of Conduct](CODE_OF_CONDUCT.md) and to license
      this contribution under the MIT License

## Getting help

See [SUPPORT.md](SUPPORT.md) for the right channel. Usage questions belong
in [Discussions](https://github.com/adammatthewsteinberger/vibey/discussions),
not bug reports.

## Code of Conduct

This project follows the
[Contributor Covenant 2.1](CODE_OF_CONDUCT.md). By participating you agree
to uphold it.

## License of contributions

By contributing, you agree that your contributions are licensed under the
[MIT License](LICENSE).
