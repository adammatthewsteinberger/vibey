---
name: ui-ux-reference
description: "Use when reviewing an interface for known anti-patterns, weighing contested questions (minimalism vs signifiers, expressive vs neutral design, consistency vs platform nativeness, APCA vs WCAG 2 contrast, chat vs GUI for AI features, hamburger menus, disabled submit buttons, A/B testing vs qualitative research, design-system centralization, whether UX = UI still holds), checking whether a platform or regulatory claim is still current (snapshot verified August 2026), finding the books, primary sources, and ongoing sources, or needing the numbers, design review checklist, and 'this feels wrong but I can't say why' diagnosis. Companion to the other ui-ux-design-principles skills."
---

# UI/UX Design: Anti-Patterns, Contested Questions, Currency, and Canon

> **Part 5 of 5** of the *UI/UX Design Principles — Mobile, Tablet, Web, Desktop* reference (plugin `ui-ux-design-principles`), covering §15–§20. Sibling skills: `ui-ux-cognition-heuristics-and-navigation` (§0–§3), `ui-ux-interaction-layout-and-visual-design` (§4–§6), `ui-ux-design-systems-platforms-and-accessibility` (§7–§9), `ui-ux-writing-forms-research-and-ethics` (§10–§14). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Verified August 2026. See §17 below for the currency snapshot and what goes stale first.
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

## §15. Anti-Patterns

| Anti-pattern | Why it fails | Do instead |
|---|---|---|
| Placeholder text as the label | Disappears on focus, fails contrast, breaks autofill and translation, invisible to some AT | Persistent label above the field |
| Two primary buttons | Von Restorff: two emphases = none | One primary, rest secondary/tertiary |
| Icon-only controls without labels | Icons aren't universal; tooltips don't exist on touch | Icon + label, or label at minimum |
| Removing focus outlines | WCAG Level A failure; breaks keyboard use | `:focus-visible` with a designed indicator |
| Disabling zoom (`user-scalable=no`) | Hostile to low-vision users; WCAG failure | Never do this |
| Fixed pixel font sizes / ignoring OS text scale | Breaks for everyone over ~45 | Relative units; test at 200% |
| Color as the only signal | Fails ~8% of men and every grayscale/low-vision case | Color + icon + text |
| Confirmation dialogs everywhere | Habituation makes them useless | Undo (§2.3 → `ui-ux-cognition-heuristics-and-navigation`) |
| Hamburger for primary navigation | Measurably reduces discovery of hidden items | Tab bar for the top 3–5 |
| Modal for anything non-blocking | Interrupts, traps, and stacks | Inline, sheet, or side panel |
| Infinite scroll where users need to find and return | Destroys position memory; breaks the footer | Pagination or "load more" |
| Carousels for important content | Very low engagement past slide 1; auto-advance is an a11y failure | Show the content |
| Auto-playing audio/video | Universally hated; a11y violation | User-initiated |
| Hijacking scroll, Back, or system gestures | Breaks the trust users place in platform behaviour | Don't |
| Equal spacing above and below labels | Proximity ambiguity — the classic form bug | Tighter within groups than between |
| Centered long body text | Ragged left edge slows reading | Left-align |
| Full-width text on wide screens | Exceeds 75-character measure | max-width or multi-column |
| Skeleton/spinner with no context | Doesn't reduce anxiety, just delays it | Say what's loading; show progress |
| "Something went wrong" | Unactionable | What/why/what next (§10.2 → `ui-ux-writing-forms-research-and-ethics`) |
| Testing only the happy path | Real pain lives in errors and second sessions | Test failure and recovery |
| Designing only at 1440 px in Figma | Never sees the 375 px reality | Design mobile-first; open the small frame |
| Hiding content on mobile with `display:none` | Mobile users are not second-class | Reorganize, don't delete |
| Optimizing engagement metrics alone | Rewards confusion and manipulation | Pair with quality metrics (§12.4 → `ui-ux-writing-forms-research-and-ethics`) |
| Adding a preference for every disagreement | Pushes design decisions onto users | Choose a good default |
| Accessibility overlay widget | Doesn't work; no legal protection; opposed by AT users | Fix the underlying markup |
| Shipping WCAG 2.0 in 2026 | Below every current legal baseline | Build to 2.2 AA (§9.2 → `ui-ux-design-systems-platforms-and-accessibility`) |
| Quoting "5 users is enough" as universal | Misreads the finding (§12.2 → `ui-ux-writing-forms-research-and-ethics`) | 5 per segment per round, 3 rounds |
| Quoting "7±2" as a menu-length rule | Miller said no such thing (§1.2 → `ui-ux-cognition-heuristics-and-navigation`) | Categorize; don't make people recall |

