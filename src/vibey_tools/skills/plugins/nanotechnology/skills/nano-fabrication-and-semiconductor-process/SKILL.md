---
name: nano-fabrication-and-semiconductor-process
description: "Use when making nanoscale structures: top-down fabrication including photolithography, EUV, etching and deposition and their resolution limits, bottom-up synthesis and self-assembly, and the semiconductor process — what a node name such as 2nm actually means, the transistor evolution from planar through FinFET to gate-all-around, and why any of it matters to a software engineer."
---

# Nanotechnology: Top-Down Fabrication, Self-Assembly, and the Semiconductor Process

> **Part 2 of 5** of the *Nanotechnology* reference (plugin `nanotechnology`), covering §3–§5. Sibling skills: `nano-scaling-laws-and-quantum-effects` (§0–§2), `nano-characterization-materials-and-nanomedicine` (§6–§9), `nano-computational-methods-and-safety` (§10–§11), `nano-reference` (§12–§17). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The physics and fabrication principles are stable; the leading-edge semiconductor node and machine-learned interatomic potentials moved. See §14 → `nano-reference` for what actually changed.

> **Framing.** Written for someone who computes. **§10 → `nano-computational-methods-and-safety` is the section where your existing
> skills apply directly** — computational nanoscience is a simulation and ML problem — and
> **§5 is the nanotechnology that produced the hardware you run on.** The rest is the
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

## §3. Top-Down Fabrication

**Lithography — the workhorse, and resolution is diffraction-limited:**
```
CD = k₁·λ/NA          Rayleigh criterion
DOF = k₂·λ/NA²        ⚠️ depth of focus — and note it degrades as NA²
```
**⚠️ The whole history of the industry is in that equation**: reduce λ (436 → 365 → 248 →
193 nm → **13.5 nm EUV**), raise NA (immersion in water raised it to 1.35), or reduce k₁
via resolution enhancement — **OPC, phase-shift masks, multiple patterning, and
computational lithography** (⚠️ **which is a heavy simulation workload, and where software
people actually work in this industry**).

**⚠️ Depth of focus is the underrated cost.** Higher NA buys resolution and loses DOF as
`NA²`, which is why wafer flatness and thin resists become critical problems, and why
High-NA EUV requires re-engineering the whole stack rather than swapping a lens.

**Other patterning**: **electron-beam** (⚠️ **sub-10 nm, direct-write, and hopelessly slow
— it makes the masks, not the wafers**), **focused ion beam** (mill and deposit,
⚠️ **implants gallium and damages the sample**), **nanoimprint** (mechanical stamping —
cheap, high resolution, defect-prone), **scanning probe lithography** (⚠️ **atomically
precise and glacially slow**).

**Deposition**: **PVD** (evaporation, sputtering — line-of-sight), **CVD** (conformal),
**⚠️ ALD — atomic layer deposition**, which is the enabling one: **self-limiting surface
reactions deposit one monolayer per cycle, giving Ångström thickness control and perfect
conformality into high-aspect-ratio features.** ⚠️ **No other method can wrap material
around a stacked nanosheet** (§5.2). **Epitaxy** (MBE, MOCVD) for crystalline layers.

**Etching**: **wet** (isotropic, chemically selective) vs **dry/plasma**
(⚠️ **anisotropic — RIE gives vertical sidewalls, which is what makes high-aspect-ratio
structures possible**). **Deep RIE / Bosch process** alternates etch and passivation for
very deep vertical features. **Selectivity and aspect-ratio-dependent etching** are the
practical constraints.

---

## §4. Bottom-Up Synthesis and Self-Assembly

**Nucleation and growth** — **LaMer** model: rapid burst nucleation followed by
diffusion-limited growth. ⚠️ **Separating nucleation from growth in time is what gives
monodisperse particles**, and it's the central trick of colloidal synthesis.
**Ostwald ripening**: ⚠️ **large particles grow at the expense of small ones**, because
smaller particles have higher surface chemical potential — a spontaneous coarsening that
must be actively suppressed.

**Colloidal synthesis**: hot injection, seeded growth, **shape control via
facet-selective ligands** (⚠️ **capping agents bind preferentially to certain crystal
faces, slowing their growth — this is how you get rods, cubes, and stars rather than
spheres**).

