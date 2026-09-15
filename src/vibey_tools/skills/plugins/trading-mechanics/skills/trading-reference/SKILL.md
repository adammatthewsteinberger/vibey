---
name: trading-reference
description: "Use when correcting a trading misconception, looking up a spread, margin, tax or outcome statistic, finding the canon, or needing the questions to answer before trading anything and a picker. Companion to the other trading-mechanics skills."
---

# Trading Mechanics: Misconceptions, Numbers, and Canon

> **Part 5 of 5** of the *Trading Mechanics* reference (plugin `trading-mechanics`), covering §18–§22. Sibling skills: `trading-evidence-microstructure-and-execution` (§0–§3), `trading-asset-classes-derivatives-and-analysis` (§4–§7), `trading-styles-arbitrage-forex-and-defi` (§8–§12), `trading-risk-costs-backtesting-and-psychology` (§13–§17). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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

## §18. Misconceptions

| Misconception | Correction |
|---|---|
| Most day traders are profitable with discipline | ⚠️ **97% of persistent Brazilian day traders lost money** (§1 → `trading-evidence-microstructure-and-execution`) |
| The failure rate is a knowledge problem | ⚠️ **It's cost arithmetic against a weak signal** (§1 → `trading-evidence-microstructure-and-execution`) |
| More screen time improves results | ⚠️ **Frequency is inversely related to returns** (§1 → `trading-evidence-microstructure-and-execution`, §14 → `trading-risk-costs-backtesting-and-psychology`) |
| A stop-loss caps your loss | ⚠️ **It triggers a market order. Gaps blow through it** (§3 → `trading-evidence-microstructure-and-execution`) |
| Zero commission means free | ⚠️ **The cost moved to spread and order flow** (§2 → `trading-evidence-microstructure-and-execution`, §14 → `trading-risk-costs-backtesting-and-psychology`) |
| Leveraged ETFs give 3× the index over time | ⚠️ **Daily rebalancing, volatility decay** (§4 → `trading-asset-classes-derivatives-and-analysis`) |
| Buying options is the safe side | ⚠️ **Theta works against you daily; you need three things to go right** (§5 → `trading-asset-classes-derivatives-and-analysis`) |
| Selling options is steady income | ⚠️ **Unbounded tail risk; the track record precedes the loss** (§5 → `trading-asset-classes-derivatives-and-analysis`) |
| Technical analysis is all noise | ⚠️ **Momentum is a robust documented anomaly** (§6 → `trading-asset-classes-derivatives-and-analysis`) |
| Technical analysis is a complete system | ⚠️ **Most pattern taxonomies don't survive testing** (§6 → `trading-asset-classes-derivatives-and-analysis`) |
| More indicators means better signal | ⚠️ **Same price series, more overfitting** (§6 → `trading-asset-classes-derivatives-and-analysis`, §15 → `trading-risk-costs-backtesting-and-psychology`) |
| Retail arbitrage opportunities exist | ⚠️ **Stale data, uncrossable prices, uncounted costs, or hidden risk** (§10 → `trading-styles-arbitrage-forex-and-defi`) |
| Impermanent loss is a fee | ⚠️ **It's the arbitrageur's profit, taken from you** (§12 → `trading-styles-arbitrage-forex-and-defi`) |
| Impermanent loss reverses | ⚠️ **Only if prices revert. LVR is the honest measure** (§12 → `trading-styles-arbitrage-forex-and-defi`) |
| Audited smart contracts are safe | ⚠️ **Audits reduce risk; audited protocols have failed** (§12 → `trading-styles-arbitrage-forex-and-defi`) |
| Leverage amplifies returns | ⚠️ **And brings forward ruin, nonlinearly** (§13 → `trading-risk-costs-backtesting-and-psychology`) |
| Positive expected value means you'll profit | ⚠️ **Path dependence and ergodicity say otherwise** (§13 → `trading-risk-costs-backtesting-and-psychology`) |
| A good backtest means a good strategy | ⚠️ **A Sharpe of 3 means you made a mistake** (§15 → `trading-risk-costs-backtesting-and-psychology`) |
| FX is a level playing field | ⚠️ **Zero-sum before costs; caps exist because of outcomes** (§11 → `trading-styles-arbitrage-forex-and-defi`) |
| SIPC protects against losses | ⚠️ **Against broker failure only** (§17 → `trading-risk-costs-backtesting-and-psychology`) |
| Trading is nothing like gambling | ⚠️ **Same reinforcement structure. Same warning signs** (§16 → `trading-risk-costs-backtesting-and-psychology`) |

