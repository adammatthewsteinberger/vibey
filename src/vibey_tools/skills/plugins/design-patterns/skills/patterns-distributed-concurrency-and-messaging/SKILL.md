---
name: patterns-distributed-concurrency-and-messaging
description: "Use when working on distributed data, failure handling, concurrency, or messaging: saga, outbox, CQRS and event sourcing, resilience patterns (circuit breaker, retry with backoff and jitter, bulkhead, timeout, idempotency), concurrency patterns (actors, structured concurrency, worker pools, CSP channels), and integration and messaging patterns."
---

# Design Patterns: Distributed Data, Resilience, Concurrency, and Messaging

> **Part 3 of 5** of the *Design Patterns* reference (plugin `design-patterns`), covering §8–§11. Sibling skills: `patterns-foundations-gof-and-alternatives` (§0–§5), `patterns-architectural` (§6–§7), `patterns-llm-agentic-and-legacy-migration` (§12–§13), `patterns-reference` (§14–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Verified August 2026. See §17 → `patterns-reference` for the currency snapshot and what goes stale first.

> **How to read this.** Reference, not a catalogue. **The 23 GoF patterns are freely
> available with diagrams and code samples everywhere** — this document does not reproduce
> them. It addresses the harder questions: which ones still earn their keep, which ones
> are artifacts of 1994's languages, what replaced them, where the genuinely useful
> modern patterns live, and **when not to use any of them.**
>
> Three markers:
> - **[DURABLE]** — design forces that recur regardless of language or era.
> - **[VERSIONED]** — language features, framework practice, emerging pattern languages.
> - **[CONTESTED]** — genuine disagreement, and **this domain has more of it than most.**
>
> **⚠️ GOTCHA** boxes mark where applying a pattern makes things worse.
>
> **The three framings that organize everything below:**
> 1. **Patterns are a vocabulary, not a construction kit.** Their durable value is that
>    "this is a circuit breaker" communicates a design in four words. **Their value was
>    never that you should go looking for places to install them** — and treating the
>    catalogue as a checklist is the single most damaging misreading of the entire
>    literature (§14 → `patterns-reference`).
> 2. **A pattern is a solution to a *force*, and the force is what's durable — not the
>    implementation.** Many GoF implementations were workarounds for what C++ and Java
>    couldn't express in 1994. **The forces persisted; the workarounds became language
>    features** (§3 → `patterns-foundations-gof-and-alternatives`). Learn to see the force.
> 3. **Over-application is the dominant failure mode, by a wide margin.** The cost of a
>    missing pattern is some duplication you can refactor later. **The cost of an unneeded
>    pattern is permanent indirection that every future reader must decode.** As one
>    2026 practitioner framing puts it: add a pattern only when it removes duplication,
>    isolates change, or clarifies intent — **and if introducing it makes the code harder
>    to explain, it's the wrong moment for it.**

---

## §8. Distributed Data Patterns

**[DURABLE in force, VERSIONED in tooling.] These exist because the moment you split your
data across services you lose ACID transactions, and everything here is a way of buying
back some consistency guarantee.**

| Pattern | What it solves | ⚠️ Costs |
|---|---|---|
| **Transactional Outbox** | **The dual-write problem** — write to your DB *and* publish an event atomically, by writing the event to an outbox table in the same transaction and relaying it after | A relay process; at-least-once delivery |
| **Inbox / Idempotent Consumer** | Deduplicating received messages | Storage of processed IDs |
| **Idempotency keys** | Preventing duplicate processing of client requests | Key management and retention |
| **Saga** | A business operation spanning services, as a sequence of local transactions with **compensating transactions** for rollback | ⚠️ **Compensation is not rollback** — the intermediate states were visible |
| **CQRS** | Separate write and read models, so each can be shaped and scaled independently | ⚠️ Two models, and eventual consistency between them |
| **Event Sourcing** | State as an append-only log of events; current state is a fold | ⚠️ **The highest-cost pattern here.** Schema evolution of events, replay complexity, and a genuinely different mental model |
| **CDC / log tailing** | Publishing changes by reading the DB transaction log (Debezium) | Coupling to the DB's log format |

> **⚠️ GOTCHA — the dual-write problem is the one to internalize**, because it's how
> real systems lose data quietly. A documented case: a team migrating to microservices
> **immediately started losing orders — the order service committed a row to its own
> database, then called an inventory service to reserve stock, and the two operations were
> not atomic.** Any failure between them leaves the system inconsistent with no error
> raised. **The outbox pattern exists for exactly this, and skipping it is the most common
> serious mistake in event-driven systems.**

**Saga: choreography vs. orchestration.** Choreography — services react to each other's
events, no coordinator. Orchestration — an explicit coordinator drives the steps. **A
reasonable published heuristic: choreography up to 2–3 steps; orchestration at 4+ or when
the logic is complex**, because choreographed flows past that point become impossible to
reason about. **[VERSIONED] Dedicated workflow engines (Temporal, and similar) are
increasingly the answer for orchestration** rather than hand-rolling it.

> **⚠️ GOTCHA — Event Sourcing is dramatically over-applied, and the cautionary tales are
> consistent.** One documented case: **a user-profile service — GET/PUT on name, email,
> address, a team of three juniors — chose full Event Sourcing. Result: four months for a
> CRUD that should have taken two weeks, state-reconstitution bugs that were impossible to
> debug, and a rewrite as conventional REST in three weeks.** The published rule of thumb
> worth carrying: **start with the simplest pattern that meets the need — plain event
> notification covers most cases, CQRS most of the remainder, and Event Sourcing is for
> the small fraction where a full audit trail is a non-negotiable business requirement.**

**[DURABLE] Compose deliberately.** Event Sourcing + CQRS + Outbox is a genuinely common
production combination — **but layer them on only when the system needs them**, starting
from pub/sub as the primitive.

---

## §9. Resilience Patterns

**[DURABLE] These assume failure is normal, which in distributed systems it is.**

**Circuit Breaker** — after consecutive failures cross a threshold, stop sending requests
and fail fast, allowing the downstream to recover. Closed → open → half-open. **⚠️ Its real
purpose is preventing cascading failure**, and it belongs on any synchronous call to an
external dependency. ⚠️ **Notably under-adopted relative to how essential it is** — survey
work has found it substantially less used than API gateways in microservice deployments,
which weakens resilience in exactly the systems that need it.

**Retry with exponential backoff and jitter** — ⚠️ **jitter is not optional**;
synchronized retries are how you turn a blip into a thundering herd. **Only retry
idempotent operations, and only on transient failures.**

**Bulkhead** — isolate resource pools (separate connection pools or thread pools per
downstream) so one saturated dependency can't consume everything.

**Timeouts** — ⚠️ **the most under-set configuration in software.** An unbounded wait is a
resource leak with extra steps. **Every network call needs one.**

**Also**: **rate limiting / throttling**, **load shedding** (⚠️ **rejecting work early
beats collapsing under it**), **graceful degradation**, **dead letter queues**,
**health checks and readiness probes**, and the **Ambassador** pattern for putting retry,
logging, and monitoring beside the application rather than inside it.

**[DURABLE] The combination is what works**: timeout + retry with jitter + circuit breaker
+ bulkhead + fallback. Any one alone leaves a gap.

---

## §10. Concurrency Patterns

**[DURABLE] Ordered by preference, and the order is the advice.**

**Don't share** — immutability, thread confinement, actors, per-key sharding. ⚠️ **Almost
always the right answer and the least explored one.**
**Message passing** — actors (Erlang/Akka), CSP channels (Go), queues between stages.
**Structured concurrency** — ⚠️ **the most important recent idea here**: child tasks cannot
outlive their scope, so cancellation and error propagation are well-defined rather than
ad hoc. Now in Kotlin, Swift, Java (virtual threads and scopes), Python's TaskGroups, and
Trio's nursery concept where it originated.
**Producer-consumer with backpressure** — ⚠️ **an unbounded queue is a memory leak that
hides the real problem.** Bound it and propagate the pressure.
**Thread pool / worker pool**, **fork-join**, **pipeline**, **scatter-gather**,
**read-copy-update**, **double-checked locking** (⚠️ **historically a famous source of
subtle bugs**; use your language's lazy-init facility instead).

**⚠️ Async/await is a pattern with a well-known cost**: **function colouring** — async
propagates up your call stack and splits your ecosystem in two. Virtual threads and green
threads are the alternative bet.

---

## §11. Integration and Messaging

**[DURABLE] Hohpe & Woolf's *Enterprise Integration Patterns* (2003) named these, and the
vocabulary is still the industry standard 20+ years on** — a genuine counterexample to
"patterns don't age."

**Message channel**, **publish-subscribe**, **point-to-point**, **message router**,
**content-based router**, **message translator**, **message filter**, **splitter and
aggregator**, **scatter-gather**, **process manager**, **claim check** (⚠️ **put the large
payload in storage and pass a reference** — the fix for oversized messages), **competing
consumers**, **dead letter channel**, **guaranteed delivery**.

**Delivery semantics, precisely:** **at-most-once** (may lose), **at-least-once** (may
duplicate — **the practical default**), **exactly-once** (⚠️ **not achievable end-to-end
in the general case** — what systems offer is at-least-once delivery plus idempotent
processing, which is the achievable and correct target).

**Event flavours matter and are frequently confused**: **event notification** (something
happened, go look), **event-carried state transfer** (the event includes the data),
**event sourcing** (§8). **Choosing the wrong one is a common source of coupling** —
event-carried state transfer looks convenient and quietly couples consumers to your
internal schema.
