---
name: mfg-process-families-machining-additive-and-moulding
description: "Use when choosing how to make something: the process families and what each is good at, casting and forming, machining including the subtractive constraints that shape design, joining, additive manufacturing and where it genuinely wins, injection moulding with tooling cost and cycle time, sheet metal, and surface treatment."
---

# Manufacturing and Mechanical Engineering: The Process Families, Casting and Forming, Machining, Joining, Additive Manufacturing, Injection Moulding, Sheet Metal, and Surface Treatment

> **Part 3 of 5** of the *Manufacturing and Mechanical Engineering for Software Devs* reference (plugin `manufacturing-mechanical-engineering-for-software-devs`), covering §9–§16. Sibling skills: `mfg-mechanics-stress-fatigue-and-materials` (§0–§5), `mfg-machine-elements-mechanisms-and-tolerances` (§6–§8), `mfg-dfm-metrology-plm-npi-and-what-transfers` (§17–§24), `mfg-reference` (§25–§30). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
> 2. **⚠️ The PROCESS determines the design, not the other way round** (§9, §17 → `mfg-dfm-metrology-plm-npi-and-what-transfers`).
>    **Geometry that's free in CAD can be impossible, or absurdly expensive, to make.**
> 3. **⚠️ FATIGUE kills things that were never overloaded** (§4 → `mfg-mechanics-stress-fatigue-and-materials`). **Most mechanical
>    failures happen far below the static strength, after many cycles — the physical
>    analogue of a bug that only appears after a million requests.**

---

## §9. The Process Families

```
⚠️ FORMATIVE  ⚠️ material forced into a shape. Casting, forging,
   moulding, stamping. ⚠️ HIGH tooling cost, LOW unit cost →
   economic only at volume
⚠️ SUBTRACTIVE  ⚠️ material removed. Machining, turning, grinding,
   EDM, laser/waterjet. ⚠️ LOW setup cost, HIGH unit cost, excellent
   precision → prototypes and low-to-mid volume
⚠️ ADDITIVE  ⚠️ material added. ⚠️ Near-zero tooling, high unit cost,
   geometric freedom → prototypes, complexity, low volume (§13, §25.1)
JOINING  welding, brazing, adhesives, fasteners (§12)
```
> **⚠️ GOTCHA — the choice is driven by VOLUME and GEOMETRY, and the crossover points are
> the whole economics.** ⚠️ **At 10 units, machine it. At 10,000, mould or cast it. The
> tooling amortization is the entire argument, and it's why "why don't they just make it
> in metal?" usually has a five-figure answer.**
> **⚠️ The corollary that surprises software people: the FIRST unit and the
> MILLIONTH have wildly different costs, and the process that wins at one loses badly
> at the other.** **⚠️ There is no equivalent of "it compiles the same at any scale."**

---

## §10. Casting and Forming

**⚠️ Casting**: **sand (cheap, rough, large), investment/lost-wax (⚠️ excellent detail,
used for turbine blades), die casting (⚠️ high volume, non-ferrous, fine finish),
continuous.**
**⚠️ Casting design rules**: ⚠️ **uniform wall thickness (thick sections shrink last and
form porosity and voids), draft angles so the part releases, generous fillets, and
awareness that PARTING LINES and gate marks appear somewhere and should be placed
deliberately.**
**⚠️ Forming** works the material plastically: **forging (⚠️ produces favourable grain flow
and superior fatigue properties — which is why critical parts are forged, not cast),
rolling, extrusion (⚠️ constant cross-section, very cheap per metre — the reason
aluminium extrusion profiles are everywhere), drawing, stamping.**
**⚠️ Work hardening and annealing**: ⚠️ **deformation strengthens and embrittles metal;
heat treatment resets it.** **⚠️ This is why you can't bend the same spot twice.**

---

## §11. Machining

**⚠️ Turning (lathe — rotating workpiece), milling (rotating tool), drilling, boring,
grinding, and ⚠️ EDM (electrical discharge — cuts hardened material and internal sharp
corners that a rotating cutter physically cannot).**
```
⚠️ THE DESIGN CONSEQUENCES OF A ROUND CUTTER
   ⚠️ Internal corners CANNOT be sharp — they carry the tool radius.
      ⚠️ Design them with a radius or you're asking for EDM
   ⚠️ Deep narrow pockets need long thin tools that CHATTER and
      deflect — depth-to-diameter ratio is a real limit
   ⚠️ Every SETUP (re-fixturing) costs money and adds tolerance error
   ⚠️ Undercuts and internal features may be unreachable
```
**⚠️ CNC and the toolpath**: ⚠️ **G-code, CAM software, 3-axis vs 5-axis (⚠️ 5-axis reduces
setups and reaches more geometry, at much higher cost), and workholding — which is
frequently the hard part, not the cutting.**
**⚠️ Speeds, feeds and tool wear** — ⚠️ **and the reason material machinability varies so
much: stainless work-hardens, aluminium gums, titanium holds heat in the tool.**

