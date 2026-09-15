---
name: biochem-atoms-bonding-and-intermolecular-forces
description: "Use when reasoning about why a substance behaves the way it does at the molecular level: atomic structure and periodic trends and their underlying cause, electronegativity as the master variable, bond types, VSEPR geometry and orbital models, and the intermolecular forces from dispersion through hydrogen bonding that set boiling points, solubility and phase behaviour, plus solutions and colligative properties. Includes the router for the whole biology-chemistry-foundations reference."
---

# Biology and Chemistry Foundations: Atoms, Bonding, and Intermolecular Forces

> **Part 1 of 5** of the *Biology and Chemistry Foundations* reference (plugin `biology-chemistry-foundations`), covering §0–§3. Sibling skills: `biochem-thermodynamics-kinetics-and-equilibrium` (§4–§7), `biochem-organic-chemistry-and-analytical-methods` (§8–§9), `biochem-biomolecules-cells-and-evolution` (§10–§16), `biochem-reference` (§17–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
>    prefer to sit (§1.3, §2).
> 2. **⚠️ ΔG determines direction; kinetics determines whether it happens in your
>    lifetime.** These are independent, and conflating them is the most common error in
>    both chemistry and biology (§4 → `biochem-thermodynamics-kinetics-and-equilibrium`, §5 → `biochem-thermodynamics-kinetics-and-equilibrium`).
> 3. **Life is a kinetically-controlled, thermodynamically-open system.** ⚠️ **Enzymes
>    never change equilibrium — they change the rate of approach to it.** Everything
>    metabolism does is couple unfavourable reactions to favourable ones and keep the
>    system far from equilibrium (§11 → `biochem-biomolecules-cells-and-evolution`, §12 → `biochem-biomolecules-cells-and-evolution`).

---

## §0. Routing

| You want... | Go to |
|---|---|
| **Atoms, periodicity, electron structure** | **§1** |
| Bonding and molecular geometry | §2 |
| Intermolecular forces, phases, solutions | §3 |
| **Thermodynamics and free energy** | **§4 → `biochem-thermodynamics-kinetics-and-equilibrium`** |
| Kinetics and catalysis | §5 → `biochem-thermodynamics-kinetics-and-equilibrium` |
| Equilibrium, acids and bases | §6 → `biochem-thermodynamics-kinetics-and-equilibrium` |
| Redox and electrochemistry | §7 → `biochem-thermodynamics-kinetics-and-equilibrium` |
| **Organic structure and mechanism** | **§8 → `biochem-organic-chemistry-and-analytical-methods`** |
| Analytical methods and spectroscopy | §9 → `biochem-organic-chemistry-and-analytical-methods` |
| Biomolecules | §10 → `biochem-biomolecules-cells-and-evolution` |
| **Enzymes** | **§11 → `biochem-biomolecules-cells-and-evolution`** |
| Bioenergetics and metabolism | §12 → `biochem-biomolecules-cells-and-evolution` |
| Membranes and transport | §13 → `biochem-biomolecules-cells-and-evolution` |
| Cell architecture | §14 → `biochem-biomolecules-cells-and-evolution` |
| Cell cycle and signalling | §15 → `biochem-biomolecules-cells-and-evolution` |
| Evolution | §16 → `biochem-biomolecules-cells-and-evolution` |
| Misconceptions | §17 → `biochem-reference` |
| Numbers | §18 → `biochem-reference` |
| Books and quick reference | §19 → `biochem-reference` |

---

## §1. Atoms and Periodicity

### 1.1 Structure
**Nucleus** (protons, neutrons) + electrons. **Atomic number Z** defines the element;
**isotopes** differ in neutrons. **⚠️ Nearly all the mass is nuclear; nearly all the volume
is electronic** — the nucleus is ~10⁻¹⁵ m against an atom's ~10⁻¹⁰ m.

**Quantum numbers**: `n` (shell, energy), `ℓ` (subshell shape: s, p, d, f), `mℓ`
(orientation), `mₛ` (spin ±½). **Orbital capacity**: s=2, p=6, d=10, f=14.

**Filling rules**: **Aufbau** (lowest energy first), **Pauli exclusion** (no two electrons
share all four quantum numbers), **Hund's rule** (⚠️ **singly occupy degenerate orbitals
with parallel spins before pairing — exchange energy makes this favourable**).

**⚠️ The exceptions that matter**: Cr is `[Ar]3d⁵4s¹` and Cu is `[Ar]3d¹⁰4s¹`, not the
naive `d⁴4s²`/`d⁹4s²` — **half-filled and filled d subshells are unusually stable.**

### 1.2 Periodic trends and their cause

**⚠️ Two competing effects explain every trend: nuclear charge pulling inward, and
shielding plus principal quantum number pushing outward.**

