---
name: security-first-agile
description: Use when planning sprints, running retrospectives, setting up security champions programs, conducting threat modeling in Agile, building Scrum processes for security-focused teams, or working with OWASP SAMM, STRIDE, DORA metrics, or misuse stories. Essential for any security-meets-Agile workflow. Triggers on sprint planning, retrospectives, Definition of Done, security backlog, threat modeling, security champions, blameless postmortems, psychological safety, or any question about Scrum process for engineering teams.
---

# Security-First Agile Scrum

A synthesis of Scrum theory, security engineering, and people-first culture for enterprise engineering teams. Applies a strict precedence hierarchy: **Security First → People First → Agile/Scrum**. Security is non-negotiable; Scrum is the framework that enables it; people are the ones who make it work.

---

## Three Laws Precedence

Every process decision resolves conflicts in this order:

1. **Security First** — No sprint completes if security gates are open. No code ships with known Critical/High vulnerabilities. This is not a negotiation.
2. **People First** — Sustainable pace, psychological safety, and blameless culture are prerequisites for security. A burned-out or blame-averse team will hide vulnerabilities.
3. **Agile/Scrum** — The framework adapts to serve the first two laws, not the other way around. Scrum ceremonies are tools, not rituals.

---

## Scrum Fundamentals

Scrum is a **lightweight empirical process control framework** built on three pillars:
- **Transparency** — work and status visible to all
- **Inspection** — artifacts and progress examined frequently
- **Adaptation** — adjustments made when inspection reveals deviation

### The Five Events
| Event | Timebox | Purpose |
|---|---|---|
| Sprint | 1–4 weeks (fixed) | Container for all other events |
| Sprint Planning | ≤8 hrs (4-wk sprint) | Why/What/How — defines Sprint Goal |
| Daily Scrum | 15 minutes | Developer sync toward Sprint Goal |
| Sprint Review | ≤4 hrs | Inspect Increment, adapt backlog |
| Sprint Retrospective | ≤3 hrs | Inspect team process, commit to improvements |

### Three Artifacts and Their Commitments
| Artifact | Commitment |
|---|---|
| Product Backlog | Product Goal |
| Sprint Backlog | Sprint Goal |
| Increment | Definition of Done |

### Core Roles (Accountabilities)
- **Product Owner** — single voice for value; orders the backlog; makes binding scope decisions
- **Scrum Master** — serves team effectiveness; removes impediments; is NOT a project manager
- **Developers** — self-managing; own the Sprint Backlog; decide who does what, when, and how

**Velocity is a planning tool, never a performance target.** Comparing velocity across teams is meaningless. Goodhart's Law: when a measure becomes a target, it ceases to be a good measure.

---

## Security as Definition of Done

The DoD applies universally to every Increment. Security gates are mandatory — an item that does not pass is returned to the backlog, not presented at Sprint Review.

```
## Security Definition of Done Checklist
- [ ] SAST scan (Semgrep + CodeQL) — 0 Critical/High findings
- [ ] SCA scan (Snyk/Dependabot) — 0 Critical CVEs in dependencies
- [ ] Secrets scan (Gitleaks) — 0 leaked secrets in commits or diffs
- [ ] IaC scan (Checkov) — 0 High misconfigs (when infra changed)
- [ ] All DB queries use parameterized patterns (no string concatenation)
- [ ] All API endpoints carry [Authorize] with appropriate policy
- [ ] CORS policy explicitly whitelists allowed origins only
- [ ] Content Security Policy headers configured (no unsafe-inline)
- [ ] Security logging verified (structured logs; no PII in logs)
- [ ] Threat model updated if new data flows or trust boundaries introduced
- [ ] AI-assisted code: PR labeled ai-assisted; reviewer confirms understanding (not just diff)
```

**Pipeline enforcement:** SAST and secrets scanning run as PR gates — the PR cannot merge on failure. SCA runs nightly and on PRs. IaC scanning triggers on infrastructure file changes only. Every gate should produce zero manual willpower.

---

## Threat Modeling in Sprint Planning

Threat modeling belongs in **backlog refinement**, not as a waterfall gate. Apply a 5–10 minute STRIDE quick-scan per user story when a story introduces new data flows, external integrations, or trust boundary changes. Full models are reserved for epics.

