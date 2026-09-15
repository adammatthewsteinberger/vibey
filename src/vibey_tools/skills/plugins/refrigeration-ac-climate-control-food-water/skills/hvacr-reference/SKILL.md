---
name: hvacr-reference
description: "Use when correcting a refrigeration, HVAC or food storage misconception, looking up a temperature, pressure, superheat, GWP, air-change or water-treatment figure, finding the books and standards, or needing a quick-reference picker — plus the current state of the refrigerant transition and cold chain capacity. Companion to the other refrigeration and climate control skills."
---

# Refrigeration and Climate Control: What's Live, Misconceptions, Numbers, and Books

> **Part 5 of 5** of the *Refrigeration, AC, Climate Control and Food/Water Storage* reference (plugin `refrigeration-ac-climate-control-food-water`), covering §25–§30. Sibling skills: `hvacr-cycle-components-refrigerants-and-diagnosis` (§0–§6), `hvacr-load-calculation-air-humidity-and-heat-pumps` (§7–§13), `hvacr-cold-chain-temperature-limits-and-validation` (§14–§21), `hvacr-preservation-water-storage-and-treatment` (§22–§24). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The thermodynamics is permanent. Two areas moved. See §25 for the refrigerant transition, and cold chain capacity and food loss.

> **⚠️ Everything here is one idea in different clothes: MOVING HEAT from where you don't
> want it to where you don't care, and doing it reliably enough that the thing being
> cooled stays safe.** **Complements a thermodynamics reference (the cycle theory and
> psychrometrics) and a cooking/cleaning reference (food safety at the point of use).**
>
> **⚠️ GOTCHA** boxes mark the diagnoses people get backwards, and the safety limits that
> aren't negotiable.
>
> **⚠️ Safety, stated once and up front:** ⚠️ **refrigerant systems hold high pressure and
> can cause frostbite and asphyxiation; A2L refrigerants are mildly flammable and require
> specific tooling and training (§25.1); ammonia is toxic; and the food temperature limits
> in §16 → `hvacr-cold-chain-temperature-limits-and-validation` are not guidance, they are the reason people don't die.** **⚠️ Refrigerant handling
> is a certified activity in most jurisdictions — venting is illegal and recovery is
> mandatory.**
>
> **The three ideas that organize this document:**
> 1. **⚠️ SUPERHEAT and SUBCOOLING are how you see inside a sealed system** (§5 → `hvacr-cycle-components-refrigerants-and-diagnosis`).
>    **Everything else in diagnosis is guessing.**
> 2. **⚠️ The cold chain is only as good as its worst link, and the worst link is almost
>    always a HANDOFF** (§15 → `hvacr-cold-chain-temperature-limits-and-validation`, §20 → `hvacr-cold-chain-temperature-limits-and-validation`). **Not the warehouse and not the truck — the dock, the
>    delay, the unmonitored gap.**
> 3. **⚠️ Preservation is about denying microbes ONE of their requirements** (§22 → `hvacr-preservation-water-storage-and-treatment`).
>    **Temperature is only one option; water activity, pH, oxygen and competition are the
>    others, and the durable methods stack several.**

---

## §25. What's Live — verified August 2026

### 25.1 ⚠️ The refrigerant transition — the biggest change since R-22
**⚠️ If you buy, service or specify cooling equipment, this changes what you can install
and what service costs.**

- **⚠️ The driver is the AIM Act in the US and the revised F-Gas Regulation in the EU**,
  **both implementing the Kigali Amendment's HFC phasedown.** ⚠️ **The US target is
  reported as an 85% reduction in HFCs by 2036; the EU quota schedule runs from 100% of
  the 2015 baseline down to 5% by 2030.**
- **⚠️ The chemistry**: **R-410A has a GWP around 2,088.** ⚠️ **Its replacements are R-32
  (GWP ~675) and R-454B (GWP ~466, an HFC blend of R-32 and R-1234yf) — both roughly
  two-thirds lower impact while matching efficiency.** **⚠️ For residential and light
  commercial comfort cooling the GWP limit is 700, which is what excludes R-410A.**
