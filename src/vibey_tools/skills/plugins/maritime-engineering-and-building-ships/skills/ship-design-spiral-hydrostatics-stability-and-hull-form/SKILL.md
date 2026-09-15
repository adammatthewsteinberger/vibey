---
name: ship-design-spiral-hydrostatics-stability-and-hull-form
description: "Use at the start of any ship question: the design spiral and why ship design iterates rather than proceeds, buoyancy and hydrostatics, stability including metacentric height, righting arm curves, free surface effect and the damaged-stability requirement, and hull form and the parameters that drive everything downstream. Includes the router for the whole maritime engineering reference."
---

# Maritime Engineering: The Design Spiral, Buoyancy and Hydrostatics, Stability, and Hull Form

> **Part 1 of 6** of the *Maritime Engineering and Building Ships* reference (plugin `maritime-engineering-and-building-ships`), covering §0–§4. Sibling skills: `ship-resistance-propulsion-seakeeping-and-manoeuvring` (§5–§8), `ship-structure-materials-machinery-systems-and-types` (§9–§13), `ship-shipyard-build-welding-launch-and-naval-vessels` (§14–§18), `ship-class-flag-imo-safety-operations-and-losses` (§19–§23), `ship-reference` (§24–§29). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
> 1. **⚠️ STABILITY IS NOT BUOYANCY** (§3). **Whether a ship floats and whether it floats
>    UPRIGHT are separate calculations, and the second is what kills people. Free surface
>    effect in particular destroys stability without changing weight at all.**
> 2. **⚠️ The design spiral exists because nothing can be fixed independently** (§1).
>    **Change the hull to reduce resistance and you change displacement, stability,
>    structure, cost and capacity. There is no linear path through a ship design.**
> 3. **⚠️ Class and flag are the mechanism** (§19 → `ship-class-flag-imo-safety-operations-and-losses`). **A ship's design, construction and
>    entire life are governed by a private-society-plus-treaty system with no direct
>    analogue in most other engineering — and understanding it explains almost everything
>    about how ships get built the way they do.**

---

## §0. Routing

| You want... | Go to |
|---|---|
| **The design spiral** | **§1** |
| Buoyancy and hydrostatics | §2 |
| **⚠️ Stability** | **§3** |
| Hull form | §4 |
| **Resistance and powering** | **§5 → `ship-resistance-propulsion-seakeeping-and-manoeuvring`** |
| Propulsion | §6 → `ship-resistance-propulsion-seakeeping-and-manoeuvring` |
| Seakeeping | §7 → `ship-resistance-propulsion-seakeeping-and-manoeuvring` |
| Manoeuvring | §8 → `ship-resistance-propulsion-seakeeping-and-manoeuvring` |
| **⚠️ Structure and longitudinal strength** | **§9 → `ship-structure-materials-machinery-systems-and-types`** |
| Materials and corrosion | §10 → `ship-structure-materials-machinery-systems-and-types` |
| Machinery | §11 → `ship-structure-materials-machinery-systems-and-types` |
| Ship systems | §12 → `ship-structure-materials-machinery-systems-and-types` |
| Ship types | §13 → `ship-structure-materials-machinery-systems-and-types` |
| **Shipyard process** | **§14–§15 → `ship-shipyard-build-welding-launch-and-naval-vessels`** |
| Welding and fabrication | §16 → `ship-shipyard-build-welding-launch-and-naval-vessels` |
| Launch, outfitting, trials | §17 → `ship-shipyard-build-welding-launch-and-naval-vessels` |
| Naval and specialist vessels | §18 → `ship-shipyard-build-welding-launch-and-naval-vessels` |
| **⚠️ Class, flag and IMO** | **§19 → `ship-class-flag-imo-safety-operations-and-losses`** |
| Safety regulation | §20 → `ship-class-flag-imo-safety-operations-and-losses` |
| Small craft | §21 → `ship-class-flag-imo-safety-operations-and-losses` |
| Operation and drydock | §22 → `ship-class-flag-imo-safety-operations-and-losses` |
| **⚠️ Why ships are lost** | **§23 → `ship-class-flag-imo-safety-operations-and-losses`** |
| **What's live** | **§24 → `ship-reference`** |
| Misconceptions, numbers | §25–§26 → `ship-reference` |
| Books, quick ref, method | §27–§29 → `ship-reference` |

---

## §1. The Design Spiral

**⚠️ Ship design is explicitly ITERATIVE, and the profession names the process rather than
pretending it's linear.**
```
⚠️ THE SPIRAL  requirements → ⚠️ estimate displacement → hull form →
   powering → structure → weights → ⚠️ RECHECK displacement →
   stability → cost → ⚠️ round again, tighter each time
⚠️ WHY IT SPIRALS  every parameter feeds every other. ⚠️ Adding
   steel adds weight adds displacement adds resistance adds power
   adds machinery weight adds displacement — ⚠️ the "weight spiral,"
   and it can diverge if you're careless
⚠️ THE PHASES  concept → preliminary → contract design →
   ⚠️ DETAIL/PRODUCTION design (⚠️ the largest by effort — it's the
   information the yard actually builds from)
```
**⚠️ The owner's requirements drive everything**: **cargo capacity, speed, range, draught
limits (⚠️ set by the ports and canals the ship must use), crew, and class notation.**
**⚠️ DESIGN MARGINS** are carried deliberately — ⚠️ **weight margin, KG margin, power
margin — because the ship as built is never the ship as drawn, and a design with no margin
fails its trials.**
**⚠️ The economics**: ⚠️ **ships are capital assets with 20–30 year lives, so the design
must anticipate two decades of regulation, fuel prices and trade patterns** (§24 → `ship-reference`).

