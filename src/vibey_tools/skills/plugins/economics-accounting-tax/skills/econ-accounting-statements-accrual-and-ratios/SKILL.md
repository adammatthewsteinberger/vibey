---
name: econ-accounting-statements-accrual-and-ratios
description: "Use when reading or preparing financial statements: double-entry bookkeeping and why the identity holds, the three statements and how they articulate, accrual accounting and revenue recognition including the timing judgements, the judgement-heavy areas where the numbers are most malleable, and ratio analysis with the interpretation traps."
---

# Economics, Accounting and Tax: Double-Entry, the Three Statements, Accrual Accounting, and Ratio Analysis

> **Part 3 of 5** of the *Economics, Accounting and Tax* reference (plugin `economics-accounting-tax`), covering §10–§14. Sibling skills: `econ-methodology-and-microeconomics` (§0–§4), `econ-macroeconomics-money-and-behavioural` (§5–§9), `econ-gaap-ifrs-audit-and-tax` (§15–§19), `econ-reference` (§20–§24). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Double-entry dates from 1494 and the accounting identities are arithmetic; tax rules change annually and vary by jurisdiction. See §21 → `econ-reference` for IFRS 18 and US Section 174.

> **⚠️ Scope and a necessary caution.** This is an explanatory reference for
> understanding financial and economic material. ⚠️ **It is not accounting, tax, legal or
> investment advice.** **Tax rules in particular are jurisdiction-specific, change every
> year, and turn on facts I can't see** — §17 → `econ-gaap-ifrs-audit-and-tax` explains why I've kept specific figures
> deliberately sparse.
>
> **⚠️ GOTCHA** boxes mark misconceptions and places where the accounting or the economics
> is counterintuitive.
>
> **The three ideas that organize all three subjects:**
> 1. **⚠️ Economics is not physics, and pretending otherwise is the field's characteristic
>    error.** Its core mechanisms are well-attested; many of its empirical magnitudes are
>    genuinely contested. **§1 → `econ-methodology-and-microeconomics` is deliberately about epistemics before content.**
> 2. **⚠️ Accounting is a closed arithmetic system, and that's its power.** Double-entry
>    means the books balance by construction, so errors surface as imbalances. **Every
>    transaction has two sides, and the three statements are three views of one reality**
>    (§10, §11).
> 3. **⚠️ Profit is an opinion, cash is a fact.** Accrual accounting requires estimates —
>    useful life, collectability, completion. **A company can be profitable and insolvent,
>    and this combination has killed many of them** (§12).

---

## §10. Double-Entry

**⚠️ Pacioli codified it in 1494 and nothing fundamental has changed, because it's
arithmetic.**
```
ASSETS = LIABILITIES + EQUITY
```
**⚠️ Every transaction affects at least two accounts, and the identity holds after every
one.** **That's not a convention — it's what makes the system self-checking.**
```
              DEBIT        CREDIT
Assets        increase     decrease
Liabilities   decrease     increase
Equity        decrease     increase
Revenue       decrease     increase
Expenses      increase     decrease
```
**⚠️ "Debit" and "credit" mean left and right. They do not mean good and bad, or increase
and decrease.** ⚠️ **The confusion with bank statements is because your bank describes the
transaction from ITS books — your deposit is a liability to them, so they credit it.**

**The expanded identity** — `Assets = Liabilities + Contributed Capital + Retained
Earnings`, and ⚠️ **retained earnings is where the income statement connects to the
balance sheet: `RE_end = RE_begin + Net Income − Dividends`.** **That single line is the
hinge of the whole system** (§11).

---

## §11. The Three Statements

```
INCOME STATEMENT   ⚠️ performance over a PERIOD
  Revenue − COGS = Gross profit
  − Operating expenses = Operating income (EBIT)
  − Interest − Tax = Net income

BALANCE SHEET      ⚠️ position at a POINT IN TIME
  Assets (current, non-current) = Liabilities + Equity

CASH FLOW          ⚠️ cash movement over a PERIOD, in three sections
  Operating (CFO) + Investing (CFI) + Financing (CFF) = Δ Cash
```
> **⚠️ GOTCHA — the three statements are three views of one reality and they are wired
> together. Understanding the wiring is what separates reading financials from
> understanding them:**
> ```
> Net income → retained earnings (balance sheet) AND top of the cash flow statement
> Depreciation → reduces net income, ⚠️ ADDED BACK in CFO (non-cash), reduces PP&E
> Working capital changes → CFO
> Capex → CFI and increases PP&E
> Debt/equity issuance → CFF and the balance sheet
> ⚠️ Ending cash on the cash flow statement IS the cash line on the balance sheet
> ```
> ⚠️ **If a model's balance sheet doesn't balance, the error is almost always a missing
> link here.**

**⚠️ The indirect method of preparing CFO confuses people**: it **starts from net income
and reverses out non-cash items and working capital changes** to get back to cash.
⚠️ **Increases in receivables and inventory are subtracted (cash tied up); increases in
payables are added (cash retained).** **It's a reconciliation, not a measurement.**

---

## §12. Accrual Accounting and Revenue Recognition

