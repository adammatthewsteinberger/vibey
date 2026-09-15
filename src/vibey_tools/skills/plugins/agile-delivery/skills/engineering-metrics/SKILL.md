---
name: engineering-metrics
description: Use when measuring engineering team performance, setting up DORA metrics, using the SPACE framework, analyzing deployment frequency, lead time, change failure rate, MTTR, or presenting engineering productivity to leadership. Triggers on engineering metrics, team performance, productivity measurement, DORA, SPACE, OKRs for engineering, cycle time analysis, or any question about how to measure software teams without causing harm.
---

# Engineering Metrics

A practitioner framework for measuring software delivery performance, team health, and engineering productivity. Grounded in the DORA research program (*Accelerate*, Forsgren, Humble, Kim, 2018), the SPACE framework (Forsgren, Storey et al., 2021), and empirical findings from 39,000+ DevOps professionals.

**Core principle: never use a single metric. Combine at least three dimensions, and always balance quantitative system telemetry with qualitative surveys.**

---

## The Measurement Hierarchy

Not all metrics are equal. Use this hierarchy to guide which metrics to invest in first:

1. **DORA four key metrics** — validated predictors of organizational performance; start here
2. **SPACE framework** — multidimensional balance; prevents gaming any single dimension
3. **Cycle time breakdown** — where to find bottlenecks in your specific system
4. **OKR structure** — connect sprint metrics to business outcomes
5. **Anti-patterns to avoid** — what not to measure and why

---

## DORA Four Key Metrics

The four key DevOps metrics from the DORA research program measure two dimensions of software delivery: **throughput** (Deployment Frequency, Lead Time) and **stability** (Change Failure Rate, Recovery Time). Elite teams achieve high throughput *and* high stability simultaneously — they are not trade-offs.

### 2024 Benchmarks

| Metric | Elite | High | Medium | Low |
|---|---|---|---|---|
| **Deployment Frequency** | Multiple per day | Daily to weekly | Weekly to monthly | Monthly to 6 months |
| **Lead Time for Changes** | < 1 day | 1 day – 1 week | 1 week – 1 month | 1–6 months |
| **Change Failure Rate** | 0–5% | ~10% | ~15% | 16–30%+ |
| **Failed Deployment Recovery Time (FDRT)** | < 1 hour | < 1 day | < 1 day | 1 week – 1 month |

**Important nuances:**
- Performance tiers are derived via **cluster analysis from annual survey data** — they shift year to year, not fixed targets
- DORA renamed MTTR to **"Failed Deployment Recovery Time" (FDRT)** and added **Reliability** as a fifth metric
- 19% of respondents reached Elite, 22% High in the 2024 survey
- The 2024 report found AI tools boost individual productivity but correlate with **worsened** software delivery performance at the team level — second consecutive year of this finding

### Metric Definitions

**Deployment Frequency (DF)**
How often code is successfully deployed to production (or released to end users). This is a proxy for batch size — teams that deploy multiple times per day are shipping small, low-risk changes continuously.

- Elite teams deploy **208–973× more frequently** than low performers
- Measure: pipeline run data; count successful production deployments per time period

**Lead Time for Changes (LT)**
Time from a code commit being made to that code being successfully running in production. Measures the speed of your delivery pipeline end-to-end.

- Measure: commit timestamp → production deployment timestamp
- Most CI/CD tools (Azure DevOps, GitHub Actions) can compute this via commit-to-release linking
- Long lead times indicate bottlenecks in review, testing, or deployment processes

**Change Failure Rate (CFR)**
Percentage of deployments that result in degraded service or require remediation (rollback, hotfix, forward-fix). Lower is better; elite teams have < 5% of deployments causing incidents.

- Measure: tag failed deployments in release pipelines; `(failed deployments / total deployments) × 100`
- Important: this measures deployments that caused incidents, not deployments that were technically successful

