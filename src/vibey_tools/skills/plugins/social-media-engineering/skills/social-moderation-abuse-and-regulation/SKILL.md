---
name: social-moderation-abuse-and-regulation
description: "Use when handling harmful content or a compliance requirement: moderation at scale (classifiers, human review queues, appeals, policy design, reviewer welfare), spam, bots and abuse engineering (rate limits, reputation, coordinated behaviour detection, account takeover), and the regulatory layer — the DSA, the Online Safety Act, age assurance and where enforcement is actually landing."
---

# Social Media Engineering: Moderation at Scale, Spam and Abuse, and Regulation

> **Part 3 of 5** of the *Social Media Engineering* reference (plugin `social-media-engineering`), covering §7–§9. Sibling skills: `social-platform-apis-and-open-protocols` (§0–§2), `social-feed-graph-ranking-and-notifications` (§3–§6), `social-media-analytics-privacy-and-presence` (§10–§13), `social-reference` (§14–§19). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Verified August 2026. See §16 → `social-reference` for the currency snapshot and what goes stale first.

> **How to read this.** The title spans two things and this document covers both, weighted
> toward the first: **§1–§12 → `social-platform-apis-and-open-protocols`, `social-feed-graph-ranking-and-notifications`, `social-media-analytics-privacy-and-presence` are about building and integrating with social systems;
> §13 → `social-media-analytics-privacy-and-presence` is about your own presence as a developer.** Skip to §13 → `social-media-analytics-privacy-and-presence` if that's what you came for.
>
> Three markers:
> - **[DURABLE]** — architecture, ranking, moderation, and abuse dynamics. Most of §2–§10 → `social-platform-apis-and-open-protocols`, `social-feed-graph-ranking-and-notifications`, `social-media-analytics-privacy-and-presence`.
> - **[VERSIONED]** — platform terms, pricing, protocols, regulation. ⚠️ **Verify all of
>   it; this is the fastest-moving material in the collection after AI.**
> - **[CONTESTED]** — genuine disagreement.
>
> **⚠️ GOTCHA** boxes mark what breaks, gets you banned, or gets you fined.
>
> **The three framings that organize everything below:**
> 1. **⚠️ Building on a platform API is building on rented land, and the rent changed.**
>    The 2023–2026 period established that platforms will reprice or withdraw access with
>    weeks of notice and no obligation. **Architect for that from day one** (§1 → `social-platform-apis-and-open-protocols`).
> 2. **The hard problems are social, not technical.** Fan-out and ranking are solved
>    engineering; **moderation, abuse, and incentive design are not, and they scale
>    worse than your database does** (§7, §8).
> 3. **⚠️ Compliance is now an architecture input, not a legal afterthought.** Age
>    assurance, transparency reporting, and appeals mechanisms have to be designed in —
>    **and regulators have started saying explicitly that self-declaration is not
>    sufficient** (§9).

---

## §7. Moderation at Scale

**[DURABLE] The hardest problem in this document, and the one engineering can only
partially address.**

**The layered pipeline everyone converges on:**
```
1. PREVENTION      rate limits, friction, account age gates, verification
2. AUTOMATED       hash matching (PhotoDNA/CSAM, known-violating media),
                   classifiers, heuristics
3. USER REPORTING  with abuse-of-reporting handling and prioritization
4. HUMAN REVIEW    queues, tooling, escalation
5. APPEALS         ⚠️ now legally required in the EU (§9)
6. TRANSPARENCY    reporting, also legally required
```

**⚠️ The realities that break naive designs:**
- **Scale**: at any real volume, human review of everything is impossible and automation
  alone is inadequate. **You will build a triage system, so design it deliberately.**
- **Context**: the same words are abuse or reclamation depending on speaker, audience, and
  history. ⚠️ **Classifiers do not have that context.**
- **Adversaries adapt** — every filter is a spec for evading it (§8).
- **⚠️ Reviewer welfare is a real duty of care.** Exposure to violent and abusive content
  causes documented psychological harm; **rotation, counselling, blurring by default and
  volume limits are not optional if you employ or contract reviewers.**
- **Cultural and linguistic coverage** — ⚠️ **most systems are dramatically weaker outside
  English, and this is where the most serious real-world harms have occurred.**
- **False positives have real costs** to real people, and appeals must actually work.

**[DURABLE] The structural point**: **CSAM detection has legal mandatory-reporting
obligations** (NCMEC in the US) and hash-matching participation is effectively expected;
**terrorism and violent extremism have their own regimes**; and ⚠️ **"we're too small to
need moderation" stops being true the moment you're large enough to be worth abusing —
which is much sooner than most teams plan for.**

