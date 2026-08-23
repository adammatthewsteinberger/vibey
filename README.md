# vibey

[![PyPI](https://img.shields.io/pypi/v/vibey)](https://pypi.org/project/vibey/)
[![PyPI downloads](https://img.shields.io/pypi/dm/vibey)](https://pypi.org/project/vibey/)
[![Python versions](https://img.shields.io/pypi/pyversions/vibey)](https://pypi.org/project/vibey/)
[![CI](https://github.com/adammatthewsteinberger/vibey/actions/workflows/ci.yml/badge.svg)](https://github.com/adammatthewsteinberger/vibey/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/adammatthewsteinberger/vibey/blob/develop/LICENSE)

**A queue-based, six-phase conductor for autonomous software delivery — with an
optional visual-design interstitial and opt-in Azure deployment — built on top
of the `*loop` autonomous session runners.**

## What problem this solves

An autonomous coding session is not autonomous software delivery. A single
`claudeloop` run can finish a task, but it cannot interview you until the spec
is sharp, split the work into parallel items, verify each one against gates it
cannot game, survive its own credit exhaustion by handing off to a different
vendor's engine *without losing a single open question*, or know that a review
finding should reopen design rather than vanish into a transcript.

Vibey conducts all of that. You describe what you want; it interviews you until
the spec is sharp, builds unattended across a pool of engines with real budget
caps, reviews the result with you, and (only if you opt in) deploys. Every
choice, finding, and handoff lives in an append-only PostgreSQL ledger — never
in one vendor's chat session.

| | |
|---|---|
| Runs on | macOS / Linux, local. No cloud control plane required. |
| Language | Python 3.12+ |
| Queue | PostgreSQL (`FOR UPDATE SKIP LOCKED`) |
| Engines | [`claudeloop`](https://github.com/adammatthewsteinberger/claudeloop), [`codexloop`](https://github.com/adammatthewsteinberger/codexloop), [`cursorloop`](https://github.com/adammatthewsteinberger/cursorloop), [`agyloop`](https://github.com/adammatthewsteinberger/agyloop) |
| State dir | `.vibey/` |
| Env prefix | `VIBEY_` |
| Done marker | Each loop's own marker (CLAUDELOOP_TASK_FULLY_COMPLETE, etc.) |

## Install

Requires **Python 3.12+**, **PostgreSQL**, and at least one `*loop` engine on
PATH. Windows is not a supported target.

```bash
uv tool install vibey          # or: pipx install vibey / pip install vibey
uv tool install claudeloop     # at least one engine; add codexloop, cursorloop, agyloop for rotation
vibey doctor                   # pre-flight: database, engines, auth
```

To add deterministic, budgeted context packets from the independently versioned
`vibey-skills` marketplace, install the optional extra and enable it per project:

```bash
uv tool install 'vibey[skills]'
vibey new my-app --repo ~/src/my-app \
  --skills-context-mode shadow --skills-context-budget 6000
```

`shadow` builds and records packet provenance without changing agent prompts.
After observing results, switch the project config to `inject` to append successful
packets to BUILD prompts. Missing tools, timeouts, low-confidence retrieval, and
insufficient budgets all fall back to the original prompt. The feature is off by
default, and wind-down prompts are never modified.

## Quickstart

```bash
vibey doctor --conformance --record          # verify each engine's contract, persist health
vibey new my-app --repo ~/src/my-app \
  --max-cycle-dollars 15                     # real budget brake, enforced from the ledger
vibey worker --engines claudeloop,agyloop -j 2   # unattended build across the pool

# When vibey parks for your input (design gates, review, budget grants):
vibey answer <gate-id> --defaults            # accept the interview defaults, or:
vibey answer <gate-id> --raw '{"max_dollars": 25}'   # raise a tripped budget cap
vibey design accept <project-id> --no-visual
vibey answer <gate-id> --verdict accept      # review demo
vibey answer <gate-id> --choice local_only   # decline deployment → DONE (local)
```

The [greeter live-demo runbook](docs/guides/greeter-live-demo.md) walks a full
paid run end to end, including the zero-touch contracts.

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
runs dry. Phase 3 asks whether to deploy; "no" is a successful local completion.
Phase 6 accepts a successful deployment, requests changed deployment details in
Phase 4, retries an unambiguous deployment in Phase 5, or routes an application
defect back to the appropriate delivery phase.

## Why it isn't just another agent framework

The hard part is not calling an LLM in a loop — `claudeloop` and its siblings
already solve that, including the distinction between a waitable rate-limit
window and exhausted credits that no amount of waiting will fix. Vibey adds the
things those runners deliberately do not do:

1. **A phase machine with loop-backs**, so a review finding becomes a new design
   conversation rather than a lost note.
2. **Round-robin engine rotation with lossless handoff** — the conversation is an
   append-only event ledger, not a chat transcript locked inside one vendor's
   session, so any engine can pick up where any other left off. A handoff that
   would lose an open question, decision, assumption, or finding is rejected by
   a pure, deterministic no-loss gate — never silently accepted.
3. **A durable queue**, so work survives a laptop lid closing, a crash, or a
   provider outage, and so multiple work items build in parallel in isolated
   git worktrees.
4. **Real money brakes** — per-cycle dollar and turn caps summed from the
   ledger's own cost events, with parks that tell you the exact command to
   grant more.

## Documentation

| Document | What's in it |
|---|---|
| [Greeter live-demo runbook](docs/guides/greeter-live-demo.md) | A full paid run, end to end, with the zero-touch contracts |
| [Expansion runbooks](docs/runbooks/expansion/) | Fifteen workstreams: JIRA, more clouds, Kubernetes server mode, clients, store submissions, … |
| [Architecture & roadmap](docs/plans/architecture-and-roadmap.md) | The master design: context, containers, layers, phases, risks, milestones |
| [Domain model](docs/plans/domain-model.md) | Every value object, ADT, and invariant in `domain/` |
| [Data model](docs/plans/data-model.md) | Full PostgreSQL DDL, queue semantics, indices |
| [Handoff protocol](docs/plans/handoff-protocol.md) | The event ledger, the envelope, and the no-loss gate |
| [Rotation & engines](docs/plans/rotation-and-engines.md) | Capability matrix, effort normalization, smooth weighted round robin |
| [Phase protocols](docs/plans/phase-protocols.md) | What all six phases do, turn by turn |
| [Implementation plan](docs/plans/implementation-plan.md) | Milestone-by-milestone, test-first task breakdown |
| [Decision records](docs/architecture/decisions/) | Why each hard call was made |

## Status

**Live-validated.** The full pipeline has conducted real paid deliveries end to
end: multi-worker builds (`-j 2`) with cross-engine rotation (claudeloop
implements, agyloop verifies), the bounded verify-repair ladder, budget caps
tripping and being granted live, and fully zero-touch DESIGN phases answered
with nothing but `--defaults`. The validation campaign's findings — a blind
budget brake, a repair-loop livelock, terminal gate-command failures — were
each fixed and re-validated live.

Every architectural layer (`domain`, `application`, `infrastructure`, `cli`)
holds a **100% branch-coverage floor**, enforced as four separate CI gates.
`domain/` is pure stdlib, enforced by import-linter and an AST-walking purity
test — the no-loss handoff gate is deterministic code, not a model's opinion.

## Related projects

| Project | What it is |
|---|---|
| [claudeloop](https://github.com/adammatthewsteinberger/claudeloop) | Autonomous Claude Code session runner — the design the family transplants |
| [codexloop](https://github.com/adammatthewsteinberger/codexloop) | The same design retargeted onto OpenAI Codex |
| [cursorloop](https://github.com/adammatthewsteinberger/cursorloop) | The same design retargeted onto Cursor |
| [agyloop](https://github.com/adammatthewsteinberger/agyloop) | The same design retargeted onto Google Antigravity / Gemini |

## License

[MIT](LICENSE) © [Adam Matthew Steinberger](https://github.com/adammatthewsteinberger)
