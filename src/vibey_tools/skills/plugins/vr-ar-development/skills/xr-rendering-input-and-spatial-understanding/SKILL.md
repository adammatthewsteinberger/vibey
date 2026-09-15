---
name: xr-rendering-input-and-spatial-understanding
description: "Use when building the core loop: stereo rendering, reprojection as the safety net, foveated rendering and the rest of the XR-specific frame budget; input and interaction including controllers, hand tracking, gorilla arm and interaction ergonomics, and locomotion as the highest-risk design decision; and AR spatial understanding with plane detection, meshing, anchors and occlusion."
---

# VR and AR Development: The XR Rendering Pipeline, Input and Interaction, and AR Spatial Understanding

> **Part 2 of 5** of the *VR and AR Development* reference (plugin `vr-ar-development`), covering §4–§6. Sibling skills: `xr-perceptual-constraints-displays-and-tracking` (§0–§3), `xr-platforms-audio-and-comfort` (§7–§9), `xr-ux-design-and-performance-budgeting` (§10–§11), `xr-reference` (§12–§17). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
>    in §9 → `xr-platforms-audio-and-comfort` and §10 → `xr-ux-design-and-performance-budgeting` is about protecting it.**

---

## §4. The XR Rendering Pipeline

### 4.1 Stereo
**Two views with an eye offset (the IPD), each with its own asymmetric projection matrix**
— ⚠️ **the frustums are off-axis, not simply translated, and getting that wrong produces
subtle depth discomfort that's hard to diagnose.**

**⚠️ Do not naively render everything twice.** The optimizations:
- **Single-pass / multiview** — ⚠️ **one geometry pass, two render targets via a
  geometry-shader-free instancing path. The standard win, roughly halving CPU draw
  overhead.**
- **Instanced stereo**, **view-dependent culling**, and ⚠️ **stereo-aware shadow and
  reflection passes that are shared rather than duplicated.**

### 4.2 Reprojection — the safety net
**⚠️ This is the mechanism that makes XR tolerable and it deserves to be understood.**
- **Timewarp / ATW (asynchronous timewarp)**: ⚠️ **just before scanout, re-warp the
  rendered frame using the very latest head orientation.** **Corrects rotational error
  only, cheaply** — and it's what decouples perceived latency from frame time.
- **Spacewarp / ASW**: ⚠️ **synthesizes an intermediate frame from motion vectors when you
  miss frame rate.** **Extrapolation, so it produces artifacts around fast-moving objects
  and disocclusions.**
- **Positional timewarp** corrects translation too, and needs depth.

> **⚠️ GOTCHA — reprojection is a safety net, not a performance budget.** It is designed
> for the occasional missed frame. ⚠️ **Shipping a title that relies on ASW to hit its
> target frame rate produces a permanently artifacted experience**, and on some platforms
> it will fail certification. **Hit native frame rate; let reprojection catch the
> outliers.**

### 4.3 Foveated rendering
**Render at full resolution where the user is looking and lower resolution in the
periphery** — ⚠️ **justified because human acuity falls sharply with eccentricity.**
- **Fixed foveated rendering (FFR)** — ⚠️ **no eye tracking needed; exploits the fact that
  lens distortion already wastes samples at the edges. Free performance, widely used.**
- **Eye-tracked foveated rendering (ETFR)** — ⚠️ **much larger savings, and it needs the
  gaze latency budget from §1.1 → `xr-perceptual-constraints-displays-and-tracking` (42–91 ms tolerable, far looser than head MTP).**

### 4.4 The rest of the XR-specific budget
**⚠️ MSAA is preferred over TAA in XR** — TAA's ghosting and blur are far more objectionable
in a stereo, head-tracked display than on a monitor, and ⚠️ **temporal artifacts break
presence.**
**Forward rendering is often preferred** over deferred, because MSAA works with it and
bandwidth is precious on mobile chips.
**⚠️ Mobile XR is tile-based deferred rendering (TBDR)** — which means **avoid
mid-frame render target switches, avoid reading back, and keep the tile resident.**
**Resolution**: render target is typically **1.2–1.4× display resolution** to survive
distortion resampling (§2 → `xr-perceptual-constraints-displays-and-tracking`).

