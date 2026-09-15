---
name: toc-type-systems-and-randomization
description: "Use when reasoning about type systems, verification, or randomized algorithms: types as logic and the Curry–Howard correspondence, decidability of type checking and inference, what formal methods actually buy and where lightweight methods win, and randomness and approximation — BPP, Monte Carlo versus Las Vegas, the PCP theorem and hardness of approximation, heuristics and No Free Lunch."
---

# Theory of Computation: Type Systems, Logic and Verification, and Randomness and Approximation

> **Part 4 of 5** of the *Theory of Computation* reference (plugin `theory-of-computation`), covering §12–§13. Sibling skills: `toc-automata-regex-and-parsing` (§0–§3), `toc-computability-and-complexity` (§4–§7), `toc-beyond-np-space-and-distributed-limits` (§8–§11), `toc-reference` (§14–§19). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Verified August 2026. See §16 → `toc-reference` for the currency snapshot and what goes stale first.

> **How to read this.** Reference, not a course. Three markers:
> - **[DURABLE]** — proven theorems and stable practice. **This is most of the document,
>   and it does not expire.**
> - **[VERSIONED]** — the small moving parts: recent results, solver capability, open
>   problems.
> - **[CONTESTED]** — genuine disagreement, mostly about pedagogy and practical relevance.
>
> **⚠️ GOTCHA** boxes mark places where ignorance of the theory produces a specific,
> expensive production failure — which is the whole argument for learning it.
>
> **The three framings that organize everything below:**
> 1. **This is the only branch of CS that tells you what you cannot do.** Everything else
>    teaches techniques. Theory tells you when to stop looking — and **knowing a problem is
>    undecidable or NP-hard is more valuable than any algorithm**, because it redirects
>    you from an impossible goal to a tractable approximation of it.
> 2. **You already use it; you may not know the names.** Regex is finite automata.
>    Your parser is a pushdown automaton. Your state machine is a DFA. Your build system's
>    cycle detection is graph theory. **The theory isn't an addition to your practice — it's
>    a description of it**, and knowing the description tells you where the edges are.
> 3. **"Hard" is not "impossible," and this is the most consequential practical point.**
>    NP-complete problems with thousands of variables are solved routinely (§9 → `toc-beyond-np-space-and-distributed-limits`). The
>    theory tells you *no algorithm is fast on all inputs* — it says nothing about
>    **your** inputs, which are usually structured. **Treating NP-hardness as a verdict
>    rather than a warning is the single most common misapplication of this material.**

---

## §12. Type Systems, Logic, and Verification

**[DURABLE] Type systems are decidable approximations of undecidable properties** (§4.1 → `toc-computability-and-complexity`) —
which is the single most clarifying sentence about them.

**The Curry–Howard correspondence**: **propositions are types; proofs are programs.**
Proving a theorem and writing a well-typed program are the same activity. This is not a
cute analogy — it's the foundation of **Coq/Rocq, Lean, Agda, Idris**, and the reason
dependent types let you encode "this list has length n" or "this index is in bounds" in the
type itself.

**The expressiveness ladder, and its cost:**
```
Simply typed          decidable, restrictive
+ polymorphism        Hindley–Milner: full inference, decidable, the ML/Haskell sweet spot
+ subtyping           inference gets harder
+ higher-rank         ⚠️ full inference becomes undecidable — you must annotate
+ dependent types     type checking decidable, inference generally not.
                      Types can express arbitrary properties — and you now write proofs
```
**⚠️ The trade-off is fundamental and not fixable**: more expressive types catch more bugs
and demand more annotation. **A type system that inferred everything and caught everything
would decide undecidable properties.**

**Practical verification** (see §7 → `toc-computability-and-complexity` for the solvers underneath): **model checking** —
exhaustively explore a finite state space, with **⚠️ state-space explosion** as the
permanent enemy, mitigated by symbolic representation, abstraction, and partial-order
reduction. **Abstract interpretation** — sound over-approximation, accepting false
positives to guarantee no false negatives (this is where sound static analyzers live).
**TLA+ / Alloy** — specify and check designs before building them, and **[DURABLE] this is
the highest-leverage formal method for most engineers** because it catches design errors
in distributed protocols where testing cannot.

**[DURABLE] The pragmatic position**: full functional verification is expensive and
justified for kernels, compilers, cryptography, and safety-critical control. **Lightweight
formal methods — property-based testing, model checking a protocol, a TLA+ spec of your
consensus design — have a far better cost/benefit ratio and are radically under-used.**

---

## §13. Randomness, Approximation, and Heuristics

**Randomized complexity**: **BPP** (bounded-error probabilistic polynomial time) — and
**[DURABLE] it is now widely conjectured that P = BPP**, i.e. randomness probably doesn't
buy asymptotic power, which was a genuine surprise. **Randomness buys simplicity and
practical speed**, which is why randomized algorithms are everywhere: quicksort's pivot,
Miller–Rabin primality, hashing, Monte Carlo methods, randomized load balancing.

**⚠️ Monte Carlo vs. Las Vegas** is worth keeping straight: Monte Carlo is fast with a
bounded error probability; Las Vegas is always correct with randomized runtime. **You need
to know which one you're deploying**, because "wrong 1 in 2^40 times" is a very different
operational posture from "occasionally slow."

**Approximation** (§6.2 → `toc-computability-and-complexity`), and the sharp edge: **the PCP theorem** implies many problems are
**hard even to approximate well** — so "just approximate it" is not universally available,
and for some problems the achievable ratio is provably capped unless P = NP.

**Heuristics and metaheuristics** — greedy, local search, simulated annealing, tabu search,
genetic algorithms, beam search. **[DURABLE] No performance guarantees, frequently
excellent in practice**, and **the No Free Lunch theorem** says no optimizer beats all
others across all problems — which is the formal version of "your heuristic works because
it exploits structure in your instances," and a reason to be suspicious of anyone selling a
universal optimizer.
