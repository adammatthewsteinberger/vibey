---
name: mech-kinematics-newtons-laws-and-forces
description: "Use when setting up a mechanics problem correctly: kinematics in one and more dimensions, Newton's laws stated precisely, the misconceptions the laws reliably generate, free-body diagrams as the discipline that prevents most errors, and the forces — gravity, normal force, friction, drag, and spring and tension — with the models and their limits. Includes the router for the whole newtonian-mechanics reference."
---

# Newtonian Mechanics: Kinematics, Newton's Laws, and the Forces

> **Part 1 of 5** of the *Newtonian Mechanics* reference (plugin `newtonian-mechanics`), covering §0–§3. Sibling skills: `mech-energy-momentum-and-collisions` (§4–§5), `mech-rotation-rigid-bodies-and-oscillations` (§6–§8), `mech-orbits-frames-analytical-mechanics-and-simulation` (§9–§14), `mech-reference` (§15–§19). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Settled since 1687 — Newton's Principia, Euler's rigid-body work in the 1750s, Lagrange 1788, Hamilton 1833. Nothing here has changed or will.

> **Scope.** Complements a fundamental-physics reference, which covers relativity, quantum
> mechanics and where classical mechanics breaks down. ⚠️ **This is the classical theory
> done properly**, including §14 → `mech-orbits-frames-analytical-mechanics-and-simulation` on numerical integration — the part that matters if
> you're simulating any of it.
>
> **⚠️ GOTCHA** boxes mark genuine misconceptions, including several that survive a
> physics degree.
>
> **The three ideas that reorganize everything once you see them:**
> 1. **⚠️ Force causes acceleration, not velocity.** This one sentence is the entire
>    content of the Aristotle-to-Newton revolution, and **the misconception it replaced is
>    the single most robust error in physics education** (§2.2).
> 2. **⚠️ The conservation laws are not consequences of `F = ma` — they're deeper than
>    it.** Momentum conservation follows from spatial translation symmetry, energy from
>    time-translation symmetry, angular momentum from rotational symmetry (Noether, 1918).
>    **They survive into relativity and quantum mechanics; `F = ma` does not** (§4.5 → `mech-energy-momentum-and-collisions`).
> 3. **⚠️ Newtonian mechanics is deterministic but not predictable.** Determinism is a
>    property of the equations; predictability is a property of your knowledge. **Chaos
>    separates them, and the separation is not a defect of your instruments** (§13 → `mech-orbits-frames-analytical-mechanics-and-simulation`).

---

## §0. Routing

| You want... | Go to |
|---|---|
| Kinematics | §1 |
| **Newton's laws, stated precisely** | **§2** |
| Forces, one by one | §3 |
| **Work, energy, conservation** | **§4 → `mech-energy-momentum-and-collisions`** |
| Momentum and collisions | §5 → `mech-energy-momentum-and-collisions` |
| **Rotation** | **§6 → `mech-rotation-rigid-bodies-and-oscillations`** |
| Rigid bodies and gyroscopes | §7 → `mech-rotation-rigid-bodies-and-oscillations` |
| **Oscillations and resonance** | **§8 → `mech-rotation-rigid-bodies-and-oscillations`** |
| Central forces and orbits | §9 → `mech-orbits-frames-analytical-mechanics-and-simulation` |
| **Non-inertial frames** | **§10 → `mech-orbits-frames-analytical-mechanics-and-simulation`** |
| Lagrangian and Hamiltonian | §11 → `mech-orbits-frames-analytical-mechanics-and-simulation` |
| Fluids and continuous media | §12 → `mech-orbits-frames-analytical-mechanics-and-simulation` |
| Chaos and predictability | §13 → `mech-orbits-frames-analytical-mechanics-and-simulation` |
| **Numerical integration** | **§14 → `mech-orbits-frames-analytical-mechanics-and-simulation`** |
| Misconceptions | §15 → `mech-reference` |
| Numbers | §16 → `mech-reference` |
| Books | §17 → `mech-reference` |
| Quick reference | §18 → `mech-reference` |

---

## §1. Kinematics

**Description of motion, before any mention of cause.**
```
v = dr/dt        a = dv/dt = d²r/dt²
Constant acceleration only:
  v = v₀ + at        r = r₀ + v₀t + ½at²        v² = v₀² + 2a·Δr
```
> **⚠️ GOTCHA — those three equations are valid only for constant acceleration**, and
> students apply them everywhere. **The moment `a` depends on position (a spring), on
> velocity (drag), or on time, they are wrong.** ⚠️ **The general case requires
> integrating the differential equation** — which is why §14 → `mech-orbits-frames-analytical-mechanics-and-simulation` exists.

**⚠️ Velocity and acceleration are independent.** A body can have zero velocity and
nonzero acceleration (**a ball at the top of its arc — this is the classic exam
question**), or constant speed and nonzero acceleration (**uniform circular motion**).

**Circular motion**: `a_c = v²/r = ω²r`, directed **toward the centre**. Angular
quantities `θ, ω, α` mirror the linear ones exactly.

**Projectile motion**: horizontal and vertical decouple (⚠️ **without drag — with drag they
couple, and there is no closed-form solution; see §3.4**). Range on level ground is
`v₀² sin(2θ)/g`, maximum at 45°.

**⚠️ Relative motion**: `v_AC = v_AB + v_BC`. **Galilean velocity addition**, and it's
exactly what special relativity replaces.

---

## §2. Newton's Laws

