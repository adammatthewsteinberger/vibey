---
name: package-manager-versioning-and-resolution
description: "Use when designing or debugging the core of a package manager: the anatomy every package manager shares (the router for the whole package-manager-development reference), semantic versioning and what it really promises, the version-scheme decision and constraint syntax, what belongs in a manifest vs a lockfile, dependency resolution stated formally (NP-complete), the algorithm families, PubGrub and why it won, MVS as the radical simplification, escape hatches when there is no solution, making resolution fast, and lockfile design — what it must contain, the properties that matter, whether libraries should commit lockfiles, and the Python standardization story."
---

# Package Manager Development: Versions, Manifests, Dependency Resolution, and Lockfiles

> **Part 1 of 5** of the *Package Manager Development* reference (plugin `package-manager-development`), covering §0–§4. Sibling skills: `package-manager-registries-and-installation` (§5–§7), `package-manager-supply-chain-and-workspaces` (§8–§10), `package-manager-ux-ecosystems-and-governance` (§11–§14), `package-manager-reference` (§15–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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

## §0. Routing

### 0.1 The anatomy — every package manager has these parts

```
┌──────────────────────────────────────────────────────────────────┐
│ MANIFEST         what the human wrote: deps + constraints        │  package.json, pyproject.toml,
│                  (+ metadata, scripts, workspaces)               │  Cargo.toml, go.mod
├──────────────────────────────────────────────────────────────────┤
│ RESOLVER         constraints + registry metadata → exact versions│  §3
│                  This is the hard part. It is NP-complete.       │
├──────────────────────────────────────────────────────────────────┤
│ LOCKFILE         the resolution, frozen, with integrity hashes   │  §4
├──────────────────────────────────────────────────────────────────┤
│ FETCHER          registry API → tarballs; retries, mirrors, auth │  §5, §7
├──────────────────────────────────────────────────────────────────┤
│ VERIFIER         hashes, signatures, attestations, policy        │  §8
├──────────────────────────────────────────────────────────────────┤
│ CACHE            content-addressed store; global, shared         │  §6
├──────────────────────────────────────────────────────────────────┤
│ LINKER           cache → project layout (copy/hardlink/symlink)  │  §6
├──────────────────────────────────────────────────────────────────┤
│ BUILDER          compile/build native code; run lifecycle scripts│  §9  ← the danger zone
├──────────────────────────────────────────────────────────────────┤
│ RUNTIME RESOLUTION  how the language finds a module at run time  │  §6.4
└──────────────────────────────────────────────────────────────────┘
```

**[DURABLE] These are separable, and separating them is the single best structural
decision you can make.** Resolution should be a pure function of (manifest, registry
metadata) with no I/O side effects, so it is testable, cacheable, and can run offline
against a snapshot. Installation should be a pure function of (lockfile, cache). Package
managers that entangle resolution with fetching and installation are the ones that can't
do `--dry-run`, can't do offline installs, can't produce deterministic lockfiles, and
can't be tested without a network.

### 0.2 The question router

| Asked about... | Go to |
|---|---|
| Version schemes, semver, constraint syntax, ranges | §1 |
| Manifest design, metadata, what to put in it | §2 |
| Resolution algorithms, SAT, PubGrub, MVS, error messages | §3 |
| Lockfiles, reproducibility, integrity hashes | §4 |
| Registry design, APIs, immutability, yanking, mirrors | §5 → `package-manager-registries-and-installation` |
| Caching, install layouts, hardlinks, hoisting, PnP | §6 → `package-manager-registries-and-installation` |
| Publishing, authentication, tokens, trusted publishing | §7 → `package-manager-registries-and-installation` |
| Supply-chain attacks, provenance, Sigstore, SLSA, policy | §8 → `package-manager-supply-chain-and-workspaces` |
| Lifecycle scripts, native builds, sandboxing | §9 → `package-manager-supply-chain-and-workspaces` |
| Workspaces, monorepos, path/git deps, overrides | §10 → `package-manager-supply-chain-and-workspaces` |
| Performance: parallelism, metadata, network | §11 → `package-manager-ux-ecosystems-and-governance` |
| UX: error messages, output, CLI design | §12 → `package-manager-ux-ecosystems-and-governance` |
| Ecosystem comparison table | §13 → `package-manager-ux-ecosystems-and-governance` |
| Governance, funding, deprecation, name squatting | §14 → `package-manager-ux-ecosystems-and-governance` |
| "Don't do this" | §15 → `package-manager-reference` |
| "Which approach is better?" | §16 → `package-manager-reference` (contested) |
| "Is this still current?" | §17 → `package-manager-reference` |
| Books, papers, people | §18 → `package-manager-reference` |

---

## §1. Versions and Constraints

### 1.1 Semantic versioning — what it promises and what it delivers

**SemVer** (`MAJOR.MINOR.PATCH[-prerelease][+build]`): MAJOR for breaking changes, MINOR
for backward-compatible features, PATCH for backward-compatible fixes.

**[CONTESTED, with unusually good empirical evidence.]** SemVer is a *social contract*
enforced by nothing, and the research consistently finds it is widely violated:
- A large Maven study found **~20% of non-major upgrades contained breaking changes**,
  though only ~8% of client programs were actually affected.
- Another Java study found a **majority of libraries had at least one syntactically
  breaking patch upgrade**.
- In Rust, a study of **yanked crates.io releases found "breaking SemVer" was the leading
  reason for yanking, at ~43%** — maintainers discovering *after publishing* that they'd
  broken the contract.
- **Hyrum's Law** is the underlying reason: *with a sufficient number of users of an API,
  all observable behaviours of your system will be depended on by somebody* — so even a
  bug fix is a breaking change for someone.

**The strongest critique** (Hynek Schlawack, and the *Software Engineering at Google*
argument) is that SemVer over-predicts breakage — consumers use a small fraction of any
API, so a "major" bump is usually harmless to any given caller — while simultaneously
under-predicting it, because "patch" changes break people via Hyrum's Law. Treating the
version number as a machine-checkable compatibility guarantee is the error; treating it as
a **statement of the author's intent** is correct and useful.

**Design implication for a package manager author:** don't build a system whose safety
depends on SemVer being honoured. Build one where (a) the lockfile is the source of truth,
(b) upgrades are an explicit, reviewable action, and (c) you have a mechanism (yank,
audit, cooldown) for when the contract is broken anyway.

### 1.2 The version scheme decision

| Scheme | Example | Used by | Notes |
|---|---|---|---|
| SemVer | `2.4.1-rc.1+build` | npm, Cargo, Go, most modern | Well-defined precedence; prerelease sorts *before* release |
| PEP 440 | `2!1.4.1rc1.post2.dev3` | Python | **Epochs**, `.postN`, `.devN`, local versions (`+local`). More expressive, harder to implement |
| Debian | `1:2.4.1-3ubuntu2~20.04` | apt | Epoch, upstream version, revision. Comparison rules are genuinely subtle (`~` sorts *before* empty) |
| RPM | `1:2.4.1-3.el9` | dnf/yum | Epoch:Version-Release; `rpmvercmp` |
| Maven | `1.4.1.RELEASE`, `1.4-SNAPSHOT` | Maven | Loose; qualifier ordering is famously surprising |
| CalVer | `2026.8.1` | Ubuntu, pip, some libs | No compatibility claim at all — arguably more honest |

> **⚠️ GOTCHA — prerelease precedence is where implementations disagree.** `1.0.0-alpha`
> < `1.0.0-alpha.1` < `1.0.0-alpha.beta` < `1.0.0-beta` < `1.0.0-rc.1` < `1.0.0`. And
> **prereleases must not satisfy a normal range unless explicitly opted into** — if
> `^1.0.0` matches `2.0.0-alpha.1`, you will ship an alpha to everyone. npm, Cargo, and
> pip all handle this specially, and every naive implementation gets it wrong.

> **⚠️ GOTCHA — version equality vs. normalization.** Is `1.0` the same as `1.0.0`? Is
> `1.0.0+build1` the same as `1.0.0+build2`? (SemVer says build metadata is ignored in
> precedence — so they compare equal, which means a registry must not allow both.) Is
> `1.0.0-RC1` the same as `1.0.0-rc1`? Decide, normalize on ingest, and store the
> normalized form. Ambiguity here becomes a cache-poisoning vector.

### 1.3 Constraint syntax

```
^1.2.3   caret     >=1.2.3 <2.0.0     (npm, Cargo)  ⚠️ For 0.x, ^0.2.3 means >=0.2.3 <0.3.0
~1.2.3   tilde     >=1.2.3 <1.3.0     (npm)         ⚠️ npm ~ and Cargo ~ differ subtly
~=1.2.3  compatible >=1.2.3 <1.3.0    (PEP 440)
1.2.*    wildcard
>=1.2,<2 range
=1.2.3   exact/pin
1.2.3    "1.2.3"   ← MEANS DIFFERENT THINGS: exact in npm, ^1.2.3 in Cargo, minimum in Go
*        any                          ⚠️ crates.io rejects wildcard deps on publish
```

**[DURABLE] Design the constraint language for the *reader*, not the writer.** Every
ecosystem that invented clever operators regrets it. The two decisions that matter:
1. **What does a bare version mean?** Exact, caret, or minimum. This is the highest-traffic
   syntax in your entire system and there is no consensus across ecosystems — pick,
   document loudly, and never change it.
2. **Are ranges allowed at all?** Go says no (§3.4). That single choice removes most of
   the resolver's complexity and most of its usefulness.

---

## §2. The Manifest

### 2.1 What belongs in it

| Field group | Contents | Notes |
|---|---|---|
| Identity | name, version, (namespace/scope) | Name rules are a security surface (§8.3 → `package-manager-supply-chain-and-workspaces`) |
| Dependencies | runtime, dev/test, build, optional, peer | The categories are the design |
| Metadata | description, license (SPDX!), authors, repository, homepage | `repository` powers provenance (§8.2 → `package-manager-supply-chain-and-workspaces`) |
| Constraints | language/runtime version, platform, architecture | |
| Entry points | main/exports/bin/scripts | |
| Build config | build system, features/extras, scripts | |
| Workspace | members, shared constraints | §10 → `package-manager-supply-chain-and-workspaces` |

**Dependency categories — get these right, they're hard to change:**
- **Runtime** — needed to run. Installed for consumers.
- **Dev** — needed to develop/test. **Not** installed transitively for consumers. Every
  ecosystem has these; the important rule is that a consumer must never pull a dependency's
  dev deps.
- **Build-time** — needed to compile (Cargo's `[build-dependencies]`, Python's
  `[build-system] requires`). Distinct from runtime because they may target a different
  platform in cross-compilation.
- **Optional / extras / features** — conditionally enabled. **This is where resolution
  complexity explodes**, because it turns one package into 2^N virtual packages.
- **Peer dependencies** — "I need the *host* to provide this, at this version, and we must
  share the same instance." Essential for plugin systems (a React component and the app
  must share one React). Notoriously confusing; npm auto-installed them in v3–v6, stopped,
  then resumed in v7.

