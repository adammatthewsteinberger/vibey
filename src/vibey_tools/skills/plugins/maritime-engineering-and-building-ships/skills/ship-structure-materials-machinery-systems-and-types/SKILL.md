---
name: ship-structure-materials-machinery-systems-and-types
description: "Use for the ship as a built object: structure and longitudinal strength with hogging, sagging and the midship section, materials and corrosion including cathodic protection and coatings, main and auxiliary machinery, ship systems from ballast and bilge to cargo handling, and the ship types and what actually drives each one's design."
---

# Maritime Engineering: Structure and Longitudinal Strength, Materials and Corrosion, Machinery, Ship Systems, and Ship Types

> **Part 3 of 6** of the *Maritime Engineering and Building Ships* reference (plugin `maritime-engineering-and-building-ships`), covering §9–§13. Sibling skills: `ship-design-spiral-hydrostatics-stability-and-hull-form` (§0–§4), `ship-resistance-propulsion-seakeeping-and-manoeuvring` (§5–§8), `ship-shipyard-build-welding-launch-and-naval-vessels` (§14–§18), `ship-class-flag-imo-safety-operations-and-losses` (§19–§23), `ship-reference` (§24–§29). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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

## §9. ⚠️ Structure and Longitudinal Strength

> **⚠️ The mental model that matters: A SHIP IS A BOX GIRDER, and it is loaded like a beam
> spanning waves.**
```
⚠️ HOGGING  wave crest amidships → ⚠️ deck in TENSION, keel in
   COMPRESSION
⚠️ SAGGING  crests at the ends, trough amidships → ⚠️ deck in
   COMPRESSION, keel in TENSION
⚠️ THE STILL WATER BENDING MOMENT depends on how CARGO IS LOADED —
   ⚠️ which is why loading computers exist and why bad loading
   can break a ship at the quayside, not just at sea
⚠️ SECTION MODULUS  ⚠️ material far from the neutral axis does the
   work, so DECK AND BOTTOM plating carry longitudinal strength
   ⚠️ Large deck openings (container ships, bulkers) remove exactly
   that material — hence heavy hatch coamings and torsion boxes
⚠️ TRANSVERSE vs LONGITUDINAL FRAMING  ⚠️ longitudinal framing gives
   better longitudinal strength (used on long ships); transverse
   is simpler. Most large ships are combination-framed
⚠️ ALSO  torsion (⚠️ severe on open-deck container ships in
   quartering seas) · racking · panting · slamming loads ·
   local loads and vibration
```
**⚠️ FATIGUE dominates ship structural life** (see a manufacturing reference §4) —
⚠️ **a hull sees tens of millions of wave cycles, so details, welds and stress
concentrations at hatch corners and bracket toes determine life, not ultimate strength.**
**⚠️ BRITTLE FRACTURE is the historical lesson**: ⚠️ **the Liberty ship failures showed that
welded (rather than riveted) construction gives a crack a continuous path through the
entire hull, and that steel undergoes a ductile-to-brittle transition in cold water.**
**⚠️ The remedies — notch-tough steel grades, crack arrestors, and better detail design —
are why modern hulls specify steel grades by temperature.**

---

## §10. Materials and Corrosion

**⚠️ Steel grades**: **mild, higher-tensile (⚠️ allows thinner plate, which saves weight and
WORSENS both fatigue and corrosion margin — a real trade), and notch-tough grades by
service temperature** (§9).
**⚠️ Aluminium** for superstructures and fast craft — ⚠️ **light, and it loses strength at
much lower temperatures in fire, and it must be isolated from steel to prevent galvanic
attack.**
**⚠️ Composites** for small craft, minehunters (⚠️ non-magnetic) and increasingly for
appendages.
```
⚠️ CORROSION IS THE PERMANENT ENEMY
   ⚠️ GALVANIC  dissimilar metals in an electrolyte — ⚠️ and seawater
      is an excellent electrolyte
   ⚠️ CATHODIC PROTECTION  sacrificial anodes (zinc/aluminium) or
      impressed current. ⚠️ Anodes are consumables and are renewed
      at every drydocking
   COATINGS  ⚠️ surface preparation determines coating life far more
      than the coating product does
   ⚠️ BALLAST TANKS are the worst environment on the ship —
      alternating wet/dry, warm, inaccessible
   ⚠️ CORROSION ALLOWANCE is designed in, and ⚠️ steel renewal when
      thickness falls below limits is a normal, planned event (§22)
```
**⚠️ Fouling** — ⚠️ **marine growth increases frictional resistance (§5 → `ship-resistance-propulsion-seakeeping-and-manoeuvring`) substantially;
antifouling coatings are regulated (⚠️ TBT was banned after severe ecological harm), and
hull cleaning is now a routine efficiency measure.**

