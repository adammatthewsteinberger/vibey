# Release process

Releases are automated by [release-please](https://github.com/googleapis/release-please)
reading Conventional Commits history on `main`, and published to PyPI via
[Trusted Publishing](https://docs.pypi.org/trusted-publishers/) (OIDC — no
long-lived API token stored anywhere).

## The automated loop

1. A PR merges into `develop`, then `develop` merges into `main` as a merge
   commit (preserving individual conventional commits — see
   [development.md](development.md#the-branch-model-gitflow)).
2. `release-please.yml` runs on every push to `main`. It maintains a single
   standing PR titled `chore(release): x.y.z`, whose body is the generated
   changelog for everything merged since the last release, and whose diff
   bumps `[project].version` in `pyproject.toml` and updates `CHANGELOG.md`.
3. **Merging that PR is what cuts a release** — it's the human review gate.
   On merge, release-please tags the commit and creates a GitHub Release.
4. `publish-to-pypi.yml` triggers on `release: published`, builds the sdist
   and wheel, and publishes to PyPI via Trusted Publishing. The GitHub
   environment `pypi` requires manual approval before the publish job runs
   — a second human gate, independent of the release-please merge.

Nothing in this loop requires the maintainer to hand-bump a version number,
hand-write a changelog entry, or hold a PyPI API token anywhere.

## One-time manual setup (already done for this repo, documented for forks)

1. **Create the GitHub repo** `adammatthewsteinberger/claudeloop`, push
   `main` and `develop`. Set **`develop` as the default branch** so the
   GitHub front door is the integration branch contributors PR into.
   `main` stays the always-releasable line that release-please watches.
   Fill in the About box (description, website, topics) as documented in
   [documentation.md](documentation.md#github-about-box-not-stored-in-git);
   enable Discussions; leave the wiki off.
2. **PyPI → Account settings → Publishing → Add a new pending publisher:**

   | Field | Value |
   |---|---|
   | PyPI Project Name | `claudeloop` |
   | Owner | `adammatthewsteinberger` |
   | Repository name | `claudeloop` |
   | Workflow name | `publish-to-pypi.yml` (the **filename** — this is load-bearing) |
   | Environment name | `pypi` |

3. **Create the GitHub environment `pypi`** (repo Settings → Environments)
   with the maintainer as a required reviewer. This is what makes Trusted
   Publishing meaningfully stronger than a repo-scoped API token — per
   PyPI's own security model documentation, anyone with commit access can
   otherwise modify a publishing workflow, so the human approval gate on the
   environment is the actual control, not the OIDC exchange by itself.
4. **Protect `main`**: require CI (`ci.yml`) to pass, disallow force-pushes.
5. **Enable GitHub Pages**, source: GitHub Actions (for `docs.yml`).

A PyPI *pending* publisher reserves nothing — the project name isn't claimed
until the first real publish succeeds. The working title `autoclaude` was
rejected as too similar to existing packages, which is why this project
ships as `claudeloop`; claim it promptly with a real `0.1.0` rather than
deferring indefinitely.

## Doing a release dry run

Before the first real PyPI publish, validate the whole OIDC + build
pipeline against **TestPyPI**:

1. Repeat the pending-publisher setup above at `test.pypi.org` (a fully
   separate account and publisher registry from `pypi.org`).
2. Trigger the TestPyPI job manually (`workflow_dispatch`), or push a
   pre-release tag if the workflow is wired to react to one.
3. `pip install -i https://test.pypi.org/simple/ claudeloop` in a scratch
   virtual environment and confirm the CLI entry point resolves.
4. Only once that round-trips cleanly, proceed with a real release-please
   PR merge against `main`.

## What CI checks before any of this runs

Every gate in [development.md](development.md#running-the-quality-gates-locally)
runs in `ci.yml` on every push and PR to `main`/`develop`, across Python
3.10–3.13. `publish-to-pypi.yml` does not re-run the test suite — it trusts
that nothing reaches `main` (protected, CI-gated) without already having
passed it, and its own `build` job runs `twine check --strict` on the built
artifacts as its only quality gate, keeping the publish job itself minimal
(it holds the OIDC token; the less it does, the smaller that surface is).

## Verifying a completed publish

- Attestations: `pypa/gh-action-pypi-publish` generates signed attestations
  automatically for Trusted Publishing flows (PEP 740) — visible on the
  PyPI project page under each release's files.
- `py.typed` shipped in the wheel: `unzip -l dist/*.whl | grep py.typed`.
- Metadata: `pypi.org/project/claudeloop/` should show the classifiers,
  keywords, and `[project.urls]` links configured in `pyproject.toml`.
