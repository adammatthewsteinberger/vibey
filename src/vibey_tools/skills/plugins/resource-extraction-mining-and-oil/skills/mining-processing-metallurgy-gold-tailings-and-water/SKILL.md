---
name: mining-processing-metallurgy-gold-tailings-and-water
description: "Use for turning rock into metal and dealing with what is left: mineral processing including flotation and separation, extractive metallurgy across pyrometallurgy and hydrometallurgy, gold specifically with cyanidation and refractory ores, tailings and the dam failure modes that make them the industry's largest catastrophic risk, and water and drainage including acid mine drainage."
---

# Resource Extraction: Mineral Processing, Extractive Metallurgy, Gold, Tailings, and Water and Drainage

> **Part 3 of 6** of the *Resource Extraction: Mining, Oil and Gas* reference (plugin `resource-extraction-mining-and-oil`), covering §9–§13. Sibling skills: `mining-grade-deposits-exploration-and-reserves` (§0–§4), `mining-surface-underground-drilling-blasting-and-comminution` (§5–§8), `mining-petroleum-geology-drilling-well-control-and-fracturing` (§14–§18), `mining-production-offshore-refining-coal-economics-and-safety` (§19–§26), `mining-reference` (§27–§32). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
> 3. **⚠️ THE LIABILITY OUTLASTS THE MINE** (§12, §13, §25 → `mining-production-offshore-refining-coal-economics-and-safety`). **Tailings dams and acid
>    drainage require management for centuries after the ore runs out, and the entity that
>    profited is frequently gone.**

---

## §9. Mineral Processing

**⚠️ Concentrating the valuable mineral, exploiting a physical or chemical property
difference.**
```
⚠️ FROTH FLOTATION  ⚠️ THE dominant method for sulfides, and one of
   the most economically important technologies of the 20th century
   ⚠️ Collectors make target mineral surfaces hydrophobic, frothers
   stabilize bubbles, depressants and activators tune selectivity;
   ⚠️ pH control is central. Target particles attach to bubbles
   and float; gangue sinks
⚠️ GRAVITY  jigs, spirals, shaking tables, centrifugal concentrators
   — ⚠️ works when there is a large density contrast (gold, tin)
⚠️ MAGNETIC  iron ore; ⚠️ ELECTROSTATIC for mineral sands
⚠️ DENSE MEDIA SEPARATION  pre-concentration, especially coal
⚠️ SORTING  ⚠️ optical and sensor-based ore sorting is genuinely
   growing — reject waste BEFORE grinding it (§8)
⚠️ DEWATERING  thickeners, filters, ⚠️ and this determines what the
   tailings look like (§12)
⚠️ RECOVERY vs GRADE  ⚠️ an unavoidable trade-off curve. You can
   have a high-grade concentrate or high recovery, not both
```

---

## §10. Extractive Metallurgy

```
⚠️ PYROMETALLURGY  heat
   ⚠️ Roasting · SMELTING (⚠️ producing matte and slag) · converting
   · refining. ⚠️ Sulfide smelting produces SO₂, which is captured
   and made into sulfuric acid — ⚠️ historically the cause of
   severe acid rain where it wasn't
   ⚠️ IRON  blast furnace (coke as both reductant and fuel) →
   basic oxygen furnace. ⚠️ EAF recycles scrap at far lower energy
⚠️ HYDROMETALLURGY  aqueous chemistry
   ⚠️ Leaching (heap, vat, pressure) → solution purification
   (⚠️ SOLVENT EXTRACTION — the workhorse, and the key technology
   in rare earth SEPARATION, §27.1) → precipitation or electrowinning
⚠️ ELECTROMETALLURGY
   ⚠️ ELECTROWINNING and ELECTROREFINING (copper cathode)
   ⚠️ HALL-HÉROULT for ALUMINIUM — ⚠️ aluminium's enormous
   electricity demand is why smelters follow cheap power, and
   why aluminium is sometimes called "solid electricity"
⚠️ THE SEPARATION PROBLEM  ⚠️ chemically similar elements are the
   hard ones. ⚠️ Rare earths are notoriously difficult precisely
   because they are so similar, requiring many solvent extraction
   stages — which is the real bottleneck in §27.1
```

---

## §11. ⚠️ Gold

