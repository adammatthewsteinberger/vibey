---
name: cad-slicing-pipeline-and-processes
description: "Use when turning a model into a physical part: the slicing pipeline including the slicing step itself, the 2D operations that follow, the decisions that actually matter, and G-code; and the processes — FDM physics and what really determines part quality, plus SLA and powder-bed specifics."
---

# CAD and 3D Printing: The Slicing Pipeline and the Printing Processes

> **Part 2 of 5** of the *CAD and 3D Printing* reference (plugin `cad-3d-printing`), covering §5–§6. Sibling skills: `cad-geometry-kernels-formats-and-code-cad` (§0–§4), `cad-design-tolerances-and-materials` (§7–§9), `cad-generative-automation-and-scanning` (§10–§12), `cad-reference` (§13–§18). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The geometry mathematics and process physics are stable; the code-CAD tooling and slicer landscape moved. See §16 → `cad-reference` for both, dated.

> **Scope.** Written for people who write code. **§2–§4 → `cad-geometry-kernels-formats-and-code-cad` are the software engineering
> (kernels, scripting, formats); §6–§9 → `cad-design-tolerances-and-materials` are the manufacturing physics you need for the
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
>    CAD (§5, §6).

---

## §5. The Slicing Pipeline

**⚠️ Slicing is where a geometric model becomes a manufacturing plan, and most of the
part's real properties are decided here.**

```
MESH → orient & place → repair/validate
  → SLICE into layers (plane-mesh intersection → closed 2D polygons)
    → PERIMETERS (offset inward by nozzle width, n times)
      → SOLID top/bottom regions & INFILL of the remainder
        → SUPPORT generation for overhangs
          → path planning & ordering → travel moves & retractions
            → EXTRUSION calculation (E per mm) → G-CODE
```

### 5.1 The slicing step itself
**Intersect the mesh with a horizontal plane per layer.** ⚠️ **The output must be closed
polygons; a non-manifold or leaking mesh produces open contours, and the slicer must
guess — which is exactly the "slicer repaired 588 errors" message.**
**Robustness tricks**: perturb the plane slightly to avoid exact vertex/edge coincidence,
and **use exact predicates or careful epsilon handling** — ⚠️ **the same numerical problem
as §2 → `cad-geometry-kernels-formats-and-code-cad`.**

### 5.2 The 2D operations that follow
**Polygon offsetting (Minkowski/Clipper)** for perimeters — ⚠️ **offsetting is
non-trivial: thin regions collapse, and self-intersections must be resolved.**
**Boolean operations** for infill clipping. **Even-odd or nonzero winding** for holes.
**⚠️ The Clipper library does most of this heavy lifting across the open slicers.**

### 5.3 The decisions that matter
**Infill patterns**: grid, gyroid (⚠️ **isotropic and non-crossing — good strength per
material, and popular for flexibles**), honeycomb, lightning (⚠️ **minimal, only supports
top surfaces**), cubic. **Infill density is sharply non-linear in benefit** — ⚠️ **beyond
about 40–50%, adding infill buys much less strength than adding perimeters.**

**Supports**: normal vs **tree/organic** (⚠️ **less material, easier removal, better
surface — the default choice now where supported**). **Overhang threshold** typically
45–55°. **Interface layers** determine the surface you get after removal.

**⚠️ Adhesion and warping**: brim, raft, skirt; and the physics is thermal contraction
(§6.1).

### 5.4 G-code
```
G0/G1 X Y Z E F     ⚠️ coordinated move; E is EXTRUDER AXIS POSITION, not a rate
G28                 home
G29                 bed level / mesh probe
M104/M109           set / set-and-wait hotend temp
M140/M190           set / set-and-wait bed temp
M106/M107           fan on / off
G90/G91             absolute / relative positioning
M82/M83             ⚠️ absolute / relative EXTRUSION — a separate mode from G90/G91
G92                 set position without moving  ⚠️ (E0 resets extruder origin)
```
**⚠️ Extrusion is computed, not commanded by volume**:
```
E_mm = (layer_height × extrusion_width × distance) / (π × (filament_d/2)²)
```
**Multiply by extrusion multiplier / flow.** ⚠️ **This is why filament diameter accuracy
matters — a nominal 1.75 mm filament that's actually 1.70 mm under-extrudes by ~6%.**

