---
name: building-disciplines-site-brief-planning-and-design
description: "Use at the front end of a project: the disciplines involved and how the lifecycle actually runs, site and ground investigation and what it determines downstream, brief and programming, planning, zoning and entitlement and why approval risk dominates early schedules, and architectural design. Includes the router for the whole buildings and civil structures reference."
---

# Buildings and Civil Structures: The Disciplines and the Lifecycle, Site and Ground, Brief and Programming, Planning, Zoning and Entitlement, and Architectural Design

> **Part 1 of 6** of the *Designing and Building Buildings and Other Civil Structures* reference (plugin `designing-and-building-buildings`), covering §0–§5. Sibling skills: `building-structure-foundations-envelope-services-and-fire` (§6–§10), `building-accessibility-energy-drawings-bim-and-codes` (§11–§14), `building-procurement-cost-sequencing-materials-and-quality` (§15–§19), `building-site-safety-commissioning-retrofit-and-why-projects-fail` (§20–§23), `building-reference` (§24–§29). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The engineering is settled. Two areas moved. See §24 → `building-reference` for tall mass timber code adoption, and embodied carbon regulation.

> **⚠️ The practice companion to a civil/industrial engineering reference.** ⚠️ **That one
> translates concepts for outsiders — factor of safety, codes as accumulated failure logs,
> the megaproject estimation record.** **This one is how the work is actually done.**
>
> **⚠️ The organizing reality: a building is a MULTI-DISCIPLINARY SYSTEM delivered by
> parties with different contracts, different liabilities and different incentives.**
> ⚠️ **Most building failures are not engineering failures — they are COORDINATION
> failures at the boundaries between disciplines and between design and construction**
> (§23 → `building-site-safety-commissioning-retrofit-and-why-projects-fail`).
>
> **⚠️ GOTCHA** boxes mark the assumptions that cause litigation.
>
> **⚠️ Scope note**: ⚠️ **structural, fire and geotechnical design are licensed activities
> in most jurisdictions for good reason. This is a map of the territory, not a
> substitute for a qualified engineer or a local code review.**
>
> **The three ideas that organize this document:**
> 1. **⚠️ Design decisions bind cost early and irreversibly** (§1, §16 → `building-procurement-cost-sequencing-materials-and-quality`). **Most of a
>    building's cost and carbon are committed during concept design, when almost nothing
>    has been spent.**
> 2. **⚠️ WATER destroys more buildings than structural failure** (§8 → `building-structure-foundations-envelope-services-and-fire`). **Envelope and
>    moisture management cause the overwhelming majority of building defects, claims and
>    premature failures — and they are the least glamorous part of the job.**
> 3. **⚠️ Load paths and lateral systems are the two things a structure is** (§6 → `building-structure-foundations-envelope-services-and-fire`).
>    **Gravity is the obvious problem; wind and seismic are the ones that govern.**

---

## §0. Routing

| You want... | Go to |
|---|---|
| **Disciplines and lifecycle** | **§1** |
| Site and geotechnical | §2 |
| Brief and programming | §3 |
| Planning and entitlement | §4 |
| Architectural design | §5 |
| **⚠️ Structural systems** | **§6 → `building-structure-foundations-envelope-services-and-fire`** |
| Foundations | §7 → `building-structure-foundations-envelope-services-and-fire` |
| **⚠️ Envelope and moisture** | **§8 → `building-structure-foundations-envelope-services-and-fire`** |
| Building services | §9 → `building-structure-foundations-envelope-services-and-fire` |
| **Fire safety** | **§10 → `building-structure-foundations-envelope-services-and-fire`** |
| Accessibility | §11 → `building-accessibility-energy-drawings-bim-and-codes` |
| Energy and comfort | §12 → `building-accessibility-energy-drawings-bim-and-codes` |
| Drawings, specs, BIM | §13 → `building-accessibility-energy-drawings-bim-and-codes` |
| **⚠️ Codes and permitting** | **§14 → `building-accessibility-energy-drawings-bim-and-codes`** |
| Procurement and delivery | §15 → `building-procurement-cost-sequencing-materials-and-quality` |
| Cost | §16 → `building-procurement-cost-sequencing-materials-and-quality` |
| **⚠️ Construction sequencing** | **§17 → `building-procurement-cost-sequencing-materials-and-quality`** |
| Materials in construction | §18 → `building-procurement-cost-sequencing-materials-and-quality` |
| Quality and inspection | §19 → `building-procurement-cost-sequencing-materials-and-quality` |
| Site safety | §20 → `building-site-safety-commissioning-retrofit-and-why-projects-fail` |
| Commissioning and handover | §21 → `building-site-safety-commissioning-retrofit-and-why-projects-fail` |
| Existing buildings | §22 → `building-site-safety-commissioning-retrofit-and-why-projects-fail` |
| **⚠️ Why projects fail** | **§23 → `building-site-safety-commissioning-retrofit-and-why-projects-fail`** |
| **What's live** | **§24 → `building-reference`** |
| Misconceptions, numbers | §25–§26 → `building-reference` |
| Sources, quick ref, method | §27–§29 → `building-reference` |

---

## §1. The Disciplines and the Lifecycle

