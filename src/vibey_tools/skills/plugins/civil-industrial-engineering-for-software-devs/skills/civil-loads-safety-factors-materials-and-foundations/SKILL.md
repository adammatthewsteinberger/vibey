---
name: civil-loads-safety-factors-materials-and-foundations
description: "Use when reaching for a civil-engineering analogy about software, or when you need the actual content behind it: why “software should be more like real engineering” keeps recurring, dead and live loads and load paths, factor of safety and load and resistance factor design, steel, concrete and timber and how each fails, and foundations, soil and bearing capacity. Includes the router for the whole civil and industrial engineering reference."
---

# Civil and Industrial Engineering: Why the Comparison Keeps Coming Up, Loads, Factors of Safety, Materials, and Foundations

> **Part 1 of 5** of the *Civil and Industrial Engineering for Software Devs* reference (plugin `civil-industrial-engineering-for-software-devs`), covering §0–§5. Sibling skills: `civil-codes-licensure-failure-analysis-and-construction` (§6–§10), `civil-industrial-engineering-queueing-toc-and-lean` (§11–§16), `civil-reliability-safety-and-what-transfers-to-software` (§17–§22), `civil-reference` (§23–§28). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The mechanics and the operations research are settled. Two areas carry live numbers. See §23 → `civil-reference` for US infrastructure condition, and the megaproject estimation data.

> **⚠️ Written for people who build software and keep hearing that they should be more
> like "real engineers."** **Complements a thermodynamics/fluids reference (the physics),
> an engineering-process reference (methodology), and a security reference (§20 → `civil-reliability-safety-and-what-transfers-to-software`'s
> hierarchy of controls recurs there).**
>
> **⚠️ The honest framing: some of this transfers extremely well and some of it does not,
> and the borrowings that fail are usually the ones taken as metaphor rather than as
> mechanism.** ⚠️ **§21 → `civil-reliability-safety-and-what-transfers-to-software` and §22 → `civil-reliability-safety-and-what-transfers-to-software` make that distinction explicitly, and they're the point of
> the document.**
>
> **⚠️ GOTCHA** boxes mark the analogies that break, and the borrowed ideas software
> commonly misuses.
>
> **The three ideas that organize this document:**
> 1. **⚠️ Civil engineering's real lesson isn't "plan more" — it's the INSTITUTIONAL
>    apparatus** (§6 → `civil-codes-licensure-failure-analysis-and-construction`, §7 → `civil-codes-licensure-failure-analysis-and-construction`, §8 → `civil-codes-licensure-failure-analysis-and-construction`). **Codes, licensure, liability and mandatory failure
>    investigation, not the calculations.**
> 2. **⚠️ Industrial engineering's queueing and constraint mathematics transfer DIRECTLY,
>    with no metaphor required** (§11 → `civil-industrial-engineering-queueing-toc-and-lean`, §12 → `civil-industrial-engineering-queueing-toc-and-lean`). **Little's Law is as true of a deployment
>    pipeline as of a factory, and it is the single most valuable import in this document.**
> 3. **⚠️ The disanalogies are load-bearing** (§22 → `civil-reliability-safety-and-what-transfers-to-software`). **Software's marginal cost of
>    replication is zero, its "material properties" are unmeasured, and its requirements
>    change during construction — and each of those breaks a specific borrowed practice.**

---

## §0. Routing

