---
name: xr-reference
description: "Use when checking an XR anti-pattern, looking up a latency, frame rate, field-of-view or resolution number, checking the platform landscape (the three-platform picture and the OpenXR and WebXR position, verified August 2026), finding resources, or needing a picker and a ship checklist. Companion to the other vr-ar-development skills."
---

# VR and AR Development: Anti-Patterns, Numbers, the Platform Landscape, and Resources

> **Part 5 of 5** of the *VR and AR Development* reference (plugin `vr-ar-development`), covering §12–§17. Sibling skills: `xr-perceptual-constraints-displays-and-tracking` (§0–§3), `xr-rendering-input-and-spatial-understanding` (§4–§6), `xr-platforms-audio-and-comfort` (§7–§9), `xr-ux-design-and-performance-budgeting` (§10–§11). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** The perceptual constraints are human physiology and permanent; the platform and hardware landscape moves fast. See §14 below for the current picture.

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

## §12. Anti-Patterns

| Anti-pattern | Why |
|---|---|
| Testing comfort only on yourself | ⚠️ **You acclimated. Fresh users are the test** (§1.2 → `xr-perceptual-constraints-displays-and-tracking`) |
| Taking camera control from the user | ⚠️ **Reliable nausea** (§1.2 → `xr-perceptual-constraints-displays-and-tracking`, §10 → `xr-ux-design-and-performance-budgeting`) |
| Smooth locomotion with no comfort options | First-session sickness (§5.4 → `xr-rendering-input-and-spatial-understanding`) |
| Smooth turning as the default | ⚠️ **Yaw rotation is the worst axis. Snap turn** (§5.4 → `xr-rendering-input-and-spatial-understanding`) |
| Relying on ASW/reprojection to hit frame rate | ⚠️ **It's a safety net, not a budget** (§4.2 → `xr-rendering-input-and-spatial-understanding`) |
| Frame rate as the thing you sacrifice | ⚠️ **Drop render scale instead** (§11 → `xr-ux-design-and-performance-budgeting`) |
| Profiling for 20 seconds on a mobile SoC | Thermal throttling changes everything (§11 → `xr-ux-design-and-performance-budgeting`) |
| Optimizing to average frame time | ⚠️ **A 1% spike is a visible hitch** (§11 → `xr-ux-design-and-performance-budgeting`) |
| Rendering the scene twice, naively | Single-pass/multiview exists (§4.1 → `xr-rendering-input-and-spatial-understanding`) |
| TAA in XR | ⚠️ **Ghosting is far worse in stereo. Prefer MSAA** (§4.4 → `xr-rendering-input-and-spatial-understanding`) |
| Rendering at exactly display resolution | ⚠️ **Distortion resampling eats centre detail** (§2 → `xr-perceptual-constraints-displays-and-tracking`, §4.4 → `xr-rendering-input-and-spatial-understanding`) |
| Head-locked UI panels | Uncomfortable, breaks presence (§10 → `xr-ux-design-and-performance-budgeting`) |
| Desktop-sized text | ⚠️ **PPD is not monitor PPI. Test on device** (§10 → `xr-ux-design-and-performance-budgeting`) |
| Content anchored to world origin in AR | ⚠️ **Origin drifts as SLAM refines. Use anchors** (§6 → `xr-rendering-input-and-spatial-understanding`) |
| Shipping AR without occlusion or contact shadows | ⚠️ **Objects float; the illusion never forms** (§6 → `xr-rendering-input-and-spatial-understanding`) |
| Expecting real-world occlusion on optical see-through | ⚠️ **Physically impossible — additive light only** (§2 → `xr-perceptual-constraints-displays-and-tracking`) |
| Untracked audio | Destroys presence instantly (§8 → `xr-platforms-audio-and-comfort`) |
| Complex hand gestures as core input | ⚠️ **Pinch is reliable; little else is** (§5 → `xr-rendering-input-and-spatial-understanding`) |
| Interaction requiring extended arms | ⚠️ **Gorilla arm within minutes** (§5.3 → `xr-rendering-input-and-spatial-understanding`) |
| Depth as the only channel for critical info | Not everyone fuses stereo (§9 → `xr-platforms-audio-and-comfort`) |
| No boundary/guardian consideration | People hit walls and each other (§9 → `xr-platforms-audio-and-comfort`) |
| Assuming inside-out tracking always works | ⚠️ **Mirrors, low light, moving vehicles** (§3 → `xr-perceptual-constraints-displays-and-tracking`) |
| Single-platform native SDK for a multi-platform product | ⚠️ **OpenXR exists for this** (§7 → `xr-platforms-audio-and-comfort`) |
| Treating eye-tracking data casually | It's biometric (§5 → `xr-rendering-input-and-spatial-understanding`) |