### STRIDE Quick-Scan (per user story, ≤10 min)

| Category | Question | Common Finding |
|---|---|---|
| **Spoofing** | Can someone impersonate a user or service? | JWT validation missing on new endpoint |
| **Tampering** | Can request data be modified in transit or at rest? | Object IDs accepted from client without server-side validation |
| **Repudiation** | Can a user deny performing an action? | No audit trail for admin operations |
| **Information Disclosure** | Does this expose data to unauthorized parties? | API returns sensitive fields the client does not need |
| **Denial of Service** | Can this be abused to exhaust resources? | Unbounded query without pagination |
| **Elevation of Privilege** | Can a lower-privilege user gain higher access? | IDOR — user accesses another user's data by changing an ID parameter |

### When to Use Each Model
- **STRIDE** — per user story during refinement (5–10 min)
- **PASTA** (Process for Attack Simulation and Threat Analysis) — for epics quarterly; 7-stage full methodology
- **MITRE ATT&CK** — for attack simulation and adversary-informed red teaming; map threats to specific techniques (T1190, T1078, T1552, T1059)

### Misuse Stories

Write a misuse story alongside every security-sensitive user story. Format:

> *As a [attacker type], I want to [exploit behavior] by [attack vector], so that I can [attain goal].*
> **Mitigations:** [specific controls] [automated test that proves the mitigation]

Example — Broken Object-Level Authorization:
> *As a malicious authenticated user, I want to access other users' order data by manipulating the orderId parameter in GET /api/orders/{orderId}, so that I can steal PII and financial data.*
> **Mitigations:** Controller verifies `order.UserId == currentUser.Id`. Integration test: authenticated User A requesting User B's order returns 403 Forbidden.

**Security spikes** handle unknowns: time-box 1–3 days. Deliverable is a recommendation and estimated stories, not production code.

---

## Security Champions Model

**One Security Champion per team** (one per 10–20 developers). Select based on curiosity and peer influence — not seniority.

### Champion Responsibilities
- **In refinement** — flag stories with security implications; propose misuse stories; initiate STRIDE quick-scans
- **In code review** — review security-tagged PRs; verify DoD security criteria
- **In Sprint Review** — present security scan dashboard; trend open vulnerabilities vs. resolved
- **Ongoing** — maintain team's security knowledge; escalate to central AppSec when needed

### Security Guild
Champions from all teams form a **Security Guild** meeting bi-weekly:
- Share findings across teams (vulnerability patterns, new attack techniques)
- Maintain shared Semgrep rulesets, Gitleaks config, and scan baselines
- Coordinate on cross-cutting security architecture decisions
- Manage the Champions rotation schedule

### Rotation Schedule
Rotate champions every 6–12 months. Overlap periods of 4 weeks for knowledge transfer. Track champion assignments on a dedicated **Champions board** in the project management tool. Never leave a team without a champion — overlap before rotating.

### Champion Training Path
1. OWASP Top 10 (foundational)
2. Threat modeling facilitation (STRIDE workshop)
3. SAST tool operation and triage
4. Penetration testing basics and scope definition
5. Incident response and blameless postmortem facilitation

---

## Security Sprint Cadence

### Recurring Security Stories (add to backlog each sprint)
- Dependency updates — triage Dependabot/Snyk alerts; fix Critical CVEs this sprint
- SAST triage — review new CodeQL/Semgrep findings; close false positives; create stories for true positives
- Security debt burndown — dedicate 10–20% of sprint capacity to security debt
- Security metric review — update vulnerability age dashboard; MTTR trends

### Security Backlog Grooming
Hold a dedicated **Security Backlog Grooming** session monthly (separate from standard refinement):
- Review OWASP SAMM maturity scores against targets
- Review all open vulnerabilities from the unified dashboard
- Prioritize using CISA Known Exploited Vulnerabilities list first
- Severity-based SLAs: Critical/CISA KEV → current sprint; CVSS ≥9.0 internet-facing → current sprint; CVSS 7.0–8.9 → within 2 sprints; lower → scheduled as capacity allows

