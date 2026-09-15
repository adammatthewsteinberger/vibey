---
name: media-reference
description: "Use when checking a media anti-pattern, weighing a contested question, confirming whether a codec, delivery-protocol or AI-rights claim is still current (snapshot verified August 2026), finding the books, specs and communities, or needing the numbers, a format picker, and the when-it-is-broken triage list. Companion to the other media-engineering skills."
---

# Media Engineering: Anti-Patterns, Contested Questions, Currency, and Canon

> **Part 5 of 5** of the *Media Engineering* reference (plugin `media-engineering`), covering §15–§20. Sibling skills: `media-fundamentals-containers-and-codecs` (§0–§3), `media-production-and-loudness` (§4–§6), `media-transcoding-streaming-and-drm` (§7–§9), `media-captions-podcasts-rights-and-qc` (§10–§14). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Verified August 2026. See §17 below for the currency snapshot and what goes stale first.

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

## §15. Anti-Patterns

| Anti-pattern | Why |
|---|---|
| Confusing container with codec | ⚠️ **"MP4 won't play" is almost never about MP4** (§2 → `media-fundamentals-containers-and-codecs`) |
| `moov` atom at the end of a streamed MP4 | ⚠️ **Won't start until fully downloaded. Use faststart** (§2 → `media-fundamentals-containers-and-codecs`) |
| Ignoring `avc1`/`avc3`, `hvc1`/`hev1` distinctions | Safari/FairPlay requires parameter sets in the config (§2 → `media-fundamentals-containers-and-codecs`) |
| Ignoring edit lists | Players disagree → A/V sync differences (§2 → `media-fundamentals-containers-and-codecs`) |
| Assuming DCI 4K and UHD are the same | 4096 vs 3840 (§1 → `media-fundamentals-containers-and-codecs`) |
| 8-bit for HDR or gradient-heavy content | Visible banding (§1 → `media-fundamentals-containers-and-codecs`) |
| Choosing a codec by efficiency table alone | ⚠️ **VVC is best-in-class with ~5% device support** (§3.2 → `media-fundamentals-containers-and-codecs`) |
| Single-codec delivery | You'll be multi-codec for years (§3.2 → `media-fundamentals-containers-and-codecs`) |
| Misaligned keyframes across ABR renditions | ⚠️ **Breaks clean switching** (§7 → `media-transcoding-streaming-and-drm`) |
| Separate TS and fMP4 packaging | CMAF serves both; halve your storage (§7 → `media-transcoding-streaming-and-drm`) |
| Fixed ABR ladder for all content | Per-title encoding is a substantial win (§7 → `media-transcoding-streaming-and-drm`) |
| Not keeping the mezzanine | You'll re-encode when the next codec lands (§7 → `media-transcoding-streaming-and-drm`) |
| **Mastering to −8 LUFS** | ⚠️ **Platforms turn it down; you lose dynamics for nothing** (§6 → `media-production-and-loudness`) |
| Peaking at 0 dBFS with no true-peak headroom | Inter-sample peaks clip after encoding (§6 → `media-production-and-loudness`) |
| Treating LUFS and LKFS as different units | They're the same (§6 → `media-production-and-loudness`) |
| Assuming 30 fps arithmetic on 29.97 material | ⚠️ **The classic timecode error** (§5.3 → `media-production-and-loudness`) |
| Mixing drop-frame and non-drop timecode | ~3.6 s/hour drift (§5.3 → `media-production-and-loudness`) |
| Editing long-GOP camera footage directly | Transcode to an intermediate (§5.1 → `media-production-and-loudness`) |
| Wrong LUT type or mismatched colour space | Silently misgrades; looks like a choice (§5.2 → `media-production-and-loudness`) |
| Allocation or locks in the audio callback | Hard real-time thread (§4 → `media-production-and-loudness`) |
| Sidecar captions only, no embedded | ⚠️ **CEA-608/708 survive transcoding; sidecars get lost** (§10 → `media-captions-podcasts-rights-and-qc`) |
| ASR captions with no human review | Legally insufficient in many contexts (§10 → `media-captions-podcasts-rights-and-qc`) |
| Treating captions as a launch-week task | Legally required in many jurisdictions (§10 → `media-captions-podcasts-rights-and-qc`) |
| DRM as anti-piracy | ⚠️ **Its function is contractual compliance** (§9 → `media-transcoding-streaming-and-drm`) |
| Shipping cenc only, or cbcs only | FairPlay needs cbcs; older deployments expect cenc (§9 → `media-transcoding-streaming-and-drm`) |
| Rebuilding your live stack on MoQ today | ⚠️ **Months from RFC; no settled killer use case** (§8.2 → `media-transcoding-streaming-and-drm`) |
| WebRTC for a million-viewer broadcast | Scales expensively (§8.1 → `media-transcoding-streaming-and-drm`) |
| RTMP for distribution | Ingest protocol; doesn't scale out (§8.1 → `media-transcoding-streaming-and-drm`) |
| Assuming podcast downloads mean listens | ⚠️ **IAB defines "download" technically; no playback telemetry** (§11 → `media-captions-podcasts-rights-and-qc`) |
| Prefix analytics without considering the dependency | It's on your critical download path (§11 → `media-captions-podcasts-rights-and-qc`) |
| Letting FFmpeg drop metadata | ⚠️ **Default behaviour; it's how royalties go unpaid** (§12 → `media-captions-podcasts-rights-and-qc`) |
| Inventing ISRCs | Validate, don't fabricate (§12 → `media-captions-podcasts-rights-and-qc`) |
| Confusing recording rights with composition rights | ⚠️ **The central structural fact in music rights** (§12 → `media-captions-podcasts-rights-and-qc`) |
| Assuming a platform's commercial-use terms equal copyright | ⚠️ **They are not the same thing** (§13.2 → `media-captions-podcasts-rights-and-qc`) |
| Accepting uploads with no AI provenance policy | ⚠️ **Deezer reports 44% of new uploads are AI-generated** (§13.2 → `media-captions-podcasts-rights-and-qc`) |
| Automated QC with no human viewing | Catches spec violations, not wrong content (§14 → `media-captions-podcasts-rights-and-qc`) |
| Optimizing directly for VMAF | It's gameable like any metric (§14 → `media-captions-podcasts-rights-and-qc`) |

