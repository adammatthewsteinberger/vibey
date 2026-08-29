# Ledger-Mediated Orchestration: Vendor-Independent Autonomous Software Delivery over a Pool of Coding Agents

**Abstract.** A single autonomous coding session is not autonomous software delivery:
sessions lose context across crashes, exhaust one vendor's capacity mid-task, and
carry no structure for the human decisions delivery legally and practically
requires. We present a ledger-mediated orchestration model in which all delivery
state is a function of an append-only ledger, $\mathrm{state}(t) =
f(\mathrm{ledger}_{\leq t})$, making engine handoff a scheduling event rather than a
loss of state. Work items are claimed from a PostgreSQL queue with
`FOR UPDATE SKIP LOCKED`, giving per-item mutual exclusion without global
coordination; delivery proceeds through a six-phase state machine whose four human
gates are exactly the fixed points where the ledger's open-question set must drain
to zero. We state the model's invariants, sketch the fairness and gate-soundness
arguments, and report the design running unattended across four heterogeneous
vendor engines.

## Introduction

Let an *engine* be an autonomous coding session runner over one vendor's model, and
let $E = \{e_1, \dots, e_m\}$ be a pool of such engines with independent failure and
capacity behavior. The delivery problem is to carry a specification from human
intent to deployed software using $E$, under three constraints that single-session
tooling violates: (i) no vendor session may be the source of truth; (ii) human
decisions must occur at defined points, not wherever a session happens to stall;
(iii) exhaustion of one vendor's capacity must not lose work.

## The ledger invariant

```latex
\begin{invariant}[Write-ahead intent]
Every decision, finding, and handoff is a row in an append-only ledger before it
takes effect; consequently $\mathrm{state}(t) = f(\mathrm{ledger}_{\leq t})$ for a
pure $f$, independent of any vendor session.
\end{invariant}
```

Crash recovery and engine handoff follow as corollaries: a successor engine
re-derives context from the ledger alone, so a mid-task credit exhaustion on $e_i$
reschedules the item onto $e_j$ with the open-question set intact.

## Queue semantics

Work items form a relation $Q$ in PostgreSQL. Workers claim with

```latex
\begin{verbatim}SELECT ... FOR UPDATE SKIP LOCKED\end{verbatim}
```

which yields two properties without any global lock: *mutual exclusion per item* —
at most one worker holds item $w$ at any instant — and *non-blocking progress* —
a worker never waits on a peer's claim, so throughput scales as
$\min(|Q|, |\mathrm{workers}|)$. Fairness follows from claim ordering over the
queue's arrival index: an item can be bypassed only while it is held, and holds are
bounded by the engine budget caps.

## The six-phase machine

$$\Sigma = \langle D, B, R, D_d, D_e, D_r \rangle$$

design, build, review, deploy-design, deploy-execute, deploy-review — with the
human-gated subset $G = \{D, R, D_d, D_r\}$.

```latex
\begin{invariant}[Gate soundness]
For every $\sigma \in G$, the transition out of $\sigma$ fires only when the
ledger's open-question set restricted to $\sigma$ is empty:
$\mathrm{open}(\sigma) = \varnothing$.
\end{invariant}
```

A review finding therefore cannot vanish into a transcript: it is a ledger row that
holds $\mathrm{open}(R) \neq \varnothing$, and the machine cannot leave $R$ until a
human closes it — reopening design when the finding demands it, which is a ledger
transition $R \to D$, not an ad-hoc prompt.

## Vendor independence

Budget caps are per-item and per-engine; capacity classification (waitable window
versus exhausted credits) is engine-local. Because of Invariant 1, the scheduler may
treat $E$ as interchangeable executors: the delivery semantics live entirely above
the vendor line. Empirically the same orchestration runs unchanged over four
engines — Claude, Codex, Cursor, and Gemini session runners — differing only in
their capacity lexicons.

## Related work

Queue-based job schedulers provide claims and retries but no delivery semantics;
agent frameworks provide sessions but bind state to one vendor's context window.
The exact-head release calculus (vibey-gh's companion paper) governs what happens
after this system emits code: the two compose at the pull request boundary.

## Conclusion

Putting the ledger — not the session — at the center makes autonomous delivery
survivable and auditable: engines become fungible, crashes become replays, and
human authority is a structural property of the state machine rather than a
prompt-engineering hope.

## References

- PostgreSQL Documentation, *SELECT ... FOR UPDATE SKIP LOCKED*, PostgreSQL Global Development Group.
- vibey-gh, *Exact-Head Evaluation: Sound and Terminating Autonomous Release Automation*, companion paper, 2026.
- The vibey repository: architecture documentation and decision records, 2026.
