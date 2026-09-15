---
name: infra-bridges-types-loads-failure-modes-and-inspection
description: "Use for bridges: bridge types and the structural logic that selects them by span, loads and load rating, materials and the details such as bearings, joints and drainage that cause most deterioration, bridge failure modes including scour, fatigue, fracture-critical members and vessel collision, and inspection and condition rating and what a rating does and does not tell you."
---

# Roads, Bridges and Infrastructure: Bridge Types and Structural Logic, Loads and Load Rating, Materials and Details, Bridge Failure Modes, and Inspection and Condition Rating

> **Part 3 of 6** of the *Roads, Bridges and Public Infrastructure* reference (plugin `roads-bridges-and-public-infrastructure`), covering §9–§13. Sibling skills: `infra-geometric-design-pavement-drainage-and-traffic` (§0–§5), `infra-intersections-road-safety-and-construction` (§6–§8), `infra-water-wastewater-transit-ports-and-utilities` (§14–§18), `infra-procurement-cost-asset-management-funding-and-equity` (§19–§26), `infra-reference` (§27–§32). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The engineering is mature and codified. Two things are live. See §27 → `infra-reference` for US surface transportation funding, and bridge vessel-collision risk.

> **⚠️ The engineering here is largely solved. The hard problems are institutional — how
> projects get chosen, financed, estimated, delivered and maintained over a century.**
>
> **Complements a buildings reference (vertical construction, codes, structural design), a
> resource-extraction reference (aggregate, steel, bitumen), and a thermodynamics/materials
> reference. The failure-analysis framing is shared with both.**
>
> **⚠️ GOTCHA** boxes mark where intuition about traffic, cost or safety is reliably wrong.
>
> **The three ideas that organize this document:**
> 1. **⚠️ THE ASSET IS THE LIABILITY** (§21 → `infra-procurement-cost-asset-management-funding-and-equity`). **Building infrastructure creates a permanent
>    maintenance obligation that nobody funds at ribbon-cutting. Every deferred-maintenance
>    crisis is this arithmetic arriving on schedule, and it is the central fact of the
>    field.**
> 2. **⚠️ TRAFFIC IS NOT A FIXED QUANTITY** (§25 → `infra-procurement-cost-asset-management-funding-and-equity`). **Demand responds to supply. Roads
>    designed as if traffic were a given volume to be accommodated produce results that
>    surprise their designers, and this has been documented for decades.**
> 3. **⚠️ SPEED IS THE VARIABLE THAT MATTERS MOST FOR SAFETY** (§7 → `infra-intersections-road-safety-and-construction`). **Kinetic energy scales
>    with the square of velocity, and human injury tolerance is a fixed biological
>    threshold. Everything in modern road safety follows from that single physical fact.**

---

## §9. ⚠️ Bridge Types and Structural Logic

```
⚠️ ⚠️ THE ORGANIZING QUESTION: HOW DOES LOAD REACH THE GROUND?
   ⚠️ BEAM / GIRDER  ⚠️ bending. Simple, cheap, short spans.
      ⚠️ The overwhelming majority of bridges
   ⚠️ TRUSS  ⚠️ bending resolved into AXIAL tension and
      compression in members — material-efficient, and
      maintenance-intensive because of the connections
   ⚠️ ARCH  ⚠️ pure COMPRESSION, thrusting outward — ⚠️ which is
      why arches need competent abutments or rock, and why
      masonry arches survive for millennia
   ⚠️ SUSPENSION  ⚠️ pure TENSION in the main cables, with the
      deck hung from them. ⚠️ The longest spans; ⚠️ AERODYNAMIC
      stability is the governing problem (§12)
   ⚠️ CABLE-STAYED  ⚠️ cables directly to towers — ⚠️ stiffer and
      cheaper than suspension in the medium-long range, and it
      has largely displaced suspension for new bridges below
      the very longest spans
   ⚠️ CULVERT and slab for the shortest
⚠️ SPAN ARRANGEMENT  simple vs continuous (⚠️ continuous is more
   efficient and REDUNDANT, §12) · integral abutments
   eliminating bearings and joints, which are the parts that
   fail (§11)
⚠️ SUBSTRUCTURE  piers, abutments, ⚠️ FOUNDATIONS (spread,
   piles, drilled shafts, caissons) — ⚠️ and foundations in
   water are the expensive, risky part (§12's scour)
⚠️ CONSTRUCTION METHOD OFTEN DICTATES THE TYPE  ⚠️ balanced
   cantilever, incremental launching, segmental — you choose a
   form you can actually build over that obstacle
```

---

## §10. Loads and Load Rating

**⚠️ Dead load** (self weight — ⚠️ **dominant on long spans, which is why long-span design is
partly a fight against the structure's own mass**), ⚠️ **superimposed dead load (surfacing,
and note that repeated resurfacing quietly adds dead load over decades), live load,
dynamic amplification, wind, seismic, thermal, and vessel or vehicle collision** (§27.2 → `infra-reference`).
**⚠️ Design vehicles** — ⚠️ **HL-93 in AASHTO, and note these are notional envelopes rather
than real trucks.**
**⚠️ LRFD (load and resistance factor design)** applies partial factors to loads and
resistances calibrated to a target reliability index — ⚠️ **which is probabilistic design
rather than a single global safety factor.**
**⚠️ LOAD RATING** is the operational counterpart: ⚠️ **inventory rating (indefinite safe
capacity) versus operating rating (maximum permissible) — and ⚠️ POSTING a bridge for
reduced weight is the cheap alternative to strengthening it, with real freight
consequences.**
**⚠️ Permit loads and superloads** require route-specific analysis.