---

## §16. Contested Questions

**16.1 Minimalism vs. signifiers.** Flat/minimal design demonstrably improved consistency
and scalability and reduced visual noise; it also removed the cues that tell people what's
clickable, with a documented cost concentrated in older and less experienced users. Neither
"add bevels back" nor "clean is always better" is right. The resolution is *deliberate
signification*: keep the aesthetic, but ensure every interactive element is identifiable
without hover, and test that assumption with real users rather than with your team.

**16.2 Expressive vs. neutral design.** Material 3 Expressive's research argues emotional
expressiveness and usability are complementary — bolder shapes and bigger primary actions
made key elements ~4× faster to spot and closed the usability age gap. The counterweight:
these are vendor studies of vendor components, the mechanism is mostly "prominence helps"
(which we already knew), and expressiveness is genuinely wrong for some contexts — Google's
own team notes you may not want a playful UI for paying a parking ticket. Direction:
well-supported. Specific numbers: don't generalize.

**16.3 Consistency vs. platform nativeness.** §8.5 → `ui-ux-design-systems-platforms-and-accessibility`.

**16.4 APCA vs. WCAG 2 contrast.** §9.3 → `ui-ux-design-systems-platforms-and-accessibility`. This one has legal consequences, so precision
matters more than usual.

**16.5 Chat vs. GUI for AI features.** §14.1 → `ui-ux-writing-forms-research-and-ethics`.

**16.6 Hamburger menus.** §3.2 → `ui-ux-cognition-heuristics-and-navigation`.

**16.7 Disabled submit buttons.** §4.6 → `ui-ux-interaction-layout-and-visual-design`.

**16.8 A/B testing vs. qualitative research.** A/B tests answer "which is better" with
statistical rigour but cannot tell you *why*, cannot evaluate options you didn't build, and
systematically favour short-term engagement over long-term value (the classic failure: the
variant that wins on click-through erodes trust over months). Qualitative research explains
mechanism and generates options but can't quantify effect. **They answer different questions
and neither substitutes for the other.** Teams that use only A/B testing optimize into local
maxima; teams that use only qualitative research ship confident guesses.

**16.9 Design system centralization.** A single central team produces consistency and
quality but becomes a bottleneck and drifts from product reality; a federated model produces
adoption and relevance but drifts toward inconsistency. Most mature organizations end up
with a small core team owning foundations plus a contribution model with review — and the
governance, not the model, is what determines whether it works.

**16.10 Does "UX = UI" still hold?** NN/g's 2026 position is that UI is becoming less of a
differentiator as design systems standardize components and AI mediation sits above the
interface. The counterargument is that this has been predicted before, that most software
in the world is still mediocre at basic interface craft, and that declaring UI solved while
83.9% of top sites fail color contrast is premature. Both can be true: the *ceiling* on
UI differentiation may be falling while the *floor* remains unmet.

---

## §17. Currency Snapshot — verified August 2026

