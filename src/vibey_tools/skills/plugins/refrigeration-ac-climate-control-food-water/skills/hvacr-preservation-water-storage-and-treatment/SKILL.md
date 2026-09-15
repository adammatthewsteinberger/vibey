---
name: hvacr-preservation-water-storage-and-treatment
description: "Use when refrigeration is not available or the question is water: preservation without refrigeration including drying, salting, curing, fermentation, canning and water activity together with the safety limits that go with them, water storage and what degrades stored water, and water treatment — filtration, disinfection, boiling and chemical treatment — and what each does and does not remove."
---

# Refrigeration and Climate Control: Preservation Without Refrigeration, Water Storage, and Water Treatment

> **Part 4 of 5** of the *Refrigeration, AC, Climate Control and Food/Water Storage* reference (plugin `refrigeration-ac-climate-control-food-water`), covering §22–§24. Sibling skills: `hvacr-cycle-components-refrigerants-and-diagnosis` (§0–§6), `hvacr-load-calculation-air-humidity-and-heat-pumps` (§7–§13), `hvacr-cold-chain-temperature-limits-and-validation` (§14–§21), `hvacr-reference` (§25–§30). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The thermodynamics is permanent. Two areas moved. See §25 → `hvacr-reference` for the refrigerant transition, and cold chain capacity and food loss.

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
> specific tooling and training (§25.1 → `hvacr-reference`); ammonia is toxic; and the food temperature limits
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
> 3. **⚠️ Preservation is about denying microbes ONE of their requirements** (§22).
>    **Temperature is only one option; water activity, pH, oxygen and competition are the
>    others, and the durable methods stack several.**

---

## §22. ⚠️ Preservation Without Refrigeration

**⚠️ Microbes need water, a tolerable pH, nutrients, a temperature range and (often)
oxygen. Deny any one and you preserve; deny several and you preserve robustly.**
```
⚠️ WATER ACTIVITY (a_w)  ⚠️ the master variable — availability of water,
   not total water content. ⚠️ Most bacteria stop below ~0.91, most
   moulds below ~0.80, and ⚠️ below ~0.60 essentially nothing grows.
   Drying, salting and sugaring all work by lowering a_w
⚠️ pH  ⚠️ below 4.6 prevents Clostridium botulinum growth — THE
   dividing line in canning. Fermentation and acidification exploit it
⚠️ HEAT  pasteurization (reduces) vs sterilization (eliminates)
   ⚠️ LOW-ACID foods (pH >4.6) REQUIRE PRESSURE CANNING — boiling
   water does not reach the temperature needed to destroy botulinum
   spores. ⚠️ This is a fatal-consequence rule, not a preference
⚠️ OXYGEN  vacuum packing, MAP (§18) ⚠️ — but note anaerobic packaging
   SELECTS FOR anaerobes, which is why vacuum-packed low-acid foods
   still need refrigeration
⚠️ COMPETITION  fermentation establishes benign organisms that crowd out
   pathogens and drop the pH
CURING  nitrite (⚠️ specifically inhibits botulinum, and gives cured
   meat its colour), smoke, salt
IRRADIATION · high-pressure processing (⚠️ non-thermal, preserves fresh
   qualities) · preservatives
```
> **⚠️ GOTCHA — the two home-preservation rules with fatal consequences.** ⚠️ **First:
> low-acid foods (vegetables, meats, most soups) MUST be pressure canned; a boiling water
> bath cannot reach 116–121°C and botulinum spores survive it.** **⚠️ Second: garlic or
> herbs in oil at room temperature is an anaerobic, low-acid environment — a textbook
> botulism risk.** **⚠️ Refrigerate and use quickly, or acidify.** **Follow tested recipes
> from a recognized authority rather than improvising ratios.**

---

# PART IV — WATER

## §23. Water Storage

**⚠️ Materials**: **food-grade HDPE, stainless, concrete, lined steel** — ⚠️ **and opaque
containers, because light drives algal growth.**
**⚠️ The three storage failure modes**: ⚠️ **stagnation (which enables biofilm and
Legionella — §10 → `hvacr-load-calculation-air-humidity-and-heat-pumps`), contamination through openings (⚠️ vents and overflows need insect
screens and should be inverted), and thermal cycling (⚠️ warm water accelerates
everything).**
**⚠️ Turnover matters more than capacity**: ⚠️ **an oversized tank with low demand stagnates
and loses disinfectant residual** — **which is a real and counterintuitive problem in
municipal storage design.**
**⚠️ Emergency storage**: **a common planning figure is roughly 4 litres (1 gallon) per
person per day, ⚠️ with more in hot climates or for medical needs; rotate stored water;
⚠️ and store away from petroleum products and pesticides, since some plastics are
permeable to vapours.**

---

## §24. Water Treatment

```
⚠️ THE BARRIERS, and multiple barriers is the design principle
  ⚠️ FILTRATION  by pore size — ⚠️ sediment → microfiltration (bacteria,
     protozoa) → ultrafiltration (viruses) → nanofiltration → RO (ions).
     ⚠️ A filter rated for bacteria does NOT remove viruses
  ⚠️ DISINFECTION
     ⚠️ CHLORINE  effective, leaves a RESIDUAL (⚠️ the key advantage —
        it keeps working through the distribution system).
        ⚠️ Poor against Cryptosporidium
     ⚠️ UV  excellent against Crypto and Giardia, ⚠️ NO residual, and
        ⚠️ requires clear water — turbidity shields organisms
     OZONE  powerful, no residual, forms bromate in some waters
     ⚠️ BOILING  ⚠️ a rolling boil for 1 minute (3 at high altitude) kills
        pathogens — and does NOT remove chemical contaminants; it
        CONCENTRATES them
  ⚠️ ADSORPTION  activated carbon for taste, odour, chlorine, many organics.
     ⚠️ Does NOT remove salts or most heavy metals, and ⚠️ a saturated
     carbon filter becomes a bacterial substrate
```
**⚠️ Match the treatment to the threat**: ⚠️ **microbial, chemical, and particulate hazards
need different barriers, and the most common consumer error is assuming a filter that
improves taste has made water microbiologically safe.**
**⚠️ Distribution**: ⚠️ **maintain positive pressure (a pressure loss allows backflow and
intrusion), prevent cross-connections with backflow preventers, and ⚠️ dead legs are where
biofilm lives.**
**⚠️ Note the lead pathway**: ⚠️ **lead comes from service lines and solder, not the source
water, and it mobilizes when water chemistry changes** — **which is the mechanism behind
several well-known municipal failures.**
