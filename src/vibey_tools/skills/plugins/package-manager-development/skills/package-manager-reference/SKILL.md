---
name: package-manager-reference
description: "Use when reviewing a package manager or registry design for known anti-patterns, weighing contested questions (MVS vs constraint solving, multiple versions coexisting, hoisted vs isolated vs PnP, lockfiles for libraries, one standard lockfile format, whether SemVer is worth it, package manager as build tool, cooldowns vs patch latency, vendoring), checking whether an ecosystem or tooling claim is still current (snapshot verified August 2026), finding the foundational writing and primary sources, or needing the build-it-in-order checklist, diagnostic first moves, and numbers. Companion to the other package-manager-development skills."
---

# Package Manager Development: Anti-Patterns, Contested Questions, Currency, and Canon

> **Part 5 of 5** of the *Package Manager Development* reference (plugin `package-manager-development`), covering §15–§20. Sibling skills: `package-manager-versioning-and-resolution` (§0–§4), `package-manager-registries-and-installation` (§5–§7), `package-manager-supply-chain-and-workspaces` (§8–§10), `package-manager-ux-ecosystems-and-governance` (§11–§14). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Verified August 2026. See §17 below for the currency snapshot and what goes stale first.

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

## §15. Anti-Patterns

| Anti-pattern | Why | Instead |
|---|---|---|
| No lockfile | Unreproducible builds; every install is a new resolution | Lockfile with integrity hashes, from v1 |
| Lockfile without hashes | Pins versions, not bytes | sha256/sha512 per artifact |
| Lockfile that only works on the generating platform | CI breaks | Universal/marker-aware lockfiles (§4.2 → `package-manager-versioning-and-resolution`) |
| Resolving in CI | Non-reproducible, and installs today's malware | `ci`/`--frozen-lockfile`/`--locked` |
| Running install scripts by default | The primary malware vector (§9 → `package-manager-supply-chain-and-workspaces`) | Default off + allowlist |
| Mutable published versions | Cache incoherence, hash breakage | Immutable + yank (§5.2 → `package-manager-registries-and-installation`) |
| Allowing new files on old releases | Retroactive poisoning | Time-bounded (§5.3 → `package-manager-registries-and-installation`) |
| Reusing deleted package names | Repojacking | Never reuse |
| Long-lived publish tokens | Harvest-now-use-later; worm fuel | Trusted publishing / OIDC (§7.1 → `package-manager-registries-and-installation`) |
| Trusting by org or `*` in trusted publishing | Looks secure, isn't | Full repo + branch/environment |
| Pinning CI actions by tag | Mutable reference; root cause of 2026 incidents | Pin by commit SHA |
| Requiring artifact download to learn dependencies | Resolution is now network-bound and slow | Metadata-only endpoints |
| Resolver that discards its derivation | Unfixably bad error messages | PubGrub-style incompatibility tracking |
| Unbounded backtracking with no diagnostics | Users experience a hang | Bound, and report what's thrashing |
| Non-deterministic lockfile serialization | Spurious diffs → unreviewed lockfiles | Sorted, stable output |
| Entangling resolve / fetch / install | No dry-run, no offline, untestable | Separate the stages (§0.1 → `package-manager-versioning-and-resolution`) |
| Non-atomic cache writes | Wedged caches users fix by `rm -rf` | Stage + verify + rename |
| Flat/hoisted layout with no strict option | Phantom dependencies | Offer an isolated linker |
| Letting a public index satisfy a private name | Dependency confusion | Scope-pinned registries |
| Treating SemVer as a guarantee | It's violated at measurable rates (§1.1 → `package-manager-versioning-and-resolution`) | Lockfile is truth; upgrades are explicit |
| Hand-editing a lockfile | Always a bug | Provide `overrides` (§10.3 → `package-manager-supply-chain-and-workspaces`) |
| No `why`/`explain` command | Users cannot debug their own tree | Ship it early |
| Delete-on-request unpublish | `left-pad` | Yank |

---

## §16. Contested Questions

**16.1 MVS vs. constraint solving.** §3.4 → `package-manager-versioning-and-resolution`. Determinism and simplicity versus automatic
patch adoption and expressiveness. Note this is genuinely unresolved: Go's ecosystem is
happy, and the rest of the world independently chose the other way.