> **⚠️ GOTCHA — the manifest is a public API.** Once published, the file format's
> semantics are frozen for every version anyone might install. Add fields; never repurpose
> them. Include a format-version field from version one. Every ecosystem that didn't has a
> painful compatibility story (`package.json`'s `exports` field rollout, `setup.py` →
> `pyproject.toml`).

### 2.2 Manifest vs. lockfile — the distinction that must never blur

```
MANIFEST                              LOCKFILE
written by humans                     generated by the tool
expresses INTENT ("^1.2")             expresses FACT ("1.4.7, sha256:...")
loose constraints                     exact versions + hashes + resolved URLs
hand-editable                         hand-editing is always a bug
committed                             committed for APPLICATIONS; see §4.3 for libraries
```
**[DURABLE] The manifest says what you'll accept; the lockfile says what you got.**
Package managers that conflate them (early `requirements.txt` usage, where people pinned
exact versions in the manifest because there was no lockfile) force users to choose
between reproducibility and expressible intent. Give them both.

---

## §3. Dependency Resolution — the hard part

### 3.1 The problem, formally

Given a root package's constraints and a universe of package versions each with their own
constraints, find an assignment of exactly one version per selected package such that every
constraint is satisfied and no unreachable package is selected.

**[DURABLE] This is NP-complete.** Di Cosmo et al. proved it in 2005 (the EDOS work) by
encoding 3SAT into Debian and RPM dependency constraints; Russ Cox's "Version SAT" restates
it, and it has been re-proven for other formulations since. The reduction is easy to see:
disjunction is encoded in the *changing dependencies across versions* of a package.

