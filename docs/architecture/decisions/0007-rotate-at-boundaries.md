# 0007 — Rotate at boundaries, never mid-turn

**Status:** accepted · **Date:** 2026-08-14

**Owes:** nothing — mechanism (ADR-0020)

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
| Engine wind-down (exit 75: out of window mid-item, state written) | yes | yes, excludes the winding-down engine; ≤3 per item, then a human gate | yes (full ledger + gated brief) |
| Effort escalation | yes | yes | yes |
| Engine crash / hang (`ENGINE` class) | yes | yes | yes |
| Phase transition | yes | no | yes |
| Operator-forced rotation (planned `vibey rotate --now`; not a command yet) | yes | yes | yes |
| Retry after a `WORK` failure | **no** | — | no |
| Mid-turn | **never** | — | — |

**What is wired today.** Rotation runs per job for `build.implement` and
`build.verify`: the composition root wraps them in `SelectingEngineProvider` (`application/engine_selection.py`),
which derives exclusions and affinity from the job's own durable state and selects
through SWRR ([ADR-0005](0005-smooth-weighted-round-robin.md)).

- **Wind-down** is the full row: `application/wind_down.py` writes the BUILD ledger
  to `<worktree>/.vibey/handoff/ledger.jsonl`, gates a brief
  ([ADR-0004](0004-no-loss-gate-on-handoff.md)), records a `handoff` row, and
  enqueues the follow-up with the winding-down engine excluded.
  `RotationHandoffService` bounds it at three wind-downs per item
  (`TooManyWindDowns` → a `too_many_wind_downs` gate).
- **Capacity rejection** defers the job and opens that engine's circuit, so the next
  claim rotates away. No brief is produced on this path yet;
  `RotationHandoffService.handle_capacity_rejection()` exists but has no caller.
- **Effort escalation** excludes the previous attempt's engine when the attempt
  crosses an effort tier; a same-tier `WORK` retry gets affinity instead.
- **Phase transitions** do not go through this selector: DESIGN, `build.decompose`,
  and REVIEW run through their own providers (for DESIGN, see
  [ADR-0027](0027-sovereign-design-provider.md)).

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

**Why wind-down is a boundary.** A runner that exits 75 has finished its last turn
cleanly and written its state; nothing is interrupted. The job settles as a
success, not a failure, so it does not consume the escalation ladder.

## Consequences

**Good.** Handoff cost is bounded and proportional to real events. Warm sessions
are preserved, which matters for both cost and quality. The "must differ"
constraints (verifier ≠ implementer, synthesizer ≠ interviewer) still deliver
cross-vendor independence where it counts, without paying for it every turn.

**Bad.** A single work item may be built entirely by one engine, so its
idiosyncrasies are not averaged out within that item. Mitigated by the mandatory
rotated verifier — the code is always read by a different vendor before it
integrates. (`build.verify` excludes the implementer's engine.)

## Alternatives rejected

- **Rotate every turn.** A handoff per turn: maximum cost and gate exposure for no
  gain in independence.
- **Rotate on every retry.** Throws away a warm session on a `WORK` failure that
  says nothing about engine health, and opens a circuit on a healthy engine.
- **Allow mid-turn rotation.** Creates a third state between `TurnCompleted` and
  failure that the ledger cannot represent.
