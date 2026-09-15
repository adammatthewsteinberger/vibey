---
name: chem-mechanisms-reactions-characterization-and-synthesis
description: "Use for reactivity and how compounds are made and identified: mechanisms as the organising principle including arrow pushing and intermediates, the major reaction classes, aromaticity and its consequences, kinetic versus thermodynamic control, characterization by NMR, IR and mass spectrometry, synthesis strategy and retrosynthetic thinking, and green chemistry."
---

# Organic Chemistry and Plastics: Mechanisms, Reaction Classes, Aromaticity, Kinetic Versus Thermodynamic Control, Characterization, Synthesis Strategy, and Green Chemistry

> **Part 2 of 6** of the *Organic Chemistry and Plastics Engineering* reference (plugin `organic-chemistry-and-plastics-engineering`), covering §6–§12. Sibling skills: `chem-carbon-bonding-functional-groups-and-stereochemistry` (§0–§5), `chem-polymers-polymerization-molecular-weight-and-morphology` (§13–§17), `chem-commodity-engineering-plastics-additives-and-processing` (§18–§23), `chem-recycling-bioplastics-and-health-regulation` (§24–§26), `chem-reference` (§27–§32). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
> 1. **⚠️ STRUCTURE DETERMINES PROPERTIES, through mechanism** (§3 → `chem-carbon-bonding-functional-groups-and-stereochemistry`, §6). **Functional
>    groups are behaviour classes, and reaction "rules" are consequences of electron
>    density and sterics rather than facts to memorize.**
> 2. **⚠️ Tg AND MORPHOLOGY GOVERN PLASTIC BEHAVIOUR more than chemistry does** (§16 → `chem-polymers-polymerization-molecular-weight-and-morphology`).
>    **Whether a polymer is rigid, rubbery, tough or brittle at your service temperature
>    follows from where Tg sits and how much crystallinity there is.**
> 3. **⚠️ Most plastic FAILURES are environmental, not mechanical** (§23 → `chem-commodity-engineering-plastics-additives-and-processing`). **Environmental
>    stress cracking, UV, and additive migration destroy far more parts than overload
>    does — and the load that causes ESC is often well below the design stress.**

---

## §6. ⚠️ Mechanisms

> **⚠️ The single most important shift in learning this subject: stop memorizing reactions
> and start tracking electrons.**
```
⚠️ CURLY ARROWS represent MOVEMENT OF ELECTRON PAIRS, always from
   a source of electron density to an electron-poor site
⚠️ NUCLEOPHILE  electron-rich, attacks
⚠️ ELECTROPHILE  electron-poor, is attacked
⚠️ INTERMEDIATES  carbocation (⚠️ stability: tertiary > secondary >
   primary, because alkyl groups donate density) · carbanion ·
   radical · carbene
⚠️ TRANSITION STATE vs INTERMEDIATE  ⚠️ a transition state is a
   maximum on the energy path and cannot be isolated; an
   intermediate sits in a well and sometimes can
⚠️ THE FOUR QUESTIONS FOR ANY MECHANISM
   ⚠️ Where is the electron density? Where is it poor?
   ⚠️ What intermediate forms, and is it stable enough?
   ⚠️ What does sterics allow?
   ⚠️ Is this under kinetic or thermodynamic control? (§9)
```
**⚠️ The canonical contrast worth internalizing**: ⚠️ **SN1 (two steps via a carbocation,
rate depends only on substrate, racemizes) versus SN2 (one step, backside attack, rate
depends on both, INVERTS configuration).** **⚠️ Which one occurs is decided by substrate
substitution, nucleophile strength and solvent — and that reasoning generalizes across the
subject.**

---

## §7. Reaction Classes

```
SUBSTITUTION  one group replaces another (SN1/SN2, aromatic §8)
⚠️ ADDITION  across a multiple bond. ⚠️ Markovnikov's rule is a
   CONSEQUENCE of carbocation stability, not an arbitrary rule
ELIMINATION  forms a multiple bond (E1/E2); ⚠️ competes with
   substitution, and temperature and base bulk decide
⚠️ REDOX  ⚠️ in organic chemistry, oxidation ≈ gaining bonds to O
   or losing bonds to H. ⚠️ The alcohol → aldehyde → carboxylic
   acid ladder is the reference sequence
⚠️ CARBONYL CHEMISTRY  nucleophilic addition (aldehydes/ketones)
   vs ⚠️ nucleophilic ACYL SUBSTITUTION (esters, amides, acid
   chlorides — because there's a leaving group)
⚠️ PERICYCLIC  concerted, orbital-symmetry-controlled —
   Diels-Alder being the workhorse
⚠️ CATALYSIS  acid/base · ⚠️ transition-metal cross-coupling
   (⚠️ Suzuki, Heck and relatives transformed synthesis and won
   a Nobel) · organocatalysis · enzymes
```

