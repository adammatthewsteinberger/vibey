---
name: browser-development-reference
description: "Use when reviewing browser or web-platform work for known anti-patterns, weighing contested questions (Manifest V3, how much capability the web should have, the engine monoculture, Site Isolation's cost, JIT or no JIT, fingerprinting strategy, blocking ads by default, living standards vs versioned specs), checking whether an engine, standard, or privacy-policy claim is still current (snapshot verified August 2026), finding the primary sources, books, people, and channels, or needing the numbers, 'why is this page slow' triage order, and browser security review checklist. Companion to the other web-browser-development skills."
---

# Browser Development: Anti-Patterns, Contested Questions, Currency, and Canon

> **Part 5 of 5** of the *Web Browser Development* reference (plugin `web-browser-development`), covering §15–§20. Sibling skills: `browser-engine-architecture-and-networking` (§0–§3), `browser-rendering-pipeline` (§4–§7), `browser-security-and-privacy` (§8–§9), `browser-extensions-platform-and-standards` (§10–§14). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Verified August 2026. See §17 below for the currency snapshot and what goes stale first.

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

## §15. Anti-Patterns

| Anti-pattern | Why | Instead |
|---|---|---|
| Trusting an origin claimed by a renderer | Compromised renderer = full cross-site read | Re-derive and validate in the browser process (§8.4 → `browser-security-and-privacy`) |
| Giving a renderer direct file/network/device access | Removes the sandbox's entire point | Broker through validated IPC |
| Unvalidated sizes/indices/handles over IPC | Memory corruption in the privileged process | Validate every field; fuzz the surface |
| Custom HTML error recovery | Compatibility divergence from the whole web | Implement the spec algorithm exactly (§4.1 → `browser-rendering-pipeline`) |
| Left-to-right selector matching | Pathological performance | Right-to-left + bloom filters (§5.2 → `browser-rendering-pipeline`) |
| Recomputing all style on any mutation | Jank | Invalidation sets (§5.3 → `browser-rendering-pipeline`) |
| Mutable layout tree holding inputs and outputs | Unpredictable incremental layout | Immutable fragment tree (§6.2 → `browser-rendering-pipeline`) |
| Doing scroll or transform animation on the main thread | Jank whenever JS is busy | Property trees + compositor thread (§6.1 → `browser-rendering-pipeline`) |
| `will-change` on everything | GPU memory exhaustion | Layerize deliberately |
| Interleaving geometry reads and style writes | Forced synchronous layout, N× cost | Batch reads, then writes (§7.3 → `browser-rendering-pipeline`) |
| Sniffing content into an executable type | XSS vector | Honour `nosniff`; restrict sniffing |
| Shipping an XSS filter as a security boundary | Bypassable; introduces its own bugs; all were removed | CSP + Trusted Types (§8.3 → `browser-security-and-privacy`) |
| Unpartitioned storage or cache | Cross-site tracking and timing side channels | Partition everything by top-level site (§9.2 → `browser-security-and-privacy`) |
| High-resolution timers plus shared-process secrets | Spectre | Coarsen timers; isolate by site (§8.6 → `browser-security-and-privacy`) |
| Adding a capability API without an entropy review | Permanent fingerprinting surface | Review entropy and permission model together (§9.3 → `browser-security-and-privacy`, §11 → `browser-extensions-platform-and-standards`) |
| Shipping a web feature without an exit plan | You can never remove it | Origin trial + use counters first (§14 → `browser-extensions-platform-and-standards`) |
| Prefixed CSS properties | `-webkit-` became a de facto standard other engines had to implement | Flags and origin trials, never prefixes |
| Reverse-engineering another engine's quirks instead of specifying them | Perpetuates the divergence | Spec it, add WPT, take it to Interop (§13 → `browser-extensions-platform-and-standards`) |
| Treating accessibility as a post-architecture concern | It crosses the process boundary; retrofitting is expensive | Design the a11y tree with the process model (§12 → `browser-extensions-platform-and-standards`) |
| Assuming the network service is trusted | It parses hostile input for all sites at once | Sandbox and memory-harden it (§3.1 → `browser-engine-architecture-and-networking`) |

