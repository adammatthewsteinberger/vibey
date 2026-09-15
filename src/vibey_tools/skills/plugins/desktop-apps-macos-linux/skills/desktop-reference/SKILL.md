---
name: desktop-reference
description: "Use when reviewing a desktop app for anti-patterns, weighing contested questions (SwiftUI vs AppKit, native vs cross-platform, Electron vs Tauri, Flatpak vs Snap vs AppImage, GTK vs Qt, sandboxed vs unsandboxed, Wayland-first, Swift 6 strict concurrency, SwiftData vs Core Data vs GRDB, menu bar vs header bar), finding primary documentation and books, learning from the case studies and hard-won lessons, checking whether a platform claim is still current (snapshot verified August 2026), or needing the 'why doesn't my app feel native', 'won't launch on a user's Mac', and 'misbehaves on Linux' checklists. Companion to the other desktop-apps-macos-linux skills."
---

# Desktop Apps (macOS & Linux): Anti-Patterns, Contested Questions, Canon, Case Studies, and Currency

> **Part 5 of 5** of the *Desktop Application Programming — macOS & Linux* reference (plugin `desktop-apps-macos-linux`), covering §14–§20. Sibling skills: `desktop-macos-platform` (§0–§3), `desktop-linux-platform` (§4–§6), `desktop-cross-platform-and-architecture` (§7–§9), `desktop-packaging-security-and-testing` (§10–§13). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Verified August 2026. See §18 below for the currency snapshot and what goes stale first.

> **How to read this.** Reference, not tutorial. Sections are independent. Three markers:
> - **[UNIVERSAL]** — true of desktop software regardless of platform or toolkit.
> - **[PLATFORM]** — specific to macOS or a particular Linux stack. Verify against current docs.
> - **[CONTESTED]** — competent engineers disagree. Both cases given; don't adjudicate for the reader.
>
> **⚠️ GOTCHA** boxes mark the failure modes that actually cost people days.
>
> **The single most important framing in this document:** macOS is *one* platform with
> *one* vendor, *one* HIG, and *one* blessed path. Linux is *not a platform* — it is a
> family of overlapping conventions (freedesktop specs), two dominant toolkits, two
> display protocols, three packaging formats, and a dozen desktop environments. Advice
> that treats them symmetrically is wrong. Almost every difficulty in cross-platform
> desktop work traces back to this asymmetry.

---

## §14. Anti-Patterns

| Anti-pattern | Why it's bad | Do instead |
|---|---|---|
| Blocking I/O on the main thread | Beachball / frozen window; the #1 perceived-quality bug | Async everything; §8.4 → `desktop-cross-platform-and-architecture` |
| A custom file browser inside your app | Ignores bookmarks, recents, cloud providers, sandbox, portals | Platform file dialog / FileChooser portal |
| Hardcoded colors instead of semantic ones | Breaks dark mode, high contrast, accent colors | Semantic colors and system materials |
| Hardcoded paths (`~/Library/...`, `~/.config/...` literal) | Breaks under sandbox and Flatpak | Platform APIs / XDG env vars |
| No keyboard access to a feature | Fails accessibility; power users bounce | Menu item + shortcut for every command |
| Removing focus rings for aesthetics | Accessibility regression | Restyle them |
| Custom-drawn controls without accessibility | Invisible to screen readers | Native widgets, or implement the a11y tree |
| Ignoring window state restoration | Feels broken every launch | Persist and restore |
| A splash screen to hide slow startup | Hides the problem; users still wait | Fix startup; show real UI progressively |
| Auto-update that isn't atomic | Bricked installs, unrecoverable | Sparkle/OSTree/transactional |
| `--filesystem=home` in a Flatpak | Defeats the sandbox; reviewers reject | Portals |
| `nodeIntegration: true` / `contextIsolation: false` in Electron | Remote content gets Node — full RCE | Preload + contextBridge (§7.3 → `desktop-cross-platform-and-architecture`) |
| Shipping an ancient Electron/Chromium | You ship known RCEs | Track upstream releases |
| Polling timers at idle | Battery drain, fan noise, uninstall | Event-driven; pause when occluded |
| One giant "AppDelegate"/"MainWindow" class | Untestable, unmergeable | Layered architecture (§8.1 → `desktop-cross-platform-and-architecture`) |
| Assuming X11 | Broken on GNOME 50+, Fedora 43+, Ubuntu 25.10+ | Test on Wayland first |
| Assuming integer display scale | Blurry/misaligned at 125%/150% | Handle fractional scaling |
| String concatenation for translated text | Untranslatable; wrong word order | Positional format strings |
| Storing secrets in prefs/plain files | Trivially harvested | Keychain / Secret Service |
| Truncate-then-write the user's document | Crash mid-write destroys data | temp + fsync + atomic rename |
| No undo | Users will not trust the app with real work | §8.3 → `desktop-cross-platform-and-architecture` |
| Changing `CFBundleIdentifier` / app ID after ship | Orphans data, keychain, licenses, store record | Choose carefully once |
| Testing only on your own machine/DE | Ships bugs on every other configuration | Matrix: macOS n and n-1; GNOME + KDE; Wayland + X11 |

