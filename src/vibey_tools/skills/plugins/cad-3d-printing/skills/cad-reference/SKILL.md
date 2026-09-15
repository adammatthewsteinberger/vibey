---
name: cad-reference
description: "Use when checking a CAD or printing anti-pattern, looking up a tolerance, temperature or dimensional value, asking what actually moved (OpenSCAD's Manifold backend, the slicer landscape, code-CAD and the LLM angle, verified August 2026), finding the books and tools, or needing a picker and a pre-print checklist. Companion to the other cad-3d-printing skills."
---

# CAD and 3D Printing: Anti-Patterns, Numbers, What Moved, and Tools

> **Part 5 of 5** of the *CAD and 3D Printing* reference (plugin `cad-3d-printing`), covering §13–§18. Sibling skills: `cad-geometry-kernels-formats-and-code-cad` (§0–§4), `cad-slicing-pipeline-and-processes` (§5–§6), `cad-design-tolerances-and-materials` (§7–§9), `cad-generative-automation-and-scanning` (§10–§12). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The geometry mathematics and process physics are stable; the code-CAD tooling and slicer landscape moved. See §16 below for both, dated.

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

## §13. Anti-Patterns

| Anti-pattern | Why |
|---|---|
| Choosing the tool before the representation | ⚠️ **Most CAD frustration is a representation mismatch** (§1 → `cad-geometry-kernels-formats-and-code-cad`) |
| Expecting arbitrary-edge fillets in OpenSCAD | ⚠️ **CSG has no edges to select** (§4.2 → `cad-geometry-kernels-formats-and-code-cad`) |
| Coplanar faces in a boolean | ⚠️ **Numerically ambiguous. Overlap by an epsilon** (§2 → `cad-geometry-kernels-formats-and-code-cad`) |
| STL as an interchange format between CAD tools | ⚠️ **Lossy and unit-less. Use STEP** (§3 → `cad-geometry-kernels-formats-and-code-cad`) |
| STL to the printer when 3MF is available | 3MF carries units, colour, settings (§3 → `cad-geometry-kernels-formats-and-code-cad`) |
| Assuming an STL's units | ⚠️ **There are none. 25.4× errors are real** (§3 → `cad-geometry-kernels-formats-and-code-cad`) |
| Round-tripping CAD → STL → CAD | You get an uneditable mesh back (§3 → `cad-geometry-kernels-formats-and-code-cad`) |
| High `$fn` / fine tessellation while iterating | ⚠️ **2 seconds becomes 2 minutes** (§4.3 → `cad-geometry-kernels-formats-and-code-cad`) |
| Magic numbers instead of named parameters | Defeats the point of code-CAD (§4.3 → `cad-geometry-kernels-formats-and-code-cad`) |
| Version-controlling the STL instead of the source | ⚠️ **Same** (§4.3 → `cad-geometry-kernels-formats-and-code-cad`) |
| Trusting automatic mesh repair blindly | ⚠️ **Heuristic; silently changes geometry** (§4.5 → `cad-geometry-kernels-formats-and-code-cad`) |
| Laplacian smoothing on a dimensioned part | ⚠️ **It shrinks the model** (§4.5 → `cad-geometry-kernels-formats-and-code-cad`) |
| Ignoring print orientation for structural parts | ⚠️ **Z is 20–50% weaker. Orientation is a design decision** (§6.1 → `cad-slicing-pipeline-and-processes`) |
| Horizontal circular holes on FDM | ⚠️ **Sagging top. Use a teardrop** (§7 → `cad-design-tolerances-and-materials`) |
| Wall thickness not a multiple of extrusion width | Gaps or over-extrusion (§7 → `cad-design-tolerances-and-materials`) |
| Fully enclosed voids in SLS or SLA | ⚠️ **Trapped powder / resin, permanently** (§6.2 → `cad-slicing-pipeline-and-processes`, §7 → `cad-design-tolerances-and-materials`) |
| Modelling holes at nominal size for FDM | ⚠️ **They print undersize** (§8 → `cad-design-tolerances-and-materials`) |
| Trusting a clearance table over a test print | Calibrate your machine and material (§8 → `cad-design-tolerances-and-materials`) |
| Printed threads for load-bearing joints | ⚠️ **Use heat-set inserts** (§8 → `cad-design-tolerances-and-materials`) |
| Printing hygroscopic filament without drying | ⚠️ **The most common invisible cause of bad prints** (§9 → `cad-design-tolerances-and-materials`) |
| Infill density as the strength lever | ⚠️ **Perimeters do more above ~40%** (§5.3 → `cad-slicing-pipeline-and-processes`) |
| Topology optimization on one load case | Fragile in every other direction (§10 → `cad-generative-automation-and-scanning`) |
| Manual slicing in a repeatable workflow | ⚠️ **Every slicer has a CLI** (§11 → `cad-generative-automation-and-scanning`) |
| Treating a scan as a model | ⚠️ **A mesh is not CAD** (§12 → `cad-generative-automation-and-scanning`) |

