---
name: gfx-transforms-rasterization-and-rendering
description: "Use when working on how an image gets made: transforms and projective geometry including homogeneous coordinates, the camera matrix and the projection pipeline; rasterization and its coverage, depth and interpolation rules; shading and physically based rendering with BRDFs, energy conservation and material parameters; and ray tracing with the rendering equation, Monte Carlo integration and importance sampling. Includes the router for the whole graphics-and-vision reference."
---

# Graphics and Vision: Transforms, Rasterization, Shading, and Ray Tracing

> **Part 1 of 5** of the *Graphics and Vision* reference (plugin `graphics-and-vision`), covering §0–§4. Sibling skills: `gfx-gpu-real-time-techniques-and-colour` (§5–§7), `gfx-image-formation-classical-vision-and-geometry` (§8–§10), `gfx-deep-learning-neural-rendering-and-performance` (§11–§13), `gfx-reference` (§14–§19). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The mathematics is permanent — projective geometry, the rendering equation, epipolar geometry. Neural rendering and vision foundation models moved. See §16 → `gfx-reference` for those.

> **Why one document.** ⚠️ **They are inverse problems over the same geometry.** Graphics
> goes scene → image; vision goes image → scene. **They share the camera model, projective
> geometry, and increasingly the representations** — §12 → `gfx-deep-learning-neural-rendering-and-performance` is where they now meet directly.
>
> **⚠️ GOTCHA** boxes mark where the math is subtle or the standard implementation is
> silently wrong.
>
> **The three ideas that unify the whole document:**
> 1. **⚠️ Homogeneous coordinates make projection linear.** Adding a fourth component turns
>    perspective — a nonlinear operation — into a matrix multiply, which is why the entire
>    pipeline is matrices (§1).
> 2. **⚠️ Rendering is an integral, and everything real-time is a sampling strategy for
>    it.** The rendering equation is the ground truth; rasterization, path tracing, and
>    every approximation in §6 → `gfx-gpu-real-time-techniques-and-colour` are ways of estimating it under a time budget (§4).
> 3. **⚠️ Vision is underdetermined and that is not a solvable bug.** A single image is a
>    projection; depth is destroyed. Every vision method is adding a constraint — multiple
>    views, motion, a learned prior — to recover what the projection threw away (§8 → `gfx-image-formation-classical-vision-and-geometry`, §10 → `gfx-image-formation-classical-vision-and-geometry`).

---

## §0. Routing

| You want... | Go to |
|---|---|
| **Transforms and projective geometry** | **§1** |
| Rasterization pipeline | §2 |
| **Shading, PBR, the rendering equation** | **§3, §4** |
| Ray and path tracing | §4 |
| GPU architecture and APIs | §5 → `gfx-gpu-real-time-techniques-and-colour` |
| **Real-time techniques** | **§6 → `gfx-gpu-real-time-techniques-and-colour`** |
| Colour and tone mapping | §7 → `gfx-gpu-real-time-techniques-and-colour` |
| **Camera model and calibration** | **§8 → `gfx-image-formation-classical-vision-and-geometry`** |
| Classical CV | §9 → `gfx-image-formation-classical-vision-and-geometry` |
| **Multiple view geometry, SfM, SLAM** | **§10 → `gfx-image-formation-classical-vision-and-geometry`** |
| Deep learning for vision | §11 → `gfx-deep-learning-neural-rendering-and-performance` |
| **Neural rendering (NeRF, 3DGS)** | **§12 → `gfx-deep-learning-neural-rendering-and-performance`** |
| Performance | §13 → `gfx-deep-learning-neural-rendering-and-performance` |
| Anti-patterns | §14 → `gfx-reference` |
| Numbers | §15 → `gfx-reference` |
| **What actually moved** | **§16 → `gfx-reference`** |
| Books | §17 → `gfx-reference` |
| Quick reference | §18 → `gfx-reference` |

---

## §1. Transforms and Projective Geometry

**Homogeneous coordinates**: a 3D point becomes `(x, y, z, w)`, with the Euclidean point
recovered as `(x/w, y/w, z/w)`. ⚠️ **`w = 0` denotes a point at infinity — a direction.**
**This is why you must transform normals and positions differently**: positions are
`(x,y,z,1)`, directions `(x,y,z,0)`, so translation applies to one and not the other.

**The pipeline of spaces:**
```
Model → [model matrix] → World → [view matrix] → View/Camera
      → [projection] → Clip → [÷w, perspective divide] → NDC
      → [viewport] → Screen
```
**⚠️ The perspective divide is where the nonlinearity enters** — everything before it is
linear, which is the entire point of homogeneous coordinates.

**⚠️ Normal transformation is the classic bug**: normals transform by the **inverse
transpose** of the model matrix, not the matrix itself. **Under non-uniform scaling, using
the model matrix skews normals off the surface and your lighting is wrong** in a way that
looks like a shading bug rather than a math bug.

**Rotations**: matrices (composable, 9 numbers, drift under repeated multiplication),
**Euler angles** (⚠️ **intuitive and gimbal-locked — avoid for interpolation or
accumulation**), **quaternions** (⚠️ **4 numbers, no gimbal lock, and `slerp` interpolates
correctly — the right internal representation**; note `q` and `−q` are the same rotation,
which trips comparison and naive interpolation), **axis-angle**, and **Lie algebra
(SO(3)/SE(3))** — ⚠️ **the right formulation for optimization, because it gives you a
minimal, unconstrained local parameterization**, which is why SLAM and bundle adjustment
use it (§10 → `gfx-image-formation-classical-vision-and-geometry`).

