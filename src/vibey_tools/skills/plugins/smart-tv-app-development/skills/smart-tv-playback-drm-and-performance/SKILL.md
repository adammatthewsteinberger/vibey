---
name: smart-tv-playback-drm-and-performance
description: "Use when implementing or debugging video on TV: the playback stack (MSE/EME, Shaka Player), formats and the adaptive bitrate ladder (HLS/DASH, codecs, HDR), the QoE metrics that matter, the three-DRM reality (Widevine, PlayReady, FairPlay) and security levels, the hardware reality and the performance and memory techniques that work on constrained devices, the app lifecycle, deep linking, and content feeds and discovery integration."
---

# Smart TV Apps: Video Playback, DRM, Performance and Memory, and Lifecycle

> **Part 2 of 4** of the *Smart TV App Development* reference (plugin `smart-tv-app-development`), covering §4–§7. Sibling skills: `smart-tv-platforms-and-10-foot-ui` (§0–§3), `smart-tv-monetization-certification-and-operations` (§8–§14), `smart-tv-reference` (§15–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Verified August 2026. See §17 → `smart-tv-reference` for the currency snapshot and what goes stale first.

> **How to read this.** Reference, not tutorial. Sections are independent. Three markers:
> - **[DURABLE]** — human factors, hardware physics, or a lesson every TV platform has
>   independently arrived at. Does not expire.
> - **[PLATFORM]** — specific to Roku, Tizen, webOS, Android TV, Fire OS/Vega, or tvOS.
>   Verify against that vendor's current docs, which change annually with the model year.
> - **[CONTESTED]** — real disagreement about approach, usually because the trade-off
>   depends on your budget and platform mix.
>
> **⚠️ GOTCHA** boxes mark the mistakes that fail certification, get discovered only on a
> five-year-old TV in someone's living room, or quietly halve your completion rate.
>
> **The three framings that organize everything below:**
> 1. **You are writing for a 2015 phone bolted to a 2025 display.** TV silicon is
>    cost-optimized to the bone. Assume ~1–2 GB RAM, a weak CPU, and a GPU that exists
>    mostly to composite video. Your desktop intuitions about performance are wrong by an
>    order of magnitude.
> 2. **The remote has a D-pad, and that is the entire input model.** No pointer, no touch,
>    no hover, no keyboard. Every interaction is up/down/left/right/OK/back. Focus
>    management is not a detail — it *is* the UI architecture.
> 3. **The platform owner is your distributor, your competitor, and your ad network.**
>    Certification is a gate they control, discovery placement is inventory they sell, and
>    on most platforms they take a cut of your revenue. This is a commercial relationship
>    wearing an SDK.

---

## §4. Video Playback

### 4.1 The stack

```
manifest (HLS .m3u8 / DASH .mpd)
  → ABR ladder selection (bitrate/resolution/codec variants)
    → segment fetch → buffer management
      → demux → DECODE (hardware!) → render
        → DRM license acquisition + key handling (§5)
          → subtitles/captions, audio track selection, trick play
```

**[DURABLE] Use the platform's player.** On every TV platform, hardware-accelerated
decode is mandatory — software decode of 4K HEVC on TV silicon does not work. That means:
Roku's `Video` node, Android's **Media3/ExoPlayer**, AVPlayer on tvOS, and the
platform-specific **AVPlay** (Tizen) or media APIs on webOS. On web platforms, MSE/EME
exists but the vendor's native path is usually the one that gets hardware decode and DRM
right.

### 4.2 Formats and the ladder

- **HLS** (Apple-originating, dominant in the US, `.m3u8`) and **DASH** (`.mpd`, dominant
  in Europe). **CMAF** lets one set of segments serve both, which is the modern answer to
  "must I encode twice?"
- **Codecs**: H.264/AVC (universal baseline), HEVC/H.265 (4K/HDR, patent-encumbered),
  VP9, AV1 (decode support is real on newer sets and absent on older ones).
  **⚠️ Codec support varies by model year and by hardware tier within a model year.**
  Query capability at runtime; never assume.
- **HDR**: HDR10, HLG, Dolby Vision, HDR10+ — each with its own licensing and signalling.
- **Audio**: AAC, AC-3/E-AC-3, Dolby Atmos. **Loudness matters**: streaming/SSAI targets
  **−23 LUFS (EBU R128)**, US broadcast contexts **−24 LKFS (ATSC A/85)**. Mismatched
  loudness between content and ads is one of the most-complained-about defects in
  streaming.
- **Ladder design**: enough rungs to adapt smoothly, not so many that switching thrashes.
  Include a low rung that works on bad connections — a TV user with a weak 5 GHz signal
  is common.

### 4.3 The metrics that matter

**[DURABLE] TV video quality is measured by four numbers, and users feel all of them:**
| Metric | Target |
|---|---|
| **Startup time (time-to-first-frame)** | **< 2 s.** Certification programmes test this |
| **Rebuffer ratio** | < 0.5% of playback time |
| **Average bitrate / bitrate at start** | As high as the connection sustains |
| **Playback failure rate** | < 1% of attempts |

**⚠️ Startup time is where TV apps most often fail certification and lose users.**
Techniques: pre-warm the player, start the license request in parallel with the manifest
fetch, use a low-bitrate first segment then ramp, and **never do a cold cascade of
sequential network round trips** (auth → entitlement → manifest → license → first segment).
Parallelize what you can.

**Trick play** (FF/RW with thumbnails) requires an I-frame playlist or a sprite sheet of
thumbnails. Users expect it; implementing it late is painful.

**Captions and subtitles are not optional** (§14.1 → `smart-tv-monetization-certification-and-operations`) — WebVTT, TTML/IMSC, CEA-608/708 —
and must honour the **platform's** caption style settings, which the user set once in
system preferences and expects everywhere.

---

## §5. DRM

### 5.1 The three-DRM reality

**[DURABLE] There is no single DRM, and you will implement at least two.**

| DRM | Owner | Where it's required |
|---|---|---|
| **Widevine** | Google | Android TV/Google TV, Fire OS, Chrome, most web TVs, modern Roku |
| **PlayReady** | Microsoft | Samsung Tizen, LG webOS, Xbox, many operators |
| **FairPlay Streaming** | Apple | tvOS, Safari, iOS |

**Widevine security levels** matter commercially: **L1** = crypto and decode both in the
TEE (required by most studios for HD/4K), **L3** = software (typically limited to SD by
licensing policy). Android TV/Google TV gives you L1 on certified devices. **PlayReady
SL3000** is the hardware-backed equivalent.

**Multi-DRM with CENC (Common Encryption)** is the standard answer: encrypt once, package
once, and serve different license flows per platform. That's what makes shipping to six
platforms tractable.

> **⚠️ GOTCHA — the encryption-scheme trap that silently breaks the older half of your
> fleet.** CENC defines two schemes: **`cenc`** (AES-128 CTR) and **`cbcs`** (AES-128 CBC
> with pattern encryption). FairPlay requires `cbcs`. Older Widevine and PlayReady devices
> support only `cenc`. Choosing one scheme for everything **works perfectly on your test
> devices and produces a black screen on a large slice of installed sets**. You generally
> need both packagings, keyed off device capability — and this is exactly the class of
> defect that reaches production because the QA fleet is all recent models.

> **⚠️ GOTCHA — DRM has dated, vendor-specific server-side requirements.** PlayReady
> revocation endpoints change; running an old license server can mean it quietly stops
> enforcing current device blocks, while missing a new address can make a modern server
> return an error the viewer experiences as a black screen. **Put vendor DRM changes on a
> calendar with a re-check date.** They are not "set and forget."

Also plan for: **HDCP** output protection (and the "HDCP handshake failed" support calls
it generates through AV receivers), **license persistence** for offline/download where
supported, **key rotation** for live, and **concurrency/device limits** as a business rule
that must be enforced server-side.

---

## §6. Performance and Memory

### 6.1 The hardware reality

**[DURABLE] Budget as if you're targeting a low-end phone from a decade ago.** Roku
devices run ARM Cortex-A53/A55/A35-class cores (some older models MIPS); TV SoCs across
all vendors are cost-optimized, thermally constrained, and shipped with the minimum RAM
that passes QA. A $30 streaming stick and a $3,000 OLED may run the same app on very
different silicon — **and the cheap device is the one most of your users have.**

**The budgets that actually matter:**
| Resource | Guidance |
|---|---|
| **App memory** | Often a few hundred MB total. Exceeding it means the OS kills you |
| **Startup to first interactive frame** | Target < 3 s cold |
| **Time to first video frame** | Target < 2 s (§4.3) |
| **Frame time** | 16.6 ms — and you will blow it far more easily than on mobile |
| **Image decode** | The dominant memory consumer in a poster-grid UI |

### 6.2 The techniques

1. **Virtualize every long list.** Never instantiate 500 tiles. Recycle views/nodes and
   render a window plus a small buffer. **This is the single highest-impact optimization
   in TV development**, because the rail-grid UI is inherently a huge-list problem.
2. **Size images server-side to the exact display size.** Downloading a 1920px poster to
   render at 300px wastes bandwidth *and* decode memory *and* CPU. Use a thumbnailing CDN
   and request precise dimensions.
3. **Aggressively evict off-screen image bitmaps.** Memory pressure on TV is real.
4. **Preload the *next* screen's data, not everything.**
5. **Minimize DOM work on web platforms** — old Chromium, weak CPU. Batch mutations,
   avoid layout thrashing, prefer `transform`/`opacity` animations, and keep the node
   count low.
6. **Never block on network during navigation.** Show the shell instantly, fill it in.
7. **Watch your JS bundle size** — parse and compile cost is significant on these CPUs.
8. **Profile on the worst device you support, not the best.**

**[PLATFORM] Roku requires memory monitoring for certification.** Apps must use the
**`roAppMemoryMonitor`** APIs to observe and respond to memory events in order to pass
certification testing — that is, the platform mandates that you handle memory pressure
rather than merely hoping. The **BrightScript Profiler** and **Roku Resource Monitor**
are the tools; Roku also ships **`rokuos-perfetto-utils`** for tracing.

---

## §7. Lifecycle, Deep Linking, and Discovery

### 7.1 Lifecycle

TV apps get suspended, backgrounded, and killed aggressively, and the user may return
hours later expecting to be exactly where they were.

**[DURABLE] Save playback position continuously — every few seconds — not on exit.** You
will not reliably get an exit callback. The same applies to navigation state, partially
completed forms, and auth state.

**[PLATFORM] Roku's Instant Resume** is a formal version of this, and it is
**becoming a certification requirement**: Roku's Spring 2026 certification update added a
requirement to implement Instant Resume **by 1 October 2026** for apps in the US Streaming
Store meeting the specified streaming criteria. The pattern — return the user to exactly
what they were watching, instantly — is where the whole industry is heading regardless of
platform.

### 7.2 Deep linking

**[DURABLE] Deep linking is not a nice-to-have; it is how the platform's search, voice,
recommendations, and home-screen rows launch your content.** If your app can't be deep
linked, **it is invisible to the platform's discovery surfaces**, which is where a large
share of your traffic would come from.

Two modes to support:
- **Play** — launch directly into playback of a specific asset.
- **Detail/preview** — launch to the content's detail page.

You must handle: cold start with a deep link, warm start with a deep link, an
unentitled user (route to sign-in or upsell **and then continue to the content**), and
content that no longer exists (a graceful message, not a crash).

### 7.3 Content feeds and discovery integration

Each platform ingests a catalogue feed to power search, voice, and home-screen rows.
**[PLATFORM]** Roku Search Feed / Direct Publisher-lineage feeds, Android TV's Watch Next
and channel/program APIs, Apple's TV App integration, Amazon's catalogue ingestion, and
Samsung/LG equivalents. **Getting into these feeds is usually the highest-leverage growth
work available**, and it is unglamorous data-plumbing rather than app development.

**Continue Watching** integration at the *platform* level (not just in-app) is
increasingly expected and, on Roku, tied to the Instant Resume requirement above.
