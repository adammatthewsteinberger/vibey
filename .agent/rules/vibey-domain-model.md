# vibey-domain-model (Antigravity mirror of `.claude/skills/vibey-domain-model/SKILL.md`)

# vibey domain model

Read `docs/plans/domain-model.md` before touching `domain/`. This skill is a
compressed orientation; the full spec lives in that doc.

## Phases

Six numbered phases plus optional visual interstitial:

```
INTAKE → ① DESIGN → [optional VISUAL_DESIGN] → ② BUILD ⇄ ③ REVIEW
         ▲──────────────────────────┘               │
                                                     │
③ ── user declines deployment ──────────────────────→ DONE (local)
  │ user opts into deployment
  ▼
④ DEPLOY_DESIGN → ⑤ DEPLOY_EXECUTE → ⑥ DEPLOY_REVIEW → DONE (deployed)
```

Interactive phases (talk to the user): ①, ③, ④, ⑥, VISUAL_DESIGN.
Autonomous phases (unattended): ②, ⑤.

**Loop-backs:**
- `BUILD → DESIGN` when blocked on ambiguity (spec insufficient).
- `REVIEW → DESIGN` (default) or `REVIEW → BUILD` (fast path when every
  finding is `unambiguous`). See ADR-0010.
- `DEPLOY_REVIEW` can route to ④, ⑤, or back to ①/②/③ depending on the
  failure classification.

**Opt-in gates:**
- Visual design: after ① accepts a buildable spec, vibey asks whether to
  enter the visual-design interstitial. Declining takes the `DESIGN → BUILD`
  edge directly.
- Deployment: after ③ has no open product findings, vibey asks whether to
  work on deployment. Declining records `completion_mode = "local"` and
  transitions to `DONE` without enqueueing any Azure job.

See ADR-0014 (optional visual-design and deployment opt-in).

## Jobs

Job kinds are strings registered against handlers in `bootstrap.py` (25 kinds
as of 2026-09-15):
- DESIGN: `design.interview`, `design.research`, `design.synthesize`, `design.spec`
- VISUAL_DESIGN: `visual.inventory`, `visual.plan`
- BUILD: `build.decompose` (alias `build.plan`), `build.implement`, `build.verify`,
  `build.integrate`
- REVIEW: `review.demo`, `review.collect`, `review.triage`, `review.deployment_choice`
- DEPLOY_DESIGN: `deploy.design`, `deploy.interview`, `deploy.synthesize`,
  `deploy.spec` (alias `deploy.accept`)
- DEPLOY_EXECUTE: `deploy.execute` (alias `deploy.graph`)
- DEPLOY_REVIEW: `deploy.demo`, `deploy.triage`, `deploy.route`

`docs/plans/phase-protocols.md` also names kinds that are not registered
(`media.generate.*`, `visual.review`, `deploy.discover`/`plan`/`validate`/`apply`/
`release`/`verify`/`recover`/`collect`); treat those as planned. Handoff is not a
job kind: it runs inside the engine-driven job through `application/wind_down.py`
and `application/handoff_orchestration.py`.

**Job lifecycle (`domain/job.py::JobState`):**
`ready → leased → succeeded | failed | awaiting_human | awaiting_capacity | cancelled`.

**Failure classes (`domain/job.py::FailureClass`):** `capacity` (opens the
circuit), `engine` (opens after 3), `work` (the code is wrong; circuit untouched),
`vibey` (our bug; circuit untouched).

**Bounded ladders park, they do not loop.** When `build.implement` or
`build.verify` exhausts its effort ladder (or a spend cap), the job parks behind a
human gate. The answer can grant a bound (`max_attempts` for implement attempts,
`max_rounds` for verify repair rounds, `max_dollars`/`max_turns` for spend);
further attempts run at the ladder's top effort until that grant is used up, then
park again (ADR-0024; `granted_limit`/`granted_amount` in
`application/build_verify_handler.py`).

**Idempotency:** every job is idempotent under replay via `idempotency_key` —
a deterministic hash of `(project_id, cycle, kind, subject)`. Re-enqueueing
the same logical work is a no-op. Handlers also guard their own side effects.

**Parallel vs serial:** some jobs run in parallel (e.g., `build.implement` —
each work item in its own git worktree). Others are serial (e.g.,
`build.integrate` — one integration branch, serialised per project and cycle by a
Postgres advisory lock in `infrastructure/db/advisory_lock.py`, ADR-0029).

See `domain/job.py` (`JobState`, `FailureClass`, `backoff()`,
`idempotency_key()`) and the handlers in `application/*_handler.py`.

## Ledger

The **append-only event log** in Postgres, written in a vendor-neutral schema.
Vendor transcripts (`~/.claude/projects/**/*.jsonl`, codex rollouts, cursor
bridge logs) are copied in as *attachments* referenced by events — they are
evidence, not state.