---

## §13. Numbers

```
LATENCY  ⚠️ THE CONSTRAINT
Motion-to-photon target      <20 ms  ⚠️ the consensus rule
Gaze-to-photon (foveation)   42–91 ms tolerable; artifacts unchanged under ~60 ms
                             ⚠️ a different, looser budget than head MTP

FRAME BUDGET
72 Hz → 13.9 ms · 90 Hz → 11.1 ms · 120 Hz → 8.3 ms   ⚠️ for BOTH eyes
Low persistence illumination ~2 ms

OPTICS
⚠️ Human acuity ~60 PPD (the "retinal" target)
Render target typically 1.2–1.4× display resolution (distortion headroom)
IPD range ~54–72 mm typical adult

SENSORS
IMU ~1000 Hz, low latency, ⚠️ unbounded drift
Camera/SLAM 30–60 Hz, drift-free, ⚠️ high latency
→ fuse for both (§3)

UX
Comfortable content depth ~0.5–20 m · reading sweet spot ~1–3 m
Primary content within ~±30° of forward gaze
⚠️ Looking up is worse than looking down
```

---

## §14. The Platform Landscape — verified August 2026

> **⚠️ GOTCHA — this section decays fastest in the document, and the sourcing is weaker
> than the rest.** Much of what follows comes from **XR trade press, vendor blogs, and
> development agencies marketing their services.** ⚠️ **The structural picture is
> corroborated across sources; specific prices, percentages and roadmap dates are not
> measurements. Verify before making a platform commitment.** **§1–§11 → `xr-perceptual-constraints-displays-and-tracking`, `xr-rendering-input-and-spatial-understanding`, `xr-platforms-audio-and-comfort`, `xr-ux-design-and-performance-budgeting` do not depend on
> any of it.**

### 14.1 The three-platform picture
**⚠️ The consistent framing across sources is that platform choice follows use case, not
quality:**
- **Meta Quest** — ⚠️ **the installed base and mature catalogue; the default for scale and
  lowest per-seat cost.** One trade study found **Meta or Quest referenced in 38% of XR
  stories over a four-month 2026 window, more than the next two companies combined.**
  ⚠️ **Horizon OS still favours Meta's own hardware and store, though it does support
  OpenXR.**
- **Apple Vision Pro / visionOS** — ⚠️ **vertically integrated, premium fidelity; the pick
  for visualization, design review and executive demos.** ⚠️ **Coverage in 2026 has been
  substantially retreat-flavoured** — a reduced headset roadmap and cancelled products
  are reported, alongside a 2025 refresh with an upgraded processor and improved
  headstrap.
- **Android XR** (Google + Samsung + Qualcomm) — ⚠️ **the fastest-rising, and reported as
  the #2 platform by coverage share.** Runs standard Android apps, **supports Unity 6,
  OpenXR 1.1 and WebXR**, with **Samsung Galaxy XR** shipping and **XREAL** glasses in the
  ecosystem. **The explicit strategy is the Android playbook applied to XR.**

**Also**: **Valve's Steam Frame** announced, **PICO** (Project Swan flagship indicated for
late 2026), **Varjo** for high-end enterprise/simulation, **HoloLens 2 in maintenance
mode** with enterprise hardware like **HMS SiNGRAY G2** positioned for that gap.
⚠️ **And the sector is volatile — one source notes four VR studios closing within a single
week in 2026.**

**⚠️ Smart glasses are the growth story, not headsets**: reported at **42% of XR coverage**,
with Meta's Ray-Ban line including a display model. **Displays are OLED-on-silicon
near-term with MicroLED in development.**