---

## §8. Aromaticity

**⚠️ Hückel's rule**: ⚠️ **cyclic, planar, fully conjugated systems with 4n+2 pi electrons
are unusually stable.** **⚠️ Benzene's stabilization is why it resists addition and
undergoes SUBSTITUTION instead.**
**⚠️ Electrophilic aromatic substitution** and ⚠️ **the directing effects — activating
groups direct ortho/para, deactivating groups generally direct meta — which follow from
resonance stabilization of the intermediate rather than from a table to memorize.**
**⚠️ Heteroaromatics** (pyridine, furan, thiophene, imidazole) ⚠️ **are everywhere in
pharmaceuticals and dyes.**
**⚠️ Aromatic rings in polymers** raise Tg and thermal stability — ⚠️ **which is exactly why
the high-performance plastics in §19 → `chem-commodity-engineering-plastics-additives-and-processing` are full of them.**

---

## §9. Kinetic vs Thermodynamic Control

**⚠️ The distinction that explains why the same reactants give different products under
different conditions.**
⚠️ **KINETIC control gives the product that forms FASTEST (lowest activation barrier) —
favoured at low temperature and short times.** ⚠️ **THERMODYNAMIC control gives the MOST
STABLE product — favoured at higher temperature and longer times, where the reaction is
reversible.**
**⚠️ Reaction coordinate diagrams** make this visible, and ⚠️ **Hammond's postulate connects
transition state structure to whether the step is exothermic or endothermic.**
**⚠️ Catalysts lower activation energy and do NOT change the equilibrium position** —
⚠️ **they change how fast you get there, in both directions equally.**

---

## §10. Characterization

**⚠️ How anyone knows what they actually made**:
```
⚠️ NMR  ⚠️ the workhorse. ¹H and ¹³C. ⚠️ Chemical shift tells you
   the electronic environment; INTEGRATION counts protons;
   SPLITTING reveals neighbours. 2D methods connect the pieces
⚠️ IR  functional group identification (⚠️ the C=O stretch is
   diagnostic and its exact position distinguishes ketone from
   ester from amide)
⚠️ MASS SPECTROMETRY  molecular weight and, at high resolution,
   ⚠️ molecular FORMULA. Fragmentation gives structure clues
⚠️ UV-VIS  conjugation and chromophores
⚠️ X-RAY CRYSTALLOGRAPHY  ⚠️ definitive 3D structure including
   absolute stereochemistry — when you can grow a crystal
CHROMATOGRAPHY  TLC, column, HPLC, GC — ⚠️ separation and purity
```
**⚠️ The professional habit**: ⚠️ **no single technique is conclusive; structures are
assigned from converging evidence.**

---

## §11. Synthesis Strategy

**⚠️ RETROSYNTHESIS** — ⚠️ **work BACKWARDS from the target, disconnecting bonds at points
where a known reaction could have formed them, until you reach available starting
materials.** **⚠️ Corey formalized this and it won a Nobel.**
**⚠️ The recurring strategic problems**: ⚠️ **PROTECTING GROUPS (temporarily masking a
reactive group, and every protection costs two steps); CHEMOSELECTIVITY (reacting one group
in the presence of others); REGIOSELECTIVITY (which position); and STEREOSELECTIVITY
(§4 → `chem-carbon-bonding-functional-groups-and-stereochemistry`).**
**⚠️ YIELD COMPOUNDS BRUTALLY**: ⚠️ **ten steps at 90% each gives about 35% overall.**
**⚠️ This is why CONVERGENT synthesis — building fragments separately and joining them
late — beats a long linear sequence, and it is a genuinely general design principle.**
**⚠️ Scale-up is a different discipline**: ⚠️ **heat transfer, mixing, exotherm control and
cost dominate, and a route that is elegant at milligram scale can be unworkable at tonne
scale.**

---

## §12. Green Chemistry

**⚠️ The twelve principles**, ⚠️ **of which the practically dominant ones are ATOM ECONOMY
(what fraction of reactant mass ends up in the product), solvent choice (⚠️ solvent is
usually the largest mass contributor and the largest waste stream), catalysis over
stoichiometric reagents, and energy efficiency.**
**⚠️ The E-FACTOR** — ⚠️ **kilograms of waste per kilogram of product — is the metric that
exposed how wasteful fine chemical and pharmaceutical synthesis is compared with bulk
chemicals.**
**⚠️ Flow chemistry** improves heat and mass transfer and safety, ⚠️ **particularly for
hazardous intermediates that are never accumulated.**
**⚠️ Biocatalysis** — ⚠️ **enzymes give exquisite selectivity under mild conditions, and
directed evolution made engineering them practical.**

---

# PART II — POLYMERS
