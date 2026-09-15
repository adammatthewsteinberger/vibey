---
name: mfg-mechanics-stress-fatigue-and-materials
description: "Use for the mechanics underneath a physical design: what mechanical engineers actually do, stress, strain and deflection, failure theories and safety factors, fatigue and why most real failures are fatigue failures rather than overload, and materials selection with the property trade-offs that drive it. Includes the router for the whole manufacturing and mechanical engineering reference."
---

# Manufacturing and Mechanical Engineering: What Mechanical Engineers Actually Do, Stress, Strain and Deflection, Failure Theories and Safety Factors, Fatigue, and Materials Selection

> **Part 1 of 5** of the *Manufacturing and Mechanical Engineering for Software Devs* reference (plugin `manufacturing-mechanical-engineering-for-software-devs`), covering §0–§5. Sibling skills: `mfg-machine-elements-mechanisms-and-tolerances` (§6–§8), `mfg-process-families-machining-additive-and-moulding` (§9–§16), `mfg-dfm-metrology-plm-npi-and-what-transfers` (§17–§24), `mfg-reference` (§25–§30). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
> 2. **⚠️ The PROCESS determines the design, not the other way round** (§9 → `mfg-process-families-machining-additive-and-moulding`, §17 → `mfg-dfm-metrology-plm-npi-and-what-transfers`).
>    **Geometry that's free in CAD can be impossible, or absurdly expensive, to make.**
> 3. **⚠️ FATIGUE kills things that were never overloaded** (§4). **Most mechanical
>    failures happen far below the static strength, after many cycles — the physical
>    analogue of a bug that only appears after a million requests.**

---

## §0. Routing

| You want... | Go to |
|---|---|
| **⚠️ What mech eng actually is** | **§1** |
| Stress and strain | §2 |
| Failure theories | §3 |
| **⚠️ Fatigue** | **§4** |
| Materials selection | §5 |
| Machine elements | §6 → `mfg-machine-elements-mechanisms-and-tolerances` |
| Mechanisms | §7 → `mfg-machine-elements-mechanisms-and-tolerances` |
| **⚠️ Tolerances and GD&T** | **§8 → `mfg-machine-elements-mechanisms-and-tolerances`** |
| **Process families** | **§9 → `mfg-process-families-machining-additive-and-moulding`** |
| Casting and forming | §10 → `mfg-process-families-machining-additive-and-moulding` |
| Machining | §11 → `mfg-process-families-machining-additive-and-moulding` |
| Joining | §12 → `mfg-process-families-machining-additive-and-moulding` |
| Additive | §13 → `mfg-process-families-machining-additive-and-moulding` |
| Injection moulding | §14 → `mfg-process-families-machining-additive-and-moulding` |
| Sheet metal | §15 → `mfg-process-families-machining-additive-and-moulding` |
| Surface treatment | §16 → `mfg-process-families-machining-additive-and-moulding` |
| **⚠️ Design for manufacture** | **§17 → `mfg-dfm-metrology-plm-npi-and-what-transfers`** |
| Metrology and QC | §18 → `mfg-dfm-metrology-plm-npi-and-what-transfers` |
| Scale economics | §19 → `mfg-dfm-metrology-plm-npi-and-what-transfers` |
| CAD and simulation | §20 → `mfg-dfm-metrology-plm-npi-and-what-transfers` |
| **⚠️ PLM — version control for atoms** | **§21 → `mfg-dfm-metrology-plm-npi-and-what-transfers`** |
| Physical supply chain | §22 → `mfg-dfm-metrology-plm-npi-and-what-transfers` |
| **NPI: EVT/DVT/PVT** | **§23 → `mfg-dfm-metrology-plm-npi-and-what-transfers`** |
| **⚠️ What transfers** | **§24 → `mfg-dfm-metrology-plm-npi-and-what-transfers`** |
| **What's live** | **§25 → `mfg-reference`** |
| Misconceptions, numbers | §26–§27 → `mfg-reference` |
| Books, quick ref, method | §28–§30 → `mfg-reference` |

---

## §1. ⚠️ What Mechanical Engineers Actually Do

**⚠️ Less calculation than software people imagine, and far more SPECIFYING, SOURCING and
TOLERANCING.**
```
⚠️ THE ACTUAL WORK  requirements → concept → detail design →
   ⚠️ TOLERANCE ANALYSIS → material and process selection →
   ⚠️ DFM review → prototype → test → qualify → release →
   ⚠️ manage changes forever (§21)
⚠️ THE HARD PARTS  ⚠️ tolerance stack-up (§8) · fatigue (§4) ·
   thermal expansion · vibration · manufacturability (§17) ·
   ⚠️ and the supply chain (§22)
⚠️ THE ANALOGUE OF "IT COMPILES"  ⚠️ a CAD model that looks right
   proves almost nothing. It must be MAKEABLE, ASSEMBLABLE,
   TOLERANT of variation, and survivable
```
**⚠️ The mindset difference worth naming immediately**: ⚠️ **a software engineer optimizes
for changeability because change is cheap.** **⚠️ A mechanical engineer optimizes for
GETTING IT RIGHT BEFORE COMMITTING, because tooling costs six figures and takes months,
and a field recall costs more than the programme.**

---

# PART I — MECHANICAL DESIGN

## §2. Stress, Strain and Deflection