- **⚠️ Both replacements are A2L — MILDLY flammable — and this is the practical change for
  anyone servicing equipment.** ⚠️ **A2L is defined by a burning velocity below 10 cm/s
  versus over 100 cm/s for propane (A3).** **⚠️ Reported practical behaviour: an A2L leak in
  a typical room rarely reaches flammable concentration before air movement dilutes it,
  and ignited flame often self-extinguishes.** **⚠️ Equipment must meet UL 60335-2-40,
  technicians need A2L-specific certification and tooling, and charge limits and leak
  detection apply.**
- **⚠️ Sector-specific EU limits are tiered rather than a single number**: **reported GWP
  2,500 as the outer limit for stationary refrigeration, 750 for new single-split AC, and
  150 for self-contained commercial refrigeration and — from 2029 — most residential AC.**
  ⚠️ **That last tier is low enough that A2L HFC blends won't clear it, pointing toward
  R-290 (propane) and other naturals.**

> **⚠️ GOTCHA — the sources CONFLICT on the R-410A installation deadline, and this matters
> if you're specifying equipment right now.** ⚠️ **Multiple 2026 sources state the EPA
> Technology Transitions Rule banned installation of new high-GWP residential systems from
> 1 January 2026.** **⚠️ But at least one source reports an EPA final rule in May 2026 that
> EXTENDED the installation deadline for pre-manufactured inventory, allowing contractors
> to still install pre-2025 R-410A stock**, **and another describes a "latest EPA action"
> that has been misread as reverting to the R-410A era.**
> **⚠️ The stable facts: manufacture of new R-410A equipment in the covered category is
> restricted, new equipment is A2L, and SERVICING existing R-410A systems remains legal
> indefinitely.** **⚠️ The unstable fact is the exact cut-off for installing existing
> inventory — verify against the EPA directly before relying on it.**

**⚠️ The economics is the part that reaches everyone**: ⚠️ **quota reduction has driven
reported R-410A price increases of roughly 40–70% from 2022 levels**, **and the phasedown
means that continues structurally regardless of supply conditions.** **⚠️ The practical
consequence: an expensive repair on an older R-410A system is a worse bet each year, and
the calculus for repair-vs-replace has shifted.** ⚠️ **Note also that you CANNOT retrofit
an A2L into an R-410A system** (§3 → `hvacr-cycle-components-refrigerants-and-diagnosis`).
**⚠️ Compliance obligations tightened too**: ⚠️ **annual leak inspections for covered
systems are reported starting January 2026, with automatic leak detection required on
systems over 1,500 lb charge.**

### 25.2 ⚠️ The cold chain gap: what missing refrigeration actually costs
**⚠️ The number that reframes §15 → `hvacr-cold-chain-temperature-limits-and-validation` from a logistics concern into a food-security one.**

- **⚠️ The UNEP–FAO *Sustainable Food Cold Chains* report finds that lack of effective
  refrigeration directly caused the loss of 526 million tonnes of food production —
  about 12% of the global total** (2017 figures). ⚠️ **Reported as enough to feed roughly
  1 billion people.**
- **⚠️ Context**: **an estimated 14% of food produced for human consumption is LOST before
  reaching the consumer and a further 17% WASTED**, ⚠️ **with the loss costing a reported
  $936 billion annually.**
- **⚠️ The emissions picture cuts both ways, which is the tension worth naming.** ⚠️ **The
  food cold chain is responsible for around 4% of total global greenhouse gas emissions
  when both the cooling technology and the food loss from missing refrigeration are
  counted** — **reported as roughly 20% direct refrigerant emissions and 80% from
  electricity generation.** **⚠️ So building cold chain adds emissions AND avoids the
  larger emissions from lost food; the answer is efficient, low-GWP cold chain rather
  than either extreme.**
- **⚠️ The distribution is what matters**: **post-harvest loss reportedly reduces the income
  of 470 million small-scale farmers by around 15%, mainly in developing countries;
  African post-harvest losses are reported at 30%+ for fresh produce; ⚠️ and low-income
  food-deficit countries account for a reported ~22% of world food loss.**
- **⚠️ Health side**: ⚠️ **the WHO has estimated nearly 25% of liquid vaccines are wasted
  each year, primarily from broken cold chains** (§21 → `hvacr-cold-chain-temperature-limits-and-validation`).