| Thing | Status as of Aug 2026 | Decay risk |
|---|---|---|
| **WCAG 2.2** | Current W3C Recommendation (Oct 2023; updated Dec 2024). **Approved as ISO/IEC 40500:2025**; the Dec-2024 text expected as ISO/IEC 40500:2026 by late 2026 | Low |
| **WCAG 3.0** | **Working Draft only.** March 2026 draft with ~174 requirements; Bronze/Silver/Gold outcome-based conformance. Candidate Rec ~Q4 2027; final Rec realistically **2028–2030**. **Not legally required anywhere.** Will not deprecate WCAG 2 | Medium |
| **EU Accessibility Act** | **Enforceable since 28 June 2025**. EN 301 549 currently → WCAG 2.1 AA; **v4.1.1 expected 2026 → WCAG 2.2**. Existing services to 28 June 2030; pre-June-2025 contracts to June 2027. Enforcement intensifying per-member-state (Dutch ACM active on e-commerce) | Medium |
| **ADA Title II** | ⚠️ **Deadlines extended one year on 20 April 2026** (Interim Final Rule): 50,000+ population → **26 April 2027**; under 50,000 and special districts → **26 April 2028**. WCAG 2.1 AA. Obligation is in force now; only the date moved. DOJ signaled possible further rulemaking; comment period closed 22 June 2026 | **High** |
| **Section 504 / HHS** | Deadlines also extended (7 May 2026): ≥15 employees → 11 May 2027; <15 → 10 May 2028 | High |
| **APCA** | Candidate contrast method for WCAG 3; available in Chrome DevTools (experimental). **Referenced by no law.** Practitioner guidance is to satisfy WCAG 2 and optionally also APCA | Medium |
| **Contrast failure rate** | WebAIM Million 2026: **83.9%** of top 1M home pages have WCAG 2 contrast failures (up from 79.1%), ~34 instances/page | Annual |
| **Core Web Vitals** | LCP ≤ **2.5 s**, INP ≤ **200 ms**, CLS ≤ **0.1**, at the 75th percentile of real Chrome users over 28 days. **INP replaced FID in March 2024.** ~43% of sites fail INP — the most commonly failed metric | Medium |
| **Container queries** | **Baseline Widely Available since August 2025** (~93% support). Now the default tool for component-level responsiveness | Low |
| **Design Tokens (DTCG)** | **First stable spec, v2025.10, published 28 Oct 2025.** A W3C **Community Group** spec, *not* a Recommendation. Style Dictionary v4 has first-class support (full 2025.10 in v5); Figma Variables export; Penpot, Tokens Studio, Terrazzo, Supernova, zeroheight adopting. Token adoption ~84% of teams (zeroheight survey, ~300 respondents) | Low |
| **Material 3 Expressive** | Announced May 2025 as an enhancement to M3 (**not "M4"**). 46 studies / 18,000+ participants; reported up to **4× faster** identification of key UI elements and closure of the usability age gap. Rolling across Google's app ecosystem | Medium |
| **Apple Liquid Glass** | Introduced in macOS 26 / iOS 26 (Sept 2025). Free on recompile for framework chrome; custom components need work; Icon Composer required for icons. Ongoing legibility criticism | Medium |
| **Dark-pattern regulation** | DSA Art. 25 and DMA in force; EDPB Guidelines 03/2022 (six categories); CRD financial-services dark-pattern ban **applicable 19 June 2026**; **Digital Fairness Act proposal expected late 2026** (not law). FTC actively enforcing, naming individual executives | **High** |
| **Enforcement scale** | FTC 2024 study: 76% of 642 sites/apps used ≥1 possible deceptive pattern. EU 2022 study: 97%. Fines: Amazon $2.5B (FTC) and €746M (EU), Epic $245M, TikTok €345M, Google €150M, Microsoft €60M | Medium |
| **Cart abandonment** | Baymard meta-analysis (50 studies, updated Sept 2025): **70.22%**; ~35.26% conversion uplift available from checkout design (upper bound, not a promise); ~23.5 form elements typical vs 12–14 achievable | Low |
| **Design tooling** | Figma **Config 2026** (June 23–25): code layers, design agents, MCP server, generative plugins. State of the Designer 2026 (n=906): **72%** use gen-AI in workflow, **98%** increased usage YoY, **91%** report quality gains. Penpot shipped an MCP server; native DTCG tokens; open-source/self-hostable | **High** |
| **NN/g position** | State of UX 2026: UI becoming less of a differentiator; AI mediation above the interface; "outcome-oriented design" framing. 36% of surveyed designers fear AI-normalized dark patterns | Medium |

**Goes stale fastest:** legal deadlines (ADA Title II moved *this year*), design-tool
feature sets, AI-interface conventions, platform design-language versions.
**Essentially never stale:** §1 → `ui-ux-cognition-heuristics-and-navigation` (perception/cognition), §2 → `ui-ux-cognition-heuristics-and-navigation` (heuristics), §3 → `ui-ux-cognition-heuristics-and-navigation` (IA), §4.1 → `ui-ux-interaction-layout-and-visual-design`–4.2
(input physics), §5.1 → `ui-ux-interaction-layout-and-visual-design` (layout primitives), §6.1 → `ui-ux-interaction-layout-and-visual-design` (typography), §10 → `ui-ux-writing-forms-research-and-ethics` (writing), §15
(anti-patterns).

