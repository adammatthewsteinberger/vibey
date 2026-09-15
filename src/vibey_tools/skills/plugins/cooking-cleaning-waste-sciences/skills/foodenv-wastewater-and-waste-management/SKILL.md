---
name: foodenv-wastewater-and-waste-management
description: "Use when the question is where it all goes: wastewater treatment and its primary, secondary and tertiary stages, the waste hierarchy and what it does and does not prioritize, landfill engineering including liners, leachate and gas capture, recycling assessed honestly against what is actually recovered and what is not, and composting and organics processing."
---

# Cooking, Cleaning and Waste Sciences: Wastewater Treatment, Landfills, Recycling, and Composting

> **Part 4 of 5** of the *Cooking, Cleaning and Waste Sciences* reference (plugin `cooking-cleaning-waste-sciences`), covering §24–§28. Sibling skills: `foodenv-food-science` (§0–§11), `foodenv-food-safety-and-food-service` (§12–§18), `foodenv-cleaning-chemistry` (§19–§23), `foodenv-reference` (§29–§34). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The chemistry and the food-safety thresholds are settled. Two areas are live. See §29 → `foodenv-reference` for recycling economics and EPR, and PFAS in biosolids.

> **⚠️ One domain, three stages: transform the food, clean up after it, deal with what's
> left.** **Complements an agriculture reference (where the food comes from) and a
> chemistry reference (the underlying reactions).**
>
> **⚠️ Two safety items stated up front, because both can kill and both are common:**
> - ⚠️ **NEVER mix bleach with ammonia, or bleach with acids** (§22 → `foodenv-cleaning-chemistry`). **These produce
>   toxic gases in ordinary domestic quantities.**
> - ⚠️ **The food-safety temperatures in §12 → `foodenv-food-safety-and-food-service` are not suggestions.** **They are the output
>   of pathogen destruction curves.**
>
> **⚠️ GOTCHA** boxes mark folklore that is wrong, and things that hurt people.
>
> **The three ideas that organize this document:**
> 1. **⚠️ Cooking is heat transfer plus chemistry, and almost every technique question is
>    really a heat-transfer question** (§2 → `foodenv-food-science`). **Understanding that replaces a hundred
>    memorized rules.**
> 2. **⚠️ Cleaning is chemistry matched to soil type** (§20–§21 → `foodenv-cleaning-chemistry`). **"Stronger cleaner"
>    is usually the wrong answer; "right chemistry" is usually the right one.**
> 3. **⚠️ The waste hierarchy is ordered by actual impact, and public attention is
>    inverted relative to it** (§25). **Recycling gets the attention; reduction and reuse
>    do the work.**

---

## §24. Wastewater Treatment

```
PRELIMINARY  ⚠️ screening and grit removal
PRIMARY      ⚠️ sedimentation. Settles solids, floats grease. ~30% BOD removal
SECONDARY    ⚠️ BIOLOGICAL — activated sludge or trickling filter. Microbes
             consume dissolved organics. ⚠️ THE core of treatment, ~85–95% BOD
TERTIARY     ⚠️ nutrient removal (N and P), filtration, polishing
DISINFECTION chlorine, UV, or ozone before discharge
SLUDGE       ⚠️ thickening, anaerobic digestion (⚠️ produces biogas — many
             plants approach energy self-sufficiency), dewatering → BIOSOLIDS (§29.2)
```
**⚠️ Key metrics**: **BOD (biochemical oxygen demand), COD, TSS, nutrients, pathogens.**
⚠️ **The reason nutrient removal exists: nitrogen and phosphorus discharge causes
eutrophication — algal blooms, then oxygen depletion, then dead zones** (see an
agriculture reference on P runoff).
**⚠️ Combined sewer overflows (CSOs)** — ⚠️ **older cities combine storm and sanitary
sewers, so heavy rain overwhelms capacity and discharges untreated sewage.** **A major
and expensive legacy infrastructure problem.**
> **⚠️ GOTCHA — "flushable" wipes are not, and this is a real infrastructure cost.**
> ⚠️ **They do not disperse like toilet paper; combined with congealed fats and oils they
> form "fatbergs" that block sewers and damage pumps.** **⚠️ Only urine, faeces and toilet
> paper should be flushed** — **and household fats, oils and grease belong in the trash,
> not the drain.**
**⚠️ Septic systems** (decentralized): **tank for settling and anaerobic digestion, then a
drain field for soil treatment.** ⚠️ **Failure modes are drain-field saturation and
clogging; pump the tank on schedule and keep solids and grease out.**

