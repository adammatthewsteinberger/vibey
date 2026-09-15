---
name: econ-reference
description: "Use when correcting an economics or accounting misconception, checking what moved (IFRS 18 as the biggest presentation change in decades, and the restoration of US Section 174 R&D expensing, verified August 2026), finding the canon, or needing the order that works for reading financial statements, the red flags, and a picker. Companion to the other economics-accounting-tax skills."
---

# Economics, Accounting and Tax: Misconceptions, What Moved, and Canon

> **Part 5 of 5** of the *Economics, Accounting and Tax* reference (plugin `economics-accounting-tax`), covering §20–§24. Sibling skills: `econ-methodology-and-microeconomics` (§0–§4), `econ-macroeconomics-money-and-behavioural` (§5–§9), `econ-accounting-statements-accrual-and-ratios` (§10–§14), `econ-gaap-ifrs-audit-and-tax` (§15–§19). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Double-entry dates from 1494 and the accounting identities are arithmetic; tax rules change annually and vary by jurisdiction. See §21 below for IFRS 18 and US Section 174.

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
>    (§10 → `econ-accounting-statements-accrual-and-ratios`, §11 → `econ-accounting-statements-accrual-and-ratios`).
> 3. **⚠️ Profit is an opinion, cash is a fact.** Accrual accounting requires estimates —
>    useful life, collectability, completion. **A company can be profitable and insolvent,
>    and this combination has killed many of them** (§12 → `econ-accounting-statements-accrual-and-ratios`).

---

## §20. Misconceptions

| Misconception | Correction |
|---|---|
| Economics predicts like physics | ⚠️ **Different inference problem, different reliability. §1 → `econ-methodology-and-microeconomics`'s gradient** |
| A model result is a finding | ⚠️ **It's a consequence of assumptions** (§1 → `econ-methodology-and-microeconomics`) |
| Whoever pays a tax bears it | ⚠️ **Incidence falls on the inelastic side** (§2 → `econ-methodology-and-microeconomics`) |
| "Efficient" means good | ⚠️ **Technical term; says nothing about distribution** (§1 → `econ-methodology-and-microeconomics`) |
| Minimum wage always reduces employment | ⚠️ **Monopsony changes the prediction; the evidence is contested** (§3 → `econ-methodology-and-microeconomics`) |
| Trade is bad because factories closed | ⚠️ **Aggregate gains, concentrated losses — both are true** (§8 → `econ-macroeconomics-money-and-behavioural`) |
| Comparative advantage needs absolute advantage | ⚠️ **No — that's the whole point** (§8 → `econ-macroeconomics-money-and-behavioural`) |
| Banks lend out deposits | ⚠️ **Lending creates deposits. Causality reversed** (§6 → `econ-macroeconomics-money-and-behavioural`) |
| National debt is like household debt | ⚠️ **`r − g`, own-currency issuance, and the ratio matter** (§7 → `econ-macroeconomics-money-and-behavioural`) |
| GDP measures welfare | ⚠️ **It measures market production and was never intended as welfare** (§5 → `econ-macroeconomics-money-and-behavioural`) |
| A higher bracket can reduce take-home pay | ⚠️ **Only income above the threshold is taxed higher** (§17 → `econ-gaap-ifrs-audit-and-tax`) |
| A deduction and a credit are similar | ⚠️ **A credit reduces tax directly and is worth more** (§17 → `econ-gaap-ifrs-audit-and-tax`) |
| Debits are decreases | ⚠️ **Debit means left. That's all** (§10 → `econ-accounting-statements-accrual-and-ratios`) |
| Profit means the company has cash | ⚠️ **Profitable and insolvent is a real and common failure** (§12 → `econ-accounting-statements-accrual-and-ratios`) |
| Revenue is cash received | ⚠️ **Cash in advance is deferred revenue — a liability** (§12 → `econ-accounting-statements-accrual-and-ratios`) |
| Bookings, billings and revenue are the same | ⚠️ **Four different numbers including cash** (§12 → `econ-accounting-statements-accrual-and-ratios`) |
| Depreciation is a cash outflow | ⚠️ **Non-cash; it's added back in CFO** (§11 → `econ-accounting-statements-accrual-and-ratios`) |
| EBITDA approximates cash flow | ⚠️ **It ignores capex, working capital and interest** (§14 → `econ-accounting-statements-accrual-and-ratios`) |
| Stock comp isn't a real expense | ⚠️ **It's a real cost of employing people** (§13 → `econ-accounting-statements-accrual-and-ratios`) |
| Book value reflects what a company is worth | ⚠️ **Internally generated intangibles aren't on it** (§13 → `econ-accounting-statements-accrual-and-ratios`) |
| High ROE means a great business | ⚠️ **Decompose with DuPont — it may be leverage** (§14 → `econ-accounting-statements-accrual-and-ratios`) |
| An audit certifies the numbers are correct | ⚠️ **Reasonable assurance, sampled, not fraud-focused** (§16 → `econ-gaap-ifrs-audit-and-tax`) |
| Tax expense equals cash tax paid | ⚠️ **Book-tax differences and deferred tax** (§18 → `econ-gaap-ifrs-audit-and-tax`) |
| GAAP and IFRS give the same answer | ⚠️ **LIFO, impairment reversal, development costs, "probable"** (§15 → `econ-gaap-ifrs-audit-and-tax`) |

