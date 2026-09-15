---
name: ui-ux-writing-forms-research-and-ethics
description: "Use when writing interface copy, designing forms and onboarding, planning or running UX research, auditing for dark patterns, or designing AI features. Covers UX-writing principles and the high-value surfaces, how localization affects design, form design and the checkout/conversion evidence, onboarding, choosing a research method, sample sizes, running a usability test that produces truth, metrics (SUS, HEART), the ethics line, the dark-pattern catalogue and the 2026 regulatory picture (DSA, FTC, DMA), and AI-era interfaces — design principles for AI features, generative UI and its risk, and tooling reality."
---

# UI/UX Design: UX Writing, Forms and Conversion, Research, Ethics, and AI-Era Interfaces

> **Part 4 of 5** of the *UI/UX Design Principles — Mobile, Tablet, Web, Desktop* reference (plugin `ui-ux-design-principles`), covering §10–§14. Sibling skills: `ui-ux-cognition-heuristics-and-navigation` (§0–§3), `ui-ux-interaction-layout-and-visual-design` (§4–§6), `ui-ux-design-systems-platforms-and-accessibility` (§7–§9), `ui-ux-reference` (§15–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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

## §10. Content and UX Writing

**[DURABLE] The interface is mostly words.** Most "confusing UI" is confusing *language*
wearing a layout.

### 10.1 Principles

- **Clarity beats cleverness. Always.** Nobody has ever been delighted by a witty error
  message they couldn't act on.
- **Front-load the meaningful words.** Users scan the first two words of a link, heading,
  or bullet. "Download the annual report (PDF)" not "Click here to download…"
- **Use the user's vocabulary**, sourced from research, support tickets, and search logs —
  not the database schema and not marketing.
- **Be consistent.** One concept, one word, everywhere. If it's a "workspace" in nav it's
  not a "team" in settings.
- **Active voice, present tense, second person.** "Your changes are saved" not "Changes
  have been saved by the system."
- **Sentence case** for UI labels reads faster than Title Case and is the modern convention
  on every major platform.
- **Numbers, dates, and units are localized.** `1,234.56` vs `1.234,56` is a real bug.

### 10.2 The high-value surfaces

**Buttons** — a verb naming the outcome. "Save changes", "Create account", "Delete
project". Never "OK", "Submit", "Yes/No" for consequential choices. The button label must
match the heading that preceded it.

**Error messages** — three parts, in this order:
1. **What happened**, plainly. ("We couldn't process your payment.")
2. **Why**, if you know and it's actionable. ("Your card was declined by your bank.")
3. **What to do next.** ("Try another card, or contact your bank.")
Never blame the user, never expose a stack trace or code as the only content (a support
reference code *in addition* is fine and useful), never say "invalid input" without saying
which input and what would be valid.

**Empty states** — the most under-designed screen in most products, and a first-run user's
first impression. It should: explain what belongs here, why it's empty, and give one clear
action to fill it. Distinguish *first-use empty* (teach), *user-cleared empty* (celebrate or
reassure), *no-results empty* (offer alternatives and a way to broaden), and *error empty*
(diagnose).

**Loading and progress** — say what's loading. "Loading your invoices" beats a spinner.

**Confirmation and success** — name what happened and offer the next step. This is the
"end" in peak-end (§1.4 → `ui-ux-cognition-heuristics-and-navigation`) and it's cheap to do well.

**Microcopy on inputs** — a persistent hint below the field (not a placeholder) explaining
format requirements *before* the user fails, not after.

### 10.3 Localization affects design, not just strings

- **Text expansion**: German/Finnish run 30–40% longer than English; some languages 100%+
  for short strings. Fixed-width buttons break. Design for expansion or use flexible
  layouts and test with pseudo-localization.
- **RTL (Arabic, Hebrew, Farsi)** mirrors the entire layout — navigation, icons with
  directionality (back arrows, progress), and reading order. Use *logical* properties
  (`margin-inline-start`, not `margin-left`) and test with a force-RTL flag.
- **Never concatenate translated fragments.** Word order differs; use positional format
  strings.
- **Plurals need real plural rules** (Arabic has six categories), not `if (n === 1)`.
- **CJK** has different line-breaking, no spaces between words, and different comfortable
  line-heights; ideographs need more vertical space.
- **Names, addresses, phone formats, honorifics, and date orders are not universal.** A
  required "First name / Last name" split is wrong for a large fraction of the world.

---

## §11. Forms, Onboarding, and Conversion

### 11.1 Form design — where usability turns directly into money

**[DURABLE] Every field you remove increases completion.** Ask only for what you need *now*.

| Rule | Why |
|---|---|
| **One column.** | Multi-column forms cause skipped fields and ambiguous tab order. Exception: genuinely paired short fields (city/state, expiry month/year). |
| **Labels above fields, always visible.** | Fastest to scan; survives zoom; works with autofill; placeholder-as-label is a documented failure. |
| **Group related fields** with clear spacing (§1.3 → `ui-ux-cognition-heuristics-and-navigation`). | Proximity does the work. |
| **Inline validation *after* the field loses focus**, not on every keystroke. | Validating while typing tells users they're wrong before they've finished being right. |
| **Show requirements up front** (password rules, format). | Error prevention > error handling (Nielsen #5). |
| **Correct `autocomplete` attributes and `inputmode`.** | Autofill is a huge completion win and an accessibility feature. `inputmode="numeric"` gives the right mobile keyboard. |
| **Never mask what the user typed** (except passwords, and offer a reveal). | Card numbers, codes, and emails all benefit from being visible for checking. |
| **Mark optional fields, not required ones** — if most are required. | Fewer asterisks, less noise. |
| **Error summary at the top + inline errors + focus the first error.** | Screen-reader users and zoomed users can't see an error 2000 px down. |
| **Preserve entered data on error.** | Losing a filled form is the fastest way to lose a user. |

### 11.2 The checkout/conversion evidence

Baymard Institute's long-running large-scale checkout usability research is the most-cited
data set here. Key figures, with the caveats they deserve:
- **~70.2% average cart abandonment**, from a meta-analysis of ~50 studies (last updated
  Sept 2025). This has been structurally stable for a decade, moving under a percentage
  point in five years.
- Baymard estimates the average large e-commerce site could gain **~35.26% conversion**
  from checkout-design improvements alone — framed by them as an upper bound from a decade
  of documented, solvable issues, **not a guaranteed return**, and explicitly excluding the
  large share of abandonment that is pure browsing intent.
- **Extra costs at checkout** (shipping, fees, tax) are consistently the top abandonment
  reason (~39%); **forced account creation** ~24%; **too long/complicated a checkout**
  ~19%; **not trusting the site with card details** ~19%.
- The average checkout shows **~23.5 form elements / ~14.9 fields**, versus an achievable
  **12–14**; most sites can cut 20–60% of elements.

**⚠️ Cite these carefully.** They are aggregates across many studies and verticals, mostly
from one (excellent, commercial) research organization; live-behaviour trackers report
higher numbers (Dynamic Yield ~77.8% on a rolling 12-month basis) because they measure
something slightly different. Use them to *prioritize*, not as targets your specific site
will hit.

**The practical hierarchy:** show total cost early → offer guest checkout → cut fields →
one obvious next step per screen → visible trust signals near the payment field → support
the payment methods your market actually uses.

### 11.3 Onboarding

- **Show value before you ask for commitment.** Delay signup, delay permissions, delay the
  tour. Permission requests should be *contextual* ("Allow notifications so we can alert
  you when your order ships") and *at the moment of need*, not at first launch — a
  cold-start permission prompt is the most reliable way to get a permanent denial.
- **Progressive onboarding beats a carousel.** Teach the feature when it's first relevant.
  Multi-screen intro carousels are almost universally skipped.
- **Reduce time-to-first-value** relentlessly. Sample data, templates, and sensible defaults
  beat an empty state plus a tutorial.
- **Let users skip, and let them return.** A tour you can't exit is a hostage situation.

---

## §12. Research and Evaluation

### 12.1 Choosing a method

| Question | Method |
|---|---|
| Can people *do* the task? | **Usability test** (moderated or unmoderated) |
| Why do they behave that way? | Interviews, contextual inquiry, diary study |
| What do they do at scale? | Analytics, funnels, session replay |
| Which version performs better? | A/B test |
| How do they think about the domain? | Card sort, tree test, mental-model interview |
| Can they *find* it? | **Tree test** (IA without UI) / first-click test |
| Is it accessible? | Expert audit + AT testing + testing with disabled users (§9.5 → `ui-ux-design-systems-platforms-and-accessibility`) |
| How do they feel over time? | Longitudinal survey (SUS/UMUX-Lite/NPS), diary |
| Does it violate known principles? | **Heuristic evaluation** (§2.1 → `ui-ux-cognition-heuristics-and-navigation`) — cheap, fast, and finds different issues than testing |

**[DURABLE] Attitudinal ≠ behavioural.** What people *say* they'd do is a poor predictor of
what they *do*. Never ship a feature on survey preference alone.

### 12.2 Sample sizes — the number everyone quotes and misuses

**Nielsen & Landauer's "5 users find ~85% of usability problems"** is the most cited and
most abused finding in UX. What it actually says: with a problem-detection probability of
~31% per user per problem, five users find about 85% of problems **in a single homogeneous
user group performing similar tasks**. What it does *not* say:
- It doesn't apply across **distinct user segments** — each segment needs its own ~5.
- It doesn't apply to **quantitative** measures (task time, success rate, satisfaction).
  Those need 20+ per condition for anything resembling a confidence interval.
- It doesn't mean five is *enough*; it means five is the point of diminishing returns for
  *one round*, and **three rounds of five beats one round of fifteen** because you fix
  things between rounds.
- The 31% detection rate itself varies with task and interface complexity.

**Rough guide:** qualitative usability 5–8 per segment per round; card sort 15–30;
tree test 30–50; quantitative benchmark 20+ per condition; A/B test — whatever your power
analysis says, calculated *before* you start.

### 12.3 Running a usability test that produces truth

- **Give tasks, not instructions.** "Find out how much it would cost to ship two of these
  to Berlin" — not "click the shipping calculator."
- **Don't lead.** When they ask "should I click here?", answer "what would you do if I
  weren't here?"
- **Silence is data.** Let them struggle for a bit; the struggle is the finding.
- **Watch behaviour, weight it above commentary.** Users are unreliable narrators of their
  own difficulty and are systematically polite about your work.
- **Recruit for the actual user**, not for whoever's convenient. Testing an enterprise tool
  on your friends produces confident nonsense.
- **Separate observation from interpretation** in your notes. "Clicked Back three times" is
  an observation; "was confused by the nav" is a hypothesis.
- **⚠️ Beware of testing only success paths.** Most real-world pain is in errors, edge cases,
  recovery, and the second session — not the happy path you designed the prototype for.

### 12.4 Metrics

**HEART** (Google) — pick per-project, and pair each with a **Goal → Signal → Metric**:
Happiness, Engagement, Adoption, Retention, Task success.

Complementary standards:
- **SUS** (System Usability Scale) — 10 items, 0–100; ~68 is average, 80+ is good.
  Comparable across products and time, which is its real value.
- **SEQ** (Single Ease Question) — one 7-point question after each task. Startlingly
  informative for its cost.
- **Task success rate, time on task, error rate** — the core behavioural triad.
- **Core Web Vitals** (§6.6 → `ui-ux-interaction-layout-and-visual-design`) for web performance.

**⚠️ Choose metrics that can go *down* when you make things worse.** Engagement metrics are
notorious for rewarding dark patterns: time-on-site rises when users are confused, and
session count rises when notifications are manipulative. Pair every engagement metric with a
quality metric (task success, retention, complaint rate, unsubscribe rate).

---

## §13. Ethics, Persuasion, and Dark Patterns

### 13.1 The line

**[DURABLE] The test is whose interest the design decision serves when the user's and the
business's diverge.** Persuasion that helps a user do what they already wanted is design.
Design that exploits a cognitive bias to produce a choice the user would not otherwise make
is a dark pattern — and increasingly, a legal violation.

### 13.2 The catalogue

| Pattern | Mechanism | Regulatory exposure |
|---|---|---|
| **Roach motel** (easy in, hard out) | Asymmetric effort | FTC: Epic $245M; Amazon $2.5B settlement (which surfaced internal emails on deliberately confusing cancellation) |
| **Sneak into basket / drip pricing** | Late disclosure | UCPD, FTC |
| **Confirmshaming** ("No thanks, I hate saving money") | Social/emotional pressure | DFA target |
| **Preselected options / pre-ticked boxes** | Default exploitation | GDPR consent invalidity |
| **Asymmetric consent** (bright "Accept all", buried "Reject") | Choice architecture | **CNIL fined Google €150M and Microsoft €60M** on exactly this; TikTok €345M (Irish DPC) for public-by-default; Amazon €746M |
| **False urgency / fake scarcity** ("1 room left!") | Manufactured pressure | UCPD; DFA named target |
| **Disguised ads** | Misrepresentation | FTC endorsement rules |
| **Nagging** | Repetition until compliance | |
| **Obstruction / privacy zuckering** | Friction as a weapon | CPRA: "dark patterns are about effect, not intent" |
| **Infinite scroll + autoplay + variable rewards** | Attention capture | DFA "addictive design" target |

### 13.3 The regulatory picture (2026)

- **EU DSA Article 25** already prohibits online-platform interfaces that "deceive,
  manipulate or otherwise materially distort" users' ability to make free and informed
  decisions. **DMA** carries fines up to 6% of global revenue for consent manipulation.
- **EDPB Guidelines 03/2022** define six GDPR dark-pattern categories: *overloading,
  skipping, stirring, obstructing, fickle, left in the dark*. Useful as a design checklist,
  not just a legal one.
- **Consumer Rights Directive amendments** ban dark patterns in distance financial-services
  interfaces — transposed by 19 December 2025, **applicable from 19 June 2026**.
- **EU Digital Fairness Act** — confirmed in the Commission's 2030 Consumer Agenda (adopted
  19 November 2025); **proposal expected late 2026**, targeting dark patterns, addictive
  design, influencer marketing, and personalization. Adoption realistically 2027+, entry
  into force 2028–2030. **Not law yet — do not describe it as such.**
- **US FTC** is actively enforcing under Section 5, including **naming individual executives
  as defendants**. Its 2024 study of 642 sites/apps found **76% used at least one possible
  deceptive pattern** and ~67% used multiple. The Commission's 2022 EU study found **97% of
  the most popular EU-used sites and apps** deployed at least one.
- **California CPRA** treats dark patterns as consent-invalidating, with the CPPA's standard
  being **symmetry**: the privacy-protective option must be *as easy* as the less protective
  one.

### 13.4 The design checklist

- [ ] Cancelling is as easy as subscribing (same channel, same number of steps).
- [ ] The privacy-protective choice is as prominent and as few clicks as the permissive one.
- [ ] No pre-ticked consent boxes; consent is a positive, unambiguous act.
- [ ] Total price, including all fees, disclosed before the user invests effort.
- [ ] Urgency and scarcity claims are literally true and verifiable.
- [ ] Decline options are neutrally worded — no shaming.
- [ ] Defaults chosen for the user's benefit, and you can say why.
- [ ] Ads and sponsored content are unmistakably labeled.
- [ ] Consent flows are documented and evidenced.
- [ ] No design element manipulates children or exploits known vulnerabilities.

**[UNIVERSAL] "It wasn't intentional" is not a defense** — the CPPA's stated position is
that dark patterns are about *effect*, not intent. An A/B test that increased conversion by
making the reject button harder to find has produced a violation regardless of what anyone
meant.

---

## §14. AI-Era Interfaces

### 14.1 What actually changed

**[CONTESTED, and the most overclaimed area in the field.]** Two framings:
- NN/g's line (Nielsen, 2023): generative AI is the **first new UI paradigm in 60 years** —
  *intent-based outcome specification* rather than command specification. NN/g's **State of
  UX 2026** extends this: UI is becoming less of a differentiator, AI-mediated interaction
  sits on top of the interface, and equating UX with UI increasingly misdescribes the work.
- The skeptical line: chat is a *regression* in discoverability, learnability, and
  efficiency for most tasks; it externalizes the interface designer's job onto the user, who
  must now guess what the system can do. A blank text box has zero affordances.

**The synthesis practitioners actually ship:** a **hybrid** — conversational or intent-based
entry, traditional UI for execution and refinement. The rule of thumb that circulates and
holds up well: *if the user can describe the task in one sentence, conversational works; if
the task requires manipulation, comparison, precision, or spatial reasoning, give them a UI.*

### 14.2 Design principles for AI features

1. **Set expectations before the first interaction.** What can this do? What can't it?
   What data does it see? Blank-box interfaces produce both over- and under-estimation.
2. **Make capability discoverable** — suggested prompts, examples, templates. This is the
   direct replacement for menus and buttons as an affordance mechanism.
3. **Show provenance and uncertainty.** Citations, sources, confidence signals. Users
   calibrate trust from these; without them they either over-trust or reject wholesale.
4. **Keep the human in control**: editable output, regenerate, undo, and a way to *not* use
   the AI path. Never make the AI the only route to a function.
5. **Design for failure as a first-class state.** Hallucination, refusal, timeout,
   irrelevance. These are not edge cases; they're the normal distribution's tail and users
   hit them constantly.
6. **Make cost and latency legible.** Streaming output is a UX decision (it converts a
   10-second wait into a 300 ms first token, §6.6 → `ui-ux-interaction-layout-and-visual-design`). Token/credit consumption should be
   visible where it matters.
7. **Feedback loops** — thumbs, corrections, "not what I meant" — both for model improvement
   and because the ability to complain is itself a control affordance.
8. **Privacy transparency** — what's sent, what's retained, what trains. This is a design
   surface, not a legal footnote.

### 14.3 Generative UI, and its risk

"Generative UI" — interfaces assembled or adapted at runtime — is real and growing, and
NN/g frames the shift as **outcome-oriented design**: designing adaptive *frameworks* that
respond to individual goals rather than optimizing single interfaces for an average user.

Two documented risks worth holding onto:
- **Homogenization.** AI generation draws on dominant patterns; one Adobe study reported
  **>42% of AI-generated interfaces shared similar navigation structures and components**.
  The floor rises; the ceiling doesn't.
- **Dark patterns at scale.** An NN/g survey found **36% of designers fear AI will
  normalize dark patterns under the banner of UX optimization** — because an optimizer
  pointed at conversion will find manipulation, and it will find it faster than a human.
  If you let a system optimize choice architecture, constrain it with the §13.4 checklist
  as hard constraints, not preferences.

**Accessibility caution:** AI-generated UI and AI-generated code produce plausible markup
with unreliable semantics. Everything in §9 → `ui-ux-design-systems-platforms-and-accessibility` still has to be verified by a human. Figma's own
framing of its AI outputs is that they still need human review for accessibility, semantics,
and production readiness — take that at face value.

### 14.4 Tooling reality (2026)

Design tooling has moved fast: Figma's **State of the Designer 2026** (survey of 906
designers) reports **72% now use generative AI in their workflows**, with **98% having
increased usage in the past year** and **91% of those saying it improves output quality**,
not just speed. Figma's **Config 2026** introduced code layers on the canvas, design agents,
and an MCP server that lets AI agents operate on the file with real design-system context;
**Penpot** (open-source, self-hostable, native DTCG tokens, CSS-native output) shipped an
MCP server too and is the credible option for regulated or open-source-constrained teams.

**The honest read:** these tools compress production, not judgment. The bottleneck moved
from making screens to knowing which screens to make — which is why the durable content in
§1–§4 → `ui-ux-cognition-heuristics-and-navigation`, `ui-ux-interaction-layout-and-visual-design` and §12 is worth more now, not less.
