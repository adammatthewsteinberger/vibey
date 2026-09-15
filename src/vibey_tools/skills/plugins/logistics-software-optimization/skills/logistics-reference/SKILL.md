---
name: logistics-reference
description: "Use when checking what is live (the solver landscape, and quantum and AI optimization claims, verified August 2026), checking an optimization anti-pattern, correcting a misconception, looking up a problem size or runtime expectation, finding the canon, or needing a picker. Companion to the other logistics-software-optimization skills."
---

# Logistics and Optimization Software: What's Live, Anti-Patterns, Misconceptions, and Canon

> **Part 5 of 5** of the *Logistics and Optimization Software* reference (plugin `logistics-software-optimization`), covering §25–§31. Sibling skills: `logistics-why-projects-fail-complexity-and-modeling` (§0–§5), `logistics-constraint-programming-metaheuristics-and-bounds` (§6–§9), `logistics-routing-packing-scheduling-and-network-design` (§10–§16), `logistics-inventory-forecasting-operations-and-solvers` (§17–§24). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The algorithms and complexity results are permanent. Two areas are live. See §25 below for the solver landscape and the quantum and AI optimization claims.

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
>    objective value** (§1 → `logistics-why-projects-fail-complexity-and-modeling`, §26).

---

## §25. What's Live — verified August 2026

### 25.1 ⚠️ The solver landscape
**⚠️ The commercial/open-source gap narrowed, the benchmark situation got murkier, and
GPUs entered LP.**

- **⚠️ The gap is roughly one order of magnitude, not two.** **Analysis in 2025–26 puts
  HiGHS at about 20× slower than the top commercial solvers on Mittelmann benchmarks** —
  ⚠️ **and explicitly notes this is "not the 'two orders of magnitude' that sales
  engineers love to claim."** **The framing worth carrying: ⚠️ "20× slower than
  instantaneous" is still instantaneous for many real applications.**
- **⚠️ HiGHS has become the default open-source choice** — **commercial-grade enough for
  many workloads without licensing complexity** — **and SCIP remains strong (check its
  licence terms for your use case).**
- **⚠️ COPT (Cardinal Optimizer) is a genuine competitor to Gurobi and CPLEX**, **and
  benchmark reports have it leading on several problem categories.** **The commercial
  field is no longer a two-horse race.**

> **⚠️ GOTCHA — the benchmark landscape itself became less trustworthy, and you should
> know this before quoting anyone's numbers.** ⚠️ **Gurobi withdrew from Hans Mittelmann's
> widely-cited benchmarks in August 2024, followed by MindOpt in December.** **One
> commentator's read: when solvers start avoiding public benchmarks it usually means
> either the results aren't flattering or the methodology has been gamed.**
> ⚠️ **Note also that commercial solver licences frequently restrict published
> benchmarking** — **the GAMS MIPfeas benchmark works around this by grouping COPT, CPLEX
> and Xpress into synthetic "Virtual Best/Mean/Worst Commercial Solver" baselines rather
> than naming per-solver results.** **⚠️ Benchmark your OWN models on YOUR instances.
> Published rankings are weakly predictive of your workload.**

- **⚠️ GPU-based first-order LP methods are real and maturing.** **PDLP/cuPDLP variants
  have been incorporated into solvers from Gurobi, COPT, FICO Xpress, HiGHS, Google and
  NVIDIA.** ⚠️ **The honest positioning: on Mittelmann's LP set, commercial simplex and
  barrier methods remain fastest overall and most reliable — one 2026 comparison has COPT
  solving 50 instances against 46 for GPU methods, and roughly 1.8× faster in shifted
  geometric mean.** **But on specific very large structured instances the advantage
  inverts dramatically** — ⚠️ **COPT reported a classic instance solved in under 15
  minutes by cuPDLP-C versus 16 hours by CPU interior point.**
  **⚠️ The read: GPU LP is not a general replacement, and it is a genuine unlock for
  certain large problems including supply chain ones. Test, don't assume.**

### 25.2 ⚠️ Quantum and AI optimization claims
**⚠️ Two hype axes where practitioners need calibration, and they need it in opposite
directions.**

> **⚠️ GOTCHA — quantum optimization for logistics is not commercially real in 2026, and
> the literature saying otherwise has documented methodological problems.**
> ⚠️ **A 2025 systematic review of peer-reviewed quantum-and-quantum-inspired transport
> optimization studies found that although several demonstrate gains over classical
> heuristics, "most rely on synthetic datasets, lack statistical robustness, and omit
> critical operational metrics."** **That is the sentence to remember.**

