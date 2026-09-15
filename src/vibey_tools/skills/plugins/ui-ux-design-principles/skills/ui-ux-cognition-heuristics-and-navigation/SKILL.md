---
name: ui-ux-cognition-heuristics-and-navigation
description: "Use when reasoning about why an interface works or fails, or structuring one. Covers the four form factors honestly compared (the router for the whole ui-ux-design-principles reference), motor control (Fitts's law), decision and attention (Hick's law), perception and grouping (Gestalt), memory of the experience (peak-end), learning and expertise, Nielsen's 10 heuristics with their failure modes, Norman's model (affordances, signifiers, the gulfs), confirmation vs undo, progressive disclosure and defaults, the IA questions in order, navigation patterns by form factor, search, and wayfinding."
---

# UI/UX Design: The Science Underneath, Usability Heuristics, and Information Architecture

> **Part 1 of 5** of the *UI/UX Design Principles — Mobile, Tablet, Web, Desktop* reference (plugin `ui-ux-design-principles`), covering §0–§3. Sibling skills: `ui-ux-interaction-layout-and-visual-design` (§4–§6), `ui-ux-design-systems-platforms-and-accessibility` (§7–§9), `ui-ux-writing-forms-research-and-ethics` (§10–§14), `ui-ux-reference` (§15–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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

## §0. Routing

### 0.1 The four form factors, honestly compared

| | **Mobile** | **Tablet** | **Web (desktop browser)** | **Desktop (native)** |
|---|---|---|---|---|
| Primary input | Thumb, one hand, imprecise | Two hands / stylus | Mouse + keyboard | Mouse + keyboard, heavy shortcut use |
| Pointer precision | ~9 mm finger contact | ~9 mm, better reach | ~1 px | ~1 px |
| Session length | Seconds–minutes | Minutes | Minutes | Hours |
| Attention | Divided, interrupted, mobile | Semi-focused, leisure | Task-focused, multi-tab | Deep focus, expert |
| Context | Anywhere, any light, any network | Couch, desk, kiosk | Desk | Desk |
| Information density | Minimum viable | Medium | Medium-high | **High — and users want it** |
| Navigation idiom | Tab bar / bottom sheet / stack | Split view, sidebar | Header nav + breadcrumbs | Menu bar, sidebar, panels, palettes |
| Discoverability need | High (few affordances visible) | High | Medium | Lower (menus are a searchable index) |
| Error cost of a mis-tap | High | Medium | Low | Low |
| Undo expectation | Weak (usually) | Weak | Weak | **Strong — unlimited, always** |
| Offline expectation | High | High | Low-medium | High |
| Governing convention | Apple HIG / Material 3 | Apple HIG / Material 3 | Web conventions + your design system | Platform HIG (macOS/Windows/GNOME/KDE) |

**[DURABLE] The most common cross-form-factor mistake is transposing density.** Shrinking
a desktop layout produces an unusable phone screen; stretching a phone layout produces a
desktop app that insults its users by wasting 70% of the screen and hiding functionality
three taps deep. Density is not a styling decision — it's a claim about how much the user
can and wants to hold in view at once, and that differs by context, not just by pixels.

### 0.2 The question router

| Asked about... | Go to |
|---|---|
| Why does this feel confusing/slow/wrong? Perception, memory, attention | §1 |
| Heuristics, usability principles, Norman's model, affordances | §2 |
| Navigation, IA, search, findability, menu structure | §3 |
| Touch vs pointer vs keyboard, gestures, thumb zones, input models | §4 → `ui-ux-interaction-layout-and-visual-design` |
| Layout, grids, responsive, breakpoints, adaptive, foldables | §5 → `ui-ux-interaction-layout-and-visual-design` |
| Typography, color, spacing, elevation, iconography, motion | §6 → `ui-ux-interaction-layout-and-visual-design` |
| Design systems, tokens, component APIs, governance | §7 → `ui-ux-design-systems-platforms-and-accessibility` |
| Platform conventions and how they differ | §8 → `ui-ux-design-systems-platforms-and-accessibility` |
| Accessibility — principles, WCAG, law, testing | §9 → `ui-ux-design-systems-platforms-and-accessibility` |
| Microcopy, error messages, empty states, tone | §10 → `ui-ux-writing-forms-research-and-ethics` |
| Forms, onboarding, checkout, conversion | §11 → `ui-ux-writing-forms-research-and-ethics` |
| Research methods, usability testing, sample size, analytics | §12 → `ui-ux-writing-forms-research-and-ethics` |
| Metrics, HEART, success criteria | §12.4 → `ui-ux-writing-forms-research-and-ethics` |
| Dark patterns, persuasion ethics, regulation | §13 → `ui-ux-writing-forms-research-and-ethics` |
| AI-era interfaces, conversational UI, generative UI | §14 → `ui-ux-writing-forms-research-and-ethics` |
| "Don't do this" | §15 → `ui-ux-reference` |
| "Which is better, X or Y?" | §16 → `ui-ux-reference` (contested) |
| Books, researchers, authoritative sources | §18 → `ui-ux-reference` |
| "Is this still current?" | §17 → `ui-ux-reference` |

---

## §1. The Science Underneath — why interfaces work or don't

Almost every defensible design decision reduces to one of these. Knowing them turns
"I don't like it" into "this will cost users ~600 ms per interaction and here's why."

### 1.1 Motor control

**Fitts's Law [DURABLE]** — time to acquire a target is a function of distance and size:
`MT = a + b·log₂(2D/W)`. Practical consequences, in rough order of value:
- **Bigger targets are faster and more accurate.** Non-negotiable, measurable, and the
  basis of every touch-target guideline in §4.2 → `ui-ux-interaction-layout-and-visual-design`.
- **Closer targets are faster.** Put the primary action near where the user's attention
  and pointer already are — not in a corner because the grid says so.
- **Screen edges and corners have effectively infinite width** in one dimension, because
  the pointer stops there. This is why the macOS menu bar (screen top) is faster to hit
  than a Windows in-window menu bar, and why the corners are the most valuable real estate
  on a desktop screen. On touch, edges have the *opposite* property — they're where the
  hand occludes and where system gestures live.
- **Dangerous actions should violate Fitts deliberately**: make Delete smaller, farther, or
  behind a confirm. Never place Cancel adjacent to a destructive primary.

**Steering Law [DURABLE]** — time to move *through* a constrained path grows with path
length and shrinks with tunnel width. This is why deep cascading menus are painful (you
must steer down a narrow corridor without leaving it) and why macOS's diagonal-tolerance
in submenus was a genuine innovation. If your nav requires precise steering, add
dwell tolerance or convert to click-to-open.

### 1.2 Decision and attention

**Hick–Hyman Law [DURABLE, but frequently over-applied]** — decision time grows
logarithmically with the number of *equally likely* alternatives: `RT = a + b·log₂(n+1)`.
- Correct use: don't put 40 undifferentiated options in one flat list.
- **⚠️ Misuse:** "Hick's Law says fewer menu items are always better" — false. The log is
  cheap; a well-*categorized* list of 40 is faster than a flat list of 8 that requires
  drilling. And options are rarely equally likely — a good default collapses the decision
  entirely. **Categorization beats reduction.**

**Miller's "7±2" [DURABLE finding, WIDELY misapplied]** — Miller (1956) described
short-term memory capacity for *chunks* in a recall task. It was never a rule about menu
length or navigation items, and Miller himself objected to that use. The better modern
number is **Cowan's ~4±1** chunks for working memory without rehearsal. The design
implication is real but different: **don't require users to hold state in their heads**.
Show the previous step. Persist the filter. Display the total. Recognition over recall
(§2.1) is the actual principle.

**Cognitive load [DURABLE]** — three types worth distinguishing:
- *Intrinsic*: inherent difficulty of the task. You can't remove it, only sequence it.
- *Extraneous*: load imposed by the interface itself. **This is the entire target of UI
  design.** Inconsistent labels, hidden state, unclear hierarchy, unnecessary choices.
- *Germane*: effort spent building a useful mental model. Worth preserving.

**Attention is selective and change-blind.** Users do not see your banner. Inattentional
blindness and **banner blindness** are well replicated: elements that look like ads, sit in
ad-shaped positions, or animate like ads get filtered out pre-consciously. If something
must be seen, it goes in the content flow, not the periphery.

### 1.3 Perception and grouping

**Gestalt principles [DURABLE]** — the visual system groups before you consciously read.
In rough order of strength:
1. **Proximity** — nearest elements group. *The single most powerful and most misused tool
   in UI layout.* If a label is equidistant between two fields, users will guess.
2. **Similarity** — same color/shape/size groups. This is why "everything is a button" and
   "nothing looks like a button" are both failures.
3. **Common region** — a shared border or background box groups strongly, and *overrides
   proximity*. Cards work because of this.
4. **Continuity / Common fate** — aligned or co-moving elements group. Alignment isn't
   aesthetics, it's grouping.
5. **Closure / Figure-ground** — the mind completes shapes and separates foreground.

**⚠️ GOTCHA — the proximity bug.** The most common spacing error in real products:
equal margins above and below a label, so it visually belongs to neither the field above
nor the field below. **Rule: the space *within* a group must be smaller than the space
*between* groups.** Almost every "this form feels cluttered" complaint is this.

**Von Restorff (isolation) effect [DURABLE]** — the item that differs is remembered and
found. This is the entire justification for having exactly **one** primary button per view.
Two primary buttons = zero primary buttons.

**Serial position effect [DURABLE]** — first and last items in a list are recalled best.
Put the most important nav item first, the second-most last.

### 1.4 Memory of the experience

**Peak-End Rule [DURABLE]** — people judge an experience by its most intense moment and
its ending, not its average. Design consequences:
- Invest disproportionately in the **worst moment** (the error, the wait, the failed
  payment) and the **last moment** (the confirmation, the success state, the offboarding).
- A pleasant confirmation screen genuinely changes the remembered quality of a tedious form.

**Zeigarnik effect [DURABLE-ish]** — incomplete tasks stay in memory. Progress indicators
and "3 of 5 steps" work partly because of this. It is also the mechanism behind
completion-pressure dark patterns (§13 → `ui-ux-writing-forms-research-and-ethics`) — same lever, different intent.

**Doherty Threshold (~400 ms) [DURABLE]** — below roughly 400 ms of system response,
users stay in flow and productivity rises superlinearly. Above ~1 s, attention wanders.
This is why perceived performance is a *design* concern (§6.6 → `ui-ux-interaction-layout-and-visual-design`), not just an engineering one.

**Time perception is malleable.** Progress bars that accelerate toward the end feel
faster. Skeleton screens feel faster than spinners because they signal *what* is coming.
Optimistic UI (show the result immediately, reconcile later) feels instant — but you must
then design the failure path honestly, not silently drop the change.

### 1.5 Learning and expertise

**Power law of practice [DURABLE]** — performance improves as a power function of
repetitions. Two consequences:
- **Novices and experts need different affordances of the same function.** A menu item
  (discoverable, slow) and a keyboard shortcut (fast, invisible) for the same command is
  not redundancy — it's the correct design. **Show the shortcut in the menu** so the
  transition happens.
- **Consistency is compound interest.** Every deviation resets the learning curve.

**Jakob's Law [DURABLE]** — users spend most of their time on *other* products, so they
expect yours to work like those. Novel interaction models carry an enormous, usually
underestimated cost. Innovate on the *product*, not on where the close button lives.

---

## §2. Usability Heuristics and Mental Models

### 2.1 Nielsen's 10 heuristics — with the failure mode of each

Still the most useful evaluation checklist ever written (Nielsen & Molich 1990, refined
1994). Below, each heuristic plus how it's commonly violated *by teams who think they're
following it*:

| Heuristic | What it means | How it fails in practice |
|---|---|---|
| 1. **Visibility of system status** | Always tell the user what's happening | A spinner with no ETA, no cancel, and no indication of what's loading. "Saving…" that never resolves. Optimistic UI that silently fails. |
| 2. **Match between system and the real world** | Speak the user's language | Internal jargon leaking into UI ("Entity", "Object", "Instance", "Sync conflict"). Icons that mean something only to the team. |
| 3. **User control and freedom** | Emergency exits, undo | Modals with no Escape. Wizards with no Back. Destructive actions with confirm-only and no undo (§2.3). |
| 4. **Consistency and standards** | Internal + platform consistency | Three different date pickers. A "Save" that means Apply on one screen and Commit on another. |
| 5. **Error prevention** | Prevent > handle | Free-text where a picker belongs. No inline validation. Allowing a state the system will reject later. |
| 6. **Recognition rather than recall** | Show, don't make them remember | Hiding the filter you applied. Requiring a code from a previous screen. Icon-only toolbars with no labels. |
| 7. **Flexibility and efficiency of use** | Accelerators for experts | No keyboard shortcuts. No bulk actions. No saved views. Optimizing solely for first-run. |
| 8. **Aesthetic and minimalist design** | No irrelevant information | **Most misread heuristic.** It says *irrelevant* — not *sparse*. Hiding necessary controls to look clean is a violation, not compliance. |
| 9. **Help users recognize, diagnose, recover from errors** | Plain language, cause, remedy | "Error 0x8007." "Something went wrong." Errors that don't say which field. |
| 10. **Help and documentation** | Findable, task-oriented | A 60-page PDF. A help center that doesn't cover the thing that's confusing. |

### 2.2 Norman's model — the vocabulary for diagnosing *why*

- **Affordance** — what an object *permits* (a real relationship between object and user).
- **Signifier** — the *perceivable cue* that communicates the affordance. In UI, you almost
  always mean signifier. A flat rectangle affords clicking; it needs a signifier to say so.
- **Mapping** — relationship between control and effect. Natural mapping = spatial
  correspondence (the volume slider goes up for louder).
- **Feedback** — immediate, informative confirmation that the system received the action.
- **Constraints** — physical, semantic, cultural, logical limits on what can be done.
- **Conceptual model** — the user's story about how the thing works.

**The Gulf of Execution** (how do I do it?) and the **Gulf of Evaluation** (did it work?).
Every usability problem lives in one of these two gaps. When someone says "the UX is bad,"
ask which gulf — the answers are completely different interventions.

> **⚠️ GOTCHA — the flat-design signifier deficit.** The flat/minimal aesthetic that has
> dominated since ~2013 systematically removed signifiers (shadows, bevels, borders,
> underlines). Research repeatedly finds users hesitate over, or fail to find, weak-signifier
> controls — and it disproportionately affects older and less experienced users. **Ghost
> buttons, borderless inputs, and unlined links are aesthetic choices with a measurable
> usability cost.** Make it deliberate, and compensate (hover states, cursor changes,
> generous targets, at minimum a border on inputs).

### 2.3 Confirmation vs. undo

**[DURABLE] Undo beats confirmation almost always.** Confirmation dialogs:
- are dismissed reflexively after the third exposure (habituation),
- interrupt flow for the 99% of cases that were intentional,
- and provide no help in the 1% where the user was wrong but *confident*.

Prefer: perform the action → show a **toast with Undo** → make it durable for a reasonable
window. Reserve confirmation for actions that are genuinely irreversible *and* consequential
(deleting an account, sending money, publishing). When you must confirm:
- Name the specific object ("Delete *Q3 Budget.xlsx*?"), never "Are you sure?"
- Label buttons with **verbs**, not Yes/No ("Delete" / "Cancel").
- State the consequence, including irreversibility.
- Make the destructive option *not* the default and *not* adjacent to the safe one.

### 2.4 Progressive disclosure and defaults

**[DURABLE] Defaults are the most powerful design decision you make.** Most users never
change them; the default *is* the product for the majority. Choose them for the user's
benefit, and be aware that choosing them for yours is what regulators now call a dark
pattern (§13 → `ui-ux-writing-forms-research-and-ethics`).

**Progressive disclosure** — show the common case; make the advanced case reachable, not
absent. The discipline is: (a) the entry point to the hidden layer must be visible,
(b) hiding must be based on *frequency of use*, not on *how tidy it looks*, and (c) never
hide something the user needs in order to understand what's on screen.

---

## §3. Information Architecture and Navigation

### 3.1 The IA questions, in order

1. **What are the objects?** (Not screens — *things*. Documents, orders, patients, tracks.)
2. **What are their attributes and relationships?**
3. **How will people look for them?** (Known-item search vs. exploratory browse vs.
   re-finding something they saw before — these are different behaviours needing
   different affordances.)
4. **What vocabulary do *they* use?** (Not your database's.)
5. **What's the primary organizing scheme?**

**Organizing schemes [DURABLE]:**
- *Exact* schemes (alphabetical, chronological, geographic) — unambiguous, good for
  known-item lookup, useless for exploration.
- *Ambiguous* schemes (by topic, task, audience, metaphor) — support exploration, require
  the user to guess your model. Most product IA is ambiguous, which is why card sorting
  (§12.2 → `ui-ux-writing-forms-research-and-ethics`) exists.
- *Hybrid* schemes fail when they mix at the same level ("Products, Support, For Teams,
  Pricing, 2024 Archive"). Mixing across levels is fine; mixing within one is confusing.

### 3.2 Navigation patterns by form factor

| Pattern | Best for | Capacity | Watch out |
|---|---|---|---|
| **Bottom tab bar** (mobile) | 3–5 top-level, equally important, frequently switched destinations | 5 max (iOS shows "More" beyond 5) | Not for actions. Not for >5. Not for hierarchy. |
| **Navigation drawer / hamburger** | Many destinations, infrequent switching | ~10 | **Measurably reduces discoverability and engagement of hidden items.** Acceptable for secondary nav; bad for primary. |
| **Segmented control / tabs** | Switching *views of the same object* | 2–5 | Not for navigation to different objects |
| **Stack / push navigation** | Drilling into hierarchy | Any depth (but >3 feels lost) | Must show where you are and how to get back |
| **Bottom sheet** | Contextual actions, secondary content, mobile modality | — | Don't nest. Don't hide primary tasks. |
| **Split view / sidebar** (tablet, desktop) | Master–detail | Large | Reflow when narrow; don't just clip |
| **Top nav + mega menu** (web) | Broad, shallow site structure | Large | Keyboard and screen reader support is usually broken |
| **Breadcrumbs** (web, desktop) | Deep hierarchy, orientation | — | Only if a real hierarchy exists; not for linear flows |
| **Command palette** (⌘K) | Expert users, large command surface | Unlimited | Excellent *supplement*, never the only path |
| **Menu bar** (desktop) | Complete, searchable command index | Unlimited | Every command should be here (§8.4 → `ui-ux-design-systems-platforms-and-accessibility`) |

**[CONTESTED] The hamburger menu.** The evidence that hiding navigation reduces usage of
hidden items is strong and replicated. The counterargument is equally real: on a 375 px
screen with eight destinations, there is no alternative that doesn't consume the content
area, and a tab bar with eight items is worse. The defensible position: **use a tab bar for
the 3–5 things people do constantly and a drawer for the long tail**, and never put a
primary revenue or activation path behind the hamburger.

### 3.3 Search

- **If the catalogue is large, search is the primary navigation** — treat it as a feature,
  not a text box in the corner.
- **Support the failure cases**: typos (fuzzy matching), synonyms and the user's vocabulary,
  zero results (offer alternatives, never a dead end), and scoped search (this folder vs.
  everything).
- **Show what was searched and what filters are active.** Losing your query on the results
  page is a top-tier frustration.
- **Autocomplete** shifts the task from recall to recognition — one of the highest-value
  patterns available. Show *categories* of suggestions, not just strings.

### 3.4 Wayfinding — the three questions

Every screen must answer, without effort: **Where am I? Where can I go? How do I get back?**
Mechanisms: persistent nav with a current-state indicator, page titles that match the link
that got you there (label consistency — a startling number of products fail this),
breadcrumbs, and a Back that does what the platform Back is supposed to do.

> **⚠️ GOTCHA — hijacking Back.** On Android, the system Back gesture/button has defined
> semantics. On the web, the browser Back must work in a SPA (History API, not just
> client-side routing that leaves the URL stale). Users trust Back more than they trust
> your UI; breaking it destroys that trust immediately and permanently.