```
⚠️ WHO DOES WHAT
   ⚠️ ARCHITECT  form, space, envelope, code compliance, and
      traditionally the coordinator of the design team
   ⚠️ STRUCTURAL ENGINEER  load paths, member sizing, stability (§6)
   ⚠️ GEOTECHNICAL ENGINEER  ground behaviour, foundations (§2, §7)
   ⚠️ MEP / SERVICES ENGINEER  mechanical, electrical, plumbing,
      fire protection (§9)
   ⚠️ CIVIL ENGINEER  site, drainage, grading, utilities, roads
   ⚠️ FIRE ENGINEER · ACOUSTICIAN · FAÇADE CONSULTANT · LANDSCAPE ·
      COST CONSULTANT / QUANTITY SURVEYOR
   ⚠️ CONTRACTOR and subcontractors · ⚠️ SPECIALIST TRADE DESIGNERS
      (who design significant portions — steel connections, façade
      systems, sprinklers — and this split is a common gap)
```
**⚠️ The lifecycle**: ⚠️ **feasibility → concept → schematic → design development →
construction documents → tender → construction → commissioning → handover → operation →
eventually adaptation or demolition** (§22 → `building-site-safety-commissioning-retrofit-and-why-projects-fail`).
> **⚠️ GOTCHA — the cost-influence curve is the single most important management fact in
> this domain.** ⚠️ **The ability to influence cost is highest at the start and collapses
> as design progresses, while expenditure does the opposite.** **⚠️ By the time
> construction begins, most of the cost is locked in — which is why late "value
> engineering" usually means removing quality rather than finding efficiency, and why
> the same is true of carbon** (§24.2 → `building-reference`).

---

# PART I — BEFORE DESIGN

## §2. Site and Ground

**⚠️ The ground is the material you did not choose and cannot fully inspect** — ⚠️ **and it
is the largest single source of construction claims.**
```
⚠️ SITE INVESTIGATION  desk study → walkover → ⚠️ BOREHOLES and
   trial pits → lab testing → geotechnical report
   ⚠️ You sample a handful of points and INTERPOLATE an entire site.
   ⚠️ "Differing site conditions" clauses exist because this is
   genuinely uncertain, not because someone was lazy
⚠️ WHAT MATTERS  bearing capacity · ⚠️ DIFFERENTIAL settlement (⚠️ what
   actually damages structures — uniform settlement mostly doesn't) ·
   groundwater level · ⚠️ expansive/shrinkable clays · liquefaction
   potential · contamination · ⚠️ made ground and archaeology
SURVEY  topographic, boundary, ⚠️ existing services (⚠️ and utility
   strikes are a recurring cause of injury and delay)
⚠️ CONTEXT  access, neighbours, party walls, rights of light,
   flood risk, microclimate, orientation
```
**⚠️ Do the investigation BEFORE committing the design.** ⚠️ **The cost of additional
boreholes is trivial against the cost of a foundation redesign after tender.**

---

## §3. Brief and Programming

**⚠️ Programming (US) / briefing (UK) is establishing what the building must DO before
deciding what it looks like.**
**⚠️ Contents**: **spatial requirements and adjacencies, occupancy and use, performance
requirements, budget, programme, operational model, and future flexibility.**
**⚠️ The brief is a requirements document and suffers the same failure modes**: ⚠️ **stated
wants versus actual needs, missing stakeholders, unstated constraints, and requirements
that only surface when a drawing makes them concrete.**
**⚠️ The most valuable early question is "what happens if this is wrong?"** — ⚠️ **because
buildings last decades and briefs are written for a moment.** **⚠️ Loose fit and generic
floorplates outlive bespoke ones.**

---

## §4. Planning, Zoning and Entitlement

**⚠️ Permission to build what you want, where you want it — and it is frequently the
longest-lead risk on a project.**
**⚠️ Typical controls**: **use/zoning, height, floor area ratio or plot ratio, setbacks,
site coverage, parking, daylight and overshadowing, heritage and conservation, design
review, and environmental impact assessment.**
**⚠️ The process is political as well as technical** — ⚠️ **public consultation, objections,
and appeal routes.** ⚠️ **Timelines are frequently measured in quarters or years, and the
risk is not that permission is refused but that it is granted with conditions that change
the scheme.**
**⚠️ Practical advice**: ⚠️ **establish the planning constraints before spending on design,
and treat pre-application engagement as cheap insurance.**

---

# PART II — DESIGN

## §5. Architectural Design

**⚠️ Beyond aesthetics, the architect resolves competing systems into one buildable
object.**
**⚠️ Design drivers**: **program and circulation, orientation and daylight, structural grid,
core placement (⚠️ which governs everything about a tall building — lifts, stairs, risers,
lateral stability), floor-to-floor height (⚠️ set by structure plus services plus ceiling,
and the fight over it is perennial), and façade module.**
**⚠️ Circulation and egress** are ⚠️ **code-driven, not preference-driven** (§10 → `building-structure-foundations-envelope-services-and-fire`) —
**travel distances, exit widths and stair capacity shape the plan before anything else.**
**⚠️ Grid coordination is the central practical discipline**: ⚠️ **a structural grid that
doesn't suit parking below or the façade module above generates cost and awkwardness
everywhere.** **⚠️ Resolve the grid early with structure, parking and façade in the room
together.**
**⚠️ Buildability is a design responsibility** — ⚠️ **a detail that cannot be built with
normal tolerances and normal sequencing will be built badly or changed on site** (§17 → `building-procurement-cost-sequencing-materials-and-quality`).
