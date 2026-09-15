---
name: smart-tv-reference
description: "Use when reviewing a TV app for known anti-patterns, weighing contested questions (native vs web vs React Native, how far back to support, SSAI vs CSAI, whether CTV measurement is trustworthy, platform billing, turnkey OTT platform vs custom build, whether to build for the long tail at all), checking whether a platform or market claim is still current (snapshot verified August 2026), finding the primary and practitioner sources, or needing the numbers, pre-launch checklist, and 'it's broken on TV' triage. Companion to the other smart-tv-app-development skills."
---

# Smart TV Apps: Anti-Patterns, Contested Questions, Currency, and Canon

> **Part 4 of 4** of the *Smart TV App Development* reference (plugin `smart-tv-app-development`), covering §15–§20. Sibling skills: `smart-tv-platforms-and-10-foot-ui` (§0–§3), `smart-tv-playback-drm-and-performance` (§4–§7), `smart-tv-monetization-certification-and-operations` (§8–§14). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Verified August 2026. See §17 below for the currency snapshot and what goes stale first.

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

## §15. Anti-Patterns

| Anti-pattern | Why | Instead |
|---|---|---|
| Porting a mobile or web UI directly | Wrong density, wrong input model, unreadable at 10 ft | Design for TV from scratch (§2 → `smart-tv-platforms-and-10-foot-ui`) |
| Any UI element that requires hover | No pointer exists | Everything visible in default state |
| Losing focus (zero focused elements) | Presents as a **completely dead remote** | Always move focus explicitly on DOM/node changes (§3.1 → `smart-tv-platforms-and-10-foot-ui`) |
| Subtle focus indicators | Invisible at 10 feet | Scale + border + brightness, at least two channels |
| Not restoring focus on back-navigation | User loses their place every time | Save and restore focus per screen |
| Content outside the ~90% safe area | Physically cut off by overscan | 5% margin all sides (§2.2 → `smart-tv-platforms-and-10-foot-ui`) |
| Body text under ~18–24 px at 1080p | Unreadable | ≥24 px body |
| Pure white on large areas | Painful on a bright panel in a dark room | ~#F0F0F0 or lower |
| Rendering an entire long list | Memory death on TV silicon | Virtualize and recycle (§6.2 → `smart-tv-playback-drm-and-performance`) |
| Full-size images scaled down in the client | Wastes bandwidth, decode memory, and CPU | Server-side exact-size thumbnails |
| Assuming an evergreen browser on Tizen/webOS | A 2024 TV is on Chromium 108; a 2018 TV on 56 | Feature-detect, transpile, test the oldest target (§1.3 → `smart-tv-platforms-and-10-foot-ui`) |
| Version-sniffing the Chromium build | Brittle and wrong | Feature detection |
| Requiring on-screen keyboard sign-in | Miserable; users abandon | Device-code pairing (§3.4 → `smart-tv-platforms-and-10-foot-ui`) |
| Saving playback position only on exit | You won't get the callback | Save continuously |
| No deep-link support | **Invisible to platform search, voice, and recommendation rows** | Support play and detail deep links (§7.2 → `smart-tv-playback-drm-and-performance`) |
| Sequential cold-start network cascade | Blows the time-to-first-frame budget | Parallelize auth/manifest/license |
| Single CENC encryption scheme | `cbcs` vs `cenc` — silently black-screens older devices | Package both, select by capability (§5.1 → `smart-tv-playback-drm-and-performance`) |
| Treating DRM config as set-and-forget | Vendor endpoints and revocation change | Calendar-driven re-checks |
| Client-side entitlement decisions | Trivially bypassed | Enforce server-side (§8.2 → `smart-tv-monetization-certification-and-operations`) |
| Reading the certification checklist before submission | Half of it is architectural | Read it before you design (§10.1 → `smart-tv-monetization-certification-and-operations`) |
| Testing only on flagship hardware | Most users are on the cheap stick | Test on the worst device you support |
| Aggregate-only analytics | Model-specific regressions are invisible | Segment by device model and OS version (§12 → `smart-tv-monetization-certification-and-operations`) |
| Ignoring the platform's caption style settings | Accessibility failure and a cert risk | Honour system settings (§14.1 → `smart-tv-monetization-certification-and-operations`) |
| Mismatched loudness between content and ads | Top-tier user complaint | −23 LUFS / −24 LKFS (§4.2 → `smart-tv-playback-drm-and-performance`) |
| Assuming one Amazon platform | Fire OS and Vega are both live, and APKs don't run on Vega | Plan for both (§1.2 → `smart-tv-platforms-and-10-foot-ui`) |

