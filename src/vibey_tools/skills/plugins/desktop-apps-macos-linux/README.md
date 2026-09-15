# Desktop Application Programming — macOS & Linux Plugin

A deep technical reference for building desktop applications on macOS and Linux: platform architecture on both sides, native UI toolkits (SwiftUI, AppKit, GTK4/libadwaita, Qt6), cross-platform frameworks and their trade-offs, Wayland versus X11, application architecture and the idioms that make an app feel native (windowing, menus, documents, undo), packaging and distribution, auto-update, sandboxing and permissions, accessibility, internationalization, performance, and testing.

One reference, split into 5 skills along its section groups so a task loads only the part it needs. Section numbers (§N) are shared across the set and cross-references into a sibling skill are written as §N → `skill`. Reference, not tutorial: sections are independent, every claim is tagged by how durable it is (stable fundamentals vs. versioned specifics vs. genuinely contested questions), and a currency snapshot (verified August 2026) flags what goes stale first.

## Skills

- **desktop-macos-platform** — macOS Platform, SwiftUI/AppKit, and Swift (§0–§3): Routing — Classify Before Answering; macOS Platform Architecture; macOS UI — SwiftUI and AppKit; Swift, Concurrency, and Persistence.
- **desktop-linux-platform** — Linux Desktop Architecture, Toolkits, and Wayland (§4–§6): Linux Desktop Architecture; Linux UI Toolkits; Wayland and X11.
- **desktop-cross-platform-and-architecture** — Cross-Platform Frameworks, Architecture, and Native Idioms (§7–§9): Cross-Platform Frameworks; Application Architecture and Patterns; The Desktop Idioms — what makes an app feel native.
- **desktop-packaging-security-and-testing** — Packaging, Auto-Update, Sandboxing, and Testing (§10–§13): Packaging and Distribution; Auto-Update; Security, Sandboxing, and Privacy; Testing, Debugging, and CI.
- **desktop-reference** — Anti-Patterns, Contested Questions, Canon, Case Studies, and Currency (§14–§20): Anti-Patterns; Contested Questions; The Canon — authorities and references; Case Studies and Hard-Won Lessons; Currency Snapshot; Quick Reference; Sources and Method.
