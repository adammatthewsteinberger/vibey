---
name: ui-ux-interaction-layout-and-visual-design
description: "Use when designing interactions, layouts, or the visual layer. Covers the genuinely different input models, the touch-target numbers, reach and the thumb zone, gestures, keyboard for accessibility and power users, feedback and state; the layout primitives, responsive vs adaptive and the modern toolkit (container queries, grid), tablet as the under-designed form factor, foldables, density and platform expectations; and visual design — typography, color, space, elevation, and depth, iconography, motion, and perceived performance as a design material."
---

# UI/UX Design: Input and Interaction, Layout and Responsiveness, and Visual Design

> **Part 2 of 5** of the *UI/UX Design Principles — Mobile, Tablet, Web, Desktop* reference (plugin `ui-ux-design-principles`), covering §4–§6. Sibling skills: `ui-ux-cognition-heuristics-and-navigation` (§0–§3), `ui-ux-design-systems-platforms-and-accessibility` (§7–§9), `ui-ux-writing-forms-research-and-ethics` (§10–§14), `ui-ux-reference` (§15–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Verified August 2026. See §17 → `ui-ux-reference` for the currency snapshot and what goes stale first.
>
> **Related:** Overlaps the `frontend-design:graphic-ux-ui-design` skill. That one is oriented to implementation-time component and token decisions; this one is oriented to design reasoning, cross-form-factor principles, research method, and the regulatory landscape. Use both.

> **How to read this.** Reference, not tutorial. Sections are independent. Three markers:
> - **[DURABLE]** — grounded in perception, cognition, motor control, or decades of
>   replicated research. Does not expire. Trust it.
> - **[PLATFORM]** — a convention of Apple, Google, Microsoft, GNOME/KDE, or the web.
>   Verify against the current HIG; these change.
> - **[CONTESTED]** — competent practitioners disagree, or the evidence is thinner than the
>   confidence with which it's usually asserted. Both cases given.
>
> **⚠️ GOTCHA** boxes mark the mistakes that survive design review and get caught in
> production, in court, or in the analytics.
>
> **The framing that organizes everything below:** an interface is a *proposal about how
> a person should think*. Good design makes the proposal match how they already think.
> Every principle in this document is a specialization of that idea — to a thumb, a
> screen size, a screen reader, a legal regime, or an attention budget.

---

## §4. Input and Interaction

### 4.1 The input models are genuinely different

| | Touch | Mouse/trackpad | Keyboard | Voice | Stylus |
|---|---|---|---|---|---|
| Precision | Low (~9 mm) | High (1 px) | N/A (discrete) | N/A | Very high |
| Hover state | **None** | Yes | Focus | No | Hover on some |
| Right-click / secondary | Long-press | Yes | Context key | No | Barrel button |
| Multi-select | Awkward; needs a mode | Shift/Ctrl-click, marquee | Shift+arrows | No | Lasso |
| Precision editing | Painful | Good | Excellent | Poor | Excellent |
| Occlusion | **Hand covers content** | None | None | None | Hand covers |
| Discoverability | Poor (gestures invisible) | Medium | Poor without hints | Very poor | Poor |

**[DURABLE] The absence of hover on touch is a structural problem, not a detail.** Every
tooltip, every "reveal on hover" action, every hover-based preview has no touch equivalent.
Designing hover-dependent affordances means designing a desktop-only feature. And on hybrid
devices (touchscreen laptops, iPad + trackpad), *both* are possible simultaneously — so
design for the capability, not the device class (`@media (hover: hover)` and
`(pointer: coarse|fine)` exist for exactly this).

### 4.2 Touch targets — the numbers

| Standard | Minimum | Nature |
|---|---|---|
| **WCAG 2.2 SC 2.5.8 (AA)** | **24 × 24 CSS px** — or smaller with ≥24 px spacing | Legal floor for web |
| **WCAG 2.2 SC 2.5.5 (AAA)** | 44 × 44 CSS px | Aspirational |
| **Apple HIG** | **44 × 44 pt** | Platform convention (iOS/iPadOS); visionOS recommends ~60 pt because gaze+pinch is less precise |
| **Material Design** | **48 × 48 dp** (~9 mm physical) | Platform convention |
| Automotive (Google Design for Driving) | ~76 dp | Context raises the bar |

**Practical rule: design to 44–48 px minimum for anything touchable; treat WCAG's 24 px as
a floor you never actually approach.** The visual element can be smaller than the hit
target — pad it. `min-height: 44px` with the icon at 24 px inside is the standard fix.

Spacing matters as much as size: adjacent targets need ≥8 px of gap; destructive actions
need ≥16 px of separation from anything else.

### 4.3 Reach and the thumb zone

**[DURABLE, with caveats]** One-handed phone use concentrates comfortable reach in the
lower-center of the screen; top corners (especially the *opposite* top corner from the
holding hand) are hardest. Consequences:
- Primary actions belong at the **bottom** on mobile. This is why bottom sheets, bottom
  tab bars, and bottom-anchored primary buttons became standard — and why iOS moved the
  Safari address bar down.
- Destructive or rarely-used actions can live up top.
- **⚠️ Caveat:** the "thumb zone" heat maps that circulate are illustrative, not
  measured law; grip varies (one-handed 49%, cradled 36%, two-handed 15% in the
  often-cited Hoober observational study), and screens have grown since. Use it as a
  prior, not a proof.

### 4.4 Gestures

**[DURABLE] Gestures are invisible, unlabeled, and unmemorable.** Every gesture needs:
1. A **visible alternative** (a button that does the same thing), *always*.
2. A **discovery mechanism** (a hint animation on first use, a partially-revealed
   affordance like a peeking drawer edge, or an onboarding coach mark used sparingly).
3. **Reversibility** — swipe-to-delete without undo is a design defect.

Reserve system gestures: edge swipes (back/home/control center), pull-to-refresh at scroll
top, pinch-zoom. Overloading these produces conflicts users experience as "the app is
broken."

### 4.5 Keyboard — the accessibility and the power-user story at once

**[DURABLE] Full keyboard operability is simultaneously an accessibility requirement
(WCAG 2.1.1, Level A) and the single biggest efficiency win for expert users.** They are
the same feature.
- **Logical tab order** matching visual order. `tabindex` above 0 is almost always a bug.
- **Visible focus indicator** — WCAG 2.2 added SC 2.4.11 *Focus Not Obscured* and SC 2.4.13
  *Focus Appearance*. Removing `:focus` outlines without a replacement is a Level A failure.
  Use `:focus-visible` to satisfy both the mouse aesthetes and the keyboard users.
- **Escape closes; Enter confirms.** Universally expected.
- **No keyboard traps** (WCAG 2.1.2). Modals must trap *deliberately* and release on close.
- **Skip links** on the web so keyboard users can bypass repeated nav.
- Shortcuts: match platform conventions (⌘ vs Ctrl), show them in menus and tooltips, and
  don't override browser/OS reserved combinations.

### 4.6 Feedback and state

Every interactive element needs a designed **default, hover, focus, active, disabled,
loading, error, and selected** state. Missing states are where interfaces feel cheap.

**On disabled buttons [CONTESTED]:** the classic guidance is to disable a submit button
until the form is valid. The counter-position — now the majority view among accessibility
practitioners — is that disabled buttons are invisible to some assistive tech, give no
explanation, and leave the user stuck with no feedback about *why*. **Preferred pattern:
keep the button enabled, and on click, validate, focus the first error, and announce it.**
Reserve `disabled` for states that are genuinely unavailable for reasons the user already
understands.

---

## §5. Layout, Responsiveness, and Adaptation

### 5.1 The layout primitives

- **Grid** — a shared coordinate system. 12-column is a convention, not a law; what matters
  is that everything aligns to *something*.
- **Spacing scale** — a geometric or 4/8-px-based scale (4, 8, 12, 16, 24, 32, 48, 64).
  **The value of a scale is that it removes decisions and makes proximity consistent**
  (§1.3 → `ui-ux-cognition-heuristics-and-navigation`). Arbitrary spacing is the visual signature of an unsystematized product.
- **Alignment** — the cheapest way to look designed. Left-align text; align edges of related
  elements; avoid center-aligning long text (ragged left edges slow reading).
- **Measure (line length)** — **45–75 characters** for body text; ~66 is the classic
  optimum. Beyond ~90 the eye loses the line return. This constraint alone dictates
  layout on wide screens: full-width text at 1600 px is unreadable, which is why you need
  a max-width or a multi-column structure.
- **White space is not empty** — it is the mechanism of grouping and hierarchy. "Reducing
  white space to fit more" reliably makes things harder to find, not denser with
  information.

### 5.2 Responsive vs. adaptive, and the modern toolkit

**Responsive** = one fluid layout that reflows continuously. **Adaptive** = discrete
layouts swapped at breakpoints. In 2026 the practical answer is layered:

| Tool | Job |
|---|---|
| **Media queries** | Page-level structure (sidebar vs. stacked) |
| **Container queries** | **Component-level** adaptation — a card responds to *its own* available space, not the viewport. **Baseline Widely Available since August 2025** (~93% support). This is the biggest shift in responsive layout since media queries. |
| **`clamp()` fluid type/space** | Smooth scaling instead of jumps at breakpoints |
| **Intrinsic layouts** (`grid-template-columns: repeat(auto-fit, minmax(…, 1fr))`, Flexbox wrap) | Breakpoint-free layouts that just work |
| `dvh`/`svh`/`lvh` | The mobile-100vh problem (`svh` is safer where mid-scroll reflow is unacceptable) |
| `prefers-reduced-motion`, `prefers-color-scheme`, `prefers-contrast` | Respecting user settings |

```css
/* Container query: the component adapts to its context, not the window */
.card-wrap { container-type: inline-size; }
@container (min-width: 400px) {
  .card { display: grid; grid-template-columns: 120px 1fr; gap: 1rem; }
}

/* Fluid type. ⚠️ The max must not exceed ~2.5× the min, and the formula MUST
   include a rem component — a pure-vw font size fails WCAG SC 1.4.4 (Resize Text)
   because it doesn't respond to browser zoom. */
:root {
  --step-0: clamp(1rem, 0.95rem + 0.25vw, 1.125rem);
  --step-3: clamp(1.75rem, 1.4rem + 1.75vw, 3rem);
}
```

**[DURABLE] Breakpoints come from your content, not from a device list.** Resize the
browser slowly and put a breakpoint where the layout *breaks* — where the measure gets too
long, the columns get too narrow, the nav wraps. A breakpoint at 768 "because iPad" is a
coincidence, and the device it named has been irrelevant for years.

Useful *starting* ranges (then adjust to content): ~360–480 (phone portrait), ~481–767
(phone landscape / small), ~768–1023 (tablet), ~1024–1279 (small laptop), 1280+ (desktop).
Note the 768–1024 band is genuinely awkward: a single text column at 840 px exceeds the
optimal measure, but a phone layout wastes the space. Two-column, or one column with
generous side padding, is usually right.

### 5.3 Tablet — the form factor everyone under-designs

**[DURABLE] A tablet is not a big phone and not a small laptop.** The common failure is
shipping a stretched phone layout: a 1024 px-wide single column of full-width list rows
with a 900 px measure. The tablet-specific moves:
- **Split view / master–detail** is the defining tablet pattern. Use it.
- Support **multitasking**: Split View / Slide Over / Stage Manager on iPadAOS, and
  freeform/split windows on Android — meaning **your app can be any width at any time**,
  and orientation can change mid-session. This is where container queries and true
  size-class-driven layout pay off, and where "we only tested full-screen portrait" breaks.
- **Keyboard and trackpad/stylus attach and detach.** Support hover, shortcuts, and
  pointer precision when present, without requiring them.

### 5.4 Foldables and novel form factors

Foldables introduce: square-ish aspect ratios, ultra-wide unfolded states, a **hinge/fold
that content must not straddle**, and **continuity** — an app that must survive a fold/unfold
transition mid-task without losing state. Practical guidance: use adaptive layout driven by
available size (not device identity), handle configuration changes without recreating state,
avoid placing interactive elements across the fold, and test the fold transition explicitly.
Container queries handle much of this without device detection.

### 5.5 Density and platform expectations

Provide density *options* in data-heavy desktop and web apps (comfortable / compact). Users
of professional tools genuinely want more rows per screen; consumer users don't. This is
one of the few places where a preference toggle beats a designer's judgment.

---

## §6. Visual Design

### 6.1 Typography

**[DURABLE] Typography is 90% of most interfaces, and hierarchy is 90% of typography.**
- **Type scale**: a modular scale (ratios ~1.125 minor second → 1.5 perfect fifth). Fewer
  sizes is better; 5–7 steps covers nearly everything. Every extra size is a decision
  someone will make inconsistently.
- **Hierarchy comes from size + weight + color + space — not size alone.** A well-designed
  hierarchy can use two sizes and be perfectly clear.
- **Body text**: ≥16 px on web (smaller triggers mobile zoom and fails low-vision users);
  line-height ~1.4–1.6 for body, tighter (1.1–1.25) for large headings.
- **Measure**: 45–75 characters (§5.1).
- **Never disable user font scaling.** iOS Dynamic Type and Android font scale are used by
  a large number of people; a layout that breaks at 200% text is a WCAG 1.4.4 failure
  (Level AA) and an ordinary usability failure for anyone over 45.
- **All-caps** reduces reading speed for anything longer than a couple of words — fine for
  a label, wrong for a sentence. **Letter-spacing** should increase slightly for all-caps
  and small text, decrease for large display text.
- **System fonts** (SF Pro, Roboto, Segoe, Inter, the `system-ui` stack) load instantly,
  render optimally, and support the full glyph range. Custom fonts cost LCP; subset them,
  `preload` the critical weight, and use `font-display: swap` (or `optional`) — an unstyled
  or invisible text flash is a CLS and a perceived-performance problem.

### 6.2 Color

- **Build a semantic layer.** Never let a component reference `blue-500`; let it reference
  `color.action.primary`, which *resolves* to `blue-500` in light mode and `blue-300` in
  dark. Without this layer, dark mode and theming are a rewrite (§7.2 → `ui-ux-design-systems-platforms-and-accessibility`).
- **Perceptually uniform color spaces (OKLCH/LCH)** make generating consistent ramps far
  easier than HSL, where equal lightness values look wildly different across hues. The DTCG
  token spec now includes advanced color support for exactly this reason.
- **Never encode meaning in color alone** (WCAG 1.4.1). ~8% of men have some form of color
  vision deficiency. Pair color with icon, text, pattern, or position. "Red row = error" is
  a failure; "red row with an error icon and a message" is not.
- **Contrast (see §9.3 → `ui-ux-design-systems-platforms-and-accessibility` for the standards fight):** WCAG 2.2 requires **4.5:1** for body
  text, **3:1** for large text (≥18 pt / 14 pt bold) and for UI components and graphical
  objects (SC 1.4.11).
- **Dark mode is not inverted light mode.** Pure black backgrounds with pure white text
  cause halation for many readers (especially with astigmatism); use a very dark gray
  (~#121212) and slightly desaturated, lighter foreground colors. Elevation in dark mode is
  expressed by *lighter* surfaces, not by shadows (shadows are nearly invisible on dark).
  Desaturate saturated brand colors or they vibrate.

### 6.3 Space, elevation, and depth

- **Spacing scale** (§5.1) — 4 or 8 px base, geometric growth.
- **Elevation** communicates layering and modality: content < raised card < sticky header <
  dropdown < modal < toast. Keep the z-index scale as **named tokens**, not magic numbers
  (`z.modal: 1000`), or you will end up with `z-index: 99999`.
- Use **one** depth language. Mixing shadows, borders, and background-fills to mean the
  same thing produces visual noise.

### 6.4 Iconography

- **Icons are not universally understood.** Only a handful are (search 🔍, home, print,
  trash, back arrow, close ×, play). Everything else — especially abstract product concepts
  — needs a **text label**. Icon-only toolbars are consistently outperformed by icon+label
  in findability testing.
- Consistent grid, stroke weight, corner radius, and optical size across the set.
- **Tooltips are not a solution on touch** (no hover, §4.1).
- Every icon that conveys meaning needs an accessible name; every purely decorative icon
  needs to be hidden from assistive tech (`aria-hidden="true"`, `alt=""`).

### 6.5 Motion

**[DURABLE] Motion's job is to explain, not to decorate.** Legitimate uses:
1. **Continuity** — show where a thing came from and went (shared-element transitions).
2. **Feedback** — confirm the tap registered.
3. **Attention** — direct the eye to a change.
4. **Perceived performance** — mask latency, communicate progress.

Timing: **UI transitions 150–300 ms**; enter slightly slower than exit; larger objects
slower than small ones. Easing: **ease-out for entering** (fast then settle),
**ease-in for exiting**. Linear easing looks mechanical and is almost always wrong.
Spring/physics-based motion (now first-class in Material 3 Expressive and SwiftUI) feels
more natural for direct-manipulation gestures because it preserves velocity continuity.

**`prefers-reduced-motion` is not optional.** Vestibular disorders make large parallax,
zoom, and slide animations genuinely nauseating. Honour the setting by replacing motion
with a cross-fade or an instant change — not by removing the feedback entirely.

### 6.6 Perceived performance is a design material

| Wait | Design response |
|---|---|
| < 100 ms | Feels instant. Do nothing. |
| 100 ms – 1 s | Users notice but stay in flow. Subtle state change. |
| 1 – 10 s | **Show progress.** Skeleton screens > spinners (they signal structure). Determinate > indeterminate. |
| > 10 s | Progress + estimate + **cancel** + ability to leave and be notified. |

**Optimistic UI** (apply the change immediately, reconcile with the server later) is the
single most effective perceived-performance technique — and the most commonly botched.
The rule: if you show success optimistically, you owe the user an honest, non-destructive
recovery when it fails. Silently reverting is worse than having waited.

**Core Web Vitals** are the closest thing the web has to a shared performance contract, and
they are field metrics (real Chrome users, 75th percentile, 28-day window) — not lab scores:

| Metric | "Good" threshold | What it measures |
|---|---|---|
| **LCP** | ≤ **2.5 s** | Loading — when the largest visible element paints |
| **INP** | ≤ **200 ms** | Responsiveness — full interaction lifecycle (**replaced FID in March 2024**) |
| **CLS** | ≤ **0.1** | Visual stability — unexpected layout shift |

**INP is the one most sites fail** (roughly 43% miss the 200 ms threshold), because fixing
it requires JavaScript architecture changes — yielding to the main thread, breaking up long
tasks — not just compressing an image. **CLS is the most *design*-caused**: always set
explicit `width`/`height` (or `aspect-ratio`) on images, videos, iframes, and ad slots, and
reserve space for anything that loads late.