| You want... | Go to |
|---|---|
| **⚠️ What actually transfers** | **§1, §21 → `civil-reliability-safety-and-what-transfers-to-software`, §22 → `civil-reliability-safety-and-what-transfers-to-software`** |
| Loads and structural basics | §2 |
| **⚠️ Factor of safety** | **§3** |
| Materials | §4 |
| Foundations and soil | §5 |
| **⚠️ Codes and standards** | **§6 → `civil-codes-licensure-failure-analysis-and-construction`** |
| **⚠️ Licensure and liability** | **§7 → `civil-codes-licensure-failure-analysis-and-construction`** |
| **⚠️ Failure analysis** | **§8 → `civil-codes-licensure-failure-analysis-and-construction`** |
| Construction sequencing | §9 → `civil-codes-licensure-failure-analysis-and-construction` |
| Infrastructure systems | §10 → `civil-codes-licensure-failure-analysis-and-construction` |
| **What IE actually is** | **§11 → `civil-industrial-engineering-queueing-toc-and-lean`** |
| **⚠️ Queueing and Little's Law** | **§12 → `civil-industrial-engineering-queueing-toc-and-lean`** |
| **Theory of Constraints** | **§13 → `civil-industrial-engineering-queueing-toc-and-lean`** |
| **⚠️ Lean and the TPS** | **§14 → `civil-industrial-engineering-queueing-toc-and-lean`** |
| Six Sigma and SPC | §15 → `civil-industrial-engineering-queueing-toc-and-lean` |
| Work measurement | §16 → `civil-industrial-engineering-queueing-toc-and-lean` |
| Scheduling and inventory | §17 → `civil-reliability-safety-and-what-transfers-to-software` |
| Human factors | §18 → `civil-reliability-safety-and-what-transfers-to-software` |
| **Reliability engineering** | **§19 → `civil-reliability-safety-and-what-transfers-to-software`** |
| **⚠️ Safety engineering** | **§20 → `civil-reliability-safety-and-what-transfers-to-software`** |
| **⚠️ What transfers** | **§21 → `civil-reliability-safety-and-what-transfers-to-software`** |
| **⚠️ What doesn't** | **§22 → `civil-reliability-safety-and-what-transfers-to-software`** |
| **What's live** | **§23 → `civil-reference`** |
| Misconceptions, numbers, books | §24–§26 → `civil-reference` |
| Quick reference, method | §27–§28 → `civil-reference` |

---

## §1. ⚠️ Why This Comparison Keeps Coming Up

**⚠️ "Software engineering isn't real engineering" is an argument with a century of
baggage, and both sides usually argue past each other.**
```
⚠️ THE CIVIL SIDE     we have codes, licensure, liability, mandatory failure
   investigation, and calculations with margins. You have none of that
⚠️ THE SOFTWARE SIDE  our requirements change during construction, our
   material has no measurable properties, and our marginal cost of
   replication is zero. Your model doesn't fit
```
**⚠️ Both are right about the facts and wrong about the conclusion.** ⚠️ **The useful
question isn't "is software engineering real engineering" — it's WHICH SPECIFIC PRACTICES
transfer and why** (§21 → `civil-reliability-safety-and-what-transfers-to-software`, §22 → `civil-reliability-safety-and-what-transfers-to-software`).
**⚠️ The pattern worth noticing up front**: ⚠️ **software's most successful borrowings are
MATHEMATICAL (queueing theory, constraint analysis, reliability statistics), and its least
successful are CULTURAL (lean-as-slogan, Six Sigma belts, "engineering discipline" as
exhortation).** **The maths transfers because the maths doesn't care what's flowing
through the system.**

---

# PART I — CIVIL ENGINEERING

## §2. Loads and Structure

