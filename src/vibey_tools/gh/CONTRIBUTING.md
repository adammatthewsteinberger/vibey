# Contributing

## Development

Use Python 3.11 or newer. Create a topic branch from `develop`; never work directly on
`main`. Install the development environment with `python -m pip install -e ".[dev]"` and
enable the managed hooks with `vibey-gh install`.

## Required checks

Run:

```bash
pytest
black --check vibey_gh test
isort --check-only vibey_gh test
ruff check vibey_gh test
mypy vibey_gh
vibey-gh check --ci
```

Tests belong under `test/`. Maintain 100% line and branch coverage and add focused tests for new
decisions, and do not weaken checks. Update README, reference docs, changelog, security
guidance, agent instructions, and configuration examples when behavior changes.

## Pull requests and provenance

Keep changes focused. Explain behavior, risk, tests, migration, and documentation impact.
Every source file carries the configured header and every commit carries the configured
`Made-With` trailer. Commit subjects must follow Conventional Commits, for example
`feat(cli): add status output` or `fix: preserve exact head`. The local hook normalizes a
nonconforming subject; for same-repository linear topic branches, the guarded workflow may
rewrite subjects and force-update the exact branch with a lease. After that update, fetch
and rebase local unpushed work onto `origin/<topic-branch>`. Automated scans, review,
repair, and merge operate on the exact head.

See `docs/development.md`, `docs/testing.md`, and `docs/releases.md`.
