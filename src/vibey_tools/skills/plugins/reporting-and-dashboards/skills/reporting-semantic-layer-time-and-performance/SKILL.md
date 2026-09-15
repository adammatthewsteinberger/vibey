---
name: reporting-semantic-layer-time-and-performance
description: "Use when centralizing definitions or making queries fast: the semantic layer and what it does and does not solve, time handling including time zones, fiscal calendars, period-over-period comparison and the late-arriving data problem, query performance with modelling and engine-level techniques, and caching and freshness and how to reason about staleness honestly."
---

# Reporting and Dashboards: The Semantic Layer, Time Handling, Query Performance, and Caching

> **Part 2 of 5** of the *Reporting and Dashboards* reference (plugin `reporting-and-dashboards`), covering §5–§8. Sibling skills: `reporting-architecture-modelling-and-aggregation-traps` (§0–§4), `reporting-dashboard-design-charts-and-alerting` (§9–§11), `reporting-access-control-embedded-and-testing` (§12–§14), `reporting-reference` (§15–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Dimensional modelling and the aggregation traps are permanent. Two areas moved. See §16 → `reporting-reference` for the semantic layer market and text-to-SQL.

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
>    in a meeting. **This is the entire argument for a semantic layer** (§5, §16.1 → `reporting-reference`).
> 3. **⚠️ Most dashboards are never looked at, and that is a design failure, not a user
>    failure.** A dashboard nobody opens cost real money and produces nothing. **Build for
>    a decision, not for coverage** (§9 → `reporting-dashboard-design-charts-and-alerting`).

---

## §5. The Semantic Layer

**⚠️ The problem it solves is organizational, not technical**: **without one, metric logic
is duplicated into every dashboard, notebook, spreadsheet and application** — ⚠️ **and
duplicated logic diverges, so two directors arrive at a meeting with different revenue
numbers and the meeting becomes about the numbers.**

**A semantic layer defines entities, dimensions and metrics once, and compiles them to
SQL on demand.**
```
Entities/models   the tables and their keys
Dimensions        what you group and filter by
Measures/metrics  ⚠️ the aggregation logic, defined ONCE
Joins             ⚠️ declared with cardinality, so the tool can avoid §3.1
```
**⚠️ Declared join cardinality is the underrated feature.** **It's what lets the layer
apply symmetric aggregates and avoid fan-out automatically** — **a class of bug removed by
construction rather than by vigilance.**

**⚠️ What it buys**: one definition, governed access, consistent results across BI tools
and notebooks and APIs, version control and code review for business logic, and
⚠️ **a stable target for AI agents that would otherwise be querying raw tables** (§16 → `reporting-reference`).
**⚠️ What it costs**: another abstraction, a modelling language to learn, a query-
compilation step to debug, and **an adoption problem — a definition nobody owns or reviews
is no better than no definition.**

---

## §6. ⚠️ Time Handling

**⚠️ Time is where reporting bugs breed, and every item here has bitten real teams.**

**Timezones:**
- **⚠️ Store UTC, convert at presentation.** **Non-negotiable.**
- ⚠️ **But "daily revenue" is a business question with a timezone answer.** **Whose
  midnight?** **A US retailer reporting in UTC will have days that don't match the store's
  day, and the numbers will never reconcile to the POS system.**
- **⚠️ DST means some local days have 23 or 25 hours.** **Hourly comparisons across a DST
  boundary are not like-for-like, and one hour either repeats or doesn't exist.**

**⚠️ Calendars**: **fiscal years often don't start in January**; **4-4-5 retail calendars**
(⚠️ **so that comparable periods have the same number of weekends — and week-over-week
comparison in a 4-4-5 calendar is not the same as ISO weeks**); **ISO weeks** (⚠️ **week 1
contains the first Thursday, so early January can be week 52 of the previous year — a
genuine source of off-by-one-year bugs**).

**⚠️ Build a date dimension table.** One row per day with fiscal period, ISO week, holiday
flags, day-of-week, and relative offsets. ⚠️ **It's trivially cheap and it removes an
entire class of date-arithmetic bugs from every query downstream.**

> **⚠️ GOTCHA — partial periods are the most common dashboard lie.** ⚠️ **A
> "month-to-date vs last month" comparison on the 8th compares 8 days against 30, and it
> will look like catastrophe.** **Either compare like-for-like (MTD vs same-period-last-
> month), or label the partial period unmistakably.** **The number of executives who have
> been alarmed by a partial-period chart is not small.**

**⚠️ Late-arriving data** — **events land after the period closed.** **A dashboard read on
Monday and again on Wednesday shows different numbers for the same past day**, which
⚠️ **destroys trust faster than almost anything else.** **The fixes: a stated data-
completeness window, restating periods explicitly, or showing an "as of" watermark.**
**⚠️ Say which one you're doing, visibly.**

**Also**: **event time vs processing time**, **backfills after logic changes** (⚠️ **and
whether historical numbers are allowed to change is a policy decision, not a technical
one**), **and slowly changing dimension timing** (§2 → `reporting-architecture-modelling-and-aggregation-traps`).

---

## §7. Query Performance

**⚠️ Columnar storage is why analytics warehouses are fast, and it dictates the tuning
rules**: only the referenced columns are read, compression is excellent on repeated
values, and vectorized execution processes batches.
⚠️ **`SELECT *` in a columnar warehouse is far more expensive relative to a targeted query
than it is in a row store.**

```
PARTITIONING       ⚠️ prune whole files — usually by date. The single biggest win
CLUSTERING/SORTING co-locate related rows; helps range and equality filters
PRE-AGGREGATION    ⚠️ materialize common roll-ups. Trades freshness and storage for latency
INCREMENTAL MODELS ⚠️ process only new data — and handle late arrivals (§6)
```
**⚠️ Order of attack when a dashboard is slow**: **check partition pruning is actually
happening** (⚠️ **read the query plan; a function applied to the partition column will
silently disable it**), **then reduce scanned columns, then pre-aggregate, then cache.**
**⚠️ Buying a bigger warehouse is the last resort and the most common first move.**

**Cost control**: ⚠️ **most warehouse spend comes from a small number of queries and from
dashboards auto-refreshing for nobody.** **Instrument query cost by dashboard, and
⚠️ audit scheduled refreshes against actual viewership — this is usually the single
largest available saving.**

---

## §8. Caching and Freshness

```
Result cache       identical query → stored result. ⚠️ Free, and invalidation is the
                   whole problem
Pre-aggregation    materialized roll-ups (§7)
Extract/import     ⚠️ BI tool holds its own copy (Power BI import, Tableau extract).
                   Fast, and now you have two sources of truth to keep in sync
Live/DirectQuery   always current, always slower, ⚠️ and every viewer hits the warehouse
```
**⚠️ Freshness is a product requirement, not a technical default.** **Ask what decision the
data supports and how stale it can be** — ⚠️ **"real-time" is asked for far more often than
it is needed, and it costs an order of magnitude more.** **A daily-refreshed dashboard
that everyone trusts beats a real-time one that's frequently broken.**
**⚠️ Always show the last-refreshed timestamp.** **A stale dashboard that looks live is
worse than no dashboard.**
