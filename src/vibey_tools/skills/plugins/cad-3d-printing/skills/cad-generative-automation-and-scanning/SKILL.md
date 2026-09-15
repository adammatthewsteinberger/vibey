---
name: cad-generative-automation-and-scanning
description: "Use when going beyond hand modelling: generative design and lattice structures and what they are actually good for, automation pipelines for batch generation, headless CAD and build integration, and scanning and reverse engineering including point clouds, registration and getting from a scan back to editable geometry."
---

# CAD and 3D Printing: Generative Design, Automation Pipelines, and Scanning

> **Part 4 of 5** of the *CAD and 3D Printing* reference (plugin `cad-3d-printing`), covering §10–§12. Sibling skills: `cad-geometry-kernels-formats-and-code-cad` (§0–§4), `cad-slicing-pipeline-and-processes` (§5–§6), `cad-design-tolerances-and-materials` (§7–§9), `cad-reference` (§13–§18). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The geometry mathematics and process physics are stable; the code-CAD tooling and slicer landscape moved. See §16 → `cad-reference` for both, dated.

> **Scope.** Written for people who write code. **§2–§4 → `cad-geometry-kernels-formats-and-code-cad` are the software engineering
> (kernels, scripting, formats); §6–§9 → `cad-slicing-pipeline-and-processes`, `cad-design-tolerances-and-materials` are the manufacturing physics you need for the
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

## §10. Generative Design and Lattices

**Topology optimization**: ⚠️ **SIMP (Solid Isotropic Material with Penalization) is the
standard method** — treat density as a continuous field per element, penalize intermediate
values, and iterate an FEA to minimize compliance under a mass constraint. **Level-set
methods** are the main alternative. **Output is organic-looking and typically needs
smoothing and interpretation before manufacture.**

**Lattices**: **strut-based (BCC, FCC, octet)** and **TPMS (gyroid, Schwarz)** —
⚠️ **TPMS are defined implicitly, self-supporting, and have no sharp junctions, which is
why they dominate in AM.** Applications: lightweighting, energy absorption, heat exchange,
and **osseointegration in medical implants.**

**⚠️ Implicit modelling is the natural representation here** (§1 → `cad-geometry-kernels-formats-and-code-cad`), because a lattice with
millions of struts is intractable as B-rep and enormous as a mesh, **but trivial as a
function you evaluate at the point of slicing.** **nTop is the prominent commercial tool;
open equivalents are improving.**

**⚠️ The honest caveat**: generative results are only as good as the load cases you
specified. **A part optimized for a single load case is often fragile in every other
direction**, and manufacturability constraints must be in the optimization, not applied
afterward.

---

## §11. Automation Pipelines

**⚠️ This is where a software background pays off most.**
```
Parametric source (git) → CI build (headless CAD) → export STEP/3MF
  → automated slicing (CLI) → G-code artifact → print farm queue → telemetry
```
**Headless invocation**:
```
openscad -o part.stl -D 'width=30' -D 'height=10' part.scad
openscad -o part.3mf --backend=manifold part.scad
prusa-slicer --export-gcode --load config.ini -o out.gcode part.stl
CuraEngine slice -j printer.def.json -l model.stl -o out.gcode
python -c "import cadquery as cq; ..."      # library, no GUI needed
```
**⚠️ All the major slicers have a CLI, and this is under-exploited** — batch slicing,
regression-testing a design change against print time and material use, and generating
variant families are all straightforward once you're in a script.

**Print farm management**: **OctoPrint**, **Klipper + Moonraker + Mainsail/Fluidd**
(⚠️ **Moonraker's API is the practical integration point**), **PrintNanny**, commercial
MES. **Telemetry, queueing, and failure detection** are the operational layer.

**⚠️ Testing a CAD pipeline** is a genuinely interesting problem: assert on **bounding
box, volume, mass properties, and manifoldness**; render images and diff them; **and check
sliced output for support volume and print time** as a regression signal.

---

## §12. Scanning and Reverse Engineering

**Methods**: structured light, laser triangulation, photogrammetry
(⚠️ **cheap — a phone and COLMAP/Meshroom**), CT (⚠️ **captures internal geometry, and
it's the only method that does**), contact probing (CMM).

**Pipeline**: capture → align/register (⚠️ **ICP — iterative closest point**) → merge →
reconstruct surface (Poisson) → clean → **and then the hard part: convert to CAD.**
**⚠️ A scan gives you a mesh, not a model.** Getting a parametric, editable solid means
fitting primitives and surfaces to the scan — semi-automatic at best, and **the actual
work in reverse engineering.**
