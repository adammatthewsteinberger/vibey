---
name: rail-adhesion-resistance-traction-physics-and-geometry
description: "Use when a rail question comes down to physics: adhesion and rolling resistance and why steel on steel changes everything, traction and braking force limits and stopping distance, the wheel-rail interface including conicity, hunting, creep and contact stress, and gradients, curves, cant and cant deficiency. Includes the router for the whole rail engineering reference."
---

# Rail Engineering: Adhesion and Resistance, Traction and Braking, the Wheel-Rail Interface, and Gradients, Curves and Cant

> **Part 1 of 6** of the *Locomotion and Train Technologies* reference (plugin `locomotion-and-train-technologies`), covering §0–§4. Sibling skills: `rail-steam-diesel-electric-and-alternative-traction` (§5–§9), `rail-track-structure-welded-rail-switches-and-electrification` (§10–§13), `rail-signalling-interlocking-train-protection-and-safety` (§14–§17), `rail-rolling-stock-braking-capacity-and-service-types` (§18–§25), `rail-reference` (§26–§31). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The physics and most of the engineering is a century settled. Two areas moved. See §26 → `rail-reference` for European signalling deployment, and rail decarbonisation traction choices.

> **⚠️ Rail exists because of one number: steel wheel on steel rail has a rolling
> resistance roughly an order of magnitude below rubber on road.** ⚠️ **Everything good
> about rail — the efficiency, the enormous train weights, the low energy per tonne-km —
> follows from that.** **And ⚠️ everything HARD about rail follows from the same fact: the
> same low friction that makes it efficient means trains cannot stop quickly, cannot climb
> steeply, and cannot steer.**
>
> **Complements a civil/industrial engineering reference (infrastructure and safety
> systems), a thermodynamics reference (traction thermodynamics), and a power engineering
> reference (electrification).**
>
> **⚠️ GOTCHA** boxes mark the physics people get backwards and the folklore that's wrong.
>
> **The three ideas that organize this document:**
> 1. **⚠️ Low adhesion is the defining constraint** (§1). **Braking distance, gradient
>    limits, and the entire existence of signalling systems all trace back to it — a train
>    cannot stop within the driver's sighting distance, so it must be told what's ahead.**
> 2. **⚠️ The wheelset steers itself, and that's why railways work** (§3). **Coned wheels
>    on a solid axle self-centre — the flanges are a last-resort guard, not the steering
>    mechanism.**
> 3. **⚠️ Capacity is set by signalling and by the SLOWEST train, not by top speed** (§20 → `rail-rolling-stock-braking-capacity-and-service-types`).
>    **Mixing traffic speeds destroys capacity faster than anything else.**

---

## §0. Routing

| You want... | Go to |
|---|---|
| **⚠️ Adhesion and resistance** | **§1** |
| Traction and braking | §2 |
| **⚠️ Wheel-rail interface** | **§3** |
| Gradients, curves, cant | §4 |
| Steam | §5 → `rail-steam-diesel-electric-and-alternative-traction` |
| **Diesel** | **§6 → `rail-steam-diesel-electric-and-alternative-traction`** |
| **Electric traction** | **§7 → `rail-steam-diesel-electric-and-alternative-traction`** |
| Power electronics | §8 → `rail-steam-diesel-electric-and-alternative-traction` |
| Alternative traction | §9 → `rail-steam-diesel-electric-and-alternative-traction` |
| **⚠️ Track structure** | **§10 → `rail-track-structure-welded-rail-switches-and-electrification`** |
| **⚠️ Continuous welded rail** | **§11 → `rail-track-structure-welded-rail-switches-and-electrification`** |
| Switches and crossings | §12 → `rail-track-structure-welded-rail-switches-and-electrification` |
| Electrification systems | §13 → `rail-track-structure-welded-rail-switches-and-electrification` |
| **⚠️ Block signalling** | **§14 → `rail-signalling-interlocking-train-protection-and-safety`** |
| Interlocking | §15 → `rail-signalling-interlocking-train-protection-and-safety` |
| **ATP, ETCS, PTC, CBTC** | **§16 → `rail-signalling-interlocking-train-protection-and-safety`** |
| Safety and failure modes | §17 → `rail-signalling-interlocking-train-protection-and-safety` |
| Rolling stock and bogies | §18 → `rail-rolling-stock-braking-capacity-and-service-types` |
| Braking systems | §19 → `rail-rolling-stock-braking-capacity-and-service-types` |
| **⚠️ Capacity** | **§20 → `rail-rolling-stock-braking-capacity-and-service-types`** |
| Freight | §21 → `rail-rolling-stock-braking-capacity-and-service-types` |
| Maintenance | §22 → `rail-rolling-stock-braking-capacity-and-service-types` |
| High-speed rail | §23 → `rail-rolling-stock-braking-capacity-and-service-types` |
| Urban rail | §24 → `rail-rolling-stock-braking-capacity-and-service-types` |
| **⚠️ Maglev and hyperloop** | **§25 → `rail-rolling-stock-braking-capacity-and-service-types`** |
| **What's live** | **§26 → `rail-reference`** |
| Misconceptions, numbers | §27–§28 → `rail-reference` |
| Books, quick ref, method | §29–§31 → `rail-reference` |

