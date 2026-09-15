---
name: delivery-velocity
description: Use when trying to ship software faster, improve team throughput, reduce cycle time, plan MVPs, prioritize features using WSJF, or implement fixed-time/variable-scope development. Triggers on delivery speed, velocity, throughput, MVP scoping, or any question about shipping faster. Also triggers on mentions of cycle time, batch size, WIP limits, Little's Law, CHAOS Report, decision latency, or contract structure for software projects.
---

# Delivery Velocity

An evidence-based playbook for maximum software delivery velocity. Every recommendation is grounded in specific empirical findings from DORA (39,000+ professionals), the Standish Group CHAOS database (50,000+ projects), QSM's 491-project analysis, McKinsey's Agile360 study (1,700+ teams), and peer-reviewed meta-analyses.

**The novel insight from this evidence synthesis: delivery speed is not primarily a technical problem — it is an organizational and contractual one.** The largest velocity gains come from removing decision bottlenecks, shrinking scope, and structuring the engagement correctly.

---

## Core Thesis: Fix Time, Vary Scope

The single highest-leverage structural decision for any delivery engagement is **fixed-time/variable-scope**.

**The evidence:**
- Standish Group CHAOS 2015: "Both satisfaction and value are greater when the features and functions delivered are much less than originally specified and only meet obvious needs."
- CHAOS 2020: Agile projects succeed at **3× the rate** of waterfall projects (42% vs. 13%)
- Small Agile projects: only a **4% failure rate**
- Jalote et al. (2004, *Journal of Systems and Software*): pipelined timeboxing delivers **n× the throughput** of serial iterations for an n-stage pipeline
- DuPont 1980s experiments: timeboxing achieved **80 function points per person-month** vs. 15–25 without — a 3–5× productivity gain

**Implementation — Basecamp Shape Up "appetite" model:**
1. Set a time budget (appetite) before scoping begins — e.g., "this initiative gets 2 weeks"
2. The team "hammers" scope down to fit the timebox
3. The question is never "how long will this take?" — it is "what can we ship in two weeks?"
4. Apply a **circuit breaker at cycle end**: if work isn't done, the project does not automatically continue — it is reassessed
5. Apply MoSCoW with **Must-Haves capped at 60% of total effort**, leaving buffer for de-scoping under pressure

Teamscope implemented this approach and **consistently shipped twelve new features per year** with immediate productivity improvements.

---

## Ruthless Scope Reduction

### The Feature Utilization Evidence

The evidence on feature utilization is damning:
- **Standish Group**: 64% of features are rarely or never used; **45% are never used at all**
- **Pendo 2019** (hundreds of software products): **80% of features are rarely or never used**; only **12% of features generate 80% of daily usage**

Every feature not built is delivery capacity reclaimed for features that matter.

### Lean Startup Validation

Camuffo et al.'s 2020 RCT — the most rigorous study ever conducted on Lean Startup methodology — tested scientific hypothesis-driven development across 116 Italian startups. The treatment group achieved **statistically significant shorter time to revenue** (P<0.05, Cox proportional hazard model), pivoted faster, and terminated unviable ideas earlier.

A 2024 replication across **759 firms in four RCTs** (Milan, Turin, London, Torino) confirmed these results. The mechanism: disciplined hypothesis testing prevents teams from building features nobody needs.

### Ruthless Scoping Process

1. **Identify the 12%** — for every proposed feature, ask "will this drive daily usage?" If not, cut it from the MVP
2. **Write a hypothesis** for every remaining feature: "We believe [feature] will [behavior change] for [user type]. We will know this is true when [measurable outcome]."
3. **Apply WSJF** to rank the remaining backlog (see below)
4. **Cap Must-Haves at 60% of sprint effort** — the remaining 40% is release pressure relief
5. **Question every Should-Have**: most Should-Haves become Could-Haves or are dropped under time pressure

---

## WSJF: Weighted Shortest Job First

