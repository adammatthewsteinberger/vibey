---
name: ui-ux-design-systems-platforms-and-accessibility
description: "Use when building or governing a design system, matching platform conventions, or meeting accessibility requirements. Covers what a design system actually is, the three-tier token architecture, component API design, measuring adoption; Apple HIG and Liquid Glass, Material 3 and M3 Expressive, web conventions, desktop (macOS, Windows, GNOME, KDE), consistency vs nativeness; and accessibility — the standards and the law in 2026 (WCAG 2.2/3.0, EN 301 549, the European Accessibility Act, ADA Title II), contrast and the APCA question, the practical checklist, and testing."
---

# UI/UX Design: Design Systems and Tokens, Platform Conventions, and Accessibility

> **Part 3 of 5** of the *UI/UX Design Principles — Mobile, Tablet, Web, Desktop* reference (plugin `ui-ux-design-principles`), covering §7–§9. Sibling skills: `ui-ux-cognition-heuristics-and-navigation` (§0–§3), `ui-ux-interaction-layout-and-visual-design` (§4–§6), `ui-ux-writing-forms-research-and-ethics` (§10–§14), `ui-ux-reference` (§15–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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

## §7. Design Systems and Tokens

### 7.1 What a design system actually is

Not a component library. A design system is **a set of shared decisions, encoded so they
can't drift** — plus the governance that keeps them shared. It has four layers:

```
Principles        — how we decide (rarely written well, hugely valuable when it is)
Foundations       — tokens: color, type, space, radius, elevation, motion, breakpoints
Components        — buttons, inputs, dialogs; with documented props, states, a11y behaviour
Patterns          — how components compose into recurring solutions (forms, empty states,
                    destructive flows, onboarding, data tables)
```
Plus: documentation, contribution model, versioning, deprecation policy, and adoption
metrics. **A component library without governance decays into a component graveyard.**

### 7.2 Token architecture — the three-tier model

```
Tier 1  PRIMITIVE / global    blue-500 = #3B82F6      spacing-4 = 16px
          ↓ referenced by
Tier 2  SEMANTIC / alias      color.action.primary → blue-500       (light)
                              color.action.primary → blue-300       (dark)
                              space.stack.md → spacing-4
          ↓ referenced by
Tier 3  COMPONENT-SPECIFIC    button.primary.background → color.action.primary
```
**[DURABLE] Components must only ever reference tiers 2 and 3.** The moment a component
hardcodes `blue-500`, you cannot theme, cannot do dark mode without a rewrite, and cannot
rebrand. This one rule is most of the value of tokens.

**The DTCG spec is now real.** The **W3C Design Tokens Community Group published its first
stable specification, version 2025.10, on 28 October 2025** — a vendor-neutral JSON
interchange format with `$value`/`$type`, composite types (shadows, gradients, typography
sets, transitions, borders), references that survive transforms, groups, `$description`,
`$extensions`, `$deprecated`, multi-file support, and modern color spaces. It was developed
with 20+ editors from Adobe, Google, Microsoft, Meta, Salesforce, Figma, Shopify, Sketch,
Penpot and others.

**⚠️ Precision matters here:** it is a **W3C *Community Group* specification, not a W3C
Recommendation** — stable and production-ready, but not on the Standards Track. Say
"the DTCG specification" rather than "the W3C standard" when accuracy counts.

Tooling as of 2026: **Style Dictionary v4** ships first-class DTCG support (full 2025.10
support is landing in v5); Figma Variables can export to the format; Tokens Studio,
Terrazzo, Penpot, Supernova, Knapsack and zeroheight support or are implementing it. File
convention: `.tokens` / `.tokens.json`, media type `application/design-tokens+json`.

```json
{
  "color": {
    "$type": "color",
    "blue": { "500": { "$value": "#3b82f6" }, "300": { "$value": "#93c5fd" } },
    "action": {
      "primary": {
        "$value": "{color.blue.500}",
        "$description": "Primary interactive fill. Light theme."
      }
    }
  },
  "space": {
    "$type": "dimension",
    "4": { "$value": { "value": 16, "unit": "px" } }
  }
}
```

**A token pipeline that works:**
```
Figma Variables / Tokens Studio
   → push branch → GitHub PR
      → CI: JSON-schema validate against DTCG
              lint (no orphan tokens, no missing $type, no raw hex in components,
                    contrast check on every semantic fg/bg pair)
              build via Style Dictionary → CSS custom properties, Swift, Kotlin, JSON
              visual regression on the component library
      → merge → versioned release → consumed by apps
```
**[DURABLE] The hard part was never the format.** It's governance: who can add a token, how
deprecation works, how you stop 400 one-off values from accumulating, and how you get teams
to actually adopt. The DTCG spec closed the interoperability problem; it did not close the
organizational one.

### 7.3 Component API design

Treat components as an API with a compatibility contract:
- **Props over variants-by-copy.** One Button with `variant`, `size`, `state` — not five
  Buttons.
- **Composition over configuration** for anything open-ended. A `Card` that accepts
  children beats a `Card` with 22 boolean props.
- **Accessibility is inside the component, not a documentation note.** If the Dialog
  component doesn't trap focus, restore focus, and wire `aria-modal`, every consumer will
  get it wrong.
- **Every component documents: purpose, when *not* to use it, all states, keyboard
  behaviour, a11y notes, and do/don't examples.** The "when not to use" section is the one
  people skip and the one that prevents misuse.
- Version with semver; deprecate with a documented migration and a codemod where possible.

### 7.4 Measuring adoption

A design system's only real metric is **adoption**: percentage of UI built from system
components, number of one-off/detached components, token coverage vs. hardcoded values,
time-to-ship a standard screen. Design-token adoption is now the norm rather than the
exception (an industry survey of ~300 professionals reported ~84% team adoption in 2026,
up from ~56% a year earlier) — so the differentiating question has moved from "do you use
tokens" to "is the token graph actually the single source of truth."

---

## §8. Platform Conventions

**[DURABLE] Jakob's Law applies to platforms.** Users bring expectations from every other
app on that OS. Violating them is expensive; the only good reason is that the convention is
genuinely wrong for your domain, and you should be able to say why.

### 8.1 Apple — HIG, and Liquid Glass

Core Apple principles: **clarity, deference (content over chrome), depth**. Concretely:
- Navigation is hierarchical (push/pop), flat (tabs), or content-driven.
- **44 × 44 pt** touch targets; **Dynamic Type** support; SF Symbols for iconography.
- Back navigation is top-left plus edge-swipe; there is no system Back button.
- Modality is a strong statement — use sheets for focused sub-tasks, alerts sparingly.
- macOS additionally expects a full menu bar, multiple windows, unlimited undo (§8.4).

**macOS 26 / iOS 26 introduced Liquid Glass** — a translucent, light-refracting material
across toolbars, sidebars, tab bars, sheets, popovers, controls, the Dock and menu bar.
What matters for design work:
- **Framework chrome adopts it free on recompile** against the 26 SDK, across SwiftUI,
  UIKit and AppKit. **Custom components do not** — that's where the work is.
- Opt-in APIs: `.glassEffect()`, `GlassEffectContainer`, `glassEffectID` for morphing.
- Navigation now *floats over* content, which changes safe-area assumptions.
- Icons require rework via **Icon Composer** (layered vector, blur/translucency, specular
  highlights) — the flat 1024 px PNG workflow is obsolete.
- **⚠️ Accessibility:** translucency degrades text contrast. Respect **Reduce Transparency**
  and **Increase Contrast**, and test with both on. Apple's own first-year implementation
  drew substantial legibility criticism; treat restraint as the default.

### 8.2 Google — Material 3 and M3 Expressive

Material 3 brought dynamic color (Material You), a token-based architecture, and adaptive
layouts. **Material 3 Expressive** (announced May 2025) is an *enhancement to M3, not "M4"*,
adding a physics-based motion system, an expanded type scale with emphasized styles, a shape
system with morphing, and bolder color.

**It is unusually well-evidenced for a design language.** Google reports **46 research
studies with 18,000+ participants over ~3 years**, using eye-tracking, surveys and usability
trials. Reported findings: users spotted key UI elements **up to 4× faster** than in prior
Material 3; time-to-tap on key actions decreased significantly; and — the most interesting
result — **the usability age gap largely disappeared**, with older participants spotting key
elements as quickly as younger ones.

**[CONTESTED] How much to generalize from that.** The studies are Google's own, largely
unpublished in peer-reviewed venues, and measure Google's components in Google's contexts.
The mechanism behind the headline result is not mysterious — bigger, bolder, better-placed
primary actions are easier to find, which Fitts and von Restorff already predicted. The
honest reading: **the direction is well-supported (expressiveness and usability are not
opposed, and prominence helps older users disproportionately); the specific multipliers
should not be quoted as universal.** Google's own team notes the intent isn't to make every
interaction playful — "you might not want a super-playful UI for paying a parking ticket."

Android specifics that trip up iOS-first designers: the **system Back** (gesture or button)
with defined semantics, the **app bar** rather than a centered title, **FAB** for a single
primary action, **48 dp** targets, and Material's own navigation components (nav bar, nav
rail for tablets, nav drawer).