> **⚠️ GOTCHA — treat these figures as directionally solid and numerically soft, and the
> literature says so itself.** ⚠️ **A peer-reviewed analysis notes that FAO food loss and
> waste data are "limited and in many cases inconsistent and uncertain due to evolving
> definitions, varying tracking and reporting methodologies, and data access and quality
> limitations"** — **and that projected losses don't align well with theoretical food
> degradation models.** **⚠️ The 526 Mt / 12% figure is widely repeated because it comes
> from an authoritative source, not because it has been independently replicated.**
> **⚠️ The robust claim is that the gap is large and concentrated in low-income countries;
> the precise magnitude is not settled.**

**⚠️ Where the practical progress is**: ⚠️ **decentralized solar-powered cold storage at the
farm and market level (ColdHubs and similar operators) targets the FIRST link — §15 → `hvacr-cold-chain-temperature-limits-and-validation`'s
precooling — which is where the leverage is highest, rather than the trunk logistics that
attract more attention.**

---

## §26. Misconceptions

| Misconception | Correction |
|---|---|
| The compressor makes the cold | ⚠️ **Latent heat in the evaporator does** (§1 → `hvacr-cycle-components-refrigerants-and-diagnosis`) |
| Systems consume refrigerant | ⚠️ **They're sealed. Low means a LEAK** (§5 → `hvacr-cycle-components-refrigerants-and-diagnosis`) |
| Low on refrigerant, so add some | ⚠️ **Check airflow first; find the leak** (§5 → `hvacr-cycle-components-refrigerants-and-diagnosis`) |
| You can drop in a different refrigerant | ⚠️ **Pressures, oil, materials, safety design all differ** (§3 → `hvacr-cycle-components-refrigerants-and-diagnosis`) |
| Charge by superheat always | ⚠️ **TXV/EEV systems charge by SUBCOOLING** (§5 → `hvacr-cycle-components-refrigerants-and-diagnosis`) |
| A bigger AC is safer | ⚠️ **Short-cycles, won't dehumidify, wears out** (§7 → `hvacr-load-calculation-air-humidity-and-heat-pumps`, §9 → `hvacr-load-calculation-air-humidity-and-heat-pumps`) |
| An iced coil means low charge | ⚠️ **Airflow first — filter, coil, blower** (§5 → `hvacr-cycle-components-refrigerants-and-diagnosis`) |
| High-MERV filter is a free upgrade | ⚠️ **Pressure drop cuts airflow. Check ESP** (§10 → `hvacr-load-calculation-air-humidity-and-heat-pumps`) |
| Heat pumps don't work in cold | ⚠️ **Modern cold-climate units do; watch the backup** (§11 → `hvacr-load-calculation-air-humidity-and-heat-pumps`) |
| The heat pump is broken — it's steaming | ⚠️ **That's a defrost cycle** (§11 → `hvacr-load-calculation-air-humidity-and-heat-pumps`) |
| COP over 1 breaks physics | ⚠️ **You're moving heat, not making it** (§11 → `hvacr-load-calculation-air-humidity-and-heat-pumps`) |
| Deep setback saves on a heat pump | ⚠️ **Recovery triggers resistance backup** (§12 → `hvacr-load-calculation-air-humidity-and-heat-pumps`) |
| Cold stops spoilage | ⚠️ **Slows it. Enzymatic and chemical continue** (§14 → `hvacr-cold-chain-temperature-limits-and-validation`) |
| If it stayed cold it's safe | ⚠️ **Listeria grows at fridge temperatures** (§14 → `hvacr-cold-chain-temperature-limits-and-validation`) |
| Freezing kills bacteria | ⚠️ **Makes them dormant** (§16 → `hvacr-cold-chain-temperature-limits-and-validation`) |
| Thaw on the counter | ⚠️ **Surface enters the danger zone. Fridge or cold water** (§16 → `hvacr-cold-chain-temperature-limits-and-validation`) |
| A big pot cools fine in the fridge | ⚠️ **It won't meet the cooling rule. Shallow pans** (§16 → `hvacr-cold-chain-temperature-limits-and-validation`) |
| Colder is always better for produce | ⚠️ **Chilling injury — bananas, tomatoes, basil** (§18 → `hvacr-cold-chain-temperature-limits-and-validation`) |
| A reefer will cool the load down | ⚠️ **It MAINTAINS. Pre-cool before loading** (§19 → `hvacr-cold-chain-temperature-limits-and-validation`) |
| Supply air temperature is the number | ⚠️ **Pulp temperature is** (§19 → `hvacr-cold-chain-temperature-limits-and-validation`, §20 → `hvacr-cold-chain-temperature-limits-and-validation`) |
| Freezer burn is a safety issue | ⚠️ **Sublimation. Quality only; fix the packaging** (§14 → `hvacr-cold-chain-temperature-limits-and-validation`, §17 → `hvacr-cold-chain-temperature-limits-and-validation`) |
| Boiling water canning works for vegetables | ⚠️ **Low-acid REQUIRES pressure canning** (§22 → `hvacr-preservation-water-storage-and-treatment`) |
| Garlic in oil keeps on the shelf | ⚠️ **Anaerobic, low-acid — botulism risk** (§22 → `hvacr-preservation-water-storage-and-treatment`) |
| Vacuum packing makes it shelf-stable | ⚠️ **It selects for anaerobes** (§22 → `hvacr-preservation-water-storage-and-treatment`) |
| Boiling purifies water | ⚠️ **Kills pathogens; CONCENTRATES chemicals** (§24 → `hvacr-preservation-water-storage-and-treatment`) |
| A carbon filter makes water safe | ⚠️ **Taste and organics; not salts or microbes reliably** (§24 → `hvacr-preservation-water-storage-and-treatment`) |
| UV is a complete solution | ⚠️ **No residual, and turbidity shields organisms** (§24 → `hvacr-preservation-water-storage-and-treatment`) |
| A bigger water tank is better | ⚠️ **Stagnation loses residual and grows biofilm** (§23 → `hvacr-preservation-water-storage-and-treatment`) |
| R-410A is banned outright | ⚠️ **Servicing stays legal; manufacture is restricted** (§25.1) |
| A2L is dangerously flammable | ⚠️ **<10 cm/s burning velocity vs >100 for propane** (§25.1) |

