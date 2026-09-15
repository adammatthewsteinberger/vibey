---
name: media-captions-podcasts-rights-and-qc
description: "Use when handling accessibility, podcasts, rights, or quality control: captions and subtitles (WebVTT, TTML, SCC, burn-in) and the accessibility requirements, podcast infrastructure including RSS, hosting, prefix analytics and dynamic ad insertion, metadata and rights identifiers (ISRC, ISWC, ISNI, EIDR, C2PA), the AI generation layer and the live music-licensing litigation, and testing and QC for media pipelines."
---

# Media Engineering: Captions, Podcast Infrastructure, Rights, AI Generation, and QC

> **Part 4 of 5** of the *Media Engineering* reference (plugin `media-engineering`), covering §10–§14. Sibling skills: `media-fundamentals-containers-and-codecs` (§0–§3), `media-production-and-loudness` (§4–§6), `media-transcoding-streaming-and-drm` (§7–§9), `media-reference` (§15–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
>    fight all determine what you may ship, not just what you can encode (§12, §13).

---

## §10. Captions and Accessibility

**[DURABLE] Legally required in many jurisdictions, and routinely treated as an
afterthought.**

**Formats**: **WebVTT** (web standard), **TTML/IMSC** (broadcast and streaming, richer
styling), **SRT** (simple, ubiquitous, ⚠️ **no positioning or styling**), **SCC/CEA-608**
and **CEA-708** (⚠️ **embedded in the video bitstream itself, which is why they survive
transcoding when sidecar files don't — and why they're a pain to edit**), **SAMI**.

**⚠️ The distinctions that matter**: **captions include non-speech audio information and
speaker identification; subtitles assume you can hear.** **Open** captions are burned into
the picture; **closed** can be toggled. **Audio description** is a separate narration
track for blind users — ⚠️ **and it has its own mixing and legal requirements.**

**Compliance**: **FCC rules** in the US, **EN 301 549** and the **European Accessibility
Act** in the EU, **WCAG** for web. **⚠️ ASR-generated captions are cheap and legally
insufficient in many contexts** — accuracy requirements typically demand human review, and
"good enough to understand" is not the standard.

---

## §11. Podcast Infrastructure

**[DURABLE] Structurally the simplest media distribution system in this document, and
that's its strength.**

**RSS is the whole protocol.** An **RSS 2.0 feed with the iTunes namespace extensions** and
an `<enclosure>` pointing at an MP3 or AAC file. ⚠️ **There is no central platform — Apple
Podcasts, Spotify, Overcast and the rest all read the same feed**, which is why podcasting
stayed open when almost nothing else did.

**Podcasting 2.0 namespace** adds transcripts, chapters, funding tags, cross-app comments,
and value-for-value payments — ⚠️ **adopted by independent apps, largely ignored by the
big platforms.**

**⚠️ The engineering realities**: **measurement is defined by IAB Podcast Measurement
Technical Guidelines** (⚠️ **a "download" has a specific technical definition involving
byte thresholds and de-duplication windows — and unlike streaming there is no playback
telemetry unless the app volunteers it**); **dynamic ad insertion (DAI)** stitches ads at
request time, which means **the file is assembled per listener** and breaks naive caching;
**prefix-based analytics services** (⚠️ **which work by proxying every download and are
therefore a hard dependency on your critical path**); **hosting** (Libsyn, Buzzsprout,
Transistor, Megaphone); and **loudness** — ⚠️ **spoken-word targets sit around −16 LUFS
mono / −19 stereo in common guidance, and the platform normalization caveat in §6 → `media-production-and-loudness` applies.**

**Production practice**: multitrack recording per speaker (⚠️ **because you cannot
un-mix**), remote recording tools that record locally and upload (Riverside, SquadCast) to
avoid capturing network artifacts, and the standard chain — noise reduction, EQ,
compression, loudness normalization.

---

## §12. Metadata, Identifiers, and Rights

**[DURABLE] Boring, unglamorous, and the thing that determines whether anyone gets paid.**

**Music identifiers**: **ISRC** (recording), **ISWC** (composition — ⚠️ **the
recording/composition split is the single most important structural fact in music
rights**), **UPC/EAN** (release), **IPI/CAE** (writer), **ISNI** (party).
**Video**: **EIDR** (⚠️ **the film/TV equivalent, and increasingly required by
distributors**), **Ad-ID** for advertising.

**Embedded metadata**: **ID3** (MP3), **Vorbis comments**, **MP4 atoms**, **BWF/iXML**
(broadcast wave, ⚠️ **which carries timecode and is how production audio syncs**),
**XMP** and **EXIF**.

**Rights infrastructure**: PROs (ASCAP, BMI, PRS, GEMA), the **MLC** in the US for
mechanicals, **DDEX** as the messaging standard between labels, distributors and DSPs
(⚠️ **and the thing you'll implement if you build a distribution system**), and
**Content ID / Audible Magic** for fingerprint-based identification.

**⚠️ The practical warning**: **metadata errors are how royalties go unpaid**, and they are
extremely common. **Validate ISRCs, don't invent them, and preserve metadata through your
transcode pipeline** — ⚠️ **FFmpeg drops most metadata by default unless you ask it not
to.**

---

## §13. AI Generation and the Licensing Fight

**[VERSIONED — the fastest-moving and most legally live material here.]**

**The tools**: music (Suno, Udio, and licensed platforms emerging from settlements), voice
(ElevenLabs and the cloning ecosystem), video (Sora, Runway, Veo, Kling), and mastering
and stem separation — ⚠️ **the last of which is genuinely uncontroversial and widely
adopted, because it's a tool applied to your own material.**

### 13.1 ⚠️ The music litigation, as of August 2026

**The RIAA sued Suno and Udio in June 2024** on behalf of all three majors, seeking
**statutory damages of up to $150,000 per infringed work.** What has happened since is
**a split, not a resolution:**

- **Universal settled with Udio (October 2025)** — upfront payment plus ongoing licensing,
  with a licensed platform announced.
- **Warner settled with Udio (November 2025) and with Suno (November 2025)** — the Suno
  deal bundled a licensing arrangement under which **Suno builds new models trained only on
  licensed catalogue**, adds download restrictions by tier, and (per reporting) acquired
  Warner's Songkick.
- **⚠️ Sony has not settled with either, and UMG continues against Suno.** Suno is fighting
  on **fair use**, leaning on the **Bartz v. Anthropic** reasoning that training on lawfully
  acquired works can be fair use while sourcing from pirate libraries is not.
- **Schedules have slipped**: reporting in mid-2026 put fact discovery closing
  **30 September 2026** and dispositive motions due **April 2027** in the Suno case,
  ⚠️ **pushing any US fair-use ruling into 2027.**
- **In Germany, a court ruled for GEMA against Suno**, finding training on GEMA's
  repertoire without a licence infringing.
- **Independent musicians filed separate class actions**, arguing the major-label
  settlements don't protect smaller rights holders.

> **⚠️ GOTCHA — the structural critique is worth taking seriously, whatever your view of
> the technology.** The observed pattern is **"launch, train, settle"**: operate using
> copyrighted material without permission, face suits only from those powerful enough to
> bring them, then legitimize through selective licensing — ⚠️ **while the work of
> creators without the resources to sue remains in the training data, uncompensated.**
> One analysis notes the emerging shape is **a two-tier regime where major labels cut
> deals and independent artists are left out**, and that **Merlin and Kobalt have become
> the main doorway for independents.**
>
> ⚠️ **And note Sony's position is not simple opposition** — it has licensed some AI music
> ventures and joined platform initiatives **while still suing Suno and Udio.**

### 13.2 What this means if you're building
**⚠️ Platform-side detection and labelling is now real infrastructure**: **Deezer reports
44% of new uploads are AI-generated**; **Spotify launched a "Verified by Spotify" badge
for non-AI artists**; **Apple Music has rejected some AI submissions.** **If you run a
platform that accepts uploads, provenance and disclosure are product requirements now, not
future ones.**

**⚠️ And the practical caution for anyone shipping AI-generated media**: **the commercial
rights a generation platform grants you in its terms are not the same thing as copyright a
court would recognize**, and the terms differ by subscription tier. **Read them, and get
advice before commercial release.** **This document is not legal advice and the situation
is actively moving.**

---

## §14. Testing and QC

**[DURABLE] Media QC is its own discipline and most software teams underinvest in it.**

**Automated**: **file validation** against a spec (⚠️ **broadcast deliverables get rejected
for things like wrong audio channel order, missing bars and tone, or a two-frame black
gap** — validate before you ship); **loudness verification** (§6 → `media-production-and-loudness`); **PSNR/SSIM/VMAF** for
encode quality (⚠️ **VMAF is Netflix's perceptual metric and the current industry default —
and like all such metrics it can be gamed by tuning to it**); **black frame, freeze frame,
and silence detection**; **A/V sync measurement**; **caption presence and timing checks.**

**Tools**: **FFmpeg/FFprobe**, **MediaInfo**, **Bitmovin Analyzer**, **Hybrik**,
**Interra Baton**, **Telestream Vidchecker**, **libvmaf**.

**⚠️ And the irreplaceable step: watch and listen to it.** Automated QC catches spec
violations; **it does not catch a wrong audio track, an upside-down insert, or a grade that
looks wrong.** Golden-reference comparison and human spot checks remain necessary.

**⚠️ Test matrix reality**: browsers × devices × OS versions × codecs × DRM × network
conditions. **You cannot cover it exhaustively — pick your top device/browser combinations
by actual audience telemetry and cover those properly.**
