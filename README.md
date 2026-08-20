# vibey

**A queue-based, six-phase conductor for autonomous software delivery — with an
optional visual-design interstitial and opt-in Azure deployment — built on top
of the `*loop` autonomous session runners.**

You describe what you want. Vibey interviews you until the spec is sharp (Phase 1),
then asks whether you want an optional visual-design pass before building. If you
opt in, it inventories every screen and state, generates the planned image, audio,
and video assets, and waits for your confirmation. It then builds autonomously,
reviews the result, and asks whether you want deployment work at all. Declining
deployment finishes the run locally; opting in enters the Azure deployment stage
set. Every choice and loop is durable and lossless.

| | |
|---|---|
| Runs on | macOS / Linux, local. No cloud control plane required. |
| Language | Python 3.12+ |
| Queue | PostgreSQL (`FOR UPDATE SKIP LOCKED`) |
| Engines | `claudeloop`, `codexloop`, `cursorloop`, `agyloop` |
| State dir | `.vibey/` |
| Env prefix | `VIBEY_` |
| Done marker | Each loop's own marker (CLAUDELOOP_TASK_FULLY_COMPLETE, etc.) |

## The shape of it

```
  DELIVERY STAGE SET
  INTAKE → ① DESIGN ──┬─ no ───────────────→ ② BUILD ⇄ ③ REVIEW
                      │                       autonomous / interactive
                      └─ yes → [VISUAL DESIGN]
                                interactive, media generation + confirmation
                                          │ visual-ready
                                          └──────────────→ ② BUILD

  ③ REVIEW ── no deployment ─────────────────────────────→ DONE (local)
       │ opt in
       ▼
  DEPLOYMENT STAGE SET
  ④ DEPLOY DESIGN ⇄ ⑤ DEPLOY EXECUTE ⇄ ⑥ DEPLOY REVIEW → DONE (deployed)
       interactive       autonomous          interactive
             ▲                 │                    │
             └─────────────────┴────────────────────┘
```

Phases 1, 3, 4, and 6 talk to you. The optional Visual Design stage also talks to
you and cannot hand work to BUILD until every planned visual is accepted or you
explicitly waive the stage. Phases 2 and 5 run unattended, survive rate-limit
windows and credit exhaustion, and rotate eligible engines/providers when one
runs dry. Phase 3 asks whether to deploy; “no” is a successful local completion.
Phase 6 accepts a successful deployment, requests changed deployment details in
Phase 4, retries an unambiguous deployment in Phase 5, or routes an application
defect back to the appropriate delivery phase.

## Why it isn't just another agent framework

The hard part is not calling an LLM in a loop — `claudeloop` and its siblings
already solve that, including the distinction between a waitable rate-limit
window and exhausted credits that no amount of waiting will fix. Vibey adds the
three things those runners deliberately do not do:

1. **A phase machine with loop-backs**, so a review finding becomes a new design
   conversation rather than a lost note.
2. **Round-robin engine rotation with lossless handoff** — the conversation is an
   append-only event ledger, not a chat transcript locked inside one vendor's
   session, so any engine can pick up where any other left off.
3. **A durable queue**, so work survives a laptop lid closing, a crash, or a
   provider outage, and so multiple work items build in parallel in isolated
   git worktrees.

## Documentation

| Document | What's in it |
|---|---|
| [Fleet program runbook](docs/plans/fleet-program-runbook.md) | The cross-repo program: current state, coverage gates, seven surfaces, and the claudeloop invocation that executes it |
| [Architecture & roadmap](docs/plans/architecture-and-roadmap.md) | The master design: context, containers, layers, phases, risks, milestones |
| [Domain model](docs/plans/domain-model.md) | Every value object, ADT, and invariant in `domain/` |
| [Data model](docs/plans/data-model.md) | Full PostgreSQL DDL, queue semantics, indices |
| [Handoff protocol](docs/plans/handoff-protocol.md) | The event ledger, the envelope, and the no-loss gate |
| [Rotation & engines](docs/plans/rotation-and-engines.md) | Capability matrix, effort normalization, smooth weighted round robin |
| [Phase protocols](docs/plans/phase-protocols.md) | What all six phases do, turn by turn |
| [Implementation plan](docs/plans/implementation-plan.md) | Milestone-by-milestone, test-first task breakdown |
| [Decision records](docs/architecture/decisions/) | Why each hard call was made |

## Status

**M10 + E1 complete.** All milestones M0 through M10 are fully implemented and verified
against the 7-gate CI sweep. Phase E1 (live engines, rotation wiring, full worker,
two-mode test harness) added real engine process management, SWRR rotation with crash-safe
cursor persistence, and the `LoopProcessAdapter` that drives all four loop binaries
through a single data-driven adapter. The complete six-phase delivery-to-deployment
pipeline is operational:

- **Phase ① DESIGN** — interactive interview, research, synthesis, spec acceptance,
  and optional visual-design interstitial
- **Phase ② BUILD** — isolated git worktree integration, escalation ladder, budget
  checks, and parallel work items
- **Phase ③ REVIEW** — demo, collect, automated findings pre-triage, triage,
  re-entrant design loop-backs, and explicit deployment-choice gate
- **Phase ④ DEPLOY DESIGN** — deployment interview, synthesis, IaC plan evaluation,
  and explicit mutation consent
- **Phase ⑤ DEPLOY EXECUTE** — durable execution graph (discover → plan → validate →
  apply → configure → migrate → release → verify), retry/escalation ladder, and
  progressive exposure with policy-bound recovery
- **Phase ⑥ DEPLOY REVIEW** — live endpoint demo, failure triage, and loop routing
  (→ DONE, → ④, → ⑤, or → ①/②/③)

Both optional paths (visual opt-in/opt-out and deployment opt-in/opt-out) are
exercised in the offline system test suite. See the
[implementation plan](docs/plans/implementation-plan.md) for the full milestone sequence.

## License

MIT.