**⚠️ What the honest technical work actually says:**
- **⚠️ Hardware can't hold real problems.** **NISQ hardware is described as "almost
  universally incompatible with full-scale optimization problems of practical
  importance."** **Circuit-model quantum algorithms can't be tested much beyond ~30 binary
  variables even on simulators; ⚠️ quantum annealers become cumbersome around a few
  hundred variables due to embedding challenges.** **A realistic VRP has orders of
  magnitude more.**
- **⚠️ Everything credible is HYBRID and decomposed.** **The most-cited serious study
  (QC Ware with Aisin, in *Scientific Reports*) handled a real-scale multi-truck routing
  problem only by iteratively generating one truck's subproblem at a time, each around
  2,500 binary variables** — **explicitly to avoid a full embedding that isn't possible.**
- **⚠️ The comparisons are frequently against weak baselines.** **A result like "85% of
  optimal at 95% faster runtime than a genetic algorithm" is measured against a GA** —
  ⚠️ **and a well-tuned classical LNS (§8 → `logistics-constraint-programming-metaheuristics-and-bounds`) is a much stronger baseline that these papers
  typically don't run.**
- **⚠️ Treat the big vendor and analyst numbers with real scepticism.** **Claims of
  "40–60% logistics cost reductions" circulate in industry-analyst material.** ⚠️ **They
  do not come from operational deployments, and the same sources acknowledge persistent
  bottlenecks in data loading, algorithm tuning and hybrid integration with existing ERP
  and WMS.**

**⚠️ On LLMs and optimization — a more nuanced picture, and the useful direction is not
the obvious one:**
⚠️ **LLMs do not solve combinatorial problems; solvers do.** **Where the research is
genuinely promising is LLMs as an INTERFACE to optimization** — **the OptiGuide-style
pattern, where natural-language what-if questions are translated into model
modifications, the solver is re-run, and results are explained back.**
⚠️ **That targets §1 → `logistics-why-projects-fail-complexity-and-modeling`'s real failure modes — constraint elicitation, explainability and
trust — rather than the solve time, which was rarely the bottleneck.** **There is also
active work on ML-guided branching and solution prediction to accelerate MIP within
solvers, with reported primal-gap improvements over solver defaults on specific
benchmarks.** ⚠️ **Both are worth watching; neither replaces knowing §5 → `logistics-why-projects-fail-complexity-and-modeling`.**

---

## §26. ⚠️ Anti-Patterns

```
⚠️ Building the optimizer before profiling the data (§1)
⚠️ No independent feasibility checker — the optimizer exploits every
   modeling gap and it looks fine until a driver tries it (§12)
⚠️ All-hard constraints, so the answer at 4am is "infeasible" (§5)
⚠️ No bound — you cannot say whether you're 2% or 40% off (§9)
⚠️ Re-optimizing from scratch nightly and destroying route stability (§1)
⚠️ Optimizing the objective operations doesn't actually care about (§1)
⚠️ Big-M set to 1e9 "to be safe" — weak relaxation, numerical garbage (§5)
⚠️ Straight-line distance in the production plan (§22)
⚠️ Flat service time for every stop (§21)
⚠️ Naive full n² distance matrix rebuild every night (§22)
⚠️ Bolting driver hours-of-service on after routing (§12)
⚠️ Routing and load planning solved independently with no iteration (§13)
⚠️ Building a MIP for something that was min-cost flow (§10)
⚠️ Reaching for a genetic algorithm because it's familiar, not because
   it's better — try LNS first (§7, §8)
⚠️ No degraded fallback mode when the optimizer fails (§1)
⚠️ Buying a commercial solver licence before proving solve time is the
   binding constraint (§24)
⚠️ Believing published solver benchmarks apply to your models (§25.1)
⚠️ Piloting quantum optimization instead of tuning your LNS (§25.2)
⚠️ Chasing forecast accuracy while ignoring forecast BIAS (§18)
⚠️ Treating the bullwhip effect as a forecasting problem (§17)
```

---

## §27. Misconceptions