---

## §14. Numbers

```
FDM
Nozzle 0.4 mm typical (0.2–0.8) · Layer 0.1–0.3 mm (⚠️ ~25–75% of nozzle Ø)
Extrusion width ≈ nozzle Ø to 1.2× · Filament 1.75 mm (or 2.85)
⚠️ Overhang limit ~45–55° · Bridging to ~50 mm with good cooling
⚠️ Z-strength 50–80% of XY · Accuracy ±0.1–0.5 mm
First layer squish, elephant's foot compensation ~0.1–0.5 mm

CLEARANCES (FDM, per side)
Press fit 0 to −0.1 · Tight sliding 0.15–0.2 · Free 0.3–0.4 · Print-in-place 0.3–0.5
⚠️ Holes print undersize: oversize by 0.1–0.4 mm

RESOLUTION BY PROCESS
Material jetting 16 µm · SLA/MSLA 25–100 µm · SLM 20–50 µm
MJF ~80 µm · SLS ~100 µm · FDM 100–300 µm

TEMPERATURES (nozzle / bed)
PLA 200/60 · PETG 240/80 · ABS 250/100 · Nylon 260/90 · PC 280/110 · TPU 225/50
⚠️ PLA softens ~60 °C — glass transition, not melting

EXTRUSION MATH
E = (layer_h × width × dist) / (π (filament_d/2)²)
⚠️ 1.75 mm nominal at 1.70 mm actual = ~6% under-extrusion

MESH
⚠️ Euler: V − E + F = 2 − 2g  for a closed surface of genus g
Manifold: every edge in exactly 2 faces
```

---

## §15. Books and Tools

| Source | Why |
|---|---|
| **Piegl & Tiller, *The NURBS Book*** | ⚠️ **The reference for §1 → `cad-geometry-kernels-formats-and-code-cad`'s surface math** |
| **Farin, *Curves and Surfaces for CAGD*** | The readable companion |
| **Botsch et al., *Polygon Mesh Processing*** | ⚠️ **§4.5 → `cad-geometry-kernels-formats-and-code-cad`, definitively** |
| **de Berg et al., *Computational Geometry*** | Algorithms and the robustness problem |
| **Shirley, *Ray Tracing in One Weekend*** | ⚠️ **The best free introduction to thinking in 3D geometry code** |
| **Gibson, Rosen & Stucker, *Additive Manufacturing Technologies*** | ⚠️ **The academic AM reference** |
| **Redwood et al., *The 3D Printing Handbook*** | ⚠️ **The practical DfAM book — get this one first** |
| **Bendsøe & Sigmund, *Topology Optimization*** | §10 → `cad-generative-automation-and-scanning` |
| **ASME Y14.5 (GD&T)** | Tolerancing formally (§8 → `cad-design-tolerances-and-materials`) |

