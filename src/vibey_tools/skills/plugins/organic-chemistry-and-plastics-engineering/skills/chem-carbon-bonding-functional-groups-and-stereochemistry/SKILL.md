---
name: chem-carbon-bonding-functional-groups-and-stereochemistry
description: "Use for the foundations of organic structure: why carbon supports the chemistry it does, bonding, hybridization and structure, the functional groups and the reactivity each confers, stereochemistry including chirality, enantiomers and why it matters biologically, and acidity and basicity with pKa reasoning as a predictive tool. Includes the router for the whole organic chemistry and plastics reference."
---

# Organic Chemistry and Plastics: Why Carbon, Bonding and Structure, Functional Groups, Stereochemistry, and Acidity and Basicity

> **Part 1 of 6** of the *Organic Chemistry and Plastics Engineering* reference (plugin `organic-chemistry-and-plastics-engineering`), covering §0–§5. Sibling skills: `chem-mechanisms-reactions-characterization-and-synthesis` (§6–§12), `chem-polymers-polymerization-molecular-weight-and-morphology` (§13–§17), `chem-commodity-engineering-plastics-additives-and-processing` (§18–§23), `chem-recycling-bioplastics-and-health-regulation` (§24–§26), `chem-reference` (§27–§32). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
> 1. **⚠️ STRUCTURE DETERMINES PROPERTIES, through mechanism** (§3, §6 → `chem-mechanisms-reactions-characterization-and-synthesis`). **Functional
>    groups are behaviour classes, and reaction "rules" are consequences of electron
>    density and sterics rather than facts to memorize.**
> 2. **⚠️ Tg AND MORPHOLOGY GOVERN PLASTIC BEHAVIOUR more than chemistry does** (§16 → `chem-polymers-polymerization-molecular-weight-and-morphology`).
>    **Whether a polymer is rigid, rubbery, tough or brittle at your service temperature
>    follows from where Tg sits and how much crystallinity there is.**
> 3. **⚠️ Most plastic FAILURES are environmental, not mechanical** (§23 → `chem-commodity-engineering-plastics-additives-and-processing`). **Environmental
>    stress cracking, UV, and additive migration destroy far more parts than overload
>    does — and the load that causes ESC is often well below the design stress.**

---

## §0. Routing

| You want... | Go to |
|---|---|
| Why carbon | §1 |
| Bonding and orbitals | §2 |
| **Functional groups** | **§3** |
| **⚠️ Stereochemistry** | **§4** |
| Acids, bases, pKa | §5 |
| **⚠️ Mechanisms** | **§6 → `chem-mechanisms-reactions-characterization-and-synthesis`** |
| Reaction classes | §7 → `chem-mechanisms-reactions-characterization-and-synthesis` |
| Aromaticity | §8 → `chem-mechanisms-reactions-characterization-and-synthesis` |
| Kinetic vs thermodynamic | §9 → `chem-mechanisms-reactions-characterization-and-synthesis` |
| Characterization | §10 → `chem-mechanisms-reactions-characterization-and-synthesis` |
| Synthesis strategy | §11 → `chem-mechanisms-reactions-characterization-and-synthesis` |
| Green chemistry | §12 → `chem-mechanisms-reactions-characterization-and-synthesis` |
| **What makes a polymer** | **§13 → `chem-polymers-polymerization-molecular-weight-and-morphology`** |
| Polymerization | §14 → `chem-polymers-polymerization-molecular-weight-and-morphology` |
| Molecular weight | §15 → `chem-polymers-polymerization-molecular-weight-and-morphology` |
| **⚠️ Tg and morphology** | **§16 → `chem-polymers-polymerization-molecular-weight-and-morphology`** |
| Mechanical behaviour | §17 → `chem-polymers-polymerization-molecular-weight-and-morphology` |
| Commodity plastics | §18 → `chem-commodity-engineering-plastics-additives-and-processing` |
| Engineering polymers | §19 → `chem-commodity-engineering-plastics-additives-and-processing` |
| **⚠️ Additives** | **§20 → `chem-commodity-engineering-plastics-additives-and-processing`** |
| Elastomers and thermosets | §21 → `chem-commodity-engineering-plastics-additives-and-processing` |
| Processing | §22 → `chem-commodity-engineering-plastics-additives-and-processing` |
| **⚠️ Degradation and ESC** | **§23 → `chem-commodity-engineering-plastics-additives-and-processing`** |
| **⚠️ Recycling honestly** | **§24 → `chem-recycling-bioplastics-and-health-regulation`** |
| Bioplastics honestly | §25 → `chem-recycling-bioplastics-and-health-regulation` |
| Health and migration | §26 → `chem-recycling-bioplastics-and-health-regulation` |
| **What's live** | **§27 → `chem-reference`** |
| Misconceptions, numbers | §28–§29 → `chem-reference` |
| Books, quick ref, method | §30–§32 → `chem-reference` |

---

## §1. Why Carbon

**⚠️ Carbon forms four strong covalent bonds, bonds readily to itself in chains and rings
of essentially unlimited length, and forms stable single, double and triple bonds** —
⚠️ **a combination no other element matches.** **⚠️ Silicon, the usual candidate, forms
weaker Si–Si bonds and its oxide is a solid rather than a gas, which is why silicon
chemistry is mineral chemistry.**
**⚠️ The result is that organic chemistry is a chemistry of STRUCTURE rather than of
composition** — ⚠️ **isomers with identical formulas can be a fuel, a drug and a poison.**
**⚠️ The discipline's shape**: ⚠️ **it is largely about predicting how electron density
moves, and the "rules" are consequences rather than axioms.**

