---
name: biz-models-strategy-operations-and-financing
description: "Use when reasoning about how a business actually works: business models and unit economics including contribution margin, CAC, LTV and payback and the ways those numbers get misstated, strategy and competitive positioning, operations and organization design, and financing from bootstrapping through venture and debt with the dilution and control consequences. Includes the router for the whole business-marketing-sales-law reference."
---

# Business, Marketing, Sales and Law: Business Models and Unit Economics, Strategy, Operations, and Financing

> **Part 1 of 5** of the *Business, Marketing, Sales and Law* reference (plugin `business-marketing-sales-law`), covering §0–§4. Sibling skills: `biz-marketing-evidence-brand-and-attribution` (§5–§9), `biz-sales-process-qualification-and-negotiation` (§10–§13), `biz-legal-contracts-ip-employment-and-privacy` (§14–§21), `biz-reference` (§22–§26). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Strategy frameworks, contract doctrine and the marketing evidence base are stable. Two areas moved. See §22 → `biz-reference` for marketing measurement after the cookie reversal and the US state privacy patchwork.

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
>    economics is where you find out whether it's true (§1).
> 2. **⚠️ Most marketing folklore is contradicted by the evidence, and the contradictions
>    are consistent across decades and categories.** Loyalty, targeting, differentiation
>    and brand purpose all mean something different empirically than they do in the trade
>    press (§6 → `biz-marketing-evidence-brand-and-attribution`).
> 3. **⚠️ Legal risk is mostly boring and preventable.** Contracts nobody read, IP nobody
>    assigned, contractors who were employees, and privacy obligations nobody checked.
>    **The expensive failures are almost never novel** (§15 → `biz-legal-contracts-ip-employment-and-privacy`).

---

## §0. Routing

| You want... | Go to |
|---|---|
| **Business models and unit economics** | **§1** |
| Strategy and competitive advantage | §2 |
| Operations and org | §3 |
| Financing | §4 |
| Marketing fundamentals | §5 → `biz-marketing-evidence-brand-and-attribution` |
| **What the marketing evidence shows** | **§6 → `biz-marketing-evidence-brand-and-attribution`** |
| Brand and advertising | §7 → `biz-marketing-evidence-brand-and-attribution` |
| **Measurement and attribution** | **§8 → `biz-marketing-evidence-brand-and-attribution`** |
| Channels | §9 → `biz-marketing-evidence-brand-and-attribution` |
| **The sales process** | **§10 → `biz-sales-process-qualification-and-negotiation`** |
| Qualification | §11 → `biz-sales-process-qualification-and-negotiation` |
| **Negotiation** | **§12 → `biz-sales-process-qualification-and-negotiation`** |
| Sales management | §13 → `biz-sales-process-qualification-and-negotiation` |
| **How to think about legal risk** | **§14 → `biz-legal-contracts-ip-employment-and-privacy`, §15 → `biz-legal-contracts-ip-employment-and-privacy`** |
| Contracts | §16 → `biz-legal-contracts-ip-employment-and-privacy` |
| IP | §17 → `biz-legal-contracts-ip-employment-and-privacy` |
| Employment | §18 → `biz-legal-contracts-ip-employment-and-privacy` |
| Privacy | §19 → `biz-legal-contracts-ip-employment-and-privacy` |
| Consumer protection and marketing law | §20 → `biz-legal-contracts-ip-employment-and-privacy` |
| Disputes | §21 → `biz-legal-contracts-ip-employment-and-privacy` |
| **What moved** | **§22 → `biz-reference`** |
| Misconceptions | §23 → `biz-reference` |
| Books | §24 → `biz-reference` |
| Quick reference | §25 → `biz-reference` |

---

# PART I — BUSINESS

---

## §1. Business Models and Unit Economics

**⚠️ The question that matters: for one unit of whatever you sell, do you make more than
it costs to acquire and serve — and how long does it take to find out?**

```
CAC        customer acquisition cost — ⚠️ FULLY loaded: ad spend, sales salaries,
           tooling, and the share of marketing that supports acquisition
LTV        lifetime value — ⚠️ GROSS MARGIN, not revenue, times expected lifetime
LTV:CAC    a common heuristic is 3:1 ⚠️ — but see the gotcha
Payback     ⚠️ months to recover CAC. THE cash-flow-relevant number
Churn       ⚠️ logo vs revenue churn; net revenue retention can exceed 100%
Contribution margin   revenue − variable cost per unit
```
> **⚠️ GOTCHA — the LTV:CAC ratio is the most abused metric in startups, and it is abused
> in a specific way.** ⚠️ **LTV is a forecast — it embeds an assumed lifetime you haven't
> observed yet, and early-cohort retention is systematically better than later cohorts
> because early customers are self-selected enthusiasts.** **A 3:1 ratio built on a
> 5-year assumed life from 8 months of data is a number about your optimism.**
> **⚠️ CAC payback period is the honest metric** — **it's observed, it's in months, and it
> directly determines how much cash you burn to grow.** **Under 12 months is generally
> healthy for B2B SaaS; over 24 means growth consumes capital faster than it produces
> it.**

