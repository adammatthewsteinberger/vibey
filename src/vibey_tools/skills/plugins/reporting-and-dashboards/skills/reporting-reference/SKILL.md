---
name: reporting-reference
description: "Use when correcting an analytics misconception, checking what moved in the semantic layer market or in natural-language querying where the benchmarks and the demos disagree (verified August 2026), looking up a threshold or performance figure, finding the canon, or needing a picker and a pre-ship checklist. Companion to the other reporting-and-dashboards skills."
---

# Reporting and Dashboards: Misconceptions, What Moved, Numbers, and Canon

> **Part 5 of 5** of the *Reporting and Dashboards* reference (plugin `reporting-and-dashboards`), covering §15–§20. Sibling skills: `reporting-architecture-modelling-and-aggregation-traps` (§0–§4), `reporting-semantic-layer-time-and-performance` (§5–§8), `reporting-dashboard-design-charts-and-alerting` (§9–§11), `reporting-access-control-embedded-and-testing` (§12–§14). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Dimensional modelling and the aggregation traps are permanent. Two areas moved. See §16 below for the semantic layer market and text-to-SQL.

> **Scope.** Written for engineers who have been handed "we need a dashboard" and
> discovered it is a harder problem than it looked. ⚠️ **§2 → `reporting-architecture-modelling-and-aggregation-traps` and §3 → `reporting-architecture-modelling-and-aggregation-traps` are where the silent
> wrong numbers come from, and they are the reason this document exists.**
>
> **⚠️ GOTCHA** boxes mark things that produce confidently wrong numbers rather than
> errors.
>
> **The three ideas that matter most:**
> 1. **⚠️ The failure mode is a plausible wrong number, not an exception.** A join that
>    double-counts, an average of averages, a timezone boundary — **all of these return
>    successfully and look reasonable.** Analytics has almost no natural error signal
>    (§2 → `reporting-architecture-modelling-and-aggregation-traps`, §3 → `reporting-architecture-modelling-and-aggregation-traps`).
> 2. **⚠️ A metric definition is an interface, and undefined interfaces diverge.** If
>    "active user" lives in six dashboards it has six definitions, and they will disagree
>    in a meeting. **This is the entire argument for a semantic layer** (§5 → `reporting-semantic-layer-time-and-performance`, §16.1).
> 3. **⚠️ Most dashboards are never looked at, and that is a design failure, not a user
>    failure.** A dashboard nobody opens cost real money and produces nothing. **Build for
>    a decision, not for coverage** (§9 → `reporting-dashboard-design-charts-and-alerting`).

---

## §15. Misconceptions

