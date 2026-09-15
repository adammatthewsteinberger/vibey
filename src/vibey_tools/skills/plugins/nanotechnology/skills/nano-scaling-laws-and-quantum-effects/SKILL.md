---
name: nano-scaling-laws-and-quantum-effects
description: "Use when reasoning about why the nanoscale behaves differently: surface-to-volume scaling and what it does to reactivity, melting point and mechanics, which forces actually dominate as size drops (van der Waals, capillary, electrostatic, gravity's irrelevance), and the quantum effects — confinement and the size-dependent band gap, tunnelling and nanoscale transport. Includes the router for the whole nanotechnology reference."
---

# Nanotechnology: Scaling Laws and Quantum Effects

> **Part 1 of 5** of the *Nanotechnology* reference (plugin `nanotechnology`), covering §0–§2. Sibling skills: `nano-fabrication-and-semiconductor-process` (§3–§5), `nano-characterization-materials-and-nanomedicine` (§6–§9), `nano-computational-methods-and-safety` (§10–§11), `nano-reference` (§12–§17). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
>    reactivity, melting-point depression, and why nanoparticles are never inert** (§1.1).
> 2. **⚠️ Different forces win at different scales.** Gravity scales as `L³`, surface
>    tension as `L¹`, van der Waals as roughly `L¹`. **Below about a micron, gravity is
>    irrelevant and adhesion dominates** — which is why nanoscale assembly is a stiction
>    problem, not a positioning problem (§1.2).
> 3. **⚠️ Confinement quantizes.** Below the de Broglie wavelength or exciton Bohr radius,
>    energy levels become discrete and **the material's properties become size-dependent
>    while its composition stays fixed** (§2).

---

## §0. Routing

| You want... | Go to |
|---|---|
| **Scaling laws** | **§1** |
| Quantum effects at the nanoscale | §2 |
| Top-down fabrication | §3 → `nano-fabrication-and-semiconductor-process` |
| Bottom-up synthesis and self-assembly | §4 → `nano-fabrication-and-semiconductor-process` |
| **Semiconductor process** | **§5 → `nano-fabrication-and-semiconductor-process`** |
| Characterization and metrology | §6 → `nano-characterization-materials-and-nanomedicine` |
| Nanomaterials | §7 → `nano-characterization-materials-and-nanomedicine` |
| DNA nanotechnology | §8 → `nano-characterization-materials-and-nanomedicine` |
| Nanomedicine | §9 → `nano-characterization-materials-and-nanomedicine` |
| **Computational nanoscience** | **§10 → `nano-computational-methods-and-safety`** |
| Safety and environmental behaviour | §11 → `nano-computational-methods-and-safety` |
| Misconceptions | §12 → `nano-reference` |
| Numbers | §13 → `nano-reference` |
| **What actually moved** | **§14 → `nano-reference`** |
| Books | §15 → `nano-reference` |
| Quick reference | §16 → `nano-reference` |

---

## §1. Scaling Laws

### 1.1 Surface-to-volume

For a sphere: `S/V = 3/r`. ⚠️ **Halve the radius, double the ratio.**
```
1 cm cube      surface fraction ~0.00000001% of atoms
100 nm particle    ~1% of atoms are surface
10 nm particle     ~10%
2 nm particle      ⚠️ ~50% of atoms are ON THE SURFACE
```
**⚠️ At 2 nm, "bulk" is a minority phase.** Surface atoms are undercoordinated, higher in
energy, and chemically reactive — which is why **nanoparticle catalysis works**, why
**nanoparticles sinter and aggregate spontaneously**, and why **gold — famously inert in
bulk — is an excellent catalyst below ~5 nm.**

**Melting point depression** (Gibbs–Thomson):
```
T_m(r) = T_m(bulk)·[1 − 2σ_sl/(ΔH_f·ρ·r)]
```
⚠️ **Gold melts at 1064 °C in bulk and near 300 °C at 2 nm.** The same equation governs
nanoparticle sintering, and it is why nanoparticle catalysts degrade thermally.