---

## §18. The Canon

### 18.1 Books

| Author | Work | Why |
|---|---|---|
| **Don Norman** | *The Design of Everyday Things* (rev. ed.) | The foundational vocabulary: affordances, signifiers, mappings, gulfs. Read first. |
| **Steve Krug** | *Don't Make Me Think, Revisited*; *Rocket Surgery Made Easy* | The best short book on web usability, and the best case for cheap, frequent testing |
| **Jeff Johnson** | *Designing with the Mind in Mind* | The cognitive-psychology basis for UI rules — the "why" behind §1 → `ui-ux-cognition-heuristics-and-navigation` |
| **Alan Cooper et al.** | *About Face: The Essentials of Interaction Design* | Interaction design canon; goal-directed design, personas, the "elastic user" |
| **Ellen Lupton** | *Thinking with Type* | The standard typography reference |
| **Robert Bringhurst** | *The Elements of Typographic Style* | The deeper one |
| **Edward Tufte** | *The Visual Display of Quantitative Information*; *Envisioning Information* | Data display; data-ink ratio; chartjunk |
| **Rosenfeld, Morville & Arango** | *Information Architecture* ("the polar bear book") | The IA reference (§3 → `ui-ux-cognition-heuristics-and-navigation`) |
| **Bill Buxton** | *Sketching User Experiences* | Why sketching and breadth-first exploration beat premature fidelity |
| **Jenifer Tidwell et al.** | *Designing Interfaces* | The pattern catalogue |
| **Luke Wroblewski** | *Web Form Design*; *Mobile First* | Still the reference on forms (§11 → `ui-ux-writing-forms-research-and-ethics`) and the origin of mobile-first |
| **Kim Goodwin** | *Designing for the Digital Age* | The most complete end-to-end process book |
| **Erika Hall** | *Just Enough Research*; *Conversational Design* | Research pragmatism; and the best sober treatment of conversational UI |
| **Torrey Podmajersky** | *Strategic Writing for UX* | UX writing (§10 → `ui-ux-writing-forms-research-and-ethics`) |
| **Alla Kholmatova** | *Design Systems* | Design systems as culture, not component libraries |
| **Sarah Wachter-Boettcher** | *Technically Wrong*; *Design for Real Life* (w/ Meyer) | Stress cases, edge cases, and design harm |
| **Harry Brignull** | *Deceptive Patterns* | By the person who coined "dark patterns" (§13 → `ui-ux-writing-forms-research-and-ethics`) |
| **Laura Kalbag** | *Accessibility for Everyone* | Accessible entry point to §9 → `ui-ux-design-systems-platforms-and-accessibility` |
| **Heydon Pickering** | *Inclusive Components* | The best practical guide to accessible component patterns |
| **Susan Weinschenk** | *100 Things Every Designer Needs to Know About People* | Research-backed, browsable |
| **Tognazzini** | *Tog on Interface* / First Principles of Interaction Design | Where a lot of Mac interaction philosophy originates |

### 18.2 Primary sources

- **W3C / WAI** — WCAG 2.2, Understanding docs, Techniques, ARIA Authoring Practices Guide
  (APG), WCAG-EM. **Use the Understanding documents**, not blog summaries — they contain
  the intent and the exceptions.
- **Apple Human Interface Guidelines** + WWDC design sessions.
- **Material Design 3** (`m3.material.io`) + Google Design (`design.google`) — the M3
  Expressive research writeups are unusually transparent for vendor material.
- **Microsoft Fluent 2**; **GNOME HIG**; **KDE HIG**.
- **Design Tokens Community Group** (`designtokens.org`, `w3.org/community/design-tokens`).
- **web.dev** — Core Web Vitals, performance, accessibility (Google, but the CWV
  documentation is the authoritative source for the metrics).
- **MDN** — the reference for what CSS/HTML/ARIA actually does.
- **EDPB Guidelines 03/2022** on deceptive design; **FTC dark patterns staff report** (2022)
  and the 2024 sweep; **EU Digital Fairness Act** initiative pages.

### 18.3 Ongoing sources