```
⚠️ STRESS σ = F/A (Pa) — ⚠️ INTENSITY of load, not load
⚠️ STRAIN ε = ΔL/L — dimensionless deformation
⚠️ YOUNG'S MODULUS E = σ/ε — ⚠️ STIFFNESS, and it is NOT strength.
   ⚠️ Steel and stainless have nearly the same E; their strengths
   differ enormously. Confusing the two is the classic beginner error
⚠️ POISSON'S RATIO — lateral contraction under axial load
⚠️ YIELD strength (permanent deformation begins) vs ULTIMATE (fracture)
⚠️ MODES  tension · compression · shear · bending · torsion ·
   ⚠️ BUCKLING (a STABILITY failure — a slender column fails long
   before it crushes, and the load depends on LENGTH SQUARED)
```
**⚠️ Stress concentration is the practical one**: ⚠️ **holes, notches, sharp internal corners
and abrupt section changes multiply local stress by a factor Kt, often 2–3×.**
**⚠️ This is why fillets exist, and why a sharp internal corner is a crack waiting to
start** (§4). **⚠️ "Add a radius" is one of the most common review comments in mechanical
design.**
**⚠️ Deflection often governs before strength** — ⚠️ **a beam that is strong enough may
still bend too much to work, and stiffness scales differently from strength (for a beam,
with the CUBE of depth), which is why I-beams and ribs exist.**

---

## §3. Failure Theories and Safety Factors

**⚠️ For ductile materials, von Mises (distortion energy) is the standard criterion;
for brittle materials, maximum normal stress.** ⚠️ **The distinction matters because
brittle materials fail in TENSION at surface flaws with no warning.**
**⚠️ Ductile vs brittle is the same lesson as elsewhere**: ⚠️ **ductile yields visibly
first; brittle fails suddenly and completely.** **⚠️ Design for ductile behaviour wherever
consequences matter.**
**⚠️ Safety factors** cover quantified uncertainty (see a civil engineering reference) —
⚠️ **material variability, load uncertainty, model error, and degradation.** **⚠️ They are
not a substitute for understanding the failure mode.**
**⚠️ Temperature changes everything**: ⚠️ **many steels undergo a ductile-to-brittle
transition on cooling — the mechanism behind several famous structural failures — and
polymers change behaviour dramatically around their glass transition.**

---

## §4. ⚠️ Fatigue

> **⚠️ The single most important failure mode, and the one software intuition has no
> analogue for.** ⚠️ **Components fail after many cycles at stresses FAR BELOW the static
> strength — sometimes below the yield point entirely.**
```
⚠️ S-N CURVE  stress amplitude vs cycles to failure
   ⚠️ Some steels show an ENDURANCE LIMIT — below it, effectively
   infinite life. ⚠️ ALUMINIUM DOES NOT. Aluminium accumulates
   damage at any stress amplitude, which is why aircraft have
   finite lives measured in cycles
⚠️ CRACK INITIATION then PROPAGATION then fast fracture
⚠️ MOST OF THE LIFE IS INITIATION, which is why SURFACE matters
   enormously — ⚠️ finish, scratches, tool marks, corrosion pits
   and stress concentrations (§2) all start cracks
⚠️ MEAN STRESS matters (Goodman/Gerber); ⚠️ COMPRESSIVE residual
   stress HELPS, which is why shot peening works
```
**⚠️ Related time-dependent failures**: ⚠️ **CREEP (slow deformation under sustained load at
high temperature — the limit on turbine blades), stress corrosion cracking, hydrogen
embrittlement, and fretting.**
**⚠️ The software translation, and it's genuinely useful**: ⚠️ **fatigue is the physical
analogue of a defect that only manifests after prolonged operation** — **memory
fragmentation, connection pool exhaustion, log disk filling, certificate expiry.**
**⚠️ Both are invisible in a short test, and both require thinking in CYCLES or TIME rather
than in single events.**

---

## §5. Materials Selection

```
⚠️ STEELS  cheap, stiff, strong, ⚠️ recyclable; rusts unless protected.
   ⚠️ Alloy and heat treatment change properties enormously — "steel"
   is a family, not a material
⚠️ STAINLESS  corrosion-resistant, ⚠️ same stiffness as steel, more
   expensive, ⚠️ poorer thermal conductivity, some grades magnetic
⚠️ ALUMINIUM  ⚠️ ~1/3 the density AND ~1/3 the stiffness of steel;
   excellent strength-to-weight, ⚠️ NO endurance limit (§4)
TITANIUM  excellent specific strength, biocompatible, ⚠️ expensive
   and difficult to machine
⚠️ POLYMERS  thermoplastics (remeltable, ⚠️ mouldable) vs thermosets
   (cured, not remeltable). ⚠️ CREEP at room temperature, and
   properties change with temperature and UV
COMPOSITES  ⚠️ anisotropic — strength depends on fibre direction.
   Superb specific properties, ⚠️ hard to inspect and to repair
CERAMICS  hard, stiff, heat-resistant, ⚠️ BRITTLE
```
**⚠️ The selection process** (Ashby's method): ⚠️ **define the function, the objective and
the constraints, derive a material index, and use property charts.** **⚠️ The key insight
is that the right property is usually a RATIO — specific strength, specific stiffness,
or strength per unit cost — not an absolute value.**
**⚠️ Galvanic corrosion is the one that bites in assembly**: ⚠️ **dissimilar metals in
electrical contact with an electrolyte corrode preferentially, and the less noble one
goes.** **Aluminium against stainless is a classic mistake.**
