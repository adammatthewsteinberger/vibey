# Capacity-Outranks-Completion: Bounded Autonomous Sessions over a Metered Coding Agent

**Abstract.** Autonomous coding sessions over metered vendor agents fail in two
characteristic ways: they block forever on interactive prompts nobody will answer, and
they trust completion claims emitted by a model that was starved of capacity. We
present the session-runner design behind cursorloop, in which every run is bounded by
an explicit vector $(T, D, \tau, \sigma, W)$ — turns, dollars, turn-timeout, stall-
timeout, and maximum wait — capacity classification is a configurable lexicon over
vendor messages partitioning failures into *waitable windows* and *non-waitable
exhaustion*, and completion requires agreement between independent evidence sources
under the invariant that **capacity verdicts outrank completion claims**. We state the
never-blocking property, the bounded-wait discipline, and the audit model
($\mathrm{state}(t)=f(\mathrm{ledger}_{\leq t})$ over an append-only JSONL trail), and
report the design running unattended against the Cursor agent and its Cloud Agents API.

## Introduction

Let a session be a sequence of agent turns $u_1, u_2, \dots$ against a metered vendor.
Unattended operation imposes three requirements that interactive tooling never meets:
(i) **no turn may wait on human input** — an unanswered prompt is an unbounded hang;
(ii) **every resource the vendor meters must be bounded above** by the operator, not
the model; (iii) **the run's outcome must be auditable** from durable state, not from a
transcript in a vendor session.

## The bound vector

A run is admitted only under an explicit bound vector:

$$\beta = (T_{\max},\ D_{\max},\ \tau_{\mathrm{turn}},\ \sigma_{\mathrm{stall}},\ W_{\max})$$

turns, dollars, per-turn watchdog, output-silence watchdog, and the ceiling on any
single capacity wait. Each component maps to a flag and a `CURSORLOOP_*` variable; the
run terminates at the FIRST bound reached, and the terminating bound is recorded in
the ledger. The budget invariant is preemptive: the ledger stops the run *before* an
overrun, never after.

## Capacity classification and the waiting policy

Vendor failure text is classified by two configurable lexicons into a three-valued
capacity verdict:

$$\kappa \in \{\mathsf{available},\ \mathsf{window},\ \mathsf{exhausted}\}$$

```latex
\begin{invariant}[Bounded waiting]
Only $\kappa = \mathsf{window}$ may enter the waiting state, and every wait carries a
deadline: the probe re-tests capacity and the excursion is capped by $W_{\max}$.
$\kappa = \mathsf{exhausted}$ (credits) is never waitable-with-a-deadline: no amount
of waiting refills a balance, so the run fails fast with the reason recorded.
\end{invariant}
```

Because the lexicons are configuration, a vendor rewording its rate-limit copy is a
config edit, not a code release.

## Never blocking

```latex
\begin{invariant}[No interactive waits]
No execution path may block on standard input: managed hooks pre-answer interactive
prompts, the session preamble declares unattended operation, non-interactive tool
variants are preferred, and the two watchdogs $(\tau_{\mathrm{turn}},
\sigma_{\mathrm{stall}})$ convert any residual hang into a loud, bounded failure.
\end{invariant}
```

## Completion under starvation

A completion claim is accepted only when independent evidence agrees: the structured
verdict fence, the explicit done marker, the empty-turn discipline (a producing-nothing
turn counts against completion), and plan reconciliation against what the session
reported doing.

```latex
\begin{theorem}[Capacity outranks completion]
A completion claim observed while $\kappa \neq \mathsf{available}$ is recorded but not
believed: a starved model emits plausible final output, so termination by capacity is
always attributed to capacity, never laundered into success.
\end{theorem}
```

## Audit model

Every turn, state transition, capacity verdict, and spend entry is one line of JSON in
an append-only trail under the run directory, with secrets redacted before write:
$\mathrm{state}(t) = f(\mathrm{ledger}_{\leq t})$. Git savepoints at meaningful steps
make rollback a ledger operation (`unwind`), refused while a run is active.

## Related work

The sibling runners (claudeloop, codexloop, agyloop, qwenloop) instantiate the same
formal core over different vendors, differing in their capacity lexicons and
transports; the ledger-mediated orchestration above them (the vibey paper) schedules
work across the pool, and the exact-head release calculus (the vibey-gh paper) governs
what happens when a session's output becomes a pull request.

## References

- The vibey repository, *Ledger-Mediated Orchestration*, companion paper, 2026.
- vibey-gh, *Exact-Head Evaluation*, companion paper, 2026.
- This repository: docs/architecture/run-loop.md, docs/guides/rate-limits-and-credits.md, 2026.
