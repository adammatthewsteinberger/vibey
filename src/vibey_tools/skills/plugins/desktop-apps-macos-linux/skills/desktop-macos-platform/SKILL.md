---
name: desktop-macos-platform
description: "Use when building, porting, or debugging a native macOS app. Covers the framework decision and the four architectures of a desktop app (the router for the whole desktop-apps-macos-linux reference), the Darwin stack, bundles, the run loop/GCD/main thread, XPC privilege separation, Apple silicon, Rosetta, and universal binaries, the 2026 SwiftUI-vs-AppKit state of play and the interop seam, Liquid Glass (macOS 26 Tahoe), Mac Catalyst, Swift 6 strict concurrency migration, and persistence on macOS (SwiftData, Core Data, GRDB)."
---

# Desktop Apps (macOS & Linux): macOS Platform, SwiftUI/AppKit, and Swift

> **Part 1 of 5** of the *Desktop Application Programming — macOS & Linux* reference (plugin `desktop-apps-macos-linux`), covering §0–§3. Sibling skills: `desktop-linux-platform` (§4–§6), `desktop-cross-platform-and-architecture` (§7–§9), `desktop-packaging-security-and-testing` (§10–§13), `desktop-reference` (§14–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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

## §0. Routing — Classify Before Answering

### 0.1 The framework decision, up front

| If the answer to this is yes... | ...then |
|---|---|
| macOS-only, deep OS integration, sold on the Mac App Store | **SwiftUI + AppKit** |
| macOS + iOS from one codebase | **SwiftUI** (multiplatform target, not Catalyst) |
| Linux-first, GNOME-native feel, will ship on Flathub | **GTK4 + libadwaita** |
| Linux-first, KDE-native, or Linux+Windows+macOS with one native-ish toolkit | **Qt 6** |
| Team is web developers; you already have a web app; deadline dominates | **Electron** |
| Team can take on Rust; bundle size / memory matter; want a small attack surface | **Tauri 2** |
| Existing .NET/WPF codebase and skills; need Linux | **Avalonia** |
| Existing Kotlin/Android codebase; JVM shop | **Compose Multiplatform** |
| Pixel-identical custom UI on every OS, mobile too, don't care about native feel | **Flutter** |
| It's a developer tool / internal utility; native feel is irrelevant | Anything. Ship it. |

**[UNIVERSAL] The framework decision is downstream of two questions people skip:**
1. **Who maintains this in three years?** Framework choice is a hiring and staffing
   decision more than a technical one. A "better" framework nobody on the team knows is
   worse.
2. **Does this app need to feel native, or merely to work?** These have completely
   different cost curves. "Feels native" means platform menus, platform keyboard
   conventions, platform file dialogs, platform accessibility, platform theming,
   platform window behaviour — and it is 3–10× the work of "works."

### 0.2 The four architectures of a desktop app

```
A. Pure native, per platform     — two codebases, best feel, highest cost
B. Native UI + shared core       — Rust/C++/Go core, SwiftUI on Mac, GTK/Qt on Linux
                                   (the "right" answer for serious cross-platform apps)
C. Single cross-platform toolkit — Qt / Flutter / Avalonia / Compose. One UI, everywhere.
D. Web UI in a shell            — Electron / Tauri. One UI, everywhere, web tech.
```
**B is underrated.** Ghostty (Zig core + SwiftUI on macOS + GTK4 on Linux), 1Password
(Rust core), Signal, and many others use it. The core is testable, portable, and
performance-critical; the UI is thin and idiomatic per platform. The cost is that you
write the UI twice — but the UI is usually the *smaller* half of a serious application,
and it's the half where "twice" buys you the most.

### 0.3 The question-type router

| Asked about... | Go to |
|---|---|
| Bundles, launchd, run loops, Darwin, XPC | §1 |
| SwiftUI, AppKit, NSViewRepresentable, Liquid Glass, menus, windows | §2 |
| Swift concurrency, @MainActor, SwiftData/Core Data | §3 |
| D-Bus, systemd user units, XDG specs, PipeWire, desktop files | §4 → `desktop-linux-platform` |
| GTK4, libadwaita, Qt6, QML, toolkit choice on Linux | §5 → `desktop-linux-platform` |
| Wayland, X11, XWayland, compositors, protocols | §6 → `desktop-linux-platform` |
| Electron, Tauri, Flutter, Avalonia, Compose, Rust GUI | §7 → `desktop-cross-platform-and-architecture` |
| MVVM, state management, undo, documents, IPC, threading | §8 → `desktop-cross-platform-and-architecture` |
| Windows, keyboard, drag & drop, HiDPI, dark mode, i18n, a11y | §9 → `desktop-cross-platform-and-architecture` |
| Notarization, DMG, Flatpak, Snap, AppImage, .deb/.rpm, AppStream | §10 → `desktop-packaging-security-and-testing` |
| Sparkle, auto-update, delta updates, rollout | §11 → `desktop-packaging-security-and-testing` |
| TCC, entitlements, hardened runtime, portals, Electron security | §12 → `desktop-packaging-security-and-testing` |
| UI testing, profiling, Instruments, sysprof, CI | §13 → `desktop-packaging-security-and-testing` |
| "Don't do this" | §14 → `desktop-reference` |
| "Which is better, X or Y?" | §15 → `desktop-reference` (contested) |
| Books, docs, HIGs, authorities | §16 → `desktop-reference` |
| Famous failures and lessons | §17 → `desktop-reference` |
| "Is this still current?" | §18 → `desktop-reference` |

---

## §1. macOS Platform Architecture

### 1.1 The stack

```
┌──────────────────────────────────────────────────┐
│ Your app: SwiftUI / AppKit / Catalyst / 3rd-party│
├──────────────────────────────────────────────────┤
│ App frameworks: AppKit, SwiftUI, UIKit(Catalyst) │
├──────────────────────────────────────────────────┤
│ Media/graphics: Core Animation, Metal, Core Image,│
│ AVFoundation, Core Text                          │
├──────────────────────────────────────────────────┤
│ Core Services: Foundation, Core Foundation, GCD, │
│ Core Data, Network.framework, XPC                │
├──────────────────────────────────────────────────┤
│ Darwin: XNU kernel (Mach + BSD), launchd, dyld,  │
│ APFS, Sandbox (Seatbelt), TCC, AMFI, SIP         │
└──────────────────────────────────────────────────┘
```

**Things that matter and are non-obvious:**
- **XNU is a hybrid kernel**: Mach (ports, IPC, VM, scheduling) + BSD (POSIX, sockets,
  VFS). Mach ports are the substrate for XPC and for essentially all privileged IPC.
- **launchd is PID 1** and the *only* supported way to run background processes. Not
  cron, not init scripts, not a daemon you fork yourself.
  - `LaunchAgents` run per-user in the GUI session (`~/Library/LaunchAgents`,
    `/Library/LaunchAgents`). `LaunchDaemons` run as root, system-wide, with no GUI
    session (`/Library/LaunchDaemons`).
  - Modern apps should prefer **`SMAppService`** (macOS 13+) to register login items and
    helpers from *inside* the app bundle, rather than dropping plists into
    `~/Library/LaunchAgents`. The user then manages them in System Settings → General →
    Login Items, which is what they expect.
- **dyld** is the dynamic linker; the **dyld shared cache** is why system frameworks load
  fast. `DYLD_*` environment variables are ignored for hardened-runtime and
  SIP-protected processes — which is exactly why your `DYLD_LIBRARY_PATH` trick works in
  development and fails in the notarized build.
- **SIP (System Integrity Protection)** makes `/System`, `/usr` (except `/usr/local`),
  and `/bin` immutable even to root. Never write outside `/usr/local`, `/opt`, or the
  app's own container.

### 1.2 Bundles — the unit of macOS software

```
MyApp.app/
└── Contents/
    ├── Info.plist              ← identity, version, doc types, URL schemes, usage strings
    ├── MacOS/
    │   └── MyApp               ← the actual executable (CFBundleExecutable)
    ├── Resources/
    │   ├── Assets.car          ← compiled asset catalog (icons, images, colors)
    │   ├── en.lproj/           ← localized strings, per language
    │   └── de.lproj/
    ├── Frameworks/             ← embedded .framework and .dylib — MUST be signed
    ├── PlugIns/                ← app extensions
    ├── XPCServices/            ← XPC helpers
    ├── Library/
    │   └── LoginItems/         ← helper apps registered via SMAppService
    ├── _CodeSignature/         ← signature over the whole bundle
    └── embedded.provisionprofile (App Store / some entitlements)
```

**Info.plist keys you will actually need:**
| Key | Purpose |
|---|---|
| `CFBundleIdentifier` | Reverse-DNS identity. **Immutable in practice** — changing it orphans user data, keychain items, and the App Store record. |
| `CFBundleShortVersionString` | Marketing version ("2.1.0") — what users see |
| `CFBundleVersion` | Build number — must **monotonically increase** per upload |
| `LSMinimumSystemVersion` | Minimum macOS |
| `CFBundleDocumentTypes` / `UTExportedTypeDeclarations` | File type ownership + custom UTIs |
| `CFBundleURLTypes` | Custom URL schemes (`myapp://`) |
| `NS*UsageDescription` | **Required** privacy strings — missing one = instant crash on first use of that API |
| `LSUIElement` | `true` = menu-bar-only app, no Dock icon |
| `LSApplicationCategoryType` | Required for the App Store |
| `ITSAppUsesNonExemptEncryption` | Saves you an export-compliance dialog on every upload |

> **⚠️ GOTCHA — missing usage strings crash, they don't warn.** Calling an API guarded by
> TCC (camera, microphone, contacts, calendar, photos, Downloads/Documents/Desktop,
> screen recording, Automation/AppleScript) without the corresponding
> `NSCameraUsageDescription`-style key in Info.plist terminates the process immediately.
> This looks like a random crash on a user's machine and is instant in the debugger.
> Write the strings as user-facing sentences — the App Store rejects vague ones.

**Where app data goes [PLATFORM]:**
| Content | Sandboxed path | Non-sandboxed |
|---|---|---|
| User-visible documents | `~/Documents` via user selection | same |
| App support / databases | `~/Library/Containers/<id>/Data/Library/Application Support/<id>` | `~/Library/Application Support/<id>` |
| Caches (deletable) | `.../Library/Caches/<id>` | `~/Library/Caches/<id>` |
| Preferences | `UserDefaults` → `.../Library/Preferences/<id>.plist` | same |
| Logs | `.../Library/Logs/<id>` | `~/Library/Logs/<id>` |

Use `FileManager.default.url(for: .applicationSupportDirectory, in: .userDomainMask, ...)`
and never hardcode paths — sandboxing silently redirects them, and hardcoded paths are the
#1 reason an app breaks when you enable the sandbox.

### 1.3 The run loop, GCD, and the main thread

**[PLATFORM, but the concept is UNIVERSAL] All UI work happens on the main thread.**
On macOS the main thread runs an `NSRunLoop`/`CFRunLoop` that dispatches events, timers,
and sources. Touching `NSView`/`NSWindow` — or SwiftUI state that a view reads — from any
other thread is undefined behaviour that manifests as corrupted rendering or a crash in
unrelated code minutes later.

- **GCD (`DispatchQueue`)**: `DispatchQueue.main` is the UI queue. Background work goes on
  `.global(qos:)` or a private serial queue. QoS classes (`.userInteractive`,
  `.userInitiated`, `.utility`, `.background`) affect scheduling priority *and*
  thermal/energy behaviour — mislabeling background work as `.userInitiated` is a real
  battery cost.
- **Swift Concurrency** (`async`/`await`, actors, `@MainActor`) is the modern layer over
  this, and as of Swift 6 the compiler *enforces* the main-thread rule (§3.2).
- **Thread explosion**: `DispatchQueue.concurrentPerform` and unbounded
  `DispatchQueue.global().async` can blow past the thread limit and deadlock. Bound your
  concurrency explicitly (semaphore, `TaskGroup` with a limit, or a serial queue).

### 1.4 XPC — the right way to do privilege separation

XPC is macOS's IPC mechanism, with lifecycle management by launchd. Use it for:
- **Crash isolation**: a plugin host, a parser handling untrusted input, a video decoder.
  If it crashes, the app survives.
- **Privilege separation**: put the network- or file-parsing code in an XPC service with
  a *tighter* sandbox than the main app. This is genuinely effective hardening.
- **Privileged helpers**: `SMJobBless`-style root helpers (modern: `SMAppService.daemon`)
  for the rare operation that truly needs root. Verify the *client's* code signature in
  the helper — an unauthenticated root helper is a local privilege-escalation
  vulnerability, and this has shipped in real products repeatedly.

```swift
// Modern XPC with NSXPCConnection, plus the security check that people omit
let connection = NSXPCConnection(serviceName: "com.example.MyApp.ParserService")
connection.remoteObjectInterface = NSXPCInterface(with: ParsingProtocol.self)
connection.resume()

let proxy = connection.remoteObjectProxyWithErrorHandler { error in
    // Service crashed or was killed — degrade gracefully, don't crash the app
    log.error("XPC failed: \(error)")
} as? ParsingProtocol
```

### 1.5 Apple silicon, Rosetta, and universal binaries

- Ship **universal 2** binaries (`arm64` + `x86_64`) via `lipo`/Xcode until you drop Intel.
  **macOS 26 Tahoe is the last macOS to support Intel Macs** — from macOS 27, Apple
  silicon only. That changes the calculus for new products: an arm64-only build is now
  defensible for apps requiring macOS 27+.
- **Rosetta 2** translates x86_64 ahead-of-time; it does *not* support AVX-512 and it
  cannot load arm64 dylibs into an x86_64 process (or vice versa) — a mixed-architecture
  plugin ecosystem is a real, painful problem.
- Apple silicon has **efficiency and performance cores**; QoS is how you steer work
  between them. Also relevant: unified memory means GPU/CPU transfers are cheap, and
  `MTLStorageMode.shared` is usually right.

---

## §2. macOS UI — SwiftUI and AppKit

### 2.1 The 2026 state of play

**[CONTESTED, and the most consequential macOS decision.]** The honest summary that
experienced Mac developers converge on: **almost nobody starts a new Mac app in pure
AppKit anymore, and almost no serious Mac app is pure SwiftUI.** The real skill is knowing
where the seam goes. Apple's own guidance (WWDC26 "Use SwiftUI with AppKit and UIKit") is
explicitly incremental: start new scenes in SwiftUI, keep existing AppKit, and there is
*no expectation* that an app becomes entirely SwiftUI.

**Case for SwiftUI on macOS:**
- Declarative state→UI eliminates a whole category of "view and model disagree" bugs.
- Dramatically less code for typical forms, lists, sidebars, settings.
- One codebase across macOS/iOS/iPadOS/visionOS when that matters.
- Apple's investment is entirely here; new APIs (including Liquid Glass adoption)
  land in SwiftUI first or exclusively.
- `@Observable` (the Observation framework) removed most of the `ObservableObject`
  boilerplate and its over-invalidation problems.

**Case for AppKit (still, in 2026):**
- **Dense, large data.** `NSTableView`/`NSOutlineView` with cell reuse still beat SwiftUI
  `List`/`Table` for tens of thousands of rows with complex cells. This is the single most
  commonly cited gap.
- **Deep menu, toolbar, and window customization** — non-native fullscreen, custom title
  bars, accessory view controllers, `NSWindow` subclassing behaviours.
- **Text.** `NSTextView`/TextKit 2 is a full text system; SwiftUI's `TextEditor` is not
  in the same category. Any editor, IDE, or writing app will use it.
- **Precise control over first responder, key equivalents, and focus.**
- **Backward deployment** to older macOS versions.
- Predictability: AppKit does what you told it. SwiftUI sometimes does what it inferred.

**The pragmatic architecture most shipping apps use:**
```
SwiftUI  → app structure (App/Scene), settings, sidebars, inspectors, simple lists,
           anything form-shaped
AppKit   → the one hard view (the editor, the canvas, the giant table), embedded via
           NSViewRepresentable / NSViewControllerRepresentable
Shared   → @Observable model layer that both read
```

### 2.2 SwiftUI on macOS — the Mac-specific parts

The parts of SwiftUI that only matter on the Mac, which iOS-shaped tutorials skip:

```swift
@main
struct MyApp: App {
    @State private var model = AppModel()          // @Observable, @MainActor

    var body: some Scene {
        // A document-based app gets New/Open/Save/Revert/Versions for free
        DocumentGroup(newDocument: MyDocument()) { file in
            EditorView(document: file.$document)
        }
        .commands {
            // Menu bar customization — Mac-only, and where most Mac apps live
            CommandGroup(replacing: .newItem) {
                Button("New Project…") { model.newProject() }
                    .keyboardShortcut("n", modifiers: [.command, .shift])
            }
            CommandMenu("Analyze") {
                Button("Run") { model.run() }.keyboardShortcut("r")
                Divider()
                Button("Clear Results") { model.clear() }
                    .disabled(model.results.isEmpty)     // menu items MUST disable
            }
        }

        // Settings scene → gets the standard ⌘, shortcut and window chrome
        Settings { SettingsView().frame(width: 520) }

        // A secondary utility window, openable via openWindow(id:)
        Window("Activity", id: "activity") { ActivityView() }
            .defaultSize(width: 400, height: 300)
            .keyboardShortcut("0", modifiers: .command)

        // Menu bar extra — the Mac's status-item idiom
        MenuBarExtra("Status", systemImage: "waveform") {
            StatusMenu()
        }
        .menuBarExtraStyle(.window)   // .menu for a plain menu, .window for a popover
    }
}

// Standard Mac three-column layout
struct RootView: View {
    var body: some View {
        NavigationSplitView {
            Sidebar()
        } content: {
            ItemList()
        } detail: {
            DetailView()
        }
        .toolbar { /* ... */ }
        .navigationSplitViewStyle(.balanced)
    }
}
```

**Mac-specific view modifiers worth knowing**: `.focusedSceneValue` (drive menu enablement
from the focused window's state — this is how you make menu items correctly gray out),
`.onKeyPress`, `.contextMenu`, `.draggable`/`.dropDestination`, `.fileExporter`/
`.fileImporter` (they route through the sandbox correctly), `.help()` (tooltips),
`.windowResizability`, `.defaultPosition`, `.presentedWindowToolbarStyle`.

### 2.3 The interop seam — where the money is

```swift
// Wrapping AppKit inside SwiftUI: the 90% case
struct TextEditorView: NSViewRepresentable {
    @Binding var text: String

    func makeNSView(context: Context) -> NSScrollView {
        let scroll = NSTextView.scrollableTextView()
        let tv = scroll.documentView as! NSTextView
        tv.delegate = context.coordinator
        tv.isRichText = false
        tv.font = .monospacedSystemFont(ofSize: 13, weight: .regular)
        return scroll
    }

    func updateNSView(_ scroll: NSScrollView, context: Context) {
        guard let tv = scroll.documentView as? NSTextView else { return }
        // ⚠️ Guard against feedback loops: only write if actually different,
        // or every keystroke round-trips and the cursor jumps to the end.
        if tv.string != text { tv.string = text }
    }

    func makeCoordinator() -> Coordinator { Coordinator(self) }

    final class Coordinator: NSObject, NSTextViewDelegate {
        let parent: TextEditorView
        init(_ p: TextEditorView) { parent = p }
        func textDidChange(_ n: Notification) {
            guard let tv = n.object as? NSTextView else { return }
            parent.text = tv.string
        }
    }
}

// Wrapping SwiftUI inside AppKit: the incremental-adoption direction
let host = NSHostingController(rootView: InspectorView(model: model))
splitViewController.addSplitViewItem(NSSplitViewItem(viewController: host))
```

> **⚠️ GOTCHA — the `updateNSView` feedback loop.** This is *the* interop bug. SwiftUI
> calls `updateNSView` whenever any observed state changes; if you unconditionally write
> to the AppKit view, and the AppKit view's delegate writes back to the binding, you get
> an infinite loop or (more insidiously) a cursor that resets to position 0 on every
> keystroke. Always compare before assigning, and consider a "programmatic change" flag.

> **⚠️ GOTCHA — sizing.** `NSViewRepresentable` doesn't automatically communicate an
> intrinsic size to SwiftUI's layout. Set `intrinsicContentSize` on the NSView, or use
> `.frame()` / `sizeThatFits` explicitly, or you'll get a zero-height view and conclude
> the wrapper is broken.

### 2.4 Liquid Glass (macOS 26 Tahoe)

macOS 26 introduced **Liquid Glass**, the biggest visual change since 2013 — a translucent,
light-refracting material applied to toolbars, sidebars, menu bar, Dock, window controls,
sheets, and popovers. What developers need to know:

- **You get most of it for free.** Recompile against the macOS 26 SDK and framework-provided
  chrome (toolbars, sidebars, sheets, popovers, standard controls) adopts the new material
  with no code changes, whether you're on SwiftUI, UIKit, or AppKit.
- **Custom components do not.** Anything you drew yourself keeps its old look and will
  now clash. This is where the actual migration work is.
- The opt-in APIs are `.glassEffect()`, `GlassEffectContainer`, and `glassEffectID` for
  morphing between glass elements.
- **Icons** need rework through Apple's **Icon Composer** (layered vector content with
  blur/translucency, real-time specular highlights) — the old flat 1024px PNG workflow is
  obsolete.
- **[UNIVERSAL, and important]** Translucency is an accessibility hazard. Respect
  **Reduce Transparency** and **Increase Contrast**; test with both on. Text over a
  glass material at low contrast is a real WCAG failure, not a style preference.

**[CONTESTED]** Whether to adopt aggressively: proponents argue apps that don't adapt will
look broken beside system apps; skeptics note the material is expensive to render, hurts
legibility when misapplied, and that Apple's own first-year implementations drew
substantial criticism. The defensible middle: adopt the *system* chrome (free), use
semantic colors and system materials rather than hardcoded palettes, and be conservative
about applying `.glassEffect()` to your own content surfaces.

### 2.5 Mac Catalyst — when (not) to use it

Catalyst runs a UIKit iPad app on the Mac. **Its purpose is porting an existing iPad app**,
and that's the only case where it's the right call. For a new multiplatform product, a
SwiftUI multiplatform target produces a better Mac app for the same effort. Note also that
Apple silicon Macs can simply *run* unmodified iPad apps, which removes much of Catalyst's
original motivation. Catalyst apps consistently read as "not quite a Mac app" to Mac users
— wrong menu structure, wrong keyboard behaviour, wrong window resizing.

---

## §3. Swift, Concurrency, and Persistence

### 3.1 Language baseline

- **Swift 6.x is current** (Xcode 26.4 ships Swift 6.3; language *modes* 4/4.2/5/6 are
  selectable per target). Objective-C remains fully supported and is still load-bearing in
  large codebases; new code should be Swift.
- **`@Observable`** (Observation framework) replaced `ObservableObject`/`@Published` for
  most purposes: finer-grained invalidation (SwiftUI only re-renders views that read the
  properties that actually changed), less boilerplate, no `objectWillChange` plumbing.
- Value types by default; `struct` for models, `final class` when you need identity,
  `actor` for shared mutable state.

### 3.2 Swift 6 strict concurrency — the migration everyone is doing

Swift 6 makes **data-race safety a compile-time guarantee**: warnings in Swift 5 mode
become errors. Core concepts:

| Concept | Meaning |
|---|---|
| `Sendable` | Marker protocol: values of this type can safely cross concurrency domains. Structs of Sendable members get it synthesized; classes only if immutable (`final` + all `let`) or internally synchronized. |
| `actor` | Reference type with automatic mutual exclusion on its state. |
| `@MainActor` | Global actor for UI. Everything touching views/view models belongs here. |
| `nonisolated` | Opt a member out of its actor's isolation (must not touch isolated state). |
| `nonisolated(unsafe)` | "Trust me." Last resort; document why. |
| `@preconcurrency` | Import a not-yet-audited module without drowning in errors. |

```swift
// The canonical shapes.
@MainActor @Observable
final class DocumentViewModel {              // UI state — main actor
    var items: [Item] = []
    var isLoading = false

    private let store: ItemStore              // an actor

    func refresh() async {
        isLoading = true
        defer { isLoading = false }
        items = await store.fetchAll()        // compiler inserts the hop
    }
}

actor ItemStore {                             // shared mutable state — isolated
    private var cache: [UUID: Item] = [:]
    func fetchAll() -> [Item] { Array(cache.values) }
    func insert(_ item: Item) { cache[item.id] = item }
}

struct Item: Sendable, Identifiable {         // crosses boundaries — must be Sendable
    let id: UUID
    var title: String
}
```

**[IMPORTANT, and recent] Swift 6.2 changed the ergonomics substantially.** The
"approachable concurrency" work (`SWIFT_APPROACHABLE_CONCURRENCY = YES`, on by default for
new Xcode 26 projects) **inverts the default**: code is main-actor-isolated unless you say
otherwise, and `nonisolated` async functions run on the *caller's* actor rather than
hopping. `@concurrent` is the explicit escape hatch for pushing CPU-heavy work
(decoding, image processing) off the main actor.

**[CONTESTED]** Whether this is an improvement: proponents say the old model buried the
signal in a wall of Sendable errors and drove people to slap `@unchecked Sendable` on
everything, so a safe-by-default model that's easy to use correctly is a net win.
Critics — notably the "Swift Concurrency is a Mess in 2026" line of argument — say the
repeated model changes eroded trust, and that main-actor-by-default hides main-thread
bottlenecks from developers who never learn to move work off it. Both observations are
accurate; which dominates depends on team seniority.

**Migration strategy that works** (from teams who've done it on 50K+ LOC):
1. Stay in Swift 5 mode; turn on **complete** strict-concurrency *checking* to surface
   warnings without breaking the build.
2. Fix **module by module**, leaf-first. Flip each target to Swift 6 mode as it goes clean.
3. Order of operations: `@MainActor` on view models and UI-adjacent classes → `Sendable`
   on value types that cross boundaries → `actor` for shared mutable services → globals
   last (`static let` + Sendable, or `@MainActor`, or as a last resort
   `nonisolated(unsafe)` with a comment explaining the invariant).
4. Expect a cascade: annotating one class forces its callers async, which forces theirs.
   Budget real time; one documented migration touched 79 files and ~2,800 lines for a
   mid-size app.

> **⚠️ GOTCHA — the singleton.** `static var shared` is non-isolated global mutable state
> and is an error in Swift 6. Fix with `static let` + `Sendable`, or `@MainActor static let`,
> or convert the type to an `actor`. Do not reach for `nonisolated(unsafe)` first.

### 3.3 Persistence on macOS

| Option | Use when | Watch out for |
|---|---|---|
| **UserDefaults** | Small preferences, window state | Not for data. Not synchronized across processes reliably. |
| **SwiftData** | New apps, macOS 14+/iOS 17+, SwiftUI-shaped models | Younger; heavyweight/custom migrations and some CloudKit sync modes still weak; measurable overhead at 10K+ rows |
| **Core Data** | Existing apps, complex object graphs, 15+ entities, batch ops, older OS support | Verbose; concurrency model fights modern Swift; `.xcdatamodeld` is an Xcode-bound artifact |
| **GRDB / SQLiteData** | Data-heavy apps, you want SQL and control, fastest reads/bulk writes | More glue code for SwiftUI reactivity; no free CloudKit |
| **Plain files (JSON/plist/SQLite)** | Document-based apps, simple state | You own migration and atomicity |

**[CONTESTED] SwiftData vs Core Data in 2026.** SwiftData is built on Core Data's storage
engine and has been stable across three major OS releases; for new apps with SwiftUI it's
the productivity default. But real teams still choose Core Data for complex models — the
common counterargument is roughly "15 entities with intricate relationships, two decades
of Core Data hardening versus three years of SwiftData, and the abstraction layer's
stability doesn't automatically inherit the storage engine's." Both positions are held by
people shipping real apps. A third camp (growing) picks **GRDB** and skips the object
graph entirely.

**[UNIVERSAL] Whatever you pick: design the migration story before v1 ships.** Desktop
apps hold years of irreplaceable user data. A schema you can't migrate is a product you
can't update.
