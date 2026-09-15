---
name: cad-geometry-kernels-formats-and-code-cad
description: "Use when modelling, converting, or scripting geometry: the representations (B-rep, meshes, implicit and voxel) and when each is right, the geometry kernels and their behaviour, file formats and precisely what each one loses in translation, and code-CAD and scripting — the landscape, the OpenSCAD versus OCCT-based trade, writing good parametric models, vendor API automation, and mesh processing and repair. Includes the router for the whole cad-3d-printing reference."
---

# CAD and 3D Printing: Geometry Representations, Kernels, File Formats, and Code-CAD

> **Part 1 of 5** of the *CAD and 3D Printing* reference (plugin `cad-3d-printing`), covering §0–§4. Sibling skills: `cad-slicing-pipeline-and-processes` (§5–§6), `cad-design-tolerances-and-materials` (§7–§9), `cad-generative-automation-and-scanning` (§10–§12), `cad-reference` (§13–§18). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The geometry mathematics and process physics are stable; the code-CAD tooling and slicer landscape moved. See §16 → `cad-reference` for both, dated.

> **Scope.** Written for people who write code. **§2–§4 are the software engineering
> (kernels, scripting, formats); §6–§9 → `cad-slicing-pipeline-and-processes`, `cad-design-tolerances-and-materials` are the manufacturing physics you need for the
> software to produce parts that work.**
>
> **⚠️ GOTCHA** boxes mark what silently produces a bad model or an unprintable part.
>
> **The three ideas that organize everything:**
> 1. **⚠️ Choose your representation before your tool.** B-rep, mesh, and implicit fields
>    are not interchangeable — each makes some operations trivial and others impossible,
>    and **most CAD frustration is a representation mismatch** (§1).
> 2. **⚠️ Every export loses something.** STL loses units, topology, colour, and all
>    parametric intent. STEP keeps the solid but not the feature tree. **Know what falls
>    off at each hop** (§3).
> 3. **⚠️ The printer does not build your model, it builds your G-code.** Slicing is a
>    lossy, opinionated transformation, and the part's real properties — strength,
>    accuracy, surface — are determined there and by the process physics, not by the
>    CAD (§5 → `cad-slicing-pipeline-and-processes`, §6 → `cad-slicing-pipeline-and-processes`).

---

## §0. Routing

| You want... | Go to |
|---|---|
| **Geometry representations** | **§1** |
| Kernels and libraries | §2 |
| **File formats** | **§3** |
| **Code-CAD and scripting** | **§4** |
| Mesh processing and repair | §4.5 |
| **The slicing pipeline** | **§5 → `cad-slicing-pipeline-and-processes`** |
| G-code | §5.4 → `cad-slicing-pipeline-and-processes` |
| **Additive processes** | **§6 → `cad-slicing-pipeline-and-processes`** |
| Design for AM | §7 → `cad-design-tolerances-and-materials` |
| Tolerances and fits | §8 → `cad-design-tolerances-and-materials` |
| Materials | §9 → `cad-design-tolerances-and-materials` |
| Generative design and lattices | §10 → `cad-generative-automation-and-scanning` |
| Automation pipelines | §11 → `cad-generative-automation-and-scanning` |
| Scanning and reverse engineering | §12 → `cad-generative-automation-and-scanning` |
| Anti-patterns | §13 → `cad-reference` |
| Numbers | §14 → `cad-reference` |
| Books and tools | §15 → `cad-reference` |
| **What actually moved** | **§16 → `cad-reference`** |
| Quick reference | §17 → `cad-reference` |

---

## §1. Geometry Representations

**⚠️ This is the decision everything else follows from.**

| Representation | Stores | Good at | ⚠️ Bad at |
|---|---|---|---|
| **B-rep** | Faces, edges, vertices; each face an exact surface | ⚠️ **Exact curves, fillets, chamfers, STEP interchange, machining** | Organic shapes; robustness of booleans |
| **CSG** | A tree of primitives + boolean ops | ⚠️ **Parametric intent, compact, always "valid"** | Fillets on arbitrary edges; export fidelity |
| **Mesh (B-rep's poor cousin)** | Triangles | Rendering, printing, scanning, simulation | ⚠️ **Approximation only; no exact curves; repair burden** |
| **Implicit / SDF** | A function `f(x,y,z)` | ⚠️ **Booleans are trivial and always valid; lattices, blends, infinite detail** | Exact dimensions, sharp features, CAD interchange |
| **Voxel** | A 3D grid | Simple booleans, topology optimization, medical | Memory (`O(n³)`), no exact surfaces |
| **Point cloud** | Points, maybe normals | Scanning output | Not a solid at all until reconstructed |

**⚠️ NURBS** underpin B-rep surfaces: a rational B-spline with control points, knot vector,
and weights. **The rational part is what lets them represent conic sections exactly** —
a circle is not a spline approximation in NURBS, it's exact. **Degree, continuity (`C⁰`
positional, `C¹` tangent, `C²` curvature — ⚠️ `G²` curvature-continuous is what makes a
surface look right in reflection), and knot multiplicity are the parameters that matter.**

