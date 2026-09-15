---
name: fundraising-instruments-dilution-terms-and-control
description: "Use when modelling a round or reading a term sheet: the capital ladder and the instruments — priced equity rounds, convertible notes and SAFEs — dilution and cap table mathematics including option pool shuffle and the effect of stacked instruments, term sheet economics with liquidation preference as the term that matters most and the rest of the economic terms, and control and governance including board composition and protective provisions."
---

# Fundraising Fundamentals: Instruments, Dilution and Cap Table Math, Term Sheet Economics, and Control

> **Part 2 of 6** of the *Fundraising Fundamentals* reference (plugin `fundraising-fundamentals`), covering §5–§9. Sibling skills: `fundraising-what-it-is-narrative-and-process` (§0–§4), `fundraising-diligence-valuation-and-exits` (§10–§13), `fundraising-public-markets-and-securities-regulation` (§14–§19), `fundraising-non-profit-donors-grants-and-metrics` (§20–§25), `fundraising-reference` (§26–§32). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Instruments, dilution mathematics and securities structure are stable. Two areas moved. See §26 → `fundraising-reference` for the concentration of the private venture market and the US charitable deduction rewrite effective January 2026.

> **⚠️ Scope.** Complements a business reference (§4 financing overview, §12 negotiation)
> and an economics/accounting/tax reference (statements, entity structure, tax).
> **This is the deep version**, and it covers three worlds most treatments handle
> separately.
>
> ⚠️ **Not legal, tax or investment advice.** **Securities law is unforgiving and
> jurisdiction-specific — §19 → `fundraising-public-markets-and-securities-regulation` exists to tell you which questions to take to a lawyer.**
>
> **The three ideas that organize all of it:**
> 1. **⚠️ All fundraising sells the same thing: a claim on future value, in exchange for
>    capital now.** **Equity sells ownership, debt sells a promise, philanthropy sells
>    *participation in an outcome*.** ⚠️ **The instruments differ enormously; the
>    persuasion structure barely differs at all** (§2 → `fundraising-what-it-is-narrative-and-process`, §3 → `fundraising-what-it-is-narrative-and-process`).
> 2. **⚠️ Fundraising is a sales process with a long cycle, and treating it as anything
>    else is the most common failure.** **Pipeline, qualification, and the fact that most
>    "no"s are actually "not now" or "not me"** (§4 → `fundraising-what-it-is-narrative-and-process`).
> 3. **⚠️ The terms matter more than the amount, in every one of the three worlds.**
>    **Liquidation preference in private, covenants in public, restriction in
>    philanthropy.** ⚠️ **Money with the wrong strings attached has sunk more
>    organizations than insufficient money.**

---

## §5. The Capital Ladder

```
BOOTSTRAP        ⚠️ revenue and savings. Full control, slowest growth
FRIENDS & FAMILY ⚠️ real money and real relationship risk. Paper it properly
ANGEL            individuals, ~$25k–$250k. ⚠️ Often the most useful capital because
                 it comes with operating experience
PRE-SEED         first institutional. Product exists, evidence thin
SEED             ⚠️ funds the hypothesis — finding product-market fit
SERIES A         ⚠️ funds THE MACHINE — repeatable go-to-market
SERIES B/C       scale what's working
GROWTH / PE      ⚠️ later, larger, often partly SECONDARY (buying existing shares)
STRATEGIC/CORP   ⚠️ money plus a relationship, and sometimes plus a conflict
```
**⚠️ The framing worth keeping**: **pre-seed funds the founder, seed funds the hypothesis,
Series A funds the machine.** ⚠️ **These are not just larger cheques — they are different
investments with different evidence requirements**, and **pitching a Series A as a bigger
seed is why many otherwise-good companies stall between them.**
**⚠️ And the base rate matters**: **a very small fraction of businesses ever raise
institutional venture capital.** **The overwhelming majority finance through revenue,
savings, credit, and small angel rounds** — ⚠️ **which is normal and successful, not
failure** (§26.1 → `fundraising-reference`).

---

## §6. Instruments

### 6.1 Priced equity round
**⚠️ You sell newly issued preferred shares at an agreed price.** **Requires a valuation,
full documents, and is the most expensive and slowest to close** — **and it's clean:
everyone knows what they own.**

### 6.2 Convertible note
**⚠️ Debt that converts to equity at a future priced round.** **Carries interest and a
maturity date** — ⚠️ **and the maturity date is a real risk: if you haven't raised by
then, the holder can in principle demand repayment you don't have.**

### 6.3 SAFE
**⚠️ Simple Agreement for Future Equity — not debt, no interest, no maturity.** **The
dominant early-stage instrument in the US.**
```
CAP           ⚠️ maximum valuation at which it converts — the investor's upside
DISCOUNT      ⚠️ e.g. 20% off the next round price
MFN           gets the best terms given to any later SAFE holder
⚠️ PRE vs POST-MONEY   the critical distinction
```
> **⚠️ GOTCHA — post-money SAFEs (the current standard) are far more dilutive than
> founders expect, and this is the most common early cap-table mistake.** ⚠️ **A
> post-money SAFE fixes the investor's percentage of the company AFTER all SAFEs
> convert** — **so every additional SAFE you sell dilutes YOU, not the earlier SAFE
> holders.** **Under the older pre-money form, SAFE holders diluted each other.**
> **⚠️ Founders who raise "just another $500k" on post-money SAFEs three or four times
> routinely discover at their priced round that they've sold 35–40% rather than the
> ~20% they had in mind.** ⚠️ **Model the conversion on a full cap table BEFORE signing
> each one — not at the round.**

