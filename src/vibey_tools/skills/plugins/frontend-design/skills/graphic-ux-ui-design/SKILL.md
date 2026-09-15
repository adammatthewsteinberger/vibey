---
name: graphic-ux-ui-design
description: "Comprehensive UX/UI and graphic design reference covering visual design fundamentals (color systems, typography, dark mode, layout), component and interaction patterns (navigation, forms, buttons, modals, loading states), accessibility standards (WCAG 2.2, APCA, screen readers), UX research methods, and design systems (token architecture, Atomic Design, governance, versioning). Use when designing interfaces, auditing accessibility, building or evaluating design systems, choosing component patterns, or applying evidence-based UX decisions."
---

# Graphic UX/UI Design: Practitioner's Reference

## Evidence Summary

Most "best practices" are context rules. The strongest, most replicated findings (top-aligned labels, 50–75ch line length, dark-grey dark mode, skeleton screens for content loading, "Load More" over infinite scroll for goal-driven tasks, semantic HTML before ARIA) hold across platforms. Density, motion, and navigation choices depend on whether you serve consumers or power users. Accessibility is the single biggest gap between rhetoric and reality: WebAIM's 2026 scan found 83.9% of top 1M home pages have low-contrast text (up from 79.1% in 2025), 56.1 errors/page. The fixes are trivial and known — they simply aren't implemented.

---

## Visual Design Fundamentals

### Color Systems

Production color architecture uses three token tiers:
- **Primitive tokens**: raw values — `blue-500: #3B82F6`
- **Semantic tokens**: intent — `color-action-primary`, `color-text-primary`, `color-status-error`
- **Component tokens**: scoped — `button-bg-primary`

Applications consume semantic tokens, not primitives. Theming and dark mode become a matter of re-pointing semantic tokens, not editing components. Neutral scales (9–12 steps) carry most of the surface area.

### WCAG Contrast Requirements

| Level | Normal text | Large text (≥24px or 18.7px bold) | Non-text UI |
|-------|-------------|-----------------------------------|-------------|
| AA    | 4.5:1       | 3:1                               | 3:1         |
| AAA   | 7:1         | 4.5:1                             | —           |

Global regulations (Section 508, EN 301 549, AODA) target AA. AAA is aspirational and not always achievable. Low-contrast text is the #1 accessibility defect for seven straight years. **Do not wait for WCAG 3/APCA to be final** — keep conforming to WCAG 2.x AA for compliance; use APCA as a supplementary check (especially for dark themes); never claim "WCAG 3 compliance" (it doesn't exist yet as of 2026).

### Oklch and Wide-Gamut Color

CSS Color Level 4 (`oklch()`, `oklab()`, `color(display-p3)`) is Baseline Widely Available (Chrome/Edge 111+, Firefox 113+, Safari 15.4+).

Why oklch matters:
1. **Perceptual uniformity** — a fixed change in L looks equally different across hues; HSL does not have this property. Use it to generate consistent tint/shade scales programmatically.
2. **Wide gamut** — Display P3 covers ~50% more colors than sRGB. Every iPhone since 7, every MacBook since 2016 supports it.

Always declare sRGB hex fallbacks first for old browsers.

### Dark Mode

