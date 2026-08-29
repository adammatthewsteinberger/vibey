# vibey-releasing (Antigravity mirror of `.claude/skills/vibey-releasing/SKILL.md`)

description: The release.yml OIDC publish workflow, Conventional Commits, and manual CHANGELOG/version bumps. Read before cutting a release.
alwaysApply: false

# vibey releasing

Vibey publishes directly from `.github/workflows/release.yml` on every push
to `develop` or `main` — there is no release-please step and no release PR.
Versioning and the changelog are both maintained by hand.

## Conventional Commits (enforced)

Every commit message must follow Conventional Commits format. A pre-commit
hook rejects anything else:

```
feat: add support for GitHub Actions deployment
fix: prevent race condition in lease renewal
docs: update handoff protocol spec
chore: bump dependencies
test: add property test for rotation fairness
```

**Scopes are optional** but recommended for large changes:

```
feat(domain): add media provider round-robin cursor
fix(cli): correct --cwd handling in run command
```

**Breaking changes** carry a `!` or a `BREAKING CHANGE:` footer:

```
feat!: require Python 3.12+

BREAKING CHANGE: Python 3.11 is no longer supported.
```

**Why this matters:** commit messages are not parsed by any release
automation here — there is no release-please. Conventional Commits are
still enforced for a legible history, but bumping the version and writing
the changelog entry are manual steps you do as part of the release commit.

## Release workflow

1. **Merge to `develop`** — feature PRs squash into `develop`. Every push to
   `develop` builds and publishes a dev-versioned build to TestPyPI as
   `vibey-dev` (the `vibey` name is squatted there by an unrelated project),
   via OIDC trusted publishing — no token stored anywhere.
2. **Bump the version by hand** — before merging to `main`, edit
   `version = "x.y.z"` in `pyproject.toml` and add a matching entry at the
   top of `CHANGELOG.md`. Nothing does this automatically.
3. **`develop` → `main`** — when ready to release, merge `develop` into
   `main` via a merge commit (never squash).
4. **`release.yml` runs on push to `main`** — it builds the wheel/sdist and
   publishes straight to PyPI as `vibey` via OIDC trusted publishing. There
   is no release PR and no separate publish workflow to merge first.
5. **`main` realigns `develop`** — a `realign` job force-syncs `develop`'s
   tree to match `main` once the publish succeeds (skipped, with a notice,
   if `AUTOMERGE_TOKEN` isn't set — harmless, since promotion compares
   branches by content).

## Manual version bump

There is no escape hatch to reach for — this *is* the normal process:

1. Edit `pyproject.toml` and bump `version = "x.y.z"`
2. Add a `## [x.y.z]` entry to `CHANGELOG.md` describing what changed
3. Commit with `chore: release x.y.z`
4. Merge to `main` — `release.yml` publishes it on push, no tag needed

## Verifying the publish

After `main` builds:

1. Check the `release.yml` run in GitHub Actions.
2. Verify PyPI: https://pypi.org/project/vibey/
3. Install and test:

```bash
uv venv --python 3.12
source .venv/bin/activate
pip install vibey==x.y.z
vibey --version
```

For a `develop` push, verify TestPyPI instead (package name `vibey-dev`);
the workflow's own `verify-testpypi` job already does this automatically.

## Common issues

**Version didn't change on PyPI:** confirm `pyproject.toml`'s `version` was
actually bumped before the push — `release.yml` reads it directly and
`skip-existing: true` means an unbumped version silently no-ops.

**CHANGELOG.md doesn't mention the shipped version:** nothing updates it
automatically; it must be edited in the same commit as the version bump.

**Publish failed:** check the `release.yml` run in GitHub Actions. Common
causes: OIDC trusted-publisher not configured for the `pypi`/`testpypi`
environment, wheel build failed, version already published.

**`develop` didn't realign after a release:** check whether
`AUTOMERGE_TOKEN` is set — the `realign` job skips (not fails) without it.

## The workflow

- `.github/workflows/release.yml` — the only release workflow. `build` runs
  on every push to `develop`/`main`; `testpypi`/`verify-testpypi` run on
  `develop`; `pypi` and `realign` run on `main`.

Triggered automatically by pushing to `develop` or `main`. Do not run it
manually unless debugging.
