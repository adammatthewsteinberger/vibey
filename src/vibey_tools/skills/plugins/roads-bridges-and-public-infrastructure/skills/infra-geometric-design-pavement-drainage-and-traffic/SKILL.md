---
name: infra-geometric-design-pavement-drainage-and-traffic
description: "Use for road engineering fundamentals: infrastructure as a system with its lifecycle and interdependencies, geometric design including sight distance, superelevation and design speed and how design speed shapes actual behaviour, pavement structure and the fourth-power load law, earthworks, geotechnics and drainage, and traffic engineering and capacity including level of service and flow relationships. Includes the router for the whole infrastructure reference."
---

# Roads, Bridges and Infrastructure: Infrastructure as a System, Geometric Design, Pavement, Earthworks, Geotechnics and Drainage, and Traffic Engineering and Capacity

> **Part 1 of 6** of the *Roads, Bridges and Public Infrastructure* reference (plugin `roads-bridges-and-public-infrastructure`), covering §0–§5. Sibling skills: `infra-intersections-road-safety-and-construction` (§6–§8), `infra-bridges-types-loads-failure-modes-and-inspection` (§9–§13), `infra-water-wastewater-transit-ports-and-utilities` (§14–§18), `infra-procurement-cost-asset-management-funding-and-equity` (§19–§26), `infra-reference` (§27–§32). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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

## §0. Routing

| You want... | Go to |
|---|---|
| Infrastructure as a system | §1 |
| **⚠️ Road geometry** | **§2** |
| **⚠️ Pavement** | **§3** |
| Earthworks and drainage | §4 |
| **⚠️ Traffic and capacity** | **§5** |
| Intersections | §6 → `infra-intersections-road-safety-and-construction` |
| **⚠️ Road safety** | **§7 → `infra-intersections-road-safety-and-construction`** |
| Construction and maintenance | §8 → `infra-intersections-road-safety-and-construction` |
| **⚠️ Bridge types** | **§9 → `infra-bridges-types-loads-failure-modes-and-inspection`** |
| Loads and rating | §10 → `infra-bridges-types-loads-failure-modes-and-inspection` |
| Materials and details | §11 → `infra-bridges-types-loads-failure-modes-and-inspection` |
| **⚠️ Bridge failure modes** | **§12 → `infra-bridges-types-loads-failure-modes-and-inspection`** |
| **⚠️ Inspection** | **§13 → `infra-bridges-types-loads-failure-modes-and-inspection`** |
| Water supply | §14 → `infra-water-wastewater-transit-ports-and-utilities` |
| Wastewater and stormwater | §15 → `infra-water-wastewater-transit-ports-and-utilities` |
| Transit | §16 → `infra-water-wastewater-transit-ports-and-utilities` |
| Ports, rail, airports | §17 → `infra-water-wastewater-transit-ports-and-utilities` |
| **⚠️ Utility coordination** | **§18 → `infra-water-wastewater-transit-ports-and-utilities`** |
| **⚠️ Procurement** | **§19 → `infra-procurement-cost-asset-management-funding-and-equity`** |
| **⚠️ Cost estimation** | **§20 → `infra-procurement-cost-asset-management-funding-and-equity`** |
| **⚠️ Asset management** | **§21 → `infra-procurement-cost-asset-management-funding-and-equity`** |
| **⚠️ Funding** | **§22 → `infra-procurement-cost-asset-management-funding-and-equity`** |
| Environmental review | §23 → `infra-procurement-cost-asset-management-funding-and-equity` |
| Resilience | §24 → `infra-procurement-cost-asset-management-funding-and-equity` |
| **⚠️ Induced demand** | **§25 → `infra-procurement-cost-asset-management-funding-and-equity`** |
| **⚠️ Distributional legacy** | **§26 → `infra-procurement-cost-asset-management-funding-and-equity`** |
| **What's live** | **§27 → `infra-reference`** |
| Misconceptions, numbers | §28–§29 → `infra-reference` |
| Sources, quick ref, method | §30–§32 → `infra-reference` |

---

## §1. Infrastructure as a System

