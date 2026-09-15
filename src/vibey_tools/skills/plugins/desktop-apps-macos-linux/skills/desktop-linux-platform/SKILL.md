---
name: desktop-linux-platform
description: "Use when building or debugging a Linux desktop app. Covers why 'Linux' is not one platform (the stack, XDG base directories, .desktop files and app IDs), D-Bus as the desktop's nervous system, PipeWire, the honest accessibility picture, GTK4 + libadwaita, Qt 6, the other toolkits, and the Wayland transition — what Wayland takes away from X11 (global hotkeys, window positioning, screen capture) and what replaces it (portals, layer-shell)."
---

# Desktop Apps (macOS & Linux): Linux Desktop Architecture, Toolkits, and Wayland

> **Part 2 of 5** of the *Desktop Application Programming — macOS & Linux* reference (plugin `desktop-apps-macos-linux`), covering §4–§6. Sibling skills: `desktop-macos-platform` (§0–§3), `desktop-cross-platform-and-architecture` (§7–§9), `desktop-packaging-security-and-testing` (§10–§13), `desktop-reference` (§14–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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

## §4. Linux Desktop Architecture

### 4.1 The stack — and why "Linux" isn't one platform

```
┌─────────────────────────────────────────────────────────┐
│ Your app: GTK4 / Qt6 / Electron / Tauri / SDL / raw      │
├─────────────────────────────────────────────────────────┤
│ Toolkit + desktop integration: libadwaita / KDE Frameworks│
│ XDG Desktop Portals (D-Bus) ── the sandbox-safe API       │
├─────────────────────────────────────────────────────────┤
│ Session services: D-Bus, systemd --user, PipeWire,        │
│ PolicyKit, UPower, NetworkManager, AT-SPI/Newton (a11y)   │
├─────────────────────────────────────────────────────────┤
│ Display: Wayland compositor (Mutter/KWin/wlroots/COSMIC)  │
│          + XWayland for legacy X11 clients                │
├─────────────────────────────────────────────────────────┤
│ Graphics: Mesa, DRM/KMS, GBM, Vulkan/OpenGL               │
├─────────────────────────────────────────────────────────┤
│ Kernel: Linux, evdev/libinput, udev                       │
└─────────────────────────────────────────────────────────┘
```

**[UNIVERSAL for Linux] The single most useful mental model: there is no vendor, only
specs.** freedesktop.org publishes the conventions; GNOME, KDE, and everyone else
implement them with varying completeness. Your app's job is to speak the specs, not to
target a desktop environment. Apps that hardcode "if GNOME then X" age badly.

**The specs you must actually know:**

| Spec | What it governs | Practical impact |
|---|---|---|
| **XDG Base Directory** | Where files go | `$XDG_CONFIG_HOME` (`~/.config`), `$XDG_DATA_HOME` (`~/.local/share`), `$XDG_CACHE_HOME` (`~/.cache`), `$XDG_STATE_HOME` (`~/.local/state`), `$XDG_RUNTIME_DIR` (`/run/user/UID`, tmpfs, cleared at logout) |
| **Desktop Entry** | `.desktop` files | How your app appears in menus/launchers, handles MIME types, declares actions |
| **Icon Theme** | Icon lookup | Ship SVG at `hicolor/scalable/apps/<app-id>.svg`; never hardcode a path |
| **AppStream (MetaInfo)** | App store metadata | Required by Flathub and by GNOME Software/Discover to show your app at all |
| **MIME (shared-mime-info)** | File types | Custom formats need a MIME XML + magic bytes |
| **Notifications** | `org.freedesktop.Notifications` | D-Bus, not a toolkit API |
| **Autostart** | `~/.config/autostart/*.desktop` | Launch at login (or use a systemd user unit) |
| **Secret Service** | Credential storage | `libsecret` → GNOME Keyring / KWallet. **The Keychain equivalent.** |
| **XDG Desktop Portal** | Sandboxed access to host resources | §12.3 → `desktop-packaging-security-and-testing` — increasingly the *only* way to do screen capture, and the *best* way to do file dialogs |
| **Trash** | `~/.local/share/Trash` | Don't `unlink()` user files; use `gio trash` semantics |

```ini
# /usr/share/applications/com.example.MyApp.desktop  (or ~/.local/share/applications)
# The filename SHOULD equal your app ID — Wayland window matching depends on it.
[Desktop Entry]
Type=Application
Name=My App
Comment=Short one-line description shown in launchers
Exec=myapp %U
Icon=com.example.MyApp
Terminal=false
Categories=Utility;TextEditor;
MimeType=text/plain;application/x-myformat;
StartupNotify=true
StartupWMClass=com.example.MyApp
Keywords=notes;editor;markdown;
X-GNOME-UsesNotifications=true

[Desktop Action NewWindow]
Name=New Window
Exec=myapp --new-window
```

> **⚠️ GOTCHA — the app ID must match everywhere.** Your D-Bus name, `.desktop` filename,
> icon filename, AppStream `<id>`, Flatpak app ID, GTK `Application` `application-id`, and
> (critically) the Wayland `app_id` your toolkit reports must all be the same reverse-DNS
> string. When they don't match, the symptom is: your window shows a generic icon in the
> dock/overview, notifications aren't attributed to your app, and "focus existing window"
> doesn't work. This is the single most common Linux packaging bug and it's invisible in
> development.

```xml
<!-- /usr/share/metainfo/com.example.MyApp.metainfo.xml — required for Flathub -->
<component type="desktop-application">
  <id>com.example.MyApp</id>
  <name>My App</name>
  <summary>Edit notes quickly</summary>
  <metadata_license>CC0-1.0</metadata_license>
  <project_license>GPL-3.0-or-later</project_license>
  <description><p>Longer description. Shown in software centres.</p></description>
  <launchable type="desktop-id">com.example.MyApp.desktop</launchable>
  <screenshots>
    <screenshot type="default"><image>https://example.com/shot1.png</image></screenshot>
  </screenshots>
  <content_rating type="oars-1.1"/>
  <releases>
    <release version="1.2.0" date="2026-08-01">
      <description><p>Fixed the thing.</p></description>
    </release>
  </releases>
  <branding><color type="primary" scheme_preference="light">#3584e4</color></branding>
</component>
```

### 4.2 D-Bus — the desktop's nervous system

Two buses: the **system bus** (root services: NetworkManager, UPower, logind, UDisks) and
the **session bus** (per-login: notifications, portals, your app, media players).

Anatomy: **bus name** (`org.freedesktop.Notifications`) → **object path**
(`/org/freedesktop/Notifications`) → **interface** (`org.freedesktop.Notifications`) →
**method/signal/property**.

```bash
# The three commands that make D-Bus tractable
busctl --user list                              # what's on the session bus
busctl --user introspect org.freedesktop.portal.Desktop /org/freedesktop/portal/desktop
gdbus call --session --dest org.freedesktop.Notifications \
  --object-path /org/freedesktop/Notifications \
  --method org.freedesktop.Notifications.Notify \
  "MyApp" 0 "dialog-information" "Title" "Body" "[]" "{}" 5000
```

**Why your app should own a D-Bus name**: single-instance enforcement, `Activate`/`Open`
actions from the launcher, MPRIS media control, and the `org.freedesktop.Application`
interface. GTK's `GApplication` and Qt's `QDBusConnection` both give you this. It is also
how "click the launcher again and raise the existing window" works.

**systemd user units** (`~/.config/systemd/user/`) are the modern way to run a background
helper, with socket activation, restart policy, and journal integration — the launchd
equivalent, and preferable to a stray autostart `.desktop` for anything daemon-shaped.

### 4.3 Audio/video: PipeWire

**PipeWire has replaced PulseAudio and JACK** as the default on essentially all modern
distributions, handling both audio and video streams with low latency. What app developers
need:
- Use a **high-level API** (GStreamer, libpulse compatibility, or PipeWire's own) rather
  than talking to ALSA directly.
- **Screen capture on Wayland goes through PipeWire** via the ScreenCast portal — there is
  no `XShmGetImage` equivalent. This is the #1 porting surprise for screenshot, screen
  recording, and video-conferencing apps.
- **WirePlumber** is the session manager (policy); PipeWire is the transport. Bugs are
  usually WirePlumber policy, not PipeWire.
- PipeWire requires an active **D-Bus session bus**. In minimal WM setups without one,
  everything silently fails — `dbus-run-session` is the fix.

### 4.4 Accessibility on Linux — the honest picture

**[UNIVERSAL] Build for accessibility from the start.** On Linux specifically:
- **AT-SPI2** over D-Bus is the current accessibility API. **Orca** is the dominant screen
  reader; **Odilia** is a newer entrant. GTK4 rewrote its a11y layer to talk to the AT-SPI
  registry directly; KDE Plasma 6 added AT-SPI2 support in 6.0.
- **AT-SPI has real architectural problems under Wayland and sandboxing**: the accessibility
  tree is severed from the windowing system (so an AT can't verify an event came from the
  focused app), and its "chatty IPC" requires many round trips, producing latency that
  makes a screen reader unresponsive when the app is merely busy.
- **Newton** is the in-progress Wayland-native replacement (built on AccessKit, with
  Wayland protocol and Mutter/GTK work), specifically designed so **Flatpak apps get
  accessibility without punching a hole in the sandbox for the AT-SPI bus**. It is
  experimental as of 2026 — track it, don't depend on it.
- **The field is chronically under-resourced** — credible assessments put the number of
  people working significantly on Linux a11y in the single digits historically. This means:
  use your toolkit's standard widgets (which carry a11y for free), don't roll custom
  controls without accessible implementations, and test with Orca yourself, because nobody
  else will.

---

## §5. Linux UI Toolkits

### 5.1 GTK4 + libadwaita

**GTK 4** is the current major version (4.22.x as of mid-2026); **libadwaita** is the
separate library that supplies GNOME's design language: adaptive containers, modern
widgets (`AdwToastOverlay`, `AdwNavigationSplitView`, `AdwPreferencesPage`,
`AdwStatusPage`), and the Adwaita style.

**[CONTESTED] The GTK/libadwaita split is politically live.** GNOME's position: GTK is a
general toolkit; libadwaita is GNOME's design language layered on top, so GTK doesn't have
to encode one desktop's opinions. Critics (notably from the Mint/Cinnamon direction, and
much of the theming community): libadwaita apps resist system theming, look foreign
outside GNOME, and the split effectively makes "GTK app" mean "GNOME app." Both readings
are defensible. **Practical consequence for you:** if you use libadwaita, your app will
look excellent on GNOME and slightly alien on KDE/XFCE, and users *will* file issues about
theming. If you use plain GTK4 without libadwaita, you get more theme neutrality and less
polish.

```c
/* GTK4 + libadwaita, C. Note GtkApplication gives you D-Bus name ownership,
   single-instance, and the org.freedesktop.Application interface for free. */
#include <adwaita.h>

static void on_activate(GtkApplication *app, gpointer user_data) {
    GtkWidget *window = adw_application_window_new(app);
    gtk_window_set_default_size(GTK_WINDOW(window), 900, 600);

    GtkWidget *header = adw_header_bar_new();
    GtkWidget *toast_overlay = adw_toast_overlay_new();
    GtkWidget *content = gtk_box_new(GTK_ORIENTATION_VERTICAL, 0);

    gtk_box_append(GTK_BOX(content), header);
    gtk_box_append(GTK_BOX(content), toast_overlay);
    adw_application_window_set_content(ADW_APPLICATION_WINDOW(window), content);
    gtk_window_present(GTK_WINDOW(window));
}

int main(int argc, char **argv) {
    /* app id MUST match .desktop filename, icon name, and AppStream id */
    AdwApplication *app = adw_application_new("com.example.MyApp",
                                              G_APPLICATION_HANDLES_OPEN);
    g_signal_connect(app, "activate", G_CALLBACK(on_activate), NULL);
    int status = g_application_run(G_APPLICATION(app), argc, argv);
    g_object_unref(app);
    return status;
}
```

```rust
// GTK4 from Rust via gtk4-rs — increasingly the default for new GTK apps.
// Keep the gtk4 and libadwaita crate versions in lockstep; they're coupled.
use adw::prelude::*;
use adw::{Application, ApplicationWindow, HeaderBar};
use gtk::{Box as GtkBox, Orientation};

fn main() -> glib::ExitCode {
    let app = Application::builder()
        .application_id("com.example.MyApp")
        .build();
    app.connect_activate(|app| {
        let content = GtkBox::new(Orientation::Vertical, 0);
        content.append(&HeaderBar::new());
        ApplicationWindow::builder()
            .application(app)
            .default_width(900).default_height(600)
            .content(&content)
            .build()
            .present();
    });
    app.run()
}
```
Note the trend: GNOME itself is migrating components to Rust (GNOME Disks' 51 rewrite
moved UI code and libgdu utilities to Rust talking to UDisks2 via `udisks-rs`). gtk4-rs is
production-grade.

**GTK4 concepts that trip people up:** the shift from GTK3's `pack_start`/container model
to explicit `append`/single-child layout; `GtkListView`/`GtkColumnView` with
`GListModel`+factories replacing `GtkTreeView`/`GtkListStore`; CSS-based styling with GTK's
own subset (not web CSS); `GtkEventController` replacing direct event handling; and
`GtkBuilder`/`.ui` XML plus **Blueprint** (a friendlier DSL that compiles to `.ui`) for
declarative UI.

**GTK5** is not imminent; treat GTK4 as the target for the foreseeable future.

### 5.2 Qt 6

Current: **Qt 6.11.x** (6.11.1, May 2026), on a ~6-month minor cadence. **Licensing is the
decision, not the technology:**
- **LGPLv3** (most modules): free, but you must permit relinking — practically, dynamic
  linking, or shipping object files. Some modules are **GPL-only** (notably Qt Charts,
  Qt Data Visualization, and parts of the tooling), which will contaminate a proprietary
  app if you use them.
- **Commercial**: required for static linking in a closed-source product, and for LTS
  patch releases. **LTS patch releases are commercial-only**; open-source users get LTS
  branches treated as ordinary releases. Since 6.8.0, LTS support runs five years
  (three before that).
- The KDE Free Qt Foundation agreement is the backstop that keeps Qt open-source.

**Qt Widgets vs Qt Quick/QML [CONTESTED]:**
- *Widgets*: mature, native-ish look, excellent for dense desktop tools (IDEs, CAD,
  engineering software), C++ only, retained-mode. Not deprecated but not where new
  investment goes.
- *Quick/QML*: declarative, GPU-accelerated, animation-friendly, JavaScript for logic,
  designed for touch/embedded/fluid UI. Better for modern-looking apps; worse for dense
  data grids and for teams that don't want a second language in the build.
- Most desktop-tool companies still ship Widgets. Most new embedded/HMI work is Quick.

**PySide6** (official, LGPL) and **PyQt6** (Riverbank, GPL/commercial) are the Python
bindings; PySide6's licensing is friendlier for proprietary work. Note that free-threaded
(GIL-less) Python support is still being worked out because a GIL-less runtime requires
Qt's own locking against the event loop.

### 5.3 The rest

| Toolkit | Status | Use when |
|---|---|---|
| **wxWidgets** | Alive, native controls per platform | You want genuinely native widgets and C++ |
| **FLTK** | Alive, tiny | Minimal dependency footprint, simple tools |
| **Tk/Tkinter** | Alive, ancient | Python scripts that need *a* window |
| **Dear ImGui** | Thriving | Debug UIs, tools, game editors. Immediate-mode; not for consumer apps |
| **EFL/Enlightenment** | Niche | — |
| **Motif/Xt** | Legacy | Maintaining 1990s software |

---

## §6. Wayland and X11

### 6.1 The state of the transition (2026) — this changed recently

- **GNOME removed X11 session support**: the X11 session was disabled by default in
  GNOME 49, and the X11 backend code was **removed from Mutter**, with GNOME 50 (March
  2026) shipping with no X11 code at all.
- **KDE Plasma will be Wayland-only in Plasma 6.8**, expected **October 2026**; the Plasma
  X11 session is supported into **early 2027** for 6.7 users. KDE's stated rationale: the
  vast majority of Plasma users are already on Wayland and many distros already dropped
  the X11 session independently.
- Distros moved first in several cases: **Fedora 43** and **Ubuntu 25.10** already ship
  without a GNOME X11 session.
- Other desktops lag: **XFCE 4.20** added initial Wayland support (using labwc as a
  stop-gap; xfwm4 is not yet a compositor); LXQt is further along than expected; Cinnamon
  and MATE are behind.
- **Xorg is not abandoned but its feature development is halted** — the same maintainers
  fix security issues; new capability work happens in Wayland. **XLibre** is a fork with
  more active development, of contested provenance, adopted by a small number of distros.
- **X11 applications keep working** through **XWayland**. Dropping the X11 *session* is not
  dropping X11 *apps*.

**[UNIVERSAL, practical] Your app must work under Wayland in 2026.** Testing only on X11 is
now testing on a legacy path.

### 6.2 What Wayland takes away, and what replaces it

This is the porting checklist. Under Wayland, a client **cannot**, by design:

| X11 capability | Wayland status | Replacement |
|---|---|---|
| Read other windows' pixels (screenshot/capture) | Forbidden | **ScreenCast portal** → PipeWire stream |
| Global hotkeys | Not in core | **GlobalShortcuts portal**, or compositor-specific |
| Set absolute window position | Forbidden | Compositor decides. `xdg-positioner` for popups only |
| Query/set the pointer position | Forbidden | Relative motion only (pointer-constraints for games) |
| Inject input into other apps | Forbidden | **RemoteDesktop portal**, **libEI** |
| Read the clipboard without focus | Forbidden | `wl_data_device`, requires focus/user action |
| Override-redirect windows | No | `xdg-shell` roles: toplevel, popup; `layer-shell` for panels |
| `XTest` automation | No | libEI / portal, or compositor-specific test protocols |

> **⚠️ GOTCHA — this list *is* the port.** If your app does screen capture, global
> hotkeys, remote control, window positioning, or input automation, "porting to Wayland"
> is not a rendering change — it's replacing those features with portal-mediated,
> user-consenting equivalents that have different UX (a permission prompt, a picker
> dialog). Budget for the UX redesign, not just the code.

**Server-side vs client-side decorations (SSD/CSD)** is a long-running friction point:
GNOME/Mutter prefers CSD (the app draws its own titlebar — that's what a GTK `HeaderBar`
is); KDE supports SSD via the `xdg-decoration` protocol. An app that assumes one gets
either a double titlebar or none. Toolkits handle this; hand-rolled Wayland clients must
negotiate it.

**Fractional scaling**: `wp_fractional_scale_v1` lets clients render at a fractional
buffer scale instead of rendering at 2× and downscaling (which is blurry). Modern GTK4/Qt6
support it; older toolkits and XWayland clients often don't, which is why "text is blurry
at 125%" is still a live complaint.

**Remote desktop is the current genuine regression.** GNOME and KDE offer RDP-based remote
desktop; many third-party tools require someone physically present to accept the
connection because of Wayland's permission model. TigerVNC has shipped a Wayland-first VNC
server. If your product does unattended remote access, investigate carefully — this is not
solved to X11 parity.
