---
name: browser-security-and-privacy
description: "Use when reasoning about browser security or privacy behaviour: the same-origin policy, the mitigation alphabet (CORS, CSP, COOP/COEP, CORB/ORB, SameSite, Trusted Types), XSS still, never trusting the renderer, memory safety (Rust, MiraclePtr), Spectre and the transient-execution problem, the third-party cookie saga and what browsers actually do now (tracking protection, storage partitioning, the fate of Privacy Sandbox), and fingerprinting — randomize or uniformize."
---

# Browser Development: The Security Model and Privacy and Anti-Tracking

> **Part 3 of 5** of the *Web Browser Development* reference (plugin `web-browser-development`), covering §8–§9. Sibling skills: `browser-engine-architecture-and-networking` (§0–§3), `browser-rendering-pipeline` (§4–§7), `browser-extensions-platform-and-standards` (§10–§14), `browser-development-reference` (§15–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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

## §8. The Security Model

### 8.1 Same-origin policy

**[DURABLE] The foundational rule: an origin is the (scheme, host, port) triple, and code
from one origin cannot read data from another.** Everything else in web security is an
exception to, or a reinforcement of, this.

The historically-permitted cross-origin operations are the source of most web
vulnerabilities: you may **embed** cross-origin (images, scripts, iframes, styles) and you
may **send** cross-origin requests (forms) — you just can't *read* the results. CSRF exists
because sending is allowed with ambient credentials; XSSI and side-channel leaks exist
because embedding is allowed.

### 8.2 The mitigation alphabet

| Mechanism | Does what |
|---|---|
| **CORS** | Server opt-in to cross-origin *reads*. Simple vs. preflighted requests; `Access-Control-Allow-*` |
| **CSP** | Author-declared allow-list of sources and behaviours. **Nonce/hash-based CSP with `strict-dynamic`** is the modern form; host allow-lists are widely bypassable |
| **Trusted Types** | Prevents DOM XSS structurally by requiring typed objects rather than strings at injection sinks. **Reached Baseline in February 2026** |
| **SameSite cookies** | CSRF defence; `Lax` by default in most engines |
| **`__Host-`/`__Secure-` prefixes** | Cookie integrity guarantees |
| **HSTS**, **CT**, **CAA** | Transport and PKI integrity |
| **Subresource Integrity** | Hash-pinned third-party scripts |
| **COOP / COEP / CORP / CORB-ORB** | Cross-origin isolation and read blocking (§8.6) |
| **Permissions Policy** | Delegating or denying powerful features per-frame |
| **Sandbox attribute / `sandbox` CSP** | Capability reduction for embedded content |
| **Secure contexts** | Powerful APIs restricted to HTTPS |

### 8.3 XSS, still

**[DURABLE] XSS remains the dominant web vulnerability class, and the browser's role is
to make it structurally impossible rather than to filter it.** The history is
instructive: engines shipped XSS *auditors* (Chrome's XSS Auditor, IE's XSS Filter), and
**all of them were removed** — they were bypassable, they introduced their own
vulnerabilities, and they caused false positives that broke sites. The lesson generalizes:
**a filter that must guess intent on a Turing-complete input is not a security boundary.**
Trusted Types and CSP are the structural replacements.

### 8.4 Never trust the renderer

**[DURABLE] The single most important implementation rule in browser security.** A
compromised renderer will lie about its origin, its URL, its permissions, and the contents
of any structure it hands you. Every privileged operation must be re-derived and
re-validated in the browser process from state the browser process owns.

**Chromium is now moving this enforcement into Rust**: the security team has been
**migrating `ChildProcessSecurityPolicy` to Rust** with a live Canary experiment, both for
memory safety and to strengthen the security-relevant invariants that Site Isolation
depends on — and has an initial **Rust Mojo client** enabling services to be implemented
fully in Rust.

### 8.5 Memory safety

**[VERSIONED — the most active area of browser security engineering.]** Roughly 70% of
serious browser vulnerabilities have historically been memory-safety bugs. The 2026 state
of the art, using Chrome as the documented example:
- **MiraclePtr / BackupRefPtr** — reference-counted raw pointers that neutralize
  use-after-free by keeping the allocation quarantined. Already credited with a major UAF
  reduction; **being expanded to Skia, ANGLE, Dawn, C++ iterators, and `std::` containers**.
- **MiracleObject** — being deployed on the **GPU main thread**, targeting up to **90%** of
  UAFs there, explicitly trading local runtime performance for temporal safety.
- **PartitionAlloc** — a hardened allocator; now enabled in Skia.
- **"Spanification"** — a systematic effort to eliminate out-of-bounds bugs by replacing
  raw pointer+length pairs with bounds-checked spans.
- **UBSan `-fsanitize=return` enabled by default in release builds**, with plans to expand.
- **Rust** — a centralized Rust SDK, new modular components written in Rust, and the
  `ChildProcessSecurityPolicy` migration above. The stated architectural payoff is
  significant: *writing new components in Rust lets complex features run inside
  high-privilege processes without the performance penalty of sandboxing* — i.e. **memory
  safety buys back architectural freedom that process isolation was spending.**
- Google has also stated it is **exploring implementing the browser's top-level UI in
  HTML/CSS/TypeScript** to reduce dependence on C++ frameworks.
- **AI-assisted vulnerability finding is now real**: Google built an agent harness in early
  2026 that found a sandbox escape — a compromised renderer tricking the browser into
  reading local files — that **had survived in the codebase for more than 13 years**.

**Engine comparison [ENGINE]:** Gecko relies on Rust for newer components (Stylo,
WebRender) but older C++ doesn't benefit from a BackupRefPtr equivalent, and mozjemalloc
is less hardened than PartitionAlloc. WebKit leans on OS integration — **pointer
authentication on ARM64**, strict code signing on iOS — and mostly uses system allocators.

### 8.6 Spectre and the transient-execution problem

**[DURABLE, and the reason the architecture looks like it does.]** Spectre showed that
**any** high-resolution timer plus speculative execution lets attacker JS read arbitrary
memory *in its own process*. There is no software fix for the CPU behaviour. So the
browsers' response was architectural: **if the secret isn't in the process, it can't be
read.** That is Site Isolation's origin story.

The supporting mitigations: reduced timer resolution and jitter, disabling
`SharedArrayBuffer` unless **cross-origin isolated** (COOP+COEP), **CORB/ORB** to stop
sensitive cross-origin responses from ever entering a renderer, and per-site process locks.

---

## §9. Privacy and Anti-Tracking

### 9.1 The third-party cookie saga — what actually happened

**[VERSIONED, and the folklore is badly out of date. This is worth getting exactly right.]**

Timeline:
- **January 2020** — Google announces intent to phase out third-party cookies in Chrome
  "within two years," alongside the **Privacy Sandbox** initiative. Deadlines slip from
  2022 → 2023 → 2024 → 2025.
- **22 July 2024** — Google announces it will **not** phase out third-party cookies,
  proposing a user-choice prompt instead. UK **CMA** competition concerns and **ICO**
  disappointment are both part of the record; the CMA had been formally engaged since 2022.
- **22 April 2025** — Google confirms it is **maintaining the current approach** and will
  **not roll out a standalone opt-out prompt**. Default behaviour — third-party cookies
  allowed — unchanged.
- **17 October 2025** — Google **retires most Privacy Sandbox APIs**, citing low adoption:
  Topics, Protected Audience, Attribution Reporting, Private Aggregation, IP Protection,
  Related Website Sets and others. Deprecation lands in **Chrome 144 (January 2026)** with
  full removal targeted for **Chrome 150 (July 2026)**. Google's stated continuing focus is
  privacy-preserving measurement plus **FedCM** and **CHIPS**.

**[DURABLE] The lesson for an engine implementer is not about advertising.** It's that
**a browser vendor whose revenue depends on advertising faces a structural conflict when
changing tracking defaults**, and that regulators now treat browser defaults as competition
policy. Note also the asymmetry that remains: **Safari, Firefox, and Brave still block
third-party cookies by default**, so roughly 17–20% of global traffic is "cookieless"
regardless of Chrome — the fragmentation didn't go away, it just stopped being Chrome-led.

### 9.2 What browsers actually do now

- **Third-party cookie blocking** (Safari ITP since 2020, Firefox ETP, Brave) vs.
  Chrome's user-choice model.
- **State partitioning / "total cookie protection"** — partitioning *all* storage
  (cookies, localStorage, IndexedDB, cache, service workers) by top-level site, so a
  third party gets a separate jar per embedding site. **This is the most important
  anti-tracking mechanism actually deployed**, because it defeats cross-site state without
  breaking same-site embedding. **CHIPS** (`Partitioned` cookies) is the opt-in
  standardized form.
- **Cache partitioning** — closing the shared-cache timing side channel.
- **Referrer trimming**, **`Referrer-Policy`** defaults.
- **Fingerprinting defences** — the hard problem (§9.3).
- **Bounce-tracking mitigation**, link decoration stripping, **Global Privacy Control**.

### 9.3 Fingerprinting

**[CONTESTED, and genuinely unresolved.]** Canvas, WebGL, fonts, audio, screen metrics,
timing, hardware concurrency, and the sheer combination of exposed APIs form an identifier
without any storage at all.

Two philosophies:
- **Randomization** (Brave): add per-session, per-site noise so the fingerprint is unstable.
- **Uniformity** (Tor Browser): make every user look identical, at real functionality cost.
- Chrome's position historically leaned on "privacy budget"-style ideas that have not
  broadly shipped.

**The honest assessment: nobody has solved this.** Every new capability API adds entropy,
which is why capability APIs (§11 → `browser-extensions-platform-and-standards`) are permanently in tension with privacy, and why "just
ship the feature" is never the whole answer.