---

## §27. Numbers

```
⚠️ DANGER ZONE        5–60°C (41–140°F) · ⚠️ 2-hour / 4-hour rule
⚠️ Refrigeration      ≤5°C (41°F) · ⚠️ Freezer −18°C (0°F)
⚠️ Cooling rule       60→21°C in 2h, then 21→5°C in 4h
⚠️ Hot holding        ≥60°C (140°F) · poultry cooked to 74°C (165°F)
⚠️ Pharma             2–8°C · −20°C frozen · −60 to −80°C ultra-cold
⚠️ Water activity     bacteria stop ~0.91 · moulds ~0.80 · nothing ~0.60
⚠️ Canning pH line    4.6 (⚠️ below = water bath; above = PRESSURE)
⚠️ Respiration rate   roughly doubles per +10°C
⚠️ Indoor RH target   40–60%
⚠️ Evacuation target  ~500 microns with a decay test
⚠️ Boil for water     1 min rolling (⚠️ 3 min at altitude)
⚠️ Emergency water    ~4 L (1 gal) per person per day
⚠️ Legionella growth  ~20–45°C in stagnant water
GWP  ⚠️ R-410A ~2,088 · R-32 ~675 · R-454B ~466 · ⚠️ residential limit 700
⚠️ A2L burning velocity  <10 cm/s (vs >100 cm/s for A3 propane)
⚠️ EU quota          100% (2015 base) → 5% by 2030 · US −85% by 2036
⚠️ R-410A price      reported +40–70% vs 2022
⚠️ Food lost to missing refrigeration  526 Mt ≈ 12% of production (2017)
⚠️ Food cold chain emissions  ~4% of global GHG
```

---

## §28. Books and Standards

