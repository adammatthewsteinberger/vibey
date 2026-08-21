# Runbook: plan-drift reconciliation — a control loop that keeps bots on plan

## Goal

Apply Kubernetes' reconciliation model to autonomous delivery. A
controller continuously compares **desired state** (the accepted plan)
against **observed state** (what the bots actually did), names the
divergence, and takes bounded corrective action to bring the system back
to the plan.

Delivered as a kopf loop in **all five repos**, each at its own altitude:

| Repo | Desired state | Observed state | Altitude |
|---|---|---|---|
| `vibey` | accepted `DesignSpec` + `WorkPlan` + phase protocol | ledger, `job` table, worktree git history, artifacts | a project across six phases |
| `claudeloop` | the plan file handed to the run + its run contract | own `events.jsonl`, `state.json`, rundir | one autonomous session |
| `codexloop` | " | " | " |
| `cursorloop` | " | " | " |
| `agyloop` | " | " | " |

Two altitudes, one pattern. vibey answers "is this *project* still
building what was accepted?"; each runner answers "is this *session*
still working the plan it was given?" A conductor-level reconciler cannot
see inside a two-hour session, and a session-level one cannot see the
project. Both are needed and neither substitutes for the other.

This loop answers "did the bots build what was planned?". Its sibling,
`18-production-fitness-reconciliation.md`, answers "is what they built
fit to run in production?" -- built on the same rails, and a separate
question, since code can match its plan exactly and still allocate
unboundedly and cost three times what it should.

## Why this is not just monitoring

The distinction that makes this worth building is Kubernetes':
**level-triggered, not edge-triggered.** The loop does not watch for a
drift event and react. It recomputes the verdict from observed state
every interval, so it is correct after a missed event, a crashed worker,
a replayed job, or an operator editing state by hand. That is the same
property vibey already relies on for job replay, extended to plan
adherence.

The second Kubernetes idea worth stealing: drift is reported as
**status conditions**, not logs. `kubectl get vibeyprojects` should show
`PLANDRIFT=True` with a reason, the same way a Deployment shows
`Available=False`. That makes drift legible to every k8s-native tool the
operator already runs.

## Phase 0 — make plans machine-checkable (blocks everything)

**A reconciler over prose is vibes with a control loop bolted on.** Today
a spec constraint reads:

```
- [hard] Scope is Front 1 items 1-4 only. Do not start Front 2 ...
- [hard] Protected test files must remain byte-untouched: ...
```

The second is mechanically checkable (hash the files). The first is not,
as written. Until a constraint carries a predicate something can evaluate,
no loop can honestly say whether it was violated.

So Phase 0 is a domain change, not a Kubernetes one: constraints gain a
structured, checkable form alongside their prose — a kind, a target, and
a predicate (`files_unchanged`, `paths_within`, `no_new_dependency`,
`coverage_at_least`, `spend_under`, `phase_is`). Prose stays for humans;
the predicate is what the reconciler reads. Constraints that genuinely
cannot be expressed as a predicate are marked `advisory` and are
explicitly **out of scope for automated action** — they can be reported,
never enforced.

Do not start Phase 1 until a real spec round-trips through this. The
honest failure mode of this whole workstream is a confident loop
enforcing constraints it cannot actually evaluate.

## Drift taxonomy

### vibey altitude

- **Scope drift** — commits touching paths outside the work item's
  declared scope, or work items appearing that the accepted plan never
  contained (gold-plating).
- **Constraint violation** — a `[hard]` constraint's predicate evaluates
  false.
- **Acceptance drift** — a work item marked complete with acceptance
  criteria never demonstrated. vibey already has the vocabulary for this;
  the loop makes it continuous rather than end-of-phase.
- **Phase drift** — work of one phase performed in another (BUILD doing
  design, REVIEW writing features).
- **Dependency drift** — jobs succeeding out of the plan's intended
  order.