**Nielsen Norman Group** (`nngroup.com`) — still the highest-volume source of
methodologically-grounded UX research; **Baymard Institute** — the deepest e-commerce
usability data set (paywalled, worth it if you sell things); **WebAIM** (the annual Million
report; a11y technique articles); **Adrian Roselli**, **Scott O'Hara**, **Heydon Pickering**,
**Sara Soueidan**, **TetraLogical**, **Deque** — the accessibility practitioner bench;
**Smashing Magazine**, **A List Apart**, **CSS-Tricks** (archive), **Josh Comeau** — craft;
**Interaction Design Foundation**; **Laws of UX** (`lawsofux.com`) — a good index, but check
each "law" against §1 → `ui-ux-cognition-heuristics-and-navigation` before citing it, because several are folk versions of real findings.

---

## §19. Quick Reference

### 19.1 The numbers
- Touch target: **44 pt** (Apple) / **48 dp** (Material) / **24 px** WCAG AA floor,
  **44 px** WCAG AAA. Design to 44–48.
- Body text: **≥16 px** web; measure **45–75 characters**; line-height **1.4–1.6**.
- Contrast: **4.5:1** body, **3:1** large text and UI components.
- Response: **<100 ms** instant · **<400 ms** stays in flow (Doherty) · **>1 s** show
  progress · **>10 s** allow cancel.
- Core Web Vitals: LCP **2.5 s** · INP **200 ms** · CLS **0.1**, at p75.
- Motion: **150–300 ms**, ease-out in, ease-in out.
- Working memory: ~**4** chunks (not 7).
- Usability testing: **5 per segment per round**, **3 rounds**.
- SUS: **68** average, **80+** good.
- Text expansion for localization: budget **+30–40%**.
- Checkout: **~70%** abandonment; target **12–14** form fields, not 23.

### 19.2 Design review checklist
- [ ] Is the primary action obvious, singular, and reachable (thumb zone on mobile)?
- [ ] Does spacing group correctly — tighter within, looser between? (§1.3 → `ui-ux-cognition-heuristics-and-navigation`)
- [ ] Is every interactive element identifiable *without* hover? (§2.2 → `ui-ux-cognition-heuristics-and-navigation`)
- [ ] Are all states designed: hover, focus, active, disabled, loading, error, empty, selected?
- [ ] Contrast ≥4.5:1 body / ≥3:1 UI; meaning never carried by color alone?
- [ ] Full keyboard operation with a visible focus indicator?
- [ ] Works at 200% zoom and 320 px reflow? Respects OS text size?
- [ ] Screen-reader tested — labels, headings, landmarks, focus management?
- [ ] Errors say what happened, why, and what to do next?
- [ ] Is there undo instead of a confirmation dialog? (§2.3 → `ui-ux-cognition-heuristics-and-navigation`)
- [ ] Does Back / Escape / Enter do what the platform says they do?
- [ ] Do the defaults serve the user rather than the business? (§13.4 → `ui-ux-writing-forms-research-and-ethics`)
- [ ] Does the copy use the user's words and front-load meaning?
- [ ] What happens at 0 items, 1 item, 10,000 items, and on a failed request?
- [ ] Has anyone outside the team completed the task without help?

### 19.3 "This feels wrong but I can't say why" — diagnostic
Hierarchy unclear (§6.1 → `ui-ux-interaction-layout-and-visual-design`) → grouping ambiguous (§1.3 → `ui-ux-cognition-heuristics-and-navigation`) → too many equal-weight options
(§1.2 → `ui-ux-cognition-heuristics-and-navigation`) → signifiers missing (§2.2 → `ui-ux-cognition-heuristics-and-navigation`) → inconsistent with itself or the platform (§2.1 → `ui-ux-cognition-heuristics-and-navigation` #4,
§8 → `ui-ux-design-systems-platforms-and-accessibility`) → language is the product's, not the user's (§10 → `ui-ux-writing-forms-research-and-ethics`) → state is hidden so the user must
remember (§1.2 → `ui-ux-cognition-heuristics-and-navigation`) → the wrong gulf: they can't figure out how to act (execution) or can't
tell whether it worked (evaluation) (§2.2 → `ui-ux-cognition-heuristics-and-navigation`).

---

## §20. Sources and Method