---

# PART I — THE PHYSICS

## §1. ⚠️ Adhesion and Resistance

```
⚠️ ADHESION COEFFICIENT (steel on steel)
   ⚠️ Dry, clean rail:     ~0.20–0.35
   ⚠️ Wet rail:            ~0.15–0.20
   ⚠️ Contaminated (leaves, oil, frost): ⚠️ can fall below 0.05
   Compare rubber on dry road: ~0.7–0.9
⚠️ ROLLING RESISTANCE  roughly 1/10th that of road vehicles.
   ⚠️ THE reason rail exists
⚠️ CONTACT PATCH  about the size of a small coin, carrying tonnes.
   ⚠️ Contact stresses approach the yield strength of steel — which is
   why rail and wheels wear, spall and fatigue (§22)
```
**⚠️ The Davis equation** describes total train resistance:
```
⚠️ R = A + Bv + Cv²
   A  ⚠️ rolling and bearing resistance (roughly constant)
   Bv ⚠️ flange and track interaction, linear in speed
   Cv² ⚠️ AERODYNAMIC — dominates at high speed (§23)
```
⚠️ **The cubic power consequence: power required rises with the CUBE of speed in the
aerodynamic regime**, **which is why high-speed rail is far more about aerodynamics and
installed power than about track.**
> **⚠️ GOTCHA — the low friction cuts both ways and this is the master fact of railway
> operations.** ⚠️ **A freight train at 100 km/h may need well over a kilometre to stop —
> far beyond the driver's sighting distance.** **⚠️ THIS is why railways need signalling
> (§14 → `rail-signalling-interlocking-train-protection-and-safety`): the driver physically cannot see far enough ahead to stop, so the system must
> tell them what lies beyond.** **Road vehicles can drive on sight; trains fundamentally
> cannot.**

**⚠️ Sanding, and its limits**: ⚠️ **sand improves adhesion for traction and braking but is
finite, contaminates ballast, and can insulate track circuits** (§14 → `rail-signalling-interlocking-train-protection-and-safety`) — **a real
interaction failure where a train becomes invisible to the signalling.**
**⚠️ Low-adhesion season is a genuine engineering problem, not an excuse**: ⚠️ **crushed
leaf material forms a hard, slick pectin layer bonded to the railhead** — **it is not
"leaves on the line" in the trivial sense, and railheads are cleaned with water jets and
treated with friction modifiers.**

---

## §2. Traction and Braking