**⚠️ Self-assembly is the bottom-up ideal, and it is thermodynamically driven, not
directed.** Components find their minimum-free-energy arrangement. Governed by:
- **The hydrophobic effect** (⚠️ **entropic — see a biology-and-chemistry reference §3.2**)
  → micelles, vesicles, bilayers.
- **Hydrogen bonding and π-stacking** → supramolecular assemblies.
- **Electrostatics**, **DLVO theory** (van der Waals attraction + electrostatic repulsion
  → ⚠️ **the energy barrier that determines whether a colloid is stable or aggregates**).
- **Entropic depletion forces** — ⚠️ **counterintuitively, adding non-adsorbing polymer
  causes particles to attract, because clustering increases the polymer's accessible
  volume.**

**Block copolymer lithography** — microphase separation gives 5–50 nm periodic patterns
(lamellae, cylinders, spheres) by annealing. ⚠️ **Directed self-assembly (DSA) uses coarse
lithographic guides to orient them, multiplying pattern density — a real industrial
technique, not a curiosity.**

**Langmuir-Blodgett** films, **self-assembled monolayers** (⚠️ **thiols on gold, silanes
on oxide — the standard way to functionalize a surface**).

---

## §5. Semiconductor Process

**[VERSIONED — §14.1 → `nano-reference` dates this. This is the nanotechnology that built your computer.]**

### 5.1 What "2nm" actually means

> **⚠️ GOTCHA — the node name is not a measurement.** "2nm" is **a marketing and
> generational label rather than a literal measurement of any single feature size.** It
> denotes the process generation after 3nm, characterized primarily by contacted gate
> pitch and metal pitch. ⚠️ **No feature on a 2nm chip is 2 nm.** Gate lengths are more
> like 12–18 nm. **Comparing nodes across foundries by name alone is meaningless** —
> compare transistor density, performance, and power.

### 5.2 The transistor evolution
```
Planar MOSFET     → gate controls the channel from ONE side
                    ⚠️ short-channel effects and leakage killed it below ~28 nm
FinFET (~22 nm)   → vertical fin, gate on THREE sides
                    ⚠️ ran out of road: fin height/width limits and quantized widths
GAA nanosheet     → ⚠️ gate wraps ALL FOUR sides of stacked horizontal sheets
                    Better electrostatic control, lower leakage, and — importantly —
                    ⚠️ continuously TUNABLE channel width (vs FinFET's quantized fins)
CFET (future)     → stack n- and p-type devices vertically
```
**⚠️ Why GAA was necessary**: as channels shorten, the drain starts to compete with the
gate for control of the channel, and leakage rises. **Wrapping the gate completely
restores electrostatic control.** Fabricating it requires **ALD to deposit high-k
dielectric and metal gate uniformly into the gaps between suspended nanosheets** (§3) —
⚠️ **which is why ALD is load-bearing for the whole node.**

**Backside power delivery** — ⚠️ **the other major architectural change, and the reason is
a genuine conflict**: in a conventional stack, the metal layers above the transistors carry
**both signals and power, and the two compete for the same tracks.** Power wants fat
low-resistance lines; signals want density. **At low voltage this shows up as IR drop and
dynamic droop — the transistor doesn't get the voltage the timing analysis assumed.**
**Moving power to the wafer's back frees the frontside entirely for signal routing.**

**High-NA EUV** — NA 0.55 vs 0.33. ⚠️ **The business case is replacing costly
multi-patterned layers with cleaner single-exposure steps**, not resolution for its own
sake. **It is a later overlay-and-pitch tool, and it is not what makes a nanosheet wrap** —
first-generation GAA does not depend on it.

### 5.3 ⚠️ Why this matters to a software engineer
**Dennard scaling ended around 2005** — power density stopped falling with feature size,
which ended frequency scaling and forced multicore. **Moore's Law in the density sense
continues; the free-lunch performance sense died two decades ago.**

**What replaced it**: **architectural specialization** (GPUs, TPUs, accelerators),
**advanced packaging and chiplets** (⚠️ **2.5D/3D integration, because moving data between
dies is now cheaper than making one bigger die yield**), and **design-technology
co-optimization** — ⚠️ **the node and the design rules are now developed together, which is
why "just port it to the new node" stopped working.**

**⚠️ And the practical consequence for code**: performance now comes from data movement, not
arithmetic. **The energy to move a word across a chip exceeds the energy to compute on it
by orders of magnitude** — which is why locality, blocking, and memory hierarchy dominate
optimization, and why that will not reverse.
