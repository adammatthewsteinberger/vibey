---
name: mfg-dfm-metrology-plm-npi-and-what-transfers
description: "Use for the engineering-organisation layer and the software analogy: design for manufacture and assembly, metrology and quality, scale economics and why unit cost depends on volume, CAD, CAE and simulation, PLM as version control for atoms and how it differs from Git, the physical supply chain, new product introduction from prototype to mass production, and an honest account of what transfers to software and what does not."
---

# Manufacturing and Mechanical Engineering: Design for Manufacture and Assembly, Metrology and Quality, Scale Economics, CAD, CAE and Simulation, PLM, the Physical Supply Chain, New Product Introduction, and What Transfers

> **Part 4 of 5** of the *Manufacturing and Mechanical Engineering for Software Devs* reference (plugin `manufacturing-mechanical-engineering-for-software-devs`), covering §17–§24. Sibling skills: `mfg-mechanics-stress-fatigue-and-materials` (§0–§5), `mfg-machine-elements-mechanisms-and-tolerances` (§6–§8), `mfg-process-families-machining-additive-and-moulding` (§9–§16), `mfg-reference` (§25–§30). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The mechanics is settled. Two areas moved. See §25 → `mfg-reference` for additive manufacturing after its correction, and industrial robotics adoption.

> **⚠️ Companion to a civil/industrial engineering reference.** ⚠️ **That one covers flow,
> constraints and safety systems; this one is about physically MAKING things — and the
> lessons are different.**
>
> **⚠️ The governing asymmetry: in software the marginal cost of a change is near zero and
> in manufacturing it is enormous.** ⚠️ **Almost every practice in this document is a
> response to that one fact — tolerances, DFM, PLM, EVT/DVT/PVT gates, and the reason
> mechanical engineers appear conservative to software people.**
>
> **⚠️ GOTCHA** boxes mark the intuitions that don't survive contact with atoms.
>
> **The three ideas that organize this document:**
> 1. **⚠️ NOTHING IS EXACT — everything is a tolerance** (§8 → `mfg-machine-elements-mechanisms-and-tolerances`). **The single biggest mental
>    shift for software people: there is no equality in the physical world, only
>    distributions, and a design that requires exactness is a design that fails.**
> 2. **⚠️ The PROCESS determines the design, not the other way round** (§9 → `mfg-process-families-machining-additive-and-moulding`, §17).
>    **Geometry that's free in CAD can be impossible, or absurdly expensive, to make.**
> 3. **⚠️ FATIGUE kills things that were never overloaded** (§4 → `mfg-mechanics-stress-fatigue-and-materials`). **Most mechanical
>    failures happen far below the static strength, after many cycles — the physical
>    analogue of a bug that only appears after a million requests.**

---

## §17. ⚠️ Design for Manufacture and Assembly

```
⚠️ DFM  ⚠️ design so the chosen process can actually make it
   Uniform walls · draft · avoid undercuts · standard tool sizes ·
   generous tolerances where function permits (§8) · ⚠️ minimize setups
⚠️ DFA  ⚠️ design so it can be assembled — the bigger win
   ⚠️ FEWER PARTS is the dominant lever
   ⚠️ Parts that can only go together ONE way (poka-yoke)
   ⚠️ Assembly from one direction, ideally straight down under gravity
   ⚠️ Self-locating features · avoid parts that tangle or nest
   ⚠️ No blind fasteners; no tools that don't fit
DFT  design for TEST — access, test points, fixturing
DFS  design for SERVICE — ⚠️ what has to come off to reach the thing
   that fails most
```
> **⚠️ GOTCHA — the highest-leverage DFM question is simply "can we delete this part?"**
> ⚠️ **Every part is a drawing, a supplier, a purchase order, an inventory line, an
> inspection, an assembly step, a failure mode and a spare.** **⚠️ Part count reduction beats
> almost every other cost optimization, which is also why §13 → `mfg-process-families-machining-additive-and-moulding`'s part consolidation is
> genuinely valuable rather than a novelty.**

**⚠️ Get manufacturing involved EARLY** — ⚠️ **the standard finding is that most of a
product's cost is locked in during design, when very little has been spent.**
**This is the physical version of "fixing it in requirements is cheaper than fixing it in
production."**

---

## §18. Metrology and Quality