**⚠️ Conventions that cause days of confusion**: row-vector vs column-vector, row-major vs
column-major storage, left- vs right-handed coordinates, and **NDC depth range —
OpenGL's `[-1,1]` vs D3D/Vulkan/Metal's `[0,1]`.** **Write yours down at the top of the
file.**

---

## §2. Rasterization

```
Vertex data → vertex shader → [optional tessellation, geometry]
  → clipping → perspective divide → viewport transform
    → triangle setup → RASTERIZE → early-Z → fragment shader
      → depth/stencil test → blend → framebuffer
```

**Rasterization** determines coverage: for each pixel, is its centre inside the triangle?
**Edge functions** (Pineda) give this as three sign tests, and ⚠️ **they're incrementally
evaluable, which is why hardware does it this way.**

**⚠️ Perspective-correct interpolation is essential and non-obvious**: interpolating an
attribute linearly in screen space is wrong under perspective. **Interpolate `attr/w` and
`1/w` linearly, then divide.** ⚠️ **Getting this wrong produces the classic warped-texture
artifact of early 3D hardware.**

**Depth**: the Z-buffer. ⚠️ **Depth precision is non-linearly distributed** — most
precision sits near the near plane, so **z-fighting at distance is caused by a near plane
that is too close, far more often than by a far plane that is too far.** **Reversed-Z with
a floating-point depth buffer** largely fixes this and is the modern default.

**Culling**: backface (winding order), frustum, occlusion, and **early-Z** — ⚠️ **which is
disabled if the fragment shader writes depth or uses `discard`, and that is a common
silent performance cliff.**

**Texturing**: UV mapping, filtering (nearest, bilinear, trilinear, **anisotropic**),
**mipmaps** (⚠️ **not an optimization — they're antialiasing in the texture domain, and
without them minified textures shimmer**), wrap modes, and compressed formats (BC/DXT,
ASTC, ETC).

---

## §3. Shading and PBR

**The BRDF** `f_r(ω_i, ω_o)` describes how light scatters at a surface. ⚠️ **A physically
valid BRDF must obey reciprocity (`f_r(ω_i,ω_o) = f_r(ω_o,ω_i)`) and energy conservation
(it cannot reflect more than it receives).**

**Legacy models**: Lambert diffuse (`n·l`), Phong and Blinn-Phong specular —
⚠️ **not energy-conserving and not reciprocal, but cheap and still everywhere.**

**Modern microfacet PBR** — the standard, built as `D · F · G / (4 (n·l)(n·v))`:
- **D — normal distribution function** (⚠️ **GGX/Trowbridge-Reitz won because its long
  tail matches measured materials far better than Beckmann**).
- **F — Fresnel** (⚠️ **Schlick's approximation; reflectance rises to 1 at grazing angles
  for every material, which is the single most important visual cue PBR added**).
- **G — geometry/shadowing-masking term** (Smith).

**⚠️ The parameterization that won**: **base colour, metallic, roughness**, plus normal,
AO, and emissive. **Metallic is a near-binary switch** — metals have no diffuse and tinted
specular; dielectrics have diffuse and ~4% white specular. ⚠️ **Intermediate metallic
values are physically meaningless and exist only for texture blending at material
boundaries.**

**IBL (image-based lighting)**: prefiltered environment maps + a split-sum approximation
BRDF LUT. **Spherical harmonics** for low-frequency irradiance — ⚠️ **9 coefficients
capture diffuse environment lighting almost exactly, which is why SH is everywhere.**

---

## §4. Ray Tracing and the Rendering Equation

**Kajiya, 1986** — ⚠️ **the ground truth for all of rendering:**
```
L_o(x, ω_o) = L_e(x, ω_o) + ∫_Ω f_r(x, ω_i, ω_o) · L_i(x, ω_i) · (n·ω_i) dω_i
```
**Outgoing radiance = emitted + integral over the hemisphere of incoming radiance times
BRDF times cosine.** ⚠️ **It's recursive — `L_i` is some other surface's `L_o` — which is
why global illumination is expensive and why every real-time technique is an
approximation of this integral.**

**Monte Carlo estimation**: sample directions, weight by `1/pdf`. **Variance falls as
`1/√N`** — ⚠️ **so halving noise costs 4× the samples, which is the fundamental economics
of path tracing.**
**Variance reduction**: **importance sampling** (⚠️ **sample proportional to the
integrand — the single biggest win**), multiple importance sampling (**MIS** — Veach),
next-event estimation, Russian roulette for unbiased termination, and stratification /
low-discrepancy sequences.

**Acceleration structures**: **BVH** (⚠️ **the standard; built with SAH — the surface area
heuristic**), kd-tree, grids. **Ray-triangle intersection**: Möller-Trumbore.

**⚠️ Denoising is now part of the algorithm, not a post-process** — real-time ray tracing
traces roughly one sample per pixel and relies on spatiotemporal denoising (SVGF, and ML
denoisers like OptiX/OIDN) to be viable at all.

**Hardware ray tracing** (RTX/DXR/Vulkan RT) accelerates BVH traversal and intersection.
⚠️ **It does not make path tracing free — it makes ray *queries* fast, and the sampling
and denoising budget still dominates.**
