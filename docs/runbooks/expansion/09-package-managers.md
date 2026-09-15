# Runbook: package everything, everywhere

> **Status (2026-09-15):** PyPI channel done — `release.yml` publishes `main`
> to PyPI by trusted publishing and `develop` to TestPyPI as `vibey-dev`
> (ADR-0028). Everything else is open. **ADR-0019 supersedes this runbook's
> channel list and order**; the tables and items below are corrected to it.

## Goal

vibey (and the loop runners, and the client SDKs) installable through the
package manager each audience already uses — one release automation,
conducted by `vibey-gh` (ADR-0028), fanning out to all of them on every
promoted version.

## Targets

In ADR-0019's order (reach per unit of effort):

| # | Channel | Artifact | Status |
|---|---|---|---|
| 0 | PyPI (`pip install vibey`, `uv tool install vibey`), pipx/uvx | sdist + wheel | Done (`release.yml`) |
| 1 | OCI image on `ghcr.io` | the image from workstream 05 | Image is built and contract-tested in CI; not pushed. `release-surfaces.yml` pushes only the Python distribution to `ghcr.io/<repo>/python` as an OCI artifact |
| 2 | Single-file executable (shiv, pex or PyInstaller) | release asset | Open; unblocks 3–8 |
| 3 | Homebrew | formula in the existing, empty `the-vibey-project/homebrew-tap` | Open |
| 4 | winget, Scoop, Chocolatey | manifests | Open |
| 5 | AUR, COPR, PPA, OBS, Alpine | PKGBUILD / spec / recipes | Open |
| 6 | Snap, Flatpak | confined bundles (decide confinement first) | Open |
| 7 | conda-forge, Nixpkgs, MacPorts, pkgsrc, FreeBSD ports | recipes | Open |
| 8 | npm wrapper (`@vibey/cli`; installs a command, not a library) | wrapper | Open |
| — | `.deb` / `.rpm` | formats, not registries: attached to GitHub Releases, not hosted apt/yum repos | Open |
| — | Desktop bundles | dmg / AppImage / deb / rpm from workstream 08 | Blocked on 08 |

The loop runners are workspace members of this repository (ADR-0021) and
publish to PyPI as their own projects; the same channel automation covers
them.

## Design

- **Packaging definitions live in this repository** and are published by
  `vibey-gh` release automation (ADR-0017, ADR-0018, ADR-0028), starting
  from the single-file executable artifact. Today `release.yml` runs on
  pushes to `develop` (dev build to TestPyPI as `vibey-dev`, because
  `vibey` on TestPyPI is not ours) and `main` (PyPI, trusted publishing
  via OIDC, no long-lived token). The fan-out below is still to build:
  - Homebrew: bump-formula PR into the tap repo (brew's
    `bump-formula-pr`), formula installs from PyPI sdist with virtualenv.
  - deb/rpm: `fpm`-built from the wheel with a bundled venv
    (`/usr/lib/vibey/venv`), postinst symlinks `/usr/bin/vibey`; attached
    to the GitHub Release (ADR-0019: formats, not registries).
  - AUR: PKGBUILD regenerated + pushed to the AUR git remote.
  - npm: `@vibey/cli` wrapper (postinstall verifies python≥3.12 or
    downloads a standalone build via `python-build-standalone`) and
    `@vibey/sdk` from workstream 12's generated client.
- The engine binaries stay separate installs (each runner's own packages)
  — `vibey doctor` already tells the user what's missing; the brew
  formula lists them as optional deps.
- Version discipline: single source in `pyproject.toml`; `vibey-gh
  promote` cuts the `chore(release): x.y.z` commit (release-please is
  retired, ADR-0028); Conventional Commits drive the changelog (also
  feeds workstream 14).

## Work items

1. PyPI trusted publishing + first public release. **Done** (PyPI
   `vibey` 0.1.0–0.6.0).
2. Push the CI-built OCI image to `ghcr.io`.
3. Single-file executable as a release asset.
4. Formula in `the-vibey-project/homebrew-tap` + bump automation.
5. winget/Scoop/Chocolatey manifests; then AUR/COPR/PPA/OBS/Alpine.
6. fpm deb/rpm build attached to GitHub Releases + install smoke tests in
   Ubuntu, Fedora containers (CI matrix).
7. Docs: the README Quickstart install block and `docs/index.md` gain a
   per-channel install matrix generated from the same channel list the
   release automation publishes.
8. The same automation covers the five runners and `vibey-gh` as
   workspace members of this repository; npm wrapper + SDK last.

## Verification

A promoted `X.Y.Z` release produces, in one run: PyPI release installable via
`uv tool install`, brew formula installing on a clean mac, deb/rpm
installing in fresh Ubuntu/Fedora containers (CI-proven), AUR building in
an Arch container, npm wrapper running `vibey --help`. Each channel's
smoke test runs `vibey doctor` successfully.

## Needs from operator

PyPI: done. Remaining: `packages:write` on ghcr.io; the single-file tool
decision; the existing `the-vibey-project/homebrew-tap`; winget, Scoop and
Chocolatey accounts; an AUR account + ssh key; an npm account last.

## Risks

- Name squatting on public registries — check first, reserve early.
- deb/rpm bundled-venv size — acceptable; document the tradeoff.
- Every channel is a forever-maintenance surface — the release pipeline
  is the only sanctioned publish path (no manual uploads), and 04 watches
  packaging-tool drift.