### 2.1 Stated precisely
**First law** — a body remains at rest or in uniform straight-line motion **unless acted on
by a net external force.**
> **⚠️ GOTCHA — the first law is not a special case of the second.** It looks redundant
> (`F=0 ⟹ a=0`), but its real content is **defining what an inertial frame is**: a frame in
> which the first law holds. ⚠️ **The second law is only valid in such frames**, so the
> first law is the precondition for the second, not a corollary of it (§10 → `mech-orbits-frames-analytical-mechanics-and-simulation`).

**Second law** — ⚠️ **properly `F = dp/dt`, not `F = ma`.** They agree only when mass is
constant. **For variable-mass systems — a rocket, a falling chain, a conveyor being
loaded — you must go back to momentum**, and ⚠️ **naively writing `F = ma` with `m(t)` is
wrong, because it ignores the momentum carried by the mass entering or leaving.** (See a
rocket-science reference for the correct derivation.)

**Third law** — forces come in equal, opposite pairs **on different bodies.**

### 2.2 ⚠️ The misconceptions the laws generate
**These are documented, robust, and survive instruction** — the Force Concept Inventory
literature exists because of them.
- **⚠️ "Motion requires a force."** The most persistent error in physics. **Constant
  velocity requires zero net force.** ⚠️ **It feels wrong because on Earth friction is
  always present, so maintaining motion does require force — to cancel friction, not to
  sustain the motion.**
- **⚠️ "A thrown ball has a forward force on it."** It does not. **After release, the only
  forces are gravity and drag.** The "force of the throw" is not a thing that persists —
  ⚠️ **what persists is momentum, and confusing the two is the whole error.**
- **⚠️ "The third-law pair cancels."** ⚠️ **They act on different bodies and therefore
  never cancel each other in a single body's free-body diagram.** **Cancellation would
  make all acceleration impossible.**
- **⚠️ "A heavier object falls faster."** Not in vacuum. In air, terminal velocity depends
  on the mass-to-drag ratio, so **heavier usually does fall faster in practice** — which
  is exactly why the misconception is so durable.
- **⚠️ "Centrifugal force pushes you outward."** ⚠️ **In an inertial frame there is no such
  force**; you feel the seat pushing you *inward* (centripetal) and your inertia resisting.
  **Centrifugal force is real and useful — but only in the rotating frame** (§10 → `mech-orbits-frames-analytical-mechanics-and-simulation`).

### 2.3 Free-body diagrams
**⚠️ The single most valuable procedural skill in mechanics, and it's mechanical:**
```
1. Isolate ONE body. Draw it alone.
2. Draw ONLY forces acting ON it. ⚠️ Not forces it exerts. Not "the force of motion."
3. Every force must have an identifiable other object exerting it.
   ⚠️ If you can't name the exerter, the force isn't real.
4. Choose axes — align one with the acceleration if possible.
5. Write ΣF = ma per axis. Solve.
```
**⚠️ Rule 3 eliminates nearly every spurious force students invent.**

---

## §3. The Forces

### 3.1 Gravity
`F = Gm₁m₂/r²`, and near a surface `W = mg`. ⚠️ **A spherically symmetric body attracts
external objects as if all its mass were at the centre** (Newton's shell theorem — and it
took him years, which is a useful thing to know when it's presented as obvious).
**⚠️ Inside a uniform shell, the field is exactly zero.**

**⚠️ Weight vs mass**: mass is invariant; weight is `mg` and depends on where you are.
**"Weightlessness" in orbit is free fall, not absence of gravity** — ⚠️ **gravity at ISS
altitude is about 90% of its surface value.** The station and its occupants are
accelerating together.

### 3.2 Normal force
**⚠️ Perpendicular to the surface, and it is not equal to `mg` in general.** It is
whatever it needs to be to prevent interpenetration — **on an incline, in an accelerating
lift, or under an applied force, it differs.** ⚠️ **"N = mg" is a special case that
students promote to a law.**

### 3.3 Friction
```
Static:  f_s ≤ μ_s N     ⚠️ an INEQUALITY — it takes whatever value prevents sliding,
                         up to the maximum
Kinetic: f_k = μ_k N     ⚠️ roughly constant, opposing relative motion; μ_k < μ_s
```
**⚠️ The inequality is the part people miss.** A block at rest on a table with no applied
force has **zero** friction, not `μ_s N`. **You compute static friction from equilibrium,
not from the formula** — the formula only gives you the threshold.

**⚠️ The Coulomb model's surprising claim**: friction is **independent of contact area**,
because real contact happens at asperities whose true contact area scales with normal
force. ⚠️ **It's an approximation — it fails for very soft materials, very clean surfaces
(which can cold-weld), and at high speed.** **Racing tyres are wide for thermal and wear
reasons the simple model doesn't capture.**

**Rolling resistance** is a different mechanism entirely — hysteretic deformation loss, not
sliding — and is much smaller.

### 3.4 Drag
```
Low Reynolds number (viscous):   F = −bv        ⚠️ linear
High Reynolds number (inertial): F = ½ρCdAv²    ⚠️ quadratic — the everyday case
```
**⚠️ Terminal velocity** when drag balances weight: `v_t = √(2mg/ρC_dA)`.
**⚠️ Quadratic drag makes the equations non-integrable in closed form** for most cases —
which is precisely why projectile problems in textbooks ignore it and why real ballistics
is numerical.

### 3.5 Spring and tension
**Hooke's law** `F = −kx` — ⚠️ **linear only within the elastic limit, and the minus sign
is the physics: the force opposes displacement, which is what makes oscillation
possible.**
**Tension** — ⚠️ **uniform throughout an ideal massless string, and an ideal pulley
changes tension's *direction* without changing its magnitude.** Real ropes have mass and
real pulleys have inertia and friction.
