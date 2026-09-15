---
name: ship-resistance-propulsion-seakeeping-and-manoeuvring
description: "Use for hydrodynamics and performance: resistance and powering with the frictional, wave-making and appendage components and how power scales with speed, propulsion including propeller design, cavitation and the alternatives, seakeeping and motion response in a seaway, and manoeuvring with rudders, turning circles and course stability."
---

# Maritime Engineering: Resistance and Powering, Propulsion, Seakeeping, and Manoeuvring

> **Part 2 of 6** of the *Maritime Engineering and Building Ships* reference (plugin `maritime-engineering-and-building-ships`), covering §5–§8. Sibling skills: `ship-design-spiral-hydrostatics-stability-and-hull-form` (§0–§4), `ship-structure-materials-machinery-systems-and-types` (§9–§13), `ship-shipyard-build-welding-launch-and-naval-vessels` (§14–§18), `ship-class-flag-imo-safety-operations-and-losses` (§19–§23), `ship-reference` (§24–§29). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The naval architecture is settled. Two areas are in flux. See §24 → `ship-reference` for IMO carbon regulation, and the alternative fuel orderbook.

> **⚠️ A ship is the only major engineered structure that must simultaneously float, stay
> upright, move efficiently, survive an environment that actively tries to destroy it, and
> do all of it while UNATTENDED BY ANY RESCUE for days at a time.**
>
> **Complements a rail reference (guided transport), an automobiles reference (propulsion
> and diagnosis), a manufacturing reference (fabrication and tolerancing), and a
> thermodynamics reference (resistance and powering physics).**
>
> **⚠️ GOTCHA** boxes mark the intuitions that sink things.
>
> **The three ideas that organize this document:**
> 1. **⚠️ STABILITY IS NOT BUOYANCY** (§3 → `ship-design-spiral-hydrostatics-stability-and-hull-form`). **Whether a ship floats and whether it floats
>    UPRIGHT are separate calculations, and the second is what kills people. Free surface
>    effect in particular destroys stability without changing weight at all.**
> 2. **⚠️ The design spiral exists because nothing can be fixed independently** (§1 → `ship-design-spiral-hydrostatics-stability-and-hull-form`).
>    **Change the hull to reduce resistance and you change displacement, stability,
>    structure, cost and capacity. There is no linear path through a ship design.**
> 3. **⚠️ Class and flag are the mechanism** (§19 → `ship-class-flag-imo-safety-operations-and-losses`). **A ship's design, construction and
>    entire life are governed by a private-society-plus-treaty system with no direct
>    analogue in most other engineering — and understanding it explains almost everything
>    about how ships get built the way they do.**

---

## §5. Resistance and Powering

```
⚠️ THE COMPONENTS
   ⚠️ FRICTIONAL  ⚠️ dominant for slow full ships. Scales with
      WETTED SURFACE AREA and roughly with speed squared.
      ⚠️ Hull fouling attacks exactly this (§22)
   ⚠️ WAVE-MAKING  ⚠️ dominant at high speed and rises VERY steeply.
      ⚠️ The ship is generating waves and paying for them
   Form/viscous pressure · appendage · air resistance
⚠️ FROUDE NUMBER Fn = V/√(gL)  ⚠️ the governing similarity parameter
   ⚠️ HULL SPEED — a displacement hull approaches a wall where wave-
   making resistance rises near-vertically. ⚠️ THIS IS WHY LONGER
   SHIPS ARE FASTER: the limit scales with √L
⚠️ POWER SCALES ROUGHLY WITH SPEED CUBED  ⚠️ so a 10% speed cut can
   cut fuel by roughly 25-30%. ⚠️ THIS IS THE ENTIRE LOGIC OF SLOW
   STEAMING, and it's the cheapest decarbonization lever available (§24)
⚠️ MODEL TESTING and FROUDE'S METHOD  ⚠️ you cannot match Reynolds
   and Froude numbers simultaneously at model scale, so you scale
   the wave-making from the model and CALCULATE the friction
   separately. ⚠️ CFD now supplements but has not replaced tank testing
```
**⚠️ Margins**: ⚠️ **sea margin (weather and fouling) and engine margin are added on top of
calm-water trial power, and a ship that only makes its speed in flat calm on a clean hull
is a design failure.**

---

## §6. Propulsion

