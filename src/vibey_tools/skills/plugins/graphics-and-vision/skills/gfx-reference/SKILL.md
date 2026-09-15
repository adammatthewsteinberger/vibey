---
name: gfx-reference
description: "Use when checking a graphics or vision anti-pattern, looking up a resolution, precision or throughput number, asking what actually moved (3D Gaussian splatting as the practical default, vision foundation models, verified August 2026), finding the books, or needing a method picker and a debug checklist for an image that looks wrong. Companion to the other graphics-and-vision skills."
---

# Graphics and Vision: Anti-Patterns, Numbers, What Moved, and Canon

> **Part 5 of 5** of the *Graphics and Vision* reference (plugin `graphics-and-vision`), covering §14–§19. Sibling skills: `gfx-transforms-rasterization-and-rendering` (§0–§4), `gfx-gpu-real-time-techniques-and-colour` (§5–§7), `gfx-image-formation-classical-vision-and-geometry` (§8–§10), `gfx-deep-learning-neural-rendering-and-performance` (§11–§13). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The mathematics is permanent — projective geometry, the rendering equation, epipolar geometry. Neural rendering and vision foundation models moved. See §16 below for those.

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
>    every approximation in §6 → `gfx-gpu-real-time-techniques-and-colour` are ways of estimating it under a time budget (§4 → `gfx-transforms-rasterization-and-rendering`).
> 3. **⚠️ Vision is underdetermined and that is not a solvable bug.** A single image is a
>    projection; depth is destroyed. Every vision method is adding a constraint — multiple
>    views, motion, a learned prior — to recover what the projection threw away (§8 → `gfx-image-formation-classical-vision-and-geometry`, §10 → `gfx-image-formation-classical-vision-and-geometry`).

---

## §14. Anti-Patterns

| Anti-pattern | Why |
|---|---|
| Transforming normals by the model matrix | ⚠️ **Use the inverse transpose** (§1 → `gfx-transforms-rasterization-and-rendering`) |
| Euler angles for interpolation or accumulation | Gimbal lock, drift (§1 → `gfx-transforms-rasterization-and-rendering`) |
| Lighting or blending in sRGB space | ⚠️ **The most common correctness bug in graphics** (§7 → `gfx-gpu-real-time-techniques-and-colour`) |
| Screen-space linear interpolation of attributes | ⚠️ **Must be perspective-correct** (§2 → `gfx-transforms-rasterization-and-rendering`) |
| Near plane at 0.001 to "be safe" | ⚠️ **Destroys depth precision. Z-fighting follows** (§2 → `gfx-transforms-rasterization-and-rendering`) |
| Fragment shader writing depth or using `discard` unnecessarily | ⚠️ **Kills early-Z silently** (§2 → `gfx-transforms-rasterization-and-rendering`) |
| Disabling mipmaps for sharpness | ⚠️ **They're antialiasing, not an optimization** (§2 → `gfx-transforms-rasterization-and-rendering`) |
| Intermediate metallic values | Physically meaningless (§3 → `gfx-transforms-rasterization-and-rendering`) |
| Constant shadow bias | ⚠️ **Acne or peter-panning. Use normal-offset** (§6 → `gfx-gpu-real-time-techniques-and-colour`) |
| Expecting SSR to reflect off-screen geometry | ⚠️ **Inherent limitation, not a bug** (§6 → `gfx-gpu-real-time-techniques-and-colour`) |
| Assuming hardware RT makes path tracing free | It accelerates queries; sampling still dominates (§4 → `gfx-transforms-rasterization-and-rendering`) |
| Branching on non-uniform values in a hot shader | ⚠️ **Warp divergence executes both paths** (§5 → `gfx-gpu-real-time-techniques-and-colour`) |
| Ignoring Vulkan/D3D12 validation layers | ⚠️ **Barrier races appear on one vendor only** (§5 → `gfx-gpu-real-time-techniques-and-colour`) |
| Calibrating with a board that never tilts | ⚠️ **Focal length and distance stay unseparable** (§8 → `gfx-image-formation-classical-vision-and-geometry`) |
| Calibration target that misses the image corners | Distortion goes unconstrained (§8 → `gfx-image-formation-classical-vision-and-geometry`) |
| Polynomial radial distortion on a fisheye | ⚠️ **Wrong model entirely** (§8 → `gfx-image-formation-classical-vision-and-geometry`) |
| Unnormalized 8-point algorithm | ⚠️ **Numerically terrible. Hartley-normalize** (§10 → `gfx-image-formation-classical-vision-and-geometry`) |
| Expecting absolute scale from a monocular sequence | ⚠️ **Inherent ambiguity** (§10 → `gfx-image-formation-classical-vision-and-geometry`) |
| Feature matching without RANSAC | Outliers are guaranteed (§9 → `gfx-image-formation-classical-vision-and-geometry`) |
| Stereo depth quoted without stating range | ⚠️ **Error grows with distance squared** (§10 → `gfx-image-formation-classical-vision-and-geometry`) |
| Augmentation that breaks task invariance | ⚠️ **Silently caps your ceiling** (§11 → `gfx-deep-learning-neural-rendering-and-performance`) |
| Reporting test-set accuracy as deployment performance | ⚠️ **Domain shift is where vision fails** (§11 → `gfx-deep-learning-neural-rendering-and-performance`) |
| Optimizing the model before profiling the pipeline | ⚠️ **Decode and resize are often the bottleneck** (§13 → `gfx-deep-learning-neural-rendering-and-performance`) |
| Expecting clean meshes or relighting from 3DGS | Both are open problems (§12 → `gfx-deep-learning-neural-rendering-and-performance`) |

