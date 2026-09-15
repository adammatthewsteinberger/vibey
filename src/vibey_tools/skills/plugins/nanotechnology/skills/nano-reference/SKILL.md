---
name: nano-reference
description: "Use when correcting a nanotechnology misconception, checking a length, energy or magnitude, asking what actually moved (the leading-edge node, verified August 2026, and foundation-model interatomic potentials), finding the books, or needing the core equations, a method picker and a sanity checklist. Companion to the other nanotechnology skills."
---

# Nanotechnology: Misconceptions, Numbers, What Moved, and Canon

> **Part 5 of 5** of the *Nanotechnology* reference (plugin `nanotechnology`), covering §12–§17. Sibling skills: `nano-scaling-laws-and-quantum-effects` (§0–§2), `nano-fabrication-and-semiconductor-process` (§3–§5), `nano-characterization-materials-and-nanomedicine` (§6–§9), `nano-computational-methods-and-safety` (§10–§11). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The physics and fabrication principles are stable; the leading-edge semiconductor node and machine-learned interatomic potentials moved. See §14 below for what actually changed.

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

## §12. Misconceptions

| Claim | Reality |
|---|---|
| "A 2nm chip has 2nm features" | ⚠️ **A generational label, not a measurement. Gate lengths ~12–18 nm** (§5.1 → `nano-fabrication-and-semiconductor-process`) |
| "Moore's Law is dead" | ⚠️ **Density scaling continues; DENNARD scaling died ~2005 — that's the one you felt** (§5.3 → `nano-fabrication-and-semiconductor-process`) |
| "Nanotech means tiny machines with gears" | ⚠️ **Stiction and Brownian motion dominate; macroscale mechanism intuition fails** (§1.2 → `nano-scaling-laws-and-quantum-effects`) |
| "Gravity holds nanostructures together" | ⚠️ **Gravity is irrelevant. Van der Waals and surface tension dominate** (§1.2 → `nano-scaling-laws-and-quantum-effects`) |
| "Gold is inert" | ⚠️ **Excellent catalyst below ~5 nm** (§1.1 → `nano-scaling-laws-and-quantum-effects`) |
| "Melting point is a material constant" | ⚠️ **Depresses sharply with radius. Gold at 2 nm melts near 300 °C** (§1.1 → `nano-scaling-laws-and-quantum-effects`) |
| "Quantum dot colour comes from composition" | ⚠️ **From SIZE. Same material, different colour** (§2.1 → `nano-scaling-laws-and-quantum-effects`) |
| "Graphene will replace silicon transistors" | ⚠️ **No bandgap. Real uses are composites, barriers, sensors** (§7.1 → `nano-characterization-materials-and-nanomedicine`) |
| "Carbon nanotubes are a material" | ⚠️ **(n,m) chirality makes them metallic or semiconducting; bulk synthesis gives a mixture** (§7.1 → `nano-characterization-materials-and-nanomedicine`) |
| "DFT is first-principles, so it's exact" | ⚠️ **The XC functional is an uncontrolled approximation; bandgaps underestimated 30–50%** (§10.2 → `nano-computational-methods-and-safety`) |
| "Standard DFT handles van der Waals" | ⚠️ **It doesn't. Add a dispersion correction** (§10.2 → `nano-computational-methods-and-safety`) |
| "MLIPs replaced DFT" | ⚠️ **They pre-screen. DFT validates. Barriers and stability still need care** (§10.3 → `nano-computational-methods-and-safety`) |
| "Lower benchmark error means a better potential" | ⚠️ **Check energy conservation — some architectures don't conserve** (§10.3 → `nano-computational-methods-and-safety`) |
| "Nanomedicine targets tumours via EPR" | ⚠️ **Robust in rodents, weak and heterogeneous in humans** (§9 → `nano-characterization-materials-and-nanomedicine`) |
| "Our targeting ligand directs the nanoparticle" | ⚠️ **The protein corona is what biology sees** (§9 → `nano-characterization-materials-and-nanomedicine`) |
| "DLS and TEM should agree on size" | ⚠️ **Different measurands. Both can be right** (§6 → `nano-characterization-materials-and-nanomedicine`) |
| "Nanoparticles are as safe as the bulk material" | ⚠️ **Toxicity is not predictable from bulk** (§11 → `nano-computational-methods-and-safety`) |
| "Self-assembly means directing components into place" | ⚠️ **It's thermodynamic minimization, not direction** (§4 → `nano-fabrication-and-semiconductor-process`) |
| "Smaller always means better catalysis" | Sintering and aggregation rise too; there's an optimum (§1.1 → `nano-scaling-laws-and-quantum-effects`) |

