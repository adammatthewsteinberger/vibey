---
name: rail-rolling-stock-braking-capacity-and-service-types
description: "Use for vehicles, operations and service types: rolling stock and bogie design, braking from air brakes to blended and eddy-current systems, capacity and headway and why the timetable is the binding constraint, freight operations and axle loads, maintenance regimes and condition monitoring, high-speed rail, metro and urban rail, and an honest assessment of maglev and hyperloop."
---

# Rail Engineering: Rolling Stock and Bogies, Braking, Capacity, Freight, Maintenance, High-Speed Rail, Urban Rail, and Maglev

> **Part 5 of 6** of the *Locomotion and Train Technologies* reference (plugin `locomotion-and-train-technologies`), covering §18–§25. Sibling skills: `rail-adhesion-resistance-traction-physics-and-geometry` (§0–§4), `rail-steam-diesel-electric-and-alternative-traction` (§5–§9), `rail-track-structure-welded-rail-switches-and-electrification` (§10–§13), `rail-signalling-interlocking-train-protection-and-safety` (§14–§17), `rail-reference` (§26–§31). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
> 1. **⚠️ Low adhesion is the defining constraint** (§1 → `rail-adhesion-resistance-traction-physics-and-geometry`). **Braking distance, gradient
>    limits, and the entire existence of signalling systems all trace back to it — a train
>    cannot stop within the driver's sighting distance, so it must be told what's ahead.**
> 2. **⚠️ The wheelset steers itself, and that's why railways work** (§3 → `rail-adhesion-resistance-traction-physics-and-geometry`). **Coned wheels
>    on a solid axle self-centre — the flanges are a last-resort guard, not the steering
>    mechanism.**
> 3. **⚠️ Capacity is set by signalling and by the SLOWEST train, not by top speed** (§20).
>    **Mixing traffic speeds destroys capacity faster than anything else.**

---

## §18. Rolling Stock and Bogies

```
⚠️ BOGIE (truck)  ⚠️ does four jobs: carries load, guides through curves,
   isolates the body from track irregularity, and transmits traction
   and braking forces
⚠️ PRIMARY SUSPENSION   axlebox to bogie frame
⚠️ SECONDARY SUSPENSION bogie to body (⚠️ usually air springs on modern
   passenger stock — they also maintain constant floor height as
   loading changes)
⚠️ YAW DAMPERS  ⚠️ suppress hunting (§3) and are what permits high speed
TILTING   ⚠️ active tilt allows higher cant deficiency (§4) on existing
   curved routes. ⚠️ Motion sickness is a real design constraint —
   tilt is deliberately incomplete
ARTICULATION  shared bogies between vehicles — ⚠️ fewer bogies, lower
   mass, and the whole set stays in line in a derailment (TGV design)
⚠️ AXLE LOAD  the master constraint on infrastructure: ~17–18 t for
   high-speed passenger, 22.5–25 t European freight, ⚠️ up to ~32.5 t
   for North American and Australian heavy haul
⚠️ LOADING GAUGE  the cross-section a vehicle may occupy. ⚠️ Britain's
   is notably restrictive; ⚠️ it is why containers and continental
   stock often cannot run there
```
**⚠️ Crashworthiness** (EN 15227 and equivalents) — ⚠️ **controlled crumple zones and
anti-climbers, so that energy is absorbed and vehicles don't override each other.**

---

## §19. Braking

