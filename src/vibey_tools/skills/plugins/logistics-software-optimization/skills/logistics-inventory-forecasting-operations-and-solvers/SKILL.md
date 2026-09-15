---
name: logistics-inventory-forecasting-operations-and-solvers
description: "Use when the surrounding system matters as much as the algorithm: inventory policy and safety stock, forecasting and its error measures, the vendor and product landscape, warehouse operations including slotting and picking, last-mile delivery, the data layer that decides most project outcomes, dynamic and stochastic problems including re-optimization, and the solver and tooling options."
---

# Logistics and Optimization Software: Inventory, Forecasting, Warehouse and Last-Mile Operations, Data, Stochastic Problems, and Solvers

> **Part 4 of 5** of the *Logistics and Optimization Software* reference (plugin `logistics-software-optimization`), covering §17–§24. Sibling skills: `logistics-why-projects-fail-complexity-and-modeling` (§0–§5), `logistics-constraint-programming-metaheuristics-and-bounds` (§6–§9), `logistics-routing-packing-scheduling-and-network-design` (§10–§16), `logistics-reference` (§25–§31). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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

## §17. Inventory

```
EOQ            ⚠️ the classic square-root formula. Assumptions rarely hold,
   and it's still a useful order-of-magnitude sanity check
⚠️ NEWSVENDOR  single period, stochastic demand. Optimal service level =
   Cu / (Cu + Co) — underage cost over total. ⚠️ THE key insight: your
   service level should follow from the COST ASYMMETRY, not from a target
   somebody picked
(s,S) / (R,Q)  reorder point policies
SAFETY STOCK   ⚠️ ≈ z · σ_demand-over-lead-time. Note it scales with the
   square root of lead time — ⚠️ so REDUCING LEAD TIME VARIABILITY beats
   reducing average lead time, usually by a lot
MULTI-ECHELON  ⚠️ where to hold stock across a network. Risk pooling:
   consolidated inventory needs less safety stock for the same service
   level, scaling with √n
ABC / XYZ      segmentation by value and by variability
```
> **⚠️ GOTCHA — the bullwhip effect is a structural property, not a forecasting failure.**
> ⚠️ **Demand variability amplifies up the supply chain because of order batching, lead
> time, price promotions and rationing behaviour** — **it arises from the STRUCTURE even
> with rational actors.** **You mitigate it with information sharing and shorter lead
> times, not with better local forecasts.**

---

## §18. Forecasting

**⚠️ Keep expectations calibrated: for intermittent, lumpy SKU-level demand, sophisticated
methods frequently fail to beat simple ones.**
**Methods**: **moving average, exponential smoothing / Holt-Winters, ARIMA, Croston's
method (⚠️ specifically for intermittent demand), gradient boosting on engineered
features, and hierarchical reconciliation (⚠️ forecast at multiple levels and reconcile so
they sum consistently).**
**⚠️ The M-competitions are the honest benchmark literature here**, **and the recurring
finding is that simple methods and combinations are extremely hard to beat**, ⚠️ **with ML
methods winning mainly where there is cross-series structure to exploit.**
**⚠️ Forecast accuracy metrics**: **MAPE (⚠️ breaks on zeros and is asymmetric — a real
problem for intermittent demand), MASE (⚠️ better), RMSE, bias.** ⚠️ **Track BIAS
separately from accuracy — a consistently biased forecast is a systematically
mis-stocked warehouse, and it's invisible in symmetric error metrics.**

---

# PART III — SYSTEMS

---

## §19. The Landscape

```
ERP    the system of record — orders, inventory, finance
OMS    order management, allocation, sourcing decisions
⚠️ WMS warehouse management — receiving, putaway, picking, packing, shipping
⚠️ TMS transportation management — planning, tendering, execution, freight audit
YMS    yard management — trailers, docks, gates
WES/WCS  execution/control — the real-time layer talking to conveyors,
       sorters and robots
LMD    last-mile delivery platforms, driver apps, customer tracking
```
**⚠️ The integration reality**: **these are usually different vendors with different data
models, and the join keys don't line up.** ⚠️ **EDI (X12/EDIFACT) remains pervasive in
freight** — **214 shipment status, 204 load tender, 990 response, 210 invoice** — **and
API-first carriers coexist with partners who will only do EDI over an SFTP drop.**
**⚠️ Budget for the integration layer as a first-class component**; **in most logistics
projects it is larger than the optimization component.**

---

## §20. Warehouse Operations

**⚠️ Travel time dominates manual picking** — **commonly cited as roughly half of picker
time** — **so most warehouse optimization is really travel reduction.**
```
SLOTTING       ⚠️ put fast movers near dispatch; account for ergonomics
               (golden zone) and for affinity (items ordered together)
PICK PATH      ⚠️ TSP on the warehouse graph. S-shape and return heuristics
               are common and near-optimal for simple layouts
BATCHING       ⚠️ pick multiple orders per trip — usually the single biggest
               travel win available
ZONING         pick-and-pass vs pick-and-sort
WAVE vs WAVELESS  ⚠️ batched release vs continuous flow
GOODS-TO-PERSON   ⚠️ AS/RS, shuttles, AMRs — inverts the problem: now you
               optimize robot fleet movement and storage assignment instead
```
**⚠️ Labour standards and ergonomics are constraints, not preferences** — **and an
optimizer that maximizes picks per hour without them produces injury rates and turnover
that cost more than the throughput gained.**

---

## §21. Last Mile