```
⚠️ WHAT MAKES IT DIFFERENT FROM OTHER ENGINEERING
   ⚠️ ⚠️ DESIGN LIFE MEASURED IN DECADES TO CENTURIES — ⚠️ built
      by people who will not maintain it, for users not yet born
   ⚠️ ⚠️ PUBLIC FUNDING means POLITICAL selection, not market
      selection — ⚠️ so the analysis in §19-§22 is not
      peripheral to the engineering, it determines what gets
      engineered
   ⚠️ ⚠️ NETWORK EFFECTS — ⚠️ a road's value depends on what it
      connects to, so segments cannot be evaluated alone
   ⚠️ IRREVERSIBILITY  ⚠️ you cannot easily undo a highway
      alignment or a demolished neighbourhood (§26)
   ⚠️ ⚠️ THE FAILURE MODE IS SLOW  ⚠️ infrastructure rarely
      collapses; it DEGRADES, and degradation is politically
      invisible until it isn't (§21)
⚠️ THE DISCIPLINES INVOLVED  ⚠️ geotechnical · structural ·
   hydraulic · transportation · materials · construction
   management · and increasingly environmental and community
⚠️ ⚠️ THE ORGANIZING QUESTION FOR ANY PROJECT: ⚠️ what problem
   does this solve, for whom, and who pays to keep it working
   in forty years?
```

---

# PART I — ROADS

## §2. ⚠️ Geometric Design

```
⚠️ ⚠️ THE DESIGN SPEED IS THE MASTER VARIABLE. ⚠️ It sets curve
   radii, sight distances, superelevation, lane and shoulder
   widths — ⚠️ and then those geometrics INVITE that speed
   regardless of the posted limit (§7)
⚠️ SIGHT DISTANCE  ⚠️ stopping (perception-reaction plus
   braking) · decision · passing · intersection
   ⚠️ Perception-reaction is conventionally taken as 2.5 seconds
   for design, which is deliberately conservative
⚠️ HORIZONTAL ALIGNMENT  ⚠️ curve radius, SUPERELEVATION (banking)
   and side friction share the job of resisting centrifugal
   force · spiral transitions
⚠️ VERTICAL ALIGNMENT  grades, crest and sag curves (⚠️ crest
   curves are governed by SIGHT distance, sag curves by
   HEADLIGHT reach and comfort)
⚠️ CROSS SECTION  lane width, shoulders, cross slope for
   drainage, ⚠️ CLEAR ZONE (the recoverable area beside the road)
⚠️ ⚠️ THE DESIGN PARADOX WORTH NAMING  ⚠️ wider lanes, larger
   clear zones and gentler curves all make a given speed SAFER —
   ⚠️ AND induce higher speeds, which can produce a NET SAFETY
   LOSS in built-up areas. ⚠️ Forgiving design is right for
   motorways and frequently wrong for streets
⚠️ ⚠️ FUNCTIONAL CLASSIFICATION  ⚠️ freeway → arterial →
   collector → local, trading MOBILITY against ACCESS.
   ⚠️ THE STROAD is the failure case — a street/road hybrid
   attempting both and achieving neither
```

---

## §3. ⚠️ Pavement

```
⚠️ ⚠️ THE STRUCTURE IS A LOAD-SPREADING SYSTEM  ⚠️ surface →
   base → subbase → SUBGRADE. ⚠️ Each layer distributes wheel
   load over a wider area so the weak natural soil sees a
   tolerable pressure
   ⚠️ ⚠️ THEREFORE THE SUBGRADE AND THE DRAINAGE DECIDE THE
   PAVEMENT'S LIFE, not the surface course (§4)
⚠️ FLEXIBLE (asphalt)  ⚠️ bituminous binder plus graded
   aggregate. ⚠️ Distributes load through the layers; fails by
   RUTTING and FATIGUE CRACKING
⚠️ RIGID (concrete)  ⚠️ the slab is stiff enough to BRIDGE the
   subgrade. ⚠️ Longer life, higher initial cost; fails by
   cracking, faulting and joint deterioration
⚠️ ⚠️ THE FOURTH POWER LAW  ⚠️ pavement damage rises
   approximately with the FOURTH POWER of axle load.
   ⚠️ THEREFORE ONE HEAVY TRUCK CAUSES DAMAGE EQUIVALENT TO
   THOUSANDS OF CARS. ⚠️ This single relationship explains
   ESALs, weight enforcement, why heavy vehicles pay far more
   in road charges, and why cars are essentially irrelevant to
   pavement wear
⚠️ MIX DESIGN  Superpave, aggregate gradation, binder grade
   selected for climate · ⚠️ warm-mix asphalt cuts energy and
   emissions · ⚠️ RAP (reclaimed asphalt) — ⚠️ asphalt is among
   the most-recycled materials by mass anywhere
⚠️ DISTRESSES  potholes (⚠️ water plus freeze-thaw plus traffic),
   ⚠️ ALLIGATOR CRACKING (fatigue, meaning structural failure
   not surface failure), rutting, thermal cracking, ravelling
⚠️ TREATMENTS  ⚠️ preventive (seals, thin overlays — cheap, and
   only work on pavement still in good condition) vs
   rehabilitation vs reconstruction (§21)
```