---

## §11. Materials and Details

**⚠️ Steel** — ⚠️ **high strength, fast erection, weathering steel eliminating painting in
suitable environments (⚠️ and failing where salt spray or persistent wetness prevents the
protective patina forming).**
**⚠️ Reinforced and prestressed concrete** — ⚠️ **prestressing puts the concrete into
compression so it does not crack under service load, and ⚠️ post-tensioning DUCT GROUTING
defects have caused serious tendon corrosion problems.**
> **⚠️ GOTCHA — the details fail before the structure does, and they are the least glamorous
> part of the design.** ⚠️ **EXPANSION JOINTS leak, letting chloride-laden water onto
> BEARINGS and pier caps below; bearings seize; drainage systems block; and deck
> waterproofing fails.** **⚠️ A large share of bridge deterioration traces to water getting
> somewhere it was not meant to — the same lesson as §4 → `infra-geometric-design-pavement-drainage-and-traffic`.**

**⚠️ CORROSION OF REINFORCEMENT** is the dominant deterioration mechanism: ⚠️ **chloride
from de-icing salt or seawater depassivates the steel, corrosion products expand, and the
concrete spalls.** ⚠️ **Epoxy-coated, galvanized and stainless reinforcement, cathodic
protection and sealers all fight it.**
**⚠️ Alkali-silica reaction and delayed ettringite formation** as concrete's own internal
failure modes.

---

## §12. ⚠️ Bridge Failure Modes

```
⚠️ ⚠️ SCOUR IS THE LEADING CAUSE OF BRIDGE FAILURE, and it is
   invisible. ⚠️ Flowing water erodes the streambed around
   piers and abutments, removing foundation support —
   ⚠️ AND THE HOLE OFTEN REFILLS AS THE FLOOD RECEDES, so a
   post-flood inspection can show nothing wrong
   ⚠️ Schoharie Creek (1987) is the reference case
   ⚠️ Countermeasures: riprap, scour countermeasures, and
   founding below the calculated scour depth
⚠️ ⚠️ FRACTURE-CRITICAL / NON-REDUNDANT MEMBERS  ⚠️ elements
   whose failure collapses the structure. ⚠️ Silver Bridge
   (1967) failed from a single eyebar with a stress-corrosion
   crack, killing 46 — ⚠️ AND IT CREATED THE US NATIONAL BRIDGE
   INSPECTION PROGRAM (§13). ⚠️ Modern practice designs for
   redundancy and inspects these members more intensively
⚠️ FATIGUE  ⚠️ cyclic loading grows cracks at welded details and
   connections. ⚠️ Detail category governs life
⚠️ ⚠️ GUSSET PLATE / DESIGN ERROR  ⚠️ I-35W (2007) — an
   undersized gusset plate, plus decades of added dead load,
   plus construction material stockpiled on the deck.
   ⚠️ The classic multi-factor failure
⚠️ AERODYNAMIC INSTABILITY  ⚠️ Tacoma Narrows (1940) —
   ⚠️ AND NOTE THE COMMON MISEXPLANATION: it was aeroelastic
   FLUTTER, a self-exciting interaction between motion and
   airflow, NOT simple resonance with vortex shedding. ⚠️ The
   textbook resonance story is wrong and persistent
⚠️ VESSEL AND VEHICLE COLLISION  ⚠️ Sunshine Skyway (1980) and
   Francis Scott Key (2024) — §27.2
⚠️ SEISMIC  unseating, column failure, liquefaction — and
   retrofit programmes after Loma Prieta and Northridge
⚠️ ⚠️ THE PATTERN ACROSS ALL OF THEM  ⚠️ single points of
   failure, deferred maintenance, loads exceeding assumptions,
   and inspection that looked but did not see
```

---

## §13. ⚠️ Inspection and Condition Rating

**⚠️ Routine inspection on a defined cycle** (⚠️ **two years is the traditional US default,
with risk-based intervals now permitted**), ⚠️ **plus in-depth, fracture-critical,
underwater and special inspections.**
**⚠️ Condition ratings** score deck, superstructure and substructure on a 0–9 scale;
⚠️ **element-level inspection records quantities in condition states, which is far more
useful for asset management** (§21 → `infra-procurement-cost-asset-management-funding-and-equity`).
> **⚠️ GOTCHA — "STRUCTURALLY DEFICIENT" DOES NOT MEAN UNSAFE, and the term has caused
> enormous public confusion.** ⚠️ **It means a major component is rated in poor condition or
> worse, triggering closer attention and often weight posting.** **⚠️ An unsafe bridge is
> closed. The headline count of deficient bridges is a MAINTENANCE BACKLOG measure, not a
> collapse-risk measure — and reporting it as the latter is both alarming and misleading.**

**⚠️ FUNCTIONALLY OBSOLETE** is a different and even more misunderstood term — ⚠️ **it means
the geometry no longer meets current standards (narrow lanes, low clearance), which is not
a structural statement at all.**
**⚠️ Non-destructive evaluation**: ⚠️ **ultrasonic, ground-penetrating radar, half-cell
potential for corrosion, acoustic emission for wire breaks.**
**⚠️ Structural health monitoring and drone or robotic inspection** are genuinely improving
coverage — ⚠️ **and the constraint is interpretation capacity, not data.**

---

# PART III — OTHER INFRASTRUCTURE