| Misconception | Correction |
|---|---|
| NP-hard means practically unsolvable | ⚠️ **Real instances solve to within a few % routinely** (§2 → `logistics-why-projects-fail-complexity-and-modeling`) |
| The algorithm is the hard part | ⚠️ **Data, hidden constraints and trust are** (§1 → `logistics-why-projects-fail-complexity-and-modeling`) |
| A better objective value is a better plan | ⚠️ **Not if operations won't run it** (§1 → `logistics-why-projects-fail-complexity-and-modeling`) |
| Stop count drives difficulty | ⚠️ **Interacting constraints and tight windows do** (§2 → `logistics-why-projects-fail-complexity-and-modeling`) |
| The solver choice matters most | ⚠️ **The formulation matters more** (§5 → `logistics-why-projects-fail-complexity-and-modeling`) |
| Make constraints hard so they're respected | ⚠️ **Soft + penalties; "infeasible" helps nobody** (§5 → `logistics-why-projects-fail-complexity-and-modeling`) |
| Genetic algorithms are state of the art for routing | ⚠️ **LNS/ALNS generally beats them** (§7 → `logistics-constraint-programming-metaheuristics-and-bounds`, §8 → `logistics-constraint-programming-metaheuristics-and-bounds`) |
| A heuristic that returns a solution is working | ⚠️ **Without a bound you know nothing** (§9 → `logistics-constraint-programming-metaheuristics-and-bounds`) |
| TSP is the hard part of routing | ⚠️ **Assignment to vehicles is** (§11 → `logistics-routing-packing-scheduling-and-network-design`, §12 → `logistics-routing-packing-scheduling-and-network-design`) |
| Straight-line distance is close enough | ⚠️ **Error is worst exactly where geography binds** (§22 → `logistics-inventory-forecasting-operations-and-solvers`) |
| Geocoding gives you a location | ⚠️ **It gives a point and a quality flag; the flag matters** (§22 → `logistics-inventory-forecasting-operations-and-solvers`) |
| Service time is roughly constant | ⚠️ **It varies hugely by stop type and destroys plans** (§21 → `logistics-inventory-forecasting-operations-and-solvers`) |
| Re-optimize continuously for best results | ⚠️ **It destabilizes the plan; freeze a near horizon** (§23 → `logistics-inventory-forecasting-operations-and-solvers`) |
| Safety stock should target a service level | ⚠️ **Newsvendor: derive it from cost asymmetry** (§17 → `logistics-inventory-forecasting-operations-and-solvers`) |
| Reduce average lead time | ⚠️ **Reducing lead time VARIABILITY usually matters more** (§17 → `logistics-inventory-forecasting-operations-and-solvers`) |
| Bullwhip is a forecasting failure | ⚠️ **It's structural** (§17 → `logistics-inventory-forecasting-operations-and-solvers`) |
| Fancy ML beats simple forecasting | ⚠️ **Often not, especially on intermittent demand** (§18 → `logistics-inventory-forecasting-operations-and-solvers`) |
| Open-source solvers are 100× slower | ⚠️ **Roughly 20×, and often fast enough** (§25.1) |
| Published solver benchmarks predict my performance | ⚠️ **Weakly. Benchmark your own models** (§25.1) |
| Quantum will solve routing soon | ⚠️ **Annealers cumbersome at a few hundred variables** (§25.2) |
| LLMs can solve optimization problems | ⚠️ **They're an interface to solvers, not a solver** (§25.2) |

---

## §28. Numbers

```
⚠️ MIP gap to aim for in production      1–3% is usually plenty
⚠️ Nearest-neighbour TSP quality         ~25% above optimal — starting point only
⚠️ Christofides guarantee                1.5× optimal (metric TSP)
⚠️ First-Fit Decreasing (bin packing)    within 11/9 of optimal
Held-Karp exact TSP                      O(n²2ⁿ) — practical to ~20 nodes
⚠️ Distance matrix size                  n². 1,000 stops → 10⁶ entries
⚠️ Safety stock                          ≈ z · σ over lead time (scales √t)
⚠️ Risk pooling benefit                  safety stock scales ~√n
⚠️ Newsvendor optimal service level      Cu / (Cu + Co)
⚠️ Travel share of manual picking        commonly ~50% of picker time
⚠️ HiGHS vs top commercial (Mittelmann)  ~20× slower (§25.1)
⚠️ Quantum annealer practical limit      a few hundred variables (§25.2)
⚠️ Circuit-model QC testable limit       ~30 binary variables (§25.2)
⚠️ ALOHA-style channel efficiency         (see a radio reference §13 — the same
   "simple protocol collapses under load" lesson applies to dispatch systems)
```

---

## §29. Books