**Failed Deployment Recovery Time (FDRT)**
How quickly a team can restore service when a deployment causes an incident. Measures resilience and operational capability.

- Previously called MTTR (Mean Time to Recover/Restore)
- Measure: incident creation timestamp → incident resolution timestamp, filtered to incidents caused by deployments
- Elite < 1 hour requires robust monitoring, clear runbooks, and practiced incident response

### Instrumenting DORA in Azure DevOps

```
Deployment Frequency:
  - Query: release pipeline runs to Production environment
  - Automate: Azure DevOps Analytics → custom widget or Power BI report
  - Tag each release with deployment date

Lead Time:
  - Requires commit-to-production timestamp linking
  - Use AB#<WorkItemID> references in commits to link work items to PRs to builds to releases
  - Azure DevOps automatically creates these links when conventions are followed
  - Report: average time from first commit in work item to production deployment

Change Failure Rate:
  - Tag failed deployments in release pipeline with a "FAILED" custom field
  - Calculate: COUNT(failed) / COUNT(total) per time window
  - Include both rollbacks and hotfixes in "failed" count

FDRT:
  - Requires integration with incident tracking (Azure DevOps, ServiceNow, PagerDuty)
  - Measure: incident.created_at to incident.resolved_at for incidents tagged deployment-related
  - Filter to P1/P2 incidents only for meaningful data
```

### DORA and CABs

A critical DORA finding: **External approval processes (CABs) are negatively correlated with all four DORA metrics and have zero correlation with change failure rate.** Teams with formal external CAB processes were 2.6× more likely to be low performers. Peer review during development + automated deployment gates outperforms human approval gates on both velocity and stability.

---

## SPACE Framework

The SPACE framework (Forsgren, Storey et al., 2021, *ACM Queue*) provides the holistic complement to DORA — measuring developer productivity across five dimensions to prevent gaming any single metric.

**Rule: Never use a single SPACE dimension alone. Combine at least three.**

### Five Dimensions

**S — Satisfaction and Well-being**
How developers feel about their work, tools, and team. Well-being directly predicts long-term productivity and retention.

What to measure:
- Developer satisfaction survey scores (quarterly pulse surveys)
- Employee Net Promoter Score (eNPS)
- Retention and voluntary turnover rate
- Reported burnout indicators (overtime hours, unplanned leave patterns)

Tools: Athenian, LinearB, Faros AI developer surveys; custom survey in Microsoft Forms or Culture Amp.

**P — Performance**
Whether the work is producing the intended outcomes. Distinct from activity — a developer can be highly active while producing no valuable outcomes.

What to measure:
- DORA metrics (the primary performance indicators)
- Reliability targets met (SLA/SLO adherence)
- Defect escape rate to production
- Customer-reported bugs per release

**A — Activity**
Counts of specific actions in the development process. Use cautiously — activity metrics alone mislead and are trivially gamed.

What to measure (with extreme caution):
- Commits per developer per week (directional only; never as a target)
- Pull requests opened and merged
- Code review participation rate (reviews given per developer)
- Build and test run frequency

**Never use activity metrics as individual performance targets.** The moment you set a commit count target, developers start making tiny commits. Use only as directional signals in aggregate.

**C — Communication and Collaboration**
How effectively developers work together and share information.

What to measure:
- PR review turnaround time (PR opened to first review; PR opened to merge)
- Onboarding effectiveness (time for new team members to ship their first production change)
- Documentation quality (tracked via usage, not just existence)
- Cross-team dependency resolution time
- Code review comment quality (directional — hard to measure mechanically)

**E — Efficiency and Flow**
How smoothly work moves through the system with minimal interruptions.

What to measure:
- Cycle time (active work start to completion)
- WIP (work in progress at any point in time)
- Context switches per developer per day (interrupt events)
- Time in meetings vs. deep work time (calendar analysis)
- Unplanned work percentage per sprint

### SPACE Dashboard Template

