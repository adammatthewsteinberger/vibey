---
name: mining-petroleum-geology-drilling-well-control-and-fracturing
description: "Use for the upstream oil and gas side: petroleum geology with source, reservoir, seal and trap, seismic exploration and what the data can and cannot resolve, drilling including mud systems and casing design, well control and the blowout mechanism that makes it the defining safety problem, and completion and hydraulic fracturing."
---

# Resource Extraction: Petroleum Geology, Seismic Exploration, Drilling, Well Control, and Completion and Hydraulic Fracturing

> **Part 4 of 6** of the *Resource Extraction: Mining, Oil and Gas* reference (plugin `resource-extraction-mining-and-oil`), covering §14–§18. Sibling skills: `mining-grade-deposits-exploration-and-reserves` (§0–§4), `mining-surface-underground-drilling-blasting-and-comminution` (§5–§8), `mining-processing-metallurgy-gold-tailings-and-water` (§9–§13), `mining-production-offshore-refining-coal-economics-and-safety` (§19–§26), `mining-reference` (§27–§32). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The engineering is mature. Two areas are moving fast. See §27 → `mining-reference` for critical mineral supply and export controls, and deep-sea mining's legal collision.

> **⚠️ The industry that everything else in this reference series depends on.** ⚠️ **Every
> other file assumes steel, copper, silicon, polymers and energy already exist. This one is
> about where they come from, and the answer is always: a specific place, at a specific
> grade, under specific rock, at a cost that either works or doesn't.**
>
> **Complements a manufacturing reference (what the metals become), an
> organic-chemistry/plastics reference (petroleum as feedstock), a civil engineering
> reference (earthworks and geotech), a thermodynamics reference (separation energy), and a
> maritime reference (offshore and bulk transport).**
>
> **⚠️ GOTCHA** boxes mark where public intuition and industrial reality diverge.
>
> **⚠️ Scope note: this covers principles and industrial practice. Mining, drilling and
> blasting are among the most hazardous industrial activities that exist, are heavily
> licensed everywhere, and nothing here is operational guidance.**
>
> **The three ideas that organize this document:**
> 1. **⚠️ GRADE AND TONNAGE DECIDE EVERYTHING** (§1 → `mining-grade-deposits-exploration-and-reserves`, §23 → `mining-production-offshore-refining-coal-economics-and-safety`). **A deposit is not "ore" because
>    of what's in it — it's ore only if it can be extracted profitably, so the price
>    changes the size of the deposit.**
> 2. **⚠️ MOST OF THE ENERGY GOES INTO BREAKING ROCK** (§8 → `mining-surface-underground-drilling-blasting-and-comminution`). **Comminution is a startling
>    share of global electricity use, and it is thermodynamically appalling — most of the
>    energy becomes heat and noise.**
> 3. **⚠️ THE LIABILITY OUTLASTS THE MINE** (§12 → `mining-processing-metallurgy-gold-tailings-and-water`, §13 → `mining-processing-metallurgy-gold-tailings-and-water`, §25 → `mining-production-offshore-refining-coal-economics-and-safety`). **Tailings dams and acid
>    drainage require management for centuries after the ore runs out, and the entity that
>    profited is frequently gone.**

---

## §14. Petroleum Geology

```
⚠️ THE PETROLEUM SYSTEM — ⚠️ ALL of these must coincide, which is
   why oil is rare despite organic matter being common
   ⚠️ SOURCE ROCK  organic-rich, buried into the OIL WINDOW
      (⚠️ a temperature range — too cool and it stays kerogen,
      too hot and it cracks to gas then graphite)
   ⚠️ MIGRATION  buoyant hydrocarbons move upward
   ⚠️ RESERVOIR  porous and PERMEABLE rock. ⚠️ POROSITY is storage;
      PERMEABILITY is flow — ⚠️ and permeability is the one that
      decides whether a well produces
   ⚠️ SEAL / CAP ROCK  impermeable barrier
   ⚠️ TRAP  ⚠️ structural (anticline, fault) or stratigraphic
   ⚠️ TIMING  the trap must exist BEFORE migration
⚠️ CONVENTIONAL vs UNCONVENTIONAL  ⚠️ unconventional means the
   hydrocarbon is still in low-permeability rock — shale, tight
   sands, coalbed methane. ⚠️ Source and reservoir are the same
   rock, which is why it needs stimulation (§18)
⚠️ FLUID PROPERTIES  API gravity · sour vs sweet (⚠️ H₂S content —
   lethal and corrosive) · GOR
```

---

## §15. Seismic Exploration

**⚠️ Acoustic imaging of the subsurface** — ⚠️ **a source generates waves, reflections from
layer boundaries return to receivers, and travel times are processed into an image.**
**⚠️ Sources**: **vibroseis trucks on land; ⚠️ airgun arrays offshore, which are a
significant marine noise concern.**
**⚠️ Processing** is the hard part: ⚠️ **stacking, migration, depth conversion — and
seismic gives you STRUCTURE reliably and FLUID CONTENT only inferentially.**
**⚠️ "Bright spots" and AVO analysis** can indicate gas, ⚠️ **and they produce false
positives, which is why nothing is proven until a well is drilled.**
**⚠️ 4D (time-lapse) seismic** monitors how a producing reservoir changes.
**⚠️ Well logging** provides the ground truth: ⚠️ **gamma ray, resistivity, porosity,
sonic, and image logs — plus core, which is expensive and definitive.**