---

## §16. Contested Questions

**16.1 AV1 or HEVC today?** *AV1*: royalty-free (⚠️ **the decisive factor for platform
operators**), ~15% better than HEVC, broad hardware decode in shipping TVs and mobile.
*HEVC*: mature production footprint, better real-time encoding economics, Apple-native.
**[CONTESTED, and the honest answer is both — the survey split (~65% HEVC in production vs
~17% AV1 with 40% planning) shows an industry mid-transition, not a decided one.]**

**16.2 Will VVC ever matter?** *For*: technically the strongest, and it's in broadcast
initiatives like Brazil's TV 3.0 and large deployments in China. *Against*: ⚠️ **~5% device
support, unresolved patent pools with many essential holders outside both, and AV2 widening
the gap.** **The likely outcome is a professional/broadcast niche rather than ubiquity.**

**16.3 Is MoQ the future or a solution seeking a problem?** §8.2 → `media-transcoding-streaming-and-drm`. *For*: real vendor
interop, Cloudflare edge deployment, browser baseline, and sub-second demos at CDN scale.
*Against*: ⚠️ **months from RFC, and no killer use case that lacks a working alternative.**
**Genuinely open, and worth tracking rather than betting on.**

**16.4 Is high-resolution audio audible?** Production benefit is real; **playback benefit
above 44.1/48 kHz is weakly supported and blind tests mostly fail to show it.**
⚠️ **Unusually heated relative to the stakes.**

**16.5 Did loudness normalization end the loudness war?** *Largely yes* — the incentive to
crush is gone when platforms normalize. *But*: ⚠️ **mastering habits lag by years**, and
plenty of releases are still over-limited out of convention rather than reason.

**16.6 Is AI-generated media legitimate?** ⚠️ **The live one.** *For*: it's a tool,
licensed platforms are emerging, and stem separation and mastering assistance are already
uncontroversially useful. *Against*: **the "launch, train, settle" pattern rewarded
infringement**, and **independent creators are structurally excluded from the settlements
that legitimized it.** **[The legal question is genuinely unresolved and heading for a 2027
US ruling; the ethical question is separate and not resolved by whichever way that goes.]**

---

## §17. Currency Snapshot — verified August 2026

