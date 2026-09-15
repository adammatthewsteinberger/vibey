---
name: package-manager-supply-chain-and-workspaces
description: "Use when hardening a package ecosystem against supply-chain attacks or designing build and monorepo features. Covers the 2025–2026 npm worm era, the attack taxonomy (typosquatting, dependency confusion, account takeover, install-time malware), registry-side controls worth building, client-side controls including install cooldowns, lifecycle scripts — the problem, why they exist and how ecosystems escaped them, running them safely — binary distribution design, workspaces, non-registry dependencies (git, path, URL), and overrides."
---

# Package Manager Development: Supply-Chain Security, Lifecycle Scripts, and Workspaces

> **Part 3 of 5** of the *Package Manager Development* reference (plugin `package-manager-development`), covering §8–§10. Sibling skills: `package-manager-versioning-and-resolution` (§0–§4), `package-manager-registries-and-installation` (§5–§7), `package-manager-ux-ecosystems-and-governance` (§11–§14), `package-manager-reference` (§15–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Verified August 2026. See §17 → `package-manager-reference` for the currency snapshot and what goes stale first.

> **How to read this.** Reference, not tutorial. Sections are independent. Three markers:
> - **[DURABLE]** — computer science, or a lesson every ecosystem has independently learned.
>   Does not expire.
> - **[ECOSYSTEM]** — specific to npm, PyPI, crates.io, Go, etc. Verify against that
>   ecosystem's current docs.
> - **[CONTESTED]** — the ecosystems have made genuinely different, defensible choices, or
>   the practitioners disagree. Both cases given.
>
> **⚠️ GOTCHA** boxes mark the design mistakes that produce unreproducible builds, wedged
> caches, exponential resolutions, or supply-chain compromise.
>
> **The framing that organizes everything below: a package manager is a distributed
> systems problem wearing a CLI.** It is a cache-coherency problem, a constraint-solving
> problem, a trust-and-identity problem, and a compatibility-contract problem, all of
> which happen to be invoked by typing `install`. Every serious difficulty in this
> document is one of those four, and treating it as "just downloading files" is the root
> of most bad designs.

---

## §8. Supply-Chain Security

### 8.1 The 2025–2026 npm worm era — what actually happened, because it changed the design space

**[ECOSYSTEM, but the lessons are universal.]** This is the most important recent case
study in package-manager security, and its details matter.

**Timeline:**
- **September 2025 — Shai-Hulud.** A **self-replicating worm** (named for the workflow file
  `shai-hulud-workflow.yml` it dropped, a *Dune* reference) entered via maintainer
  phishing. It injected malicious **postinstall** scripts, stole credentials, then — the
  novel part — **used the stolen npm token to authenticate as the compromised developer,
  enumerate their other packages, inject itself, and publish new versions.** Exponential
  spread with no attacker involvement. It also created public GitHub repos named
  "Shai-Hulud" containing the victim's exfiltrated secrets. GitHub removed 500+ compromised
  packages and blocked uploads matching the malware's IoCs.
- **November 2025 — Shai-Hulud 2.0.** Moved from **postinstall to preinstall**, widening
  impact to run before installation even completed.
- **2026 — continued waves**: "The Third Coming" (April), "Mini Shai-Hulud" (April–May,
  attributed to TeamPCP), and **August 2026's "ChainDrop"** — a Mini Shai-Hulud variant
  that compromised **`keyv`, `flat-cache`, `cache-manager` and 400+ packages across
  multiple unrelated publishers, ~2 billion monthly installs, within hours.** Microsoft's
  analysis describes a heavily obfuscated **Bun-based** payload executing via npm
  `preinstall`, harvesting npm, GitHub, AWS, Kubernetes, and HashiCorp Vault credentials.
- **The tradecraft shift that matters most:** earlier waves published using stolen tokens.
  **The 2026 waves increasingly ride the victim project's own release workflow** — pushing
  to `main` and cutting a release through legitimate CI. JFrog documented one sample that,
  inside a *specific* GitHub Actions run, requested an Actions OIDC token with audience
  `npm:registry.npmjs.org` — i.e. **abusing trusted publishing itself.**
- Parallel campaigns hit PyPI: **LiteLLM 1.82.7/1.82.8 (24 March 2026, ~95M monthly
  downloads) and telnyx 4.87.1/4.87.2**, part of a chain that began with a compromise of
  the **Trivy GitHub Action**. The LiteLLM payload used a **`.pth` file**, which
  auto-executes on *every interpreter start* — no import required.

**Scale context**: ReversingLabs measured a **73% year-over-year increase in malicious
open-source packages**, with npm accounting for roughly 90% of open-source malware;
Sonatype tracked 512,847 malicious packages in a single year.

**[DURABLE] The five design lessons:**
1. **Lifecycle scripts are the primary payload delivery mechanism.** See §9.
2. **A publishing credential is a lateral-movement primitive**, not just a secret. Any
   design where one credential can publish many packages is a worm substrate.
3. **Signing and provenance are necessary but not sufficient.** A worm that publishes
   through the victim's real CI earns a *legitimate* attestation. The VentureBeat framing
   is exact: the worm "didn't fake its security check — it earned a legitimate one."
4. **Detection speed is now a design parameter.** Socket reported average detection at
   ~5 minutes 18 seconds after publication during the August wave — and hundreds of
   packages still propagated.
5. **Containment beats prevention.** The controls that actually limited damage were
   short-lived credentials, script execution defaults, cooldowns, and blast-radius limits —
   not detection.

**npm's response** (worth knowing as the reference remediation): mandatory 2FA for
publishing, **revocation of legacy never-expiring tokens**, granular access tokens with
short expiry, and trusted publishing so build systems push without stored credentials.

### 8.2 The attack taxonomy

| Attack | Mechanism | Defense |
|---|---|---|
| **Typosquatting** | `reqeusts`, `python-dateutil` vs `dateutil` | Name-similarity checks at publish, install-time warnings |
| **Dependency confusion** | Public package shadows a private one of the same name | **Scoped/namespaced private packages; never let a public index satisfy an internal name.** Configure per-registry scope pinning |
| **Maintainer account takeover** | Phishing, credential stuffing | Mandatory 2FA/WebAuthn, trusted publishing |
| **Token theft** | Exfiltrated from CI, dotfiles, a compromised machine | Short-lived OIDC credentials; no long-lived tokens |
| **Self-replicating worm** | Stolen token → publish to all your packages | §8.1; per-package publish scoping |
| **Malicious maintainer / hostile handoff** | Legitimate owner turns, or hands the package to an attacker | Ownership-change alerts, cooldowns, code review of updates |
| **Protestware / sabotage** | Author deliberately breaks or wipes | Lockfiles + cooldowns + vendoring for critical paths |
| **Release poisoning** | Add a malicious file to an old, trusted release | §5.3 → `package-manager-registries-and-installation` — PyPI's 14-day rule |
| **Repojacking / name reuse** | Take over an abandoned name or deleted repo | **Never allow name reuse**; verify repo ownership continuously |
| **Compromised build tool** | The CI action itself is backdoored (Trivy, KICS in 2026) | Pin actions **by commit SHA, never by mutable tag** |
| **`.pth` / import-time execution** | Python-specific auto-execution | Restrict what installs may place on `sys.path` |
| **Compromised mirror / MITM** | Substituted bytes | TLS + lockfile hashes + transparency logs |

> **⚠️ GOTCHA — mutable references are a recurring root cause.** The March 2026 LiteLLM and
> Telnyx compromises traced to a **mutable reference in their use of the Trivy GitHub
> Action**. `uses: some/action@v1` is a moving target controlled by someone else. Pin to a
> full commit SHA. This single practice would have prevented multiple 2026 incidents.

### 8.3 Registry-side controls worth building

- **Mandatory 2FA / WebAuthn for publishing**, especially for high-impact packages.
- **Trusted publishing** and deprecation of long-lived tokens (§7.1 → `package-manager-registries-and-installation`).
- **Provenance generation by default**, not opt-in (§7.2 → `package-manager-registries-and-installation`).
- **Quarantine**, not delete — freeze a suspected package pending investigation while
  preserving existing installs.
- **Name-similarity scoring at publish time** and an appeals process.
- **Publish-event alerting to maintainers**, so an unexpected release is noticed in minutes.
- **A public, machine-readable advisory feed** (OSV format is the interoperable standard).
- **Malware scanning at ingest** — imperfect, but the August 2026 detection times show it
  meaningfully compresses exposure windows.
- **Upload timestamps in the API** so clients can implement cooldowns.

### 8.4 Client-side controls — and the one with the best evidence

**Cooldowns / minimum release age are the highest-value new control.** The idea: refuse to
install a version published less than N days ago, so the ecosystem's detection machinery
gets a chance first.

- **pip 26.1 (April 2026) added `--uploaded-prior-to`**; **uv has `--exclude-newer`**;
  **pnpm has `minimum-release-age`**; Dependabot has a cooldown setting. All rely on
  registry-reported upload timestamps (PEP 700 in Python).
- **The reported evidence**: research cited alongside the pip 26.1 release found that a
  **7-day cooldown would have prevented 8 out of 10 analyzed supply-chain attacks from
  reaching end users**. That is an unusually strong result for a control this cheap.
- **The honest limitations**, which the pip team and others state plainly: it does not stop
  a sophisticated attack that evades detection for longer, does nothing about
  vulnerabilities in packages you already depend on, and **delays security patches** — so
  you need an expedite path for genuine fixes.

The rest of the client-side baseline:
- **`--frozen-lockfile` / `ci` mode everywhere in CI.** Never resolve in CI.
- **Disable lifecycle scripts by default** (§9), allowlisting the few that need them.
- **Pin CI actions by SHA.**
- **Generate an SBOM per build** (SPDX or CycloneDX; `npm sbom`, `syft`) — this is what
  turns "are we affected?" from a week into minutes, and is increasingly a legal
  requirement (§14.3 → `package-manager-ux-ecosystems-and-governance`).
- **Verify provenance where available** — prefer packages with attestations, and pin
  *publisher identities* where your tooling supports it.
- **Vendor or mirror** the dependencies of anything you cannot afford to have change.

---

## §9. Lifecycle Scripts and Building

### 9.1 The problem, stated plainly

**[DURABLE] Arbitrary code execution at install time is the original sin of package
management.** `npm install` running `preinstall`/`postinstall`, `pip install` executing
`setup.py`, `gem install` running `extconf.rb` — in every case, *fetching a dependency
executes attacker-controlled code with the developer's full privileges.*

Every major worm in §8.1 used this. Shai-Hulud's move from `postinstall` to `preinstall`
was specifically to execute *before* installation completed, widening the blast radius.

### 9.2 Why it exists, and how ecosystems escaped it

It exists because native code needs compiling and platforms differ. The escapes, in order
of how well they worked:

1. **Prebuilt binary artifacts.** Python's **wheels** are the great success story here: a
   wheel is a zip that is *installed by copying*, with no code execution. The
   `manylinux`/`musllinux`/`macosx` platform tag scheme made prebuilt binaries portable.
   **This single change removed install-time execution from the overwhelming majority of
   Python installs** — and it's why sdists (which do run `setup.py`) are now the risky path.
2. **Declarative build metadata.** `pyproject.toml`'s `[build-system]` replaced executable
   `setup.py` configuration with data. Cargo's `Cargo.toml` was declarative from birth
   (with `build.rs` as a deliberate, visible exception).
3. **Separate build from install.** Go does not execute dependency code at fetch time at
   all — it compiles it as part of *your* build, which is a different and much better trust
   boundary.
4. **Default-off with an allowlist.** pnpm's `onlyBuiltDependencies` is the pragmatic
   modern answer: scripts don't run unless you name the package. npm has `--ignore-scripts`.
   Bun and Yarn have equivalents.

**[DURABLE] If you are designing a package manager today: do not run install-time scripts
by default.** Provide an explicit, per-package allowlist that lives in the manifest and is
reviewable in a diff. The compatibility cost is real (native modules — node-gyp builds,
`sharp`'s prebuilt binaries, Prisma's engine downloads — all use postinstall) and it is
worth paying.

### 9.3 If you must run them

- **Sandbox**: no network, restricted filesystem, no access to credentials or environment
  secrets. Nix and Guix's build sandboxes are the reference implementations.
- **Log everything** the script does, visibly.
- **Never run scripts for transitive dependencies the user didn't name**, at minimum
  without a prompt.
- **Deterministic environment**: fixed `PATH`, no ambient config, no `$HOME` dotfiles.

### 9.4 Binary distribution design

If you ship prebuilt artifacts, you need a **platform tag scheme** answering: OS, libc
(glibc version! musl!), CPU architecture, and language/ABI version. Python's
`manylinux_2_28_x86_64` encodes a glibc floor; that design is worth copying because it
expresses *forward* compatibility rather than distro identity.

Also decide: what happens when there's no matching binary? Fall back to source (and thus to
executing a build), or fail? Both answers are defensible; **silently falling back to source
build is how "it worked on my machine and took 40 minutes in CI" happens.**