**⚠️ The screw propeller**: ⚠️ **pitch, diameter, blade area ratio, and the fundamental
trade — a large slow-turning propeller is more efficient, and draught and hull clearance
limit how large you can go.**
> **⚠️ GOTCHA — CAVITATION is the propeller failure mode that has no everyday analogue.**
> ⚠️ **Local pressure on the blade back drops below vapour pressure, vapour bubbles form,
> and they COLLAPSE violently on re-pressurization.** **⚠️ The result is erosion that eats
> metal, vibration, noise and lost thrust.** **⚠️ It is a PRESSURE phenomenon, not a
> temperature one, and it constrains blade loading and hence propeller design.**

**⚠️ Other arrangements**: **controllable pitch propellers (⚠️ useful where the engine
can't change speed or reversing is frequent), ducted/Kort nozzles (⚠️ efficient at high
thrust and low speed — tugs and trawlers), azimuth thrusters and pods (⚠️ propulsion and
steering combined; transformed offshore and cruise vessel manoeuvring), waterjets
(high speed, shallow draught), and Voith Schneider cycloidal drives.**
**⚠️ Efficiency chain**: ⚠️ **the useful number is quasi-propulsive coefficient — hull
efficiency, open water efficiency and relative rotative efficiency multiplied together.**
**⚠️ Energy saving devices** (pre-swirl stators, ducts, rudder bulbs) ⚠️ **recover swirl
energy and deliver real but modest single-digit gains; claims should be treated with the
scepticism due to any retrofit market.**
**⚠️ Wind-assist** (rotor sails, suction wings, kites) ⚠️ **is genuinely re-emerging, and
its economics depend heavily on route and on the regulatory value of the saved fuel** (§24 → `ship-reference`).

---

## §7. Seakeeping

**⚠️ Six degrees of freedom**: ⚠️ **surge, sway, heave (translations); roll, pitch, yaw
(rotations).** **⚠️ Roll is the lightly damped one and therefore the problem.**
**⚠️ Natural roll period** depends on GM (§3 → `ship-design-spiral-hydrostatics-stability-and-hull-form`) — ⚠️ **stiff ship, short violent period; tender
ship, long slow period.** **⚠️ SYNCHRONOUS ROLLING occurs when encounter period matches the
natural period, and the response can grow alarmingly.**
**⚠️ PARAMETRIC ROLLING** is ⚠️ **the counterintuitive one: in head or following seas —
where you would expect no roll excitation at all — the waterplane changes as waves pass,
GM oscillates, and roll can build rapidly to extreme angles.** ⚠️ **It has caused major
container losses on ships that were entirely stable by conventional measures.**
**⚠️ Mitigation**: **bilge keels (⚠️ cheap and surprisingly effective), anti-roll tanks,
fin stabilizers (⚠️ only work with way on), and — most importantly — ⚠️ CHANGING COURSE OR
SPEED, which is free.**
**⚠️ Slamming, deck wetness, propeller emergence and green water** all impose VOLUNTARY
speed reduction — ⚠️ **the master slows down, so seakeeping determines the speed actually
achieved in service, not the trial speed.**

---

## §8. Manoeuvring

**⚠️ The rudder generates a LIFT force**, ⚠️ **and the ship turns because that force creates
a moment — the ship then pivots about a point roughly a third of the length from the bow.**
**⚠️ Standard measures**: **turning circle (advance, transfer, tactical diameter), zig-zag
manoeuvre for course-keeping, and crash-stop distance.**
> **⚠️ GOTCHA — a large ship's stopping distance is measured in KILOMETRES and MINUTES, and
> a loaded VLCC may need well over a ship-length just to begin responding.** ⚠️ **There is
> no braking. Reversing the propeller on a large ship also destroys steering, because
> rudder effectiveness depends on propeller wash over it.**
> **⚠️ This is why collision avoidance at sea is about EARLY, LARGE, EARLY-COMMUNICATED
> alterations, and why COLREGS is built around predictability rather than reaction.**

**⚠️ Shallow water effects**: ⚠️ **SQUAT (the ship sinks bodily and trims as it moves in
shallow water — a genuine grounding cause), bank effect, and interaction between passing
ships.**
**⚠️ Directional stability versus turning ability trade off** — ⚠️ **a ship that turns
eagerly is tiring to steer straight.**