| Thing | Status as of Aug 2026 | Decay risk |
|---|---|---|
| **⚠️ AV2** | **AOMedia released AV2 v1.0 in 2026** (announced Sept 2025 for year-end 2025; v1.0 reported June 2026). **~30% better compression than AV1, royalty-free.** **dav2d** decoder project emerging. ⚠️ **Introduces ML-assisted coding tools**; targets AV1's weak spots — real-time, AR/VR, split-screen, screen content. **Devices expected from 2026; broader adoption 2027–28** | **High** |
| **AV1** | Established as the preferred next-gen OTT codec: **~15% additional efficiency over HEVC**, royalty-free, broad hardware decode in shipping TVs. Netflix expanded it into cloud gaming and is evaluating it for high-concurrency live. ⚠️ **Real-time workloads remain computationally problematic** | Medium |
| **⚠️ Codec adoption** | **NETINT 2026 State of Video Encoding survey (via Dan Rayburn): HEVC in production at 65%** (+20% planning), **AV1 in production at 17%** (+40% planning 2026). ⚠️ **Not market share; planned ≠ launched; survey distributed via an encoding-hardware vendor's channels, so likely over-represents encoder-evaluating organizations** | Medium |
| **⚠️ VVC / H.266** | Finalized July 2020; **~50% better than HEVC**. ⚠️ **2026 hardware decode footprint ~5% of consumer devices — no shipping mobile silicon, no browser support.** **Many essential patent holders remain outside both pools as of March 2026** (Apple, Google, Qualcomm, Samsung, Sony and others named). **Android 17 added native VVC support where hardware decoders exist** — not a software player. Traction in smart TVs, STBs, broadcast; **Brazil TV 3.0 and TikTok in China** cited | Medium |
| **⚠️ Media over QUIC** | IETF WG moving through **monthly draft revisions toward Working Group Last Call**; transport at **draft-17** in early 2026 with **Cisco, Google and Meta co-editors**. **Cloudflare MoQ relays across 330+ cities.** **Eleven vendors demoed interop at NAB 2026 (April).** Browser baseline **March 2026: Chrome, Firefox, Safari 26.4+** via WebTransport/HTTP-3. Formats: **CMSF** (CMAF/fMP4 via MSE, DRM via EME, ~0.5–1 s) and **MSF** (LOC raw frames via WebCodecs, <150 ms). One open-source implementation reports **200–300 ms in production**. ⚠️ **Still needs a defined killer use case; months from RFC** | **High** |
| **LL-HLS / LL-DASH** | Classic HLS **20–45 s**; low-latency variants **~2–6 s** in practice per NAB 2026 reviews (2–4 s under ideal tuning) | Low |
| **⚠️ AI music litigation** | **RIAA sued Suno and Udio June 2024**; damages sought **up to $150k/work**. **UMG–Udio settled Oct 2025**; **WMG–Udio and WMG–Suno settled Nov 2025** (Suno to ship licensed-only models, download limits by tier). ⚠️ **Sony has settled with neither; UMG still litigating against Suno.** Suno arguing **fair use**, citing **Bartz v. Anthropic** (June 2025: training on lawfully acquired books can be fair use; pirate sourcing is not). **Fact discovery to 30 Sept 2026, dispositive motions April 2027 — pushing a US fair-use ruling into 2027.** **German court ruled for GEMA against Suno.** Independent-artist class actions filed separately | **High** |
| **AI platform response** | **Deezer: 44% of new uploads AI-generated.** **Spotify "Verified by Spotify" badge for non-AI artists.** **Apple Music rejecting some AI submissions.** Licensing deals now span **Merlin and Kobalt** as the main doorway for independents; **Sony has licensed some AI ventures while still suing Suno and Udio** | **High** |

**Goes stale fastest:** §13 → `media-captions-podcasts-rights-and-qc` entirely, and §8.2 → `media-transcoding-streaming-and-drm`. **Essentially never stale:** §1 → `media-fundamentals-containers-and-codecs`, §2 → `media-fundamentals-containers-and-codecs`, §4 → `media-production-and-loudness`'s
real-time constraint, §5.3 → `media-production-and-loudness`, §6 → `media-production-and-loudness`'s mechanics, §10 → `media-captions-podcasts-rights-and-qc`, §12 → `media-captions-podcasts-rights-and-qc`, §15.

---

## §18. The Canon

### 18.1 Books and references

| Author | Work | Why |
|---|---|---|
| **Katz, Bob** | ***Mastering Audio*** | ⚠️ **The definitive book on §6 → `media-production-and-loudness` and audio delivery** |
| **Senior, Mike** | *Mixing Secrets for the Small Studio* | Practical, evidence-based, and free companion site |
| **Owsinski** | *The Mixing/Mastering Engineer's Handbook* | Industry-standard practical references |
| **Richardson, Iain** | ***The H.264 Advanced Video Compression Standard*** | The clearest codec-internals writing |
| **Ozer, Jan** | *Video Encoding by the Numbers*; *Learn to Produce Video with FFmpeg* | ⚠️ **The most practically useful streaming-encoding author working** |
| **Poynton, Charles** | ***Digital Video and HD*** | ⚠️ **The reference on colour, gamma, and why video is the way it is** |
| **Hullfish** | *The Art and Technique of Digital Color Correction* | §5.2 → `media-production-and-loudness` |
| **Case, Alex** | *Sound FX* | How audio effects actually work, musically |
| **Rumsey & McCormick** | *Sound and Recording* | The academic grounding |
| **Ascher & Pincus** | *The Filmmaker's Handbook* | The production-side context engineers usually lack |