---

## §15. Numbers

```
FRAME BUDGETS
60 fps = 16.6 ms · 120 fps = 8.3 ms · ⚠️ VR 90 Hz ≈ 11 ms per eye
GPU warp/wavefront: 32 (NVIDIA) · 32/64 (AMD)

MATH
Homogeneous: position w=1, direction w=0
⚠️ Normals: inverse transpose · Quaternion: q and −q are the same rotation
NDC depth: OpenGL [−1,1] · D3D/Vulkan/Metal [0,1]
Monte Carlo variance ~1/√N  ⚠️ (4× samples to halve noise)
SH: 9 coefficients ≈ diffuse environment lighting

PBR
Dielectric F0 ≈ 0.04 (4%) · Metals: no diffuse, tinted specular
GGX/Trowbridge-Reitz for D · Schlick for F · Smith for G

VISION
⚠️ Stereo depth error ∝ Z² · Z = f·B/d
Essential matrix: 5 DOF, t up to scale, 4 candidate decompositions
⚠️ Shot noise is Poisson — SNR ∝ √signal
Bayer: 2 green per 1 red, 1 blue

NEURAL RENDERING (§16.1 for verification)
NeRF ~5 fps, hours to train · 3DGS 100+ fps, minutes to train
Quality both ~25–33 dB PSNR
```

---

## §16. What Actually Moved — verified August 2026

**⚠️ Everything in §1–§11 → `gfx-transforms-rasterization-and-rendering`, `gfx-gpu-real-time-techniques-and-colour`, `gfx-image-formation-classical-vision-and-geometry`, `gfx-deep-learning-neural-rendering-and-performance` is stable. These two areas are not.**

### 16.1 Neural rendering: 3DGS has become the practical default
- **3DGS** was introduced by **Kerbl et al. at SIGGRAPH 2023** (ACM TOG 42(4)), and
  **demonstrated state-of-the-art quality matching or exceeding Mip-NeRF 360** on
  Tanks and Temples and the synthetic NeRF dataset.
- **⚠️ Reported comparison against NeRF: ~100+ fps versus roughly 5 fps, training in
  minutes rather than hours, at equal or better quality (~25–33 dB PSNR).**
- **As of early 2026 it is described as one of the dominant paradigms in 3D scene
  representation, increasingly displacing NeRF-based approaches**, with commercial
  adoption across VR/AR, VFX, real estate and autonomous driving, and consumer capture via
  Luma AI, Polycam and similar.
- **⚠️ The standardization signal is the strongest evidence it's durable**: adoption into
  **OpenUSD (reported April 2026)** and **Khronos glTF via a `KHR_gaussian_splatting`
  extension.** ⚠️ **A representation getting into the interchange standards is what
  separates a technique from a research result.**
- **Active research directions**: compression and pruning (⚠️ **memory is the main
  practical constraint — LightGaussian reports ~15× reduction with 200+ fps; RadSplat
  reports 900+ fps**), reflections and specular handling, mesh extraction, semantics
  (LERF, GARField), robotics and driving applications, and ray-traced Gaussians.