| Author | Work | Why |
|---|---|---|
| **Williams** | ***Model Building in Mathematical Programming*** | ⚠️ **THE book on §5 → `logistics-why-projects-fail-complexity-and-modeling`. Read it before any solver documentation** |
| **Wolsey** | *Integer Programming* | The rigorous §4 → `logistics-why-projects-fail-complexity-and-modeling` reference |
| **Toth & Vigo** | ***Vehicle Routing: Problems, Methods, Applications*** | ⚠️ **The VRP bible (§12 → `logistics-routing-packing-scheduling-and-network-design`)** |
| **Applegate et al.** | *The Traveling Salesman Problem* | §11 → `logistics-routing-packing-scheduling-and-network-design`, exhaustive |
| **Pisinger & Ropke** | *"Large Neighborhood Search"* (chapter) | ⚠️ **§8 → `logistics-constraint-programming-metaheuristics-and-bounds`. The technique that actually wins** |
| **Ahuja, Magnanti & Orlin** | *Network Flows* | ⚠️ **§10 → `logistics-routing-packing-scheduling-and-network-design`. Recognize flow problems and save yourself** |
| **Silver, Pyke & Thomas** | *Inventory and Production Management* | §17 → `logistics-inventory-forecasting-operations-and-solvers` |
| **Hyndman & Athanasopoulos** | ***Forecasting: Principles and Practice*** | ⚠️ **§18 → `logistics-inventory-forecasting-operations-and-solvers`. Free online, excellent** |
| **Bartholdi & Hackman** | ***Warehouse & Distribution Science*** | ⚠️ **§20 → `logistics-inventory-forecasting-operations-and-solvers`. Free PDF, genuinely good** |
| **Chopra & Meindl** | *Supply Chain Management* | The business-level frame |

**⚠️ Also**: **the OR-Tools documentation and examples are unusually good and are the
fastest practical on-ramp**; **CVRPLIB and Solomon instances for benchmarking (§9 → `logistics-constraint-programming-metaheuristics-and-bounds`)**;
**and ⚠️ the *Operations Research* / *Transportation Science* / *EJOR* literature, where
the honest comparative studies live — as distinct from the vendor material.**

---

## §30. Quick Reference

### 30.1 Picker
| Question | Answer |
|---|---|
| Where do I start on a new project? | ⚠️ **Profile the data. Not the model** (§1 → `logistics-why-projects-fail-complexity-and-modeling`) |
| Is my heuristic any good? | ⚠️ **Get a bound. Any bound** (§9 → `logistics-constraint-programming-metaheuristics-and-bounds`) |
| Solver says infeasible at 4am | ⚠️ **Soften constraints with penalties** (§5 → `logistics-why-projects-fail-complexity-and-modeling`) |
| Routing engine architecture? | ⚠️ **Cluster → construct → ALNS → post-process → validate** (§12 → `logistics-routing-packing-scheduling-and-network-design`) |
| Which metaheuristic? | ⚠️ **LNS/ALNS first** (§8 → `logistics-constraint-programming-metaheuristics-and-bounds`) |
| Is this actually a hard problem? | ⚠️ **Check whether it's min-cost flow** (§10 → `logistics-routing-packing-scheduling-and-network-design`) |
| Scheduling with resources and precedence? | ⚠️ **CP-SAT** (§6 → `logistics-constraint-programming-metaheuristics-and-bounds`, §15 → `logistics-routing-packing-scheduling-and-network-design`) |
| Distance matrix too slow/expensive? | ⚠️ **Self-host OSRM; k-nearest only** (§22 → `logistics-inventory-forecasting-operations-and-solvers`) |
| Plans keep running late | ⚠️ **Measure real service times; add buffer** (§21 → `logistics-inventory-forecasting-operations-and-solvers`, §23 → `logistics-inventory-forecasting-operations-and-solvers`) |
| Drivers reject the plan | ⚠️ **Stability penalty + an explainer** (§1 → `logistics-why-projects-fail-complexity-and-modeling`) |
| How much safety stock? | ⚠️ **Newsvendor on cost asymmetry, not a target SL** (§17 → `logistics-inventory-forecasting-operations-and-solvers`) |
| Which solver? | ⚠️ **OR-Tools + HiGHS until proven otherwise** (§24 → `logistics-inventory-forecasting-operations-and-solvers`) |
| Should we try quantum? | ⚠️ **No. Tune your LNS** (§25.2) |
| Can an LLM do this? | ⚠️ **As an interface and explainer, yes. As a solver, no** (§25.2) |