| Dimension | Metric | Current | Target | Trend |
|---|---|---|---|---|
| Satisfaction | Developer satisfaction score | 3.8/5 | 4.2/5 | ↑ |
| Satisfaction | Voluntary turnover (annualized) | 18% | <12% | → |
| Performance | Deployment frequency | 2/week | Daily | ↑ |
| Performance | Change failure rate | 12% | <5% | ↑ |
| Performance | Defect escape rate | 8% | <5% | → |
| Activity | PR review participation rate | 68% | >80% | ↑ |
| Communication | Avg PR review turnaround | 18 hrs | <8 hrs | ↑ |
| Communication | Onboarding time to first production deploy | 12 days | <5 days | → |
| Efficiency | Average cycle time | 6.2 days | <3 days | ↑ |
| Efficiency | WIP per developer | 3.1 | <2 | → |

---

## Cycle Time Breakdown

Cycle time (active work start to completion) is the most actionable flow metric. Break it into phases to identify bottlenecks.

### Cycle Time Phases

```
[Story pulled into In Progress]
       ↓
  CODING TIME (developer working)
       ↓
  PR OPEN (code complete, PR created)
       ↓
  REVIEW WAIT (waiting for first reviewer to engage)
       ↓
  REVIEW TIME (active review, back-and-forth)
       ↓
  MERGE WAIT (approved, waiting to merge / merge queue)
       ↓
  CI PIPELINE (build, test, scan — automated)
       ↓
  DEPLOY WAIT (waiting for deployment window or approval)
       ↓
  PRODUCTION (deployed)
```

### Typical Bottleneck Locations

| Bottleneck | Symptom | Fix |
|---|---|---|
| Review wait too long | PRs sit open > 4 hours before first review | Set team review SLA; use PR review rotation |
| PR size too large | Review time > 1 day; high change failure rate | Cap PRs at 400 lines; break stories into smaller items |
| Merge queue backup | Many approved PRs waiting to merge | Enable merge queue; move to trunk-based development |
| CI pipeline slow | Pipeline > 30 minutes; developers context-switch while waiting | Parallelize tests; cache dependencies; run fast tests first |
| Deploy wait | Code merged but not deployed for days | Remove manual deployment gates; automate deployment |
| Coding time too variable | Some stories take 1 day, others 2 weeks | Stories not broken down to 1–3 day items |

### Lead Time vs. Cycle Time

- **Cycle time** = active work start → completion (measures team efficiency)
- **Lead time** = request/commit → completion (measures customer experience)

A team with fast cycle time but slow lead time has a **queue problem** — work waits too long before anyone starts it. Track both; use cycle time for team improvement and lead time for stakeholder communication.

---

## OKR Structure for Engineering

OKRs drive transformation and align engineering work to business outcomes. KPIs monitor ongoing operational health. Use both — OKRs for improvement initiatives, KPIs for steady-state monitoring.

### OKR Template for Engineering

**Objective:** [Inspiring, qualitative statement of direction]
- **KR1:** [Measurable outcome, not activity] — from X to Y by [date]
- **KR2:** [Measurable outcome] — from X to Y by [date]
- **KR3:** [Measurable outcome] — from X to Y by [date]

Sprint Goals should derive from current-quarter OKRs. If a Sprint Goal cannot be traced to an OKR, question why the work is being done.

### Example Engineering OKRs

**Objective 1:** Make our delivery pipeline a competitive advantage
- KR1: Deployment frequency from 2/week to multiple times per day
- KR2: Lead time for changes from 3 days to under 4 hours
- KR3: Change failure rate from 15% to under 5%

**Objective 2:** Build the most reliable internal developer platform in the organization
- KR1: Achieve 99.9% uptime for CI/CD infrastructure (up from 99.2%)
- KR2: Reduce mean time to resolve tool incidents from 4 hours to under 30 minutes
- KR3: Zero P1 incidents caused by tool configuration errors

