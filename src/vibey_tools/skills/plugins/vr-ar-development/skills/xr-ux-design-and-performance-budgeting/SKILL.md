---
name: xr-ux-design-and-performance-budgeting
description: "Use when designing the experience and making it hold frame rate: UX design for 3D including affordances, depth cues, text legibility, comfortable placement zones and the conventions users already expect, and performance budgeting — the frame budget, draw calls, fill rate, and the profiling method for a target device."
---

# VR and AR Development: UX Design for 3D and Performance Budgeting

> **Part 4 of 5** of the *VR and AR Development* reference (plugin `vr-ar-development`), covering §10–§11. Sibling skills: `xr-perceptual-constraints-displays-and-tracking` (§0–§3), `xr-rendering-input-and-spatial-understanding` (§4–§6), `xr-platforms-audio-and-comfort` (§7–§9), `xr-reference` (§12–§17). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
>    in §9 → `xr-platforms-audio-and-comfort` and §10 is about protecting it.**

---

## §10. UX Design for 3D

**⚠️ Text is the first thing that goes wrong.** Panel resolution and PPD (§2 → `xr-perceptual-constraints-displays-and-tracking`) mean text
must be **larger and closer than your instinct says**, high contrast, and **never at the
extreme periphery.** **Test on device, always** — desktop preview is systematically
misleading.

**Comfortable placement**: ⚠️ **content roughly 0.5–20 m; the sweet spot for reading is
around 1–3 m.** **Keep the primary content within a modest cone around forward gaze
(roughly ±30° horizontal, less vertically)** — ⚠️ **and remember neck strain: looking up is
much worse than looking down.**

**⚠️ Diegetic UI beats floating panels.** A screen welded to the face breaks presence and
is uncomfortable; **put the interface on a wrist, a tool, a physical panel in the world.**

**Scale and affordance**: ⚠️ **incorrect scale is immediately and viscerally wrong** to
users, even when they can't articulate why. **Objects that look grabbable must be
grabbable.** **Give feedback for everything** — highlight, haptic, sound — because
⚠️ **without haptics, the visual and audio confirmation is the only signal that an
interaction registered.**

**⚠️ Never move the camera without user input** (§1.2 → `xr-perceptual-constraints-displays-and-tracking`). **Never lock content to the head
rigidly** — use lazy-follow / body-locked positioning with damping.

---

## §11. Performance Budgeting

**⚠️ The budget is brutal and it is per-eye.** At **90 Hz you have 11.1 ms for two eyes**;
at 120 Hz, **8.3 ms.** ⚠️ **And on standalone hardware you're on a mobile SoC with a
thermal ceiling — sustained performance is well below burst performance, so profile after
20 minutes, not after 20 seconds.**

**Where the time goes**: draw calls and CPU submission (⚠️ **batch aggressively; single-pass
stereo, §4.1 → `xr-rendering-input-and-spatial-understanding`**), overdraw and fill rate (⚠️ **the usual mobile-XR killer**), bandwidth
(TBDR, §4.4 → `xr-rendering-input-and-spatial-understanding`), shader complexity, and physics.

**Levers**: aggressive LOD, occlusion culling, **baked lighting** (⚠️ **lightmaps remain
the best quality-per-millisecond in XR**), **FFR** (§4.3 → `xr-rendering-input-and-spatial-understanding`), texture atlasing, **GPU
instancing**, simplified shaders, and **reducing render scale before reducing frame rate**
— ⚠️ **frame rate is non-negotiable in a way resolution isn't.**

**⚠️ Profile on device.** The editor and a desktop GPU tell you almost nothing about a
standalone headset. **RenderDoc, the platform's own profilers, and frame-time histograms
rather than averages** — ⚠️ **because a 1% frame spike is a visible, presence-breaking
hitch and averages hide it completely.**