---

## §16. Contested Questions

**16.1 Manifest V3.** §10.2 → `browser-extensions-platform-and-standards`. Real security argument; real conflict of interest; Firefox
demonstrating that supporting both is technically possible.

**16.2 Capability APIs — how much should the web be able to do?** §11 → `browser-extensions-platform-and-standards`. Chrome's "the web
should match native" versus Apple's and Mozilla's "every API is attack surface and
fingerprinting entropy." Both coherent; the disagreement is about risk appetite and,
inescapably, about business models.

**16.3 The engine monoculture.** *For consolidation*: one excellent open-source engine
beats five mediocre ones; interop problems vanish. *Against*: 81% share means one vendor's
priorities become web policy, "works in Chrome" replaces "follows the spec," and there's no
check on capability expansion. Note that the counterweight is weakening — Gecko is at ~3%
and Mozilla's revenue depends largely on a Google search deal.

**16.4 Site Isolation's cost.** §2.2 → `browser-engine-architecture-and-networking`. Chromium's own docs concede the process-count ceiling,
especially on Android. The emerging answer is memory-safe languages buying back the
isolation that processes were paying for.

**16.5 JIT or no JIT.** §7.1 → `browser-rendering-pipeline`. Ladybird's no-JIT position and Apple's JIT entitlement
restrictions on iOS come from the same reasoning: JITs are enormous exploit surfaces.
The cost is performance, and nobody has shown a no-JIT engine that's competitive on
JS-heavy sites.

**16.6 Fingerprinting: randomize or uniformize.** §9.3 → `browser-security-and-privacy`.

**16.7 Should the browser block ads by default?** Brave does; others don't. It's a
security control (malvertising), a privacy control, and an existential threat to the
ad-funded web simultaneously.

**16.8 Living standards vs. versioned specs.** Living standards track reality and never go
stale; they also mean "conformant" is not a fixed target, which is hard for anyone
building an independent implementation — a point Ladybird and Servo feel directly.

---

## §17. Currency Snapshot — verified August 2026

