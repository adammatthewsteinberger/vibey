---
name: infra-water-wastewater-transit-ports-and-utilities
description: "Use for the other infrastructure networks: water supply including treatment, distribution and the leakage and lead-service-line problems, wastewater and stormwater including combined sewer overflows, transit and its capacity and cost drivers, ports, rail and airports, and utility coordination and the buried-services problem that delays and endangers roadworks."
---

# Roads, Bridges and Infrastructure: Water Supply, Wastewater and Stormwater, Transit, Ports, Rail and Airports, and Utility Coordination

> **Part 4 of 6** of the *Roads, Bridges and Public Infrastructure* reference (plugin `roads-bridges-and-public-infrastructure`), covering §14–§18. Sibling skills: `infra-geometric-design-pavement-drainage-and-traffic` (§0–§5), `infra-intersections-road-safety-and-construction` (§6–§8), `infra-bridges-types-loads-failure-modes-and-inspection` (§9–§13), `infra-procurement-cost-asset-management-funding-and-equity` (§19–§26), `infra-reference` (§27–§32). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The engineering is mature and codified. Two things are live. See §27 → `infra-reference` for US surface transportation funding, and bridge vessel-collision risk.

> **⚠️ The engineering here is largely solved. The hard problems are institutional — how
> projects get chosen, financed, estimated, delivered and maintained over a century.**
>
> **Complements a buildings reference (vertical construction, codes, structural design), a
> resource-extraction reference (aggregate, steel, bitumen), and a thermodynamics/materials
> reference. The failure-analysis framing is shared with both.**
>
> **⚠️ GOTCHA** boxes mark where intuition about traffic, cost or safety is reliably wrong.
>
> **The three ideas that organize this document:**
> 1. **⚠️ THE ASSET IS THE LIABILITY** (§21 → `infra-procurement-cost-asset-management-funding-and-equity`). **Building infrastructure creates a permanent
>    maintenance obligation that nobody funds at ribbon-cutting. Every deferred-maintenance
>    crisis is this arithmetic arriving on schedule, and it is the central fact of the
>    field.**
> 2. **⚠️ TRAFFIC IS NOT A FIXED QUANTITY** (§25 → `infra-procurement-cost-asset-management-funding-and-equity`). **Demand responds to supply. Roads
>    designed as if traffic were a given volume to be accommodated produce results that
>    surprise their designers, and this has been documented for decades.**
> 3. **⚠️ SPEED IS THE VARIABLE THAT MATTERS MOST FOR SAFETY** (§7 → `infra-intersections-road-safety-and-construction`). **Kinetic energy scales
>    with the square of velocity, and human injury tolerance is a fixed biological
>    threshold. Everything in modern road safety follows from that single physical fact.**

---

## §14. Water Supply

**⚠️ The chain**: ⚠️ **source (surface or groundwater) → treatment (coagulation,
flocculation, sedimentation, filtration, disinfection) → transmission → storage →
distribution.**
**⚠️ Storage towers exist for pressure and peaking**, ⚠️ **not primarily for volume — elevation
provides head without continuous pumping.**
**⚠️ Distribution network design**: ⚠️ **looped rather than branched for redundancy, with
pressure zones and hydraulic modelling.**
> **⚠️ GOTCHA — LEAD SERVICE LINES are a legacy problem of a scale most people
> underestimate**, ⚠️ **with millions still in service; ⚠️ and Flint demonstrated that a
> CHEMISTRY change — switching source water without corrosion control — can mobilize lead
> from pipes that were previously stable.** **⚠️ The pipe is the hazard; the water chemistry
> determines whether it is expressed.**

**⚠️ Non-revenue water** (⚠️ **leakage plus unbilled use — commonly a substantial fraction of
production**) is the quiet efficiency problem.
**⚠️ PFAS** has become the significant new treatment obligation (see an organic-chemistry
reference).

---

## §15. Wastewater and Stormwater

