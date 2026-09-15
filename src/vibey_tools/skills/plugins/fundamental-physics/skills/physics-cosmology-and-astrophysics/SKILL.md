---
name: physics-cosmology-and-astrophysics
description: "Use when working on cosmology or astrophysics: FLRW geometry and the Friedmann equations, the LCDM model and its parameters, the CMB, nucleosynthesis and inflation, stellar structure and evolution and the nuclear burning stages, compact objects (white dwarfs, the Chandrasekhar limit, neutron stars, their equation of state), and galaxies, dark matter evidence, and large-scale structure formation."
---

# Fundamental Physics: Cosmology, Stars, Compact Objects, and Structure

> **Part 3 of 5** of the *Fundamental Physics* reference (plugin `fundamental-physics`), covering §7–§10. Sibling skills: `physics-quantum-mechanics-and-field-theory` (§0–§3), `physics-relativity-black-holes-and-gravitational-waves` (§4–§6), `physics-measurement-problem-and-quantum-gravity` (§11–§12), `physics-reference` (§13–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
> **Conventions**: `ħ = c = 1` in §1–§4 → `physics-quantum-mechanics-and-field-theory`, `physics-relativity-black-holes-and-gravitational-waves` unless stated; metric signature `(−,+,+,+)`;
> Greek indices 0–3, Latin 1–3; Einstein summation throughout.
>
> **The three facts that structure everything:**
> 1. **Symmetry determines dynamics.** Noether's theorem turns every continuous symmetry
>    into a conservation law, and **gauge symmetry doesn't just constrain the Standard
>    Model — it generates it.** Demanding local invariance forces the existence and the
>    couplings of the force carriers (§3.1 → `physics-quantum-mechanics-and-field-theory`).
> 2. **⚠️ Relativity is geometry, not force.** Gravity is not a field on spacetime; it *is*
>    the curvature of spacetime, and free-fall is unaccelerated motion. Nearly every
>    confusion about GR dissolves once that's internalized (§4 → `physics-relativity-black-holes-and-gravitational-waves`).
> 3. **⚠️ The two frameworks are both spectacularly confirmed and mutually inconsistent.**
>    QFT treats spacetime as a fixed stage; GR makes it dynamical. **This is not a
>    technicality awaiting cleanup — it is the central unsolved problem in physics** (§12 → `physics-measurement-problem-and-quantum-gravity`).

---

## §7. Cosmology

### 7.1 FLRW and the Friedmann equations

**Assume homogeneity and isotropy** (the cosmological principle) and the metric is forced:
```
ds² = −c²dt² + a(t)²[dr²/(1−kr²) + r²dΩ²]
```
Substituting into the field equations gives:
```
(ȧ/a)² = (8πG/3)ρ − kc²/a² + Λc²/3           Friedmann I
ä/a = −(4πG/3)(ρ + 3p/c²) + Λc²/3            Friedmann II
ρ̇ + 3(ȧ/a)(ρ + p/c²) = 0                     continuity
```
⚠️ **Note the `ρ + 3p` in the acceleration equation — pressure gravitates.** This is why
`w = p/ρc² < −1/3` (dark energy) produces acceleration and ordinary matter doesn't.

**Scaling with `a`**: matter `ρ ∝ a⁻³`, radiation `ρ ∝ a⁻⁴` (⚠️ **the extra factor from
redshifting**), curvature `∝ a⁻²`, **Λ constant**. **Hence the eras: radiation → matter →
Λ**, and the ordering is a consequence of the exponents, not a coincidence.

**⚠️ Redshift is not Doppler.** `1 + z = a(t_0)/a(t_e)` — wavelengths stretch with space
itself. **Recession velocities can and do exceed `c` without violating relativity**,
because nothing is moving *through* space faster than light.

### 7.2 ΛCDM

**Six parameters** fit essentially all cosmological data: `Ω_b h², Ω_c h², θ_*, τ, A_s, n_s`.
Derived: **≈ 5% baryons, ≈ 27% cold dark matter, ≈ 68% dark energy**, spatially flat to
sub-percent, age **13.8 Gyr**.

**The evidence pillars**: **CMB** (⚠️ **acoustic peaks whose positions and heights encode
the whole parameter set — the most information-dense dataset in cosmology**), **BBN**
(primordial D, ³He, ⁴He, ⁷Li abundances from the first three minutes — **a completely
independent measure of baryon density that agrees**), **large-scale structure and BAO**,
and **Type Ia supernovae** (the 1998 acceleration discovery).

### 7.3 Inflation

**⚠️ Motivated by three problems**: **horizon** (why is the CMB uniform across regions that
were never causally connected?), **flatness** (why is Ω so close to 1, when that's an
unstable fixed point?), and **monopoles**.

**Mechanism**: a scalar field in slow roll gives `a ∝ e^(Ht)`, expanding by `≳ e^60`.
⚠️ **The genuine triumph is not solving those problems — it's that quantum fluctuations of
the inflaton, stretched to cosmic scales, predict a nearly scale-invariant spectrum of
density perturbations with `n_s` slightly below 1.** **Planck measures `n_s ≈ 0.965`** —
a prediction made before the measurement.

⚠️ **What's not settled**: which inflaton, whether eternal inflation follows (and whether
that's science), and **primordial gravitational waves (`r`) remain undetected**, which
would be the decisive confirmation.

---

## §8. Stellar Astrophysics

**[DURABLE] Stellar structure equations** — four coupled ODEs closed by an equation of
state and opacity:
```
dP/dr = −Gm(r)ρ/r²              hydrostatic equilibrium
dm/dr = 4πr²ρ                   mass continuity
dL/dr = 4πr²ρε                  energy generation
dT/dr = −3κρL/(16πacr²T³)       radiative transport (or the adiabatic gradient if convective)
```

**⚠️ The Eddington limit** — where radiation pressure balances gravity:
`L_Edd = 4πGMm_p c/σ_T ≈ 1.26×10³¹ (M/M_⊙) W`. **This caps stellar masses and accretion
rates**, and is why supermassive black hole growth has a timescale problem (§17 → `physics-reference`).

**Nuclear burning**: **pp chain** (dominant below ~1.3 M_⊙), **CNO cycle** (⚠️ **`∝ T¹⁵`
versus pp's `T⁴` — the extreme temperature sensitivity is why massive stars are convective
in the core and low-mass stars aren't**), **triple-alpha** (⚠️ **requires the Hoyle
resonance in ¹²C, predicted from the existence of carbon and then found**), and successive
burning to iron.

**⚠️ Iron is the endpoint because ⁵⁶Fe has the highest binding energy per nucleon.**
Fusion beyond it consumes energy rather than releasing it — which is why the core collapses.

**The mass-luminosity relation `L ∝ M^3.5`** has a brutal consequence:
⚠️ **lifetime `∝ M/L ∝ M^−2.5`.** The Sun lasts 10 Gyr; a 30 M_⊙ star lasts a few Myr.

---

## §9. Compact Objects

**Degeneracy pressure** — a purely quantum-mechanical support mechanism from the exclusion
principle, **independent of temperature.**

**Chandrasekhar limit ≈ 1.4 M_⊙** for white dwarfs. ⚠️ **The derivation is elegant: as
mass rises, electrons become relativistic, the equation of state softens from `P ∝ ρ^5/3`
to `P ∝ ρ^4/3`, and at `4/3` the star has no stable configuration.** **The limit depends
only on fundamental constants** — which is why Type Ia supernovae are standardizable
candles, and therefore why we know the universe is accelerating.

**Neutron stars**: ~1.4 M_⊙ in ~10 km, central density above nuclear saturation.
⚠️ **The maximum mass (~2.2–2.3 M_⊙) is uncertain because the dense-matter equation of
state is unknown** — genuinely open physics (§17 → `physics-reference`), and constrained by NICER and by
gravitational-wave tidal deformability from GW170817.

**Supernovae**: **core-collapse (II, Ib, Ic)** — ⚠️ **99% of the energy leaves as
neutrinos**, and the explosion mechanism (neutrino-driven, multidimensional) is still not
fully settled; **Type Ia** — thermonuclear disruption of a white dwarf.

**⚠️ Pulsars as physics laboratories**: millisecond pulsars are timekeepers rivalling
atomic clocks, and the **Hulse–Taylor binary's orbital decay** matched GR's
gravitational-wave prediction decades before direct detection.

---

## §10. Galaxies, Dark Matter, Structure

**[DURABLE] The dark matter evidence is multiple and independent**, which is what makes it
robust:
1. **Galaxy rotation curves** — flat at large radii where Keplerian falloff is expected.
2. **Velocity dispersions in clusters** (Zwicky, 1933 — the original observation).
3. **Gravitational lensing**, including ⚠️ **the Bullet Cluster, where the lensing mass is
   spatially separated from the X-ray-emitting baryons after a collision** — the single
   hardest observation for modified-gravity alternatives.
4. **CMB acoustic peak ratios** — ⚠️ **the third peak's height directly measures
   non-baryonic matter density.**
5. **Structure formation** — without dark matter, perturbations don't grow enough between
   recombination and now.

**⚠️ Candidates and status**: WIMPs (⚠️ **direct-detection experiments have excluded much of
the natural parameter space and are approaching the irreducible neutrino background**),
axions (motivated independently by the strong-CP problem — §17 → `physics-reference`), sterile neutrinos, and
primordial black holes (constrained but not excluded in some mass windows). **Nothing has
been detected non-gravitationally.**

**MOND** fits galaxy rotation curves with impressive economy (⚠️ **the baryonic
Tully–Fisher relation is genuinely tight and unexplained by ΛCDM at the galaxy scale**) but
**fails at cluster scales and does not reproduce the CMB** — §16 → `physics-reference`.

**Structure formation**: hierarchical, small-to-large, from inflationary seeds through
gravitational instability, with the **cosmic web** confirmed observationally.
**Galaxy scaling relations** (Tully–Fisher, Faber–Jackson, fundamental plane) and the
**M–σ relation** — ⚠️ **supermassive black hole mass correlating tightly with bulge velocity
dispersion, implying co-evolution and AGN feedback.**
