---
name: toc-computability-and-complexity
description: "Use when you need to know whether a problem is solvable and how hard it is: the halting problem, Rice's theorem and why static analysis has false positives, reductions as the most transferable skill here, complexity classes and the P versus NP map, recognizing NP-hardness and the escape hatches in order of usefulness, and SAT and SMT solvers and why 'NP-complete' is not a verdict."
---

# Theory of Computation: Computability, Complexity Classes, NP-Hardness, and Solvers

> **Part 2 of 5** of the *Theory of Computation* reference (plugin `theory-of-computation`), covering §4–§7. Sibling skills: `toc-automata-regex-and-parsing` (§0–§3), `toc-beyond-np-space-and-distributed-limits` (§8–§11), `toc-type-systems-and-randomization` (§12–§13), `toc-reference` (§14–§19). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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

## §4. Computability — What You Cannot Do

### 4.1 The halting problem and what follows

**[DURABLE] There is no program that takes an arbitrary program and input and correctly
decides whether it halts.** The proof is a two-line diagonalization, and its consequences
are everywhere in your tooling.

**Rice's theorem generalizes it, and this is the version engineers should know:**
**every non-trivial semantic property of programs is undecidable.** Not "hard" —
**undecidable.** Does this program ever throw? Is this variable ever null? Are these two
functions equivalent? Is this code dead? Does this ever access out of bounds?
**All undecidable in general.**

> **⚠️ GOTCHA — this is why your tools behave the way they do, and knowing it changes how
> you use them.** A static analyzer cannot be simultaneously **sound** (no false negatives)
> and **complete** (no false positives) and **terminating**. It must pick two. So:
> - **Linters and most analyzers choose "terminating + roughly useful"** and accept both
>   false positives and false negatives.
> - **Sound analyzers** (used in avionics, automotive) accept **false positives** — they'll
>   flag safe code — because missing a real bug is unacceptable.
> - **Type systems** are decidable approximations that reject some correct programs.
>   **When the compiler rejects code you know is fine, that is the theory, not a bug.**
>
> **The engineering consequence: stop asking for a tool with no false positives.** You are
> asking for a solution to the halting problem. Ask instead which side of the trade-off the
> tool sits on, and whether that matches your risk.

### 4.2 Reductions — the most transferable skill here

**[DURABLE] "If I could solve B, I could solve A; A is impossible; therefore B is
impossible."** This is how nearly every undecidability and hardness result is proved, and
**it is a reasoning pattern you can apply directly at work.**

The practical version: when a stakeholder asks for a feature, ask whether it reduces to
something known impossible or known hard. *"Detect all infinite loops before deployment"*
reduces to halting. *"Find the optimal assignment across all these constraints"* frequently
reduces to something NP-hard (§6). **Recognizing the reduction saves you a quarter.**

