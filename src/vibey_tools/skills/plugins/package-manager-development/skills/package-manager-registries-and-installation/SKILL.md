---
name: package-manager-registries-and-installation
description: "Use when building or operating a package registry or the install side of a client. Covers the registry API surface, immutability as the single most important property, mutable-release poisoning, namespacing and name allocation, the content-addressed store, the layout problem's four answers (flat, nested, isolated, PnP), multiple versions coexisting, runtime resolution as part of the design, and publishing and authentication — the evolution from API tokens to trusted publishing with OIDC, provenance and attestations, Sigstore, and SLSA."
---

# Package Manager Development: Registry Design, Cache, Layout, and Linking, Publishing and Authentication

> **Part 2 of 5** of the *Package Manager Development* reference (plugin `package-manager-development`), covering §5–§7. Sibling skills: `package-manager-versioning-and-resolution` (§0–§4), `package-manager-supply-chain-and-workspaces` (§8–§10), `package-manager-ux-ecosystems-and-governance` (§11–§14), `package-manager-reference` (§15–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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

## §5. Registry Design

### 5.1 The API surface

```
GET  /packages/{name}                  → all versions + metadata (the resolver's hot path)
GET  /packages/{name}/{version}        → one version's metadata
GET  /packages/{name}/{version}/dl     → the artifact (usually a CDN redirect)
POST /packages                         → publish (authenticated)
DELETE / POST /yank                    → yank/unyank (NOT delete — see 5.2)
GET  /search, /index, /changes         → discovery and incremental sync
```
**Design notes that matter at scale:**
- **Separate metadata from artifacts.** Metadata is small, hot, highly cacheable, and
  resolver-critical. Artifacts are large, cold, and belong on a CDN. Conflating them makes
  resolution slow (§3.6 → `package-manager-versioning-and-resolution`).
- **Support conditional requests and incremental sync** (`ETag`, `If-None-Match`, a change
  feed). Mirrors and CI caches depend on it.
- **Paginate and bound everything.** A package with 10,000 versions must not return a
  10 MB JSON blob on every resolution step.
- **Publish upload timestamps** (Python's PEP 700 does) — this is what makes cooldowns
  possible (§8.4 → `package-manager-supply-chain-and-workspaces`).

### 5.2 Immutability — the single most important registry policy

**[DURABLE] A published (name, version) must never change its bytes.** Consequences of
getting this wrong are severe and every ecosystem has learned it, usually the hard way:
- Caches everywhere become incoherent.
- Lockfile integrity hashes break for everyone.
- The `left-pad` incident (2016) — an unpublished package broke thousands of builds —
  established that **unpublishing must be tightly restricted**.

**The correct primitive is a *yank* (or *quarantine*), not a delete:**
- Yanked versions remain downloadable so existing lockfiles keep working.
- They are excluded from *new* resolutions.
- crates.io, PyPI (quarantine), and npm's deprecate/unpublish windows all converge on this.

**⚠️ And immutability has a security cost you must design for:** Go's `proxy.golang.org`
and `sum.golang.org` provide extremely strong reproducibility — but that same immutability
means **a malicious module version, once published and cached, persists and continues to be
served even after the source repository is removed.** Reproducibility and takedown are in
direct tension. Have a documented answer for it.

### 5.3 Mutable-release poisoning — a live design problem

Even with immutable versions, most registries historically allowed **adding new files to an
existing release** (e.g. a new wheel for a new Python version, months later). That's a
poisoning vector: a stolen token lets an attacker add a malicious artifact to a
long-trusted release.

**PyPI closed this in July 2026: new files are rejected on releases older than 14 days.**
The reasoning is instructive — the change was proposed during PEP 740 discussions in
January 2024, stalled, and was revived by the **March 2026 LiteLLM and Telnyx
compromises**. Before shipping, PyPI measured the impact: of the top 15,000 projects, only
**56** had uploaded a Python 3.14-compatible wheel more than 14 days after the release
first appeared. Seth Larson's stated rationale is worth internalizing: it prevents releases
from entering "an indeterminate and confusing state of both compromised and not
compromised, where only a subset of files could be poisoned."

**[DURABLE] That's the template for registry policy changes: identify the vector, measure
the legitimate usage you'd break, publish the numbers, then change the default.**

### 5.4 Namespacing and name allocation

| Model | Example | Trade-off |
|---|---|---|
| Flat, first-come | npm (unscoped), PyPI, crates.io | Simple; **land-grab, typosquatting, permanent name exhaustion** |
| Scoped/namespaced | `@org/pkg` (npm), NuGet prefixes | Ties identity to an owner; reduces squatting |
| Domain-derived | **Go** (`github.com/user/mod`), Maven (reverse-DNS groupId) | Namespace is *inherited from an existing trust root*. Elegant; couples you to the host |
| Content-addressed | Nix, Guix | Names are labels, identity is a hash |

**[DURABLE] Go's and Maven's approach — deriving the namespace from a domain or repo you
already control — eliminates an entire class of problems** (squatting, name disputes,
ownership transfer ambiguity) at the cost of coupling package identity to a hosting
provider. If you're designing new, seriously consider it.

Whatever you choose, you need policy for: name similarity (§8.3 → `package-manager-supply-chain-and-workspaces`), abandoned packages,
ownership transfer, trademark disputes, and reuse of deleted names (**never reuse a name —
that's the "repojacking" attack**).

---

## §6. Cache, Layout, and Linking

### 6.1 The content-addressed store

**[DURABLE] The right shape for a package cache is a global, content-addressed store.**
```
~/.cache/pm/
  index/         metadata, keyed by (name, version), immutable → cacheable forever
  files/         file blobs keyed by content hash (sha256)
  packages/      package trees, assembled from file blobs
  tmp/           staging — assemble here, then atomically rename into place
```
Properties you get for free: deduplication across projects, integrity verification by
construction, safe concurrent access (a hash-named file either exists and is correct, or
doesn't exist), and trivial garbage collection.

**Write atomically**: download to `tmp/`, verify the hash, then `rename()` into place.
A partially-written cache entry that looks complete is the classic "wedged cache" bug that
users fix by deleting the whole cache and cursing your name.

**pnpm's contribution** was demonstrating how much this matters: a single content-addressed
store hard-linked into each project's `node_modules` means one copy of a given package
version on the whole machine, saving developers with many projects tens of gigabytes.

### 6.2 The layout problem — four answers

This is the JavaScript ecosystem's defining argument, and it generalizes.

| Layout | Mechanism | Ecosystem | Trade-off |
|---|---|---|---|
| **Nested** | Each package gets its own `node_modules` | npm v2 | Correct; enormous duplication; Windows path-length failures |
| **Flat / hoisted** | Everything flattened to the top, conflicts nested | npm v3+, Yarn Classic, Bun (default) | Compact, compatible; **allows phantom dependencies** (§6.3) |
| **Isolated / symlinked** | Content-addressed store + hardlinks + a symlink tree mirroring the true graph | **pnpm**, **Bun `--linker isolated`** | Strict — packages can only see what they declared; occasional postinstall scripts assume a hoisted shape and break |
| **No node_modules** | A `.pnp.cjs` map from import to zip archive | **Yarn Berry PnP** | Fastest, strictest, "zero installs"; requires runtime cooperation and breaks tools that stat the filesystem |

> **⚠️ GOTCHA — phantom dependencies are a correctness bug, not a style issue.** Under a
> hoisted layout, `require('lodash')` works even if you never declared lodash, because
> something else hoisted it to the top. Your code then breaks when that transitive
> dependency changes — a failure with no visible cause in your own manifest. Strict layouts
> exist entirely to make this impossible, and **that, not disk space, is their real
> argument.**

**[DURABLE] The generalizable lesson:** you're choosing between *the real dependency graph*
and *a flattened approximation that the runtime finds easier*. Flattening is faster and
more compatible; it is also lying to the program about what it can see. Ecosystems whose
runtime resolution is explicit (Python's `sys.path` per-venv, Cargo's compiler-passed
`--extern`, Go's import paths) never had this problem, because the layout was never the
lookup mechanism.

### 6.3 Multiple versions coexisting

If your runtime can load two versions of the same package simultaneously (npm, Cargo), the
resolver can escape most conflicts (§3.5 → `package-manager-versioning-and-resolution`) — at the cost of duplicated code, larger
artifacts, and **singleton bugs**. If it can't (Python, Java on one classpath), a conflict
is fatal and must be reported, which makes resolution failures far more common and your
error messages far more important.

Cargo's rule is a good middle: **semver-compatible versions are unified into one; semver-
incompatible versions coexist.** This maximizes deduplication while keeping the escape
hatch, and the "expected `foo::Type`, found `foo::Type`" error is the price.

### 6.4 Runtime resolution is part of your design

The package manager's job doesn't end at install; the runtime has to find the code.
- **Node**: directory walk up from the importer, looking for `node_modules` — the reason
  layout *is* resolution.
- **Python**: `sys.path`, one environment per virtualenv — flat, one version of anything.
- **Cargo/Rust**: the compiler is passed explicit `--extern` paths — no filesystem search
  at all, which is why Rust can have two versions of a crate without ambiguity.
- **Go**: import path includes the major version (`/v2`) — **semantic import versioning**,
  so two majors are literally different packages.
- **JVM**: classpath order; first match wins. The source of endless "jar hell."

**[DURABLE] If you're designing a new ecosystem, make runtime resolution explicit and
independent of directory layout.** It removes phantom dependencies, path-length limits,
and hoisting entirely.

---

## §7. Publishing and Authentication

### 7.1 The evolution, and where it landed

```
Gen 1  username + password                  → phishable, reused, no scoping
Gen 2  long-lived API token                 → phishable, exfiltratable, "harvest now use later"
Gen 3  token + 2FA on the account           → helps login, does NOT help a stolen CI token
Gen 4  TRUSTED PUBLISHING (OIDC)            → no long-lived credential exists at all  ★
       + provenance attestations            → and the artifact proves where it came from
```

**[DURABLE] Trusted publishing is the current best practice and the direction every major
registry has moved.** The mechanism:
1. The registry pre-registers a trust relationship: "GitHub Actions workflow
   `.github/workflows/release.yml` on repo `org/repo`, environment `release`, may publish
   package X."
2. At publish time, CI requests a short-lived **OIDC token** from its provider.
3. The registry validates the token's claims (repo, workflow, ref/environment) against the
   registration and issues a **short-lived, minimally-scoped** upload credential.
4. No long-lived secret is ever stored anywhere.

PyPI shipped this in April 2023; npm added it in response to Shai-Hulud; crates.io has it
GA. **PEP 807** proposes standardizing the mechanism so *any* Python index can implement
it, encapsulating PyPI's existing implementation.

**Its explicit security properties**, as PEP 807 states them: credentials are short-lived
and minimally scoped, limiting blast radius; automatic expiry means **attackers cannot
mount "harvest now, use later" campaigns**; and the upload is conceptually linked to the
CI identity authorized to perform it.

> **⚠️ GOTCHA — trusted publishing is only as good as its trust configuration.** Trust by
> *full repository*, not by org or wildcard. Trust by *branch or environment*, not by any
> ref. A trusted-publishing config that accepts any workflow on any branch is worse than a
> token, because it looks secure. The 2026 attacks specifically exploited this class of
> misconfiguration.

### 7.2 Provenance and attestations

**The vocabulary, precisely — people conflate these constantly:**
- **Provenance** = a *factual claim* about how an artifact was built (source repo, commit,
  builder, parameters). **On its own it has no integrity properties whatsoever.**
- **Attestation** = provenance wrapped in a *signed* envelope, so the claim has a
  cryptographically verifiable author.
- The dominant envelope is **DSSE** (Dead Simple Signing Envelope); the dominant payload
  format is an **in-toto statement** with a **SLSA provenance** predicate. "Attestation"
  in 2026 almost always means DSSE + in-toto.
- **SLSA** describes build integrity *levels*; **Sigstore** is the signing mechanism that
  makes the claims trustworthy rather than self-asserted text.

**Sigstore's keyless model** is why this became practical: instead of maintainers managing
long-lived signing keys (which historically nobody did well — see the PGP-on-PyPI
experience), you generate an **ephemeral keypair**, exchange a CI OIDC token with the
**Fulcio** CA for a short-lived X.509 certificate binding that key to the CI identity, sign,
publish the signature to the **Rekor** transparency log, and **throw the key away**. No key
management, and anyone can verify both the signature and the identity that made it.

**Registry state as of 2026:**
- **npm** — Sigstore-backed SLSA provenance, GA since 2023, generated by the npm CLI itself.
- **PyPI** — **PEP 740** digital attestations, Final in 2024, generated automatically by
  `pypa/gh-action-pypi-publish` v1.11.0+ when using trusted publishing. **Over 132,000
  PyPI packages carried attestations as of March 2026.**
- **crates.io** — trusted publishing is GA, but **Sigstore-based signing/provenance
  (RFC 3403) remains at the proposal stage**; integrity comes from elsewhere.
- **Go** — arguably the strongest *integrity* story of any ecosystem via `sum.golang.org`,
  but no build provenance; achieving higher SLSA levels goes through the build platform,
  not the registry.
- **Maven Central** — PGP signatures traditionally; Sigstore adoption is emerging and Java
  provenance is the least mature of the major ecosystems.
- **GitHub Artifact Attestations** provide a language-agnostic path (SLSA Build L2 by
  default, L3 with reusable workflows), which is how ecosystems without registry support
  get provenance at all.

**[DURABLE, and the sentence to remember] Provenance does not prove a package is safe. It
proves it came from the build pipeline its maintainers claim.** That is precisely enough to
detect the dominant 2025–26 attack pattern — a malicious version published from a stolen
token outside the project's normal CI — and precisely not enough to detect a maintainer who
was themselves compromised (§8.1 → `package-manager-supply-chain-and-workspaces`).
