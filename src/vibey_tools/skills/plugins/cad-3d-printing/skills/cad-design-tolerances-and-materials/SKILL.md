---
name: cad-design-tolerances-and-materials
description: "Use when designing a part that has to work rather than just print: design for additive manufacturing including overhangs, supports, orientation and anisotropy, tolerances and fits and how to achieve them on a printer that does not hold them natively, and materials and their mechanical, thermal and environmental behaviour."
---

# CAD and 3D Printing: Design for Additive Manufacturing, Tolerances and Fits, and Materials

> **Part 3 of 5** of the *CAD and 3D Printing* reference (plugin `cad-3d-printing`), covering §7–§9. Sibling skills: `cad-geometry-kernels-formats-and-code-cad` (§0–§4), `cad-slicing-pipeline-and-processes` (§5–§6), `cad-generative-automation-and-scanning` (§10–§12), `cad-reference` (§13–§18). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The geometry mathematics and process physics are stable; the code-CAD tooling and slicer landscape moved. See §16 → `cad-reference` for both, dated.

> **Scope.** Written for people who write code. **§2–§4 → `cad-geometry-kernels-formats-and-code-cad` are the software engineering
> (kernels, scripting, formats); §6–§9 → `cad-slicing-pipeline-and-processes` are the manufacturing physics you need for the
> software to produce parts that work.**
>
> **⚠️ GOTCHA** boxes mark what silently produces a bad model or an unprintable part.
>
> **The three ideas that organize everything:**
> 1. **⚠️ Choose your representation before your tool.** B-rep, mesh, and implicit fields
>    are not interchangeable — each makes some operations trivial and others impossible,
>    and **most CAD frustration is a representation mismatch** (§1 → `cad-geometry-kernels-formats-and-code-cad`).
> 2. **⚠️ Every export loses something.** STL loses units, topology, colour, and all
>    parametric intent. STEP keeps the solid but not the feature tree. **Know what falls
>    off at each hop** (§3 → `cad-geometry-kernels-formats-and-code-cad`).
> 3. **⚠️ The printer does not build your model, it builds your G-code.** Slicing is a
>    lossy, opinionated transformation, and the part's real properties — strength,
>    accuracy, surface — are determined there and by the process physics, not by the
>    CAD (§5 → `cad-slicing-pipeline-and-processes`, §6 → `cad-slicing-pipeline-and-processes`).

---

## §7. Design for Additive Manufacturing

**⚠️ The constraint list, and each one has a physical reason:**
- **Overhangs** — ⚠️ **45° is the classic threshold for FDM**, and it comes from each layer
  needing roughly half its width supported by the one below. **Design chamfers instead of
  overhangs where you can.**
- **Bridges** — flat over a gap beats an unsupported curve.
- **⚠️ Hole shape**: horizontal circular holes print with a sagging top.
  **A teardrop or diamond profile prints cleanly without support** — a genuinely useful
  trick.
- **Minimum wall thickness** — ⚠️ **relate it to nozzle width**: a wall should be a whole
  multiple of extrusion width (e.g. 0.8 mm or 1.2 mm for a 0.4 mm nozzle), or the slicer
  leaves a gap or over-extrudes to fill it.
- **⚠️ First layer and elephant's foot** — chamfer the bottom edge by 0.5 mm.
- **Orientation** — §6.1 → `cad-slicing-pipeline-and-processes`. **Strength, surface finish, support requirement and print time
  are all decided by it, and they conflict.**
- **⚠️ Escape holes** for SLA resin and SLS powder (§6.2 → `cad-slicing-pipeline-and-processes`).
- **Print-in-place mechanisms** — ⚠️ **need a clearance of roughly 0.3–0.5 mm on FDM to
  avoid fusing.**
- **Consolidate assemblies** — the classic AM win, ⚠️ **but check you can still service it.**

---

## §8. Tolerances and Fits

**⚠️ The dimensions you model are not the dimensions you get.** Sources: extrusion width
and flow, thermal shrinkage, elephant's foot, backlash, and slicer offset behaviour.

```
⚠️ FDM typical accuracy    ±0.1–0.5 mm (dimension-dependent)
SLA                         ±0.05–0.15 mm
SLS/MJF                     ±0.15–0.3 mm
Metal (post-processed)      ±0.1 mm, better with machining
```
**⚠️ Holes print undersize on FDM** — the extrudate on the inside of a curve compresses
inward. **Oversize modelled holes by 0.1–0.4 mm, or design for a drill/tap operation.**

**Practical clearances (FDM, per side)**:
```
Press fit          0.0 to −0.1 mm    ⚠️ interference
Tight sliding      0.15–0.2 mm
Free running       0.3–0.4 mm
Print-in-place     0.3–0.5 mm        ⚠️ (§7)
```
**⚠️ Calibrate your own machine and material rather than trusting these** — a tolerance
test print with a range of clearances takes 20 minutes and is worth more than any table.

**Threads**: printed threads work above roughly M6 but are weak. ⚠️ **Heat-set inserts are
the right answer for anything load-bearing in FDM**, followed by tapping into a printed
boss, then captive nuts.

---

## §9. Materials

| Material | ⚠️ Character |
|---|---|
| **PLA** | ⚠️ **Easy, stiff, low warp; softens ~60 °C — useless in a hot car** |
| **PETG** | Tougher, less brittle, more temperature resistant; ⚠️ **strings, and sticks to build plates too well** |
| **ABS/ASA** | Heat and impact resistant; ⚠️ **warps badly, needs an enclosure, emits styrene — ventilate** |
| **Nylon (PA)** | ⚠️ **Tough and wear-resistant; hygroscopic — must be dried, and absorbs moisture within hours** |
| **TPU** | Flexible; ⚠️ **needs direct drive and slow speeds** |
| **PC** | Strong and heat resistant; hard to print |
| **PEEK/PEI** | ⚠️ **Engineering-grade, 350+ °C hotends, chamber heating** |
| **Composite (CF/GF-filled)** | Stiffer, dimensionally stable; ⚠️ **abrasive — hardened nozzle mandatory** |
| **SLA resins** | Standard, tough, castable, dental, high-temp; ⚠️ **uncured resin is a sensitiser — gloves, always** |

**⚠️ Moisture is the most common invisible cause of bad prints** — hygroscopic filament
(nylon especially, but also PETG and TPU) hydrolyses and steams at the nozzle, producing
stringing, popping, weak layers and poor surface. **Dry it; store it dry.**
