---
name: software-design
description: "Advanced software design practitioner guide: design-as-decision-making, just-enough design, monolith-first doctrine, SOLID/DRY/KISS/YAGNI as contextual heuristics, ADRs, C4 model, fitness functions/ArchUnit, architecture advice process, design process by scale, DDD strategic/tactical patterns, AI impact on maintainability (GitClear 2024), bounded contexts, event storming, design docs/RFCs, and evolutionary architecture governance."
---

# Software Design: Advanced Practitioner Reference Guide

## Core Philosophy

Software design is the **disciplined, iterative practice of making and recording trade-off decisions under uncertainty** — not a separate up-front phase. The single most valuable skill is expert judgment about *when to apply which technique at which scale*.

**Ford & Richards's Two Laws:**
1. **First Law:** "Everything in software architecture is a trade-off. If you think you've found something that isn't a trade-off, you likely just haven't found the trade-off yet."
2. **Second Law:** "Why is more important than how." — The organizing principle behind ADRs, RFCs, and design docs.

**The practical goal:** "Never shoot for the best architecture, but rather for the least worst one."

---

## Design as Decision-Making

### What Architecture Actually Is
Ford & Richards define architecture as: **structure + architecture characteristics ("-ilities") + architecture decisions + design principles.**

Useful working distinction:
- **Architecture** = decisions that are expensive to reverse ("the stuff that's hard to change later")
- **High-level/detailed design** = component and class decisions that are cheaper to change

The boundary is fluid — microservices made "change a first-class design consideration," partly invalidating the old "hard to change" definition.