**⚠️ Firmware differences are real**: Marlin, Klipper (⚠️ **input shaping and pressure
advance move motion planning to a Linux host — and it changes what the slicer should
emit**), RepRapFirmware, Prusa's fork. **Flavour selection in the slicer is not cosmetic.**

**Post-processing scripts** are the underused power feature: ⚠️ **every major slicer can
run a script over the G-code before saving.** Use it for custom pauses (filament change
at layer N), Z-hop tweaks, adding M73 progress, or injecting per-object settings. **It's
just text processing.**

---

## §6. The Processes

| Process | How | Resolution | ⚠️ Notes |
|---|---|---|---|
| **FDM/FFF** | Extrude molten filament | 0.1–0.3 mm layers | ⚠️ **Cheapest, most common, ANISOTROPIC (§6.1)** |
| **SLA/DLP/MSLA** | Photopolymerize resin | ⚠️ **25–100 µm** | Excellent detail; ⚠️ **brittle, UV-degrading, messy post-processing** |
| **SLS** | Laser-sinter nylon powder | ~100 µm | ⚠️ **No supports needed — the powder bed supports. Great for complex geometry** |
| **MJF** | Fusing agent + IR, powder | ~80 µm | Similar to SLS, faster, good properties |
| **Binder jetting** | Binder into powder, then sinter | — | ⚠️ **Significant sintering shrinkage to compensate** |
| **SLM/DMLS** | Laser-melt metal powder | 20–50 µm | ⚠️ **Residual stress; needs supports AND heat treatment AND removal from plate** |
| **Material jetting** | Inkjet photopolymer | ⚠️ **16 µm** | Multi-material, full colour; expensive |
| **DED** | Blown powder/wire + laser | coarse | Repair, large parts |

### 6.1 ⚠️ FDM physics — what actually determines part quality
**Layer adhesion is thermal welding of polymer chains across the interface**, and it is
**weaker than the bulk material.**
> **⚠️ GOTCHA — FDM parts are anisotropic, typically 20–50% weaker in Z (across layers)
> than in XY.** **This is the single most important design fact in FDM**: ⚠️ **part
> orientation is a structural decision, not a print-time convenience.** **Orient so that
> load paths run along layers, never across them.**

**Warping** is differential thermal contraction: the first layers cool and shrink while
upper material is still hot. ⚠️ **Worse with high-shrinkage materials (ABS, nylon), larger
footprints, and sharp corners** — hence enclosures, heated beds, and brims.
**Elephant's foot** — the first layer squashed by nozzle pressure and bed heat;
compensate in the slicer.
**Stringing** — molten material oozing on travel; retraction and temperature are the
levers.
**Bridging** — unsupported horizontal spans work because the extrudate is under tension and
cooled fast; ⚠️ **reliable to roughly 50 mm with good part cooling.**

### 6.2 SLA and powder specifics
**SLA**: ⚠️ **supports are needed even for overhangs the part could self-support, because
peel forces during separation are the dominant load.** **Hollow + drain holes** to save
resin and avoid suction cups. ⚠️ **Post-cure is required for final properties, and
over-curing makes parts brittle.**
**SLS/MJF**: ⚠️ **design for powder escape — fully enclosed voids trap unfused powder
permanently.** **Nesting in 3D is what makes it economical.**
**Metal**: ⚠️ **residual stress can distort or crack parts on the plate; supports are
structural (holding shape against stress) not just gravitational, and stress relief before
removal is standard.**
