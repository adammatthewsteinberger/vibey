---
name: trading-evidence-microstructure-and-execution
description: "Use when getting oriented in how markets actually operate: what the outcome literature actually shows about retail trading performance, market microstructure including order books, market makers, spreads, latency and price formation, and orders and execution covering the order types, routing, slippage and the difference between the price you see and the price you get. Includes the router for the whole trading-mechanics reference."
---

# Trading Mechanics: What the Evidence Shows, Market Microstructure, and Orders and Execution

> **Part 1 of 5** of the *Trading Mechanics* reference (plugin `trading-mechanics`), covering §0–§3. Sibling skills: `trading-asset-classes-derivatives-and-analysis` (§4–§7), `trading-styles-arbitrage-forex-and-defi` (§8–§12), `trading-risk-costs-backtesting-and-psychology` (§13–§17), `trading-reference` (§18–§22). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Microstructure, derivatives pricing and the outcome literature are stable; the retail outcome studies and DeFi mechanics were re-checked for August 2026.

> **⚠️ Scope.** This explains how markets and instruments work. ⚠️ **It is not investment
> advice, and nothing here is a recommendation to trade anything.** **§1 is deliberately
> first, because the evidence on outcomes is the single most important input to any
> decision about participating, and it is systematically absent from most material on
> this subject.**
>
> **⚠️ GOTCHA** boxes mark mechanics that cost people money.
>
> **The three things that structure everything below:**
> 1. **⚠️ Trading is negative-sum after costs.** Every trade has two sides; the market as a
>    whole earns the market return, and costs come out before anyone's profit. **Short-term
>    trading is a zero-sum game against professionals, minus fees** (§1, §14 → `trading-risk-costs-backtesting-and-psychology`).
> 2. **⚠️ Your counterparty is usually better equipped than you are.** Faster, better
>    informed, better capitalized, and paid to take the other side. **This isn't a reason
>    not to understand markets; it's a reason to be precise about where any edge would
>    come from** (§2).
> 3. **⚠️ Position sizing determines survival; edge only determines the long-run
>    average.** **You can have a genuine edge and still be wiped out by sizing** (§13 → `trading-risk-costs-backtesting-and-psychology`).

---

## §0. Routing

| You want... | Go to |
|---|---|
| **The outcome evidence** | **§1** |
| Market microstructure | §2 |
| Orders and execution | §3 |
| Asset classes | §4 → `trading-asset-classes-derivatives-and-analysis` |
| **Derivatives** | **§5 → `trading-asset-classes-derivatives-and-analysis`** |
| Technical analysis, honestly | §6 → `trading-asset-classes-derivatives-and-analysis` |
| Quantitative and factor approaches | §7 → `trading-asset-classes-derivatives-and-analysis` |
| Swing trading | §8 → `trading-styles-arbitrage-forex-and-defi` |
| **Day trading** | **§9 → `trading-styles-arbitrage-forex-and-defi`** |
| **Arbitrage — real vs apparent** | **§10 → `trading-styles-arbitrage-forex-and-defi`** |
| Forex | §11 → `trading-styles-arbitrage-forex-and-defi` |
| **DeFi mechanics** | **§12 → `trading-styles-arbitrage-forex-and-defi`** |
| **Risk and position sizing** | **§13 → `trading-risk-costs-backtesting-and-psychology`** |
| Costs and frictions | §14 → `trading-risk-costs-backtesting-and-psychology` |
| **Backtesting pitfalls** | **§15 → `trading-risk-costs-backtesting-and-psychology`** |
| Psychology and harm | §16 → `trading-risk-costs-backtesting-and-psychology` |
| Regulation | §17 → `trading-risk-costs-backtesting-and-psychology` |
| Misconceptions | §18 → `trading-reference` |
| Numbers | §19 → `trading-reference` |
| Books | §20 → `trading-reference` |
| Quick reference | §21 → `trading-reference` |

---

## §1. ⚠️ What the Evidence Actually Shows

**⚠️ This is the best-documented question in the entire subject and it is almost never
presented to people considering it. The findings are consistent across countries,
decades, instruments and methodologies.**

**⚠️ Brazil (Chague, De-Losso & Giovannetti, 2020)** — the cleanest study, because it
observes **everyone**, not a self-selected sample. **They tracked all 19,646 individuals
who began day trading Brazilian equity futures between 2013 and 2015 using regulator
records.** Of those who **persisted more than 300 trading days**:
```
⚠️ 97%   lost money
⚠️ 1.1%  earned more than the Brazilian minimum wage
⚠️ 0.5%  earned more than a bank teller's starting salary
```
⚠️ **The authors' conclusion is unusually blunt for an academic paper: it is "virtually
impossible for individuals to day trade for a living, contrary to what course providers
claim."**

**⚠️ And the risk-adjusted picture is worse than the headline.** **Among the handful who
earned more than a bank teller, daily profit standard deviation ranged from roughly
$632 to $3,308.** ⚠️ **The single top earner averaged ~$310/day with a standard deviation
of ~$2,560** — **an 8:1 noise-to-signal ratio, which means even the winners cannot be
distinguished from luck.**

