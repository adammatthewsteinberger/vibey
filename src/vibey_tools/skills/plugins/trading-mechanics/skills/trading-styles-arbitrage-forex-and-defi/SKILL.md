---
name: trading-styles-arbitrage-forex-and-defi
description: "Use when examining a specific style or venue mechanically: swing trading and day trading and the structural constraints each faces, real versus apparent arbitrage and why most apparent arbitrage is compensation for risk or cost, forex and its leverage and carry mechanics, and DeFi mechanics including automated market makers, impermanent loss, liquidations and MEV."
---

# Trading Mechanics: Trading Styles, Arbitrage, Forex, and DeFi Mechanics

> **Part 3 of 5** of the *Trading Mechanics* reference (plugin `trading-mechanics`), covering §8–§12. Sibling skills: `trading-evidence-microstructure-and-execution` (§0–§3), `trading-asset-classes-derivatives-and-analysis` (§4–§7), `trading-risk-costs-backtesting-and-psychology` (§13–§17), `trading-reference` (§18–§22). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Microstructure, derivatives pricing and the outcome literature are stable; the retail outcome studies and DeFi mechanics were re-checked for August 2026.

> **⚠️ Scope.** This explains how markets and instruments work. ⚠️ **It is not investment
> advice, and nothing here is a recommendation to trade anything.** **§1 → `trading-evidence-microstructure-and-execution` is deliberately
> first, because the evidence on outcomes is the single most important input to any
> decision about participating, and it is systematically absent from most material on
> this subject.**
>
> **⚠️ GOTCHA** boxes mark mechanics that cost people money.
>
> **The three things that structure everything below:**
> 1. **⚠️ Trading is negative-sum after costs.** Every trade has two sides; the market as a
>    whole earns the market return, and costs come out before anyone's profit. **Short-term
>    trading is a zero-sum game against professionals, minus fees** (§1 → `trading-evidence-microstructure-and-execution`, §14 → `trading-risk-costs-backtesting-and-psychology`).
> 2. **⚠️ Your counterparty is usually better equipped than you are.** Faster, better
>    informed, better capitalized, and paid to take the other side. **This isn't a reason
>    not to understand markets; it's a reason to be precise about where any edge would
>    come from** (§2 → `trading-evidence-microstructure-and-execution`).
> 3. **⚠️ Position sizing determines survival; edge only determines the long-run
>    average.** **You can have a genuine edge and still be wiped out by sizing** (§13 → `trading-risk-costs-backtesting-and-psychology`).

---

## §8. Swing Trading

**Holding days to weeks, capturing intermediate moves.**
**⚠️ Why it's structurally more plausible than day trading**: **fewer trades means costs
consume a smaller fraction of returns; you're not competing on speed; and momentum and
mean-reversion effects do exist at multi-day horizons** (§7 → `trading-asset-classes-derivatives-and-analysis`).
**⚠️ What it still requires**: **a stated edge, position sizing** (§13 → `trading-risk-costs-backtesting-and-psychology`), **overnight gap
risk that no stop protects against** (§3 → `trading-evidence-microstructure-and-execution`), **and the discipline to hold through
drawdown.**
⚠️ **The honest framing: it moves you from competing against HFT to competing against
professional discretionary and systematic managers — better odds, not good odds.**

---

## §9. Day Trading

**⚠️ Mechanics**: opening and closing ranges, VWAP, level 2, tape reading, scalping,
momentum and reversal setups, halts and circuit breakers.
**⚠️ US pattern day trader rule**: **four or more day trades in five business days in a
margin account requires maintaining $25,000 equity.** **This is a regulatory floor, not a
capital adequacy recommendation.**

**⚠️ The structural problems, stated plainly:**
- **⚠️ Costs are paid hundreds of times per year** (§14 → `trading-risk-costs-backtesting-and-psychology`), **against an intraday signal that
  is very weak.**
- **⚠️ Your counterparties are faster by orders of magnitude** (§2 → `trading-evidence-microstructure-and-execution`).
- **⚠️ Leverage magnifies the negative expectation.**
- ⚠️ **The Taiwan authors observed that the small profitable minority appear to earn by
  supplying liquidity via passive limit orders to impatient uninformed traders** — **that
  is, by trading against other retail participants.** **Which tells you what the winning
  seat looks like, and it's a market-making seat.**
- **⚠️ A US Senate subcommittee found the average day trader needed $464/day just to break
  even after commissions.** **Dated, but the structure of the problem hasn't changed.**

⚠️ **§1 → `trading-evidence-microstructure-and-execution` is the section that matters here, and I'd rather state it once clearly than
soften it: the documented base rate for persistent retail day trading is a 97% loss rate,
and this is not controversial in the literature.**

---

## §10. Arbitrage — Real vs Apparent

**⚠️ True arbitrage is a riskless profit from simultaneous offsetting positions, and it is
essentially extinct at retail scale** — ⚠️ **because it is the single thing every
professional firm is best equipped to find, and it disappears in microseconds.**

