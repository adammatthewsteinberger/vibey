# Release and promotion

Changes merge to `develop`, receive a derived development version, publish to TestPyPI,
and deploy Preview documentation. Promotion opens a `develop → main` PR. After exact-head
checks and review policy pass, it is rebase-merged without deleting either permanent
branch. Main creates the production tag, GitHub Release, PyPI distribution, GHCR package,
Production documentation, provenance, and then realigns develop safely.

The `Release` workflow that performs the TestPyPI/PyPI publish is hand-authored by the
adopting repository, not rendered by `vibey-gh install`: publish steps are project-specific
in a way the other managed workflows are not. It must exist under the exact name `Release`
and, on `develop` and `main`, derive and apply the version with `vibey-gh version --apply`,
build the package, and publish through the `testpypi` (develop) and `pypi` (main)
trusted-publishing environments. `github-release.yml`, `release-surfaces.yml`, and
`release-repair.yml` all trigger from a `workflow_run` named exactly `Release`; without a
correctly named and behaving workflow, none of the tag, GitHub Release, GHCR, documentation,
repository-profile, or release-repair steps below ever run.

Not every push to the release branch carries a new version — a docs-only or tooling-only
promotion, per `version.content_paths`/`code_paths`, is expected to publish nothing new. By
default, `github-release.yml` treats a push whose version is already tagged at a different
commit as that intentional no-op rather than a failure. Set `[github_release]
require_new_version = true` on a repository whose release branch should carry a new version
on every push, so a tag that would otherwise move is reported as the mistake it is. See
`docs/configuration.md`.

## Superseded releases

After each publish, `vibey-gh report-superseded` runs against the index that was just
published to and writes a job-summary list of every release the new version supersedes,
honouring `[yank] keep` and linking the project's release-management page. It reports
rather than yanks because **PyPI exposes no yank API** — the upload endpoint answers
`405` for a yank action and the web route is CSRF-protected — so the analysis is
automated and the click stays human. The configuration lives in
[`[yank]`](configuration.md#yank); both indexes default off.