---

## §13. Numbers

```
SCALE
Atom 0.1–0.3 nm · C–C bond 0.154 nm · DNA diameter 2 nm · DNA rise 0.34 nm/bp
Protein 2–10 nm · Virus 20–300 nm · Bacterium 1–5 µm · Red blood cell 7 µm
Human hair 50–100 µm · Visible light 400–700 nm
⚠️ Optical diffraction limit ~200 nm · Silicon lattice 0.543 nm

SURFACE FRACTION
100 nm ~1% · 10 nm ~10% · ⚠️ 2 nm ~50% of atoms on surface

QUANTUM
Exciton Bohr radius: CdSe 5.6 nm · PbS 18 nm · Si ~5 nm
Conductance quantum G₀ = 2e²/h ≈ 77.5 µS (12.9 kΩ)
⚠️ Gate oxide direct tunnelling becomes severe below ~2 nm
Thermal energy k_BT at 300 K = 25.7 meV = 4.11×10⁻²¹ J

LITHOGRAPHY
193 nm ArF immersion (NA 1.35) · EUV 13.5 nm (NA 0.33) · High-NA EUV (NA 0.55)
CD = k₁λ/NA · ⚠️ DOF = k₂λ/NA²

TRANSPORT
D = k_BT/6πηr · ⟨x²⟩ = 2Dt (1D) · ⚠️ Re at nanoscale ≈ 10⁻⁵ or less
10 nm particle in water: D ≈ 4×10⁻¹¹ m²/s

SIMULATION
⚠️ MD timestep 1–2 fs · DFT O(N³), practical to ~1000 atoms
MLIP: 10⁵–10⁷ atoms, ns–µs · CCSD(T) O(N⁷)
MOF surface area up to >7000 m²/g · SERS enhancement 10⁸–10¹¹
```

---

## §14. What Actually Moved

### 14.1 The leading-edge node — verified August 2026

**⚠️ Verified directly against TSMC's technology page**, because secondary sources
conflicted:
- **TSMC N2 started volume production in 4Q25**, featuring **first-generation nanosheet
  (GAA) transistors**, plus low-resistance RDL and **super high-performance MiM
  capacitors** in the power delivery network.
- ⚠️ **N2 does NOT include backside power delivery.** TSMC's **A16** is the node that
  "integrates leading nanosheet transistors with innovative backside power rail solution,"
  and **A12** is described as the *second* generation of that backside rail.
  **⚠️ Multiple secondary sources incorrectly attribute backside power to N2P — including
  sources contradicting each other within the same month. Do not trust node feature lists
  that aren't from the foundry.**
- **Intel 18A** pairs **RibbonFET** (its GAA) with **PowerVia** (its backside power),
  taking the more aggressive combined path; **Samsung SF2** is frontside, with the backside
  variant roadmapped later.
- **Reported N2 yields** in the 65–75% range — ⚠️ **these are trade-press figures, not
  foundry disclosures, and yield numbers are among the least reliable public data in this
  industry.**
- ⚠️ **First-generation GAA does not require High-NA EUV.** High-NA is a later
  overlay-and-pitch tool.

**⚠️ The synthesis worth keeping**: 2 nm is **not a single breakthrough but the industrial
integration of GAA nanosheets, advanced EUV, refined metallization, and power-delivery
changes** — and the hard part is **a repeatable line where scanner, mask, resist, etch,
metrology, transistor, interconnect, package and power all agree.**

### 14.2 Foundation-model interatomic potentials
**The genuine methodological shift** (§10.3 → `nano-computational-methods-and-safety`): universal MLIPs trained on large DFT datasets
— **MACE-MP-0** (Materials Project trajectories), **MatterSim** (⚠️ **reported 17 million
DFT-labelled structures**), **CHGNet, GRACE, eSEN, UMA**. **Generative structure models**
(MatterGen, DiffCSP, Chemeleon) propose candidates; ⚠️ **GNoME reported over 2.2 million
new stable materials by combining graph networks with active-learning-driven DFT
validation** — **note that the DFT validation is part of the claim, which is the right
pattern.**

**⚠️ The honest caveats, from the literature itself**: foundation models "do not yet achieve
the accuracy required to predict reaction barriers, phase transitions, and material
stability" without fine-tuning; **direct-force architectures fail to conserve energy in
MD**; and **benchmark rank does not imply physical soundness.** **Fine-tuning tutorials and
frozen-transfer-learning methods are now mature enough to be standard practice.**

---

## §15. Books