**⚠️ You cannot control what you cannot measure, and measurement itself has error.**
**⚠️ Instruments**: **calipers, micrometers, CMMs (coordinate measuring machines), optical
and laser scanners, gauge blocks, and go/no-go gauges (⚠️ which check conformance without
producing a number — fast and cheap on the line).**
**⚠️ Gauge R&R** is the concept software people should steal: ⚠️ **formally quantifying how
much of your observed variation is the MEASUREMENT SYSTEM rather than the process.**
**⚠️ If your gauge error is a large fraction of the tolerance, your data is noise.**
**⚠️ SPC and process capability** (**Cp, Cpk**) — ⚠️ **Cpk accounts for centring, so a
process can be capable in spread and still produce scrap by being off-target.**
**⚠️ First article inspection, sampling plans, and traceability** — ⚠️ **and the honest
point that 100% inspection is expensive and imperfect, which is why capable processes beat
inspection.**

---

# PART III — SYSTEMS

## §19. Scale Economics

```
⚠️ COST = tooling/NRE amortized + material + labour + machine time +
   scrap + overhead
⚠️ THE CROSSOVERS ARE THE WHOLE GAME
   ⚠️ 1–10 units       machining, AM, hand assembly
   ⚠️ 100–1,000        soft tooling, cast urethane, low-volume moulds
   ⚠️ 10,000+          hard tooling, injection moulding, stamping,
                       automation (§25.2)
⚠️ LEARNING CURVE  ⚠️ Wright's law — unit cost falls a fixed percentage
   per DOUBLING of cumulative production. Real, and repeatedly validated
```
**⚠️ Why "just make a few" is expensive**: ⚠️ **setup, first-article inspection, minimum
order quantities and supplier attention are all roughly fixed costs per order.**
**⚠️ The design-vs-manufacturing cost trade**: ⚠️ **at volume, spending engineering effort to
remove a cent per unit is rational; at ten units it is not.** **⚠️ Software people often get
this backwards in both directions.**

---

## §20. CAD, CAE and Simulation

**⚠️ Parametric, feature-based modelling** (**SolidWorks, Fusion, Onshape, Creo, NX,
CATIA**) — ⚠️ **the model is a program: features in a dependency tree, driven by parameters,
and it can break when a parent feature changes.** **⚠️ "Model regeneration failed" is the
mechanical equivalent of a broken build, and robust modelling practice is real skill.**
**⚠️ Assemblies and MATES/CONSTRAINTS** — ⚠️ **and over-constraining an assembly in CAD is
the digital echo of §7 → `mfg-machine-elements-mechanisms-and-tolerances`'s over-constraint in metal.**
**⚠️ Simulation**: **FEA (stress, thermal, modal), CFD, multibody dynamics, and mould-flow
analysis.**
> **⚠️ GOTCHA — FEA will always give you a colourful answer, and it is frequently wrong.**
> ⚠️ **Garbage in, colourful garbage out: results depend on mesh quality, boundary
> conditions, material models and load assumptions, and the errors are not obvious.**
> **⚠️ The professional habit is to sanity-check against a hand calculation and to validate
> against physical test.** **⚠️ Treat simulation as a hypothesis generator, not evidence.**

**⚠️ Topology optimization and generative design** — ⚠️ **genuinely powerful, and they
produce organic shapes that frequently can only be made additively** (§13 → `mfg-process-families-machining-additive-and-moulding`).

---

## §21. ⚠️ PLM — Version Control for Atoms

> **⚠️ The section software people find most immediately legible, and the comparison is
> instructive in both directions.**
```
⚠️ PART NUMBERS  ⚠️ the immutable identifier. A part number identifies
   a specific, fully-specified thing
⚠️ REVISIONS  ⚠️ Rev A, B, C. ⚠️ THE RULE: if the change makes the new
   part NON-INTERCHANGEABLE with the old, it needs a NEW PART NUMBER,
   not a revision. ⚠️ This is semantic versioning with real consequences,
   because the old part physically exists in warehouses and in the field
⚠️ BOM (Bill of Materials)  ⚠️ the dependency tree. Multi-level,
   with quantities. ⚠️ EBOM (as designed) vs MBOM (as manufactured)
   vs ⚠️ AS-BUILT (what THIS serial number actually contains)
⚠️ ECO / ECN (Engineering Change Order/Notice)  ⚠️ the formal change
   process: what changes, why, effectivity date, disposition of
   existing stock, and approvals
⚠️ EFFECTIVITY  ⚠️ from which serial number or date the change applies.
   ⚠️ There is no "deploy to all users" — the old version stays in
   the field for its entire service life
```
**⚠️ Where the software analogy holds**: **version control, dependency trees, semantic
versioning, change review, release management.**
> **⚠️ GOTCHA — where it BREAKS, and this is the important half.**
> ⚠️ **You cannot roll back atoms.** **⚠️ Every previous revision physically exists — in
> inventory, in transit, in customers' hands — potentially for decades.** **⚠️ A change must
> therefore specify what happens to existing stock (use up, rework, scrap) and whether
> field units need retrofit.**
> **⚠️ There is no "everyone's on the latest version." Spares must be supportable for the
> product's whole service life, which is why part numbering discipline is treated as
> seriously as it is.**

