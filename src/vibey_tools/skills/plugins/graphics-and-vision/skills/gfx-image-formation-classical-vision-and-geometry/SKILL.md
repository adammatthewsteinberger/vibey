---
name: gfx-image-formation-classical-vision-and-geometry
description: "Use when recovering information from images: image formation and camera calibration including lens models, intrinsics, extrinsics and distortion; classical computer vision — filtering, edges, features, descriptors, matching and segmentation; and multiple view geometry with epipolar geometry, the fundamental and essential matrices, triangulation, structure from motion and bundle adjustment."
---

# Graphics and Vision: Image Formation, Classical Computer Vision, and Multiple View Geometry

> **Part 3 of 5** of the *Graphics and Vision* reference (plugin `graphics-and-vision`), covering §8–§10. Sibling skills: `gfx-transforms-rasterization-and-rendering` (§0–§4), `gfx-gpu-real-time-techniques-and-colour` (§5–§7), `gfx-deep-learning-neural-rendering-and-performance` (§11–§13), `gfx-reference` (§14–§19). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
>    every approximation in §6 → `gfx-gpu-real-time-techniques-and-colour` are ways of estimating it under a time budget (§4 → `gfx-transforms-rasterization-and-rendering`).
> 3. **⚠️ Vision is underdetermined and that is not a solvable bug.** A single image is a
>    projection; depth is destroyed. Every vision method is adding a constraint — multiple
>    views, motion, a learned prior — to recover what the projection threw away (§8, §10).

---

## §8. Image Formation and Calibration

**The pinhole model** — the shared foundation of §1 → `gfx-transforms-rasterization-and-rendering` and everything in vision:
```
        [fx  s  cx]
K =     [0  fy  cy]        x = K [R | t] X
        [0   0   1]
```
**`K` is intrinsics** (focal lengths in pixels, principal point, skew — ⚠️ **skew is
essentially always 0 in real cameras**); **`[R|t]` is extrinsics** (pose).

**⚠️ Distortion is not in that model and must be handled separately**: radial
(`k1, k2, k3` — barrel/pincushion) and tangential (`p1, p2`). **Fisheye and wide-angle
need a different model entirely** (equidistant, Kannala-Brandt) — ⚠️ **applying the
polynomial radial model to a fisheye lens fails badly.**

**Calibration**: **Zhang's method** — a planar checkerboard at multiple orientations,
solve for `K` and distortion, refine by bundle adjustment.
**⚠️ The practical failures**: too few orientations (⚠️ **you need real tilt, not just
translation, or focal length and distance are unseparable**), the board not covering the
image corners (⚠️ **where distortion is largest, so it goes unconstrained**), a non-flat
printed target, and **rolling shutter** on a moving camera.

**Sensor realities**: **Bayer pattern** and demosaicing, rolling vs global shutter
(⚠️ **rolling shutter skews moving objects and breaks the rigid-projection assumption
underlying SfM**), exposure and noise (photon/shot noise is Poisson — ⚠️ **noise scales
with the square root of signal, which is why dark regions are noisier**), and **the ISP
pipeline**, which has usually already applied sharpening, denoising and tone curves before
you see the image.

---

## §9. Classical Computer Vision

**⚠️ Still the right answer for many problems, and cheaper and more debuggable than a
network.**

**Filtering**: convolution, Gaussian blur (⚠️ **separable — `O(n)` per pixel instead of
`O(n²)`**), median (edge-preserving, good for salt-and-pepper), bilateral (edge-preserving
smoothing), morphological (erode, dilate, open, close).

**Edges**: Sobel/Scharr gradients, **Canny** (⚠️ **gradient → non-maximum suppression →
hysteresis thresholding — the double threshold is what makes it robust**), Laplacian of
Gaussian.

**Features**: **Harris** corners (⚠️ **the structure tensor's eigenvalues distinguish flat,
edge and corner**), **SIFT** (⚠️ **scale and rotation invariant; the benchmark for two
decades and now patent-free**), SURF, **ORB** (⚠️ **fast, binary descriptor, free — the
default for real-time SLAM**), AKAZE, and learned features (SuperPoint, DISK)
with **learned matching (SuperGlue, LightGlue)** — ⚠️ **which substantially outperform
nearest-neighbour matching on hard pairs.**

**Matching and robustness**: ratio test (Lowe), and **RANSAC** — ⚠️ **the workhorse:
randomly sample a minimal set, fit, count inliers, repeat. Everything in §10 depends on it,
because feature matches always contain outliers.** MAGSAC++ is the modern variant.

**Other classical**: Hough transform, template matching, optical flow (**Lucas-Kanade**
sparse, **Farnebäck** dense, ⚠️ **RAFT and successors for learned flow**), background
subtraction, watershed and graph-cut segmentation.

---

## §10. Multiple View Geometry

**⚠️ This is the mathematical core of 3D vision and it has not changed.**

**Epipolar geometry**: given two views, a point in one image constrains its match to a
**line** in the other.
```
x'ᵀ F x = 0      fundamental matrix, uncalibrated (7 DOF)
x'ᵀ E x = 0      essential matrix, calibrated:  E = Kᵀ F K'
```
**⚠️ `E` decomposes into `R` and `t` — with `t` only up to scale, and four candidate
solutions.** **Cheirality (the requirement that points be in front of both cameras) picks
the right one.** ⚠️ **Monocular reconstruction has an inherent scale ambiguity that no
amount of processing removes — you need a known baseline, an object of known size, or
another sensor.**

**Estimation**: 8-point and normalized 8-point for `F`, **5-point (Nistér)** for `E`,
**PnP** for pose from known 3D-2D correspondences, homography (`H`) for planes or pure
rotation.
**⚠️ Hartley normalization is not optional** — the unnormalized 8-point algorithm is
numerically terrible, and this is one of the best-known "the textbook version fails"
results in the field.

**Triangulation** → 3D points. **Bundle adjustment** — ⚠️ **the global nonlinear
least-squares refinement of all poses and points simultaneously, minimizing reprojection
error.** Sparse Levenberg-Marquardt exploiting the **Schur complement** structure; **Ceres**
and **g2o** are the standard solvers.

**Pipelines**: **SfM** (offline, incremental or global — **COLMAP** is the reference),
**MVS** for dense reconstruction, **visual SLAM** (⚠️ **ORB-SLAM3 as the classical
benchmark; feature-based vs direct methods like DSO/LSD-SLAM**), **VIO** (⚠️ **fusing an
IMU resolves scale and handles fast motion — which is why every practical AR system is
visual-inertial**).

**Stereo**: rectify → disparity → depth (`Z = f·B/d`). ⚠️ **Depth error grows with the
square of distance**, so a stereo rig has a usable range set by its baseline. **SGM
(semi-global matching)** is the classical standard.
