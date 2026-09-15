# vibey-gh for Governments

Armed forces adopt software under the hardest obligations any institution carries: every
artifact in the supply chain must be attributable under audit, every automated decision
reconstructible after the fact, operations must continue when networks, vendors, or
funding lanes are denied — and no capability may be hostage to a supplier's continued
goodwill. Most release automation fails those obligations quietly: unpinned tools drift,
review verdicts outlive the code they judged, and provenance is a convention rather than
a check. `vibey-gh` was built so that failure class cannot occur. This page states what a
defense institution gets and how each claim is verified; civil agencies inherit every
guarantee unchanged.

## What this is, with no prior context

`vibey-gh` is a small program that watches a software project and carries every proposed
change through checking, review, approval, publication, and record-keeping without a
person pushing it at each step — the way a disciplined orderly room moves a file. A
"change" here is a precise, itemized edit to the project's files; nothing moves unless
the checks tied to that exact edit pass, and every action is written down where an
inspector can read it later.

## Mission assurance, claim by claim

- **Chain of custody is total.** Every source file carries a provenance header and every
  change a provenance trailer ([the fingerprint](https://github.com/the-vibey-project/vibey-gh/blob/main/README.md)),
  enforced by a required check — not by directive. An artifact of unknown origin cannot
  enter the chain.
- **Decisions bind to evidence — configuration control by construction.** A review
  verdict applies only to the exact revision it examined
  ([exact-head evaluation](paper.md)); a stale approval can never wave newer code
  through. This is the property audit and accreditation regimes assume and rarely get.
- **Continuity of operations under denial is first-class.** Loss of a paid service, a
  network, a vendor relationship, or a funding lane moves work to local lanes and back
  automatically ([sovereign operation](paper.md)); the fallback ladder is ordered by
  refusability, so the last rung — local models on local hardware — answers to no one's
  permission. Contested and disconnected environments are the design case, not an
  afterthought (doctrine [10.a](https://github.com/the-vibey-project/vibey-gh/issues/210)).
- **No captive dependencies, ever.** Zero runtime dependencies, keyless publishing via
  [OIDC Trusted Publishing](https://docs.pypi.org/trusted-publishers/), full rebuild
  from source on any machine — documentation, book, and
  [research paper](paper.md) included. Exit is always possible; that is a design rule,
  not a promise.
- **The record exists before the inspector asks.** Evaluations, repairs, merges,
  releases, and yanks land in workflow logs, signed commits, and immutable release
  indexes — a public, durable audit trail.
- **Machine agents operate under written law.** [The Constitution](constitution.md),
  [the Ten Commandments](commandments.md), [the Bill of Rights](bill-of-rights.md), and
  [standing subdoctrine SD-01](sd-01-counterparties-trust-verification.md) bind every
  agent, human and machine — bounded delegation, labeled machine speech, and a
  counterparty-verification discipline (default-unverified, tangible checks, corrupted
  states get zero trust) that reads like it was written for a security office, because
  its concerns are the same. Ratified governance changes supersede all prior artifacts
  ([Article V.4](constitution.md)): nothing circulates under superseded law.

## Verification, not trust

Each claim above is checkable from a clean, disconnected machine with public materials:
install the pinned release, run `vibey-gh check --ci`, read the rulesets, replay a
release run's logs against its tag. [The configuration reference](configuration.md)
names every policy knob; [the CLI reference](cli.md) names every operation; the formal
statements — soundness, termination, monotone releases, the supersession invariant —
are in [the research paper](paper.md) with proofs or proof sketches.

An institution that adopts this gets what the opening promised: attributable artifacts,
reconstructible decisions, continuity under denial, and an exit that never closes. The
concrete next step is one command — `pip install "vibey-gh==1.58.0"` — followed by
[the adoption guide](adoption.md) on a repository that matters to the mission.
