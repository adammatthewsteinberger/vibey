---
name: biochem-biomolecules-cells-and-evolution
description: "Use when working on the biology side: proteins and their folding, nucleic acids, carbohydrates and lipids; enzymes and enzyme kinetics including the Michaelis-Menten treatment and inhibition; bioenergetics and metabolism from ATP coupling through glycolysis, the citric acid cycle and oxidative phosphorylation; membranes and transport; cell architecture and organelles; the cell cycle and signal transduction; and evolution as the organizing principle underneath all of it."
---

# Biology and Chemistry Foundations: Biomolecules, Enzymes, Metabolism, Cells, and Evolution

> **Part 4 of 5** of the *Biology and Chemistry Foundations* reference (plugin `biology-chemistry-foundations`), covering §10–§16. Sibling skills: `biochem-atoms-bonding-and-intermolecular-forces` (§0–§3), `biochem-thermodynamics-kinetics-and-equilibrium` (§4–§7), `biochem-organic-chemistry-and-analytical-methods` (§8–§9), `biochem-reference` (§17–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
>    system far from equilibrium (§11, §12).

---

## §10. Biomolecules

### 10.1 Proteins
**20 amino acids**, all L except glycine (achiral). **Grouped by side chain**: nonpolar,
polar uncharged, acidic (Asp, Glu), basic (Lys, Arg, His), and special (⚠️ **Gly — tiny and
flexible; Pro — ring, a helix-breaker; Cys — forms disulfides**).

**Peptide bond**: amide, ⚠️ **partial double-bond character from resonance, so it is planar
and rotation is restricted — which is why only φ and ψ are free** and why the
Ramachandran plot exists.

**Levels**: primary (sequence) → secondary (**α-helix**: 3.6 residues/turn, H-bond i to
i+4; **β-sheet**: parallel or antiparallel) → tertiary → quaternary.
**⚠️ Folding is driven by the hydrophobic effect** (§3.2 → `biochem-atoms-bonding-and-intermolecular-forces`) — nonpolar residues bury,
polar face solvent — with H-bonds, salt bridges, disulfides, and van der Waals providing
specificity rather than the main driving force.

**⚠️ Levinthal's paradox**: random search of conformational space would take longer than
the universe's age; **folding is funnel-shaped and cooperative**, not a search.

### 10.2 Nucleic acids
**Nucleotide** = base + sugar + phosphate. **Purines (A, G)** two rings, **pyrimidines
(C, T, U)** one. ⚠️ **A–T two hydrogen bonds, G–C three — which is why GC-rich DNA has a
higher melting temperature**, and why primer design cares.
**B-DNA**: right-handed, 10.5 bp/turn, ~2 nm diameter, **antiparallel strands**.
**RNA**: 2′-OH (⚠️ **makes it base-labile and catalytically capable**), uracil, usually
single-stranded with extensive secondary structure.

### 10.3 Carbohydrates and lipids
**Sugars**: aldose/ketose, D/L, ring forms (⚠️ **α/β anomers at the anomeric carbon**),
glycosidic bonds. **Starch/glycogen (α-1,4) is digestible; cellulose (β-1,4) is not** —
⚠️ **a single stereochemical difference separates food from fibre.**

**Lipids**: fatty acids (saturated vs unsaturated — ⚠️ **cis double bonds kink the chain,
lowering melting point and increasing membrane fluidity**), triglycerides,
**phospholipids** (⚠️ **amphipathic — the basis of membranes, §13**), sterols, and
sphingolipids.

---

## §11. Enzymes

**⚠️ Enzymes lower ΔG‡ (§5 → `biochem-thermodynamics-kinetics-and-equilibrium`). They do not change ΔG, K, or equilibrium position.** They
accelerate forward and reverse equally.

**Catalytic strategies**: **proximity and orientation** (⚠️ **a large effective
concentration effect**), **acid-base catalysis**, **covalent catalysis**, **metal ion
catalysis**, **electrostatic stabilization**, and ⚠️ **transition-state stabilization —
which is the deepest one. An enzyme binds the transition state more tightly than the
substrate**, and that differential binding *is* the catalysis. **Transition-state analogues
are therefore potent inhibitors, and this is a real drug-design principle.**

**Michaelis-Menten**:
```
v = V_max[S]/(K_m + [S])            V_max = k_cat[E]_T
K_m = [S] at half V_max             ⚠️ an inverse proxy for affinity, with caveats
k_cat/K_m = catalytic efficiency    ⚠️ the number to compare enzymes by
```
**⚠️ Derived under the quasi-steady-state assumption, requiring [S] ≫ [E]** — routinely
violated inside cells, where many enzymes and substrates are at comparable concentration.

**⚠️ The diffusion limit is ~10⁸–10⁹ M⁻¹s⁻¹**, and enzymes approaching it (triosephosphate
isomerase, catalase, carbonic anhydrase) are called **catalytically perfect** — every
encounter produces reaction, and further improvement is physically impossible.

**Inhibition** — ⚠️ **and the diagnostic pattern is the point:**
```
Competitive       binds active site      K_m ↑   V_max unchanged   (surmountable by [S])
Uncompetitive     binds ES complex       K_m ↓   V_max ↓
Noncompetitive    binds E and ES         K_m —   V_max ↓
Mixed             both, unequally        both change
Irreversible      covalent               ⚠️ V_max ↓, not surmountable
```
**Regulation**: **allostery** (⚠️ **cooperative, sigmoidal kinetics — Hill equation; MWC
and KNF models**), covalent modification (⚠️ **phosphorylation is the dominant switch**),
proteolytic activation (zymogens), and feedback inhibition.

---

## §12. Bioenergetics and Metabolism

### 12.1 ATP and coupling
**ATP hydrolysis ΔG°′ ≈ −30.5 kJ/mol**; ⚠️ **in cells, with actual concentrations, ΔG is
closer to −50 kJ/mol** (§4.1 → `biochem-thermodynamics-kinetics-and-equilibrium` — Q matters).

> **⚠️ GOTCHA — there is no "high-energy phosphate bond."** The energy doesn't reside in
> the bond; it comes from the **whole reaction**: charge repulsion relief in ATP,
> **resonance stabilization of the released phosphate**, and favourable solvation of the
> products. **Bond breaking always costs energy.** The teaching shorthand is actively
> misleading.

**⚠️ ATP is a currency, not a store.** The body turns over roughly its own body weight in
ATP per day while holding only ~50 g at any moment.

### 12.2 The pathways
```
GLYCOLYSIS      glucose → 2 pyruvate | 2 ATP net, 2 NADH | cytosol, anaerobic-capable
                ⚠️ Investment phase costs 2 ATP; payoff yields 4
PYRUVATE OX.    pyruvate → acetyl-CoA | 1 NADH, 1 CO₂ each | ⚠️ irreversible in animals
CITRIC ACID     acetyl-CoA → 2 CO₂ | 3 NADH, 1 FADH₂, 1 GTP per turn
OXIDATIVE PHOS. NADH/FADH₂ → ~2.5 / ~1.5 ATP | ⚠️ ~30–32 ATP per glucose total
```
**⚠️ The old "36–38 ATP" figure is outdated.** Modern estimates are ~30–32, because the
proton-to-ATP stoichiometry isn't integral and transport costs protons.

**⚠️ Chemiosmotic hypothesis (Mitchell, 1961)** — the key insight, and it was resisted for
years: **the electron transport chain pumps protons across the inner mitochondrial
membrane, creating an electrochemical gradient (proton-motive force), and ATP synthase is
a rotary motor driven by proton flow back down it.** **Energy is stored as a gradient, not
as a chemical intermediate.** ⚠️ **Uncouplers (DNP) dissipate the gradient — respiration
continues, ATP synthesis stops, and the energy leaves as heat.**

**Other pathways**: pentose phosphate (⚠️ **NADPH for biosynthesis and ribose for
nucleotides — a different reducing currency from NADH, and the distinction matters**),
β-oxidation, gluconeogenesis (⚠️ **not simply reverse glycolysis — it bypasses the three
irreversible steps**), glycogen metabolism, urea cycle, photosynthesis.

**⚠️ Catabolism is oxidative and uses NAD⁺; anabolism is reductive and uses NADPH.**
Keeping the two pools separate lets a cell run both directions simultaneously.

---

## §13. Membranes and Transport

**Fluid mosaic**: phospholipid bilayer with embedded proteins. **Self-assembly is driven by
the hydrophobic effect** (§3.2 → `biochem-atoms-bonding-and-intermolecular-forces`) — ⚠️ **no energy input required; the bilayer forms because
water's entropy demands it.**

**Fluidity** is modulated by **unsaturation** (⚠️ **cis kinks increase fluidity**), chain
length, and **cholesterol** — ⚠️ **which is a bidirectional buffer: it decreases fluidity
above the transition temperature and increases it below.**

**Permeability, fastest to slowest**: small nonpolar (O₂, CO₂) → small uncharged polar
(H₂O, urea — ⚠️ **water slowly by diffusion, fast through aquaporins**) → large polar →
⚠️ **ions, which are essentially impermeant and require channels.**

```
Passive diffusion       down gradient, no protein, no energy
Facilitated diffusion   down gradient, via channel/carrier, ⚠️ saturable
Primary active          against gradient, direct ATP  (Na⁺/K⁺-ATPase, ⚠️ 3 Na⁺ out : 2 K⁺ in)
Secondary active        against gradient, using another ion's gradient (symport/antiport)
```
**⚠️ Secondary active transport is why the sodium gradient is so valuable** — the Na⁺/K⁺
pump spends ATP to build a gradient that then powers glucose and amino acid uptake, and
Ca²⁺ and H⁺ export. **One pump, many derived transports.**

**Bulk transport**: endocytosis (phagocytosis, pinocytosis, ⚠️ **receptor-mediated via
clathrin**) and exocytosis.

---

## §14. Cell Architecture

**Prokaryote vs eukaryote**: no nucleus/organelles vs compartmentalized; ⚠️ **70S vs 80S
ribosomes — which is exactly why many antibiotics are selectively toxic.**

**Organelles and their function**: nucleus, **rough ER** (⚠️ **co-translational secretory
protein synthesis**), smooth ER (lipids, detox, Ca²⁺ store), **Golgi** (modification and
sorting), lysosome (⚠️ **acidic hydrolases, pH ~4.5**), **peroxisome** (⚠️ **very-long-chain
fatty acid oxidation and H₂O₂ handling**), **mitochondrion** (§12), chloroplast,
cytoskeleton.

**Cytoskeleton**: **microfilaments (actin, 7 nm)** — motility, cytokinesis, myosin motors;
**intermediate filaments (10 nm)** — ⚠️ **mechanical strength only, no motors**;
**microtubules (25 nm)** — ⚠️ **dynamic instability, tracks for kinesin (plus-end) and
dynein (minus-end), and the mitotic spindle.**

**⚠️ Endosymbiotic theory** for mitochondria and chloroplasts — the evidence is unusually
strong: **double membrane, own circular DNA, 70S ribosomes, binary fission, and
phylogenetic placement within bacteria.**

---

## §15. Cell Cycle and Signalling

**Cycle**: G1 → S (replication) → G2 → M. **G0** as quiescence.
**Control**: **cyclins and CDKs** (⚠️ **cyclin concentration oscillates; CDK is
constitutive — the cyclin is the timer**), checkpoints at G1/S (⚠️ **restriction point —
commitment**), G2/M, and spindle assembly.
**⚠️ p53 is "the guardian of the genome"** — DNA damage → arrest, repair, or apoptosis;
**and it is the most commonly mutated gene in human cancer.**

**Mitosis** (PMAT) vs **meiosis** — ⚠️ **two divisions, and the genetic variety comes from
crossing over in prophase I plus independent assortment in metaphase I.**

**Apoptosis** — controlled, non-inflammatory; caspase cascade; intrinsic (mitochondrial,
cytochrome c release) and extrinsic (death receptor) pathways. ⚠️ **Contrast necrosis:
uncontrolled, lytic, inflammatory.**

**Signalling**: ligand → receptor → transduction → response.
**Receptor classes**: **GPCR** (⚠️ **the largest class and the target of ~a third of
approved drugs** — G protein, second messengers cAMP/IP₃/DAG), **receptor tyrosine
kinase** (⚠️ **dimerization → autophosphorylation → MAPK, PI3K cascades — and the central
oncogenic pathway**), **ion channel receptors** (fast, §13), **nuclear receptors**
(⚠️ **lipophilic ligands cross the membrane; the receptor is a transcription factor —
slow and direct**).

**⚠️ Why cascades**: amplification (one ligand → many molecules of response), integration
of multiple inputs, and opportunities for regulation at every tier.

---

## §16. Evolution

**Mechanisms**: **natural selection** (⚠️ **requires only variation, heritability, and
differential reproduction — it follows necessarily from those three**), **drift**
(⚠️ **dominant in small populations, and neutral theory says most molecular change is
drift**), gene flow, mutation, non-random mating. **Mathematics in a
genetics-and-neuroscience reference §4.**

**Speciation**: allopatric (geographic), sympatric, parapatric; reproductive isolation
pre- and post-zygotic.

**Evidence**: fossils, ⚠️ **molecular phylogeny — the concordance of independently-derived
gene trees is the strongest single line**, homology vs analogy, vestigial structures,
biogeography, and **observed evolution** (antibiotic resistance, industrial melanism).

**⚠️ Common misreadings worth correcting**: evolution has no goal or direction;
"survival of the fittest" means reproductive success, not strength; ⚠️ **individuals do not
evolve — populations do**; and a **theory** in science is an explanatory framework, not a
guess.

**Phylogenetics**: parsimony, maximum likelihood, Bayesian; ⚠️ **the molecular clock is
approximate and rate-variable across lineages and genes** — calibrate it or don't use it.