---

## §16. Drilling

```
⚠️ THE RIG  rotary drilling; ⚠️ the DRILL BIT (roller cone or PDC)
   turned either by the rotary table/top drive or by a downhole
   MUD MOTOR
⚠️ ⚠️ DRILLING MUD does four jobs at once and they conflict
   ⚠️ 1. HYDROSTATIC PRESSURE to hold back formation fluids —
        ⚠️ THE primary well control barrier (§17)
   ⚠️ 2. Carry cuttings to surface
   ⚠️ 3. Cool and lubricate the bit
   ⚠️ 4. Stabilize the borehole wall
   ⚠️ MUD WEIGHT must sit between PORE PRESSURE (below which the
   well flows) and FRACTURE GRADIENT (above which you break the
   formation and lose circulation). ⚠️ That window narrows with
   depth and can close entirely
⚠️ CASING and CEMENT  ⚠️ progressively smaller strings cemented in
   place. ⚠️ CEMENT INTEGRITY is the barrier that isolates zones —
   and cement failure is implicated in major blowouts (§17)
⚠️ DIRECTIONAL and HORIZONTAL DRILLING  ⚠️ measurement-while-drilling
   and rotary steerable systems made long horizontal laterals
   routine — ⚠️ and horizontal drilling plus fracturing is what
   unlocked shale (§18)
⚠️ THE HAZARDS  stuck pipe · lost circulation · ⚠️ KICKS (§17) ·
   H₂S · wellbore instability
```

---

## §17. ⚠️ Well Control

> **⚠️ The single most consequential safety system in the industry, and the failures are
> catastrophic and well documented.**
```
⚠️ THE PHYSICS  ⚠️ a KICK is an unwanted influx of formation fluid,
   occurring when formation pressure exceeds mud hydrostatic
   pressure. ⚠️ Uncontrolled, a kick becomes a BLOWOUT
⚠️ WHY GAS KICKS ARE PARTICULARLY DANGEROUS  ⚠️ gas EXPANDS as it
   rises and pressure falls, displacing more mud, further reducing
   hydrostatic pressure — ⚠️ an accelerating feedback
⚠️ BARRIERS  ⚠️ the principle is TWO INDEPENDENT TESTED BARRIERS
   at all times. ⚠️ Mud is the primary; casing, cement and the
   BLOWOUT PREVENTER stack are secondary
⚠️ WARNING SIGNS  ⚠️ drilling break · flow with pumps off · pit
   gain · increased return flow. ⚠️ Crews are trained to shut in
   FIRST and diagnose after
⚠️ THE LESSON OF MAJOR BLOWOUTS  ⚠️ they are almost never a single
   failure. ⚠️ Deepwater Horizon involved cement design, a
   misinterpreted negative pressure test, BOP condition, and
   organizational decisions under commercial pressure —
   ⚠️ the classic multi-barrier, multi-organization failure
   (see a civil/industrial engineering reference)
```
**⚠️ Well INTEGRITY continues after drilling** — ⚠️ **through production, and critically
through ABANDONMENT.** **⚠️ Orphaned and improperly abandoned wells leak methane and are a
substantial and growing liability** (§25 → `mining-production-offshore-refining-coal-economics-and-safety`).

---

## §18. Completion and Hydraulic Fracturing

**⚠️ Completion** turns a drilled hole into a producing well: ⚠️ **perforating the casing,
installing tubing and packers, and controlling which zones flow.**
**⚠️ Hydraulic fracturing** injects fluid above the fracture gradient to create fractures,
held open by PROPPANT (usually sand) — ⚠️ **creating permeability where the rock had
almost none** (§14).
**⚠️ Frac fluid** is overwhelmingly water and sand with a small fraction of chemical
additives — ⚠️ **friction reducers, biocides, scale inhibitors — and disclosure of those
additives was a major regulatory fight.**
```
⚠️ THE GENUINE ENVIRONMENTAL ISSUES, distinguished
   ⚠️ WATER CONSUMPTION — large, and locally significant in arid basins
   ⚠️ PRODUCED / FLOWBACK WATER — ⚠️ often highly saline and
      sometimes naturally radioactive; disposal is the problem
   ⚠️ INDUCED SEISMICITY — ⚠️ overwhelmingly associated with
      WASTEWATER DISPOSAL INJECTION rather than fracturing itself.
      This distinction is real and frequently muddled
   ⚠️ METHANE LEAKAGE — ⚠️ decisive for the climate case, because
      methane's short-term warming potency means the leak rate
      determines whether gas beats coal
   ⚠️ WELL INTEGRITY — ⚠️ groundwater contamination, where it has
      occurred, is generally attributable to casing/cement failure
      or surface spills rather than fractures propagating
      thousands of feet up to aquifers
```
