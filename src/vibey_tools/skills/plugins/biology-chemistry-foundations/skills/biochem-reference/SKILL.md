---
name: biochem-reference
description: "Use when correcting a common chemistry or biology misconception, checking a constant, magnitude or physiological value, finding the textbook canon, or needing the core equations and a reasoning checklist for approaching an unfamiliar problem. Companion to the other biology-chemistry-foundations skills."
---

# Biology and Chemistry Foundations: Misconceptions, Numbers, and Canon

> **Part 5 of 5** of the *Biology and Chemistry Foundations* reference (plugin `biology-chemistry-foundations`), covering §17–§20. Sibling skills: `biochem-atoms-bonding-and-intermolecular-forces` (§0–§3), `biochem-thermodynamics-kinetics-and-equilibrium` (§4–§7), `biochem-organic-chemistry-and-analytical-methods` (§8–§9), `biochem-biomolecules-cells-and-evolution` (§10–§16). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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

## §17. Misconceptions

| Claim | Reality |
|---|---|
| "Spontaneous means it happens quickly" | ⚠️ **ΔG < 0 says nothing about rate. Diamond → graphite** (§4.1 → `biochem-thermodynamics-kinetics-and-equilibrium`) |
| "Exothermic reactions are spontaneous" | ⚠️ **Ice melting is endothermic and spontaneous** (§4.1 → `biochem-thermodynamics-kinetics-and-equilibrium`) |
| "ΔG° applies in cells" | ⚠️ **`ΔG = ΔG° + RT ln Q`; cells are far from standard state** (§4.1 → `biochem-thermodynamics-kinetics-and-equilibrium`) |
| "Entropy is disorder" | ⚠️ **Microstate count. The hydrophobic effect breaks the metaphor** (§4.1 → `biochem-thermodynamics-kinetics-and-equilibrium`) |
| "Catalysts drive reactions forward" | ⚠️ **They accelerate both directions. K is unchanged** (§5 → `biochem-thermodynamics-kinetics-and-equilibrium`, §11 → `biochem-biomolecules-cells-and-evolution`) |
| "Enzymes make reactions happen that otherwise couldn't" | ⚠️ **They change rate only** (§11 → `biochem-biomolecules-cells-and-evolution`) |
| "ATP stores energy in a high-energy bond" | ⚠️ **No such thing. Bond breaking costs energy** (§12.1 → `biochem-biomolecules-cells-and-evolution`) |
| "Glucose yields 36–38 ATP" | ⚠️ **~30–32; non-integral H⁺/ATP stoichiometry** (§12.2 → `biochem-biomolecules-cells-and-evolution`) |
| "The hydrophobic effect is a force between nonpolar molecules" | ⚠️ **It's entropic — water reorganization** (§3.2 → `biochem-atoms-bonding-and-intermolecular-forces`) |
| "Oil and water don't mix because they repel" | Same as above (§3.2 → `biochem-atoms-bonding-and-intermolecular-forces`) |
| "Ionic and covalent are distinct categories" | ⚠️ **A continuum set by ΔEN** (§1.3 → `biochem-atoms-bonding-and-intermolecular-forces`) |
| "Lewis structures explain O₂" | ⚠️ **They predict diamagnetic; O₂ is paramagnetic. MO theory required** (§2.3 → `biochem-atoms-bonding-and-intermolecular-forces`) |
| "HF is the strongest hydrohalic acid" | ⚠️ **HI > HBr > HCl > HF — size beats electronegativity** (§6 → `biochem-thermodynamics-kinetics-and-equilibrium`) |
| "Resonance means the molecule flips between forms" | ⚠️ **One delocalized structure** (§2.3 → `biochem-atoms-bonding-and-intermolecular-forces`) |
| "Markovnikov's rule is a fundamental principle" | ⚠️ **A consequence of carbocation stability** (§8.2 → `biochem-organic-chemistry-and-analytical-methods`) |
| "Enantiomers are chemically identical" | ⚠️ **Identical in achiral environments only. Biology is chiral** (§8.1 → `biochem-organic-chemistry-and-analytical-methods`) |
| "Le Chatelier fully cancels the disturbance" | ⚠️ **Partially opposes** (§6 → `biochem-thermodynamics-kinetics-and-equilibrium`) |
| "Water conducts electricity" | Pure water barely does; dissolved ions do |
| "Cell membranes need energy to form" | ⚠️ **Self-assembly is entropically driven** (§13 → `biochem-biomolecules-cells-and-evolution`) |
| "Evolution is progress toward complexity" | ⚠️ **No goal, no direction** (§16 → `biochem-biomolecules-cells-and-evolution`) |
| "Individuals evolve" | ⚠️ **Populations do** (§16 → `biochem-biomolecules-cells-and-evolution`) |
| "A theory is an educated guess" | An explanatory framework supported by evidence (§16 → `biochem-biomolecules-cells-and-evolution`) |
| "Mitochondria are just the powerhouse" | Also apoptosis, Ca²⁺ buffering, biosynthesis (§14 → `biochem-biomolecules-cells-and-evolution`) |
| "Organic means carbon-based and natural" | ⚠️ **Organic chemistry is carbon chemistry; naturalness is irrelevant** |