**16.2 Should multiple versions coexist?** §6.3 → `package-manager-registries-and-installation`. Compatibility and resolvability versus
duplication and singleton bugs. Language runtime capability largely decides this for you.

**16.3 Hoisted vs. isolated vs. PnP.** §6.2 → `package-manager-registries-and-installation`. Compatibility versus correctness. The
phantom-dependency argument is the strongest technical case for strictness; the volume of
postinstall scripts that assume a hoisted shape is the strongest case against.

**16.4 Lockfiles for libraries.** §4.3 → `package-manager-versioning-and-resolution`.

**16.5 One standard lockfile format vs. per-tool formats.** §4.4 → `package-manager-versioning-and-resolution`. The Python experience
suggests standard-as-interchange is achievable, standard-as-canonical is not, once
competing formats have shipped.

**16.6 Is SemVer worth it?** §1.1 → `package-manager-versioning-and-resolution`. The empirical violation rates are not in dispute; what's
disputed is whether an imperfect declared intent beats no signal at all. (Most people who
say "SemVer doesn't work" still want maintainers to use it.)

**16.7 Should the package manager also be the build tool?** Cargo and Bun say yes
(integration, one config, coherent caching). npm/pip historically say no (separation of
concerns, competing build tools can innovate). Integration wins on UX and loses on
flexibility; both camps ship successful tools.

**16.8 Cooldowns: safety vs. patch latency.** §8.4 → `package-manager-supply-chain-and-workspaces`. The 8-in-10 prevention figure is
striking; the counter is that a cooldown also delays the fix for the *next* incident.
Nobody has a clean answer to "how do you expedite genuine security patches through a
cooldown" that doesn't reintroduce the attack surface.

**16.9 Vendoring.** Vendored dependencies give you total control, auditability, and
immunity to registry outages and takedowns — at the cost of enormous repos and manual
security updates. Go supports it first-class; most ecosystems treat it as a last resort.
Both positions are held by serious organizations.

---

## §17. Currency Snapshot — verified August 2026

| Thing | Status as of Aug 2026 | Decay risk |
|---|---|---|
| **npm supply-chain threat** | **Shai-Hulud worm family, Sept 2025 – Aug 2026.** Latest: **"ChainDrop"/Mini Shai-Hulud, 4 Aug 2026** — `keyv`, `flat-cache`, `cache-manager`, **400+ packages, 2,234 artifacts, ~2B monthly installs**, obfuscated Bun payload via npm `preinstall`, harvesting npm/GitHub/AWS/Kubernetes/Vault credentials. Waves in Sept 2025, Nov 2025 (v2, preinstall), Apr 2026 ("Third Coming", "Mini"), May 2026 (TeamPCP) | **Very high** |
| **npm remediation** | Mandatory 2FA for publishing, **legacy never-expiring tokens revoked**, granular short-expiry tokens, trusted publishing GA. 500+ packages removed in the Sept 2025 response | Medium |
| **PyPI incidents** | **LiteLLM 1.82.7/1.82.8 (24 Mar 2026, ~95M monthly downloads) and telnyx 4.87.1/4.87.2 (27 Mar)** — TeamPCP campaign originating from a **compromised Trivy GitHub Action** via a mutable reference. LiteLLM used a `.pth` file for import-time execution. PyPI quarantined the project | Medium |
| **PyPI release immutability** | ⚠️ **Since 8 July 2026, PyPI rejects new files on releases older than 14 days.** Analysis showed only 56 of the top 15,000 projects would be affected | Low |
| **PyPI attestations** | **PEP 740** Final since 2024; auto-generated by `pypa/gh-action-pypi-publish` v1.11.0+ with trusted publishing. **>132,360 packages carried attestations as of March 2026** | Medium |
| **Trusted publishing** | PyPI (2023), npm (2025), crates.io (GA). **PEP 807** proposes standardizing it for any Python index | Medium |
| **Cooldowns** | **pip 26.1 (26 April 2026) added `--uploaded-prior-to`**; uv `--exclude-newer`; pnpm `minimum-release-age`. Cited research: a **7-day cooldown would have prevented 8 of 10 analyzed attacks** | Medium |
| **PEP 751 / pylock.toml** | Accepted March/April 2025. Producers: uv ≥0.6.15, pip ≥25.1, PDM ≥2.24. **pip 26.1 added experimental `pip install -r pylock.toml`.** Both sides still **experimental**; install side lacks extras/dependency-group support. **uv keeps `uv.lock` as native; Poetry had not shipped support as of April 2026** | Medium |
| **pip** | **26.1** (April 2026): cooldowns, pylock install, 2020-resolver fixes, **dropped Python 3.9** | Medium |
| **PubGrub** | Powers Dart pub, uv, Poetry (Mixology), Bundler; the Rust `pubgrub` crate is the **designated replacement for Cargo's solver** | Medium |
| **JS package managers** | npm 11.x, Yarn 4.x (Berry), pnpm 10.x, **Bun 1.3**. **Bun added a pnpm-style `--linker isolated`** storing packages under `node_modules/.bun/`; hoisted remains its default and existing projects are unchanged | Medium |
| **crates.io provenance** | Trusted publishing GA; **Sigstore signing/provenance (RFC 3403) still at proposal stage** | Medium |
| **Go** | MVS unchanged; `proxy.golang.org` + `sum.golang.org` remain the strongest integrity story. ⚠️ Research notes immutability means **malicious module versions persist in the proxy cache even after the source repo is removed** | Low |
| **Malware volume** | ReversingLabs: **+73% YoY** malicious open-source packages, npm ~90% of open-source malware. Sonatype: 512,847 malicious packages in a year (+156%) | Annual |
| **EU CRA** | Vulnerability/incident **reporting obligations begin 11 Sept 2026**; full application 11 Dec 2027. CISA requires machine-readable SBOMs (SPDX/CycloneDX) | **Imminent** |