### Penetration Testing Cadence
| Tier | Frequency | Scope |
|---|---|---|
| Automated DAST (OWASP ZAP baseline) | Every PR/build | Changed endpoints |
| Security Champion review | Each sprint | Security-critical features |
| Internal manual pentest | Quarterly | Full application scope |
| External firm engagement | Annually | Full scope including social engineering |

With 2-week sprints, annual external testing leaves 25 of 26 releases untested. Layer all four tiers.

---

## Psychological Safety (Project Aristotle)

Google's 2012 Project Aristotle studied 180+ teams and found **psychological safety is the single strongest predictor of team effectiveness** — stronger than individual talent, colocation, or seniority.

### Five Dynamics of Effective Teams (in order of importance)
1. **Psychological safety** — safe to take interpersonal risks without embarrassment or punishment
2. **Dependability** — members complete quality work on time
3. **Structure and clarity** — clear roles, plans, and goals
4. **Meaning** — personal sense of purpose in the work
5. **Impact** — belief that work contributes to something larger

Teams with high psychological safety were rated effective **2× more often** by executives and exceeded targets by 17% in sales. Low-safety teams fell short by 19%.

### Timothy Clark's Four Stages (cumulative — each enables the next)
1. **Inclusion Safety** — you belong here
2. **Learner Safety** — safe to ask questions and make mistakes
3. **Contributor Safety** — safe to participate actively and voice ideas
4. **Challenger Safety** — safe to challenge the status quo without repercussion

### Security-Safety Connection
Amy Edmondson's hospital research found stronger teams reported *higher* error rates — not because they made more mistakes, but because they felt safe reporting them. The same dynamic applies to security: teams without psychological safety **hide vulnerabilities to avoid blame**. Psychological safety is a security control.

### Building Safety in Practice
- Scrum Master models vulnerability: "I don't know — let's find out together"
- React to mistakes with curiosity, not judgment: "What did we learn?"
- Run safety check at retrospective start: "Rate 1–5 how safe you feel speaking openly"
- Use anonymous input channels for sensitive feedback
- Remove management observers from retrospectives

---

## Blameless Postmortems

Adapted from Google SRE. A blameless postmortem assumes everyone involved had good intentions and made the best decision they could with the information they had at the time.

### Postmortem Template
1. **Incident summary** — one paragraph, factual
2. **Impact assessment** — affected users, revenue impact, duration
3. **Timeline** — chronological, using roles not names
4. **Root causes and triggers** — systemic factors, not individual failures
5. **What went well** — detection speed, response effectiveness, communication
6. **What went wrong** — gaps in monitoring, process failures, tooling gaps
7. **Where luck intervened** — reveals future risks that could materialize without the lucky condition
8. **Action items** — SMART, single owner, due date, linked to Sprint Backlog ticket
9. **Lessons learned** — generalizable insights for future incidents

**Store postmortems in a searchable team wiki.** Review action item status at the next Sprint Retrospective. Use past incidents for "Wheel of Misfortune" training with new team members. Focus on systems, not individuals — the goal is to prevent recurrence, not assign blame.

---

## Retrospective Formats

**The #1 reason retrospectives fail: action items never get completed.** Every unresolved action item teaches the team that participation is pointless.

### Rules for Effective Retrospectives
- Limit to **1–3 action items** per retrospective
- Each action item must be SMART: Specific, Measurable, Achievable, Relevant, Time-bound
- Assign a **single owner** (not "the team")
- Action items become Sprint Backlog tickets — they are real work
- **First 5 minutes**: review previous action items before generating new ones
- Open with Norman Kerth's **Retrospective Prime Directive**: *"Regardless of what we discover, we understand and truly believe that everyone did the best job they could, given what they knew at the time."*

### Format Menu (rotate every 3–4 sprints)
| Format | Best Used When | Structure |
|---|---|---|
| **Start/Stop/Continue** | Default; fast | Three columns, sticky notes, dot vote |
| **4Ls** | Milestone retrospectives | Liked / Learned / Lacked / Longed For |
| **Sailboat** | Team struggling with alignment | Wind (helps) / Anchor (slows) / Rocks (risks) / Island (goal) |
| **Mad/Sad/Glad** | Burned-out or high-stress teams | Emotional temperature check |
| **Lean Coffee** | Mature teams wanting open agenda | Participant-proposed topics, dot-vote, timeboxed discussion |
| **Starfish** | Teams needing nuance | More Of / Less Of / Keep / Start / Stop |

