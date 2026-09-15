---
name: logistics-routing-packing-scheduling-and-network-design
description: "Use when solving the classic combinatorial problems: shortest path and network flow, the travelling salesman problem, vehicle routing as the core problem of the field with its time windows, capacities and real-world side constraints, packing and loading, assignment and matching, scheduling, and facility location and network design."
---

# Logistics and Optimization Software: Shortest Path, TSP, Vehicle Routing, Packing, Assignment, Scheduling, and Facility Location

> **Part 3 of 5** of the *Logistics and Optimization Software* reference (plugin `logistics-software-optimization`), covering §10–§16. Sibling skills: `logistics-why-projects-fail-complexity-and-modeling` (§0–§5), `logistics-constraint-programming-metaheuristics-and-bounds` (§6–§9), `logistics-inventory-forecasting-operations-and-solvers` (§17–§24), `logistics-reference` (§25–§31). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
>    of optimal every night by well-engineered heuristics** (§2 → `logistics-why-projects-fail-complexity-and-modeling`, §8 → `logistics-constraint-programming-metaheuristics-and-bounds`).
> 3. **⚠️ A 2% better solution that operations won't execute is worth 0%.** **Stability,
>    explainability and consistency with yesterday's plan routinely matter more than the
>    objective value** (§1 → `logistics-why-projects-fail-complexity-and-modeling`, §26 → `logistics-reference`).

---

## §10. Shortest Path and Network Flow

**⚠️ The tractable core. These are in P, and they're the primitives everything else calls.**
```
Dijkstra          ⚠️ non-negative weights. O((V+E) log V) with a heap
Bellman-Ford      handles negative weights; detects negative cycles
A*                ⚠️ Dijkstra + admissible heuristic. Needs a heuristic that
                  never overestimates, or you lose optimality
⚠️ CONTRACTION HIERARCHIES / CH  the reason your map app answers instantly.
   Heavy preprocessing, microsecond queries on continental road networks
Floyd-Warshall    ⚠️ all-pairs, O(V³) — fine for small graphs, hopeless for road nets
MIN COST FLOW     ⚠️ hugely underused. Transportation, transshipment,
   assignment and many balancing problems are all min-cost-flow in disguise
MAX FLOW / MIN CUT   capacity analysis, bottleneck identification
```
**⚠️ Recognizing a network flow problem is a genuine superpower**: ⚠️ **if you can model it
as min-cost flow, it solves in polynomial time with integral solutions guaranteed —
no MIP needed, no gap, no time limit.** **Many people build a MIP for a problem that was
secretly a flow.**

---

## §11. TSP

**⚠️ Historically the most-studied combinatorial problem, and mostly a building block
rather than a real business problem on its own.**
**Exact**: **Held-Karp DP is O(n²2ⁿ) — fine to about 20 nodes; branch-and-cut (Concorde)
has solved instances with tens of thousands of cities to proven optimality.**
**Heuristics**: **nearest neighbour (⚠️ fast and typically 25% above optimal — use only as
a starting point), Christofides (⚠️ 1.5-approximation for metric TSP), 2-opt/3-opt, and
⚠️ Lin-Kernighan / LKH which routinely gets within a fraction of a percent.**
**⚠️ The practical note**: **for a single vehicle's stop sequence, LKH or even 2-opt with
Or-opt is more than adequate.** ⚠️ **The hard part of real routing is the assignment of
stops to vehicles, not the sequencing within one** (§12).

---

## §12. ⚠️ Vehicle Routing — The Core Problem

**⚠️ The variant alphabet, because the acronym tells you what you're dealing with:**
```
CVRP     capacitated
VRPTW    ⚠️ + time windows. THE most common real variant, and the tightest
         windows are where feasibility itself becomes hard
VRPPD    pickup and delivery (⚠️ + precedence and pairing constraints)
MDVRP    multi-depot
HFVRP    heterogeneous fleet
PVRP     periodic (multi-day patterns)
⚠️ SDVRP  split delivery — one customer served by multiple vehicles
DVRP     dynamic (§23)      SVRP  stochastic (§23)
⚠️ VRPB   backhauls
OVRP     open (vehicles don't return to depot — common with contractors)
```
**⚠️ The constraints that actually appear in real deployments, and which the textbook
formulations omit:**
```
⚠️ Driver hours, mandatory breaks, and legal duty limits (HOS/tachograph)
⚠️ Skills and certifications — who can service what
⚠️ Vehicle-site compatibility — height, weight, access restrictions
⚠️ Multiple capacity dimensions — weight AND volume AND pallet positions
⚠️ Loading sequence / LIFO — you can't unload what's behind something else (§13)
⚠️ Time-dependent travel times — rush hour is not a constant multiplier
⚠️ Customer preferences, standing appointments, "same driver" requirements
⚠️ Depot dock capacity and loading windows
⚠️ Multi-day / multi-trip — a vehicle returns and reloads
⚠️ Fairness across drivers — an equity objective nobody mentions until day one
```
> **⚠️ GOTCHA — driver hours-of-service rules are where naive VRP implementations break,
> and the failure is expensive rather than merely suboptimal.** ⚠️ **Break placement
> interacts with time windows non-trivially: a required break can push you past a window,
> and where you place the break changes which windows remain reachable.** **Bolting HOS on
> after the fact produces plans that are illegal to execute.** **Model it from the start.**

