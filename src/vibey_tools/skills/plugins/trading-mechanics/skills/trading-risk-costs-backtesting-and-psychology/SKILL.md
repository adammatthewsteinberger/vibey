---
name: trading-risk-costs-backtesting-and-psychology
description: "Use when evaluating a system or a claim rather than building one: risk and position sizing including drawdown, ruin and why sizing dominates edge, costs and frictions and how they consume apparent returns, backtesting pitfalls covering lookahead bias, survivorship, overfitting and the multiple-comparisons problem, psychology and the documented harms including addiction risk, and regulation and tax obligations."
---

# Trading Mechanics: Risk and Position Sizing, Costs, Backtesting Pitfalls, Psychology and Harm, and Regulation

> **Part 4 of 5** of the *Trading Mechanics* reference (plugin `trading-mechanics`), covering §13–§17. Sibling skills: `trading-evidence-microstructure-and-execution` (§0–§3), `trading-asset-classes-derivatives-and-analysis` (§4–§7), `trading-styles-arbitrage-forex-and-defi` (§8–§12), `trading-reference` (§18–§22). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
>    trading is a zero-sum game against professionals, minus fees** (§1 → `trading-evidence-microstructure-and-execution`, §14).
> 2. **⚠️ Your counterparty is usually better equipped than you are.** Faster, better
>    informed, better capitalized, and paid to take the other side. **This isn't a reason
>    not to understand markets; it's a reason to be precise about where any edge would
>    come from** (§2 → `trading-evidence-microstructure-and-execution`).
> 3. **⚠️ Position sizing determines survival; edge only determines the long-run
>    average.** **You can have a genuine edge and still be wiped out by sizing** (§13).

---

## §13. Risk and Position Sizing

**⚠️ This is the section that determines whether you survive long enough for an edge to
matter.**
```
Risk per trade   ⚠️ commonly 0.5–2% of capital. Position size = risk budget ÷ stop distance
Kelly criterion  f* = (bp − q)/b   ⚠️ optimal GROWTH, and full Kelly is far too
                 volatile in practice — fractional Kelly (¼ to ½) is standard
R-multiples      express results in units of initial risk
Correlation      ⚠️ ten positions in one sector is ONE position
Drawdown math    ⚠️ −50% requires +100% to recover. This asymmetry is the whole argument
                 for capping losses
```
> **⚠️ GOTCHA — leverage does not amplify returns; it amplifies returns and brings
> forward ruin.** ⚠️ **With enough leverage, a sequence of losses that would be survivable
> becomes terminal, and markets produce such sequences routinely.** **Risk of ruin rises
> nonlinearly with position size, and the point at which it becomes near-certain arrives
> earlier than intuition suggests.**
>
> ⚠️ **Never risk money you need.** **Rent, tuition, and emergency reserves have no place
> in a trading account, and this is not moralizing — it is that being forced to liquidate
> at a bad moment converts a temporary drawdown into a permanent loss.**

**⚠️ Path dependence is the underrated point**: **the same set of trades in a different
order can leave you fine or bankrupt.** **Expected value says nothing about survival.**
**⚠️ Ergodicity**: **time-average and ensemble-average returns differ under multiplicative
dynamics** — **which is the formal statement of why a positive expected return can still
ruin you.**

---

## §14. Costs and Frictions

```
Commissions      ⚠️ often zero on US equities — the cost moved elsewhere (§2)
Spread           ⚠️ paid on EVERY round trip, and it is the dominant cost for
                 frequent traders
Slippage         §3
Market impact    §3
Financing        margin interest, overnight swap, futures roll
Borrow fees      short selling — ⚠️ can be enormous on hard-to-borrow names
Taxes            §17 — ⚠️ short-term gains are typically taxed less favourably
Data and tools   real cost, frequently ignored in profitability calculations
⚠️ OPPORTUNITY COST  the time, and the return you'd have earned passively
```
**⚠️ The arithmetic that decides it**: **round-trip cost × trades per year, against your
edge per trade.** ⚠️ **A 0.1% round-trip cost with 500 trades a year consumes 50% of
capital in costs alone.** **You need an edge exceeding that before you have earned
anything, and that is why frequency is the enemy** (§1 → `trading-evidence-microstructure-and-execution`).

