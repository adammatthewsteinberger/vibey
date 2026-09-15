---
name: reporting-architecture-modelling-and-aggregation-traps
description: "Use when the numbers on a dashboard are wrong or at risk of being wrong: the analytics architecture and where each layer's responsibility sits, dimensional modelling with facts, dimensions and grain, the aggregation traps — fan-out, the chasm trap, additivity, and why distinct counts do not decompose — and the metric definition pitfalls that make two dashboards disagree. Includes the router for the whole reporting-and-dashboards reference."
---

# Reporting and Dashboards: The Architecture, Dimensional Modelling, the Aggregation Traps, and Metric Definitions

> **Part 1 of 5** of the *Reporting and Dashboards* reference (plugin `reporting-and-dashboards`), covering §0–§4. Sibling skills: `reporting-semantic-layer-time-and-performance` (§5–§8), `reporting-dashboard-design-charts-and-alerting` (§9–§11), `reporting-access-control-embedded-and-testing` (§12–§14), `reporting-reference` (§15–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Dimensional modelling and the aggregation traps are permanent. Two areas moved. See §16 → `reporting-reference` for the semantic layer market and text-to-SQL.

> **Scope.** Written for engineers who have been handed "we need a dashboard" and
> discovered it is a harder problem than it looked. ⚠️ **§2 and §3 are where the silent
> wrong numbers come from, and they are the reason this document exists.**
>
> **⚠️ GOTCHA** boxes mark things that produce confidently wrong numbers rather than
> errors.
>
> **The three ideas that matter most:**
> 1. **⚠️ The failure mode is a plausible wrong number, not an exception.** A join that
>    double-counts, an average of averages, a timezone boundary — **all of these return
>    successfully and look reasonable.** Analytics has almost no natural error signal
>    (§2, §3).
> 2. **⚠️ A metric definition is an interface, and undefined interfaces diverge.** If
>    "active user" lives in six dashboards it has six definitions, and they will disagree
>    in a meeting. **This is the entire argument for a semantic layer** (§5 → `reporting-semantic-layer-time-and-performance`, §16.1 → `reporting-reference`).
> 3. **⚠️ Most dashboards are never looked at, and that is a design failure, not a user
>    failure.** A dashboard nobody opens cost real money and produces nothing. **Build for
>    a decision, not for coverage** (§9 → `reporting-dashboard-design-charts-and-alerting`).

---

## §0. Routing

| You want... | Go to |
|---|---|
| The architecture | §1 |
| **Dimensional modelling** | **§2** |
| **The aggregation traps** | **§3** |
| **Metric definition pitfalls** | **§4** |
| The semantic layer | §5 → `reporting-semantic-layer-time-and-performance` |
| **Time handling** | **§6 → `reporting-semantic-layer-time-and-performance`** |
| Query performance | §7 → `reporting-semantic-layer-time-and-performance` |
| Caching and freshness | §8 → `reporting-semantic-layer-time-and-performance` |
| **Dashboard design** | **§9 → `reporting-dashboard-design-charts-and-alerting`** |
| Chart selection | §10 → `reporting-dashboard-design-charts-and-alerting` |
| Alerting | §11 → `reporting-dashboard-design-charts-and-alerting` |
| Access control | §12 → `reporting-access-control-embedded-and-testing` |
| Embedded analytics | §13 → `reporting-access-control-embedded-and-testing` |
| **Testing analytics** | **§14 → `reporting-access-control-embedded-and-testing`** |
| Misconceptions | §15 → `reporting-reference` |
| **What moved** | **§16 → `reporting-reference`** |
| Numbers | §17 → `reporting-reference` |
| Books | §18 → `reporting-reference` |
| Quick reference | §19 → `reporting-reference` |

---

## §1. The Architecture

```
Sources → INGESTION → raw/landing → TRANSFORMATION → modelled tables
  → [SEMANTIC LAYER] → BI tool / API / embedded → humans and agents
                    ↘ alerting, exports, reverse ETL
```
**⚠️ ELT beat ETL because storage got cheap and warehouses got fast**: load raw, transform
in-warehouse, keep the raw layer so you can re-derive when definitions change.
⚠️ **The ability to reprocess history after fixing a definition is worth more than the
storage it costs.**

**Layering** (medallion, or staging/intermediate/marts — the names vary and the shape
doesn't):
```
Raw/bronze     ⚠️ immutable, source-shaped, never modified
Staging/silver cleaned, typed, deduplicated, renamed to conventions
Marts/gold     ⚠️ business-shaped: facts and dimensions, or wide tables
```
**⚠️ Resist transforming in the BI tool.** **Logic in a dashboard is invisible, untested,
unversioned and unreusable** — and it's how you get six definitions of the same metric
(§5 → `reporting-semantic-layer-time-and-performance`).

---

## §2. Dimensional Modelling

**⚠️ Kimball's star schema is 1996 and still correct, because it solves a problem that
hasn't changed: making a warehouse queryable by people who didn't build it.**

```
FACT table       ⚠️ measurements at a defined GRAIN, plus foreign keys
DIMENSION tables descriptive attributes you filter and group by
```
> **⚠️ GOTCHA — declaring the grain is the single most important modelling decision, and
> skipping it causes most fact-table bugs.** ⚠️ **"One row per order line per shipment" is
> a grain; "orders" is not.** **Every measure in the table must be true at that grain.**
> **If you find yourself unsure whether to sum a column, the grain was never properly
> declared.**

**Fact types, and the distinction drives everything downstream:**
```
Transaction     one row per event. ⚠️ Fully additive
Periodic snapshot  state at intervals (daily balance). ⚠️ NOT additive over time
Accumulating snapshot  one row per process instance, updated as it progresses
Factless        ⚠️ events with no measure — attendance, eligibility. Count the rows
```

**Dimensions**: **conformed** (⚠️ **shared across facts — this is what makes cross-process
analysis possible, and it's the hard organizational part**), **degenerate** (an order
number living on the fact), **junk** (⚠️ **flags bundled together rather than exploding
your dimension count**), **role-playing** (⚠️ **one date dimension viewed as order date,
ship date, return date**).

**⚠️ Slowly changing dimensions — get this wrong and history silently rewrites itself:**
```
Type 1  overwrite       ⚠️ history LOST. Last year's report changes when someone
                        moves territory. Often not what anyone wanted
Type 2  new row + validity dates + current flag  ⚠️ the standard for real history
Type 3  previous-value column   limited
Type 4/6  hybrids
```
⚠️ **The symptom of an unintended Type 1 is a historical report that no longer reproduces
— and by the time someone notices, the old values are gone.**

**One Big Table (OBT)** — ⚠️ **denormalize everything into a wide table.** **Columnar
storage makes this cheap and it's genuinely simpler for consumers.** ⚠️ **The costs are
real though: update anomalies, storage, and the fan-out problem (§3) baked in
permanently rather than at query time.** **Use it for a well-understood consumption
surface, not as the modelling layer.**

---

## §3. ⚠️ The Aggregation Traps

**⚠️ This section is the highest-value part of the document. These bugs return successful
queries with wrong numbers, and they are extremely common.**

### 3.1 Fan-out (the chasm trap)
> **⚠️ GOTCHA — joining a fact to a one-to-many relationship multiplies your measures.**
> ```
> orders (1 row, amount = $100)
>   JOIN order_items (3 rows)
>   → SUM(orders.amount) = $300     ⚠️ WRONG, and it looks fine
> ```
> ⚠️ **The join duplicated the order row three times, and the sum duplicated with it.**
> **This is the single most common cause of inflated revenue figures in BI**, and it is
> especially insidious because **the number is plausible — just too big.**
>
> **The fixes**: **aggregate before joining** (⚠️ **the cleanest**), use
> `SUM(DISTINCT ...)` carefully, use window functions, ⚠️ **or let a semantic layer handle
> it — Looker's `symmetric aggregates` and MetricFlow's join logic exist specifically for
> this** (§5 → `reporting-semantic-layer-time-and-performance`).

### 3.2 The chasm trap proper
**⚠️ Two fact tables joined through a shared dimension produce a Cartesian product.**
```
customers ← orders  (3 orders)
customers ← support_tickets (4 tickets)
JOIN both through customers → ⚠️ 12 rows. Both sums are wrong
```
**⚠️ The fix is never a join**: aggregate each fact separately and combine the results —
**a `FULL OUTER JOIN` on the aggregates, or a union-and-pivot pattern.**

### 3.3 Additivity
```
FULLY ADDITIVE      revenue, units — ⚠️ sum across every dimension including time
SEMI-ADDITIVE       ⚠️ balances, inventory, headcount — additive across everything
                    EXCEPT time. Summing December's daily balances is nonsense;
                    you want the last value, or an average
NON-ADDITIVE        ⚠️ ratios, percentages, averages, distinct counts.
                    NEVER sum, and never average
```
> **⚠️ GOTCHA — the most common non-additive error is averaging a ratio.**
> **Conversion rate for three regions: 10%, 20%, 30%. The company rate is NOT 20%.**
> ⚠️ **You must recompute from the components: `SUM(conversions)/SUM(visits)`.**
> **The average-of-averages answer is wrong whenever the denominators differ, which is
> essentially always.**

### 3.4 ⚠️ Distinct counts don't decompose
**`COUNT(DISTINCT user)` per region does not sum to `COUNT(DISTINCT user)` overall** —
⚠️ **a user active in two regions is counted twice.** **This breaks pre-aggregation,
breaks roll-ups, and breaks any cached daily table you were hoping to sum into a monthly
figure.**
**⚠️ The mitigations**: recompute at each grain (expensive but correct), or use
**HyperLogLog sketches**, which ⚠️ **are mergeable and approximate — and the approximation
is usually fine for a dashboard and not fine for billing.**

---

## §4. Metric Definition Pitfalls

**⚠️ Simpson's paradox** — a trend present in every subgroup can reverse in the aggregate.
⚠️ **This is not a curiosity; it happens in real business data whenever group sizes shift.**
**A treatment can improve outcomes for every segment while appearing to worsen results
overall, because the mix changed.** **The defence is to always be able to decompose a
metric by its main dimensions, and to be suspicious when an aggregate moves against all
its parts.**

**⚠️ Other definitional traps:**
- **Numerator/denominator mismatch** — ⚠️ **counting conversions over a different window
  or population than visits. Extremely common and rarely noticed.**
- **Survivorship** — ⚠️ **"average customer lifetime" computed only over churned customers
  is systematically wrong.**
- **Cohort vs snapshot** — "retention" means different things, and both are legitimate.
  ⚠️ **Say which.**
- **⚠️ Attribution** — first-touch, last-touch, linear, time-decay all give different
  answers from identical data, and **none is objectively correct.**
- **Active user** — ⚠️ **daily/weekly/monthly, what counts as activity, whether bots and
  internal users are excluded.** **Define it in writing.**
- **⚠️ Averages hide distributions.** **Report percentiles for anything latency-like or
  skewed. p50 and p95 tell you more than a mean, and a mean of a long-tailed distribution
  is close to meaningless.**
- **Goodhart's law** — ⚠️ **any metric used as a target ceases to be a good measure.**
  **Expect the metric to be optimized, sometimes destructively, and instrument the thing
  it's a proxy for.**
