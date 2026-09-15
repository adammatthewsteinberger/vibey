---
name: media-production-and-loudness
description: "Use when working on the production side: audio production (DAWs, plugin formats such as VST3, AU and AAX, latency and buffer sizes, sample-accurate automation), video production (NLEs, intermediate codecs, colour management, timecode and sync, frame-rate pulldown), and loudness — LUFS, true peak, the broadcast standards, and why a mix that sounds right in the studio is quiet on streaming platforms."
---

# Media Engineering: Audio Production, Video Production, and Loudness

> **Part 2 of 5** of the *Media Engineering* reference (plugin `media-engineering`), covering §4–§6. Sibling skills: `media-fundamentals-containers-and-codecs` (§0–§3), `media-transcoding-streaming-and-drm` (§7–§9), `media-captions-podcasts-rights-and-qc` (§10–§14), `media-reference` (§15–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Verified August 2026. See §17 → `media-reference` for the currency snapshot and what goes stale first.

> **How to read this.** Reference for engineers building media systems — deliberately
> distinct from a DSP reference (which covers the algorithms) and a smart-TV reference
> (which covers app platforms). **This is the production, packaging and delivery stack.**
>
> Three markers:
> - **[DURABLE]** — formats, workflow structure, and the physical and perceptual
>   constraints. Most of this document.
> - **[VERSIONED]** — codecs, protocols, platforms, rights. ⚠️ **Verify.**
> - **[CONTESTED]** — genuine disagreement.
>
> **⚠️ GOTCHA** boxes mark where media pipelines silently corrupt, desync, or get rejected.
>
> **The three framings that organize everything below:**
> 1. **⚠️ Media is a compatibility problem wearing a compression costume.** The hard part
>    is almost never the codec — it's that **every device, browser, and platform accepts a
>    different subset of a different container with different DRM**, and you must serve all
>    of them (§3 → `media-fundamentals-containers-and-codecs`, §8 → `media-transcoding-streaming-and-drm`).
> 2. **Every media decision is a triangle: quality, bitrate, and compute.** ⚠️ **You pick
>    two.** A better codec moves the triangle; it doesn't abolish it — **and encoding
>    complexity is the price AV1 and VVC charge for their bitrate savings** (§3.2 → `media-fundamentals-containers-and-codecs`).
> 3. **⚠️ The rights layer is now as load-bearing as the technical one**, and it's moving
>    faster. Loudness normalization, content ID, licensing metadata, and the AI training
>    fight all determine what you may ship, not just what you can encode (§12 → `media-captions-podcasts-rights-and-qc`, §13 → `media-captions-podcasts-rights-and-qc`).

---

## §4. Audio Production

**[DURABLE] The stack an audio engineer actually uses, and what a software engineer needs
to know to integrate with it.**

**DAWs**: Pro Tools (⚠️ **still the post-production and studio standard**), Logic, Ableton
Live, Reaper (⚠️ **cheap, scriptable, and beloved by engineers**), Cubase, FL Studio,
Studio One, Bitwig.

**Plugin formats** — ⚠️ **the interop layer, and a real engineering concern**:
**VST3** (cross-platform, Steinberg), **AU / AUv3** (Apple), **AAX** (Pro Tools only),
**LV2** (Linux/open), and **CLAP** — ⚠️ **the newer open format (Bitwig/u-he) with better
threading, modulation and note expression, gaining real traction.** **JUCE** is the
dominant framework for writing plugins across all of them.

**⚠️ The real-time constraint governs everything**: the audio callback is a hard real-time
thread. **No allocation, no locks, no file I/O, no logging.** Buffer size sets latency
(⚠️ **64 samples at 48 kHz ≈ 1.3 ms; 512 ≈ 10.7 ms**) and trades against CPU. **Lock-free
ring buffers** to talk to the UI thread.

**MIDI**: 7-bit values, note on/off, CC, and the ⚠️ **note-off-vs-velocity-zero
ambiguity**. **MIDI 2.0** adds 32-bit resolution, per-note controllers, and
bidirectional negotiation — ⚠️ **adoption is real but slow, and MIDI 1.0 remains the
lingua franca.** **MPE** gives per-note pitch and pressure over MIDI 1.0 and is widely
supported.

**Audio interfaces and drivers**: **ASIO** (Windows, low-latency, ⚠️ **and the reason
WDM/DirectSound is unusable for production**), **Core Audio** (macOS, excellent),
**ALSA/JACK/PipeWire** (Linux — ⚠️ **PipeWire has largely resolved the historic
JACK/PulseAudio split**). **Network audio**: **Dante** (⚠️ **the professional standard**),
AES67, AVB, NDI for video-plus-audio over IP.

---

## §5. Video Production

**5.1 Acquisition and intermediates.** **Camera formats**: ProRes (⚠️ **the post-production
standard — cheap to decode, expensive in storage**), DNxHD/HR, **RAW** (BRAW, R3D, ARRIRAW
— ⚠️ **maximum flexibility, enormous files, and debayering cost**), and long-GOP camera
codecs (⚠️ **H.264/HEVC from a camera is painful to edit — transcode to an intermediate
first**). **Proxies** are standard practice: edit at low resolution, conform to full
resolution at the end.

**5.2 Colour.** **Log formats** (S-Log, C-Log, V-Log, Log C) preserve dynamic range for
grading. **LUTs** for transforms — ⚠️ **and a 1D LUT cannot do what a 3D LUT does; using
the wrong kind silently misgrades**. **ACES** is the standardized colour-managed pipeline.
⚠️ **The recurring bug: mismatched colour space or transfer function between stages,
producing washed-out or oversaturated output that looks like a grading choice rather
than an error.**

**5.3 ⚠️ Timecode — the most common source of "off by a few frames"**
**SMPTE timecode**, and the killer detail: **drop-frame vs non-drop-frame.**
At 29.97 fps, ⚠️ **drop-frame timecode skips frame *numbers* (never actual frames) to keep
clock time accurate — 2 numbers per minute, except every tenth minute.** Non-drop counts
sequentially and drifts ~3.6 seconds per hour against wall clock.
**⚠️ Mixing them, or assuming 30 fps arithmetic on 29.97 material, is the classic sync
error.** **Genlock and word clock** keep devices frame- and sample-aligned in a facility.

**5.4 Editing and delivery.** NLEs: Premiere, Final Cut, DaVinci Resolve (⚠️ **which
absorbed colour grading and audio into one application and changed the market**), Avid
Media Composer (broadcast/film standard). **Interchange**: EDL, AAF, XML, **OTIO**
(⚠️ **OpenTimelineIO — the open, scriptable interchange format, and the one worth knowing
if you're building tooling**). **Deliverables**: IMF for studio distribution, DCP for
cinema, and **broadcast spec sheets that will reject your file for reasons you did not
anticipate** (§14 → `media-captions-podcasts-rights-and-qc`).

---

## §6. Loudness

**[DURABLE] The single most practically useful section for anyone shipping audio, and the
one most often discovered too late.**

**⚠️ Peak level and perceived loudness are different things.** A track can peak at 0 dBFS
and sound quiet, or peak at −6 and sound crushed. **The loudness war** — decades of
ever-heavier compression to sound louder than the competition — **was ended not by taste
but by normalization.**

**The standards**: **ITU-R BS.1770** defines the measurement (K-weighted, gated).
**EBU R128** (Europe) targets **−23 LUFS integrated** with a max true peak of −1 dBTP;
**ATSC A/85** (US broadcast) targets **−24 LKFS**. ⚠️ **LUFS and LKFS are the same unit
with different names.**

**⚠️ The units to keep straight**: **Integrated LUFS** (whole-programme average),
**short-term** (3 s), **momentary** (400 ms), **LRA** (loudness range),
and **True Peak (dBTP)** — ⚠️ **which measures the inter-sample peaks that appear after
D/A conversion or lossy encoding, and is why a file that peaks at exactly 0 dBFS can clip
on playback.** Leave −1 dBTP of headroom minimum.

> **⚠️ GOTCHA — this is why your master sounds quiet on streaming.** **Every major platform
> normalizes playback loudness**, typically in the region of **−14 LUFS**, though **targets
> differ by platform and change without announcement.** If you master to −8 LUFS, the
> platform **turns it down** — and you've spent your dynamic range for nothing, arriving
> quieter *and* more crushed than a competitor who mastered sensibly.
>
> ⚠️ **Do not master to a platform target as a hard number.** Master for the music, keep
> true peak headroom, and check the integrated value. **Verify current targets per platform
> at release time rather than trusting any figure — including the one in this document.**