**⚠️ The most expensive segment — commonly cited as a large share of total delivery cost —
and the most constrained.**
**Key issues**: **failed first delivery attempts** (⚠️ **each retry is close to a full
additional delivery cost, which is why access codes, safe-place instructions and
notification quality have outsized ROI**), **time window promises vs cost** (⚠️ **narrow
windows are extremely expensive; letting customers self-select from optimizer-suggested
windows is far cheaper than accepting arbitrary ones**), **parking and access reality that
no routing model captures, gig vs employed fleets, lockers and pickup points, and returns
as a first-class flow rather than an exception.**
**⚠️ Service time is where routing plans die.** ⚠️ **Modeling every stop at a flat 3
minutes when apartment buildings take 12 produces a plan that is an hour behind by
midday.** **Measure actual service times per stop type and per location, and feed the
distribution back** (§22).

---

## §22. ⚠️ Data

**⚠️ Where the projects actually live or die.**
```
⚠️ ADDRESSES     unstructured, misspelled, ambiguous, missing units.
   ⚠️ Geocoding returns a point that may be a street centroid, a rooftop,
   or the middle of a postcode — and the QUALITY FLAG matters more than
   the coordinate. Rooftop vs interpolated is the difference between
   arriving and circling
⚠️ ROAD NETWORKS OSM, HERE, TomTom. Turn restrictions, one-ways, height
   and weight limits, seasonal closures
⚠️ DISTANCE MATRIX  n² entries. ⚠️ THE dominant cost and latency issue at scale
TRAVEL TIME     ⚠️ time-dependent, and asymmetric — A→B ≠ B→A
⚠️ SERVICE TIME  measure it; don't assume it (§21)
MASTER DATA     ⚠️ vehicle capacities, driver skills, customer constraints.
   Usually stale, and nobody owns it
```
> **⚠️ GOTCHA — the distance matrix is the hidden scaling wall.** ⚠️ **1,000 stops = a
> million matrix entries; 10,000 stops = 100 million.** **Commercial matrix APIs charge
> per element and rate-limit, so a naive nightly full-matrix rebuild is both slow and
> expensive.**
> **⚠️ The mitigations**: **self-host a routing engine (OSRM, Valhalla, GraphHopper) —
> which turns a per-element cost into a fixed server cost**; **compute only the k-nearest
> neighbours per stop, since a good solution never uses most of the matrix**;
> **cache aggressively — road networks change slowly**; **and ⚠️ use haversine distance
> for early filtering and clustering, never for the final plan.**

**⚠️ And a warning about the cheap shortcut**: **straight-line distance times a fudge
factor is fine for clustering and wrong for planning.** ⚠️ **The error is not uniform —
it's worst exactly where geography constrains routing (rivers, motorways, one-way
systems), which is precisely where your plan will fail.**

---

## §23. Dynamic and Stochastic

**⚠️ Real logistics is not a static problem solved once.**
```
DYNAMIC       ⚠️ orders arrive during execution; vehicles are en route
STOCHASTIC    ⚠️ travel times, service times and demand are random variables
ONLINE        ⚠️ decide without knowing the future. Competitive ratio analysis
ROLLING HORIZON  ⚠️ re-optimize periodically over a moving window. THE
   standard practical approach
```
**Techniques**: **rolling-horizon re-optimization; scenario-based stochastic programming;
sample average approximation; robust optimization (⚠️ optimize the worst case — often too
conservative for logistics); chance constraints; and reinforcement learning
(⚠️ genuinely promising for dispatch-style sequential decisions, and much harder to
validate and deploy than the literature implies).**
**⚠️ The practical patterns that matter more than the theory:**
- ⚠️ **Buffer time in the plan.** **A plan with zero slack fails on the first delay and
  cascades.**
- ⚠️ **Re-optimize on a schedule AND on trigger events**, **not continuously — continuous
  re-optimization destabilizes the plan** (§1 → `logistics-why-projects-fail-complexity-and-modeling`).
- ⚠️ **Freeze a near horizon.** **Don't change what a driver is doing in the next 30
  minutes.** **This is both operationally necessary and a large search-space reduction.**
- **Anticipate rather than react where you can** — **positioning idle capacity toward
  expected demand.**

---

## §24. Solvers and Tooling

```
COMMERCIAL MIP   ⚠️ Gurobi · IBM CPLEX · FICO Xpress · COPT (§25.1)
OPEN SOURCE MIP  ⚠️ HiGHS (the current default) · SCIP (excellent, check
                 licence terms) · CBC (older, slower)
CP               ⚠️ OR-Tools CP-SAT (outstanding, free) · IBM CP Optimizer
ROUTING          ⚠️ OR-Tools routing library · VROOM (open source, fast) ·
                 jsprit · commercial routing engines
MODELING LAYERS  ⚠️ Pyomo · PuLP · JuMP (Julia) · AMPL/GAMS · linopy
ROAD ROUTING     ⚠️ OSRM · Valhalla · GraphHopper (self-host; §22)
FIRST-ORDER/GPU  ⚠️ PDLP and cuPDLP — GPU LP for very large instances (§25.1)
```
**⚠️ Sensible defaults for a team starting out**: **OR-Tools for routing and scheduling
(free, well-documented, genuinely good); HiGHS for LP/MIP; a self-hosted OSRM for
distances; Pyomo or JuMP if you want solver portability.** ⚠️ **Buy a commercial MIP
licence when you have demonstrated that solve time is your binding constraint — and not
before, because §1 → `logistics-why-projects-fail-complexity-and-modeling` says it usually isn't.**