| Source | Why |
|---|---|
| **ASHRAE Handbook** (Fundamentals / Refrigeration / HVAC Systems / Applications) | ⚠️ **The reference. Four volumes, one per year of rotation** |
| **ASHRAE 34** | ⚠️ **Refrigerant designation and safety classification** (§3 → `hvacr-cycle-components-refrigerants-and-diagnosis`) |
| **ASHRAE 15** | Safety standard for refrigeration systems |
| **ASHRAE 62.1 / 62.2** | Ventilation (§10 → `hvacr-load-calculation-air-humidity-and-heat-pumps`) |
| **ASHRAE 188** | ⚠️ **Legionella water management** (§10 → `hvacr-load-calculation-air-humidity-and-heat-pumps`, §23 → `hvacr-preservation-water-storage-and-treatment`) |
| **ACCA Manual J / S / D** | ⚠️ **Load, equipment selection, ducts — §7 → `hvacr-load-calculation-air-humidity-and-heat-pumps`, §8 → `hvacr-load-calculation-air-humidity-and-heat-pumps`** |
| **UL 60335-2-40** | ⚠️ **The A2L equipment standard** (§25.1) |
| **Althouse, Turnquist & Bracciano** | *Modern Refrigeration and Air Conditioning* — ⚠️ **the trade standard** |
| **FDA Food Code** | ⚠️ **§16 → `hvacr-cold-chain-temperature-limits-and-validation`'s limits, authoritative** |
| **USDA / NCHFP** | ⚠️ **Tested home preservation recipes — §22 → `hvacr-preservation-water-storage-and-treatment`. Use these, not blogs** |
| **IIR** (International Institute of Refrigeration) | Cold chain technical guidance |
| **WHO / PQS** | ⚠️ **Vaccine cold chain equipment standards** (§21 → `hvacr-cold-chain-temperature-limits-and-validation`) |
| **EPA Section 608 / F-Gas guidance** | ⚠️ **§25.1 — verify current status directly** |

---

## §29. Quick Reference

### 29.1 Diagnostic picker
| Symptom | Where |
|---|---|
| Not cooling enough | ⚠️ **Superheat + subcooling before anything else** (§5 → `hvacr-cycle-components-refrigerants-and-diagnosis`) |
| High superheat, low subcooling | ⚠️ **Undercharge — find the leak** (§5 → `hvacr-cycle-components-refrigerants-and-diagnosis`) |
| Low superheat, high subcooling | ⚠️ **Overcharge** (§5 → `hvacr-cycle-components-refrigerants-and-diagnosis`) |
| Both high | ⚠️ **Restriction** (§5 → `hvacr-cycle-components-refrigerants-and-diagnosis`) |
| Iced evaporator | ⚠️ **Airflow first** (§5 → `hvacr-cycle-components-refrigerants-and-diagnosis`, §8 → `hvacr-load-calculation-air-humidity-and-heat-pumps`) |
| High head pressure | ⚠️ **Dirty condenser, overcharge, non-condensables** (§5 → `hvacr-cycle-components-refrigerants-and-diagnosis`) |
| Cold but clammy building | ⚠️ **Oversized, short-cycling, no dehumidification** (§7 → `hvacr-load-calculation-air-humidity-and-heat-pumps`, §9 → `hvacr-load-calculation-air-humidity-and-heat-pumps`) |
| Some rooms won't condition | ⚠️ **Duct design, ESP, return path** (§8 → `hvacr-load-calculation-air-humidity-and-heat-pumps`) |
| Heat pump bills disappointing | ⚠️ **Resistance backup running. Check controls** (§11 → `hvacr-load-calculation-air-humidity-and-heat-pumps`) |
| Water dripping from the air handler | ⚠️ **Condensate drain or trap** (§9 → `hvacr-load-calculation-air-humidity-and-heat-pumps`) |
| Produce spoiling fast | ⚠️ **Precooling and ethylene separation** (§15 → `hvacr-cold-chain-temperature-limits-and-validation`, §18 → `hvacr-cold-chain-temperature-limits-and-validation`) |
| Load arrived warm | ⚠️ **Was it pre-cooled? Airflow blocked? Door openings?** (§19 → `hvacr-cold-chain-temperature-limits-and-validation`) |
| Frozen product weeping on thaw | ⚠️ **Frozen too slowly, or storage fluctuated** (§17 → `hvacr-cold-chain-temperature-limits-and-validation`) |
| Is this excursion a problem? | ⚠️ **Cumulative time, and MKT for pharma** (§15 → `hvacr-cold-chain-temperature-limits-and-validation`, §20 → `hvacr-cold-chain-temperature-limits-and-validation`) |
| Preserving without a fridge | ⚠️ **Pick a barrier: a_w, pH, heat, oxygen** (§22 → `hvacr-preservation-water-storage-and-treatment`) |
| Is this water safe? | ⚠️ **Match barrier to threat; taste ≠ safe** (§24 → `hvacr-preservation-water-storage-and-treatment`) |

