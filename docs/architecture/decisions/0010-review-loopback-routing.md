# 0010 — Review loops back to design by default, to build on the fast path

**Status:** accepted · **Date:** 2026-08-14

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

The fast path is taken only when **every** open finding is classified `clear`.
`strict_loopback = true` in `vibey.toml` disables it entirely, restoring the
original specification exactly.

## What makes a finding `clear`

All four must hold — this is deliberately strict, because the cost of wrongly
skipping design is building the wrong thing again:

1. The desired end state is stated unambiguously.
2. It maps to an existing acceptance criterion, or the new criterion is obvious
   and testable.
3. No new NFR or constraint is implied.
4. It does not contradict a recorded `DecisionRecorded`.

Classification happens in `review.triage` at `HIGH` effort, escalating to `MAX`
for `critical` findings — it is a judgment call, and it is the judgment that
routes the entire next cycle, so it gets the best model available.

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
the four-condition bar, by `MAX` effort on critical findings, and by the fact that
a fast-path build that turns out ambiguous can still transition `② → ①` when an
item is `blocked_on_ambiguity` — the mistake is recoverable, one phase later.
