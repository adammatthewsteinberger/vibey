# Quota-Aware Autonomy: Adaptive Waiting and Drift-Gated Vendor Surfaces for an Unattended Gemini Session Runner

**Abstract.** Running autonomous coding sessions against Google's Gemini models poses
two problems its sibling vendors do not: capacity is governed by *per-model,
per-window quotas* whose reset behavior is observable but not contractual, and the
vendor exposes two divergent API planes (Developer and Vertex) whose generated
surfaces drift. We present agyloop's answers: a five-member capacity state
$\mathcal{K} = \{\mathsf{available}, \mathsf{window}, \mathsf{quota},
\mathsf{exhausted}, \mathsf{unknown}\}$ with quota-aware probes that *learn* reset
timing from observation while every wait stays deadline-bounded; a generated REST
surface guarded by a **drift gate** that fails CI when the vendor's published schema
diverges from the generated client; and the family's shared invariants — never
blocking, capacity-outranks-completion, and the append-only audit ledger
$\mathrm{state}(t) = f(\mathrm{ledger}_{\leq t})$ — instantiated over the Antigravity
SDK transport. Auth is proven, never guessed: the doctor refuses to choose between
Developer and Vertex lanes when both look possible.

## Introduction

The session-runner family (claudeloop, codexloop, cursorloop, agyloop, qwenloop)
shares one formal core: bounded runs, three-way capacity classification, evidence-based
completion, ledger audit. Each instantiation earns its existence by what its vendor
does differently. For Gemini the differences are structural: quotas with windowed
resets rather than flat rate limits, two authentication universes (Developer API key
versus Vertex application-default credentials), and a REST plane broad enough that a
hand-written client rots — hence generation, and hence the gate on generation drift.

## The five-member capacity state

Binary rate-limit classification is insufficient under quotas. agyloop's verdict set:

$$\mathcal{K} = \{\mathsf{available},\ \mathsf{window},\ \mathsf{quota},\ \mathsf{exhausted},\ \mathsf{unknown}\}$$

- $\mathsf{window}$: a conventional rate-limit — waitable with a fixed bounded probe.
- $\mathsf{quota}$: a per-model, per-window quota — waitable, but the probe is
  **adaptive**: observed reset behavior tunes the next probe's timing, so the runner
  neither hammers a closed window nor sleeps past an open one.
- $\mathsf{exhausted}$: billing — never waitable; fail fast with the reason recorded.
- $\mathsf{unknown}$: unclassifiable vendor text — treated pessimistically as
  non-waitable, because optimism about an unknown failure is how runs hang.

```latex
\begin{invariant}[Deadline-bounded adaptivity]
Adaptive probing may tune WHEN the next probe fires, never WHETHER the excursion
ends: every waiting excursion, adaptive or fixed, is capped by the run's
$W_{\max}$.
\end{invariant}
```

## The drift gate

The Developer and Vertex REST clients are generated from the vendor's published
surface. Generation without verification merely moves the rot: the **drift gate**
regenerates in CI and fails on any divergence between the committed client and the
current schema (ADR 0015), so a vendor-side change is a loud red build, never a
silent runtime 400.

```latex
\begin{invariant}[Proven auth]
The runner never guesses between the Developer and Vertex lanes. The doctor reports
exactly what each credential source proves; when both look possible, it refuses to
choose and says so — ambiguity is surfaced to the operator, not resolved by
optimism.
\end{invariant}
```

## Shared core, instantiated

The family invariants hold unchanged: no execution path blocks on stdin; every run is
admitted under an explicit bound vector (turns, dollars, per-turn and stall watchdogs,
maximum wait); completion requires agreement of independent evidence and **capacity
outranks completion** — a done-claim from a quota-starved model is recorded, not
believed; every turn, verdict, and spend entry is one JSONL line in the run ledger,
with git savepoints making rollback (`unwind`) a ledger operation refused during an
active run.

## Related work

The sibling papers formalize the shared core (cursorloop: the bound vector and
capacity-outranks-completion) and the layers around it (vibey: ledger-mediated
orchestration across the pool; vibey-gh: the exact-head release calculus receiving the
sessions' output). This paper's contributions are the quota-adaptive probe under a
hard deadline and the drift-gated generated surface.

## References

- cursorloop, *Capacity-Outranks-Completion*, companion paper, 2026.
- The vibey repository, *Ledger-Mediated Orchestration*, companion paper, 2026.
- This repository: ADR 0015 (generated Gemini REST with a drift gate), docs/usage.md, 2026.
