---
name: aero-drones-launch-vehicles-flight-test-and-design
description: "Use when working on a specific vehicle class or taking a design through to approval: drones and UAS with multirotor dynamics, configurations and hazards and the regulatory position, launch vehicles from an atmospheric-flight perspective, flight test and certification including the test process and the certification bases, and the aircraft design process from requirements through sizing iterations."
---

# Aerospace Engineering: Drones and UAS, Launch Vehicles, Flight Test and Certification, and the Design Process

> **Part 4 of 5** of the *Aerospace Engineering* reference (plugin `aerospace-engineering`), covering §11–§14. Sibling skills: `aero-aerodynamics-airfoils-and-compressible-flow` (§0–§4), `aero-performance-stability-and-propulsion` (§5–§7), `aero-structures-aeroelasticity-and-avionics` (§8–§10), `aero-reference` (§15–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
>    coupled to everything** (§14).
> 3. **⚠️ Margins in aerospace are small and the consequences are absolute.** Structural
>    factor of safety is typically **1.5**, against 3–5 in civil engineering. **Every
>    kilogram is fought for, which is why aerospace failures are rarely about ignorance
>    and usually about a margin that was correct on paper** (§8 → `aero-structures-aeroelasticity-and-avionics`, §13).

---

## §11. Drones and UAS

### 11.1 Multirotor dynamics
**⚠️ A quadrotor has four actuators and six degrees of freedom — it is underactuated, and
that shapes everything.** **It cannot translate without tilting.**
```
Thrust    T ∝ ω²        ⚠️ so control is quadratic in motor speed
Roll/pitch  differential thrust across opposing pairs
Yaw       ⚠️ differential TORQUE — speed up one rotation direction, slow the other.
          This is why yaw authority is weak and yaw is the slowest axis
```
**⚠️ Control architecture is nested loops**: **rate (inner, fast, gyro-driven) → attitude →
velocity → position (outer, slow, GNSS-driven).** ⚠️ **Tune inner loops first; a badly
tuned rate loop cannot be fixed by the outer loops.**
**State estimation** — ⚠️ **complementary or Kalman filter fusing IMU with magnetometer,
barometer, GNSS and optical flow.** ⚠️ **Magnetometers are routinely corrupted by motor
currents and nearby steel; most "toilet bowling" behaviour is a compass problem.**

**⚠️ Physics of scale, and it's the reason drones exist as a category**: **rotor thrust
scales with disc area while mass scales with volume**, ⚠️ **so small multirotors have
enormous thrust-to-weight and very fast attitude dynamics.** **The same design does not
scale up gracefully.**
**⚠️ Endurance is brutally limited**: **typical small multirotor 20–40 minutes**, because
**hover consumes power continuously and battery specific energy (~250–300 Wh/kg for Li-ion)
is roughly 50× worse than kerosene.** **Fixed-wing and VTOL-hybrid designs exist precisely
to escape this.**

### 11.2 Configurations and hazards
**Multirotor** (hover, simple, inefficient), **fixed-wing** (efficient, needs
launch/recovery), **VTOL hybrid** (⚠️ **tiltrotor, tailsitter, or lift+cruise — carrying
the mass of both systems is the trade**), **helicopter**, **lighter-than-air**.
**⚠️ Hazards specific to rotorcraft**: **vortex ring state** (⚠️ **descending into your own
downwash — recovery is to move laterally, not to add power**), **ground effect**, **loss
of GNSS**, **battery thermal runaway**, **prop strikes.**

### 11.3 Regulation — §16.1 for the current picture
**Core concepts**: **VLOS vs BVLOS**, **Remote ID** (⚠️ **broadcast registration and
position — a digital licence plate**), registration, **detect-and-avoid**, **UTM/U-space**,
airspace authorization (LAANC), and weight-class thresholds.
**⚠️ The regulatory dividing line everywhere is BVLOS**, because it removes the human
who was providing collision avoidance.

---

## §12. Launch Vehicles

**⚠️ Propulsion physics, the rocket equation, staging and reentry are in a rocket-science
reference.** **What's specifically vehicle engineering:**
- **⚠️ Structural mass fraction is everything.** **Tanks are the structure; propellant is
  most of the mass.** ⚠️ **Balloon tanks (Atlas) were pressure-stabilized and would
  collapse unpressurized — an extreme illustration of how hard mass is fought for.**
- **Max-Q** — ⚠️ **peak dynamic pressure, typically ~11–14 km, and the structural design
  driver for the ascent phase; vehicles throttle down through it.**
- **Aerodynamic loads and gust response during ascent**; **thrust vector control**;
  **slosh and POGO** (⚠️ **structural-propulsion coupling that destroyed vehicles before it
  was understood**).
- **Reusability** — ⚠️ **the mass and performance penalty of return propellant, legs and
  grid fins against amortized hardware cost.** **The engineering question is turnaround
  cost, not whether it can be done.**
- **Fairings, separation events** (⚠️ **each is a single-point failure opportunity**),
  **and payload environments — acoustic, vibration, shock.**

---

## §13. Flight Test and Certification

**⚠️ Certification is a large fraction of an aircraft programme's cost and schedule.**
```
FAA Part 23   normal-category (light) aircraft   ⚠️ now performance-based, not prescriptive
FAA Part 25   transport category
Part 27/29    rotorcraft
Part 33/35    engines/propellers
⚠️ Part 108 / Part 107   UAS (§16.1)
Powered-lift SFAR + Part 194  ⚠️ eVTOL operations (§16.2)
EASA CS-23/25/27/29, SC-VTOL
```
**⚠️ The type certification sequence**: **certification basis agreed → means of compliance
accepted → design and analysis → ground and structural test → flight test (with Type
Inspection Authorization for "for-credit" flying with agency pilots) → type certificate →
production certificate → air carrier certificate for commercial operation.**
⚠️ **Those last two are separate approvals, and a type certificate alone does not let you
carry paying passengers** — a distinction §16.2 → `aero-reference` shows being widely blurred.

**⚠️ Flight test discipline**: **envelope expansion incrementally** (⚠️ **especially for
flutter, §9 → `aero-structures-aeroelasticity-and-avionics`**), instrumentation and telemetry, **build-up approach**, **and test pilots as
a profession because the hazard is real.**
**Structural test**: static test to ultimate (⚠️ **often to destruction**), full-scale
fatigue test running multiple lifetimes ahead of the fleet, bird strike, and
⚠️ **the wing bend-to-failure test, which is the most photographed moment of any
programme.**

---

## §14. The Design Process

**⚠️ Conceptual → preliminary → detail, and the first phase locks in most of the cost.**
```
Requirements (payload, range, speed, field length, regulation)
  → ⚠️ THE SIZING LOOP: guess weight → estimate L/D and SFC → Breguet (§5)
    → fuel fraction → new weight → iterate to convergence
      → wing loading W/S and thrust loading T/W from constraint analysis
        → configuration → detail design → test → certify
```
**⚠️ The constraint diagram is the central design tool**: plot `T/W` against `W/S` with
lines for takeoff distance, climb gradient, cruise, ceiling and landing. ⚠️ **The feasible
region is bounded, and the design point is usually the lowest `T/W` that satisfies
everything — because thrust is expensive.**

**⚠️ Weight estimation is where programmes are won or lost**: statistical relations early,
component build-up later, ⚠️ **and weight growth during development is close to a law of
nature — carrying explicit margin is professional practice, not pessimism.**
**Multidisciplinary optimization (MDO)** couples aero, structures, propulsion and control
because ⚠️ **optimizing them separately gives a worse aircraft than optimizing them
together — the couplings are strong.**
