---
name: logistics-why-projects-fail-complexity-and-modeling
description: "Use at the start of an optimization project: why these projects fail for organizational and data reasons more often than algorithmic ones, complexity assessed honestly rather than as a verdict, linear programming and duality, mixed-integer programming and branch-and-bound, and how to model well — formulation strength, symmetry breaking, and the modelling choices that decide whether a solver finds anything. Includes the router for the whole logistics-software-optimization reference."
---

# Logistics and Optimization Software: Why Projects Fail, Complexity, Linear Programming, MIP, and Modeling Well

> **Part 1 of 5** of the *Logistics and Optimization Software* reference (plugin `logistics-software-optimization`), covering §0–§5. Sibling skills: `logistics-constraint-programming-metaheuristics-and-bounds` (§6–§9), `logistics-routing-packing-scheduling-and-network-design` (§10–§16), `logistics-inventory-forecasting-operations-and-solvers` (§17–§24), `logistics-reference` (§25–§31). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
>    run** (§1). **The maths is the easy part and it is not where your time goes.**
> 2. **⚠️ NP-hard does not mean unsolvable — it means no guaranteed-fast exact method.**
>    **Real instances with tens of thousands of stops are solved to within a few percent
>    of optimal every night by well-engineered heuristics** (§2, §8 → `logistics-constraint-programming-metaheuristics-and-bounds`).
> 3. **⚠️ A 2% better solution that operations won't execute is worth 0%.** **Stability,
>    explainability and consistency with yesterday's plan routinely matter more than the
>    objective value** (§1, §26 → `logistics-reference`).

---

## §0. Routing

| You want... | Go to |
|---|---|
| **⚠️ Why these projects fail** | **§1** |
| Complexity, honestly | §2 |
| LP and duality | §3 |
| MIP and branch-and-bound | §4 |
| **⚠️ Modeling well** | **§5** |
| Constraint programming | §6 → `logistics-constraint-programming-metaheuristics-and-bounds` |
| Metaheuristics | §7 → `logistics-constraint-programming-metaheuristics-and-bounds` |
| **⚠️ Local search and LNS** | **§8 → `logistics-constraint-programming-metaheuristics-and-bounds`** |
| Bounds and solution quality | §9 → `logistics-constraint-programming-metaheuristics-and-bounds` |
| Shortest path and flow | §10 → `logistics-routing-packing-scheduling-and-network-design` |
| TSP | §11 → `logistics-routing-packing-scheduling-and-network-design` |
| **⚠️ VRP — the core problem** | **§12 → `logistics-routing-packing-scheduling-and-network-design`** |
| Packing and loading | §13 → `logistics-routing-packing-scheduling-and-network-design` |
| Assignment and matching | §14 → `logistics-routing-packing-scheduling-and-network-design` |
| Scheduling | §15 → `logistics-routing-packing-scheduling-and-network-design` |
| Facility location and network design | §16 → `logistics-routing-packing-scheduling-and-network-design` |
| **Inventory** | **§17 → `logistics-inventory-forecasting-operations-and-solvers`** |
| Forecasting | §18 → `logistics-inventory-forecasting-operations-and-solvers` |
| **The systems landscape** | **§19 → `logistics-inventory-forecasting-operations-and-solvers`** |
| Warehouse operations | §20 → `logistics-inventory-forecasting-operations-and-solvers` |
| Last mile | §21 → `logistics-inventory-forecasting-operations-and-solvers` |
| **⚠️ Data and distance matrices** | **§22 → `logistics-inventory-forecasting-operations-and-solvers`** |
| Dynamic and stochastic | §23 → `logistics-inventory-forecasting-operations-and-solvers` |
| Solvers and tooling | §24 → `logistics-inventory-forecasting-operations-and-solvers` |
| **What's live** | **§25 → `logistics-reference`** |
| **⚠️ Anti-patterns** | **§26 → `logistics-reference`** |
| Misconceptions | §27 → `logistics-reference` |
| Numbers, books, quick ref | §28–§30 → `logistics-reference` |

---

## §1. ⚠️ Why Optimization Projects Fail

**⚠️ Ranked roughly by how often I'd expect each to be the actual cause:**
```
1. ⚠️ THE DATA IS WRONG. Bad addresses, stale service times, wrong vehicle
   capacities, missing time windows. ⚠️ The optimizer faithfully optimizes
   a fiction and produces a confidently infeasible plan
2. ⚠️ HIDDEN CONSTRAINTS. "You can't send Dave to that site." "That customer
   must be first." "The forklift can't reach aisle 12 after 3pm."
   ⚠️ These live in people's heads and surface only when the plan is rejected
3. ⚠️ THE OBJECTIVE ISN'T WHAT THEY SAID. They said "minimize cost." They
   meant "don't upset the big customer, keep drivers on familiar routes,
   and never be late to the hospital"
4. ⚠️ NOBODY TRUSTS IT. A black box that outputs a different plan every day
   loses to a dispatcher's spreadsheet, even when it's better
5. ⚠️ NO FEASIBLE FALLBACK. Optimizer down or infeasible at 4am → operations
   halts. ⚠️ You need a degraded mode that always produces SOMETHING
6. Runtime doesn't fit the operational window
7. ⚠️ Then, occasionally, the algorithm
```
> **⚠️ GOTCHA — solution STABILITY is an unstated requirement in essentially every
> logistics deployment, and violating it kills more rollouts than poor objective
> values.** ⚠️ **Re-optimizing from scratch each night produces plans that differ wildly
> from yesterday's for a 0.3% gain.** **Drivers lose route familiarity, customers lose
> consistent delivery windows, and planners lose confidence.** **⚠️ Add an explicit
> penalty for deviation from the incumbent plan, and expose it as a tunable knob.**