| Author | Work | Why |
|---|---|---|
| **Cao & Wang** | *Nanostructures and Nanomaterials* | Solid general reference |
| **Poole & Owens** | *Introduction to Nanotechnology* | Accessible entry |
| **Ozin, Arsenault & Cademartiri** | *Nanochemistry* | ⚠️ **Bottom-up synthesis, excellent** |
| **Israelachvili** | ***Intermolecular and Surface Forces*** | ⚠️ **The book for §1.2 → `nano-scaling-laws-and-quantum-effects` and §4 → `nano-fabrication-and-semiconductor-process`. Indispensable** |
| **Plummer, Deal & Griffin** | *Silicon VLSI Technology* | §3 → `nano-fabrication-and-semiconductor-process`, §5 → `nano-fabrication-and-semiconductor-process` fabrication |
| **Wong & Salahuddin** et al. / **Sze** | *Physics of Semiconductor Devices* | Device physics |
| **Martin** | ***Electronic Structure*** | ⚠️ **DFT done properly (§10.2 → `nano-computational-methods-and-safety`)** |
| **Sholl & Steckel** | *Density Functional Theory: A Practical Introduction* | ⚠️ **The one to actually start with** |
| **Frenkel & Smit** | *Understanding Molecular Simulation* | ⚠️ **The MD and Monte Carlo reference** |
| **Allen & Tildesley** | *Computer Simulation of Liquids* | The classic |
| **Datta** | *Quantum Transport: Atom to Transistor* | §2.2 → `nano-scaling-laws-and-quantum-effects`, and readable |
| **Feynman** | *"There's Plenty of Room at the Bottom"* (1959) | ⚠️ **The founding talk. Twenty minutes, still sharp** |
| **Drexler** | *Engines of Creation* / *Nanosystems* | ⚠️ **Historically important, and its molecular-assembler vision remains contested — read the Smalley-Drexler exchange alongside** |

**Tools and data**: **ASE**, **pymatgen**, **LAMMPS**, **GROMACS**, **Quantum ESPRESSO**
(free), **VASP** (licensed), **MACE** (⚠️ **open, and the easiest entry to foundation
MLIPs**), **Materials Project**, **NOMAD**, **AFLOW**, **OQMD**, **caDNAno** and **oxDNA**
(§8 → `nano-characterization-materials-and-nanomedicine`), **OVITO**.

---

## §16. Quick Reference

### 16.1 Equations
```
S/V = 3/r                              surface-to-volume, sphere
T_m(r) = T_m[1 − 2σ/(ΔH·ρ·r)]          Gibbs-Thomson melting depression
E_n = n²h²/(8mL²)                      particle in a box
T ≈ e^(−2κd)                           tunnelling ⚠️ exponential in distance
G₀ = 2e²/h                             conductance quantum
E_C = e²/2C                            charging energy (Coulomb blockade)
CD = k₁λ/NA · DOF = k₂λ/NA²            lithography ⚠️ resolution vs focus
D = k_BT/(6πηr)                        Stokes-Einstein
⟨x²⟩ = 2Dt                             diffusion
Re = ρvL/µ                             ⚠️ ~10⁻⁵ at nanoscale
d = λ/(2NA)                            Abbe limit ~200 nm
```

### 16.2 Picker
| Need | Use |
|---|---|
| Image surface topography, nm | SEM or AFM (§6 → `nano-characterization-materials-and-nanomedicine`) |
| Image internal structure, atomic | ⚠️ **TEM/STEM — destructive prep** (§6 → `nano-characterization-materials-and-nanomedicine`) |
| Size in suspension | DLS ⚠️ (intensity-weighted) (§6 → `nano-characterization-materials-and-nanomedicine`) |
| Surface composition and oxidation state | XPS (§6 → `nano-characterization-materials-and-nanomedicine`) |
| Conformal coating in a tight gap | ⚠️ **ALD** (§3 → `nano-fabrication-and-semiconductor-process`) |
| Vertical sidewalls | ⚠️ **Plasma/RIE, not wet etch** (§3 → `nano-fabrication-and-semiconductor-process`) |
| Sub-10 nm pattern, prototype | E-beam (⚠️ slow) (§3 → `nano-fabrication-and-semiconductor-process`) |
| 5–50 nm periodic pattern at scale | Block copolymer DSA (§4 → `nano-fabrication-and-semiconductor-process`) |
| Monodisperse nanoparticles | ⚠️ **Separate nucleation from growth** (§4 → `nano-fabrication-and-semiconductor-process`) |
| Electronic structure, ~100s of atoms | DFT (⚠️ pick the functional deliberately) (§10.2 → `nano-computational-methods-and-safety`) |
| Accurate bandgap | ⚠️ **Hybrid or GW — not PBE** (§10.2 → `nano-computational-methods-and-safety`) |
| Layered material or molecular crystal | ⚠️ **DFT + dispersion correction** (§10.2 → `nano-computational-methods-and-safety`) |
| MD at near-DFT accuracy, 10⁵+ atoms | ⚠️ **MLIP, fine-tuned, energy-conserving** (§10.3 → `nano-computational-methods-and-safety`) |
| Rare events beyond µs | Enhanced sampling or kMC (§10.4 → `nano-computational-methods-and-safety`) |
| Nanoscale structural scaffold | ⚠️ **DNA origami** (§8 → `nano-characterization-materials-and-nanomedicine`) |
| Deliver nucleic acid in vivo | ⚠️ **LNP with ionizable lipid** (§9 → `nano-characterization-materials-and-nanomedicine`) |

