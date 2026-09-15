---
name: mining-surface-underground-drilling-blasting-and-comminution
description: "Use for getting rock out and broken: surface mining including open pit design and stripping ratio, underground mining methods and how ground conditions select them, drilling and blasting, and comminution — crushing and grinding, and why it dominates the energy budget of a mine."
---

# Resource Extraction: Surface Mining, Underground Mining, Drilling and Blasting, and Comminution

> **Part 2 of 6** of the *Resource Extraction: Mining, Oil and Gas* reference (plugin `resource-extraction-mining-and-oil`), covering §5–§8. Sibling skills: `mining-grade-deposits-exploration-and-reserves` (§0–§4), `mining-processing-metallurgy-gold-tailings-and-water` (§9–§13), `mining-petroleum-geology-drilling-well-control-and-fracturing` (§14–§18), `mining-production-offshore-refining-coal-economics-and-safety` (§19–§26), `mining-reference` (§27–§32). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
> 2. **⚠️ MOST OF THE ENERGY GOES INTO BREAKING ROCK** (§8). **Comminution is a startling
>    share of global electricity use, and it is thermodynamically appalling — most of the
>    energy becomes heat and noise.**
> 3. **⚠️ THE LIABILITY OUTLASTS THE MINE** (§12 → `mining-processing-metallurgy-gold-tailings-and-water`, §13 → `mining-processing-metallurgy-gold-tailings-and-water`, §25 → `mining-production-offshore-refining-coal-economics-and-safety`). **Tailings dams and acid
>    drainage require management for centuries after the ore runs out, and the entity that
>    profited is frequently gone.**

---

## §5. Surface Mining

**⚠️ Cheaper per tonne than underground, and limited by how much waste you must move.**
```
⚠️ OPEN PIT  ⚠️ benches, haul ramps, and ⚠️ PIT SLOPE ANGLE as the
   critical geotechnical decision — a degree steeper saves enormous
   stripping cost and increases failure risk. ⚠️ Slope stability
   is monitored continuously with radar
⚠️ STRIP MINING  ⚠️ coal and other flat-lying deposits; dragline
   or shovel, backfilling behind the advance
⚠️ QUARRYING  aggregate and dimension stone
⚠️ PLACER and DREDGING  gravity separation of alluvial material
⚠️ IN-SITU LEACHING (ISL/ISR)  ⚠️ dissolve the mineral underground
   and pump the solution up — ⚠️ used for uranium and some copper.
   ⚠️ No pit, no tailings, and a groundwater contamination risk
   that must be actively managed
⚠️ THE EQUIPMENT  ⚠️ the economics are dominated by SCALE — ultra-class
   haul trucks and electric rope shovels exist because cost per
   tonne falls with equipment size
```
**⚠️ The transition point**: ⚠️ **a pit deepens until the stripping ratio makes the next
increment uneconomic; then you either stop or go underground beneath it.**

---

## §6. Underground Mining

```
⚠️ THE CENTRAL TRADE  ⚠️ selective (low dilution, low tonnage,
   expensive) vs BULK (high tonnage, cheap, more dilution)
⚠️ METHODS
   ⚠️ ROOM AND PILLAR  leave pillars to hold the roof.
      ⚠️ Coal, potash, flat deposits
   ⚠️ CUT AND FILL  selective, backfilled — narrow high-grade veins
   ⚠️ SUBLEVEL and LONGHOLE STOPING  drill and blast into a void
   ⚠️ BLOCK / PANEL CAVING  ⚠️ undercut the orebody and let GRAVITY
      break it. ⚠️ The cheapest underground method per tonne, huge
      capital cost and very long lead time, and ⚠️ it causes
      SURFACE SUBSIDENCE by design
   ⚠️ LONGWALL  coal; the roof is allowed to collapse behind the face
⚠️ GROUND SUPPORT  rock bolts, mesh, shotcrete, cable bolts
⚠️ VENTILATION  ⚠️ the largest single power consumer in a deep mine,
   and non-negotiable — heat, diesel particulate, blasting fumes,
   radon, and methane in coal (§24)
⚠️ DEPTH LIMITS  ⚠️ rock temperature rises with depth (refrigeration
   plants at the deepest mines), and ⚠️ ROCKBURSTS — violent
   failure of highly stressed rock — set a practical ceiling
```

---

## §7. Drilling and Blasting

**⚠️ The most efficient way to break rock, and the most tightly controlled activity on any
mine.**
**⚠️ The design variables**: ⚠️ **hole diameter, burden and spacing, sub-drill, stemming
(⚠️ the inert material confining the charge — inadequate stemming wastes energy and throws
material), and the DELAY SEQUENCE.**
**⚠️ Millisecond delays** are the key idea — ⚠️ **firing holes in a designed sequence creates
free faces for successive holes, controls fragmentation, and dramatically reduces ground
vibration compared with firing everything at once.**
**⚠️ What blasting controls**: ⚠️ **FRAGMENTATION SIZE, which directly sets comminution
energy downstream (§8) — this is the "mine-to-mill" insight that finer blasting can reduce
total energy even though it costs more explosive.**
**⚠️ The nuisances that cause community conflict**: ⚠️ **ground vibration, airblast, flyrock
and dust — all monitored and regulated.**
**⚠️ Explosives are licensed, tracked and regulated everywhere**, ⚠️ **and handling is a
specialist trade.**

---

## §8. ⚠️ Comminution

> **⚠️ The energy story of mining, and it is far worse than most people assume.**
```
⚠️ THE STAGES  blasting → crushing (jaw, gyratory, cone) →
   ⚠️ GRINDING (SAG mill, ball mill, HPGR, stirred mills)
⚠️ WHY  ⚠️ you must LIBERATE the valuable mineral grains from the
   gangue before you can separate them (§9). ⚠️ Finer grinding
   improves liberation and costs energy super-linearly
⚠️ THE ENERGY  ⚠️ comminution is estimated at a few percent of GLOBAL
   ELECTRICITY consumption, and it is typically the largest energy
   consumer on a mine site
⚠️ THE EFFICIENCY IS APPALLING  ⚠️ the overwhelming majority of the
   input energy becomes heat, noise and vibration rather than new
   surface area. ⚠️ Estimates of the fraction doing useful work are
   commonly quoted at only a few percent
⚠️ HPGR (high pressure grinding rolls) and stirred mills are
   substantially more efficient than tumbling mills and are
   displacing them where the ore suits
⚠️ THE DESIGN TENSION  ⚠️ grind finer → better recovery, more
   energy, and ⚠️ finer tailings that are harder to dewater (§12)
```
**⚠️ This is why "just recycle metals" is genuinely powerful** — ⚠️ **recycling skips
mining, comminution and much of the metallurgy, and the energy saving for aluminium in
particular is very large.**
