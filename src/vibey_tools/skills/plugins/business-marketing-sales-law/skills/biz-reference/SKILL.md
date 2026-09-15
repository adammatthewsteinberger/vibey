---
name: biz-reference
description: "Use when checking what moved in marketing measurement after the cookie reversal or in the US state privacy patchwork (verified August 2026), correcting a business, marketing, sales or legal misconception, finding the canon, or needing a picker and the checklist to run before signing anything. Companion to the other business-marketing-sales-law skills."
---

# Business, Marketing, Sales and Law: What Moved, Misconceptions, and Canon

> **Part 5 of 5** of the *Business, Marketing, Sales and Law* reference (plugin `business-marketing-sales-law`), covering §22–§26. Sibling skills: `biz-models-strategy-operations-and-financing` (§0–§4), `biz-marketing-evidence-brand-and-attribution` (§5–§9), `biz-sales-process-qualification-and-negotiation` (§10–§13), `biz-legal-contracts-ip-employment-and-privacy` (§14–§21). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Strategy frameworks, contract doctrine and the marketing evidence base are stable. Two areas moved. See §22 below for marketing measurement after the cookie reversal and the US state privacy patchwork.

> **⚠️ Scope.** Complements an economics/accounting/tax reference (which covers economics,
> financial statements, and tax structure). **This is the operating layer.**
> ⚠️ **Part IV is legal orientation, not legal advice** — §15 → `biz-legal-contracts-ip-employment-and-privacy` says exactly what that
> distinction means and where it binds.
>
> **⚠️ GOTCHA** boxes mark received wisdom that the evidence contradicts.
>
> **The three ideas that organize all four domains:**
> 1. **⚠️ A business is a repeatable system for creating more value than it consumes.**
>    Everything else — strategy, marketing, sales — is a mechanism for that, and unit
>    economics is where you find out whether it's true (§1 → `biz-models-strategy-operations-and-financing`).
> 2. **⚠️ Most marketing folklore is contradicted by the evidence, and the contradictions
>    are consistent across decades and categories.** Loyalty, targeting, differentiation
>    and brand purpose all mean something different empirically than they do in the trade
>    press (§6 → `biz-marketing-evidence-brand-and-attribution`).
> 3. **⚠️ Legal risk is mostly boring and preventable.** Contracts nobody read, IP nobody
>    assigned, contractors who were employees, and privacy obligations nobody checked.
>    **The expensive failures are almost never novel** (§15 → `biz-legal-contracts-ip-employment-and-privacy`).

---

## §22. What Moved — verified August 2026

### 22.1 ⚠️ Marketing measurement — the cookie reversal
**⚠️ This is a genuine correction, and a great deal of advice written between 2020 and
2024 was written for a future that did not arrive.**

**What actually happened:**
- **⚠️ Google reversed course. It abandoned full third-party cookie deprecation in July
  2024, and in April 2025 confirmed it would not introduce the user-choice prompt
  either.** ⚠️ **Third-party cookies remain enabled by default in Chrome.**
- **⚠️ In October 2025 Google wound down ten Privacy Sandbox APIs — including the
  Attribution Reporting API — citing low adoption.** **The replacement was retired before
  the thing it was replacing.**

> **⚠️ GOTCHA — and this is the part that matters: the cookie survived, and the
> measurement did not.** ⚠️ **Safari and Firefox have blocked cross-site tracking by
> default for years, and iOS App Tracking Transparency did the rest.** **Reported figures
> vary by source, but the direction is consistent: attribution coverage fell from 90%+ to
> roughly 60–80%, and in some channels to 30–60%.** ⚠️ **So multi-touch attribution
> degraded regardless of Chrome's decision, and "Google reversed it, so nothing changed"
> is exactly the wrong conclusion.**

