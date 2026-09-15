---
name: reporting-access-control-embedded-and-testing
description: "Use when analytics has to be secure, embedded in a product, or trustworthy over time: access control including row-level and column-level security and the multi-tenant cases, embedded analytics and its architectural and licensing considerations, and testing analytics — the assertions worth writing, reconciliation, and catching a metric regression before a stakeholder does."
---

# Reporting and Dashboards: Access Control, Embedded Analytics, and Testing Analytics

> **Part 4 of 5** of the *Reporting and Dashboards* reference (plugin `reporting-and-dashboards`), covering §12–§14. Sibling skills: `reporting-architecture-modelling-and-aggregation-traps` (§0–§4), `reporting-semantic-layer-time-and-performance` (§5–§8), `reporting-dashboard-design-charts-and-alerting` (§9–§11), `reporting-reference` (§15–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
>    in a meeting. **This is the entire argument for a semantic layer** (§5 → `reporting-semantic-layer-time-and-performance`, §16.1 → `reporting-reference`).
> 3. **⚠️ Most dashboards are never looked at, and that is a design failure, not a user
>    failure.** A dashboard nobody opens cost real money and produces nothing. **Build for
>    a decision, not for coverage** (§9 → `reporting-dashboard-design-charts-and-alerting`).

---

## §12. Access Control

**Row-level security** (⚠️ **a manager sees only their region — and the rule must be
enforced in the semantic or database layer, not in a dashboard filter, which is trivially
bypassed**), **column-level masking** for PII, **object-level** permissions.
**⚠️ The aggregation leak is the subtle one**: **someone with no row access to salaries but
access to averages can often infer individual values from a small enough group.**
**Minimum-group-size thresholds exist for this reason.**
**⚠️ And embedded analytics multiplies the risk** — **a tenant filter applied client-side
is not access control** (§13).

---

## §13. Embedded Analytics

**⚠️ Multi-tenancy is the whole problem.** **A tenant filter must be enforced server-side
from a signed token, never from a client-supplied parameter.**
**Approaches**: **iframe with a signed URL** (simple, limited styling), **SDK/JS
embedding**, ⚠️ **or headless/API — query a semantic layer and render in your own UI,
which gives full control and the most work** (§5 → `reporting-semantic-layer-time-and-performance`, §16.1 → `reporting-reference`).
**⚠️ Practical concerns**: per-tenant performance isolation (⚠️ **one large tenant should
not degrade everyone**), white-labelling, and **caching correctly per tenant — a cache key
that omits tenant identity is a data breach.**

---

## §14. Testing Analytics

**⚠️ Analytics code is under-tested relative to its blast radius, and the reason is that
the failures are silent** (§0 → `reporting-architecture-modelling-and-aggregation-traps`).
```
SCHEMA/CONTRACT   ⚠️ upstream column dropped or retyped — catch at the boundary
FRESHNESS         has data arrived?
VOLUME            ⚠️ row count anomalies — a 90% drop is usually a pipeline break
UNIQUENESS        ⚠️ the primary key really is unique — this catches §3.1 at the source
NOT NULL / accepted values / referential integrity
RECONCILIATION    ⚠️ does the total match the source system? THE most valuable test
BUSINESS ASSERTIONS  revenue non-negative, percentages in [0,100], grain preserved
```
**⚠️ Reconciliation against the system of record deserves emphasis.** **It's the only test
that catches modelling errors as opposed to data errors** — **a fan-out bug passes every
schema and null test cheerfully.**

**⚠️ Practices worth adopting**: **dbt tests or equivalent in CI**, **PR review of metric
definitions like any other code**, **staging environments with production-shaped data**,
**lineage so you know what breaks when a column changes**, **and version-controlled
dashboards where the tool allows it.**