**Goes stale fastest:** npm attack campaigns (a new wave roughly every two months through
2026); Python packaging PEP adoption; JS package-manager versions and benchmarks.
**Essentially never stale:** §1.1 → `package-manager-versioning-and-resolution` (SemVer's empirical reality), §3.1–§3.3 → `package-manager-versioning-and-resolution` (resolution
theory), §4 → `package-manager-versioning-and-resolution` (lockfile design), §5.2 → `package-manager-registries-and-installation` (immutability), §6.2 → `package-manager-registries-and-installation` (layout trade-offs), §9.1 → `package-manager-supply-chain-and-workspaces`
(install-time execution), §15 (anti-patterns).

---

## §18. The Canon

### 18.1 Foundational writing

| Author | Work | Why |
|---|---|---|
| **Natalie Weizenbaum** | *PubGrub: Next-Generation Version Solving* (2018) | The algorithm now in Dart, uv, Poetry, Bundler, and slated for Cargo. Read the blog post *and* `dart-lang/pub/doc/solver.md` |
| **Russ Cox** | *Go & Versioning* series — esp. *Minimal Version Selection*, *The Principles of Versioning in Go*, ***Version SAT*** | The best-argued minority position in the field, plus the clearest statement of why the problem is NP-complete |
| **Di Cosmo, Mancinelli, Vouillon et al.** | The **EDOS** work; *Dependency solving: a separate concern in component evolution management* | The original NP-completeness proof and the "dependency solving is a separate concern" framing |
| **Hynek Schlawack** | *Semantic Versioning Will Not Save You* | The strongest, most-cited critique of SemVer-as-guarantee |
| **Hyrum Wright** | Hyrum's Law | One sentence that explains why every compatibility scheme leaks |
| **Winters, Manshreck, Wright** | *Software Engineering at Google* (the versioning chapter) | The extended argument against SemVer, and the "live at HEAD" alternative |
| **Andrew Nesbitt** | `nesbitt.io` — *Dependency Resolution Methods*, package-management reading lists; **ecosyste.ms** | The best single index of how each ecosystem actually resolves, and cross-ecosystem data |
| **Eelco Dolstra** | The Nix thesis, *The Purely Functional Software Deployment Model* | The most rigorous rethinking of what a package manager is |
| **Pinckney et al.** | *PacSolve* / *MaxNPM* | Research on customizable resolution objectives beyond "any valid solution" |

