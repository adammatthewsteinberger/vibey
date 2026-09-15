---
name: chem-polymers-polymerization-molecular-weight-and-morphology
description: "Use for polymer fundamentals: what makes a polymer different from a small molecule, the polymerization routes and what each controls, molecular weight distributions and why the average alone is misleading, glass transition, melting and morphology including crystallinity, and mechanical behaviour with viscoelasticity, creep and the strain-rate and temperature dependence."
---

# Organic Chemistry and Plastics: What Makes a Polymer, Polymerization, Molecular Weight, Tg, Melting and Morphology, and Mechanical Behaviour

> **Part 3 of 6** of the *Organic Chemistry and Plastics Engineering* reference (plugin `organic-chemistry-and-plastics-engineering`), covering §13–§17. Sibling skills: `chem-carbon-bonding-functional-groups-and-stereochemistry` (§0–§5), `chem-mechanisms-reactions-characterization-and-synthesis` (§6–§12), `chem-commodity-engineering-plastics-additives-and-processing` (§18–§23), `chem-recycling-bioplastics-and-health-regulation` (§24–§26), `chem-reference` (§27–§32). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The chemistry is settled. Two regulatory areas are moving. See §27 → `chem-reference` for the global plastics treaty, and the EU PFAS restriction.

> **⚠️ Two disciplines joined at one hinge: organic chemistry explains what molecules DO,
> and polymer engineering explains what happens when you make them very long.** ⚠️ **Chain
> length changes almost everything — a C₂₀ hydrocarbon is a wax and a C₂₀₀,₀₀₀ one is a
> structural material, with identical chemistry.**
>
> **Complements a manufacturing reference (moulding and processing), a materials/textiles
> reference (fibres and finishing), and a thermodynamics reference (phase behaviour).**
>
> **⚠️ SCOPE NOTE: this is a conceptual map of mechanisms, materials and industrial
> practice. It is not a laboratory manual and contains no procedures.** ⚠️ **Practical
> synthetic work requires trained supervision, proper facilities and hazard assessment —
> organic chemistry involves flammables, toxics, corrosives and exotherms that hurt people
> who improvise.**
>
> **⚠️ GOTCHA** boxes mark where intuition fails and where products actually break.
>
> **The three ideas that organize this document:**
> 1. **⚠️ STRUCTURE DETERMINES PROPERTIES, through mechanism** (§3 → `chem-carbon-bonding-functional-groups-and-stereochemistry`, §6 → `chem-mechanisms-reactions-characterization-and-synthesis`). **Functional
>    groups are behaviour classes, and reaction "rules" are consequences of electron
>    density and sterics rather than facts to memorize.**
> 2. **⚠️ Tg AND MORPHOLOGY GOVERN PLASTIC BEHAVIOUR more than chemistry does** (§16).
>    **Whether a polymer is rigid, rubbery, tough or brittle at your service temperature
>    follows from where Tg sits and how much crystallinity there is.**
> 3. **⚠️ Most plastic FAILURES are environmental, not mechanical** (§23 → `chem-commodity-engineering-plastics-additives-and-processing`). **Environmental
>    stress cracking, UV, and additive migration destroy far more parts than overload
>    does — and the load that causes ESC is often well below the design stress.**

---

## §13. What Makes a Polymer

**⚠️ Long chains of repeating units, and LENGTH is the property-determining variable.**
```
⚠️ ARCHITECTURE  linear · branched (⚠️ branching disrupts packing
   and lowers crystallinity and density) · crosslinked ·
   network · star, comb, dendrimer
⚠️ COPOLYMERS  random · alternating · ⚠️ BLOCK (⚠️ different blocks
   phase-separate at nanoscale, which is how thermoplastic
   elastomers work) · graft
⚠️ TACTICITY  ⚠️ the stereochemical regularity along the chain.
   ⚠️ ISOTACTIC polypropylene crystallizes and is a useful plastic;
   ATACTIC polypropylene is a tacky amorphous material of little
   use. ⚠️ SAME MONOMER, SAME FORMULA, COMPLETELY DIFFERENT
   MATERIAL — and Ziegler-Natta catalysis, which made this
   controllable, won a Nobel
⚠️ THERMOPLASTIC  melts and re-solidifies reversibly; ⚠️ recyclable
   in principle (§24)
⚠️ THERMOSET  ⚠️ irreversibly crosslinked. Does NOT melt.
   ⚠️ Cannot be melt-recycled, which is a lifecycle problem
```
**⚠️ ENTANGLEMENT is why long chains are strong**: ⚠️ **above a critical molecular weight,
chains physically thread through one another, and load transfers between them.** **⚠️ Below
it, the material is a brittle wax.**

---

## §14. Polymerization