---

## §22. Physical Supply Chain

**⚠️ Make vs buy; ⚠️ single vs dual sourcing (resilience versus volume leverage); ⚠️ minimum
order quantities; lead times measured in weeks to months; and ⚠️ tooling ownership, which
determines whether you can move suppliers.**
**⚠️ The specific risks**: ⚠️ **component obsolescence and end-of-life notices (⚠️ especially
electronics, where a discontinued part can force a redesign), allocation during shortages,
counterfeit parts, quality drift after the initial samples, and the reality that a supplier
change means requalification.**
**⚠️ Incoterms and logistics** determine who bears cost and risk at each point; ⚠️ **and
tariffs and trade policy are now a live design input rather than a back-office concern.**
**⚠️ The lesson software people underestimate**: ⚠️ **a bill of materials is a set of
long-term relationships, not a package manifest.** **You cannot `npm install` a machined
housing.**

---

## §23. New Product Introduction

```
⚠️ THE GATED PIPELINE
   ⚠️ EVT (Engineering Validation)  does the design work at all?
      Hand-built, ugly, functional
   ⚠️ DVT (Design Validation)  does it meet ALL requirements —
      environmental, regulatory, drop, EMC, life testing?
      Production-intent parts, soft tooling
   ⚠️ PVT (Production Validation)  can the FACTORY make it, at
      rate, at yield, with production tooling and real operators?
   ⚠️ MP (Mass Production)  ramp
⚠️ THE GATES EXIST because each stage costs an order of magnitude
   more than the last, and problems get exponentially more
   expensive to fix as you go
```
**⚠️ Also in scope**: ⚠️ **regulatory and certification testing (CE, FCC, UL, and
sector-specific), which has long lead times and can force redesign; qualification of
suppliers and processes; and the ramp itself, where YIELD is the number that matters.**
**⚠️ The software analogue is real but weaker**: ⚠️ **staged rollout is genuinely similar,
and the disanalogy is that a failed software rollout can be reverted in minutes while a
failed PVT means scrapped tooling and a lost quarter.**

---

## §24. ⚠️ What Transfers — and What Doesn't

```
⚠️ TRANSFERS WELL
   ⚠️ 1. TOLERANCE THINKING (§8) — ⚠️ nothing is exact; design for
        distributions, not values. ⚠️ The best single import here
   ⚠️ 2. EXACT CONSTRAINT (§7) — over-constraint creates conflict,
        not robustness. Redundant sources of truth fight
   ⚠️ 3. FATIGUE AS A MODEL (§4) — failures that only appear after
        many cycles, invisible in short tests
   ⚠️ 4. DFA's "delete the part" (§17) — ⚠️ the physical version of
        "the best code is no code," and it's taken far more seriously
   ⚠️ 5. GAUGE R&R (§18) — how much of your measured variation is
        the measurement system?
   ⚠️ 6. INTERCHANGEABILITY RULES (§21) — ⚠️ semantic versioning
        with teeth, because you cannot recall the past
   ⚠️ 7. STAGE GATES (§23) where reversal is genuinely expensive
   ⚠️ 8. SIMULATION SCEPTICISM (§20) — validate models against reality

⚠️ DOESN'T TRANSFER
   ⚠️ 1. FRONT-LOADED DESIGN as a universal virtue. ⚠️ It's rational
        when change costs six figures; it's waterfall when change
        costs nothing
   ⚠️ 2. TOOLING AMORTIZATION — ⚠️ software has no equivalent of
        "the first unit costs $80,000 and the rest cost $2"
   ⚠️ 3. PHYSICAL CONSTRAINTS as a forcing function — ⚠️ mechanical
        designs are disciplined by physics; software has no
        equivalent external constraint, which is both freedom and
        the reason scope creeps
   ⚠️ 4. MATERIAL PROPERTY DATA — ⚠️ there is no handbook of code
        strength (see a civil engineering reference)
   ⚠️ 5. ADVERSARIAL LOADS — ⚠️ steel doesn't probe your assumptions
```
**⚠️ The synthesis I'd offer**: ⚠️ **borrow mechanical engineering's TOLERANCE AND
CONSTRAINT thinking, not its process ceremony.** **⚠️ The ceremony is a rational response
to expensive change; the tolerance thinking is true regardless of what change costs.**