### 18.2 Primary sources

- **Specs**: `semver.org`; **PEP 440** (versions), **PEP 508** (dependency specifiers),
  **PEP 517/518/621** (build/metadata), **PEP 658/714** (metadata-only fetches),
  **PEP 700** (upload timestamps), **PEP 740** (attestations), **PEP 751** (pylock),
  **PEP 807** (trusted publishing), and the canonical `pylock.toml` spec on the **PyPA
  specs page** (the PEP is explicitly a historical document).
- **Ecosystem docs**: `go.dev/ref/mod` (the best-written package-manager reference in
  existence, full stop); the **Cargo Book**; **npm docs** on provenance and trusted
  publishing; the **pnpm** docs on the store and linker; `docs.rs/pubgrub`.
- **Security**: **SLSA** (`slsa.dev`), **Sigstore** (`sigstore.dev` and its blog),
  **in-toto**, **OSV** (`osv.dev` — the interoperable advisory format), **OpenSSF
  Scorecard**, and the OpenSSF **Securing Software Repositories WG**
  (`repos.openssf.org`) — whose *Build Provenance for All Package Registries* guide is the
  implementation manual if you're adding provenance to a registry.
- **Incident reporting** (for how attacks actually work): Microsoft Threat Intelligence,
  Unit 42, JFrog Security Research, Socket, ReversingLabs, Datadog Security Labs,
  Sonatype, Aikido. These are vendor blogs with commercial incentives — cross-read them,
  but they are where the technical detail lives.
- **PyPI blog** (`blog.pypi.org`) and **discuss.python.org/c/packaging** — packaging policy
  is decided in public there; **GitHub Changelog** and the **npm blog** for the JS side.

---

## §19. Quick Reference

### 19.1 If you're building one, in order
1. **Version type + comparison + range semantics.** Test the prerelease edge cases first.
2. **Manifest format**, with a format-version field.
3. **Resolver** — pure function, PubGrub unless you have a reason, derivation retained for
   errors.
4. **Lockfile** — hashes, deterministic serialization, marker-aware, manifest-linked.
5. **Content-addressed cache** with atomic writes.
6. **Linker**, with a strict mode.
7. **`--frozen`/`ci` mode.** Before you ship anything else.
8. **Registry API**: metadata separate from artifacts, immutable, timestamped, paginated.
9. **Publishing**: trusted publishing from day one; never ship long-lived tokens.
10. **Provenance** generated by default.
11. **No install scripts by default.**
12. **`why`, `--dry-run`, `--json`, and good errors.**

### 19.2 Diagnostic first moves
| Symptom | Look at |
|---|---|
| "Works locally, fails in CI" | Is CI resolving instead of using the lockfile? Platform markers? |
| Resolution hangs | Which package is being backtracked; add a constraint; check metadata endpoint |
| Integrity hash mismatch | Registry served different bytes, a mirror, or a mutable release |
| "Cannot find module X" but it's installed | Phantom dependency, or hoisting/linker mismatch |
| Two versions of the same type | Semver-incompatible duplicate in the graph (`cargo tree -d`, `npm ls`) |
| Install suddenly slow | Cache invalidated, metadata endpoint changed, or a new sdist-only dependency |
| Unexpected package in the tree | `why`/`ls`/`mod why` |
| Compromise suspected | Check upload timestamps, provenance/attestation, and whether it published outside normal CI |

### 19.3 Numbers worth knowing
- Dependency resolution is **NP-complete** (Di Cosmo et al., 2005).
- **~20%** of non-major Maven upgrades contained breaking changes; **~43%** of yanked
  crates.io releases were yanked for SemVer breakage.
- A **7-day cooldown** would reportedly have blocked **8 of 10** analyzed supply-chain
  attacks.
- Malicious open-source packages: **+73% YoY**; npm ≈ **90%** of open-source malware.
- August 2026 ChainDrop wave: **400+ packages, ~2B monthly installs, hours to spread**,
  ~5 min average detection latency.
- **>132,000** PyPI packages carried PEP 740 attestations by March 2026.
- PyPI's 14-day file rule affected only **56 of the top 15,000** projects.

---

## §20. Sources and Method