---

## §12. Joining

**⚠️ Welding** (**MIG, TIG, spot, laser, friction stir**): ⚠️ **the HEAT-AFFECTED ZONE is
where welded structures fail — the parent metal's properties are altered, residual stresses
are locked in, and distortion follows.** **⚠️ Weld inspection (dye penetrant, ultrasonic,
radiographic) exists because the defects are internal.**
**⚠️ Brazing and soldering** join without melting the parent metal.
**⚠️ Adhesives** — ⚠️ **excellent in SHEAR, poor in PEEL and CLEAVAGE, so joint design
matters more than adhesive selection; surface preparation dominates strength; and cure
conditions are a process control problem.**
**⚠️ Mechanical fastening** (§6 → `mfg-machine-elements-mechanisms-and-tolerances`) is ⚠️ **the only one that's reversible, which matters
enormously for serviceability and for recycling.**

---

## §13. Additive Manufacturing

```
⚠️ FDM/FFF  extruded thermoplastic. ⚠️ ANISOTROPIC — much weaker
   between layers, so print orientation is a structural decision
SLA / DLP / vat photopolymerization  ⚠️ excellent resolution; resins
   are often brittle and UV-sensitive
SLS  powder bed polymer, ⚠️ no support structures needed
⚠️ LPBF / SLM  metal laser powder bed — ⚠️ the dominant industrial
   metal process. Requires supports, stress relief, and usually
   post-machining of critical surfaces
BINDER JETTING (MBJ) · DED (⚠️ good for repair and large parts) ·
E-BEAM
```
**⚠️ Where AM genuinely wins**: ⚠️ **geometry impossible by other means (internal channels,
lattices), PART CONSOLIDATION (an assembly of 20 parts becoming one — eliminating
fasteners, welds, assembly labour and failure points), one-offs and spares, and cases
where LEAD TIME matters more than unit cost.**
**⚠️ Where it loses**: ⚠️ **anything simple in volume.** **⚠️ Injection moulding, stamping,
casting and machining all beat it at scale** (§9, §25.1 → `mfg-reference`).
**⚠️ The realities that catch people**: ⚠️ **surface finish usually needs post-processing;
support removal is labour; metal parts need stress relief and often HIP; and
QUALIFICATION for critical parts is the real bottleneck, not printing.**

---

## §14. Injection Moulding

**⚠️ The dominant process for plastic parts at volume, and its design rules are strict:**
```
⚠️ UNIFORM WALL THICKNESS — ⚠️ thick sections cool slowly and SINK,
   leaving visible depressions. Core out thick areas
⚠️ DRAFT ANGLE on every vertical face, or the part won't eject
⚠️ RIBS for stiffness instead of thick walls (⚠️ rib thickness
   typically ~50-60% of the wall to avoid sink marks)
⚠️ AVOID UNDERCUTS — they require side actions or lifters, which
   multiply tool cost
⚠️ GATE and PARTING LINE locations are visible; ⚠️ WELD LINES form
   where flow fronts meet and are structurally weak
⚠️ TOOLING IS THE CAPITAL COST — often five to six figures and
   weeks to months of lead time. ⚠️ A tool change is not a
   software patch
```
**⚠️ The economics**: ⚠️ **high tooling, very low unit cost, so the crossover versus
machining or AM is entirely about volume** (§19 → `mfg-dfm-metrology-plm-npi-and-what-transfers`).

---

## §15. Sheet Metal

**⚠️ Cutting (laser, punch, waterjet) and bending — and the constraints are geometric:**
⚠️ **minimum bend radius (too tight cracks the material), BEND ALLOWANCE (the flat pattern
is not the sum of the leg lengths, because material stretches), minimum flange length
(the brake needs material to grip), and hole-to-bend distance (holes near a bend distort).**
**⚠️ Springback** — ⚠️ **the material relaxes after bending, so tooling overbends to
compensate, and the amount depends on the material batch.**
**⚠️ Sheet metal is the cheapest way to make an enclosure at low-to-mid volume**, ⚠️ **and
it's why so much industrial equipment looks the way it does.**

---

## §16. Surface Treatment

**⚠️ Surface finish is specified (Ra), and it matters for fatigue (§4 → `mfg-mechanics-stress-fatigue-and-materials`), sealing, friction,
wear and appearance.**
**⚠️ Treatments**: **anodizing (⚠️ aluminium — hard, and it CHANGES DIMENSIONS slightly),
plating, powder coating, painting, passivation (stainless), heat treatments (⚠️ hardening,
tempering, case hardening, and note they can DISTORT the part, which is why critical
features are machined after).**
**⚠️ Corrosion protection** is a system decision — ⚠️ **material choice, coating, sacrificial
anodes, and design that avoids water traps and crevices.**
