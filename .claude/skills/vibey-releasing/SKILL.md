---
name: vibey-releasing
description: The release flow — merge train into develop, vibey-gh promote to main, release.yml publishing (develop to TestPyPI as vibey-dev, main to PyPI), github-release.yml tags, and release-surfaces.yml docs, book and paper. Read before cutting a release.
allowed-tools: Read Bash
---

# vibey releasing

`vibey-gh` owns the release (ADR-0028). There is no release-please step and no
hand-run publish. The version is *derived*, not chosen: `vibey-gh version` reads
what changed against `[version] content_paths` and `code_paths` in
`.vibey-gh.toml` and answers minor, patch, or nothing. `vibey-gh promote` applies
that answer. The changelog entry is written by hand.

Every workflow on the release path installs the tree's own `vibey-gh` from the
declared `[install] self_source = "src/vibey_tools/gh"`, and falls back to
`vibey-gh==1.73.0` from PyPI only when that path does not hold a `vibey-gh`
package. A change to `vibey-gh` therefore changes the release path on the next push.

## Where a release goes

PyPI is not the finish line. These are command-line applications, and someone
installing a CLI reaches for `brew install` or `winget install` -- that it is
written in Python is an implementation detail they should not have to care about.

Publish to every registry that can carry it, and treat the channel as part of
shipping rather than a follow-up. Every packaging definition -- formula, PKGBUILD,
snapcraft.yaml, nuspec, winget manifest -- is to live in this repository and be
published by automation, never hand-edited in a tap (ADR-0018, ADR-0019,
sub-doctrine 2.b). A stale formula is worse than no formula: it installs an old
version silently.

**As of 2026-09-15 none of those packaging definitions exist yet.** The channels
this repository publishes today are:

- PyPI `vibey` (from `main`) and TestPyPI `vibey-dev` (from `develop`) — `release.yml`
- An OCI release bundle of the exact wheel and sdist at
  `ghcr.io/<owner>/<repo>/python` — `release-surfaces.yml`
- The documentation site, book and paper — `release-surfaces.yml` (below)
- A Git tag and GitHub Release per released version — `github-release.yml`

The container image (`deploy/docker/Dockerfile`) and Helm chart
(`deploy/helm/vibey`) are defined and tested in CI (`image`, `cluster-smoke`) but
not pushed to a registry by any workflow. ADR-0019 is the backlog for the rest.

Note what publishing does and does not mean per target. `dpkg`, `rpm` and
`apk-tools` are formats, not registries. `podman` wants an OCI image, which this
repository already builds. npm, Maven, Cargo and the rest cannot carry a Python
library at all -- only a wrapper that fetches the CLI, which is a different
promise and has to say so. See ADR-0019 for the grouping and the order.

The workspace tenants (`claudeloop`, `codexloop`, `cursorloop`, `agyloop`,
`qwenloop`, `vibey-gh`, `vibey-skills`, `vibey-bootstrap`) still exist on PyPI
under their own names, but their source now lives in this repository (ADR-0021)
and the workflows below publish only `vibey`.

## Conventional Commits (enforced)

Every commit message must follow Conventional Commits format. A commit-msg hook
rejects anything else:

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

**Why this matters:** commit messages are not parsed by the release
automation. The bump is derived from *which paths changed*, not from commit
types. Conventional Commits are still enforced for a legible history and
because the provenance gate reads every commit in a range — which is why the
automation's own release commit is `chore(release): x.y.z`.

A breaking change is never derived: the derivation answers only minor, patch or
nothing. A major bump is a deliberate edit (see "A deliberate bump").

## How the version is derived

`uv run vibey-gh version --since origin/main --explain` prints the answer and why.
It compares `origin/main` to `HEAD`, ignores files whose only change is the
provenance header, and then:

- any changed file under `[version] content_paths` → **minor**
- otherwise, any changed file under `[version] code_paths` → **patch**
- otherwise (docs, workflows, tooling only) → **nothing to release**

This repository sets both to `["src/vibey/"]`, so in practice any change under
`src/vibey/` is a minor bump and a change elsewhere (including the tenants under
`src/vibey_runners/` and `src/vibey_tools/`) releases nothing. If the version on
`HEAD` already differs from `origin/main`, the derivation leaves it alone.

`[version] files` lists what a bump writes: `pyproject.toml` and
`src/vibey/__init__.py`. `vibey-gh`'s `apply_version` also re-runs `uv lock` when
`uv.lock` is present, because the lock carries vibey's own version and CI's
`uv-lock` job runs `uv lock --check` before the other jobs.

## Release workflow

