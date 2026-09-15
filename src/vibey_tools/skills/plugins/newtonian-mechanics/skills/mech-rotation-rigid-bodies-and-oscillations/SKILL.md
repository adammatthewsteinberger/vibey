---
name: mech-rotation-rigid-bodies-and-oscillations
description: "Use when things spin or vibrate: rotational kinematics and dynamics, torque, moment of inertia and angular momentum, rigid body motion including the inertia tensor, precession and the gyroscopic behaviour that seems paradoxical, and oscillations — simple harmonic motion, damping, driven systems and resonance."
---

# Newtonian Mechanics: Rotation, Rigid Bodies and Gyroscopes, and Oscillations

> **Part 3 of 5** of the *Newtonian Mechanics* reference (plugin `newtonian-mechanics`), covering §6–§8. Sibling skills: `mech-kinematics-newtons-laws-and-forces` (§0–§3), `mech-energy-momentum-and-collisions` (§4–§5), `mech-orbits-frames-analytical-mechanics-and-simulation` (§9–§14), `mech-reference` (§15–§19). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
>    the single most robust error in physics education** (§2.2 → `mech-kinematics-newtons-laws-and-forces`).
> 2. **⚠️ The conservation laws are not consequences of `F = ma` — they're deeper than
>    it.** Momentum conservation follows from spatial translation symmetry, energy from
>    time-translation symmetry, angular momentum from rotational symmetry (Noether, 1918).
>    **They survive into relativity and quantum mechanics; `F = ma` does not** (§4.5 → `mech-energy-momentum-and-collisions`).
> 3. **⚠️ Newtonian mechanics is deterministic but not predictable.** Determinism is a
>    property of the equations; predictability is a property of your knowledge. **Chaos
>    separates them, and the separation is not a defect of your instruments** (§13 → `mech-orbits-frames-analytical-mechanics-and-simulation`).

---

## §6. Rotation

```
τ = r × F              ⚠️ a cross product — magnitude rF sinθ, direction by right-hand rule
I = Σmᵢrᵢ²             moment of inertia — ⚠️ depends on the AXIS, not just the body
τ = Iα                 (fixed axis)
L = Iω  or  L = r × p
KE_rot = ½Iω²
```
**⚠️ Moment of inertia is not a property of an object alone** — it's a property of an
object *and an axis*. **The same rod has `mL²/12` about its centre and `mL²/3` about its
end.**

**Parallel axis theorem**: `I = I_cm + Md²`. ⚠️ **Which shows `I` is always minimized about
an axis through the centre of mass.**

**Common values** (§16 → `mech-reference`): hoop `MR²`, disc `½MR²`, solid sphere `⅖MR²`, shell `⅔MR²`.
**⚠️ The classic demonstration**: objects rolling down an incline race in order of `I/MR²`,
**independent of mass and radius** — a solid sphere always beats a disc, which always
beats a hoop.

**Rolling without slipping**: `v = ωR`, `a = αR`. ⚠️ **The contact point is instantaneously
at rest, which is why static friction acts and does no work** — this is why rolling can
conserve mechanical energy while sliding cannot.

**⚠️ Angular momentum conservation** when net external torque is zero. **The spinning
skater pulling arms in — and note that `KE = L²/2I` means KE *increases* as `I` decreases.
The skater does work pulling their arms in against the centrifugal effect.** ⚠️ **That
energy doesn't come from nowhere, and the question "where does it come from?" is the good
one.**

---

## §7. Rigid Bodies and Gyroscopes

**General rigid body motion = translation of the centre of mass + rotation about it.**
**⚠️ In 3D, `I` is a tensor, not a scalar**, and `L = Iω` means ⚠️ **`L` and `ω` are
generally not parallel.** **The principal axes are the eigenvectors of the inertia tensor**
— rotation about those is the only case where they align.

**⚠️ The intermediate axis theorem (Dzhanibekov effect)**: rotation about the axes of
largest and smallest moment of inertia is stable; **rotation about the intermediate axis
is unstable** and the object tumbles chaotically. ⚠️ **This is a real, dramatic, and
completely classical effect — throw a book or a tennis racket and watch it flip.**

**Gyroscopic precession**: `τ = dL/dt` means ⚠️ **a torque perpendicular to `L` changes its
*direction*, not its magnitude.** A spinning top under gravity precesses rather than
falling. ⚠️ **This is the most counterintuitive result in classical mechanics and it is
pure `τ = dL/dt`** — no new physics, just the vector nature of the equation taken
seriously. **Nutation** is the additional wobble.

**Static equilibrium** requires **both** `ΣF = 0` and `Στ = 0`. ⚠️ **Torque must be
computed about a chosen point — and it's zero about every point if it's zero about one,
provided `ΣF = 0`. Choosing the right pivot (one that kills an unknown force) is the whole
trick to statics problems.**

---

## §8. Oscillations and Resonance

**Simple harmonic motion** — ⚠️ **arises whenever the restoring force is proportional to
displacement, which is the leading-order behaviour of *any* smooth potential minimum.**
**That's why SHM is everywhere: it's the first term in a Taylor expansion.**
```
mẍ + kx = 0     →     x = A cos(ωt + φ),  ω = √(k/m)
Pendulum (small angle): ω = √(g/L)   ⚠️ small angle only — sin θ ≈ θ
                        ⚠️ period independent of amplitude ONLY in that approximation
```
**Damped**: `mẍ + bẋ + kx = 0` → **underdamped** (oscillates, decaying),
**critically damped** (⚠️ **fastest return to equilibrium without overshoot — what you
want for a door closer or a control system**), **overdamped** (slow, no overshoot).

**Driven and resonance**: amplitude peaks near `ω_drive ≈ ω₀`.
**Q factor** ≈ `ω₀/Δω` — ⚠️ **high Q means sharp resonance and slow decay.**
> **⚠️ GOTCHA — resonance is not automatically destructive, and the Tacoma Narrows bridge
> is not an example of it.** ⚠️ **That collapse is now attributed to aeroelastic flutter —
> a self-excited oscillation where the structure's motion changes the aerodynamic forces,
> a feedback instability rather than an external periodic driver matching a natural
> frequency.** **It's in every textbook as "resonance" and the attribution is wrong.**
