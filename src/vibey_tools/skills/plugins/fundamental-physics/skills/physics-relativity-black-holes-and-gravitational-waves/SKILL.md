---
name: physics-relativity-black-holes-and-gravitational-waves
description: "Use when working with relativity and strong gravity: special relativity, Lorentz transformations and spacetime, the equivalence principle, curvature and the Einstein field equations, the Schwarzschild and Kerr solutions, horizons, the no-hair theorem, singularities, black hole thermodynamics, Hawking radiation and the information paradox, and gravitational waves — their generation, the LIGO/Virgo/KAGRA detection method, and what the observed mergers established."
---

# Fundamental Physics: Relativity, Black Holes, and Gravitational Waves

> **Part 2 of 5** of the *Fundamental Physics* reference (plugin `fundamental-physics`), covering §4–§6. Sibling skills: `physics-quantum-mechanics-and-field-theory` (§0–§3), `physics-cosmology-and-astrophysics` (§7–§10), `physics-measurement-problem-and-quantum-gravity` (§11–§12), `physics-reference` (§13–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The formalism is settled — QM 1925, GR 1915, the Standard Model complete by the 1970s and confirmed in 2012. See §17 → `physics-reference` for the experimental frontier, which is the only part that moves.

> **How to read this.** The physics and its mathematics, organized so the connections are
> visible — because the interesting content of this subject is where the frameworks meet
> and where they fail to.
>
> Two markers:
> - **[DURABLE]** — established formalism and confirmed results. Almost everything.
> - **[CONTESTED]** — genuine disagreement among competent physicists (§15 → `physics-reference`, §16 → `physics-reference`, §17 → `physics-reference`).
>
> **⚠️ GOTCHA** boxes mark where the popular account is actively wrong, or where a
> technically-correct statement is routinely misread.
>
> **Conventions**: `ħ = c = 1` in §1–§4 → `physics-quantum-mechanics-and-field-theory` unless stated; metric signature `(−,+,+,+)`;
> Greek indices 0–3, Latin 1–3; Einstein summation throughout.
>
> **The three facts that structure everything:**
> 1. **Symmetry determines dynamics.** Noether's theorem turns every continuous symmetry
>    into a conservation law, and **gauge symmetry doesn't just constrain the Standard
>    Model — it generates it.** Demanding local invariance forces the existence and the
>    couplings of the force carriers (§3.1 → `physics-quantum-mechanics-and-field-theory`).
> 2. **⚠️ Relativity is geometry, not force.** Gravity is not a field on spacetime; it *is*
>    the curvature of spacetime, and free-fall is unaccelerated motion. Nearly every
>    confusion about GR dissolves once that's internalized (§4).
> 3. **⚠️ The two frameworks are both spectacularly confirmed and mutually inconsistent.**
>    QFT treats spacetime as a fixed stage; GR makes it dynamical. **This is not a
>    technicality awaiting cleanup — it is the central unsolved problem in physics** (§12 → `physics-measurement-problem-and-quantum-gravity`).

---

## §4. Relativity

### 4.1 Special relativity

**Two postulates**: physics is identical in all inertial frames; `c` is invariant.
Everything follows.

**Minkowski interval** — the invariant: `ds² = −c²dt² + dx² + dy² + dz²`.
⚠️ **The minus sign is the whole of relativity.** Timelike (`ds² < 0`), null (`= 0`),
spacelike (`> 0`) separation determines causal structure.

**Lorentz transformations** with `γ = 1/√(1−v²/c²)`: time dilation, length contraction,
relativity of simultaneity. **Four-vectors**: `p^μ = (E/c, **p**)`, with
`p^μp_μ = −m²c²` giving `E² = (pc)² + (mc²)²`.

⚠️ **Note the massless case**: `E = pc`. Photons carry momentum without mass. **And "relativistic
mass" is a deprecated concept** — mass is the invariant `m`, and treating it as
velocity-dependent causes more confusion than it resolves.

### 4.2 General relativity

**[DURABLE] The equivalence principle is the seed**: locally, free-fall is
indistinguishable from inertial motion — **gravitational and inertial mass are the same
thing.** ⚠️ **Therefore gravity is not a force; it is the geometry of spacetime, and
freely-falling bodies follow geodesics — the straightest available paths.**

**The apparatus:**
```
Metric:        ds² = g_μν dx^μ dx^ν
Christoffel:   Γ^λ_μν = ½g^λσ(∂_μ g_σν + ∂_ν g_σμ − ∂_σ g_μν)
Geodesic:      d²x^λ/dτ² + Γ^λ_μν (dx^μ/dτ)(dx^ν/dτ) = 0
Riemann:       R^ρ_σμν = ∂_μΓ^ρ_νσ − ∂_νΓ^ρ_μσ + Γ^ρ_μλΓ^λ_νσ − Γ^ρ_νλΓ^λ_μσ
Ricci:         R_μν = R^λ_μλν          Scalar: R = g^μν R_μν
```

**The Einstein field equations (1915):**
```
G_μν + Λg_μν = (8πG/c⁴) T_μν       where G_μν = R_μν − ½R g_μν
```
**Wheeler's summary is exactly right: matter tells spacetime how to curve; spacetime tells
matter how to move.**

⚠️ **These are ten coupled nonlinear PDEs.** The nonlinearity is physical, not
technical — **gravitational energy itself gravitates**, which is why there's no
superposition principle and why exact solutions are rare and precious.

**`G_μν` is divergence-free by the Bianchi identities** (`∇^μG_μν = 0`), which **forces**
`∇^μT_μν = 0` — ⚠️ **local energy-momentum conservation is a consequence of the geometry,
not an extra postulate.**

**Classical tests, all passed**: perihelion precession of Mercury (43″/century — ⚠️ **a
retrodiction, calculated before publication and the reason Einstein knew he was right**),
light deflection (1.75″ at the solar limb, twice the Newtonian value), gravitational
redshift, Shapiro delay, frame dragging (Gravity Probe B), and **binary pulsar orbital
decay matching GR's gravitational-wave prediction to ~0.1%.**

---

## §5. Black Holes

### 5.1 Schwarzschild

The unique static spherically-symmetric vacuum solution (**Birkhoff's theorem** —
⚠️ **which also means a spherically pulsating star emits no gravitational waves**):
```
ds² = −(1 − r_s/r)c²dt² + (1 − r_s/r)^(−1) dr² + r²dΩ²,     r_s = 2GM/c²
```
**⚠️ The `r = r_s` singularity is a coordinate artifact, not physics** — curvature
invariants are finite there. Kruskal–Szekeres coordinates remove it. **The `r = 0`
singularity is real**: curvature diverges.

**⚠️ Nothing locally special happens at the horizon for an infalling observer.** The
horizon is a *global* causal boundary, defined by where the future light cones tip inward.
**An infalling observer crosses in finite proper time and notices nothing**; a distant
observer sees them asymptotically freeze and redshift away. **Both descriptions are
correct.**

**Photon sphere at `1.5 r_s`**; **ISCO at `3 r_s`** — ⚠️ **the innermost stable circular
orbit is why accretion discs have an inner edge and why ~6% (Schwarzschild) to ~42%
(maximal Kerr) of rest mass can be radiated**, making accretion the most efficient
energy-release mechanism known short of annihilation.

### 5.2 Kerr and the no-hair theorem

Rotating black holes (Kerr, 1963) have an **ergosphere** where frame-dragging makes static
observers impossible — ⚠️ **and the Penrose process can extract rotational energy from it**,
the likely engine of relativistic jets via Blandford–Znajek.

**No-hair theorem**: a stationary black hole is fully described by **mass, angular
momentum, and charge**. ⚠️ **Nothing else survives.** This is what makes black hole
information (§5.4) a paradox rather than a curiosity.

### 5.3 Singularities
**Penrose–Hawking theorems**: under reasonable energy conditions, singularities are
generic, not artifacts of symmetry. ⚠️ **Correctly read, this is a statement that GR
predicts its own breakdown** (§12 → `physics-measurement-problem-and-quantum-gravity`).

### 5.4 Black hole thermodynamics

**[DURABLE] The deepest known clue about quantum gravity.**
```
T_H = ħc³/(8πGMk_B)              Hawking temperature
S_BH = k_B A/(4ℓ_P²)             Bekenstein–Hawking entropy
```
**⚠️ Read those two equations carefully — they contain `ħ`, `c`, `G`, and `k_B`
simultaneously.** They are the only well-established results that involve quantum
mechanics, relativity, gravity, and thermodynamics at once.

**⚠️ Entropy scales with AREA, not volume** — a violation of everything ordinary
thermodynamic intuition suggests, and the origin of the **holographic principle**: the
degrees of freedom in a region are bounded by its boundary area in Planck units.

**Hawking radiation**: `T_H ∝ 1/M`. ⚠️ **Black holes have negative heat capacity — they get
hotter as they evaporate.** A solar-mass black hole has `T_H ≈ 60 nK`, far below the CMB,
so it absorbs more than it emits. **Evaporation time `∝ M³`** — ~10⁶⁷ years for a solar
mass.

**⚠️ The information paradox**: Hawking's original calculation gives exactly thermal
radiation, which is information-free. If the black hole evaporates completely, the
information in what fell in is destroyed — **and that is non-unitary, contradicting QM.**
Recent progress (**replica wormholes and the Page curve**, ~2019–20) suggests unitarity is
preserved, but ⚠️ **the mechanism of information return is not settled** (§17 → `physics-reference`).

---

## §6. Gravitational Waves

**[DURABLE]** Linearize `g_μν = η_μν + h_μν` for weak fields; in transverse-traceless
gauge the field equations reduce to a wave equation `□h̄_μν = −(16πG/c⁴)T_μν`.
**Two polarizations, `+` and `×`, at 45° to each other** (⚠️ **not 90° as for EM — a
consequence of the spin-2 nature of the graviton**).

**⚠️ There is no monopole or dipole radiation.** Mass conservation kills the monopole;
momentum conservation kills the dipole. **The leading term is the quadrupole:**
```
h ~ (2G/c⁴r)·d²Q/dt²
```
**⚠️ The `c⁴` in the denominator (≈ 8×10³³ in SI) is why gravitational waves are so
absurdly weak** — LIGO measures strains of `h ~ 10⁻²¹`, a fraction of a proton diameter
over kilometres.

**Detection**: LIGO/Virgo/KAGRA (10 Hz–kHz, stellar-mass mergers — **GW150914** in 2015),
**pulsar timing arrays** (nanohertz, supermassive binaries — a stochastic background
reported in 2023), **LISA** (millihertz, planned). ⚠️ **GW170817** — a neutron star merger
seen in gravitational waves *and* across the electromagnetic spectrum — **confirmed that
GW propagate at `c` to ~1 part in 10¹⁵ and that neutron star mergers produce heavy
elements**, settling the r-process question.