**Tools**: **OpenSCAD**, **CadQuery**, **build123d**, **FreeCAD**, **SolveSpace**
(⚠️ **an underrated constraint-based parametric modeller**), **Blender**, **Rhino +
Grasshopper**, **nTop** (implicits), **Onshape** (⚠️ **best commercial API**),
**Fusion 360**. **Mesh**: trimesh, pymeshlab, MeshLab, Open3D, libigl, Manifold, OpenVDB.
**Slicers**: §16.2. **Print management**: OctoPrint, Klipper/Moonraker, Mainsail, Fluidd.
**Communities**: Printables, Thingiverse, MakerWorld, ⚠️ **and the slicer projects'
GitHub issues, which are the best documentation of real failure modes.**

---

## §16. What Actually Moved — verified August 2026

### 16.1 ⚠️ OpenSCAD's Manifold backend
**The most significant change to open code-CAD in years, and one worth getting right
because outdated descriptions are everywhere.**

- **OpenSCAD historically used CGAL**, which is exact and ⚠️ **notoriously slow.**
- **Manifold** replaced it as an alternative backend. **Reported speedups:
  5–30× over CGAL's fast-csg**, which was itself **30–150× over baseline CGAL Nef
  routines** — ⚠️ **with a 1,000× improvement reported on at least one model.**
- **⚠️ Since 2024-09-28 the Manifold backend is no longer experimental** — selectable in
  Preferences → Advanced → 3D Rendering → Backend, or `openscad --backend=manifold` on the
  command line. ⚠️ **The old feature-flag method was removed, which broke some
  command-line scripts.**
- **⚠️ At that announcement, CGAL was still the default backend**, with Manifold opt-in.
- **⚠️ That changed on 2025-08-17**, when OpenSCAD maintainer Marius Kintel announced on the
  project mailing list that **Manifold is now the default backend in development
  snapshots**, calling it "battle tested"; CGAL remains selectable via preferences or
  `--backend=cgal`. ⚠️ **The most recent tagged "stable" release is still 2021.01, which
  predates Manifold support entirely** — anyone using Manifold at all is already on a
  development snapshot, where the default has now flipped.

> **⚠️ GOTCHA — two things to be careful about here.**
> **First, many current sources — including reference documentation and comparison
> articles — still describe OpenSCAD's kernel as simply "CGAL."** That was accurate and
> is now at best incomplete. ⚠️ **Check which backend you're actually running before
> attributing behaviour to a kernel.**
> **Second, the backends are not equivalent in output.** A February 2026 bug report shows
> **a model where Manifold produced STL with open edges that PrusaSlicer auto-repaired,
> while CGAL made most of the model vanish entirely** — and ⚠️ **the reporter's fix was
> adding a small overlap, i.e. the §2 → `cad-geometry-kernels-formats-and-code-cad` epsilon problem.** **If a model behaves oddly, try
> the other backend as a diagnostic.**

### 16.2 The slicer landscape
**⚠️ Almost everything descends from Slic3r.** **OrcaSlicer** is a fork of **Bambu
Studio**, which forked **PrusaSlicer**, which began as **Slic3r PE**. **Cura** is the
separate lineage.

**As of 2026**: **OrcaSlicer** is widely described as the strongest for advanced FDM
tuning — ⚠️ **best-in-class calibration workflows (temperature, flow, pressure advance,
retraction, max volumetric speed), the broadest third-party printer support, native
presets for Klipper input-shaping and pressure-advance, no cloud requirement, and leading
tree/organic support generation.** **Bambu Studio** is strongest on Bambu hardware,
**PrusaSlicer** on Prusa hardware and mature multi-material with a 1–3 month-slower
release cadence, and **Cura** remains the broad beginner-friendly standby with the plugin
ecosystem.

**⚠️ Read that as ecosystem fit, not a ranking**: the honest summary from the comparisons
is that **the right slicer depends almost entirely on what you're printing on**, and
**Klipper users in particular have a clear answer.**