> **⚠️ GOTCHA — two cautions on the numbers above.** **The fps and PSNR comparisons come
> from a commercial 3D-scanning site**, and while they are consistent with the original
> paper's claims and the broad literature, ⚠️ **they are marketing-adjacent and vary
> enormously with scene, resolution and hardware. Treat them as order-of-magnitude.**
> **And "3DGS replaced NeRF" is too strong**: ⚠️ **NeRF-family methods remain competitive
> where the scene is small and quality matters more than speed, and much 3DGS research
> still benchmarks against Mip-NeRF 360.** **The right claim is that 3DGS won the
> real-time and production niche decisively.**

### 16.2 Vision foundation models
**⚠️ The structural change: task-specific models trained on narrow datasets have been
substantially displaced by large pretrained backbones you prompt, adapt, or distil.**

**The current landscape (August 2026):**
- **SAM 3** (Meta, late 2025) — ⚠️ **the significant step is from geometry to concepts.**
  SAM 1 (2023) segmented from clicks and boxes on images; SAM 2 (2024) added video
  tracking; **SAM 3 introduces Promptable Concept Segmentation — a short noun phrase
  ("yellow school bus") or an image exemplar finds and segments *all* instances across an
  image or video.** ⚠️ **It's open-vocabulary rather than a fixed taxonomy.**
- **DINOv3** — self-supervised backbone; ⚠️ **the choice when you need strong features
  with limited labels**, with distilled variants (ViT-S/B/L, ConvNeXt) for edge deployment.
- **Grounding DINO** — text-prompted bounding boxes; **YOLO-World** — fast open-vocabulary
  detection without masks; **RF-DETR** and **YOLO26** for task-specific speed;
  **CLIP / SigLIP 2** for embeddings and zero-shot; **Florence-2** (compact multi-task);
  **Qwen3-VL** (broader visual reasoning, VQA, documents); **Depth Anything 3**.
- **⚠️ The dominant production pattern is composition, not a single model**: e.g. text
  prompt → Grounding DINO detection → SAM segmentation (**Grounded-SAM**), or
  open-vocabulary detection → promptable segmentation and tracking → self-supervised
  embedding → a small task head.
- **⚠️ And the deployment pattern is distil-then-ship**: use the foundation model to
  generate labels or as a teacher, then run a small task-specific student in production.
  A 2026 paper distils **SAM 3's 446M-parameter Perception Encoder into a 40.66M student**,
  reporting **~7.8× parameter reduction and ~3× lower peak VRAM for ~1.7 points of MOTA** —
  ⚠️ **which is the shape of the whole trend: foundation models for labels and prototyping,
  compact models for deployment.**

**⚠️ What this does NOT mean.** **Classical CV (§9 → `gfx-image-formation-classical-vision-and-geometry`) and multiple view geometry (§10 → `gfx-image-formation-classical-vision-and-geometry`) are
not obsolete** — ⚠️ **calibration, epipolar geometry, RANSAC, bundle adjustment and
optical flow remain the correct tools, and a foundation model does not give you metric
3D.** **The honest framing is that recognition and segmentation were substantially
absorbed by foundation models; geometry was not.**

⚠️ **Sourcing caveat**: much of the model-landscape detail above comes from **Roboflow's
comparison posts and similar vendor blogs**, which are competent and current but are
commercially interested in the tooling ecosystem. **The SAM 3 architecture claims trace to
the paper and to independent research using it**; the model rankings should be read as
orientation, not evaluation.

---

## §17. Books

| Author | Work | Why |
|---|---|---|
| **Akenine-Möller, Haines & Hoffman** | ***Real-Time Rendering*** (4th ed.) | ⚠️ **The graphics reference. Nothing else is close** |
| **Pharr, Jakob & Humphreys** | ***Physically Based Rendering*** | ⚠️ **Free online, and it IS the path tracer. Won a Sci-Tech Oscar** |
| **Shirley** | *Ray Tracing in One Weekend* series | ⚠️ **Free. The best possible starting point** |
| **Hughes et al.** | *Computer Graphics: Principles and Practice* | The classic foundation |
| **Hartley & Zisserman** | ***Multiple View Geometry in Computer Vision*** | ⚠️ **§10 → `gfx-image-formation-classical-vision-and-geometry` is this book. The definitive text** |
| **Szeliski** | ***Computer Vision: Algorithms and Applications*** | ⚠️ **Free online. The broad modern survey** |
| **Forsyth & Ponce** | *Computer Vision: A Modern Approach* | The other standard text |
| **Prince** | *Understanding Deep Learning* | ⚠️ **Free, and the best-written modern DL book** |
| **Gortler** | *Foundations of 3D Computer Graphics* | ⚠️ **Excellent on §1 → `gfx-transforms-rasterization-and-rendering`'s transform conventions** |
| **Marschner & Shirley** | *Fundamentals of Computer Graphics* | Course-standard |