---

## §8. Spam, Bots, and Abuse

**[DURABLE] Adversarial engineering — assume a motivated opponent who reads your
documentation.**

**The attack surface**: bulk account creation, **coordinated inauthentic behaviour**
(⚠️ **the hard one — individually plausible accounts acting in concert**), engagement
farming, scraping (see a web-scraping reference), impersonation, phishing in DMs, spam in
replies and mentions, **brigading and targeted harassment**, and vote or metric
manipulation.

**Defences, roughly in order of value**: **friction at signup** (email/phone verification,
⚠️ **and an awareness that this trades against accessibility and privacy**),
**rate limiting per account, per IP, per device, and per behaviour pattern**,
**behavioural signals over content signals** (⚠️ **timing, sequence, and network structure
are much harder to fake than text**), **graph analysis for coordination** — clusters
behaving identically are the signal — **device and browser fingerprinting** (privacy
trade-off, and increasingly regulated), **shadow-limiting rather than hard blocking**
(⚠️ **so the adversary doesn't learn immediately that they were caught — though this is
ethically contested when applied to real users**), and **reputation systems that decay.**

**⚠️ And the AI-era additions**: **generated content at volume is cheap now**, which breaks
detection heuristics built on "does this look human-written"; **and provenance signals
(C2PA and similar) are the direction of travel** but not yet dependable.

---

## §9. Regulation and Compliance

**[VERSIONED — and this now determines what you may ship.]**

### 9.1 The regimes

**EU Digital Services Act.** ⚠️ **Applies if you operate in the EU or have a "substantial
connection" to it — headquarters elsewhere does not exempt you**, and non-EU providers must
nominate a legal representative. **Enforcement is split: the Commission handles VLOPs;
national Digital Services Coordinators handle everyone else.** Obligations include
**user-friendly illegal-content reporting, a ban on targeted advertising to minors,
statements of reasons when content is restricted, an internal appeals system, annual
transparency reporting, and law-enforcement notification** for potential criminal activity.

**UK Online Safety Act.** ⚠️ **"Highly effective age assurance" required from July 2025**
for services exposing under-18s to harmful content. **Ofcom accepts photo-ID matching,
facial age estimation, Open Banking, digital identity services, and mobile-network
checks** — ⚠️ **self-declaration alone is explicitly not sufficient.** Penalties reach
**up to 10% of global turnover.**

**US**: no federal age-verification law as of mid-2026, but **more than a dozen states have
enacted requirements**. **Australia** has an active regime with penalties up to
**AUD $49.5M**.

### 9.2 ⚠️ Enforcement is real and it's landing on age assurance

**This is the part that has changed most**, and the direction is unambiguous:
- **The UK ICO fined Reddit £14.5 million** in early 2026 for failing to adequately protect
  children's data and **relying heavily on self-declaration.**
- **Ofcom has fined adult sites** for lacking "highly effective" age assurance.
- **The Commission preliminarily found Meta in breach** (April 2026) for failing to prevent
  under-13s accessing Facebook, and **preliminarily found TikTok in breach** over minors'
  account safety.
- **Snapchat's self-declaration approach was deemed insufficient** in an investigation that
  began as a Dutch inquiry and was taken over at EU level.

> **⚠️ GOTCHA — the message regulators are sending, stated plainly: passive age gates are
> no longer acceptable.** Emerging enforcement shows **the inadequacy of age-assurance
> methods based on self-declaration and age estimation rather than verification.**
> ⚠️ **If your compliance plan is a "are you over 13?" checkbox, it is already behind.**
>
> **And note the compounding problem**: platforms operating across the EU and UK
> **face overlapping obligations and must satisfy whichever standard is stricter on each
> surface.**

### 9.3 Where it's heading
**The EU Digital Identity Wallet** is required to be operational by **31 December 2026**,
with the Commission developing an **interim age-verification solution** in the meantime.
⚠️ **A structural proposal worth watching: shifting age verification to the operating
system**, so a device verifies once and passes an age signal to apps — **Colorado
legislators have considered exactly this.** If that model wins, it changes the integration
problem entirely.

**[DURABLE] What to build regardless**: **an appeals mechanism that works**,
**transparency reporting infrastructure** (⚠️ **you cannot retrofit the data collection**),
**statements of reasons attached to enforcement actions**, **documented risk assessments**,
**and age-assurance that doesn't require you to store identity documents** — ⚠️ **receive a
token and an audit ID, not a passport scan, or you have created a much worse liability than
the one you were solving.**
