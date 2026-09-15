---
name: desktop-cross-platform-and-architecture
description: "Use when choosing or using a cross-platform desktop framework (Electron vs Tauri, Flutter, Avalonia, Compose Multiplatform, Rust GUIs — the comparison table and the web-shell security checklist), structuring a desktop app (layering, state management, the document model with undo and autosave, threading and responsiveness, IPC and multi-process design, single instance and the launch protocol), or making an app feel native — windows, menus and keyboard, files, drag and drop and clipboard, dark mode and HiDPI, internationalization, accessibility, and the performance targets users perceive."
---

# Desktop Apps (macOS & Linux): Cross-Platform Frameworks, Architecture, and Native Idioms

> **Part 3 of 5** of the *Desktop Application Programming — macOS & Linux* reference (plugin `desktop-apps-macos-linux`), covering §7–§9. Sibling skills: `desktop-macos-platform` (§0–§3), `desktop-linux-platform` (§4–§6), `desktop-packaging-security-and-testing` (§10–§13), `desktop-reference` (§14–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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

## §7. Cross-Platform Frameworks

### 7.1 The comparison table

| Framework | Language | Rendering | Bundle (typical) | Idle RAM (typical) | Native feel | Maturity |
|---|---|---|---|---|---|---|
| **Electron** | JS/TS + Node | Bundled Chromium | 80–200 MB | 150–300 MB | Low (unless heavily worked) | Very high (13 yrs) |
| **Tauri 2** | JS/TS + Rust | **OS WebView** | 2–10 MB | 30–50 MB | Medium | High, younger |
| **Wails 3** | JS/TS + Go | OS WebView | small | low | Medium | Medium |
| **Neutralino** | JS/TS + thin C++ | OS WebView | 1–5 MB | very low | Low | Low |
| **Qt 6** | C++ / Python / QML | Own (raster/RHI) | 20–60 MB | 40–80 MB | High (Widgets) | Very high (31 yrs) |
| **Flutter** | Dart | Own (Impeller/Skia) | 20–50 MB | 60–120 MB | Low (identical everywhere by design) | High on mobile, medium on desktop |
| **Avalonia** | C#/XAML | Own (Skia → Impeller in progress) | ~40 MB + runtime | medium | Medium (drawn, WPF-like) | High for desktop |
| **.NET MAUI** | C#/XAML | Native controls per platform | — | — | Medium | Mobile-first; **no first-party Linux** |
| **Compose Multiplatform** | Kotlin | Own (Skia) | JVM-sized | higher | Low-Medium | Growing fast |
| **Slint** | Rust/C++/JS + DSL | Own | small | low | Medium | Medium; embedded-focused |
| **egui / iced / Xilem / GPUI** | Rust | Own | small | low | Low | Varies; see §7.4 |

*(Figures are representative ranges from published 2026 comparisons, not measurements of
your app. **Benchmark your own workload** — this is the one place vendor numbers are least
trustworthy.)*

### 7.2 Electron vs Tauri — the argument everyone is having

**[CONTESTED], and the numbers are real but not the whole story.**

**Case for Electron:**
- **Rendering consistency.** It ships its own Chromium, so CSS, WebGL, WebRTC, service
  workers, and codecs behave identically on every OS. For a visually complex or
  media-heavy app this eliminates an entire cross-platform testing burden.
- **Thirteen years of ecosystem**: `electron-builder`, `electron-updater`, code-signing
  recipes, crash reporting, native modules, Stack Overflow answers for every failure mode.
- **Proven at the top end**: VS Code, Slack, Discord, Notion, Postman, 1Password, Obsidian,
  Figma desktop. These are not accidents; they're evidence the trade-offs are survivable
  at billion-user scale.
- Bundle size rarely blocks a *desktop* install the way it would on mobile.

**Case for Tauri 2:**
- **Order-of-magnitude smaller bundles and ~4–5× lower idle memory**, because it uses the
  OS WebView (WKWebView on macOS, WebKitGTK on Linux, WebView2 on Windows) plus a Rust
  backend with no bundled runtime.
- **Capability-based permission model** — you declare exactly which commands the frontend
  may invoke. This is materially easier to defend in a SOC 2 / HIPAA audit than "Node is
  available in the renderer, we promise we turned it off."
- Smaller attack surface; memory-safe backend.
- **Tauri 2 (stable) added iOS and Android**, making one codebase span desktop and mobile.

**Case against Tauri (the honest knocks):**
- **WebView heterogeneity is the cost you pay for the small bundle.** WebKitGTK on Linux
  is meaningfully behind Chromium; you will hit "works in Chrome, broken in the Linux
  build" bugs. Your testing matrix expands even as your bundle shrinks.
- Native integrations require Rust. If nobody on the team writes Rust, "we'll just add a
  small native command" is not small.
- Fewer battle scars at very large scale.

**Migration reality**: porting a mid-size Electron app is commonly reported at ~2–3 months
— you must reimplement every Node native integration in Rust, rework IPC, and chase
WebView rendering differences. Do it when bundle size or memory is causing *actual user
pain*, not on principle.

**Also in this space**: **Wails 3** (Go backend, clean DX, performance claims still mostly
vendor-reported), and **`deno desktop`** (shipped in Deno 2.9, June 2026) — best ergonomics
for porting an existing web app, but explicitly experimental, and Deno's own docs concede
Tauri produces far smaller apps.

### 7.3 If you go the web-shell route: the security baseline

```js
// main.js — the settings that separate a safe Electron app from a browser
// with filesystem access. These are non-negotiable.
const win = new BrowserWindow({
  webPreferences: {
    contextIsolation: true,       // MUST be true (default since Electron 12)
    nodeIntegration: false,       // MUST be false
    sandbox: true,                // renderer in an OS sandbox
    webSecurity: true,            // never disable to "fix" CORS
    preload: path.join(__dirname, 'preload.js'),
  }
});

// preload.js — expose a MINIMAL, typed, validated surface. Never expose ipcRenderer.
const { contextBridge, ipcRenderer } = require('electron');
contextBridge.exposeInMainWorld('api', {
  // Good: one narrow, named operation
  readConfig: () => ipcRenderer.invoke('config:read'),
  // BAD (do not do this): send: (ch, ...a) => ipcRenderer.send(ch, ...a)
});

// main process — validate EVERY argument. The renderer is untrusted.
ipcMain.handle('config:read', async (event) => {
  if (!isTrustedSender(event.senderFrame)) throw new Error('untrusted');
  return await loadConfigFromKnownPath();   // never a caller-supplied path
});
```
Plus: a strict **Content-Security-Policy**; block `will-navigate` and
`setWindowOpenHandler` to external origins; never `shell.openExternal()` a URL that came
from remote content; **keep Electron current** (you inherit every Chromium CVE, and old
Electron versions are a standing supply-chain liability).

Tauri's equivalent discipline: keep the capability/permission JSON tight, validate command
arguments in Rust, and don't enable `withGlobalTauri` in production.

### 7.4 Rust GUI — the honest 2026 assessment

The ecosystem is real but **fragmented, and every option is a compromise.**

| Library | Model | Best for | Weakness |
|---|---|---|---|
| **egui** (eframe) | Immediate mode | Tools, debug UIs, fastest zero→window | Non-native look; no retained accessibility model; re-renders continuously |
| **iced** | Elm/functional | Structured apps; more native feel than egui | Documentation gaps; ecosystem thinner |
| **Slint** | Declarative DSL | Polished product UI, embedded + desktop; commercial licensing available | DSL is another language; smaller community |
| **Dioxus** | React-like | Web devs; can render via WebView or natively | WebView path inherits WebView trade-offs |
| **Xilem** | Data-first, from the Druid team | Aligned with Rust's architecture; the "future" bet | Still maturing |
| **GPUI** | GPU-first, from Zed | Extreme performance, custom rendering | Effectively Zed's framework; limited outside it |
| **gtk4-rs / cxx-qt** | Bindings | You want a *real* mature toolkit with Rust | You're using GTK/Qt, with binding friction |
| **wxDragon / fltk-rs** | Bindings to native | **Genuinely native controls → free screen-reader accessibility** | Older toolkits, dated aesthetics |

**[CONTESTED] Is Rust GUI production-ready?** Advocates point to shipping apps and rapid
improvement. Skeptics point to a widely-circulated 2026 write-up in which a developer
benchmarked egui, iced, Slint, and GTK for a data-heavy table application (search, filter,
sort, inline edit), hit walls in each, and shipped Electron for the UI with Rust for the
core. Both accounts are honest. **The reliable synthesis:** Rust GUI is ready for tools,
utilities, and apps where you control the design; it is not yet a low-risk choice for
dense, data-grid-heavy business applications, and **accessibility is the weakest link**
across every self-drawn Rust toolkit.

---

## §8. Application Architecture and Patterns

### 8.1 The layering that survives contact with two platforms

```
┌───────────────────────────────────────────────────────┐
│ Platform UI      SwiftUI/AppKit  │  GTK4/Qt6           │ ← thin, idiomatic, per-platform
├──────────────────────────────────┴──────────────────── ┤
│ Presentation     view models / stores / commands       │ ← testable, platform-free
├───────────────────────────────────────────────────────┤
│ Domain           entities, rules, use cases            │ ← pure. no I/O, no UI, no clock
├───────────────────────────────────────────────────────┤
│ Ports (traits/protocols)  FileStore, Clock, Net, Prefs │ ← the seam
├───────────────────────────────────────────────────────┤
│ Adapters         real FS, real network, real keychain  │ ← platform-specific, thin
└───────────────────────────────────────────────────────┘
```
**[UNIVERSAL] The domain layer must not import a UI framework, a clock, or a filesystem.**
Everything it needs comes in through a port you can substitute in tests. This is the single
highest-leverage architectural decision in a desktop app, for the same reason it is in
firmware: it converts a 30-second click-through into a 30-millisecond test.

### 8.2 State management

| Pattern | Where it's idiomatic | Notes |
|---|---|---|
| **MVVM** | SwiftUI (`@Observable` view models), Qt/QML, Avalonia, WPF-lineage | The desktop default. Keep view models free of framework types. |
| **MVC** | AppKit, GTK (loosely) | Classic; degrades into massive controllers without discipline |
| **Unidirectional / Redux-ish** | Elm-inspired (iced), TCA on Apple platforms, Electron+Redux | Excellent for undo/replay/time-travel; verbose |
| **MVP / MVVM-C** | Large enterprise apps | Explicit navigation ownership |

**[UNIVERSAL] Single source of truth.** Desktop apps have multiple windows, inspectors,
sidebars, and a menu bar all reflecting the same state. The moment two of them own
overlapping state, you get the classic desktop bug: change something in the inspector, and
the sidebar shows the old value. One store; views derive.

### 8.3 The document model, undo, and autosave

Desktop apps that edit user data have obligations that web apps don't:

- **Undo/redo is not optional** and it must be *unlimited* by default, *coalescing*
  (typing 30 characters is one undo step, not 30), and *scoped per document window*.
  - macOS: `UndoManager` — register undo closures at the model layer, not the view layer.
  - Cross-platform: a command/memento stack in your domain layer. Storing *inverse
    operations* scales better than storing full snapshots.
- **Autosave + versioning.** macOS gives you `NSDocument` autosave-in-place and Versions
  browsing largely for free; SwiftUI's `DocumentGroup` inherits it. On Linux you implement
  it: write to a temp file in the same directory, `fsync`, then `rename()` (atomic on the
  same filesystem). **Never truncate-and-write the user's file in place** — a crash
  mid-write destroys their data.
- **Dirty state and window close.** Modified documents must prompt. macOS convention: the
  close button shows a dot; the sheet offers Save/Don't Save/Cancel.
- **Crash recovery.** Periodically persist an unsaved-changes journal; offer restoration
  on next launch. Users forgive crashes; they don't forgive lost work.

```swift
// Undo done at the model layer, with coalescing — the shape that works
final class TextModel {
    private(set) var text: String = ""
    weak var undoManager: UndoManager?
    private var coalescingToken: Int = 0

    func replace(with new: String, actionName: String, coalesce: Bool = false) {
        let old = text
        if coalesce && undoManager?.isUndoing == false {
            // group rapid edits into one undoable action
            undoManager?.groupsByEvent = false
        }
        undoManager?.registerUndo(withTarget: self) { target in
            target.replace(with: old, actionName: actionName)   // inverse re-registers redo
        }
        undoManager?.setActionName(actionName)   // "Undo Typing" in the Edit menu
        text = new
    }
}
```

### 8.4 Threading and responsiveness

**[UNIVERSAL] The main thread budget is ~8 ms per frame at 120 Hz, ~16 ms at 60 Hz.**
Everything else goes off it.

| Work | Where |
|---|---|
| Any file I/O (yes, even "small" reads) | Background |
| Network | Background |
| Parsing, decoding, compression | Background |
| Database queries | Background (or a dedicated actor/queue) |
| Layout, drawing, widget mutation | **Main only** |
| Sorting/filtering a 10k-row list | Background, deliver a prepared snapshot |

Platform mechanics: macOS → Swift Concurrency (`@MainActor` + `actor` + `Task`) or GCD.
GTK → do work on a thread, marshal back with `glib::idle_add_local` /
`g_main_context_invoke`. Qt → `QThread`/`QtConcurrent` + queued signal-slot connections
(cross-thread signals are queued automatically, which is the point).

> **⚠️ GOTCHA — the progress indicator that isn't.** A spinner rendered on the same
> thread that's blocked doesn't spin. If your "loading" UI freezes, the work is on the
> main thread. This is diagnostic, not cosmetic.

**Cancellation is a first-class requirement on desktop.** Users close windows, switch
documents, and retype search queries. Every long operation needs a cancellation token
checked at intervals, and a UI affordance to trigger it.

### 8.5 IPC and multi-process design

Reasons to split processes: crash isolation, privilege separation, plugin sandboxing,
using a different language/runtime for part of the app.

| Platform | Mechanism |
|---|---|
| macOS | **XPC** (lifecycle-managed, typed, launchd-integrated) |
| Linux | **D-Bus** (discoverable, desktop-standard) or plain Unix sockets |
| Cross-platform | Unix domain sockets + a length-prefixed framed protocol; or gRPC; or stdin/stdout with JSON-RPC (what LSP does, and it works fine) |

**[UNIVERSAL] Design the protocol to be versioned and forward-compatible from message
one.** In a desktop app the two processes can end up at different versions during an
update; ignoring unknown fields and negotiating a version at handshake avoids a whole
class of upgrade bugs.

### 8.6 Single instance, and the launch protocol

Desktop users expect: clicking the launcher when the app is running **raises the existing
window**; opening a file when the app is running opens it in the running instance.

- macOS: automatic. `NSApplication` handles reopen and `application(_:open:)`.
- Linux: `GtkApplication`/`GApplication` with `G_APPLICATION_HANDLES_OPEN` gives you
  D-Bus-based single-instance and `Open`/`Activate` for free. Qt requires
  `QtSingleApplication`-style code or your own lock file + D-Bus name.
- **⚠️ GOTCHA:** a lock file in `/tmp` is not a correct single-instance mechanism — it
  survives crashes, breaks across users, and fails under Flatpak. Own a D-Bus name.

---

## §9. The Desktop Idioms — what makes an app feel native

This section is the difference between "a program with a window" and "a Mac app" / "a
GNOME app." It is mostly unglamorous and almost entirely what users notice.

### 9.1 Windows

- **Restore state**: size, position, which display, scroll offset, open documents,
  sidebar width, selected tab. macOS: `NSWindow.setFrameAutosaveName` /
  `@SceneStorage`; Linux: persist to `$XDG_STATE_HOME` yourself (Wayland will not let
  you set absolute position — restore *size* and let the compositor place it).
- **Multi-window is the norm on desktop**, not an edge case. Two documents open side by
  side must not share mutable state.
- **Minimum sizes** that are actually usable, and **resizability** that reflows rather
  than clips.
- **Multi-monitor**: different scale factors per display, windows dragged between them
  mid-render, monitors disconnected while a window is on them. Test all three.

### 9.2 Menus and keyboard

**[PLATFORM] The macOS menu bar is a contract.** Users expect: an App menu with
About/Settings(⌘,)/Services/Hide/Quit(⌘Q); File with New(⌘N)/Open(⌘O)/Close(⌘W)/Save(⌘S);
Edit with Undo(⌘Z)/Redo(⇧⌘Z)/Cut/Copy/Paste/Select All; a Window menu with
Minimize(⌘M)/Zoom and the window list; a Help menu with searchable help. **Every command
in your app should be in a menu**, even if it's also a toolbar button — that's how Help
search and accessibility find it, and how power users discover shortcuts.

**[PLATFORM] On Linux, menu conventions are contested.** GNOME's HIG moved away from menu
bars toward header bars with a hamburger menu; KDE retains traditional menu bars. If you
use libadwaita you follow GNOME; if you use Qt/KDE you follow the traditional model. Either
is defensible; **inconsistency within your own app is not.**

**Keyboard, everywhere [UNIVERSAL]:**
- Full keyboard navigation: Tab order that matches visual order, Escape closes/cancels,
  Enter activates the default, arrow keys move within lists/grids.
- Visible focus indicators. (Removing the focus ring because it's "ugly" is an
  accessibility regression; style it instead.)
- Don't steal system shortcuts. On Linux, don't grab Super/Meta.
- Platform modifier differences: ⌘ on macOS vs Ctrl on Linux, ⌥ vs Alt, and — the one
  people always miss — **Home/End/PageUp/PageDown and word-movement semantics differ**
  (⌥← vs Ctrl+←, ⌘← vs Home).

### 9.3 Files, drag & drop, clipboard

- **Use the platform file dialog.** On macOS, `NSOpenPanel`/`fileImporter`. On Linux, the
  **FileChooser portal** — even if you're not sandboxed, because it gives the user their
  desktop's real dialog, with their bookmarks and recent files. A custom file browser is
  almost always a mistake.
- **Drag & drop both ways.** Accept drops from Finder/Files; support dragging *out* to
  other apps. Declare the right UTIs (macOS) / MIME types (Linux).
- **Clipboard**: offer multiple representations (rich text *and* plain text; image *and*
  file reference). Respect that on Linux the clipboard lives in the source app — copying
  and then quitting loses the data unless a clipboard manager is running.
- **Recent files**: macOS `NSDocumentController` handles it; Linux uses
  `GtkRecentManager` / the `recently-used.xbel` spec.

### 9.4 Appearance: dark mode, HiDPI, theming

- **Dark mode**: use **semantic colors** (`NSColor.labelColor`, `Color.primary`,
  GTK's `@theme_fg_color`, Qt's palette roles), never hardcoded hex. React to live
  changes (macOS: `NSApp.effectiveAppearance` KVO / SwiftUI `@Environment(\.colorScheme)`;
  Linux: the **Settings portal**'s `color-scheme` key, which works for sandboxed apps too).
- **HiDPI**: ship vector assets or @2x/@3x rasters; never assume integer scale factors
  (fractional scaling is normal on Linux); test at 100%, 125%, 150%, 200%, and with two
  displays at different scales.
- **Reduce Motion / Reduce Transparency / Increase Contrast**: honour them. On macOS these
  are accessibility settings with APIs; on Linux, `gtk-enable-animations` and the
  high-contrast theme.
- **[CONTESTED] Linux theming.** Users expect apps to follow their system theme; libadwaita
  apps largely don't, and Flatpak apps can't read host theme files from inside the sandbox
  without an explicit runtime. GNOME's position is that arbitrary restyling breaks apps and
  that the accent-color/light-dark API is the supported surface. Users' position is that
  their desktop should look coherent. There is no resolution; know that you will receive
  issues about it either way.

### 9.5 Internationalization

- **Externalize every user-visible string** from commit one. Retrofitting i18n is
  brutal. macOS: `String(localized:)` + String Catalogs (`.xcstrings`). Linux: `gettext`
  (`_("...")`), `.po`/`.mo`, or Qt's `tr()` + Linguist. Rust: `fluent`.
- **Never concatenate translated fragments.** Use format strings with positional
  arguments, because word order differs.
- **Plurals** need real plural rules (Arabic has six forms), not `if n == 1`.
- **RTL** (Arabic, Hebrew) mirrors your entire layout. Toolkits do it if you use logical
  (leading/trailing) rather than physical (left/right) constraints. Test with a
  force-RTL flag before a user tells you.
- **Locale affects more than language**: date formats, decimal separators (`,` vs `.` —
  a classic parsing bug), sort order, first day of the week, paper size (A4 vs Letter),
  and address/name formats.
- Leave ~30–40% expansion room; German is long, and truncated buttons are the visible
  symptom of a fixed-width layout.

### 9.6 Accessibility

**[UNIVERSAL] Non-negotiable, increasingly a legal requirement** (ADA/Section 508 in the
US; the **European Accessibility Act** obligations that landed in 2025 for many consumer
products in the EU). The floor:
- Every interactive element has an accessible **name**, **role**, and **value**.
- Keyboard-only operation of every feature.
- Contrast ratios ≥ 4.5:1 for body text (WCAG AA).
- Respect system font size settings; don't hardcode point sizes.
- Announce dynamic changes (macOS: `NSAccessibility.post(element:notification:)`;
  ARIA-live equivalents in web shells).

**Testing**: macOS → **VoiceOver** (⌘F5) and Accessibility Inspector (bundled with Xcode).
Linux → **Orca** plus Accerciser to inspect the AT-SPI tree. Web shells → the browser's
accessibility tree devtools. **Custom-drawn UI has zero accessibility unless you build
it** — this is the strongest practical argument for native widget toolkits.

### 9.7 Performance targets that users perceive

| Metric | Target | Why |
|---|---|---|
| Cold launch to interactive | < 1 s (macOS), < 2 s | Beyond this it "feels slow" |
| Frame time | < 16 ms (60 Hz), < 8 ms (120 Hz ProMotion) | Dropped frames read as jank |
| Input → visible response | < 100 ms | Perceived as instantaneous |
| Any operation > 1 s | Must show progress | Otherwise "it froze" |
| Any operation > 10 s | Must be cancellable + backgroundable | |
| Idle CPU | ~0% | A desktop app that burns CPU idle drains laptops and gets uninstalled |
| Idle RAM | As low as the framework allows | The most common complaint about Electron apps |

**The idle-CPU point deserves emphasis.** Timers that fire every 100 ms "just in case",
animations that never stop, polling loops, and immediate-mode GUIs that re-render
continuously all produce measurable battery drain. Use event-driven updates and pause work
when the window isn't visible (macOS: `occlusionState`; Wayland: `frame` callbacks stop
for hidden surfaces — respect them rather than rendering blind).
