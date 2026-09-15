---
name: nano-computational-methods-and-safety
description: "Use when simulating nanoscale systems or assessing their risk: the computational method ladder, density functional theory and what you need to know to use it honestly, machine-learned interatomic potentials as the genuine recent change, molecular dynamics and multiscale modelling, and nanoparticle safety, toxicology and environmental behaviour."
---

# Nanotechnology: Computational Nanoscience and Safety

> **Part 4 of 5** of the *Nanotechnology* reference (plugin `nanotechnology`), covering §10–§11. Sibling skills: `nano-scaling-laws-and-quantum-effects` (§0–§2), `nano-fabrication-and-semiconductor-process` (§3–§5), `nano-characterization-materials-and-nanomedicine` (§6–§9), `nano-reference` (§12–§17). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The physics and fabrication principles are stable; the leading-edge semiconductor node and machine-learned interatomic potentials moved. See §14 → `nano-reference` for what actually changed.

> **Framing.** Written for someone who computes. **§10 is the section where your existing
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

## §10. Computational Nanoscience

**⚠️ This is where a computational background applies directly, and the field is
fundamentally a multiscale simulation problem.**

### 10.1 The method ladder
```
Method              Length        Time         Accuracy      Cost
Quantum Monte Carlo  ~10 atoms    —            ⚠️ benchmark   brutal
CCSD(T)              ~50 atoms    —            "gold std"    ⚠️ O(N⁷)
DFT                  100s–1000s   ps           good-ish      ⚠️ O(N³)
Tight binding        10⁴–10⁵      ns           approximate   O(N)–O(N³)
MLIP (§10.3)         10⁵–10⁷      ⚠️ ns–µs      near-DFT      O(N)
Classical MD         10⁶–10⁹      µs–ms        force-field    O(N)
Coarse-grained       10⁶+         ms–s         topological    O(N)
Continuum/FEM        macroscale   —            constitutive   —
```
**⚠️ The central problem of the field is that the interesting phenomena sit in the gap
between what's accurate and what's affordable.**

### 10.2 DFT — what you need to know to use it honestly
**Hohenberg-Kohn**: ground-state energy is a functional of electron density `n(r)` — ⚠️ **3
variables instead of 3N.** **Kohn-Sham**: map to non-interacting electrons in an effective
potential, solved self-consistently.

**⚠️ The exchange-correlation functional is the approximation, and it is not systematically
improvable** — you cannot converge to the right answer by turning a dial.
```
LDA      overbinds; underestimates bandgaps badly
GGA (PBE) the workhorse; ⚠️ still underestimates bandgaps ~30–50%
meta-GGA (SCAN)  better geometries and energetics
Hybrid (HSE, B3LYP)  ⚠️ much better gaps, ~10-100× the cost
GW / BSE  ⚠️ proper excited states and optical spectra; expensive
DFT+U     for correlated d/f electrons
```
**⚠️ The failure modes to know**: **bandgaps are systematically underestimated** (a
well-known consequence of the derivative discontinuity, not a bug you can tune away);
**van der Waals is absent from standard functionals** — ⚠️ **you must add a dispersion
correction (Grimme D3/D4) or you will get layered materials and molecular crystals badly
wrong**; **strongly correlated systems** are genuinely hard; and **finite-temperature and
entropy effects are not included** unless you do extra work.

**Practical**: plane-wave codes (VASP, Quantum ESPRESSO, ABINIT) vs localized-basis
(Gaussian, FHI-aims, CP2K). ⚠️ **Convergence testing on cutoff energy and k-point mesh is
mandatory and routinely skipped** — an unconverged calculation produces confident numbers.

### 10.3 ⚠️ Machine-learned interatomic potentials — the genuine change

**[VERSIONED — §14.2 → `nano-reference`.]** **The premise**: train a model on DFT energies and forces, then
run MD at near-DFT accuracy for **orders of magnitude less cost.**

