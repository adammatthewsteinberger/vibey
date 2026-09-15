---
name: econ-methodology-and-microeconomics
description: "Use when evaluating an economic claim or reasoning about a market: how economics establishes what it claims and how strong the identification actually is, microeconomics including supply and demand, elasticity, marginal reasoning and consumer theory, firms and market structure from competition through monopoly, and market failure covering externalities, public goods, information asymmetry and the standard remedies. Includes the router for the whole economics-accounting-tax reference."
---

# Economics, Accounting and Tax: How Economics Knows What It Claims, Microeconomics, Market Structure, and Market Failure

> **Part 1 of 5** of the *Economics, Accounting and Tax* reference (plugin `economics-accounting-tax`), covering §0–§4. Sibling skills: `econ-macroeconomics-money-and-behavioural` (§5–§9), `econ-accounting-statements-accrual-and-ratios` (§10–§14), `econ-gaap-ifrs-audit-and-tax` (§15–§19), `econ-reference` (§20–§24). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
>    genuinely contested. **§1 is deliberately about epistemics before content.**
> 2. **⚠️ Accounting is a closed arithmetic system, and that's its power.** Double-entry
>    means the books balance by construction, so errors surface as imbalances. **Every
>    transaction has two sides, and the three statements are three views of one reality**
>    (§10 → `econ-accounting-statements-accrual-and-ratios`, §11 → `econ-accounting-statements-accrual-and-ratios`).
> 3. **⚠️ Profit is an opinion, cash is a fact.** Accrual accounting requires estimates —
>    useful life, collectability, completion. **A company can be profitable and insolvent,
>    and this combination has killed many of them** (§12 → `econ-accounting-statements-accrual-and-ratios`).

---

## §0. Routing

| You want... | Go to |
|---|---|
| **How economics knows things** | **§1** |
| Micro fundamentals | §2 |
| Firms and market structure | §3 |
| Market failure | §4 |
| **Macro aggregates** | **§5 → `econ-macroeconomics-money-and-behavioural`** |
| Money and monetary policy | §6 → `econ-macroeconomics-money-and-behavioural` |
| Fiscal policy and debt | §7 → `econ-macroeconomics-money-and-behavioural` |
| Trade and growth | §8 → `econ-macroeconomics-money-and-behavioural` |
| Behavioural findings | §9 → `econ-macroeconomics-money-and-behavioural` |
| **Double-entry** | **§10 → `econ-accounting-statements-accrual-and-ratios`** |
| **The three statements** | **§11 → `econ-accounting-statements-accrual-and-ratios`** |
| **Accrual and revenue recognition** | **§12 → `econ-accounting-statements-accrual-and-ratios`** |
| The judgement-heavy areas | §13 → `econ-accounting-statements-accrual-and-ratios` |
| **Ratio analysis** | **§14 → `econ-accounting-statements-accrual-and-ratios`** |
| GAAP vs IFRS | §15 → `econ-gaap-ifrs-audit-and-tax` |
| Audit and controls | §16 → `econ-gaap-ifrs-audit-and-tax` |
| **Tax fundamentals** | **§17 → `econ-gaap-ifrs-audit-and-tax`** |
| **Book-tax differences and deferred tax** | **§18 → `econ-gaap-ifrs-audit-and-tax`** |
| Entity choice | §19 → `econ-gaap-ifrs-audit-and-tax` |
| Misconceptions | §20 → `econ-reference` |
| **What moved** | **§21 → `econ-reference`** |
| Books | §22 → `econ-reference` |
| Quick reference | §23 → `econ-reference` |

---

# PART I — ECONOMICS

---

## §1. ⚠️ How Economics Knows What It Claims

**⚠️ Read this before §2, because it governs how much weight to put on everything after
it.**

**Economics is a social science studying systems with no controlled experiments at
national scale, reflexive participants who respond to predictions, and enormous
confounding.** ⚠️ **It is not weak by comparison to physics; it is doing a harder inference
problem with worse data.**

**⚠️ The reliability gradient is real and worth internalizing:**
```
STRONGLY ESTABLISHED   ⚠️ incentives change behaviour · opportunity cost · comparative
                       advantage · supply and demand direction · marginal analysis
                       · money creation mechanics · accounting identities
WELL-SUPPORTED         ⚠️ minimum wage effects at moderate levels (small, contested at
                       the margin) · trade raises aggregate output while creating
                       concentrated losers · rent control reduces supply long-run
CONTESTED MAGNITUDES   ⚠️ fiscal multipliers · elasticity of taxable income ·
                       the level of NAIRU · monetary transmission lags
GENUINELY DISPUTED     ⚠️ optimal top tax rates · the causes of secular stagnation ·
                       how much market power has risen · macro modelling foundations
```
**⚠️ The credibility revolution** — natural experiments, difference-in-differences,
regression discontinuity, instrumental variables, RCTs — **substantially improved
empirical microeconomics from the 1990s onward.** ⚠️ **Macro is harder because there is
one economy and no control group.**

