---
name: physics-quantum-mechanics-and-field-theory
description: "Use when you need the actual quantum formalism and what it means: the postulates, Hilbert space, operators and observables, the Schrodinger equation, measurement and the Born rule, entanglement and the Bell/CHSH results that constrain interpretation, the analytically solved systems (harmonic oscillator, hydrogen, spin, angular momentum) and the atomic structure they explain, and quantum field theory — path integrals, Feynman diagrams, renormalization and the running of couplings, and the gauge structure and particle content of the Standard Model. Includes the router for the whole fundamental-physics reference."
---

# Fundamental Physics: Quantum Mechanics, Solved Systems, and Quantum Field Theory

> **Part 1 of 5** of the *Fundamental Physics* reference (plugin `fundamental-physics`), covering §0–§3. Sibling skills: `physics-relativity-black-holes-and-gravitational-waves` (§4–§6), `physics-cosmology-and-astrophysics` (§7–§10), `physics-measurement-problem-and-quantum-gravity` (§11–§12), `physics-reference` (§13–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
> **Conventions**: `ħ = c = 1` in §1–§4 → `physics-relativity-black-holes-and-gravitational-waves` unless stated; metric signature `(−,+,+,+)`;
> Greek indices 0–3, Latin 1–3; Einstein summation throughout.
>
> **The three facts that structure everything:**
> 1. **Symmetry determines dynamics.** Noether's theorem turns every continuous symmetry
>    into a conservation law, and **gauge symmetry doesn't just constrain the Standard
>    Model — it generates it.** Demanding local invariance forces the existence and the
>    couplings of the force carriers (§3.1).
> 2. **⚠️ Relativity is geometry, not force.** Gravity is not a field on spacetime; it *is*
>    the curvature of spacetime, and free-fall is unaccelerated motion. Nearly every
>    confusion about GR dissolves once that's internalized (§4 → `physics-relativity-black-holes-and-gravitational-waves`).
> 3. **⚠️ The two frameworks are both spectacularly confirmed and mutually inconsistent.**
>    QFT treats spacetime as a fixed stage; GR makes it dynamical. **This is not a
>    technicality awaiting cleanup — it is the central unsolved problem in physics** (§12 → `physics-measurement-problem-and-quantum-gravity`).

---

## §0. Routing

| You want... | Go to |
|---|---|
| **QM postulates and formalism** | **§1** |
| Solved systems, angular momentum, spin | §2 |
| QFT: fields, path integrals, renormalization | §3 |
| The Standard Model | §3.4 |
| Special relativity | §4.1 → `physics-relativity-black-holes-and-gravitational-waves` |
| **General relativity and the field equations** | **§4.2 → `physics-relativity-black-holes-and-gravitational-waves`** |
| Black holes, Schwarzschild, Kerr | §5 → `physics-relativity-black-holes-and-gravitational-waves` |
| Black hole thermodynamics and information | §5.4 → `physics-relativity-black-holes-and-gravitational-waves` |
| Gravitational waves | §6 → `physics-relativity-black-holes-and-gravitational-waves` |
| **Cosmology: FLRW, ΛCDM, inflation** | **§7 → `physics-cosmology-and-astrophysics`** |
| Stellar structure and evolution | §8 → `physics-cosmology-and-astrophysics` |
| Compact objects and endpoints | §9 → `physics-cosmology-and-astrophysics` |
| Galaxies, dark matter, structure | §10 → `physics-cosmology-and-astrophysics` |
| **The measurement problem** | **§11 → `physics-measurement-problem-and-quantum-gravity`** |
| **Why QM and GR don't fit** | **§12 → `physics-measurement-problem-and-quantum-gravity`** |
| Numbers and constants | §13 → `physics-reference` |
| Misconceptions | §14 → `physics-reference` |
| Contested interpretation | §15 → `physics-reference` |
| Contested physics | §16 → `physics-reference` |
| **What's actually open** | **§17 → `physics-reference`** |
| Textbooks | §18 → `physics-reference` |
| Quick reference | §19 → `physics-reference` |

---

## §1. Quantum Mechanics: Formalism

### 1.1 The postulates

**[DURABLE] Stated cleanly, because most confusion is a failure to keep them separate:**

1. **States.** A physical state is a ray in a complex Hilbert space `ℋ` — a unit vector
   `|ψ⟩` up to phase.
2. **Observables.** Measurable quantities are **self-adjoint operators** on `ℋ`.
   Self-adjointness guarantees real eigenvalues and a complete orthonormal eigenbasis.
3. **Measurement outcomes.** The only possible results are eigenvalues of the operator.
4. **Born rule.** `P(a_n) = |⟨a_n|ψ⟩|²`.
5. **Unitary evolution.** `iħ ∂|ψ⟩/∂t = Ĥ|ψ⟩` — the Schrödinger equation.
6. **Composite systems.** States combine by **tensor product**, `ℋ_AB = ℋ_A ⊗ ℋ_B`.

> **⚠️ GOTCHA — postulates 4 and 5 are in tension, and that tension is the measurement
> problem (§11 → `physics-measurement-problem-and-quantum-gravity`).** Evolution is **linear, deterministic, and reversible**; measurement is
> **nonlinear, stochastic, and irreversible**. **The theory does not say which one applies
> when, or what constitutes a "measurement."** Everything in §11 → `physics-measurement-problem-and-quantum-gravity` and §15 → `physics-reference` is an attempt to
> resolve that.

**⚠️ And postulate 6 is where the physics gets strange, not postulate 4.** The tensor
product's dimension grows *multiplicatively* — `2ⁿ` for n qubits — and **most states in
`ℋ_A ⊗ ℋ_B` do not factorize.** Those non-factorizing states are entangled. **Entanglement
is a consequence of linear algebra, not an extra assumption.**

### 1.2 The machinery

**Commutators**: `[Â,B̂] = ÂB̂ − B̂Â`. **Canonical**: `[x̂,p̂] = iħ`.
**The uncertainty relation is a theorem, not a measurement limitation:**
```
σ_A σ_B ≥ ½|⟨[Â,B̂]⟩|      →      σ_x σ_p ≥ ħ/2
```
⚠️ **Derived from Cauchy–Schwarz.** It says non-commuting observables **do not have
simultaneous sharp values**, not that your apparatus is clumsy. **Heisenberg's microscope
is pedagogically useful and philosophically misleading.**

**Pictures**: Schrödinger (states evolve), **Heisenberg** (operators evolve:
`dÂ/dt = (i/ħ)[Ĥ,Â] + ∂Â/∂t` — ⚠️ **note the structural echo of Poisson brackets in
classical mechanics**), and **interaction** (used for perturbation theory).

**Density matrices** for mixed states: `ρ̂ = Σ p_i|ψ_i⟩⟨ψ_i|`, with `⟨Â⟩ = Tr(ρ̂Â)`.
⚠️ **The distinction that matters: a pure state has `Tr(ρ²) = 1`; a mixed state has
`Tr(ρ²) < 1`.** For an entangled pair, **each subsystem's reduced density matrix is mixed
even though the joint state is pure** — the information is in the correlations, not the
parts. **This is the technical content of "entanglement."**

**Symmetries and Noether**: every continuous symmetry gives a conserved quantity.
Time translation → energy. Space translation → momentum. Rotation → angular momentum.
⚠️ **In QM the generator *is* the conserved observable**, which is why `p̂ = −iħ∇` (the
generator of translations) and `Ĥ` (the generator of time evolution) have the forms
they do.

### 1.3 The results that constrain interpretation

**[DURABLE] These are theorems. Any interpretation must accommodate them.**

**Bell's theorem (1964)**: no local hidden-variable theory reproduces QM's correlations.
The CHSH inequality bounds local-realist correlations at `|S| ≤ 2`; QM permits
`|S| ≤ 2√2` (**Tsirelson's bound**). ⚠️ **Experimentally violated, with the detection and
locality loopholes closed simultaneously in 2015** — and the 2022 Nobel went to Aspect,
Clauser and Zeilinger for this line of work.

**⚠️ What Bell actually rules out**: the *conjunction* of locality and definite
pre-existing values. **You may keep either one by giving up the other** — which is exactly
what the interpretations do (§15 → `physics-reference`).

**Kochen–Specker**: no non-contextual hidden-variable assignment exists (for dim ≥ 3).
**PBR theorem (2012)**: under stated assumptions, the wavefunction cannot be merely
epistemic. **No-cloning**: `|ψ⟩ → |ψ⟩|ψ⟩` is not unitary — ⚠️ **the foundation of quantum
cryptography, and the reason quantum error correction had to be cleverer than repetition.**
**No-communication**: entanglement transmits no information. ⚠️ **Measurement on A does not
change A's local statistics at all**; correlation only appears when the results are
compared classically. **This is why entanglement is not faster-than-light signalling.**

---

## §2. Solved Systems and Structure

**[DURABLE] The handful of exactly-solvable systems that everything else is perturbation
around:**

**Free particle** — plane waves, continuous spectrum.
**Infinite well** — `E_n = n²π²ħ²/(2mL²)`. ⚠️ **Note the L⁻² scaling: confinement costs
energy, which is why quantum dots tune colour by size.**
**Harmonic oscillator** — `E_n = ħω(n + ½)`. ⚠️ **The zero-point `½ħω` is not removable,
and its field-theoretic version is the vacuum energy that becomes §17 → `physics-reference`'s cosmological
constant problem.** Ladder operators `â, â†` generalize to field quantization (§3.1).
**Hydrogen** — `E_n = −13.6 eV/n²`. ⚠️ **The `n²`-fold degeneracy is an "accidental"
degeneracy from a hidden SO(4) symmetry (the Laplace–Runge–Lenz vector)** — the same
symmetry that closes Kepler orbits classically.

**Angular momentum**: `[L_i,L_j] = iħε_ijk L_k`. Eigenvalues `ħ²l(l+1)` and `ħm`.
**Spin** is intrinsic and has no classical analogue — ⚠️ **spin-½ requires a 720° rotation
to return to the same state**, which is a genuine physical fact (demonstrated with neutron
interferometry), not a mathematical artifact.

**Spin-statistics theorem**: half-integer spin → fermions → antisymmetric states →
**Pauli exclusion**; integer spin → bosons → symmetric → **Bose–Einstein condensation**.
⚠️ **This is a theorem of relativistic QFT, not an assumption of QM** — it follows from
Lorentz invariance plus positive energies plus causality.

**Perturbation theory**, **variational method**, **WKB**, and **Fermi's golden rule**
`Γ = (2π/ħ)|⟨f|Ĥ'|i⟩|²ρ(E_f)` for transition rates.

---

## §3. Quantum Field Theory

### 3.1 The framework

**[DURABLE] Why fields:** combining QM with special relativity forces it. Relativity
permits particle creation and destruction (`E = mc²`), so **a fixed-particle-number Hilbert
space is untenable.** Fields are the objects; particles are their quantized excitations.

**Construction**: promote the field `φ(x)` to an operator, expand in modes, and the
coefficients become creation and annihilation operators — ⚠️ **the harmonic oscillator's
ladder operators, one per mode.** A "particle" is a quantum of excitation.

**The Lagrangian formulation** is the working language:
```
Klein–Gordon (spin 0):  ℒ = ½(∂_μφ)(∂^μφ) − ½m²φ²
Dirac (spin ½):         ℒ = ψ̄(iγ^μ∂_μ − m)ψ
Maxwell (spin 1):       ℒ = −¼F_μν F^μν
```

**⚠️ Gauge symmetry is the generative principle, and this is the deepest structural fact
in particle physics.** Take the free Dirac Lagrangian, demand invariance under a *local*
phase rotation `ψ → e^(iα(x))ψ`. The derivative spoils it. **To restore invariance you
must introduce a vector field `A_μ` transforming compensatingly, and replace `∂_μ` with
`D_μ = ∂_μ − iqA_μ`.** Out falls electromagnetism — the photon's existence, masslessness,
and coupling — **from a symmetry demand alone.**

**Generalize the group and you get the rest**: `U(1)` → QED. `SU(2)` → weak. `SU(3)` →
QCD, with **eight gluons** carrying colour charge themselves (⚠️ **because SU(3) is
non-abelian, gluons self-interact — which is why QCD confines and QED doesn't**).

**Path integral**: `⟨f|i⟩ = ∫𝒟φ e^(iS[φ]/ħ)` — sum over all field histories weighted by
`e^(iS/ħ)`. ⚠️ **The classical path emerges as the stationary-phase point**, which is the
cleanest statement of how classical mechanics sits inside quantum mechanics.

### 3.2 Renormalization

**[DURABLE] The conceptual shift that made QFT respectable.** Loop integrals diverge.
The historical response was to absorb infinities into redefined ("bare") parameters —
which worked and felt like a swindle.

**⚠️ Wilson's reframing (1970s) is the correct one and it changed the meaning entirely**:
a QFT is an **effective theory valid below some cutoff Λ**. Integrating out high-energy
modes makes couplings **run** with scale:
```
μ dg/dμ = β(g)
```
- **QED**: β > 0. ⚠️ **Coupling grows at high energy** — α goes from 1/137 at low energy to
  ~1/128 at the Z mass.
- **QCD**: β < 0. ⚠️ **Asymptotic freedom** (Gross, Politzer, Wilczek — Nobel 2004):
  quarks are nearly free at short distance and **confined at long distance**, which is why
  you never see an isolated quark.

**⚠️ "Renormalizable" stopped being a fundamental requirement and became a statement about
which terms dominate at low energy.** Non-renormalizable terms are suppressed by powers of
`E/Λ` — **which is why the Standard Model works so well without knowing what's above it,
and why the Fermi theory of beta decay was a perfectly good theory until it wasn't.**

### 3.3 Predictive success

**⚠️ QED's prediction of the electron anomalous magnetic moment agrees with experiment to
about twelve significant figures** — the most precisely verified prediction in science.
That number is the reason the framework is taken seriously despite §12 → `physics-measurement-problem-and-quantum-gravity`.

### 3.4 The Standard Model

**Gauge group `SU(3)_C × SU(2)_L × U(1)_Y`**, spontaneously broken to
`SU(3)_C × U(1)_EM`.

**Matter — three generations of fermions:**
```
Quarks   (u,d)  (c,s)  (t,b)        colour triplets, fractional charge
Leptons  (e,ν_e) (μ,ν_μ) (τ,ν_τ)     colourless
```
**Forces:** photon (EM), **W±, Z⁰** (weak, massive), **8 gluons** (strong).
**Higgs** — one scalar, found 2012 at ~125 GeV.

**⚠️ The Higgs mechanism, stated precisely, because the popular version is wrong.** A
scalar field with potential `V(φ) = μ²|φ|² + λ|φ|⁴` and `μ² < 0` has a **Mexican-hat**
shape; the vacuum sits at `|φ| = v/√2 ≈ 174 GeV`, breaking the symmetry **spontaneously**
(the Lagrangian keeps the symmetry; the ground state doesn't). **Gauge bosons acquire mass
by absorbing the would-be Goldstone modes** — the W and Z eat three, gaining longitudinal
polarizations. **Fermions get mass through separate Yukawa couplings `y_f`, and those
couplings are free parameters, not predictions.**

**⚠️ "The Higgs gives everything mass" is wrong.** It gives the W, Z, and fundamental
fermions their masses. **Over 98% of the mass of ordinary matter is QCD binding energy** —
the proton's ~938 MeV against its quarks' ~9 MeV of Higgs-derived mass.

**⚠️ 19+ free parameters** (masses, mixing angles, couplings, θ_QCD), plus more for neutrino
masses. **The Standard Model does not explain: why three generations, why these masses
(spanning 12 orders of magnitude), or why the gauge group is what it is.**

**Chirality**: ⚠️ **the weak force couples only to left-handed fermions**, which is the
sharpest parity violation in nature and remains structurally unexplained.
**CKM matrix** mixes quark generations and contains **one CP-violating phase** — ⚠️ **far
too little to explain the matter–antimatter asymmetry** (§17 → `physics-reference`).