```
DEAD LOAD      permanent — the structure's own weight
LIVE LOAD      ⚠️ variable and occupancy-dependent — people, furniture, traffic
ENVIRONMENTAL  wind, snow, seismic, thermal, hydrostatic
⚠️ DYNAMIC vs STATIC  ⚠️ a moving or oscillating load is not the same as its
   static equivalent — resonance and fatigue are separate failure paths
```
**⚠️ Load paths**: ⚠️ **every load must have a continuous path to the foundation, and
tracing that path is the core structural skill.** **A load path that's interrupted — by a
removed wall, a modified connection — is how buildings fail.**
**Structural elements**: **beams (bending), columns (⚠️ compression, and buckling as a
STABILITY failure distinct from crushing), ties (tension), trusses (⚠️ axial only, which
is why they're efficient), arches and cables (⚠️ shape-dependent force paths), shear walls
and bracing (lateral).**
**⚠️ The software-relevant abstraction**: ⚠️ **structural analysis is about tracing how
demand propagates to where it's ultimately resisted** — **which is exactly what
dependency and load analysis is in a distributed system, and the "interrupted load path"
failure has an exact analogue in a removed layer of redundancy nobody re-derived.**

---

## §3. ⚠️ Factor of Safety

**⚠️ The idea software people cite most and understand least.**
```
⚠️ FoS = capacity / demand.  Typically ~1.5–2.0 for structures, higher
   where consequences are severe or knowledge is poor
⚠️ IT COVERS IGNORANCE, NOT SLOPPINESS: material variability, workmanship
   tolerance, load uncertainty, model error, degradation over time
⚠️ MODERN PRACTICE has largely moved to LIMIT STATE / LRFD design —
   separate partial factors applied to LOADS and to RESISTANCES,
   calibrated probabilistically, rather than one global fudge factor
```
> **⚠️ GOTCHA — a factor of safety is not "build it twice as strong to be safe," and it is
> not a margin for bad work.** ⚠️ **It's a calibrated allowance for QUANTIFIED
> uncertainty in materials, loads and models.** **⚠️ The reason software can't simply adopt
> it is that software has no equivalent of a characteristic material strength — there is
> no distribution of "code strength" to apply a partial factor to.**
> **⚠️ What software CAN adopt is the underlying logic: identify the specific
> uncertainties, size the margin to each one, and state it.** **Capacity headroom, error
> budgets and rate limits are the real analogues** (§21 → `civil-reliability-safety-and-what-transfers-to-software`).

**⚠️ Redundancy vs margin is a genuine distinction**: ⚠️ **a factor of safety makes one
element stronger; redundancy provides an alternative path when one fails.**
**⚠️ Structural robustness — resistance to DISPROPORTIONATE collapse — is the redundancy
concept, and it entered codes largely because of Ronan Point** (§8 → `civil-codes-licensure-failure-analysis-and-construction`).

---

## §4. Materials

```
STEEL      ⚠️ strong in tension AND compression, DUCTILE (⚠️ it yields
   visibly before failing — a warning), predictable, corrodes, loses
   strength in fire
CONCRETE   ⚠️ strong in compression, WEAK in tension, BRITTLE, cheap,
   durable. ⚠️ Reinforced concrete puts steel where the tension is —
   which is the single most important composite idea in construction
TIMBER     ⚠️ anisotropic (properties depend on grain direction), renewable;
   mass timber (CLT) is the modern engineered form
SOIL       ⚠️ the most variable "material" and rarely fully characterized (§5)
```
**⚠️ Properties that matter**: **strength, stiffness (⚠️ Young's modulus — a stiff
structure and a strong one are different things, and serviceability failures are stiffness
failures), ductility, toughness, fatigue resistance, creep.**
> **⚠️ GOTCHA — DUCTILE vs BRITTLE failure is the concept most worth stealing.**
> ⚠️ **Ductile materials deform visibly and progressively before failing, giving warning
> and time to evacuate; brittle materials fail suddenly and completely.** **Seismic design
> deliberately engineers ductility so buildings bend rather than shatter.**
> **⚠️ The software translation is exact and underused: design systems to DEGRADE
> GRACEFULLY rather than fail suddenly.** **Load shedding, backpressure, circuit breakers
> and feature degradation are ductility. A system that runs perfectly until it falls over
> completely is brittle.**

---

## §5. Foundations and Soil

**⚠️ Soil is the material you didn't choose and cannot fully inspect, which makes it the
dominant source of uncertainty in most projects.**
**Bearing capacity, settlement (⚠️ DIFFERENTIAL settlement is what damages structures,
not uniform settlement), consolidation, shear strength, effective stress, liquefaction.**
**Foundation types**: **shallow (spread footings, mat) vs deep (piles, caissons) —
⚠️ chosen by what's available at depth, not by preference.**
**⚠️ Site investigation is always insufficient**: ⚠️ **you sample a few boreholes and
interpolate an entire site**, **and "differing site conditions" is one of the most common
sources of construction claims.**
**⚠️ The software parallel is genuine**: **⚠️ the legacy system, the undocumented data, the
production environment you inherited — you sample it, you interpolate, and the surprises
are in what you didn't sample.**
