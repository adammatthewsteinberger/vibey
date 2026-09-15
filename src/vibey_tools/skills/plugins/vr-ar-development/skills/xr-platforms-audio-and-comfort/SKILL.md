---
name: xr-platforms-audio-and-comfort
description: "Use when targeting real devices and real users: platforms and APIs including OpenXR and WebXR and the engine integrations, spatial audio with HRTFs, room modelling and why audio carries more presence than expected, and comfort, safety and accessibility including guardian systems, session length, and designing for seated, standing and mobility-limited users."
---

# VR and AR Development: Platforms and APIs, Spatial Audio, and Comfort, Safety and Accessibility

> **Part 3 of 5** of the *VR and AR Development* reference (plugin `vr-ar-development`), covering §7–§9. Sibling skills: `xr-perceptual-constraints-displays-and-tracking` (§0–§3), `xr-rendering-input-and-spatial-understanding` (§4–§6), `xr-ux-design-and-performance-budgeting` (§10–§11), `xr-reference` (§12–§17). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The perceptual constraints are human physiology and permanent; the platform and hardware landscape moves fast. See §14 → `xr-reference` for the current picture.

> **Scope.** Assumes a graphics reference for the rendering fundamentals (rasterization,
> PBR, the rendering equation) and a computer-vision reference for SLAM and multi-view
> geometry. **This is the XR-specific layer built on top of both.**
>
> **⚠️ GOTCHA** boxes mark what makes users physically ill or breaks presence.
>
> **The three facts that make XR its own discipline:**
> 1. **⚠️ You are rendering to a nervous system, not a screen.** The frame budget is set by
>    human perception, and missing it doesn't drop quality — **it makes people nauseated**
>    (§1 → `xr-perceptual-constraints-displays-and-tracking`). **No other software has this property.**
> 2. **⚠️ Latency is the master constraint and it is not a performance metric.** Motion-to-
>    photon under ~20 ms is the consensus threshold, and it governs your entire
>    architecture (§1.1 → `xr-perceptual-constraints-displays-and-tracking`).
> 3. **⚠️ Presence is fragile and asymmetric.** It takes sustained correctness to build and
>    one bad frame, one wrong-scale object, one mistracked hand to destroy. **Everything
>    in §9 and §10 → `xr-ux-design-and-performance-budgeting` is about protecting it.**

---

## §7. Platforms and APIs

**⚠️ OpenXR (Khronos) is the answer to the fragmentation question**: a royalty-free open
standard providing a unified API across headsets, acting as an abstraction layer so
**applications built against OpenXR run on any conformant headset without
modification.** ⚠️ **Both Unity and Unreal recommend OpenXR for cross-platform XR, and
maintaining separate SteamVR / Meta-native / MSMR code paths is significant avoidable
overhead.** **Any project targeting more than one platform should build on it** (§14 → `xr-reference`).

**Engines**: **Unity** (⚠️ **the most production-ready cross-platform option; XR
Interaction Toolkit; PolySpatial for visionOS**), **Unreal** (higher fidelity, heavier),
**Godot** (improving OpenXR support), and **native** (RealityKit/ARKit on Apple, Jetpack
XR on Android XR).
**Web**: **WebXR** — ⚠️ **one codebase across headsets and phone browsers; Three.js,
Babylon.js, A-Frame, React Three Fiber** (§14.2 → `xr-reference`).

**⚠️ Abstraction has a cost worth knowing about**: Unity's PolySpatial layer for visionOS
is reported at **15–25% worse rendering performance than native RealityKit**, with some
visionOS-specific features not reachable through it. **Cross-platform is a real trade,
not a free win.**

---

## §8. Spatial Audio

**⚠️ Audio contributes more to presence per unit of engineering effort than almost
anything in graphics, and it is chronically neglected.**

**HRTF (head-related transfer function)** — how your head, ears and torso filter sound by
direction. Convolving with an HRTF produces convincing 3D localization over headphones.
⚠️ **HRTFs are individual; generic ones work adequately but front-back confusion is
common, and small head movements resolve it — which is why head-tracked audio matters
more than HRTF quality.**

**Ambisonics** for scene-based audio, **room acoustics** (early reflections, reverb,
**occlusion and obstruction** by geometry), and **distance attenuation with air
absorption.**
**⚠️ Head-tracked audio is non-negotiable**: the soundfield must stay fixed in world space
as the head turns. **Untracked audio destroys presence immediately.**

---

## §9. Comfort, Safety, Accessibility

**Comfort options are a shipping requirement, not a nicety** (§5.4 → `xr-rendering-input-and-spatial-understanding`): ⚠️ **vignette
intensity, snap vs smooth turn, teleport vs smooth locomotion, seated vs standing,
dominant hand, height calibration, and a comfort rating on the store page.**

**Physical safety**: **guardian/boundary systems**, ⚠️ **passthrough on boundary
approach**, and design that **discourages large fast movements or backward walking.**
**⚠️ Real-world hazards are your problem** — people swing controllers into walls, ceiling
fans and other people.

**Health**: ⚠️ **encourage breaks; eye strain from VAC (§1.3 → `xr-perceptual-constraints-displays-and-tracking`) accumulates.** Manufacturer
guidance on age limits exists and is generally conservative. **Hygiene for shared
headsets.** **Photosensitivity — avoid strobing.**

**Accessibility**: ⚠️ **XR is unusually exclusionary by default.** Consider **seated and
one-handed play**, **subtitles positioned in 3D space** (⚠️ **and readable — see §10 → `xr-ux-design-and-performance-budgeting`**),
**colourblind-safe design**, **adjustable text size and interaction distance**, **height
adjustment for wheelchair users**, and ⚠️ **alternatives to gestures that require full hand
function.** **Not everyone has stereo vision** — around a few percent of people don't
fuse stereo, so **don't make depth the sole channel for critical information.**
