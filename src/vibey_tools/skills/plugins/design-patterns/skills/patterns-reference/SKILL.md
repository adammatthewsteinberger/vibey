---
name: patterns-reference
description: "Use when checking a pattern anti-pattern — over-application is the dominant failure mode in this domain — weighing a contested question, confirming whether a claim is still current (snapshot verified August 2026), finding the books and sources, or needing the problem-to-pattern table and the checklist to run before adding a pattern. Companion to the other design-patterns skills."
---

# Design Patterns: Anti-Patterns, Contested Questions, Currency, and Canon

> **Part 5 of 5** of the *Design Patterns* reference (plugin `design-patterns`), covering §14–§20. Sibling skills: `patterns-foundations-gof-and-alternatives` (§0–§5), `patterns-architectural` (§6–§7), `patterns-distributed-concurrency-and-messaging` (§8–§11), `patterns-llm-agentic-and-legacy-migration` (§12–§13). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Verified August 2026. See §17 below for the currency snapshot and what goes stale first.

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
>    literature (§14).
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

## §14. Anti-Patterns

**[DURABLE] Naming these is at least as valuable as naming the patterns.**

**Structural**: **God object / god class**, **anemic domain model** (⚠️ **data-bags plus a
service layer — arguably the default outcome of layered architecture done carelessly**),
**spaghetti**, **lasagna** (so many layers each adds nothing), **big ball of mud**,
**circular dependencies**, **feature envy**, **shotgun surgery** (one change touches
fifteen files).

**Pattern-specific**: **Singleton abuse** (⚠️ **global mutable state with a design-pattern
name on it** — hostile to testing, hides dependencies, causes ordering bugs), **Service
Locator** (§5 → `patterns-foundations-gof-and-alternatives`), **the Poltergeist** (a class that exists only to call another),
**BaseBean** (inheriting for convenience rather than for an is-a relationship),
**over-abstracted factories**.

