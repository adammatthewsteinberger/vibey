---
name: desktop-packaging-security-and-testing
description: "Use when shipping a desktop app: macOS code signing, the Hardened Runtime, notarization and stapling, the four macOS distribution channels including the Mac App Store; the Linux packaging matrix (Flatpak, Snap, AppImage, distro packages); auto-update (Sparkle, Squirrel, Flatpak); sandboxing and privacy (TCC, entitlements, the App Sandbox, Keychain and secrets, XDG portals, supply-chain and dependency risk); and the desktop testing pyramid, tools, and CI."
---

# Desktop Apps (macOS & Linux): Packaging, Auto-Update, Sandboxing, and Testing

> **Part 4 of 5** of the *Desktop Application Programming — macOS & Linux* reference (plugin `desktop-apps-macos-linux`), covering §10–§13. Sibling skills: `desktop-macos-platform` (§0–§3), `desktop-linux-platform` (§4–§6), `desktop-cross-platform-and-architecture` (§7–§9), `desktop-reference` (§14–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Verified August 2026. See §18 → `desktop-reference` for the currency snapshot and what goes stale first.

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

## §10. Packaging and Distribution

### 10.1 macOS: the four distribution channels

| Channel | Signing | Sandbox | Notarization | Update mechanism | Trade-off |
|---|---|---|---|---|---|
| **Mac App Store** | Apple Distribution cert | **Required** | N/A (review instead) | App Store | Discovery + trust; 15–30% cut; review latency; sandbox limits |
| **Developer ID (direct)** | Developer ID Application | Optional | **Required** | Sparkle or your own | Full capability, your prices, you own support |
| **Both** | Two builds | Differs | — | — | Common for pro apps; maintain two entitlement sets |
| **Homebrew Cask** | Developer ID | Optional | Required | `brew upgrade` | Great for developer tools; not a discovery channel for consumers |

**The Developer ID pipeline, precisely:**

```bash
# 1. Sign everything inside-out: frameworks, helpers, XPC services, then the app.
#    --options=runtime enables the Hardened Runtime — REQUIRED for notarization.
codesign --force --timestamp --options=runtime \
  --sign "Developer ID Application: Example Inc (TEAMID)" \
  MyApp.app/Contents/Frameworks/*.framework

codesign --force --timestamp --options=runtime \
  --entitlements MyApp.entitlements \
  --sign "Developer ID Application: Example Inc (TEAMID)" \
  MyApp.app

# 2. Verify BEFORE you ship, not after a user's bug report.
codesign --verify --deep --strict --verbose=2 MyApp.app
spctl --assess --type exec --verbose=4 MyApp.app

# 3. Notarize. Use an App Store Connect API key in CI — it doesn't expire
#    and doesn't trip 2FA, unlike an app-specific password.
ditto -c -k --keepParent MyApp.app MyApp.zip
xcrun notarytool submit MyApp.zip \
  --key AuthKey_XXXX.p8 --key-id XXXX --issuer <issuer-uuid> --wait

# 4. Staple the ticket so Gatekeeper works OFFLINE.
xcrun stapler staple MyApp.app
xcrun stapler validate MyApp.app

# 5. Ship a DMG or PKG — and notarize + staple THAT too, not just the .app.
```

> **⚠️ GOTCHA — notarization failures are almost always one of five things:**
> (1) Hardened Runtime not enabled on *every* executable, including helpers and embedded
> binaries in `Contents/MacOS/` subdirectories; (2) a nested binary that wasn't signed;
> (3) a missing `--timestamp` (signatures without a secure timestamp expire with the
> certificate); (4) a JIT or unsigned-memory requirement without
> `com.apple.security.cs.allow-jit` / `allow-unsigned-executable-memory` (this hits every
> Electron, JVM, Python, and .NET app); (5) an entitlement you're not authorized for.
> The notarization log URL Apple emails you names the exact file — read it rather than
> guessing.

> **⚠️ GOTCHA — app translocation.** Gatekeeper runs quarantined apps from a randomized,
> read-only path on first launch. Anything that assumes it can write next to itself, or
> that reads its own path to find resources outside the bundle, breaks in a way that never
> reproduces in development. Fix: ship in a DMG that instructs dragging to /Applications,
> and never write beside the bundle.

**Entitlements** (`MyApp.entitlements`), the ones that matter:
```xml
<key>com.apple.security.app-sandbox</key><true/>              <!-- required for MAS -->
<key>com.apple.security.files.user-selected.read-write</key><true/>
<key>com.apple.security.files.bookmarks.app-scope</key><true/> <!-- persist file access -->
<key>com.apple.security.network.client</key><true/>
<key>com.apple.security.device.camera</key><true/>
<key>com.apple.security.cs.allow-jit</key><true/>              <!-- Electron/JVM/JIT -->
<key>com.apple.security.temporary-exception.files.home-relative-path.read-write</key>
```
**Security bookmarks are the key sandbox concept**: when the user picks a file, you get
access to *that file* for *this launch*. To keep access across launches, create a
**security-scoped bookmark**, persist it, and resolve it later with
`startAccessingSecurityScopedResource()` / `stopAccessing…` (balanced — leaking these
exhausts a limited resource).

### 10.2 Linux: the packaging matrix

| Format | Sandbox | Updates | Store | Distro reach | Best for |
|---|---|---|---|---|---|
| **Flatpak** | Bubblewrap + namespaces + portals | Delta via OSTree | **Flathub** (community-governed, self-hostable remotes) | Universal; default on Fedora, Mint, elementary, Steam Deck | **The default recommendation for GUI apps** |
| **Snap** | AppArmor + seccomp | Automatic, transactional, rollback | Snap Store (**Canonical-only, no alternate remotes**) | Ubuntu-centric | Ubuntu targeting; CLI tools; servers/IoT; daemons |
| **AppImage** | **None** | **None built in** | AppImageHub (community directory) | Anywhere with FUSE | Portable single-file distribution, no-root environments, testing a version |
| **.deb / .rpm** | None | Distro repo | Distro archives | Per-distro | System-level software; when a distro packages you |
| **AUR / Homebrew / nix** | Varies | Varies | — | Per-ecosystem | Developer tools |

**[CONTESTED] but with a clear centre of gravity:** the 2026 consensus in most practitioner
comparisons is **Flatpak+Flathub as the primary universal format for desktop GUI apps**
(largest catalogue — Flathub passed ~3,200 apps and 433M downloads in 2025 and continues
growing; strongest sandboxing story; shared runtimes save disk; OSTree deltas save
bandwidth), **Snap where you're Ubuntu-aligned or shipping daemons/CLI**, and **AppImage
for portability**. The recurring criticisms are also real: universal packages start slower
than native ones (Snap notably), theming integration is imperfect, runtimes are large on
first install, and **neither Flathub nor the Snap Store vets aggressively** — both have
hosted fake crypto wallets and other malware. Verified-publisher badges exist for a reason;
tell your users to check them.

```yaml
# com.example.MyApp.yaml — a Flatpak manifest
app-id: com.example.MyApp
runtime: org.gnome.Platform
runtime-version: '48'
sdk: org.gnome.Sdk
command: myapp
finish-args:
  - --socket=wayland
  - --socket=fallback-x11          # NOT --socket=x11; fallback prefers Wayland
  - --device=dri                   # GPU
  - --share=network
  # NOTE: no --filesystem=home. Use the FileChooser portal instead — that is
  # the entire point, and Flathub will flag broad filesystem access.
  - --talk-name=org.freedesktop.secrets   # keyring, if you need it
modules:
  - name: myapp
    buildsystem: meson
    sources:
      - type: archive
        url: https://example.com/myapp-1.2.0.tar.xz
        sha256: <hash>
```

> **⚠️ GOTCHA — `--filesystem=home` is a sandbox escape hatch, not a solution.** It's the
> first thing developers reach for and the first thing reviewers push back on. If your app
> needs "access to files," the answer is the FileChooser portal, which grants access to
> exactly what the user picked, transparently, through the toolkit's normal file dialog.

**Reduce your distro-support burden**: ship one Flatpak, tell everyone else to use it, and
let volunteers maintain AUR/nixpkgs. Trying to build and test `.deb` and `.rpm` across six
distro versions is a full-time job that adds no user value in 2026.

---

## §11. Auto-Update

**[UNIVERSAL] Requirements for any desktop updater**, identical in spirit to firmware OTA:
signed, atomic, resumable, rollback-capable, and staged. A half-applied update that leaves
an unlaunchable app is the worst possible outcome — worse than never updating.

| Platform / stack | Mechanism | Notes |
|---|---|---|
| macOS direct | **Sparkle 2** | The de facto standard. EdDSA-signed appcast (RSS/XML), delta updates, atomic installs, **works with sandboxed apps** (a Sparkle 2 feature), fully rebrandable, works with any toolkit (Cocoa, SwiftUI, Qt, .NET). |
| macOS MAS | App Store | You don't control timing. |
| Electron | `electron-updater` / Squirrel.Mac | Mature; test the update flow in CI, not just the app. |
| Tauri | Built-in updater plugin | Signed manifests. |
| Flatpak | `flatpak update` / GNOME Software | OSTree deltas; you just push to the remote. |
| Snap | Automatic, transactional | You get rollback for free; you also lose control of update timing. |
| Distro packages | Distro's updater | Slowest path to users. |
| Cross-platform .NET | WinSparkle/Sparkle wrappers (e.g. UpSparkle) | Thin wrappers over the native frameworks. |

**Ecosystem note (2026):** the third-party Mac update-tracking tool **MacUpdater was
discontinued on 1 January 2026** (final free build 3.5.0; its database is scheduled to go
dark at the end of 2026), pushing users toward Homebrew, `mas-cli`, and Sparkle-aware tools
like Latest and Updatest. **Practical implication:** shipping a working Sparkle appcast is
now more important, because the safety net of third-party trackers is gone.

**Rollout discipline [UNIVERSAL]:** canary → percentage → full, with a kill switch. Ship a
crash reporter *before* you ship auto-update, so you can tell whether a release is bad
within hours instead of learning it from reviews.

---

## §12. Security, Sandboxing, and Privacy

### 12.1 macOS: the three separate systems people conflate

They are independent, and you need all three straight:

1. **Code signing** — proves *who* built it. Developer ID or Apple Distribution certificate.
2. **Entitlements** — declare *what it may do*. Sandbox on/off plus each specific capability.
3. **Notarization** — proves *Apple scanned it* for malware. Required for anything
   distributed outside the App Store since macOS 10.15. **Requires Hardened Runtime.**

Plus, at runtime:
- **Hardened Runtime** — blocks code injection, DYLD hijacking, and unsigned executable
  memory. Mandatory for notarization. This is what breaks JIT-based runtimes unless you
  add the corresponding entitlement.
- **App Sandbox** — kernel-enforced confinement to your container. **Required for the Mac
  App Store; optional (and recommended) outside it.**
- **TCC (Transparency, Consent, Control)** — the per-resource consent database (camera,
  mic, screen recording, Documents/Desktop/Downloads, Contacts, Automation…). Independent
  of the sandbox: **a non-sandboxed app is still subject to TCC.**
- **Gatekeeper** — checks signature + notarization ticket at first launch, tracks
  provenance of files written by downloaded software, and randomizes launch paths when
  necessary.

> **⚠️ GOTCHA — enabling the sandbox late is a project, not a checkbox.** It relocates
> your data directory, revokes filesystem access outside the container, breaks hardcoded
> paths, breaks direct access to other apps' data, and may break your update mechanism.
> Decide sandbox/no-sandbox before v1 and develop with it on.

### 12.2 macOS secrets

Use the **Keychain** (`kSecClass...` / the Security framework) for credentials and tokens.
Not UserDefaults, not a file in Application Support, not obfuscated in the binary. For
higher-value secrets, `kSecAttrAccessibleWhenUnlockedThisDeviceOnly` and the Secure
Enclave (via `SecKeyCreateRandomKey` with `kSecAttrTokenIDSecureEnclave`).

### 12.3 Linux: portals are the model

**XDG Desktop Portals** are the Linux answer to entitlements/TCC: a set of D-Bus
interfaces at `org.freedesktop.portal.Desktop` that mediate access to resources outside an
app's sandbox, with a user-controlled permission system and per-desktop backends
(`xdg-desktop-portal-gnome`, `-kde`, `-wlr`, and newer generic backends for COSMIC/niri).

**[UNIVERSAL for Linux] Use portals even if you are not sandboxed.** The portal docs say
this explicitly, and the reasons are practical:
- Free desktop integration: the FileChooser portal gives you *the user's own* file dialog.
- Some capabilities are **only** available via portals — screen capture and screenshots on
  Wayland go through the ScreenCast/Screenshot portals; some desktops expose no other path.
- Your app works identically packaged and unpackaged.

Key portals: FileChooser, OpenURI, ScreenCast (v6), Screenshot, RemoteDesktop, Camera,
Print, Notification, Settings (theme/accent/color-scheme), Inhibit (prevent sleep),
GlobalShortcuts, Background/Autostart, Secret, Account, Location, Clipboard, Trash.

GTK3/GTK4 and Qt5/Qt6 route through portals **transparently** for common operations —
which is why "use the toolkit's file dialog" is usually the whole answer.

```bash
# Debugging the portal stack — the checklist that resolves most "file picker won't
# open" and "OBS can't see my screen" reports:
echo $XDG_SESSION_TYPE $XDG_CURRENT_DESKTOP
systemctl --user status xdg-desktop-portal
systemctl --user status pipewire wireplumber
journalctl --user -u xdg-desktop-portal -f
# Most common cause: multiple portal backends installed, wrong one selected for
# an interface. The fix is installing the CORRECT backend, not more backends.
```

**Linux secrets**: the **Secret Service** API (`libsecret`) → GNOME Keyring or KWallet. In
Flatpak, request `--talk-name=org.freedesktop.secrets` or use the Secret portal.

### 12.4 Supply chain and dependency risk [UNIVERSAL]

Desktop apps ship a full dependency tree to end-user machines and often run with the
user's full privileges.
- **Pin and audit dependencies**; generate an **SBOM** (SPDX/CycloneDX) per release.
- **Sign everything** with keys held in an HSM or a hosted signing service — never a key
  file on a laptop or in a repo.
- **Keep the runtime current.** An Electron app two majors behind ships known Chromium
  RCEs to your users. A Flatpak on an EOL runtime is the same problem.
- **Reproducible builds** where you can; at minimum, build in a pinned container so
  "it built on my machine" isn't part of your release process.
- The **EU Cyber Resilience Act** applies to desktop software sold into the EU: vulnerability
  and incident **reporting obligations begin 11 September 2026**, full application
  11 December 2027. If you sell a desktop app in Europe, you need an SBOM, a monitored
  vulnerability intake, and a reporting runbook — this is not a firmware-only concern.

---

## §13. Testing, Debugging, and CI

### 13.1 The testing pyramid for desktop

```
        ▲  Crash + telemetry from real users     ← the ultimate integration test
       ╱ ╲ Manual exploratory on real hardware/DEs
      ╱   ╲ UI automation (XCUITest / dogtail / Squish / Playwright)
     ╱     ╲ Integration: real window, real event loop, fake I/O
    ╱       ╲ Unit tests of domain + view models (no UI)   ← the bulk
   ╱_________╲ Static analysis + compiler warnings
```
**[UNIVERSAL] UI tests are slow, flaky, and expensive — so keep the UI thin.** If your view
models are pure and testable (§8.1 → `desktop-cross-platform-and-architecture`), you need very few UI tests: enough to verify wiring
and the two or three critical user journeys, not to test logic.

### 13.2 Tools

| Need | macOS | Linux |
|---|---|---|
| Unit tests | **Swift Testing** (`@Test`/`#expect`), XCTest | GTest/Catch2, pytest, `cargo test`, QTest |
| UI automation | **XCUITest**, Accessibility Inspector | **dogtail** (AT-SPI), Squish, `wlheadless`/`weston --backend=headless` for CI |
| Web-shell UI tests | Playwright/WebdriverIO against Electron | same |
| Profiling (CPU/alloc/time) | **Instruments** (Time Profiler, Allocations, Leaks, Metal, Energy Log, SwiftUI template) | **sysprof**, `perf`, Hotspot, Valgrind/Massif, heaptrack |
| Graphics debugging | Metal debugger, Quartz Debug | RenderDoc, `GTK_DEBUG=interactive`, `apitrace` |
| Widget inspection | Xcode View Debugger | **GTK Inspector** (`GTK_DEBUG=interactive`), **Qt's `GammaRay`** |
| Memory errors | ASan/TSan/UBSan via Xcode schemes | ASan/TSan/UBSan, Valgrind |
| Leaks | `leaks`, Instruments Leaks, Xcode Memory Graph | heaptrack, `G_DEBUG=gc-friendly` + Valgrind |
| Logging | **`os.Logger`** (unified logging; `log stream --predicate`) | `journalctl`, `G_MESSAGES_DEBUG=all`, `QT_LOGGING_RULES` |
| Crash reports | `~/Library/Logs/DiagnosticReports`, Xcode Organizer, Sentry/Crashlytics | `coredumpctl`, ABRT, Sentry |
| D-Bus tracing | — | `busctl monitor`, `dbus-monitor`, `d-feet` |

**The two most underused tools**: on macOS, **Instruments' Time Profiler with "Record
Waiting Threads"** turns "the app hangs sometimes" into a stack; on Linux,
`GTK_DEBUG=interactive` gives you a live widget inspector with CSS editing in any GTK app,
including ones you didn't write.

### 13.3 CI for desktop apps

```
push
 ├─ lint + format (SwiftLint/SwiftFormat; clang-format; clippy; eslint)
 ├─ unit tests: domain + view models ................ fast, every commit
 ├─ build all targets (macOS universal; Linux x86_64 + aarch64)
 ├─ ASan/TSan run of the test suite (nightly)
 ├─ package: .app + notarize + staple + DMG | Flatpak build + lint
 ├─ SBOM + dependency CVE scan
 ├─ sign artifacts (HSM/hosted signing, never a laptop key)
 └─ nightly: UI smoke tests on real macOS + headless Wayland; update-flow test
```

**Platform-specific CI realities:**
- **macOS builds require macOS runners.** Notarization requires network access and an App
  Store Connect API key. GitHub-hosted macOS images change their default Xcode on a
  schedule — **pin your Xcode version** (`sudo xcode-select -s /Applications/Xcode_26.4.app`
  or the setup-xcode action), or a runner-image update will break your build without a
  commit from you.
- **Linux GUI tests need a display.** Use a headless Wayland compositor (`weston
  --backend=headless-backend.so`, `wlheadless-run`, or `cage`) or Xvfb for X11 paths.
- **Test the update path in CI**, not just the app. A broken updater is unrecoverable
  without asking users to reinstall manually.
- **Test on the oldest OS you claim to support.** "Deployment target macOS 13" that has
  only ever run on macOS 26 is a claim, not a fact.