**Why it's tractable in practice anyway:** real dependency graphs are nothing like the
worst case. They're shallow-ish, mostly consistent, and heavily biased toward recent
versions. Every production resolver is an algorithm with terrible worst-case behaviour and
good typical behaviour — plus heuristics and a timeout.

**The canonical hard case, the diamond:**
```
        root
       /    \
   A ^1.0   B ^1.0
      |       |
   D ^1.0   D ^2.0        ← no version of D satisfies both. Now what?
```
The resolver must find a D that satisfies both, prove none exists, or use an escape hatch
(§3.5).

### 3.2 The algorithm families

| Family | How it works | Used by | Trade-off |
|---|---|---|---|
| **Backtracking / DFS** | Try highest version; on conflict, back up and try the next | pip (2020 resolver), Cargo, Swift PM | Simple; exponential worst case; **historically terrible error messages** |
| **Backtracking + forward checking / backjumping** | Prune early, jump past irrelevant choices | Molinillo (Bundler, CocoaPods — Bundler has since moved to PubGrub) | Better pruning, still heuristic |
| **Full SAT / CDCL** | Encode as boolean satisfiability, use a real solver | Composer, **libsolv** (dnf, Conda via libmamba), 0install | Complete and fast; explanations are hard; encoding is fiddly |
| **PubGrub (CDCL specialized for versions)** | Conflict-driven clause learning over version ranges, with derivation tracking | **Dart pub, uv, Poetry (Mixology), Bundler, and the designated replacement for Cargo's solver** | Fast *and* explains failures. The modern default |
| **ASP (Answer Set Programming)** | Declarative, with optimization objectives | **Spack** (via Clingo) | Handles multi-objective optimization (compilers, variants, targets) |
| **Pseudo-Boolean optimization** | SAT + an objective function | Research; some distro tooling | "Best" solution, not just any solution |
| **MVS (Minimal Version Selection)** | No search at all — take the max of the required minimums | **Go modules** | O(graph); trivially reproducible; no ranges |
| **Avoid the problem** | Allow multiple versions to coexist | npm (nesting), Nix/Guix (content-addressed store) | Turns resolution into a layout problem |