### JEDUF — Just-Enough Design Up Front
The empirical evidence for the "cost-of-change curve" (Boehm's 1970s hypothesis that defects cost exponentially more to fix later) is **weakly supported**. A 2016 Menzies et al. study found "no credence to the hypothesis" across 171 projects. The honest position:

> **JEDUF:** Design enough to de-risk irreversible decisions; defer the rest. Most real design happens iteratively during implementation.

### Type 1 / Type 2 Decision Mapping (Bezos)
- **Invest up-front effort in irreversible (Type 1) decisions:** data model, service boundaries, public API contracts, persistence choices
- **Defer reversible (Type 2) decisions:** internal class structure, library choices behind an interface

Kent Beck's *Tidy First?* (2023) formalizes the economic logic: structural changes are reversible options ("just as a bad haircut is more reversible than a bad tattoo"). Software value = discounted future cash flows + the value of options created by good structure. Sometimes ship behavior first and tidy after — the time value of money applies.

### The Canonical Decision Framework
1. Identify options
2. Analyze trade-offs
3. Decide
4. Record (in an ADR)

**Three recurring decisions at every scale:** build/buy/reuse, sync/async, stateful/stateless.

Watch for **Brooks's Second System Effect** (over-engineering the rewrite) and apply YAGNI to defer speculative generality.

### Essential vs. Accidental Complexity
- **Essential complexity:** inherent to the domain — cannot be eliminated
- **Accidental complexity:** introduced by the solution — always worth reducing
- **Core domain:** your competitive advantage; worth heavy design investment
- **Generic/supporting subdomains:** candidates for buy-or-off-the-shelf (DDD strategic distinction)

---

## Design Process by Scale

### Bug Fix
1. Root-cause to determine fix location
2. Design a regression test
3. Assess blast radius
4. Decide: targeted patch vs. refactoring opportunity

**Beck's *Tidy First?* warning:** "More than one hour tidying at a time before making any behavioral changes likely means you have lost track of the minimum set of structural changes needed." Structural and behavioral changes go in **separate commits/PRs**.

The symptom may indicate a deeper design problem — decide consciously: fix vs. redesign.

### Small Feature (Days–2 Weeks)
Lightweight process:
1. Understand the requirement
2. Time-boxed spike if uncertain
3. Design the interface first
4. Design the data-model change for forward/backward compatibility
5. Design the test strategy

Central decision: extend existing code vs. create new.

### Medium Feature (Weeks–2 Months)
A **written design document or RFC earns its keep** at this scale. (See Design Communication section.)

### Large / Greenfield System
**The C4 sequence:**
1. Vision → stakeholder/actor identification
2. System Context (C4 Level 1)
3. Containers — deployable units (C4 Level 2)
4. Components — non-deployable elements inside a container (C4 Level 3)
5. Code (C4 Level 4, rarely needed)

Key practices:
- Identify external actors and systems
- Choose architectural style against explicit decision criteria
- Non-functional requirements (NFRs) as **primary design drivers**
- Phase delivery: MVP → Phase 2 → Phase 3
- **Walking skeleton** — the thinnest end-to-end slice that proves the architecture — is the recommended starting build

---

## Principles as Contextual Heuristics

### SOLID
**SRP, OCP, LSP, ISP, DIP** — remains the default OO vocabulary but should be treated as heuristics, not binary laws.

**Dan North's CUPID critique (2021):** "Every single element of SOLID is wrong." His alternative: **CUPID** — Composable, Unix-philosophy, Predictable, Idiomatic, Domain-based. North reframes these as *properties* (a direction to move toward) rather than *principles* (binary rules).

> "Principles are like rules: you are either compliant or you are not... Instead, I started thinking about properties: qualities or characteristics of code... Properties define a goal or centre to move towards." — Dan North

**2025 practical view:** SOLID works well in large monolithic backends but is a poor fit for data engineering and functional styles.

### DRY — and the Wrong Abstraction
DRY is about **knowledge duplication, not code duplication**. Two identical code fragments expressing different domain concepts do NOT violate DRY.

**Sandi Metz's critical nuance:** "Duplication is far cheaper than the wrong abstraction." When an abstraction has gone wrong:

> "Re-introduce duplication by inlining the abstracted code back into every caller... When the abstraction is wrong, the fastest way forward is back." — Sandi Metz

**Fowler's Rule of Three:** Wait for three instances before abstracting. This is the practical guard against premature abstraction.

### KISS, YAGNI, and Other Foundational Principles
- **KISS:** Hardest to follow — experienced engineers over-engineer
- **YAGNI:** Defer speculative work; don't build for requirements you don't have
- **Separation of Concerns:** The most fundamental design principle
- **High cohesion / low coupling:** Measurable via Ford & Richards's connascence, instability, abstractness, and distance-from-main-sequence metrics
- **Law of Demeter:** Talk only to your immediate collaborators
- **Composition over inheritance:** Prefer delegation and composition
- **Fail-fast:** Surface errors as early as possible
- **Encapsulation as information hiding (Parnas):** Hide decisions likely to change — Sam Newman invokes this for database decomposition in microservices

---

## Architectural Design Patterns and Styles

### Layered / N-Tier
Common, but watch for:
- The "god layer" anti-pattern
- Greater than 50% pass-through layers with no logic → collapse the layer

### Hexagonal / Clean / Onion Architecture
All three are variations on one idea: a **dependency rule pointing inward to a framework-independent domain core**, with adapters at the edges for testability.
- **Hexagonal (Ports & Adapters):** Cockburn
- **Clean Architecture:** Martin
- **Onion Architecture:** Palermo

### Event-Driven Architecture
- Choreography vs. orchestration — each has distinct trade-offs
- Eventual consistency is the default consistency model
- Pattern vocabulary: Outbox, Saga, Idempotent Consumer, Claim Check

### CQRS and Event Sourcing
Powerful but frequently over-engineering for CRUD applications. Apply only when the complexity is justified by the requirements.

### Microservices
Bounded contexts as service boundaries; database-per-service. See Monolith-First Doctrine below before choosing this path.

### Strangler Fig, Sidecar/Service Mesh, Pipes and Filters, Space-Based and Cell-Based
For extreme scale or legacy migration. Cell-based architecture provides isolated failure domains.

---

## Monolith-First Doctrine

### The Mainstream Consensus (2024–2026)
Start with a well-factored modular monolith. Extract services only when concrete pain justifies the distributed-systems tax.

**Martin Fowler's MonolithFirst:**
> "You should build a new application as a monolith initially, even if you think it's likely that it will benefit from a microservices architecture later on."

Citing Simon Brown: "If you can't build a well-structured monolith, what makes you think you can build a well-structured set of microservices?"

**DHH's Majestic Monolith:**
> "The vast majority of web applications should start life as a Majestic Monolith."

**Shopify's canonical case:** Core monolith of over 2.8 million lines of Ruby and 500,000 commits, reorganized into 37 components using the open-sourced **Packwerk** tool to enforce dependency and privacy boundaries. Shopify's Kirsten Westeinde: "I would actually recommend that new products and new companies start with a monolith."

**Amazon Prime Video case (Kolny, 2023):** Moving one internal audio/video monitoring pipeline from microservices to a monolith "reduced our infrastructure cost by over 90% [and] increased our scaling capabilities." Critically, Kolny explicitly cautioned this was not a company-wide recommendation. Amazon CTO Werner Vogels: "Building evolvable software systems is a strategy, not a religion."

**Thoughtworks Radar:** "It's often advisable to start with a well-factored monolith and only break out separately deployable units when the application reaches a scale where the benefits of microservices outweigh the additional complexity inherent in distributed systems."

### The Distributed Monolith — The Worst Failure Mode
Sam Newman: "Microservices should not be the default choice." The worst outcome is **the distributed monolith** — many services that must be deployed together.

Tell-tale sign: someone has a full-time job as "release coordination manager." Caused by splitting along technical layers rather than business/domain boundaries.

> **Benchmark:** If a "release coordination manager" role appears → you have a distributed monolith; stop splitting and re-modularize.

### Threshold to Escalate to Microservices
Extract a service only when you feel **concrete pain**:
- Independent deployability is blocked by the monolith
- Divergent scaling needs that cannot be addressed in-process
- Team-autonomy bottlenecks requiring separate deployment pipelines

**AND** you have the operational maturity (observability, CI/CD) to pay the distributed-systems tax.

---

## Domain-Driven Design (DDD)

### Strategic DDD
**Bounded Contexts:** The primary tool for managing complexity at scale. Each context has its own ubiquitous language and model.

**Language test:** When the same word means different things in two parts of the system, you've found a context boundary.

**Context Maps** (integration patterns between contexts):
- Shared Kernel — shared model owned jointly
- Customer-Supplier — upstream/downstream relationship
- Conformist — downstream conforms to upstream's model
- Anticorruption Layer (ACL) — translation layer protecting a new context from a legacy/foreign model
- Open-Host Service — well-defined API for others to integrate against

**Subdomain classification:**
- **Core domain:** Competitive advantage; invest heavily here
- **Supporting subdomain:** Needed but not differentiating; custom-build if required
- **Generic subdomain:** Buy or use open-source

**Accessible framing (Khononov):** Use "Functional Area" instead of "Bounded Context" and "Shared Vocabulary" instead of "Ubiquitous Language" to avoid alienating stakeholders.

### Tactical DDD
- **Entities:** Have identity that persists across state changes
- **Value Objects:** Defined entirely by their attributes; immutable
- **Aggregates:** Consistency boundary; keep small; reference other aggregates by ID only
- **Domain Events:** Record that something meaningful happened in the domain
- **Repositories:** Abstraction over persistence for aggregates
- **Domain Services:** Stateless operations that don't belong to a single entity
- **Application Services:** Orchestrate use cases, coordinate infrastructure

**DDD-lite:** Tactical patterns without full ceremony — recommended for most teams. Full DDD is overkill for simple CRUD.

### Event Storming (Brandolini)
The dominant 2024–2026 collaborative technique for discovering bounded contexts and aggregates.

**Core insight:** "Merge the people, split the software."

Process: Domain experts and developers use sticky notes on a large surface to map domain events, commands, aggregates, and policies. Outputs let teams "confidently design the data models and determine the appropriate software architecture."

**Domain Storytelling:** Uni-directional flows indicate bounded context candidates.

---

## Architecture Decision Records (ADRs)

### The Standard Format (Nygard, 2011)
ADRs are the single highest-ROI design practice. Store them **in source control next to the code** (Thoughtworks 2016 recommendation).

Five sections:
1. **Title** — Short noun phrase
2. **Status** — Proposed / Accepted / Deprecated / Superseded
3. **Context** — The forces at play; the problem
4. **Decision** — The response to those forces
5. **Consequences** — What becomes easier or harder; accepted trade-offs

One decision per record.

### Variants
- **MADR (Markdown Architectural Decision Records):** Adds decision drivers and considered options with pros/cons — better for genuinely contested decisions
- **Y-Statements (Zimmermann):** Concise one-sentence format: "In the context of [situation], facing [concern], we decided [option], to achieve [quality], accepting [downside]."

### The Operating Model — Most ADR Practices Die Without It
Teams pick a format but never decide:
- **When** an ADR is required (decisions that are hard to reverse OR wide in blast radius)
- **Who** advises (all affected parties + those with domain expertise)
- **Where** it lives (same repo, architecture/ directory, or decision log)

Without an explicit operating model, the practice dies within a quarter.

### Tooling
adr-tools, Log4brains, dotnet-adr, docToolchain, Structurizr

---

## The C4 Model (Simon Brown)

The dominant lightweight diagramming approach. Notation- and tool-independent.

### Four Levels
| Level | Name | Shows |
|---|---|---|
| 1 | **System Context** | Your system and its relationships to users and other systems |
| 2 | **Container** | Deployable/runnable units (apps, databases, microservices) |
| 3 | **Component** | Non-deployable logical groupings inside a container |
| 4 | **Code** | Classes, interfaces (rarely needed; auto-generate from IDE) |

**Most common error:** Mixing containers and components on the same diagram.

### Key Corrections (Brown, GOTO 2024)
- C4 does **not** replace UML
- **Complements** (does not conflict with) DDD and ADRs
- Works for both monoliths and microservices
- Diagrams should "show the **outcomes** of decisions, not the decision-making process" — use ADRs for that

### Docs-as-Code and Diagramming-as-Code (2024–2026)
- **Mermaid.js:** Native in GitHub/GitLab/Confluence — text-based, Git-versioned
- **PlantUML:** Mature, wide tool support
- **Structurizr (C4-as-code DSL):** Purpose-built for C4; generates multiple diagrams from one model
- **Excalidraw, draw.io:** For freeform collaborative whiteboarding

Trend: text-based, Git-versioned diagrams that stay in sync with code. AI-generated C4 from codebases (e.g., via Claude Code → Structurizr DSL) is emerging with quality caveats.

---

## Design Documents and RFCs

### When to Write One
Medium+ features (weeks to months of work) where the design involves non-trivial trade-offs, affects multiple teams, or makes hard-to-reverse decisions.

### Industry Practice
Used by Google ("design docs"), Amazon (6-pager / PR-FAQ), Uber (DUCK → RFC → ERD), Stripe, Spotify. The Pragmatic Engineer's research is the best public catalog.

**Key insight (Stedi):** "Writing a doc is not a perfunctory gesture."

### Uber's Scaling Failures (Cautionary)
As RFCs scaled to hundreds weekly:
- Noise: too many RFCs
- Ambiguity: unclear what requires an RFC
- Discoverability: old RFCs hard to find

**Avoid Meta's low-documentation approach** — the Pragmatic Engineer cautions against copying this.

### RFC Structure (Minimal Viable Template)
1. **Problem** — What is being solved and why
2. **Goals / Non-goals** — Explicit scope boundaries
3. **Proposed design** — Options considered, trade-offs, chosen approach
4. **Open questions** — What still needs resolution
5. **Timeline** — Milestones

---

## Architecture Advice Process

### The 2024–2026 Shift Away from ARBs
**Architecture Review Boards are now considered counterproductive.**

Per Thoughtworks Technology Radar: "The State of DevOps report reveals that the traditional approach of Architecture Review Boards is counterproductive, often hindering workflow and **correlating with low organizational performance**."

### Harmel-Law's Architecture Advice Process (*Facilitating Software Architecture*, 2024)
> "Anyone can make any decision, as long as they seek **advice** (which is different from **permission**) from all affected parties and those with expertise."

The architect's role becomes **facilitation and curation of conversations**, not gatekeeping. Guardrails come from:
- Architectural principles
- A tech radar
- ADRs in source control

### Decision Frameworks
- **DACI:** Driver, Approver, Contributor, Informed — clarifies ownership without creating approval gates
- **Rough consensus** for technical decisions
- **Critique frameworks:** "I like, I wish, what if"

### Operating at Scale
- Use an **architecture advisory forum** for conversations, not approvals
- Codify recurring decisions as architectural principles + a tech radar
- If the same questions recur across RFCs → add a template field, not another gate
- If decisions stall → clarify decision ownership, don't add an approval gate

---

## Fitness Functions and Automated Governance

### What Fitness Functions Are
From Ford, Parsons, Kua (*Building Evolutionary Architectures*, 2nd ed. 2023):
> "Any mechanism that performs an objective integrity assessment of some architecture characteristic."

Implemented as build-failing tests that enforce dependency direction, cycle-freedom, and layer rules.

### Tooling by Ecosystem
| Tool | Language | Enforces |
|---|---|---|
| **ArchUnit** | Java (gold standard) | Package dependencies, layer rules, naming conventions |
| **NetArchTest** | .NET | Namespace dependencies, layer rules |
| **dependency-cruiser** | JavaScript/TypeScript | Module dependency rules, cycle detection |
| **go-arch-lint** | Go | Package dependency rules |
| **jMolecules** | Java | DDD building blocks as annotations |

### The 2026 Frontier
- LLM-based fitness functions that check PR diffs against ADR-derived violation prompts
- MCP (Model Context Protocol) as an anticorruption layer for "agentic architecture governance"

### Governance Operating Model
1. Map every accepted ADR to at least one fitness function
2. Fail the build on architectural drift
3. Track tolerable-violation counts; ratchet them down over time
4. Use **DORA metrics** (especially change failure rate) as a feedback signal on design quality

> **Benchmark:** If code duplication or two-week churn rises materially after AI-tool rollout → reinstate refactoring discipline and review gates.

---

## API Design

### Right Protocol per Boundary (2024–2026 Consensus)
There is no single winner; match protocol to context:

| Protocol | Best For | Key Trade-Off |
|---|---|---|
| **REST** | Public/third-party APIs | Simplicity, HTTP caching, ubiquity |
| **gRPC** | Internal service-to-service | ~3–10× faster, 60–80% smaller than JSON (Protobuf) |
| **GraphQL** | Client-driven / BFF data needs | Solves over/under-fetching; N+1 requires DataLoader |
| **tRPC** | End-to-end TypeScript | Full type safety; TypeScript-only |
| **MCP** | AI-tool interaction | JSON-RPC-based; Anthropic standard |

### Core Disciplines
- **API-first:** OpenAPI or .proto as the design artifact — written before implementation
- **Consumer-driven contracts (Pact):** Tests that verify provider behavior matches consumer expectations
- **Expand-and-contract:** The standard pattern for backward-compatible API evolution

---

## Non-Functional Design

### Performance
- Algorithmic complexity and data-structure/query decisions are the **hardest to fix later**
- Caching layers: client → CDN → application → database; invalidation is the hard part
- Async where complexity is justified; N+1 prevention; resource pooling

### Scalability
- Stateless design for horizontal scaling
- Partitioning/sharding for data
- Queue-based load leveling
- Scatter-gather for parallel reads
- **Cell-based architecture** for blast-radius isolation at extreme scale

### Resilience (Nygard, *Release It!*)
Design for failure. Key patterns:
- **Circuit Breaker:** "Hope is not a design method"
- **Timeouts:** The #1 missing protection against cascading failures
- **Bulkhead:** Isolated thread/connection pools — Netflix assigns isolated pools per dependency
- **Idempotency keys:** Prevent duplicate effects on retry
- **Saga + compensating transactions:** For distributed transactions
- **Health/ready/live endpoints:** For Kubernetes and orchestration platforms

**2025 research findings (arXiv 2512.16959):**
- Naive retry backoff without jitter "causes retry storms"
- "Transactional outbox + deduplication is the practical solution" to exactly-once delivery
- Hedging "cuts P99 latency by up to 40% but hurts throughput when capacity is tight"

### Security by Design
- **Threat modeling at design time** (STRIDE, trust boundaries on architecture diagrams)
- Least privilege throughout
- AuthN/AuthZ placement — enforce tenant context at a single chokepoint
- Encryption at rest and in transit
- Input validation defense-in-depth
- Secrets management (never in source control)
- **Zero-trust architecture** — recurring Thoughtworks Radar staple

### Observability
Design in from the start, not added later:
- **Correlation IDs** from the first request
- **RED method:** Rate, Errors, Duration (for services)
- **USE method:** Utilization, Saturation, Errors (for resources)
- Distributed tracing with span design and sampling strategy
- SLO-based alerting (not raw metrics thresholds)
- **OpenTelemetry** is the de-facto standard (vendor-neutral)

---

## AI Impact on Software Design

### GitClear 2024 Findings (211 Million Changed Lines)
The most comprehensive empirical study on AI coding tools' effect on maintainability:
- **Duplicated code blocks rose eightfold during 2024**
- **Refactored ("moved") lines fell from 25% of changes in 2021 to under 10% in 2024**
- **Short-term churn** (code revised within two weeks) rose from 3.1% (2020) to 5.7% (2024)
- 2024 was the **first year copy-pasted lines exceeded moved lines**

### DORA 2024 and Harness 2025
- Increasing AI adoption **correlated with reduced delivery throughput and stability** despite higher perceived productivity
- Majority of developers spend **more time debugging AI-generated code** and more time resolving AI-generated security vulnerabilities

### The Design Implication
AI lowers the cost of **producing** artifacts. It raises the premium on the human disciplines — **refactoring, abstraction judgment, boundary enforcement** — that keep systems maintainable.

> "There has been more evidence every year that code duplication keeps growing." — Bill Harding, GitClear CEO

### Where AI Genuinely Helps
- Brainstorming architectural alternatives
- Generating boilerplate and C4/Structurizr diagrams from code
- Explaining legacy systems ("archaeology")
- Architecture knowledge management

### Where AI Fails
- Generates "plausible but incorrect designs" requiring human validation
- Must be validated via compilers, tests, simulation
- Partial satisfaction of architectural drivers — human oversight and iterative refinement are non-negotiable

### 2026 Context Engineering Shift
Thoughtworks Vol 33 Radar (Nov 2025): "Vibe coding practically disappeared," replaced by **context engineering** and spec-driven development (Amazon Kiro, GitHub Spec Kit). This is a move toward structured human-AI collaboration on design artifacts.

---

## Legacy / Brownfield Design

### Before Redesigning
- **Characterization tests** — capture current behavior before changing anything
- **"Archaeology"** — understand what the system actually does before deciding what it should do
- Separate essential complexity from historical accident

### Migration Patterns
- **Strangler Fig:** Route traffic incrementally; new system grows around the old
- **Anticorruption Layer (ACL):** Protect the new bounded context from the legacy model's language and assumptions
- **Expand-and-contract:** Backward-compatible data/API evolution
- **Incremental over big-bang** — always; big-bang rewrites have a poor track record

### 2025 Emerging Technique
"GenAI for forward engineering" — AI-generated specifications of what legacy code *does* (hiding *how* it's implemented) as a modernization input. On Thoughtworks Radar as a technique to watch.

---

## Quality Metrics and Anti-Patterns

### Code Quality Metrics
- Cyclomatic complexity and cognitive complexity
- LCOM (Lack of Cohesion in Methods)
- Instability, abstractness, and distance-from-main-sequence (Martin's metrics, in Ford & Richards)
- SonarQube debt ratio / SQALE rating
- **DORA change failure rate** as a design-quality signal

### Code Smells (Fowler)
- **Bloaters:** God Class, Long Method, Long Parameter List
- **Change Preventers:** Shotgun Surgery (one change requires changes in many places), Divergent Change (one class changes for many reasons)
- **Couplers:** Feature Envy (method more interested in another class's data)

### Architecture Anti-Patterns
- **Big Ball of Mud:** No discernible structure; implicit, uncontrolled dependencies
- **Distributed Monolith:** Multiple services that must be deployed together — "the worst of both worlds"
- **Chatty Microservices:** Fine-grained calls that create excessive network overhead
- **Shared Database:** Multiple services accessing the same database schema, creating hidden coupling
- **Anemic Domain Model:** Business logic in service/transaction scripts rather than domain objects

### Over- and Under-Engineering
- **Over-engineering:** Enterprise abstractions in a startup, premature generalization, "pattern overload"
- **Under-engineering:** Domain logic in controllers, data access mixed into the domain layer

---

## Refactoring and Evolution

### Beck's *Tidy First?* (2023) — 15 Tidyings
Structural changes go in **separate commits from behavioral changes**. Representative tidyings:
- Guard clauses (replace nested conditionals with early returns)
- Extract helper (isolate a coherent chunk of logic)
- Normalize symmetries (make similar things look similar)

### Debt Paydown Strategies
- **Opportunistic Boy Scout Rule:** Leave code better than you found it — judiciously, within scope
- **Scheduled debt sprints:** Periodic dedicated refactoring iterations
- **Targeted architectural redesign:** For pervasive structural problems

### Fitness Function Evolution
As the architecture changes, the fitness functions must change with it. Evolving fitness functions are how you avoid governance debt.

---

## Benchmarks That Should Change Your Approach

| Signal | Diagnosis | Response |
|---|---|---|
| "Release coordination manager" role appears | Distributed monolith | Stop splitting; re-modularize |
| >50% of a layer is pass-through with no logic | Unnecessary abstraction layer | Collapse the layer |
| Adding parameters and conditionals to preserve a shared abstraction | Wrong abstraction (Metz) | Inline back to duplication; re-derive |
| ADRs stop being written within a quarter | Operating model broken, not the format | Fix the operating model |
| Code duplication or two-week churn rises after AI-tool rollout | AI maintainability debt accumulating | Reinstate refactoring discipline and review gates |

---

## Cross-Cutting Themes

1. **Judgment over pattern-count.** Senior designers know *when* to apply *which* pattern and *when to stop*. "Architecture is the stuff you can't Google."

2. **Design is communication and persuasion** as much as technical problem-solving — hence the centrality of RFCs, ADRs, C4, and the advice process.

3. **Most teams under-document decisions**, paying for it in repeated debates and lost rationale. ADRs are cheap insurance but die without an operating model.

4. **Taste matters** — Beck: "Don't underestimate how much better you are as a programmer when you are happy." The "clean feeling" of a good design is a real, if soft, signal.

5. **Diverse, loosely-coupled teams produce better designs.** DORA links loosely coupled architecture *and* teams to higher organizational performance — Conway's Law and the Inverse Conway Maneuver.

6. **Designers develop through deliberate practice:** architecture katas (Ted Neward), reading others' ADRs/RFCs, post-decision reviews.

7. **AI changes artifact production, not judgment.** The maintainability evidence (GitClear, DORA 2024, Harness 2025) argues for *more* design discipline, not less.

8. **The good-enough-now vs. perfect-later tension is permanent.** Resolved by reversibility analysis: "make the least-worst decision."

---

## Staged Recommendations

### Stage 1 — Establish Cheap, High-Leverage Practices (Any Team Size)
1. Adopt **ADRs in source control** with the Nygard 5-section template; define explicitly *when required*, *who advises*, and *where they live*
2. Adopt the **C4 model** using Mermaid or Structurizr so diagrams are Git-versioned and stay near code
3. Default new systems to a **well-factored modular monolith** with module boundaries enforced by a fitness function in CI from day one
4. Extract to microservices only on concrete pain + operational maturity

### Stage 2 — Scale the Decision Process (Growing Org)
1. Introduce a lightweight **RFC/design-doc process** for medium+ features; async-first with time-boxed review
2. Replace any Architecture Review Board with the **architecture advice process** (Harmel-Law)
3. Use an architecture advisory forum for *conversations*, not approvals
4. Codify recurring decisions as **architectural principles + a tech radar**

### Stage 3 — Govern Evolution Automatically (Mature Org)
1. Map every accepted ADR to at least one **fitness function**; fail the build on drift
2. Use **DORA metrics** as a feedback signal on design quality
3. Treat **AI design assistance as a force multiplier with guardrails**: require human validation; monitor duplication/churn metrics

---

## Expert's Diagnostic Questions
When approaching any design problem:
1. What problem am I *actually* solving?
2. Who are the users?
3. What are the boundaries?
4. What quality attributes matter most?
5. What can change vs. what can't?
6. What does success look like?

Experts use analogy and pattern-matching ("this is like X except..."), treat domain experts as design partners, and handle uncertainty via prototyping, reversible decisions, and deliberate deferral.

---

## Key Sources and Authorities
- Ford & Richards, *Fundamentals of Software Architecture* (2nd ed. 2025)
- Simon Brown, *The C4 Model: Visualizing Software Architecture* (O'Reilly, July 2026 ed.)
- Martin Fowler — MonolithFirst, Refactoring catalog, PoEAA
- Kent Beck, *Tidy First?* (2023)
- Eric Evans, *Domain-Driven Design*; Vlad Khononov, *Learning Domain-Driven Design*
- Sam Newman, *Building Microservices*
- Andrew Harmel-Law, *Facilitating Software Architecture* (2024)
- Ford, Parsons, Kua, Sadalage, *Building Evolutionary Architectures* (2nd ed. 2023)
- Michael Nygard, *Release It!*; ADR format (2011)
- Dan North — CUPID critique (2021)
- Sandi Metz — "The Wrong Abstraction"
- GitClear, *AI Copilot Code Quality* (2025) — 211M line study
- DORA 2024 State of DevOps Report
- Harness, *State of Software Delivery* (2025)
- Thoughtworks Technology Radar (Vol 31–33, 2024–2025)
- Shopify Engineering, *Under Deconstruction: The State of Shopify's Monolith*
- Marcin Kolny (Amazon), "Scaling up the Prime Video audio/video monitoring service" (2023)