### 8.3 Web

The web has no HIG — it has conventions, and breaking them is more costly than on any
native platform because users arrive with expectations from the entire internet:
- Logo top-left links home. Nav in the header. Search where search goes.
- **Links look like links** (underline or unambiguous styling) and behave like links
  (middle-click, right-click, ⌘-click all work — which requires a real `<a href>`, not a
  `<div onClick>`).
- Browser **Back must work**, including in SPAs.
- Forms submit on Enter. Autofill works (correct `autocomplete` attributes — this is both
  a conversion and an accessibility feature).
- **Never disable zoom** (`user-scalable=no` / `maximum-scale=1`) — WCAG failure and a
  hostile act toward low-vision users.
- Respect `prefers-color-scheme`, `prefers-reduced-motion`, `prefers-contrast`.

### 8.4 Desktop (macOS / Windows / GNOME / KDE)

- **Menu bar as complete command index.** Every command should appear in a menu even if
  it's also a toolbar button — that's how Help search, keyboard discovery, and accessibility
  find it.
- **Unlimited, coalescing undo.** Typing 30 characters is one undo step.
- **Multi-window and window-state restoration** are baseline expectations, not features.
- **Keyboard-first** operation; show shortcuts in menus.
- **Density is higher and users want it.** Desktop is where power users live.
- **[PLATFORM] Linux is not one convention.** GNOME's HIG favours header bars with a
  hamburger and no menu bar; KDE retains traditional menu bars and far more configurability.
  Pick per your target desktop and be internally consistent; use libadwaita/KDE components
  and you inherit the right answer.

