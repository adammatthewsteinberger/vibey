---
name: xr-perceptual-constraints-displays-and-tracking
description: "Use when reasoning about why an XR experience feels wrong: motion-to-photon latency and its budget, cybersickness and what actually causes it, the vergence-accommodation conflict, and presence; displays and optics including panels, lenses, field of view and distortion correction; and tracking — inside-out and outside-in, degrees of freedom, drift and prediction. Includes the router for the whole vr-ar-development reference."
---

# VR and AR Development: The Perceptual Constraints, Displays and Optics, and Tracking

> **Part 1 of 5** of the *VR and AR Development* reference (plugin `vr-ar-development`), covering §0–§3. Sibling skills: `xr-rendering-input-and-spatial-understanding` (§4–§6), `xr-platforms-audio-and-comfort` (§7–§9), `xr-ux-design-and-performance-budgeting` (§10–§11), `xr-reference` (§12–§17). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
>    (§1). **No other software has this property.**
> 2. **⚠️ Latency is the master constraint and it is not a performance metric.** Motion-to-
>    photon under ~20 ms is the consensus threshold, and it governs your entire
>    architecture (§1.1).
> 3. **⚠️ Presence is fragile and asymmetric.** It takes sustained correctness to build and
>    one bad frame, one wrong-scale object, one mistracked hand to destroy. **Everything
>    in §9 → `xr-platforms-audio-and-comfort` and §10 → `xr-ux-design-and-performance-budgeting` is about protecting it.**

---

## §0. Routing

| You want... | Go to |
|---|---|
| **The perceptual constraints** | **§1** |
| Displays and optics | §2 |
| **Tracking** | **§3** |
| **The XR rendering pipeline** | **§4 → `xr-rendering-input-and-spatial-understanding`** |
| Input and interaction | §5 → `xr-rendering-input-and-spatial-understanding` |
| Locomotion | §5.4 → `xr-rendering-input-and-spatial-understanding` |
| **AR spatial understanding** | **§6 → `xr-rendering-input-and-spatial-understanding`** |
| Platforms and APIs | §7 → `xr-platforms-audio-and-comfort` |
| Spatial audio | §8 → `xr-platforms-audio-and-comfort` |
| **Comfort, safety, accessibility** | **§9 → `xr-platforms-audio-and-comfort`** |
| UX design for 3D | §10 → `xr-ux-design-and-performance-budgeting` |
| Performance budgeting | §11 → `xr-ux-design-and-performance-budgeting` |
| Anti-patterns | §12 → `xr-reference` |
| Numbers | §13 → `xr-reference` |
| **The platform landscape** | **§14 → `xr-reference`** |
| Resources | §15 → `xr-reference` |
| Quick reference | §16 → `xr-reference` |

---

## §1. The Perceptual Constraints

**⚠️ Read this section before writing any XR code. Everything else is downstream of it.**

### 1.1 Motion-to-photon latency
**The time from a head movement to the corresponding photons reaching the eye.**
```
sense IMU → fuse → predict → simulate → render → composite → scanout → photons
```
**⚠️ Consensus is the "20 millisecond rule": end-to-end MTP should stay below ~20 ms** to
be generally imperceptible and give a comfortable experience. **Above it, the world feels
attached to your head with elastic**, and ⚠️ **latency is a documented cause of
cybersickness and a documented reducer of presence.**

**⚠️ You cannot hit 20 ms honestly by rendering fast alone** — the pipeline is too long.
**The trick that makes XR viable is prediction plus reprojection** (§4.2 → `xr-rendering-input-and-spatial-understanding`): predict where
the head will be at scanout, and re-warp the finished frame against the newest pose
immediately before display. **⚠️ This means your effective latency is decoupled from your
frame rate — which is why a dropped frame is survivable and a broken reprojection is
not.**

**⚠️ Note the distinction for eye tracking**: gaze-contingent foveated rendering has its
own "eye-motion-to-photon" budget, and it is **more forgiving than head latency** —
measured maximum tolerable system latency for foveated rendering lands in the
**42–91 ms** range depending on foveal region size and the degradation applied, with
artifact detection reportedly unchanged below ~60 ms. ⚠️ **Do not confuse the two budgets;
they differ by roughly 3×.**

### 1.2 Cybersickness
**⚠️ The dominant explanation is sensory conflict**: your eyes report motion your
vestibular system does not. **The documented primary contributors are latency, field of
view, vergence-accommodation mismatch, and unnatural locomotion.**

> **⚠️ GOTCHA — susceptibility varies enormously between people, and developers are the
> worst possible test population.** You acclimate. ⚠️ **Something that feels fine to you
> after six months of daily use can make a first-timer ill in ninety seconds.** **Test
> with fresh users, and take the first ten minutes seriously.**

**Mitigations that have evidence behind them:**
- **⚠️ Hit frame rate consistently.** The single biggest lever.
- **Avoid imposed acceleration** — ⚠️ **the worst offender is camera motion the user did
  not initiate.** Constant velocity is much better than accelerating; instant is better
  still.
- **Dynamic FOV restriction (vignetting) during locomotion** — reduces peripheral optic
  flow, which is what drives vection.