**⚠️ The practitioner consensus has converged on triangulation rather than a single source
of truth**, in three layers:
```
1. SERVER-SIDE TRACKING   ⚠️ first-party data plus conversion APIs. Recovers a
   meaningful share of lost signal (reported at 20–40% for Meta's CAPI paired with
   the pixel using event deduplication). Table stakes
2. INCREMENTALITY TESTING ⚠️ holdout and geo experiments. The only causal method,
   and in a January 2026 survey of 500 senior US decision-makers it earned the most
   trust of any measurement method — ahead of MMM and well ahead of the in-platform
   reporting most budgets are still steered by
3. MMM  ⚠️ aggregate regression, no personal data, cookie-proof. For budget allocation
```
**⚠️ MMM's revival is real and the reason is access, not method.** **The technique dates
from the 1960s and was gated behind six-figure consulting engagements.** ⚠️ **Google
open-sourced Meridian (January 2025), Meta maintains Robyn, and PyMC Labs ships
PyMC-Marketing** — **so any team with roughly two years of weekly spend and outcome data
can now run one in-house.**

**⚠️ The honest caveat**: **the IAB's State of Data 2026, surveying 400+ senior planning
and analytics decision-makers, found three in four marketers saying their existing
measurement — attribution, incrementality and MMM alike — is not delivering the speed,
accuracy or trust they need.** ⚠️ **The methods are understood; the data layer beneath
them eroded.** **Nobody has fully solved this, and claims otherwise are sales.**

### 22.2 ⚠️ The US state privacy patchwork
**⚠️ There is still no comprehensive US federal privacy law** — **the American Privacy
Rights Act expired without a vote** — **so states have filled the gap individually.**

> **⚠️ GOTCHA — sources disagree on the count, and I am not going to pretend otherwise.**
> ⚠️ **Most sources checking mid-2026 say **20 states** have comprehensive laws in
> effect** — with **Indiana, Kentucky and Rhode Island** the newest, all effective
> **1 January 2026** — **and citing the IAPP tracker.** **Some say 19; at least one
> reports the landscape expanded from 20 to 24 during 2026 following a further
> legislative wave.**
> ⚠️ **The discrepancy is partly definitional — enacted versus in effect, and whether
> Florida's narrower law counts — and partly that it is genuinely moving.**
> **⚠️ Check the IAPP US State Privacy Legislation Tracker for the current number; do not
> rely on any secondary source including this one for the count.**

**⚠️ What is consistent across sources, and more useful than the count:**
- **Most laws follow the Virginia template**: **opt-out for ordinary data, opt-in for
  sensitive data, AG-only enforcement.** ⚠️ **California is the outlier with a dedicated
  regulator (CPPA) and the only private right of action, for breaches.**
- **⚠️ Thresholds vary and are lower than small businesses assume**: **commonly 100,000
  consumers, but Rhode Island covers 35,000 (or 10,000 if >20% of revenue comes from
  selling data), and Texas has NO revenue threshold — it applies to any covered business
  not classified as a small business by the SBA.**
- **⚠️ Cure periods are disappearing** — **California and Colorado no longer provide them,
  and Rhode Island launched without one.** **The grace period era is ending.**
- **⚠️ Universal opt-out signals are now the leading enforcement theme, and the reason is
  testability**: **a reported twelve states require honouring Global Privacy Control**,
  and ⚠️ **an enforcer can simply load your site with the signal on and watch what
  happens.** **No subpoena required.**
- **⚠️ Enforcement is no longer light** — **a $2.75 million CCPA settlement was announced
  in February 2026, reported as the largest to date, over alleged opt-out failures.**

**⚠️ The practical read for a small business**: **you likely fall below most thresholds —
but "we're too small" is not a safe conclusion**, because ⚠️ **sectoral laws, marketing
laws (§20 → `biz-legal-contracts-ip-employment-and-privacy`), and your vendors' obligations reach you anyway**, and **the §19 → `biz-legal-contracts-ip-employment-and-privacy` baseline is
worth doing regardless of which statute technically applies.**

---

## §23. Misconceptions