### 8.5 Cross-platform: consistency vs. nativeness

**[CONTESTED]** Brand-consistent-everywhere (Flutter, a strong web design system) versus
native-idiomatic-per-platform (SwiftUI + Material + platform toolkit).
- *For consistency*: one design, one implementation, one QA surface; users recognize your
  product across devices; cheaper by a large factor.
- *For nativeness*: users' expectations are set by the platform, not by you; native
  components carry accessibility, localization, dark mode, dynamic type, and platform
  updates **for free**; the uncanny-valley cost of "almost native" is real and is felt as
  low quality.
- **The defensible split:** be brand-consistent in *identity* (color, type, tone, iconography,
  illustration) and platform-native in *interaction* (navigation model, gestures, controls,
  system integration). Users forgive different-looking; they don't forgive different-behaving.

---

## §9. Accessibility

### 9.1 The frame

**[DURABLE] Accessibility is not a feature for a minority.** Roughly 1.3 billion people
live with significant disability; add situational (bright sun, one hand full, noisy room)
and temporary (broken arm, eye dilation) impairments and the addressable population is
everyone. It is also now, in most of the markets a product ships to, **the law**.

**POUR** — the four WCAG principles:
- **Perceivable** — information must be presentable in ways users can perceive (alt text,
  captions, contrast, not-color-alone).
- **Operable** — all functionality via keyboard, enough time, no seizure triggers,
  navigable, adequate targets.
- **Understandable** — readable, predictable, error-preventing and error-explaining.
- **Robust** — works with assistive technologies; valid, semantic markup.

### 9.2 The standards and the law (2026)

| Regime | Standard | Status |
|---|---|---|
| **WCAG 2.2** | Current W3C Recommendation (Oct 2023, updated Dec 2024) | **Approved as ISO/IEC 40500:2025** — enabling more countries to adopt it formally |
| **WCAG 2.1 AA** | The level most laws actually cite | The de facto global legal baseline |
| **WCAG 3.0** | **Working Draft only** (updated March 2026, ~174 requirements; Bronze/Silver/Gold outcome-based scoring replacing A/AA/AAA) | **Not a legal requirement anywhere.** Candidate Recommendation anticipated ~late 2027; final Recommendation realistically 2028–2030. **Will not deprecate WCAG 2.** |
| **EU — European Accessibility Act** | EN 301 549 (currently incorporates WCAG 2.1 AA; **v4.1.1 expected 2026 will move to WCAG 2.2**) | **Enforceable since 28 June 2025** for new products/services. Applies to businesses *anywhere* selling to EU consumers. Existing services have until 28 June 2030; contracts concluded pre-June-2025 until June 2027. Microenterprise exemption (<10 employees AND <€2M turnover) applies to services, not products, and not to non-EU firms serving the EU. Enforcement is per-member-state. |
| **US — ADA Title II** | WCAG 2.1 AA, by DOJ final rule (April 2024) | ⚠️ **Deadlines extended by one year on 20 April 2026** via Interim Final Rule: entities serving **50,000+ → 26 April 2027**; under 50,000 and special districts → **26 April 2028**. The extension changes only the date — the underlying obligation is in force now and people can sue today. |
| **US — ADA Title III** (private business) | No explicit WCAG mandate | Courts apply WCAG anyway; thousands of suits per year (4,600+ in 2025, up ~14% YoY per UsableNet). |
| **US — Section 508** | WCAG 2.0 AA (federal) | |
| **US — Section 504 / HHS** | WCAG 2.1 AA | Deadlines also extended in May 2026: ≥15 employees → 11 May 2027; <15 → 10 May 2028 |
| **UK** | Equality Act; PSBAR for public sector | WCAG 2.1/2.2 AA |

