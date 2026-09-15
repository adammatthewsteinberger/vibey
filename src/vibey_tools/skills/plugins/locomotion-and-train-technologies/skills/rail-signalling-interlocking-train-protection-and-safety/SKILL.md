---
name: rail-signalling-interlocking-train-protection-and-safety
description: "Use for signalling and safety questions: fixed and moving block signalling and how headway follows from it, interlocking and how routes are set, locked and proved, the train protection systems — ATP, the ETCS levels, PTC and CBTC — and how they differ, and rail safety and failure modes including signals passed at danger, derailment causes and the fail-safe principle."
---

# Rail Engineering: Block Signalling, Interlocking, Train Protection with ATP, ETCS, PTC and CBTC, and Safety and Failure Modes

> **Part 4 of 6** of the *Locomotion and Train Technologies* reference (plugin `locomotion-and-train-technologies`), covering §14–§17. Sibling skills: `rail-adhesion-resistance-traction-physics-and-geometry` (§0–§4), `rail-steam-diesel-electric-and-alternative-traction` (§5–§9), `rail-track-structure-welded-rail-switches-and-electrification` (§10–§13), `rail-rolling-stock-braking-capacity-and-service-types` (§18–§25), `rail-reference` (§26–§31). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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

## §14. ⚠️ Block Signalling

**⚠️ Because trains cannot stop on sight (§1 → `rail-adhesion-resistance-traction-physics-and-geometry`), the line is divided into BLOCKS and only one
train is permitted in a block at a time.**
```
⚠️ TRACK CIRCUIT  ⚠️ the elegant original: a low voltage applied to the
   two rails of a block, with a relay at the far end. ⚠️ A train's axles
   SHORT the circuit, dropping the relay and proving occupancy
   ⚠️ FAIL-SAFE BY DESIGN: a broken rail, a power failure or a
   disconnection all drop the relay and show the block as OCCUPIED
   ⚠️ Vulnerable to poor shunting — rust, sand (§1), lightweight vehicles
AXLE COUNTERS  count axles in and out. ⚠️ Works with any rail condition
   and does NOT detect broken rails — a real trade-off
⚠️ MULTI-ASPECT SIGNALLING  green / double yellow / yellow / red gives
   the driver progressively more braking distance than one block provides
⚠️ ABSOLUTE BLOCK, permissive block, token and staff systems on
   single lines (⚠️ physical possession of a unique token as a
   mechanical guarantee — crude and extremely robust)
```
> **⚠️ GOTCHA — "fail-safe" in railway signalling means something specific and stronger
> than in most engineering.** ⚠️ **It means every credible failure moves the system toward
> the RESTRICTIVE state: signals show danger, relays drop, brakes apply.** **⚠️ This is
> why railway signalling used heavy gravity-drop relays for a century and why the
> discipline was so conservative about electronics — a stuck-up relay contact is a
> fatality.**

---

## §15. Interlocking

**⚠️ The logic that prevents conflicting movements being signalled, and the safety-critical
heart of a railway.**
```
⚠️ THE CORE RULES
   ⚠️ Points must be correctly SET, LOCKED and DETECTED before a
      signal can clear
   ⚠️ Conflicting routes cannot be set simultaneously
   ⚠️ Route locking holds the route until the train has passed
   ⚠️ Approach locking prevents pulling a route from under an
      approaching train
   ⚠️ Flank protection guards against a movement running into the route
GENERATIONS  ⚠️ mechanical (lever frames with physical locking bars —
   the logic is literally machined into metal) → relay → ⚠️ SSI and
   computer-based interlocking
```
**⚠️ Mechanical interlocking deserves respect**: ⚠️ **the safety logic was implemented as
physical shapes that could not be defeated by a wiring error or a software bug**, **and
migrating that assurance level to software is precisely why modern signalling projects are
slow and expensive** (§26.1 → `rail-reference`).

---

## §16. Train Protection: ATP, ETCS, PTC, CBTC

```
⚠️ THE PROBLEM  signals only work if the driver sees and obeys them.
   ⚠️ SPADs (Signal Passed At Danger) have caused many major accidents
⚠️ AWS / warning systems  audible warning; driver must acknowledge.
   ⚠️ Warns but does not enforce — and acknowledgement can become reflex
⚠️ ATP (Automatic Train Protection)  ⚠️ ENFORCES. Supervises speed and
   applies brakes if the driver does not
⚠️ ETCS LEVELS
   ⚠️ L1  intermittent, balise-based, works alongside lineside signals
   ⚠️ L2  continuous radio (GSM-R → FRMCS), ⚠️ movement authority in
      the cab, LINESIDE SIGNALS CAN BE REMOVED. The current standard
   ⚠️ L3  moving block — ⚠️ no fixed block sections; requires reliable
      train integrity monitoring, which is the hard part for freight
⚠️ PTC (US)  Positive Train Control — enforces stops, speed limits,
   work zones and switch position
⚠️ CBTC  metro-focused, radio-based, ⚠️ moving block, the basis of
   driverless operation
⚠️ GoA (Grades of Automation) 1–4  ⚠️ GoA4 is unattended
```
**⚠️ The capacity argument for ETCS L2 is genuine** — ⚠️ **SNCF reports an expected 25%
capacity increase on one line, from 13 to 16 trains per hour per direction** — **because
continuous supervision allows shorter, better-optimized headways than fixed multi-aspect
signals** (§20 → `rail-rolling-stock-braking-capacity-and-service-types`).
**⚠️ Why moving block is hard for freight** (§26.1 → `rail-reference`): ⚠️ **the system must know where the
REAR of the train is, and a freight train that has parted must be detected.** **On a metro
with fixed-formation units this is trivial; on a 100-wagon freight it is not.**

---

## §17. Safety and Failure Modes

**⚠️ Rail's safety record per passenger-km is excellent, and it was bought with a century
of investigated failures** (see a civil engineering reference on failure analysis).
**⚠️ The recurring accident causes**: **SPAD, ⚠️ overspeed on curves (the reason ATP
enforces rather than warns), track buckling (§11 → `rail-track-structure-welded-rail-switches-and-electrification`), rail breaks and fatigue, level crossing
collisions (⚠️ statistically dominant in many countries and almost always caused by road
user behaviour), landslips, and derailment from wheel or bearing failure.**
**⚠️ Hot axle box detectors, wheel impact load detectors and acoustic bearing detectors are
the trackside defence** — ⚠️ **catching failures before they become derailments.**
**⚠️ Independent investigation bodies** (**RAIB, NTSB, BEA-TT, and equivalents**) ⚠️ **publish
findings regardless of embarrassment and feed them into rules** — **the practice that
makes the safety record possible.**