**⚠️ Tractive effort is limited by TWO ceilings and the binding one changes with speed:**
```
⚠️ ADHESION LIMIT   TE_max = adhesive weight × adhesion coefficient
   ⚠️ Dominates at LOW speed. More weight on driven axles = more pull
⚠️ POWER LIMIT      TE = Power / velocity
   ⚠️ Dominates at HIGH speed — TE falls hyperbolically as speed rises
```
⚠️ **This is why a locomotive's TE curve is flat at low speed then falls away, and why
"horsepower" and "pulling power" are different questions.**
**⚠️ Axle load and the number of driven axles matter enormously**: ⚠️ **a Co-Co locomotive
(six driven axles) outpulls a Bo-Bo (four) of the same power at low speed, because
adhesive weight is the limit there.**
**⚠️ Wheelslip control** — ⚠️ **modern AC drives detect incipient slip and modulate torque
per axle in milliseconds, which raised usable adhesion substantially over DC-era
equipment** (§8 → `rail-steam-diesel-electric-and-alternative-traction`).
**⚠️ Braking** (detailed in §19 → `rail-rolling-stock-braking-capacity-and-service-types`): **friction (tread, disc), dynamic (rheostatic and
regenerative), and ⚠️ non-adhesion brakes (magnetic track brake, eddy current) which do NOT
depend on wheel-rail adhesion and are therefore the fallback in low-adhesion conditions.**

---

## §3. ⚠️ The Wheel-Rail Interface

> **⚠️ The most elegant piece of engineering in the whole subject, and almost universally
> misunderstood.**
> ⚠️ **Railway wheels are CONED (typically around 1:20 to 1:40), and the two wheels are
> RIGIDLY fixed to a common axle.** **⚠️ When the wheelset moves off-centre, the wheel on
> one side runs on a larger effective rolling radius and the other on a smaller one — so
> that side travels further per revolution and the wheelset STEERS ITSELF BACK.**
> **⚠️ THE FLANGES ARE NOT THE STEERING MECHANISM.** **They are a last-resort guard against
> derailment; in normal running they should rarely contact the rail, and flange contact is
> a sign of something wrong.**

**⚠️ HUNTING OSCILLATION is the price of that self-steering**: ⚠️ **the restoring action
overshoots, producing a lateral oscillation that grows with speed until, above a critical
speed, it becomes unstable.** **⚠️ Hunting is the fundamental speed limit of a conventional
bogie, and it's managed with yaw dampers, suspension design and conicity choice** (§18 → `rail-rolling-stock-braking-capacity-and-service-types`).
**⚠️ Curving**: ⚠️ **on a curve the outer wheel needs to travel further, and coning provides
exactly that if the curve is gentle enough.** **On tight curves the geometry runs out,
flanges contact, and you get wear and squeal** — **hence lubrication and, on very tight
curves, check rails.**
**⚠️ Wheel and rail profiles are matched and wear into each other** — ⚠️ **a worn wheel on a
worn rail can be stable while a new wheel on that rail is not, which is why profile
management is a maintenance discipline** (§22 → `rail-rolling-stock-braking-capacity-and-service-types`).

---

## §4. Gradients, Curves and Cant

```
⚠️ GRADIENTS are brutally limited by adhesion (§1)
   ⚠️ Main line typically ≤1–1.5% · ⚠️ 2.5–3% is steep and needs
   assistance · rack railways for anything beyond
   ⚠️ "Ruling gradient" sets the maximum train weight for the route
⚠️ CURVE RADIUS  limited by cant, speed and comfort
⚠️ CANT (superelevation)  the outer rail raised so the resultant of
   gravity and centrifugal force points through the track
   ⚠️ CANT DEFICIENCY  running faster than the balanced speed —
   permitted within limits, and what TILTING TRAINS exploit
   ⚠️ CANT EXCESS  running slower than balanced — a real problem where
   fast passenger and slow freight share track, since ONE cant value
   cannot suit both (§20)
⚠️ TRANSITION CURVES  the clothoid/spiral between straight and curve,
   with cant applied gradually. ⚠️ Without it, lateral acceleration
   would step discontinuously — uncomfortable and damaging
```
**⚠️ The mixed-traffic cant conflict is a genuinely under-appreciated constraint**:
⚠️ **cant chosen for 200 km/h passenger trains puts heavy freight running at 80 km/h into
significant cant excess, which loads the inner rail and accelerates wear.** **It's one
reason dedicated high-speed lines exist.**

---

# PART II — TRACTION
