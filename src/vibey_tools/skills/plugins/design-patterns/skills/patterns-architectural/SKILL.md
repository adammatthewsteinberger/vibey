---
name: patterns-architectural
description: "Use when choosing or evaluating an application architecture: layered architecture, hexagonal / ports and adapters (and Clean and Onion), Domain-Driven Design and its tactical and strategic halves, and the monolith versus modular monolith versus microservices decision — including when a distributed architecture is the wrong answer and what it costs you."
---

# Design Patterns: Architectural Patterns, Monoliths, Modules, and Microservices

> **Part 2 of 5** of the *Design Patterns* reference (plugin `design-patterns`), covering §6–§7. Sibling skills: `patterns-foundations-gof-and-alternatives` (§0–§5), `patterns-distributed-concurrency-and-messaging` (§8–§11), `patterns-llm-agentic-and-legacy-migration` (§12–§13), `patterns-reference` (§14–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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

## §6. Architectural Patterns

### 6.1 Layered

Presentation → Application → Domain → Infrastructure. **Familiar, easy to explain, and
adequate for a great deal of software.** ⚠️ Its failure modes: **anemic domain models**
(logic drains into the service layer, leaving data-bags — see §14 → `patterns-reference`), layer-skipping that
nobody notices, and **dependency flowing the wrong way toward infrastructure.**

### 6.2 Hexagonal / Ports and Adapters (and Clean, and Onion)

**[DURABLE] The single most valuable architectural idea for most business applications,
and the family is largely one idea under three names.**

**Domain logic in the centre, knowing nothing about the outside world. Ports are
interfaces the domain defines. Adapters implement them for a database, an HTTP API, a
queue, a third-party service.** ⚠️ **The dependency rule is the whole point: dependencies
point inward, always.** Infrastructure depends on the domain; the domain depends on
nothing.

**What you actually get**: the domain is testable without a database or a network; you can
replace infrastructure without touching business rules; and **the business logic is
findable**, which matters more than it sounds.

**⚠️ What it costs**: more indirection, more files, and **it's genuinely overkill for a
CRUD app.** The honest heuristic: **if your domain logic is thin, you don't need this** —
and much software has thin domain logic.

### 6.3 Domain-Driven Design

**Strategic DDD is the more valuable half and the more neglected one**: **bounded
contexts** (⚠️ **the single most useful concept here** — the same word means different
things in different parts of the business, and pretending otherwise produces the
universal-model disaster), **ubiquitous language**, and **context mapping**.

**Tactical DDD**: entities, value objects (**⚠️ underused — most "primitives" in a domain
are value objects with invariants**), aggregates (**consistency boundaries — and the "one
aggregate per transaction" rule is what makes them useful**), repositories, domain events,
domain services.

**⚠️ The characteristic DDD failure is adopting the tactical patterns without the strategic
work** — you get repositories and value objects laid over a model nobody talked to the
business about, which is the ceremony without the benefit.

---

## §7. Monoliths, Modules, and Microservices

**[CONTESTED, though the pendulum has swung noticeably.]**

**[DURABLE] The modular monolith is the correct default for most teams**: one deployable,
strong internal module boundaries, no network between your own components. You get
enforced boundaries without distributed-systems tax.

**⚠️ Microservices buy independent deployment and scaling, and they cost you: distributed
transactions (§8 → `patterns-distributed-concurrency-and-messaging`), network failure as a permanent condition, debugging across process
boundaries, eventual consistency everywhere, and operational overhead per service.**
The honest framing: **microservices are an organizational solution to a team-coordination
problem, adopted for a technical-sounding reason.** If your teams aren't blocked on each
other's deploys, you're paying the cost without collecting the benefit.

**Related patterns**: **Strangler Fig** (§13 → `patterns-llm-agentic-and-legacy-migration`), **API Gateway**, **Backend for Frontend
(BFF)**, **Sidecar / Ambassador** (cross-cutting concerns beside rather than inside your
process — the basis of service meshes), **Anti-Corruption Layer** (⚠️ **the essential
pattern when integrating a legacy or third-party model you don't control** — translate at
the boundary so their model doesn't leak into yours).

**Serverless/event-driven adds its own**: function-per-endpoint, fan-out/fan-in, and
⚠️ **cold-start and statelessness constraints that are design forces, not implementation
details.**