---

## §21. What Moved — verified August 2026

### 21.1 ⚠️ IFRS 18 — the biggest presentation change in decades
**⚠️ Issued April 2024, effective for annual reporting periods beginning on or after
1 January 2027, replacing IAS 1.** **Early application is permitted.**

**⚠️ The deadline is closer than it looks, and this is the practical point**: **application
is retrospective with restated comparatives**, ⚠️ **so for calendar-year entities the 2026
financial year is the comparative period.** **The work is happening now, not in 2027.**

**What changes:**
- **⚠️ All income and expenses must be classified into five defined categories**:
  **operating, investing, financing, income taxes, and discontinued operations.**
- **⚠️ Two new required subtotals: operating profit, and profit before financing and income
  taxes.** ⚠️ **This is significant because "operating profit" has never been defined in
  IFRS, so companies defined it themselves and comparability suffered.**
- **⚠️ Management-defined performance measures (MPMs) come INTO the audited financial
  statements with mandatory disclosures.** ⚠️ **Non-GAAP measures that previously lived in
  press releases now require reconciliation inside the audited statements — arguably the
  most consequential change for how companies communicate.**
- **Enhanced guidance on aggregation, disaggregation, location and labelling.**
- **Consequential amendments to IAS 7 (cash flows), IAS 8, IAS 33 (EPS) and IAS 34.**

**⚠️ Important scope limit**: **IFRS 18 does not change recognition or measurement — the
numbers don't change, the presentation does.** ⚠️ **But it may change what an entity
reports as operating profit**, and one source notes companies may need to revisit **bank
covenants and bonus arrangements** that reference affected subtotals.

**Also**: **IFRS 19** (⚠️ **reduced disclosure for eligible subsidiaries — reported as
roughly 70% less note volume, effective January 2027, and it can only be adopted alongside
IFRS 18**), and **UK GAAP's FRS 102/105 gaining a five-step revenue model** based on
IFRS 15 for 2026.

### 21.2 ⚠️ US Section 174 — R&D expensing restored
**⚠️ Directly relevant to software businesses, and it was the single most disruptive tax
change of the decade for them.**

**The background**: **TCJA required domestic R&E expenditures — explicitly including
software development — to be capitalized and amortized over five years from 2022**, and
⚠️ **foreign R&E over fifteen.** **The effect on cash-burning software companies was
severe: firms with no accounting profit owed tax on income that existed only because their
engineers' salaries could not be deducted.**

**⚠️ The One Big Beautiful Bill Act (OBBBA), enacted 4 July 2025, created Section 174A**:
- **⚠️ Domestic R&E — including domestic software development — is again fully deductible
  in the year incurred, for tax years beginning after 31 December 2024.** **Permanent, per
  the reporting.**
- **⚠️ Foreign R&E remains subject to 15-year amortization.** **The domestic/foreign split
  is now the permanent structural feature**, and ⚠️ **one source draws the obvious
  consequence: the cost of offshore engineering now carries a tax drag it didn't before
  2022.**
- **Taxpayers may still elect to capitalize and amortize domestic costs over at least 60
  months** if that suits their position.
- **⚠️ For 2022–2024 capitalized amounts**: **eligible small businesses — average gross
  receipts of $31 million or less under §448(c) — may elect retroactive application and
  amend those returns**; ⚠️ **larger taxpayers cannot amend but may deduct the remaining
  unamortized balance entirely in 2025, or 50/50 across 2025 and 2026.**
