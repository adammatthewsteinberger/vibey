---
name: browser-extensions-platform-and-standards
description: "Use when working on the web platform surface around the engine: extension architecture and Manifest V3 precisely, storage (cookies, IndexedDB, quotas), media (codecs, EME, WebRTC), capability APIs, the accessibility tree and assistive-technology integration, how the web is specified (WHATWG, W3C, TC39, living standards), Interop and Baseline, and testing (web-platform-tests), telemetry, and shipping."
---

# Browser Development: Extensions, Storage, Media, and Capabilities, Accessibility, Standards and Interop, Testing and Shipping

> **Part 4 of 5** of the *Web Browser Development* reference (plugin `web-browser-development`), covering §10–§14. Sibling skills: `browser-engine-architecture-and-networking` (§0–§3), `browser-rendering-pipeline` (§4–§7), `browser-security-and-privacy` (§8–§9), `browser-development-reference` (§15–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Verified August 2026. See §17 → `browser-development-reference` for the currency snapshot and what goes stale first.

> **How to read this.** Reference, not tutorial. Sections are independent. Three markers:
> - **[DURABLE]** — architecture, algorithms, or a constraint every engine has
>   independently arrived at. Does not expire.
> - **[ENGINE]** — specific to Blink/Chromium, Gecko, WebKit, or Servo/Ladybird. Verify
>   against that project's source or docs.
> - **[CONTESTED]** — the vendors genuinely disagree, often because their business models
>   differ. Both cases given, including the commercial motive where it's load-bearing.
>
> **⚠️ GOTCHA** boxes mark the mistakes that produce security holes, jank, or
> compatibility breakage that can never be undone.
>
> **The two framings that organize everything below:**
> 1. **A browser is a hostile-input execution environment that must never say no.** It
>    runs untrusted code from anyone, on documents that are frequently malformed, and it
>    is not permitted to refuse or crash. Every architectural decision — the multi-process
>    model, the error-tolerant parser, the sandbox — descends from that.
> 2. **The web's compatibility constraint is stronger than any other platform's.** You
>    cannot break existing sites. Not the well-written ones, not the abandoned ones. This
>    is why the platform accretes and rarely subtracts, and why "just fix it properly"
>    is almost never available.

---

## §10. Extensions

### 10.1 The architecture

Manifest, background context (persistent page → **service worker** in MV3), content scripts
(isolated worlds sharing a DOM), permission model, and — the crux — the network
interception API.

### 10.2 Manifest V3, precisely

**[VERSIONED, and the most politically charged topic in browser development.]**

MV3 replaced the **blocking `webRequest`** API — which let an extension observe and modify
each request in real time — with **`declarativeNetRequest`**, where the extension registers
static rules in advance and the browser applies them.

**Google's stated rationale**: security (no remote code execution, no arbitrary
request-time interception), privacy (the extension never sees request contents), and
performance.

**The consequences, as they actually landed:**
- **uBlock Origin's full version cannot be implemented under MV3.** Chrome users get
  **uBlock Origin Lite**, a reduced-functionality build; the author has stated there is no
  MV3 version of uBO proper.
- **MV3 caps the number of filtering rules** and eliminates the dynamic blocking that is
  effective against rapidly-changing ad delivery.
- Timeline: Chrome Web Store warnings from June 2024; auto-disabling from early 2025;
  **by June 2026 Chromium removed the `kExtensionManifestV2Disabled` feature flag** that
  had allowed controlled MV2 availability, with **Chrome 150/151 removing the last
  overrides**. Edge and Opera follow Chromium.
- **Firefox supports both MV2 and MV3, and retains blocking `webRequest` alongside
  `declarativeNetRequest`** — a deliberate divergence, stated in terms of Mozilla's
  manifesto principle that individuals must be able to shape their own experience.
  Full uBO remains available on Firefox and Brave.

