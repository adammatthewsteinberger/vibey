---
name: infra-reference
description: "Use when correcting an infrastructure misconception, looking up a design speed, load, capacity, condition-rating, cost or lifespan figure, finding the sources, or needing a quick-reference picker — plus the current state of US surface transportation funding and bridge vessel-collision risk. Companion to the other infrastructure skills."
---

# Roads, Bridges and Infrastructure: What's Live, Misconceptions, Numbers, and Sources

> **Part 6 of 6** of the *Roads, Bridges and Public Infrastructure* reference (plugin `roads-bridges-and-public-infrastructure`), covering §27–§32. Sibling skills: `infra-geometric-design-pavement-drainage-and-traffic` (§0–§5), `infra-intersections-road-safety-and-construction` (§6–§8), `infra-bridges-types-loads-failure-modes-and-inspection` (§9–§13), `infra-water-wastewater-transit-ports-and-utilities` (§14–§18), `infra-procurement-cost-asset-management-funding-and-equity` (§19–§26). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The engineering is mature and codified. Two things are live. See §27 for US surface transportation funding, and bridge vessel-collision risk.

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

## §27. What's Live — checked August 2026

### 27.1 ⚠️ US surface transportation funding expires in five weeks
**⚠️ §22 → `infra-procurement-cost-asset-management-funding-and-equity`'s structural problem arriving at a hard date — and this is the single most
consequential item in the file for anyone working in US infrastructure.**

- **⚠️ THE DEADLINE.** ⚠️ **The Infrastructure Investment and Jobs Act's surface
  transportation authorization expires 30 September 2026.** ⚠️ **After that date, absent a
  new bill or an extension, formula funding for highways, bridges and transit reverts to
  pre-IIJA levels and discretionary grant programmes stop making new awards.**
- ⚠️ **As of mid-2026, no replacement bill had been introduced in either chamber, though
  committees have held hearings since January 2025 and AASHTO published reauthorization
  priorities in May 2025.**
- **⚠️ THE UNDERLYING ARITHMETIC IS THE REAL STORY, and it is §22 → `infra-procurement-cost-asset-management-funding-and-equity`'s fuel-tax problem
  quantified.** ⚠️ **The federal gas tax has been 18.4 cents per gallon since 1993 —
  thirty-three years without adjustment.** ⚠️ **IIJA required $118 billion in GENERAL FUND
  TRANSFERS to keep the Highway Trust Fund solvent over its life, and CRS notes this
  general-fund reliance will have been de facto policy for 18 years by the time IIJA
  expires.**
- **⚠️ CBO PROJECTIONS.** ⚠️ **A five-year reauthorization beginning in FY2027 would face a
  projected gap between revenues and outlays of $166 billion, and CBO projects the highway
  account balance approaching zero in FY2028.**
- ⚠️ **One analysis frames the annual mismatch plainly: maintaining IIJA-level spending
  would require more than $102 billion a year against roughly $44 billion in gas tax
  receipts.**

> **⚠️ GOTCHA — the inflation point is the one that gets lost, and it reframes the whole
> "historic investment" narrative.** ⚠️ **CRS notes that although average annual funding rose
> roughly 62% in NOMINAL terms from the previous authorization to IIJA, the PURCHASING POWER
> of FY2025 funding was LESS than that of FY2005 — the first year of SAFETEA.**
> **⚠️ So two decades of nominal increases produced a real-terms decline, against an asset
> base that kept ageing** (§21 → `infra-procurement-cost-asset-management-funding-and-equity`).
> ⚠️ **Congress has historically operated on short-term extensions for a substantial share of
> the time, and the last two surface transportation bills both required multiple extensions
> before final passage — so an extension rather than a full reauthorization is the
> historically likely outcome.**

**⚠️ Sourcing note: the dates, the $118bn transfer, the $166bn projected gap and the
purchasing-power comparison come from Congressional Research Service reports drawing on CBO
baselines — about as disinterested as this subject gets.** ⚠️ **Advocacy organizations on
several sides are also active here and I have kept to the CRS figures.**