**⚠️ Accrual recognizes revenue when earned and expenses when incurred, regardless of when
cash moves.** **Cash-basis accounting does the opposite and is simpler and less
informative.**
**Matching principle**: recognize expenses in the period of the revenue they generate.

> **⚠️ GOTCHA — profit is an opinion, cash is a fact, and this is not a cynicism.**
> ⚠️ **Accrual accounting requires estimates: useful lives, bad debt, warranty provisions,
> percentage of completion, inventory obsolescence.** **Every one is a judgement, and
> judgements can be stretched.**
> **⚠️ A company can report profits while running out of cash — this is the classic growth
> failure mode**: sales grow, receivables and inventory absorb cash faster than profit
> generates it, and the company becomes insolvent while profitable. ⚠️ **Always read the
> cash flow statement alongside the income statement, and be suspicious when net income
> and CFO diverge persistently.**

**Revenue recognition (ASC 606 / IFRS 15) — the five-step model, now converged:**
```
1. Identify the contract
2. Identify performance obligations       ⚠️ distinct goods/services
3. Determine the transaction price        ⚠️ including variable consideration
4. Allocate to performance obligations    ⚠️ by standalone selling price
5. Recognize revenue as obligations are satisfied  (point in time or over time)
```
**⚠️ Why this matters for software and subscription businesses specifically**: **a
multi-year contract signed today is not revenue today.** ⚠️ **Cash received in advance is
DEFERRED REVENUE — a liability, because you owe the service.** **This is why bookings,
billings, revenue and cash are four different numbers, and why conflating them is the
most common error in SaaS discussion.**

---

## §13. The Judgement-Heavy Areas

**⚠️ These are where accounting policy choices meaningfully change reported results.**

**Inventory**: **FIFO**, **weighted average**, ⚠️ **LIFO — permitted under US GAAP,
PROHIBITED under IFRS**, and **in inflation LIFO raises COGS and lowers reported profit
and tax.** ⚠️ **Lower of cost or net realizable value; IFRS permits reversal of
write-downs, US GAAP generally does not.**

**Depreciation and amortization**: straight-line, declining balance, units of production.
⚠️ **Useful life and salvage value are estimates, and changing them changes profit
immediately.** **Impairment when carrying value exceeds recoverable amount** —
⚠️ **and IFRS allows reversal of impairments (other than goodwill) while US GAAP does
not.**

**⚠️ Leases (ASC 842 / IFRS 16)** — **the big change of recent years: operating leases
came onto the balance sheet as a right-of-use asset and a lease liability.** ⚠️ **Before
this, lease obligations were a major source of hidden leverage, and comparisons across the
transition are not like-for-like.**

**Intangibles** — ⚠️ **the area with the largest gap between accounting and economics:**
**purchased intangibles and goodwill are capitalized; internally generated ones generally
are not.** ⚠️ **So a company that builds its brand and software expenses it, while a
company that buys the same thing capitalizes it — and the balance sheets are not
comparable.** **IFRS permits capitalizing development costs meeting criteria; US GAAP is
more restrictive outside software.**
⚠️ **This is why book value has become progressively less informative for
intangible-intensive businesses**, and why price-to-book comparisons across eras mislead.

**Also**: **provisions and contingencies** (⚠️ **recognition thresholds differ: "probable"
means roughly >50% under IFRS and a higher bar under US GAAP — the same word, different
meanings**), **share-based compensation** (⚠️ **a real expense, and "adjusted" figures
that exclude it are excluding a genuine cost of employing people**), **consolidation**,
**fair value hierarchy** (⚠️ **Level 3 is model-based and unobservable — read those
disclosures**).

---

## §14. Ratio Analysis

```
PROFITABILITY
Gross margin · Operating margin · Net margin
ROA = NI/Assets · ROE = NI/Equity · ⚠️ ROIC = NOPAT/Invested Capital
⚠️ DuPont: ROE = Margin × Asset Turnover × Leverage — decompose before concluding

LIQUIDITY
Current ratio · Quick ratio (⚠️ excludes inventory) · ⚠️ Cash conversion cycle
   = DSO + DIO − DPO   ⚠️ can be NEGATIVE, which is a structural advantage

LEVERAGE
Debt/Equity · Net debt/EBITDA · ⚠️ Interest coverage = EBIT/Interest

EFFICIENCY
Asset turnover · Inventory turnover · Receivables turnover

VALUATION
P/E · EV/EBITDA (⚠️ capital-structure neutral, which is why acquirers use it) ·
P/B · FCF yield
```
> **⚠️ GOTCHA — DuPont is the analytical move most people skip.** ⚠️ **High ROE from thin
> margins and heavy leverage is a completely different business from high ROE on fat
> margins and no debt, and the headline number cannot distinguish them.** **Always
> decompose.**

**⚠️ EBITDA warnings, because it is the most abused metric in finance**: **it is not a
GAAP measure, it is not cash flow, and Munger's objection is the right one — it excludes
depreciation, which for a capital-intensive business is a real economic cost of staying in
operation.** ⚠️ **"Adjusted EBITDA" is worse: check every adjustment, and treat recurring
"one-off" items as recurring.**
**⚠️ Ratios are only meaningful against something** — the same company over time, a close
peer, or an industry norm. **A current ratio of 1.2 is fine for a supermarket and alarming
for a shipbuilder.**
