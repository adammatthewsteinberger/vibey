# 0010 — Review loops back to design by default, to build on the fast path

**Status:** accepted · **Date:** 2026-08-14

**Owes:** nothing — mechanism (ADR-0020)

## Context

The original specification states that Phase 3 loops back to Phase 1 when changes
are needed, and that Phase 2 re-enters from Phase 1 once details are clarified.
That gives the canonical cycle `③ → ① → ② → ③`.

In practice, review findings vary enormously in ambiguity. "The retry policy
should be bounded, but I'm not sure what the cap should be or how it interacts
with the outbox" genuinely needs a design conversation. "You misspelled 'receive'
in the header" does not — routing it through a full elicitation wastes the
developer's time, which is the scarcest resource in the loop.

## Decision

**Both edges exist. `③ → ①` is the default.**

```python
def next_phase_after_review(findings, *, strict_loopback: bool) -> Phase:
    if not findings:
        return Phase.DONE
    if strict_loopback:
        return Phase.DESIGN
    if any(f.ambiguity is Ambiguity.NEEDS_CLARIFICATION for f in findings):
        return Phase.DESIGN
    return Phase.BUILD          # fast path
```

This is `domain/phase.py::next_phase_after_review()`, called by `review.triage`.
In practice the empty case never reaches it: with no open findings the handler
enqueues `review.deployment_choice` instead, which asks the opt-in question from
[ADR-0014](0014-optional-visual-design-and-deployment-opt-in.md) before anything is
`DONE`. A `DESIGN` result enqueues `design.interview` at `cycle + 1`; a `BUILD`
result carries the accepted spec forward to `cycle + 1` and enqueues `build.plan`.

The fast path is taken only when **every** open finding is classified `clear`.
`strict_loopback = true` under `[project]` in `vibey.toml` is meant to disable it
entirely, restoring the original specification exactly. The key is parsed, but it
does not reach the router yet: `review.triage` reads `strict_loopback` from its job
payload, and `review.collect` enqueues the triage job without it, so the fast path
is always available today.

## What makes a finding `clear`

All four must hold — this is deliberately strict, because the cost of wrongly
skipping design is building the wrong thing again:

1. The desired end state is stated unambiguously.
2. It maps to an existing acceptance criterion, or the new criterion is obvious
   and testable.
3. No new NFR or constraint is implied.
4. It does not contradict a recorded `DecisionRecorded`.

Classification happens in `review.triage` as a deterministic check over the
finding text and the recorded decisions (`domain/review.py::check_clear_conditions`,
called by `triage_finding`) — no model call. It is a heuristic, and a partial one:
condition 1 fails on findings under three words or containing hedging phrases
("maybe", "not sure", "rethink", …); condition 3 fails on phrases that imply a new
NFR ("requests per second", "migrate to", …); condition 4 fails when the text names
a recorded decision's rejected alternative together with "switch"; condition 2 is
not checked yet (the accepted spec is passed in but unused).

Severity is classified the same way, by keyword (`classify_finding_severity`), and
sets the effort of the *next cycle's* first job: `MAX` when any finding is
`critical`, else `HIGH`, `STANDARD`, or `LOW` (`domain/effort.py::triage_required_effort`).

## Rationale

The default is the specified behavior because ambiguity is the common case and
re-interviewing is cheap relative to building the wrong thing twice. The fast path
exists because a system that treats a typo and an architectural rethink
identically will be experienced as bureaucratic and worked around.

The asymmetry is deliberate: **the failure mode of wrongly routing to DESIGN is a
few wasted minutes; the failure mode of wrongly taking the fast path is a wasted
build cycle.** So the bar for the fast path is four conjunctive conditions and the
default is always the safe edge.

## Consequences

**Good.** Trivial changes round-trip in minutes. Substantive changes get the
design conversation they need. The behavior is configurable for teams who want
the original strictness.

**Bad.** Triage misclassification sends work down the wrong path. Mitigated by
the four-condition bar, by running the follow-up work for critical findings at
`MAX` effort, and by the fact that
a fast-path build that turns out ambiguous can still transition `② → ①` when an
item is `blocked_on_ambiguity` — the mistake is recoverable, one phase later.
That recovery edge is guarded in `domain/phase.py` (`BUILD -> DESIGN` requires an
item blocked on ambiguity), but no BUILD handler marks an item that way yet, so
today the recovery happens at the next review.

**Bad.** A keyword heuristic misses ambiguity phrased any other way, so the fast path
is taken more often than the four conditions intend. Replacing the heuristic with a
real judgment behind the same function signature is open work.

## Alternatives rejected

- **Always `③ → ①` (the literal specification).** Kept as `strict_loopback`;
  rejected as the default because it routes a typo through an interview.
- **Always `③ → ②`.** Builds the wrong thing twice whenever a finding hides a design
  question.
- **Let the reviewing engine choose the edge.** Puts cycle routing in a model with
  no stated bar. The four conjunctive conditions are the bar, and they are testable
  in the domain.