```
                 ← left to right →      ↓ down a group ↓
Atomic radius         decreases              increases
Ionization energy     increases              decreases
Electronegativity     increases              decreases
Metallic character    decreases              increases
```
**Effective nuclear charge** `Z_eff ≈ Z − S` (Slater's rules for S). ⚠️ **Across a period,
Z rises while shielding barely changes — so Z_eff rises and the atom contracts.**

**⚠️ Ionization energy is not monotonic**, and the dips are informative: B < Be (a p
electron is easier to remove than a paired s), and O < N (⚠️ **the fourth p electron must
pair, and pairing costs repulsion energy**).

**⚠️ The lanthanide contraction** — poor f-orbital shielding — makes period-6 elements
smaller than expected, which is why **Zr and Hf are nearly identical in size and famously
hard to separate**, and why the third-row transition metals are dense.

### 1.3 ⚠️ Electronegativity — the master variable
Pauling scale: **F 4.0 > O 3.5 > N ≈ Cl 3.0 > C ≈ S 2.5 > H 2.1 > metals**.
```
ΔEN < 0.4        nonpolar covalent
ΔEN 0.4–1.7      polar covalent
ΔEN > 1.7        ⚠️ largely ionic — but a spectrum, not a category
```
**⚠️ Nearly everything downstream follows from this**: bond polarity → dipole moments →
intermolecular forces → solubility → boiling points → acidity → reaction mechanisms.

---

## §2. Bonding and Geometry

### 2.1 Bond types
**Ionic** (electron transfer, lattice energy `∝ q₁q₂/r` — ⚠️ **which is why MgO melts far
higher than NaCl: doubled charges on both ions**), **covalent** (sharing), **metallic**
(delocalized electron sea), **coordinate/dative** (both electrons from one atom —
⚠️ **the basis of ligand binding and of Lewis acid-base chemistry**).

### 2.2 VSEPR geometry
**Electron domains repel; lone pairs repel more than bonding pairs.**
```
Domains  Electron geometry   Shape (with lone pairs)          Angle
2        linear              linear                            180°
3        trigonal planar     trigonal planar / bent            120°
4        tetrahedral         tetrahedral / trigonal pyramidal / bent   109.5°
5        trigonal bipyramidal  seesaw / T-shape / linear      120°, 90°
6        octahedral          square pyramidal / square planar  90°
```
**⚠️ Lone-pair compression is why water is 104.5°, not 109.5°**, and why NH₃ is 107°.
**In trigonal bipyramidal, lone pairs always occupy equatorial positions** — less repulsion
at 120° than 90°.

### 2.3 Orbital models
**Hybridization**: sp (linear), sp² (trigonal, ⚠️ **leaves an unhybridized p for π
bonding**), sp³ (tetrahedral). **σ bonds** from head-on overlap (rotatable);
**π bonds** from side-on p overlap (⚠️ **rotation breaks them — which is why C=C has
cis/trans isomers and C–C doesn't**).

**⚠️ Molecular orbital theory is what you need when hybridization fails.** Bond order
`= (bonding − antibonding)/2`. **The canonical case: O₂ is paramagnetic** — two unpaired
electrons in π* orbitals. ⚠️ **Lewis structures predict it diamagnetic and are simply
wrong; MO theory gets it right**, and O₂'s biradical character is why it reacts slowly
with organic matter despite enormous thermodynamic favourability.

**Resonance and delocalization**: ⚠️ **the real structure is a single delocalized one, not
a rapid interconversion between forms.** **Aromaticity** requires cyclic, planar, fully
conjugated, and **4n+2 π electrons (Hückel)** — conferring substantial extra stability,
which is why benzene resists addition.

---

## §3. Intermolecular Forces, Phases, Solutions

### 3.1 The forces, weakest to strongest
```
London dispersion   0.05–40 kJ/mol   ⚠️ present in EVERYTHING; scales with
                                      polarizability, i.e. size and electron count
Dipole-dipole       5–25 kJ/mol
Hydrogen bond       10–40 kJ/mol     ⚠️ requires H bonded to N, O or F
Ion-dipole          40–600 kJ/mol    solvation of ions
```
**⚠️ Dispersion forces are routinely dismissed and shouldn't be.** They're why I₂ is a
solid and F₂ a gas, and why long alkanes have higher boiling points than short ones. **In
large molecules, cumulative dispersion can exceed hydrogen bonding.**

**⚠️ Water's anomalies all trace to hydrogen bonding** — high boiling point for its mass,
**high heat capacity** (thermal buffering, biologically critical), high surface tension,
**high heat of vaporization** (evaporative cooling), and ⚠️ **ice being less dense than
liquid**, because the tetrahedral H-bond lattice is more open than the liquid.

### 3.2 Solutions
**"Like dissolves like"** is a statement about matching intermolecular forces.
⚠️ **The hydrophobic effect is not a force** — nonpolar solutes aggregate because doing so
*releases ordered water*, so it is **entropically driven.** **This is the single most
important organizing principle in biological structure** — it drives protein folding,
membrane formation, and micelle assembly (§10 → `biochem-biomolecules-cells-and-evolution`, §13 → `biochem-biomolecules-cells-and-evolution`).

**Colligative properties** depend on particle number, not identity: boiling point elevation
`ΔT_b = i·K_b·m`, freezing point depression `ΔT_f = i·K_f·m`, **osmotic pressure**
`Π = iMRT` (⚠️ **the one that matters physiologically — it's what drives water across
membranes**). **`i` is the van 't Hoff factor** — NaCl gives ~2.

**Henry's law**: `C = k·P` — ⚠️ **gas solubility is proportional to partial pressure**, and
this is the basis of blood gas transport and of decompression sickness.
