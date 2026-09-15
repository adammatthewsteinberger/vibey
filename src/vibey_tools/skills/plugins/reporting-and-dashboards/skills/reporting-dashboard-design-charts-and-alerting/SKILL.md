---
name: reporting-dashboard-design-charts-and-alerting
description: "Use when designing what people actually look at: dashboard design including audience, hierarchy, defaults and the failure modes of the everything-dashboard, chart selection matched to the question being asked, and alerting including threshold design, noise, and why most alerting gets ignored."
---

# Reporting and Dashboards: Dashboard Design, Chart Selection, and Alerting

> **Part 3 of 5** of the *Reporting and Dashboards* reference (plugin `reporting-and-dashboards`), covering §9–§11. Sibling skills: `reporting-architecture-modelling-and-aggregation-traps` (§0–§4), `reporting-semantic-layer-time-and-performance` (§5–§8), `reporting-access-control-embedded-and-testing` (§12–§14), `reporting-reference` (§15–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
>    a decision, not for coverage** (§9).

---

## §9. Dashboard Design

> **⚠️ GOTCHA — most dashboards are built and then never opened, and the cause is
> predictable.** **They were built to display available data rather than to support a
> decision.** ⚠️ **The diagnostic question is: "what will someone do differently based on
> this?" If there's no answer, don't build it.**

**⚠️ Know which kind you're building — they have different rules:**
```
OPERATIONAL   ⚠️ monitored continuously; real-time; alerting-adjacent; few metrics,
              large, glanceable
ANALYTICAL    exploratory; filters and drill-down; for analysts
STRATEGIC/EXEC ⚠️ periodic; highly summarized; trend and target-focused; annotated
```
**Structure**: **inverted pyramid — the headline number first, then breakdown, then
detail.** ⚠️ **Above the fold matters; users do not scroll.** **Left-to-right, top-to-bottom
reading order for the primary language.** **Five to nine elements maximum.**

**⚠️ Context is what makes a number actionable, and it's what's usually missing**: **a
number alone is nearly useless.** **Give it a comparison (prior period, target,
benchmark), a trend, and a definition.** ⚠️ **"Revenue: $1.2M" tells you nothing.
"$1.2M, +8% vs last month, 94% of target" tells you what to do.**

**⚠️ Practical rules**: **consistent colour semantics** (⚠️ **pick red-bad/green-good or
brand colours and never mix**), **direct labelling over legends**, **no decoration**
(3D, gradients, unnecessary gridlines), **⚠️ accessible palettes — around 8% of men have
some form of colour vision deficiency, so never encode meaning in red-vs-green alone**,
**mobile consideration if executives read on phones**, and **document every metric
definition where it's displayed, not in a wiki nobody opens.**

---

## §10. Chart Selection

**⚠️ Cleveland and McGill's perceptual ranking is the evidence base and it's worth knowing
in order:**
```
1. Position on a common scale      ⚠️ most accurate — bar and line charts
2. Position on non-aligned scales
3. Length
4. Angle / slope
5. Area                            ⚠️ substantially worse
6. Colour saturation / density     least accurate
```
⚠️ **This is why bar charts beat pie charts for comparison, and it's a measured result
rather than a stylistic opinion.**

| Goal | Chart |
|---|---|
| Compare categories | ⚠️ **Bar (horizontal if labels are long)** |
| Change over time | **Line** (⚠️ many points) or **column** (few) |
| Part-to-whole | **Stacked bar; ⚠️ pie only for 2–3 slices, and reluctantly** |
| Correlation | **Scatter** |
| Distribution | ⚠️ **Histogram, box plot, violin — not a mean** |
| Precise values, many dimensions | ⚠️ **A table. Tables are underrated** |
| Single KPI | **Big number + sparkline + comparison** |
| Geographic | ⚠️ **Choropleth for rates, NOT counts — see below** |

**⚠️ The chart errors that mislead:**
- **Truncated y-axis on a bar chart** — ⚠️ **bars encode length, so truncation
  misrepresents by construction.** **Line charts may be truncated; bars may not.**
- **⚠️ Dual axes** — ⚠️ **you can manufacture any apparent correlation by choosing the
  scales.** **Avoid, or use indexed values on one axis.**
- **⚠️ Choropleth of raw counts** — **you have drawn a population map.** **Normalize.**
- **Pie charts with many slices**; **3D anything**; **rainbow colour scales**
  (⚠️ **perceptually non-uniform — use viridis or similar**).

---

## §11. Alerting

**⚠️ Alerting is where reporting becomes operational, and the failure mode is fatigue.**
**Threshold** (simple, brittle), **relative change**, **statistical/anomaly** (⚠️ **must
account for seasonality — Monday is not Sunday, and December is not November**),
**forecast-band**.
**⚠️ Rules that keep alerting useful**: **every alert names an action**; **route to someone
specific**; **suppress duplicates and storms**; ⚠️ **and delete alerts that are routinely
ignored — an ignored alert is worse than none, because it trains people to ignore the
channel.** **Data-quality alerts (freshness, volume, null rate, schema change) usually
matter more than metric alerts** (§14 → `reporting-access-control-embedded-and-testing`).