---

## §16. Contested Questions

**16.1 Native vs. web vs. React Native.** §13.1 → `smart-tv-monetization-certification-and-operations`. The calculus genuinely changed in 2026:
React Native became strategically relevant because Amazon made it a **first-class citizen
on Vega**, with core RN and common dependencies precompiled into the OS. If your mix is
Vega + Android TV + tvOS, RN is now a defensible primary choice in a way it wasn't before.
If your mix is Tizen + webOS + the long tail, a web app still wins.

**16.2 How far back to support.** Every additional model year you support drags your web
baseline backwards (§1.3 → `smart-tv-platforms-and-10-foot-ui`) and adds DRM and codec permutations. *For long support*: those
TVs are in living rooms for a decade and their owners are real users. *Against*: the
engineering tax is superlinear. **Decide with usage data from your own analytics, not with
market-share reports.**

**16.3 SSAI vs. CSAI.** §9.2 → `smart-tv-monetization-certification-and-operations`. SSAI wins on user experience and blocker resistance; CSAI
gives the client richer signal and simpler debugging. SSAI is the default and the argument
is mostly settled, but the measurement complexity it introduces is real.

**16.4 Is CTV measurement trustworthy?** §9.3 → `smart-tv-monetization-certification-and-operations`.

**16.5 Platform billing.** *For*: frictionless signup, the platform's stored payment
method, and higher conversion. *Against*: revenue share, and the platform owns your
customer relationship and churn flow. There's no universal answer; there is a very
different answer for a $5/month niche service than for a major studio.

**16.6 Turnkey OTT platform vs. custom build.** *For turnkey*: fast, covers many
platforms, handles certification and updates. *Against*: you don't control the UX, you're
one of thousands of similar apps, and differentiation is limited to branding. Reasonable
if content is your product and the app is a delivery mechanism.

**16.7 Whether to build for the long tail at all.** VIDAA, whaleOS, webOS Hub, Xumo,
Titan OS, SmartCast — each is a certification cycle and a QA burden for a small slice.
Regionally, though, some of them are *not* small: ignoring VIDAA in markets where Hisense
is dominant is a real revenue decision.

---

## §17. Currency Snapshot — verified August 2026