### 4.3 Other undecidable things you may encounter
Program equivalence. Whether a CFG is ambiguous. Whether two CFGs generate the same
language. The Post Correspondence Problem (the standard tool for proving other things
undecidable). Type inference for some sufficiently expressive systems (§12 → `toc-type-systems-and-randomization`). Whether an
arbitrary Diophantine equation has a solution (Hilbert's 10th). **Some tile-matching and
configuration problems** — which is why certain package-resolution and layout problems are
genuinely, formally hard.

**[DURABLE] Undecidable does not mean useless.** Every practical tool works on a decidable
*subset*, or accepts approximation, or uses a timeout. **Termination checkers, model
checkers, and dependent type systems all exist and work** — by restricting the problem, not
by solving the impossible one.

---

## §5. Complexity Classes

### 5.1 The map

```
    P  ⊆  NP  ⊆  PSPACE  ⊆  EXPTIME
    │      │       │
    │      │       └── games, quantified formulas, some planning
    │      └────────── verifiable in poly time (SAT, TSP-decision, scheduling…)
    └───────────────── solvable in poly time
    
  ⚠️ We know P ≠ EXPTIME (time hierarchy theorem).
     We do NOT know whether P = NP, NP = PSPACE, or P = PSPACE.
```

**[DURABLE] The definition of NP that actually helps engineers**: not "solvable by a
nondeterministic machine" but **"a proposed solution can be checked quickly."** If someone
hands you an assignment, can you verify it in polynomial time? Then it's in NP. **That
framing makes NP-membership obvious for most problems you'll meet.**

**NP-hard**: at least as hard as everything in NP. **NP-complete**: in NP *and* NP-hard —
the hardest problems in NP, all equivalent under polynomial reduction.
**⚠️ NP-hard problems need not be in NP** — optimization versions and problems outside NP
are often NP-hard without being NP-complete, and the distinction matters when someone
claims a "solution."

**co-NP** contains problems whose *no*-instances are easily verified. **Tautology checking
is co-NP-complete** — which is why proving a formula always true is structurally harder to
certify than finding a counterexample.

### 5.2 Some honest cautions

**⚠️ Polynomial ≠ fast.** An O(n¹⁰⁰) algorithm is polynomial and useless. Galactic
algorithms with enormous constants are polynomial and never run. **P is a robust
theoretical boundary, not a promise about your latency budget.**

**⚠️ Asymptotics hide constants and cache behaviour.** For real n, an O(n log n) algorithm
with terrible locality routinely loses to an O(n²) one that fits in cache. **Measure**
(§9 → `toc-beyond-np-space-and-distributed-limits` makes this precise in the other direction).

**⚠️ Worst case ≠ your case.** Quicksort is O(n²) worst case and the practical default.
Simplex is exponential worst case and dominates linear programming in practice.
**This gap is the entire subject of §6.3.**

---

## §6. Your Problem Is NP-Hard. Now What?

**[DURABLE] This is the section with the most direct daily value, and the one most
engineers get wrong in both directions** — either despairing, or not recognizing the
hardness at all and shipping something that falls over at scale.

### 6.1 Recognizing it

**The canonical problems worth knowing by sight**, because your problem is usually one of
them wearing a business costume:

| Problem | Shows up as |
|---|---|
| **SAT / 3-SAT** | Configuration, feature flags, dependency resolution |
| **Knapsack / Subset Sum** | Budget allocation, resource packing, cart optimization |
| **Bin Packing** | VM placement, container scheduling, shipping |
| **Graph Coloring** | Register allocation, scheduling with conflicts, frequency assignment |
| **TSP / Vehicle Routing** | Delivery, tool-path, sequencing anything |
| **Set Cover** | Minimum test suite, sensor placement, feature selection |
| **Clique / Independent Set** | Compatibility groups, conflict-free selection |
| **Scheduling with constraints** | Almost every scheduling problem you'll be handed |
| **Integer Programming** | ⚠️ **The general form of most of the above** |

**[DURABLE] The tell**: you're choosing a subset or an ordering, constraints interact, and
a greedy choice early can be shown to force a bad outcome later. **When a problem has that
shape, look for the reduction before you start optimizing.**

### 6.2 The escape hatches, in order of usefulness

```
1. IS THE INPUT SMALL?           n=20 exhaustive search is instant. Check first.
2. IS IT ACTUALLY THE HARD CASE? Real inputs are structured; §6.3
3. USE A SOLVER                  SAT/SMT/MIP/CP — §7. Often the right answer
4. APPROXIMATE                   Many NP-hard problems have provable ratio bounds
5. HEURISTIC                     Greedy, local search, simulated annealing, GA
6. FIXED-PARAMETER TRACTABLE     f(k)·poly(n) — exponential only in a small parameter
7. PSEUDO-POLYNOMIAL             Knapsack is O(nW) — fine if W is small
8. SPECIAL CASE                  Is your graph a tree? planar? bounded treewidth?
9. RELAX THE PROBLEM             ⚠️ Often the real answer: does the business need OPTIMAL?
10. CHANGE THE PROBLEM           Ditto
```

**[DURABLE] #9 and #10 deserve more attention than they get.** "Optimal" is usually a
requirement someone assumed rather than one the business stated. **A solution within 2% of
optimal, computed in 100 ms, beats an optimal one computed in six hours** for nearly every
real application — and asking that question is often worth more than any algorithm.

**Approximation with guarantees** is genuinely useful: Vertex Cover has a simple 2-approx;
Set Cover has a ln(n) approximation and **that's provably the best possible unless P = NP**;
Metric TSP has classical constant-factor results. **⚠️ Some problems are hard even to
approximate** — that's the PCP theorem's practical legacy, and it means "just approximate
it" is not always available.

### 6.3 The most important practical caveat

**[DURABLE] NP-hardness is a statement about worst-case inputs over all instances. It says
nothing about yours.**

Real instances have structure: dependency graphs are sparse and near-acyclic, schedules
have natural clustering, configuration constraints are mostly independent. **Modern SAT
solvers routinely handle industrial instances with millions of variables** (§7) — instances
that are formally NP-complete and empirically easy.

**⚠️ The failure mode in both directions:**
- **Giving up because it's NP-hard**, when a solver would have done it in a second.
- **Assuming it'll be fine because it worked in testing**, when your test data was
  structured and production data isn't. **The exponential is still there and it will find
  you.** Set timeouts, have a fallback, and monitor solve times.

---

## §7. SAT, SMT, and Solvers

**[DURABLE] The single most useful practical lesson in complexity for working engineers:
NP-complete does not mean unsolvable, and there is mature, free tooling that will do it
for you.**

**SAT** — Boolean satisfiability. The first problem proved NP-complete (Cook–Levin), and
the one where the gap between theory and practice is widest. Modern **CDCL** solvers
(conflict-driven clause learning, with unit propagation, watched literals, restarts,
clause learning) have made SAT solving one of the great practical successes in CS — the
literature's own phrase for it is **"the unreasonable effectiveness of SAT solvers."**

**SMT** — SAT plus theories: integers and reals, bit-vectors, arrays, strings, algebraic
datatypes, uninterpreted functions. **This is what makes it useful for software**, because
your constraints aren't Boolean.

**[VERSIONED] The tools**: **Z3** (Microsoft — general-purpose, the default, especially
strong on quantifier-free arithmetic and arrays), **cvc5** (strings, algebraic datatypes,
advanced arithmetic), **Bitwuzla** (bit-vectors and floating point; successor to
Boolector), **Yices 2** (fast on linear arithmetic and bit-vectors), **MathSAT**
(interpolation, model generation), and **CaDiCaL**/**Kissat** on the pure-SAT side.
**MiniZinc/OR-Tools** for constraint programming; **Gurobi/CPLEX/HiGHS** for MIP.

**Where they're actually used**: **program verification** (Dafny, Verus, F\*, Viper,
Creusot, and the whole bounded-model-checking family), **symbolic execution** and test
generation, **type checking** for refinement types, **package dependency resolution**
(PubGrub and friends), **scheduling and configuration**, and **hardware verification**,
which is where the money was that built these tools.

> **⚠️ GOTCHA — the practical failure modes of solvers, which nobody warns you about:**
> - **Encoding dominates everything.** The same problem stated two ways can differ by
>   orders of magnitude. **Move as much of the problem outside the solver as you can** —
>   the solver is the scalability bottleneck, so preprocessing pays enormously.
> - **⚠️ Instability is real and under-appreciated.** Semantically identical queries can
>   flip between solved and timed-out based on trivial syntactic differences — variable
>   naming, term ordering, formula shape. Research on program-verification workloads has
>   measured this directly and built tooling specifically to normalize queries and
>   stabilize solve times. **If your CI intermittently fails a verification step, this may
>   be why, and it is not your logic being wrong.**
> - **Non-linear arithmetic is where solvers fall over**, and disabling the non-linear
>   solver is a known stabilization technique in production verification work.
> - **Always set a timeout and handle `unknown`.** `unknown` is a real answer, not an error.
> - **Solvers disagree**, and portfolio approaches (dispatch to whichever solver suits the
>   theory) are standard in serious tools for exactly that reason.
