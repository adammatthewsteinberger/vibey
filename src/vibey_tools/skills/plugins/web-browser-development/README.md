# Web Browser Development Plugin

A deep technical reference for building and reasoning about web browsers: engine architecture and the multi-process model, networking, HTML parsing and the DOM, CSS and style resolution, layout, paint, and compositing, JavaScript engine integration and the event loop, the security model from the same-origin policy to site isolation and Spectre mitigations, privacy and anti-tracking, extensions, storage and media, accessibility, standards and interop, testing and telemetry, and the economics and governance of engine development.

One reference, split into 5 skills along its section groups so a task loads only the part it needs. Section numbers (§N) are shared across the set and cross-references into a sibling skill are written as §N → `skill`. Reference, not tutorial: sections are independent, every claim is tagged by how durable it is (stable fundamentals vs. versioned specifics vs. genuinely contested questions), and a currency snapshot (verified August 2026) flags what goes stale first.

## Skills

- **browser-engine-architecture-and-networking** — The Engine Landscape, Process Model and Sandboxing, and Networking (§0–§3): Routing; The Engine Landscape; Process Model, IPC, and Sandboxing; Networking.
- **browser-rendering-pipeline** — HTML Parsing and the DOM, CSS and Style, Layout, Paint, Compositing, and JavaScript Integration (§4–§7): HTML Parsing and the DOM; CSS and Style; Layout, Paint, and Compositing; JavaScript Integration.
- **browser-security-and-privacy** — The Security Model and Privacy and Anti-Tracking (§8–§9): The Security Model; Privacy and Anti-Tracking.
- **browser-extensions-platform-and-standards** — Extensions, Storage, Media, and Capabilities, Accessibility, Standards and Interop, Testing and Shipping (§10–§14): Extensions; Storage, Media, and Capabilities; Accessibility; Standards and Interop; Testing, Telemetry, and Shipping.
- **browser-development-reference** — Anti-Patterns, Contested Questions, Currency, and Canon (§15–§20): Anti-Patterns; Contested Questions; Currency Snapshot; The Canon; Quick Reference; Sources and Method.
