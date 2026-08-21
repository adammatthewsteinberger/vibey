# Runbook: production-fitness reconciliation — is the delivered code actually production-grade?

## Goal

A second kopf control loop, sibling to
[17](17-plan-drift-reconciliation.md), that continuously audits **what
the jobs produced** against its declared production budgets: latency,
memory, database behavior, cloud cost, artifact weight, dependency
health. Where 17 asks *"did the bots build what was planned?"*, this asks
*"is what they built fit to run in production?"* Both are real failures
and neither implies the other — code can match its plan exactly and still
allocate unboundedly, N+1 every request, and cost three times what it
should.

Runs in all five repos on the same reconcile machinery as 17, and vibey
dogfoods it on itself, since vibey is built by vibey.

## Why this one is not blocked on a Phase 0

17 cannot start until constraints carry machine-checkable predicates,
because they are prose today. **This loop does not have that problem**,
and the reason is already in the codebase:

```python
class NonFunctionalRequirement:
    """Planguage. 'fast' is not an NFR; a scale and a meter are."""

    nfr_id: str
    attribute: str
    scale: str
    meter: str
    must: str
    wish: str | None
    fit_criterion: str
```

Planguage already forces every NFR to name a **scale** (the unit), a
**meter** (how it is measured), a **must** (the threshold that fails),
and a **wish** (the target). That is a machine-checkable contract by
construction — the design decision that makes this workstream
tractable is one that was made long before it.

What is missing is smaller and concrete: a **meter registry** mapping
meter names to executable probes. A meter reading "measured by hand
during review" cannot be automated, and NFRs carrying one are `advisory`
— reported, never actioned. Building the registry is work item 1, not a
blocking research phase.

## The rule that keeps this from becoming a nuisance

**Act only on a breach or a regression. Never on "could be better."**

An always-on optimizer always finds something. Unbounded, it generates
infinite work, churns correct code, and trains everyone to ignore it.
So the loop acts in exactly two situations:

1. an NFR's `must` is breached, or
2. a measurement regressed against the project's recorded baseline
   beyond a stated tolerance.

Absolute-quality opinions — "this could use a better algorithm", "this
dependency is heavier than necessary" — are **recorded and never
actioned**. They are input to a human deciding to raise work, not work
the loop raises itself. A `wish` is a target to report progress against,
never a trigger.

The second rule: **the loop never applies an optimization.** A finding
becomes a repair ticket that goes through the normal BUILD → REVIEW path
with the full gate suite behind it. An optimizer that edits code directly
is an unreviewed second author, and performance work is exactly the kind
that silently trades correctness for speed.

## Fitness dimensions

| Dimension | Measured from | Typical finding |
|---|---|---|
| Latency / throughput | benchmark suite, NFR meters | a `must` breached; a regression past tolerance |
| Memory | peak RSS, allocation profiles | unbounded cache or buffer; growth across a run |
| Database | `pg_stat_statements`, `EXPLAIN` | N+1, sequential scan on a hot path, missing index, pool mis-sizing |
| Cloud cost / right-sizing | metrics-server vs declared requests | pods requesting 4x observed usage; over-provisioned PVCs; idle replicas |
| Artifact weight | image size, layer count, dep tree | image growth, a heavy transitive dependency, slow cold start |
| Concurrency | lock waits, serialization points | a global lock on a hot path |
| Dependency health | lockfile, upstream releases | abandoned or duplicated transitive deps (weight, not CVEs — `pip-audit` owns security) |
| Delivery economics | ledger `cost_usd` per work item | spend per unit of delivered work drifting up |

**Right-sizing is the most k8s-native of these** and the natural first
deliverable: comparing a Deployment's declared `resources.requests`
against observed usage is something the operator can do with data the
cluster already produces, and the finding is directly actionable — it is
a values change, not a code change. vibey's own chart is the first
subject; its worker requests `250m` CPU and `512Mi` today, chosen by
judgement rather than by measurement.

## Design

1. **Pure evaluator in `domain/`.** Given NFRs, a baseline, and a
   measurement set, return findings. No I/O, stdlib only, property-tested
   — identical to 17's detector and subject to the same import-linter
   contract.