**⚠️ Taiwan (Barber, Lee, Liu & Odean, 2014)** — the entire stock exchange, 1992–2006,
around 360,000 day traders. ⚠️ **Fewer than 1% demonstrated predictably profitable
performance net of fees.** **The top ~0.14% did earn persistent profits surviving costs —
so skill exists — but they are extreme outliers.**

**⚠️ US (Barber & Odean, 2000)** — 66,000 accounts at a discount broker. ⚠️ **The most
active quintile earned 11.4% annually against a market return of 17.9%** — **underperforming
by roughly 6.5 percentage points per year.** **The authors attribute it to overconfidence:
active traders believed they knew more than they did.**

**⚠️ Note the honest complication in this literature.** **Shorter-window studies find
higher profit rates** — **around 20% net of fees in Taiwan and Taiwanese futures, ~25% in
Korean index futures, ~36% in one small US sample.** ⚠️ **The Brazilian authors' point is
precisely that these overstate it: once you condition on people who trade for a long
time, the odds collapse.** **Short-run profitability is substantially survivorship and
luck.**

> **⚠️ GOTCHA — read the failure rate correctly.** ⚠️ **It is not primarily a discipline
> problem or a knowledge gap, and framing it that way is what the education industry sells
> against.** **It is arithmetic: paying full transaction costs hundreds of times a year to
> extract a signal that barely exists at intraday horizons, against counterparties who are
> faster by orders of magnitude** (§2, §14 → `trading-risk-costs-backtesting-and-psychology`). ⚠️ **More screen time does not fix a negative
> expected value per trade.**

**⚠️ Aggregate scale**: **India's SEBI reported aggregate retail F&O losses exceeding
$21.5B over three years**; **Brazilian retail day traders lost an aggregate R$9.9 billion
across ~968,000 individuals during 2020–2023.**

**⚠️ What this does and doesn't imply.** **It does not mean markets are unbeatable —
professional firms extract returns consistently.** **It means the retail short-horizon
version of the activity has a documented base rate that is very bad**, and ⚠️ **that the
most reliable long-run finding in the whole literature is that trading frequency is
inversely related to returns.** **The counterweight is the boring one: broad, low-cost,
long-horizon exposure has a well-documented positive expected return, and it requires
almost no activity.**

---

## §2. Market Microstructure

**⚠️ Understanding who you're trading against is prerequisite to any claim of edge.**

**The order book**: bids and asks, **the spread**, depth, **price-time priority** in most
lit venues.
**Participants**: **market makers** (⚠️ **quote both sides, earn the spread, and manage
inventory — they are paid to be your counterparty**), **HFT** (⚠️ **latency arbitrage,
microsecond horizons, colocated**), institutions (⚠️ **working large orders over hours or
days to minimize impact**), retail, and **hedgers.**

**⚠️ Adverse selection is the concept that explains market maker behaviour**: **a market
maker loses to informed traders and profits from uninformed ones, so the spread is
partly compensation for that risk.** ⚠️ **Which means: if your order is easy to fill, that
is information about your order.**

**⚠️ Payment for order flow (PFOF)**: **retail orders are routed to wholesalers who
internalize them.** ⚠️ **The trade is real in both directions — retail typically gets
price improvement versus the displayed quote, and the wholesaler is paying for the flow
because it is profitable to trade against, being uninformed.** **"Free" commissions are
paid for somewhere.**
**Dark pools**, **lit venues**, **fragmentation and the consolidated tape**, **auctions**
(⚠️ **open and close auctions concentrate enormous volume, and the close is often the most
liquid moment of the day**).

**⚠️ Latency reality**: **professional infrastructure operates in microseconds; a retail
order travels over the public internet in milliseconds.** ⚠️ **That is roughly a
thousand-fold difference, and any strategy whose edge depends on speed is not available
to you.**

---

## §3. Orders and Execution

```
MARKET      ⚠️ guarantees execution, NOT price. Dangerous in thin markets or at the open
LIMIT       ⚠️ guarantees price, NOT execution. The default for anything not urgent
STOP        becomes a market order at the trigger — ⚠️ so it does NOT guarantee your price
STOP-LIMIT  ⚠️ may not fill at all, which in a fast move is the failure you didn't want
TRAILING STOP · IOC / FOK · MOC / LOC · ICEBERG
```
> **⚠️ GOTCHA — a stop-loss is not a loss limit.** ⚠️ **It triggers a market order, and in
> a gap or a fast move you fill far below it.** **Overnight gaps, halts and news events
> routinely blow through stops.** **"I had a stop at 5% so my risk was 5%" is false, and
> people learn this expensively.**

**Slippage** — the difference between expected and realized price. **Market impact** — your
own order moving the price, ⚠️ **which scales roughly with the square root of order size
relative to volume.** **Execution algorithms** (VWAP, TWAP, POV, implementation shortfall)
exist because of this.
**⚠️ Liquidity is not constant**: it evaporates exactly when you most want it, and
⚠️ **wide spreads at the open and close of illiquid names are where retail orders get
harvested.**