> **⚠️ GOTCHA — the representation determines which operations are even possible.**
> **"Fillet this edge by 3 mm" is natural in B-rep, awkward in CSG, and meaningless on a
> mesh** (you can only approximate it). **"Union these two shapes reliably" is trivial for
> implicits, routine for meshes, and a well-known source of failure in B-rep.** ⚠️ **When
> a CAD operation fails inexplicably, the question is usually whether you're asking the
> representation to do something it isn't built for.**

---

## §2. Kernels

| Kernel | Type | Used by | ⚠️ Notes |
|---|---|---|---|
| **OCCT (Open CASCADE)** | B-rep | FreeCAD, CadQuery, build123d | ⚠️ **>1M lines of C++; the open B-rep kernel. Steep, and failures are surprising** |
| **Parasolid** | B-rep | SolidWorks, NX, Onshape | Commercial, robust |
| **ACIS** | B-rep | AutoCAD, others | Commercial |
| **CGAL** | Exact-arithmetic geometry | OpenSCAD (historically), research | ⚠️ **Exact and correct, and slow** |
| **Manifold** | Mesh booleans | OpenSCAD (modern), others | ⚠️ **Fast, guarantees manifold output** (§16.1 → `cad-reference`) |
| **libigl / Open3D / VTK / trimesh** | Mesh processing | Research, pipelines | §4.5 |
| **OpenVDB** | Sparse voxel/level set | VFX, implicit modelling | Excellent for offsets and thickening |

**⚠️ The exact-vs-floating-point trade is the core engineering problem in geometry
kernels.** Exact arithmetic (CGAL) gives provably correct results and is slow; floating
point is fast and produces **robustness failures — coincident faces, near-degenerate
triangles, and booleans that fail on geometry that "should" work.**

**⚠️ Which is why coplanar faces are the classic CSG failure**: subtracting a box whose face
sits exactly on another face is numerically ambiguous. **The universal workaround is to
overlap by a small epsilon** — `0.01 mm` or so — and it appears in every OpenSCAD codebase
for exactly this reason.

---

## §3. File Formats — and what each one loses