```
⚠️ AUTOMATIC AIR BRAKE (Westinghouse) — ⚠️ THE fail-safe principle:
   the brake pipe is PRESSURIZED to HOLD BRAKES OFF. ⚠️ A burst pipe,
   a parted train or a leak causes pressure loss and the brakes APPLY
   AUTOMATICALLY. This is why a runaway from a parted coupling is rare
⚠️ Consequences of pneumatics: ⚠️ the brake application propagates
   along the train at roughly the speed of sound in air, so a long
   freight brakes progressively front-to-back — causing in-train forces
   and long stopping distances (§21)
ELECTRO-PNEUMATIC (EP)  ⚠️ electrical signal applies all brakes
   simultaneously — much shorter stopping distance. Passenger stock
   and modern freight (⚠️ the ECP argument, §26)
DYNAMIC   rheostatic and regenerative (§8) — ⚠️ saves brake wear and
   energy, but fades to nothing at very low speed
⚠️ NON-ADHESION  magnetic track brake, eddy current — ⚠️ independent of
   wheel-rail adhesion, so they still work on contaminated rail (§1)
```
**⚠️ Wheel slide protection** is the braking analogue of wheelslip control — ⚠️ **a sliding
wheel develops a FLAT, which then hammers the track at every revolution.**

---

## §20. ⚠️ Capacity

> **⚠️ The most misunderstood topic in rail, including by policymakers.**
```
⚠️ HEADWAY = the minimum time between trains, set by BLOCK LENGTH,
   braking distance, and signalling system — NOT by top speed
⚠️ CAPACITY IS DESTROYED BY HETEROGENEITY. ⚠️ Mixing a 200 km/h
   passenger train with an 80 km/h freight on the same track consumes
   far more capacity than either alone, because the fast train's path
   must be protected from catching the slow one
⚠️ THE FLIGHTING PRINCIPLE  grouping similar-speed trains together
   recovers much of that loss
⚠️ STOPPING PATTERNS  a stopping service among fast services has the
   same effect as a slow train
⚠️ JUNCTIONS AND TERMINI are usually the real constraints, not
   plain line. ⚠️ Flat junctions where paths conflict; platform
   occupancy and turnaround time at termini
⚠️ RECOVERY TIME / PADDING  a timetable with no slack cannot absorb
   small delays and propagates them — and too much padding wastes capacity
```
**⚠️ The counterintuitive conclusion that follows**: ⚠️ **building a dedicated high-speed
line often relieves the CLASSIC line more than it adds high-speed capacity** — **because
removing the fastest trains from a mixed railway makes the remainder far more homogeneous
and therefore denser.** **⚠️ That's a major part of the case for high-speed lines and it's
rarely the part that gets argued.**

---

## §21. Freight

**⚠️ Rail freight's economics is entirely about scale**: ⚠️ **very long, heavy trains
amortize the crew and path cost, which is why North American and Australian heavy haul push
axle loads and train lengths far beyond European practice.**
**⚠️ In-train forces are the operational difficulty**: ⚠️ **slack action between couplers,
buff (compression) and draft (tension) forces, and the risk of stringlining a light train
on a curve under braking.** **⚠️ Distributed power (locomotives mid-train and at the rear)
manages this and is standard in heavy haul.**
**⚠️ Couplers**: **⚠️ knuckle/AAR automatic couplers in North America and Australia versus
⚠️ screw couplings and side buffers in Europe — the latter requiring manual coupling by a
person going between vehicles**, **which is the reason for the Digital Automatic Coupling
(DAC) programme.**
**⚠️ Intermodal, wagonload versus block trains, and last-mile access** — ⚠️ **rail wins on
long, dense, predictable flows and loses on short, fragmented, time-sensitive ones.**

---

## §22. Maintenance

**⚠️ Track**: **tamping and lining (⚠️ restoring geometry, and it disturbs ballast — see
§11 → `rail-track-structure-welded-rail-switches-and-electrification`), ballast cleaning, rail grinding (⚠️ removes surface fatigue and restores profile —
genuinely preventive), rail lubrication on curves, and welding.**
**⚠️ Rolling contact fatigue (RCF)** is the characteristic modern rail defect — ⚠️ **surface
cracking from repeated high contact stress, which grinding removes before it grows into a
break.**
**⚠️ Inspection**: **ultrasonic and eddy-current rail testing, track recording vehicles,
⚠️ and increasingly instrumented in-service trains monitoring the infrastructure
continuously.**
**⚠️ Possession management is the real constraint**: ⚠️ **a railway can only be maintained
when trains aren't running, so maintenance competes directly with capacity (§20)** —
**and this tension shapes everything from night-work practice to why some networks close
lines for weeks instead of working weekends.**