| Misconception | Correction |
|---|---|
| LTV:CAC of 3:1 means the model works | ⚠️ **LTV is a forecast. Use CAC payback** (§1 → `biz-models-strategy-operations-and-financing`) |
| Loyalty drives market share | ⚠️ **Double jeopardy — share largely drives loyalty** (§6 → `biz-marketing-evidence-brand-and-attribution`) |
| Focus on your heavy users | ⚠️ **Light buyers dominate volume** (§6 → `biz-marketing-evidence-brand-and-attribution`) |
| Differentiation is what matters | ⚠️ **Distinctiveness matters more** (§6 → `biz-marketing-evidence-brand-and-attribution`) |
| Narrow targeting is efficient | ⚠️ **Your future customers mostly don't buy you yet** (§6 → `biz-marketing-evidence-brand-and-attribution`) |
| Brand purpose drives purchase | ⚠️ **Weak evidence in actual behaviour** (§6 → `biz-marketing-evidence-brand-and-attribution`) |
| Performance marketing is more effective because it's measurable | ⚠️ **Measurability biases spend toward activation** (§6 → `biz-marketing-evidence-brand-and-attribution`, §8 → `biz-marketing-evidence-brand-and-attribution`) |
| Platform-reported conversions are measurement | ⚠️ **They mark their own homework and double-count** (§8 → `biz-marketing-evidence-brand-and-attribution`) |
| Retargeting drives the conversions attributed to it | ⚠️ **It harvests existing intent** (§8 → `biz-marketing-evidence-brand-and-attribution`) |
| Google reversed cookie deprecation so nothing changed | ⚠️ **Coverage fell anyway via Safari/Firefox/ATT** (§22.1) |
| First mover advantage is real | ⚠️ **Only into network effects** (§2 → `biz-models-strategy-operations-and-financing`) |
| Strategy is a plan | ⚠️ **It's choosing what not to do** (§2 → `biz-models-strategy-operations-and-financing`) |
| A VC-fundable business and a good business are the same | ⚠️ **Different bets entirely** (§4 → `biz-models-strategy-operations-and-financing`) |
| Valuation is the key term | ⚠️ **Liquidation preference and control matter more** (§4 → `biz-models-strategy-operations-and-financing`) |
| Higher utilization means more output | ⚠️ **Above ~80%, queues explode** (§3 → `biz-models-strategy-operations-and-financing`) |
| Enthusiasm from a contact means a champion | ⚠️ **A champion advocates when you're absent** (§11 → `biz-sales-process-qualification-and-negotiation`) |
| Deals are lost to competitors | ⚠️ **Most B2B deals are lost to no decision** (§10 → `biz-sales-process-qualification-and-negotiation`) |
| Discounting closes the deal | ⚠️ **It resets renewal price and teaches waiting** (§12 → `biz-sales-process-qualification-and-negotiation`) |
| Contractors' work belongs to you | ⚠️ **Not without written assignment** (§17 → `biz-legal-contracts-ip-employment-and-privacy`) |
| You can choose contractor vs employee | ⚠️ **It's a legal test, not a label** (§18 → `biz-legal-contracts-ip-employment-and-privacy`) |
| Non-competes are enforceable | ⚠️ **Highly jurisdiction-dependent; often not** (§18 → `biz-legal-contracts-ip-employment-and-privacy`) |
| Consent is the standard privacy basis | ⚠️ **One of six, and often the wrong one** (§19 → `biz-legal-contracts-ip-employment-and-privacy`) |
| We're too small for privacy law | ⚠️ **Thresholds are lower than assumed; other layers reach you** (§22.2) |
| A privacy policy is a formality | ⚠️ **Describing what you don't do is itself a violation** (§19 → `biz-legal-contracts-ip-employment-and-privacy`) |
| Winning a judgment means getting paid | ⚠️ **Collection is a separate problem** (§21 → `biz-legal-contracts-ip-employment-and-privacy`) |

---

## §24. Books

**Business and strategy**
| Author | Work | Why |
|---|---|---|
| **Rumelt** | ***Good Strategy / Bad Strategy*** | ⚠️ **The best book on what strategy actually is** |
| **Porter** | *Competitive Strategy* | The canonical framework |
| **Christensen** | *The Innovator's Dilemma* / *Competing Against Luck* | Disruption and JTBD |
| **Goldratt** | *The Goal* | ⚠️ **§3 → `biz-models-strategy-operations-and-financing`'s constraint thinking, as a novel** |
| **Thiel** | *Zero to One* | ⚠️ **Opinionated and worth arguing with** |
| **Feld & Mendelson** | ***Venture Deals*** | ⚠️ **§4 → `biz-models-strategy-operations-and-financing`. The terms explained honestly** |