**⚠️ Practical architecture that works:**
```
1. ⚠️ CLUSTER FIRST, ROUTE SECOND for very large instances — geographic or
   capacity-based decomposition into tractable subproblems
2. ⚠️ Construct an initial solution (savings/Clarke-Wright, insertion)
3. ⚠️ ALNS to improve, with the time budget as the stopping rule (§8)
4. ⚠️ Post-process for the human requirements: stability vs yesterday,
   fairness, and any preference rules
5. ⚠️ Validate feasibility INDEPENDENTLY of the optimizer. A separate
   checker catches modeling bugs the optimizer will happily exploit
```
**⚠️ Step 5 is not optional.** **An optimizer will find and exploit every gap in your
constraint model, and it will look like a great solution until a driver tries to run it.**

---

## §13. Packing and Loading

```
1D BIN PACKING   ⚠️ First-Fit Decreasing is within 11/9 of optimal and takes
   ten lines. Excellent effort/quality ratio
2D / 3D PACKING  ⚠️ containers, pallets, parcels. Much harder
CUTTING STOCK    ⚠️ the classic column generation application (§4)
KNAPSACK         ⚠️ pseudo-polynomial DP; fine for realistic sizes
```
**⚠️ Real 3D loading constraints that make published algorithms inapplicable**: **load
bearing (⚠️ what can stack on what), orientation restrictions, stability (no floating
boxes), ⚠️ LIFO/unloading sequence tied to the route order (§12), axle weight
distribution, and hazmat separation.**
⚠️ **The route and the load are coupled** — **the best route may be unloadable** — **and
most systems handle this by iterating between a router and a loader rather than solving
them jointly.**

---

## §14. Assignment and Matching

**⚠️ Genuinely polynomial and often overlooked:**
**the Hungarian algorithm solves assignment in O(n³); bipartite matching; the
transportation problem; stable matching (Gale-Shapley); and generalized assignment
(⚠️ NP-hard, but a natural MIP).**
**⚠️ Where it shows up**: **order-to-picker, driver-to-route, dock-to-truck, load-to-carrier
tendering, and ⚠️ ride-hailing dispatch — where the modern approach is batched matching
over short windows rather than greedy first-come assignment**, because batching
substantially improves match quality.

---

## §15. Scheduling

**Job shop, flow shop, parallel machines, RCPSP, crew scheduling and rostering.**
⚠️ **Crew scheduling and rostering are the classic column-generation domain (§4 → `logistics-why-projects-fail-complexity-and-modeling`) — the
"columns" are legal duty pairings, of which there are astronomically many.**
**⚠️ CP-SAT is usually the right first tool for shop scheduling** (§6 → `logistics-constraint-programming-metaheuristics-and-bounds`).
**⚠️ Note the recurring structure**: **most scheduling problems are "assign + sequence +
time," and the tractable decomposition is often to fix the assignment, solve the sequence,
then repair.**

---

## §16. Facility Location and Network Design

```
p-median / p-center   ⚠️ minimize average vs minimize WORST distance —
   these give very different answers, and picking the wrong one is a
   real and common error
UFLP / CFLP           uncapacitated / capacitated facility location
HUB LOCATION          ⚠️ hub-and-spoke vs point-to-point
NETWORK DESIGN        ⚠️ the strategic layer: how many DCs, where, serving what
```
**⚠️ These are strategic (annual) rather than operational (daily), which changes
everything about how you should build them**: **run times of hours are fine; ⚠️ what
matters instead is SCENARIO ANALYSIS and robustness.** **The output people act on is
"how does this decision perform across demand scenarios," not a single optimal
configuration.** ⚠️ **Present a frontier, not an answer.**