**⚠️ Stacked SAFEs with different caps are a genuine mess at conversion**, and **they
interact with the option pool refresh (§8) in ways that compound.**

---

## §7. ⚠️ Dilution and Cap Table Math

**⚠️ Work a real example, because this is where intuition fails:**
```
Start:  Two founders, 10,000,000 shares, 50/50.

SEED — raise $3M at $12M pre-money → $15M post
  Investor gets 3/15 = 20%
  ⚠️ New total = 10,000,000 / 0.80 = 12,500,000 shares
  Investor: 2,500,000 (20%) · Founders: 10,000,000 (80%, 40% each)

⚠️ OPTION POOL — investor requires a 15% post-close pool, created PRE-money
  This comes out of the FOUNDERS' share, not everyone's — see the gotcha
  Founders now ≈ 65% combined

SERIES A — raise $10M at $40M pre → $50M post = 20% to the new investor
  ⚠️ EVERYONE existing dilutes by 20%
  Founders: 65% × 0.80 ≈ 52% · Seed investor: 20% × 0.80 = 16%

SERIES B — 20% again
  Founders ≈ 42% · Seed ≈ 12.8%
```
> **⚠️ GOTCHA — the option pool shuffle is the most reliably overlooked term in a term
> sheet.** ⚠️ **When the pool is created PRE-money, it comes entirely out of the existing
> shareholders — i.e. you.** **A "$12M pre-money with a 15% post-close pool" is
> economically a lower price than $12M pre-money with the pool created post-money.**
> **⚠️ Always ask whether the pool is inside or outside the pre-money**, and **negotiate
> the SIZE of the pool by reference to an actual hiring plan** — **a pool sized "because
> that's standard" is money you gave away for no reason.**

**⚠️ Structural realities to plan around:**
- **⚠️ Each priced round typically takes ~20%** — **that number moves much less than
  founders hope**, because it's driven by the lead's ownership target, not your valuation.
- **⚠️ Founders reaching Series B have commonly sold 35–40% already**, before B dilutes
  further.
- **⚠️ Dilution is not inherently bad.** **A smaller share of a much larger company is the
  entire point.** **What's bad is dilution that bought nothing** — **which is why §3 → `fundraising-what-it-is-narrative-and-process`'s
  milestone-linked ask matters.**
- **⚠️ Pro-rata rights let existing investors maintain percentage** by investing in later
  rounds, **and they consume allocation you might want to give someone else.**

---

## §8. ⚠️ Term Sheet Economics

**⚠️ Valuation is what founders negotiate. These determine what they actually receive:**

### 8.1 Liquidation preference — the big one
```
1x NON-PARTICIPATING   ⚠️ the market standard and what you want. Investor takes
                       EITHER their money back OR converts to common and takes
                       their percentage — whichever is greater. Not both
1x PARTICIPATING       ⚠️ "double dip" — money back AND their percentage of the rest
MULTIPLE (2x, 3x)      ⚠️ money back several times over first
```
**⚠️ Worked example. Investor put in $10M for 20%, company sells for $30M:**
```
1x non-participating   ⚠️ max($10M, 20% of $30M = $6M) = $10M. Others split $20M
1x participating       ⚠️ $10M + 20% of remaining $20M = $14M. Others split $16M
2x participating       ⚠️ $20M + 20% of $10M = $22M. Others split $8M
```
⚠️ **In a modest exit — which is the most likely non-zero outcome — preference structure
determines whether the founders and employees receive anything at all.** **A stacked
preference across several rounds can exceed the entire sale price, leaving common
shareholders with nothing on a sale that looks like a success in the press.**

### 8.2 The rest
```
ANTI-DILUTION      ⚠️ broad-based weighted average (normal) vs FULL RATCHET
                   (⚠️ punitive — reprices ALL their shares to the down-round price)
PAY-TO-PLAY        ⚠️ investors must join later rounds or lose preference. GOOD for you
DIVIDENDS          cumulative dividends accrue and compound into the preference
REDEMPTION         ⚠️ investor can demand their money back after N years
DRAG-ALONG         majority can force minority to sell
PROTECTIVE PROVISIONS  ⚠️ a veto list — see §9
NO-SHOP / EXCLUSIVITY  ⚠️ you stop talking to others for 30–60 days. Keep it short
```
**⚠️ The general rule**: **accept a lower valuation with clean terms over a higher
valuation with structure.** ⚠️ **A headline number bought with participating preferred,
full ratchet and a redemption right is a worse deal in almost every scenario except the
one where everything goes perfectly.**

---

## §9. Control and Governance

```
BOARD          ⚠️ composition is the real control question. Founder seats,
               investor seats, INDEPENDENTS. Who breaks a tie?
PROTECTIVE     ⚠️ a preferred-holder veto over: selling the company, new financings,
PROVISIONS     changing share terms, budget, hiring/firing the CEO
INFO RIGHTS    reporting obligations — reasonable and real work
FOUNDER VESTING ⚠️ yes, on YOUR shares too. Standard and correct
VOTING         classes, and dual-class structures in some cases
```
**⚠️ Control is lost gradually and then suddenly.** **Each round adds a board seat and a
veto item; three rounds in, a founder with 40% economic ownership may have no working
control.** ⚠️ **Track board composition across your projected rounds, not just
percentages** — **and note that the ability to remove the CEO usually sits with the board,
not the shareholders.**