### Signs of Dysfunctional Retrospectives
- Only 2–3 people talk (lack of psychological safety)
- Same issues raised every sprint (action items not tracked)
- Retrospective is the first ceremony cut (team sees no value)
- Blame language directed at individuals

---

## Team Health Checks

### Spotify Squad Health Check (Kniberg & Lindwall, 2014)
Rate eleven dimensions on green/yellow/red with trend arrows:
Easy to Release, Suitable Process, Tech Quality, Value, Speed, Mission, Fun, Learning, Support, Pawns or Players, Teamwork.

**Run quarterly as a workshop with simultaneous card reveals** — the conversation is the value, not the score. Track trends across quarters; scan across teams to spot systemic patterns.

### Bus Factor Mitigation
Bus factor = minimum team members whose sudden absence would stall the project. Research of 25 popular GitHub projects found 10 had a bus factor of 1.

**Strategies:**
- **Pair programming** — NC State research: ~15% development-time cost; 86–94% test pass rate vs. 73–78% solo
- **Mob programming** — whole team on one problem; best for complex architectural decisions
- **Code review limits** — SmartBear/Cisco: optimal review size 200–400 lines; defect detection drops sharply above 400 LOC
- **Architecture Decision Records** — capture reasoning, not just decisions

---

## Architecture Decision Records (ADRs)

ADRs (Michael Nygard, 2011; Thoughtworks Radar "Adopt" 2018) capture the reasoning behind architectural decisions for future team members and for system evolution.

### ADR Template
```
# ADR-NNN: [Short title]

**Status:** Proposed | Accepted | Deprecated | Superseded by ADR-NNN

**Context:** [What is the situation forcing this decision? What constraints apply?]

**Decision:** [What was decided?]

**Consequences:** [What becomes easier or harder as a result?]
```

**Store in `docs/adr/` in the repository** — co-located with code, version-controlled, always current. Create ADRs during spikes and refinement. Reference them in Sprint Planning when related work appears. Present significant decisions in Sprint Review.

---

## Sprint Planning Checklist with Security Gates

### Before Sprint Planning
- [ ] Security backlog groomed; Critical/High vulnerabilities assigned severity SLA
- [ ] Previous sprint security scan results reviewed; open findings triaged
- [ ] OWASP SAMM targets for this quarter reviewed
- [ ] Champion available for the sprint (not on PTO)

### During Sprint Planning
- [ ] Sprint Goal drafted before selecting backlog items
- [ ] Capacity calculated realistically (subtract ceremony time, PTO, support rotation, interrupt buffer)
- [ ] Each story with new data flows or integrations: STRIDE quick-scan assigned (5–10 min during planning or refinement)
- [ ] Security stories included (dependency updates, SAST triage, debt reduction)
- [ ] Misuse stories written for security-sensitive features
- [ ] AI-assisted work tagged; augmented DoD requirements confirmed
- [ ] Security DoD checklist reviewed with team

### Security Work Allocation Target
- 50–60% feature development
- 10–20% infrastructure
- 10–20% data engineering / analytics
- **10–20% security hardening and debt reduction**

---

## AI Coding Governance in Agile

The evidence (2024–2026) is sobering. The METR RCT (July 2025, 246 tasks) found AI tools made developers **19% slower** despite developers believing they were 20% faster. Apiiro found AI-assisted commits merged **4× faster** while introducing 322% more privilege escalation paths. Veracode found **45% of AI-generated code samples fail security tests**. Google DORA 2025 found a **9% increase in bug rates** correlated with 90% increase in AI adoption.

### Decision Framework: When to Use AI

| Use AI First | Use Human First | Human Only |
|---|---|---|
| Boilerplate/scaffolding (CRUD, DTOs) | Complex business logic | Authentication flows |
| Unit test generation | Domain-specific reasoning | Cryptography |
| Documentation | Familiar codebases | PII handling |
| Migration generation | Security-adjacent features | IaC for sensitive infra |