---

## §15. Contested Questions

Present the strongest version of each side; the right answer is context-dependent.

**15.1 SwiftUI vs AppKit** — §2.1 → `desktop-macos-platform`. Dividing line: SwiftUI for structure and forms; AppKit
for dense data, text systems, and deep window/menu control. Nobody serious is 100% either.

**15.2 Native per-platform vs one cross-platform toolkit** — Native wins on feel,
accessibility, platform integration, and long-term maintainability *per platform*;
cross-platform wins on total cost and consistency. The synthesis that keeps winning is
architecture **B** from §0.2 → `desktop-macos-platform`: shared core, native UI.

**15.3 Electron vs Tauri** — §7.2 → `desktop-cross-platform-and-architecture`. Consistency and ecosystem maturity versus footprint and
permission model. Both camps are shipping real products.

**15.4 Flatpak vs Snap vs AppImage** — §10.2 → `desktop-packaging-security-and-testing`. Flatpak has the ecosystem centre of gravity
for GUI apps; Snap has the Ubuntu/server/daemon story and transactional updates but a
single centralized store; AppImage has portability and no update or sandbox story. Trying
to force one format everywhere is the actual mistake.

**15.5 GTK+libadwaita vs Qt on Linux** — libadwaita gives you a GNOME-perfect app and a
GNOME-shaped one. Qt gives you cross-desktop and cross-OS reach with a licensing decision
attached (LGPL relinking constraints; GPL-only modules; commercial for static linking and
LTS patches). Neither is wrong; the deciding factors are usually licensing and whether you
also target Windows.

**15.6 Sandboxed (App Store/Flatpak) vs unsandboxed distribution** — Sandboxing buys user
trust, store distribution, and genuine security; it costs capability (some apps simply
cannot be sandboxed), engineering time, and — on macOS — a revenue share. Many pro Mac
apps ship both builds with different feature sets, and say so plainly on their site.

**15.7 Wayland-first vs keeping X11 support** — GNOME has removed X11 code and KDE follows
in Plasma 6.8; new apps should be Wayland-native and use portals. The counterweight: LTS
distributions, XFCE/MATE/Cinnamon users, remote-desktop workflows, and accessibility tools
that still work better on X11 will exist for years. Support both if your users need it,
but *develop* on Wayland.

**15.8 Swift 6 strict concurrency: too much or just right** — §3.2 → `desktop-macos-platform`.

**15.9 SwiftData vs Core Data vs GRDB** — §3.3 → `desktop-macos-platform`.

**15.10 Menu bar vs header-bar/hamburger on Linux** — GNOME HIG says header bar; KDE and
traditional-desktop users expect menus; power users and accessibility tooling both benefit
from a discoverable menu structure. Pick per your target desktop and be internally
consistent.

---

## §16. The Canon — authorities and references

### 16.1 Primary documentation (always prefer these)

**Apple**
- **Human Interface Guidelines** — the macOS sections specifically; the Mac patterns
  differ from iOS in ways tutorials elide.