- **⚠️ The small-business retroactive election deadline is reported as the earlier of
  6 July 2026 or the statute of limitations** — ⚠️ **which, as of this writing, has
  passed. Verify current status.**
- **Coordination with the §41 R&D credit and §280C matters** and ⚠️ **requires modelling
  rather than a default choice.**

**Related OBBBA provisions**: **100% bonus depreciation restored permanently for qualifying
property acquired and placed in service after 19 January 2025** (⚠️ **it had been phasing
down and would have expired**); **§179 expensing raised to $2.5M with phase-out from $4M**;
**§163(j) interest limitation moved back to an EBITDA basis from 2025** (⚠️ **more
generous than the EBIT basis it replaced**); and **QSBS gross asset threshold raised to
$75M.**

> **⚠️ GOTCHA — every figure in §21.2 is US federal, dated, and subject to change, and
> state conformity varies.** ⚠️ **States that automatically conform to the IRC generally
> follow; others may not, so a state-level §174 liability can persist after the federal
> one is gone.** **This is exactly the kind of detail that makes §17 → `econ-gaap-ifrs-audit-and-tax`'s caution
> non-negotiable.** **Verify before acting.**

---

## §22. Books

**Economics**
| Author | Work | Why |
|---|---|---|
| **The CORE Team** | ***The Economy*** | ⚠️ **Free online, modern, and starts from real problems rather than perfect competition** |
| **Mankiw** | *Principles of Economics* | The standard, conventional |
| **Wheelan** | *Naked Economics* | ⚠️ **The readable non-technical entry** |
| **Banerjee & Duflo** | ***Good Economics for Hard Times*** | ⚠️ **What the evidence actually shows on contested questions** |
| **Angrist & Pischke** | *Mostly Harmless Econometrics* | ⚠️ **§1 → `econ-methodology-and-microeconomics`'s credibility revolution, from its architects** |
| **Kahneman** | *Thinking, Fast and Slow* | §9 → `econ-macroeconomics-money-and-behavioural` — ⚠️ **read alongside the replication discussion** |
| **Acemoglu & Robinson** | *Why Nations Fail* | §8 → `econ-macroeconomics-money-and-behavioural`'s institutions argument |

**Accounting**
| **Ittelson** | ***Financial Statements*** | ⚠️ **The clearest first book. Genuinely beginner-proof** |
| **Berman & Knight** | *Financial Intelligence* | For non-financial managers |
| **Penman** | *Financial Statement Analysis and Security Valuation* | ⚠️ **Rigorous §14 → `econ-accounting-statements-accrual-and-ratios`** |
| **Schilit** | ***Financial Shenanigans*** | ⚠️ **How the numbers get manipulated. Essential counterweight to §11 → `econ-accounting-statements-accrual-and-ratios`** |
| **Damodaran** | *Investment Valuation* + free online materials | ⚠️ **Outstanding and free** |
| **Kieso, Weygandt & Warfield** | *Intermediate Accounting* | The professional textbook |

**Tax**: ⚠️ **primary sources over books, because books date instantly** — **IRS
publications**, **your national revenue authority**, **the OECD for international**, and
⚠️ **a qualified professional for anything with money attached.**

---

## §23. Quick Reference

### 23.1 Reading financial statements — the order that works
```
1. ⚠️ Cash flow statement FIRST. Is CFO positive and growing? Does it track net income?
2. Revenue trend and gross margin. Is growth real and is it profitable growth?
3. ⚠️ Balance sheet: leverage, liquidity, and what the assets actually ARE
4. ⚠️ THE NOTES. Accounting policies, segments, contingencies, related parties,
   the effective tax rate reconciliation (§18)
5. ⚠️ Reconcile any non-GAAP measure to GAAP yourself. Check every adjustment
6. Compare to peers and to the same company three years ago
```

### 23.2 Red flags
- [ ] ⚠️ **Net income rising while CFO falls or stays flat** (§12 → `econ-accounting-statements-accrual-and-ratios`)
- [ ] Receivables or inventory growing much faster than revenue
- [ ] Frequent "one-time" charges that recur
- [ ] Accounting policy changes or a change of auditor without clear cause
- [ ] Revenue recognition policy that differs from peers
- [ ] Heavy reliance on Level 3 fair values (§13 → `econ-accounting-statements-accrual-and-ratios`)
- [ ] ⚠️ **Large or growing gap between GAAP and "adjusted" figures** (§14 → `econ-accounting-statements-accrual-and-ratios`)
- [ ] Related-party transactions of significance
- [ ] ⚠️ **A deferred tax valuation allowance being recorded** (§18 → `econ-gaap-ifrs-audit-and-tax`)
- [ ] Aggressive capitalization of costs peers expense (§13 → `econ-accounting-statements-accrual-and-ratios`)