**⚠️ Treatment stages**: ⚠️ **preliminary screening → primary settling → SECONDARY
biological treatment (activated sludge, trickling filters — where most of the work happens)
→ tertiary nutrient removal → disinfection → biosolids handling.**
**⚠️ COMBINED SEWERS** carry sewage and stormwater in one pipe — ⚠️ **so heavy rain causes
COMBINED SEWER OVERFLOWS discharging untreated sewage, and separating them in an old city is
enormously expensive.** ⚠️ **This is a nineteenth-century design decision still generating
consent decrees.**
**⚠️ Inflow and infiltration** — ⚠️ **groundwater and stormwater entering sanitary sewers
through defects — consumes treatment capacity that was sized for sewage.**
**⚠️ Stormwater management** has shifted from ⚠️ **conveyance (get it away fast) to
DETENTION and infiltration (slow it down, treat it) — because rapid conveyance simply moves
the flood downstream.** ⚠️ **Green infrastructure, permeable paving and bioswales are the
current toolkit.**
**⚠️ Design storms and return periods** — ⚠️ **and §24 → `infra-procurement-cost-asset-management-funding-and-equity`'s problem is that the rainfall
statistics these are based on are no longer stationary.**

---

## §16. Transit

**⚠️ The modes by capacity and cost**: ⚠️ **bus → BRT → light rail → metro → commuter rail,
and the honest observation is that the mode is frequently chosen for its symbolism rather
than for the corridor's demand.**
**⚠️ What actually determines ridership**: ⚠️ **FREQUENCY (⚠️ the single strongest lever —
service every 10 minutes is usable without a timetable, service every 40 is not), span of
service, reliability, network connectivity and land use — ⚠️ not vehicle comfort or
technology.**
**⚠️ The ridership-versus-coverage trade** is the fundamental transit planning decision, and
⚠️ **it is a value choice about whether the system maximizes trips or serves everyone
thinly.**
**⚠️ Right-of-way separation** is what makes transit fast and reliable — ⚠️ **a bus in mixed
traffic inherits every problem of the road.**
**⚠️ US transit capital costs per mile are markedly higher than international peers**,
⚠️ **and the research points to a combination of procurement fragmentation, consultant
reliance, station overbuild, low agency in-house capacity and litigation exposure rather
than to any single cause** (§19 → `infra-procurement-cost-asset-management-funding-and-equity`, §20 → `infra-procurement-cost-asset-management-funding-and-equity`).

---

## §17. Ports, Rail and Airports

**⚠️ Ports** — ⚠️ **container terminals, channel depth as the binding constraint on vessel
size, landside connection as the usual bottleneck** (see a maritime reference).
**⚠️ Freight rail** — ⚠️ **track structure, clearances, and the fact that rail's efficiency
advantage is enormous for bulk over distance and disappears for short-haul with transfers.**
**⚠️ Passenger rail** — ⚠️ **and the crucial distinction that high-speed rail requires
dedicated track; running fast trains on freight-shared infrastructure delivers neither.**
**⚠️ Airports** — ⚠️ **runway geometry and pavement designed for very different load
patterns, terminal flow, and airside/landside separation.**
**⚠️ The intermodal point**: ⚠️ **the transfer is where cost and time accumulate, which is
why containerization was transformative and why last-mile connections determine whether a
freight corridor works.**

---

## §18. ⚠️ Utility Coordination

**⚠️ The subsurface is crowded and poorly documented**: ⚠️ **water, sewer, gas, electric,
telecom, and abandoned everything.**
**⚠️ ONE-CALL / 811 systems** require locating before digging, ⚠️ **and utility strikes
remain common — with gas strikes potentially lethal and fibre strikes economically
severe.**
**⚠️ SUE (subsurface utility engineering)** grades information quality from records-only to
physically exposed, ⚠️ **and the recurring lesson is that paying for higher-quality utility
information up front is cheaper than discovering it during construction.**
**⚠️ The coordination failure everyone recognizes**: ⚠️ **a street resurfaced and then dug
up weeks later — which is an institutional problem of separate agencies with separate
budgets and no shared schedule, not an engineering one.**
**⚠️ Utility corridors and joint trenching** are the structural fix, and they require the
coordination that is missing in the first place.

---

# PART IV — THE SYSTEM