**[CONTESTED — and state the conflict of interest plainly, because it's material.]**
*For MV3*: the security argument is real — blocking `webRequest` gave every extension
plaintext access to all traffic, and extension compromise is a genuine and recurring attack
vector. *Against*: Google's advertising revenue creates an obvious conflict when the
capability being removed is the one that makes ad blocking effective; **CISA has
recommended ad blockers as a defence against malvertising**, so this is a security
trade-off in both directions, not security versus convenience.

**[DURABLE] If you're designing an extension platform, the real lesson is that the network
interception API *is* the policy.** Whatever you allow there determines what class of
extension can exist, and you will not be able to change it later without a multi-year
migration and a public fight.

---

## §11. Storage, Media, and Capabilities

**Storage**: cookies, localStorage/sessionStorage (synchronous — a main-thread hazard),
**IndexedDB** (the real database), Cache API, Origin Private File System, and the
**Storage Standard**'s quota and eviction model. **All of it must be partitioned** (§9.2 → `browser-security-and-privacy`),
and all of it needs a clear "clear browsing data" story.

**Service workers** — a programmable proxy for a scope, with a lifecycle (install →
activate → idle → terminate) that is a common source of both bugs and confusion. They are
also a persistence mechanism with security implications.

**Media**: the codec matrix (H.264/AVC, VP9, AV1, HEVC — with **patent licensing driving
which engine ships what**), Media Source Extensions, **Encrypted Media Extensions and
CDMs** (proprietary binary blobs in your process — sandbox them), WebCodecs, WebRTC,
autoplay policy, and hardware decode paths.

**Capability APIs** — WebUSB, WebBluetooth, WebSerial, WebHID, WebNFC, File System Access,
WebGPU, geolocation, notifications.
**[CONTESTED] The capability question is the deepest philosophical split between engines.**
Chrome ships them behind permission prompts, arguing the web should be able to do what
native can. Apple and Mozilla have declined many, citing attack surface and fingerprinting
entropy. *Both positions are coherent*: every capability is simultaneously a user
empowerment and a new way to be attacked or identified. There is no neutral answer, and
"the other engine is just being obstructive" is usually wrong.

---

## §12. Accessibility

**[DURABLE] The browser builds a parallel tree — the accessibility tree — derived from the
DOM, computed styles, and ARIA, and exposes it to platform APIs** (UIA on Windows, NSAccessibility
on macOS, AT-SPI on Linux, AccessibilityNodeInfo on Android).

What that requires: computing role, name (per the **accname** spec — a genuinely intricate
algorithm), state, and relations for every node; keeping the tree updated on mutation;
firing platform events; handling focus order and keyboard interaction; honouring OS
settings (**reduced motion, increased contrast, forced colors, larger text**); and
supporting caret browsing and text ranges.

**⚠️ The accessibility tree lives in the renderer, but assistive technology talks to the
browser process** — so it crosses the security boundary, and in a Site Isolation world it
must be assembled across processes. This is real, under-discussed engineering work, and
it's why accessibility regressions cluster around architectural changes.

---

## §13. Standards and Interop

### 13.1 How the web is specified

**WHATWG** maintains **living standards** (HTML, DOM, Fetch, URL, Streams) — continuously
updated, no versions. **W3C** handles CSS (per-module levels), WebRTC, WebAuthn, and
accessibility. **TC39** owns JavaScript, with a staged proposal process. **IETF** owns HTTP,
TLS, QUIC.

**[DURABLE] The web's specs are unusual in being written to describe what implementations
must do down to error cases** (§4.1 → `browser-rendering-pipeline`). That's a response to a specific historical failure —
under-specified standards produced incompatible engines, and the compatibility debt is
permanent.

**Web Platform Tests (WPT)** is the shared, cross-vendor conformance suite and the
mechanism that makes "interoperable" measurable rather than aspirational.

### 13.2 Interop and Baseline

**[VERSIONED]** The **Interop** project — Apple, Google, Igalia, Microsoft, and Mozilla —
picks a shared set of focus areas each year, measured by WPT pass rate, and works them
together. **2026 is the fifth year.**

The 2025 results are the strongest argument for the process: **the overall Interop score
across all four browsers went from 25 to 95, and Firefox's own score went from 46 to 99.**
Features that reached cross-browser availability through it include Same-Document View
Transitions, CSS Anchor Positioning, the Navigation API, `@scope`, and URLPattern.

**Interop 2026** focus areas include cross-document view transitions, `blocking="render"`,
`<link rel="expect">`, `:active-view-transition-type()`, the CSS `attr()` function,
`contrast-color()`, custom highlights, scroll-driven animations, scroll snap, `shape()`,
the Navigation API's `precommitHandler`, scoped `CustomElementRegistry`, fetch streaming
request bodies, plus a continuing **mobile testing** investigation.

**Baseline** is the companion developer-facing signal: *Newly available* (works in the
current version of all major engines) vs. *Widely available* (30 months later). Recent
Baseline arrivals include **Trusted Types**, the CSS `shape()` function, **zstd** content
encoding, and the Navigation API.

**[DURABLE] For an engine implementer, WPT + Interop + Baseline is the closest thing to an
objective definition of "done."** Ship a feature, pass the tests, watch the dashboard.

---

## §14. Testing, Telemetry, and Shipping

**Testing layers**: unit tests; **WPT** for conformance; **reference tests** (render two
documents that should look identical — the standard technique for layout and paint, since
pixel-exact expectations are unmaintainable across platforms); pixel tests with tolerance;
performance benchmarks (Speedometer, JetStream, MotionMark) *plus* real-page corpora;
**fuzzing** (Domato-style DOM fuzzers, IPC fuzzers, format fuzzers — a browser is one of
the most-fuzzed artifacts in existence); and cluster-scale **crawler-based regression
testing** against millions of real sites, because real sites are the actual spec.

**Shipping a web feature** — the process every engine now follows in some form: an
explainer, a spec, cross-vendor **standards positions**, security and privacy review,
WPT coverage, an **origin trial** (time-limited real-world testing on real sites), a
**use-counter** measuring how much of the web touches it, then enable by default —
and the knowledge that **you can essentially never remove it afterwards** without a
deprecation trial and a use-counter approaching zero.

**Release cadence**: Chrome and Firefox ship roughly every 4 weeks with channels
(canary/nightly → dev/beta → stable) and staged percentage rollouts with kill switches.
**A browser is an always-on auto-update channel into hundreds of millions of machines** —
that pipeline is itself critical security infrastructure.