### 16.3 Sanity checklist
- [ ] Is the node name being read as a dimension? (§5.1 → `nano-fabrication-and-semiconductor-process`)
- [ ] Reporting particle size with the measurement method? (§6 → `nano-characterization-materials-and-nanomedicine`)
- [ ] DFT: cutoff and k-points converged? Functional justified? (§10.2 → `nano-computational-methods-and-safety`)
- [ ] DFT: dispersion correction for a layered/molecular system? (§10.2 → `nano-computational-methods-and-safety`)
- [ ] MLIP: energy-conserving architecture? Fine-tuned for the task? (§10.3 → `nano-computational-methods-and-safety`)
- [ ] MLIP predictions validated by DFT before claiming discovery? (§10.3 → `nano-computational-methods-and-safety`)
- [ ] MD: timestep compatible with the fastest vibration? (§10.4 → `nano-computational-methods-and-safety`)
- [ ] Nanoparticle biology: is EPR being assumed? Corona considered? (§9 → `nano-characterization-materials-and-nanomedicine`)
- [ ] Toxicity claim: size, surface chemistry, agglomeration state reported? (§11 → `nano-computational-methods-and-safety`)
- [ ] Is a macroscale force intuition (gravity, inertia) being applied? (§1.2 → `nano-scaling-laws-and-quantum-effects`)

---

## §17. Method

**§1–§4 → `nano-scaling-laws-and-quantum-effects`, `nano-fabrication-and-semiconductor-process`, §6–§9 → `nano-characterization-materials-and-nanomedicine` and §11 → `nano-computational-methods-and-safety` rest on standard references** — Israelachvili for surface forces,
Ozin for nanochemistry, Plummer for fabrication, Frenkel & Smit and Martin for simulation
theory — **and on physics that has been settled for decades.** ⚠️ **None of that was
web-verified, and none needed to be.**

**Two searches were run in August 2026**, on the two areas that genuinely moved: the
**leading-edge semiconductor node** and **ML interatomic potentials**.

**⚠️ The node section required a primary-source check and it changed the answer.**
Secondary sources contradicted each other on whether N2P carries backside power delivery —
including two sources from the same month asserting opposite things — so I fetched
**TSMC's own technology page**, which states N2 volume production in 4Q25 and attributes
the backside power rail to **A16** (with A12 as its second generation). **§14.1 reflects
the foundry, not the trade press**, and I have flagged the discrepancy rather than silently
picking a side.

**For §10.3 → `nano-computational-methods-and-safety` and §14.2**: the *Journal of Chemical Physics* MACE-MP-0 foundation-model
paper, the *Nature Reviews Chemistry* review of foundation models for atomistic simulation,
*npj Computational Materials* on frozen transfer learning and on GRACE, a 2026 *Advanced
Energy Materials* review for the benchmark and energy-conservation observations, and a 2026
AIP tutorial on fine-tuning universal MLIPs.

**Confidence.** **High** in §1–§9 → `nano-scaling-laws-and-quantum-effects`, `nano-fabrication-and-semiconductor-process`, `nano-characterization-materials-and-nanomedicine` and §11 → `nano-computational-methods-and-safety` — settled physics, with numbers as representative
ranges. **High** in §14.1's TSMC facts (primary source) and in §10.3 → `nano-computational-methods-and-safety`'s methodological
caveats, which come from the peer-reviewed literature and are stated there explicitly
rather than being my inference.

⚠️ **Lower confidence, flagged in place, on two things.** **Yield figures** in §14.1 are
trade-press estimates — **foundries do not disclose yields, and these numbers vary widely
between sources.** And ⚠️ **the GNoME "2.2 million stable materials" figure is a
count of computational predictions with DFT validation, not of synthesized materials** —
the distinction matters enormously and is frequently collapsed in coverage. **§12's
misconception entries about MLIPs and DFT are the ones most likely to save someone a
wasted month.**
