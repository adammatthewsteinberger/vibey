---
name: browser-engine-architecture-and-networking
description: "Use when working on or reasoning about browser architecture: the anatomy of a browser (the router for the whole web-browser-development reference), who actually renders the web (Blink, WebKit, Gecko, Servo, Ladybird) and what it costs to build one, what a browser is besides an engine, why multiple processes, Site Isolation, sandboxing per platform, IPC design, and the networking stack — HTTP/1.1, HTTP/2, HTTP/3 and QUIC, TLS, DNS, and caching."
---

# Browser Development: The Engine Landscape, Process Model and Sandboxing, and Networking

> **Part 1 of 5** of the *Web Browser Development* reference (plugin `web-browser-development`), covering §0–§3. Sibling skills: `browser-rendering-pipeline` (§4–§7), `browser-security-and-privacy` (§8–§9), `browser-extensions-platform-and-standards` (§10–§14), `browser-development-reference` (§15–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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

## §0. Routing

### 0.1 The anatomy

```
┌────────────────────────────────────────────────────────────────────────┐
│ BROWSER PROCESS (privileged)                                           │
│   UI · tab/window management · profile & storage · permissions         │
│   navigation & session history · extension host · IPC broker           │
└───────┬─────────────────┬──────────────────┬───────────────────────────┘
        │ IPC             │ IPC              │ IPC
┌───────▼──────┐  ┌───────▼────────┐  ┌──────▼───────┐  ┌───────────────┐
│ RENDERER     │  │ NETWORK        │  │ GPU          │  │ UTILITY       │
│ (sandboxed,  │  │ SERVICE        │  │ PROCESS      │  │ (audio, media │
│  one per     │  │ HTTP/TLS/cache │  │ raster, draw │  │  codecs, data │
│  site)       │  │ cookies, DNS   │  │ compositing  │  │  decoders)    │
│              │  └────────────────┘  └──────────────┘  └───────────────┘
│  ┌─────────────────────────────────────────────┐
│  │ HTML parser → DOM                            │
│  │ CSS parser → CSSOM → style resolution        │
│  │ LAYOUT → PAINT (display lists) → COMMIT      │
│  │ JS engine (heap, JIT) · event loop            │
│  │ compositor thread (scroll, transform anims)   │
│  └─────────────────────────────────────────────┘
└──────────────┘
```

**[DURABLE] The single most important architectural fact: the renderer is assumed to be
compromised.** It is sandboxed, it has no filesystem or network access of its own, and
every privileged operation goes through an IPC message that the browser process must
independently validate. **Never trust a renderer's claim about its own origin** — that is
the whole ballgame (§8.4 → `browser-security-and-privacy`).

### 0.2 The question router

| Asked about... | Go to |
|---|---|
| Engine landscape, who builds what, why it matters | §1 |
| Process model, IPC, sandboxing, site isolation | §2 |
| Networking, HTTP, TLS, caching, DNS | §3 |
| HTML parsing, DOM, error recovery | §4 → `browser-rendering-pipeline` |
| CSS: cascade, selectors, style resolution, invalidation | §5 → `browser-rendering-pipeline` |
| Layout algorithms and fragmentation | §6.1 → `browser-rendering-pipeline` |
| Paint, raster, compositing, GPU | §6.2 → `browser-rendering-pipeline`–6.4 |
| JS engine integration, bindings, GC interaction | §7 → `browser-rendering-pipeline` |
| Event loop, scheduling, rendering lifecycle | §7.3 → `browser-rendering-pipeline` |
| Security: SOP, CORS, CSP, XSS, Spectre, memory safety | §8 → `browser-security-and-privacy` |
| Privacy, tracking, cookies, fingerprinting | §9 → `browser-security-and-privacy` |
| Extensions | §10 → `browser-extensions-platform-and-standards` |
| Storage, media, devices, capability APIs | §11 → `browser-extensions-platform-and-standards` |
| Accessibility | §12 → `browser-extensions-platform-and-standards` |
| Standards, interop, compatibility | §13 → `browser-extensions-platform-and-standards` |
| Testing, telemetry, shipping | §14 → `browser-extensions-platform-and-standards` |
| "Don't do this" | §15 → `browser-development-reference` |
| "Which approach is better?" | §16 → `browser-development-reference` (contested) |
| "Is this still current?" | §17 → `browser-development-reference` |
| Books, docs, people | §18 → `browser-development-reference` |

---

## §1. The Engine Landscape

### 1.1 Who actually renders the web

**[VERSIONED — as of 2026, three engines carry essentially all of it:]**

| Engine | Share (desktop+mobile+tablet, ~May 2026) | Ships in |
|---|---|---|
| **Blink** (Chromium) | **~81%** | Chrome, Edge, Brave, Arc, Opera, Vivaldi, Samsung Internet, and nearly every Electron app |
| **WebKit** (Apple) | **~14%** | Safari — and, **outside the EU**, *every* iOS browser, because the App Store mandated WebKit (Chrome/Firefox/Edge on iOS are WebKit wrappers) |
| **Gecko** (Mozilla) | **~3%** | Firefox and derivatives. The last major engine that is neither Chromium nor Apple |

That's ~99%. The remaining ~1% is Pale Moon's Goanna, Ekioh's commercial GPU-accelerated
Flow, and the two ground-up rewrites below.

**The two new engines, and their honest status [VERSIONED]:**
- **Servo** — originated at Mozilla as a Rust, parallel, embeddable engine co-developed
  with Rust itself (2012–2020); donated to the Linux Foundation, now under **Linux
  Foundation Europe**. Modular; several components (Stylo, WebRender) were upstreamed into
  Firefox and are in production there. Positioned as an **embeddable webview**, not a
  browser.
- **Ladybird** — Andreas Kling's independent C++ engine (**LibWeb** + **LibJS**), spun out
  of SerenityOS, backed by the non-profit Ladybird Browser Initiative (incorporated 2024),
  funded by private sponsorship including GitHub and Shopify founders and Cloudflare, with
  roughly 7–10 full-time engineers. **No code from Blink, WebKit, or Gecko.** Explicit
  policy of never taking search-default money. **First Alpha targeted 2026 for Linux and
  macOS**, aimed at developers and early adopters; **beta expected 2027, general stable
  2028.** Roadmap items include moving style and layout to Rust, sandboxing, GPU isolation,
  and WebAssembly GC — note that those are *roadmap*, not shipped.

**[DURABLE] Why the count matters more than the market share.** With one engine at 81%,
"works in Chrome" becomes the de facto standard regardless of what the spec says, and a
single vendor's product decisions become web-wide policy. Every argument in §9 → `browser-security-and-privacy`, §10 → `browser-extensions-platform-and-standards`, and
§13 → `browser-extensions-platform-and-standards` is downstream of this.

### 1.2 What it costs to build one

**[DURABLE] A browser engine is one of the largest artifacts in commercial software** —
tens of millions of lines, decades of accumulated compatibility behaviour, and a security
surface that attracts state-level attackers. The realistic assessment:
- **Nobody has built a competitive from-scratch engine in twenty years** and shipped it to
  general users. Ladybird's 2026-alpha/2028-stable timeline with ~10 full-time engineers is
  the current experiment in whether that's still possible.
- The hard part is **not** the parts that are fun (parser, layout algorithms). It's the
  long tail: compatibility with two decades of quirks, media codecs and DRM, accessibility,
  the security architecture, and the sheer surface area of the platform.
- **Forking is the rational choice and is why the landscape looks like it does.** Every
  "new browser" of the last decade is a Chromium shell with different UI and policy.

### 1.3 What a browser is besides an engine

Product surface that is genuinely half the work: profiles and sync, password and payment
management, downloads, bookmarks and history, autofill, the update mechanism (a
**security-critical** always-on channel), enterprise policy, crash reporting and telemetry,
DevTools, and the extension platform.

---

## §2. Process Model, IPC, and Sandboxing

### 2.1 Why multiple processes

**[DURABLE]** Chrome's 2008 multi-process design solved three problems at once and every
engine has since converged on it: **stability** (a renderer crash kills a tab, not the
browser), **performance** (parallelism across cores; one page's main thread can't block
another's), and — the one that turned out to matter most — **security** (renderers run in
a restricted sandbox with no direct filesystem, network, or device access).

**The Chromium terminology, precisely, because people conflate these:**
- **Multi-process architecture** — the broad design choice of separate OS processes.
- **Site Isolation** — the stricter *policy* that a renderer process is locked to a single
  site or origin, including for iframes.
- **Sandboxing** — the OS-level restriction layer limiting what a compromised process can
  do *after* code execution.

### 2.2 Site Isolation

**[ENGINE, and the reference design]** Chrome enabled Site Isolation by default in Chrome
67, motivated directly by **Spectre** (§8.6 → `browser-security-and-privacy`). Its two halves:
1. **Locked renderer processes** — a renderer may contain documents and workers from only
   one site or origin, *even in iframes*. Getting this right required solving genuinely
   hard cases: `srcdoc` URLs, `data:` URLs, base URLs, and sandboxed frames (Chrome enabled
   **isolated sandboxed frames** by default in 2024, adding a process boundary between an
   origin and the untrustworthy content it hosts).
2. **Browser-enforced restrictions** — the privileged browser process validates every IPC
   message and refuses cross-site data requests (`ChildProcessSecurityPolicy::
   CanAccessDataForOrigin` is the canonical check). This is what stops a *fully compromised*
   renderer from simply asking for another site's cookies.

**Firefox's equivalent is Project Fission**, which isolates at the **origin** boundary
rather than the site boundary — stricter than Chrome's default, because Chrome's site
boundary does not separate `mail.example.com` from `pay.example.com`.

**[DURABLE] The security payoff, stated precisely:** under Site Isolation, an attacker with
full remote code execution inside a renderer still cannot read another site's DOM, cookies,
or JS heap, because **those objects are simply not in that process's address space**. To
reach them the attacker must chain a second exploit — a browser-process privilege
escalation or a kernel sandbox escape. That's the whole design.

> **⚠️ GOTCHA — the cost is memory and process count, and it binds hardest on mobile.**
> Chromium's own security documentation is unusually candid: *"we are reaching the limits
> of sandboxing and site isolation. A key limitation is that the process is the smallest
> unit of isolation, but processes are not cheap. Especially on Android, using more
> processes impacts device health overall: background activities get killed with far
> greater frequency."* It also notes that processes still share information about multiple
> sites — the network service is one large C++ component parsing complex input from
> anyone on the network. **Process isolation has a ceiling, and the industry has hit it.**

### 2.3 Sandboxing, per platform

| Platform | Mechanism |
|---|---|
| **Windows** | Restricted token + job object + alternate desktop + **AppContainer** + **Win32k lockdown** (blocking direct access to the win32k syscall surface, historically a huge kernel attack surface) |
| **macOS** | Seatbelt (`sandbox_init`) profiles |
| **Linux** | **seccomp-bpf** syscall filter + user namespaces + `setuid` sandbox (legacy) |
| **Android** | Process sandbox reinforced by **SELinux** policy; isolated processes |
| **iOS** | System sandbox; JIT requires special entitlement — hence the WebKit mandate historically |

**[DURABLE] Renderers must be denied filesystem, network, and device access.** All of it
routes through brokered IPC to the browser process, which validates. Any capability you
hand directly to the renderer is a capability the attacker gets.

### 2.4 IPC design

**[DURABLE] The IPC layer is a security boundary, and it must be treated like a network
protocol from a hostile peer.** The rules:
- **Validate everything in the privileged process.** Never trust a size, an index, a
  handle, or — especially — an *origin* claimed by a renderer.
- **Capability-style interfaces** (Chromium's **Mojo**) beat giant switch statements on
  message IDs: a renderer holds a pipe to a specific service with a specific interface,
  rather than the ability to send any message.
- **Fuzz the IPC surface.** It is the highest-value fuzzing target in the browser.
- Mind the **serialization** cost: IPC on the rendering hot path shows up directly in
  frame time.

---

## §3. Networking

### 3.1 The stack

```
URL parse (WHATWG URL — the spec exists because everyone did this differently)
  → HSTS check → scheme handling
  → DNS (system, DoH, DoT) → Happy Eyeballs (race IPv4/IPv6, prefer fast path)
  → TCP + TLS 1.3, or QUIC (UDP) for HTTP/3
  → connection pool / coalescing
  → HTTP/1.1 · HTTP/2 (multiplex) · HTTP/3 (QUIC, no head-of-line blocking)
  → response: caching, decompression (gzip/br/zstd), MIME sniffing
  → hand to renderer as a stream
```

**Points that matter for implementers:**
- **HTTP/2** multiplexes over one TCP connection, eliminating per-request connections —
  but a lost packet stalls *all* streams (TCP head-of-line blocking).
- **HTTP/3 / QUIC** moves to UDP with per-stream loss recovery, fixing that, plus
  0-RTT resumption and connection migration across network changes. QUIC is implemented in
  userspace, which is why browsers ship their own.
- **Connection coalescing**: reusing one connection for multiple hosts that resolve to the
  same IP with a covering certificate. A real performance win and a subtle correctness trap.
- **HTTP caching is a specification, not a heuristic** — `Cache-Control`, `ETag`,
  `Last-Modified`, `Vary`, revalidation, and the freshness lifetime rules. ⚠️ **Cache
  partitioning by top-level site is now standard** (§9.2 → `browser-security-and-privacy`) and changed the performance
  calculus of shared CDN resources permanently.
- **MIME sniffing** exists because servers lie. It is also a security hazard —
  `X-Content-Type-Options: nosniff` exists to turn it off, and sniffing a response into an
  executable type is a classic XSS vector.
- **Preload/preconnect/prefetch/priority hints** — the browser's scheduling of what to
  fetch when is a large part of real-world page speed.

> **⚠️ GOTCHA — the network service parses hostile input from everyone, in C++, for all
> sites at once.** Chromium names this explicitly as a residual risk (§2.2). Whatever
> your architecture, that component deserves memory-safe implementation, aggressive
> fuzzing, and its own sandbox.
