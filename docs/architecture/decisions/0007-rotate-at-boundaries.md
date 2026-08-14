# 0007 — Rotate at boundaries, never mid-turn

**Status:** accepted · **Date:** 2026-08-14

## Context

"Round robin across AIs" could mean rotating on every turn, every work item, or
only when forced. Each handoff costs: a brief generation, a gate run, possibly
three regenerations, and a cold engine reading a ledger.

## Decision

Rotation fires **only at boundaries**, and never during a turn.

| Trigger | Rotates | Forced | Handoff |
|---|---|---|---|
| New work item claimed | yes | no | no (fresh context) |
| Capacity rejection | yes | yes, excludes rejector | yes |
| Effort escalation | yes | yes | yes |
| Engine crash / hang (`ENGINE` class) | yes | yes | yes |
| Phase transition | yes | no | yes |
| Operator `vibey rotate --now` | yes | yes | yes |
| Retry after a `WORK` failure | **no** | — | no |
| Mid-turn | **never** | — | — |

## Rationale

**Why not every turn.** It would mean a handoff on every turn: maximum cost,
maximum exposure to gate failure, and no benefit — the point of rotation is to
spread load across capacity pools and to get independent perspectives at
decision points, not to shuffle continuously. Stickiness is implemented by the
`affinity_factor` of 2.0 in the rotation weight, which strongly favors the engine
already holding a warm session unless rotation is forced.

**Why never mid-turn.** A turn is the atomic unit against a live vendor session.
Interrupting one leaves the vendor's session state and vibey's ledger disagreeing
about what happened — the exact inconsistency the event-sourced design exists to
prevent. A turn either completes and produces a `TurnCompleted` event, or it fails
and produces a failure event. There is no third state, and rotation cannot create
one.

**Why `WORK` failures don't rotate.** If the tests fail because the code is wrong,
that is not evidence the engine is unhealthy. Rotating would throw away a warm
session with full context for no reason, and would open a circuit on a healthy
engine ([failure attribution](../../plans/rotation-and-engines.md#63-failure-attribution)).
The escalation ladder handles genuinely stuck items at attempts 3 and 5, where
rotation *is* forced.

## Consequences

**Good.** Handoff cost is bounded and proportional to real events. Warm sessions
are preserved, which matters for both cost and quality. The "must differ"
constraints (verifier ≠ implementer, synthesizer ≠ interviewer) still deliver
cross-vendor independence where it counts, without paying for it every turn.

**Bad.** A single work item may be built entirely by one engine, so its
idiosyncrasies are not averaged out within that item. Mitigated by the mandatory
rotated verifier — the code is always read by a different vendor before it
integrates.