| Thing | Status as of Aug 2026 | Decay risk |
|---|---|---|
| **Engine share** | Blink **~81%**, WebKit **~14%**, Gecko **~3%** (desktop+mobile+tablet, ~May 2026). Remaining ~1%: Goanna, Flow, Servo, Ladybird | Low |
| **Ladybird** | Independent C++ engine (LibWeb/LibJS), non-profit-backed, ~7–10 FT engineers, no code from other engines, no search-deal funding. **Alpha targeted 2026 (Linux/macOS), beta 2027, stable 2028.** Roadmap (not shipped): Rust style/layout, sandboxing, GPU isolation, Wasm GC | **High** |
| **Servo** | Rust, embeddable, parallel; under **Linux Foundation Europe**; components (Stylo, WebRender) shipped in Firefox. Positioned as a webview, not a browser | Medium |
| **Third-party cookies** | ⚠️ **Not being deprecated in Chrome.** 22 Jul 2024 first reversal; **22 Apr 2025** confirmed current approach with **no standalone prompt**. Safari/Firefox/Brave still block by default (~17–20% of traffic) | Medium |
| **Privacy Sandbox** | ⚠️ **Mostly shut down.** On **17 Oct 2025** Google retired most APIs (Topics, Protected Audience, Attribution Reporting, Private Aggregation, IP Protection, Related Website Sets) citing low adoption. Deprecated in **Chrome 144 (Jan 2026)**, full removal targeted **Chrome 150 (Jul 2026)**. Continuing focus: privacy-preserving measurement, FedCM, CHIPS | Medium |
| **Manifest V2** | ⚠️ **Essentially dead in Chrome.** By **June 2026** Chromium removed `kExtensionManifestV2Disabled`; Chrome 150/151 remove the last overrides. Edge and Opera follow. **Full uBlock Origin unavailable on Chrome** (uBO Lite only); available on **Firefox and Brave**. Firefox retains **both MV2 and MV3 with blocking `webRequest`** | Medium |
| **Interop** | **Interop 2026** is the fifth year (Apple, Google, Igalia, Microsoft, Mozilla). **Interop 2025 finished with an overall score of 95 (from 25); Firefox went 46 → 99.** 2026 areas: cross-document view transitions, `attr()`, `contrast-color()`, custom highlights, scroll-driven animations, scroll snap, `shape()`, Navigation API `precommitHandler`, scoped `CustomElementRegistry`, fetch streaming bodies, mobile testing | Medium |
| **Baseline** | **Trusted Types** reached Baseline **February 2026**; also `shape()`, **zstd**, Navigation API. *Newly available* = all major engines; *Widely available* = +30 months | Medium |
| **Chrome memory safety** | MiraclePtr expanding to **Skia, ANGLE, Dawn, C++ iterators, `std::` containers**; **MiracleObject on the GPU main thread targeting ~90% of UAFs there**; "spanification" against OOB; UBSan `-fsanitize=return` default in release; **PartitionAlloc in Skia**; **`ChildProcessSecurityPolicy` being migrated to Rust** (Canary experiment) plus an initial **Rust Mojo client**; exploring an **HTML/CSS/TypeScript top-level UI** | **High** |
| **AI in browser security** | Google's early-2026 Gemini-based agent harness found a **sandbox escape that had survived >13 years** in Chrome's codebase | **High** |
| **Site Isolation ceiling** | Chromium docs state plainly that sandboxing and site isolation are reaching their limits — processes are not cheap, especially on Android where extra processes cause background activities to be killed more often | Low |

**Goes stale fastest:** Chrome's memory-safety program and AI-assisted vuln finding;
Ladybird's alpha timeline; MV2 removal specifics; Privacy Sandbox removal milestones.
**Essentially never stale:** §2.1 → `browser-engine-architecture-and-networking`–2.4 (process model and IPC discipline), §4.1 → `browser-rendering-pipeline` (HTML
parsing), §5.1 → `browser-rendering-pipeline`–5.2 (cascade and selector matching), §6.1 → `browser-rendering-pipeline`–6.2 (pipeline and immutability),
§7.3 → `browser-rendering-pipeline` (event loop), §8.1 → `browser-security-and-privacy`–8.4 (security model), §15 (anti-patterns).

---

## §18. The Canon

### 18.1 Primary sources — overwhelmingly the best material

- **The specifications themselves**, and they are unusually readable:
  **html.spec.whatwg.org** (the parsing algorithm in §4.1 → `browser-rendering-pipeline` is worth reading in full),
  **dom.spec.whatwg.org**, **fetch.spec.whatwg.org**, **url.spec.whatwg.org**, the
  **CSS specs** at `drafts.csswg.org`, and **HTML Standard §"event loops."**
- **Chromium documentation** — `chromium.org` and `chromium.googlesource.com/chromium/src/+/main/docs/`.
  Specifically: the **Site Isolation design doc**, `process_model_and_site_isolation.md`,
  the **memory safety** page (unusually honest about limits), and the **Chrome Security
  quarterly updates**, which are the single best running account of browser security
  engineering anywhere.
- **RenderingNG series** on `developer.chrome.com/docs/chromium/` — overview, architecture,
  **key data structures**, **BlinkNG**, **LayoutNG**, VideoNG. Chris Harrelson et al. This
  is the best public description of a modern rendering engine's architecture, full stop.
- **Mozilla**: `firefox-source-docs.mozilla.org`, **Mozilla Hacks** (Stylo, WebRender,
  Quantum, and Fission write-ups), the **Mozilla standards-positions** repo.
- **WebKit blog** (`webkit.org/blog`) — especially the Interop and ITP posts.
- **web.dev** and **MDN** — MDN is the de facto platform reference; web.dev carries
  Baseline and the Chrome rendering/performance material.