- **Apple Developer Documentation**: AppKit, SwiftUI, Foundation, Security, `notarytool`,
  "Notarizing macOS software before distribution", "Adopting Liquid Glass",
  "Adopting strict concurrency in Swift 6".
- **WWDC session videos** — genuinely the best source for new API rationale. For this
  domain: "Use SwiftUI with AppKit and UIKit" (WWDC26), "Build a SwiftUI app with the new
  design" (WWDC25), the privacy/Gatekeeper "What's new in privacy" series (2022–2024
  cover app-bundle, container, and app-group protection changes).
- **Apple Platform Security guide** — Gatekeeper, notarization, runtime protection.
- **Swift Evolution proposals** (SE-####) for concurrency semantics; the **Swift Forums**
  are where the real migration discussions happen.

**Linux / freedesktop**
- **freedesktop.org specifications** — Base Directory, Desktop Entry, Icon Theme,
  AppStream, MIME, Notifications, Autostart, Trash, Secret Service.
- **XDG Desktop Portal documentation** (`flatpak.github.io/xdg-desktop-portal`) — the
  API reference *and* the "Reasons to Use Portals" / "For App Developers" pages.
- **GNOME Human Interface Guidelines** and the **libadwaita** docs; **GTK4 API reference**;
  **gtk4-rs book**.
- **KDE Human Interface Guidelines**; **Qt documentation** (`doc.qt.io`) — especially the
  licensing and release pages, which are the authoritative word on LGPL/GPL/commercial.
- **Flatpak documentation** (sandbox permissions, manifests) and **Flathub's** submission
  requirements.
- **ArchWiki** — despite being distro-specific, it is the best practical reference for
  PipeWire, portals, Wayland, systemd/user, and D-Bus. Use it as documentation, not as
  Arch advocacy.
- **LWN.net** — the highest-signal reporting on Linux desktop architecture changes
  (the accessibility/Newton coverage is the reference on that topic).

### 16.2 Books and long-form

| Author / source | Work | Why |
|---|---|---|
| **Aaron Hillegass** | *Cocoa Programming for OS X* | The classic AppKit text; still the best explanation of the Cocoa object model and delegation |
| **Matt Neuburg** | *Programming iOS/macOS* series | Rigorous, precise, updated frequently |
| **Paul Hudson** | *Hacking with Swift / Hacking with macOS* | The best free practical Swift/SwiftUI reference; his Swift 6 concurrency writeups are widely cited |
| **Chris Eidhof, Florian Kugler, Wouter Swierstra (objc.io)** | *Advanced Swift*, *Thinking in SwiftUI* | The deepest treatment of how SwiftUI actually evaluates |
| **Fatbobman (Xu Yang)** | Core Data / SwiftData blog series | The most thorough independent analysis of Apple's persistence stack |
| **Michael Tsai** | Blog | The community's institutional memory for Apple platform changes and their consequences |
| **Jasper St. Pierre** | *Xplain* | The clearest existing explanation of how X11 actually works — read before arguing about Wayland |
| **Daniel Stone** | "The Real Story Behind Wayland and X" (talk) | The canonical account of why Wayland exists |
| **Havoc Pennington** | D-Bus design writing | Origin rationale for the desktop's IPC model |
| **Blanchette & Summerfield** | *C++ GUI Programming with Qt* | Dated but still the best structured Qt introduction |
| **Andrew Krause** | *Foundations of GTK+ Development* | GTK's conceptual model (GTK3-era; concepts transfer) |
| **Jeff Johnson** | *Designing with the Mind in Mind*; *GUI Bloopers* | The cognitive-psychology basis for UI decisions |
| **Alan Cooper** | *About Face* | The interaction-design canon |
| **Bruce Tognazzini** | *Tog on Interface* / First Principles | Where much of the Mac's interaction philosophy originates |

### 16.3 Ongoing sources
**Apple side**: Michael Tsai's blog, The Eclectic Light Company (Howard Oakley — deep,
accurate macOS internals), Hacking with Swift, objc.io, SwiftLee, Swift Forums,
`developer.apple.com/forums` (the Gatekeeper/code-signing tags are staffed by Apple's
DTS and are the definitive answer source for signing problems).
**Linux side**: LWN.net, Phoronix (news, treat benchmarks carefully), GNOME and KDE
developer blogs (`blogs.gnome.org`, `blogs.kde.org` — KDE's "This Week in Plasma" is
excellent), 9to5Linux/OMG!Ubuntu for release tracking, the Flatpak and freedesktop
GitLab issue trackers.
**Cross-platform**: the Electron and Tauri blogs and release notes; `areweguiyet.com` and
boringcactus's periodic Rust GUI survey.