```
⚠️ CHAIN-GROWTH (addition)  monomer adds one at a time to an
   active site. ⚠️ High MW polymer exists from the start;
   monomer is consumed steadily
   ⚠️ FREE RADICAL — cheap, tolerant, ⚠️ poor control of structure
   ⚠️ IONIC (anionic/cationic) — better control, demanding conditions
   ⚠️ COORDINATION (Ziegler-Natta, metallocene) — ⚠️ controls
      tacticity and branching. ⚠️ THIS is what made HDPE and
      isotactic PP possible
   ⚠️ CONTROLLED RADICAL (ATRP, RAFT) — ⚠️ block copolymers and
      narrow distributions with radical tolerance
⚠️ STEP-GROWTH (condensation)  any two species with reactive ends
   combine. ⚠️ HIGH MOLECULAR WEIGHT ONLY AT VERY HIGH CONVERSION
   — ⚠️ Carothers' equation shows you need >99% conversion for
   useful chains, which is why STOICHIOMETRIC BALANCE AND PURITY
   ARE CRITICAL in nylon and polyester production
   ⚠️ Also why a monofunctional impurity is a chain terminator
⚠️ PROCESSES  bulk · solution · ⚠️ suspension · emulsion (⚠️ good
   heat control; the basis of latex)
```
**⚠️ Polymerization is strongly EXOTHERMIC** — ⚠️ **heat removal is the central reactor
engineering problem, and runaway is a real industrial hazard.**

---

## §15. Molecular Weight

**⚠️ A polymer sample is a DISTRIBUTION, not a single molecular weight** — ⚠️ **which is
unlike every small molecule and is a persistent source of confusion.**
⚠️ **Mn (number average) weights every chain equally; Mw (weight average) weights by mass
and is therefore always ≥ Mn.** ⚠️ **The DISPERSITY Mw/Mn describes the breadth: near 1.0
for anionic and controlled radical polymerization, around 2 for typical step-growth, and
much broader for some radical and coordination systems.**
**⚠️ Why it matters practically**: ⚠️ **mechanical properties rise with MW and then plateau,
while MELT VISCOSITY keeps rising steeply — roughly with MW to the 3.4 power above the
entanglement threshold.** **⚠️ So there is an optimum: high enough for strength, low enough
to process.** ⚠️ **This trade is why "melt flow index" is a specification.**
**⚠️ Measurement**: **GPC/SEC (⚠️ relative to standards unless coupled to light scattering),
light scattering, viscometry.**

---

## §16. ⚠️ Tg, Melting and Morphology

> **⚠️ THE section. If you understand where Tg sits relative to service temperature and how
> much crystallinity there is, you can predict most of a plastic's behaviour.**
```
⚠️ GLASS TRANSITION Tg  ⚠️ NOT a melting point — it is the
   temperature at which amorphous chain segments gain enough
   mobility to move cooperatively
   ⚠️ BELOW Tg  hard, glassy, ⚠️ BRITTLE
   ⚠️ ABOVE Tg  rubbery or leathery, tough
   ⚠️ THIS IS WHY A PLASTIC PART THAT IS TOUGH IN SUMMER SHATTERS
      IN WINTER — you crossed Tg, and nothing else changed
⚠️ MELTING Tm  only CRYSTALLINE regions melt; ⚠️ amorphous polymers
   have NO Tm at all, they just soften progressively
⚠️ SEMI-CRYSTALLINE  ⚠️ crystalline lamellae in an amorphous matrix,
   organized into spherulites. ⚠️ NO polymer is fully crystalline
   ⚠️ Crystallinity raises stiffness, strength, density, chemical
      resistance and opacity; ⚠️ lowers transparency and toughness
⚠️ WHAT DETERMINES CRYSTALLINITY  ⚠️ chain regularity (tacticity,
   §13) · lack of bulky side groups · cooling rate (⚠️ fast
   cooling suppresses it — which is a PROCESSING variable, so the
   same resin gives different properties depending on mould
   temperature) · nucleating agents
⚠️ RAISING Tg  chain stiffness · aromatic rings (§8) · polar groups ·
   crosslinking · ⚠️ and PLASTICIZERS LOWER IT deliberately (§20)
```
> **⚠️ GOTCHA — the same polymer can be transparent or opaque depending only on how it was
> cooled.** ⚠️ **Spherulites scatter light when they approach its wavelength; quench fast
> enough to suppress crystallization and you get a clear part.** **⚠️ PET does exactly this
> — a clear bottle preform and an opaque crystallized tray from the same resin.**

---

## §17. Mechanical Behaviour

**⚠️ Polymers are VISCOELASTIC — part solid, part liquid, and TIME AND TEMPERATURE ARE
INTERCHANGEABLE in their effect** (time-temperature superposition).
```
⚠️ CREEP  ⚠️ continued deformation under constant load. ⚠️ THE
   distinguishing polymer behaviour, and the reason you cannot
   design a plastic part from a single tensile datasheet number —
   you need creep data at the service temperature and duration
⚠️ STRESS RELAXATION  falling stress at constant strain — ⚠️ why
   plastic snap-fits and bolted joints lose their preload
⚠️ YIELD, DRAWING and NECKING  ⚠️ chains align in the neck, which
   is why drawn fibres are far stronger along the axis
⚠️ TOUGHNESS  ⚠️ crazing (microvoids bridged by fibrils — absorbs
   energy) vs cracking. ⚠️ Rubber toughening works by nucleating
   many small crazes instead of one crack
⚠️ IMPACT  ⚠️ strongly temperature dependent through Tg (§16)
⚠️ FATIGUE  ⚠️ and polymers can fail by HYSTERETIC HEATING —
   internal damping converts cyclic work into heat faster than it
   conducts away, and the part melts rather than cracks
```