**Method.** Narrative (not systematic) review. The durable material — §1 → `ui-ux-cognition-heuristics-and-navigation` (perception,
cognition, motor control), §2 → `ui-ux-cognition-heuristics-and-navigation` (heuristics and Norman's model), §3 → `ui-ux-cognition-heuristics-and-navigation` (IA), §4.1 → `ui-ux-interaction-layout-and-visual-design`–4.2 (input),
§5.1 → `ui-ux-interaction-layout-and-visual-design`, §6.1 → `ui-ux-interaction-layout-and-visual-design`–6.5, §10 → `ui-ux-writing-forms-research-and-ethics`, §11.1 → `ui-ux-writing-forms-research-and-ethics`, §12 → `ui-ux-writing-forms-research-and-ethics`, §15 — is synthesized from the primary research literature
and canonical texts in §18. Every **time-sensitive** claim (standards versions, legal
deadlines, platform design-language status, tooling, survey figures) was verified against a
primary or near-primary source in **August 2026** and is flagged in §17 with a decay-risk
rating. Where practitioners disagree, §16 presents both cases rather than adjudicating.

**Search log** (August 2026): WCAG 3.0 status and timeline · European Accessibility Act and
ADA Title II deadlines · Material 3 Expressive research · Core Web Vitals thresholds ·
W3C Design Tokens Community Group specification status · responsive design, container
queries, and foldables · APCA vs. WCAG 2 contrast · NN/g and AI-era UX patterns · WCAG 2.2
touch-target requirements vs. platform guidelines · dark-pattern regulation (FTC, EU DFA,
EDPB, CPRA) · design tooling 2026 (Figma Config, Penpot) · Baymard checkout research.

**Primary and near-primary sources consulted (selected):**
- W3C / WAI — WCAG 2 Overview; WCAG 3.0 Working Draft (March 2026); WAI Current Work;
  ISO/IEC 40500:2025 announcement
- ADA.gov and the **Federal Register** — Extension of Compliance Dates for ADA Title II
  web accessibility (Interim Final Rule, 20 April 2026)
- European Commission / EU consumer-policy materials — European Accessibility Act;
  Digital Fairness Act initiative and 2030 Consumer Agenda; EDPB Guidelines 03/2022
- Design Tokens Community Group — `designtokens.org`; W3C DTCG announcement of the first
  stable specification (28 October 2025); Style Dictionary DTCG documentation
- Google — `developers.google.com/search` Core Web Vitals documentation; Google Design,
  "Expressive Design: Google's UX Research" and the Material 3 Expressive Design Notes
- Apple — Newsroom announcement of the new software design (Liquid Glass); WWDC25/26
  design sessions; "Adopting Liquid Glass" documentation
- Nielsen Norman Group — articles index; State of UX 2026 coverage; "AI: First New UI
  Paradigm in 60 Years"; outcome-oriented design
- Baymard Institute — cart abandonment meta-analysis (`baymard.com/lists/cart-abandonment-rate`)
- Adrian Roselli — "WCAG3 Contrast as of April 2026"; APCA project documentation
- WebAIM — Million report figures (via secondary reporting)
- Figma — Config 2026 recap; State of the Designer 2026; AI documentation. Penpot — MCP and
  tokens announcements

**Confidence statement.** **High confidence** in §1–§6 → `ui-ux-cognition-heuristics-and-navigation`, `ui-ux-interaction-layout-and-visual-design`, §9.1 → `ui-ux-design-systems-platforms-and-accessibility`–9.2, §10 → `ui-ux-writing-forms-research-and-ethics`, §12 → `ui-ux-writing-forms-research-and-ethics`, §15, §18–§19 —
these rest on primary research, standards documents, and law. **High confidence** in §17's
verified items as of the stated date. **Moderate confidence** in §7.4 → `ui-ux-design-systems-platforms-and-accessibility`, §11.2 → `ui-ux-writing-forms-research-and-ethics`, §13 → `ui-ux-writing-forms-research-and-ethics`'s
enforcement figures, and §14.4 → `ui-ux-writing-forms-research-and-ethics` — these rest on vendor surveys, commercial research
organizations, and practitioner reporting where methodology is often unpublished and
incentives differ; they are stated as reported findings with their sources named, not as
established fact. The Material 3 Expressive figures in §8.2 → `ui-ux-design-systems-platforms-and-accessibility` and the Baymard figures in
§11.2 → `ui-ux-writing-forms-research-and-ethics` are specifically flagged in place as vendor/commercial research whose *direction*
is more reliable than its *magnitudes*.