**Architecture lineage**: Behler-Parrinello descriptors → GAP (Gaussian process) →
**equivariant message-passing GNNs** — ⚠️ **equivariance under rotation/translation/
permutation is built into the architecture rather than learned, which is why these models
are so data-efficient.** **MACE, NequIP, Allegro, CHGNet, M3GNet, GRACE, MatterSim.**

**⚠️ The shift that matters: foundation models.** Instead of fitting a potential per system
— which took months of expert effort and thousands of DFT calculations — **general-purpose
models trained on large public datasets now run stable MD across a wide range of chemistry
out of the box.** MACE-MP-0 demonstrated this across **solids, liquids, gases, chemical
reactions, interfaces, and even small-protein dynamics.**

> **⚠️ GOTCHA — foundation MLIPs are not a free lunch, and the literature is explicit
> about it.** **They "do not yet achieve the accuracy required to predict reaction
> barriers, phase transitions, and material stability"** out of the box. **Fine-tuning is
> normally required** for a specific task, and it works well — ⚠️ **frozen transfer
> learning reaches chemical accuracy with orders of magnitude less data than training from
> scratch.**
>
> **Two more traps**: ⚠️ **some architectures predict forces directly rather than as the
> energy gradient, and those models do not conserve energy in MD** — which silently
> corrupts any thermodynamic result. And ⚠️ **benchmark leaderboard position does not
> guarantee physical soundness**; check energy conservation and phonon behaviour, not just
> the error metric.

**⚠️ The workflow discipline that follows**: **MLIPs pre-screen; DFT validates.** Treat
model output as a hypothesis generator over a large candidate space, then verify the
survivors with physics. **Anyone reporting a discovery on ML prediction alone has skipped
the step that matters.**

### 10.4 Molecular dynamics and multiscale
**Integrate Newton's equations** with a force field; **~1–2 fs timestep** set by the
fastest vibration (⚠️ **C–H stretch; constraining it via SHAKE/RATTLE buys you 2 fs**).
**Thermostats** (Nosé-Hoover, Langevin) and **barostats**; **periodic boundary conditions**;
**Ewald/PME** for long-range electrostatics.
**⚠️ The timescale problem is fundamental**: interesting events (nucleation, folding, rare
transitions) take microseconds to seconds; you can afford nanoseconds to microseconds.
**Enhanced sampling** — metadynamics, umbrella sampling, replica exchange — buys the gap by
biasing and then unbiasing.

**Kinetic Monte Carlo** for rare-event dynamics on a lattice (growth, diffusion).
**Phase field** and **FEM** for continuum. **⚠️ Coupling scales is the unsolved general
problem** — handshake regions, boundary condition mismatch, and spurious wave reflection at
interfaces.

**Software worth knowing**: LAMMPS, GROMACS, ASE (⚠️ **the Python glue for atomistic work —
learn this first**), pymatgen, Materials Project, AiiDA and FireWorks for workflow
management, OVITO/VMD for visualization.

---

## §11. Safety and Environmental Behaviour

**⚠️ Nanoparticle toxicity is not predictable from bulk toxicity of the same material.**
Drivers: size (⚠️ **<100 nm can cross biological barriers; <40 nm can enter nuclei; ~35 nm
can cross the blood-brain barrier**), shape (⚠️ **high-aspect-ratio fibres including some
long CNTs raise the asbestos-like frustrated-phagocytosis concern**), surface chemistry
(usually **more determinative than core composition**), solubility, and **oxidative stress
generation**, which is the most common mechanism.

**⚠️ The characterization requirement is the practical point**: a toxicology result without
size distribution, surface chemistry, agglomeration state, and dispersion protocol is
uninterpretable — **and much early nanotoxicology literature lacks these**, which is why
the field's findings are inconsistent.

**Environmental**: aggregation and dissolution govern transport; **silver nanoparticles
dissolve to Ag⁺, which is the actual toxic species**; nanoplastics are an active concern.
**Exposure control**: engineering controls first, and ⚠️ **standard respirators are not
designed for this size range** — though filtration efficiency is actually non-monotonic,
with the **most-penetrating particle size around 300 nm**, so very small particles are
captured better than intuition suggests (diffusion capture).