**Objective 3:** Make engineers love their developer experience
- KR1: Developer satisfaction score from 3.1 to 4.2/5
- KR2: Onboarding time to first production deploy from 12 days to under 5 days
- KR3: Reduce time spent on unplanned work from 35% to under 15% of sprint capacity

### Initiative Mapping
For each KR, define 1–3 initiatives (the "how"):

```
KR: Lead time < 4 hours
  Initiative 1: Parallelize test execution (pytest-xdist + matrix strategy)
  Initiative 2: Eliminate manual deployment approval gate to staging
  Initiative 3: Move to trunk-based development; eliminate feature branch delay
```

---

## Engineering Efficiency Ratios

Track the ratio of **value-creating work** to **toil** as a sprint-level metric.

### Feature Work vs. Toil

```
Feature Work % = (Sprint capacity on new features) / (Total sprint capacity) × 100
Toil %         = (Sprint capacity on unplanned work, incidents, support) / (Total) × 100
```

**Targets:**
- Feature work: > 70% of sprint capacity
- Planned improvements: 10–20% (tech debt, security, tooling)
- Toil (unplanned): < 15% of sprint capacity

If toil consistently exceeds 20%, the system has a stability or process problem that must be addressed before velocity can improve. Toil above 30% indicates a systemic issue.

### Tracking Toil
Tag all work items as Feature, Improvement, Toil, or Security in your project management tool. Report the ratio at each Sprint Review. Trend lines over quarters reveal whether system investment is paying off.

---

## DORA Assessment: Running a Team Assessment

### Self-Assessment Process
1. **Gather 2–3 months of deployment data** from your pipeline before the assessment
2. **Run a team survey** using the official DORA survey questions (available at dora.dev)
3. **Calculate your current tier** for each metric
4. **Identify your top constraint** — the single metric furthest from target
5. **Map improvement actions** to Sprint Backlog items

### One-Constraint Focus
Don't try to improve all four metrics simultaneously. Identify the single metric that is most limiting throughput or stability, and focus one quarter's improvement OKR on it.

Typical progression:
1. Start with **Deployment Frequency** — automation and trunk-based development unlock everything else
2. Then **Lead Time** — remove review and deployment bottlenecks
3. Then **Change Failure Rate** — invest in test coverage and deployment safety practices
4. Then **FDRT** — invest in observability, runbooks, and incident response practices

---

## Presenting Metrics to Leadership

### Executive Dashboard Principles

1. **Show trends, not snapshots** — a single data point is noise; 6–12 months of trend lines tell a story
2. **Benchmark against DORA tiers** — "we're Medium, targeting High by Q3" is more meaningful than raw numbers
3. **Connect to business outcomes** — deployment frequency → faster time to market; CFR → customer trust; FDRT → revenue protection
4. **Use three colors consistently** — Red (below Medium), Yellow (Medium/High), Green (Elite)
5. **Never show individual-level activity metrics** to leadership — this destroys psychological safety and causes gaming

### Executive Dashboard Template

```
Engineering Performance Dashboard — [Quarter]

THROUGHPUT
  Deployment Frequency:  2.3/day    ↑  [Elite ✓]
  Lead Time for Changes: 6.2 hours  ↑  [Elite ✓]

STABILITY
  Change Failure Rate:   8.2%       ↑  [High — target <5%]
  Recovery Time (FDRT):  47 mins    →  [Elite ✓]

DEVELOPER EXPERIENCE
  Satisfaction Score:    3.8/5      ↑  [Yellow — target 4.2]
  Cycle Time (avg):      3.1 days   ↑  [Improving]

THIS QUARTER'S FOCUS
  OKR: Reduce Change Failure Rate from 8.2% to < 5%
  Initiative: Expand integration test coverage to 80% of API endpoints
  Status: On track (currently at 67%, up from 52%)
```

### Handling the "Are People Working Hard Enough?" Question