2. **Meter registry in `infrastructure/`.** Named probes, each returning
   a value on the NFR's declared scale. An NFR whose meter has no
   registered probe is `advisory` and says so out loud, rather than
   silently passing.
3. **Cheap timer, budgeted probes.** The kopf timer reads cached
   measurements and evaluates. Anything expensive — a profile, a load
   test, a full benchmark suite — is a **budgeted job the loop enqueues**,
   never work the timer performs inline. A fitness loop that itself burns
   CPU every 30 seconds has failed on its own terms.
4. **Baselines are recorded, append-only.** A baseline is a ledger
   artifact per project, so "regression" has a definition and a history.
   Re-baselining is an explicit, recorded act — never an automatic
   overwrite, or the loop will happily ratchet toward slower over time.
5. **Statistical honesty.** Measurements on shared runners are noisy.
   A regression requires N samples and a stated confidence, not one bad
   reading. This is the difference between a useful gate and a flaky one.
6. **Same action ladder as 17**, with the ceiling in `spec.fitnessPolicy`:
   record → raise a repair ticket → fail the phase gate → escalate →
   halt. Ships at `record` everywhere.

### Relationship to the neighbours

- **17** shares the reconcile machinery, the condition vocabulary, and
  the action ladder. Build 17 first; this is the second loop on the same
  rails, not a parallel invention.
- **13** is the other side of the coin and must not be duplicated: 13
  optimizes *vibey's own* dev loop and engine spend (suite duration, CI
  caching, effort right-sizing, cost-aware rotation). This runbook
  optimizes *the code vibey's jobs produce*. Where they meet — delivery
  economics from ledger `cost_usd` — 13 owns the measurement and this
  loop consumes it.
- **05** supplies the operator, CRD, and condition plumbing.

## Work items

1. Meter registry + probes for the meters real specs already use.
2. Pure fitness evaluator in `vibey/domain/`, property-tested.
3. Baseline artifact: recording, reading, explicit re-baselining.
4. Measurement collectors: benchmark, memory, `pg_stat_statements`,
   metrics-server, image size.
5. kopf timer + `Fitness` condition + Events, at `record` only.
6. Right-sizing recommendations for the chart's own resource requests.
7. Ladder rungs behind `fitnessPolicy`, promoted one dimension at a time.
8. The same loop in the four *loop repos, at their own altitude.
9. `docs/guides/production-fitness.md` per repo.

## Verification

- **The quiet test, and the most important one:** a codebase already
  within budget produces **zero** findings across a full greeter run. A
  loop that chirps on healthy code will be muted, and then it protects
  nothing.
- A seeded regression — an NFR's `must` deliberately breached — is caught
  within one reconcile interval and produces a repair ticket that flows
  through BUILD → REVIEW and closes.
- A seeded N+1 on a hot path is caught from `pg_stat_statements` rather
  than from someone reading the diff.
- Right-sizing: a recommendation for the vibey worker's own requests,
  derived from measured usage over a real run, replacing the current
  judgement-based `250m` / `512Mi`.
- Noise floor measured and recorded before any dimension is promoted past
  `record`.

## Needs from operator

- 05's operator and 17's reconcile machinery landed first.
- metrics-server (or Prometheus) in-cluster for the right-sizing arm.
- `pg_stat_statements` enabled on the target database.
- A decision on the production `fitnessPolicy` ceiling.

## Risks

- **Optimization churn.** The single biggest risk, and the breach-or-
  regression rule is the whole mitigation. Resist every request to make
  the loop act on absolute quality.
- **Correctness traded for speed.** Every finding goes through the normal
  review path with the full gate suite; the loop never edits code.
- **Measurement noise.** Addressed by sampling and confidence, and by
  measuring the noise floor before promoting a dimension.
- **Ratcheting baselines.** Automatic re-baselining would let the system
  drift steadily slower while reporting green. Re-baselining stays
  explicit and recorded.
- **Premature micro-optimization.** A `wish` is a reporting target, never
  a trigger. If a dimension has no `must`, the loop cannot act on it.