**Practical**: **LearnOpenGL** (⚠️ **the best free graphics tutorial series**),
**Vulkan Tutorial** and **vkguide**, **WebGPU Fundamentals**, **Shadertoy**,
**Íñigo Quílez's articles** (⚠️ **SDFs and raymarching, from a master**),
**scratchapixel**, **GPU Gems / GPU Zen / Ray Tracing Gems** (much free),
**SIGGRAPH course notes** (⚠️ **the real state of the art in real-time rendering, and
free**), **OpenCV docs**, **COLMAP**, **Nerfstudio**, **PyTorch3D**, **Kornia**,
and **papers with code / CVPR-ICCV-ECCV proceedings.**

---

## §18. Quick Reference

### 18.1 Picker
| Need | Use |
|---|---|
| Rotation storage and interpolation | ⚠️ **Quaternions** (§1 → `gfx-transforms-rasterization-and-rendering`) |
| Rotation optimization | ⚠️ **Lie algebra (SO(3)/SE(3))** (§1 → `gfx-transforms-rasterization-and-rendering`) |
| Many dynamic lights | Deferred or clustered forward (§6 → `gfx-gpu-real-time-techniques-and-colour`) |
| Geometric edge antialiasing only | MSAA (§6 → `gfx-gpu-real-time-techniques-and-colour`) |
| Modern AA + upscaling | ⚠️ **TAA-based (DLSS/FSR/XeSS)** (§6 → `gfx-gpu-real-time-techniques-and-colour`) |
| Ground-truth quality, offline | Path tracing (§4 → `gfx-transforms-rasterization-and-rendering`) |
| Cheap ambient occlusion | GTAO (§6 → `gfx-gpu-real-time-techniques-and-colour`) |
| Reflections including off-screen | ⚠️ **Not SSR — needs RT or probes** (§6 → `gfx-gpu-real-time-techniques-and-colour`) |
| Learn a modern graphics API first | ⚠️ **WebGPU** (§5 → `gfx-gpu-real-time-techniques-and-colour`) |
| Camera pose from a known 3D model | **PnP + RANSAC** (§9 → `gfx-image-formation-classical-vision-and-geometry`, §10 → `gfx-image-formation-classical-vision-and-geometry`) |
| Two-view geometry, calibrated | **5-point essential matrix** (§10 → `gfx-image-formation-classical-vision-and-geometry`) |
| Refine a whole reconstruction | ⚠️ **Bundle adjustment (Ceres/g2o)** (§10 → `gfx-image-formation-classical-vision-and-geometry`) |
| Real-time camera tracking | ORB-SLAM3, or ⚠️ **VIO if you have an IMU** (§10 → `gfx-image-formation-classical-vision-and-geometry`) |
| Metric scale from one camera | ⚠️ **Impossible without a prior — add IMU/stereo/known size** (§10 → `gfx-image-formation-classical-vision-and-geometry`) |
| Photorealistic capture → real-time render | ⚠️ **3DGS** (§12 → `gfx-deep-learning-neural-rendering-and-performance`, §16.1) |
| Segment anything by text prompt | **SAM 3**, or Grounded-SAM (§16.2) |
| Strong features, few labels | **DINOv3** (§16.2) |
| Fast open-vocab detection, no masks | YOLO-World (§16.2) |
| Ship on edge hardware | ⚠️ **Distil a foundation model into a small student** (§16.2) |