### 16.3 Code-CAD and the LLM angle
**CadQuery and build123d** wrap **OCCT**, giving exact B-rep, true fillets and chamfers,
and **STEP import/export that OpenSCAD cannot do.** **build123d** replaces CadQuery's
fluent method-chaining with **context managers, so ordinary Python loops, references and
filtering work naturally.**

⚠️ **One genuinely interesting current finding, reported by more than one party building
LLM-to-CAD tooling**: **language models write OpenSCAD substantially more reliably than
CadQuery or build123d** — one benchmark reports **3–4× fewer code errors** — attributed to
training-data volume and to OCCT's complexity leaking through the Python wrapper.
> **⚠️ GOTCHA — take that with real caution.** ⚠️ **Both sources reporting it are
> companies whose product is built on OpenSCAD**, so they are not disinterested. **The
> underlying reasoning is plausible** (OpenSCAD's language is small and its corpus is
> large), **but this is a vendor-adjacent benchmark, not an independent one.** ⚠️ **And it
> says nothing about which kernel is better for a human** — the same sources concede that
> OCCT is the more capable kernel.

---

## §17. Quick Reference

### 17.1 Picker
| Need | Use |
|---|---|
| Parametric part, simple geometry, scriptable | **OpenSCAD** (§4.1 → `cad-geometry-kernels-formats-and-code-cad`) |
| Same, but needs fillets/chamfers and STEP | ⚠️ **CadQuery or build123d** (§4.2 → `cad-geometry-kernels-formats-and-code-cad`) |
| Full CAD app automation | **FreeCAD Python**, or **Onshape REST** (§4.4 → `cad-geometry-kernels-formats-and-code-cad`) |
| Constraint-based parametric, lightweight GUI | **SolveSpace** (§15) |
| Organic/artistic modelling | Blender (⚠️ not engineering CAD) (§4.1 → `cad-geometry-kernels-formats-and-code-cad`) |
| Lattices, implicit geometry, millions of features | ⚠️ **Implicit/SDF representation** (§1 → `cad-geometry-kernels-formats-and-code-cad`, §10 → `cad-generative-automation-and-scanning`) |
| Reliable booleans on messy meshes | **Manifold** (§2 → `cad-geometry-kernels-formats-and-code-cad`) |
| Repair a broken mesh | trimesh / pymeshlab / Netfabb; ⚠️ **voxel remesh as last resort** (§4.5 → `cad-geometry-kernels-formats-and-code-cad`) |
| CAD → CAD interchange | ⚠️ **STEP** (§3 → `cad-geometry-kernels-formats-and-code-cad`) |
| CAD → printer | ⚠️ **3MF** (§3 → `cad-geometry-kernels-formats-and-code-cad`) |
| Batch/CI generation | ⚠️ **Headless CLI — all of them have one** (§11 → `cad-generative-automation-and-scanning`) |
| Klipper printer | **OrcaSlicer** (§16.2) |
| Strong part, FDM | ⚠️ **Orient for load along layers; add perimeters, not infill** (§5.3 → `cad-slicing-pipeline-and-processes`, §6.1 → `cad-slicing-pipeline-and-processes`) |
| Load-bearing threaded joint, FDM | **Heat-set insert** (§8 → `cad-design-tolerances-and-materials`) |
| Complex geometry, no supports | ⚠️ **SLS/MJF — the powder bed supports it** (§6 → `cad-slicing-pipeline-and-processes`) |
| Fine detail | SLA/MSLA (§6 → `cad-slicing-pipeline-and-processes`) |