### 23.3 Picker
| Question | Where |
|---|---|
| Who really bears this tax? | ⚠️ **The inelastic side** (§2 → `econ-methodology-and-microeconomics`) |
| Is this economic claim solid? | ⚠️ **§1 → `econ-methodology-and-microeconomics`'s reliability gradient** |
| Why doesn't the balance sheet balance? | ⚠️ **A missing statement link** (§11 → `econ-accounting-statements-accrual-and-ratios`) |
| Is this company generating cash? | **CFO, not net income** (§11 → `econ-accounting-statements-accrual-and-ratios`, §12 → `econ-accounting-statements-accrual-and-ratios`) |
| Is this ROE good? | ⚠️ **DuPont-decompose it first** (§14 → `econ-accounting-statements-accrual-and-ratios`) |
| Why is tax expense ≠ cash tax? | ⚠️ **Book-tax differences** (§18 → `econ-gaap-ifrs-audit-and-tax`) |
| Comparing a US and a European company? | ⚠️ **Check LIFO, impairment, intangibles** (§15 → `econ-gaap-ifrs-audit-and-tax`) |
| Anything with real money at stake | ⚠️ **A qualified professional** (§17 → `econ-gaap-ifrs-audit-and-tax`) |

---

## §24. Method

**Parts I and II rest on stable material** — **Pacioli (1494), the accounting identities,
Ricardo on comparative advantage (1817), the standard micro and macro framework, and the
converged revenue standard (ASC 606 / IFRS 15)** — sourced from the texts in §22.
⚠️ **The arithmetic of double-entry cannot change; the economics has been stable in its
core mechanisms for decades even where magnitudes are disputed.**

**Two searches were run in August 2026**, on **accounting standards** and **US tax
provisions** — ⚠️ **the two areas here that genuinely date.**

**Confidence.** **High** in §10–§16 → `econ-accounting-statements-accrual-and-ratios`, `econ-gaap-ifrs-audit-and-tax` and §18–§19 → `econ-gaap-ifrs-audit-and-tax`'s structure — **accounting is a defined
system and I have stated the rules with the frameworks they belong to.**
**High** in §21.1: **IFRS 18's effective date, retrospective application, five categories,
two new subtotals and MPM requirements are consistent across the IASB itself, the Big
Four, ICAEW and Grant Thornton.**
**High** in §21.2's structure: **the OBBBA §174A facts — enactment 4 July 2025, domestic
expensing from tax years beginning after 31 December 2024, foreign 15-year amortization
retained, the $31M small-business threshold, and the 2025 / 2025–26 catch-up options —
recur consistently across many independent accounting firms.**

⚠️ **Three deliberate choices.**

**§1 → `econ-methodology-and-microeconomics` puts epistemics before content**, which is unusual for a reference and I think
correct here. ⚠️ **Economics is routinely presented with a confidence its evidential base
doesn't support, and the reliability gradient — from near-certain mechanisms to genuinely
disputed magnitudes — is the most useful thing to carry.** **I've tried to mark contested
questions as contested rather than picking sides**, including on **minimum wage,
multipliers, and the Phillips curve.** ⚠️ **Where I've stated something as settled — tax
incidence, comparative advantage, bank money creation — it's because the profession is
close to unanimous, not because I find it congenial.**

**§17 → `econ-gaap-ifrs-audit-and-tax` deliberately withholds specific tax numbers.** ⚠️ **Rates, brackets and thresholds
change annually and vary by jurisdiction, and a stale figure in a reference document is
actively harmful.** **The structural concepts are what transfer.** ⚠️ **§21.2 breaks this
rule for the OBBBA provisions because they are the specific change most relevant to
software businesses — and I've flagged that every figure there is US federal, dated,
subject to state non-conformity, and that the small-business retroactive deadline reported
as 6 July 2026 has apparently now passed.**

⚠️ **On §21.2's sourcing**: **the accounting-firm material is technically reliable and
commercially motivated — these firms sell §174 advisory services, and the framing tends
toward urgency.** **The underlying statutory facts are consistent across enough
independent firms that I'm confident in them; the "you should act now" framing is
marketing wrapped around correct technical content.**