---

## §17. Case Studies and Hard-Won Lessons

| Case | What happened | Transferable lesson |
|---|---|---|
| **Ghostty's non-native fullscreen** | Mitchell Hashimoto's terminal (Zig core, SwiftUI on macOS, GTK4 on Linux) needed "non-native fullscreen." Online samples suggested a dozen lines; the real PR was +802/−239. | The last 10% of *native feel* is where AppKit knowledge is irreplaceable. Budget for it, and note the architecture: shared core, per-platform UI — §0.2 → `desktop-macos-platform` pattern B. |
| **Google Cloud IoT Core / Microsoft App Center retirements** | Platform services people built on were withdrawn with notice periods measured in months. | Anything vendor-hosted in your update or telemetry path is a dependency with an expiry date. Own your appcast; keep your update mechanism replaceable. |
| **MacUpdater shutdown (Jan 2026)** | An 8-year-old app-tracking service wound down; its database goes dark end of 2026, already producing false positives. | Third-party update discovery is not a distribution strategy. Ship a working in-app updater. |
| **Electron's `nodeIntegration` era** | Early Electron apps ran remote content with full Node access; XSS became RCE. Defaults were changed (contextIsolation on, nodeIntegration off) in later majors. | Framework *defaults* are a security control. Apps that pinned old versions to avoid migration inherited the vulnerable defaults. |
| **The GNOME/KDE X11 removal** | Years of "Wayland isn't ready" gave way to GNOME removing X11 code entirely and KDE scheduling the same. | Deprecation announcements on the Linux desktop are slow, then sudden. Treat "we'll port later" as accruing interest. |
| **libadwaita theming controversy** | A widely-read post about theming triggered a large, still-unresolved argument about GTK vs libadwaita and who owns an app's appearance. | On Linux, appearance is a *social* contract as much as a technical one. Whatever you choose, expect to defend it in your issue tracker. |
| **The Linux accessibility resourcing gap** | Credible assessments found single-digit numbers of people working significantly on Linux a11y over a decade, while Wayland and sandboxing broke AT-SPI's assumptions. | If you use custom-drawn UI on Linux, you are almost certainly shipping an inaccessible app, and no ecosystem safety net will catch it. Use standard widgets. |
| **Apple silicon transition (2020–2026)** | Universal binaries, Rosetta 2, and now the end of Intel support in macOS 26. | Multi-year architecture transitions are normal on macOS. Keep your build system capable of producing fat binaries and your dependencies capable of both architectures. |
| **Sandbox retrofits** | Countless Mac apps that added App Sandbox years in discovered their data directory moved, their file access vanished, and their helper tools stopped working. | Sandbox decisions are architectural, not packaging. Decide before v1. |
| **The `.desktop`/app-ID mismatch class of bug** | Apps ship with a generic icon in the dock and no notification attribution because the Wayland `app_id` doesn't match the desktop file name. | Invisible in development, universal in bug reports. Verify the whole chain (§4.1 → `desktop-linux-platform`). |

---

## §18. Currency Snapshot — verified August 2026

