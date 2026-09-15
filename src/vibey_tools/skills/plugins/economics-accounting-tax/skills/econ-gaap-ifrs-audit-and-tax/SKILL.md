---
name: econ-gaap-ifrs-audit-and-tax
description: "Use when the reporting framework or the tax treatment matters: GAAP versus IFRS and the differences that actually change the numbers, audit and internal controls and what an audit opinion does and does not assert, tax fundamentals kept deliberately general and why specific figures are sparse here, book-tax differences and deferred tax, and entity choice and its tax consequences. Orientation, not tax advice."
---

# Economics, Accounting and Tax: GAAP versus IFRS, Audit and Controls, and Tax

> **Part 4 of 5** of the *Economics, Accounting and Tax* reference (plugin `economics-accounting-tax`), covering §15–§19. Sibling skills: `econ-methodology-and-microeconomics` (§0–§4), `econ-macroeconomics-money-and-behavioural` (§5–§9), `econ-accounting-statements-accrual-and-ratios` (§10–§14), `econ-reference` (§20–§24). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Double-entry dates from 1494 and the accounting identities are arithmetic; tax rules change annually and vary by jurisdiction. See §21 → `econ-reference` for IFRS 18 and US Section 174.

> **⚠️ Scope and a necessary caution.** This is an explanatory reference for
> understanding financial and economic material. ⚠️ **It is not accounting, tax, legal or
> investment advice.** **Tax rules in particular are jurisdiction-specific, change every
> year, and turn on facts I can't see** — §17 explains why I've kept specific figures
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

## §15. GAAP vs IFRS

**⚠️ The framing difference matters more than any individual rule**: **US GAAP is more
rules-based (bright lines, detailed guidance); IFRS is more principles-based (professional
judgement).** ⚠️ **Rules invite structuring right up to the line; principles invite
inconsistency. Neither is strictly better and both failure modes are real.**

| Area | US GAAP | IFRS |
|---|---|---|
| **Inventory** | ⚠️ **LIFO permitted** | ⚠️ **LIFO prohibited** |
| **Impairment reversal** | ⚠️ **Generally prohibited** | ⚠️ **Permitted (not goodwill)** |
| **Development costs** | Generally expensed | ⚠️ **Capitalized if criteria met** |
| **Revaluation of PP&E** | Not permitted | ⚠️ **Permitted** |
| **"Probable"** | ⚠️ **A high threshold** | ⚠️ **Roughly >50%** |
| **Presentation** | Detailed SEC rules | ⚠️ **IFRS 18 from 2027 — §21.1 → `econ-reference`** |

**⚠️ The practical consequence**: **the same company reports different numbers under the
two frameworks**, and **cross-border comparison requires care.** ⚠️ **Convergence stalled
after the major joint projects (revenue, leases) and full convergence is no longer an
active goal.**

---

## §16. Audit and Controls

**⚠️ What an audit actually is, because it's widely misunderstood**: **reasonable — not
absolute — assurance that statements are free of material misstatement, in accordance with
the framework.** ⚠️ **It is a sampling exercise, not a certification of accuracy, and it is
not primarily designed to detect fraud.** **Opinions: unqualified, qualified, adverse,
disclaimer.**

**Internal control** — **COSO framework**; **segregation of duties** (⚠️ **the person who
authorizes, the person who records, and the person who has custody should be three people
— and this single control prevents a large share of occupational fraud**); reconciliations;
authorization limits.
**⚠️ Sarbanes-Oxley §404** requires management assessment and (for accelerated filers)
auditor attestation of internal control over financial reporting.
**⚠️ The fraud triangle** — **pressure, opportunity, rationalization** — and
⚠️ **materiality is a judgement, which is exactly where audit disputes concentrate.**

---

# PART III — TAX

---

## §17. ⚠️ Tax Fundamentals and Why This Section Is Deliberately General

> **⚠️ GOTCHA — everything in Part III is structural, not numerical, and that is a
> deliberate choice.** ⚠️ **Tax rates, brackets, thresholds and allowances change every
> year and differ by country, state and entity type.** **Any specific figure I give you
> here is a liability, not an asset** — **it will be stale, and stale tax numbers are
> worse than none.** ⚠️ **The concepts below are stable; look up the current numbers, and
> for anything consequential use a professional.**