---

# PART I — ORGANIC FUNDAMENTALS

## §2. Bonding and Structure

```
⚠️ HYBRIDIZATION predicts geometry
   sp³  tetrahedral, ~109.5°, ⚠️ FREE ROTATION about single bonds
   sp²  trigonal planar, ~120°, ⚠️ NO ROTATION about the double bond
        — which is why cis/trans isomers exist (§4)
   sp   linear, 180°
⚠️ SIGMA bonds  head-on overlap, strong, rotatable
⚠️ PI bonds  side-on overlap, weaker, ⚠️ and the ELECTRON DENSITY
   ABOVE AND BELOW THE PLANE is what makes alkenes nucleophilic
⚠️ POLARITY  electronegativity differences create dipoles;
   ⚠️ INDUCTIVE effects transmit through sigma bonds and fall off
   with distance; ⚠️ RESONANCE delocalizes through pi systems and
   is usually the stronger effect
⚠️ INTERMOLECULAR FORCES, which govern physical properties
   ⚠️ Hydrogen bonding ≫ dipole-dipole > London dispersion
   ⚠️ Dispersion scales with SURFACE AREA and molecular size —
   which is why long chains have high boiling points and why
   branched isomers boil lower than linear ones
```

---

## §3. Functional Groups

**⚠️ The organizing abstraction of the whole subject: a functional group behaves
approximately the same regardless of the molecule it sits on.**
```
⚠️ HYDROCARBONS  alkane (⚠️ unreactive) · alkene · alkyne · arene (§8)
⚠️ OXYGEN  alcohol · ether (⚠️ inert, hence good solvents) ·
   aldehyde · ketone · ⚠️ CARBOXYLIC ACID · ester (⚠️ often
   pleasant-smelling — flavours and fragrances) · anhydride
⚠️ NITROGEN  amine (⚠️ basic) · amide (⚠️ NOT basic — the lone pair
   is delocalized into the carbonyl. ⚠️ This is why proteins and
   nylons are amides and why they're stable) · nitrile · nitro
SULFUR  thiol (⚠️ odorous, and forms disulfide crosslinks) · sulfide
HALIDES  alkyl and aryl halides
⚠️ THE CARBONYL C=O IS THE CENTRAL MOTIF  ⚠️ polarized, with an
   ELECTROPHILIC carbon. An enormous fraction of organic reactivity
   is nucleophiles attacking carbonyl carbons
```
**⚠️ Nomenclature (IUPAC)** exists because common names don't scale — ⚠️ **but note that
industry runs largely on common and trade names, so both are needed.**

---

## §4. ⚠️ Stereochemistry

> **⚠️ The area where "same molecule" is most misleading, and it has killed people.**
```
⚠️ CONSTITUTIONAL ISOMERS  different connectivity
⚠️ STEREOISOMERS  same connectivity, different arrangement in space
   ⚠️ ENANTIOMERS  non-superimposable mirror images. ⚠️ IDENTICAL
      in every scalar physical property except interaction with
      other chiral things (including polarized light and, crucially,
      BIOLOGY)
   ⚠️ DIASTEREOMERS  stereoisomers that aren't mirror images —
      ⚠️ genuinely different physical properties
⚠️ CHIRAL CENTRE  typically carbon with four different groups
⚠️ R/S nomenclature (Cahn-Ingold-Prelog) · ⚠️ RACEMIC = 50:50 mixture
⚠️ CONFORMATION  rotational arrangements — chair vs boat in
   cyclohexane, and ⚠️ axial vs equatorial substituent preference
```
> **⚠️ GOTCHA — BIOLOGY IS CHIRAL, and this is not a subtlety.** ⚠️ **Enzymes and receptors
> are chiral, so enantiomers can have completely different biological effects: one active,
> one inactive, one differently active, or one toxic.**
> **⚠️ The thalidomide catastrophe is the canonical case — and note the complication that
> is often left out: the enantiomers INTERCONVERT in the body, so selling the single "safe"
> enantiomer would not have prevented it.** ⚠️ **The lesson is stronger than "separate the
> isomers"; it is that stereochemistry must be understood, not just controlled.**
> **⚠️ Regulators now generally require enantiomers to be characterized separately, and
> asymmetric synthesis and chiral resolution are major industrial activities.**

---

## §5. Acidity and Basicity

**⚠️ pKa is the most useful single number in organic chemistry** — ⚠️ **it predicts which
proton comes off, which base is strong enough, and whether a compound is charged at a given
pH.**
**⚠️ What makes an acid strong: STABILITY OF THE CONJUGATE BASE.** ⚠️ **Resonance
delocalization (carboxylic acids), electronegativity, inductive withdrawal by nearby
halogens, and the size of the atom bearing the charge.**
**⚠️ The practical consequence people underuse**: ⚠️ **pH controls charge, charge controls
solubility and partitioning — which is the basis of acid-base extraction, of why drugs are
often formulated as salts, and of how compounds cross membranes.**
**⚠️ Lewis acids and bases** generalize this to electron pair acceptors and donors, ⚠️ **and
that generalization is what makes catalysis intelligible.**