---

## §4. Earthworks, Geotechnics and Drainage

**⚠️ Cut and fill balance** drives alignment economics — ⚠️ **hauling material is expensive,
so alignments are shaped to balance excavation against embankment.**
**⚠️ Compaction** to a specified density is the quality-control heart of earthwork,
⚠️ **because inadequate compaction produces settlement that shows up years later as a
failing pavement.**
**⚠️ Soil investigation**: ⚠️ **boreholes, SPT and CPT, laboratory classification — and the
recurring lesson from a buildings reference applies, that ground investigation is the
cheapest risk reduction available and the first thing cut from a budget.**
**⚠️ Slope stability, retaining structures and ground improvement** for difficult sites.
> **⚠️ GOTCHA — WATER IS THE PRIMARY ENEMY OF EVERY PAVEMENT AND EVERY EMBANKMENT.**
> ⚠️ **Water weakens subgrade, enables frost heave, drives pothole formation and undermines
> foundations.** **⚠️ Drainage is consistently the highest-return investment in road
> longevity and consistently the item value-engineered out first.**

**⚠️ The systems**: ⚠️ **surface drainage and cross slope, subsurface and edge drains,
culverts sized to a design storm, and ⚠️ CULVERT CAPACITY as a common failure point in
flood events** (§24 → `infra-procurement-cost-asset-management-funding-and-equity`).

---

## §5. ⚠️ Traffic Engineering and Capacity

```
⚠️ THE THREE VARIABLES  ⚠️ FLOW (vehicles per hour) = DENSITY
   (vehicles per mile) × SPEED. ⚠️ Everything follows from this
   identity
⚠️ ⚠️ THE FUNDAMENTAL DIAGRAM  ⚠️ flow rises with density up to
   a MAXIMUM, then FALLS as congestion sets in.
   ⚠️ THEREFORE MAXIMUM FLOW OCCURS BELOW FREE-FLOW SPEED, and
   ⚠️ A CONGESTED ROAD CARRIES FEWER VEHICLES PER HOUR THAN AN
   UNCONGESTED ONE. ⚠️ This is why ramp metering — deliberately
   restricting input — increases throughput, which sounds
   backwards and isn't
⚠️ LEVEL OF SERVICE  ⚠️ A to F. ⚠️ And note the critique: LOS
   measures VEHICLE DELAY, so a design that speeds cars while
   degrading walking and cycling scores well — ⚠️ which is why
   several jurisdictions have moved to vehicle-miles-travelled
   or multimodal metrics instead
⚠️ ⚠️ SHOCKWAVES AND PHANTOM JAMS  ⚠️ a single braking event
   propagates BACKWARD through dense traffic and can persist
   long after its cause is gone. ⚠️ Congestion is often a
   dynamic phenomenon, not a capacity shortfall
⚠️ FORECASTING  ⚠️ the four-step model (generation, distribution,
   mode choice, assignment) · activity-based models
   ⚠️ ⚠️ AND FORECASTS HAVE A DOCUMENTED ACCURACY PROBLEM —
   traffic on new roads is systematically mis-predicted, in both
   directions, which matters because forecasts justify the
   spending (§20, §25)
⚠️ SIGNALS  cycle, split, offset · ⚠️ COORDINATION and green
   waves · actuated and adaptive control
```
