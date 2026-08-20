# Runbook: package everything, everywhere

## Goal

vibey (and the loop runners, and the client SDKs) installable through the
package manager each audience already uses — one `release` pipeline
fanning out to all of them on every tagged version.

## Targets

| Channel | Artifact | Audience |
|---|---|---|
| PyPI (`pip install vibey`, `uv tool install vibey`) | sdist + wheel | Python users — the canonical channel |
| Homebrew (`brew install <tap>/vibey`) | formula in a `homebrew-vibey` tap | macOS/Linux devs |
| apt | .deb in a hosted repo (Cloudsmith/packagecloud or self-hosted aptly on Pages) | Ubuntu/Debian |
| yum/dnf | .rpm in a hosted repo | Fedora/RHEL |
| AUR | `vibey` PKGBUILD | Arch |
| npm/yarn/bun (`npm i -g @vibey/cli` wrapper; `@vibey/sdk`) | wrapper + TS SDK | JS ecosystem |
| pipx/uvx | rides PyPI | one-off runners |
| Docker/GHCR (`ghcr.io/.../vibey`) | images from workstream 05 | cluster users |
| Desktop bundles | dmg / AppImage / deb / rpm from workstream 08 | GUI users |

Loop runners get the same treatment (PyPI + brew + npm wrapper) from
their own repos with the same reusable pipeline.

## Design

- **One version, one tag, one pipeline**: a `release.yml` workflow on tag
  push — build sdist/wheel (uv build), sign (Sigstore), publish PyPI via
  trusted publishing (OIDC, no long-lived token), then fan out:
  - Homebrew: bump-formula PR into the tap repo (brew's
    `bump-formula-pr`), formula installs from PyPI sdist with virtualenv.
  - deb/rpm: `fpm`-built from the wheel with a bundled venv
    (`/usr/lib/vibey/venv`), postinst symlinks `/usr/bin/vibey`; pushed to
    the hosted apt/yum repos.
  - AUR: PKGBUILD regenerated + pushed to the AUR git remote.
  - npm: `@vibey/cli` wrapper (postinstall verifies python≥3.12 or
    downloads a standalone build via `python-build-standalone`) and
    `@vibey/sdk` from workstream 12's generated client.
- The engine binaries stay separate installs (each runner's own packages)
  — `vibey doctor` already tells the user what's missing; the brew
  formula lists them as optional deps.
- Version discipline: single source in `pyproject.toml`; the pipeline
  refuses tags that don't match it; Conventional Commits drive the
  changelog (release notes generated per tag — also feeds workstream 14).

## Work items

1. PyPI trusted publishing + first public release (name availability
   check first; fall back to `vibey-conductor` if squatted).
2. `homebrew-vibey` tap + formula + CI bump automation.
3. fpm deb/rpm build + repo hosting + install smoke tests in Ubuntu,
   Fedora containers (CI matrix).
4. AUR PKGBUILD + ssh publish key.
5. npm wrapper + SDK publish.
6. Release workflow tying it all to tag push, with per-channel dry-run
   mode.
7. Docs: `docs/getting-started/install.md` rewritten per-channel.
8. Repeat the pipeline template across the four (five with copilotloop)
   runner repos.

## Verification

A `vX.Y.Z` tag produces, in one run: PyPI release installable via
`uv tool install`, brew formula installing on a clean mac, deb/rpm
installing in fresh Ubuntu/Fedora containers (CI-proven), AUR building in
an Arch container, npm wrapper running `vibey --help`. Each channel's
smoke test runs `vibey doctor` successfully.

## Needs from operator

PyPI + npm accounts (trusted publishing needs one-time web setup), a tap
repo, an AUR account + ssh key, and a packagecloud/Cloudsmith account (or
GitHub Pages hosting decision) for apt/yum.

## Risks

- Name squatting on public registries — check first, reserve early.
- deb/rpm bundled-venv size — acceptable; document the tradeoff.
- Every channel is a forever-maintenance surface — the release pipeline
  is the only sanctioned publish path (no manual uploads), and 04 watches
  packaging-tool drift.