**Event kinds (25 total, `domain/ledger.py::EventKind`):** `SessionSeeded`,
`TurnRequested`, `TurnCompleted`, `ToolInvoked`, `FileEdited`, `VerdictRendered`,
`CapacityRejected`, `QuestionAsked`, `AnswerGiven`, `DecisionRecorded`,
`AssumptionStated`, `FindingRaised`, `FindingResolved`, `ArtifactProduced`,
`SavePointCreated`, `HandoffInitiated`, `HandoffAccepted`, `PhaseTransitioned`,
`BudgetSpent`, and the ADR-0014 opt-in gate events `VisualDesignOptedIn`,
`VisualDesignDeclined`, `VisualDesignAccepted`, `VisualDesignWaived`,
`DeploymentOptedIn`, `DeploymentDeclined`.

**Closable events:** `QuestionAsked`, `DecisionRecorded`, `AssumptionStated`,
`FindingRaised` — these are the events the no-loss gate checks.

**Digest:** every event carries a `digest` (SHA-256 of canonical JSON payload).
`digest_range()` computes an order-sensitive Merkle-ish fold of a sequence of
events — this is what R6 (range integrity) checks.

See `domain/ledger.py` and `docs/plans/handoff-protocol.md`.

## Handoff and the no-loss gate

When an engine hits `CreditsExhausted`, vibey:
1. Produces a `HandoffBrief` (the outgoing engine writes it, or the incoming
   engine synthesizes it if the outgoing is dead).
2. Verifies it against the **no-loss gate** (`domain/noloss.py::verify()`).
3. If the gate passes, writes the full ledger to
   `<worktree>/.vibey/handoff/ledger.jsonl` and seeds the next engine.
4. If the gate fails, regenerates (up to 3 attempts), then escalates to
   `full_transcript` mode (entire ledger inlined), then raises a human gate.

**The 10 rules (R1–R10):**
- R1: remaining-work closure
- R2: open-question closure
- R3: decision closure
- R4: assumption closure
- R5: finding closure
- R6: range integrity (digest match)
- R7: artifact closure
- R8: budget carry
- R9: constraint closure
- R10: containment (nothing in the brief contradicts the spec)

The gate is **pure and deterministic** — no model call. This is the reason
rotation is safe.

See ADR-0004 (no-loss gate on handoff) and `domain/noloss.py`.

## Rotation

**Smooth weighted round robin** (nginx-style SWRR), not naive modulo. Engines
are selected from the eligible set via `domain/rotation.py::select()`.

**Eligibility:** installed, authenticated (`doctor` passed within TTL),
circuit not `open`, capability requirements met, and per-phase allow-list
permits it.

**When rotation happens:** at boundaries only — never mid-turn. Triggers:
new work item starts, capacity rejection (forced, exclude the rejecting
engine), effort escalation, phase transition, operator-requested handoff.

**Properties (property-tested):**
- No starvation: over `sum(effective_weight)` consecutive selections, every
  candidate with `effective_weight > 0` is selected at least once.
- Weight fidelity: selection counts converge to weight ratios within ±1 over
  any full period.
- Smoothness: no candidate is selected twice consecutively while another with
  `effective_weight > 0` has gone unselected longer.
- Determinism: identical candidate state produces an identical selection.

**Wiring:** `application/engine_selector.py::EngineSelector` calls `select()`
for engine-driven BUILD jobs, through `SelectingEngineProvider` in `bootstrap.py`.
Candidates come from `engine_health` rows, so an engine without a recorded
`vibey doctor --conformance --record` pass is never eligible. qwenloop joins only
when its feature flag is on, as a standby engine (ADR-0015).

See ADR-0005 (smooth weighted round robin), ADR-0007 (rotate at boundaries),
and `domain/rotation.py`.

## Effort ladder

Vibey speaks a normalized 5-level ladder: `TRIVIAL, LOW, STANDARD, HIGH, MAX`.
Each engine descriptor provides a **projection** onto native flags, which may
saturate.

**Phase base effort:**
- ① DESIGN: `HIGH`
- VISUAL_DESIGN: `HIGH`
- ② BUILD: `LOW` (auto-escalating to `STANDARD` → `HIGH` after failures)
- ③ REVIEW: `HIGH`
- ④ DEPLOY_DESIGN: `HIGH`
- ⑤ DEPLOY_EXECUTE: `LOW` (auto-escalating)
- ⑥ DEPLOY_REVIEW: `HIGH`

`Phase` also carries `DEPLOY` (a legacy single-phase bridge, base `LOW`) and
`ABANDONED`; the phase diagram omits them deliberately.

See ADR-0006 (normalized effort ladder) and `domain/effort.py`.

## Capacity states

`Available | WindowExhausted | CreditsExhausted | AuthenticationFailed`

**The one rule that matters:**
`CreditsExhausted` has **no `resets_at` field** and can never acquire one.
This is enforced at three independent layers:
1. Type-level: `domain/capacity.py`'s dataclass has no such attribute.
2. Property-tested: `schedule_probe(CreditsExhausted(...))` can only return a
   `BackoffProbe`, never a `DeadlineProbe`.
3. Database-level: the `engine_health` table has a CHECK constraint
   `credits_never_have_a_deadline` that rejects any `INSERT`/`UPDATE` with
   `capacity_state = 'CreditsExhausted'` and non-null `resets_at`.

See `domain/capacity.py`, `domain/circuit.py`, the constraint in
`migrations/0007_engine_health_rotation.sql`, and the CLAUDE.md non-negotiable "A
capacity rejection always outranks a completion claim" (it has no ADR of its
own).