### 27.2 ⚠️ Bridges and vessel collision after the Key Bridge
**⚠️ §12 → `infra-bridges-types-loads-failure-modes-and-inspection`'s failure mode producing a systematic national response — and the NTSB's central
finding is about a calculation that was never performed.**

- **⚠️ WHAT HAPPENED.** ⚠️ **On 26 March 2024 the 984-foot containership Dali lost power and
  struck Pier 17 of the Francis Scott Key Bridge in Baltimore, causing catastrophic collapse
  and killing six roadworkers.**
- **⚠️ THE NTSB'S FINDING IS THE STRIKING PART.** ⚠️ **A post-incident vulnerability
  assessment calculated the Key Bridge's annual frequency of collapse at nearly 30 TIMES the
  AASHTO acceptable risk threshold for critical or essential bridges.** ⚠️ **NTSB Chair
  Jennifer Homendy stated that had the Maryland Transportation Authority conducted the
  assessment, it "would have known the risk and could have taken action" — and that "the
  collapse could have been prevented."**
- **⚠️ THE HISTORY MAKES IT WORSE.** ⚠️ **AASHTO developed and published the vulnerability
  assessment calculation in 1991, in response to the NTSB's investigation of the 1980
  Sunshine Skyway collapse, and recommended at the time that owners assess EXISTING bridges
  — reiterating that recommendation in 2009.** ⚠️ **FHWA has required new bridges to be
  designed against vessel collision since 1994; the Key Bridge predated that requirement.**
- **⚠️ THE RECOMMENDATION.** ⚠️ **In March 2025 the NTSB recommended that 30 owners of 68
  bridges across 19 states conduct vulnerability assessments using AASHTO's Method II
  calculation, and develop comprehensive risk reduction plans where results exceed the
  threshold.** ⚠️ **All 68 were designed before the AASHTO guidance existed and lacked a
  current assessment.** ⚠️ **NTSB also recommended FHWA, the Coast Guard and the Army Corps
  form an interdisciplinary team to assist owners.**

> **⚠️ GOTCHA — the NTSB was explicit that this is not a list of bridges expected to
> collapse.** ⚠️ **Its own statement said the report "does not suggest that the 68 bridges
> are certain to collapse" — the recommendation is to CALCULATE a risk that is currently
> UNKNOWN.**
> ⚠️ **Some owners responded that their structures are already protected: the Verrazzano
> Narrows towers are protected by rock islands, and the Port Authority noted that
> Dali-class ships do not transit under several of its bridges and that vessels which do are
> roughly a third the tonnage.** **⚠️ Those are substantive answers, and they are exactly
> the kind of site-specific analysis the assessment is meant to produce.**
> **⚠️ The transferable lesson is §12 → `infra-bridges-types-loads-failure-modes-and-inspection`'s pattern precisely: a known method, a known
> recommendation, a structure predating the requirement, and no trigger forcing anyone to
> run the numbers** — ⚠️ **the same shape as the buildings reference's account of how design
> knowledge fails to reach the structure that needs it.**

**⚠️ The remedies available** are the ones §9 → `infra-bridges-types-loads-failure-modes-and-inspection` and §12 → `infra-bridges-types-loads-failure-modes-and-inspection` describe: ⚠️ **protective dolphins and
islands, fendering, and operational changes such as tug escorts and transit restrictions —
and the NTSB report notes the cost differences between them, with crushable concrete and
timber fendering used widely because it is relatively cheap and only effective against minor
impact.**
**⚠️ Sourcing note: this comes from the NTSB's own press release and marine investigation
report MIR2510, plus AASHTO's and affected owners' responses — primary throughout.**

---

## §28. Misconceptions

