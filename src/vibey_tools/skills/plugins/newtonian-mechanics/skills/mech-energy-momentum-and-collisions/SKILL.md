---
name: mech-energy-momentum-and-collisions
description: "Use when a problem is better attacked with conserved quantities than with forces: work, energy and power, potential energy and conservative forces, why the conservation laws are deeper than Newton's laws, and momentum, impulse, centre of mass and collisions from perfectly elastic through perfectly inelastic."
---

# Newtonian Mechanics: Work, Energy, Power, Momentum, and Collisions

> **Part 2 of 5** of the *Newtonian Mechanics* reference (plugin `newtonian-mechanics`), covering §4–§5. Sibling skills: `mech-kinematics-newtons-laws-and-forces` (§0–§3), `mech-rotation-rigid-bodies-and-oscillations` (§6–§8), `mech-orbits-frames-analytical-mechanics-and-simulation` (§9–§14), `mech-reference` (§15–§19). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
>    **They survive into relativity and quantum mechanics; `F = ma` does not** (§4.5).
> 3. **⚠️ Newtonian mechanics is deterministic but not predictable.** Determinism is a
>    property of the equations; predictability is a property of your knowledge. **Chaos
>    separates them, and the separation is not a defect of your instruments** (§13 → `mech-orbits-frames-analytical-mechanics-and-simulation`).

---

## §4. Work, Energy, Power

```
W = ∫F·dr           ⚠️ the dot product: only the component along displacement does work
KE = ½mv²           PE_grav = mgh (local) = −GMm/r (general)
PE_spring = ½kx²    P = dW/dt = F·v
```
**Work-energy theorem**: `W_net = ΔKE`. ⚠️ **Always true — it's just `F = ma` integrated
over displacement.**

**⚠️ Conservative forces** — work is path-independent, equivalently `∮F·dr = 0`,
equivalently `∇×F = 0`. **Only conservative forces admit a potential energy.** Gravity and
springs are conservative; **friction and drag are not**, which is why there's no "friction
potential energy."

**Mechanical energy conservation** `KE + PE = const` — ⚠️ **only when no non-conservative
force does work.** Otherwise `ΔKE + ΔPE = W_nc`.

> **⚠️ GOTCHA — "energy is lost to friction" is a shorthand that hides the physics.**
> ⚠️ **Energy is never lost.** It becomes thermal energy — disordered kinetic energy of
> molecules. **The distinction matters because it's the entry point to the second law**:
> the energy is still there, it's just no longer available to do work. **See a
> chemistry-foundations reference on entropy for why.**

### 4.5 ⚠️ Why conservation laws are deeper than Newton's laws
**Noether's theorem (1918)**: every continuous symmetry of the action yields a conserved
quantity.
```
Time-translation symmetry       →  energy conservation
Spatial-translation symmetry    →  momentum conservation
Rotational symmetry             →  angular momentum conservation
```
**⚠️ This is one of the most important results in physics** and it explains something
otherwise mysterious: **why conservation laws survive the transition to relativity and
quantum mechanics while `F = ma` does not.** ⚠️ **The conservation laws aren't consequences
of Newtonian dynamics — Newtonian dynamics is one realization of the underlying
symmetries.**

---

## §5. Momentum and Collisions

`p = mv`, and **impulse** `J = ∫F dt = Δp`.
**⚠️ Momentum is conserved for any isolated system, regardless of the internal forces** —
this follows directly from the third law, and it's more robust than energy conservation
because it doesn't care whether the interaction is dissipative.

**⚠️ The impulse insight that saves lives**: for a given `Δp`, **extending the collision
time reduces the peak force.** Crumple zones, airbags, helmets, and bending your knees on
landing are all this. **The momentum change is fixed by physics; the force is a design
choice.**

**Collisions**:
```
Elastic     ⚠️ KE conserved AND momentum conserved
Inelastic   momentum conserved, KE not
Perfectly inelastic  they stick; ⚠️ maximum KE loss consistent with momentum conservation
```
**⚠️ The 1D elastic collision result worth memorizing**: **equal masses exchange
velocities.** (Newton's cradle, and the basis of neutron moderation — ⚠️ **which is why
moderators use light nuclei: hydrogen has nearly the same mass as a neutron and takes the
most energy per collision.**)

**Centre of mass**: `R = Σmᵢrᵢ/Σmᵢ`. ⚠️ **The centre of mass moves as though all mass were
concentrated there and all external force applied there — regardless of how complicated
the internal motion is.** **An exploding shell's centre of mass continues on the original
parabola.**