```
Cross-exchange       ⚠️ requires capital pre-positioned on BOTH venues, and transfer
                     latency is exactly what kills it
Triangular (FX)      §11
Cash-and-carry       spot vs futures — ⚠️ this is a financing trade, and the return
                     IS the financing rate
Merger arb           ⚠️ NOT riskless — you are short the deal-break probability
Convertible arb      ⚠️ leveraged, and it failed spectacularly in 2008
Statistical arb      ⚠️ not arbitrage at all — a positive-expectancy bet
```
> **⚠️ GOTCHA — most "arbitrage opportunities" a retail participant sees are one of four
> things**: ⚠️ **stale data**, **a price you cannot actually transact at** (the quote
> disappears when you send the order), **a cost you haven't counted** (withdrawal fees,
> spreads, financing, tax), **or a genuine risk you haven't identified** (counterparty,
> settlement, or the asset not being fungible across venues).
> ⚠️ **If it looks riskless and it's still there, you are the one who hasn't found the
> risk.** **The crypto cross-exchange spread that persists is usually a withdrawal
> restriction or a solvency signal.**

---

## §11. Forex

**⚠️ The largest and most liquid market in the world, and the one with the worst retail
outcomes.**
**Mechanics**: currency pairs, **pips**, lots, **the carry trade** (⚠️ **borrow low-yield,
lend high-yield — and it earns steadily then loses violently, because exchange rate risk
is exactly what you're being paid for**), **rollover/swap**, and **triangular arbitrage**
which is professionally arbitraged away continuously.
**Drivers**: rate differentials, ⚠️ **purchasing power parity which holds only over
decades if at all**, current accounts, central bank policy, and risk sentiment.
**⚠️ Why retail FX is especially unfavourable:**
- **⚠️ Very high leverage is available** — **regulators cap it precisely because of
  documented outcomes** (⚠️ **and the required broker disclosures in the EU/UK, showing
  the percentage of retail accounts losing money, are among the most honest numbers
  published in finance**).
- **⚠️ Many retail FX brokers take the other side of your trade**, which is a conflict of
  interest that varies by jurisdiction and model.
- **⚠️ There is no positive expected return in holding a currency** the way there is in
  holding equity — **FX is close to zero-sum before costs and strictly negative after.**
- **Spreads widen dramatically around news**, and ⚠️ **stops are frequently taken out in
  the resulting spikes.**

---

## §12. DeFi Mechanics

**⚠️ The mechanics are genuinely interesting engineering. The risk profile is severe and
different in kind from traditional markets.**

**AMMs** replace the order book with a formula. **Constant product: `x · y = k`.** ⚠️ **The
pool always quotes a price and always has liquidity — that's the innovation — and it
prices purely off its own reserves, so it needs arbitrageurs to track the outside market.**
**Concentrated liquidity (Uniswap V3)** lets LPs specify a price range, ⚠️ **improving
capital efficiency and adding active management burden.**

**⚠️ Impermanent loss — the most misunderstood concept in DeFi:**
> **⚠️ GOTCHA — impermanent loss is not a fee or a bug. It is the arbitrageur's profit,
> paid by you.** ⚠️ **When the external price moves, arbitrageurs buy the underpriced side
> of your pool and sell the overpriced side until the pool matches the market. That
> difference is extracted from the LP.**
> **The mechanical result: you always end up with more of the asset that fell and less of
> the one that rose.** ⚠️ **If ETH rises 50%, an ETH/stablecoin LP position is worth more
> than at deposit but meaningfully less than simply holding** — **a worked example puts
> it around 5.7% below holding for a 50% move.**
> ⚠️ **"Impermanent" assumed prices revert. They frequently don't, and the loss
> crystallizes on withdrawal.** **The academic literature has largely moved to
> loss-versus-rebalancing (LVR), which measures adverse selection against continuous
> rebalancing and — unlike IL — is monotonically increasing and path-dependent.**
> ⚠️ **LVR is the more honest measure, and it is worse than IL suggests.**

**⚠️ Fees can offset IL, and whether they do is an empirical question per pool** —
**high-volume, low-volatility pairs are where the arithmetic works; volatile pairs in
trending markets are where it doesn't.**

**MEV** — ⚠️ **value extracted by reordering, inserting or censoring transactions in a
block.** **Sandwich attacks (front-run your swap, back-run it), liquidation racing,
arbitrage.** ⚠️ **Empirical work shows MEV amplifies LP losses beyond what IL alone
predicts.** **Mitigations: private mempools, intent-based systems where solvers compete to
fill your order (CoW Swap, UniswapX), slippage limits.**

**Lending protocols** — ⚠️ **over-collateralized by necessity, because there is no recourse
and no identity.** **Liquidation when the health factor breaches; liquidators are
incentivized with a bonus.** ⚠️ **Cascading liquidations in a sharp move are a documented
systemic pattern.**
**Oracles** — ⚠️ **smart contracts cannot see external prices, so oracles bridge that gap
and are therefore the attack surface.** **Oracle manipulation caused $403.2 million in
losses in 2022 alone.** **TWAP oracles reduce manipulation risk and add lag.**

**⚠️ Risks with no traditional-market analogue**: **smart contract bugs (immutable and
often unrecoverable), admin key and governance risk, bridge exploits, rug pulls, protocol
insolvency, and total loss of self-custodied keys.** ⚠️ **There is no deposit insurance,
no chargeback, and frequently no legal recourse.** **"Audited" reduces risk; it does not
eliminate it, and audited protocols have failed.**
