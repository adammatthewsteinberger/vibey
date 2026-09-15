---
name: biochem-organic-chemistry-and-analytical-methods
description: "Use when working with organic structures or interpreting an analytical result: structure, functional groups, stereochemistry and isomerism, and reaction mechanism as the reasoning that actually transfers rather than a list of named reactions; plus analytical methods and spectroscopy — chromatography, mass spectrometry, NMR, IR and UV-Vis — and what each one can and cannot tell you."
---

# Biology and Chemistry Foundations: Organic Chemistry and Analytical Methods

> **Part 3 of 5** of the *Biology and Chemistry Foundations* reference (plugin `biology-chemistry-foundations`), covering §8–§9. Sibling skills: `biochem-atoms-bonding-and-intermolecular-forces` (§0–§3), `biochem-thermodynamics-kinetics-and-equilibrium` (§4–§7), `biochem-biomolecules-cells-and-evolution` (§10–§16), `biochem-reference` (§17–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Settled science — thermodynamics is 19th century, quantum chemistry and the Michaelis-Menten treatment early 20th, the genetic code and the chemiosmotic hypothesis 1960s. Nothing here has a currency dependency.

> **Scope.** The layer underneath. A biomedical-engineering reference covers imaging,
> signals, PK/PD and clinical statistics; a genetics-and-neuroscience reference covers
> molecular genetics, gene regulation and circuits. **This document is what both of those
> assume you already know** — and it points there rather than repeating.
>
> **⚠️ GOTCHA** boxes mark where the standard teaching account is wrong, or where an
> equation gets applied outside its validity.
>
> **The three ideas that unify everything below:**
> 1. **⚠️ Electronegativity difference drives nearly all of chemistry.** Bonding type,
>    polarity, solubility, acidity, and reaction direction all follow from where electrons
>    prefer to sit (§1.3 → `biochem-atoms-bonding-and-intermolecular-forces`, §2 → `biochem-atoms-bonding-and-intermolecular-forces`).
> 2. **⚠️ ΔG determines direction; kinetics determines whether it happens in your
>    lifetime.** These are independent, and conflating them is the most common error in
>    both chemistry and biology (§4 → `biochem-thermodynamics-kinetics-and-equilibrium`, §5 → `biochem-thermodynamics-kinetics-and-equilibrium`).
> 3. **Life is a kinetically-controlled, thermodynamically-open system.** ⚠️ **Enzymes
>    never change equilibrium — they change the rate of approach to it.** Everything
>    metabolism does is couple unfavourable reactions to favourable ones and keep the
>    system far from equilibrium (§11 → `biochem-biomolecules-cells-and-evolution`, §12 → `biochem-biomolecules-cells-and-evolution`).

---

## §8. Organic Chemistry

### 8.1 Structure and isomerism
**Functional groups** in rough order of oxidation: alkane → alcohol → aldehyde/ketone →
carboxylic acid. Plus amine, amide, ester, ether, thiol, phosphate.

**Isomerism**: constitutional → stereoisomers → **enantiomers** (non-superimposable
mirror images, ⚠️ **identical physical properties except optical rotation and behaviour in
a chiral environment**) and **diastereomers** (different physical properties).
**R/S by Cahn-Ingold-Prelog priority.**

**⚠️ Chirality is biologically decisive because enzymes are chiral.** Nearly all natural
amino acids are **L**; nearly all sugars are **D**. ⚠️ **Two enantiomers of a drug can have
entirely different pharmacology — thalidomide is the notorious case, though it racemizes
in vivo, which is itself the deeper lesson.**

**Conformation**: Newman projections, staggered vs eclipsed, ⚠️ **cyclohexane chair with
axial/equatorial positions — bulky substituents prefer equatorial**, and this controls
reactivity and sugar chemistry.

### 8.2 Mechanism — the reasoning that actually transfers

**⚠️ Almost all organic mechanism reduces to: electrons flow from electron-rich to
electron-poor.** Nucleophile (electron-rich, Lewis base) attacks electrophile
(electron-poor, Lewis acid). **Curly arrows show electron pair movement, always from the
donor.**

**Substitution:**
```
Sɴ1   two steps via carbocation.  Rate = k[substrate]
      ⚠️ Favoured by: 3° substrate, polar protic solvent, weak nucleophile
      ⚠️ RACEMIZATION (planar intermediate attacked from both faces)
Sɴ2   one step, backside attack.  Rate = k[substrate][nucleophile]
      ⚠️ Favoured by: 1° substrate, polar aprotic solvent, strong nucleophile
      ⚠️ INVERSION of configuration (Walden inversion)
```
**⚠️ Carbocation stability 3° > 2° > 1° > methyl** — hyperconjugation and induction — and
this single ordering explains most of Sɴ1/E1 selectivity. **Carbocations rearrange** via
hydride and alkyl shifts, which is a classic exam trap and a real synthetic hazard.

**Elimination**: **E1** (carbocation, with Sɴ1), **E2** (concerted, ⚠️ **requires
anti-periplanar H and leaving group**). **Zaitsev** gives the more substituted alkene;
**Hofmann** the less, with a bulky base.

**Addition** to C=C and C=O: **Markovnikov** (⚠️ **H adds to the carbon with more H's,
because that generates the more stable carbocation — the rule is a consequence, not a
principle**), anti-Markovnikov with radicals.

**Carbonyl chemistry** — the workhorse: nucleophilic addition to aldehydes/ketones,
**nucleophilic acyl substitution** for esters and amides (⚠️ **reactivity order acid
chloride > anhydride > ester > amide, set by leaving-group ability**), enolate chemistry
(aldol, Claisen — ⚠️ **the α-carbon is nucleophilic once deprotonated, and this is how
biology builds carbon chains**).

**Aromatic**: electrophilic aromatic substitution, with ⚠️ **activating groups being
ortho/para-directing and deactivating groups meta-directing — except halogens, which
deactivate but direct ortho/para.**

---

## §9. Analytical Methods and Spectroscopy

| Method | Measures | ⚠️ Key point |
|---|---|---|
| **UV-Vis** | Electronic transitions | ⚠️ **Conjugation shifts λ_max longer. Beer-Lambert `A = εcl`** |
| **IR** | Bond vibrations | ⚠️ **Functional group fingerprint: O–H 3200–3600 broad, C=O ~1700 sharp, N–H ~3300** |
| **¹H NMR** | Proton environments | ⚠️ **Chemical shift (environment), integration (how many), splitting n+1 (neighbours)** |
| **¹³C NMR** | Carbon skeleton | Low natural abundance; usually decoupled |
| **Mass spec** | m/z | ⚠️ **Molecular ion, isotope patterns (Cl 3:1, Br 1:1), fragmentation** |
| **X-ray crystallography** | Electron density | Definitive structure; needs crystals |
| **Chromatography** | Separation | GC, HPLC, TLC — partition between phases |
| **Electrophoresis** | Charge/size separation | SDS-PAGE, isoelectric focusing |

**⚠️ Structure determination in practice is convergent, not single-method**: MS gives
formula, IR gives functional groups, NMR gives connectivity. **No one technique settles
it.**
