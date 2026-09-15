---
name: mech-orbits-frames-analytical-mechanics-and-simulation
description: "Use when the problem outgrows elementary methods: central forces and orbits, non-inertial frames with centrifugal and Coriolis terms, Lagrangian and Hamiltonian formulations and when they are worth the setup cost, fluids and continuous media in brief, chaos and the practical limits of prediction, and numerical integration including the methods, why symplectic integrators matter for long simulations, and the practicalities."
---

# Newtonian Mechanics: Orbits, Non-Inertial Frames, Lagrangian and Hamiltonian Mechanics, Chaos, and Integration

> **Part 4 of 5** of the *Newtonian Mechanics* reference (plugin `newtonian-mechanics`), covering §9–§14. Sibling skills: `mech-kinematics-newtons-laws-and-forces` (§0–§3), `mech-energy-momentum-and-collisions` (§4–§5), `mech-rotation-rigid-bodies-and-oscillations` (§6–§8), `mech-reference` (§15–§19). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Settled since 1687 — Newton's Principia, Euler's rigid-body work in the 1750s, Lagrange 1788, Hamilton 1833. Nothing here has changed or will.

> **Scope.** Complements a fundamental-physics reference, which covers relativity, quantum
> mechanics and where classical mechanics breaks down. ⚠️ **This is the classical theory
> done properly**, including §14 on numerical integration — the part that matters if
> you're simulating any of it.
>
> **⚠️ GOTCHA** boxes mark genuine misconceptions, including several that survive a
> physics degree.
>
> **The three ideas that reorganize everything once you see them:**
> 1. **⚠️ Force causes acceleration, not velocity.** This one sentence is the entire
>    content of the Aristotle-to-Newton revolution, and **the misconception it replaced is
>    the single most robust error in physics education** (§2.2 → `mech-kinematics-newtons-laws-and-forces`).
> 2. **⚠️ The conservation laws are not consequences of `F = ma` — they're deeper than
>    it.** Momentum conservation follows from spatial translation symmetry, energy from
>    time-translation symmetry, angular momentum from rotational symmetry (Noether, 1918).
>    **They survive into relativity and quantum mechanics; `F = ma` does not** (§4.5 → `mech-energy-momentum-and-collisions`).
> 3. **⚠️ Newtonian mechanics is deterministic but not predictable.** Determinism is a
>    property of the equations; predictability is a property of your knowledge. **Chaos
>    separates them, and the separation is not a defect of your instruments** (§13).

---

## §9. Central Forces and Orbits

**Any central force conserves angular momentum** ⟹ ⚠️ **motion is confined to a plane, and
Kepler's second law (equal areas in equal times) follows immediately** — it's angular
momentum conservation, nothing more.

**Kepler's laws**, derived from `F = GMm/r²`:
1. Ellipses with the Sun at a focus.
2. Equal areas in equal times (⚠️ **= angular momentum conservation**).
3. `T² ∝ a³`.

**Orbital energy**: `E = −GMm/2a`. ⚠️ **The sign is the physics: bound orbits have negative
total energy.** `E = 0` is parabolic escape, `E > 0` hyperbolic.
**Escape velocity** `v_esc = √(2GM/r)` = `√2 ×` circular orbital velocity.