| Misconception | Correction |
|---|---|
| A successful query means a correct number | ⚠️ **Analytics fails silently. That's the core problem** (§0 → `reporting-architecture-modelling-and-aggregation-traps`, §3 → `reporting-architecture-modelling-and-aggregation-traps`) |
| Joining tables then summing is fine | ⚠️ **Fan-out multiplies your measures** (§3.1 → `reporting-architecture-modelling-and-aggregation-traps`) |
| You can join two fact tables via a dimension | ⚠️ **Cartesian product. Aggregate separately** (§3.2 → `reporting-architecture-modelling-and-aggregation-traps`) |
| All measures can be summed | ⚠️ **Semi-additive and non-additive measures exist** (§3.3 → `reporting-architecture-modelling-and-aggregation-traps`) |
| Average the regional conversion rates | ⚠️ **Recompute from components. Averages of ratios are wrong** (§3.3 → `reporting-architecture-modelling-and-aggregation-traps`) |
| Distinct counts roll up | ⚠️ **They don't. Recompute or use HLL** (§3.4 → `reporting-architecture-modelling-and-aggregation-traps`) |
| If every segment improves, the total improves | ⚠️ **Simpson's paradox** (§4 → `reporting-architecture-modelling-and-aggregation-traps`) |
| The average is a useful summary | ⚠️ **For skewed data, use percentiles** (§4 → `reporting-architecture-modelling-and-aggregation-traps`) |
| A metric target is a good measure | ⚠️ **Goodhart's law** (§4 → `reporting-architecture-modelling-and-aggregation-traps`) |
| Store timestamps in local time | ⚠️ **UTC, convert at presentation — but ask whose day it is** (§6 → `reporting-semantic-layer-time-and-performance`) |
| A day is 24 hours | ⚠️ **Not across a DST boundary** (§6 → `reporting-semantic-layer-time-and-performance`) |
| ISO week 1 is the first week of January | ⚠️ **It contains the first Thursday** (§6 → `reporting-semantic-layer-time-and-performance`) |
| MTD vs last month is a fair comparison | ⚠️ **8 days vs 30. The most common dashboard lie** (§6 → `reporting-semantic-layer-time-and-performance`) |
| Yesterday's number is final | ⚠️ **Late-arriving data. State a completeness window** (§6 → `reporting-semantic-layer-time-and-performance`) |
| Type 1 SCD is the simple default | ⚠️ **It silently rewrites history** (§2 → `reporting-architecture-modelling-and-aggregation-traps`) |
| Slow dashboard means a bigger warehouse | ⚠️ **Check partition pruning first** (§7 → `reporting-semantic-layer-time-and-performance`) |
| Real-time is better | ⚠️ **Usually unnecessary and an order of magnitude more expensive** (§8 → `reporting-semantic-layer-time-and-performance`) |
| Logic in the BI tool is fine for now | ⚠️ **Invisible, untested, and it's how definitions diverge** (§1 → `reporting-architecture-modelling-and-aggregation-traps`, §5 → `reporting-semantic-layer-time-and-performance`) |
| Truncating the y-axis is a style choice | ⚠️ **On bar charts it misrepresents by construction** (§10 → `reporting-dashboard-design-charts-and-alerting`) |
| Pie charts are fine for comparison | ⚠️ **Angle ranks poorly perceptually. Use bars** (§10 → `reporting-dashboard-design-charts-and-alerting`) |
| A choropleth of counts shows activity | ⚠️ **It shows population. Normalize** (§10 → `reporting-dashboard-design-charts-and-alerting`) |
| A dashboard filter enforces access | ⚠️ **Trivially bypassed. Enforce server-side** (§12 → `reporting-access-control-embedded-and-testing`, §13 → `reporting-access-control-embedded-and-testing`) |
| Schema tests cover analytics correctness | ⚠️ **A fan-out bug passes all of them. Reconcile to source** (§14 → `reporting-access-control-embedded-and-testing`) |
| More dashboards means more insight | ⚠️ **Most are never opened** (§9 → `reporting-dashboard-design-charts-and-alerting`) |
| Natural language querying has solved BI | ⚠️ **Enterprise accuracy is far below benchmark headlines** (§16.2) |

---

## §16. What Moved — verified August 2026

### 16.1 The semantic layer
**⚠️ It stopped being an optional BI feature.** **Gartner elevated it to essential
infrastructure in its 2025 Hype Cycle for BI and Analytics**, and the market has
consolidated around a handful of options.

**⚠️ The market splits four ways, and the split is the useful framing:**
- **Standalone/vendor-neutral** — **dbt Semantic Layer (MetricFlow)**, ⚠️ **described
  across multiple sources as the most widely adopted vendor-neutral approach**; **Cube**
  (⚠️ **headless and API-first — SQL, REST, GraphQL, MDX — with an Apache-2.0 open-source
  core, and the usual pick for embedded analytics and products**); **AtScale**.
- **Warehouse-native** — ⚠️ **and this is the genuinely new part: Snowflake Semantic Views
  reached SQL-query GA in March 2026, and Databricks Metric Views reached GA in April
  2026.**
- **BI-native** — **LookML** (⚠️ **and it's worth noting Google's $2.6bn Looker
  acquisition is widely read as having been for LookML, not the visualization layer**),
  **Power BI semantic models**, **Tableau Semantics**.
- **Context/catalog layers** sitting above them.

**⚠️ Two structural developments:**
- **The Open Semantic Interchange (OSI)** specification — ⚠️ **launched with dbt Labs and
  Snowflake backing and reported as finalized in January 2026** — **a vendor-neutral
  standard for moving semantic definitions between tools and AI systems.** ⚠️ **If it
  gains adoption it addresses the portability problem, which is currently the main
  argument against committing to any one layer.**
- **dbt Labs and Fivetran merged**, ⚠️ **reported as completed in April 2026** —
  consolidating ingestion, transformation and semantic modelling under one company.
  ⚠️ **Whether that's convenience or lock-in depends on how much you value platform
  independence, and it's a legitimate open question rather than a settled one.**

> **⚠️ GOTCHA — the trade-offs are concrete and the marketing obscures them.**
> ⚠️ **The dbt Semantic Layer requires dbt Cloud: MetricFlow is open source, but the
> serving layer that makes metrics queryable is a Cloud feature, so dbt Core alone won't
> do it.** **Warehouse-native layers are convenient right up until you need embedded,
> multi-warehouse, or agent access.** **BI-native layers are strongest inside their own
> platform, and portability is the price.**
>
> ⚠️ **And the honest constraint that applies to all of them, which one source states
> well: adoption fails on the unglamorous work** — **bootstrapping the model, keeping
> definitions consistent as systems evolve, and migrating logic as tools change.** **A
> technically correct metric definition that nobody owns, reviews or tests is not a
> solution.** ⚠️ **Choose the layer that matches how your team already ships, not the one
> with the best architecture diagram.**

