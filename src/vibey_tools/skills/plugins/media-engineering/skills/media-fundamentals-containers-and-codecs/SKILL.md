---
name: media-fundamentals-containers-and-codecs
description: "Use when choosing a format or debugging a file that will not play: the fundamentals of digital media (sample rates, bit depth, frame rates, chroma subsampling, colour spaces), containers and muxing (MP4, MKV, MXF, fragmented MP4, timestamps and track layout), and codecs — the audio family, the 2026 video landscape (H.264, HEVC, AV1, VVC) with its licensing and hardware-support realities, and the encoding knobs that actually matter. Includes the router for the whole media-engineering reference."
---

# Media Engineering: Fundamentals, Containers and Muxing, and Codecs

> **Part 1 of 5** of the *Media Engineering* reference (plugin `media-engineering`), covering §0–§3. Sibling skills: `media-production-and-loudness` (§4–§6), `media-transcoding-streaming-and-drm` (§7–§9), `media-captions-podcasts-rights-and-qc` (§10–§14), `media-reference` (§15–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
>    of them (§3, §8 → `media-transcoding-streaming-and-drm`).
> 2. **Every media decision is a triangle: quality, bitrate, and compute.** ⚠️ **You pick
>    two.** A better codec moves the triangle; it doesn't abolish it — **and encoding
>    complexity is the price AV1 and VVC charge for their bitrate savings** (§3.2).
> 3. **⚠️ The rights layer is now as load-bearing as the technical one**, and it's moving
>    faster. Loudness normalization, content ID, licensing metadata, and the AI training
>    fight all determine what you may ship, not just what you can encode (§12 → `media-captions-podcasts-rights-and-qc`, §13 → `media-captions-podcasts-rights-and-qc`).

---

## §0. Routing

| Asked about... | Go to |
|---|---|
| Digital media fundamentals | §1 |
| Containers, wrappers, muxing | §2 |
| **Codecs — choosing and the 2026 landscape** | **§3** |
| Audio production: DAWs, plugins, MIDI | §4 → `media-production-and-loudness` |
| Video production, colour, timecode | §5 → `media-production-and-loudness` |
| **Loudness — why your audio is quiet** | **§6 → `media-production-and-loudness`** |
| Transcoding and packaging pipelines | §7 → `media-transcoding-streaming-and-drm` |
| **Streaming delivery and latency** | **§8 → `media-transcoding-streaming-and-drm`** |
| DRM and content protection | §9 → `media-transcoding-streaming-and-drm` |
| Captions, subtitles, accessibility | §10 → `media-captions-podcasts-rights-and-qc` |
| Podcast infrastructure | §11 → `media-captions-podcasts-rights-and-qc` |
| Metadata, identifiers, rights | §12 → `media-captions-podcasts-rights-and-qc` |
| **AI generation and the licensing fight** | **§13 → `media-captions-podcasts-rights-and-qc`** |
| Testing and QC | §14 → `media-captions-podcasts-rights-and-qc` |
| "Don't do this" | §15 → `media-reference` |
| "Which side is right?" | §16 → `media-reference` |
| "Is this still current?" | §17 → `media-reference` |
| Books, tools, people | §18 → `media-reference` |

---

## §1. Fundamentals

**[DURABLE] The numbers that constrain everything downstream.**

**Audio**: **44.1 kHz** (CD, historical), **48 kHz** (⚠️ **the video and broadcast
standard — use this unless you have a reason not to**), 96/192 kHz in production.
**16-bit** for delivery, **24-bit or 32-bit float** for production (⚠️ **32-bit float
effectively eliminates clipping during recording, which is why modern field recorders use
it**). **Channel layouts**: mono, stereo, 5.1, 7.1, and object-based (Dolby Atmos,
which stores objects plus a bed rather than fixed channels).

**Video**: **frame rates** — 23.976, 24, 25, 29.97, 30, 50, 59.94, 60, 120.
⚠️ **The .976 and .97 rates are NTSC colour-subcarrier artifacts from 1953 and they are
still ruining timecode arithmetic today** (§5.3 → `media-production-and-loudness`). **Resolutions**: 1920×1080, 3840×2160
(UHD), 4096×2160 (DCI 4K — ⚠️ **not the same as UHD, and conflating them is a common
error**). **Chroma subsampling**: 4:4:4 (full), 4:2:2 (broadcast/production), **4:2:0**
(⚠️ **delivery standard — half the chroma resolution in both directions, and the reason
saturated red text looks bad in compressed video**). **Bit depth**: 8-bit (⚠️ **visible
banding in gradients**), 10-bit (HDR minimum), 12-bit.

**⚠️ Interlacing** is a 1930s bandwidth hack that will not die: 1080i is 1920×1080 in two
fields of 540 lines. **Deinterlacing is lossy and the artifacts are distinctive.** Progressive
everywhere you can.

**Colour**: **Rec. 709** (HD), **Rec. 2020** (UHD container), **DCI-P3**, **sRGB**.
**Transfer functions**: gamma for SDR, **PQ (SMPTE ST 2084)** and **HLG** for HDR.
**HDR formats**: HDR10 (static metadata), **HDR10+** and **Dolby Vision** (dynamic,
per-scene), HLG (broadcast-friendly, backwards-compatible-ish).

---

## §2. Containers and Muxing

**[DURABLE] The container is not the codec, and conflating them causes endless confusion.**
An `.mp4` can contain H.264, HEVC, AV1, AAC, or Opus. **"MP4 doesn't play" is almost never
about MP4.**

| Container | Use | ⚠️ Notes |
|---|---|---|
| **MP4 / ISOBMFF** | Universal delivery | The base for CMAF and fMP4 (§7 → `media-transcoding-streaming-and-drm`) |
| **fMP4 / CMAF** | ⚠️ **Streaming — the convergence format** | One set of segments serves both HLS and DASH |
| **MPEG-TS** | Broadcast, legacy HLS | Higher overhead; robust to corruption |
| **MKV / WebM** | Open, flexible | WebM is a Matroska subset |
| **MOV** | Apple production | ProRes lives here |
| **MXF** | Broadcast mastering | ⚠️ **Notoriously many incompatible flavours** |
| **WAV / AIFF** | Uncompressed audio | ⚠️ **WAV is 4 GB-limited unless RF64/BW64** |
| **FLAC / ALAC** | Lossless audio | |
| **Ogg** | Vorbis, Opus, Theora | |

**⚠️ The muxing details that bite**: **timestamps** — PTS (presentation) vs DTS (decode),
which differ whenever B-frames exist; **timescales** and rounding drift; **edit lists**
(⚠️ **an mp4 edit list can offset playback and many tools ignore it, producing A/V sync
differences between players**); **`moov` atom placement** — ⚠️ **at the end means the file
won't start playing until fully downloaded; `faststart` moves it to the front**, and this
is the single most common "why won't my MP4 stream" cause; and **sample entry codes** —
`avc1` vs `avc3`, `hvc1` vs `hev1` (⚠️ **the difference is whether parameter sets are in
the decoder config or inline, and Safari/FairPlay requires the former** — a real
interoperability trap).

---

## §3. Codecs

### 3.1 Audio

| Codec | Position |
|---|---|
| **AAC** (LC, HE-AAC) | ⚠️ **The compatibility baseline. Everything plays it** |
| **Opus** | ⚠️ **Technically the best general-purpose choice** — speech to music, 6 kb/s to transparent; mandatory in WebRTC. Weaker in Apple/broadcast ecosystems |
| **MP3** | Legacy, universal, patents expired |
| **FLAC / ALAC** | Lossless distribution |
| **Dolby AC-3 / E-AC-3 / AC-4** | Broadcast and streaming surround |
| **Dolby Atmos / MPEG-H** | Object-based immersive |

### 3.2 ⚠️ Video — the 2026 landscape

**[VERSIONED, and this is where the most changed.]**

| Codec | Efficiency vs H.264 | Status |
|---|---|---|
| **H.264 / AVC** | baseline | ⚠️ **Still the compatibility floor. Everything decodes it** |
| **VP9** | ~HEVC-ish | Google-ecosystem; central to YouTube, limited elsewhere |
| **HEVC / H.265** | ~50% better | ⚠️ **Mature production footprint; Apple's preference; patent-pool complexity** |
| **AV1** | ~50%+, ~15% over HEVC | ⚠️ **Royalty-free, and now the preferred next-gen OTT codec** |
| **VVC / H.266** | ~50% over HEVC | Technically superb; ⚠️ **almost no hardware footprint** |
| **AV2** | ~30% over AV1 | ⚠️ **v1.0 released 2026. Royalty-free** |

**⚠️ The adoption reality is not the efficiency table.** A 2026 encoding survey found
**HEVC in production at ~65% of responding organizations (another 20% planning), against
AV1 at ~17% in production with ~40% planning deployment during 2026** — ⚠️ **note these are
not market-share figures, planned deployments aren't launches, and the survey was
distributed through an encoding-hardware vendor's channels, so it likely over-represents
organizations already evaluating encoders.** The pattern is still informative: **HEVC has
the mature footprint, AV1 has the momentum.**

> **⚠️ GOTCHA — VVC is the cautionary tale, and the lesson generalizes.** VVC is
> technically the strongest codec available: **~50% better than HEVC**, finalized July 2020.
> But as of 2026 its **hardware decode footprint is roughly 5% of consumer devices** —
> a few high-end TVs and set-top boxes, **no shipping mobile silicon, no browser support** —
> against AV1's broad presence. And **many essential patent holders remain outside both
> licensing pools**, leaving the royalty position unresolved.
>
> **Android 17 added native VVC support on devices with compatible hardware decoders** —
> ⚠️ **but that's exposing hardware decode that may exist, not shipping a software player,
> and Google is otherwise firmly in the AV1/AV2 camp.**
>
> **The likely equilibrium through the late 2020s: AV1 rules web streaming, HEVC remains
> the workhorse for device capture and Apple workflows, and VVC finds a professional and
> broadcast niche rather than mainstream ubiquity.** ⚠️ **A reminder that the best
> technology doesn't always win — the economics favoured a free competitor.**

**[VERSIONED] AV2 arrived**: AOMedia released **AV2 v1.0 in 2026**, ~30% better compression
than AV1, still royalty-free, with the **dav2d** decoder project filling the
implementation gap. ⚠️ **It introduces ML-assisted coding tools — a structural shift in
codec design philosophy — and targets AV1's weak spots: real-time workloads, AR/VR,
split-screen, and screen content.** **Devices are expected from 2026 with broader adoption
2027–28**, so treat it as a roadmap item, not a deployment decision.

**⚠️ And the AV1 caveat worth knowing**: it works extremely well for VOD and archival;
**for real-time workloads the computational overhead is still problematic.**

**[DURABLE] The practical answer is multi-codec delivery.** Encode H.264 as the floor, add
HEVC and/or AV1 for capable devices, and let the manifest and device capabilities decide.
**⚠️ You will be running at least two codecs for years.**

### 3.3 The encoding knobs that matter
**CRF/CQ vs. bitrate targeting** (⚠️ **CRF for VOD where you want consistent quality;
capped-CRF for streaming**), **preset** (⚠️ **the direct compute-vs-efficiency dial**),
**GOP length and keyframe placement** (⚠️ **must align with your segment duration or ABR
switching breaks** — §7 → `media-transcoding-streaming-and-drm`), **B-frames**, **two-pass vs. single-pass**, and
**per-title/per-shot encoding** — ⚠️ **which Netflix popularized and which yields real
savings because an animation and a sports broadcast need very different bitrates for the
same perceived quality.**