### 1.2 ⚠️ Which forces matter

```
Force                Scales as     At 1 µm     At 10 nm
Gravity / weight        L³         negligible   ⚠️ utterly irrelevant
Surface tension         L¹         dominant     dominant
Van der Waals        ~L¹ (spheres) significant  ⚠️ dominant
Electrostatic         varies       significant  significant
Brownian motion       ⚠️ ∝ 1/√(mass)  strong    ⚠️ overwhelming
```
**⚠️ The consequences invert macroscale engineering:**
- **Stiction, not gravity, is the enemy.** MEMS devices fail by surfaces sticking
  permanently — ⚠️ **an assembled nanostructure doesn't fall apart, it refuses to come
  apart.**
- **⚠️ Brownian motion is not noise at this scale — it's the dominant transport
  mechanism.** `⟨x²⟩ = 2Dt` (Einstein), with `D = k_BT/(6πηr)` (Stokes-Einstein).
  **A 10 nm particle in water diffuses its own diameter in microseconds.**
- **⚠️ Reynolds number is tiny** (`Re = ρvL/µ`, ~10⁻⁵ or less) — **flow is entirely
  laminar and viscous, inertia is meaningless, and motion stops the instant force is
  removed.** Purcell's point: **a bacterium swimming is like a human in honey**, and
  reciprocal motion produces zero net displacement.
- **Diffusion beats convection**: mixing time `t ≈ L²/D`, so ⚠️ **at small L, diffusion is
  fast and stirring is pointless.**

---

## §2. Quantum Effects

### 2.1 Confinement

When a structure is smaller than the charge carrier's natural extent, energy levels
discretize. **Particle in a box**: `E_n = n²h²/(8mL²)` — ⚠️ **note the `1/L²`: energy
rises steeply as the box shrinks.**

**The relevant length is the exciton Bohr radius**: CdSe ~5.6 nm, PbS ~18 nm, Si ~5 nm.
**Below it, the bandgap widens as the particle shrinks:**
```
E_g(r) ≈ E_g(bulk) + h²/(8µr²) − 1.8e²/(4πεε₀r)
```
> **⚠️ GOTCHA — this is why quantum dots are the canonical nanotech demonstration.**
> **The same chemical composition emits different colours purely as a function of
> size.** A 2 nm CdSe dot emits blue; 6 nm emits red. **Nothing changed but the geometry**
> — and that is the cleanest possible illustration that at this scale, size is a material
> property.

**Dimensionality** changes the density of states qualitatively: 3D bulk (`∝ √E`) →
2D quantum well (step function) → 1D wire (⚠️ **van Hove singularities**) → 0D dot
(⚠️ **discrete delta functions — "artificial atoms"**).

### 2.2 Tunnelling and transport

**Tunnelling probability** `T ≈ e^(−2κd)`, with `κ = √(2m(V−E))/ħ`.
⚠️ **The exponential dependence on distance is what makes STM work** — a 1 Å change in tip
height changes current by roughly an order of magnitude, which is where atomic resolution
comes from (§6 → `nano-characterization-materials-and-nanomedicine`).

**⚠️ It's also the leakage mechanism that ended classical transistor scaling**: below ~2 nm
of gate oxide, direct tunnelling current becomes unmanageable, **which is why high-k
dielectrics exist** (§5.2 → `nano-fabrication-and-semiconductor-process`).

**Ballistic transport** when the device is shorter than the mean free path — ⚠️ **no
scattering, so resistance stops depending on length.** **Conductance quantizes** in units
of `G₀ = 2e²/h ≈ 77.5 µS` (~12.9 kΩ per channel). **Coulomb blockade**: when charging
energy `E_C = e²/2C` exceeds `k_BT`, ⚠️ **electrons must transfer one at a time — the basis
of single-electron transistors, and it requires very small C or very low T.**