**⚠️ Worth separating because its chemistry, economics and social footprint are all
unusual.**
```
⚠️ OCCURRENCE  ⚠️ often as free gold, or locked in sulfides
   (⚠️ "refractory" ore, requiring oxidation before leaching)
⚠️ GRAVITY  ⚠️ gold's density (~19.3) makes gravity separation
   effective — the basis of panning, sluicing and placer mining
⚠️ CYANIDATION  ⚠️ the dominant industrial process. Dilute cyanide
   dissolves gold as a complex; recovered by carbon adsorption
   (CIL/CIP) or zinc precipitation
   ⚠️ Cyanide is acutely toxic and DEGRADES in the environment
   rather than persisting; ⚠️ the catastrophic risk is a TAILINGS
   RELEASE (§12) — the Baia Mare spill being the reference case
   ⚠️ The International Cyanide Management Code is the voluntary
   governance framework
⚠️ HEAP LEACHING  low-grade ore on a lined pad
⚠️ ⚠️ MERCURY AMALGAMATION  ⚠️ obsolete industrially and WIDESPREAD in
   artisanal and small-scale mining (§26). ⚠️ ASM gold is reported
   as the largest single source of anthropogenic mercury emissions,
   and the health harm falls on miners and their communities.
   ⚠️ The Minamata Convention specifically targets it
⚠️ REFINING  Miller (chlorination) and Wohlwill (electrolytic)
```

---

## §12. ⚠️ Tailings

> **⚠️ The largest volume product of mining, the longest-lived liability, and the source of
> its worst disasters.**
```
⚠️ WHAT THEY ARE  ⚠️ finely ground rock plus process water plus
   residual reagents. ⚠️ At 1% ore grade, 99% of what you mined
   becomes tailings
⚠️ CONVENTIONAL STORAGE  a slurry impounded behind a DAM
⚠️ ⚠️ CONSTRUCTION METHODS — this is the critical distinction
   ⚠️ UPSTREAM  the dam is raised by building ON TOP OF THE
      PREVIOUSLY DEPOSITED TAILINGS. ⚠️ Cheapest, and the least
      stable — vulnerable to LIQUEFACTION under seismic or rapid
      loading. ⚠️ Implicated in the worst failures and now BANNED
      in some jurisdictions
   ⚠️ DOWNSTREAM  raised away from the pond. Most stable, most
      expensive
   ⚠️ CENTRELINE  intermediate
⚠️ ALTERNATIVES  ⚠️ thickened and PASTE tailings · FILTERED "dry
   stack" (⚠️ no dam, no liquefaction risk, higher cost and
   power) · backfill into mined voids
⚠️ THE FAILURE MECHANISM  ⚠️ static or seismic LIQUEFACTION —
   saturated loose material momentarily behaves as a fluid and the
   whole mass flows. ⚠️ Brumadinho showed this can occur with NO
   external trigger and essentially no warning
⚠️ GOVERNANCE  ⚠️ the Global Industry Standard on Tailings
   Management (GISTM) was created after those failures, with
   independent review and named accountable executives
```
> **⚠️ GOTCHA — a tailings facility is a PERMANENT structure that must remain stable
> forever, built by a company with a finite life, using the cheapest acceptable method, and
> raised incrementally over decades by successive engineers** (see a civil engineering
> reference on failure). ⚠️ **The incentive structure and the required timescale are
> fundamentally mismatched, and that — more than any specific engineering error — is why
> failures recur.**

---

## §13. Water and Drainage

**⚠️ ACID MINE DRAINAGE (AMD) is the defining long-term environmental problem of sulfide
mining.**
⚠️ **Sulfide minerals (especially pyrite) exposed to air and water oxidize, generating
sulfuric acid, and the acid mobilizes heavy metals.** ⚠️ **The reaction is catalysed by
bacteria and is SELF-SUSTAINING once started.**
**⚠️ It can persist for centuries** — ⚠️ **Roman-era mine sites still drain acid — and
prediction (acid-base accounting, kinetic testing) is done before mining precisely because
prevention is far cheaper than treatment in perpetuity.**
**⚠️ Prevention and treatment**: ⚠️ **keeping sulfides saturated or covered to exclude
oxygen, blending with neutralizing material, lime treatment, constructed wetlands and
passive systems.**
**⚠️ Water more broadly** is frequently the binding constraint on a project: ⚠️ **supply in
arid regions (much copper and lithium is in deserts), competition with agriculture and
communities, discharge quality, and dewatering's effect on local groundwater.**

---

# PART II — OIL AND GAS