**Marketing**
| **Sharp** | ***How Brands Grow*** | ⚠️ **§6 → `biz-marketing-evidence-brand-and-attribution`. The evidence base. Read this before any other marketing book** |
| **Binet & Field** | ***The Long and the Short of It*** | ⚠️ **§6 → `biz-marketing-evidence-brand-and-attribution`'s 60/40 and effectiveness evidence** |
| **Ries & Trout** | *Positioning* | Dated, foundational |
| **Kahneman** | *Thinking, Fast and Slow* | Consumer behaviour underpinnings |

**Sales and negotiation**
| **Dixon & Adamson** | *The Challenger Sale* | ⚠️ **Data-driven, and its claims are contested — read the critiques** |
| **Fisher & Ury** | ***Getting to Yes*** | ⚠️ **§12 → `biz-sales-process-qualification-and-negotiation`. Still the best starting point** |
| **Voss** | *Never Split the Difference* | Tactical, entertaining, ⚠️ less evidence-based |
| **Roughgarden / Ury** | *Getting Past No* | Difficult counterparties |

**Law** — ⚠️ **primary sources and a lawyer beat books here**, but: **Nolo's small
business titles** are unusually good plain-English orientation, **the IAPP** for privacy,
**your national IP office** for trademarks and patents, and ⚠️ **the FTC's business
guidance** for §20 → `biz-legal-contracts-ip-employment-and-privacy`, which is free and clearer than most paid material.

---

## §25. Quick Reference

### 25.1 Picker
| Question | Where |
|---|---|
| Is this business model viable? | ⚠️ **CAC payback, contribution margin** (§1 → `biz-models-strategy-operations-and-financing`) |
| Do we have a defensible position? | **Moat type and durability** (§2 → `biz-models-strategy-operations-and-financing`) |
| Why is everything slow? | ⚠️ **Find the constraint; check utilization** (§3 → `biz-models-strategy-operations-and-financing`) |
| Should we raise venture capital? | ⚠️ **Only if the outcome shape fits** (§4 → `biz-models-strategy-operations-and-financing`) |
| How should we price? | ⚠️ **Value-based, anchored on customer economics** (§5 → `biz-marketing-evidence-brand-and-attribution`) |
| Should we target narrowly? | ⚠️ **Usually not — reach category buyers** (§6 → `biz-marketing-evidence-brand-and-attribution`) |
| Is our advertising working? | ⚠️ **Incrementality test. Not the platform dashboard** (§8 → `biz-marketing-evidence-brand-and-attribution`, §22.1) |
| How do we allocate budget across channels? | **MMM** (§8 → `biz-marketing-evidence-brand-and-attribution`, §22.1) |
| Why do deals stall? | ⚠️ **Decision process and cost of inaction** (§10 → `biz-sales-process-qualification-and-negotiation`, §11 → `biz-sales-process-qualification-and-negotiation`) |
| How do we improve terms? | ⚠️ **Improve your BATNA** (§12 → `biz-sales-process-qualification-and-negotiation`) |
| Contractor built our product — do we own it? | ⚠️ **Only with written assignment** (§17 → `biz-legal-contracts-ip-employment-and-privacy`) |
| Is this person a contractor? | ⚠️ **It's a test — check it** (§18 → `biz-legal-contracts-ip-employment-and-privacy`) |
| Does privacy law apply to us? | ⚠️ **Check thresholds; do the baseline anyway** (§19 → `biz-legal-contracts-ip-employment-and-privacy`, §22.2) |
| Can we make this claim in an ad? | ⚠️ **Substantiate before, not after** (§20 → `biz-legal-contracts-ip-employment-and-privacy`) |
| Should we sue? | ⚠️ **Cost, time, collectability, attention** (§21 → `biz-legal-contracts-ip-employment-and-privacy`) |

