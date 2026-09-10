# The Transplantable Session Runner: Window-versus-Credit Discrimination and Safe Resumption for Autonomous Claude Code Sessions

**Abstract.** claudeloop is the original of a five-runner family, and its central
claims are the ones its siblings transplanted: an onion architecture whose pure core
decides *run, wait, or stop* from values alone; a capacity discrimination that never
confuses an exhausted **rate-limit window** (waitable, deadline-bounded) with exhausted
**credits** (never waitable); and **safe resumption across usage windows** — a session
interrupted by capacity resumes with its intent intact, because state is a function of
an append-only ledger, $\mathrm{state}(t) = f(\mathrm{ledger}_{\leq t})$, not of any
vendor session. We state the transplant thesis — one formal core, $N$ vendors, with
vendor variance confined to capacity lexicons and transports — and the evidence: four
independent retargets (Codex, Cursor, Gemini, local Qwen) preserving the invariants
unchanged.

## Introduction

An autonomous session over a metered vendor agent must answer three questions without
a human: may it act now, when should it try again, and when is it actually done?
claudeloop's design answers them once, in a dependency-free core, and treats the
vendor as a replaceable adapter. The wager — made here first — is that EVERYTHING
vendor-specific fits in two places: the classification lexicons that read the vendor's
failure text, and the transport that speaks to it.

## Window versus credits

The discrimination this family is named for:

$$\kappa(\mathrm{failure\ text}) \in \{\mathsf{window},\ \mathsf{credits}\}$$

```latex
\begin{invariant}[Waitability]
$\mathsf{window}$ is waitable with a deadline: the window will reopen, so a bounded
probe re-tests capacity and the excursion is capped by $W_{\max}$. $\mathsf{credits}$
is never waitable: no amount of waiting refills a balance, and treating billing as a
window is an unbounded hang wearing a hopeful face. Unclassifiable text is treated as
$\mathsf{credits}$ — pessimism is the only safe default for unknown failures.
\end{invariant}
```

## Safe resumption

```latex
\begin{invariant}[Resumption]
A run interrupted at any point — capacity, crash, operator stop — resumes from the
ledger alone: open intent, spend so far, savepoints, and verdict history are rows,
not session memory. Consequently a usage-window interruption costs the wait and
nothing else.
\end{invariant}
```

Git savepoints anchor the working tree at meaningful steps; `unwind` is a ledger
operation, refused while a run is active.

## Bounded runs and honest completion

Runs are admitted under the explicit bound vector (turns, dollars, per-turn watchdog,
stall watchdog, maximum wait) with preemptive budget enforcement; completion requires
agreement of independent evidence — verdict fence, done marker, empty-turn discipline,
plan reconciliation — under the family theorem that **capacity outranks completion**:
a done-claim from a starved model is recorded, never believed.

## The transplant thesis, tested

Four retargets falsifiable-tested the wager: codexloop (OpenAI Codex; its lexicon must
never read `insufficient_quota` as a waitable `rate_limit_exceeded`), cursorloop
(Cursor's agent and Cloud API), agyloop (Gemini's quotas force a five-member verdict
and adaptive probes — the one place the core grew), and qwenloop (a local model, where
capacity is hardware, not billing). In every case the invariants above survived
unchanged; only lexicons and transports moved. The orchestration layer (vibey)
schedules across the resulting pool precisely because the runners are behaviorally
interchangeable.

## References

- cursorloop, *Capacity-Outranks-Completion*; agyloop, *Quota-Aware Autonomy* — sibling papers, 2026.
- The vibey repository, *Ledger-Mediated Orchestration*, companion paper, 2026.
- This repository: the architecture decision records; docs/usage.md, 2026.