| Misconception | Correction |
|---|---|
| Adding lanes relieves congestion | ⚠️ **Induced demand; elasticity near 1 in urban corridors** (§25 → `infra-procurement-cost-asset-management-funding-and-equity`) |
| Removing a road causes gridlock | ⚠️ **Traffic evaporation is documented too** (§25 → `infra-procurement-cost-asset-management-funding-and-equity`) |
| Congestion means insufficient capacity | ⚠️ **It's the price paid in time when money price is zero** (§22 → `infra-procurement-cost-asset-management-funding-and-equity`, §25 → `infra-procurement-cost-asset-management-funding-and-equity`) |
| More traffic means more flow | ⚠️ **Past the peak, flow FALLS with density** (§5 → `infra-geometric-design-pavement-drainage-and-traffic`) |
| Cars wear out roads | ⚠️ **Fourth power law — heavy axles do essentially all of it** (§3 → `infra-geometric-design-pavement-drainage-and-traffic`) |
| The surface course determines pavement life | ⚠️ **Subgrade and drainage do** (§3 → `infra-geometric-design-pavement-drainage-and-traffic`, §4 → `infra-geometric-design-pavement-drainage-and-traffic`) |
| Fix the worst roads first | ⚠️ **Mathematically wrong. Treat before the cliff** (§21 → `infra-procurement-cost-asset-management-funding-and-equity`) |
| "Structurally deficient" means unsafe | ⚠️ **It's a maintenance-backlog measure. Unsafe bridges close** (§13 → `infra-bridges-types-loads-failure-modes-and-inspection`) |
| "Functionally obsolete" is structural | ⚠️ **It means geometry doesn't meet current standards** (§13 → `infra-bridges-types-loads-failure-modes-and-inspection`) |
| Bridges mostly fail structurally | ⚠️ **Scour is the leading cause, and it hides** (§12 → `infra-bridges-types-loads-failure-modes-and-inspection`) |
| Tacoma Narrows was resonance | ⚠️ **Aeroelastic flutter. The textbook story is wrong** (§12 → `infra-bridges-types-loads-failure-modes-and-inspection`) |
| Safer road design is always safer | ⚠️ **Forgiving design invites speed. Context decides** (§2 → `infra-geometric-design-pavement-drainage-and-traffic`, §7 → `infra-intersections-road-safety-and-construction`) |
| Speed limits control speed | ⚠️ **Geometry does. Design self-enforcing streets** (§2 → `infra-geometric-design-pavement-drainage-and-traffic`, §7 → `infra-intersections-road-safety-and-construction`) |
| Crashes are caused by bad drivers | ⚠️ **Safe System: design so mistakes aren't fatal** (§7 → `infra-intersections-road-safety-and-construction`) |
| A site improved, so the fix worked | ⚠️ **Regression to the mean. Use comparison groups** (§7 → `infra-intersections-road-safety-and-construction`) |
| Roundabouts are less safe | ⚠️ **8 conflict points vs 32, and no crossing conflicts** (§6 → `infra-intersections-road-safety-and-construction`) |
| Level of Service measures road quality | ⚠️ **It measures vehicle delay only** (§5 → `infra-geometric-design-pavement-drainage-and-traffic`) |
| Water towers store water for supply | ⚠️ **Primarily pressure and peaking** (§14 → `infra-water-wastewater-transit-ports-and-utilities`) |
| Flint was a water-quality event | ⚠️ **A chemistry change mobilized lead from existing pipes** (§14 → `infra-water-wastewater-transit-ports-and-utilities`) |
| Storm drains should move water fast | ⚠️ **That moves the flood downstream. Detain and infiltrate** (§15 → `infra-water-wastewater-transit-ports-and-utilities`) |
| Transit ridership follows vehicle quality | ⚠️ **Frequency, reliability and land use** (§16 → `infra-water-wastewater-transit-ports-and-utilities`) |
| P3s save public money | ⚠️ **Private capital costs more. Savings must come from efficiency** (§19 → `infra-procurement-cost-asset-management-funding-and-equity`) |
| Cost overruns are random bad luck | ⚠️ **Systematically biased — optimism plus strategic misrepresentation** (§20 → `infra-procurement-cost-asset-management-funding-and-equity`) |
| Financing solves a funding problem | ⚠️ **It moves payment in time. Someone still pays** (§22 → `infra-procurement-cost-asset-management-funding-and-equity`) |
| The gas tax just needs raising | ⚠️ **Fixed per gallon, efficiency gains, EVs. Structurally dying** (§22 → `infra-procurement-cost-asset-management-funding-and-equity`, §27.1) |
| IIJA was a historic funding increase | ⚠️ **Nominally yes; FY2025 purchasing power below FY2005** (§27.1) |
| Design storms are a settled input | ⚠️ **The statistics are no longer stationary** (§24 → `infra-procurement-cost-asset-management-funding-and-equity`) |
| Highway routing was neutral engineering | ⚠️ **Path of least resistance, and sometimes explicit** (§26 → `infra-procurement-cost-asset-management-funding-and-equity`) |