### 14.2 ⚠️ The genuinely actionable finding — OpenXR and WebXR
**This is the part I'd act on regardless of how the hardware race resolves.**
- **⚠️ OpenXR is the hedge.** Applications built against it run on any conformant headset
  unmodified; **Unity and Unreal both recommend it; Android XR supports OpenXR 1.1, which
  means the same rendering pipeline reaches Quest.** ⚠️ **A multi-platform program is
  increasingly the realistic answer, which is exactly the argument for an OpenXR-based,
  engine-portable strategy now.**
- **WebXR adoption reportedly grew 40% in 2026**, with **Interop 2026 proposing WebXR as a
  focus area** — meaning browser vendors coordinating to close compatibility gaps.
  ⚠️ **One codebase across Quest, Vision Pro, Galaxy XR and phone browsers is a real
  proposition now**, with the usual web trade-offs in performance and device access.

---

## §15. Resources

| Source | Why |
|---|---|
| **LaValle, *Virtual Reality*** | ⚠️ **Free online, rigorous, the best foundation — perception, geometry, tracking** |
| **Jerald, *The VR Book: Human-Centered Design for VR*** | ⚠️ **§1 → `xr-perceptual-constraints-displays-and-tracking`, §9 → `xr-platforms-audio-and-comfort` and §10 → `xr-ux-design-and-performance-budgeting` in depth** |
| **Schmalstieg & Höllerer, *Augmented Reality: Principles and Practice*** | The AR reference |
| **Oculus/Meta Developer "Best Practices"** | ⚠️ **Hard-won comfort guidance; still the practical baseline** |
| **Apple HIG for visionOS** | ⚠️ **Excellent 3D interaction design thinking, platform-independent value** |
| **Khronos OpenXR specification** | §7 → `xr-platforms-audio-and-comfort` |
| **Abrash's blog and talks** | ⚠️ **The clearest writing on why XR is perceptually hard** |
| **Albert et al., "Latency requirements for foveated rendering in VR"** | §1.1 → `xr-perceptual-constraints-displays-and-tracking`'s gaze budget |
| **IEEE VR / ISMAR / CHI proceedings** | Where the comfort research lives |

---

## §16. Quick Reference

### 16.1 Picker
| Need | Use |
|---|---|
| Multi-platform target | ⚠️ **OpenXR + Unity or Unreal** (§7 → `xr-platforms-audio-and-comfort`, §14.2) |
| Widest reach, one codebase, lowest cost | **WebXR** (§14.2) |
| Comfortable locomotion | ⚠️ **Teleport + snap turn as defaults** (§5.4 → `xr-rendering-input-and-spatial-understanding`) |
| Precise interaction | **Controllers** — don't default to hands (§5 → `xr-rendering-input-and-spatial-understanding`) |
| Low-fatigue interaction | ⚠️ **Gaze + pinch; hands near the body** (§5.3 → `xr-rendering-input-and-spatial-understanding`) |
| Free GPU headroom | ⚠️ **Fixed foveated rendering** (§4.3 → `xr-rendering-input-and-spatial-understanding`) |
| Halve CPU draw overhead | **Single-pass/multiview stereo** (§4.1 → `xr-rendering-input-and-spatial-understanding`) |
| Antialiasing in XR | ⚠️ **MSAA, not TAA** (§4.4 → `xr-rendering-input-and-spatial-understanding`) |
| AR content that stays put | ⚠️ **Anchors, never world coordinates** (§6 → `xr-rendering-input-and-spatial-understanding`) |
| Make AR objects look real | ⚠️ **Occlusion + contact shadows** (§6 → `xr-rendering-input-and-spatial-understanding`) |
| Presence per unit effort | ⚠️ **Head-tracked spatial audio** (§8 → `xr-platforms-audio-and-comfort`) |

