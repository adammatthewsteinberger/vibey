---
name: gfx-deep-learning-neural-rendering-and-performance
description: "Use when applying learned methods or profiling a pipeline: deep learning for vision including detection, segmentation, backbones and the training realities; neural rendering where graphics and vision meet, covering NeRF, 3D Gaussian splatting and their trade-offs; and performance — profiling, bottleneck analysis, and the memory and bandwidth limits that dominate in practice."
---

# Graphics and Vision: Deep Learning for Vision, Neural Rendering, and Performance

> **Part 4 of 5** of the *Graphics and Vision* reference (plugin `graphics-and-vision`), covering §11–§13. Sibling skills: `gfx-transforms-rasterization-and-rendering` (§0–§4), `gfx-gpu-real-time-techniques-and-colour` (§5–§7), `gfx-image-formation-classical-vision-and-geometry` (§8–§10), `gfx-reference` (§14–§19). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The mathematics is permanent — projective geometry, the rendering equation, epipolar geometry. Neural rendering and vision foundation models moved. See §16 → `gfx-reference` for those.

> **Why one document.** ⚠️ **They are inverse problems over the same geometry.** Graphics
> goes scene → image; vision goes image → scene. **They share the camera model, projective
> geometry, and increasingly the representations** — §12 is where they now meet directly.
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
>    every approximation in §6 → `gfx-gpu-real-time-techniques-and-colour` are ways of estimating it under a time budget (§4 → `gfx-transforms-rasterization-and-rendering`).
> 3. **⚠️ Vision is underdetermined and that is not a solvable bug.** A single image is a
>    projection; depth is destroyed. Every vision method is adding a constraint — multiple
>    views, motion, a learned prior — to recover what the projection threw away (§8 → `gfx-image-formation-classical-vision-and-geometry`, §10 → `gfx-image-formation-classical-vision-and-geometry`).

---

## §11. Deep Learning for Vision

**⚠️ The general ML framework sits in an ML reference; here's what's vision-specific.**

**CNNs**: convolution as a learned filter bank with **weight sharing and translation
equivariance** — ⚠️ **the inductive bias that made vision learnable with limited data.**
Receptive field, stride, dilation, pooling. **ResNet's skip connections** solved the
degradation problem and made depth trainable.

**Vision Transformers**: image → patches → tokens → self-attention.
⚠️ **ViTs have weaker inductive bias than CNNs, so they need more data or stronger
augmentation — but they scale better and dominate at large scale.** Hierarchical variants
(Swin) reintroduce locality.

**Tasks and the standard architectures**: classification; **detection** (two-stage
R-CNN family, one-stage YOLO/SSD/RetinaNet, ⚠️ **DETR's set-prediction formulation removed
NMS and anchor design — a genuine simplification**); **segmentation** (semantic: U-Net,
DeepLab with atrous convolution; instance: Mask R-CNN; panoptic); depth estimation; pose
estimation; tracking; and generation (§16.2 → `gfx-reference` for the current model landscape).

**⚠️ The practical failure modes that matter more than architecture choice:**
- **Data quality and label noise dominate.** ⚠️ **Almost always worth more than a better
  model.**
- **Augmentation is where much of the performance lives** — and ⚠️ **an augmentation that
  breaks the task's invariance (horizontal flip on text or on left/right-labelled data)
  silently caps your ceiling.**
- **Class imbalance** — focal loss, resampling.
- **⚠️ Domain shift**: train on daylight, deploy at night. **Test-set performance is not
  deployment performance**, and the gap is where vision systems fail in the field.
- **⚠️ Shortcut learning** — the model keys on the watermark, the hospital's scanner, or
  the ruler in the frame. See a biomedical-engineering reference §4.3 for documented
  cases.

---

## §12. Neural Rendering — Where the Fields Meet

**⚠️ The problem: novel view synthesis.** Given photos of a scene, render it from a
viewpoint you never captured. **This is vision (recover the scene) and graphics (render
it) as a single optimization**, and it's the most significant development in either field
in a decade.

**NeRF (2020)** — represent the scene as a continuous function `(x, y, z, θ, φ) →
(colour, density)`, learned as an MLP, rendered by **volumetric ray marching**, optimized
by comparing rendered pixels to captured photos. **Differentiable rendering is the key
idea** — the renderer is the loss function's forward pass.
⚠️ **NeRF's problem was always cost**: volumetric rendering requires many network
evaluations per ray. Instant-NGP's multiresolution hash encoding cut training to minutes;
rendering stayed slow.

**3D Gaussian Splatting (Kerbl et al., SIGGRAPH 2023)** — represent the scene as millions
of **anisotropic 3D Gaussian ellipsoids** with position, covariance, opacity, and
view-dependent colour via spherical harmonics. **Initialize from SfM points, then
interleave optimization with adaptive density control (splitting and cloning Gaussians
where reconstruction error is high), and rasterize with a fast visibility-aware
differentiable splatting algorithm.**

> **⚠️ The conceptual point that makes 3DGS click**: it is **explicit, not neural.**
> ⚠️ **There is no network evaluated at render time at all** — it's a rasterization of
> primitives, which is why it hits real-time on a GPU that was already built to rasterize.
> **The "neural" part is the optimization, not the representation.** ⚠️ **It's also not
> new in lineage — EWA splatting dates to 2002; what changed is differentiable
> optimization and adaptive densification.**

**§16.1 → `gfx-reference` for the current state.**

**⚠️ Limitations worth knowing regardless of version**: specular and reflective surfaces
are handled poorly (spherical harmonics can't represent view-dependent reflection well,
and the optimizer compensates by scattering Gaussians, hurting geometry); extracting a
clean **mesh** from either representation is a separate, imperfect step; **relighting** is
mostly unsolved because appearance and illumination are entangled; and **memory/storage**
for high-fidelity scenes is large, which is why compression is such an active area.

---

## §13. Performance

**Graphics**: ⚠️ **profile before optimizing, and identify which stage is the bottleneck**
— vertex, fragment, memory bandwidth, or CPU submission. **Tools**: RenderDoc, Nsight
Graphics, PIX, Xcode's frame debugger, RGP.
**Common wins**: reduce draw calls (instancing, batching, ⚠️ **indirect and bindless
rendering**), LOD, culling, ⚠️ **overdraw reduction via depth prepass or front-to-back
sorting**, texture compression and mipmaps, and shader complexity in that order.
**⚠️ The frame budget is brutal**: 16.6 ms at 60 fps, 8.3 ms at 120, ~11 ms per eye at 90
for VR — **and VR's cost of a dropped frame is nausea, not a stutter.**

**Vision**: ⚠️ **the biggest wins are usually resolution and preprocessing, not model
architecture.** Then quantization (INT8), pruning, distillation, batching, and the right
runtime (TensorRT, ONNX Runtime, OpenVINO, Core ML, TFLite). **⚠️ Measure end-to-end
including decode, resize and colour conversion** — on many pipelines the model is not the
bottleneck.
