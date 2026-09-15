---
name: process-engineering
description: "Comprehensive process engineering and project management reference covering methodology selection (Cynefin, Agile, Scrum, Kanban, SAFe, LeSS, PMBOK, PRINCE2), flow metrics (DORA, Little's Law, Monte Carlo forecasting, cycle time/throughput/WIP), Lean Six Sigma, OKRs, Shape Up, Continuous Discovery, Team Topologies, and the empirical evidence base for what actually works. Use when advising on process selection, scaling Agile, project governance, flow optimization, team structure, organizational design, delivery metrics, or Agile transformation."
---

# Process Engineering Reference Guide

## Core Principle: Context Fit Over Framework Loyalty

No single methodology wins. Context-fit and execution discipline win. The framework matters less than fit-to-context and execution quality — a point PMI's own data confirms by showing little performance variation across predictive, hybrid, and agile approaches when consistently applied.

**The 2025–2026 dominant pattern**: deliberate hybridization and "project-to-product" shift. 74% of organizations use hybrid/homegrown approaches.

---

## Cynefin Framework — The Meta-Framework for Method Selection

Developed by Dave Snowden (1999; HBR 2007 with Mary Boone, "A Leader's Framework for Decision Making").

| Domain | Decision Logic | Recommended Approach |
|---|---|---|
| **Clear/Obvious** | Sense–categorize–respond; best practice | Predictive/PMBOK, waterfall; rules and SOPs |
| **Complicated** | Sense–analyze–respond; good practice | Analysis, expert judgment, phase gates; RUP |
| **Complex** | Probe–sense–respond; emergent practice | Agile/Scrum/Kanban; safe-to-fail experiments |
| **Chaotic** | Act–sense–respond; novel practice | Incident response; act first to stabilize, then move toward Complex |
| **Disorder (center)** | Multiple domains at once | Decompose into known domains |

**Most damaging error**: treating Complex problems as merely Complicated — over-planning the unknowable. Product development is Complex; production incidents start Chaotic then become Complicated.

---

## The Empirical Reality: What the Evidence Actually Supports

### The Standish CHAOS Problem
The widely-cited claim "Agile Projects are 3× more likely to succeed than Waterfall" is not credible evidence. Eveleens & Verhoef's peer-reviewed critique (IEEE Software, 2010) applied Standish's own definitions to 5,457 real project forecasts and concluded the definitions are "misleading, one-sided, pervert the estimation practice, and result in meaningless figures." A best-in-class organization with unbiased estimates scored only 35% "success" under Standish's combined criteria. Standish eventually stopped publishing the report.

### What Rigorous Evidence Supports
- **Serrador & Pinto (IJPM, 2015)**: 1,002-project sample found Agile methods have a positive impact on both efficiency (time/budget/scope) and stakeholder satisfaction. The quality of vision/goals is a significant moderator.
- **Dybå & Dingsøyr (IST, 2008)**: systematic review of 1,996 studies, only 36 empirical; strength of evidence is "very low." The conclusion in 2024–2025 remains: evidence is "mixed and context-dependent."
- **TDD** (Rafique & Mišić meta-analysis, 27 studies): "small positive effect on quality but little to no discernible effect on productivity"; larger effects in industrial settings. Industrial studies (Nagappan et al.): 40–90% defect-density reduction, 15–35% more initial development time.

**The defensible claim**: iterative delivery, small batches, fast feedback, customer involvement, and engineering discipline *correlate* with better outcomes in complex, uncertain work.

---

## Agile Foundations

### Agile Manifesto (2001)
The values and 12 principles remain sound; the failure is in practice — "dark Agile," "zombie Scrum," cargo-culting structure without mindset. The gap between *doing* Agile and *being* Agile.

### XP Engineering Practices (Adoption Status, 2026)
- **TDD**: mainstream/standard.
- **CI**: mainstream/standard.
- **Pair programming**: contested; research evidence is "mixed," useful "in the right circumstances."
- **Refactoring**: mainstream; Kent Beck's *Tidy First?* (2023) frames structural "tidyings" as separated from behavioral changes, valued through optionality (coupling, cohesion, reversibility).

### Lean Software Development (Poppendieck)
Seven principles: eliminate waste, amplify learning, decide as late as possible, deliver as fast as possible, empower the team, build integrity in, see the whole.