When leadership asks about individual productivity, redirect to system performance:
- "We measure team output, not individual activity. Individual activity metrics cause gaming and harm collaboration."
- "The SPACE framework (Google/Microsoft Research, 2021) establishes that productivity is a multidimensional system property — it cannot be reduced to individual commits or story points."
- "What I can show you is how fast our system delivers value: deployment frequency, lead time, and change failure rate."

---

## Common Metrics Anti-Patterns

### Story Points as Productivity Metrics
**What goes wrong:** Teams inflate estimates, cherry-pick easy work, sacrifice quality for point counts. Comparing points across teams is meaningless — each team's estimates reflect unique domain complexity.

**Correct use:** Story points are team-internal planning tools for forecasting sprint capacity. Never a target, never compared across teams.

### Lines of Code
**What goes wrong:** Incentivizes verbose code; penalizes refactoring; rewards copy-paste over abstraction.

**Never use.** Not even directionally useful.

### Utilization Rate
**What goes wrong:** 100% utilization in a variable system causes cycle time to explode exponentially (Little's Law). Teams at 100% utilization have no capacity to handle surprises, help teammates, or improve processes.

**Target 80–85% utilization** to maintain flow efficiency. 15–20% slack is productive capacity, not waste.

### Coverage as a Target
**What goes wrong:** 100% coverage targets are gamed — trivial tests that don't validate behavior get written to hit the number. Teams pass coverage while having brittle, meaningless test suites.

**Correct use:** Coverage is a **floor** (minimum acceptable level), not a goal. Set a minimum threshold (e.g., 80%), track coverage deltas on PRs to prevent regression, and focus test investment on **critical paths** (authentication, data access, payment flows) rather than overall percentage.

### Velocity as Performance Target
**What goes wrong:** Goodhart's Law applies mercilessly. When velocity becomes a target, teams inflate estimates, cherry-pick easy work, and sacrifice quality for throughput. Comparing velocity across teams is meaningless.

**Correct use:** Velocity is a team-internal planning tool for sprint forecasting only. If velocity is declining, investigate why — but do not treat it as a performance problem in isolation.

### Single Metric Dashboard
**What goes wrong:** Any single metric can be optimized at the expense of everything else. Maximizing deployment frequency without maintaining change failure rate produces frequent broken deployments.

**Correct use:** Always use the DORA four together as a balanced set. Add SPACE dimensions to prevent gaming the DORA metrics.

---

## Using Metrics to Identify Systemic Problems (Not Blame)

### The Principle
Metrics should reveal **system problems**, not surface **individual failures**. The system produces the outcomes; individuals operate within the system. This mirrors Amy Edmondson's psychological safety research and Google SRE's blameless postmortem model.

### Investigation Pattern

When a metric deteriorates:
1. **Observe the trend** — is this one sprint or a sustained pattern?
2. **Hypothesize system causes** — what in the process, tooling, or architecture could produce this outcome?
3. **Test the hypothesis** — gather supporting data before drawing conclusions
4. **Identify the leverage point** — where in the system can one change produce the most improvement?
5. **Create an improvement story** — add a Backlog item; own the fix as a team

Example: Change Failure Rate increases over 3 sprints.
- Not: "The engineers are writing worse code"
- Investigate: Did test coverage drop? Was there a new area of the codebase with no integration tests? Did PR review thoroughness decrease (review turnaround time data)?
- Finding: New microservice was added with no contract tests; it fails when the provider changes its API
- Fix: Add Pact contract testing for this service; add to Definition of Done for new service creation

---

## Reliability as the Fifth DORA Metric

DORA added **Reliability** as a fifth metric (2021). It measures whether teams are meeting their reliability targets (SLOs/SLAs).

What to measure:
- SLO adherence rate (% of time service meets its defined objectives)
- Error budget consumption rate (how fast is the error budget being used?)
- Availability over 30/90-day rolling windows
- P95/P99 latency against defined targets

High performers on reliability are **3× more likely** to have adopted loosely coupled architectures (DORA finding). Reliability is an architectural outcome as much as an operational one.