| Format | Carries | ⚠️ Loses |
|---|---|---|
| **STL** | Triangles only | ⚠️ **Units, colour, topology (it's a "triangle soup"), materials, ALL parametric intent** |
| **OBJ** | Triangles, UVs, materials | Solid topology |
| **3MF** | ⚠️ **Mesh + units + colour + materials + print settings, zipped XML** | Parametric history |
| **AMF** | Similar intent to 3MF | ⚠️ **Largely superseded by 3MF** |
| **STEP (AP203/214/242)** | ⚠️ **Exact B-rep solids, assemblies; AP242 adds PMI** | Feature tree, parametric history |
| **IGES** | Surfaces | ⚠️ **Legacy, often no solid topology. Avoid if STEP is available** |
| **native (.sldprt, .f3d, .FCStd)** | Everything including history | ⚠️ **Portability** |
| **glTF** | Rendering-oriented | Engineering data |

> **⚠️ GOTCHA — STL has no units.** The file contains bare numbers. **"Is this
> millimetres or inches?" is resolved by convention and hope**, which is why parts
> occasionally arrive 25.4× wrong. **3MF fixes this and should be your default mesh
> format** — it carries units, and modern slicers all read it.
>
> **⚠️ And STL is a triangle soup, not a mesh**: each triangle independently lists three
> vertices with no shared-vertex indexing. **Adjacency has to be reconstructed by
> position-matching, which is where floating-point tolerance decides whether your model
> is watertight.**

**⚠️ The pipeline rule**: **STEP between CAD tools, 3MF to the printer, STL only when
something old demands it.** Going CAD → STL → CAD is a lossy round trip that leaves you
with a mesh you cannot parametrically edit.

---

## §4. Code-CAD and Scripting

### 4.1 The landscape

| Tool | Language | Kernel | ⚠️ Character |
|---|---|---|---|
| **OpenSCAD** | Own C-like DSL | CGAL / Manifold | ⚠️ **CSG-first, declarative, no fillets on arbitrary edges. Simple and predictable** |
| **CadQuery** | Python | OCCT | ⚠️ **Fluent/method-chaining API; exports STEP** |
| **build123d** | Python | OCCT | ⚠️ **Successor-in-spirit to CadQuery; context managers instead of chaining, so full Python control flow works naturally** |
| **FreeCAD scripting** | Python | OCCT | Full application automation |
| **JSCAD** | JavaScript | own | Browser-native |
| **Grasshopper** | Visual + C#/Python | Rhino | ⚠️ **Dominant in architecture and computational design** |
| **Fusion/SolidWorks/Onshape APIs** | Python / VBA / JS | vendor | Automating a commercial tool |
| **Blender (bpy)** | Python | mesh | ⚠️ **Mesh/organic modelling, not engineering CAD** |

### 4.2 ⚠️ OpenSCAD vs the OCCT-based tools — the real trade

**⚠️ OpenSCAD's language is functional and declarative, and this surprises people**:
variables are **set at compile time, not assignment** — ⚠️ **assigning twice in the same
scope does not do what an imperative programmer expects; the last value wins for the whole
scope.** There are no loops with mutation; you use recursion and list comprehensions.

**The kernel difference is the substantive one:**
- **OpenSCAD is mesh/CSG**: ⚠️ **it cannot fillet an arbitrary edge, because it has no
  concept of an edge — only the boolean result.** You design fillets in by construction
  (`minkowski`, `hull`, or explicit geometry).
- **CadQuery/build123d are B-rep on OCCT**: ⚠️ **exact curved surfaces, and `fillet()` and
  `chamfer()` on selected edges — plus STEP export, which OpenSCAD cannot do.**

**⚠️ The honest counterweight**: OCCT's complexity leaks through the Python wrapper.
**Operations that look simple — "fillet this edge" — fail in surprising ways depending on
surrounding geometry**, and diagnosing that requires understanding the kernel. **OpenSCAD
fails more predictably.**

### 4.3 Writing good parametric models
```
⚠️ Parameterize intent, not dimensions:  wall_thickness, clearance, screw_size
   — not magic numbers scattered through the file
Named constants at the top; derive everything else
⚠️ Build a library of your own fasteners, clearances, and joints — reuse compounds
Assertions on parameters (⚠️ OpenSCAD's assert(); Python's naturally)
⚠️ $fn / tessellation: coarse while iterating, fine only for final export —
   this is usually the difference between 2 seconds and 2 minutes
Version-control the source, not the STL     ⚠️ this is the whole point of code-CAD
```
**⚠️ The genuine advantage of code-CAD over GUI CAD**: **diffable, reviewable,
version-controlled, and generatable.** A single script produces a family of parts. **You
can put it in CI.**

**⚠️ The genuine disadvantage**: **spatial reasoning in text is hard**, iteration is
slower than direct manipulation for organic shapes, and **there is no constraint solver** —
if you want "this face always tangent to that cylinder," you compute it yourself.

### 4.4 Vendor API automation
**Fusion (Python/C++), SolidWorks (VBA/C#), Onshape (REST + FeatureScript), NX, CATIA.**
⚠️ **Onshape is architecturally the outlier — a genuine REST API over a cloud document
model, which makes it the easiest commercial CAD to automate against** and the only one
where "CAD in CI" is straightforward.

**Common automation tasks**: batch parameter sweeps and export, drawing generation, BOM
extraction, design-rule checking, and **PLM integration.**

### 4.5 Mesh processing and repair
**⚠️ The properties that determine whether a mesh is printable:**
```
Manifold      ⚠️ every edge shared by exactly 2 faces
Watertight    closed, no holes — encloses a definite volume
Orientable    consistent normals (outward)
Non-self-intersecting   ⚠️ the one that repair tools handle worst
```
**⚠️ The Euler characteristic `V − E + F = 2 − 2g` is a fast sanity check** — for a closed
surface of genus `g`. A result that isn't an even integer means the mesh is broken.

**Common defects**: holes, non-manifold edges (⚠️ **3+ faces on one edge**), non-manifold
vertices (two shells touching at a point), flipped normals, duplicate/degenerate faces,
self-intersection, **and internal geometry left inside a solid** (⚠️ **invisible, and it
confuses slicers**).

**Repair**: **Meshmixer** (legacy but effective), **Netfabb**, **Blender 3D-Print
Toolbox**, **MeshLab**, **trimesh** and **pymeshlab** in Python, **Manifold** for
guaranteed-valid booleans. ⚠️ **Automatic repair is heuristic and can silently change your
geometry — inspect the result.**

**Algorithms worth knowing**: **marching cubes** (implicit → mesh), **Poisson surface
reconstruction** (points → mesh), **quadric edge-collapse decimation** (⚠️ **the standard
simplification method**), **Laplacian smoothing** (⚠️ **shrinks the model — use
taubin smoothing if that matters**), **voxel remeshing** (⚠️ **the nuclear option for
repair: voxelize and re-surface. Guarantees manifold output, destroys sharp features**).