**⚠️ The structural concepts that are stable:**
```
TAX BASE           what is taxed (income, consumption, property, transactions, payroll)
RATE STRUCTURE     ⚠️ progressive, flat, regressive — and note MARGINAL vs EFFECTIVE
DEDUCTION vs CREDIT ⚠️ a deduction reduces taxable income; a credit reduces tax owed
                   directly. A credit is worth more per dollar
REFUNDABLE vs NON  ⚠️ refundable credits can produce a payment below zero liability
TIMING             ⚠️ deferral has real value — a dollar of tax paid later is cheaper
CHARACTER          ordinary income vs capital gain, often taxed differently
```
> **⚠️ GOTCHA — the marginal rate misconception is the most damaging piece of tax
> illiteracy in circulation.** ⚠️ **"A raise pushed me into a higher bracket so I take home
> less" is essentially always false in a progressive system**: **only the income above the
> threshold is taxed at the higher rate.** **The genuine exceptions are benefit cliffs
> where an assistance programme cuts off abruptly** — ⚠️ **those are real and they are a
> defect of the benefit design, not of the tax brackets.**

**Tax avoidance (legal) vs evasion (illegal)** — ⚠️ **the line is meaningful and the middle
ground is contested; "aggressive avoidance" attracts anti-avoidance rules, economic
substance doctrine, and reputational risk.**

---

## §18. Book-Tax Differences and Deferred Tax

**⚠️ This is the concept that connects Parts II and III, and it explains why a company's
tax expense doesn't match its cash tax paid.**

**Financial accounting income and taxable income are computed under different rules for
different purposes** — ⚠️ **financial reporting serves investors; tax law serves revenue
collection and policy objectives. There is no reason for them to agree, and they don't.**

```
PERMANENT DIFFERENCES   ⚠️ never reverse — municipal bond interest, certain fines,
                        some meals/entertainment. These change the EFFECTIVE TAX RATE
TEMPORARY DIFFERENCES   ⚠️ reverse over time — different depreciation methods, warranty
                        provisions, revenue timing. These create DEFERRED TAX
```
**⚠️ Deferred tax liabilities** arise when book income exceeds taxable income now and will
reverse — ⚠️ **the classic case is accelerated depreciation for tax and straight-line for
books.**
**⚠️ Deferred tax assets** arise the other way, and from **net operating loss
carryforwards.** ⚠️ **A valuation allowance is required when realization is not "more
likely than not"** — **and a company recording a large valuation allowance is telling you
it doesn't expect enough future profit to use its losses, which is a substantive signal.**

**⚠️ The effective tax rate reconciliation in the notes is one of the most informative
disclosures in a filing**, and it's routinely skipped: **it walks from the statutory rate
to the actual rate and shows exactly what is driving the difference.**

---

## §19. Entity Choice

**⚠️ Structural, jurisdiction-specific, and worth understanding conceptually.**
```
SOLE PROPRIETOR   ⚠️ no liability separation; income taxed to the owner
PARTNERSHIP / LLC ⚠️ PASS-THROUGH — the entity generally pays no income tax; income
                  flows to owners' returns. Flexible allocations
S CORPORATION (US) ⚠️ pass-through with restrictions on owners and share classes
C CORPORATION     ⚠️ entity-level tax, then dividend tax = DOUBLE TAXATION —
                  but it is the structure institutional investment expects
```
**⚠️ The trade-offs that actually decide it**: **liability protection, double taxation,
payroll versus distribution treatment, ability to raise venture capital (⚠️ which
generally requires a C corporation in the US), the ability to retain earnings at a lower
rate, and administrative burden.**
⚠️ **This is genuinely a professional-advice question — the right answer depends on the
owners' tax positions, growth plans and jurisdiction, and getting it wrong is expensive to
unwind.**

**International**: ⚠️ **transfer pricing (arm's length principle)**, **permanent
establishment**, **double tax treaties and foreign tax credits**, **withholding taxes**,
**and the OECD BEPS work including Pillar Two's global minimum tax**, ⚠️ **which is being
implemented on different timetables by different jurisdictions and is a live compliance
burden for multinationals.**