---

## §19. Numbers

```
OUTCOME EVIDENCE ⚠️
Brazil (persistent day traders, >300 days): 97% lost money · 1.1% > minimum wage
  · 0.5% > bank teller starting salary
⚠️ Top earner: ~$310/day average, ~$2,560 daily standard deviation
Taiwan (360k traders, 15 yrs): <1% predictably profitable net of fees
  · top 0.14% earned ~37.9 bps/day after costs
US (Barber & Odean 2000): most active quintile 11.4% vs 17.9% market
  ⚠️ ~6.5 percentage points annual underperformance
Shorter-window studies: 19–36% profitable net of fees ⚠️ (survivorship)

COSTS ⚠️
0.1% round trip × 500 trades/yr = 50% of capital in costs
Drawdown recovery: −50% needs +100%

RULES
US pattern day trader: $25,000 equity for 4+ day trades in 5 days
Wash sale: 30 days either side

DEFI
Constant product x·y = k · ⚠️ 50% price move ≈ 5.7% below holding (IL)
Oracle attacks: $403.2M in losses in 2022

SIZING
Risk per trade commonly 0.5–2% · ⚠️ fractional Kelly (¼–½), never full
```

---

## §20. Books

| Author | Work | Why |
|---|---|---|
| **Chague, De-Losso & Giovannetti** | ***"Day Trading for a Living?"*** (SSRN 2020) | ⚠️ **Read the actual paper. It is short and decisive** |
| **Barber & Odean** | *"Trading Is Hazardous to Your Wealth"* (2000) | ⚠️ **The foundational retail-performance study** |
| **Malkiel** | ***A Random Walk Down Wall Street*** | ⚠️ **The strongest statement of the passive case** |
| **Bogle** | *The Little Book of Common Sense Investing* | The arithmetic of costs |
| **Harris** | ***Trading and Exchanges*** | ⚠️ **§2 → `trading-evidence-microstructure-and-execution` and §3 → `trading-evidence-microstructure-and-execution`, definitively. The microstructure reference** |
| **Hull** | *Options, Futures, and Other Derivatives* | ⚠️ **§5 → `trading-asset-classes-derivatives-and-analysis`. The standard** |
| **Natenberg** | *Option Volatility and Pricing* | Practitioner options |
| **Taleb** | *Dynamic Hedging* / *Fooled by Randomness* | ⚠️ **Tail risk and the luck/skill problem** |
| **Chan** | *Quantitative Trading* / *Algorithmic Trading* | §7 → `trading-asset-classes-derivatives-and-analysis`, §15 → `trading-risk-costs-backtesting-and-psychology` practically |
| **López de Prado** | ***Advances in Financial Machine Learning*** | ⚠️ **§15 → `trading-risk-costs-backtesting-and-psychology` rigorously. Unsparing about backtest overfitting** |
| **Mackay / Kindleberger** | *Extraordinary Popular Delusions* / *Manias, Panics and Crashes* | Bubbles, historically |
| **Lewis** | *Flash Boys* | ⚠️ **Contested in its claims, useful on §2 → `trading-evidence-microstructure-and-execution`'s structure** |

**⚠️ Note what is absent**: **no signal services, no courses, no "systems."** ⚠️ **§16 → `trading-risk-costs-backtesting-and-psychology`
explains why.**

---

## §21. Quick Reference

### 21.1 Questions to answer before trading anything
- [ ] ⚠️ **What is my edge, stated specifically — who is on the other side and why are they wrong?**
- [ ] Have I read §1 → `trading-evidence-microstructure-and-execution`'s evidence and does my plan explain why I'd be the exception?
- [ ] ⚠️ **Round-trip cost × expected trades per year — what does that consume?** (§14 → `trading-risk-costs-backtesting-and-psychology`)
- [ ] What is my risk per trade, and can I survive 20 consecutive losses? (§13 → `trading-risk-costs-backtesting-and-psychology`)
- [ ] ⚠️ **Is this money I can lose entirely without it changing my life?** (§13 → `trading-risk-costs-backtesting-and-psychology`)
- [ ] Am I measuring against buy-and-hold, net of costs, tax and my time? (§14 → `trading-risk-costs-backtesting-and-psychology`)
- [ ] If backtested — have I checked for look-ahead, survivorship and overfitting? (§15 → `trading-risk-costs-backtesting-and-psychology`)
- [ ] ⚠️ **What is my stop condition — the drawdown at which I stop, decided now?**
- [ ] Would I be comfortable showing a close friend my full P&L? (§16 → `trading-risk-costs-backtesting-and-psychology`)