---

## §18. Numbers

```
CONSTANTS
N_A = 6.022×10²³ · R = 8.314 J/(mol·K) = 0.08206 L·atm/(mol·K)
F = 96,485 C/mol · k_B = 1.381×10⁻²³ J/K · h = 6.626×10⁻³⁴ J·s
Molar volume ideal gas at STP = 22.4 L · K_w = 1.0×10⁻¹⁴ at 25 °C
RT at 25 °C ≈ 2.48 kJ/mol · ⚠️ RT ln10 ≈ 5.7 kJ/mol (one pK unit)

BOND ENERGIES (kJ/mol)
C–C 348 · C=C 614 · C≡C 839 · C–H 413 · C–O 358 · C=O 799
O–H 463 · N–H 391 · ⚠️ Hydrogen bond 10–40 · van der Waals 0.4–4

CHEMISTRY
Electronegativity: F 4.0, O 3.5, N/Cl 3.0, C/S 2.5, H 2.1
pK_a: HCl −7, carboxylic acid ~4.8, H₂CO₃ 6.1, H₂PO₄⁻ 7.2, NH₄⁺ 9.2, alcohol ~16
Water: mp 0 °C, bp 100 °C, ΔH_vap 40.7 kJ/mol, C_p 4.18 J/(g·K), density max at 4 °C

BIOCHEMISTRY
ATP hydrolysis ΔG°′ −30.5 kJ/mol (⚠️ ~−50 in vivo)
NADH → O₂: ΔE°′ ≈ 1.14 V · Glucose complete oxidation −2870 kJ/mol
⚠️ ~30–32 ATP per glucose · NADH ~2.5 ATP · FADH₂ ~1.5 ATP
Diffusion limit 10⁸–10⁹ M⁻¹s⁻¹ · Physiological pH 7.4 (blood), 7.2 (cytosol)
Amino acids 20 · Codons 64 · Peptide bond planar, φ/ψ free
α-helix 3.6 residues/turn · B-DNA 10.5 bp/turn, 2 nm diameter
⚠️ A–T 2 H-bonds, G–C 3

CELL
Bacterium 1–5 µm · Eukaryotic cell 10–100 µm · Mitochondrion 0.5–1 µm
Ribosome 70S (prok) / 80S (euk) · Membrane thickness ~5 nm (⚠️ ~4 nm hydrophobic core)
Resting membrane potential −70 mV · Cytosolic [Ca²⁺] ~100 nM vs 1–2 mM extracellular
```

---

## §19. Books and Quick Reference

### 19.1 Books

| Author | Work | Why |
|---|---|---|
| **Atkins & de Paula** | ***Physical Chemistry*** | ⚠️ **The standard for §4–§7 → `biochem-thermodynamics-kinetics-and-equilibrium`** |
| **Zumdahl** or **Oxtoby** | *Chemical Principles* | General chemistry, well-explained |
| **Clayden, Greeves & Warren** | ***Organic Chemistry*** | ⚠️ **The best organic textbook written. Mechanism-first, and genuinely readable** |
| **Carey & Sundberg** | *Advanced Organic Chemistry* | The graduate reference |
| **Anslyn & Dougherty** | *Modern Physical Organic Chemistry* | Why mechanisms work |
| **Nelson & Cox** | ***Lehninger Principles of Biochemistry*** | ⚠️ **The biochemistry reference** |
| **Berg, Tymoczko & Stryer** | *Biochemistry* | The main alternative; more structural |
| **Alberts et al.** | ***Molecular Biology of the Cell*** | ⚠️ **§14 → `biochem-biomolecules-cells-and-evolution`, §15 → `biochem-biomolecules-cells-and-evolution`, and the foundation of everything cellular** |
| **Campbell & Reece** | *Biology* | The comprehensive survey |
| **Fersht** | *Structure and Mechanism in Protein Science* | ⚠️ **§11 → `biochem-biomolecules-cells-and-evolution` done properly** |
| **Nicholls & Ferguson** | *Bioenergetics* | ⚠️ **§12 → `biochem-biomolecules-cells-and-evolution`'s chemiosmosis, from the authority** |
| **Futuyma & Kirkpatrick** | *Evolution* | §16 → `biochem-biomolecules-cells-and-evolution` |
| **Silberberg** | *Chemistry: The Molecular Nature of Matter and Change* | Strong on visualization |
| **Pauling** | *The Nature of the Chemical Bond* | Historical, and still clarifying |

