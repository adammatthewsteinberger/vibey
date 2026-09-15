---
name: smart-tv-platforms-and-10-foot-ui
description: "Use when scoping or designing a TV app. Covers the platform matrix and who actually owns the living room (Roku, Samsung Tizen, LG webOS, Android TV/Google TV, Fire OS and Vega OS, tvOS, VIDAA, SmartCast), the two structural shifts in progress, the frozen-browser problem, why TV design is genuinely different, the 10-foot numbers and the standard layout vocabulary, focus as the architecture, spatial navigation, the remote, and text entry. Includes the router for the whole smart-tv-app-development reference."
---

# Smart TV Apps: The Platform Landscape, the 10-Foot UI, and Focus and Input

> **Part 1 of 4** of the *Smart TV App Development* reference (plugin `smart-tv-app-development`), covering §0–§3. Sibling skills: `smart-tv-playback-drm-and-performance` (§4–§7), `smart-tv-monetization-certification-and-operations` (§8–§14), `smart-tv-reference` (§15–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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

## §0. Routing

### 0.1 The platform matrix

**[PLATFORM/VERSIONED — the single most important table in this document.]**

| Platform | Language / model | UI framework | Notes |
|---|---|---|---|
| **Roku OS** | **BrightScript** (proprietary, BASIC-like, dynamically typed, single-threaded interpreter) | **SceneGraph** (XML scene graph) | **No browser engine. No HTML/CSS/JS.** A wholly separate discipline |
| **Samsung Tizen** | **HTML/CSS/JS web app** | Your own / any web framework | Runs in a **model-year-frozen Chromium**. See §1.3 — this is the defining constraint |
| **LG webOS** | **HTML/CSS/JS web app** | Your own / **Enact** (React-based) | Same frozen-engine problem as Tizen |
| **Android TV / Google TV** | **Kotlin/Java** (or Compose for TV) | Leanback / **Jetpack Compose for TV** | Real native media stack (**Media3/ExoPlayer**), Widevine L1 |
| **Amazon Fire OS** | Android (AOSP fork) — Kotlin/Java | Leanback/Compose | ⚠️ Being **replaced** — see below |
| **Amazon Vega OS** | **React Native 0.72** or web (**Vega WebView**) | React Native for Vega | ⚠️ **Linux-based, NOT Android. APKs do not run.** New packaging (VPKG) |
| **Apple tvOS** | **Swift** (SwiftUI/UIKit) or **TVML/TVMLKit** | SwiftUI for TV | The most consistent hardware; smallest US share |
| **VIDAA** (Hisense), **whaleOS**, **webOS Hub**, **VIZIO SmartCast**, **Xumo**, **Titan OS** | Mostly web apps | varies | The long tail. Each is its own certification and QA burden |

**[DURABLE] There are three programming models, not eight**: **web apps** (Tizen, webOS,
VIDAA, most of the long tail, Vega WebView), **Android/Kotlin** (Android TV, Google TV,
Fire OS), and **proprietary** (Roku BrightScript, tvOS Swift, Vega React Native). Your
cross-platform strategy (§13 → `smart-tv-monetization-certification-and-operations`) is really a decision about how many of those three you're
willing to staff.

### 0.2 The question router

| Asked about... | Go to |
|---|---|
| Which platforms to target, market reality | §1 |
| The 10-foot UI, safe areas, typography, layout | §2 |
| Focus, spatial navigation, remote input | §3 |
| Video playback, HLS/DASH, ABR, players | §4 → `smart-tv-playback-drm-and-performance` |
| DRM and content protection | §5 → `smart-tv-playback-drm-and-performance` |
| Performance and memory on TV silicon | §6 → `smart-tv-playback-drm-and-performance` |
| App lifecycle, resume, deep linking, discovery feeds | §7 → `smart-tv-playback-drm-and-performance` |
| Monetization: subs, IAP, AVOD/FAST | §8 → `smart-tv-monetization-certification-and-operations` |
| CTV advertising: VAST, SSAI, ad pods, measurement | §9 → `smart-tv-monetization-certification-and-operations` |
| Certification and store submission | §10 → `smart-tv-monetization-certification-and-operations` |
| Testing on real devices | §11 → `smart-tv-monetization-certification-and-operations` |
| Analytics and QoE | §12 → `smart-tv-monetization-certification-and-operations` |
| Cross-platform strategy and frameworks | §13 → `smart-tv-monetization-certification-and-operations` |
| Accessibility, privacy, ACR, regulation | §14 → `smart-tv-monetization-certification-and-operations` |
| "Don't do this" | §15 → `smart-tv-reference` |
| "Which approach is better?" | §16 → `smart-tv-reference` (contested) |
| "Is this still current?" | §17 → `smart-tv-reference` |
| Docs, tools, people | §18 → `smart-tv-reference` |

---

## §1. The Platform Landscape

### 1.1 Who actually owns the living room

**[VERSIONED — and note that the numbers disagree wildly depending on what's being
measured.]** Three different, all-defensible framings:

- **US usage share** (Parks Associates, Streaming Video Tracker, April 2026, "device used
  most frequently to watch online video" in US broadband households): **Roku OS 28%,
  Samsung Tizen 23%**, with Amazon Fire TV, LG webOS, and VIZIO SmartCast mid-tier, and
  tvOS, consoles, and Android TV smaller.
- **US activated screens**: Roku OS around **38%**, with Google TV growing ~2.6%/year.
- **Global units shipped**: an entirely different ranking, where **Tizen and Android TV
  lead** because Samsung and the Android licensees ship the most TVs worldwide, and Roku
  barely registers outside North America.

**[DURABLE] Reconcile those before you plan.** *Installed base* ≠ *units shipped* ≠
*hours watched* ≠ *ad revenue*. Roku's US strength and near-absence in Europe is the
canonical trap for teams that read one number and built one app.

Rough scale anchors for 2026: **Android TV/Google TV crossed ~300M monthly active
devices** globally; **Roku passed ~100M streaming households**; **LG webOS is ~12%
overall but ~52% of the premium OLED tier**; and **smart-TV ownership is heading past
1.1 billion households**.

Parks Associates' framing is the one worth internalizing: *"Control of the platform layer
is central to competition in the connected TV market. Operating systems determine what
content consumers see, how services are positioned, and how advertising is delivered."*
A small number of OSes account for the majority of usage, **limiting visibility for
services without strong distribution partnerships** — which is a polite way of saying
discovery placement is negotiated, not earned.

### 1.2 The two structural shifts in progress

**[VERSIONED — both are live as of 2026 and both change build plans.]**

**Amazon is replacing Fire OS with Vega OS.** Vega is **Linux-based, built from the ground
up, and not Android** — it cannot natively run APKs. Apps are built with **React Native
0.72** ("React Native for Vega") or web via **Vega WebView**, packaged as **VPKG** rather
than APK. Timeline: first shipped on the **Fire TV Stick 4K Select (late 2025)**, then the
**Fire TV Stick HD (April 2026)**; Amazon's developer site states that **starting with the
4K Select, all future Fire TV Sticks run Vega**. Existing Fire OS devices are **not being
upgraded** and are supported with security updates through at least 2030 (or four years
from purchase).

What this means practically:
- **Porting is re-engineering, not recompiling** — new APIs, new packaging, and rewritten
  UI, focus management, and entitlement flows. React Native apps reuse the most.
- Amazon is **cloud-streaming selected apps** during the transition, with roughly nine
  months of free hosting, to buy publishers time to build native Vega versions.
- **Sideloading is gone** on Vega devices — Amazon Appstore only.
- **⚠️ You now support two Amazon platforms simultaneously**, indefinitely. That is a real
  and unwelcome addition to an already-fragmented matrix.

**Fox agreed to acquire Roku (announced April 2026, ~$22B cash-and-stock).** If it
completes, it shifts the strategic value of a TV OS further toward distribution and
advertising, and it will affect OS licensing and ad-supply negotiations. **Treat any
Roku commercial term as subject to change.**

### 1.3 The frozen-browser problem

**[PLATFORM — this is the single most under-anticipated constraint in TV development, and
it deserves its own section.]**

On Tizen and webOS your app is a web app running in the browser engine the TV shipped
with — **and that engine is never updated**. Samsung publishes the mapping, and it is
sobering:

| TV model year | Tizen | Web engine |
|---|---|---|
| **2026** | 10.0 | **Chromium M130** |
| 2025 | 9.0 | Chromium M120 |
| 2024 | 8.0 | Chromium M108 |
| 2023 | 7.0 | Chromium M94 |
| 2022 | 6.5 | Chromium M85 |
| 2021 | 6.0 | Chromium M76 |
| 2020 | 5.5 | Chromium M69 |
| 2019 | 5.0 | Chromium M63 |
| 2018 | 4.0 | Chromium M56 |
| 2017 | 3.0 | Chromium M47 |
| 2016 / 2015 | 2.4 / 2.3 | **WebKit** |

Read that table again: **a 2024 TV shipped with Chromium 108 while desktop Chrome was on
130.** A 2018 TV is on Chromium 56 — an engine from 2016. webOS has the same structure.

Consequences you must design around:
- **Your baseline is whatever the oldest model year you support shipped**, not "modern
  evergreen browsers." A team targeting 2019+ Samsungs is writing for **Chromium 63**.
- **Feature-detect, never version-sniff.** An API introduced in Chrome 110 works on 2025+
  sets and **fails silently** on everything older.
- **Transpile and polyfill aggressively**, and *test what your bundler actually emits* —
  a modern framework's default output targets browsers your fleet doesn't have.
- **⚠️ Teams routinely start with Next.js or a modern SPA framework and hit a wall**,
  because both platforms run considerably outdated Chromium. Budget for this in week one,
  not month four.
- **No webview embedding on Tizen** — the only way to embed external content is an
  `iframe`, which sites can refuse via frame-ancestors/X-Frame-Options.
- Old engines also mean **no security updates**: Chromium 56 and below are unsafe to run
  web content on at all.
- **[VERSIONED] Native binaries have their own cliff**: Samsung used **GCC 9.2.0 through
  the 2025 model year and moved to GCC 14.2.0 for 2026**, so any native library must be
  rebuilt for 2026 sets.

---

## §2. The 10-Foot UI

### 2.1 Why TV design is genuinely different

**[DURABLE] The name is the specification: the viewer is ~10 feet (3 m) away.** Everything
follows from that plus the D-pad:

| Constraint | Consequence |
|---|---|
| Viewing distance ~10× a phone | Everything must be far larger relative to the screen |
| No pointer | Only focusable elements are reachable — nothing is "clickable" |
| No hover | Every affordance must be visible in the default state |
| No text input worth the name | On-screen keyboards are miserable; minimize typing (§3.4) |
| Shared/social viewing | Others are watching you navigate. Errors are public |
| Lean-back intent | The user wants to *watch*, not to *operate a UI* |
| Ambient light varies wildly | Contrast must survive a sunlit room and a dark one |
| Overscan on older sets | Content near the edge may be physically cut off |

### 2.2 The numbers

- **Design canvas: 1920×1080**, scaled to 4K by the platform. Most platforms want 1080p
  assets; a few accept 4K UI. **Design at 1080p and let the compositor scale.**
- **Safe area: keep all UI inside ~90% of the screen** — i.e. a **5% margin on every
  side** (≈96 px horizontally, ≈54 px vertically at 1080p). Older sets overscan; text at
  the edge disappears.
- **Minimum body text ~24 px at 1080p**; titles 32–48 px. **Anything under ~18 px is
  unreadable at 10 feet** regardless of what it looks like on your monitor.
- **Focusable targets ≥ 60–80 px** in their smallest dimension, with clear separation.
- **Contrast**: aim well above the WCAG 4.5:1 minimum. **Avoid pure white (#FFFFFF) on
  large areas** — on a bright HDR panel in a dark room it's genuinely painful; use ~#F0F0F0
  or lower. Similarly avoid pure black backgrounds on OLED for UI chrome that persists.
- **Avoid thin fonts and hairline strokes.** Compression, upscaling, and chroma subsampling
  destroy them.
- **Frame budget: 16.6 ms at 60 Hz** — and TV silicon will miss it far more easily than
  a phone (§6 → `smart-tv-playback-drm-and-performance`).

### 2.3 The standard layout vocabulary

**[DURABLE] TV UI has converged on a small set of patterns, and deviating from them costs
you.** Users navigate a dozen apps with the same muscle memory:
- **The rail/row grid** — horizontal shelves of posters, vertically stacked by category.
  This is *the* content-browse pattern on every platform.
- **Hero/spotlight** at the top with a featured item.
- **Left sidebar nav**, often collapsed to icons until focused.
- **Detail page** — big art, synopsis, a primary CTA (Play/Resume) that must be the first
  focused element.
- **Player with a transport overlay** that auto-hides.
- **Grid** for search results and full catalogues.

**⚠️ Do not invent a novel navigation model.** The cost is not aesthetic — a user who
can't find the back-out path with a D-pad simply leaves, and you will never learn why.

---

## §3. Focus and Input

### 3.1 Focus is the architecture

**[DURABLE] On TV, "what is focused" is application state as fundamental as "what page am
I on."** Get this wrong and nothing else matters.

The rules:
1. **Exactly one thing is focused at all times.** Never zero. If a focused element is
   removed, you must explicitly move focus somewhere sensible — this is the single most
   common TV bug, and it manifests as a **completely dead remote**.
2. **The focus indicator must be unmissable** — scale, border, glow, and/or brightness.
   A subtle 1 px outline is invisible at 10 feet. Use at least two visual channels.
3. **Focus must be predictable**: pressing Right then Left should return you where you
   were. Users build a spatial model, and violating it feels broken even when it isn't.
4. **Restore focus on return** — coming back from a detail page must land on the tile you
   left from, not the start of the row.
5. **Set initial focus on every screen**, on the primary action.

### 3.2 Spatial navigation

The engine that decides, given the currently focused element and a direction, what gets
focus next. Approaches:
- **Geometric** — compute the nearest candidate in the direction pressed, using overlap
  and distance heuristics. Flexible, and produces surprising results with irregular layouts.
- **Explicit graph** — declare each element's up/down/left/right neighbours. Predictable;
  tedious; and the right answer for complex screens.
- **Hybrid** — geometric by default with explicit overrides. **What most production apps
  end up doing.**

**[PLATFORM]** Roku's SceneGraph has focus built into the node hierarchy
(`setFocus`, `focusable`); Android TV uses the Android focus system plus
`nextFocusUp/Down/Left/Right` (and Compose for TV's focus APIs); web platforms have
**CSS `spatial-navigation`** in limited/uneven form, so most teams ship a JS library or
their own engine; tvOS has the **focus engine** with focus guides.

> **⚠️ GOTCHA — the classic focus traps.** Focus lands on an off-screen element and the
> user sees nothing move. Focus enters a container it cannot leave. A modal opens without
> capturing focus, so D-pad presses go to the page behind it. A carousel wraps
> inconsistently at the ends. Async content loads and steals focus mid-navigation.
> **Every one of these presents to the user as "the remote stopped working."**

### 3.3 The remote

**[DURABLE] Assume the minimal remote**: D-pad + OK, Back, Home, and maybe
Play/Pause/FF/RW. Everything else is optional and varies by manufacturer, model year, and
whether it's the OEM remote or a universal one.

- **Back must always work and must be predictable.** Back from the player returns to
  detail; back from detail returns to the row; back at the root exits the app (usually
  with a confirmation). **Never trap the user.**
- **Home always exits**, immediately, and you don't get to intervene. Save state
  *continuously*, not on exit.
- **Long-press, key-repeat, and rapid input** — users hold Down to scroll a long row.
  Your list must handle a burst of repeats without falling behind or crashing; debounce
  navigation, and never do heavy work per keypress.
- **Voice** is a first-class input on most platforms (Alexa, Google Assistant, Bixby, and
  in 2026 the LG webOS integrations with Copilot and Gemini) — mostly consumed as
  **deep-link intents** (§7.3 → `smart-tv-playback-drm-and-performance`) rather than in-app.
- **Colour buttons** (red/green/yellow/blue) exist in European broadcast contexts and are
  frequently the right answer for secondary actions there.

### 3.4 Text entry

**[DURABLE] Typing on a TV is so bad that avoiding it is a design requirement, not a
nicety.** Entering a password with a D-pad on an on-screen grid keyboard takes a minute
and fails often. The answers, in order of preference:
1. **Device-code pairing** — show a short code, user enters it on their phone at a URL.
   **This is the standard and correct pattern for sign-in.** Roku's "on-device
   authentication" work is in this family.
2. **Account linking via the platform identity** where offered.
3. **QR code** on screen to hand off to a phone.
4. Voice input for search.
5. Only then, an on-screen keyboard — and if you must, support the platform's native one
   rather than rolling your own.