### Augmented DoD for AI-Assisted Code
- [ ] PR labeled `ai-assisted`
- [ ] At least one human reviewer confirms they *understand* the code (not just reviewed the diff)
- [ ] SAST and secrets scanning passed
- [ ] Parameterized queries verified (AI frequently generates string concatenation)
- [ ] License compliance checked (AI hallucinates package names — verify all AI-introduced dependencies exist)
- [ ] Test coverage maintained at parity with human-written code

### Team Norms
- **Approved tools** — enterprise-tier tools with audit logging only (no consumer AI tools with production code)
- **Prohibited** — pasting production secrets or PII into AI prompts; using AI output without human review
- **Track metrics** — AI-assisted vs. human-only defect rates per sprint; if security debt exceeds budget, reduce AI-assisted work next sprint

### Timeboxing AI Agent Sessions
- Time-box AI agent coding sessions to avoid runaway scope
- Review AI-generated changes as a complete unit before merging (not incrementally)
- Set a maximum PR size for AI-assisted work (e.g., 400 lines per review session)

---

## DORA Metrics (2024 Benchmarks)

The four key DevOps metrics from the DORA research program (*Accelerate*, Forsgren, Humble, Kim, 2018):

| Metric | Elite | High | Medium | Low |
|---|---|---|---|---|
| **Deployment Frequency** | Multiple per day | Daily to weekly | Weekly to monthly | Monthly to 6 months |
| **Lead Time for Changes** | < 1 day | 1 day – 1 week | 1 week – 1 month | 1–6 months |
| **Change Failure Rate** | 0–5% | ~10% | ~15% | 16–30%+ |
| **Failed Deployment Recovery Time** | < 1 hour | < 1 day | < 1 day | 1 week – 1 month |

**Important nuances:**
- Performance tiers are derived via cluster analysis from annual survey data — they shift year to year, not fixed benchmarks
- DORA renamed MTTR to "Failed Deployment Recovery Time" (FDRT) in recent releases
- The 2024 report found AI tools boost individual productivity but correlate with **worsened** software delivery performance at the team level — second consecutive year of this finding
- 19% of respondents reached Elite, 22% High in 2024

**Instrument in CI/CD:** Deployment Frequency via pipeline run data; Lead Time via commit-to-production timestamps; Change Failure Rate by tagging failed deployments; FDRT by measuring incident creation to resolution.

---

## OWASP SAMM Integration

OWASP Software Assurance Maturity Model v2 provides a structured path for security program maturity.

### Assessment Cadence
1. **Baseline** — run SAMM assessment using the online questionnaire
2. **Target setting** — set target maturity per practice area based on organizational risk profile
3. **Backlog mapping** — convert SAMM improvement activities to Product Backlog items
4. **Quarterly reassessment** — track maturity improvement over time

### SAMM Business Functions and Practice Areas
- **Governance**: Strategy & Metrics, Policy & Compliance, Education & Guidance
- **Design**: Threat Assessment, Security Requirements, Security Architecture
- **Implementation**: Secure Build, Secure Deployment, Defect Management
- **Verification**: Architecture Assessment, Requirements-Driven Testing, Security Testing
- **Operations**: Incident Management, Environment Management, Operational Management

Security Backlog Grooming sessions should review SAMM scores and connect improvement work to quarterly Sprint Goals.

---

## Security Debt Management

**60% of organizations carry critical security debt** (Veracode 2026 State of Software Security). Security debt is technical debt with higher blast radius.

### Visibility Mechanisms
- Unified dashboard: open vulnerabilities by age, security debt trend per sprint, MTTR by severity
- CISA Known Exploited Vulnerabilities list checked weekly
- Vulnerability age tracked as a sprint metric (average days open by severity tier)

### Prioritization SLAs
| Severity | SLA |
|---|---|
| CISA KEV or CVSS ≥9.0 (internet-facing) | Current sprint |
| CVSS 7.0–8.9 | Within 2 sprints |
| CVSS 4.0–6.9 | Within current quarter |
| CVSS <4.0 | Scheduled as capacity allows |

Dedicate **10–20% of sprint capacity** to security debt. Make this a standing capacity allocation visible in Sprint Planning — not something negotiated away under feature pressure.