---

## §29. Numbers

```
⚠️ ⚠️ FOURTH POWER LAW  ⚠️ pavement damage ∝ axle load⁴
⚠️ ⚠️ KINETIC ENERGY ∝ v² — the basis of all speed management
⚠️ Survivability (approx)  ⚠️ pedestrian ~30 km/h · side ~50 ·
   head-on ~70
⚠️ Design perception-reaction  2.5 s (conservative, by design)
⚠️ Conflict points  ⚠️ 4-leg intersection 32 · roundabout 8
⚠️ Induced demand elasticity  ⚠️ ~1.0 (VMT to lane-km, urban)
⚠️ Condition rating scale  0-9 · ⚠️ inspection cycle typically 2 yr
⚠️ ⚠️ US federal gas tax  ⚠️ 18.4¢/gal, UNCHANGED SINCE 1993
⚠️ ⚠️ IIJA expires  ⚠️ 30 SEPTEMBER 2026
⚠️ IIJA general fund transfers  ⚠️ $118 billion (CRS)
⚠️ ⚠️ Projected 5-yr HTF gap from FY2027  ⚠️ $166 billion (CBO)
⚠️ Highway account balance approaching zero  ⚠️ FY2028 (CBO)
⚠️ Spending vs receipts  ⚠️ ~$102bn needed vs ~$44bn gas tax
⚠️ ⚠️ Purchasing power  ⚠️ FY2025 BELOW FY2005 despite +62% nominal
⚠️ ⚠️ Key Bridge collapse  ⚠️ 26 March 2024 · Dali, 984 ft · 6 dead
⚠️ ⚠️ Key Bridge risk  ⚠️ ~30× the AASHTO threshold for essential
   bridges (0.0001 annual frequency of collapse)
⚠️ NTSB recommendation  ⚠️ 68 bridges · 30 owners · 19 states
⚠️ AASHTO assessment method published  ⚠️ 1991 (after Sunshine
   Skyway 1980) · FHWA required for new bridges since 1994
```

---

## §30. Sources

| Source | Why |
|---|---|
| **AASHTO Green Book (*Geometric Design of Highways and Streets*)** | ⚠️ **§2 → `infra-geometric-design-pavement-drainage-and-traffic`, the reference** |
| **AASHTO LRFD Bridge Design Specifications** | ⚠️ **§9–§11 → `infra-bridges-types-loads-failure-modes-and-inspection`** |
| **Highway Capacity Manual (TRB)** | ⚠️ **§5 → `infra-geometric-design-pavement-drainage-and-traffic`** |
| **MUTCD** | Traffic control devices, US |
| **NACTO Urban Street Design Guide** | ⚠️ **§2 → `infra-geometric-design-pavement-drainage-and-traffic`, §7 → `infra-intersections-road-safety-and-construction` — the urban counterweight to the Green Book** |
| **NTSB accident reports** | ⚠️ **§12 → `infra-bridges-types-loads-failure-modes-and-inspection`, §27.2 — read these directly. Free and excellent** |
| **Flyvbjerg, *Megaprojects and Risk* / *How Big Things Get Done*** | ⚠️ **§20 → `infra-procurement-cost-asset-management-funding-and-equity`** |
| **Duranton & Turner on induced demand** | ⚠️ **§25 → `infra-procurement-cost-asset-management-funding-and-equity`, the key empirical paper** |
| **CRS reports on transportation funding** | ⚠️ **§22 → `infra-procurement-cost-asset-management-funding-and-equity`, §27.1 — disinterested and free** |
| **FHWA Bridge Inspector's Reference Manual** | ⚠️ **§13 → `infra-bridges-types-loads-failure-modes-and-inspection`** |
| **Safe System resources (FHWA, iRAP, Vision Zero Network)** | ⚠️ **§7 → `infra-intersections-road-safety-and-construction`** |
| **Jeff Speck, *Walkable City*; Marohn, *Strong Towns*** | §2 → `infra-geometric-design-pavement-drainage-and-traffic`, §21 → `infra-procurement-cost-asset-management-funding-and-equity` — accessible and opinionated |