### 16.2 Ship checklist
- [ ] Native frame rate hit without relying on reprojection? (§4.2 → `xr-rendering-input-and-spatial-understanding`)
- [ ] Frame-time histogram clean — no 1% spikes? (§11 → `xr-ux-design-and-performance-budgeting`)
- [ ] Profiled on device, thermally soaked 20+ minutes? (§11 → `xr-ux-design-and-performance-budgeting`)
- [ ] Tested with users who have never used XR? (§1.2 → `xr-perceptual-constraints-displays-and-tracking`)
- [ ] Comfort options: vignette, snap turn, teleport, seated mode, height? (§9 → `xr-platforms-audio-and-comfort`)
- [ ] Camera never moves without user input? (§1.2 → `xr-perceptual-constraints-displays-and-tracking`, §10 → `xr-ux-design-and-performance-budgeting`)
- [ ] Text legible on device, not just in the editor? (§10 → `xr-ux-design-and-performance-budgeting`)
- [ ] UI body-locked or diegetic, not head-locked? (§10 → `xr-ux-design-and-performance-budgeting`)
- [ ] Audio head-tracked? (§8 → `xr-platforms-audio-and-comfort`)
- [ ] Tracking-loss and relocalization failure handled gracefully? (§3 → `xr-perceptual-constraints-displays-and-tracking`, §6 → `xr-rendering-input-and-spatial-understanding`)
- [ ] AR: anchors used, occlusion and contact shadows present? (§6 → `xr-rendering-input-and-spatial-understanding`)
- [ ] Accessibility: seated, one-handed, subtitles, non-stereo fallback? (§9 → `xr-platforms-audio-and-comfort`)
- [ ] Guardian/boundary interaction sane? (§9 → `xr-platforms-audio-and-comfort`)

---

## §17. Method

**§1–§11 → `xr-perceptual-constraints-displays-and-tracking`, `xr-rendering-input-and-spatial-understanding`, `xr-platforms-audio-and-comfort`, `xr-ux-design-and-performance-budgeting` rest on perceptual research and stable engineering practice** — **LaValle**,
**Jerald**, the platform best-practice documents, and the IEEE VR / ISMAR literature.
⚠️ **Human physiology does not version, which is why §1 → `xr-perceptual-constraints-displays-and-tracking` is the most durable part of this
document and the part I'd read first.**

**Scoped to complement**: rasterization, PBR and the rendering equation sit in a graphics
reference; SLAM, VIO and multi-view geometry in a computer-vision reference. ⚠️ **§3 → `xr-perceptual-constraints-displays-and-tracking` and
§6 → `xr-rendering-input-and-spatial-understanding` deliberately point at those rather than restating them.**

**Two searches were run in August 2026**: **the platform and hardware landscape**, and
**the perceptual thresholds** (motion-to-photon, cybersickness factors, VAC, foveated
rendering latency).

**Confidence.** **High** in §1 → `xr-perceptual-constraints-displays-and-tracking` — the 20 ms MTP consensus, the four primary cybersickness
contributors, the VAC consequence list, and the 42–91 ms foveated-rendering latency
tolerance all come from **peer-reviewed sources and are consistent across them.**
⚠️ **The §1.1 → `xr-perceptual-constraints-displays-and-tracking` point that gaze latency and head latency are different budgets by roughly 3×
is worth internalizing and is frequently conflated in practitioner writing.**
**High** in §2–§11 → `xr-perceptual-constraints-displays-and-tracking`, `xr-rendering-input-and-spatial-understanding`, `xr-platforms-audio-and-comfort`, `xr-ux-design-and-performance-budgeting`, which are established practice.

⚠️ **§14 is explicitly the weak section and is flagged as such in place.** The sourcing is
**XR trade press, vendor blogs, and development agencies who sell XR services** — several
of the comparison articles returned are marketing for consultancies. **The structural
claims are corroborated across independent sources** (OpenXR as the portability layer;
Android XR rising; Quest holding installed-base advantage; smart glasses growing faster
than headsets). ⚠️ **The specific figures — the 40% WebXR growth, the 38% coverage share,
the 15–25% PolySpatial overhead, prices and roadmap dates — are single-source or
vendor-adjacent, and I have attributed rather than asserted them.** **Verify before
committing budget.**

**§14.2 is the part I'd act on**: ⚠️ **the OpenXR argument holds regardless of which
hardware vendor wins, which is precisely what makes it the safe architectural bet.**
