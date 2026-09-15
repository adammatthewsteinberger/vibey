---
name: logistics-constraint-programming-metaheuristics-and-bounds
description: "Use when exact methods are not the right tool or you need to judge a solution: constraint programming and where it beats MIP, metaheuristics including simulated annealing, tabu search and genetic algorithms, local search and large neighbourhood search as the workhorses of practical routing, and bounds and solution quality — how to know how good an answer is rather than assuming."
---

# Logistics and Optimization Software: Constraint Programming, Metaheuristics, Local Search, and Bounds

> **Part 2 of 5** of the *Logistics and Optimization Software* reference (plugin `logistics-software-optimization`), covering §6–§9. Sibling skills: `logistics-why-projects-fail-complexity-and-modeling` (§0–§5), `logistics-routing-packing-scheduling-and-network-design` (§10–§16), `logistics-inventory-forecasting-operations-and-solvers` (§17–§24), `logistics-reference` (§25–§31). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The algorithms and complexity results are permanent. Two areas are live. See §25 → `logistics-reference` for the solver landscape and the quantum and AI optimization claims.

> **⚠️ Scope.** For engineers building or integrating logistics systems. Complements a
> data-engineering reference (pipelines), an operations reference (process), and a
> business reference (unit economics).
>
> **⚠️ GOTCHA** boxes mark things that sink projects or silently produce wrong answers.
>
> **The three ideas that organize this document:**
> 1. **⚠️ Optimization projects almost never fail on the algorithm.** **They fail on data
>    quality, on constraints nobody told you about, and on solutions the drivers refuse to
>    run** (§1 → `logistics-why-projects-fail-complexity-and-modeling`). **The maths is the easy part and it is not where your time goes.**
> 2. **⚠️ NP-hard does not mean unsolvable — it means no guaranteed-fast exact method.**
>    **Real instances with tens of thousands of stops are solved to within a few percent
>    of optimal every night by well-engineered heuristics** (§2 → `logistics-why-projects-fail-complexity-and-modeling`, §8).
> 3. **⚠️ A 2% better solution that operations won't execute is worth 0%.** **Stability,
>    explainability and consistency with yesterday's plan routinely matter more than the
>    objective value** (§1 → `logistics-why-projects-fail-complexity-and-modeling`, §26 → `logistics-reference`).

---

## §6. Constraint Programming

**⚠️ A different paradigm, and often better than MIP for scheduling and sequencing.**
**CP works by constraint propagation — domain filtering — plus search, rather than by LP
relaxation.**
**⚠️ Where CP wins**: **scheduling with precedence and resource constraints, rostering,
problems with complex logical conditions, and anything with rich global constraints
(`alldifferent`, `cumulative`, `noOverlap`, `element`).** ⚠️ **CP-SAT in particular
(OR-Tools) is exceptionally strong on scheduling and has largely displaced hand-rolled
approaches for those problems.**
**⚠️ Where MIP wins**: **problems with strong linear structure, cost-driven objectives, and
where you need good bounds.**
⚠️ **Modern CP-SAT solvers hybridize — they include SAT-style clause learning and
LP relaxations — so the paradigm boundary is blurrier than it was.**

---

## §7. Metaheuristics

**⚠️ When exact methods don't fit the time budget. All of them are variations on "search
the neighbourhood, sometimes accept worse, escape local optima."**
```
LOCAL SEARCH / HILL CLIMBING   ⚠️ the base. Gets stuck
SIMULATED ANNEALING            accept worse with decreasing probability
TABU SEARCH                    ⚠️ forbid recent moves to escape cycles.
                               Historically very strong on VRP
GENETIC / EVOLUTIONARY         ⚠️ popular, and frequently OUTPERFORMED by
                               simpler LNS on routing. Popularity ≠ performance
ANT COLONY, PARTICLE SWARM     ⚠️ heavily published, rarely the best choice
   in production. Be sceptical of the metaphor-driven literature here
GRASP, VNS, ⚠️ LNS/ALNS        §8 — the ones that actually win
HYPER-HEURISTICS               choose among heuristics adaptively
```
> **⚠️ GOTCHA — the metaheuristic literature has a serious novelty problem.** ⚠️ **A large
> body of published "novel" nature-inspired metaheuristics (harmony search, various animal
> algorithms) has been criticized as rebranding existing methods with new metaphors, and
> comparisons are frequently against weak baselines on synthetic instances.** **This is a
> well-documented critique within the OR community.** **⚠️ For routing, start with LNS —
> it is the practical state of the art and it is simple.**

---

## §8. ⚠️ Local Search and Large Neighbourhood Search

**⚠️ This is what actually powers production routing engines, and it's conceptually
simple.**
```
⚠️ LNS / ALNS (Adaptive LNS)
  1. Start from any feasible solution
  2. DESTROY — remove part of it (random stops, a geographic cluster,
     a whole route, the most "expensive" stops)
  3. REPAIR — reinsert greedily or with a small exact solve
  4. Accept or reject; ⚠️ ADAPT the weights on destroy/repair operators
     based on which have been working
  5. Repeat until the time budget is gone
```
**⚠️ Why it wins in practice:**
- ⚠️ **It handles arbitrary messy constraints.** **The repair step just has to respect
  them; you never need a clean mathematical formulation of every business rule.**
- ⚠️ **It's anytime.** **Stop whenever; you have a valid solution.** **This matches
  operational reality where you have 20 minutes, not "until optimal."**
- **⚠️ It warm-starts naturally**, **which is exactly what you need for §1 → `logistics-why-projects-fail-complexity-and-modeling`'s stability
  requirement and for §23 → `logistics-inventory-forecasting-operations-and-solvers`'s dynamic re-optimization.**
- **It parallelizes reasonably.**

**⚠️ Classic VRP local search moves worth knowing**: **2-opt and Or-opt (within a route),
relocate and swap (between routes), 2-opt* (cross-route tail exchange), and ⚠️ ejection
chains.** **Combined with LNS these cover most of what commercial engines do.**

---

## §9. Bounds and Solution Quality

> **⚠️ GOTCHA — without a bound you have no idea whether your heuristic is 2% or 40% from
> optimal, and "it produced a solution" tells you nothing.** ⚠️ **This is the single most
> common gap in home-grown optimizers.**

**⚠️ How to get a bound**: **the LP relaxation; a Lagrangian relaxation; a simplified
problem (e.g. the assignment relaxation of a TSP); or a column-generation lower bound.**
**⚠️ Even a crude bound is transformative** — **it converts "the heuristic ran" into "we
are within X%," which is the number that justifies further investment or closes the
project.**
**⚠️ Benchmark against standard instance libraries**: **TSPLIB, CVRPLIB / Solomon and
Gehring-Homberger for VRPTW, MIPLIB for MIP.** ⚠️ **And benchmark against the HUMAN
baseline too, because that's the actual decision.**

---

# PART II — THE CORE PROBLEM FAMILY