### 29.2 Cold chain checklist
- [ ] ⚠️ **Product AT temperature before loading — the unit maintains** (§19 → `hvacr-cold-chain-temperature-limits-and-validation`)
- [ ] Precooling as fast as possible after harvest (§15 → `hvacr-cold-chain-temperature-limits-and-validation`)
- [ ] ⚠️ **Airflow path unobstructed; load within the red line** (§19 → `hvacr-cold-chain-temperature-limits-and-validation`)
- [ ] Ethylene producers separated from sensitive product (§18 → `hvacr-cold-chain-temperature-limits-and-validation`)
- [ ] ⚠️ **Chilling-injury-sensitive items NOT refrigerated** (§18 → `hvacr-cold-chain-temperature-limits-and-validation`)
- [ ] ⚠️ **Sensors placed where mapping found the worst case** (§20 → `hvacr-cold-chain-temperature-limits-and-validation`)
- [ ] Handoffs and dock time monitored, not just endpoints (§15 → `hvacr-cold-chain-temperature-limits-and-validation`)
- [ ] ⚠️ **Pulp temperature measured, not just supply air** (§19 → `hvacr-cold-chain-temperature-limits-and-validation`)
- [ ] Excursions assessed cumulatively (§15 → `hvacr-cold-chain-temperature-limits-and-validation`, §20 → `hvacr-cold-chain-temperature-limits-and-validation`)

---

## §30. Method

**§1–§24 → `hvacr-cycle-components-refrigerants-and-diagnosis`, `hvacr-load-calculation-air-humidity-and-heat-pumps`, `hvacr-cold-chain-temperature-limits-and-validation`, `hvacr-preservation-water-storage-and-treatment` rests on settled thermodynamics, established trade practice and public-health
standards** — **the vapour-compression cycle, superheat and subcooling diagnosis,
psychrometric humidity control, the FDA Food Code limits, water activity and pH
thresholds, and standard water treatment barriers.** ⚠️ **None of it needed verification;
the botulism pH line and the danger zone are not going to move.**

**Two searches were run in August 2026**, on **the refrigerant transition** and **the cold
chain gap** — ⚠️ **the first because it changes what you can legally install and what
service costs, the second because it reframes §15 → `hvacr-cold-chain-temperature-limits-and-validation` from logistics into food security.**

**Confidence.** **High** in §5 → `hvacr-cycle-components-refrigerants-and-diagnosis`, which is the section I'd most want read. ⚠️ **Superheat and
subcooling are the only way to see inside a sealed system, and the single most useful
correction in this document is that a system does not consume refrigerant — "low on
refrigerant" means a leak, and most such calls are actually airflow problems.**
**High** in §16 → `hvacr-cold-chain-temperature-limits-and-validation` and §22 → `hvacr-preservation-water-storage-and-treatment`'s limits, which are public-health standards with fatal
consequences attached, and I've stated them as rules rather than guidance.

**High** on §25.1's chemistry and direction — **R-410A at GWP ~2,088 replaced by R-32
(~675) and R-454B (~466) against a 700 GWP limit for residential comfort cooling, both
A2L, requiring UL 60335-2-40 equipment and A2L technician certification.** ⚠️ **These
recur consistently across every source.**
⚠️ **But I've flagged a genuine conflict rather than papering over it: sources disagree on
the R-410A INSTALLATION deadline, with several stating a 1 January 2026 ban and at least
one reporting a May 2026 EPA final rule extending the deadline for pre-manufactured
inventory.** **⚠️ Much of this material comes from HVAC vendors, contractors and CMMS
companies with commercial interests in the transition, so I anchored on the parts they all
agree about and marked the rest as reported.** **Verify the installation cut-off against
EPA directly.**

**Moderate** on §25.2's magnitudes, and the caveat is in the section rather than hidden
here. ⚠️ **The 526 Mt / 12% figure comes from a UNEP–FAO report and is repeated widely
because of its source's authority — but a peer-reviewed analysis explicitly notes that FAO
food loss data are inconsistent and uncertain due to evolving definitions and
methodologies, and that projections don't align well with degradation models.**
⚠️ **The robust claims are that the gap is large, concentrated in low-income countries, and
that the emissions trade-off runs both ways — building cold chain emits, and missing cold
chain emits more through lost food.** **The precise tonnage is not independently replicated
and I would not use it as a load-bearing figure in an argument.**