> **⚠️ GOTCHA — be alert to three specific failure modes when reading economic claims.**
> ⚠️ **Model results presented as findings** — a DSGE model's output is a consequence of
> its assumptions, not evidence about the world.
> ⚠️ **Point estimates without confidence intervals** — "the multiplier is 1.5" usually
> summarizes a literature ranging from 0.5 to 2.5.
> ⚠️ **Normative conclusions smuggled in as positive analysis** — "efficient" is a
> technical term that says nothing about distribution, and efficiency-versus-equity is a
> value judgement the mathematics cannot settle.

---

## §2. Microeconomics

**⚠️ Opportunity cost is the foundational concept and the most under-applied**: **the value
of the best forgone alternative.** ⚠️ **"Free" almost never is, and capital that's already
yours still has a cost.**
**⚠️ Sunk costs are irrelevant to forward decisions** — and people, including firms,
systematically fail at this (§9 → `econ-macroeconomics-money-and-behavioural`).
**⚠️ Marginal thinking**: decisions are made at the margin, not on averages. **"Is this
profitable overall?" is the wrong question; "does one more unit add more than it costs?"
is the right one.**

**Supply and demand**: equilibrium where quantity supplied equals demanded. ⚠️ **Movement
ALONG a curve (price change) versus a SHIFT of the curve (anything else) is the
distinction most confused discussion turns on.**

**⚠️ Elasticity** — percentage response to a percentage change:
```
|E| > 1  elastic     |E| < 1  inelastic
```
> **⚠️ GOTCHA — tax incidence falls on the more INELASTIC side, regardless of who legally
> pays it.** ⚠️ **Who writes the cheque is irrelevant to who bears the burden.** **A tax on
> employers is partly borne by employees through wages; a tax on a good with inelastic
> demand is borne almost entirely by consumers.** **This is one of the most robust results
> in economics and one of the most consistently ignored in public debate.**

**Consumer and producer surplus**; **deadweight loss** (⚠️ **the value destroyed by
transactions that don't happen, not the revenue transferred**); **price ceilings produce
shortages and price floors produce surpluses** — ⚠️ **both are arithmetic consequences,
though the size and the distributional judgement are separate questions.**

---

## §3. Firms and Market Structure

**Costs**: fixed vs variable, **average vs marginal** (⚠️ **and marginal cost is what
drives supply decisions, not average**), economies and diseconomies of scale.
⚠️ **Economic profit subtracts opportunity cost, so zero economic profit means a normal
return — it is not the same as zero accounting profit** (§11 → `econ-accounting-statements-accrual-and-ratios`).

```
PERFECT COMPETITION  price takers, P = MC, ⚠️ zero economic profit long-run
MONOPOLISTIC COMP.   differentiated products, ⚠️ the common real case
OLIGOPOLY            ⚠️ strategic interdependence — this is game theory (see that reference)
MONOPOLY             price maker, ⚠️ P > MC, deadweight loss
MONOPSONY            ⚠️ single BUYER — increasingly emphasized in labour market research,
                     and it changes the minimum-wage prediction
```
**⚠️ Monopsony matters for a reason worth knowing**: **under monopsony, a minimum wage can
raise both wages and employment** — the opposite of the competitive prediction. ⚠️ **This
is a large part of why the minimum-wage literature is genuinely contested rather than
merely politicized.**

**⚠️ Network effects, switching costs and two-sided markets** produce concentration
without conventional barriers to entry, **which is why platform competition analysis is
hard and why the antitrust framework is being actively rethought.**

---

## §4. Market Failure

```
EXTERNALITIES        ⚠️ costs/benefits to third parties. Pigouvian taxes, cap-and-trade,
                     or Coasean bargaining where transaction costs are low
PUBLIC GOODS         ⚠️ non-rival AND non-excludable → free-riding → undersupply
COMMON POOL          ⚠️ rival but non-excludable → overuse. And note Ostrom's finding
                     that communities often solve this through institutions rather
                     than requiring privatization or state control
INFORMATION ASYMMETRY  ⚠️ adverse selection (hidden type) and moral hazard (hidden
                     action) — see a game-theory reference §9
MARKET POWER         §3
```
**⚠️ The theory of the second best is the caveat that gets omitted**: **if one market has
an unfixable distortion, correcting a distortion elsewhere does not necessarily improve
welfare.** ⚠️ **Piecemeal "fixes" can make things worse, which is a genuine argument for
humility in policy design.**
**Government failure** — ⚠️ **regulatory capture, information problems, and the fact that
"the market failed" does not by itself establish that intervention will do better.**
