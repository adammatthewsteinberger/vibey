---
name: patterns-foundations-gof-and-alternatives
description: "Use when naming, choosing, or resisting a design pattern: what a pattern actually is (a vocabulary, not a construction kit), the honest critique of the Gang of Four, the pattern-by-pattern audit of which of the 23 are obsolete, still useful, or situational in modern languages, the functional and data-oriented alternatives, and dependency injection and inversion of control. Includes the router for the whole design-patterns reference."
---

# Design Patterns: What a Pattern Is, the GoF Audit, and the Alternatives

> **Part 1 of 5** of the *Design Patterns* reference (plugin `design-patterns`), covering §0–§5. Sibling skills: `patterns-architectural` (§6–§7), `patterns-distributed-concurrency-and-messaging` (§8–§11), `patterns-llm-agentic-and-legacy-migration` (§12–§13), `patterns-reference` (§14–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
>    features** (§3). Learn to see the force.
> 3. **Over-application is the dominant failure mode, by a wide margin.** The cost of a
>    missing pattern is some duplication you can refactor later. **The cost of an unneeded
>    pattern is permanent indirection that every future reader must decode.** As one
>    2026 practitioner framing puts it: add a pattern only when it removes duplication,
>    isolates change, or clarifies intent — **and if introducing it makes the code harder
>    to explain, it's the wrong moment for it.**

---

## §0. Routing

| Asked about... | Go to |
|---|---|
| What a pattern actually is, and the vocabulary argument | §1 |
| **The honest critique of GoF** | **§2** |
| Which of the 23 survive — the audit | §3 |
| Functional and data-oriented alternatives | §4 |
| Dependency injection and inversion | §5 |
| Architectural patterns (layered, hexagonal, DDD) | §6 → `patterns-architectural` |
| Monolith vs. microservices, and modular monoliths | §7 → `patterns-architectural` |
| Distributed data patterns (saga, outbox, CQRS, ES) | §8 → `patterns-distributed-concurrency-and-messaging` |
| Resilience patterns (circuit breaker, bulkhead, retry) | §9 → `patterns-distributed-concurrency-and-messaging` |
| Concurrency patterns | §10 → `patterns-distributed-concurrency-and-messaging` |
| Integration and messaging patterns | §11 → `patterns-distributed-concurrency-and-messaging` |
| **LLM and agentic patterns** | §12 → `patterns-llm-agentic-and-legacy-migration` |
| Migration and legacy patterns | §13 → `patterns-llm-agentic-and-legacy-migration` |
| **Anti-patterns and over-application** | **§14 → `patterns-reference`, §15 → `patterns-reference`** |
| "Which side is right?" | §16 → `patterns-reference` |
| "Is this still current?" | §17 → `patterns-reference` |
| Books | §18 → `patterns-reference` |

---

## §1. What a Pattern Is

**[DURABLE] Christopher Alexander's original definition, from architecture, is still the
best one**: a pattern describes **a problem that occurs over and over, and the core of a
solution to it, such that you can use the solution a million times without ever doing it
the same way twice.**

**The three parts that matter, and the order matters:**
1. **The forces** — the competing pressures creating the problem. *This is the durable
   part.*
2. **The resolution** — how the pattern balances them.
3. **The consequences** — ⚠️ **including what it costs.** A pattern description without a
   "consequences" section is marketing.

**[DURABLE] The genuine, lasting value is the shared vocabulary.** "Put a circuit breaker
in front of it" or "that's a saga" or "wrap it in an adapter" carries a full design in a
handful of words, and that compression is real. **What patterns are *not* is a catalogue of
things your code should contain.**

**⚠️ The most important quote in this entire literature is from one of the authors.**
Ralph Johnson, a GoF co-author: **"Conformity to patterns is not a measure of goodness."**
Keep that in view for everything below.

---

## §2. The Honest Critique of GoF

**[CONTESTED — and this is a genuine, decades-long disagreement, not a settled question.
Both sides below have real merit and I'll give each its strongest form.]**

### 2.1 The case against

*Design Patterns: Elements of Reusable Object-Oriented Software* (Gamma, Helm, Johnson,
Vlissides, 1994) was written in a C++ context, in an era when — as one widely-cited
critique puts it — **programmers were "festooning their code with virtual methods,
superclasses, subclasses, and clever mixins,"** and **"language limitations and static
types were locking them out of improvements they later wanted to make."**

The structural argument: **each chapter tackled a design conundrum posed by the era's
limited programming languages**, and most solutions **"introduced new classes to cleverly
decouple code that would otherwise be too tightly linked."** Where languages have since
gained first-class functions, modules, and richer type systems, **several patterns
dissolve into a language feature** (§3).

A common academic complaint: the book **"was developed to address several things that
cannot easily be done in C++, which have been better handled in newer languages"**, and
that heavy reliance on the catalogue **"may feel a bit like making the problem fit the
solution instead of building a new solution to fit the problem."**

**⚠️ And the cultural damage was real.** For two decades, **knowing the GoF by heart was
treated as a marker of seniority** — which produced a generation of codebases with
`AbstractSingletonProxyFactoryBean`-shaped indirection installed for its own sake.
Recent commentary describes a **"post-pattern" turn toward "enlightened simplicity,"**
driven by language maturation, functional programming, data-oriented design, and cognitive
load theory.

### 2.2 The case for

**⚠️ The "patterns are just C++ deficiencies" claim is historically shaky**, and the
strongest rebuttal makes three points: **patterns came as much from Smalltalk as from
C++** — and Smalltalk is dynamic with first-class functions, so the deficiency story
doesn't fit the origin; **first-class functions alone don't fully obviate patterns like
Strategy** (they change the implementation, not always the design conversation); and
**providing an alternative implementation doesn't make the original bad.**

The forces argument, which is the strongest one: **design problems repeat even when
technology changes** — creation, composition, variation, decoupling, and behaviour
coordination are permanent. **The names and tooling evolve; the problems don't.**

And the absorption argument cuts both ways: **frameworks from Spring to .NET to Angular
implicitly implement these patterns.** You may not write a Factory, but you configure one
daily — and **you still need to recognize the pattern to judge whether the framework's use
of it fits your case.**

### 2.3 The synthesis this document takes

**[DURABLE] Learn the patterns as vocabulary and as a way of seeing forces. Do not learn
them as a catalogue of things to install.** Concretely:
- **Know all 23 by name and force.** The recognition is cheap and permanently useful.
- **Implement almost none of them literally.** Your language or framework probably has it.
- **Start simple. Add a pattern only when it removes duplication, isolates change, or
  clarifies intent** — and **if it makes the code harder to explain, it's premature.**
- **Weight the modern pattern languages higher** (§8–§12 → `patterns-distributed-concurrency-and-messaging`, `patterns-llm-agentic-and-legacy-migration`). They address forces that are
  live in 2026 in a way that Abstract Factory is not.

---

## §3. The GoF Audit

**[VERSIONED — the verdicts depend on your language, and that's the point.]**

### 3.1 Largely obsolete or absorbed into languages

| Pattern | What happened |
|---|---|
| **Iterator** | **Built into every modern language.** `for…of`, generators, `IEnumerable`, `Iterator`. ⚠️ Emulating the GoF recipe in Python is explicitly pointless — the language *is* the pattern |
| **Singleton** | ⚠️ **Widely regarded as an anti-pattern now** (§14 → `patterns-reference`). In Python and JS, **modules are natural singletons**. Where you genuinely need one instance, DI container lifetime management is the modern answer |
| **Command** | **A function is a command.** The pattern existed to give a callable first-class status in languages that lacked it. ⚠️ Still earns its keep when you need undo/redo, queuing, or serializable operations — the *object* buys you something the closure doesn't |
| **Strategy** | **A function parameter.** ⚠️ Though see §2.2 — when strategies carry state, configuration, or need naming and discovery, the object form still has value |
| **Template Method** | Inheritance-heavy and **⚠️ composition generally wins in modern codebases.** Higher-order functions do this without the inheritance tree |
| **Prototype** | Absorbed by `clone`/copy semantics, and by JS's prototype model outright |
| **Interpreter** | Rarely hand-rolled; parser generators and existing DSL tooling win (see a parsing reference) |

### 3.2 Still genuinely useful

| Pattern | Why it survives |
|---|---|
| **Adapter** | ⚠️ **Permanently useful.** Impedance mismatch between your code and someone else's interface never goes away. The core of hexagonal architecture (§6.2 → `patterns-architectural`) |
| **Facade** | Simplifying a complex subsystem is a durable need |
| **Decorator** | Composable behaviour layering — middleware, wrappers, Python decorators, HTTP handler chains. **This one arguably got *more* important** |
| **Observer** | Underpins every event system, reactive framework, and pub/sub. ⚠️ **Now usually reached via a library** (RxJS, signals, event emitters), not hand-rolled |
| **Composite** | Trees where leaves and nodes share an interface — UI, filesystems, expression trees |
| **Builder** | ⚠️ **Genuinely valuable** in languages without named/default/optional arguments. **Largely unnecessary in Python or Kotlin.** A clean language-dependence example |
| **State** | Explicit state machines are underused and this pattern names them well |
| **Proxy** | Lazy loading, remoting, access control, caching. Every ORM lazy-loading implementation |
| **Flyweight** | Niche but real — string interning, glyph caches, ECS |
| **Visitor** | ⚠️ Awkward, but **the right answer for operations over a stable type hierarchy** (compilers, ASTs). **Pattern matching and sum types replace it more cleanly** where available (§4) |

### 3.3 Situational
**Factory Method / Abstract Factory** — ⚠️ **heavily over-applied**, but real when object
creation genuinely varies by configuration or platform. **Bridge** — real when two
dimensions vary independently, rare in practice. **Chain of Responsibility** — middleware
pipelines are exactly this and are everywhere. **Mediator** — can degenerate into a god
object (§14 → `patterns-reference`). **Memento** — undo and snapshots.

---

## §4. Functional and Data-Oriented Alternatives

**[DURABLE] Many OO patterns have a functional counterpart that is smaller and often
clearer**, and knowing the mapping is more useful than knowing either list alone.

| OO pattern | Functional equivalent |
|---|---|
| Strategy | A function parameter |
| Command | A closure |
| Template Method | A higher-order function |
| Decorator | Function composition |
| Observer | Streams / signals / reactive sequences |
| Visitor | **Pattern matching over a sum type** |
| Factory | A function returning a value |
| Null Object | `Option` / `Maybe` |
| Singleton | A module |

**The functional patterns proper**: **immutability by default** (removes whole categories
of bug), **pure core / imperative shell** (⚠️ **one of the highest-value structural ideas
available** — put logic in pure functions, push I/O to the edges, and testing becomes
trivial), **algebraic data types + exhaustive pattern matching** (the compiler enforces
that you handled every case), **`Result`/`Either` for errors** as values rather than
control flow, **persistent data structures**, and **the monadic patterns** (⚠️ useful
concepts, and **the terminology is a genuine barrier that the community often
underestimates**).

**Data-oriented design** inverts the OO framing entirely: **model the data and its
transformations, not the objects.** Struct-of-arrays layouts, separating data from
behaviour, entity-component systems. **⚠️ It's a serious alternative in performance-critical
domains, not a stylistic preference** — for the hardware reasons, see an algorithms
reference on memory layout.

---

## §5. Dependency Injection and Inversion

**[DURABLE] The most consequential idea in this whole area, and the most commonly
misunderstood.**

**Three distinct things people conflate:**
- **Dependency Inversion Principle** — depend on abstractions, not concretions. *A design
  principle.*
- **Dependency Injection** — pass dependencies in rather than constructing them inside.
  *A technique.* **⚠️ Constructor injection is DI. It requires no framework at all.**
- **DI container / IoC framework** — Spring, Guice, .NET's built-in container. *A tool*,
  and an optional one.

> **⚠️ GOTCHA — the failure modes, and they're common:**
> - **Interfaces with exactly one implementation, created "for testability."** If nothing
>   else will ever implement it, the interface is ceremony. **Modern test tooling can fake
>   concrete types.**
> - **Container magic** — runtime-resolved graphs that are impossible to trace by reading
>   code, and that fail at startup in production rather than at compile time.
> - **Over-abstracting stable dependencies.** You are not going to swap out the standard
>   library's date type.
> - **⚠️ Service Locator is not DI.** It hides dependencies inside the implementation
>   rather than declaring them in the signature, and it is widely regarded as an
>   anti-pattern for that reason.

**[DURABLE] The pragmatic default: constructor injection, plain, no framework, until the
object graph is large enough to genuinely hurt.** Introduce an interface when you have a
second implementation or a real seam — not speculatively.