### 16.2 ⚠️ Natural-language querying — read the benchmarks, not the demos
**⚠️ This is the clearest gap between marketing and evidence in the current BI market, and
the research literature is unusually blunt about it.**

**The benchmark progression tells the story:**
```
Spider 1.0    ⚠️ ~91% execution accuracy — 200 clean databases, 10–20 tables
BIRD          ⚠️ ~73% — "dirty" databases, real content, external knowledge needed
Spider 2.0    ⚠️ ~21% — ENTERPRISE conditions: 3,000+ column schemas,
              multiple SQL dialects, multi-step agentic workflows
```
> **⚠️ GOTCHA — that is not a gentle degradation, it is a cliff, and it is the number that
> matters for your organization.** ⚠️ **Frontier models reported at 17–21% on Spider 2.0
> against ~91% on original Spider.** **Your warehouse looks like Spider 2.0, not Spider
> 1.0.**

**⚠️ Why the benchmarks flatter, and each reason is independently documented:**
- **⚠️ Benchmark data is in the training corpus.** **A senior practitioner's summary in
  CACM puts it plainly: the data is "in the pile," and an LLM finds what it has seen
  before. Real warehouses sit behind enterprise access controls and are not in any
  training set.**
- **⚠️ BIRD itself has annotation errors** — **one analysis reports 52.8% annotation
  errors in certain subsets, with performance shifting between −3% and +31% after
  correction.** ⚠️ **Cross-benchmark numbers are not directly comparable, and the
  literature says so explicitly.**
- **⚠️ Real schemas are far larger.** **Even Spider 2.0 averages ~52 tables and ~800
  columns per database; enterprise warehouses exceed this.** **The BEAVER benchmark, built
  from actual data warehouses, finds off-the-shelf LLMs perform poorly on real enterprise
  data.**
- **⚠️ Production adds problems benchmarks don't model** — **LinkedIn's deployment study
  identifies ambiguous user intent, evolving schemas, and the need for explanation
  alongside results.**

**⚠️ The failure mode is the important part, and it's the same one as §3 → `reporting-architecture-modelling-and-aggregation-traps`**: **a wrong query
that runs successfully and returns a plausible number.** ⚠️ **Silent, scalable error** —
which is exactly why this belongs in the same document as the fan-out trap.

**⚠️ What actually helps, and it's the §5 → `reporting-semantic-layer-time-and-performance` argument again**: **point the model at a
governed semantic layer rather than raw tables.** **Metric definitions, declared joins,
and enforced row-level security constrain what the model can get wrong**, and ⚠️ **the
consistency test is the useful one to run: ask "total revenue last quarter" and then
"revenue growth quarter-over-quarter" and check the answers are mathematically
consistent.** **Systems where the calculation shifts with phrasing fail on anything
business-critical.**

⚠️ **Note the incentive structure when reading this material**: **semantic-layer vendors
have an obvious interest in the "agents need governed metrics" argument, and I've leaned
on the peer-reviewed benchmark literature rather than vendor blogs for the numbers.**
**The mechanism they propose is nonetheless well-supported.**

**⚠️ The defensible position**: **natural-language querying is a genuine productivity tool
over curated, governed data, and it is not a replacement for analysts or for a modelled
warehouse.** **Treat generated SQL as a draft requiring review**, ⚠️ **especially for
financial or executive reporting where a silently wrong number is expensive.**

---

## §17. Numbers

```
BENCHMARKS (text-to-SQL) ⚠️
Spider 1.0 ~91% · BIRD ~73% · ⚠️ Spider 2.0 (enterprise) ~21%
Human expert on BIRD ~92–93%
⚠️ Cross-benchmark figures are NOT directly comparable

PERCEPTION (Cleveland-McGill) ⚠️
position > length > angle > area > colour saturation
~8% of men have some colour vision deficiency

DASHBOARD
5–9 elements max · ⚠️ above-the-fold is what gets seen
Always show last-refreshed time

MODELLING
⚠️ Declare the grain first
SCD Type 1 = overwrite (history lost) · Type 2 = new row + validity dates
Fully / semi- / non-additive — ⚠️ know which every measure is

TIME
Store UTC · ⚠️ ISO week 1 contains the first Thursday
4-4-5 retail calendars · ⚠️ DST days are 23 or 25 hours

PERFORMANCE
⚠️ Partition pruning is the biggest single win — verify in the query plan
Columnar: SELECT * is disproportionately expensive
```