### 18.2 Primary sources and specs
**RFC 8216** (HLS) and Apple's LL-HLS extension docs, **ISO/IEC 23009** (DASH) and
**DASH-IF** guidelines, **ISO/IEC 23000-19** (CMAF), **IETF MoQ working group drafts**
(⚠️ **check the datatracker directly — this moves monthly**), **ITU-R BS.1770**,
**EBU R128**, **ATSC A/85**, **AOMedia** for AV1/AV2, **SMPTE** standards,
**IAB Podcast Measurement Technical Guidelines**, **DDEX**, and the **FFmpeg
documentation** (⚠️ **dense and worth the effort — it's the substrate of the industry**).

### 18.3 People and communities
**Jan Ozer** (⚠️ **Streaming Learning Center — the most consistently useful independent
analysis of codecs and encoding economics**), **Dan Rayburn** (streaming industry
economics and a reliable hype-check), **Bob Katz** (mastering and loudness),
**Charles Poynton** (colour), **Jean-Marc Valin** (Opus — see a DSP reference),
**Fabrice Bellard** (FFmpeg's originator), the **FFmpeg** and **GStreamer** communities,
**Demuxed** (⚠️ **the video-engineering conference worth watching talks from**),
**Streaming Media** and **Mux's** engineering blog, **Music Business Worldwide** and
**Chartlex** for the rights and litigation layer, **/r/audioengineering** and
**gearspace** for production practice.

---

## §19. Quick Reference

### 19.1 Numbers
- **48 kHz** audio for anything with video; **44.1** for music-only legacy
- **−23 LUFS** EBU R128 · **−24 LKFS** ATSC A/85 · **≈ −14 LUFS** typical streaming
  normalization ⚠️ **(verify per platform)**
- **−1 dBTP** true-peak ceiling, minimum
- **29.97 fps drop-frame skips 2 frame *numbers* per minute, except every 10th**
- **Segment duration 2–6 s**; keyframes must align across renditions
- **Classic HLS 20–45 s · LL-HLS/LL-DASH 2–6 s · WebRTC sub-second · MoQ 0.15–1 s**
- **AV1 ≈ 15% better than HEVC · AV2 ≈ 30% better than AV1 · VVC ≈ 50% better than HEVC**
- **VVC hardware decode ≈ 5% of consumer devices**

### 19.2 Picker
| Need | Use |
|---|---|
| Universal video compatibility | **H.264** baseline |
| Best royalty-free efficiency today | **AV1** |
| Apple-native, device capture | **HEVC** |
| Audio, best quality per bit | **Opus** |
| Audio, universal compatibility | **AAC** |
| Package once for HLS and DASH | **CMAF** |
| Live, huge scale, latency tolerable | **LL-HLS / LL-DASH** |
| Live, interactive, small audience | **WebRTC** |
| Live, sub-second at scale | ⚠️ **MoQ — prototype, don't bet** |
| Contribution over a lossy link | **SRT / RIST** |
| Premium content protection | **CENC + Widevine/PlayReady/FairPlay** |
| Captions on the web | **WebVTT** |
| Captions that survive transcoding | **CEA-608/708 embedded** |
| Podcast distribution | **RSS + enclosure. That's it** |
| Encode quality measurement | **VMAF** (⚠️ plus human review) |
| Anything at all | **FFmpeg** |

### 19.3 When it's broken
1. **`ffprobe` it.** Codec, container, timestamps, streams — most answers are here
2. **Check `moov` placement** if it won't start streaming (§2 → `media-fundamentals-containers-and-codecs`)
3. **Check keyframe alignment** if ABR switching stutters (§7 → `media-transcoding-streaming-and-drm`)
4. **Check PTS/DTS and edit lists** if A/V is out of sync (§2 → `media-fundamentals-containers-and-codecs`)
5. **Check timecode base** — 29.97 vs 30, drop vs non-drop (§5.3 → `media-production-and-loudness`)
6. **Check colour space and transfer function** if it looks washed out (§5.2 → `media-production-and-loudness`)
7. **Measure LUFS and dBTP** if it's quiet or clipping (§6 → `media-production-and-loudness`)
8. **Check DRM mode** — cenc vs cbcs — if playback fails on one platform (§9 → `media-transcoding-streaming-and-drm`)
9. **Check the device's actual codec support**, not the spec sheet (§3.2 → `media-fundamentals-containers-and-codecs`)

---

## §20. Sources and Method

**Method.** Narrative review, written as engineering guidance for people building media
systems, and deliberately complementary to a DSP reference (algorithms) and a smart-TV
reference (app platforms). **§1 → `media-fundamentals-containers-and-codecs`, §2 → `media-fundamentals-containers-and-codecs`, §4 → `media-production-and-loudness`'s constraints, §5 → `media-production-and-loudness`, §6 → `media-production-and-loudness`'s mechanics, §10 → `media-captions-podcasts-rights-and-qc`, §11 → `media-captions-podcasts-rights-and-qc`, §12 → `media-captions-podcasts-rights-and-qc`,
§14 → `media-captions-podcasts-rights-and-qc` and §15 are stable** — container semantics, timecode, loudness measurement, caption
formats and identifier schemes have been settled for years and rest on the standards and
the practitioner literature rather than on anything searched. Three targeted searches were
run in **August 2026** on the layers that genuinely moved: the codec landscape, delivery
protocols, and the AI rights fight.

**Search log** (August 2026): AV1/AV2/VVC/HEVC adoption and licensing · Media over QUIC,
LL-HLS and low-latency streaming · Suno/Udio litigation, settlements, and AI music
licensing.

**Primary and near-primary sources consulted (selected):**
- **Codecs**: *Streaming Media*'s "State of Streaming Codecs 2026" and Jan Ozer's
  analysis; the **NETINT 2026 State of Video Encoding survey** as summarized by Dan
  Rayburn; AOMedia's AV2 announcements; multiple 2026 VVC guides for the hardware-footprint
  and patent-pool position
- **MoQ**: the **Fraunhofer FOKUS** MoQ page for the data model and the CMSF/MSF format
  split, **Streaming Learning Center** (Jan Ozer) and *The Register* for the NAB 2026
  interop and standardization state, plus vendor engineering write-ups from Wowza,
  Cloudflare-adjacent sources and Qualabs
- **AI music litigation**: **Music Business Worldwide** and **Reuters** for the settlement
  terms, **Chartlex's** litigation and licensing trackers for the case-by-case status, and
  a **Forbes** analysis for the "launch, train, settle" structural critique

**Confidence statement.** **High confidence** in §1 → `media-fundamentals-containers-and-codecs`, §2 → `media-fundamentals-containers-and-codecs`, §5 → `media-production-and-loudness`, §6 → `media-production-and-loudness`, §10 → `media-captions-podcasts-rights-and-qc`, §11 → `media-captions-podcasts-rights-and-qc`, §12 → `media-captions-podcasts-rights-and-qc` and §14 → `media-captions-podcasts-rights-and-qc` —
these are standards and long-settled practice. **High confidence in the MoQ technical
description** (§8.2 → `media-transcoding-streaming-and-drm`), which comes from Fraunhofer's implementation documentation and the
IETF working group's own materials. **Moderate confidence in §3.2 → `media-fundamentals-containers-and-codecs`'s adoption figures**: the
survey is explicitly self-selecting (⚠️ **and I have flagged its distribution channel in
both §3.2 → `media-fundamentals-containers-and-codecs` and §17 rather than presenting the numbers as market share**), and the
VVC device-support figure comes from a single 2026 analysis.

⚠️ **Lower confidence, and deliberately hedged, on two things.** **The AV2 release date**
— sources place v1.0 variously at year-end 2025 (as announced) and June 2026 (as reported),
which I have noted rather than resolved; **verify against AOMedia directly** before
relying on it. And **§13 → `media-captions-podcasts-rights-and-qc`'s litigation status is the fastest-decaying material in this
document**: settlement terms are largely private, case schedules have already slipped
once, court reporting varies in accuracy (⚠️ **I encountered conflicting attributions of
which judge is hearing the Suno summary-judgment motion, which is why I have not named
one**), and **any US fair-use ruling now appears to land in 2027.** §13 → `media-captions-podcasts-rights-and-qc` is **not legal
advice**; anyone with money or a release at stake should take proper advice, and §16.6's
ethical question is separate from whichever way the legal one resolves.