**Seven software wastes**: partially done work, extra features, relearning, handoffs, delays, task switching, defects. Lean is the philosophical parent of both Kanban and much of Agile.

---

## Scrum (2020 Scrum Guide)

### Key 2020 Changes
- Eliminated "Development Team" — now just **Developers** within one Scrum Team (removes team-within-a-team and proxy-PO anti-patterns).
- Introduced the **Product Goal** — the commitment for the Product Backlog.
- Three **commitments**: Product Goal → Product Backlog; Sprint Goal → Sprint Backlog; Definition of Done → Increment.
- Sprint Planning now includes "Why" (Sprint Goal) as a third topic.
- Dropped the three prescribed Daily Scrum questions.
- Emphasized **self-managing** (not just self-organizing) team.
- Removed software-specific language to broaden applicability.

### Three Pillars, Five Values, Three Accountabilities
- **Pillars**: transparency, inspection, adaptation.
- **Values**: commitment, focus, openness, respect, courage.
- **Accountabilities**: Product Owner (value maximization), Scrum Master (process + impediment removal), Developers (building the Increment).

### Common Role Failures
- **Product Owner**: backlog administrator/proxy rather than value-maximizing visionary.
- **Scrum Master**: note-taker/meeting-scheduler/status-reporter rather than coach and impediment-remover.
- **Most wasted event**: the Retrospective, when action items are never followed through.
- **Sprint Review**: should be a business conversation about value, not demo theater.

### Backlog and Estimation
- **INVEST**: Independent, Negotiable, Valuable, Estimable, Small, Testable.
- **Estimation debate**: story points (Fibonacci) vs. #NoEstimates (flow-based forecasting) vs. t-shirt sizing.
- **Velocity**: legitimate planning aid; frequently abused as a performance/comparison metric.
- **EBM** (Evidence-Based Management): tracks Current Value, Unrealized Value, Ability to Innovate, Time to Market.

---

## Kanban and Flow Metrics

### Kanban Method (David J. Anderson)
Core principles: visualize workflow, limit WIP, manage flow, make policies explicit, implement feedback loops, improve collaboratively.

WIP limits work because of **Little's Law**: Average Cycle Time = Average WIP / Average Throughput. "Stop starting, start finishing."

**Classes of service**: Standard, Fixed Date, Expedite, Intangible — drive policy-based prioritization.

**STATIK** (Systems Thinking Approach to Introducing Kanban): standard onboarding method.

**Kanban Maturity Model**: describes organizational maturity (0–5), not board complexity.

**Use Kanban for**: evolutionary change, continuous flow, operations/support, product work without fixed iterations.
**Use Scrum for**: time-boxed product development with defined sprint goals.

### Flow Metrics (Daniel Vacanti)
Core metrics: **cycle time, lead time, throughput, WIP, and flow efficiency** (value-add time / total lead time — typically low in knowledge work).

**Monte Carlo simulation**: uses historical throughput to forecast "when will it be done?" probabilistically — without story-point estimation.

**Critical prerequisite**: enforced WIP limits and stable flow. Vacanti: "No WIP limit = no flow, which means no predictability."

**Important caveat**: Little's Law only *describes the past*; it cannot itself predict the future. Its assumptions (stable flow, comparable item sizes) must hold.

**Practical tools**: Service Level Expectations (e.g., "85% of items complete within X days"), cycle-time scatterplots, Cumulative Flow Diagrams (CFDs).

---

## Scaled Agile Frameworks

### SAFe 6.0 (2023)
- Retired the House of Lean; four core values: alignment, transparency, respect for people, relentless improvement.
- Principle #6 reframed around flow and **Value Stream Management** with eight flow accelerators.
- Added OKRs to the spanning palette; expanded AI/Big Data/Cloud guidance.
- Configurations: Essential, Large Solution, Portfolio, Full.
- The **ART** (Agile Release Train, ~50–125 people) is the value-delivery vehicle.
- **PI/Planning-Interval Planning**: cross-team alignment event.
- **WSJF** (Weighted Shortest Job First = cost of delay ÷ job size) for prioritization.
- **2025 adoption**: rebounded to ~44% (down from 53% peak, up from 26% low).

**Honest assessment**: SAFe adds value for genuine large-scale coordination but is widely criticized for bureaucracy, "SAFe theater," and diluting team-level agility.

### LeSS (Large-Scale Scrum)
Organizational simplicity: one Product Owner, one Product Backlog, multiple teams, one Increment. Philosophical counterweight to SAFe's coordination layers.

