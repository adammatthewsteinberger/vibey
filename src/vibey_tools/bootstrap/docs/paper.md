# One Call, Fail Closed: A Cross-Cutting Bootstrap Layer for Cloud Workloads with Verifiable Delivery and Tamper-Evident Audit

**Abstract.** Every service in a cloud estate re-implements the same first hundred
lines — logging, configuration, secrets, telemetry — and every re-implementation is
another chance to fail *open*: a worker that starts without its Key Vault, logs
without its sink, or drops the audit record on the floor. vibey-bootstrap collapses
that surface to **one call** that assembles the chain logging → App Configuration +
Key Vault → Application Insights into a populated environment, under a single
discipline: **absence of a required dependency halts the start; degradation is
explicit, never silent.** Above the bootstrap sit delivery and audit primitives with
stated guarantees: a transactional **outbox** giving at-least-once delivery with
exactly-once *marking* over SQL; a **hash-chained audit log** in which record $r_i$
carries $H(r_{i-1} \| r_i)$ so truncation and tampering are detectable; bounded
**retry** with typed rate-limit callbacks that cannot mask the original error; and a
fan-out transport layer (blob, SQL, document, ADX, Event Hubs, SIEM) behind one
interface. The layer is enforced at 100% per-module coverage, and its own delivery
runs on the exact-head release calculus of its sibling tooling.

## Introduction

Let a workload's preconditions be $P = \{p_1, \dots, p_k\}$ — reachable config,
resolvable secrets, an attached telemetry sink. The classic failure is the service
that starts with $P' \subset P$ satisfied and discovers the difference at 3 a.m.,
one request at a time.

```latex
\begin{invariant}[Fail closed]
Bootstrap completes only when every required precondition is proven; a missing
$p_i$ halts startup with $p_i$ named. Optional capabilities degrade EXPLICITLY —
a disabled feature is a recorded decision, never a silent absence.
\end{invariant}
```

The `failclose` primitives extend the discipline past startup: guarded operations
refuse to proceed when their invariants lapse mid-flight.

## The outbox

Side effects and state changes must not race: the outbox writes intent
transactionally beside the state change, and a separate dispatcher delivers.

```latex
\begin{theorem}[Delivery]
Every committed intent is delivered at least once, and marked delivered exactly
once: dispatch marks under the same transactional discipline that recorded the
intent, so a crash between delivery and marking yields a retry, never a loss.
\end{theorem}
```

## Tamper-evident audit

Audit records form a hash chain: $c_0 = H(r_0)$, $c_i = H(c_{i-1} \| r_i)$. A
verifier recomputes the chain; any edit, insertion, or truncation breaks every
subsequent link.

```latex
\begin{invariant}[Chain integrity]
The audit trail is append-only and chained: the validity of record $r_n$ attests
the integrity of all $r_{i<n}$. Verification is offline and requires no trust in
the writer.
\end{invariant}
```

## Bounded retry with honest errors

Retries are built once (`build_retry`): typed retryable exceptions, exponential
bounds, counter namespaces for observability, and rate-limit callbacks with one
subtle guarantee proven in test — **a callback that raises never masks the original
error**. Unbounded or error-swallowing retry is how transient faults become
permanent mysteries.

## Transports

One emission interface fans out to blob, SQL, document stores, ADX, Event Hubs, and
SIEM endpoints (Sumo Logic, Panther); each transport is optional-by-extra, so a
service's dependency tree carries exactly what its configuration uses — the
zero-assumption posture of the no-guarantees doctrine applied to dependencies.

## Related work

The exact-head release calculus (vibey-gh) delivers this library; the ledger
principle it shares with the orchestration paper (vibey) appears here twice, as the
outbox and as the audit chain — the same append-before-act discipline at two scales.

## References

- vibey-gh, *Exact-Head Evaluation*; vibey, *Ledger-Mediated Orchestration* — companion papers, 2026.
- This repository: vibey_bootstrap/db/outbox.py, vibey_bootstrap/audit/, vibey_bootstrap/retry/, and their tests, 2026.