- **⚠️ Rest frames** — a static cockpit, nose reference, or grid gives the vestibular
  system something consistent. **Peripheral teleportation and similar rest-frame designs
  are an active research direction.**
- **Foveated depth-of-field blur and peripheral degradation** — ⚠️ **reduces peripheral
  motion information, and studies indicate a measurable reduction in simulator sickness.**
- **⚠️ Never take control of the camera.** No cutscene head movement, no forced rotation,
  no screen shake.

### 1.3 Vergence-accommodation conflict
**⚠️ The unsolved optical problem of every mainstream headset.**
In natural vision, **vergence** (the eyes rotating to converge on a point) and
**accommodation** (the lens focusing) are coupled and specify the same depth. **In an HMD,
the eyes accommodate to a fixed screen distance while continuing to converge freely** on
virtual objects at varying depths.
**⚠️ The documented consequences**: discomfort and fatigue, cybersickness, longer
time-to-focus, **distorted distance perception, and impaired motor planning and control** —
⚠️ **which matters enormously for surgical training and any task where a few centimetres
of error is serious.**
**Mitigations**: **varifocal** and **multi-focal** displays (⚠️ **prototypes and
research; multi-focal AR prototypes add their own MTP burden**), light fields, and
**the practical one available today — keep interactive content in a comfortable depth
range and avoid forcing rapid depth changes.**

### 1.4 Presence
**The perceptual illusion of being there.** Built by consistent, low-latency, plausible
sensory input; ⚠️ **destroyed instantly by tracking loss, a hand passing through a solid
object, wrong-scale environments, or latency spikes.** **Presence is the product, and
§9 → `xr-platforms-audio-and-comfort` and §10 → `xr-ux-design-and-performance-budgeting` exist to protect it.**

---

## §2. Displays and Optics

**The metrics that matter**, and ⚠️ **note that FOV and PPD trade against each other for a
fixed panel:**
```
FOV                horizontal/vertical, per-eye and combined
⚠️ PPD (pixels per degree)   THE resolution metric — human acuity is ~60 PPD
Refresh rate       72 / 90 / 120 Hz
Persistence        ⚠️ low-persistence illumination (~2 ms) prevents smearing during
                   head motion — a critical and under-appreciated property
IPD                interpupillary distance ⚠️ — wrong IPD causes eye strain and
                   distorts perceived scale
```
**Panel technologies**: LCD, OLED, **micro-OLED / OLED-on-silicon** (⚠️ **the current
high-end standard**), and **MicroLED** in development for brightness and efficiency.

**Optics**: Fresnel (⚠️ **god rays and glare**), **pancake lenses** (⚠️ **thinner and
sharper, at a significant light-efficiency cost — which is why pancake headsets need
brighter panels**), and for AR: **waveguides** (diffractive/reflective — ⚠️ **the only
practical path to glasses form factor, and they cost you FOV, brightness and colour
uniformity**) vs **birdbath** (better image, bulkier).

**⚠️ Optical distortion correction is mandatory and it is not free**: lenses distort, so
you render and then apply an inverse barrel distortion, **with per-channel correction for
chromatic aberration.** ⚠️ **This is why you never render at exactly display resolution —
distortion resampling means the source must be supersampled to avoid losing detail in the
centre.**

**AR display modes**: **optical see-through** (⚠️ **you cannot render black — additive
only, so occlusion of real objects is physically impossible**) vs **video passthrough**
(⚠️ **full control and true occlusion, but the passthrough camera's own latency now sits
in the user's view of the real world**).

---

## §3. Tracking

**3DoF** (rotation only) vs **6DoF** (rotation + position). ⚠️ **3DoF for seated video;
anything interactive needs 6DoF.**

**Approaches**: **outside-in** (external base stations — ⚠️ **highly accurate, fixed
volume, setup burden**) vs **inside-out** (on-headset cameras running SLAM — ⚠️ **the
consumer standard; no setup, but it fails in the conditions SLAM fails in**).

**⚠️ The sensor fusion is the whole trick**: an **IMU** gives you angular rate and
acceleration at ~1000 Hz with **very low latency but unbounded drift** (double-integrating
accelerometer noise diverges fast). **Cameras give you drift-free absolute pose at 30–60 Hz
with high latency.** **Fusing them — typically an EKF or a factor graph — gives you both**,
and this is exactly the VIO problem from a computer-vision reference.

**⚠️ Prediction is mandatory** (§1.1): you must render for where the head *will* be.
**Prediction error shows up as swimming or overshoot on rapid head turns** — and ⚠️ **it's
worse the longer your pipeline, which is another reason to keep it short.**

**⚠️ Where inside-out tracking actually fails** — design for these, don't hope:
featureless white walls, ⚠️ **low light**, **highly repetitive texture** (patterned
carpet, brick), **mirrors and large glass**, ⚠️ **moving environments — a train, a car, a
boat, where the visual world and the vestibular world genuinely disagree**, and rapid
motion causing blur. **Detect tracking degradation and degrade gracefully rather than
letting the world lurch.**

**Controller tracking**: constellation IR + IMU, or ⚠️ **camera-visible controllers,
which lose tracking behind the body or out of the camera frustum — hence the IMU dead
reckoning that briefly covers the gap.**