### Nexus (Scrum.org)
Integration-focused; coordinates 3–9 teams via a Nexus Integration Team. Stays closer to the Scrum Guide than SAFe.

### Scrum@Scale (Sutherland)
Uses Scrum-of-Scrums + Executive Action Team patterns.

### The Spotify Model — Cautionary Tale
Never a framework — a 2012 snapshot by Kniberg and Ivarsson; Spotify never fully implemented it. Jeremiah Lee's 2020 critique documents that copying squads/tribes/chapters/guilds without the underlying culture produces "new vocabulary for old problems." Co-authors and Spotify coaches have publicly told others not to copy it.

**Recommendation**: harvest the ideas (cross-functional teams, communities of practice/guilds), don't copy the org chart; prefer **Team Topologies** for practical guidance.

---

## Traditional/Predictive Project Management

### PMBOK Evolution
- **PMBOK 6**: 49 processes, 10 knowledge areas — the "ITTO" era.
- **PMBOK 7 (2021)**: radical shift — 12 principles + 8 performance domains; "how" → "what/why"; a 34-year paradigm shift.
- **PMBOK 8 (2025)**: rebalanced after practitioner feedback — 6 principles, 7 domains, 40 non-prescriptive processes re-embedded in a single unified publication.
- **PMP exam aligns to PMBOK 8 on July 9, 2026**: ~50% predictive, ~50% agile/hybrid across People/Process/Business Environment domains.

**Core PMBOK toolset** (still widely used): EVM (PV/EV/AC; SV/CV; SPI/CPI; EAC/TCPI), Critical Path Method, Monte Carlo schedule/cost risk analysis, WBS, RACI/RASCI/DACI.

### PRINCE2 7 (2023, PeopleCert)
- Integrated **People** as a central element.
- Renamed 7 Themes to **Practices**.
- Added **Sustainability** as a 7th performance target (alongside time, cost, scope, quality, risk, benefits).
- Raised exam pass marks from 55% to 60%.
- Strong in UK/Europe/Australia/government.

### Universal PM Concepts
- **Iron Triangle**: scope/time/cost with quality at center; extends to risk, resources, and benefits.
- **PMI 2024 redefinition of success**: "delivered value that was worth the effort and expense" — output → outcome shift.
- **Change management models**: ADKAR (individual change), Kotter's 8 steps (organizational), Bridges' Transition Model (emotional journey: Endings → Neutral Zone → Beginnings).
- **Theory of Constraints** (Goldratt) and Critical Chain underpin resource/throughput management.

### Certification ROI
- **PMP**: median US salary $135,000 vs. $109,157 non-certified (23.9% premium per PMI Salary Survey, 14th ed., 2025; 17% higher globally). Test on PMBOK 8 if exam is after July 9, 2026.
- **PSM (Scrum.org)**: more rigorous and cheaper than CSM; ~85% pass mark.
- **PMP + CSM**: recognized hybrid-delivery premium.
- Increasingly, demonstrated outcomes outweigh certification alphabet soup.

---

## Lean, Six Sigma, and Continuous Improvement

### Lean
- **Five principles**: define value, map the value stream, create flow, establish pull, pursue perfection.
- **7+1 wastes** (TIMWOOD + unused talent), plus Mura (unevenness) and Muri (overburden).
- Tools: VSM (current/future state), Kaizen events, 5S, A3 thinking, poka-yoke (in software: type safety, linters, automated checks).

### Six Sigma
- **DMAIC** (Define-Measure-Analyze-Improve-Control): for existing processes.
- **DMADV/DFSS**: for new process/product design.
- Statistical tools: control charts, Cp/Cpk, DOE; belt hierarchy (White → Master Black Belt).
- Target: 3.4 DPMO (defects per million opportunities).

**Important scope boundary**: Six Sigma applies well to repeatable, measurable operational processes in software/IT (deployment, support, defect reduction) but *poorly* to creative/discovery product development. DMAIC is a process-improvement tool, not a product-development one.

### Continuous Improvement Models
- **PDCA/Deming cycle**: Plan → Do → Check → Act.
- **Improvement Kata** (Rother): current condition → target condition → obstacles → experiments.
- **Senge's five-discipline learning organization**: systems thinking, personal mastery, mental models, shared vision, team learning.

---

## Modern Product and Delivery Frameworks