---

## §23. High-Speed Rail

**⚠️ What actually changes above roughly 200–250 km/h:**
```
⚠️ AERODYNAMICS DOMINATE  Cv² in the Davis equation (§1). ⚠️ Nose shape,
   smooth skin, bogie fairings, pantograph shrouding
⚠️ TUNNEL ENTRY  ⚠️ the pressure wave — "tunnel boom" and passenger ear
   discomfort. Drives long tapered noses (the Shinkansen 500's famously
   extreme nose was a tunnel-boom solution) and sealed vehicle bodies
⚠️ TRACK  slab track (§10), very large curve radii, gentle transitions
⚠️ CURRENT COLLECTION  pantograph wave-propagation limits (§7)
⚠️ SIGNALLING  ⚠️ lineside signals are unreadable at speed — CAB
   SIGNALLING IS MANDATORY, which is why ETCS L2 and equivalents
   are inseparable from HSR (§16)
⚠️ SEGREGATION  dedicated lines avoid the mixed-traffic capacity
   penalty (§20) and the cant conflict (§4)
```
**⚠️ Distributed power (EMU) versus power cars**: ⚠️ **Shinkansen-style distributed traction
spreads axle load, improves adhesion and braking, and frees end space; TGV-style power cars
concentrate maintenance and noise.** **⚠️ The industry has broadly moved toward distributed.**

---

## §24. Urban Rail

**⚠️ Metro, light rail, tram-train and their distinct constraints.**
**⚠️ Metro is a capacity machine**: ⚠️ **CBTC moving block (§16 → `rail-signalling-interlocking-train-protection-and-safety`), platform screen doors,
short headways (⚠️ 90 seconds or better on the best systems), high acceleration and
deceleration, and DWELL TIME as the binding constraint** — **which is why door width,
number and platform layout matter more to capacity than train speed.**
**⚠️ Light rail and trams**: ⚠️ **street running means tight curves, low floors and mixed
traffic; ⚠️ tram-train vehicles must satisfy both tramway and mainline rules, including
crashworthiness and dual electrification.**
**⚠️ The rubber-tyred metro** (Paris, Montreal, Mexico City) ⚠️ **trades rolling resistance
for adhesion — better acceleration and gradients, worse efficiency, and it is the exception
that proves §1 → `rail-adhesion-resistance-traction-physics-and-geometry`'s rule.**

---

## §25. ⚠️ Maglev and Hyperloop

**⚠️ Maglev is real and deployed, and its niche is narrow.**
```
⚠️ EMS (electromagnetic suspension)  attraction, actively controlled,
   small gap. Transrapid, and the Shanghai airport line
⚠️ EDS (electrodynamic suspension)  repulsion from induced currents,
   ⚠️ requires wheels at low speed. Japan's SCMaglev / Chūō Shinkansen
⚠️ THE CASE   no rolling resistance, no adhesion limit, very high speed
⚠️ THE PROBLEM  ⚠️ zero interoperability with the existing 1.4 million km
   of railway. A maglev line cannot use any existing track, station or
   depot — so it competes with building an entire parallel network,
   which is why so few exist
```
> **⚠️ GOTCHA — hyperloop should be assessed as a vacuum-tube engineering problem, not as
> a transport proposal.** ⚠️ **Maintaining a near-vacuum in a structure hundreds of
> kilometres long, with thermal expansion, safe passenger egress, and pressure-breach
> consequences, is the actual problem — and it has not been solved at any meaningful
> scale.** **⚠️ Several high-profile hyperloop ventures wound down without demonstrating
> passenger-scale operation.** **⚠️ Treat capacity and cost claims sceptically: proposed
> pod sizes imply throughput far below a conventional high-speed line, which inverts the
> usual argument for building rail at all** (§20).