---

## §18. Books

| Author | Work | Why |
|---|---|---|
| **Kimball & Ross** | ***The Data Warehouse Toolkit*** | ⚠️ **§2 → `reporting-architecture-modelling-and-aggregation-traps`. Still the standard, thirty years on** |
| **Few** | ***Information Dashboard Design*** | ⚠️ **§9 → `reporting-dashboard-design-charts-and-alerting`. The book on why your dashboard isn't used** |
| **Few** | *Show Me the Numbers* | Table and chart design |
| **Tufte** | *The Visual Display of Quantitative Information* | ⚠️ **Foundational, opinionated, worth arguing with** |
| **Cleveland & McGill** | *"Graphical Perception"* (1984) | ⚠️ **§10 → `reporting-dashboard-design-charts-and-alerting`'s ranking. The primary source** |
| **Wilke** | ***Fundamentals of Data Visualization*** | ⚠️ **Free online, modern, excellent** |
| **Knaflic** | *Storytelling with Data* | Practical communication |
| **Wexler et al.** | *The Big Book of Dashboards* | ⚠️ **Real annotated examples — unusually useful** |
| **Reis & Housley** | *Fundamentals of Data Engineering* | The surrounding stack |
| **Huff** | *How to Lie with Statistics* | ⚠️ **Short, old, and still the best inoculation** |

**Practical**: **dbt documentation** (⚠️ **the testing and modelling patterns are good
regardless of whether you use dbt**), **Cube and MetricFlow docs** for semantic modelling
concepts, **the Spider/BIRD/Spider 2.0 papers** for §16.2, **ColorBrewer** and
**viridis** for palettes, and ⚠️ **your own warehouse's query-plan documentation, which
almost nobody reads and which explains most of your performance problems.**

---

## §19. Quick Reference

### 19.1 Picker
| Situation | Do |
|---|---|
| Modelling a new subject area | ⚠️ **Declare the grain, then star schema** (§2 → `reporting-architecture-modelling-and-aggregation-traps`) |
| Attribute changes over time | ⚠️ **SCD Type 2 unless you're sure history doesn't matter** (§2 → `reporting-architecture-modelling-and-aggregation-traps`) |
| Joining to a one-to-many | ⚠️ **Aggregate before joining** (§3.1 → `reporting-architecture-modelling-and-aggregation-traps`) |
| Two facts, one dimension | ⚠️ **Aggregate separately, then combine** (§3.2 → `reporting-architecture-modelling-and-aggregation-traps`) |
| A ratio across groups | ⚠️ **SUM(num)/SUM(denom), never AVG(ratio)** (§3.3 → `reporting-architecture-modelling-and-aggregation-traps`) |
| Distinct counts at multiple grains | ⚠️ **Recompute, or HLL if approximation is acceptable** (§3.4 → `reporting-architecture-modelling-and-aggregation-traps`) |
| Same metric in many places | ⚠️ **Semantic layer** (§5 → `reporting-semantic-layer-time-and-performance`) |
| Date arithmetic anywhere | ⚠️ **A date dimension table** (§6 → `reporting-semantic-layer-time-and-performance`) |
| Comparing an incomplete period | ⚠️ **Like-for-like, or label it unmistakably** (§6 → `reporting-semantic-layer-time-and-performance`) |
| Dashboard is slow | ⚠️ **Query plan → partition pruning → columns → pre-aggregate** (§7 → `reporting-semantic-layer-time-and-performance`) |
| Skewed data | ⚠️ **Percentiles, not the mean** (§4 → `reporting-architecture-modelling-and-aggregation-traps`) |
| Comparing categories | **Bar chart** (§10 → `reporting-dashboard-design-charts-and-alerting`) |
| Precise multi-dimensional values | ⚠️ **A table** (§10 → `reporting-dashboard-design-charts-and-alerting`) |
| Multi-tenant embedding | ⚠️ **Server-side tenant enforcement from a signed token** (§13 → `reporting-access-control-embedded-and-testing`) |
| Catching modelling errors | ⚠️ **Reconcile to the source system** (§14 → `reporting-access-control-embedded-and-testing`) |
| Evaluating a text-to-SQL tool | ⚠️ **Test on YOUR schema; check phrasing consistency** (§16.2) |