---

## §25. The Waste Hierarchy

**⚠️ Ordered by actual environmental benefit, and public attention is roughly inverted
relative to it:**
```
1. ⚠️ PREVENT / REDUCE   the only tier that avoids the impact entirely
2. ⚠️ REUSE              retains the embodied energy of manufacture
3. RECYCLE               ⚠️ recovers material, spends energy to do it
4. RECOVER               energy from waste (incineration with recovery, digestion)
5. ⚠️ DISPOSE            landfill. The default when the above fail
```
**⚠️ The uncomfortable implication: recycling is the THIRD-best option and it absorbs most
of the public attention and moral energy.** ⚠️ **A reusable item used many times beats a
recyclable one every time, and not producing the item beats both.**
**⚠️ Food waste is the highest-leverage domestic waste stream**, **because it carries the
embodied water, land, fertilizer, labour and transport of the food itself** (see an
agriculture reference) — ⚠️ **so wasting food wastes far more than the food.** **A large
share of household food waste is avoidable through planning, storage and portioning.**
**⚠️ Municipal solid waste composition (US, roughly)**: **organics (food and yard) is the
largest single category at around a third, then paper and cardboard, then plastics, then
metals, glass and textiles.** ⚠️ **Which is why organics diversion (§28) has more tonnage
leverage than plastics recycling does.**

---

## §26. Landfills

**⚠️ A modern sanitary landfill is an engineered containment structure, not a dump.**
```
LINER SYSTEM   ⚠️ compacted clay + geomembrane (HDPE). ⚠️ Liners have finite
               design lives — containment is not permanent, it's managed
LEACHATE       ⚠️ contaminated liquid from percolation. Collected and treated
LANDFILL GAS   ⚠️ roughly 50% METHANE, 50% CO₂ from anaerobic decomposition.
               ⚠️ Collected for flaring or energy — methane is a far more
               potent greenhouse gas than CO₂ over short horizons
DAILY COVER    soil or alternatives; controls vermin, odour, litter
FINAL CAP + POST-CLOSURE CARE  ⚠️ monitoring for decades after closure
```
> **⚠️ GOTCHA — modern landfills are designed to ENTOMB, not to decompose, and this
> surprises people.** ⚠️ **Excavation studies have recovered decades-old newspapers still
> readable and food waste still identifiable.** **The dry, anaerobic, sealed environment
> largely halts decomposition.**
> ⚠️ **This means "biodegradable" and "compostable" labelling is close to meaningless for
> anything landfilled** — **and worse, organic material that DOES decompose there produces
> methane.** **Compostable packaging only delivers its benefit in an actual composting
> facility that accepts it** (§28).

**⚠️ Waste-to-energy incineration** — **substantial volume reduction and energy recovery;
⚠️ requires serious air pollution control (dioxins, mercury, particulates), produces ash
requiring disposal, and is politically contested and expensive to build.** ⚠️ **A genuine
critique worth knowing: WTE plants need a guaranteed waste stream, which can create
institutional resistance to waste reduction.**

---

## §27. ⚠️ Recycling, Honestly