### 25.2 Before you sign anything
- [ ] ⚠️ **Limitation of liability — is it capped, and are consequential damages excluded?** (§16 → `biz-legal-contracts-ip-employment-and-privacy`)
- [ ] ⚠️ **Indemnity — what am I agreeing to defend, and is it capped?** (§16 → `biz-legal-contracts-ip-employment-and-privacy`)
- [ ] IP ownership stated explicitly? (§16 → `biz-legal-contracts-ip-employment-and-privacy`, §17 → `biz-legal-contracts-ip-employment-and-privacy`)
- [ ] Auto-renewal and notice period? (§16 → `biz-legal-contracts-ip-employment-and-privacy`)
- [ ] Termination rights — mine as well as theirs? (§16 → `biz-legal-contracts-ip-employment-and-privacy`)
- [ ] Governing law and venue — could I realistically enforce this? (§16 → `biz-legal-contracts-ip-employment-and-privacy`)
- [ ] Payment terms and what triggers the obligation? (§16 → `biz-legal-contracts-ip-employment-and-privacy`)
- [ ] Does this conflict with an agreement I've already signed? (§16 → `biz-legal-contracts-ip-employment-and-privacy`)
- [ ] ⚠️ **If material: has a lawyer read it?** (§14 → `biz-legal-contracts-ip-employment-and-privacy`)

---

## §26. Method

**§1–§5 → `biz-models-strategy-operations-and-financing`, `biz-marketing-evidence-brand-and-attribution`, §7 → `biz-marketing-evidence-brand-and-attribution`, §9–§21 → `biz-marketing-evidence-brand-and-attribution`, `biz-sales-process-qualification-and-negotiation`, `biz-legal-contracts-ip-employment-and-privacy` rest on stable material** — **strategy frameworks, contract doctrine,
IP categories, the employment classification tests, and the Ehrenberg-Bass and Binet &
Field marketing evidence** — sourced from §24. ⚠️ **None of it needed verification.**

**Two searches were run in August 2026**, on **marketing measurement** and **the US state
privacy landscape** — ⚠️ **the two areas where a 2024-vintage answer would now be
actively wrong.**

**Confidence.** **High** in §1–§5 → `biz-models-strategy-operations-and-financing`, `biz-marketing-evidence-brand-and-attribution` and §9–§21 → `biz-marketing-evidence-brand-and-attribution`, `biz-sales-process-qualification-and-negotiation`, `biz-legal-contracts-ip-employment-and-privacy`. **High in §6 → `biz-marketing-evidence-brand-and-attribution`**, which is the section I'd most
want read: ⚠️ **the Ehrenberg-Bass findings — double jeopardy, light-buyer dominance,
distinctiveness over differentiation, the limits of loyalty — are empirical
generalizations replicated across categories and decades, and they contradict a great deal
of what the marketing industry sells.** **I've flagged their scope limits honestly: they
are strongest for established consumer categories and weakest for genuinely new products
and small niche markets.**

**High** in §22.1's facts. ⚠️ **The Google reversal sequence — deprecation abandoned July
2024, user-choice prompt dropped April 2025, ten Privacy Sandbox APIs including
Attribution Reporting retired October 2025 — is consistent across many independent
sources.** **The important interpretive point is mine and I think it's right: the cookie
survived and the measurement didn't, so "nothing changed" is the wrong reading.**
⚠️ **Coverage figures (90%+ down to 60–80%, or 30–60% in some channels) and CAPI recovery
rates (20–40%) vary by source and I've presented them as ranges rather than facts.**

⚠️ **§22.2 has an explicit disagreement I have not resolved, and I'd rather flag it than
pick.** **Most mid-2026 sources say 20 states with comprehensive laws in effect, citing
the IAPP tracker; one says 19; one reports expansion to 24 during 2026.** **The
discrepancy appears partly definitional (enacted vs in effect; whether Florida's narrower
law counts) and partly that the count genuinely moves.** ⚠️ **I've pointed at the IAPP
tracker as the primary source and told you not to rely on the number in this document —
including the structural facts, which are far better attested than the count and are the
part that actually affects decisions.**

⚠️ **A sourcing caution across both subsections**: **much of the marketing-measurement and
privacy-compliance material online is published by vendors selling measurement platforms
or consent-management tools**, and the framing tends toward urgency. **The underlying
facts recur across enough independent sources to be reliable; the "act now" framing is
marketing wrapped around correct technical content** — ⚠️ **which is itself a §6 → `biz-marketing-evidence-brand-and-attribution` lesson.**