### 19.2 Pre-ship checklist
- [ ] What decision does this support? ⚠️ **If none, don't ship it** (§9 → `reporting-dashboard-design-charts-and-alerting`)
- [ ] Grain declared, and is every measure valid at it? (§2 → `reporting-architecture-modelling-and-aggregation-traps`)
- [ ] Any one-to-many joins — is fan-out handled? (§3.1 → `reporting-architecture-modelling-and-aggregation-traps`)
- [ ] Every measure classified additive / semi / non? (§3.3 → `reporting-architecture-modelling-and-aggregation-traps`)
- [ ] Ratios computed from components, not averaged? (§3.3 → `reporting-architecture-modelling-and-aggregation-traps`)
- [ ] Timezone semantics stated — whose day is it? (§6 → `reporting-semantic-layer-time-and-performance`)
- [ ] Partial periods labelled or compared like-for-like? (§6 → `reporting-semantic-layer-time-and-performance`)
- [ ] Late-arriving data policy stated, watermark shown? (§6 → `reporting-semantic-layer-time-and-performance`)
- [ ] Last-refreshed timestamp visible? (§8 → `reporting-semantic-layer-time-and-performance`)
- [ ] Every number has a comparison and a definition? (§9 → `reporting-dashboard-design-charts-and-alerting`)
- [ ] Reconciles to the source system? (§14 → `reporting-access-control-embedded-and-testing`)
- [ ] Row-level security enforced server-side, not by filter? (§12 → `reporting-access-control-embedded-and-testing`)
- [ ] Will anyone actually open this in a month? (§9 → `reporting-dashboard-design-charts-and-alerting`)

---

## §20. Method

**§1–§15 → `reporting-architecture-modelling-and-aggregation-traps`, `reporting-semantic-layer-time-and-performance`, `reporting-dashboard-design-charts-and-alerting`, `reporting-access-control-embedded-and-testing` and §17 rest on stable material** — **Kimball's dimensional modelling (1996),
Cleveland and McGill's perceptual work (1984), Few's dashboard design, and the
aggregation and additivity rules, which are properties of arithmetic rather than of
tools.** ⚠️ **The fan-out trap in §3.1 → `reporting-architecture-modelling-and-aggregation-traps` was a problem in 1998 and it is a problem in every
BI tool shipping today.** **None of that needed verification.**

**Two searches were run in August 2026**, on **the semantic layer market** and
**text-to-SQL accuracy.**

**Confidence.** **High** in §1–§15 → `reporting-architecture-modelling-and-aggregation-traps`, `reporting-semantic-layer-time-and-performance`, `reporting-dashboard-design-charts-and-alerting`, `reporting-access-control-embedded-and-testing`. ⚠️ **§3 → `reporting-architecture-modelling-and-aggregation-traps` is the section I'd most want read — those bugs
are common, they produce plausible wrong numbers rather than errors, and I have seen every
one of them described as a mystery rather than as the well-known trap it is.**

⚠️ **Two sourcing cautions.**

**§16.1's landscape is drawn largely from vendor and vendor-adjacent comparison content**,
and ⚠️ **almost every "best semantic layer tools 2026" article is published by a company
selling one.** **I have reported the structural facts that recur across independent
sources** — the four-way market split, dbt Semantic Layer's adoption position, Cube's
headless architecture and Apache-2.0 core, ⚠️ **the Snowflake (March 2026) and Databricks
(April 2026) GA dates, OSI's January 2026 finalization, and the dbt-Fivetran merger** —
**and I have deliberately included the trade-offs those articles tend to bury**,
especially **the dbt Cloud dependency for the serving layer** and **the adoption problem,
which the most candid source frames as the real reason semantic layers stall.**

⚠️ **§16.2 I have grounded deliberately in peer-reviewed benchmark literature rather than
vendor claims, because the gap between the two is the whole story.** **The Spider 1.0 →
BIRD → Spider 2.0 progression from ~91% to ~73% to ~21% comes from the academic papers
themselves**, ⚠️ **including their own explicit caveat that cross-benchmark figures are
not directly comparable and that BIRD contains substantial annotation errors.** **The
CACM practitioner piece and the BEAVER and LinkedIn findings independently corroborate the
enterprise gap.**

⚠️ **I want to be clear about my own position there**: **the semantic-layer-plus-LLM
argument is one that semantic layer vendors have an obvious commercial interest in
making.** **I think the mechanism is nonetheless right — constraining a model to governed
metric definitions with declared joins genuinely removes classes of error** — **but the
supporting numbers in this document come from the benchmark literature, not from the
vendors making that argument.** **The defensible claim is a productivity tool over curated
data requiring review, not a replacement for analysts.**
