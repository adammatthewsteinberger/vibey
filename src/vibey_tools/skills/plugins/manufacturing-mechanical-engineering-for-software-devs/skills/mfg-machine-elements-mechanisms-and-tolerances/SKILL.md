---
name: mfg-machine-elements-mechanisms-and-tolerances
description: "Use when specifying parts and how they fit together: machine elements including bearings, fasteners, springs, gears and shafts, mechanisms and kinematics with degrees of freedom and linkages, and tolerances and geometric dimensioning and tolerancing — what a tolerance actually costs and why over-tolerancing is the expensive default."
---

# Manufacturing and Mechanical Engineering: Machine Elements, Mechanisms and Kinematics, and Tolerances and GD&T

> **Part 2 of 5** of the *Manufacturing and Mechanical Engineering for Software Devs* reference (plugin `manufacturing-mechanical-engineering-for-software-devs`), covering §6–§8. Sibling skills: `mfg-mechanics-stress-fatigue-and-materials` (§0–§5), `mfg-process-families-machining-additive-and-moulding` (§9–§16), `mfg-dfm-metrology-plm-npi-and-what-transfers` (§17–§24), `mfg-reference` (§25–§30). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
> 1. **⚠️ NOTHING IS EXACT — everything is a tolerance** (§8). **The single biggest mental
>    shift for software people: there is no equality in the physical world, only
>    distributions, and a design that requires exactness is a design that fails.**
> 2. **⚠️ The PROCESS determines the design, not the other way round** (§9 → `mfg-process-families-machining-additive-and-moulding`, §17 → `mfg-dfm-metrology-plm-npi-and-what-transfers`).
>    **Geometry that's free in CAD can be impossible, or absurdly expensive, to make.**
> 3. **⚠️ FATIGUE kills things that were never overloaded** (§4 → `mfg-mechanics-stress-fatigue-and-materials`). **Most mechanical
>    failures happen far below the static strength, after many cycles — the physical
>    analogue of a bug that only appears after a million requests.**

---

## §6. Machine Elements

**⚠️ Most mechanical design is SELECTING standard components, not designing new ones.**
```
⚠️ FASTENERS  ⚠️ a bolted joint works by CLAMPING — preload creates
   friction that carries the load, and the bolt should ideally not
   see shear directly. ⚠️ This is why TORQUE SPEC matters and why
   under-torqued bolts fatigue and fail
   ⚠️ Torque is a poor proxy for preload (friction scatter is large),
   which is why critical joints use angle or stretch measurement
⚠️ BEARINGS  rolling vs plain vs fluid film. ⚠️ Rated by L10 life —
   a STATISTICAL life at which 10% have failed, not a guarantee
⚠️ GEARS  ratio, module/pitch, ⚠️ backlash (lost motion on reversal —
   a real problem in positioning systems)
SPRINGS · SEALS (⚠️ dynamic seals are a common failure point) ·
COUPLINGS · belts and chains
```
**⚠️ Standard parts exist and should be used**: ⚠️ **ISO/ANSI threads, standard bearing
sizes, stock material thicknesses.** **⚠️ A custom fastener is a supply chain liability
forever** (§22 → `mfg-dfm-metrology-plm-npi-and-what-transfers`).
**⚠️ Threadlocking, prevailing-torque nuts and lock washers** — ⚠️ **and note that ordinary
split lock washers have been shown to be largely ineffective, which is folklore that
persists.**

---

## §7. Mechanisms and Kinematics

**⚠️ Degrees of freedom, linkages (⚠️ four-bar being the workhorse), cams, and the
distinction between kinematics (motion) and dynamics (forces causing it).**
> **⚠️ GOTCHA — EXACT CONSTRAINT (kinematic) design is the concept software people find
> most surprising and most useful.** ⚠️ **A rigid body has six degrees of freedom; constrain
> each exactly once and the assembly is deterministic.** **⚠️ OVER-CONSTRAINT — the
> intuitive "add more bolts and pins to make it solid" — forces parts to fight each other,
> transmits manufacturing variation into stress, and produces assemblies that bind or warp
> unpredictably.**
> **⚠️ The classic example: a three-legged stool never rocks; a four-legged one does,
> because it's over-constrained.**
> **⚠️ The software analogue is real: redundant sources of truth don't add robustness, they
> add contradiction.**

**⚠️ Vibration and resonance**: ⚠️ **every structure has natural frequencies; excite one and
amplitude grows until damping or failure limits it.** **⚠️ Modal analysis, damping, tuned
mass dampers, and the practical rule to keep excitation frequencies away from natural
ones.**

---

## §8. ⚠️ Tolerances and GD&T

> **⚠️ THE conceptual shift for software people. In the physical world there is no
> equality — only distributions.** ⚠️ **A "10 mm" hole is never 10 mm; it is 10 mm ± something,
> and the design must work across the whole range.**
```
⚠️ TOLERANCE  the permitted variation. ⚠️ TIGHTER TOLERANCE COSTS
   MORE, often NON-LINEARLY — halving a tolerance can multiply cost
   several-fold by forcing a different process (§9) or added
   inspection. ⚠️ Over-tolerancing is the most common and most
   expensive novice error in mechanical design
⚠️ FITS  clearance · transition · interference (⚠️ press fits, where
   the parts are deliberately the "wrong" size)
⚠️ STACK-UP  ⚠️ tolerances ACCUMULATE across an assembly
   ⚠️ WORST CASE  sum of all tolerances — safe, expensive, and
      astronomically unlikely
   ⚠️ STATISTICAL (RSS)  root-sum-square — realistic, and it
      ASSUMES independence and centred distributions, which
      real processes often violate
⚠️ GD&T (ASME Y14.5 / ISO GPS)  ⚠️ specifies FUNCTION rather than
   just dimensions: form (flatness, straightness), orientation
   (perpendicularity, angularity), location (⚠️ TRUE POSITION),
   and runout — all relative to explicitly declared DATUMS
⚠️ MMC / BONUS TOLERANCE  ⚠️ as a feature departs from maximum
   material condition, extra positional tolerance becomes
   available — because the ASSEMBLY still works. This is
   tolerancing the FUNCTION, not the number
```
**⚠️ Why GD&T exists at all**: ⚠️ **plus/minus dimensioning is ambiguous about what matters
and creates square tolerance zones where the function wants round ones.** **⚠️ GD&T states
the design intent unambiguously, which is exactly what a specification should do.**
**⚠️ DATUMS are the key idea**: ⚠️ **they define how the part is referenced and therefore how
it is measured and fixtured — and inconsistent datums between design, manufacture and
inspection is a recurring source of parts that "measure fine" and don't fit.**

---

# PART II — MAKING THINGS
