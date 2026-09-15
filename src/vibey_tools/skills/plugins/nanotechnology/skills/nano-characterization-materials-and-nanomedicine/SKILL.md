---
name: nano-characterization-materials-and-nanomedicine
description: "Use when identifying, choosing, or applying a nanomaterial: characterization methods (electron microscopy, scanning probe, scattering and spectroscopy) and what each resolves, nanomaterials including carbon allotropes, 2D materials beyond graphene, and nanoparticles and their optical behaviour, DNA nanotechnology and origami, and nanomedicine including drug delivery and the targeting problem."
---

# Nanotechnology: Characterization, Nanomaterials, DNA Nanotechnology, and Nanomedicine

> **Part 3 of 5** of the *Nanotechnology* reference (plugin `nanotechnology`), covering §6–§9. Sibling skills: `nano-scaling-laws-and-quantum-effects` (§0–§2), `nano-fabrication-and-semiconductor-process` (§3–§5), `nano-computational-methods-and-safety` (§10–§11), `nano-reference` (§12–§17). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The physics and fabrication principles are stable; the leading-edge semiconductor node and machine-learned interatomic potentials moved. See §14 → `nano-reference` for what actually changed.

> **Framing.** Written for someone who computes. **§10 → `nano-computational-methods-and-safety` is the section where your existing
> skills apply directly** — computational nanoscience is a simulation and ML problem — and
> **§5 → `nano-fabrication-and-semiconductor-process` is the nanotechnology that produced the hardware you run on.** The rest is the
> physics you need for those two to make sense.
>
> Chemistry foundations (bonding, thermodynamics, intermolecular forces) sit in a
> biology-and-chemistry reference; nanomedicine's biological side in a
> biomedical-engineering reference.
>
> **⚠️ GOTCHA** boxes mark where macroscale intuition actively fails.
>
> **The three scaling facts that generate everything else:**
> 1. **⚠️ Surface-to-volume ratio scales as 1/r.** Shrink something 1000× and surface
>    effects become 1000× more dominant. **This single ratio explains nanoscale catalysis,
>    reactivity, melting-point depression, and why nanoparticles are never inert** (§1.1 → `nano-scaling-laws-and-quantum-effects`).
> 2. **⚠️ Different forces win at different scales.** Gravity scales as `L³`, surface
>    tension as `L¹`, van der Waals as roughly `L¹`. **Below about a micron, gravity is
>    irrelevant and adhesion dominates** — which is why nanoscale assembly is a stiction
>    problem, not a positioning problem (§1.2 → `nano-scaling-laws-and-quantum-effects`).
> 3. **⚠️ Confinement quantizes.** Below the de Broglie wavelength or exciton Bohr radius,
>    energy levels become discrete and **the material's properties become size-dependent
>    while its composition stays fixed** (§2 → `nano-scaling-laws-and-quantum-effects`).

---

## §6. Characterization

**⚠️ The fundamental constraint: you cannot see a nanostructure with light.** Abbe's limit
is `d = λ/(2·NA)` ≈ 200 nm for visible. **Everything below uses electrons, physical probes,
or clever tricks.**

| Method | Resolution | What it gives | ⚠️ Limitation |
|---|---|---|---|
| **SEM** | ~1 nm | Surface topography | ⚠️ **Needs conductive coating; vacuum** |
| **TEM** | ⚠️ **<0.1 nm** | Internal structure, lattice | ⚠️ **Sample must be <100 nm thin — destructive prep** |
| **STEM-EDS/EELS** | atomic | Composition mapped to structure | Beam damage |
| **AFM** | ~0.1 nm vertical | Topography, force, mechanics | ⚠️ **Tip convolution broadens lateral features** |
| **STM** | atomic | Electronic structure | ⚠️ **Conductive samples only** |
| **XRD** | — | Crystal structure, ⚠️ **Scherrer for size** | Needs crystallinity |
| **XPS** | — | ⚠️ **Surface composition and oxidation state, top ~10 nm** | Surface only |
| **DLS** | — | Hydrodynamic size in suspension | ⚠️ **Intensity-weighted — biased toward large particles** |
| **Raman** | ~1 µm | Bonding; ⚠️ **graphene layer count from 2D peak** | Weak signal |
| **Super-resolution optical** (STED, PALM/STORM) | 20–50 nm | ⚠️ **Optical, in living cells** | Needs fluorophores |

**⚠️ Metrology is a genuine bottleneck in manufacturing**, not just a lab concern: you must
measure critical dimensions on billions of features nondestructively and fast. **Optical
scatterometry plus modelling is what's actually used inline** — ⚠️ **which is an inverse
problem, and therefore a computational one.**

**⚠️ The characterization rule**: no single technique is sufficient. **DLS says 50 nm, TEM
says 30 nm — and both are right**, because DLS measures the hydrodynamic diameter including
the solvation shell and ligands, and weights by intensity (`∝ r⁶`). **Report the method
with the number.**

---

## §7. Nanomaterials

### 7.1 Carbon
**Fullerene C₆₀**, **carbon nanotubes** (⚠️ **rolled graphene; the chiral vector (n,m)
determines electronic character — metallic if `n−m` is divisible by 3, otherwise
semiconducting. This is the central fact about CNTs, and it is why bulk-synthesized tubes
are a mixture you must sort**), **graphene** (⚠️ **single layer, linear dispersion near the
Dirac point → massless Dirac fermions, carrier mobility >200,000 cm²/V·s suspended**),
**graphene oxide**, **nanodiamond** (⚠️ **NV centres for quantum sensing and biolabelling**).

