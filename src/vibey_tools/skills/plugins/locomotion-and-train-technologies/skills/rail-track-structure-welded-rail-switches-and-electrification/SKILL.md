---
name: rail-track-structure-welded-rail-switches-and-electrification
description: "Use for the infrastructure under and over the train: track structure with rail, sleepers, ballast and slab track, continuous welded rail with stress-free temperature, buckling and rail breaks, switches and crossings and why they dominate maintenance and delay, and electrification infrastructure including overhead line equipment and third rail with their clearance and current limits."
---

# Rail Engineering: Track Structure, Continuous Welded Rail and Thermal Stress, Switches and Crossings, and Electrification Infrastructure

> **Part 3 of 6** of the *Locomotion and Train Technologies* reference (plugin `locomotion-and-train-technologies`), covering §10–§13. Sibling skills: `rail-adhesion-resistance-traction-physics-and-geometry` (§0–§4), `rail-steam-diesel-electric-and-alternative-traction` (§5–§9), `rail-signalling-interlocking-train-protection-and-safety` (§14–§17), `rail-rolling-stock-braking-capacity-and-service-types` (§18–§25), `rail-reference` (§26–§31). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
> 3. **⚠️ Capacity is set by signalling and by the SLOWEST train, not by top speed** (§20 → `rail-rolling-stock-braking-capacity-and-service-types`).
>    **Mixing traffic speeds destroys capacity faster than anything else.**

---

## §10. Track Structure

```
⚠️ RAIL       flat-bottom (Vignoles) is now near-universal. ⚠️ Specified
   by mass per metre (e.g. 60 kg/m); ⚠️ head-hardened rail for curves
   and heavy haul
SLEEPERS/TIES  timber, concrete (⚠️ monobloc or twin-block), steel.
   ⚠️ Concrete is heavier, holds gauge better, lasts longer
FASTENINGS    ⚠️ resilient clips (Pandrol and similar) — they hold the
   rail down while allowing controlled longitudinal restraint (§11)
⚠️ BALLAST     angular crushed stone. ⚠️ Its jobs: distribute load, hold
   the track laterally and longitudinally, drain, and provide
   adjustability for tamping. ⚠️ ROUNDED stone is useless — it's the
   ANGULARITY and interlock that provides resistance
SUBGRADE      ⚠️ the most-neglected layer; most persistent geometry
   faults are subgrade or drainage faults, not track faults
⚠️ SLAB TRACK  concrete instead of ballast. Higher capital cost, far
   lower maintenance, no ballast flight at high speed. ⚠️ Tunnels,
   high-speed lines, and hard to repair if the base settles
```
**⚠️ DRAINAGE is the single most important maintenance factor and the least glamorous** —
⚠️ **water in the formation causes pumping, ballast fouling, and geometry loss.**
**⚠️ Track gauge**: **1,435 mm standard; ⚠️ broad (Russia 1,520, Iberia, India, Ireland) and
narrow (Cape 1,067, metre) elsewhere.** ⚠️ **Break-of-gauge is a permanent operational tax
requiring transhipment, bogie exchange or variable-gauge axles.**

---

## §11. ⚠️ Continuous Welded Rail and Thermal Stress

> **⚠️ The most important non-obvious fact in track engineering.**
> ⚠️ **Jointed rail had expansion gaps — that's what produced the classic "clickety-clack."**
> **⚠️ Continuous welded rail has NO gaps, so it CANNOT expand.** **Instead, thermal stress
> builds internally: the rail is under compression in summer and TENSION in winter.**
```
⚠️ STRESS-FREE TEMPERATURE (SFT / neutral temperature) — the temperature
   at which the rail is unstressed. ⚠️ Set deliberately during
   installation to suit the local climate
⚠️ TOO HOT  → compression → ⚠️ BUCKLING (a "sun kink") — the track
   snakes sideways and derails trains. ⚠️ This is why speed restrictions
   are imposed in extreme heat, and it is NOT precautionary theatre
⚠️ TOO COLD → tension → ⚠️ RAIL BREAK or pull-apart at welds
```
**⚠️ Management**: ⚠️ **the ballast shoulder provides the lateral resistance that prevents
buckling — which is why disturbed ballast (after tamping, before consolidation) means
temporary speed restrictions**, **and why painting rails white on some networks is a real
measure to reduce railhead temperature.**
**⚠️ Breather/adjustment switches** at structures and boundaries allow controlled movement.
**⚠️ The counterintuitive part**: ⚠️ **rail temperature can be 20°C or more above air
temperature in sun** — **so "it's only 35°C out" is not the relevant number.**

---

## §12. Switches and Crossings

**⚠️ The most maintenance-intensive and failure-prone assets on the railway.**
**⚠️ Anatomy**: **switch rails (points), stock rails, ⚠️ the CROSSING or frog (where one
rail must cross another — inherently a gap, and the source of impact loading), check
rails, and the point machine.**
**⚠️ Failure modes**: ⚠️ **point machines failing to throw or detect, obstruction by ice,
snow or debris (hence point heaters), wear at the switch toe, and crossing nose damage
from repeated impact.**
**⚠️ Speed through turnouts is limited by the crossing angle** — ⚠️ **a 1-in-8 turnout is
slow, high-speed turnouts (1-in-30 and beyond, with swing-nose crossings that eliminate the
gap) are long, expensive, and what makes high-speed junction moves possible.**
**⚠️ Facing vs trailing points**: ⚠️ **a facing point failure can split a train; trailing
points are inherently safer, which is why historic signalling practice minimized facing
points and why detection and locking of facing points is a core interlocking requirement**
(§15 → `rail-signalling-interlocking-train-protection-and-safety`).

---

## §13. Electrification Infrastructure

**⚠️ Overhead line equipment**: **contact wire, catenary (messenger) wire, droppers,
registration arms, ⚠️ auto-tensioning with balance weights or springs to maintain constant
tension across temperature.** ⚠️ **Constant tension is what makes high-speed current
collection possible.**
**⚠️ The economics is the whole story**: ⚠️ **electrification is reported around €1–2 million
per kilometre**, **and the cost is dominated by structures, clearances, bridges and
immunization of signalling — not by the wire itself.** **⚠️ Which is why bridge rebuilds and
tunnel clearances often dominate an electrification business case.**
**⚠️ Third rail**: **cheap and low-clearance; ⚠️ severe voltage-drop and current limits, ice
problems, and a live conductor at ground level, which is why it's generally not built new
for mainline.**

---

# PART IV — SIGNALLING AND SAFETY
