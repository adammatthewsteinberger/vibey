# 0028 — vibey-gh owns provenance and release; release-please is retired

**Status:** accepted · **Date:** 2026-08-21 (PR #77; vibey-gh 1.39.0 adoption PR #91, 2026-08-28; recorded 2026-09-15) · **Extends:** ADR-0017, ADR-0018

## Context

Until #77 this repository ran release-please: it derived a version from Conventional Commits, opened a release pull request, wrote `CHANGELOG.md`, and `publish-to-pypi.yml` fired on `release: published`. The five runners and `vibey-skills` had meanwhile adopted `vibey-gh`, the family's own automation: provenance fingerprints on every source file, a derived version, a merge train, a promote-to-main flow, managed workflow templates, a PR-review gate with a local-model fallback, and a ProperDocs site. Running both against one branch is a race, not a belt and braces — both derive versions and both open release PRs.

## Decision

**One release system, and it is the family's.** release-please and `publish-to-pypi.yml` were removed outright.

- **Channels.** Every push to `develop` publishes a dev build to TestPyPI as `vibey-dev` — versioned `<next release>.dev<run number>`, because an index version is immutable and `vibey` on TestPyPI belongs to an unrelated project — and verifies it installs and runs. Every push to `main` publishes to PyPI. The two paths are deliberately disjoint: publishing a final version to TestPyPI first would make a release depend on a second registry and can collide with an immutable version already uploaded there. The version is derived by `vibey-gh version`, never remembered; vibey-gh 1.73.0 re-locks `uv.lock` when a promotion bumps `pyproject.toml` (three earlier releases needed a follow-up lock fix).
- **Pinned templates** (`pin_version = true`): an upgrade is a reviewed diff, never a runner's resolver deciding for us — the failure that took vibey-skills' CI red for two days.
- **Provenance.** Every source file carries the fingerprint header; `E501` is ignored for exactly that unwrappable line. The provenance gate is a required check.
- **Gated automation that degrades, not blocks.** The PR gate and issue triage fall back to a local model on a self-hosted runner when the paid path returns no verdict; `trusted_only` keeps fork PRs off it.
- **Hooks chain, they do not replace.** Installing vibey-gh points `core.hooksPath` at `.githooks`, after which `.git/hooks` is never consulted — which silently disables the pre-commit framework that holds the local gate suite. vibey-gh chains to `<hook>.local`, and those exec the framework's generated hook (not `pre-commit` by name, which a git hook's environment may not find).
- **Docs.** ProperDocs, published per channel by the managed `release-surfaces.yml`; `docs/plans` excluded because superseded planning notes published as reference present drafts as truth.

## Consequences

**Good.** The conductor is released by the tooling it conducts (ADR-0017), and every behaviour of the release is a file in the tree (ADR-0018): `.vibey-gh.toml` is the whole configuration. Releases 0.2.0 through 0.6.0 shipped through it.

**Bad, and left unhandled for four releases.** `CHANGELOG.md` was a release-please artifact; nothing wrote it afterwards, so it stopped at 0.2.0 while PyPI reached 0.6.0. GitHub Releases stopped at v0.1.2 — not because vibey-gh cannot create them (`github-release.yml` does), but because this repository never adopted that template. `CONTRIBUTING.md` kept describing release-please. Settled on 2026-09-15: the changelog is reconstructed from the release commits and written by hand in each release commit (the `vibey-releasing` skill), `github-release.yml` is adopted so every promotion tags and releases (PR #147), and `CONTRIBUTING.md` describes this flow. A develop release also failed for three pushes when `release.yml` pinned a published vibey-gh too old to parse this repository's configuration; it now installs the tree's own copy (PR #146).

**Rule status.** Mechanism (which tool); the standing rules are ADR-0017 and ADR-0018. Does not pass ADR-0020's test on its own.

## Alternatives rejected

- **Keep release-please, add vibey-gh for provenance only.** Two version derivations on one branch; the first disagreement is a broken release.
- **Keep release-please, skip vibey-gh.** Violates ADR-0017 and leaves the conductor as the one family member not on the family's automation.
- **Publish straight to PyPI from `main`.** Loses the only pre-upload rehearsal an immutable index allows.
- **Replace pre-commit with vibey-gh hooks.** The gate suite lives in the framework; the chain keeps both.