**Method.** Narrative (not systematic) review. Durable material — §1.1 → `package-manager-versioning-and-resolution` (SemVer's empirical
record), §3 → `package-manager-versioning-and-resolution` (resolution theory), §4 → `package-manager-versioning-and-resolution` (lockfile design), §5.2 → `package-manager-registries-and-installation` (immutability), §6 → `package-manager-registries-and-installation` (layout),
§9 → `package-manager-supply-chain-and-workspaces` (install-time execution), §15 (anti-patterns) — is synthesized from the primary
literature, ecosystem specifications, and the canonical writing in §18. Every
**time-sensitive** claim (incidents, versions, dates, adoption figures) was verified
against a primary or near-primary source in **August 2026** and is flagged in §17 with a
decay-risk rating. Where ecosystems have made different defensible choices, §16 presents
both cases rather than adjudicating.

**Search log** (August 2026): npm supply-chain attacks and Shai-Hulud/ChainDrop timeline ·
PEP 751 / pylock.toml adoption and pip 26.1 · PubGrub, SAT, and dependency-resolution
theory · Sigstore / SLSA / provenance adoption across registries · npm vs pnpm vs Yarn vs
Bun layouts and linkers · Go modules, MVS, and the checksum database · PyPI security
posture, PEP 740, trusted publishing, and the 14-day rule · SemVer compliance research and
Hyrum's Law.

**Primary and near-primary sources consulted (selected):**
- **PEPs and PyPA specs** — PEP 740, 751, 807; the `pylock.toml` specification on
  packaging.python.org; pip 26.1 release notes (Richard Si) and changelog
- **Microsoft Security Blog** — "ChainDrop supply chain compromise: anatomy of a
  self-propagating worm" (4 Aug 2026); **JFrog Security Research**; **Unit 42**;
  **Datadog Security Labs** (LiteLLM/telnyx TeamPCP campaign); **ReversingLabs**;
  **Socket**; **Sygnia**
- **GitHub Blog** — "Our plan for a more secure npm supply chain"; "Introducing npm package
  provenance"; **npm docs** on generating provenance statements
- **Sigstore** — project blog (npm provenance GA; cosign verification), community roadmap;
  **SLSA** specification (distributing provenance); **OpenSSF** Securing Software
  Repositories WG
- **PyPI Blog** — 2025 year in review; Help Net Security and contemporaneous reporting on
  the 14-day upload restriction (Seth Larson, Mike Fiedler)
- **go.dev/ref/mod**; **research.swtch.com** (Version SAT, vgo principles)
- **dart-lang/pub** solver documentation; **pubgrub-rs**; **DeepWiki** on uv's resolver
- **Bun documentation** (isolated installs); pnpm documentation
- **Andrew Nesbitt** (`nesbitt.io`) — dependency resolution methods; **ecosyste.ms**
  package-manager-resolvers reference
- Academic: Di Cosmo et al. (EDOS), Maven and Go SemVer-compliance studies, the crates.io
  yanked-releases study, arXiv work on hypergraph dependency resolution

**Confidence statement.** **High confidence** in §1–§7 → `package-manager-versioning-and-resolution`, `package-manager-registries-and-installation`, §9–§12 → `package-manager-supply-chain-and-workspaces`, `package-manager-ux-ecosystems-and-governance`, §15, §18–§19 — these rest
on specifications, primary ecosystem documentation, and peer-reviewed or widely-replicated
research. **High confidence** in §17's verified items as of the stated date.
**Moderate confidence** in §8 → `package-manager-supply-chain-and-workspaces`'s incident specifics and §11 → `package-manager-ux-ecosystems-and-governance`'s performance figures: the
attack narratives come from security-vendor research with commercial incentives and were
cross-read across multiple independent vendors (Microsoft, JFrog, Unit 42, Datadog, Socket,
ReversingLabs) where possible, but package counts and detection latencies are
vendor-measured and vary between reports; the package-manager benchmark figures are
single-machine and single-project and are flagged in place as directional only. The
"7-day cooldown would have prevented 8 of 10 attacks" figure is reported alongside the pip
26.1 release and is repeated here with its source named — it is a compelling result from a
single analysis, not an established measurement.
