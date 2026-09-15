---
name: mining-production-offshore-refining-coal-economics-and-safety
description: "Use for production through to the end of an asset's life: production and decline curves, offshore operations, refining and gas processing, coal, the economics including cost curves, price cycles and capital intensity, safety and the major hazards in both industries, closure, remediation and long-term legacy liabilities, and social licence including artisanal and small-scale mining."
---

# Resource Extraction: Production and Decline, Offshore, Refining and Processing, Coal, Economics, Safety, Closure and Legacy, and Social Licence

> **Part 5 of 6** of the *Resource Extraction: Mining, Oil and Gas* reference (plugin `resource-extraction-mining-and-oil`), covering §19–§26. Sibling skills: `mining-grade-deposits-exploration-and-reserves` (§0–§4), `mining-surface-underground-drilling-blasting-and-comminution` (§5–§8), `mining-processing-metallurgy-gold-tailings-and-water` (§9–§13), `mining-petroleum-geology-drilling-well-control-and-fracturing` (§14–§18), `mining-reference` (§27–§32). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
> 1. **⚠️ GRADE AND TONNAGE DECIDE EVERYTHING** (§1 → `mining-grade-deposits-exploration-and-reserves`, §23). **A deposit is not "ore" because
>    of what's in it — it's ore only if it can be extracted profitably, so the price
>    changes the size of the deposit.**
> 2. **⚠️ MOST OF THE ENERGY GOES INTO BREAKING ROCK** (§8 → `mining-surface-underground-drilling-blasting-and-comminution`). **Comminution is a startling
>    share of global electricity use, and it is thermodynamically appalling — most of the
>    energy becomes heat and noise.**
> 3. **⚠️ THE LIABILITY OUTLASTS THE MINE** (§12 → `mining-processing-metallurgy-gold-tailings-and-water`, §13 → `mining-processing-metallurgy-gold-tailings-and-water`, §25). **Tailings dams and acid
>    drainage require management for centuries after the ore runs out, and the entity that
>    profited is frequently gone.**

---

## §19. Production and Decline

**⚠️ Drive mechanisms**: ⚠️ **solution gas, gas cap, water drive (⚠️ the most efficient),
gravity drainage — and artificial lift (pumpjacks, ESPs, gas lift) once natural pressure
falls.**
**⚠️ Recovery factors are humbling**: ⚠️ **primary recovery typically leaves most of the oil
in place; secondary (water and gas injection) improves it; ⚠️ ENHANCED OIL RECOVERY —
thermal, chemical, CO₂ miscible — pushes further at higher cost.**
**⚠️ DECLINE CURVES** — ⚠️ **production falls predictably once past peak, and shale wells in
particular decline very steeply in the first year or two, which is why sustaining shale
output requires continuous drilling rather than a one-off capital programme.**
**⚠️ Surface facilities**: **separation of oil, gas and water; gas processing; ⚠️ and
FLARING, which is a substantial and largely avoidable emissions source.**

---

## §20. Offshore

**⚠️ Everything is harder and an order of magnitude more expensive** (see a maritime
reference for the vessel engineering).
**⚠️ Structures by water depth**: ⚠️ **fixed platforms (shallow) → compliant towers → floating
production (semi-submersibles, FPSOs, spars, TLPs) → SUBSEA tiebacks to existing
infrastructure, which is now the dominant development model because it avoids a new
platform.**
**⚠️ The specific challenges**: ⚠️ **station-keeping and dynamic positioning, riser dynamics
and fatigue, HYDRATE formation in cold subsea lines (⚠️ a plugging problem managed with
insulation, methanol and heating), long-distance flow assurance, and intervention costs
measured in millions per day.**
**⚠️ Decommissioning** is now a major industry in mature basins — ⚠️ **and the cost is
frequently larger and later than originally provisioned** (§25).

---

## §21. Refining and Processing

**⚠️ Crude oil is a feedstock, not a product.**
⚠️ **DISTILLATION separates by boiling point; CONVERSION units (catalytic cracking,
hydrocracking, coking) break heavy fractions into lighter, more valuable ones;
⚠️ REFORMING and alkylation build octane; TREATING (hydrodesulfurization) removes sulfur to
meet fuel specifications.**
**⚠️ The refinery's economics** are the CRACK SPREAD — ⚠️ **the difference between crude cost
and product value — and complexity determines which crudes a refinery can profitably run.**
**⚠️ Petrochemical feedstock**: ⚠️ **naphtha and ethane crack to olefins, which become the
polymers in an organic-chemistry reference.** ⚠️ **This is why "phasing out oil" and
"phasing out plastics" are linked but distinct problems.**
**⚠️ Natural gas processing**: **removing water, acid gases, and NGLs; ⚠️ liquefaction for
LNG.**

---

## §22. Coal

**⚠️ Rank matters**: ⚠️ **peat → lignite → sub-bituminous → bituminous → anthracite, with
rising carbon and energy content.**
**⚠️ Two distinct markets that are often conflated**: ⚠️ **THERMAL coal for power, which is
substitutable; and METALLURGICAL/coking coal for steelmaking, which currently has no
drop-in substitute at scale — hydrogen direct reduction and EAF are the alternatives and
they are not yet equivalent** (§10 → `mining-processing-metallurgy-gold-tailings-and-water`).
**⚠️ Mining methods**: **longwall and room-and-pillar underground; strip and mountaintop
removal at surface.**
**⚠️ The specific hazards**: ⚠️ **METHANE explosions, coal dust explosions (⚠️ propagated by
the dust raised by an initial blast, which is why stone dusting exists), spontaneous
combustion, and pneumoconiosis — black lung — which has been RESURGENT rather than
eliminated.**