WSJF (from Don Reinertsen's *The Principles of Product Development Flow*) provides the economic framework for prioritization and scope decisions.

### Formula
```
WSJF = Cost of Delay / Job Duration (size)
```

Higher WSJF = do this first. WSJF naturally favors high-value, short-duration work and penalizes bloated scope.

### Cost of Delay Components
Cost of Delay = User/Business Value + Time Criticality + Risk Reduction/Opportunity Enablement

Score each on a relative scale (1, 2, 3, 5, 8, 13) using the Fibonacci sequence. Sum the three components, then divide by job size.

### Why WSJF Matters
- **85% of product managers cannot quantify their Cost of Delay** (Reinertsen)
- Intuitive estimates of Cost of Delay differ by **50:1 across team members** without explicit discussion
- Making Cost of Delay explicit transforms prioritization from opinion-driven to evidence-driven
- WSJF prevents the common mistake of sequencing large, low-value items over small, high-value ones

### Practical Application
| Feature | Value | Time Crit. | Risk/Opp. | CoD | Size | WSJF |
|---|---|---|---|---|---|---|
| Login SSO | 13 | 8 | 5 | 26 | 3 | **8.7** |
| Dashboard export | 5 | 2 | 1 | 8 | 5 | 1.6 |
| Audit log | 8 | 13 | 8 | 29 | 8 | 3.6 |

Do Login SSO first (highest WSJF), then Audit log, then Dashboard export.

---

## Little's Law and WIP Limits

### Little's Law

```
Cycle Time = Work in Progress / Throughput
```

This is not a heuristic or a model — it is a **mathematical identity** (proven by John Little in 1961). If throughput stays constant, halving WIP halves cycle time. This relationship holds for any stable system.

**Empirical confirmation:** Sjøberg et al. (ESEM 2018) analyzed **8,000+ work items across 5 teams over 4 years** and confirmed empirically that "WIP correlates with lead time; lower WIP indicates shorter lead times."

### Why Large Batches Are Dangerous

Reinertsen's analysis: with 25 changes in one batch, assuming a 1% base error rate per change interaction, there is an **88% chance of at least one error**. Debugging complexity grows **quadratically** with batch size.

**TrainHeroic case study:** Reduced batch size from 10+ tickets per release to 1.25 tickets per release → **330% increase in deployment frequency per engineer**.

### WIP Limit Recommendations

- Set WIP limits at **~2/3 of team size** (Featureban simulations across ~90 teams)
- Example: 9-person team → WIP limit of 6
- When prioritizing which WIP item to advance, **always pick the oldest in-progress item first** (this causal mechanism reduced cycle time in the Featureban data, not just correlation)
- Break all work into items deliverable in **1–3 days**

### MoSCoW with WIP Discipline
- **Must-Have**: capped at 60% of sprint effort; these enter WIP first
- **Should-Have**: 20% of effort; pulled in only when Must-Haves clear
- **Could-Have**: the scope release valve — cut when time pressure appears
- **Won't-Have**: explicitly out; documented to prevent scope creep

---

## Pipelined Timeboxes: The Throughput Multiplier

Jalote et al.'s formalization: an **n-stage pipelined timebox delivers n times the throughput** of serial iterations at steady state.

**Example — 3-stage pipeline with 3-week cycles:**
- Stage 1: Requirements + design (weeks 1–3)
- Stage 2: Development (weeks 4–6)
- Stage 3: Testing + deployment (weeks 7–9)

In serial mode: one release every 9 weeks.
In pipelined mode: first release at week 9, then **one release every 3 weeks** thereafter — 3× the throughput.

**Implementation:** Structure work so multiple initiatives can be in different pipeline stages simultaneously. While one initiative is in development, the next is in design, and the prior one is being validated.

---

## Team Size: 5 ± 2 People

### The QSM Evidence

QSM's analysis of **491 completed projects** (Putnam, 1997) is the definitive dataset:
- **Teams of 3–7 are optimal**
- **2–5 person teams complete projects with ~1/3 the effort** of 7–14 person teams for comparable-sized systems
- Kate Armel's 2012 follow-up across 1,060 projects: large teams on small projects are **3× more costly** and deliver **2× as many defects**; on large projects, **4× more expensive** with **3× the defects**

Rodríguez et al. (2012, *Journal of Systems and Software*, ISBSG repository): teams of 9+ are "significantly less productive."

**Why:** Communication paths grow as n(n-1)/2. A 6-person team has 15 communication paths. A 25-person team has 300.

### Autonomy Compound Effect

- DORA 2019: organizations with formal external approval processes (CABs) are **2.6× more likely to be low performers** across all four metrics
- DORA found **no evidence that formal approval processes improve stability** — they slow delivery without compensating benefit
- McKinsey Agile360 (1,700+ teams): empowered product owners who made decisions through open dialogue completed features **4× faster**
- **Team autonomy and minimized cross-team dependencies** was the #1 driver of productivity (T-value: 5.18) in McKinsey's regression

### Staffing Recommendation
One cross-functional team of **5 ± 2 people** with all skills needed to ship independently:
- 1 product-focused person (empowered, can make binding scope decisions within 4 hours)
- 2–3 engineers (all seniority levels, cross-functional as needed)
- Deployment/design capability embedded in the team

Give the team full authority over technical and scope decisions without external approval.

---

## CI/CD as a Velocity Multiplier

### The Evidence

CircleCI 2025 (15 million workflows, 22,000+ organizations): top-quartile teams ship updates **3× faster** and complete critical workflows **5× faster** than bottom-quartile teams.

The 2017 State of DevOps Report: high performers automated **33% more** configuration management, **27% more** testing, **30% more** deployments, and **27% more** change approvals than low performers. The freed capacity went directly to feature development.

DORA's elite benchmark: **208–973× more frequent deployment** than low performers.

### Specific Practices Driving Elite Deployment Frequency

- **Trunk-based development** with ≤3 active branches and daily merges to trunk. Long-lived feature branches create merge events requiring stabilization periods.
- **Automated build and test pipelines** — 92% of successful CD teams use automated build tools, 87% use automated unit tests
- **Loosely coupled architecture** — one of the strongest predictors of CD success; elite teams meeting reliability targets are **3× more likely** to have adopted loosely coupled architectures
- **Containerization** — Docker/Kubernetes deployments achieve up to **40% reduction in build and deployment time** compared to VM-based systems (Debbiche, Ståhl, and Bosch)
- **Deploy every green build** — eliminate staging queues where possible
- **Feature flags** — decouple deployment (technical event) from release (business decision); enables instant rollback

### Procurify Case Study
Deployment time reduced from **1 hour 40 minutes to 10 minutes** after CI/CD implementation.

### Day-One Investment Rule
Invest in CI/CD infrastructure on day one — before writing application code. It is not overhead; it is the primary velocity multiplier for the engagement.

---

## Decision Latency: The #1 Delivery Killer

### The CHAOS Report Finding

Standish Group 2018 CHAOS Report — **Decision Latency Theory:**
- Projects with good decision latency (hours/days): **75% success rate**
- Projects with bad decision latency (weeks/months): **21% success rate**
- Failure rate inverts from **4% to 43%**

Jim Johnson, Standish Group chairman, to Jeff Sutherland: "I've finally worked out why Agile beats Waterfall. It's the speed of decision-making."

### The Economics

- A project generates approximately **one decision per $1,000 in labor cost** — a $1M engagement involves ~1,000 decisions
- If decisions take 4 hours each, decision-making consumes **as much time as actual delivery work**
- Organizations with average decision latency exceeding 3 hours **reverse or revisit 40% of their decisions**, inflating 1,000 decisions to 2,200+
- Simply reducing decision latency can improve project performance by **25%**

### Queue Problem: The Fuzzy Front End

Reinertsen's flow analysis: in most organizations, work items spend only **15–40% of their time being actively worked on** — the rest is waiting. The "fuzzy front end" — queue time before work begins — typically accounts for **80% of total lead time**.

A team with fast cycle time but slow lead time has a **queue problem**, not a process problem.

### Decision SLA Requirements

Non-negotiable contract requirements for fast delivery:
- Client provides a **dedicated product owner** who responds to questions within **4 business hours**
- Daily standup participation is contractual (or a named delegate with decision authority)
- Weekly demo is contractual — stakeholders must attend and provide feedback
- Any open question older than **24 hours** is escalated automatically to the product owner's manager
- Scope changes mid-cycle require product owner decision within **1 business day**

**Frame this requirement explicitly**: the team's velocity is capped by the client's decision speed. No amount of engineering talent compensates for organizational decision latency.

---

## What to Eliminate

The research converges on a clear list of delivery-killing practices. Each has specific evidence showing negative throughput impact.

| Practice | Evidence | Replace With |
|---|---|---|
| **Change Advisory Boards** | 2.6× more likely to be low performer (DORA 2019); no compensating stability benefit | Peer review (PRs) + automated deployment gates |
| **Large batch sizes** | 88% error probability at 25-change batch; quadratic debugging complexity (Reinertsen) | 1–3 day work items; daily trunk merges |
| **Large teams (7+)** | 3–4× more effort; 2–3× more defects (QSM) | Single team of 5 ± 2 |
| **Fixed-scope contracts** | 66% of technology projects end in partial/total failure (CHAOS 2020) | Fixed-time/variable-scope with 2-week billing cycles |
| **Heavy upfront documentation** | Waterfall creates 80% overhead (Standish); Agile halves overhead | Working software as primary artifact + lightweight ADRs |
| **Long-lived feature branches** | Merge complexity requiring stabilization periods | Trunk-based development; branches ≤3 days |
| **High capacity utilization (>80%)** | Reinertsen: high utilization in variable systems increases cycle time exponentially | Maintain **15–20% slack** in team capacity |
| **Annual/quarterly planning cycles** | Institutionalize large batch thinking | Continuous prioritization at each iteration boundary |
| **CAB-style governance** | DORA: "Approval by an external body simply doesn't work to increase the stability of production systems. However, it certainly slows things down." | Automated quality gates + peer review |

---

## Contract Structure for Velocity

### The Evidence

Jørgensen et al. (2017, *International Journal of Project Management*): **fixed-price contracts are connected with a higher risk of project failure** compared to T&M contracts. Mechanism: fixed-price requires extensive upfront specification before any code is written, freezes scope based on flawed initial understanding, and creates adversarial dynamics around change requests.

McKinsey: IT projects are delayed by **59% on average**, largely due to rigid scope commitments.

### Optimal Contract Model

**Time-and-materials with fixed-time iterations and a monthly budget cap:**
- Team bills for actual hours worked within 2-week cycles
- Scope negotiated at the start of each cycle based on deployed learnings
- Client pays for velocity, not for a specification document
- Monthly budget cap provides cost predictability without scope rigidity
- Formal scope review at each cycle boundary: client can reprioritize, add, or cut features

**Deliverable per cycle:** number of deployed increments (working software in production), not a scope specification.

This model aligns incentives: consultancy is paid for shipping; client gets steering flexibility.

---

## DORA Elite Benchmarks

| Metric | Elite | What It Means |
|---|---|---|
| **Deployment Frequency** | Multiple per day | Each team capability independently deployable |
| **Lead Time for Changes** | < 1 hour | Commit to production in under an hour |
| **Change Failure Rate** | < 5% | 95%+ of deployments succeed without rollback |
| **Failed Deployment Recovery Time** | < 1 hour | Incidents resolved within the hour |

Elite performers deploy **208–973× more frequently** than low performers while achieving **better stability** outcomes — not worse. Speed and stability are not trade-offs at elite performance levels.

DORA's 2024 finding: AI tools are associated with a **9% increase in bug rates** and a **91% increase in code review workload** at the team level — second consecutive year of this finding. The DORA thesis: "AI doesn't fix a team; it amplifies what's already there."

---

## The Delivery-First Operating Model: Seven Principles

1. **Fix time, vary scope** — this single structural decision improves success rates 3×
2. **Cut 80% of proposed features** — only 12–20% drive meaningful value; every eliminated feature is reclaimed capacity
3. **Work in batches of 1–3 days with explicit WIP limits** — Little's Law guarantees WIP reduction reduces cycle time; empirical data shows 330% throughput gains
4. **Staff a single team of 5 ± 2 with full decision authority** — QSM data shows 3× efficiency vs. larger teams
5. **Deploy continuously via automated CI/CD** — the 182× deployment frequency gap between elite and low performers is driven primarily by automation
6. **Contractually guarantee fast client decisions** — decision latency is the #1 predictor of project success; a 25% performance improvement is achievable by reducing it
7. **Eliminate every approval gate and governance ceremony** between the team and production — DORA proves these slow delivery without improving stability

---

## Applying the Playbook: Per-Engagement Checklist

### Week 0 (Setup)
- [ ] Establish 2-week fixed cycles and scope-as-release-valve agreement with client
- [ ] Apply WSJF to full proposed feature list; cut to 20% of original scope
- [ ] Write hypotheses for all Must-Have features
- [ ] Set up CI/CD pipeline with commit-to-production target of < 1 hour
- [ ] Configure trunk-based development; no long-lived branches
- [ ] Establish WIP limits at ~2/3 team size
- [ ] Define decision SLA with client (4-hour response commitment)

### Each Cycle Boundary
- [ ] Demo deployed increment to client (not a slide deck — working software)
- [ ] WSJF re-ranking of remaining backlog based on what was learned
- [ ] Scope review: cut Could-Haves, reassess Should-Haves
- [ ] Measure cycle time (commit to production); identify and remove top bottleneck
- [ ] Check WIP levels; reduce if above limit

### Signs Velocity Is Being Constrained (in order of frequency)
1. Decision latency > 4 hours → escalate decision SLA issue immediately
2. WIP above limit → enforce limit; do not start new work until existing work ships
3. Batch size > 3 days → break stories further before pulling into WIP
4. Long-lived branches → force merge to trunk; resolve conflicts now
5. Manual approval gates → automate or eliminate
6. Team > 7 people → split or reduce; do not add members to a late project
