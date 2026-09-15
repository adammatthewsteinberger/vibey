---
name: aero-performance-stability-and-propulsion
description: "Use when sizing or flying the aircraft: performance including the Breguet range equation, climb, turn and field-length constraints and the drag polar; static and dynamic stability, the control axes, trim and the handling-qualities modes; and air-breathing propulsion covering the engine cycles, thrust and specific fuel consumption, and propeller and turbofan behaviour."
---

# Aerospace Engineering: Performance, Stability and Control, and Air-Breathing Propulsion

> **Part 2 of 5** of the *Aerospace Engineering* reference (plugin `aerospace-engineering`), covering §5–§7. Sibling skills: `aero-aerodynamics-airfoils-and-compressible-flow` (§0–§4), `aero-structures-aeroelasticity-and-avionics` (§8–§10), `aero-drones-launch-vehicles-flight-test-and-design` (§11–§14), `aero-reference` (§15–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
>    does not, and it's what most people were taught (§1.2 → `aero-aerodynamics-airfoils-and-compressible-flow`).
> 2. **⚠️ Aircraft design is a convergence loop, not a sequence.** Weight drives lift
>    drives wing area drives weight. **You iterate to a fixed point, and everything is
>    coupled to everything** (§14 → `aero-drones-launch-vehicles-flight-test-and-design`).
> 3. **⚠️ Margins in aerospace are small and the consequences are absolute.** Structural
>    factor of safety is typically **1.5**, against 3–5 in civil engineering. **Every
>    kilogram is fought for, which is why aerospace failures are rarely about ignorance
>    and usually about a margin that was correct on paper** (§8 → `aero-structures-aeroelasticity-and-avionics`, §13 → `aero-drones-launch-vehicles-flight-test-and-design`).

---

## §5. Performance

**Steady level flight**: `L = W`, `T = D`.
**⚠️ Breguet range equation** — the single most important performance relation:
```
Jet:      R = (V/c)·(L/D)·ln(W_i/W_f)
Propeller: R = (η/c)·(L/D)·ln(W_i/W_f)
```
⚠️ **Range depends on aerodynamic efficiency (L/D), propulsive efficiency (SFC), and the
LOGARITHM of the weight fraction.** **The log is the crucial part: doubling fuel does not
double range.** **This is the atmospheric sibling of the rocket equation, and it has the
same structure for the same reason.**

**Climb**: `rate of climb = excess power / weight`. ⚠️ **Best rate of climb (V_y) and best
angle of climb (V_x) are different speeds and answer different questions — V_x for
obstacle clearance, V_y for getting to altitude quickly.**
**Turning**: `n = 1/cos φ`; ⚠️ **a 60° bank is 2g and raises stall speed by 41%.**
**The `V-n` diagram** bounds manoeuvre and gust loads.
**Takeoff and landing distance**, **service ceiling**, ⚠️ **and the payload-range diagram,
whose kinks correspond to trading payload for fuel at MTOW.**

---

## §6. Stability and Control

**⚠️ Static stability is the tendency to return toward equilibrium; dynamic stability is
whether the resulting oscillation damps.** **You can be statically stable and dynamically
unstable.**

**⚠️ Longitudinal stability comes down to CG position:**
- **The neutral point** is where `dC_m/dα = 0`. ⚠️ **CG ahead of it = stable; static
  margin is the distance between them as a fraction of chord.**
- **⚠️ Forward CG: more stable, heavier control forces, higher stall speed, more trim
  drag. Aft CG: lighter controls, less trim drag, and dangerous past the aft limit.**
  **This is why CG limits exist and why loading matters.**
- ⚠️ **Deliberately relaxed static stability (fighters) buys manoeuvrability and trim drag
  reduction, and it makes the aircraft unflyable without a flight control computer** (§10 → `aero-structures-aeroelasticity-and-avionics`).

**Lateral-directional**: dihedral effect (roll due to sideslip), weathercock stability.
**⚠️ The classic dynamic modes:**
```
Phugoid          ⚠️ slow, lightly damped exchange of altitude and airspeed. Easily flown
Short period     fast pitch oscillation. ⚠️ Must be well damped — it's what the pilot feels
Dutch roll       ⚠️ coupled yaw-roll oscillation; yaw dampers exist for this
Spiral mode      slow divergence into a tightening turn
Roll subsidence  heavily damped, benign
```
**Control surfaces**: elevator, aileron (⚠️ **adverse yaw — the down-going aileron adds
more drag, so you need rudder coordination or differential/Frise ailerons**), rudder,
plus spoilers, canards, elevons, ruddervators.
**⚠️ Spin** — autorotation in a stalled condition, with one wing more stalled than the
other. **Recovery is type-specific and the standard sequence (PARE) is not universal.**

---

## §7. Air-Breathing Propulsion

**⚠️ Brayton cycle**: intake → compressor → combustor → turbine → nozzle.
```
Turbojet     ⚠️ high exhaust velocity — efficient only at high speed
Turbofan     ⚠️ bypass air accelerated moderately. HIGH BYPASS = high efficiency
             at subsonic speed. This is why airliners look the way they do
Turboprop    very high mass flow, low velocity; ⚠️ best below ~M 0.6
Turboshaft   helicopters
Ramjet       ⚠️ no moving compressor — needs M > ~2 and can't start from rest
Scramjet     supersonic combustion, M > 5
Piston/electric   light aircraft, drones (§11)
```
> **⚠️ GOTCHA — the propulsive efficiency principle explains the whole table.**
> ⚠️ **`η_p ≈ 2/(1 + V_exhaust/V_aircraft)`.** **Efficiency is maximized when exhaust
> velocity is only slightly above flight velocity** — **so for a given thrust, accelerating
> a LARGE mass of air a LITTLE beats accelerating a small mass a lot.** **That single
> relation is why bypass ratios climbed from 1 to 12+, why propellers beat jets at low
> speed, and why a helicopter rotor is enormous.**

**⚠️ Thrust falls with altitude** (density) **and with airspeed** for a turbojet; **thermal
efficiency rises with pressure ratio and turbine inlet temperature** — ⚠️ **which is why
turbine blade materials and cooling are the technology that gates engine performance.**
**Single-crystal superalloys with film cooling run above the alloy's melting point.**