---

# PART III — SYSTEMS

## §23. ⚠️ Economics

```
⚠️ CUTOFF GRADE  ⚠️ the marginal decision: process this material
   only if its value exceeds the INCREMENTAL cost. ⚠️ Rises when
   prices fall, which shrinks reserves overnight (§1, §4)
⚠️ THE COST CURVE  ⚠️ producers ranked by cost. ⚠️ The marginal
   producer sets the price, and low-cost producers survive
   downturns. ⚠️ Position on the curve matters more than absolute cost
⚠️ CAPITAL INTENSITY  ⚠️ mines cost billions and take 10–20 years
   from discovery to production. ⚠️ Long lead times mean supply
   responds to price with a LAG of years
⚠️ THEREFORE THE CYCLE  ⚠️ high prices → investment → supply arrives
   years later, often together → glut → price crash → underinvestment
   → shortage. ⚠️ This is structural, not a failure of foresight
⚠️ VALUATION  NPV and DCF (see an investment reference), with
   ⚠️ enormous sensitivity to price and discount rate assumptions
⚠️ RESOURCE NATIONALISM  ⚠️ royalties, taxes, export restrictions
   and expropriation risk — ⚠️ and it rises when prices do (§27.1)
```

---

## §24. Safety

**⚠️ Mining and drilling remain among the most hazardous industries, and the fatality
patterns are well characterized.**
**⚠️ Mining**: ⚠️ **ground failure and rockfall, mobile equipment (⚠️ haul truck interactions
are a leading fatality cause and drive proximity detection systems), falls from height,
inrush of water or mud, explosives, confined spaces, and ⚠️ methane and coal dust
explosions** (§22).
**⚠️ Occupational health is the slower killer**: ⚠️ **SILICA dust (silicosis — ⚠️ and note
the resurgence associated with engineered stone benchtop fabrication, which is a genuinely
current occupational disaster), coal dust, diesel particulate, noise, vibration, and
heat.**
**⚠️ Oil and gas**: ⚠️ **well control (§17 → `mining-petroleum-geology-drilling-well-control-and-fracturing`), H₂S, fire and explosion, dropped objects,
confined space, and the offshore-specific problem that evacuation is slow.**
**⚠️ The systemic lesson** (see a civil/industrial reference): ⚠️ **major disasters are
organizational — Piper Alpha, Upper Big Branch, Deepwater Horizon and Brumadinho all
combined technical failure with production pressure, degraded barriers and normalized
deviance.**

---

## §25. Closure and Legacy

**⚠️ Mine closure is a design requirement, not an afterthought** — ⚠️ **and modern permitting
requires a closure plan and FINANCIAL ASSURANCE (bonds) up front, precisely because
historically companies dissolved and left the liability to the public.**
**⚠️ The elements**: ⚠️ **landform reshaping, capping and covering reactive material,
long-term tailings stability (§12 → `mining-processing-metallurgy-gold-tailings-and-water`), water treatment potentially in perpetuity (§13 → `mining-processing-metallurgy-gold-tailings-and-water`),
revegetation, and post-closure monitoring.**
**⚠️ Oil and gas abandonment**: ⚠️ **plugging wells properly, and ⚠️ ORPHANED WELLS —
millions of undocumented and improperly abandoned wells worldwide leaking methane and
contaminating groundwater — are now recognized as a substantial public liability, with
government programmes funding remediation the original operators did not.**
> **⚠️ GOTCHA — the recurring structural problem is that the profit is realized in years and
> the liability persists for centuries.** ⚠️ **Bonding is the mechanism intended to fix
> this, and bonds are frequently set well below true closure cost, so the residual risk
> sits with the public.** **⚠️ When evaluating any extractive project, "who pays for closure
> and is that amount actually adequate?" is the question that most often has a bad answer.**

---

## §26. Social Licence and Artisanal Mining

**⚠️ Social licence to operate** is not a legal instrument — ⚠️ **it is the practical
consent of affected communities, and its absence stops projects that hold every permit.**
**⚠️ FREE, PRIOR AND INFORMED CONSENT** for indigenous peoples is codified in ILO 169 and
UNDRIP, ⚠️ **and implementation varies enormously.**
**⚠️ The recurring conflicts**: ⚠️ **water competition (§13 → `mining-processing-metallurgy-gold-tailings-and-water`), land access and resettlement,
distribution of benefits, and the fact that impacts are local while benefits are often
national or foreign.**
**⚠️ THE RESOURCE CURSE** — ⚠️ **the observed tendency for resource-rich economies to
underperform, through Dutch disease, revenue volatility, and rent-seeking — is real as a
pattern and NOT deterministic, with Norway and Botswana as the standard counterexamples.**
**⚠️ ARTISANAL AND SMALL-SCALE MINING (ASM)** employs many millions of people worldwide —
⚠️ **it is a livelihood as much as an industry, and framing it purely as a problem to be
eliminated ignores that.** ⚠️ **The genuine harms are mercury exposure (§11 → `mining-processing-metallurgy-gold-tailings-and-water`), child labour,
unsafe workings and financing of armed groups; the responses are formalization, direct
purchasing schemes, and mercury-free processing rather than prohibition.**
**⚠️ Conflict minerals and traceability**: ⚠️ **3TG (tin, tantalum, tungsten, gold) schemes,
Dodd-Frank Section 1502, the EU Conflict Minerals Regulation — ⚠️ and an honest note that
some evaluations found de-facto embargo effects that harmed legitimate artisanal miners
without ending the conflict financing.**