---

## §15. Backtesting Pitfalls

**⚠️ A backtest is a hypothesis, not evidence, and almost every appealing backtest is
wrong for one of these reasons:**
```
LOOK-AHEAD BIAS      ⚠️ using data unavailable at the time — restated fundamentals,
                     index membership known in advance, closing prices to trade the close
SURVIVORSHIP BIAS    ⚠️ delisted and bankrupt companies missing from your universe
OVERFITTING          ⚠️ testing enough variants guarantees one looks good by chance
DATA SNOOPING        ⚠️ the whole community mining the same dataset — even honest
                     out-of-sample tests are contaminated
IGNORING COSTS       ⚠️ §14 — the most common single reason a strategy dies live
IGNORING CAPACITY    it worked on $10k and moves the market at $10M
REGIME DEPENDENCE    ⚠️ a strategy tested only in a bull market
```
**⚠️ Practices that help**: **out-of-sample and walk-forward testing, holding out data you
genuinely never look at, penalizing parameter count, paper trading before capital,
and — the discipline almost nobody keeps — counting every strategy you tested, because
the tenth variant looking good is expected by chance.**
⚠️ **If a backtest shows a Sharpe of 3, the prior should be that you have made a mistake,
and it is usually look-ahead bias.**

---

## §16. ⚠️ Psychology and Harm

**Documented biases with direct trading consequences** (see an economics reference §9):
**overconfidence** (⚠️ **the mechanism Barber and Odean identified as driving
underperformance**), **loss aversion and the disposition effect** (⚠️ **selling winners
and holding losers — precisely backwards given momentum**), **sunk cost**, **recency**,
**confirmation bias**, **hindsight bias** (⚠️ **which makes every past chart look
tradeable**), and **the gambler's fallacy.**

> **⚠️ GOTCHA — and this is the part most trading material omits entirely.**
> ⚠️ **Trading shares structural features with gambling: variable-ratio reinforcement,
> near-misses, rapid feedback, and the ability to chase losses.** **These are the features
> that make slot machines compulsive, and mobile trading apps replicate them
> deliberately.** **Problem-gambling instruments are used in trading research for this
> reason.**
>
> ⚠️ **The warning signs are the same as for gambling**: trading more after losses to
> recover them; hiding activity or losses from people close to you; using money allocated
> to something else; escalating size to make back a drawdown; sleep and mood tracking with
> the position; and the feeling that stopping would mean accepting the loss as real.
> **⚠️ If any of that is familiar, the correct action is to stop and talk to someone —
> a professional, or a problem-gambling helpline, which cover trading.** **The financial
> damage is usually the smaller part.**

**⚠️ And on the education industry specifically**: **the Brazilian paper explicitly frames
its finding as contradicting what course providers claim.** ⚠️ **Signal-selling, paid
"mentorship," prop-firm evaluation fees and affiliate-monetized brokerage links are
businesses that earn from your participation regardless of your outcome.** **A verified
long-run track record, net of costs, with drawdowns shown, is the minimum evidentiary bar
and is almost never provided.**

---

## §17. Regulation and Tax

**⚠️ Jurisdiction-specific, and this is orientation only.**
**US**: **SEC and FINRA** (securities), **CFTC and NFA** (futures and retail FX),
**pattern day trader rule** (§9 → `trading-styles-arbitrage-forex-and-defi`), **Reg T margin**, **wash sale rule** (⚠️ **a loss is
disallowed if you repurchase substantially identical securities within 30 days either
side — and it is a common and unpleasant surprise for active traders**), **SIPC** (⚠️ **which
protects against broker failure, NOT against losses**).
**EU/UK**: **MiFID II**, **ESMA leverage caps and mandatory risk disclosures**, **CFD
restrictions.**
**Crypto**: ⚠️ **fragmented and evolving; custody, exchange solvency and tax treatment all
vary significantly by jurisdiction.**
**⚠️ Tax**: **short vs long-term capital gains, mark-to-market elections, treatment of
derivatives, and — genuinely difficult in practice — crypto cost basis tracking.**
⚠️ **See an economics/accounting reference §17: rates change annually and this needs a
professional, not a document.**
