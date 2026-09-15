---
name: gfx-gpu-real-time-techniques-and-colour
description: "Use when making rendering run fast and look right: GPU architecture and the modern APIs and their execution model, real-time techniques including shadows, ambient occlusion, deferred and forward rendering, temporal methods and upscaling, and colour and tone mapping — colour spaces, transfer functions, HDR and the display pipeline."
---

# Graphics and Vision: GPU Architecture and APIs, Real-Time Techniques, and Colour

> **Part 2 of 5** of the *Graphics and Vision* reference (plugin `graphics-and-vision`), covering §5–§7. Sibling skills: `gfx-transforms-rasterization-and-rendering` (§0–§4), `gfx-image-formation-classical-vision-and-geometry` (§8–§10), `gfx-deep-learning-neural-rendering-and-performance` (§11–§13), `gfx-reference` (§14–§19). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
>    pipeline is matrices (§1 → `gfx-transforms-rasterization-and-rendering`).
> 2. **⚠️ Rendering is an integral, and everything real-time is a sampling strategy for
>    it.** The rendering equation is the ground truth; rasterization, path tracing, and
>    every approximation in §6 are ways of estimating it under a time budget (§4 → `gfx-transforms-rasterization-and-rendering`).
> 3. **⚠️ Vision is underdetermined and that is not a solvable bug.** A single image is a
>    projection; depth is destroyed. Every vision method is adding a constraint — multiple
>    views, motion, a learned prior — to recover what the projection threw away (§8 → `gfx-image-formation-classical-vision-and-geometry`, §10 → `gfx-image-formation-classical-vision-and-geometry`).

---

## §5. GPU Architecture and APIs

**The execution model that explains most performance behaviour**: **SIMT** — threads run in
**warps (32, NVIDIA) or wavefronts (32/64, AMD)** in lockstep.
> **⚠️ GOTCHA — divergence is the cost you can't see in the source.** If threads in a warp
> take different branches, **both paths execute with the inactive lanes masked off.** A
> branch that splits a warp costs the sum of both sides. ⚠️ **This is why "avoid branches
> in shaders" is advice, and why the real rule is "avoid branches that diverge *within a
> warp*"** — a branch on a uniform value is free.

**Memory hierarchy**: registers → shared/LDS → L1 → L2 → VRAM. ⚠️ **Coalesced access —
adjacent threads reading adjacent addresses — is the difference between full bandwidth and
a fraction of it.** **Occupancy** (warps in flight) hides latency, and ⚠️ **register
pressure limits occupancy, so a shader that uses too many registers runs slower even if it
does less work.**

**APIs**: **Vulkan / D3D12 / Metal** — explicit, low-overhead, you manage synchronization
and memory. **OpenGL / D3D11** — legacy, driver-managed. **WebGPU** (⚠️ **the modern
browser target, and a genuinely reasonable API to learn first — it's Vulkan's model with
the sharp edges removed**). **CUDA / OpenCL / SYCL** for compute.
**Shading languages**: GLSL, HLSL, MSL, **WGSL**, **Slang** (⚠️ **increasingly the
cross-compilation target of choice**).

**⚠️ The explicit-API burden that surprises people**: pipeline state objects, descriptor
sets, command buffers, and **barriers and layout transitions** — ⚠️ **incorrect barriers
produce races that manifest as flickering or corruption on one vendor's driver and not
another's.** **Use the validation layers; they exist for exactly this.**

---

## §6. Real-Time Techniques

**Shadows**: **shadow mapping** — render depth from the light, compare. ⚠️ **Shadow acne
(self-shadowing from depth precision) and peter-panning (from over-biasing) are the two
failure modes, and normal-offset bias handles both better than constant bias.**
**Cascaded shadow maps** for directional lights, **PCF/PCSS** for soft edges,
**variance/moment** shadow maps.

**Antialiasing**: **MSAA** (⚠️ **supersamples coverage and depth but shades once — cheap
and effective for geometric edges, useless for shader aliasing**), **FXAA/SMAA**
(post-process), **TAA** — ⚠️ **jitter the projection per frame and accumulate with
reprojection. It's the modern default and it brings ghosting, blur and disocclusion
artifacts that require history rejection heuristics to manage.**
**Upscaling**: DLSS, FSR, XeSS, TSR — ⚠️ **temporal upscalers are TAA generalized, and
they are now the assumed rendering path rather than an optional extra.**

**Deferred vs forward**: **deferred** decouples geometry from lighting via a G-buffer —
⚠️ **many lights become cheap, but transparency and MSAA become hard.** **Forward+ /
clustered** — light culling into tiles or clusters, keeping forward's flexibility.
**Visibility buffer** for very high geometry density.

**Global illumination, approximated**: lightmaps (static, still the highest quality per
frame), irradiance probes, **SSAO/GTAO**, **SSR** (⚠️ **screen-space reflections cannot
reflect what's off-screen or behind geometry — the artifact is inherent, not a bug**),
voxel GI, and **hardware-RT GI**.

**⚠️ The through-line for all of §6**: every technique here is a way of estimating §4 → `gfx-transforms-rasterization-and-rendering`'s
integral within about 16 or 8 milliseconds. **Knowing what each one approximates tells you
what its artifacts will be.**

---

## §7. Colour and Tone Mapping

**⚠️ Linear vs sRGB is the single most common correctness bug in graphics.** sRGB encoding
is roughly a **2.2 gamma** curve. **All lighting math must happen in linear space.**
```
Texture (sRGB) → decode to linear → light and blend in LINEAR → tone map
  → encode to sRGB → display
```
⚠️ **Use hardware sRGB texture formats and framebuffers so the conversion happens for
free and in the right place. Blending in sRGB space produces visibly wrong midtones** —
the classic symptom is dark fringes around bright objects and washed-out alpha edges.

**HDR and tone mapping**: rendering happens in unbounded linear HDR; the display is
limited. **Reinhard** (simple), **ACES** (⚠️ **the film-industry standard curve, and the
default look for a reason**), **AgX** (⚠️ **newer, and better-behaved at extreme
saturation where ACES skews hues**), **Uncharted 2 / Hable**.
**Colour spaces**: sRGB/Rec.709, **Rec.2020**, DCI-P3, ACEScg (⚠️ **the right working
space for wide-gamut rendering**). **PQ (ST.2084)** and HLG for HDR display transfer.