### 17.2 Pre-print checklist
- [ ] Mesh manifold, watertight, correct normals? (§4.5 → `cad-geometry-kernels-formats-and-code-cad`)
- [ ] Units correct — and is it 3MF rather than STL? (§3 → `cad-geometry-kernels-formats-and-code-cad`)
- [ ] Oriented for the load path, not just for print time? (§6.1 → `cad-slicing-pipeline-and-processes`)
- [ ] Overhangs under ~45°, or supported, or redesigned as chamfers? (§7 → `cad-design-tolerances-and-materials`)
- [ ] Horizontal holes teardropped? (§7 → `cad-design-tolerances-and-materials`)
- [ ] Walls a whole multiple of extrusion width? (§7 → `cad-design-tolerances-and-materials`)
- [ ] Clearances calibrated for *this* machine and material? (§8 → `cad-design-tolerances-and-materials`)
- [ ] Escape holes for powder/resin if applicable? (§6.2 → `cad-slicing-pipeline-and-processes`)
- [ ] Filament dried if hygroscopic? (§9 → `cad-design-tolerances-and-materials`)
- [ ] Perimeters increased before infill for strength? (§5.3 → `cad-slicing-pipeline-and-processes`)

---

## §18. Method

**§1–§12 → `cad-geometry-kernels-formats-and-code-cad`, `cad-slicing-pipeline-and-processes`, `cad-design-tolerances-and-materials`, `cad-generative-automation-and-scanning` rest on stable material** — NURBS and B-rep mathematics, computational geometry,
mesh processing, and additive manufacturing process physics — sourced from the references
in §15, chiefly **Piegl & Tiller**, **Botsch et al.**, and **Gibson, Rosen & Stucker**,
plus the file-format specifications. ⚠️ **None of that needed web verification; the
geometry math is decades old and the process physics is thermodynamics.**

**Two searches were run in August 2026**, confined to the tooling: **the code-CAD
ecosystem** and **the OpenSCAD kernel and slicer landscape.**

**⚠️ The second search materially corrected the first.** Several sources returned by the
code-CAD search — **including CadQuery's own documentation and multiple 2026
comparison articles** — describe OpenSCAD's kernel as CGAL and contrast it unfavourably
with OCCT on that basis. **That framing predates the Manifold work.** I followed up
specifically and found the **OpenSCAD mailing list announcement (2024-09-28) that Manifold
is no longer experimental**, a **later mailing list post (2025-08-17) from the same
maintainer confirming Manifold became the default backend in development snapshots**, plus
**the Manifold project's own performance discussion** for the speedup figures. ⚠️ **§16.1
reflects that; the widely-repeated "OpenSCAD uses CGAL" line is now incomplete.**

**Confidence.** **High** in §1–§12 → `cad-geometry-kernels-formats-and-code-cad`, `cad-slicing-pipeline-and-processes`, `cad-design-tolerances-and-materials`, `cad-generative-automation-and-scanning` — established mathematics and process physics, with
numbers stated as representative ranges that vary by machine and material. **High** in
§16.1's Manifold facts, which come from the project and the OpenSCAD maintainers directly,
including that **CGAL remained the default backend at the time of the 2024-09-28
announcement, and that Manifold became the default in development snapshots as of
2025-08-17** — ⚠️ **verify which snapshot and backend you are actually running rather than
assuming, since the tagged "stable" release (2021.01) predates either backend option.**

⚠️ **Two explicit hedges.** **§16.2's slicer assessment is drawn from comparison articles,
which are opinion-shaped and frequently affiliate-monetized**; I have framed it as
ecosystem fit rather than a ranking, and the technical lineage (Slic3r → PrusaSlicer →
Bambu Studio → OrcaSlicer) is the part that is unambiguous. And ⚠️ **§16.3's LLM benchmark
is flagged in place as vendor-adjacent** — **both parties reporting it build products on
OpenSCAD.** The mechanism they propose is plausible and the finding may well be right, but
**it is not an independent evaluation and I have not treated it as one.**

**§14's tolerance and clearance figures are starting points, not specifications** —
⚠️ **the §8 → `cad-design-tolerances-and-materials` advice to run a calibration print is the actual recommendation, and it
supersedes any table including mine.**