### 21.2 Picker
| Question | Where |
|---|---|
| Should I expect to profit day trading? | ⚠️ **§1 → `trading-evidence-microstructure-and-execution`. The base rate is 97% losing** |
| Why did my stop fill so far below? | ⚠️ **Stops become market orders** (§3 → `trading-evidence-microstructure-and-execution`) |
| Why is my leveraged ETF underperforming? | Daily rebalancing decay (§4 → `trading-asset-classes-derivatives-and-analysis`) |
| Why is my option losing with the stock flat? | ⚠️ **Theta** (§5 → `trading-asset-classes-derivatives-and-analysis`) |
| Why did my LP position underperform holding? | ⚠️ **IL / LVR** (§12 → `trading-styles-arbitrage-forex-and-defi`) |
| Why did my backtest fail live? | ⚠️ **Costs, then look-ahead bias** (§14 → `trading-risk-costs-backtesting-and-psychology`, §15 → `trading-risk-costs-backtesting-and-psychology`) |
| How large should this position be? | ⚠️ **Risk budget ÷ stop distance; fractional Kelly** (§13 → `trading-risk-costs-backtesting-and-psychology`) |
| Is this arbitrage real? | ⚠️ **Find the risk you've missed** (§10 → `trading-styles-arbitrage-forex-and-defi`) |
| I'm trading to make back losses | ⚠️ **§16 → `trading-risk-costs-backtesting-and-psychology`. Stop and talk to someone** |

---

## §22. Method

**§2–§5 → `trading-evidence-microstructure-and-execution`, `trading-asset-classes-derivatives-and-analysis`, §7 → `trading-asset-classes-derivatives-and-analysis`, §10 → `trading-styles-arbitrage-forex-and-defi`, §11 → `trading-styles-arbitrage-forex-and-defi` and §13–§15 → `trading-risk-costs-backtesting-and-psychology` rest on stable material** — **market microstructure
(Harris), derivatives pricing (Hull, Black-Scholes 1973), the factor literature, and the
backtesting critique (López de Prado)** — and needed no verification.

**Two searches were run in August 2026**: **the retail outcome literature** and **DeFi
mechanics.**

**Confidence.** **⚠️ Very high in §1 → `trading-evidence-microstructure-and-execution`**, which is the most important section here. **The
Brazilian study (Chague, De-Losso & Giovannetti, SSRN 2020) observes the full population
of 19,646 entrants via regulator records rather than a self-selected sample, which
eliminates the selection bias that plagues most trading statistics.** **Its 97% / 1.1% /
0.5% figures are quoted identically across the SSRN abstract, mainstream financial press,
and multiple independent secondary sources.** **The Taiwan (Barber, Lee, Liu & Odean,
2014) and US (Barber & Odean, 2000) findings are peer-reviewed and long-standing.**
⚠️ **I have also included the complication honestly — shorter-window studies find 19–36%
profitability — because presenting only the worst number would be the mirror image of the
error I'm criticizing.** **The Brazilian authors' point stands: conditioning on
persistence collapses the odds.**

⚠️ **A sourcing note worth making explicitly.** **Much of the material that surfaces on
this topic is published by prop firms, brokers, signal services and trading-education
sites**, several of which appeared in my search results offering more encouraging numbers
alongside affiliate links. ⚠️ **I have anchored §1 → `trading-evidence-microstructure-and-execution` and §19 on the primary academic sources
and the SSRN abstract rather than on those summaries.** **Where I cite an aggregate figure
from a secondary source — SEBI's Indian F&O losses, the Senate breakeven figure — I've
attributed it as such.**

**High confidence in §12 → `trading-styles-arbitrage-forex-and-defi`'s DeFi mechanics**, drawn from the AMM literature including the
**loss-versus-rebalancing** work (Milionis et al.) and empirical MEV findings. ⚠️ **I've
foregrounded LVR over impermanent loss deliberately, because IL is path-independent and
understates the true adverse-selection cost, and the academic literature has moved on
while most consumer-facing DeFi material has not.**

⚠️ **On §16 → `trading-risk-costs-backtesting-and-psychology` I want to be direct about why it's there.** **Trading material almost never
discusses compulsion, and the structural similarity to gambling is well-documented rather
than rhetorical.** **Including the warning signs is, I think, the single most useful thing
this document can do for anyone it might apply to** — **and the Brazilian paper's explicit
framing against "what course providers claim" is the field's own acknowledgement that an
industry profits from the base rate in §1 → `trading-evidence-microstructure-and-execution`.**