- **Budget drift** — spend outpacing the plan's projection for remaining
  work. The brake already stops a runaway cycle (PR #58); this predicts
  one early enough to re-plan.
- **Stall drift** — no forward progress: repair rounds cycling, a work
  item bouncing ready→failed→ready, a phase not advancing.
- **Silent-partial drift** — a handoff that passed the no-loss gate
  marginally, or a completion claim whose ledger shows no corresponding
  work.

### runner altitude (each *loop repo)

- **Prompt drift** — turns spent on work the plan file does not contain.
- **Turn-budget drift** — turns burned without advancing any plan item.
- **Verdict drift** — a "done" verdict with plan items unaddressed. This
  is the session-level twin of vibey's no-loss gate.
- **Path drift** — writes outside the declared worktree scope.
- **Loop drift** — the same failing action repeated: the "stuck"
  detector. Each runner already has partial signal for this; the loop
  makes it a first-class, reported condition.

## The action ladder (bounded, enumerated, never creative)

Escalating, with the ceiling set by policy per project or run:

1. **Record** — a drift event in the ledger, a CR status condition, a
   Kubernetes Event. *Always happens; the only rung enabled by default.*
2. **Nudge** — enqueue a corrective job through the normal application
   service (a repair ticket, a re-verify).
3. **Reject** — the completion claim does not stand; the work item
   returns to ready.
4. **Escalate** — park a human gate carrying the drift evidence.
5. **Halt** — stop claiming for this project; a circuit break.

**The reconciler never repairs creatively.** It selects from this list.
A loop that reasons freely about how to fix drift is a second autonomous
agent, and it will drift — about drift. If a drift kind genuinely needs
model judgment, that is a *budgeted, rate-limited job* the loop enqueues
(rung 2), never work the timer does inline.

## Design

1. **Detector lives in `domain/`, pure.** Given a plan and an observation
   snapshot, return findings. Stdlib only, no I/O, no async — so it is
   property-testable and identical across replays. This is the piece that
   must be right; kopf is delivery.
2. **kopf timer per CR.** `@kopf.timer` on `VibeyProject` (05's CRD) and
   on each runner's own run CR. The timer gathers the observation
   snapshot, calls the pure detector, writes conditions, and applies at
   most one rung.
3. **Conditions and Events.** A shared condition vocabulary across all
   five repos — `PlanDrift`, with `reason` drawn from the taxonomy above —
   so one dashboard reads every repo. Divergent vocabularies across five
   implementations is the predictable failure; a conformance suite pins
   it, the same way the engine conformance suite pins adapter behavior.
4. **One write path.** Corrective actions call the same application
   services `vibey answer` and the normal enqueue path call. 05 already
   names this risk for the CRD answer channel; it applies with more force
   here, because the reconciler writes far more often than a human does.
5. **Policy.** `spec.driftPolicy` caps the ladder (`observe`, `nudge`,
   `reject`, `escalate`, `halt`) globally and per drift kind. Ship
   `observe` as the default everywhere and promote a drift kind only once
   its false-positive rate has been measured on real runs.

### Guardrails inherited from the non-negotiables

- **Never block a worker on a human.** Escalation is a parked job plus a
  `human_gate` row. The reconciler never waits.
- **The ledger is append-only.** Drift findings are new events; a
  resolved finding is superseded, never mutated.
- **Idempotent under replay.** The verdict is a pure function of the
  observation snapshot, so re-running the timer changes nothing.
- **`domain/` stays pure.** Enforced by import-linter, as everywhere else.
- **A drift finding outranks a completion claim** — the same precedence
  rule as capacity rejection, and for the same reason: the claim is the
  thing under suspicion.

## Work items

1. Phase 0: checkable constraints in vibey's domain + spec round-trip.
2. Pure drift detector in `vibey/domain/`, property-tested.
3. Observation snapshot assembler in `application/` (ledger + jobs + git).
4. kopf timer on `VibeyProject`; conditions + Events; `observe` only.
5. Action ladder rungs 2–5 behind `driftPolicy`, promoted one at a time.
6. Runner-altitude detector in each of the four *loop repos (their own
   `domain/`, their own coverage budget).
7. Shared condition vocabulary + a cross-repo conformance suite.
8. `docs/guides/drift-reconciliation.md` in each repo.

## Verification

- A seeded scope violation (a commit touching a path outside the work
  item's scope) surfaces as `PlanDrift=True` with reason `ScopeDrift` on
  `kubectl get vibeyprojects`, within one reconcile interval.
- A seeded stall (a work item bounced N times) escalates to a human gate
  under `driftPolicy: escalate`, and the worker never blocks.
- Killing the operator mid-drift and restarting it reproduces the same
  verdict from observed state alone — the level-triggered property.
- Measured false-positive rate per drift kind over a full greeter run,
  recorded as evidence before any kind is promoted past `observe`.
- One runner-altitude drift (verdict drift: "done" with plan items
  unaddressed) caught in a real session in each of the four repos.

## Needs from operator

- 05's kopf operator and CRD landed first (this is a loop on top of it).
- 16's runner containers, for the runner-altitude loops.
- A decision on the default `driftPolicy` ceiling in production values.

## Risks

- **Prose constraints.** Addressed by Phase 0; the risk is skipping it.
- **False positives halting healthy work.** Mitigated by shipping
  `observe`-only and promoting per kind on measured evidence. A
  reconciler that halts good runs will be turned off, and then it
  protects nothing.
- **Reconciler cost.** The timer runs constantly and must stay cheap —
  DB queries and git, no model calls in the hot path.
- **Five implementations diverging.** The conformance suite is not
  optional; without it the shared vocabulary is aspirational.
- **Drift about drift.** The bounded action ladder is the whole mitigation.
  Resist every temptation to let the loop reason its way to a fix.