---

## §10. Workspaces, Monorepos, and Overrides

### 10.1 Workspaces

Multiple packages in one repository, resolved together, with local packages satisfying each
other's dependencies instead of the registry.

Requirements that make a workspace implementation good:
- **A single lockfile for the whole workspace.** Per-package lockfiles defeat the purpose.
- **One shared resolution**, so two members can't end up on incompatible versions of a
  shared dependency by accident.
- **An explicit local-link protocol.** pnpm's `workspace:*` **always** resolves to the local
  package — making it impossible to accidentally test against the published version when you
  meant local. That is the correct default and worth copying.
- **Shared version constraints** — pnpm's *catalogs*, Cargo's `[workspace.dependencies]`,
  Maven's `dependencyManagement`. Without this, upgrading a dependency across 50 packages is
  50 edits.
- **Filtering and topological task execution** — `--filter`, run in dependency order.

### 10.2 Non-registry dependencies

Path, git (with a **pinned commit**, never a branch), URL, and vendored dependencies. Each
needs a lockfile representation that preserves reproducibility — a git dependency locked to
a branch name is not locked.

### 10.3 Overrides

`overrides` (npm, pnpm), `resolutions` (Yarn), `[patch]` (Cargo), `replace` (Go).
**[DURABLE] You need this escape hatch** — a transitive dependency has a CVE and the
intermediate package hasn't updated. Design it explicitly rather than letting people
hand-edit lockfiles.

But make it **loud**: overrides silently violate a dependency's declared constraints, which
means you own the compatibility risk. Print them on install. Make them expire or require
periodic re-confirmation if you can.