**Process**: **premature optimization**, **premature generalization** (⚠️ **"we might need
this later" is the most expensive sentence in software**), **cargo cult architecture**
(⚠️ **adopting Netflix's architecture at 1/10000th of Netflix's scale**), **resume-driven
development**, **the distributed monolith** (⚠️ **microservices that must deploy together —
all the cost, none of the benefit, and the most common microservice failure mode**),
**golden hammer**, **not-invented-here**, **stringly-typed** code, **magic numbers**,
**boat anchor** (dead code kept "just in case"), **feature toggle debt**.

> **⚠️ GOTCHA — pattern over-application, stated plainly, because it is the failure mode
> this whole document exists to prevent.** Symptoms: interfaces with exactly one
> implementation; factories that construct one type; three layers of indirection between
> the caller and the work; class names ending in `Manager`, `Helper`, `Processor`, or
> `AbstractProxyFactoryBean`; **you cannot find where anything actually happens.**
>
> **The asymmetry that should govern your default**: a missing pattern costs you some
> duplication, which you can refactor when the third case appears and you can see the real
> shape. **An unnecessary pattern costs every future reader permanently, and is far harder
> to remove than to add.** When in doubt, don't.

---

## §15. Anti-Patterns Table

| Anti-pattern | Why |
|---|---|
| Learning patterns as a catalogue to install | **"Conformity to patterns is not a measure of goodness"** — Ralph Johnson, GoF co-author (§1 → `patterns-foundations-gof-and-alternatives`) |
| Adding a pattern that makes the code harder to explain | That's the signal it's premature (§2.3 → `patterns-foundations-gof-and-alternatives`) |
| Hand-rolling Iterator in a language with iteration | ⚠️ The language is the pattern (§3.1 → `patterns-foundations-gof-and-alternatives`) |
| Singleton for shared state | **Global mutable state with a nice name** (§14) |
| Interface with exactly one implementation "for testing" | Modern test tooling fakes concrete types (§5 → `patterns-foundations-gof-and-alternatives`) |
| Service Locator instead of DI | Hides dependencies rather than declaring them (§5 → `patterns-foundations-gof-and-alternatives`) |
| Container magic you can't trace by reading | Runtime failures where compile-time ones belonged (§5 → `patterns-foundations-gof-and-alternatives`) |
| Hexagonal architecture over a CRUD app | ⚠️ **If domain logic is thin, you don't need it** (§6.2 → `patterns-architectural`) |
| Tactical DDD without the strategic work | Ceremony without the benefit (§6.3 → `patterns-architectural`) |
| Microservices when teams aren't blocked on deploys | Paying the cost, not collecting the benefit (§7 → `patterns-architectural`) |
| Microservices that must deploy together | ⚠️ **Distributed monolith** (§14) |
| Adopting a hyperscaler's architecture at 1/10000th the scale | Cargo cult (§14) |
| Writing to your DB then publishing an event | ⚠️ **The dual-write problem. Real systems lose orders this way** (§8 → `patterns-distributed-concurrency-and-messaging`) |
| Event Sourcing for CRUD | ⚠️ **Four months for a two-week feature, then rewritten** (§8 → `patterns-distributed-concurrency-and-messaging`) |
| Choreographed saga past ~3 steps | Becomes impossible to reason about (§8 → `patterns-distributed-concurrency-and-messaging`) |
| Treating compensation as rollback | The intermediate state was visible (§8 → `patterns-distributed-concurrency-and-messaging`) |
| Synchronous external call with no circuit breaker | Cascading failure (§9 → `patterns-distributed-concurrency-and-messaging`) |
| Retry without jitter | Thundering herd (§9 → `patterns-distributed-concurrency-and-messaging`) |
| Retrying non-idempotent operations | Duplicates (§9 → `patterns-distributed-concurrency-and-messaging`) |
| **Any network call without a timeout** | ⚠️ **The most under-set config in software** (§9 → `patterns-distributed-concurrency-and-messaging`) |
| Unbounded producer-consumer queue | A memory leak hiding the real problem (§10 → `patterns-distributed-concurrency-and-messaging`) |
| Double-checked locking by hand | Famously subtle; use the language's lazy init (§10 → `patterns-distributed-concurrency-and-messaging`) |
| Promising exactly-once delivery | At-least-once + idempotency is the achievable target (§11 → `patterns-distributed-concurrency-and-messaging`) |
| Event-carried state transfer by default | Couples consumers to your internal schema (§11 → `patterns-distributed-concurrency-and-messaging`) |
| Agent where a workflow would do | ⚠️ **Prefer predefined code paths** (§12 → `patterns-llm-agentic-and-legacy-migration`) |
| Multi-agent for a single-agent task | Over-applied buzzword (§12 → `patterns-llm-agentic-and-legacy-migration`) |
| Agentic loop with no iteration cap | A financial failure mode (§12 → `patterns-llm-agentic-and-legacy-migration`) |
| Prompts embedded in orchestration code | Treat prompts as versioned artifacts (§12 → `patterns-llm-agentic-and-legacy-migration`) |
| Framework chosen before pattern | Backwards (§12 → `patterns-llm-agentic-and-legacy-migration`) |
| Big-bang rewrite | Use Strangler Fig (§13 → `patterns-llm-agentic-and-legacy-migration`) |
| Schema change without expand-contract | The only safe way under live traffic (§13 → `patterns-llm-agentic-and-legacy-migration`) |
| "We might need this later" | ⚠️ **The most expensive sentence in software** (§14) |

---

## §16. Contested Questions

**16.1 Are GoF patterns obsolete?** §2 → `patterns-foundations-gof-and-alternatives` in full. **[CONTESTED, genuinely.** The "patterns
are C++ deficiencies" claim is historically shaky given the Smalltalk origins; the
"patterns are timeless" claim under-weights how much modern languages absorbed. **The
defensible position is per-pattern, not wholesale** — §3 → `patterns-foundations-gof-and-alternatives` audits them individually.]

**16.2 Do patterns help or hurt juniors?** *Help*: shared vocabulary, exposure to
considered designs, a path past reinventing. *Hurt*: **encourages installing patterns
rather than solving problems**, and pattern-recognition becomes a proxy for judgment.
**The teaching order that seems to work: forces first, then patterns as named responses,
and never the catalogue first.**

**16.3 OOP vs. functional vs. data-oriented?** All three have real domains. **The
industry has broadly moved toward composition over inheritance, immutability by default,
and functions as first-class**, without abandoning objects. **⚠️ Treat strong advocacy in
any direction as a signal of narrow exposure.**

**16.4 Is Clean Architecture worth its cost?** *For*: testability, replaceable
infrastructure, findable business logic. *Against*: **file-count explosion, indirection,
and genuine overkill for thin-domain applications.** Much of the criticism is really
criticism of applying it uniformly rather than of the idea.

**16.5 Microservices — solved question or ongoing mistake?** The pendulum has swung toward
modular monoliths, and **"microservices are an organizational solution adopted for
technical-sounding reasons"** is now a mainstream position rather than a contrarian one.
Still genuinely right at sufficient organizational scale.

**16.6 Is Event Sourcing worth it?** *For*: complete audit trail, temporal queries,
debugging by replay, and in some regulated domains it's a requirement. *Against*: §8 → `patterns-distributed-concurrency-and-messaging`'s
cautionary case is representative rather than exceptional. **[CONTESTED, but the evidence
leans toward "less often than practitioners think."]**

**16.7 Are the agentic patterns real patterns or vendor framing?** ⚠️ **Genuinely
unresolved and worth holding loosely.** Some — workflow-vs-agent, human-in-the-loop,
evaluator-optimizer, guardrails — describe forces that clearly recur. Others are framework
marketing with a pattern name attached. **Multiple competing taxonomies is what an
immature pattern language looks like**, and this one is two to three years old against
GoF's decade of prior art.

---

## §17. Currency Snapshot — verified August 2026

**[DURABLE] Most of this document doesn't move.** GoF is 1994, Fowler's *PoEAA* 2002,
Hohpe & Woolf 2003, Evans' *DDD* 2003 — and the forces they describe are unchanged.
Here is what actually shifted.

| Thing | Status as of Aug 2026 | Decay risk |
|---|---|---|
| **The GoF critique** | ⚠️ **Now mainstream rather than contrarian.** 2026 commentary describes a **"post-pattern" turn toward "enlightened simplicity"**, attributed to language maturation, FP, data-oriented design, and cognitive load theory. Counter-position remains live: patterns originated as much in **Smalltalk** (dynamic, first-class functions) as C++, so the "C++ deficiency" story is historically incomplete | Low |
| **Absorbed patterns** | **Iterator, Singleton, Command, Strategy, Template Method** are largely language features or trivial in modern languages. **Modules act as natural singletons in Python and JS.** Frameworks (Spring, .NET, Angular) implement Factory/Proxy/Observer implicitly — **you configure them rather than write them** | Low |
| **Practitioner heuristic** | Widely-repeated 2026 framing: **"Start simple. Add a pattern only when it removes duplication, isolates change, or clarifies intent. If introducing a pattern makes the code harder to explain, it is probably the wrong moment for it."** Composition over inheritance is the settled default | Low |
| **Distributed data patterns** | **Outbox + Saga + CQRS (+ Event Sourcing) is the established production stack** for event-driven microservices. **Debezium/CDC** for log-based publishing. ⚠️ **Dedicated workflow engines (Temporal, Watermill and similar) increasingly preferred over hand-rolled orchestration** | Medium |
| **Saga guidance** | Published heuristic: **choreography for 2–3 steps, orchestration for 4+ or complex logic**. Choreography-plus-Postgres-outbox with a background relay is a common concrete pattern | Medium |
| **⚠️ Event Sourcing caution** | Now widely stated rather than fringe: **event notification covers the majority of cases, CQRS most of the remainder, and Event Sourcing is for the minority where a full audit trail is a hard business requirement.** Documented failure case: a 3-junior team choosing full ES for a profile CRUD — **4 months for what should have taken 2 weeks, undebuggable state-reconstitution bugs, rewritten as REST in 3 weeks** | Low |
| **⚠️ Circuit breaker adoption** | Survey work on microservice deployments found **circuit breaker notably less adopted than API gateway** — roughly half the usage — **which the researchers note weakens resilience** in exactly the systems that need it | Medium |
| **⚠️ Agentic patterns** | **The live, unsettled pattern language.** At least three overlapping taxonomies in circulation (Ng's four, Anthropic's workflow patterns, and emergent reliability/memory patterns from 2025–26). Core distinction — **workflows = predefined code paths; agents = model decides next step** — is stable and useful. Academic work is now presenting FM/agent patterns **in GoF format**. **ReAct predates the current framing by ~2 years.** Multi-agent widely described as a 2023–24 buzzword that is over-applied | **High** |
| **Agentic operational practice** | **Prompts as versioned code**; step-level tracing with token-cost and guardrail-violation metrics (MLflow, LangSmith and similar); **iteration caps as a cost control**; **progressive disclosure against "context rot"** | **High** |

**Goes stale fastest:** §12 → `patterns-llm-agentic-and-legacy-migration` entirely. **Essentially never stale:** §1 → `patterns-foundations-gof-and-alternatives`, §2 → `patterns-foundations-gof-and-alternatives`'s forces
argument, §5 → `patterns-foundations-gof-and-alternatives`, §6.2 → `patterns-architectural`, §9 → `patterns-distributed-concurrency-and-messaging`, §13 → `patterns-llm-agentic-and-legacy-migration`, §14, §15.

---

## §18. The Canon

### 18.1 Books

| Author | Work | Why |
|---|---|---|
| **Gamma, Helm, Johnson & Vlissides** | ***Design Patterns*** (1994) | The original. ⚠️ **Read with §2 → `patterns-foundations-gof-and-alternatives` in hand** — it's a historical document with durable content, not a manual |
| **Fowler** | ***Patterns of Enterprise Application Architecture*** (2002) | ⚠️ **Arguably more useful than GoF for most working engineers.** Repository, Unit of Work, Active Record, Data Mapper |
| **Fowler** | *Refactoring* (2nd ed.) | The other half — how to get *to* a design, not just name it |
| **Hohpe & Woolf** | ***Enterprise Integration Patterns*** (2003) | §11 → `patterns-distributed-concurrency-and-messaging`, and **the vocabulary is still standard 20+ years on** |
| **Evans** | ***Domain-Driven Design*** (2003) | Dense. **Read Vernon's *Implementing DDD* or *DDD Distilled* first** |
| **Nygard** | ***Release It!*** (2nd ed.) | ⚠️ **§9 → `patterns-distributed-concurrency-and-messaging`'s source, and the best book on production failure modes.** If you read one book here, consider this one |
| **Richardson** | *Microservices Patterns* | §7–§8 → `patterns-architectural`, `patterns-distributed-concurrency-and-messaging`, and **microservices.io** is the free companion catalogue |
| **Kleppmann** | *Designing Data-Intensive Applications* | The forces underneath §8 → `patterns-distributed-concurrency-and-messaging` |
| **Newman** | *Building Microservices*; *Monolith to Microservices* | §7 → `patterns-architectural` and §13 → `patterns-llm-agentic-and-legacy-migration` |
| **Feathers** | *Working Effectively with Legacy Code* | §13 → `patterns-llm-agentic-and-legacy-migration`, and still unmatched |
| **Freeman & Robson** | *Head First Design Patterns* | **The most approachable way in.** Updated for modern Java |
| **Ramalho** | *Fluent Python* | ⚠️ **Ch. 10, "Design Patterns with First-Class Functions," is the single best demonstration of §4 → `patterns-foundations-gof-and-alternatives`'s argument** |
| **Hunt & Thomas** | *The Pragmatic Programmer* | The judgment layer around all of it |
| **Alexander** | *A Pattern Language* | Where the whole idea came from. Architecture, not software |

### 18.2 Sites and people
**refactoring.guru** (the best free pattern catalogue — clear diagrams, multi-language),
**python-patterns.guide** (⚠️ **the sharpest published critique of GoF-in-a-modern-language**),
**martinfowler.com** (bliki — the reference for most of this vocabulary),
**microservices.io** (Chris Richardson's free catalogue for §7–§8 → `patterns-architectural`, `patterns-distributed-concurrency-and-messaging`),
**Microsoft's Cloud Design Patterns** and **AWS Prescriptive Guidance** (solid, vendor-shaped),
**c2.com wiki** (where the patterns community argued it out originally — still worth reading).

**People**: **Martin Fowler**, **Kent Beck**, **Michael Nygard**, **Gregor Hohpe**,
**Eric Evans** and **Vaughn Vernon**, **Sam Newman**, **Chris Richardson**,
**Rich Hickey** (*Simple Made Easy* — ⚠️ **the best single talk on why simplicity beats
familiarity**), **Sandi Metz** (OO design, and unusually good on when *not* to abstract),
**Kevlin Henney**, **Ralph Johnson** (§1 → `patterns-foundations-gof-and-alternatives`'s quote).

---

## §19. Quick Reference

### 19.1 Problem → pattern

| Problem | Pattern |
|---|---|
| Their interface doesn't match mine | **Adapter** (§3.2 → `patterns-foundations-gof-and-alternatives`) |
| Complex subsystem, simple need | Facade |
| Layer behaviour composably | **Decorator** / middleware |
| Notify many of a change | Observer / pub-sub |
| Many optional construction params | Builder — ⚠️ **unless your language has named args** |
| Behaviour varies by state | State (explicit machine) |
| Operations over a stable type hierarchy | Visitor — ⚠️ **or pattern matching** (§4 → `patterns-foundations-gof-and-alternatives`) |
| Swap an algorithm | ⚠️ **A function parameter** (§4 → `patterns-foundations-gof-and-alternatives`) |
| Testable business logic | **Hexagonal / ports and adapters** (§6.2 → `patterns-architectural`) |
| Same word, different meanings across the business | **Bounded contexts** (§6.3 → `patterns-architectural`) |
| Integrating a model I don't control | **Anti-Corruption Layer** (§7 → `patterns-architectural`) |
| Write to DB *and* publish an event | ⚠️ **Transactional Outbox** (§8 → `patterns-distributed-concurrency-and-messaging`) |
| Business operation spanning services | **Saga** — choreography ≤3 steps, else orchestration (§8 → `patterns-distributed-concurrency-and-messaging`) |
| Reads and writes have different shapes | CQRS (§8 → `patterns-distributed-concurrency-and-messaging`) |
| Full audit trail is a hard requirement | Event Sourcing — ⚠️ **and only then** (§8 → `patterns-distributed-concurrency-and-messaging`) |
| Duplicate messages | Idempotent consumer / inbox (§8 → `patterns-distributed-concurrency-and-messaging`) |
| Downstream failing, don't cascade | **Circuit breaker** (§9 → `patterns-distributed-concurrency-and-messaging`) |
| Transient failure | Retry with backoff **and jitter** (§9 → `patterns-distributed-concurrency-and-messaging`) |
| One dependency shouldn't consume everything | Bulkhead (§9 → `patterns-distributed-concurrency-and-messaging`) |
| Overloaded | Load shedding — ⚠️ **reject early, don't collapse** (§9 → `patterns-distributed-concurrency-and-messaging`) |
| Replace a legacy system | **Strangler Fig** (§13 → `patterns-llm-agentic-and-legacy-migration`) |
| Change a schema under live traffic | **Expand-contract** (§13 → `patterns-llm-agentic-and-legacy-migration`) |
| Verify a migration | **Parallel run** (§13 → `patterns-llm-agentic-and-legacy-migration`) |
| Multi-step LLM task | ⚠️ **A workflow, not an agent, if you can sequence it** (§12 → `patterns-llm-agentic-and-legacy-migration`) |
| LLM needs current or private data | RAG (§12 → `patterns-llm-agentic-and-legacy-migration`) |
| LLM output quality varies | Evaluator-optimizer with **separated roles** (§12 → `patterns-llm-agentic-and-legacy-migration`) |
| Agent could do something costly | **Human-in-the-loop gate + iteration cap** (§12 → `patterns-llm-agentic-and-legacy-migration`) |

### 19.2 Before adding a pattern
- [ ] What **force** am I resolving? Can I state it in one sentence?
- [ ] Does my language already have this as a feature? (§3 → `patterns-foundations-gof-and-alternatives`, §4 → `patterns-foundations-gof-and-alternatives`)
- [ ] Do I have **two** cases, or am I speculating about the second?
- [ ] Does this **remove duplication, isolate change, or clarify intent**?
- [ ] Would a new team member find the code **easier** to explain, or harder?
- [ ] What does it **cost** — and have I said that out loud?
- [ ] Am I solving a problem, or demonstrating knowledge?

---

## §20. Sources and Method

**Method.** Narrative review, written as **judgment guidance rather than a catalogue** —
the 23 GoF patterns are exhaustively documented for free elsewhere and reproducing them
adds nothing. The durable material rests on the primary pattern literature (GoF, Fowler,
Hohpe & Woolf, Evans, Nygard) and on failure modes reported consistently across two
decades of practice. Three targeted searches were run in **August 2026** on the areas where
the picture could have moved: the current standing of the GoF critique, distributed-pattern
practice, and the emerging agentic pattern language.

**⚠️ A note on §2 → `patterns-foundations-gof-and-alternatives` and §16 specifically.** This is a domain with real, live disagreement
among competent practitioners, and I have tried to **give each side its strongest form
rather than adjudicate.** Where I take a position — §2.3 → `patterns-foundations-gof-and-alternatives`'s synthesis, §14's asymmetry
argument — I've marked it as the position this document takes, not as consensus.

**Search log** (August 2026): GoF relevance and critique in modern languages ·
distributed-system patterns (saga, outbox, circuit breaker, CQRS, event sourcing) in 2026
practice · LLM and agentic design patterns and their taxonomies.

**Primary and near-primary sources consulted (selected):**
- **python-patterns.guide** for the sharpest form of the "patterns as language
  deficiencies" argument; a **Microsoft archived blog post** and related commentary for the
  Smalltalk-origins rebuttal; **Fluent Python** Ch. 10 (and Ralph Johnson's quote via its
  epigraph); **Kansas State's CC 410 textbook** for the standard academic critique;
  practitioner posts from 2026 for the "post-pattern"/enlightened-simplicity framing and
  the start-simple heuristic
- **microservices.io** (Chris Richardson) for the saga and outbox definitions; 2026
  practitioner write-ups for the choreography/orchestration step heuristic, the documented
  order-loss and Event-Sourcing-for-CRUD cautionary cases, and the
  event-notification/CQRS/ES proportions; an academic survey of microservice architecture
  patterns for the circuit-breaker adoption finding
- **Anthropic's *Building Effective Agents*** framing (workflows vs. agents) as reported
  in practitioner coverage; **Databricks' agent system design patterns** documentation;
  **arXiv 2601.19752** on agentic design patterns as a system-theoretic framework, which
  notes FM/agent patterns being presented in GoF format; 2026 pattern catalogues describing
  the Ng / Anthropic / emergent taxonomy overlap

**Confidence statement.** **High confidence** in §1 → `patterns-foundations-gof-and-alternatives`, §3–§7 → `patterns-foundations-gof-and-alternatives`, `patterns-architectural`, §9–§11 → `patterns-distributed-concurrency-and-messaging`, §13–§15 → `patterns-llm-agentic-and-legacy-migration` — these rest on
the primary pattern literature and long-stable practice rather than on anything searched.
**High confidence** that the §2 → `patterns-foundations-gof-and-alternatives` debate exists in the form described, with **explicitly no
position on who is right**, because it is a values disagreement about cost and clarity that
evidence does not settle. **Moderate confidence** in §8 → `patterns-distributed-concurrency-and-messaging`'s specific heuristics — the
choreography-vs-orchestration step counts and the event-notification/CQRS/ES proportions
are **practitioner rules of thumb from individual write-ups, not measured findings**, and
should be treated as starting points rather than thresholds. The cautionary cases in §8 → `patterns-distributed-concurrency-and-messaging` are
**reported anecdotes**; I've included them because they're representative of a widely
described pattern of failure, not because any single one is authoritative. **Lower
confidence in §12 → `patterns-llm-agentic-and-legacy-migration`**, and deliberately so: the agentic pattern language is 2–3 years old,
naming is unstable, several sources are vendor-adjacent with obvious incentives, and
**multiple competing taxonomies is exactly what an immature pattern language looks like** —
which is why §16.7 leaves the "real patterns or vendor framing" question open rather than
resolving it.