### 3.3 PubGrub — why it won

Natalie Weizenbaum designed PubGrub for Dart's `pub` in 2018. Its two contributions:

1. **CDCL over version ranges.** Instead of assigning boolean variables, it works with
   *incompatibilities* — sets of terms that cannot all be true. On conflict it derives a
   *new* incompatibility (clause learning), which prunes an entire region of the search
   space rather than just backing up one step.
2. **The derivation graph is the error message.** Because every incompatibility records
   why it was derived, a failure produces a human-readable proof:
   ```
   Because no versions of foo match >1.0.0 <2.0.0
     and foo 1.0.0 depends on bar ^2.0.0,
     every version of foo requires bar ^2.0.0.
   So, because myapp depends on both foo ^1.0.0 and bar ^3.0.0,
     version solving failed.
   ```
   **[DURABLE] This is the single biggest UX advance in package management in fifteen
   years.** Every prior resolver's failure mode was "could not find a compatible set,"
   which is useless. If you are building a resolver in 2026 and you do not produce an
   explanation, you are shipping a known-solved problem as a known bug.

The Rust `pubgrub` crate is generic over package type (including virtual packages),
version format, and version sets, and lets the caller control prioritization (highest-
versus lowest-version solving) and error rendering. **uv extends it with "forking"** —
splitting the resolution when environment markers (Python version, OS, architecture)
partition the solution space, producing a *universal* lockfile valid across platforms
rather than one lockfile per machine. That extension is the interesting part for anyone
building a cross-platform resolver.

### 3.4 MVS — the radical simplification

