---
name: geo-surface-processes-soils-and-hydrology
description: "Use when working at the Earth's surface or with water: weathering, erosion, sediment transport and landform evolution, soils and their formation and classification, surface hydrology including the water balance, runoff generation and flood frequency, and groundwater with aquifers, Darcy's law, well hydraulics and the consequences of over-abstraction."
---

# Geoscience: Surface Processes, Soils, Surface Hydrology, and Groundwater

> **Part 3 of 5** of the *Geoscience* reference (plugin `geoscience`), covering §7–§10. Sibling skills: `geo-earth-structure-tectonics-rocks-and-deep-time` (§0–§4), `geo-earthquakes-seismology-and-volcanism` (§5–§6), `geo-oceans-cryosphere-cycles-hazards-and-observation` (§11–§16), `geo-reference` (§17–§22). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Tectonics, stratigraphy, hydraulics and seismological theory are settled; satellite-measured continental water storage and deep learning in seismology recently changed the science. See §17 → `geo-reference` for both.

> **Scope.** Complements a weather-science reference (the atmosphere) and a
> Newtonian-mechanics reference (the physics). ⚠️ **This is the solid Earth, the water,
> and the land surface.**
>
> **⚠️ GOTCHA** boxes mark genuine misconceptions and places where intuition fails badly.
>
> **The three ideas that organize the field:**
> 1. **⚠️ Deep time is the hardest thing to internalize and the most important.** Processes
>    imperceptible on human timescales — millimetres per year — build mountains and open
>    oceans given tens of millions of years. **Almost every geological misconception is a
>    failure of timescale intuition** (§3 → `geo-earth-structure-tectonics-rocks-and-deep-time`).
> 2. **⚠️ The Earth runs on two engines.** Internal heat (radiogenic decay plus primordial)
>    drives tectonics, building topography; solar energy drives the water cycle and
>    weathering, tearing it down. **Everything at the surface is the interaction** (§1 → `geo-earth-structure-tectonics-rocks-and-deep-time`, §7).
> 3. **⚠️ Rates and residence times explain more than mechanisms do.** Water in a river
>    resides for days, in groundwater for millennia. **Whether something is renewable
>    depends entirely on the ratio of extraction rate to renewal rate** — and it's why
>    §10 is the most consequential section here (§10, §17.1 → `geo-reference`).

---

## §7. Surface Processes

**Weathering**: **physical** (frost wedging, thermal, exfoliation, biological) and
**chemical** (⚠️ **hydrolysis of silicates is the dominant one, plus dissolution,
oxidation, carbonation**). **⚠️ Chemical weathering of silicates consumes CO₂ and is the
long-term climate thermostat** (§13 → `geo-oceans-cryosphere-cycles-hazards-and-observation`).

**Erosion, transport, deposition** by water, wind, ice and gravity.
**⚠️ The Hjulström curve is the non-obvious result**: **fine clay requires *higher*
velocity to erode than sand**, because cohesion holds it together — **but once suspended
it stays suspended at very low velocity.** ⚠️ **Erosion threshold and deposition threshold
are different curves, and the gap is why fine sediment travels so far.**

**Landform systems**:
- **Fluvial** — ⚠️ **base level controls everything**; graded profile, meanders and point
  bars, floodplains, terraces, deltas, alluvial fans. **Drainage patterns encode the
  underlying geology.**
- **Glacial** — U-shaped valleys, cirques, moraines, drumlins, erratics, ⚠️ **and
  isostatic rebound continuing thousands of years after ice loss** (§12 → `geo-oceans-cryosphere-cycles-hazards-and-observation`).
- **Aeolian** — dunes, loess, desert pavement, ventifacts.
- **Coastal** — ⚠️ **longshore drift is the master process; interrupt it with a structure
  and you starve the beach downdrift.** Barrier islands migrate.
- **Karst** — ⚠️ **limestone dissolution: caves, sinkholes, springs, and disappearing
  streams. Aquifers in karst behave like plumbing, not porous media** (§10).
- **Mass wasting** — ⚠️ **the factor of safety is the ratio of resisting to driving
  forces, and water reduces it by adding weight AND raising pore pressure, which reduces
  effective stress.** **That's why landslides follow rain.**

---

## §8. Soils

