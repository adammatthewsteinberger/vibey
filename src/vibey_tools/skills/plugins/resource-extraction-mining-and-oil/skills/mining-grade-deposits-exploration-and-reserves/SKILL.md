---
name: mining-grade-deposits-exploration-and-reserves
description: "Use for the framing that governs every extraction claim: grade, tonnage and why ore is an economic rather than a geological category, how deposits form, exploration from geochemistry through drilling programmes, and the resources-versus-reserves distinction and the reporting codes that make it enforceable. Includes the router for the whole resource extraction reference."
---

# Resource Extraction: Grade, Tonnage and the Nature of Ore, How Deposits Form, Exploration, and Resources Versus Reserves

> **Part 1 of 6** of the *Resource Extraction: Mining, Oil and Gas* reference (plugin `resource-extraction-mining-and-oil`), covering §0–§4. Sibling skills: `mining-surface-underground-drilling-blasting-and-comminution` (§5–§8), `mining-processing-metallurgy-gold-tailings-and-water` (§9–§13), `mining-petroleum-geology-drilling-well-control-and-fracturing` (§14–§18), `mining-production-offshore-refining-coal-economics-and-safety` (§19–§26), `mining-reference` (§27–§32). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
> 1. **⚠️ GRADE AND TONNAGE DECIDE EVERYTHING** (§1, §23 → `mining-production-offshore-refining-coal-economics-and-safety`). **A deposit is not "ore" because
>    of what's in it — it's ore only if it can be extracted profitably, so the price
>    changes the size of the deposit.**
> 2. **⚠️ MOST OF THE ENERGY GOES INTO BREAKING ROCK** (§8 → `mining-surface-underground-drilling-blasting-and-comminution`). **Comminution is a startling
>    share of global electricity use, and it is thermodynamically appalling — most of the
>    energy becomes heat and noise.**
> 3. **⚠️ THE LIABILITY OUTLASTS THE MINE** (§12 → `mining-processing-metallurgy-gold-tailings-and-water`, §13 → `mining-processing-metallurgy-gold-tailings-and-water`, §25 → `mining-production-offshore-refining-coal-economics-and-safety`). **Tailings dams and acid
>    drainage require management for centuries after the ore runs out, and the entity that
>    profited is frequently gone.**

---

## §0. Routing

| You want... | Go to |
|---|---|
| **⚠️ Grade, tonnage, why it matters** | **§1** |
| How deposits form | §2 |
| Exploration | §3 |
| **⚠️ Resources vs reserves** | **§4** |
| Surface mining | §5 → `mining-surface-underground-drilling-blasting-and-comminution` |
| Underground mining | §6 → `mining-surface-underground-drilling-blasting-and-comminution` |
| Drill and blast | §7 → `mining-surface-underground-drilling-blasting-and-comminution` |
| **⚠️ Comminution** | **§8 → `mining-surface-underground-drilling-blasting-and-comminution`** |
| Mineral processing | §9 → `mining-processing-metallurgy-gold-tailings-and-water` |
| Extractive metallurgy | §10 → `mining-processing-metallurgy-gold-tailings-and-water` |
| **⚠️ Gold** | **§11 → `mining-processing-metallurgy-gold-tailings-and-water`** |
| **⚠️ Tailings** | **§12 → `mining-processing-metallurgy-gold-tailings-and-water`** |
| Water and drainage | §13 → `mining-processing-metallurgy-gold-tailings-and-water` |
| Petroleum geology | §14 → `mining-petroleum-geology-drilling-well-control-and-fracturing` |
| Seismic | §15 → `mining-petroleum-geology-drilling-well-control-and-fracturing` |
| **Drilling** | **§16 → `mining-petroleum-geology-drilling-well-control-and-fracturing`** |
| **⚠️ Well control** | **§17 → `mining-petroleum-geology-drilling-well-control-and-fracturing`** |
| Completion and fracturing | §18 → `mining-petroleum-geology-drilling-well-control-and-fracturing` |
| Production and decline | §19 → `mining-production-offshore-refining-coal-economics-and-safety` |
| Offshore | §20 → `mining-production-offshore-refining-coal-economics-and-safety` |
| Refining | §21 → `mining-production-offshore-refining-coal-economics-and-safety` |
| Coal | §22 → `mining-production-offshore-refining-coal-economics-and-safety` |
| **⚠️ Economics** | **§23 → `mining-production-offshore-refining-coal-economics-and-safety`** |
| Safety | §24 → `mining-production-offshore-refining-coal-economics-and-safety` |
| Closure | §25 → `mining-production-offshore-refining-coal-economics-and-safety` |
| Social licence and ASM | §26 → `mining-production-offshore-refining-coal-economics-and-safety` |
| **What's live** | **§27 → `mining-reference`** |
| Misconceptions, numbers | §28–§29 → `mining-reference` |
| Sources, quick ref, method | §30–§32 → `mining-reference` |

---

## §1. ⚠️ Grade, Tonnage and the Nature of "Ore"