---

# PART I — NAVAL ARCHITECTURE

## §2. Buoyancy and Hydrostatics

```
⚠️ ARCHIMEDES  ⚠️ a floating body displaces its own WEIGHT of water.
   ⚠️ DISPLACEMENT IS THE SHIP'S WEIGHT — the terms are the same thing
⚠️ THE KEY POINTS
   ⚠️ B — CENTRE OF BUOYANCY: centroid of the underwater volume.
      ⚠️ It MOVES as the ship heels — this is the whole of §3
   ⚠️ G — CENTRE OF GRAVITY: centroid of the ship's mass
   ⚠️ M — METACENTRE: where the vertical through the shifted B
      crosses the centreline
⚠️ TONNES PER CENTIMETRE IMMERSION (TPC) · ⚠️ MOMENT TO CHANGE TRIM
⚠️ RESERVE BUOYANCY  ⚠️ the watertight volume ABOVE the waterline.
   ⚠️ This is what freeboard actually is, and it's why load lines
   exist (§20)
⚠️ DENSITY MATTERS  ⚠️ a ship floats deeper in fresh water than salt.
   Hence the FWA (fresh water allowance) and the seasonal load line marks
```
**⚠️ Deadweight vs displacement vs tonnage — routinely confused:**
⚠️ **DISPLACEMENT is actual weight; DEADWEIGHT (DWT) is cargo plus fuel plus stores —
what the ship can carry; LIGHTSHIP is the empty ship; ⚠️ and GROSS TONNAGE is a
dimensionless VOLUME measure, not a weight at all, used for regulation and fees.**

---

## §3. ⚠️ Stability

> **⚠️ THE section. Floating and floating UPRIGHT are different problems, and ships that
> capsize usually had plenty of buoyancy.**
```
⚠️ THE MECHANISM  heel the ship → the underwater shape changes →
   ⚠️ B MOVES toward the immersed side → buoyancy up through B and
   weight down through G form a COUPLE
   ⚠️ If that couple RIGHTS the ship, it's stable. If it heels it
   further, it capsizes
⚠️ GM (metacentric height) = KM − KG  ⚠️ the initial stability measure
   ⚠️ GM POSITIVE → stable · ⚠️ GM NEGATIVE → loll or capsize
   ⚠️ GM TOO LARGE is also bad: ⚠️ a very stiff ship snaps back
   violently with a short roll period, which is uncomfortable,
   damages cargo and can break lashings (§7)
⚠️ GZ CURVE  righting lever versus heel angle. ⚠️ Initial GM is just
   the SLOPE AT THE ORIGIN — the full curve is what matters at
   large angles. ⚠️ Range of stability, angle of vanishing
   stability, area under the curve (= energy to capsize)
```
> **⚠️ GOTCHA — FREE SURFACE EFFECT is the one that catches people, because it reduces
> stability WITHOUT ADDING ANY WEIGHT.** ⚠️ **A partially filled tank lets liquid run to the
> low side as the ship heels, shifting weight in the worst possible direction and producing
> a VIRTUAL RISE IN G.** **⚠️ The effect scales with the CUBE of the tank's breadth, which
> is why tanks are subdivided longitudinally and why slack tanks are minimized.**
> **⚠️ The lethal versions: firefighting water accumulating on a car deck or in a
> superstructure; a partly flooded ro-ro deck (⚠️ a wide undivided deck is a free surface
> nightmare — the mechanism behind several major ferry disasters); and fish or grain
> shifting in bulk.**

**⚠️ Other stability killers**: ⚠️ **free liquid in cargo (liquefaction of ore concentrates
and nickel ore — a recurring cause of bulk carrier losses), ice accretion topside, water
on deck, high loading of containers, and lifting a weight with a crane (⚠️ the load acts at
the DERRICK HEAD the moment it lifts, instantly raising G).**
**⚠️ DAMAGE STABILITY** — ⚠️ **stability after flooding, calculated by the lost buoyancy or
added weight method, with SUBDIVISION and watertight bulkheads sized so the ship survives
defined damage** (§20 → `ship-class-flag-imo-safety-operations-and-losses`).
**⚠️ The inclining experiment** is how KG is determined in reality: ⚠️ **move a known weight
across the deck, measure the heel, and compute G.** **⚠️ It's done on completion because
the calculated lightship weight and centre are never exactly right.**

---

## §4. Hull Form

**⚠️ The form coefficients describe the hull in a few numbers:**
```
⚠️ Cb  BLOCK COEFFICIENT — fullness. ⚠️ ~0.5 fine/fast (warships),
   ~0.85 full/slow (bulkers and tankers). ⚠️ Full hulls carry more
   and go slower; the trade is direct
Cp prismatic · Cm midship · Cw waterplane (⚠️ drives stability
   through the second moment of the waterplane area, §3)
⚠️ RATIOS  L/B (⚠️ length drives speed potential and structural
   demand), B/T, L/D
⚠️ THE LINES PLAN  sheer, half-breadth and body plan — ⚠️ the
   three orthogonal views that define a hull, and FAIRING them
   (making them mutually consistent and smooth) is the classical
   naval architecture skill, now done in software
⚠️ BULBOUS BOW  ⚠️ creates a wave that partially cancels the bow
   wave — ⚠️ effective only near its DESIGN SPEED and draught, which
   is why slow steaming made many bulbous bows counterproductive
   and drove a wave of bow retrofits
```