### 18.2 Debug checklist
- [ ] Everything black? → check transform order, winding/culling, near/far planes
- [ ] Lighting looks flat or washed out? → ⚠️ **linear vs sRGB (§7 → `gfx-gpu-real-time-techniques-and-colour`)**
- [ ] Lighting wrong under non-uniform scale? → ⚠️ **normal matrix (§1 → `gfx-transforms-rasterization-and-rendering`)**
- [ ] Textures warp toward edges? → perspective-correct interpolation (§2 → `gfx-transforms-rasterization-and-rendering`)
- [ ] Flickering surfaces at distance? → ⚠️ **push the near plane out; reversed-Z (§2 → `gfx-transforms-rasterization-and-rendering`)**
- [ ] Shadow acne or floating shadows? → normal-offset bias (§6 → `gfx-gpu-real-time-techniques-and-colour`)
- [ ] Ghosting on motion? → TAA history rejection (§6 → `gfx-gpu-real-time-techniques-and-colour`)
- [ ] Corruption on one GPU vendor only? → ⚠️ **barriers. Run validation layers (§5 → `gfx-gpu-real-time-techniques-and-colour`)**
- [ ] Reconstruction drifts or scale is wrong? → ⚠️ **monocular scale ambiguity (§10 → `gfx-image-formation-classical-vision-and-geometry`)**
- [ ] Calibration reprojection error high? → board tilt and corner coverage (§8 → `gfx-image-formation-classical-vision-and-geometry`)
- [ ] Model great in test, bad in field? → ⚠️ **domain shift, or a shortcut feature (§11 → `gfx-deep-learning-neural-rendering-and-performance`)**

---

## §19. Method

**§1–§15 → `gfx-transforms-rasterization-and-rendering`, `gfx-gpu-real-time-techniques-and-colour`, `gfx-image-formation-classical-vision-and-geometry`, `gfx-deep-learning-neural-rendering-and-performance` rest on permanent material** — projective geometry, **Kajiya's rendering equation
(1986)**, microfacet theory, epipolar geometry, and the classical CV algorithms — sourced
from the references in §17, chiefly **Real-Time Rendering**, **PBRT**, **Hartley &
Zisserman**, and **Szeliski**. ⚠️ **None of it needed web verification, and §19's whole
point is that the ratio of permanent to perishable in this field is very high — the
frontier moves fast, the foundations do not.**

**Two searches were run in August 2026**, confined to the two genuinely moving areas:
**neural rendering** and **vision foundation models.** ⚠️ **Both are quarantined in §16 so
the rest of the document doesn't rot around them.**

**Confidence.** **High** in §1–§15 → `gfx-transforms-rasterization-and-rendering`, `gfx-gpu-real-time-techniques-and-colour`, `gfx-image-formation-classical-vision-and-geometry`, `gfx-deep-learning-neural-rendering-and-performance`: standard mathematics and long-established technique,
with the subtleties (normal matrices, Hartley normalization, perspective-correct
interpolation, warp divergence, linear-vs-sRGB) stated because ⚠️ **those are precisely
where correct-looking implementations are silently wrong.**

**High** in **§12 → `gfx-deep-learning-neural-rendering-and-performance` and §16.1's technical content** — the 3DGS description traces to the
original SIGGRAPH 2023 paper and Inria's project page: **anisotropic covariance
optimization, interleaved density control, visibility-aware differentiable rasterization,
and SfM initialization** are all as the authors describe them. ⚠️ **The observation that
3DGS is explicit rather than neural, and descends from EWA splatting (2002), is my
framing, and I think it's the single most clarifying thing to understand about it.**

⚠️ **Three hedges, all flagged in place.** **The 3DGS-vs-NeRF performance figures come
from a commercial 3D-scanning site** — consistent with the literature, but marketing-
adjacent and hugely scene- and hardware-dependent. **The OpenUSD and glTF standardization
claims come from the same source** and I have marked the OpenUSD date as reported;
⚠️ **verify against Khronos and the OpenUSD project before relying on it.** And
**§16.2's model landscape leans on Roboflow's comparison posts and similar vendor blogs** —
current and competent, but commercially interested. **The SAM 3 capability claims trace to
the paper and to independent research papers using it, which is stronger evidence than the
rankings.**

**⚠️ One judgement I'll state plainly**: the framing in §16.2 that **recognition and
segmentation were substantially absorbed by foundation models while geometry was not** is
my assessment. **I think it's well-supported — the 2026 literature still runs SfM, bundle
adjustment and RANSAC underneath the learned components — but it is an interpretation,
not a citation.**
