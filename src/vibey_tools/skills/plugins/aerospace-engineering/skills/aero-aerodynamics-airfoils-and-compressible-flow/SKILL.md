---
name: aero-aerodynamics-airfoils-and-compressible-flow
description: "Use when reasoning about the air itself: the governing quantities (Reynolds and Mach number, dynamic pressure, the coefficients), how lift actually works and why the common explanations are wrong, airfoils and wing planform including aspect ratio, sweep and stall behaviour, the drag breakdown into induced, parasite and wave components, and compressible and supersonic flow with shocks, expansion and the transonic drag rise. Includes the router for the whole aerospace-engineering reference."
---

# Aerospace Engineering: Aerodynamics Fundamentals, Airfoils and Wings, Drag, and Compressible Flow

> **Part 1 of 5** of the *Aerospace Engineering* reference (plugin `aerospace-engineering`), covering §0–§4. Sibling skills: `aero-performance-stability-and-propulsion` (§5–§7), `aero-structures-aeroelasticity-and-avionics` (§8–§10), `aero-drones-launch-vehicles-flight-test-and-design` (§11–§14), `aero-reference` (§15–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Aerodynamics, structures and flight mechanics are settled — Lanchester-Prandtl circulation theory, the Breguet range equation, von Karman. Two regulatory areas moved. See §16 → `aero-reference` for BVLOS drone rules and eVTOL certification.

> **Scope.** Complements a rocket-science reference (propulsion physics, orbital
> mechanics, reentry), a flight-software reference (avionics and DO-178C), and a
> space-exploration reference. ⚠️ **This is vehicle engineering: how air vehicles and
> launchers are actually designed.**
>
> **⚠️ GOTCHA** boxes mark misconceptions and killers — and aerospace has both in
> quantity.
>
> **The three ideas that organize the field:**
> 1. **⚠️ Lift comes from turning the flow, and the popular explanation is wrong.**
>    Newton's third law and circulation both describe it correctly; "equal transit time"
>    does not, and it's what most people were taught (§1.2).
> 2. **⚠️ Aircraft design is a convergence loop, not a sequence.** Weight drives lift
>    drives wing area drives weight. **You iterate to a fixed point, and everything is
>    coupled to everything** (§14 → `aero-drones-launch-vehicles-flight-test-and-design`).
> 3. **⚠️ Margins in aerospace are small and the consequences are absolute.** Structural
>    factor of safety is typically **1.5**, against 3–5 in civil engineering. **Every
>    kilogram is fought for, which is why aerospace failures are rarely about ignorance
>    and usually about a margin that was correct on paper** (§8 → `aero-structures-aeroelasticity-and-avionics`, §13 → `aero-drones-launch-vehicles-flight-test-and-design`).

---

## §0. Routing

| You want... | Go to |
|---|---|
| **Aerodynamics fundamentals** | **§1** |
| Airfoils and wings | §2 |
| **Drag** | **§3** |
| Compressible and supersonic flow | §4 |
| **Performance** | **§5 → `aero-performance-stability-and-propulsion`** |
| **Stability and control** | **§6 → `aero-performance-stability-and-propulsion`** |
| Air-breathing propulsion | §7 → `aero-performance-stability-and-propulsion` |
| Structures and materials | §8 → `aero-structures-aeroelasticity-and-avionics` |
| **Aeroelasticity and flutter** | **§9 → `aero-structures-aeroelasticity-and-avionics`** |
| Flight controls and avionics | §10 → `aero-structures-aeroelasticity-and-avionics` |
| **Drones and UAS** | **§11 → `aero-drones-launch-vehicles-flight-test-and-design`** |
| Launch vehicles | §12 → `aero-drones-launch-vehicles-flight-test-and-design` |
| **Flight test and certification** | **§13 → `aero-drones-launch-vehicles-flight-test-and-design`** |
| The design process | §14 → `aero-drones-launch-vehicles-flight-test-and-design` |
| Misconceptions | §15 → `aero-reference` |
| **What moved** | **§16 → `aero-reference`** |
| Numbers | §17 → `aero-reference` |
| Books | §18 → `aero-reference` |
| Quick reference | §19 → `aero-reference` |

---

## §1. Aerodynamics Fundamentals

### 1.1 The governing quantities
```
Dynamic pressure   q = ½ρV²      ⚠️ everything aerodynamic scales with this
Lift               L = ½ρV²S·C_L
Drag               D = ½ρV²S·C_D
Reynolds number    Re = ρVL/μ    ⚠️ inertial/viscous — sets laminar vs turbulent
Mach number        M = V/a       ⚠️ compressibility
```
**⚠️ `C_L` and `C_D` are non-dimensional and that's the point**: they let you transfer
wind-tunnel results to full-scale aircraft **provided Reynolds and Mach match** —
⚠️ **and matching both simultaneously at model scale is often impossible, which is the
central difficulty of experimental aerodynamics.**

### 1.2 ⚠️ How lift actually works
> **⚠️ GOTCHA — the "equal transit time" explanation is simply false, and it is what most
> people were taught.** ⚠️ **It claims air over the longer upper surface must travel faster
> to "meet up" with air below. There is no physical reason parcels must meet, and
> measurement shows upper-surface flow arrives *earlier*, not simultaneously.**
> **The explanation also fails to account for symmetric airfoils, flat plates, and
> inverted flight, all of which generate lift perfectly well.**

**⚠️ Two correct and complementary explanations:**
- **Newtonian / momentum**: ⚠️ **the wing deflects air downward; the reaction force is
  lift.** `L = ṁ·Δv` in essence. **Correct, intuitive, and doesn't tell you how much.**
- **Circulation / Kutta-Joukowski**: `L' = ρV∞Γ` — ⚠️ **lift per unit span equals density ×
  freestream velocity × circulation.** **The Kutta condition** (⚠️ **flow must leave the
  sharp trailing edge smoothly**) **determines `Γ` uniquely, which is what makes the
  theory predictive.** **This is the quantitative version.**

**⚠️ They are not competing explanations — they are the same physics in different
bookkeeping.** **Bernoulli is valid along a streamline and correctly relates the pressure
field to the velocity field; the error is in the false claim about *why* velocities
differ, not in Bernoulli itself.**

**Boundary layer**: ⚠️ **the thin region where viscosity matters and velocity goes from
zero at the wall to freestream.** **Laminar (low drag, easily separated) vs turbulent
(higher skin friction, ⚠️ far more resistant to separation — which is why turbulators and
vortex generators are deliberately added).**
**⚠️ Separation** occurs under an adverse pressure gradient; ⚠️ **it is the mechanism
behind stall, and it is a boundary-layer phenomenon, not a wing-shape phenomenon.**

---

## §2. Airfoils and Wings

**Geometry**: chord, camber, thickness, leading-edge radius. **NACA series** (⚠️ **4-digit
digits literally encode camber, camber position and thickness**), supercritical
(⚠️ **flattened upper surface delays shock formation — §4**), laminar-flow sections.

**`C_L` vs angle of attack** is linear until stall.
> **⚠️ GOTCHA — stall is a function of ANGLE OF ATTACK, not airspeed.** ⚠️ **An aircraft
> can stall at any speed and any attitude.** **The "stall speed" in the manual is the
> speed at which 1g level flight requires the critical AoA — change the load factor and
> it changes: `V_stall ∝ √n`.** **A 2g turn raises stall speed by ~41%.** ⚠️ **This
> misconception has killed people, which is why AoA indicators exist and why stall
> warning is AoA-based.**

**⚠️ Finite wings differ fundamentally from 2D airfoils**: **pressure equalization at the
tips creates trailing vortices, which induce a downwash, which tilts the local lift vector
backwards.** ⚠️ **That backwards component IS induced drag — it is the unavoidable price
of generating lift with a finite wing** (§3).
```
Aspect ratio AR = b²/S     ⚠️ high AR = low induced drag (gliders, airliners)
                            low AR = structurally light, manoeuvrable (fighters)
Elliptical lift distribution ⚠️ minimizes induced drag — the Spitfire's famous rationale
Taper, sweep, twist (washout — ⚠️ makes the root stall first, preserving aileron authority)
```
**High-lift devices**: flaps (⚠️ **increase camber and sometimes area**), slats
(⚠️ **re-energize the boundary layer to delay separation to higher AoA**), and the
resulting trade of `C_L,max` against drag.

---

## §3. Drag

```
PARASITE (independent of lift, ⚠️ ∝ V²)
  Skin friction   ⚠️ dominant on slender/wetted-area-heavy vehicles
  Form/pressure   from separation — streamlining attacks this
  Interference    junctions between components; ⚠️ fairings exist for this
INDUCED (from lift, ⚠️ ∝ 1/V²)
  C_Di = C_L²/(π·AR·e)      e = Oswald efficiency (~0.7–0.9)
WAVE (⚠️ transonic and above — shock losses, §4)
```
**⚠️ The drag polar and its consequence:** `C_D = C_D0 + C_L²/(πARe)`.
**Because parasite drag rises with `V²` and induced drag falls with `1/V²`, total drag has
a minimum** — ⚠️ **and that speed, where induced equals parasite drag, gives maximum
`L/D`, best glide range, and best endurance conditions.** **Flying slower than best-glide
speed increases drag, which is counterintuitive and operationally important.**

**⚠️ `L/D` is the master efficiency figure**: ~15–20 for a light aircraft, ~17–20 for an
airliner, **40–70 for a high-performance sailplane**, ⚠️ **and 4–6 for the Space Shuttle
on approach, which is why it landed like a brick.**

---

## §4. Compressible and Supersonic Flow

**⚠️ Below M ≈ 0.3, air is effectively incompressible. Above it, density changes matter.**
```
Subsonic     M < 0.8      Transonic  0.8–1.2  ⚠️ THE hard regime — mixed subsonic and
                                     supersonic flow, shocks forming on the wing
Supersonic   1.2–5        Hypersonic M > 5    ⚠️ real gas effects, dissociation
```
**⚠️ Shock waves** — discontinuous jumps in pressure, density and temperature.
**Normal shocks** are always to subsonic downstream; **oblique** turn the flow;
**expansion fans** (Prandtl-Meyer) accelerate it.
**⚠️ Critical Mach number** is where flow first reaches M=1 somewhere on the wing;
**drag divergence** follows as shocks form and cause wave drag and shock-induced
separation.

**⚠️ The transonic fixes, and each has a clear physical reason**: **swept wings**
(⚠️ **only the velocity component normal to the leading edge matters, so sweep effectively
reduces it**), **supercritical airfoils**, **area ruling** (⚠️ **the "Coke bottle" fuselage
— smooth the total cross-sectional area distribution and transonic drag falls
dramatically**).

**⚠️ Aerodynamic centre shifts aft** from ~25% chord subsonically to ~50% supersonically —
⚠️ **which produces a large nose-down trim change and is why Concorde pumped fuel between
tanks to move its CG.**

**Hypersonics**: ⚠️ **aerodynamic heating scales roughly with `V³`, which is why reentry is
a thermal problem rather than a drag problem** (see a rocket-science reference).