### OKRs (Grove/Doerr)
- Intel (Andy Grove, 1970s) → Google (John Doerr, 1999) → mainstream (*Measure What Matters*, 2018).
- Structure: an Objective (qualitative, inspiring) + 2–5 measurable Key Results.
- Target scoring: 0.7 for aspirational OKRs; consistent 1.0 signals insufficient ambition.
- **"OKRs drive change; KPIs monitor health"** — "KPIs with soul."

**Common failures**: too many objectives, Key Results that are activities (not outcomes), using OKRs as performance-review tools, sandbagging, over-aggressive cascading.

**Current best practice**: skip individual OKRs (Rick Klau's reversal — they become task lists and conflate with performance reviews). Focus on company/team levels with weekly/bi-weekly check-ins and quarterly scoring. OKR Institute: failure rate >60% when organizations first attempt them.

### Shape Up (Basecamp, Ryan Singer, 2019)
Core concepts:
- **Appetite**: time as a fixed constraint, not an estimate.
- **Shaping**: bounded problem + rough solution with rabbit holes and no-gos identified.
- **Betting table**: no backlog grooming; pitches compete for 6-week cycle slots.
- **6-week cycles + 2-week cool-down**: cool-down is for fixing, learning, and shaping the next cycle.
- **Hill Charts**: uphill = figuring out unknowns; downhill = execution of known work. More honest than burndowns.

**Shines for**: small/medium autonomous product teams that own their roadmap.
**Struggles with**: regulated/enterprise contexts, heavy operational loads, large teams with complex dependencies, external-stakeholder roadmap commitments — "no backlog" conflicts with sales/board reporting.

### Continuous Discovery (Teresa Torres)
Opportunity Solution Tree: **Outcome (root) → Opportunities (customer needs/pains) → Solutions → Assumption Tests/Experiments**.

- Weekly customer interviews by the product trio (PM + designer + engineer).
- Generate *multiple* solutions per opportunity (avoid confirmation bias).
- Break ideas into **assumptions**; test the riskiest first with lightweight experiments.
- **Dual-track Agile**: discovery + delivery running in parallel.

### JTBD (Jobs to Be Done)
- Christensen/Moesta: jobs, outcomes, constraints, Four Forces of Progress (push/pull/anxiety/inertia).
- **Outcome-Driven Innovation** (Ulwick): operationalizes JTBD with job statements and importance-satisfaction mapping.
- **Lean Startup** (Ries): Build-Measure-Learn; validated learning; the pivot/persevere decision.
- **MVP**: the most misunderstood concept in software — the smallest experiment to learn, not an underdone product.

---

## Flow Engineering and Delivery Metrics

### Flow Framework (Mik Kersten, *Project to Product*, 2018)
Value streams as the unit of measurement. Five flow metrics:
- **Flow Velocity**: items completed per time period.
- **Flow Efficiency**: active time / total time (reveals wait states).
- **Flow Time**: time from start to done.
- **Flow Load**: WIP.
- **Flow Distribution**: Features/Defects/Risk/Debt — the distribution reveals team health.

### DORA + Flow Together
DORA and Flow are complementary, not competing. DORA measures delivery performance; Flow connects delivery to business value.

**Third-party tooling**: LinearB, Sleuth, Faros AI, Jellyfish, Haystack, DX, Cortex.

### Value Stream Management Platforms
Planview (Tasktop), Broadcom, ConnectAll.

---

## Team Dynamics and Organizational Design

### Team Topologies (Skelton & Pais, 2019)
**Four team types**:
1. **Stream-Aligned**: owns a value stream end-to-end; the default team type.
2. **Platform**: reduces extraneous cognitive load via self-service "golden paths"; treats platform as a product.
3. **Enabling**: helps stream-aligned teams acquire capabilities; temporary engagement.
4. **Complicated-Subsystem**: handles high-specialist-knowledge components.

**Three interaction modes**: Collaboration (working closely together, temporary), X-as-a-Service (one team consumes another's capability), Facilitating (enabling team helping another upskill).

**Core principle**: **team cognitive load as the primary design constraint** (intrinsic/extraneous/germane).

**Conway's Law + Inverse Conway Maneuver**: design team boundaries to produce the desired architecture.

### Psychological Safety
- Google's Project Aristotle named it the #1 predictor of team effectiveness.
- Amy Edmondson: interpersonal risk and speaking up are prerequisites for effective retrospectives and failure learning.
- **Norm Kerth's Prime Directive**: "Regardless of what we discover, we understand and truly believe that everyone did the best job they could, given what they knew at the time..."

### Retrospective Formats
Formats (Start/Stop/Continue, 4Ls, DAKI, Sailboat, Starfish, 5 Whys, Lean Coffee) matter far less than follow-through on action items.

**Pre-mortems** (Gary Klein): forward-looking risk; imagine the project has already failed.

---

## AI's Impact on Process Engineering (2024–2026)

### The "Mirror and Multiplier" Thesis (DORA 2025)
AI amplifies whatever organizational system it enters — it does not fix broken ones.

| Study | Key Finding |
|---|---|
| DORA 2024 | AI adoption → −1.5% throughput, −7.2% stability per 25% adoption increase; cause was larger batch sizes |
| DORA 2025 | AI now correlates positively with throughput; instability still negative; AI is a "mirror and multiplier" |
| State of Agile 2025 | 63% report declining software quality (up 12 points YoY) despite more AI adoption and visibility |

**DORA 2025**: Value Stream Management converts individual AI gains into organizational performance; platform engineering (90% of orgs have at least one internal platform) is the foundation.

**AI in PM tools**: Atlassian Intelligence, Asana AI, Monday AI for planning/reporting; ML for estimation and risk identification; auto-theming retrospective feedback.

**PMI 2025**: only ~20% of PMs report strong practical AI skills — a significant capability gap.

### Practical Guidance
- Establish a clear, communicated AI stance before rolling out tools.
- Ensure healthy, unified data ecosystems and strong version control.
- Measure whether local AI productivity gains translate to organizational throughput via Value Stream Management.
- If AI adoption rises but stability/throughput fall, the root cause is batch size and testing discipline — not the AI.

---

## Recommendations by Stage

### Stage 1 — Diagnose Context Before Choosing (Week 0)
Use Cynefin to classify the work:
- Clear/Complicated + stable requirements + compliance → predictive/PMBOK or PRINCE2 with phase gates.
- Complex/uncertain product work → Scrum or Kanban with strong engineering practices.
- Operational/support flow → Kanban.
- Small autonomous product team that owns its roadmap → consider Shape Up.

### Stage 2 — Fundamentals Before Scaling (Months 1–3)
1. Instrument DORA + flow metrics (cycle time, throughput, WIP) to establish a baseline.
2. Enforce WIP limits and small batch sizes — these are precisely what make AI a multiplier rather than a destabilizer.
3. Establish a real Definition of Done and a follow-through mechanism for retrospective action items.
4. **Threshold**: do not adopt a scaling framework (SAFe/LeSS/Nexus) until at least one team demonstrates stable flow and a healthy DORA profile.

### Stage 3 — Scale Deliberately (Months 3–12)
1. Apply Team Topologies: stream-aligned teams owning value end-to-end, platform teams reducing cognitive load.
2. Connect delivery to strategy via OKRs (company/team level only) and EBM/Flow business metrics.
3. Prefer the lightest framework that resolves your actual dependencies (Nexus or LeSS before Full SAFe).
4. **Threshold to add governance/PMO**: when cross-team dependencies and portfolio trade-offs can no longer be resolved informally — build a value-adding, value-stream-oriented PMO, not a controlling one.

### Stage 4 — AI as Organizational Transformation (Ongoing)
- Establish clear AI stance, healthy data ecosystems, strong version control.
- Measure local AI gains → organizational throughput via Value Stream Management.
- Treat AI like a mirror: fix the underlying system first.

---

## Key Caveats

- **Standish CHAOS figures** are methodologically discredited (Eveleens & Verhoef, 2010). Do not use them as evidence.
- **DORA is correlation, not causation**: survey-based findings; do not use as cross-org benchmarks. The 2024→2025 reversal on AI's effect shows how fast these findings move.
- **TDD industrial case study effects** (40–90% defect reduction) are non-randomized and likely overstate effects relative to controlled experiments and meta-analyses (which show small/modest quality gains).
- **State of Agile 2025**: only 349 respondents (down from 788 in 2024); year-over-year comparisons should be read cautiously.
- **Survey populations are biased**: Stack Overflow and JetBrains surveys skew toward their own engaged users.
- **PMBOK 8 / PMP exam alignment** (July 9, 2026) and ongoing AI-in-PM capabilities are still settling.