Russ Cox's argument for Go modules: most version selection algorithms are overcomplicated.
MVS:
- Modules declare **minimum required versions**, not ranges.
- The build list is: for each module in the graph, **the maximum of all the minimums**
  required by anything in the graph.
- One pass. No backtracking. No SAT. No solver. Deterministic by construction.

**[CONTESTED] MVS's trade-off is the whole argument.**
- *For*: builds are **high-fidelity** — adding a dependency cannot silently upgrade an
  unrelated one, and the result is identical today and in five years without a lockfile.
  It's a dozen lines of pseudocode. There is no resolution failure mode to debug.
- *Against*: you **do not get security patches automatically**. If your dependency requires
  `logrus v1.2.0` and v1.2.1 fixes a CVE, MVS keeps you on v1.2.0 until someone explicitly
  bumps it. Proponents call that a feature (upgrades are deliberate); critics call it a
  security liability at ecosystem scale.
- Note the naming confusion, which appears even in reputable sources: MVS selects the
  **maximum of the required minimums**, which people describe both as "the minimum version
  that satisfies all requirements" and "the highest required version." Both descriptions
  are of the same operation, and the ambiguity causes real misunderstanding.

Go's ecosystem also learned an important lesson the hard way: the original design computed
MVS from a root `go.mod` listing only *direct* dependencies, which meant the file said
`v1.2.3` while the build used `v1.5.0`. Users were endlessly confused and security scanners
couldn't read it statically. **`go mod tidy` and `go get` were changed to write the full
resolved requirement list into the root `go.mod`.** *Lesson: if the manifest doesn't state
the actual answer, tooling and humans will both get it wrong.*

### 3.5 Escape hatches — what to do when there's no solution

| Strategy | Mechanism | Used by |
|---|---|---|
| **Allow multiple versions** | Install both, isolate them | npm (nested `node_modules`), Cargo (multiple semver-major versions coexist), Nix |
| **Version mediation** | Pick one by a rule (nearest-wins, first-declared) | **Maven** — "nearest definition wins," which is deterministic but often surprising |
| **Overrides / resolutions** | User forcibly pins a transitive dep | npm `overrides`, Yarn `resolutions`, pnpm `overrides`, Cargo `[patch]` |
| **Fail loudly** | Report the conflict, make the human decide | pip, Cargo (for same-major conflicts), Bundler |

**[DURABLE] "Allow multiple versions" is not free.** It works for pure, self-contained
libraries. It breaks catastrophically for anything with a *singleton*: a global registry, a
type identity that must be shared, a native library that can only be loaded once, a
database connection pool. That's exactly what peer dependencies exist to express, and why
Rust distinguishes semver-compatible (unified) from semver-incompatible (coexisting) —
and still hits "two versions of the same type, and they're not the same type" errors.

### 3.6 Making resolution fast

The dominant cost is almost never the solver — **it's fetching metadata**. Design for this:

1. **Publish dependency metadata separately from the artifact.** PyPI's historic failure to
   provide dependency metadata via a plain API meant Poetry and pip had to *download and
   unpack sdists* just to learn their dependencies. This is the single largest reason
   Python resolution was slow for a decade. (PEP 658/714 metadata-only fetches fixed much
   of it; uv's speed comes substantially from exploiting them.)
2. **Serve a queryable index**, not one file per package that must be fetched serially.
   Cargo's move from a git index to a **sparse HTTP index** was a large real-world win.
3. **Cache metadata aggressively and immutably** (§5.2 → `package-manager-registries-and-installation` immutability makes this safe).
4. **Prefetch speculatively** — start downloading the versions you're likely to pick while
   still solving.
5. **Bound the search**: prioritize by (fewest versions remaining) then (highest version),
   deprioritize packages with huge version counts, and have a hard timeout with a *useful*
   message rather than an infinite spin.

> **⚠️ GOTCHA — the "backtracking forever" experience.** pip's resolver visibly downloading
> dozens of versions of one package is the canonical user-facing symptom of an unbounded
> backtracking search with expensive metadata access. If your resolver can do this, your
> users will experience it as a hang. Detect it, report which package is thrashing, and
> suggest a narrower constraint.

---

## §4. Lockfiles

### 4.1 What a lockfile must contain

```
For each resolved package:
  name, exact version
  INTEGRITY HASH of the artifact           ← the security property
  resolved source (registry URL / git rev / path)
  its dependencies (the resolved edges, not the constraints)
  platform/marker applicability            ← for universal lockfiles
Plus:
  lockfile format version
  a hash of the MANIFEST it was derived from   ← detects "manifest changed, lock is stale"
```

**[DURABLE] The integrity hash is the point.** Without it, a lockfile pins versions but not
*bytes*, and a registry that serves different content for the same version (or a
man-in-the-middle, or a compromised mirror) defeats it entirely. Hash the artifact, and
prefer hashing the *content* rather than the archive where you can, so recompression doesn't
break it.

### 4.2 Design properties that matter

1. **Deterministic serialization.** Sorted keys, stable ordering, consistent formatting.
   A lockfile that produces spurious diffs will not be reviewed, and an unreviewed lockfile
   is a supply-chain hole. (npm's `package-lock.json` reaching 50,000+ lines for large
   projects with noisy diffs is the widely-cited failure of this property.)
2. **Merge-friendliness.** Lockfiles conflict constantly in team workflows. Either make the
   format merge cleanly (flat, per-package, sorted) or ship a merge driver. Most ecosystems
   did the second, late, after years of pain.
3. **Cross-platform validity.** A lockfile generated on macOS must install correctly on
   Linux CI. This requires recording platform-conditional entries rather than only what the
   generating machine needed. uv's universal resolution and Cargo's approach do this;
   `pip freeze` never did, which is why it isn't a lockfile.
4. **Verifiability offline.** `npm ci`, `pip install -r pylock.toml`, `cargo build
   --locked`, `pnpm install --frozen-lockfile` — every ecosystem eventually adds a mode
   that says *install exactly this, fail if the manifest and lock disagree, never resolve*.
   **Build this mode from day one; it is what CI should always use.**

### 4.3 Should libraries commit lockfiles?

**[CONTESTED, and the consensus is more nuanced than the folklore.]**
- The classic rule: *applications commit lockfiles; libraries don't*, because a library's
  lockfile is ignored by consumers and pinning it hides the fact that your declared ranges
  are broken.
- The counter-position, now common: **commit it anyway**, because it makes *your own CI*
  reproducible and lets you bisect. Then add a *separate* CI job that resolves fresh
  (and ideally one that resolves *minimum* versions) to catch range breakage.
- Cargo shipped the modern answer: commit `Cargo.lock` for everything, and it is simply
  ignored when the crate is consumed as a dependency. That removes the trade-off.

### 4.4 The Python standardization story — a case study in lockfile politics

Worth knowing because it illustrates how hard "one lockfile format" is:
- The quest began in **2019**. **PEP 665 was rejected** for being too restrictive (it
  excluded sdists). **PEP 751 went through three complete rewrites** and 1,800+ forum posts
  before acceptance in **March/April 2025**, defining `pylock.toml`.
- Adoption moved fast on the *export* side: pip ≥25.1 (`pip lock`, April 2025), PDM ≥2.24,
  uv ≥0.6.15 all write it. **pip 26.1 (April 2026) added experimental `pip install -r
  pylock.toml`** on the install side.
- **But the flagship tool declined to adopt it as its native format.** uv's author stated
  plainly that `pylock.toml` files "are not sufficient to replace `uv.lock`" — the key
  limitation being that pylock records a fixed marker per package rather than a *graph* of
  dependencies, so it can't express installing an arbitrary subset of the graph. Poetry had
  not shipped support as of April 2026.
- **The durable lesson**: tools with a native lockfile treat a standard format as an
  *export target*, not a replacement, because per-tool lockfiles capture information the
  standard doesn't. Standardizing an interchange format is achievable; standardizing the
  *canonical* format when competing formats are already entrenched is much harder.

> **⚠️ GOTCHA — `pip freeze` and `requirements.txt` are not lockfiles.** No hashes by
> default, no platform markers, no distinction between direct and transitive, no manifest
> linkage. `pip install --require-hashes` gets you partway. Do not design a new system with
> this shape.