1. **PRs land on `develop` through the merge train.** `pr-automation.yml`
   re-evaluates a PR each time `CI` or `Provenance` completes;
   `merge-train.yml` runs each time a PR-automation run completes, deliberately
   whatever its conclusion (with a weekly Monday cron and manual dispatch as
   backstops); `vibey-gh merge-train` merges only PRs whose head carries a
   successful `PR automation / gate`. PRs into
   `develop` are squash-merged. Never implement on `main`.
2. **Every push to `develop` publishes a dev build.** `release.yml` stamps
   `x.y.z.devN` (`vibey-gh version --dev <run number> --apply`), renames the
   distribution to `vibey-dev` in the runner only (the `vibey` name on TestPyPI
   is squatted by an unrelated project), publishes to TestPyPI via OIDC trusted
   publishing, and `verify-testpypi` installs that exact version and runs
   `vibey --version`.
3. **Promotion is automatic.** `promote-to-main.yml` runs after the merge train
   completes (weekly Monday cron backstop; manual dispatch with `dry_run`). It runs
   `vibey-gh promote`, which:
   - compares `develop` and `main` **by tree content** and stops if they are identical;
   - derives the version on `develop` and, when a bump is due, commits
     `chore(release): x.y.z` (version files plus `uv.lock`) and pushes it to
     `develop`, raising if the push fails;
   - opens or reuses the `develop` → `main` promotion PR, titled
     `chore(release): <version>`.

   The PR-automation gate and merge train then merge the promotion PR once its
   checks pass, with **rebase** (`promote.DEFAULT_METHOD = "rebase"`; the merge
   train uses rebase for any PR based on `main`). Because `main` is rebase-merged,
   its commits are rewritten copies with new SHAs.
4. **Every push to `main` publishes to PyPI.** `release.yml` builds the wheel
   and sdist and publishes `vibey` to PyPI via OIDC trusted publishing
   (`skip-existing: true`).
5. **`main` realigns `develop`.** The `realign` job runs `vibey-gh realign`, which
   converges `develop` onto `main` only when the two trees are identical. It skips
   with a notice when `AUTOMERGE_TOKEN` is not set — harmless, since promotion
   compares branches by content.
6. **After a successful Release run on `main`**, `github-release.yml` runs
   `vibey-gh github-release --target <sha>`: it creates the immutable tag
   `v<version>` (the default `[github_release] tag_prefix`) and the GitHub
   Release, and never moves an existing tag. A manual dispatch must prove the
   target SHA is on `main` and has a successful Release run.
7. **After a successful Release run on `develop` or `main`**,
   `release-surfaces.yml` publishes the documentation surfaces and the OCI bundle
   (see "The workflows").

To preview what the next promotion will do, run
`uv run vibey-gh version --since origin/main --explain`, or dispatch
`promote-to-main.yml` with `dry_run`.

A ratified change to the doctrine canon is also a release event: Article V.4 of
the constitution (`src/vibey_tools/gh/docs/constitution.md`) requires every prior
release to be yanked. See the `vibey-architecture` skill.

## The changelog

Nothing in the release path writes `CHANGELOG.md`. Add entries under
`## [Unreleased]` in the PR that lands the user-visible change, grouped as the
file already does (`### Features`, `### Bug Fixes`, with issue and commit links).
When a version ships, the `[Unreleased]` entries move under `## [x.y.z] (date)`.
Entries 0.2.0 through 0.6.0 were reconstructed from the release commits on
2026-09-15; a released version without an entry is a documentation bug.

## Documentation surfaces

The documentation ships with every release channel, so treat it as release
content:

- **Site:** `properdocs.yml` at the repository root drives the ProperDocs build of
  `docs/`. `docs/plans/**` is excluded on purpose (working material, not
  reference). A page not listed under `nav` is still built but is not reachable
  from the navigation.
- **ADRs:** a new decision record is `docs/architecture/decisions/NNNN-slug.md`
  with the next contiguous number and a `**Status:** · **Date:**` line. It must be
  added to the `properdocs.yml` nav, and the "(N ADRs" count in `CLAUDE.md`,
  `AGENTS.md`, `GEMINI.md`, `README.md` and `docs/index.md` must match the files on
  disk. `tests/meta/test_adr_counts.py` enforces all three.
- **Paper:** `docs/paper.md` is the source for both the HTML page (`/paper/`) and
  `paper.pdf`.
- **Book:** generated from the built channel site by `vibey-gh book`; there is no
  separate book source. A page added to the site is in the next book.
- **Agent surfaces:** every skill exists in four trees — `.claude/skills/`,
  `.agents/skills/`, `.cursor/rules/`, `.agent/rules/` — and a change to one lands
  in all four in the same PR.

