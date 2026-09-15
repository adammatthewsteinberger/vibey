# Ledger-Mediated Orchestration: Vendor-Independent Autonomous Software Delivery over a Pool of Coding Agents

**Abstract.** A single autonomous coding session is not autonomous software delivery:
sessions lose context across crashes, exhaust one vendor's capacity mid-task, and
carry no structure for the human decisions delivery legally and practically
requires. We present a ledger-mediated orchestration model in which all delivery
state is a function of an append-only ledger, $\mathrm{state}(t) =
f(\mathrm{ledger}_{\leq t})$, making engine handoff a scheduling event rather than a
loss of state. Work items are claimed from a PostgreSQL queue with
`FOR UPDATE SKIP LOCKED` under renewable leases, giving per-item mutual exclusion
without global coordination; a handoff between engines is admitted only by a pure,
model-free no-loss predicate over the ledger; and delivery proceeds through a
six-phase state machine whose four human gates each require both an empty
ledger-derived open set and an explicit recorded human verdict. We state the model's
invariants, sketch the fairness and gate-soundness arguments, and describe the
engine pool the design is validated against: four paid vendor session runners and
an opt-in local, sovereign engine.

*Artifacts.* This paper is typeset from `docs/paper.md` and published as
[PDF](https://the-vibey-project.github.io/vibey/main/paper.pdf) and
[HTML](https://the-vibey-project.github.io/vibey/main/paper/). The complete
documentation is published as a book:
[PDF](https://the-vibey-project.github.io/vibey/main/book.pdf),
[EPUB](https://the-vibey-project.github.io/vibey/main/book.epub) and
[print HTML](https://the-vibey-project.github.io/vibey/main/book-print.html).

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

The invariant is enforced, not conventional: the event relation carries database
rules that turn every `UPDATE` and `DELETE` into a no-op, and the per-project sequence
number is claimed inside the same transaction as the insert, so every ledger range
has a well-defined digest. Corrections are new events that supersede prior ones. The
function $f$ is a set of pure projections — open items, the decision log, the cost
report — computed from the event sequence alone.

Crash recovery and engine handoff follow as corollaries: a successor engine
re-derives context from the ledger alone, so a credit exhaustion on $e_i$ between
turns of an item reschedules the item onto $e_j$ with the open-question set intact.

## The no-loss handoff gate

A handoff from $e_i$ to $e_j$ carries a *brief* $\beta$: objective, constraints, done
and remaining work, open questions, decisions, assumptions, findings, artifacts, and a
reference $\rho$ to the ledger range it summarises. The brief is admitted only if a
pure predicate $\mathrm{gate}(\mathrm{ledger}_{\rho}, \beta)$ holds, evaluated
without any model call.

```latex
\begin{invariant}[No loss]
Let $\mathrm{open}_k(\rho)$ be the ids opened by event kind $k$ in range $\rho$ and
not closed or superseded. The gate holds iff $\mathrm{open}_k(\rho) \subseteq
\mathrm{ids}_k(\beta)$ for $k \in \{$questions, decisions, assumptions, findings,
artifacts$\}$ (R2--R5, R7); every remaining-work item of the last verdict appears in
$\beta$ (R1); the digest of $\rho$ recomputed from the ledger equals the digest
carried by $\beta$ (R6); the budget carried by $\beta$ agrees with the ledger's (R8);
every hard constraint of the specification is restated (R9); and no free-text field
of $\beta$ carries a tool grant, a permission change, or an acceptance-criteria
mutation (R10).
\end{invariant}
```

The gate has modes. In *strict* mode all ten rules apply, and a failing brief is
regenerated up to three times. It then escalates to *full-transcript* mode, which
makes the brief advisory: the successor is to work from the whole range $\rho$, so the
gate stops checking R1--R5, R7 and R9, while R6, R8 and R10 still run, because they
check facts about the range and the brief's containment rather than its completeness.
In the current implementation the range reaches the successor as a file rather than
inline: the full ledger is written into the receiving worktree and the seed prompt
names it, so in this mode completeness rests on the successor reading that file, not
on the gate. Inlining the range into the seed, or keeping the closure rules enabled
until it is inlined, is open work. Further failure parks the item on a *human* gate; a
fourth, *forced* mode is reserved for an explicit operator override. A handoff that
fails the gate is therefore a retry, an escalation, or a human decision — never a
silent partial.

## Queue semantics

Work items form a relation $Q$ in PostgreSQL. Workers claim with

```latex
\begin{verbatim}SELECT ... FOR UPDATE SKIP LOCKED\end{verbatim}
```

which yields two properties without any global lock: *mutual exclusion per item* —
at most one worker holds item $w$ at any instant — and *non-blocking progress* —
a worker never waits on a peer's claim, so throughput scales as
$\min(|Q|, |\mathrm{workers}|)$.

Claims are ordered by $(\mathrm{priority}\downarrow, \mathrm{run\_after}\uparrow,
\mathrm{id}\uparrow)$ within a project and exclude items whose dependencies have not
succeeded. Within one priority class an item can be bypassed only while it is held,
and every hold is bounded by a lease: a claim sets $\mathrm{lease\_expires\_at} =
\mathrm{now} + L$, a live worker renews it, and a reaper returns any expired lease to
the ready state. A crashed worker therefore costs at most $L$ of delay and never a
lost item. Across priority classes the discipline is strict priority, not arrival
order. Because workers die and leases expire, every job is idempotent under replay.

## The six-phase machine

$$\Sigma = \langle D, B, R, D_d, D_e, D_r \rangle$$

design, build, review, deploy-design, deploy-execute, deploy-review — with the
human-gated subset $G = \{D, R, D_d, D_r\}$.

```latex
\begin{invariant}[Gate soundness]
For every $\sigma \in G$ the exit guard is a conjunction of an explicit human verdict
recorded as a ledger row and, where the phase accumulates open items, the emptiness
of a ledger-derived open set. $D \to B$ requires at least one acceptance criterion,
every criterion mapped, and an accepting verdict; $R \to \mathrm{Done}$ requires
$\mathrm{open}_{\mathrm{findings}}(R) = \varnothing$ and an accepting verdict; $D_d
\to D_e$ requires the deployment specification accepted and consent recorded; $D_r
\to \mathrm{Done}$ requires the demonstration accepted. Emptiness is never
sufficient: no gate exits on the absence of objections alone.
\end{invariant}
```

A review finding therefore cannot vanish into a transcript: it is a ledger row that
holds $\mathrm{open}(R) \neq \varnothing$, and the machine cannot leave $R$ for
completion until a human closes it. Loop-back is a routing decision over the
findings: an unambiguous finding routes $R \to B$, and a finding that needs
clarification, or a project configured for strict loop-back, routes $R \to D$. Both
are ledger transitions, not ad-hoc prompts.

A gate is not a blocked thread. A handler that needs a human returns a *park* value;
the worker records a gate row, marks the item as awaiting a human, releases its
lease, and claims the next item. The answer is itself a ledger row that re-readies
the item. Human latency therefore never holds a queue slot, and the non-blocking
progress of the previous section survives humans in the loop.

Two refinements do not change the analysis. An optional visual-design interstitial
$V$ may be inserted between $D$ and $B$ on explicit opt-in; it is human-gated on the
same terms, exiting only when the visual plan is accepted or explicitly waived. The
deployment triple $\langle D_d, D_e, D_r \rangle$ is entered only on an explicit
opt-in recorded in the ledger; declining records a successful local completion.

## Vendor independence

Budget caps are per item (turns) and per cycle (dollars), summed from the cost the
engines report on each completed turn; engines carry cost rates, not caps. An
exhausted budget parks the item before a session starts, never after. Capacity
classification is engine-local and three-valued — available, a waitable window with
an optional reset time, or exhausted credits — and the credits state deliberately has
no clock: the type has no reset field, and a property test forbids one.

Because of the ledger invariant and the no-loss gate, the scheduler may treat $E$ as
substitutable executors and choose among them by policy rather than by state: the
delivery semantics live entirely above the vendor line. The same orchestration is
written once over five engines — the Claude, Codex, Cursor and Antigravity/Gemini
session runners, which form the paid pool, and a local model runner that is an
opt-in standby for the build phase and can serve the design interview with no vendor
account at all — differing only in their capacity lexicons and in whether a credit
balance exists.

### Engine selection

At each rotation point the eligible engines — installed, conformant, authenticated,
circuit not open — are ranked by smooth weighted round robin. Each candidate carries
an effective weight $w_i = \max\bigl(1, \mathrm{round}(b_i \cdot h_i \cdot f_i \cdot
c_i \cdot a_i)\bigr)$ for base weight $b_i$, health $h_i$ from a per-engine circuit
breaker, fidelity $f_i$ of the engine's effort projection to the requested effort, a
cost factor $c_i$ (fixed at 1 in the current implementation), and a warm-session
affinity $a_i$. The selector adds $w_i$ to each candidate's running total, picks the
maximum, and subtracts $\sum_i w_i$ from the winner, so the sequence is deterministic
and spreads load in proportion to weight without bursts. Rotation fires only at
boundaries — a new item, a capacity rejection (which excludes the rejecting engine),
a graceful wind-down, an effort escalation, an engine crash, or a phase transition —
and never inside a turn, so every handoff has a well-defined ledger range $\rho$.

## Validation

The model is validated at three levels. At the *property* level, the gate, the phase
guards and the selector are pure functions under a 100% branch-coverage floor per
architectural layer, with property tests on the selector and the credits type. At the
*chaos* level, concurrent workers process a job set against a real PostgreSQL while
each randomly abandons claimed jobs mid-flight and a concurrent reaper reclaims the
expired leases; the verified property is no double execution, no lost job, and every
job terminal. At the *live* level, a runbook drives one project from design through
build and review to local completion on two paid engines, `claudeloop` and
`agyloop`, including a forced rotation between them. Live runs over the other
engines rest today on a scripted-binary conformance suite that asserts each runner's
flags, run-directory shape, event vocabulary, capacity mapping and completion marker
against the installed binary; they are not yet reported here.

## Related work

Queue-based job schedulers built on `SKIP LOCKED` provide claims, leases and retries
but no delivery semantics; the ledger here is event sourcing applied above the queue,
with the write-ahead discipline of ARIES and the lease bound of Gray and Cheriton.
Agent frameworks such as SWE-agent and AutoGen provide sessions and tool loops but
bind state to one vendor's context window; here the session is disposable and the
ledger is not. Selection reuses nginx's smooth weighted round robin and the circuit
breaker pattern. The exact-head release calculus — the companion paper of `vibey-gh`,
in this repository at `src/vibey_tools/gh/docs/paper.md` — governs what happens after
this system emits code: the two compose at the pull request boundary.

## Conclusion

Putting the ledger — not the session — at the center makes autonomous delivery
survivable and auditable: engines become fungible, crashes become replays, and
human authority is a structural property of the state machine rather than a
prompt-engineering hope.

## References

- PostgreSQL Global Development Group, *SELECT — The Locking Clause* (`FOR UPDATE SKIP LOCKED`, available since PostgreSQL 9.5). PostgreSQL documentation, `https://www.postgresql.org/docs/current/sql-select.html`.
- M. Fowler, *Event Sourcing*, 2005. `https://martinfowler.com/eaaDev/EventSourcing.html`.
- P. Helland, "Immutability Changes Everything," *Communications of the ACM* 59(1):64–70, 2016. doi:10.1145/2844112.
- C. Mohan, D. Haderle, B. Lindsay, H. Pirahesh, and P. Schwarz, "ARIES: A Transaction Recovery Method Supporting Fine-Granularity Locking and Partial Rollbacks Using Write-Ahead Logging," *ACM Transactions on Database Systems* 17(1):94–162, 1992. doi:10.1145/128765.128770.
- C. Gray and D. Cheriton, "Leases: An Efficient Fault-Tolerant Mechanism for Distributed File Cache Consistency," *Proceedings of the 12th ACM Symposium on Operating Systems Principles*, 1989, pp. 202–210. doi:10.1145/74850.74870.
- nginx, smooth weighted round-robin upstream balancing, introduced in nginx 1.3.1 (2012), `ngx_http_upstream_round_robin.c`.
- M. T. Nygard, *Release It! Design and Deploy Production-Ready Software*, 2nd ed., Pragmatic Bookshelf, 2018 (the circuit breaker pattern).
- J. Yang, C. E. Jimenez, A. Wettig, K. Lieret, S. Yao, K. Narasimhan, and O. Press, "SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering," *NeurIPS*, 2024. arXiv:2405.15793.
- Q. Wu et al., "AutoGen: Enabling Next-Gen LLM Applications via Multi-Agent Conversation," 2023. arXiv:2308.08155.
- A. M. Steinberger, *Exact-Head Evaluation: Sound and Terminating Autonomous Release Automation for Collaborative Repositories*, companion paper, `src/vibey_tools/gh/docs/paper.md`, the-vibey-project/vibey, 2026.
- The vibey repository: architecture decision records, `https://github.com/the-vibey-project/vibey/tree/main/docs/architecture/decisions`, 2026.