**Free and primary**: **LibreTexts** (⚠️ **genuinely good, open, and covers all of this**),
**MIT OpenCourseWare**, **PubChem**, **NIST Chemistry WebBook** (⚠️ **thermodynamic data,
authoritative**), **RCSB PDB**, **KEGG** and **Reactome** (pathways), **BRENDA** (enzyme
kinetics), **UniProt**.

### 19.2 Equations
```
ΔG = ΔH − TΔS                       ΔG = ΔG° + RT ln Q
ΔG° = −RT ln K                      ΔG° = −nFE°
S = k_B ln W                        PV = nRT
k = A e^(−Ea/RT)                    t½ = ln2/k  (first order)
pH = pK_a + log([A⁻]/[HA])          K_w = [H⁺][OH⁻]
E = E° − (0.0592/n) log Q           A = εcl
v = V_max[S]/(K_m+[S])              k_cat/K_m  (catalytic efficiency)
Π = iMRT                            C = kP  (Henry)
```

### 19.3 Reasoning checklist
- [ ] Asked about direction (ΔG) or rate (Ea)? ⚠️ **They're independent** (§4 → `biochem-thermodynamics-kinetics-and-equilibrium`, §5 → `biochem-thermodynamics-kinetics-and-equilibrium`)
- [ ] Using ΔG° where actual concentrations matter? (§4.1 → `biochem-thermodynamics-kinetics-and-equilibrium`)
- [ ] Is the "catalyst" being credited with shifting equilibrium? (§5 → `biochem-thermodynamics-kinetics-and-equilibrium`)
- [ ] Electronegativity difference checked before assigning bond type? (§1.3 → `biochem-atoms-bonding-and-intermolecular-forces`)
- [ ] Lone pairs counted in the VSEPR domain count? (§2.2 → `biochem-atoms-bonding-and-intermolecular-forces`)
- [ ] Conjugate base stability considered for acidity? (§6 → `biochem-thermodynamics-kinetics-and-equilibrium`)
- [ ] E°′ (pH 7) or E° (pH 0) for a biological half-reaction? (§7 → `biochem-thermodynamics-kinetics-and-equilibrium`)
- [ ] Carbocation rearrangement possible? (§8.2 → `biochem-organic-chemistry-and-analytical-methods`)
- [ ] Stereochemical outcome: inversion (Sɴ2) or racemization (Sɴ1)? (§8.2 → `biochem-organic-chemistry-and-analytical-methods`)
- [ ] Is [S] ≫ [E] actually true for Michaelis-Menten? (§11 → `biochem-biomolecules-cells-and-evolution`)
- [ ] NADH (catabolic) or NADPH (anabolic)? (§12.2 → `biochem-biomolecules-cells-and-evolution`)

---

## §20. Method

**No searches were run for this document, and none were warranted.** ⚠️ **This is the most
stable material in the collection**: thermodynamics is 19th-century (Gibbs 1876), the
quantum treatment of bonding and the Michaelis-Menten derivation are early 20th
(1913–1931), the peptide-bond and α-helix geometry is Pauling 1951, DNA structure 1953, and
the chemiosmotic hypothesis Mitchell 1961. **Performing currency checks on settled physical
chemistry would be theatre.**

**Sources** are the standard texts named in §19.1 — **Atkins, Clayden, Lehninger, Alberts,
Fersht, Nicholls & Ferguson** — plus the primary results they compile. **Numerical values
in §18 are from standard reference tables** (NIST, CRC-type compilations) and are quoted at
the precision the application needs.

**Scoped to complement**: molecular genetics, gene regulation and neural biology sit in a
genetics-and-neuroscience reference; imaging, signals, PK/PD and clinical statistics in a
biomedical-engineering reference. **This is the layer both of those assume.**

**Confidence: very high throughout.** The equations are standard and stated with their
validity conditions — which is where the actual value is, since ⚠️ **most errors in this
material come from applying a correct equation outside its assumptions** (ΔG° in a cell,
Michaelis-Menten when [E] ≈ [S], ideal gas at high pressure).

⚠️ **Two honest caveats.** **The numbers in §18 are representative values at standard
conditions** — bond energies vary with molecular context, pK_a values shift with solvent
and substitution, and biological figures like ATP yield are estimates whose exact value
depends on assumptions (which is precisely why the 36–38 figure persisted so long). **Treat
them as orientation, not as constants to five figures.** And **§17's entries are teaching
misconceptions**, some of which — "high-energy bond," "entropy is disorder" — persist in
textbooks as deliberate simplifications rather than errors; **I have marked them because
they mislead once you go one level deeper**, not because the people teaching them are
confused.