## A deliberate bump

Use this only for a major bump or when the train is down:

1. `uv run vibey-gh version --since origin/main --explain` to see the derived answer.
2. Edit the version in `pyproject.toml` and `src/vibey/__init__.py` (or pass
   `--apply` to write the derived one), then run `uv lock`.
3. Commit with `chore(release): x.y.z` — the exact subject `vibey-gh promote`
   writes.
4. Land it on `develop` through a PR. `vibey-gh promote` sees that `develop`
   already differs from `main` in version, leaves the bump alone, and still opens
   the promotion PR.

## Verifying the publish

After `main` builds:

1. Check the `Release` run in GitHub Actions, then `GitHub Release` and
   `Release surfaces`.
2. Verify PyPI: https://pypi.org/project/vibey/
3. Install and test:

```bash
uv venv --python 3.12
source .venv/bin/activate
pip install vibey==x.y.z
vibey --version
```

4. Check the published surfaces for the `main` channel:
   - Documentation: https://the-vibey-project.github.io/vibey/main/
   - Paper: https://the-vibey-project.github.io/vibey/main/paper/ and
     https://the-vibey-project.github.io/vibey/main/paper.pdf
   - Book: https://the-vibey-project.github.io/vibey/main/book.pdf,
     https://the-vibey-project.github.io/vibey/main/book.epub,
     https://the-vibey-project.github.io/vibey/main/book-print.html

For a `develop` push, the `verify-testpypi` job already installs the dev build.
On TestPyPI, read the release history of `vibey-dev`, not its "latest" version:
dev builds (`x.y.z.devN`) are pre-releases, so the project page shows the last
final version uploaded there (0.1.2) while dev builds such as `0.6.0.dev63` keep
landing.

## Common issues

**Version didn't change on PyPI:** the derivation found nothing under
`src/vibey/` (docs, workflow and tenant changes release nothing), or the bump was
never pushed. An unbumped version with `skip-existing: true` is a green run that
publishes nothing.

**`uv-lock` fails after a version change:** the lock carries vibey's own
version. Run `uv lock` and commit it with the bump.

**Publish failed:** check the `Release` run. Common causes: OIDC trusted
publisher not configured for the `pypi`/`testpypi` environment, wheel build
failed, or the in-tree `vibey-gh` rejected `.vibey-gh.toml`.

**Promotion PR does not merge:** the checks must pass on the promotion head, and
a ruleset that requires an approving review needs `AUTOMERGE_TOKEN` (a token whose
owner holds the required ruleset role).

**`develop` didn't realign after a release:** check whether `AUTOMERGE_TOKEN`
is set — the `realign` job skips (not fails) without it. To realign by hand, and
only when the trees match: `git push --force-with-lease origin main:develop`.

**CHANGELOG.md doesn't mention the shipped version:** nothing updates it
automatically; add the entry (see "The changelog").

## The workflows

- `.github/workflows/pr-automation.yml` — the event-driven review and
  merge-readiness gate, re-run on each `CI`/`Provenance` completion.
- `.github/workflows/merge-train.yml` — merges ready PRs (squash into `develop`,
  rebase into `main`).
- `.github/workflows/promote-to-main.yml` — `vibey-gh promote`.
- `.github/workflows/release.yml` — `build` on every push to `develop`/`main`;
  `testpypi`/`verify-testpypi` on `develop`; `pypi` and `realign` on `main`.
- `.github/workflows/github-release.yml` — tag and GitHub Release after a
  successful `Release` on `main`.
- `.github/workflows/release-surfaces.yml` — after a successful `Release` on
  `develop` or `main` (or manual dispatch per channel):
  - the ProperDocs site for that channel at
    `https://the-vibey-project.github.io/vibey/<channel>/`, all channels on one
    GitHub Pages deployment with a channel chooser at the root;
  - the book (`vibey-gh book` → `book.epub` and `book-print.html`, plus `book.pdf`
    when Chromium is available on the runner);
  - the paper (`docs/paper.md`, served as `paper/`, and `vibey-gh paper` → LaTeX →
    `paper.pdf`);
  - the OCI bundle `ghcr.io/<owner>/<repo>/python:<version>`, also tagged with the
    channel and `sha-<commit>`, and `latest` on `main`.
- `.github/workflows/provenance.yml` — the server-side provenance check on every
  push and PR.
- `.github/workflows/automation-bootstrap.yml` — the admin-only recovery path for a
  PR that repairs a broken privileged gate.

All but `automation-bootstrap.yml` (manual dispatch only) are triggered by pushes,
pull requests, workflow completions or schedules. Dispatch one by hand only to
recover or debug.
