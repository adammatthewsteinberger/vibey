# Theory of operation

This page is the formal statement of what the automation guarantees and why the
guarantees hold — the material the rest of the documentation applies. It is written for
the reader who wants the invariants, the state machine, and the termination argument,
with the empirical failures that motivated each.

## The exact-head invariant

Let a pull request's history be a sequence of heads `h₀, h₁, …, hₙ` (commits, each
replacing the last). Every artifact the automation produces — a scan result, a review
verdict, a gate conclusion — is a pair `(claim, hᵢ)`: the claim is *about* exactly one
head.

**Invariant 1 (exact-head).** A claim `(c, hᵢ)` never participates in a decision about
`hⱼ` for `j ≠ i`.

This is stronger than "checks must pass": GitHub's own status model attaches checks to
commits, but consumers routinely relax it (branch-level approvals, stale-review
tolerance). Here the gate check-run is *published to* the evaluated SHA, the review
prompt pins the head it audits, and the merge train re-reads the head at merge time.
The empirical case for the strictness is issue #161: a verdict recorded for `hᵢ` was
allowed to stand in for `hᵢ₊₁` during exhaustion accounting, and a fully repaired pull
request was escalated as unrepairable. The fix (#163) restored the invariant: an
unreviewed head always receives its own review.

## The evaluation state machine

Evaluation is a pure function `E(head, checks, stored) → state` where `stored` is the
persisted automation state (attempts `a`, last-reviewed SHA `r`, verdict `v`, heals
`k`). The reachable states:

```
pending → review → repair → blocked
   ↓         ↓        ↑↓
 ready ←── ready    (new head)
```

- `pending` — required checks incomplete; no claim is made.
- `review` — checks green and `r ≠ head`: the head has no verdict of its own.
- `ready` — checks green, `r = head`, `v = pass`.
- `repair` — `r = head`, `v = fail`, and `a < A` (the attempt budget): one bounded
  repair is dispatched, producing a new head and incrementing `a`.
- `blocked` — a terminal operator state: `v = fail` with `a ≥ A`, or failing checks
  with the scan budget spent.

**Invariant 2 (budget placement).** The budget guard `a ≥ A` is evaluated only at the
point another *repair* would be spent — never before the `r ≠ head` test. Reviews are
free; repairs are counted. This ordering is precisely what #163 corrected, and the
regression test pins it.

**Termination.** Heads advance only through repairs (contributor pushes reset the
lineage by definition — they are new work, not automation output). Repairs are bounded
by `A`, and `A` is refillable only by the explicit operator action `self-heal`, itself
bounded by `max_self_heals`. Hence the automation's own loop is finite: at most
`A × (1 + max_self_heals)` repairs per lineage, after which every path lands in
`ready` or `blocked` — both terminal absent human input.

## The trust boundary model

Three principals act, with strictly separated capabilities:

| Principal | May | May never |
|---|---|---|
| `GITHUB_TOKEN` (per-job) | publish check runs, read the repo | merge, push to permanent branches |
| `ANTHROPIC_API_KEY` (review/repair) | read the exact head, propose commits on guarded branches | merge, alter settings, touch permanent branches |
| `AUTOMERGE_TOKEN` (train) | merge ready pull requests, push the promotion bump | review its own work — it consumes verdicts, never produces them |

The separation is load-bearing: the principal that *judges* (review) cannot *act*
(merge), and the principal that acts cannot judge. A fork pull request is data to all
three — the `pull_request_target` execution model runs only base-branch code, and
`trusted_only` additionally keeps fork heads off self-hosted hardware (see
[Threat model](threat-model.md)).

## Release monotonicity

Published versions form a monotone sequence because the version is *derived*, not
remembered: `version(main ∪ Δ) ≥ version(main)`, with equality exactly when Δ contains
no shippable content — and the publish step treats an already-published version as a
no-op rather than an error. A deliberate bump already present in Δ is never compounded
(the "never double-bump" rule), which makes the derivation idempotent across repeated
promotions of the same content.

## References

- PEP 592 — *Adding "Yank" Support to the Simple API*: the design reasoning behind
  report-only supersession in [Releases](releases.md).
- PyPI *Trusted Publishers* documentation: the OIDC model that removes stored
  credentials from the publish path.
- GitHub *repository rulesets* and `pull_request_target` documentation: the
  enforcement primitives Invariants 1 and 2 compile down to.
- Issues #161/#163 in this repository: the recorded failure and fix that motivated
  Invariant 2's budget placement — kept as the empirical companion to this page.