**Never use pure black (#000000).** Material Design recommends #121212 as the base dark surface — pure black causes halation/blooming and disables shadows.

Express elevation through lightness, not shadow:

| Layer       | Approximate L% |
|-------------|----------------|
| Base        | 10–12%         |
| Sidebars    | 14–16%         |
| Cards       | 17–20%         |
| Modals      | 22–26%         |
| Popovers    | 26–30%         |

Keep ~3–5 points between each level. Desaturate accent colors (they vibrate against dark surfaces). Use off-white (~#E1E1E1 or white at 87% opacity) rather than pure white text. A naive light-palette inversion fails — light and dark modes have asymmetric perceptual requirements. Always let users toggle; don't force it.

### Typography

| Guideline             | Value                     |
|-----------------------|---------------------------|
| Optimal line length   | 50–75 characters (66ch sweet spot) |
| WCAG line length cap  | 80 characters (40 for CJK) |
| CSS implementation    | `max-width: 66ch`         |
| Line height (body)    | ~1.5                      |
| Fluid type            | `clamp()` to preserve ch range across viewports |

Hierarchy priority: size → weight → color → spacing. Adding typefaces is the classic mistake. Variable fonts are worth the complexity only when shipping multiple weights/widths.

**Web font loading**: `font-display: swap` (or `optional` for CLS-sensitive cases), `<link rel="preload">` for the critical font, `size-adjust`/`ascent-override` on fallback `@font-face` to minimize layout shift.

### Layout and Grid

- **8pt grid** with a 4pt sub-grid is the de facto spacing system
- **12-column grids** dominate web layout
- Use **CSS Grid** for two-dimensional layout; **Flexbox** for one-dimensional component distribution
- The F-pattern (NN/g, 2006, confirmed 2017) is a symptom of poor formatting, not a goal. Good headings, bolding, and front-loaded content replace F-scanning with more thorough "layer-cake" scanning
- Users read at most 28% of words on a page on average (Nielsen, 2008, ~50,000 page views); 20% is more likely
- Gestalt principles (proximity, similarity, continuity, closure, figure-ground) are the most practically useful perceptual framework

**Content density is a genuine fork:**
- Dense UIs: correct for pro tools, dashboards, IDEs, analytics (information-per-screen, expert efficiency)
- Airy UIs: correct for consumer onboarding and marketing (reduce cognitive load, guide one action)

---

## Component and Interaction Patterns

### Navigation

| Pattern    | When to use                                                  |
|------------|--------------------------------------------------------------|
| Top nav    | Marketing sites, shallow IA                                  |
| Side nav   | Deep app-like hierarchies (SaaS, admin)                      |
| Bottom nav | Mobile top-level (3–5 destinations, thumb zone)              |
| Mega menus | Broad e-commerce/content taxonomies                          |

**The "≤7 menu items" rule is a myth** — a misapplication of Miller's Law. Breadth often beats depth; it reduces clicks and keeps users oriented.

### Forms

**Top-aligned labels are the most usable and accessible default.** Advantages over left-aligned:
- Eye travels in one direction (down only)
- Label/field sit close together — ~50ms to move from label to field vs ~500ms for left-aligned (Penzo, 2006 eye-tracking — treat as directional; the accessibility and localization advantages are the more durable case)
- Better on mobile (left-aligned labels truncate the input)

Rules:
- **Never use placeholder text as a label** — it disappears on input, fails contrast, and is unreliable for screen readers
- Floating labels: fashionable but measurably worse for accessibility and motion sensitivity
- Validate inline **after a field is completed**, not on every keystroke
- Keep the submit button enabled; write recovery-oriented error messages
- Break long forms into logical steps

### Buttons and CTAs

Hierarchy: primary → secondary → tertiary/ghost → destructive (visually distinct).

All interactive states must be visually distinct: hover, focus, active, disabled, loading.

**Touch target sizes:**

| Standard     | Minimum          |
|--------------|------------------|
| Apple HIG    | 44×44 pt         |
| Material     | 48×48 dp (~9mm)  |
| WCAG 2.2 AA  | 24×24 CSS px     |
| WCAG 2.5.5 AAA | 44×44 CSS px   |
| visionOS     | 60 pt (gaze-based) |

Aim for the larger platform values.

### Modals and Dialogs

Use for focused, must-complete decisions. Harmful when overused for non-blocking info. Drawers/sheets are better for secondary content and on mobile.

Required for every modal:
- Focus trap
- Restore focus on close
- Support Escape key
- Proper `aria-labelledby`/`aria-describedby`

Inaccessible modals are a top accessibility failure.

### Loading States

| State type       | Best pattern                                      |
|------------------|---------------------------------------------------|
| Content loading  | Skeleton screens (generally reduce perceived wait) |
| Short discrete actions | Spinner                                    |
| No state at all  | Never — worst possible option                     |

Caveat: A 2017 Viget study found skeletons performed *worst* on perceived duration in some conditions. The rule is: show structure for content loading, use a spinner for short discrete actions.

### Lists: Infinite Scroll vs. Pagination vs. Load More

Based on Baymard's multi-year, 50+ site studies:

| Pattern         | Best for                                                  |
|-----------------|-----------------------------------------------------------|
| Load More + lazy-loading | Default; superior for most product lists       |
| Pagination      | Goal-driven look-up, bookmarking, SEO                     |
| Infinite scroll | Exploratory/inspirational feeds (Pinterest, image galleries) |

Infinite scroll "can be downright harmful" for goal-driven search — users lose their place, can't bookmark/compare, the footer becomes unreachable.

### Tables and Data Grids

Provide: sorting, filtering, sticky headers, pagination or "load more." Responsive patterns: horizontal scroll with frozen first column, or card stacking on mobile.

### Notifications

| Type       | Use for                                      | Behavior           |
|------------|----------------------------------------------|--------------------|
| Toast/snackbar | Transient confirmations                  | Auto-dismiss       |
| Banner     | Persistent page-level status                 | Stays until dismissed |
| Inline     | Contextual/field errors                      | Adjacent to source |

Never put critical, action-required info in an auto-dismissing toast.

### Motion and Microinteractions

Dan Saffer's model: trigger → rules → feedback → loops/modes.

Disney timing principles:
- Ease-out for entrances
- Ease-in for exits
- UI transitions: ~150–300ms
- Motion should communicate (state change, spatial relationship, progress), not decorate

**Always honor `prefers-reduced-motion`** — disable or reduce non-essential animation for vestibular safety.

WCAG 2.2 SC 2.5.7: drag interactions must have a single-pointer (non-drag) alternative.

---

## Accessibility and Inclusive Design

### State of the Web (WebAIM Million)

| Year | Pages with WCAG failures | Low-contrast text | Errors/page |
|------|--------------------------|-------------------|-------------|
| 2025 | 94.8%                    | 79.1%             | 51.0        |
| 2026 | (implied regression)     | 83.9%             | 56.1        |

The six issue types accounting for 96% of all errors:
1. Low-contrast text (83.9% of pages)
2. Missing alt text (55.5% of pages; ~18.5% of images)
3. Missing form labels (48.2% of pages)
4. Empty links (45.4%)
5. Empty buttons
6. Missing document language

### WCAG 2.2 Key Additions (Oct 2023)

AA-level additions designers must know:
- **2.4.11 Focus Not Obscured (Minimum)**: sticky headers/footers can't fully hide a focused element
- **2.5.7 Dragging Movements**: drag must have a single-pointer alternative
- **2.5.8 Target Size (Minimum)**: 24×24 CSS px or adequate spacing
- **3.3.8 Accessible Authentication**: no cognitive-function test without an alternative
- **3.2.6 Consistent Help** (Level A)
- **3.3.7 Redundant Entry** (Level A)

Note: 4.1.1 Parsing was removed in WCAG 2.2.

### Semantic HTML and ARIA

**Use native HTML elements first.** They carry built-in roles, keyboard handling, and focus management.

"No ARIA is better than bad ARIA": pages *with* ARIA averaged ~34–41% *more* detected errors than pages without (WebAIM). ARIA adds semantics but never behavior — a `div role="button"` still requires manual keyboard handlers. Reserve ARIA for genuinely custom widgets (tabs, comboboxes, live regions).

### Keyboard and Screen Reader Testing

Provide: logical tab order, visible focus indicators, skip links, managed focus in SPAs (move focus on route change, trap in modals, restore on close).

Test with multiple screen readers — they differ in behavior:
- VoiceOver (macOS/iOS, Safari)
- NVDA (Windows, Firefox/Chrome)
- JAWS (Windows, Firefox/Chrome)

Automated tools (axe, Lighthouse, WAVE) catch only **30–40% of issues**. Manual keyboard + screen-reader testing is mandatory.

### Color-Vision Deficiency

~8% of men have a color-vision deficiency. Never rely on color alone — add icons, labels, patterns (WCAG SC 1.4.1 Use of Color).

### Inclusive vs. Accessible Design

- **Accessibility** = meeting the needs of people with disabilities (standards/compliance)
- **Inclusive design** = methodology of designing for the full range of human diversity (ability, language, context, device, situational constraints) from the start

Compliance can be met while still excluding people. Inclusive design treats accessibility as one outcome of a broader commitment.

---

## UX Research Methods

### Method Selection by Question Type

| Phase      | Methods                                                       |
|------------|---------------------------------------------------------------|
| Generative/Discovery | User interviews, contextual inquiry, diary studies, JTBD |
| Evaluative  | Usability testing (moderated/unmoderated), tree testing      |
| IA          | Card sorting (open/closed/hybrid), tree testing              |
| Behavioral at scale | Analytics, heatmaps, session recordings (Hotjar, FullStory) |
| Quantitative UX | SUS, SUPR-Q, NPS                                        |

A/B testing works for high-traffic, isolatable changes with proper statistical significance. Misused for low-traffic pages or as a substitute for qualitative "why."

### Usability Benchmarks

**SUS (System Usability Scale):**
- Mean score across 446 studies: **68** (SD: 12.5) — this is the "C" / 50th percentile
- ≥80.3: "A" grade (top ~10–15%)
- <51: bottom ~15%
- SUS is not a percentage

**Cognitive laws (useful heuristics, not physics):**
- **Hick's Law**: decision time grows logarithmically with number/complexity of choices → argues for progressive disclosure and chunking, not blanket minimalism
- **Fitts's Law**: acquisition time depends on target size and distance → make primary targets big and close; make destructive actions small and far
- **Miller's Law ("7±2")**: frequently misused to justify arbitrary 7-item limits; the real lesson is chunking and recognition-over-recall, not capping menus at 7

**Nielsen's 10 Heuristics** — most commonly violated in practice:
1. Visibility of system status
2. Error prevention
3. User control and freedom (undo/escape)
4. Match between system and real world

### Information Architecture

- Card sorting + tree testing + sitemapping
- Generally favor breadth over depth for findability
- Design for both search AND browse
- Faceted navigation + a sound taxonomy is the backbone of e-commerce and large content sites

---

## Design Systems

### What a Design System Is

"A design system is a living, funded product with a roadmap & backlog, serving an ecosystem." (Nathan Curtis)

Components:
- Component library (coded components)
- Pattern library (documented solutions)
- Tokens (the shared contract)
- Guidelines + governance + people

### Three-Tier Token Architecture

```
Primitives      →   Semantic/Alias     →   Component
blue-500: #3B82F6   color-action-primary   button-bg-primary
                    color-text-primary
```

- Applications consume **semantic** tokens, not primitives
- Semantic names encode intent, not value: `color-text-primary`, not `color-blue-500`
- Small teams can use two tiers (primitive + semantic)
- Enterprise/multi-brand/multi-theme needs all three
- More than three tiers is rarely justified
- This architecture is what makes multi-mode theming (light/dark, density, brand) a matter of re-pointing tokens

### Tooling Pipeline

| Tool             | Role                                             |
|------------------|--------------------------------------------------|
| Style Dictionary | Transform design tokens into platform code      |
| Tokens Studio    | Figma-based token management                    |
| W3C DTCG format  | Standardizing JSON (`$value`/`$type`)           |
| Figma Variables  | Primitives, semantic tokens, multi-mode collections |
| Storybook        | Code-first component documentation              |
| Zeroheight / Supernova | Design-first documentation                |

### Atomic Design: What Holds and What Doesn't

Atoms → Molecules → Organisms → Templates → Pages (Brad Frost, 2013).

**What holds:** Systems-thinking, shared vocabulary that "UIs are interconnected hierarchical systems," templates/pages for testing real content.

**What's outdated:** The atom/molecule/organism taxonomy is "too fuzzy" and abstracts too early. Practitioners now recommend starting with a flat component hierarchy and letting structure emerge. Frost himself has moved "subatomic" — toward design tokens as the smallest unit.

### Governance Models (Nathan Curtis / EightShapes)

| Model       | Description                                                |
|-------------|------------------------------------------------------------|
| Solitary    | One team builds for its own needs ("Overlords don't scale") |
| Centralized | Dedicated team makes and spreads decisions for other teams |
| Federated   | Designers from multiple product teams decide together      |
| Cyclical    | Centralized team + federated contributor community (Jina Anne/Salesforce) |

Curtis's contribution principle: "central system team members can't make all the decisions… a system practice must model and foster a federated community."

Relevance heuristic for what belongs in the system: useful to 3 products → discuss; useful to 5 → it probably belongs.

### Versioning (SemVer)

"Every discussion about versioning design system outputs begins and ends with SemVer." (Curtis)

- **MAJOR**: breaking changes
- **MINOR**: backwards-compatible features
- **PATCH**: backwards-compatible fixes

**Library-level vs. component-level versioning:**
- Library-level: one version across all assets — common for vanilla HTML/CSS
- Component-level: mix-and-match (e.g., Atlaskit Badge v15.0.8) — suited to React/continuous-release

Package tokens as a separate dependency so style can evolve independently of component APIs.

### Adoption Measurement

Distinguish:
- **Usage** (breadth): which components, how often
- **Coverage** (depth): how much of the UI is built from the system

Tools:
- Figma Library Analytics: insertions, total instances, detaches
- `react-scanner` for static component-instance analysis from code
- Omlet, Preply's visual-coverage tool

Track detach rate as a diagnostic — a rising detach rate signals a bug, missing variant, or unmet need, and should trigger investigation, not enforcement.

### Deprecation Process

Atlassian's 6-step process: communicate intent → set a timeline → add docs notice → run deprecation commands → communicate again → delete.

Timeline guidance by audience:
- Salesforce: 18 months
- Financial Times Origami: 3–6 months (tight developer community)

Run enhanced + deprecated in parallel before removal in the next major version.

---

## AI Design Tools: Honest Assessment

| Tool            | Strengths                                              | Weaknesses                                  |
|-----------------|--------------------------------------------------------|---------------------------------------------|
| v0 (Vercel)     | React + Tailwind + shadcn/ui generation; best for dev iteration | Generic output without customization |
| Figma Make      | Multi-screen prototypes, rapid concept exploration     | Variable credits; can't iterate after manual edits |
| Stitch (ex-Galileo, Google Labs) | High-fidelity mockups, Figma export    | Labs-only, no SLA, weak for production work |

Consistent verdict across reviewers: get you "80% of the way there," require human judgment for UX quality, **frequently fail accessibility audits by default** (always verify contrast manually). Treat as accelerators, not replacements. Tool volatility is high — don't over-commit to any single one.

---

## Anti-Patterns and Dark Patterns

- **Dark patterns** are now actively regulated. FTC's 2024 review of 642 subscription sites found 76% used at least one dark pattern; the EU Digital Services Act (fully effective Feb 2024) and CCPA/CPRA prohibit dark patterns for consent. The FTC finalized its Click-to-Cancel/Negative Option Rule in October 2024.
- Over-designing: gold-plating where simplicity serves better
- Building a design system prematurely (before products exist to serve)
- Confirmation bias in design critique

---

## Staged Recommendations

**Stage 1 — Fix cheap, high-impact accessibility failures (weeks 1–4):**
Run axe/Lighthouse/WAVE; manually fix the six WebAIM categories: contrast (4.5:1 / 3:1 AA), alt text, form labels, empty links/buttons, document language. Add visible focus styles and skip links. Verify keyboard operability of every interactive element.

**Stage 2 — Standardize foundations as tokens (months 2–3):**
Establish three-tier token system; implement dark mode via semantic re-pointing (no pure black, elevation by lightness); set `max-width: 66ch` and `line-height: 1.5` on body; adopt 8pt grid; define button hierarchy + states + touch targets (≥44pt/48dp). Move to `oklch()` with sRGB fallbacks.

**Stage 3 — Apply pattern evidence to your context (ongoing):**
Top-aligned labels; inline-after-completion validation; skeletons for content loading, spinners for short actions; Load More/pagination for goal-driven lists, infinite scroll only for exploratory feeds; honor `prefers-reduced-motion`. Decide density deliberately (dense for pro tools, airy for consumer/onboarding).

**Stage 4 — Operationalize the design system (quarter 2+):**
Adopt SemVer; pick a governance model (centralized to start, federate as contributors mature); define a deprecation process with an explicit window; measure adoption (coverage + usage).

**Stage 5 — Pilot AI tooling without betting the system on it:**
Use for rapid prototyping and concept exploration; require a human accessibility/contrast pass before anything ships; re-evaluate tool choice quarterly.