- **Web Platform Tests** (`web-platform-tests.org`, `wpt.fyi`) and the
  **Interop dashboard**.
- **Ladybird** (`ladybird.org`, and the GitHub repo) and **Servo** (`servo.org`) —
  both are readable codebases in a way the big three are not, which makes them excellent
  learning material even if you never ship them.

### 18.2 Books and long-form

| Work | Why |
|---|---|
| **Tali Garsiel & Paul Irish, "How Browsers Work"** | The classic single-article overview. Dated in specifics, correct in shape |
| **"Web Browser Engineering" (Panchekha & Harrelson)** | **Free online.** Build a browser in Python, chapter by chapter. **The best hands-on introduction that exists** |
| **Alan Grosskurth & Michael Godfrey**, "A Reference Architecture for Web Browsers" | The academic framing of the component decomposition |
| **Michal Zalewski, *The Tangled Web*** | The best book on web security's actual model and its historical accidents |
| **Ryan Barnett / OWASP materials**; **Google's Web Fundamentals security docs** | Practical |
| **Ilya Grigorik, *High Performance Browser Networking*** | **Free online.** The networking reference (§3 → `browser-engine-architecture-and-networking`) |
| **Lin Clark's cartoon deep-dives** (Mozilla) | Stylo, WebRender, and Wasm explained better than anywhere else |
| **"Inside look at modern web browser"** (Mariko Kosaka, Chrome) | A clear four-part architecture series |

### 18.3 People and channels
Chris Harrelson (Blink rendering), Charlie Reis and Adrienne Porter Felt (Chrome security
and Site Isolation), Andreas Kling (Ladybird — his development streams are unusually good
teaching material), Lin Clark (Mozilla), Ilya Grigorik (networking), Alex Russell
(platform, opinionated and worth reading precisely for that), Jen Simmons and Rachel
Andrew (CSS layout), Anne van Kesteren (WHATWG specs), Michal Zalewski (web security).
Follow the **blink-dev** and **mozilla.dev.platform** intent-to-ship threads if you want
to see the platform being decided in public.

---

## §19. Quick Reference

### 19.1 Numbers
- Frame budget: **16.6 ms @ 60 Hz**, **8.3 ms @ 120 Hz** — for *everything*.
- Engine share: Blink **~81%**, WebKit **~14%**, Gecko **~3%**.
- Interop 2025 overall score: **25 → 95**; Firefox **46 → 99**.
- Baseline *Widely available* = *Newly available* **+ 30 months**.
- Memory-safety bugs ≈ **70%** of serious browser vulnerabilities historically.
- MiracleObject target: neutralize up to **90%** of GPU-main-thread UAFs.
- ~**17–20%** of global traffic blocks third-party cookies by default regardless of Chrome.

### 19.2 "Why is this page slow?" — triage order
1. **Network**: TTFB, blocking subresources, no preload, no compression, uncached.
2. **Main thread**: long tasks, parse/compile cost, forced synchronous layout (§7.3 → `browser-rendering-pipeline`).
3. **Style**: huge selector count, invalidation storms from class toggles on ancestors.
4. **Layout**: layout thrashing, deep flex/grid nesting, table layout.
5. **Paint/raster**: large paint areas, no layer promotion, or too many layers.
6. **Compositing**: main-thread scroll (non-passive listeners), non-composited animations.
7. **GPU/memory**: texture memory exhaustion, checkerboarding.

### 19.3 Browser security review checklist
- [ ] Does this feature let a renderer assert something the browser process trusts?
- [ ] Is every IPC field validated in the privileged process?
- [ ] Does it read cross-origin data into a renderer that shouldn't have it? (CORB/ORB)
- [ ] Does it add a timing signal usable for Spectre?
- [ ] Does it add fingerprinting entropy, and has that been quantified?
- [ ] Is it restricted to secure contexts? Permissions-Policy delegable?
- [ ] Is storage partitioned by top-level site?
- [ ] What is the permission UX, and can it be spoofed by page content?
- [ ] Does it parse untrusted binary input, and in what language, in which process?
- [ ] Is there an origin trial, a use counter, and a removal path?