**⚠️ Model archetypes and what each one's hard constraint is:**
```
Subscription/SaaS   ⚠️ churn is the killer; NRR is the compounding lever
Transactional       ⚠️ repeat rate and margin per transaction
Marketplace         ⚠️ liquidity and the cold-start problem; take rate; DISINTERMEDIATION
Advertising         ⚠️ needs enormous scale before it works at all
Freemium            ⚠️ conversion rate and the cost of serving free users
Services            ⚠️ utilization and rate — scales linearly with headcount
Hardware            ⚠️ working capital and inventory; margins are structurally thinner
```
**⚠️ Fixed vs variable cost structure determines everything about operating leverage**:
**high fixed, low variable (software) means losses until scale then very high margins;
high variable (services, hardware) means margins are roughly constant and growth requires
proportional cost.**

**⚠️ Cash is the constraint, not profit** (see an accounting reference §12): **runway,
burn rate, and the working capital cycle.** ⚠️ **A growing business consumes cash — that
is the normal case, not a warning sign, but it's why growth without financing kills
otherwise healthy companies.**

---

## §2. Strategy

**⚠️ Strategy is choosing what NOT to do.** **A plan that says yes to everything is a
budget, not a strategy.**

**Porter's Five Forces** — supplier power, buyer power, new entrants, substitutes,
rivalry. ⚠️ **Useful as a structured diagnostic, and dated in that it assumes relatively
stable industry boundaries.**
**Generic positions**: cost leadership, differentiation, focus. ⚠️ **Porter's "stuck in the
middle" warning is contested empirically, but the underlying point — that trying to be
cheapest and best simultaneously usually means being neither — holds up.**

**⚠️ Moats, roughly in order of durability:**
```
Network effects      ⚠️ direct, indirect, local. The strongest and rarest
Switching costs      data, integration, workflow, contracts, retraining
Scale economies      ⚠️ real only where fixed costs dominate
Brand                ⚠️ genuine but slow and expensive to build (§7)
Regulatory/IP        ⚠️ durable and expires
Counter-positioning  ⚠️ incumbents CAN'T copy you without damaging their own model
Process/cost         ⚠️ usually the weakest — copyable
```
**⚠️ "First mover advantage" is largely a myth as usually stated** — **the evidence favours
whoever gets the model right, not whoever is earliest.** **What's real is first mover into
a *network effect*, where early scale compounds.**

**⚠️ Jobs to be Done is the most useful reframe here**: **customers hire a product to make
progress in a situation.** **It reorients competitive analysis from product category to
the alternative the customer would otherwise use — often "do nothing" or a spreadsheet.**

---

## §3. Operations and Organization

**⚠️ Constraints and throughput (Goldratt)**: **a system's output is set by its
bottleneck**, ⚠️ **so improving anything else is wasted effort.** **Find the constraint,
exploit it, subordinate everything to it, elevate it, then repeat — because the
constraint moves.**
**Process**: **lean and waste elimination**, **Six Sigma** (⚠️ **variation reduction, and
it can suppress the experimentation a growing business needs**), **queueing theory**
(⚠️ **utilization above ~80% causes wait times to explode nonlinearly — which is why
fully-loaded teams are slower, not faster**).
**Organization**: functional, divisional, matrix; ⚠️ **Conway's law — your product
architecture will mirror your communication structure whether you plan it or not**;
**span of control**; **and Dunbar-style coordination costs meaning that adding people to a
coordination-bound problem slows it down.**

---

## §4. Financing

```
BOOTSTRAP        ⚠️ retain control and full economics; growth limited by cash flow
DEBT             bank, revenue-based, venture debt — ⚠️ no dilution, and it must be repaid
                 regardless of outcome
EQUITY           angel, VC, PE — ⚠️ dilution, control terms, and an EXIT expectation
GRANTS/NON-DIL   R&D credits, grants
```
**⚠️ The venture model is a specific and narrow bet**: **VCs need a small number of
enormous outcomes to return a fund, which means they need companies that can plausibly
become very large.** ⚠️ **A profitable business growing 30% a year is an excellent
business and a poor venture investment, and confusing the two leads founders to raise
money that forces a strategy they didn't want.**
**Terms that matter more than valuation**: **liquidation preference** (⚠️ **participating
vs non-participating changes founder outcomes dramatically in a modest exit**),
**anti-dilution**, **board composition and control**, **pro rata**, **option pool
(⚠️ and whether it's pre- or post-money, which shifts real dilution)**, **vesting and
cliffs.**
⚠️ **Valuation is the number founders negotiate and the terms are what determine
outcomes.**

---

# PART II — MARKETING