**[DURABLE, practical] Build to WCAG 2.2 AA.** It is a superset of 2.1 AA, so you exceed
every current legal requirement, you're already compliant when EN 301 549 moves to 2.2, and
you're positioned for whatever 3.0 becomes. **Do not wait for WCAG 3.0** — Bronze is
expected to be roughly equivalent to today's 2.2 AA, so conforming now is the head start.

### 9.3 Contrast, and the APCA question

**Current requirement (WCAG 2.x, and therefore the law):** 4.5:1 body text, 3:1 large text
(≥18 pt / 14 pt bold), 3:1 for UI components and graphical objects (SC 1.4.11). The
algorithm is a relative-luminance ratio, polarity-insensitive.

**[CONTESTED — and this one has legal consequences.] APCA** (Advanced Perceptual Contrast
Algorithm) is a perceptual model producing an `Lc` value that accounts for font size,
weight, and polarity. Its proponents argue — with real evidence — that WCAG 2's math
systematically **overstates** contrast when both colors are dark (which is why WCAG-passing
dark-mode palettes can be functionally unreadable) and **understates** some light-background
pairs that are demonstrably readable.

**But:** APCA is a *candidate* method for WCAG 3, which is a Working Draft. No law anywhere
references it. And accessibility practitioners — notably Adrian Roselli, whose April 2026
analysis is the reference on this — warn that advising teams to *replace* WCAG 2 contrast
with APCA creates legal risk, and that WCAG 3's contrast approach is far from settled.

**The defensible position for 2026: conform to WCAG 2 contrast (that's what you'll be
audited against), and optionally *also* check APCA to catch the cases WCAG 2's math misses
— particularly in dark mode.** Choose colors that satisfy both. Do not present APCA
conformance as legal compliance.

Worth internalizing: contrast remains the **most common accessibility failure on the web** —
the WebAIM Million 2026 report found WCAG 2 contrast failures on **83.9% of the top million
home pages**, up from 79.1% the prior year, averaging ~34 low-contrast instances per page.
This is the cheapest defect class to fix and the one most consistently shipped.

### 9.4 The practical checklist

Beyond contrast, the failures that appear on the overwhelming majority of sites are: missing
alt text, unlabeled form inputs, empty links/buttons, and missing document language. Those
four plus contrast are ~95% of automatically-detectable issues.

- **Semantic structure** — real headings in order (no skipping levels), landmarks, lists as
  lists, tables with headers. A screen-reader user navigates by headings; a page of styled
  `<div>`s is a wall.
- **Every input has a persistent, programmatically associated `<label>`.** Placeholder text
  is not a label — it disappears on focus, fails contrast, and breaks autofill and
  translation.
- **Alt text**: describe *purpose*, not appearance. Decorative images get `alt=""`.
  Complex images (charts) need a longer description elsewhere.
- **Focus management**: on route change, on modal open/close, on dynamic content insertion.
  Announce with a live region when appropriate; don't overuse `aria-live="assertive"`.
- **ARIA rule zero: no ARIA is better than bad ARIA.** Use a native `<button>` before you
  build `role="button"` with keyboard handlers.
- **Captions and transcripts** for media; audio description where visual info is essential.
- **Don't rely on hover or precise timing.**
- **Support 200% zoom and 320 px reflow** without horizontal scrolling (SC 1.4.10).

### 9.5 Testing

- **Automated tools (axe, Lighthouse, WAVE, Pa11y) catch roughly a third of issues.** They
  are necessary and radically insufficient. Run them in CI as a floor.
- **Manual keyboard pass**: unplug the mouse, do every task.
- **Screen reader pass**: VoiceOver (macOS/iOS), NVDA or JAWS (Windows), TalkBack (Android),
  Orca (Linux). Test with at least one; behaviours differ meaningfully.
- **Zoom to 200% and 400%**; test with OS-level larger text.
- **Test with users with disabilities.** This is the only method that finds the issues the
  other four can't.
- **⚠️ Accessibility overlay widgets** (one-line JavaScript "compliance" products) have
  repeatedly failed to provide a defense in litigation and drew FTC action; they are widely
  opposed by the accessibility community and by screen-reader users. They are not a
  remediation strategy.