---

## §20. Sources and Method

**Method.** Narrative (not systematic) review. Durable material — §2 → `browser-engine-architecture-and-networking` (process model and IPC
discipline), §4.1 → `browser-rendering-pipeline` (HTML parsing), §5 → `browser-rendering-pipeline` (cascade and matching), §6 → `browser-rendering-pipeline` (pipeline architecture),
§7.3 → `browser-rendering-pipeline` (event loop), §8.1 → `browser-security-and-privacy`–8.4 (security model), §12 → `browser-extensions-platform-and-standards` (accessibility), §15 (anti-patterns) —
is synthesized from the specifications and from engine documentation listed in §18. Every
**time-sensitive** claim (engine shares, project status, policy changes, security-program
specifics) was verified against a primary or near-primary source in **August 2026** and is
flagged in §17 with a decay-risk rating. Where vendors genuinely disagree, §16 presents
both cases — and names the commercial interest where it is material to the disagreement,
because in this domain it usually is.

**Search log** (August 2026): browser engine landscape and Ladybird/Servo status ·
Privacy Sandbox and third-party cookie policy · Interop 2026 and Baseline · Chrome site
isolation, sandboxing, and memory safety · Manifest V3 and the extension platform ·
RenderingNG, BlinkNG, and LayoutNG architecture.

**Primary and near-primary sources consulted (selected):**
- **chromium.org** — Site Isolation design doc and overview; `process_model_and_site_isolation.md`;
  the **memory safety** page; **Chrome Security quarterly updates**
- **developer.chrome.com** — the **RenderingNG** series (overview, architecture, key data
  structures, BlinkNG, LayoutNG), Chris Harrelson et al.
- **blog.google / Google Security** — "Stronger with every update: How we're making Chrome
  and the web safer in the AI Era" (2026); **SecurityWeek** coverage of the 13-year-old
  flaw found by Google's agent harness
- **privacysandbox.google.com** — "Next steps for Privacy Sandbox and tracking protections
  in Chrome"; contemporaneous reporting on the Oct 2025 API retirements
- **web.dev** — Interop 2026 announcement, Baseline monthly digests; **webkit.org** —
  "Announcing Interop 2026"; **hacks.mozilla.org** — "Launching Interop 2026";
  **web-platform-tests/interop** 2026 README
- **ladybird.org** and the Ladybird W3C/TPAC session description; **servo.org** and Servo's
  W3C presentation materials
- **ublockorigin.com** and the uBlock wiki on MV2 deprecation; **Mozilla Blog** on its MV3
  approach; **Neowin**, **The Register**, **PCWorld** on the MV2 flag removals
- WHATWG and W3C specifications as cited throughout

**Confidence statement.** **High confidence** in §2–§8 → `browser-engine-architecture-and-networking`, `browser-security-and-privacy` and §11–§15 → `browser-extensions-platform-and-standards`, §18–§19 — these rest on
specifications and first-party engine documentation, much of it unusually candid.
**High confidence** in §17's verified items as of the stated date. **Moderate confidence**
in the engine market-share figures in §1.1 → `browser-engine-architecture-and-networking` and §19.1: browser share is measured by
analytics vendors with known sampling biases, varies by region and device class, and the
~81/14/3 split should be read as approximate and directional. **Moderate confidence** in
§9.1 → `browser-security-and-privacy`'s timeline granularity — the third-party-cookie story reversed twice and secondary
sources disagree about which date was "the" reversal, so the dates here follow Google's own
posts and are given as a sequence rather than a single event. The Ladybird timeline in
§1.1 → `browser-engine-architecture-and-networking` and §17 is a **project target**, not a shipped fact, and such targets have slipped
before across this entire field.