---

# PART II — SYSTEMS

## §11. Machinery

```
⚠️ LOW-SPEED TWO-STROKE DIESEL  ⚠️ the workhorse of deep-sea shipping.
   Directly coupled to the propeller — ⚠️ NO GEARBOX — burns heavy
   fuel, and reaches the highest thermal efficiency of any prime
   mover in commercial use (⚠️ around 50%+)
   ⚠️ It is REVERSIBLE — the engine itself runs backwards
MEDIUM-SPEED FOUR-STROKE  geared, multiple engines, ferries and
   offshore. More power-dense, less efficient
GAS TURBINE  ⚠️ superb power-to-weight, poor part-load efficiency —
   naval and fast ferries
⚠️ DIESEL-ELECTRIC and INTEGRATED ELECTRIC PROPULSION  ⚠️ decouples
   engine speed from propeller speed, allows optimal engine loading
   and flexible layout. Cruise ships, offshore, icebreakers, warships
⚠️ DUAL-FUEL  ⚠️ the current centre of gravity of newbuilding (§24.2)
BATTERY-HYBRID and FULL ELECTRIC  ⚠️ genuinely viable for ferries
   and short sea; ⚠️ energy density rules it out for deep sea
```
**⚠️ Waste heat recovery** — ⚠️ **exhaust gas economizers and turbogenerators, and see a
thermodynamics reference on why the largest exergy losses sit where they do.**
**⚠️ Emissions control**: **scrubbers (⚠️ and the open-loop discharge controversy), SCR and
EGR for NOx, and ECAs where limits are stricter** (§24.1 → `ship-reference`).

---

## §12. Ship Systems

**⚠️ The ship is a self-contained settlement, and the systems reflect that.**
**⚠️ Electrical**: **generators, switchboard, ⚠️ EMERGENCY generator (⚠️ required, above the
bulkhead deck, self-starting), shore power (⚠️ increasingly mandated in port).**
⚠️ **BLACKOUT and dead-ship recovery is a designed-for scenario, not a hypothetical.**
**⚠️ Steering gear**: ⚠️ **redundancy is mandatory — two independent power units and the
ability to steer from an alternative position.**
**⚠️ Bilge and ballast**: ⚠️ **and BALLAST WATER TREATMENT is now required to prevent
invasive species transfer, a substantial retrofit obligation across the fleet.**
**⚠️ Fire**: **detection, fixed systems (CO₂, water mist, foam), fire pumps and the
emergency fire pump, structural fire protection by division class.**
**⚠️ Also**: **fresh water generation, sewage treatment, HVAC, cargo systems by type (§13),
mooring, anchoring, and lifesaving appliances.**

---

## §13. Ship Types and What Drives Them

```
⚠️ CONTAINER  ⚠️ speed and slot capacity; open decks → TORSION (§9);
   ⚠️ lashing and stack weight limits; parametric roll exposure (§7)
BULK CARRIER  ⚠️ simple, cheap, and ⚠️ historically the most
   dangerous type — cargo liquefaction and hold flooding (§23)
TANKER  ⚠️ DOUBLE HULL mandated after major spills; inert gas
   systems; cargo heating; ⚠️ segregated ballast
GAS CARRIER (LNG/LPG)  ⚠️ containment systems (membrane vs Moss
   spherical), ⚠️ BOIL-OFF GAS which can be burned as fuel,
   cryogenic materials
RO-RO and FERRY  ⚠️ large undivided decks = ⚠️ THE free surface
   problem (§3); bow/stern doors; ⚠️ damage stability is the
   binding constraint
CRUISE  ⚠️ enormous hotel load, high superstructure, evacuation
   of thousands, ⚠️ "safe return to port" requirements
OFFSHORE  ⚠️ DYNAMIC POSITIONING, station keeping, heavy lift
FISHING  ⚠️ disproportionately high casualty rates; stability
   compromised by catch and by ice accretion
```

---

# PART III — BUILDING SHIPS