### 30.2 Before going live
- [ ] ⚠️ **Data profiled: address quality, service times, capacities, skills** (§22 → `logistics-inventory-forecasting-operations-and-solvers`)
- [ ] ⚠️ **Independent feasibility checker, separate from the optimizer** (§12 → `logistics-routing-packing-scheduling-and-network-design`)
- [ ] ⚠️ **A bound, so you can state solution quality** (§9 → `logistics-constraint-programming-metaheuristics-and-bounds`)
- [ ] Hard constraints limited to genuine impossibilities (§5 → `logistics-why-projects-fail-complexity-and-modeling`)
- [ ] ⚠️ **Stability penalty against the incumbent plan** (§1 → `logistics-why-projects-fail-complexity-and-modeling`)
- [ ] ⚠️ **Degraded fallback that always returns something** (§1 → `logistics-why-projects-fail-complexity-and-modeling`)
- [ ] Plan explainer: "why is this stop on this route?" (§1 → `logistics-why-projects-fail-complexity-and-modeling`)
- [ ] ⚠️ **Driver hours / breaks modeled, not bolted on** (§12 → `logistics-routing-packing-scheduling-and-network-design`)
- [ ] Runtime fits the operational window with margin (§1 → `logistics-why-projects-fail-complexity-and-modeling`)
- [ ] ⚠️ **Shadow-mode comparison against current human plans** (§1 → `logistics-why-projects-fail-complexity-and-modeling`)
- [ ] Penalty weights exposed as a business-facing interface (§5 → `logistics-why-projects-fail-complexity-and-modeling`)
- [ ] ⚠️ **Benchmarked on YOUR instances, not published rankings** (§25.1)

---

## §31. Method

**§1–§24 → `logistics-why-projects-fail-complexity-and-modeling`, `logistics-constraint-programming-metaheuristics-and-bounds`, `logistics-routing-packing-scheduling-and-network-design`, `logistics-inventory-forecasting-operations-and-solvers` and §26–§30 rest on stable material** — **complexity theory, LP/MIP/CP,
metaheuristics, the classical OR problem family, inventory theory and warehouse
science** — sourced from §29. ⚠️ **None of it needed verification; Dijkstra, Held-Karp,
the newsvendor result and branch-and-bound are not going to change.**

**Two searches were run in August 2026**, on **the solver landscape** and **quantum/AI
optimization claims** — ⚠️ **one because the buy-vs-open-source decision genuinely
shifted, and one because it's where practitioners are currently being mis-sold.**

**Confidence.** **High** in §1 → `logistics-why-projects-fail-complexity-and-modeling`, which is the section I'd most want read and the one that
is least present in textbooks. ⚠️ **The claim that these projects fail on data, hidden
constraints and trust rather than on algorithms is a position, and I've presented it as
an ordered judgement rather than a measured finding** — **but the stability requirement,
the need for a feasibility checker independent of the optimizer, and the soft-constraints
recommendation in §5 → `logistics-why-projects-fail-complexity-and-modeling` are the three things I'd defend hardest.**

**High** in §2 → `logistics-why-projects-fail-complexity-and-modeling`'s framing. ⚠️ **"NP-hard ≠ unsolvable" is the correction that most changes
how a software engineer approaches this domain**, **and the practical difficulty drivers
(interacting constraints, tight time windows) matter far more than instance size.**

**Moderate-to-high** in §25.1's specifics. ⚠️ **The ~20× HiGHS-vs-commercial figure and
the "one order of magnitude, not two" framing come from 2025–26 analysis referencing
Mittelmann benchmarks, and I've attributed rather than asserted them.** **The Gurobi
(August 2024) and MindOpt (December 2024) benchmark withdrawals are reported, and the
interpretation offered — that withdrawal signals unflattering results or gamed methodology
— is one commentator's read, which I've labelled as such.** ⚠️ **The structural point is
more reliable than any number: commercial licences often restrict published benchmarking,
which is why GAMS uses anonymized "virtual commercial solver" baselines — so treat all
public rankings as weakly predictive and benchmark your own models.**

**High** in §25.2's sceptical read, and this is the section I'd stand behind most firmly
against the surrounding marketing. ⚠️ **The decisive evidence is a peer-reviewed
systematic review finding that most quantum transport-optimization studies "rely on
synthetic datasets, lack statistical robustness, and omit critical operational
metrics."** **The hardware limits — ~30 binary variables for circuit-model testing, a few
hundred for annealer embedding — come from the technical literature including the QC Ware
paper, which is notably candid about them.** ⚠️ **I've deliberately contrasted that honest
work against the analyst claims of 40–60% cost reductions, and flagged that the latter
don't come from operational deployments.**

⚠️ **Sourcing caution**: **solver vendors publish benchmarks showing they win; quantum
vendors and analysts publish projections showing transformation.** **Where I could anchor
on peer-reviewed work, a systematic review, or a neutral party (the GAMS benchmark
methodology, arXiv comparisons), I did.** ⚠️ **The LLM-as-interface point in §25.2 is my
own synthesis — that the promising direction targets §1 → `logistics-why-projects-fail-complexity-and-modeling`'s failure modes rather than solve
time — and I'd flag it as an argument rather than a finding.**