```
⚠️ ORE IS AN ECONOMIC TERM, NOT A GEOLOGICAL ONE
   ⚠️ Rock is ore if it can be mined and processed at a profit.
   ⚠️ Therefore the metal price CHANGES THE SIZE OF THE DEPOSIT —
   a price rise converts waste into ore and a fall does the reverse
⚠️ GRADE  concentration. ⚠️ Copper porphyry ~0.3–1% Cu · gold in
   grams per tonne · iron ore in tens of percent
⚠️ THE GRADE-TONNAGE RELATIONSHIP  ⚠️ high-grade deposits are small
   and rare; large deposits are low grade. ⚠️ The distribution is
   roughly log-normal, which is why the giants dominate supply
⚠️ CUTOFF GRADE  ⚠️ the grade at which material pays to process (§23)
⚠️ STRIPPING RATIO  ⚠️ tonnes of waste per tonne of ore. Often the
   single biggest cost driver in an open pit
⚠️ THE LONG-RUN TREND  ⚠️ average grades have FALLEN for most metals
   as the best deposits were mined first — so energy, water and
   waste per tonne of metal have all RISEN. ⚠️ This is the
   underlying physical reason mining's footprint grows
```
**⚠️ The consequence people miss**: ⚠️ **"there's plenty left in the ground" and "supply is
constrained" are both true simultaneously.** **⚠️ Crustal abundance is enormous;
economically extractable, permitted, financed and processable supply is not — and the
binding constraint is usually PROCESSING rather than geology** (§27.1 → `mining-reference`).

---

# PART I — MINING

## §2. How Deposits Form

**⚠️ Ore deposits are geological accidents — places where a normally dispersed element got
concentrated by orders of magnitude.**
```
⚠️ MAGMATIC  ⚠️ crystal settling and sulfide immiscibility —
   nickel, PGE, chromium
⚠️ HYDROTHERMAL  ⚠️ the big one. Hot fluids dissolve metals, migrate,
   and deposit them when conditions change
   ⚠️ PORPHYRY (copper, molybdenum — low grade, enormous tonnage) ·
   epithermal (gold, silver) · VMS · skarn · orogenic gold
⚠️ SEDIMENTARY  banded iron formations (⚠️ formed when the
   atmosphere oxygenated — most iron ore is a fossil of the Great
   Oxidation Event) · evaporites · placers (⚠️ gravity concentration
   in rivers — how gold rushes start)
⚠️ WEATHERING  ⚠️ laterites (nickel, ALUMINIUM as bauxite) ·
   supergene enrichment
⚠️ BRINES and EVAPORATION  lithium
```
**⚠️ Why this matters practically**: ⚠️ **deposit type predicts geometry, grade
distribution, mineralogy and therefore the whole mining and processing route.** **⚠️ You
explore for a MODEL, not for a metal.**

---

## §3. Exploration

**⚠️ A funnel with brutal odds** — ⚠️ **the overwhelming majority of exploration projects
never become mines, which is why exploration is financed as high-risk venture capital.**
```
⚠️ THE SEQUENCE  regional targeting → geological mapping →
   ⚠️ GEOCHEMISTRY (soil, stream sediment, rock chip) →
   ⚠️ GEOPHYSICS (magnetics, gravity, electromagnetics, IP —
   ⚠️ INDUCED POLARIZATION is the classic sulfide finder) →
   trenching → ⚠️ DRILLING → resource estimation (§4)
⚠️ DRILLING IS WHERE THE MONEY GOES  ⚠️ diamond core (⚠️ gives
   intact rock, structure and geotechnical data) vs RC
   (reverse circulation — faster, cheaper, chips only)
⚠️ ASSAYING and QA/QC  ⚠️ blanks, standards and duplicates are
   inserted into the sample stream because assay fraud and
   sample mix-ups have both happened at scale
⚠️ THE MODERN CHALLENGE  ⚠️ outcropping deposits are largely found.
   Exploration is increasingly UNDER COVER, which is far harder
   and more expensive
```
**⚠️ The Bre-X lesson**: ⚠️ **the largest gold fraud in history involved salted samples, and
the modern chain-of-custody and independent-verification requirements exist because of
it.**

---

## §4. ⚠️ Resources versus Reserves

> **⚠️ A precise, legally enforceable distinction that outsiders routinely collapse — and
> the collapse is the mechanism of most mining investment misunderstanding.**
```
⚠️ MINERAL RESOURCE  ⚠️ a concentration with REASONABLE PROSPECTS
   for eventual economic extraction
   ⚠️ INFERRED (low confidence — ⚠️ CANNOT be converted directly
      into a reserve) → INDICATED → MEASURED
⚠️ ORE RESERVE  ⚠️ the economically mineable part of an INDICATED or
   MEASURED resource, ⚠️ after applying MODIFYING FACTORS — mining
   method, processing recovery, metallurgy, infrastructure,
   economics, marketing, legal, environmental, social, GOVERNMENTAL
   ⚠️ PROBABLE → PROVED
⚠️ THE CODES  ⚠️ JORC (Australia) · NI 43-101 (Canada) ·
   SAMREC · SK-1300 (US) — ⚠️ all under the CRIRSCO umbrella
⚠️ COMPETENT / QUALIFIED PERSON  ⚠️ a named individual with personal
   liability for the estimate. ⚠️ That personal accountability is
   the point of the whole system
```
> **⚠️ GOTCHA — a RESOURCE is not money in the ground.** ⚠️ **Reporting "10 million ounces
> of resource" says nothing about whether any of it can be mined profitably.** **⚠️ The
> reserve figure is the one that has survived economic and legal scrutiny, and the
> conversion rate from resource to reserve is often poor.**
> **⚠️ Equivalent caution in oil and gas: PROVED (1P), PROBABLE (2P), POSSIBLE (3P), and
> the difference between them is enormous.** ⚠️ **Note also that national "reserves"
> figures for some petrostates are politically determined rather than audited.**