| Thing | Status as of Aug 2026 | Decay risk |
|---|---|---|
| **macOS** | **macOS 26 "Tahoe"** shipped 15 Sept 2025; latest **26.6.2** (17 Aug 2026). **Last macOS to support Intel Macs.** macOS 27 "Golden Gate" in public beta, September release expected | **High** |
| **Xcode / Swift** | Xcode **26.6** current (26.4 pairs with Swift compiler **6.3**; language modes 4/4.2/5/6). Xcode 26.4 requires macOS Tahoe 26.2+ | High |
| **Swift concurrency** | Swift 6 strict concurrency is the default in Swift 6 mode; **Swift 6.2's "approachable concurrency"** (`SWIFT_APPROACHABLE_CONCURRENCY`, main-actor-by-default, `nonisolated(nonsending)` per SE-0461, `@concurrent` escape hatch) is on by default for new Xcode 26 projects | Medium |
| **Liquid Glass** | Introduced macOS 26; free for framework chrome on recompile; custom components need work; Icon Composer required for icons | Medium |
| **SwiftData** | Production-viable for new apps on macOS 14+/iOS 17+; stable across three OS releases; gained migration tooling in iOS 18; model inheritance added in the 2025 cycle. Still weaker than Core Data for complex graphs, heavyweight migrations, and some CloudKit sync modes | Medium |
| **GTK** | **GTK 4.22.x** (4.22.4, Apr 2026) current. GTK5 not imminent. libadwaita tracks GNOME releases | Medium |
| **GNOME** | GNOME 49 disabled the X11 session; **X11 backend code removed from Mutter; GNOME 50 (Mar 2026) ships with zero X11 code**. GNOME 51 due Sept 2026 | High |
| **KDE Plasma** | **Plasma 6.8 will be Wayland-only**, expected ~**14 Oct 2026**; Plasma X11 session supported into **early 2027** | High |
| **Distros** | Fedora 43 and Ubuntu 25.10 already ship no GNOME X11 session; Ubuntu 26.04 makes Wayland exclusive for major DEs | High |
| **Xorg / XLibre** | Xorg still maintained for security, **feature development halted**. XLibre is an actively-developed fork of contested provenance, adopted by a few distros (e.g. Artix default) | Medium |
| **Qt** | **Qt 6.11.x** current (6.11.1, May 2026); ~6-month minor cadence. LTS = 5 years since 6.8.0; **LTS patches are commercial-only** | Medium |
| **Wayland ancillary** | PipeWire **1.6.x** is the default audio/video server nearly everywhere; screen capture requires ScreenCast portal + PipeWire | Medium |
| **Linux a11y** | AT-SPI2 is current; **Newton** (AccessKit-based, Wayland-native, sandbox-compatible) is the experimental successor. KDE added AT-SPI2 in Plasma 6.0; keyboard-event API landed in Mutter 48/GNOME 48 and KWin/KDE 6.4 | Medium |
| **Flatpak/Flathub** | Flathub ~3,200–3,500 apps, 433M downloads reported for 2025; default on Fedora, Mint, elementary, Steam Deck; Canonical ships a Flatpak plugin for GNOME Software | Low |
| **Electron** | Still the most-used desktop framework; powers VS Code, Slack, Discord, Notion, Postman, 1Password, Obsidian, Linear, Figma desktop | Low |
| **Tauri** | **Tauri 2 stable**, mobile (iOS/Android) supported; the default recommendation for new size/memory-sensitive projects in most 2026 comparisons | Medium |
| **Deno desktop** | `deno desktop` shipped in **Deno 2.9 (25 June 2026)**; explicitly experimental | High |
| **Avalonia** | **Avalonia 12** released ~Apr 2026 (large rendering-performance work; Impeller renderer in partnership with Google's Flutter team). **Avalonia.MAUI** backend brings MAUI to Linux/browser — preview | Medium |
| **.NET MAUI** | Mobile-first; **no first-party Linux support**; desktop via WinUI + Mac Catalyst | Medium |
| **Sparkle** | Still the macOS standard; Sparkle 2 supports sandboxed apps, custom UI, EdDSA signing, delta updates | Low |
| **MacUpdater** | **Discontinued 1 Jan 2026**; database scheduled dark end of 2026 | Settled |
| **EU CRA** | Reporting obligations **11 Sept 2026**; full application **11 Dec 2027** — applies to desktop software sold in the EU | **Imminent** |

**What goes stale fastest**: macOS/Xcode versions; GNOME and Plasma release status; Swift
concurrency defaults; cross-platform framework version claims and benchmarks.
**What essentially never goes stale**: §8 → `desktop-cross-platform-and-architecture` (architecture), §9 → `desktop-cross-platform-and-architecture` (desktop idioms), §14
(anti-patterns), §17 (lessons).

---

## §19. Quick Reference

### 19.1 "Why doesn't my app feel native?" — the checklist
1. Menu bar / header bar follows the platform HIG, with every command present
2. Keyboard shortcuts match platform conventions; full keyboard navigation works
3. Platform file dialogs (not a custom browser)
4. Semantic colors; dark mode and high contrast work; respects Reduce Transparency/Motion
5. Window size/position/state restored across launches
6. Drag & drop in *and* out; clipboard with multiple representations
7. Undo/redo, unlimited and coalescing; autosave; crash recovery
8. Correct app ID everywhere → icon, notifications, and window matching work (Linux)
9. Screen-reader accessible (VoiceOver / Orca) — actually tested
10. Idles at ~0% CPU

### 19.2 "The app won't launch on a user's Mac"
Signature broken (`codesign --verify --deep --strict`) → not notarized or ticket not
stapled (`stapler validate`) → quarantine + translocation breaking a relative path →
missing `NS*UsageDescription` for an API it calls at launch → an embedded binary unsigned
or lacking Hardened Runtime → architecture mismatch (arm64-only on Intel, or a
mixed-arch plugin) → `LSMinimumSystemVersion` above their OS.

### 19.3 "The app misbehaves on Linux"
Wrong/missing `.desktop` file or app-ID mismatch → Wayland vs X11 assumption → missing or
wrong portal backend → no D-Bus session bus → Flatpak sandbox denying something (check
`flatpak run --command=sh` and the portal logs) → missing runtime dependency the distro
didn't pull in → fractional scaling → theme assumptions.

### 19.4 Numbers worth knowing
- Frame budget: **16.7 ms** @60 Hz, **8.3 ms** @120 Hz.
- "Instantaneous" to a user: **< 100 ms**. Needs a spinner: **> 1 s**. Needs
  cancel + progress: **> 10 s**.
- Cold launch target: **< 1 s** to interactive.
- WCAG AA contrast: **4.5:1** body text, **3:1** large text and UI components.
- Electron: ~80–200 MB bundle, ~150–300 MB idle RAM. Tauri: ~2–10 MB, ~30–50 MB.
- macOS deployment: notarization requires **Hardened Runtime**; Mac App Store requires
  **App Sandbox**; both require **code signing**.
- Flatpak runtime download on first install: **500 MB+** (GNOME/KDE platform) — mention
  it in your install docs so users don't think your 8 MB app is 500 MB.

### 19.5 Reviewing someone else's desktop app
- [ ] Is there a UI-framework-free domain layer with tests? (§8.1 → `desktop-cross-platform-and-architecture`)
- [ ] Any file/network I/O on the main thread? (§8.4 → `desktop-cross-platform-and-architecture`)
- [ ] Are long operations cancellable, with progress?
- [ ] Undo, autosave, atomic writes for user data? (§8.3 → `desktop-cross-platform-and-architecture`)
- [ ] Window state restoration? Multi-window safe?
- [ ] Semantic colors, dark mode, HiDPI, Reduce Transparency? (§9.4 → `desktop-cross-platform-and-architecture`)
- [ ] Every command reachable by keyboard and present in a menu? (§9.2 → `desktop-cross-platform-and-architecture`)
- [ ] Screen-reader tested (VoiceOver/Orca)? (§9.6 → `desktop-cross-platform-and-architecture`)
- [ ] Strings externalized; plurals and RTL handled? (§9.5 → `desktop-cross-platform-and-architecture`)
- [ ] Secrets in Keychain / Secret Service, not files? (§12 → `desktop-packaging-security-and-testing`)
- [ ] macOS: signed + hardened + notarized + stapled; entitlements minimal? (§10.1 → `desktop-packaging-security-and-testing`)
- [ ] Linux: app ID consistent; portals used; no `--filesystem=home`? (§4.1 → `desktop-linux-platform`, §12.3 → `desktop-packaging-security-and-testing`)
- [ ] Electron: contextIsolation on, nodeIntegration off, CSP, current version? (§7.3 → `desktop-cross-platform-and-architecture`)
- [ ] Update path atomic, signed, rollback-capable, and tested in CI? (§11 → `desktop-packaging-security-and-testing`, §13.3 → `desktop-packaging-security-and-testing`)
- [ ] Idle CPU ≈ 0?

---

## §20. Sources and Method

**Method.** Narrative (not systematic) review. Durable material — §8 → `desktop-cross-platform-and-architecture` (architecture),
§9 → `desktop-cross-platform-and-architecture` (desktop idioms), §14 (anti-patterns), §16–17 — is synthesized from established
practice and the canonical literature in §16. Every **time-sensitive** claim (versions,
dates, deprecation schedules, product status) was verified against a primary or
near-primary source in **August 2026** and is flagged in §18 with a decay-risk rating.
Where practitioners disagree, §15 gives both cases rather than adjudicating, and disputed
claims are marked in place.

**Search log** (August 2026): macOS current version and Xcode/Swift pairing · SwiftUI vs
AppKit state of play · GTK4/libadwaita versions and GNOME releases · Qt 6 releases and
licensing · Wayland/X11 transition status across GNOME, KDE, and distros · Flatpak vs Snap
vs AppImage · Tauri 2 vs Electron · macOS notarization, Hardened Runtime, entitlements,
Gatekeeper · XDG Desktop Portals · Swift 6 strict concurrency and 6.2 approachable
concurrency · Rust GUI ecosystem maturity · PipeWire, D-Bus, systemd user services ·
Sparkle and desktop auto-update · Linux accessibility (AT-SPI, Orca, Newton) · macOS 26
Liquid Glass adoption · .NET MAUI / Avalonia / Compose Multiplatform desktop status ·
SwiftData vs Core Data.

**Primary and near-primary sources consulted (selected):**
- Apple Developer documentation and WWDC sessions — Xcode system requirements page,
  macOS 26 release notes, "Use SwiftUI with AppKit and UIKit" (WWDC26), "Build a SwiftUI
  app with the new design" (WWDC25), "Adopting Liquid Glass", "Adopting strict concurrency
  in Swift 6", "Notarizing macOS software before distribution"
- Apple Support — Gatekeeper and runtime protection; macOS Tahoe 26 update notes
- Bluetooth-unrelated: Qt Company — `doc.qt.io` releases and licensing pages; Qt release blogs
- GNOME — `blogs.gnome.org` (X11 Session Removal FAQ; Newton accessibility updates);
  GTK releases; libadwaita
- KDE — `blogs.kde.org` "Going all-in on a Wayland future"; Plasma/Wayland community wiki
- freedesktop.org — D-Bus specification; XDG Desktop Portal documentation and API reference
- Flatpak — sandbox permissions documentation; Flathub
- Snapcraft — XDG Desktop Portals documentation
- ArchWiki — PipeWire, XDG Desktop Portal
- LWN.net — "Modernizing accessibility for desktop Linux"; "Enhancing screen-reader
  functionality in modern GNOME"
- Sparkle Project — `sparkle-project.org` and GitHub
- Electron — `electron.build` notarization docs; `electron/notarize`
- Avalonia UI — Avalonia 12 release blog; MAUI backend announcement
- Espressif-unrelated: Deno release notes (via secondary coverage) for `deno desktop`
- European Commission — Cyber Resilience Act reporting obligations

**Confidence statement.** High confidence in §1–§2 → `desktop-macos-platform`, §4–§6 → `desktop-linux-platform`, §8–§14 → `desktop-cross-platform-and-architecture`, §16–§17, §19 (durable
architecture, well-documented platform mechanics, and verifiable history). High confidence
in §18's verified items as of the stated date. **Moderate confidence** in the framework
comparison figures in §7.1 → `desktop-cross-platform-and-architecture` and the adoption characterizations in §7.2 → `desktop-cross-platform-and-architecture`, §7.4 → `desktop-cross-platform-and-architecture`, and §10.2 → `desktop-packaging-security-and-testing` —
these rest substantially on practitioner blogs and vendor material where incentives differ
and methodology is rarely published. They are stated as representative ranges and
tendencies, **not measurements**; benchmark your own workload before making a decision
that depends on them.