| Thing | Status as of Aug 2026 | Decay risk |
|---|---|---|
| **US platform share** | Parks Associates (Apr 2026, most-used device for online video, US broadband households): **Roku OS 28%, Samsung Tizen 23%**; Fire TV, webOS, SmartCast mid-tier; tvOS, consoles, Android TV smaller. Other measures put Roku at ~38% of activated screens. **Global shipments rank differently** — Tizen and Android TV lead worldwide | Medium |
| **Scale anchors** | Android TV/Google TV **~300M monthly active devices**; Roku **~100M streaming households**; webOS ~12% overall but **~52% of premium OLED**; smart TV ownership heading past **1.1B households** | Medium |
| **Amazon Vega OS** | ⚠️ **Linux-based, not Android — APKs do not run.** React Native 0.72 or Vega WebView; **VPKG** packaging. Shipped on Fire TV Stick 4K Select (2025) and Fire TV Stick HD (Apr 2026); Amazon states **all future Fire TV Sticks run Vega**. Existing Fire OS devices **not upgraded**, supported through at least 2030. **No sideloading.** Selected apps cloud-streamed with ~9 months free hosting during transition | **High** |
| **Fox–Roku** | ⚠️ **April 2026: Fox announced an agreement to acquire Roku for ~$22B** (cash and stock). Expected to affect OS licensing and ad-supply terms | **High** |
| **Samsung Tizen web engine** | **2026: Tizen 10.0 / Chromium M130** · 2025: 9.0/M120 · 2024: 8.0/**M108** · 2023: 7.0/M94 · 2022: 6.5/M85 · 2021: 6.0/M76 · 2020: 5.5/M69 · 2019: 5.0/M63 · 2018: 4.0/**M56** · 2017: 3.0/M47 · 2016 and earlier: WebKit. **Never updated after ship** | Low (annual) |
| **Samsung native toolchain** | ⚠️ **GCC 9.2.0 through the 2025 model year; GCC 14.2.0 from 2026.** Native binaries must be rebuilt for 2026 sets | Low |
| **LG webOS** | **webOS 26** introduced Jan 2026 with AI assistant integrations (**Microsoft Copilot** and **Google Gemini**). Enact (React-based) remains the LG-blessed framework | Medium |
| **Roku certification** | ⚠️ **Spring 2026 update: Instant Resume required by 1 October 2026** for qualifying US Streaming Store apps. **`roAppMemoryMonitor`** usage required to pass certification testing. Static Analysis must pass to publish; App Behavior Analysis for free/ad-based apps. **Direct Publisher has been wound down** — no-code publishing now goes through third-party OTT platforms | Medium |
| **Roku OS** | 15.0 (Oct 2025). Linux-based; BrightScript + SceneGraph; ARM Cortex-A53/A55/A35 and some MIPS | Medium |
| **CTV ad specs** | **VAST 4.x required** for full CTV format and measurement support. **SSAI is the default.** Loudness **−23 LUFS (EBU R128)** streaming/SSAI, **−24 LKFS (ATSC A/85)** US broadcast. Creative typically ≤200 MB (≤150 MB preferred). **Universal Ad ID** and **OM SDK** are the IAB Tech Lab interop answers | Medium |
| **CTV market** | US digital video ad spend projected **>$80B in 2026**, passing **60% of total TV/video spend** for the first time. Streaming hit **~48.6% of US TV watch-time (Nielsen, May 2026)** | Annual |
| **Privacy/ACR regulation** | **US Cyber Trust Mark** programme and **Kentucky HB 692** (ACR data handling) named as shaping 2026 privacy-by-design roadmaps. **Caption discovery** is a 2026 US accessibility compliance milestone | **High** |

**Goes stale fastest:** the Vega transition; the Fox–Roku deal; Roku certification
requirements; ACR/privacy legislation; ad-market figures. **Essentially never stale:**
§2 → `smart-tv-platforms-and-10-foot-ui` (10-foot UI), §3 → `smart-tv-platforms-and-10-foot-ui` (focus and input), §4.3 → `smart-tv-playback-drm-and-performance` (playback metrics), §5.1 → `smart-tv-playback-drm-and-performance`'s `cenc`/`cbcs` trap,
§6.2 → `smart-tv-playback-drm-and-performance` (performance techniques), §15 (anti-patterns).

---

## §18. The Canon

### 18.1 Primary sources — and here, they're nearly all you have

**[DURABLE] Unlike web or mobile, TV development has almost no independent literature.
The vendor docs are the field.** Read them directly and read them annually.

- **Roku**: `developer.roku.com` — the SceneGraph course, **certification docs**, the
  BrightScript reference, and the **`rokudev` GitHub org**, especially
  **`scenegraph-master-sample`** (a certification-compliant reference channel you can use
  as a template) and `samples`. The **Roku developer blog's Certification category** is
  where requirement changes are announced — subscribe to it.
- **Samsung**: `developer.samsung.com/smarttv` — and specifically the **Web Engine
  Specifications** page, which carries the model-year/Chromium/feature-support matrix in
  §1.3 → `smart-tv-platforms-and-10-foot-ui` and §17. This single page will save you more time than anything else in this list.
  Also **General Specifications** for HLS/DASH tag support and the toolchain notes.
- **LG**: `webostv.developer.lge.com` — webOS TV docs, the **Enact** framework, and the
  Simulator/CLI tooling.
- **Google**: `developer.android.com/tv` — Leanback, **Compose for TV**, **Media3/
  ExoPlayer**, Watch Next and channel APIs, and the Android TV quality guidelines.
- **Amazon**: `developer.amazon.com` — Fire TV docs and, critically, the **Vega Developer
  Tools** getting-started guides, VS Code extension, and CLI.
- **Apple**: the **tvOS Human Interface Guidelines** (the best-written TV design doc from
  any vendor, and worth reading even if you never ship tvOS) plus TVMLKit and SwiftUI docs.
- **IAB Tech Lab**: the **CTV Programmatic Guide**, VAST 4.x, **Universal Ad ID**, and
  **OM SDK** specs — the standards layer under §9 → `smart-tv-monetization-certification-and-operations`.
- **Standards bodies**: HbbTV (Europe), ATSC 3.0 (US broadcast), DASH-IF, and CTA
  specifications, depending on your market.

### 18.2 Practitioner sources

Vendor-neutral analysis lives with the OTT integrators and the measurement firms rather
than in books: **Conviva** (State of Streaming — the QoE benchmark data),
**Parks Associates** and **Nielsen** (share and viewing), **Bitmovin's annual Video
Developer Report**, **Accedo**, **Float Left**, **Fora Soft**, and **Lightcast** (platform
notes and build-cost writeups — commercially motivated, but the technical detail is real
and hard to find elsewhere). **AFTVnews** is the best source on Fire TV/Vega specifics.
**Dolby OptiView**, **Bitmovin**, **JW Player**, **THEO**, and **Shaka Player** docs are
the practical references for the player and DRM layers.

**⚠️ Almost every source in this domain is a vendor or an integrator selling something.**
Cross-read, and treat platform-share numbers especially carefully (§1.1 → `smart-tv-platforms-and-10-foot-ui`).

---

## §19. Quick Reference

### 19.1 Numbers
- Design canvas **1920×1080**; **safe area 90%** (5% margin each side).
- Body text **≥24 px**; nothing below ~18 px.
- Focusable targets **≥60–80 px**.
- Frame budget **16.6 ms**; time-to-first-video-frame **<2 s**; cold start **<3 s**.
- Rebuffer ratio **<0.5%**; playback failure **<1%**.
- Loudness **−23 LUFS** (streaming/SSAI), **−24 LKFS** (US broadcast).
- Ad creative **≤200 MB** (≤150 MB preferred); **VAST 4.x**.
- Samsung 2024 TVs run **Chromium 108**; 2018 TVs run **Chromium 56**.
- Roku **Instant Resume required by 1 Oct 2026** (qualifying US apps).

### 19.2 Pre-launch checklist
- [ ] Focus never lost; Back always predictable; initial focus set on every screen
- [ ] Everything inside the 90% safe area; readable at 10 feet
- [ ] Tested on the **cheapest** device and the **oldest model year** you support
- [ ] Long lists virtualized; images server-sized; memory monitored
- [ ] Cold start and time-to-first-frame measured on the slowest device
- [ ] Deep links work: cold start, warm start, unentitled user, missing content
- [ ] Playback position saved continuously; resume verified after a long suspend
- [ ] Both `cenc` and `cbcs` packaging verified on old and new devices
- [ ] Captions render and honour system style settings
- [ ] Sign-in via device-code pairing, not an on-screen keyboard
- [ ] Platform billing implemented per policy; entitlement enforced server-side
- [ ] Analytics segmented by device model and OS version
- [ ] Certification checklist walked end-to-end **before** submission
- [ ] Catalogue feed submitted for platform search/voice/recommendation rows

### 19.3 "It's broken on TV" triage
| Symptom | First look |
|---|---|
| Remote appears dead | Focus lost, or focus trapped in a container (§3.1 → `smart-tv-platforms-and-10-foot-ui`) |
| Blank/white screen on some models only | Frozen-Chromium feature gap — check the engine version (§1.3 → `smart-tv-platforms-and-10-foot-ui`) |
| Black screen on playback, older devices | `cenc`/`cbcs` mismatch, or codec unsupported on that tier (§5.1 → `smart-tv-playback-drm-and-performance`) |
| App killed during use | Memory budget exceeded — profile image cache and list virtualization |
| Slow to start playing | Sequential cold-start network cascade (§4.3 → `smart-tv-playback-drm-and-performance`) |
| Fails certification on launch time | Same, plus JS bundle parse cost |
| Works via deep link, broken from search | Catalogue feed mapping or unentitled-user path (§7.2 → `smart-tv-playback-drm-and-performance`–7.3) |
| Ads too loud | Loudness normalization (§4.2 → `smart-tv-playback-drm-and-performance`) |
| Fine on the OLED, broken on the stick | You tested on the wrong device (§11 → `smart-tv-monetization-certification-and-operations`) |

---

## §20. Sources and Method

**Method.** Narrative (not systematic) review. The durable material — §2 → `smart-tv-platforms-and-10-foot-ui` (10-foot UI),
§3 → `smart-tv-platforms-and-10-foot-ui` (focus and input), §4.3 → `smart-tv-playback-drm-and-performance` (playback metrics), §5.1 → `smart-tv-playback-drm-and-performance` (DRM structure), §6 → `smart-tv-playback-drm-and-performance` (performance),
§8.2 → `smart-tv-monetization-certification-and-operations`, §12 → `smart-tv-monetization-certification-and-operations`, §15 — is synthesized from vendor design guidelines, long-standing platform
documentation, and consistent practitioner reporting. Every **time-sensitive** claim
(platform shares, OS versions, engine matrices, certification requirements, ad specs,
regulation) was verified against a primary or near-primary source in **August 2026** and
is flagged in §17 with a decay-risk rating. Where the trade-off genuinely depends on
platform mix or budget, §16 presents both cases.

**Search log** (August 2026): smart TV OS market share and platform landscape · Amazon
Vega OS and the Fire OS transition · Roku SceneGraph/BrightScript and certification
requirements · Samsung Tizen and LG webOS SDK and Chromium version constraints · CTV
advertising specs, SSAI, ACR, and measurement.

**Primary and near-primary sources consulted (selected):**
- **Samsung Developer** — **Web Engine Specifications** (the model-year/Chromium table),
  General Specifications (HLS/DASH support, GCC toolchain change), TV Extension archive
- **Roku Developer** — certification testing docs, SceneGraph course, the Roku developer
  blog's Certification category (Spring 2026 update), the `rokudev` GitHub org
- **Amazon Developer** — "Announcing Vega OS" / Get started with Vega Developer Tools;
  **Software Mansion**'s account of building React Native for Vega; **AFTVnews**,
  **Ars Technica**-sourced reporting, **PCWorld**, and **Dolby OptiView** on the transition
- **Parks Associates** (April 2026 Streaming Video Tracker press release, via PRNewswire
  and TV Tech) — US platform shares; **Mordor Intelligence** on activated screens, the
  Fox–Roku agreement, webOS 26, and the Cyber Trust Mark / Kentucky HB 692 regulatory notes
- **IAB Tech Lab** — CTV Programmatic Guide (Universal Ad ID, OM SDK); **Equativ** —
  2026 CTV ad formats and specs, including loudness targets
- **Nielsen** figures via **M+C Saatchi Performance**; **ScreenCloud** and **Play Signage**
  on real-world Chromium version limits; **Float Left**, **Fora Soft**, **Lightcast**,
  and **Accedo** on platform development practice

**Confidence statement.** **High confidence** in §2–§8 → `smart-tv-platforms-and-10-foot-ui`, `smart-tv-monetization-certification-and-operations`, §10–§12 → `smart-tv-monetization-certification-and-operations`, §15, and §19 — these rest
on vendor documentation and consistently-reported practitioner experience. **High
confidence** in the Samsung engine matrix (§1.3 → `smart-tv-platforms-and-10-foot-ui`, §17), which comes directly from Samsung's
own specification page, and in the Roku certification requirements, which come from Roku's
own blog. **Moderate confidence** in §1.1 → `smart-tv-platforms-and-10-foot-ui`'s market-share figures: the sources genuinely
disagree because they measure different things (usage vs. activated screens vs. global
shipments), the numbers come from commercial research firms with differing methodologies,
and I have deliberately presented three framings rather than one number. **Moderate
confidence** in §9 → `smart-tv-monetization-certification-and-operations`'s advertising specifications — these come from ad-tech vendors and the
IAB, are directionally consistent across sources, but vary by publisher in practice, and
the guidance throughout is to confirm specs with the specific publisher or platform rather
than treating any single figure as universal. The Fox–Roku acquisition (§1.2 → `smart-tv-platforms-and-10-foot-ui`, §17) was
**announced**, and announced deals do not always close.