---

## §31. Quick Reference

### 31.1 Picker
| Question | Where |
|---|---|
| Will widening fix congestion? | ⚠️ **No, in a growing urban corridor** (§25 → `infra-procurement-cost-asset-management-funding-and-equity`) |
| What actually fixes congestion? | ⚠️ **Pricing** (§22 → `infra-procurement-cost-asset-management-funding-and-equity`, §25 → `infra-procurement-cost-asset-management-funding-and-equity`) |
| Why does this road keep failing? | ⚠️ **Drainage and subgrade, not the surface** (§3 → `infra-geometric-design-pavement-drainage-and-traffic`, §4 → `infra-geometric-design-pavement-drainage-and-traffic`) |
| Which roads should we resurface? | ⚠️ **Not the worst. Treat before the cliff** (§21 → `infra-procurement-cost-asset-management-funding-and-equity`) |
| Is this bridge dangerous? | ⚠️ **"Deficient" ≠ unsafe. Unsafe ones close** (§13 → `infra-bridges-types-loads-failure-modes-and-inspection`) |
| Why did that bridge fail? | ⚠️ **Suspect scour first** (§12 → `infra-bridges-types-loads-failure-modes-and-inspection`) |
| How do we cut crashes? | ⚠️ **Speed and geometry, not education campaigns** (§7 → `infra-intersections-road-safety-and-construction`) |
| What speed limit for this street? | ⚠️ **The survivable crash type decides** (§7 → `infra-intersections-road-safety-and-construction`) |
| Is this cost estimate credible? | ⚠️ **Compare to completed similar projects, not the build-up** (§20 → `infra-procurement-cost-asset-management-funding-and-equity`) |
| Is a P3 a good idea here? | ⚠️ **Ask what risk actually transfers, and what capital costs** (§19 → `infra-procurement-cost-asset-management-funding-and-equity`) |
| Where will the money come from? | ⚠️ **Separate funding from financing first** (§22 → `infra-procurement-cost-asset-management-funding-and-equity`) |
| Should we rebuild this asset? | ⚠️ **A real question, not a given** (§21 → `infra-procurement-cost-asset-management-funding-and-equity`) |

### 31.2 Project evaluation checklist
- [ ] ⚠️ **What problem does this solve, and is it the stated one?** (§1 → `infra-geometric-design-pavement-drainage-and-traffic`)
- [ ] ⚠️ **Lifecycle cost, not capital cost — who maintains it in year 40?** (§21 → `infra-procurement-cost-asset-management-funding-and-equity`)
- [ ] ⚠️ **Estimate sanity-checked against a reference class** (§20 → `infra-procurement-cost-asset-management-funding-and-equity`)
- [ ] ⚠️ **Induced demand accounted for in the traffic forecast** (§25 → `infra-procurement-cost-asset-management-funding-and-equity`)
- [ ] Safety assessed by Safe System, not by driver blame (§7 → `infra-intersections-road-safety-and-construction`)
- [ ] ⚠️ **Drainage designed and NOT value-engineered out** (§4 → `infra-geometric-design-pavement-drainage-and-traffic`)
- [ ] Geotechnical investigation adequate before design is fixed (§4 → `infra-geometric-design-pavement-drainage-and-traffic`)
- [ ] ⚠️ **Design storms updated for non-stationary climate** (§24 → `infra-procurement-cost-asset-management-funding-and-equity`)
- [ ] Utility information quality established up front (§18 → `infra-water-wastewater-transit-ports-and-utilities`)
- [ ] ⚠️ **Who bears the costs; who receives the benefits** (§26 → `infra-procurement-cost-asset-management-funding-and-equity`)
- [ ] Multimodal access considered, not just vehicle LOS (§5 → `infra-geometric-design-pavement-drainage-and-traffic`, §16 → `infra-water-wastewater-transit-ports-and-utilities`)
- [ ] ⚠️ **For bridges over navigable water: has the vulnerability assessment been run?** (§27.2)

