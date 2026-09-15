# The glossary bridge

Every project word in plain language, with a link to the page that carries
the depth. Read it top to bottom once; after that it's a lookup table.

| Word | Plain meaning | Full depth |
|---|---|---|
| **provenance / fingerprint** | A signature line stamped into files and commits proving what tooling produced them, checked on every push. | [Security](../security.md) |
| **trailer** | The `Made-With:` line the commit hook appends to every commit message — provenance for changes in files that can't carry a header. | [Security](../security.md) |
| **the gate** | A required status check called `PR automation / gate`. A pull request cannot merge until the automation certifies its exact latest commit. | [Workflows](../workflows.md) |
| **exact-head** | Every decision is tied to the precise commit it evaluated — a result computed for an older commit can never approve a newer one. | [Architecture](../architecture.md) |
| **merge train** | The scheduled process that merges every pull request that is green, conflict-free, and reviewed — one at a time, so merges never race. | [Workflows](../workflows.md) |
| **repair** | When review or scans find a problem, the automation attempts one bounded fix on a guarded branch and re-reviews — it never retries forever. | [Workflows](../workflows.md) |
| **promotion** | The automated pull request that carries `develop` into `main` when their content differs, applying the derived version bump. | [Releases](../releases.md) |
| **derived version** | Nobody remembers version numbers: the bump is computed from what actually changed since `main`. | [Releases](../releases.md) |
| **dual channels** | Two publishing lanes — `develop` → TestPyPI + a preview docs site, `main` → PyPI + the production docs site — so a preview can never be mistaken for a release. | [Releases](../releases.md) |
| **Trusted Publishing** | Publishing to PyPI via GitHub's identity (OIDC) instead of a stored password token — there is no long-lived secret to leak. | [Releases](../releases.md) |
| **doctor** | The offline preflight: reads your configuration and predicts whether the automation will actually work, before anything runs. | [Adoption](../adoption.md) |
| **local fallback** | A local AI model on your own machine that reviews a pull request only when the paid reviewer returned no verdict at all — a billing problem stops being a hard stop. | [Threat model](../threat-model.md) |
| **trusted_only** | The rule that keeps pull requests from strangers' forks off your own machine's runner. | [Threat model](../threat-model.md) |

Comfortable with these? You've graduated: [Adoption](../adoption.md) onward
is the engineering reference, and it assumes exactly this vocabulary.

---

**The short version, again**: twelve words stand between you and the
engineering docs, and now you have all twelve. **Your next step**:
[Adoption](../adoption.md) — the full map, in the vocabulary you just
learned.