**⚠️ The `1/r²` law is special in two ways worth knowing**: it produces **closed orbits**
(Bertrand's theorem — ⚠️ **only `1/r²` and the harmonic `r` potential do**), and it admits
the extra conserved **Laplace-Runge-Lenz vector**, which is why the orbit's orientation
doesn't drift. ⚠️ **Mercury's perihelion precession is the observed failure of this, and
it's a general-relativity effect.**

---

## §10. Non-Inertial Frames

**⚠️ `F = ma` is false in an accelerating frame.** You can rescue it by adding **fictitious
(inertial) forces** — real in their effects within that frame, absent in an inertial one.
```
Linear acceleration:  F_fict = −ma_frame
Centrifugal:          F = mω²r  (outward)
Coriolis:             F = −2m(ω × v)   ⚠️ acts only on bodies MOVING in the frame
Euler:                from angular acceleration of the frame
```
**⚠️ The Coriolis force is the interesting one.** It deflects moving objects — **right in
the northern hemisphere, left in the southern** — and it governs **cyclone rotation, ocean
gyres, and long-range ballistics.**

> **⚠️ GOTCHA — Coriolis does not determine which way your bathtub drains.** ⚠️ **The
> effect at that scale is many orders of magnitude smaller than residual water motion,
> basin asymmetry, and how you pulled the plug.** **It's a genuine effect and a bogus
> example**, and the bogus version is very widely repeated.

**⚠️ The Earth is a rotating frame**, so strictly it's non-inertial: measured `g` varies
with latitude (⚠️ **centrifugal reduction at the equator plus the equatorial bulge**), and
a **Foucault pendulum** visibly demonstrates the rotation.

---

## §11. Lagrangian and Hamiltonian Mechanics

**⚠️ Not new physics — a reformulation that is vastly more powerful for anything with
constraints.**

**Lagrangian** `L = T − V`, with the **Euler-Lagrange equations**:
```
d/dt (∂L/∂q̇ᵢ) − ∂L/∂qᵢ = 0
```
**⚠️ Why this is transformative:**
- **Constraint forces disappear.** ⚠️ **You never compute the normal force or the rod
  tension unless you want it** — choose generalized coordinates that already satisfy the
  constraints.
- **It's coordinate-independent.** Polar, spherical, whatever fits the problem.
- **It's scalar.** ⚠️ **No vector bookkeeping, no free-body diagrams.**
- **Symmetries become manifest**: ⚠️ **if `L` doesn't depend on a coordinate, its conjugate
  momentum is conserved — Noether's theorem falls out mechanically** (§4.5 → `mech-energy-momentum-and-collisions`).

**Hamiltonian** `H = Σp q̇ − L` — usually the total energy — with
```
q̇ = ∂H/∂p        ṗ = −∂H/∂q
```
**⚠️ First-order equations in phase space**, and the natural bridge to statistical
mechanics and quantum mechanics. **⚠️ Liouville's theorem — phase space volume is
conserved — is the property that §14's symplectic integrators are built to respect.**

**Principle of least action**: the actual path extremizes `S = ∫L dt`.
⚠️ **This is arguably the deepest formulation of classical mechanics**, and it generalizes
directly to field theory and quantum mechanics (Feynman's path integral).

---

## §12. Fluids and Continuous Media — briefly

**Statics**: `P = ρgh`, **Pascal's principle**, **Archimedes** (⚠️ **buoyant force =
weight of displaced fluid**).
**Dynamics**: continuity `A₁v₁ = A₂v₂`; **Bernoulli** `P + ½ρv² + ρgh = const` —
⚠️ **valid only along a streamline, for steady, incompressible, inviscid flow, and it is
routinely misapplied.** ⚠️ **The popular "equal transit time" explanation of aeroplane
lift is wrong** — see a signal-processing or aerodynamics reference for circulation and
the actual account.

**Reynolds number** `Re = ρvL/μ` — ⚠️ **the ratio of inertial to viscous forces, and the
single most important dimensionless group in fluid mechanics**; it decides laminar vs
turbulent and determines which drag law in §3.4 → `mech-kinematics-newtons-laws-and-forces` applies.
**⚠️ Navier-Stokes has no general existence-and-smoothness proof** — it's a Millennium
Prize problem, and turbulence remains the outstanding unsolved problem of classical
physics.

---

## §13. Chaos and the Limits of Prediction

**⚠️ Newtonian mechanics is deterministic. It is not predictable. These are different
claims and conflating them is a real error.**

**Sensitive dependence on initial conditions**: nearby trajectories diverge exponentially,
at a rate set by the **Lyapunov exponent**. ⚠️ **Since you never know initial conditions
exactly, prediction has a horizon** — and **improving your measurements buys you only
logarithmic improvement in that horizon.** **Ten times better data gets you a modest
constant more time, not ten times more.**

**⚠️ Chaos requires nonlinearity and at least three dimensions in a continuous autonomous
system.** Examples: the **double pendulum** (⚠️ **the canonical demonstration, and
genuinely chaotic despite being a two-body problem**), the **three-body problem**
(⚠️ **no general closed-form solution — Poincaré, 1890, and this is where chaos was
discovered**), driven oscillators, and weather.

**⚠️ KAM theory** — the useful counterweight: **under small perturbations, many quasi-
periodic orbits survive rather than dissolving into chaos.** **The solar system is not
obviously stable and not obviously chaotic; its long-term behaviour is a live research
question.**

---

## §14. Numerical Integration

**⚠️ The section that matters if you simulate any of this, and the failure mode is
specific and non-obvious.**

### 14.1 The methods
```
Explicit (forward) Euler    x += v·dt ; v += a·dt
  ⚠️ First order. SYSTEMATICALLY GAINS ENERGY in oscillatory systems. Orbits spiral out.
Implicit (backward) Euler
  ⚠️ Stable, but systematically LOSES energy. Orbits spiral in, springs die.
Semi-implicit (symplectic) Euler   v += a·dt ; x += v·dt    ⚠️ NOTE THE ORDER
  ⚠️ Same cost as explicit Euler, and it CONSERVES ENERGY on average. Nearly free win.
Velocity Verlet             second order, symplectic, time-reversible
  ⚠️ The standard for molecular dynamics and orbital mechanics
Leapfrog                    equivalent to Verlet, staggered
RK4                         ⚠️ Fourth order, very accurate per step, NOT symplectic —
                            energy drifts slowly over long runs
```

> **⚠️ GOTCHA — the most important numerical fact in classical simulation.** ⚠️ **Explicit
> Euler and semi-implicit Euler differ by the order of two lines of code, and that
> difference determines whether your simulation is stable over long times.**
> ```
> Explicit:       x_new = x + v*dt;  v_new = v + a(x)*dt      ⚠️ energy grows
> Semi-implicit:  v_new = v + a(x)*dt;  x_new = x + v_new*dt  ⚠️ energy bounded
> ```
> **Same operations, same cost, one uses the updated velocity.** ⚠️ **This is why game
> physics engines and orbital simulators use semi-implicit Euler or Verlet, and it is why
> a naive planet simulation spirals into the sun or off to infinity.**

### 14.2 Why symplectic matters
**⚠️ Symplectic integrators preserve the phase-space structure that §11's Hamiltonian
formulation describes** — Liouville's theorem. **They don't conserve energy exactly, but
the error oscillates within a bound rather than accumulating.**
⚠️ **The counterintuitive consequence**: **for long-duration simulation, a second-order
symplectic method (Verlet) beats fourth-order RK4**, because RK4's superior per-step
accuracy doesn't stop its energy from drifting monotonically. **Order of accuracy is the
wrong figure of merit for long integrations.**

### 14.3 Practical
**Timestep**: ⚠️ **must resolve the fastest timescale in the system** — the stiffest
spring, the closest orbital approach. **Adaptive stepping** for systems with wide dynamic
range (⚠️ **near-collision in gravitational N-body**).
**⚠️ Stiff systems** — where timescales differ by orders of magnitude — force impractically
small steps for explicit methods; **implicit methods are the answer despite their cost.**
**Constraints**: ⚠️ **stiff penalty springs are the naive approach and they make the system
stiff. Lagrange multipliers or projection methods (SHAKE/RATTLE) are the right ones.**
**Collision handling**: discrete detection **misses fast-moving thin objects (tunnelling)**
— ⚠️ **continuous collision detection or swept volumes.**
**⚠️ Always monitor a conserved quantity** — energy, momentum, angular momentum — **as a
correctness check. If it drifts, your integrator or timestep is wrong, and it's the
cheapest diagnostic you have.**
