# Release process

Releases are automated by [release-please](https://github.com/googleapis/release-please)
reading Conventional Commits on `main`, and published to PyPI via
[Trusted Publishing](https://docs.pypi.org/trusted-publishers/) (OIDC — no
long-lived API token stored anywhere).

The **first** public tag is `v0.1.0` from the version already in
`pyproject.toml` and `.release-please-manifest.json`. Do **not** wait for
release-please to invent `0.1.1` for that cut. Later releases: squash to
`develop`, merge-commit to `main`, merge the release-please PR.

## The automated loop (after 0.1.0)

1. Feature PRs squash-merge into `develop`.
2. `develop` merge-commits into `main`.
3. `release-please.yml` (`target-branch: main`) maintains
   `chore(release): x.y.z`.
4. Merging that PR tags and creates a GitHub Release.
5. `publish-to-pypi.yml` on `release: published` publishes to PyPI via the
   `pypi` environment (manual approval).

## One-time GitHub / PyPI setup

Documented so a fork can reproduce it.

1. Create public repo `adammatthewsteinberger/agyloop`. Push `develop` and
   `main`. Default branch: **`develop`**.
2. GitHub Pages: source = GitHub Actions (`docs.yml`).
   Site: `https://adammatthewsteinberger.github.io/agyloop/`
3. Environments:

   | Name | URL | Required reviewers |
   |---|---|---|
   | `github-pages` | Pages URL | optional |
   | `testpypi` | `https://test.pypi.org/p/agyloop` | yes (maintainer) |
   | `pypi` | `https://pypi.org/p/agyloop` | yes (maintainer) |

4. Branch protection (FOSS, solo maintainer — require CI, **do not**
   require CODEOWNER reviews or the owner cannot merge):

   **`main`**

   - Require a pull request
   - Required checks from `ci.yml` (lint, typecheck, imports, security,
     test, docs, build)
   - No force-push, no delete
   - Allow **merge commits** (gitflow)
   - Dismiss stale reviews: optional

   **`develop`**

   - Require a pull request
   - Same required checks
   - No force-push, no delete
   - Allow **squash merge**

5. Trusted Publisher on pypi.org and test.pypi.org (you must click this in
   the PyPI UI; the workflow cannot register itself):

   | Field | Value |
   |---|---|
   | PyPI Project Name | `agyloop` |
   | Owner | `adammatthewsteinberger` |
   | Repository name | `agyloop` |
   | Workflow name | `publish-to-pypi.yml` (filename is load-bearing) |
   | Environment name | `pypi` or `testpypi` |

## TestPyPI dry run

```bash
# workflow_dispatch publish-to-pypi.yml with target=testpypi
# Approve environment testpypi
pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ agyloop
```

`--extra-index-url` is required so runtime deps resolve from real PyPI.

## First public 0.1.0

1. Merge `develop` → `main` as a merge commit.
2. `workflow_dispatch` TestPyPI; approve `testpypi`.
3. `gh release create v0.1.0` on `main` (notes from CHANGELOG). That fires
   `release: published` → approve env `pypi`.
4. Confirm `https://pypi.org/project/agyloop/`,
   `https://adammatthewsteinberger.github.io/agyloop/`,
   `pip install agyloop`, and `agyloop --help`.

## Verifying a completed publish

- `twine check --strict` in the build job
- `py.typed` in the wheel
- `[project.urls]` on the PyPI project page