**⚠️ Graphene's honest engineering position**: extraordinary intrinsic properties,
**no bandgap** (a fundamental problem for digital logic — you cannot switch it off),
and ⚠️ **properties degrade sharply from lab-scale exfoliated flakes to CVD-grown
large-area films.** **Its real successes are in composites, barriers, and sensors, not the
transistor replacement that was promised in 2004.**

### 7.2 2D materials beyond graphene
**TMDCs** (MoS₂, WSe₂) — ⚠️ **direct bandgap in monolayer, indirect in bulk**, so
monolayers luminesce; usable for transistors. **hBN** (insulating substrate, ⚠️ **atomically
flat and the standard dielectric for 2D device stacks**), phosphorene, MXenes.
**⚠️ Van der Waals heterostructures** — stack arbitrary 2D layers without lattice matching,
and **twist angle becomes a design parameter** (⚠️ **magic-angle bilayer graphene at ~1.1°
shows correlated insulating and superconducting states — "twistronics"**).

### 7.3 Nanoparticles and optics
**Quantum dots** (§2.1 → `nano-scaling-laws-and-quantum-effects`) — displays, bioimaging, photovoltaics.
**⚠️ Plasmonic nanoparticles**: gold and silver support **localized surface plasmon
resonance** — collective electron oscillation — giving intense, **size- and
shape-dependent colour** (⚠️ **which is why medieval stained glass contains gold
nanoparticles; the effect predates the explanation by a millennium**). **Applications**:
SERS (⚠️ **enhancement factors up to 10⁸–10¹¹, enabling single-molecule Raman**),
photothermal therapy, sensing.
**Magnetic nanoparticles** — ⚠️ **superparamagnetic below a critical size (~20 nm for
magnetite): strongly magnetizable in a field, zero remanence out of it, so they don't
aggregate magnetically.** MRI contrast, hyperthermia, separation.
**Nanoporous**: zeolites, MOFs (⚠️ **enormous surface areas, >7000 m²/g reported —
gas storage and separation**), aerogels, mesoporous silica.

---

## §8. DNA Nanotechnology

**⚠️ The insight: DNA base pairing is a programmable, sequence-addressable binding code.**
It is used here as a **structural and information-bearing material**, not for genetics.

**DNA origami** (Rothemund) — a long viral scaffold strand (~7,000 nt M13) folded by
hundreds of short "staple" strands into an arbitrary 2D or 3D shape. ⚠️ **Design is
computational (caDNAno, oxDNA for simulation), assembly is a single thermal anneal, and
yields are high.** **~6 nm addressable resolution.**

**Beyond structure**: **DNA walkers and motors**, **strand-displacement circuits**
(⚠️ **toehold-mediated displacement implements Boolean logic and even neural-network-like
computation in solution — genuinely programmable chemistry**), **DNA data storage**
(⚠️ **theoretical density ~10¹⁸ bytes/mm³ and millennia of stability; the limits are
write cost and random access, not capacity**), and **scaffolds for positioning
nanoparticles, proteins, or fluorophores with nanometre precision.**

**⚠️ Why a software person should care**: this is the one area of nanotechnology where the
design problem is genuinely a compiler problem — **sequence design, secondary-structure
prediction, and thermodynamic optimization** — and the tooling is open.

---

## §9. Nanomedicine

**Drug delivery** — ⚠️ **the dominant real-world nanotech application by revenue.**
- **Liposomes** (Doxil was the first approved nanomedicine), **polymeric nanoparticles**,
  **micelles**, **dendrimers**, **albumin-bound** (Abraxane).
- **⚠️ Lipid nanoparticles** — ionizable lipid, helper lipid, cholesterol, PEG-lipid.
  **The delivery vehicle for mRNA vaccines and for in vivo gene editing** (see a
  genetics-and-neuroscience reference §6.1). ⚠️ **Ionizable rather than cationic is the key
  design choice: neutral at physiological pH (low toxicity), protonated in the acidic
  endosome (drives escape).**

**⚠️ The EPR effect is the field's most important caveat.** Enhanced permeability and
retention — leaky tumour vasculature passively accumulating nanoparticles — was the
founding premise of cancer nanomedicine. **It is real in rodent models and much weaker and
more heterogeneous in human tumours**, and the field's translation record reflects that.
**⚠️ Treat EPR-based targeting claims sceptically.**

**⚠️ The protein corona** is the other underrated problem: **within seconds of entering
blood, a nanoparticle is coated in serum proteins.** **The biological system sees the
corona, not your engineered surface** — which is why in vitro targeting results frequently
fail in vivo. **Active targeting ligands are often buried by it.**

**Biodistribution reality**: ⚠️ **the liver and spleen take the majority of injected
nanoparticles** via the mononuclear phagocyte system. **PEGylation extends circulation but
provokes anti-PEG antibodies and accelerated blood clearance on repeat dosing.**

**Other**: imaging contrast (iron oxide, gold), theranostics, **nanoparticle vaccines**,
antimicrobial silver (⚠️ **and resistance is emerging**), tissue scaffolds.