**⚠️ The mechanics first, because they explain most of the frustration:**
```
CURBSIDE → MRF (materials recovery facility) → sort → bale → market → reprocess
⚠️ Single-stream boosts participation and INCREASES contamination
⚠️ Dual-stream / source separation gives cleaner material, lower participation
```
**⚠️ How materials actually differ, which is the part most people don't know:**
```
⚠️ ALUMINIUM   genuinely excellent. Infinitely recyclable, and recycling uses
   a small fraction of the energy of primary production. ⚠️ The best case by far
⚠️ STEEL       excellent, magnetically separable, strong markets
⚠️ PAPER/CARD  good. ⚠️ Fibres shorten each cycle — finite number of loops
⚠️ GLASS       infinitely recyclable in principle; ⚠️ heavy, so transport
   economics are poor, and mixed-colour cullet has limited use
⚠️ PLASTICS    ⚠️ the problem child. #1 PET and #2 HDPE have real markets.
   #3–#7 largely do not. ⚠️ Mostly DOWNCYCLED (bottle → fibre → landfill),
   and polymers degrade with each cycle
```
> **⚠️ GOTCHA — the resin identification code (the number in the triangle) is NOT a
> recyclability symbol, and this is probably the most widespread waste misconception.**
> ⚠️ **It identifies polymer type for sorting.** **Its resemblance to the recycling
> chasing-arrows symbol has misled consumers for decades, and it is a live regulatory
> issue** — **California's SB 343 "truth in labeling" law targets exactly this.**

**⚠️ Wishcycling** — **putting non-recyclable items in the bin hoping they'll be handled —
⚠️ is actively harmful: it contaminates loads, damages equipment, and can send entire
batches to landfill.** **⚠️ The rule is "when in doubt, throw it out," which feels wrong
and is correct.**
**⚠️ The classic MRF-killers**: **plastic bags and film (⚠️ tangle in sorting screens and
shut down lines — return them to store drop-offs instead), tanglers (hoses, cords,
chains), ⚠️ food-contaminated items (greasy pizza box bottoms), small items that fall
through screens, and ⚠️ lithium batteries, which cause serious fires in trucks and
facilities.**
**⚠️ Empty, clean and dry** — **and ⚠️ leave caps on bottles in most modern programs
(guidance changed; check locally).** ⚠️ **Rules are genuinely local — what's accepted
varies by facility, and there is no universal answer.**
**⚠️ Chemical/advanced recycling** — **depolymerization back to feedstock.** ⚠️ **Promising
in principle, and it is currently expensive, energy-intensive and small-scale; treat
claims about it sceptically until yields and energy balances are published.**

---

## §28. Composting and Organics

```
⚠️ C:N RATIO   target roughly 25–30:1. "Browns" (carbon: leaves, cardboard,
   straw) to "greens" (nitrogen: food scraps, grass, manure)
⚠️ MOISTURE    ~50–60% — like a wrung-out sponge
⚠️ OXYGEN      ⚠️ turn it. Anaerobic = odour + methane, and that's the failure
⚠️ TEMPERATURE thermophilic 130–160°F/55–70°C kills pathogens and weed seeds
   ⚠️ Cold composting works but doesn't sanitize
```
**⚠️ Home composting**: **avoid meat, dairy and oils (pests and odour) unless using bokashi
or an in-vessel system; ⚠️ vermicomposting is excellent for food scraps at small scale.**
**Industrial composting** — **windrow, aerated static pile, in-vessel** — ⚠️ **reaches
temperatures and residence times home systems can't, which is why "commercially
compostable" is a distinct and narrower claim than "compostable."**
**⚠️ Anaerobic digestion** — **captures methane as biogas rather than releasing it, and
produces digestate** — ⚠️ **which is why it's often preferable to composting for wet food
waste at municipal scale.**
**⚠️ The recurring failure**: **compostable serviceware in a jurisdiction with no
collection program.** ⚠️ **It goes to landfill, where it doesn't compost (§26) and may
generate methane, while also contaminating the recycling stream if mistaken for plastic.**
