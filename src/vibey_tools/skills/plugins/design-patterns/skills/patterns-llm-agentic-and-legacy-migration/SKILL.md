---
name: patterns-llm-agentic-and-legacy-migration
description: "Use when designing an LLM or agentic system, or moving a legacy codebase: the emerging agentic pattern language (prompt chaining, routing, tool use, ReAct, reflection, multi-agent orchestration, RAG, guardrails, human-in-the-loop) and migration and legacy patterns including strangler fig, anti-corruption layer, and branch by abstraction."
---

# Design Patterns: LLM and Agentic Patterns, and Migration and Legacy Patterns

> **Part 4 of 5** of the *Design Patterns* reference (plugin `design-patterns`), covering §12–§13. Sibling skills: `patterns-foundations-gof-and-alternatives` (§0–§5), `patterns-architectural` (§6–§7), `patterns-distributed-concurrency-and-messaging` (§8–§11), `patterns-reference` (§14–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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

## §12. LLM and Agentic Patterns

**[VERSIONED — the one genuinely new pattern language, and it is still forming.]**

**⚠️ Treat this section differently from the rest.** These patterns are 2–3 years old,
the naming is not yet stable, and **multiple overlapping taxonomies are in circulation** —
practitioners currently work from at least three sources: Andrew Ng's four foundational
patterns, Anthropic's workflow patterns, and a growing set of emergent reliability and
memory patterns. Some are genuine recurring solutions; some are vendor framing. **The
distinction is not yet settled, and anyone claiming otherwise is ahead of the evidence.**

**The distinction that organizes everything**: **workflows** — LLMs and tools orchestrated
through **predefined code paths**, where the flow is fixed and the model only generates
within each step — versus **agents**, where the model decides what comes next. **⚠️ Prefer
workflows.** They are more predictable, more auditable, cheaper, easier to test, and lower
latency; reach for agency only when the task genuinely can't be sequenced in advance.

| Pattern | What it is |
|---|---|
| **Prompt chaining** | Fixed sequence, each step consuming the last, with **programmatic gates between steps** that halt on bad output. Trades latency for accuracy; errors don't snowball |
| **Routing** | Classify the input, dispatch to a specialized handler |
| **RAG** | Retrieve, augment, generate — grounding output in a controlled corpus. ⚠️ **A fixed RAG chain is a workflow, not an agent**: the order is hardcoded and the model doesn't get a vote |
| **Tool use / function calling** | The model calls external capabilities |
| **ReAct** | Interleaved reasoning and action in a loop, adjusting on each observation. **Good for exploratory tasks**; predates the current framing by ~2 years |
| **Plan-and-Execute** | A planner produces a full multi-step plan, an executor runs it. **Better for long structured tasks where mid-stream drift is costly** |
| **Reflection / Evaluator-Optimizer** | A generator produces, a separate evaluator critiques, iterate. ⚠️ **Separated roles is what distinguishes this from single-model self-critique** |
| **Programmatic planning** | Hardcoded sequences or state machines for business processes requiring strict adherence — **high determinism, easier debugging, "golden paths"** |
| **Multi-agent / topologies** | Specialized agents with restricted toolsets; chain, star, and mesh communication topologies |
| **Human-in-the-loop** | ⚠️ **A cross-cutting modifier insertable into any pattern** as an approval gate, with **stopping conditions such as a maximum iteration count** |
| **Memory** | Short-term, long-term, episodic, procedural — retrieved separately and combined into context |
| **Guardrails** | Input and output validation at the boundary |
| **Progressive disclosure** | Load capability and context on demand to combat **context rot** |

> **⚠️ GOTCHA — the design forces that are specific to this domain and catch experienced
> engineers:**
> - **Non-determinism is the substrate.** Every pattern here is scaffolding to make a
>   probabilistic component behave like a reliable one. **The mental shift is from
>   "LLM-as-oracle" to "LLM-as-component."**
> - **Context is a scarce, contended resource**, and quality degrades as it fills.
> - **Cost and latency scale with orchestration.** Each agentic decision is another call.
>   **Runaway loops are a real financial failure mode** — hence iteration caps.
> - **⚠️ Multi-agent was a 2023–24 buzzword and is substantially over-applied.** A single
>   well-scaffolded agent beats a committee for most tasks.
> - **Observability is different**: step-level tracing, token cost tracking, hallucination
>   detection, and guardrail-violation metrics — **standard API logs won't show you where a
>   multi-step workflow went wrong.**
> - **Treat prompts as code** — versioned, decoupled from orchestration, testable.
> - **Don't pick a framework before you know which pattern you need.**

**[DURABLE, and this is the transferable insight]**: **if your system needs multiple steps,
external data, conditional branching, or retry logic, you are already building an agent
whether or not you called it one** — and the patterns in §8–§11 → `patterns-distributed-concurrency-and-messaging` apply to it, because it is
a distributed system with an unusually unreliable component in it.

---

## §13. Migration and Legacy Patterns

**Strangler Fig** — ⚠️ **the default for legacy replacement.** Route traffic through a
facade, replace behind it incrementally, retire the old system when nothing routes to it.
**Big-bang rewrites fail at a rate that should have settled this argument decades ago.**

**Branch by Abstraction** — introduce an abstraction over the thing you're replacing,
implement the new side behind it, switch, remove. **Lets large changes live on trunk.**

**Anti-Corruption Layer** (§7 → `patterns-architectural`) — translate at the boundary so a legacy or vendor model
doesn't infect yours.

**Also**: **parallel run** (⚠️ **run both and compare outputs before cutting over** —
the highest-confidence migration technique available and badly underused), **feature
toggles** (with a plan for removal — see §14 → `patterns-reference`), **expand-contract / parallel change** for
schema and API migration (add the new, migrate, remove the old — **the only safe way to
change a schema under live traffic**), **characterization tests** (capture current
behaviour before changing it, bugs included).