**⚠️ Soil is not dirt — it's a structured, living, slowly-formed system.**
**Formation factors (Jenny)**: **CLORPT** — **cl**imate, **o**rganisms, **r**elief,
**p**arent material, **t**ime.
**Horizons**: **O** (organic), **A** (topsoil, humus), **E** (eluviated/leached),
**B** (subsoil, accumulation), **C** (weathered parent), **R** (bedrock).

**Texture** — sand/silt/clay proportions, ⚠️ **which control water retention and drainage
more than anything else.** **Structure**, **porosity**, **cation exchange capacity (CEC)**
— ⚠️ **the clay-and-organic-matter capacity to hold nutrients against leaching, and it's
the single best proxy for soil fertility.**

**⚠️ Soil forms at roughly 0.01–0.1 mm/year and is being lost far faster in many
agricultural systems.** **On any human timescale it is a non-renewable resource**, which
is §3 → `geo-earth-structure-tectonics-rocks-and-deep-time`'s timescale problem with immediate consequences.

---

## §9. Surface Hydrology

**The water balance**: `P = Q + ET + ΔS` — precipitation partitions into runoff,
evapotranspiration, and storage change.

**⚠️ Runoff generation, and the mechanism matters for prediction:**
- **Infiltration-excess (Hortonian)** — rainfall rate exceeds infiltration capacity.
  ⚠️ **Arid regions, and crucially urban and compacted surfaces.**
- **Saturation-excess (Dunne)** — soil saturates from below; ⚠️ **the dominant mechanism in
  humid vegetated catchments.**
- **⚠️ Variable source area**: the contributing area expands and contracts during a storm.
  **Runoff does not come uniformly from the whole catchment.**

**The hydrograph**: rising limb, peak, recession, **baseflow.**
⚠️ **Urbanization makes the hydrograph flashier — higher peak, shorter lag — by replacing
infiltration with impervious surface and drainage.** **This is the core mechanism of urban
flood risk.**

**⚠️ Floods and the return-period misconception:**
> **⚠️ GOTCHA — a "100-year flood" is a 1% annual exceedance probability, not an event
> that happens once a century.** ⚠️ **Two in consecutive years is unremarkable** —
> **P(at least one in 30 years) ≈ 26%.** **Worse, the estimate comes from a fitted
> distribution on a short record, so it carries large uncertainty, and
> ⚠️ non-stationarity — land use change and a changing climate — undermines the
> assumption that the past record represents the present distribution.**

**Flood types**: riverine, **flash** (⚠️ **the deadliest, and the reason is short warning
time**), urban, coastal/surge, and dam failure. **Levees raise protection locally and
⚠️ transfer risk downstream while encouraging development behind them — the "levee
effect."**

---

## §10. Groundwater

**⚠️ The most consequential section here, and the least visible resource.**

**Concepts**: **porosity** (⚠️ **how much water it holds**) vs **permeability/hydraulic
conductivity** (⚠️ **how easily water moves — and clay has high porosity and terrible
permeability, which is why the two are not interchangeable**). **Aquifer vs aquitard.**
**Unconfined** (water table) vs **confined** (⚠️ **under pressure — a well may flow
artesian**).

**Darcy's law**: `Q = −KA(dh/dl)` — ⚠️ **flow is proportional to hydraulic conductivity and
hydraulic gradient. The entire quantitative foundation of hydrogeology.**
**⚠️ Hydraulic head, not depth, drives flow** — groundwater can and does flow upward.

**Wells**: **cone of depression**, well interference, **safe yield.**
**⚠️ Subsidence from over-pumping is often permanent**: clay layers compact irreversibly,
so **the aquifer's storage capacity is destroyed, not merely emptied.** ⚠️ **This is the
under-appreciated part — you can refill an aquifer, but you cannot un-compact it.**

**⚠️ Residence times span the whole range**: days in a shallow alluvial aquifer to
**thousands to millions of years** in deep confined systems. **"Fossil water" in the
Nubian Sandstone and Ogallala is effectively non-renewable** — ⚠️ **extraction from it is
mining, not harvesting, and calling it a renewable resource is a category error.**

**Contamination**: point (⚠️ **plumes, and remediation is slow and expensive because you
can't see it**) and non-point (agricultural nitrate — the largest global problem);
**saltwater intrusion** in coastal aquifers; ⚠️ **natural arsenic and fluoride, which
affect tens of millions of people and have nothing to do with pollution.**