---

## §5. Input and Interaction

**Controllers** — ⚠️ **still the most precise and lowest-fatigue input, with haptics and
unambiguous button state.** Don't dismiss them.

**Hand tracking** — ⚠️ **natural and requires no hardware, and it is genuinely worse for
precision work**: no haptic feedback, occlusion when hands overlap or leave the camera
frustum, and **fatigue** (§5.3). **Pinch is the reliable gesture; complex gestures are
not.**

**Eye tracking** — foveated rendering (§4.3), **gaze-based selection** (⚠️ **"gaze and
pinch" is visionOS's core interaction and it works well**), social presence via avatar
eyes, and analytics. ⚠️ **Eye data is biometric and privacy-sensitive — treat it
accordingly.**

**Others**: voice, body/face tracking, haptic gloves and vests, treadmills, **and
passthrough-based real-world input.**

### 5.3 ⚠️ Gorilla arm and interaction ergonomics
**Holding arms extended is exhausting within minutes.** **Design for hands resting near
the body**: ⚠️ **short pinch gestures over big arm movements, interaction targets below
eye level and within a comfortable cone, and no sustained holding.** **visionOS's
gaze-targets-and-hand-confirms model exists precisely to avoid this**, and it's worth
copying regardless of platform.

### 5.4 Locomotion — the highest-risk design decision
| Method | Comfort | ⚠️ Notes |
|---|---|---|
| **Room-scale physical** | ⚠️ **Best** | No conflict at all; limited by play space |
| **Teleport** | ⚠️ **Very high** | No optic flow; breaks immersion, and that's an acceptable trade |
| **Dash / blink** | High | Very fast movement reads as instant |
| **Smooth locomotion + vignette** | Moderate | ⚠️ **Offer, don't impose; always with comfort options** |
| **Smooth locomotion, no mitigation** | ⚠️ **Worst** | Common cause of first-session nausea |
| **Snap turn** | High | ⚠️ **Avoid smooth turning — rotation is worse than translation** |
| **Redirected walking** | High | Needs a large tracked space |

**⚠️ Rotation is more nauseating than translation, and yaw is the worst axis.** **Snap
turn should be the default and smooth turn opt-in.**

---

## §6. AR Spatial Understanding

**Anchors** — ⚠️ **a pose the system continuously refines as its map improves.** **Attach
content to an anchor rather than to world coordinates**, because ⚠️ **the world origin
drifts as SLAM refines; anchored content stays put relative to the real world and
unanchored content visibly slides.**

**Plane detection** (horizontal/vertical), **mesh reconstruction** (⚠️ **scene meshing
gives you physics and occlusion geometry**), **semantic scene understanding** (this is a
wall / a table / a floor), **image and object tracking**, and **hit testing** against
detected geometry.

**⚠️ Occlusion is the hardest and most important AR correctness problem.** Without it,
virtual objects float in front of everything and the illusion never forms. **Approaches**:
depth from a sensor or stereo, reconstructed mesh, and **learned monocular depth** —
⚠️ **and note §2 → `xr-perceptual-constraints-displays-and-tracking`: on optical see-through hardware, true occlusion of the real world is
physically impossible because you can only add light.**

**Lighting estimation** — match virtual lighting to the real environment (ambient
intensity, colour temperature, dominant direction, environment probe). ⚠️ **A correctly
lit and shadowed object at the wrong scale still looks wrong; a mediocre model with a
correct contact shadow looks glued down. Contact shadows are the highest-leverage AR
rendering feature.**

**⚠️ Persistence and sharing**: cloud anchors and shared coordinate frames for multi-user
AR, and **localization against a saved map.** ⚠️ **Relocalization is fragile under changed
lighting and rearranged furniture** — design for it failing.
