# 0005 — Smooth weighted round robin, not modulo rotation

**Status:** accepted · **Date:** 2026-08-14

## Context

Every phase rotates across engines. The set of eligible engines changes
continuously as circuits open (credits exhausted, rate-limit window) and close
(window reset, top-up). Engines are not equal: some are faster, cheaper, or
capable of higher effort tiers.

## Decision

**nginx's Smooth Weighted Round Robin**, over the *eligible* set, with effective
weights derived from health, fidelity, cost, and affinity.

```
for each selection:
    for e in eligible:  e.current += e.effective_weight
    winner = argmax(e.current)          # ties broken by a stable `order`
    winner.current -= sum(e.effective_weight for e in eligible)
```

## Rationale

`engines[i % len(engines)]` fails three ways here:

1. **The eligible set resizes.** Modulo over a shrinking list remaps every index,
   so the cursor jumps arbitrarily when a circuit opens — the opposite of fair.
2. **It ignores weight.** A developer's stated preference has nowhere to live.
3. **Naive weighted RR clumps.** Weights `{A:3, B:2, C:1}` produce `AAABBC` — three
   consecutive items to A, which is exactly the burst that exhausts A's
   rate-limit window while B and C idle. SWRR produces `ABACAB`.

Point 3 is not cosmetic. Vibey's whole reason for rotating is to spread load
across independent capacity pools; a scheduler that bursts defeats the purpose.

## Effective weight

```
effective = base × health × fidelity × cost × affinity
```

| Factor | Range | Meaning |
|---|---|---|
| health | 0.0–1.0 | 1.0 closed, 0.25 half-open, 0.0 open; decays on recent transient failures |
| fidelity | 0.5–1.0 | penalizes an engine that saturates below the requested effort |
| cost | 0.5–1.5 | relative $/Mtok, inverted; off by default |
| affinity | 1.0 or 2.0 | 2.0 when the engine holds a warm session and rotation is not forced |

`affinity` is what implements stickiness: ordinary retries stay put, and rotation
happens when something actually changed ([ADR-0007](0007-rotate-at-boundaries.md)).

## Consequences

**Good.** Deterministic, so testable. Six properties are enforced by Hypothesis:
no starvation, weight fidelity, smoothness, determinism, totality, exclusion
honored. Rotation state is a single integer per engine, updated in the same
transaction as the job lease, so a crash cannot advance the cursor without doing
the work.

**Bad.** More state than modulo, and the four factors are tuning knobs that can be
set badly. Mitigated by exporting `vibey_engine_selected_total` so the empirical
distribution is checkable against the intended weights in production, not just in
unit tests.

## Alternatives rejected

- **Modulo.** Above.
- **Random / weighted random.** Non-deterministic, so untestable by property, and
  it clumps by chance.
- **Least-loaded.** Requires a load signal vibey does not have — an engine's
  remaining quota is not observable until it is rejected.
- **Cost-optimal routing.** Would concentrate work on the cheapest engine until it
  runs dry, converting a fairness problem into a capacity problem. Cost is a
  *factor* here, deliberately not the objective.
