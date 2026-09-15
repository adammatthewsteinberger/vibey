# 0019 — Vibey is installable wherever its users already are

**Status:** accepted · **Date:** 2026-09-15 · **Extends:** ADR-0017, ADR-0018

## Context

Ten distributions come out of this tree and every one of them reaches exactly one
audience: people who already have Python and reach for `pip`. That is the wrong
shape for what these are. `vibey`, the five `*loop` runners and `vibey-gh` are
**command-line applications**. Someone installing a CLI runs `brew install`,
`winget install`, `apt install` — the fact that it happens to be written in
Python is an implementation detail they should never have to care about, and
`pip install` asks them to care.

The evidence that this is already felt: a Homebrew tap already exists —
`adammatthewsteinberger/homebrew-tap`, tapped as `brew tap adammatthewsteinberger/tap`
— with `Formula/` and `Casks/` directories, and both are empty.

## Decision

**Publish to every registry that can carry these projects, and treat a
distribution channel as part of shipping rather than as a follow-up.**

A release is not finished when PyPI has the wheel. It is finished when the
channels that carry it have it.

### What the targets actually are

Taking the list literally would produce an unactionable plan, because it names
four different kinds of thing. Grouped by what publishing to each one *means*:

**1. Registries we can publish to ourselves, today.** These accept a submission
from the author with no gatekeeper, which makes them the whole near-term plan.

| | |
|---|---|
| macOS / Linux | Homebrew (our own tap exists and is empty), MacPorts, pkgsrc, Nixpkgs |
| Linux, self-served | Arch AUR, Fedora COPR, Ubuntu PPA, openSUSE OBS, Alpine aports |
| Linux, sandboxed | Snap (Snapcraft), Flatpak (Flathub) |
| Windows | winget, Chocolatey, Scoop |
| FreeBSD | ports |
| Python-adjacent | conda-forge |

**2. Official distribution repositories, which need a human.** Debian, Fedora,
Arch `extra`, openSUSE and Ubuntu's own archive all require a package maintainer
and a review process; nobody self-publishes into them. They are a goal reached
*through* group 1 — a package that has lived in AUR/COPR/PPA with users is the
normal path to a maintainer picking it up. Planning them as tasks would be
planning someone else's decision.

**3. Formats and tools, not registries.** `dpkg`, `rpm` and `apk-tools` are how a
`.deb`, `.rpm` or `.apk` is *built and installed*, not places to publish. We
produce those artifacts — and attaching them to a GitHub Release is genuinely
useful — but "publish to dpkg" has no meaning, and the work it stands for is
already covered by group 1.

`podman` is a container runtime, not a package manager. What it actually wants is
an OCI image, and this repository **already builds one** (`deploy/docker/`,
multi-arch amd64+arm64, gated by four image contracts in CI). `release-surfaces.yml`
already pushes to `ghcr.io` on every release, but what it pushes is the wheel and
sdist as an OCI *artifact* (`ghcr.io/<repository>/python`), not the runnable container
image. Publishing the image is a small, real task, and it serves Docker, podman, Kubernetes and
anything else that speaks OCI at once.

**4. Registries for other languages' libraries.** npm, yarn, Maven, Gradle,
Cargo, NuGet, Composer, RubyGems, sbt, vcpkg, Deno and PEAR carry JavaScript,
Java, Rust, .NET, PHP, Ruby, Scala and C++ packages. **None can carry a Python
library.** What they *can* carry is a thin wrapper that downloads the CLI — which
is a real, common pattern, and a different promise: `npm install vibey` would
give you the command, never an importable library, and the package must say so.

So these are judged individually on whether the audience is real rather than
adopted as a set. **npm is worth it** — a very large population of developers
installs tooling that way and never touches Python. The rest are not: a Maven
artifact that shells out to a Python CLI serves nobody, and publishing one is
noise in someone else's ecosystem. PEAR is superseded by Composer; Fink is
dormant; `wpkg` is dead; `par` names no package manager we could identify.
Revisit any of them when a real user asks.

### How it is done, per the doctrines this extends

**Every packaging definition lives in this repository** (ADR-0018). A Homebrew
formula, a PKGBUILD, a snapcraft.yaml, a nuspec, a winget manifest — all of them
are code, reviewed in a pull request, and rendered or published by automation.
A recipe that exists only in a tap somebody edits by hand is exactly the clicked
state that ADR forbids.

**vibey-gh conducts it** (ADR-0017). Releasing to N channels is release
automation, and this family already has release automation. The capability
belongs there — beside `report-superseded`, which already knows about indexes —
and not in a pile of per-repository workflow YAML.

**One artifact, many wrappers.** Most of group 1 needs a self-contained
executable rather than a Python package, so a single-file build (shiv, pex or
PyInstaller) becomes a release artifact that the majority of these channels then
just point at. That one piece of work unblocks most of the list, which is why it
comes first.

## Consequences

**Sequenced by reach per unit of effort, not by list order:**

1. **OCI image to `ghcr.io`.** Already built and contract-tested; only publishing
   is missing. Serves podman, Docker and Kubernetes at once.
2. **A single-file executable as a release artifact.** Unblocks most of what
   follows.
3. **Homebrew.** The tap exists and is empty; the largest macOS/Linux developer
   audience per line of effort.
4. **winget, Scoop, Chocolatey.** Manifest-only, and the only reasonable way a
   Windows user installs a CLI.
5. **AUR, COPR, PPA, OBS, Alpine.** Self-served Linux, and the route toward
   group 2.
6. **Snap and Flatpak.** Higher effort; both want a confinement story, and a
   worker that spawns engine subprocesses and writes git worktrees is not
   obviously confinable. Decide the confinement level before starting.
7. **conda-forge, Nixpkgs, MacPorts, pkgsrc, FreeBSD ports.** Each has its own
   review culture; steady rather than urgent.
8. **npm wrapper.** Only after the single-file artifact exists, and it must
   document that it installs a command, not a library.

**Every channel is a support surface.** A stale formula is worse than no formula,
because it installs an old version silently. Nothing is added here without being
published by the same automation as everything else — which is the real reason
this is one ADR rather than thirty tickets.

**A caveat worth stating plainly:** `vibey` needs PostgreSQL and at least one
`*loop` engine on `PATH` to do anything. Several of these channels imply "install
and it works". The packaging has to be honest about that — a post-install note,
and `vibey doctor` already reports what is missing.