---

## §32. Method

**§1–§26 → `infra-geometric-design-pavement-drainage-and-traffic`, `infra-intersections-road-safety-and-construction`, `infra-bridges-types-loads-failure-modes-and-inspection`, `infra-water-wastewater-transit-ports-and-utilities`, `infra-procurement-cost-asset-management-funding-and-equity` rests on codified practice and a mature research literature** — **AASHTO
geometric and bridge design, the Highway Capacity Manual, the Safe System framework, the
fourth-power law, the deterioration curve, and the NTSB's accumulated failure
investigations.** ⚠️ **None needed verification; the fourth-power relationship dates to the
AASHO Road Test of the late 1950s and the induced-demand literature has been consistent for
decades.**

**Two searches were run in August 2026**, on **US surface transportation funding** and
**bridge vessel-collision risk** — ⚠️ **the first because §22 → `infra-procurement-cost-asset-management-funding-and-equity`'s structural problem hits a
hard statutory date five weeks from now, the second because §12 → `infra-bridges-types-loads-failure-modes-and-inspection`'s failure mode produced a
systematic national response whose central finding is worth understanding precisely.**

**Confidence.** **High** in §21 → `infra-procurement-cost-asset-management-funding-and-equity` and §7 → `infra-intersections-road-safety-and-construction`, which are the sections I'd most want read.
⚠️ **The "worst first" correction is the single most actionable thing here: the deterioration
curve means the optimal policy is treating roads that still look fine, which is politically
almost impossible to explain and mathematically not close.** ⚠️ **§7 → `infra-intersections-road-safety-and-construction`'s physics is the other
one — kinetic energy scales with v² against a fixed biological injury threshold, and once
you hold that, the Safe System conclusions follow rather than being asserted.**
**⚠️ §25 → `infra-procurement-cost-asset-management-funding-and-equity`'s induced demand is well evidenced and I have tried to state its LIMIT honestly:
it does not make road expansion always wrong, it makes the CONGESTION RELIEF PROMISE
unsupportable.**

**High** on §27.1, which comes from Congressional Research Service reports drawing on CBO
baselines: ⚠️ **the 30 September 2026 expiry, the $118 billion in general fund transfers
under IIJA, the $166 billion projected five-year gap, and the highway account approaching
zero in FY2028.**
⚠️ **The finding I would most want carried is the purchasing-power one — that FY2025 funding
bought less than FY2005 funding despite roughly 62% nominal growth — because it reframes a
decade of "historic investment" language against §21 → `infra-procurement-cost-asset-management-funding-and-equity`'s ageing asset base.**

**High** on §27.2, which is primary throughout: ⚠️ **the NTSB's own press release and marine
investigation report, plus AASHTO's and bridge owners' responses.**
⚠️ **The detail that makes it more than a news item is the chronology: AASHTO published the
assessment method in 1991 after Sunshine Skyway, recommended existing bridges be assessed,
reiterated it in 2009, and the Key Bridge was never assessed — with a calculated risk
roughly 30 times the threshold.** **⚠️ I have also carried the NTSB's own caveat that the 68
bridges are not expected to collapse, and the substantive responses from owners whose
structures are already protected, because reporting this as "68 bridges at risk of collapse"
would misstate what the recommendation says.**