**⚠️ What to do about it, in order**: **spend your first weeks on data profiling, not
modeling**; ⚠️ **build a feasibility checker and a plan EXPLAINER before you build the
optimizer** — **"why is this stop on this route?" is the question you'll be asked
daily**; **run shadow mode against human plans for weeks before switching**; **and
⚠️ measure against the CURRENT process, not against the theoretical optimum, because that
is the comparison that determines whether the project survives.**

---

# PART I — OPTIMIZATION FOUNDATIONS

---

## §2. Complexity, Honestly

```
P            solvable in polynomial time. ⚠️ Shortest path, LP, max flow,
             assignment, min spanning tree
NP-complete  ⚠️ decision problems where a solution is checkable fast
NP-hard      ⚠️ at least as hard. TSP, VRP, bin packing, most scheduling
```
> **⚠️ GOTCHA — "NP-hard" is routinely used to mean "impossible," and that is wrong in a
> way that matters commercially.** ⚠️ **It means no known algorithm guarantees optimality
> in polynomial time IN THE WORST CASE.** **It says nothing about your instances.**
> **⚠️ TSP instances with tens of thousands of cities have been solved to proven
> optimality; real VRPs with thousands of stops are routinely solved to within 1–3% of a
> lower bound in minutes.** **Structure in real data — geographic clustering, tight time
> windows, capacity limits — often makes practical instances far easier than the worst
> case.**
> **⚠️ The correct inference from NP-hardness is "don't expect a guaranteed-optimal exact
> method to scale," not "give up."**

**⚠️ What actually drives difficulty in practice** — **and it's rarely raw stop count:**
**the number of INTERACTING constraints; time window tightness (⚠️ tight windows can make
finding any feasible solution the hard part); heterogeneous fleets; and multi-objective
tradeoffs.** ⚠️ **A 500-stop problem with driver skills, time windows, capacity in three
dimensions, break rules and multi-day horizons is far harder than a 5,000-stop pure
capacitated VRP.**

---

## §3. Linear Programming

**⚠️ Continuous variables, linear objective and constraints. Polynomial-time solvable and
essentially a solved technology — LP is the workhorse underneath everything else.**
```
Simplex     ⚠️ exponential worst case, excellent in practice; warm-starts well
Interior point  polynomial; better on very large sparse problems
⚠️ DUALITY  every LP has a dual. Dual values = SHADOW PRICES — the marginal
   value of relaxing a constraint by one unit
```
**⚠️ Shadow prices are the most under-used output in applied optimization.** **They tell
you what to change about the BUSINESS, not just the plan:** ⚠️ **"the capacity constraint
at depot 3 has a shadow price of $400/unit" is an investment case, and it falls out of the
solve for free.**
**⚠️ Sensitivity analysis matters more than the optimal solution in planning contexts** —
**how much can a cost change before the plan changes?**

---

## §4. MIP and Branch-and-Bound

**⚠️ Add integrality and you leave P.** **Nearly every logistics decision is integer:
which vehicle, whether to open a facility, which order goes where.**
```
⚠️ BRANCH AND BOUND
  Solve the LP relaxation → a BOUND on the best possible
  Branch on a fractional variable → two subproblems
  PRUNE any subproblem whose bound is worse than the incumbent
⚠️ CUTTING PLANES  add valid inequalities to tighten the relaxation
BRANCH AND CUT     ⚠️ both. What every modern solver does
⚠️ PRESOLVE        eliminate variables and constraints before solving.
   Often the single largest speedup, and it's automatic
COLUMN GENERATION / BRANCH AND PRICE  ⚠️ for problems with enormous variable
   counts — generate columns (e.g. whole routes) as needed. THE technique
   behind exact VRP and crew scheduling methods
```
**⚠️ The MIP gap is the number you actually operate on**: **(incumbent − bound) /
incumbent.** ⚠️ **A 2% gap means you're provably within 2% of optimal — usually far more
than good enough, and often reached in seconds while proving optimality would take
hours.** **Set a gap tolerance and a time limit. Always.**

---

## §5. ⚠️ Modeling Well

**⚠️ The formulation matters more than the solver. A good model on a free solver beats a
bad model on an expensive one, routinely.**
```
⚠️ TIGHT vs LOOSE formulations. Two models with identical feasible integer
   sets can have vastly different LP relaxations. ⚠️ The tighter relaxation
   prunes far more and can be orders of magnitude faster
⚠️ BIG-M   the classic trap. M too large → weak relaxation, numerical
   instability, garbage. ⚠️ Use the SMALLEST valid M you can prove
⚠️ SYMMETRY  identical vehicles/machines mean the solver explores equivalent
   solutions repeatedly. Break it with ordering constraints
INDICATOR CONSTRAINTS  ⚠️ often better than big-M; solvers handle them natively
SOS constraints · piecewise linear via SOS2
⚠️ SOFT CONSTRAINTS  penalize in the objective rather than forbidding.
   ⚠️ THE most important practical modeling decision — see below
```
> **⚠️ GOTCHA — an infeasible model is useless to operations and "infeasible" is the worst
> possible output at 4am.** ⚠️ **Make almost everything soft with a penalty, ordered by
> business priority: hard constraints only for genuine physical or legal impossibilities.**
> **Then you always get a plan, and the violations are visible and ranked.**
> **⚠️ Bonus: penalty weights become the interface where operations expresses priorities,
> which converts an argument about the algorithm into a conversation about the business.**

**⚠️ Numerical hygiene** — **keep coefficient magnitudes within a few orders of magnitude
of each other; scale your data.** ⚠️ **Mixing costs in cents with distances in millimetres
produces coefficient ranges that make solvers behave erratically and unreproducibly.**
