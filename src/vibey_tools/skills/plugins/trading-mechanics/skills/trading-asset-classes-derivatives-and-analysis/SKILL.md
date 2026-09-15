---
name: trading-asset-classes-derivatives-and-analysis
description: "Use when reasoning about instruments and analytical methods: the asset classes and their differing mechanics, derivatives including options and futures with payoff structure, the Greeks and how leverage and expiry actually behave, technical analysis assessed honestly against the evidence, and quantitative and factor approaches including what the documented factors are and how much of the effect survives costs."
---

# Trading Mechanics: Asset Classes, Derivatives, Technical Analysis, and Quantitative Approaches

> **Part 2 of 5** of the *Trading Mechanics* reference (plugin `trading-mechanics`), covering §4–§7. Sibling skills: `trading-evidence-microstructure-and-execution` (§0–§3), `trading-styles-arbitrage-forex-and-defi` (§8–§12), `trading-risk-costs-backtesting-and-psychology` (§13–§17), `trading-reference` (§18–§22). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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

## §4. Asset Classes

**Equities** — ownership; ⚠️ **the only major asset class with a well-documented long-run
positive real expected return, and that return is compensation for genuinely bearing
risk.** Dividends, splits, corporate actions.
**Bonds** — ⚠️ **price and yield move inversely; duration measures interest-rate
sensitivity and convexity is the second-order correction.** **Credit risk, the yield
curve, and the fact that most bond trading is OTC and far less transparent than
equities.**
**FX** — §11 → `trading-styles-arbitrage-forex-and-defi`. **Commodities** — ⚠️ **futures-based, so returns include spot change plus
roll yield; contango and backwardation matter more than the headline commodity price**
(⚠️ **which is why commodity ETFs can lose money while the commodity rises**).
**Crypto** — ⚠️ **24/7, high volatility, fragmented venues, uneven regulation, and
custody risk that has no analogue in traditional markets** (§12 → `trading-styles-arbitrage-forex-and-defi`, §17 → `trading-risk-costs-backtesting-and-psychology`).
**ETFs and funds** — ⚠️ **check the structure: physical vs synthetic, and leveraged/inverse
ETFs rebalance DAILY, so they suffer volatility decay and do NOT deliver the multiple of
the index over any period longer than a day.** **This is a design feature that is
routinely misunderstood as a defect.**

---

## §5. Derivatives

**Futures** — ⚠️ **standardized, exchange-traded, daily mark-to-market with margin calls.**
**Leverage is embedded and large.** **Contango/backwardation and roll.**
**Options**:
```
Call / put · long / short · strike · expiry · American / European
Intrinsic + extrinsic value
GREEKS ⚠️
  Delta  sensitivity to underlying
  Gamma  ⚠️ rate of change of delta — why short options positions blow up suddenly
  Theta  ⚠️ time decay, and it ACCELERATES near expiry
  Vega   sensitivity to implied volatility
  Rho    interest rates
```
**⚠️ Black-Scholes assumes constant volatility, which is false** — ⚠️ **the volatility
smile/skew is the market's correction, and it exists because the model's assumption
doesn't hold.**
> **⚠️ GOTCHA — long options lose money by default, and short options have unbounded
> risk.** ⚠️ **Buying options means you need the move to happen, in your direction, before
> expiry, by more than the premium plus decay — three conditions, and theta works against
> you every day.** **Selling options inverts it: you win small amounts frequently and lose
> catastrophically rarely.** ⚠️ **A short-volatility strategy will show an excellent track
> record right up until it doesn't, and the loss distribution means historical returns
> systematically overstate its quality.**

**⚠️ Implied vs realized volatility is the actual trade in most options positions**, not
direction. **Selling options is structurally short volatility; there is a documented
volatility risk premium, which is compensation for bearing exactly that tail risk.**
**Swaps and CFDs** — ⚠️ **CFDs are banned for US retail, heavily restricted in the EU/UK,
and the broker disclosures required in those jurisdictions are themselves data on
outcomes** (§1 → `trading-evidence-microstructure-and-execution`).

---

## §6. Technical Analysis, Honestly

**⚠️ What it is**: price and volume patterns — support/resistance, trend, moving averages,
RSI, MACD, Bollinger bands, candlestick patterns, Fibonacci levels, Elliott waves.

**⚠️ The honest assessment, in both directions:**
- **⚠️ Some of it has a defensible basis.** **Momentum is one of the most robust documented
  anomalies in academic finance across markets and centuries** (§7). **Volume and
  volatility clustering are real statistical properties.** **Support and resistance can be
  partly self-fulfilling because order clusters actually sit at round numbers and prior
  extremes.**
- **⚠️ Much of it does not survive testing.** **Elaborate pattern taxonomies, Fibonacci
  ratios and Elliott wave counts have very weak evidential support**, and ⚠️ **humans are
  extraordinarily good at seeing patterns in random data** — **a chart of a random walk
  displays convincing head-and-shoulders formations.**
- ⚠️ **Indicator proliferation is a warning sign, not sophistication.** **Most indicators
  are transformations of the same price series; adding more does not add information, and
  it does add overfitting risk** (§15 → `trading-risk-costs-backtesting-and-psychology`).

**⚠️ The efficient market hypothesis in its useful form** is not "prices are correct" but
**"it is hard to profit from public information after costs."** ⚠️ **The strong form is
clearly false; the weak-to-semi-strong version is a good prior, and documented anomalies
exist but are typically small, crowded, and expensive to harvest.**

---

## §7. Quantitative and Factor Approaches

**⚠️ Documented factors with long academic track records**: **value, size, momentum,
quality/profitability, low volatility, carry.** ⚠️ **These are the anomalies that have
survived out-of-sample testing, and even they have gone through decade-long periods of
underperformance** — **value's post-2007 drawdown is the standing example.**
**⚠️ The factor zoo problem**: **hundreds of published factors, most of which fail
replication** — ⚠️ **a data-mining problem the field has publicly reckoned with.**
**Statistical arbitrage**: pairs trading, cointegration, mean reversion.
**⚠️ Market making** as a strategy is fundamentally about **inventory management and
adverse selection** (§2 → `trading-evidence-microstructure-and-execution`), not prediction.
**Execution alpha** — ⚠️ **for large institutions, trading better is often worth more than
predicting better.**
