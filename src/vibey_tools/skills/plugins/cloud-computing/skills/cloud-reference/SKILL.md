---
name: cloud-reference
description: "Use when checking a cloud anti-pattern, weighing a contested question, confirming whether a pricing, regulatory or provider claim is still current (snapshot verified August 2026), finding the primary sources worth reading instead of blogs, or needing the design checklist, the numbers worth remembering, and a triage list. Companion to the other cloud-computing skills."
---

# Cloud Computing: Anti-Patterns, Contested Questions, Currency, and Canon

> **Part 5 of 5** of the *Cloud Computing* reference (plugin `cloud-computing`), covering §15–§20. Sibling skills: `cloud-models-providers-and-primitives` (§0–§3), `cloud-architecture-and-resilience` (§4–§6), `cloud-cost-security-and-operations` (§7–§9), `cloud-migration-sovereignty-and-ai-workloads` (§10–§14). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Verified August 2026. See §17 below for the currency snapshot and what goes stale first.

> **How to read this.** Reference, not a certification guide. Three markers:
> - **[DURABLE]** — architectural principles and trade-offs that survive provider churn.
> - **[VERSIONED]** — market data, pricing, service names, regulation. **Verify before
>   quoting.**
> - **[CONTESTED]** — genuine disagreement.
>
> **⚠️ GOTCHA** boxes mark the mistakes that produce outages or surprise invoices.
>
> **Provider-neutral by default**, with AWS/Azure/GCP names where the concept needs an
> anchor. Service names change; the primitives don't.
>
> **The three framings that organize everything below:**
> 1. **The cloud is someone else's computer, rented, with an API and a metered bill.**
>    Every genuine advantage (elasticity, global reach, managed services, capex→opex) and
>    every genuine failure mode (cost surprise, lock-in, shared fate, opaque outages)
>    follows from that one sentence.
> 2. **⚠️ Your failure domain is always larger than your architecture diagram says.**
>    The 2025 outages taught this expensively: multi-AZ deployments failed because of
>    control-plane dependencies nobody had drawn (§6 → `cloud-architecture-and-resilience`). **Map what you actually depend on,
>    not what you think you depend on.**
> 3. **Cost is an architectural property, not an operational afterthought.** It is
>    determined by design decisions — data placement, service selection, egress paths —
>    and **discovered on an invoice 30 days later** (§7 → `cloud-cost-security-and-operations`). Design for it up front or pay
>    for it forever.

---

## §15. Anti-Patterns

| Anti-pattern | Why |
|---|---|
| Lift-and-shift everything, then be surprised by the bill | Fixed-capacity design on per-hour billing (§10 → `cloud-migration-sovereignty-and-ai-workloads`) |
| Treating cost as an ops problem | ⚠️ **It's set at design time** (§7 → `cloud-cost-security-and-operations`) |
| No tagging strategy | **You can't allocate what you can't attribute** (§7 → `cloud-cost-security-and-operations`) |
| Ignoring commitment discounts | **Fewer than half of orgs use any** — free money (§7.1 → `cloud-cost-security-and-operations`) |
| Never using spot for interruptible work | 60–90% cheaper (§3 → `cloud-models-providers-and-primitives`, §13 → `cloud-migration-sovereignty-and-ai-workloads`) |
| Provisioned block storage sized for peak, forever | You pay for the ask, not the use (§3 → `cloud-models-providers-and-primitives`) |
| No storage lifecycle policy | Minutes to set, runs forever (§3 → `cloud-models-providers-and-primitives`) |
| **Assuming multi-AZ protects against regional failure** | ⚠️ **The single most expensive lesson of 2025** (§6 → `cloud-architecture-and-resilience`) |
| Multi-region compute with single-region data | The dependency that actually took people down (§6.2 → `cloud-architecture-and-resilience`) |
| Not auditing whether failover routes through us-east-1 | Global services anchor there (§6.2 → `cloud-architecture-and-resilience`) |
| Monitoring and alerting behind the same provider you're monitoring | ⚠️ **Failed exactly this way in 2025** (§6.2 → `cloud-architecture-and-resilience`) |
| CI/CD and IaC state in the region you'd fail over *from* | Can't deploy the fix (§6.3 → `cloud-architecture-and-resilience`) |
| Untested failover runbook | It's a hypothesis, not a plan (§6.3 → `cloud-architecture-and-resilience`) |
| Binary up/down with no degraded mode | Read-only beats down, and costs far less (§6.3 → `cloud-architecture-and-resilience`) |
| Long-lived access keys | ⚠️ **The most common breach vector.** Use workload identity (§8 → `cloud-cost-security-and-operations`) |
| Wildcard IAM policies that were "temporary" | They never are (§8 → `cloud-cost-security-and-operations`) |
| Treating a VPC as a trust boundary | Network location ≠ authorization (§8 → `cloud-cost-security-and-operations`) |
| Assuming provider compliance certification = your compliance | It enables it; config is yours (§8 → `cloud-cost-security-and-operations`) |
| Alerting on CPU instead of user-visible symptoms | Alert fatigue is a reliability problem (§9 → `cloud-cost-security-and-operations`) |
| **Assuming data residency equals sovereignty** | ⚠️ **The "residency illusion"** — CLOUD Act reach (§11.1 → `cloud-migration-sovereignty-and-ai-workloads`) |
| Signing or auto-renewing EU cloud contracts without the 2027 ban in view | ⚠️ **Locks in an outdated fee structure** (§11.2 → `cloud-migration-sovereignty-and-ai-workloads`) |
| Thinking egress fees were the whole of lock-in | APIs, formats and IAM outlast the invoice line (§11.2 → `cloud-migration-sovereignty-and-ai-workloads`, §12 → `cloud-migration-sovereignty-and-ai-workloads`) |
| Chatty service mesh spanning AZs | Cross-AZ transfer is a real, invisible cost (§11.3 → `cloud-migration-sovereignty-and-ai-workloads`) |
| Kubernetes for three services and five engineers | ⚠️ **Adopting a platform team's problem without the platform team** (§5 → `cloud-architecture-and-resilience`) |
| Serverless for sustained high-volume load | The cost curve inverts (§5 → `cloud-architecture-and-resilience`) |
| Multi-cloud portability as a default goal | Lowest common denominator, multiplied ops (§12 → `cloud-migration-sovereignty-and-ai-workloads`) |
| Accidental lock-in | ⚠️ **You paid the abstraction cost and got locked in anyway** (§12 → `cloud-migration-sovereignty-and-ai-workloads`) |
| Statically provisioned GPU fleets | **30–40% utilization; fastest-growing waste** (§13 → `cloud-migration-sovereignty-and-ai-workloads`) |
| Training on on-demand instead of spot with checkpointing | Bursty and interruption-tolerant by nature (§13 → `cloud-migration-sovereignty-and-ai-workloads`) |
| Retrofitting AI cost attribution later | **What the 2026 waste reversal is measuring** (§7.1 → `cloud-cost-security-and-operations`, §13 → `cloud-migration-sovereignty-and-ai-workloads`) |
| Quoting a cloud market share figure without its source | ⚠️ **They differ by 4+ points on methodology** (§2 → `cloud-models-providers-and-primitives`) |

---

## §16. Contested Questions

**16.1 Is cloud cheaper than on-prem?** *For*: no capex, elastic, no datacenter staff,
you pay for what you use. *Against*: at **steady, predictable, high utilization**, owned
hardware is frequently cheaper — and that's exactly the profile that gets repatriated.
**[CONTESTED, and the honest answer is workload-dependent.]** The 2026 data supports a
middle reading: **~21% of workloads repatriated, but new cloud workloads outstrip the
exits.** ⚠️ **From 2027 the EU removes exit-cost distortion from this comparison, which
means the TCO math should genuinely be re-run** rather than assumed.

**16.2 Is repatriation a real trend or vendor noise?** Real but bounded. **Selective
repatriation of steady-state, high-utilization workloads is happening**, driven partly by
FinOps tooling finally making the comparison visible. **Wholesale cloud exit is not.**

**16.3 Multi-cloud: insurance or expensive complexity?** §12 → `cloud-migration-sovereignty-and-ai-workloads`. The 2025 outages strengthened
the resilience argument; the operational reality strengthened the complexity argument.
**Both got more true at once.**

**16.4 Is Kubernetes over-adopted?** **[CONTESTED but leaning yes.]** Excellent at scale
with a platform team, poor fit below that, and adopted for reasons that are often about
résumés and perceived sophistication rather than requirements.

**16.5 Does serverless deliver?** *For*: genuinely excellent for event-driven, spiky, and
low-volume workloads; operational burden near zero. *Against*: cost inversion at sustained
volume, cold starts, testing friction, vendor coupling. **The pendulum settled around
"right tool for specific shapes" rather than a default.**

**16.6 Is sovereign cloud meaningful or theatre?** *For*: the CLOUD Act tension is real
and residency genuinely doesn't solve it. *Against*: much of what's marketed as sovereign
is residency with extra branding. **⚠️ The EU's proposed Cloud and AI Development Act
(June 2026) is an attempt to settle this by defining graded sovereignty levels** — which
is itself an admission that the term is currently unregulated marketing.

**16.7 Are the hyperscalers over-building for AI?** ⚠️ **Genuinely unknown, and the stakes
are large.** ~$570B+ of combined 2026 capex guidance is a bet that AI demand
materializes. Revenue growth currently supports it. **If it disappoints, the write-downs
would be historically large** — and buyers should factor that uncertainty into
long-horizon commitments.

---

## §17. Currency Snapshot — verified August 2026

| Thing | Status as of Aug 2026 | Decay risk |
|---|---|---|
| **Market structure** | Q1 2026 cloud infrastructure spend **~$129B, +35% YoY**, ninth consecutive quarter of accelerating YoY growth. Big Three **~60–68%** depending on methodology. ⚠️ **Synergy: AWS 28% / Azure 21% / GCP 14%. Other sources: 30/24–25/13 or 32/23/11** — **cite source and scope** (§2 → `cloud-models-providers-and-primitives`). Azure and GCP growing faster off smaller bases; **Microsoft doesn't break out Azure revenue, only growth rate** | **High** |
| **Capex** | 2026 guidance: **Amazon ~$200B, Microsoft ~$190B, Alphabet ~$180–190B.** Guidance, not actuals | **High** |
| **AI share of cloud spend** | **~19% in 2026, up from ~8% in 2023** | **High** |
| **⚠️ Cloud waste** | **Flexera 2026: 29% of IaaS/PaaS wasted, up from 27% — reversing a five-year decline**, attributed to **AI adoption outpacing tagging/attribution/governance**. n=753. **Managing cloud spend now the #1 priority (84%), above security** | Medium |
| **FinOps adoption** | **FinOps teams ~63%, CCoE ~71%.** ⚠️ **Fewer than half use any one commitment discount per provider.** **AI cost management the top future priority (98%)** and most-wanted skillset. **FOCUS** standardizing cross-provider cost data. Practitioners report **the easy waste is gone** — remaining savings are smaller and harder | Medium |
| **Repatriation** | **~21% of workloads repatriated**, but **new cloud workloads outstrip exits — cloud continues to grow** | Medium |
| **GPU economics** | **GPUs ~18% of spend at AI-forward orgs (up from ~4% in 2023); statically provisioned fleets at 30–40% utilization.** Idle accelerators = fastest-growing waste category | **High** |
| **⚠️ Oct–Nov 2025 outages** | **AWS us-east-1, 20 Oct, ~14–15h** — latent **race condition in DynamoDB's DNS management** wiped DNS records, cascading across dozens of services. **Azure, 29 Oct** — **Azure Front Door** / global identity. **Cloudflare, 18 Nov** — Bot Management config **doubled a feature file past a hard-coded limit**, crashing proxies globally; **engineers spent ~2h believing it was a DDoS**. Common pattern: **subtle single-subsystem defect → global cascade**; diagnosis is **immature blast-radius modelling**, not human error | Low (historical) |
| **us-east-1 concentration** | Reported at **~69% of AWS usage** by one analysis and **44%+ of AWS requests** by another. **Global operations (parts of IAM, Route 53) anchor there** | Medium |
| **⚠️ EU Data Act** | Reg. (EU) 2023/2854. In force 11 Jan 2024. **Switching rights enforceable 12 Sept 2025.** **12 Sept 2026: products released after must have user data accessible by default.** **⚠️ 12 January 2027: all switching charges including egress fees banned outright** — IaaS, PaaS and SaaS, **for every provider serving EU customers**. Transition allows only direct, transparent, pre-agreed cost. Enforcement by **national authorities**, penalties set in **local legislation**. AWS/Azure/Google waived full-exit egress in 2024 (narrower than 2027 requires) | **High** |
| **DMA / sovereignty** | **DMA investigating AWS and Azure as potential gatekeepers**; ⚠️ **analysts flag genuine friction with the Data Act** — conflicting timelines, split enforcement (member states vs. Commission). **3 June 2026: Commission proposed the Cloud and AI Development Act** (Tech Sovereignty Package) to define **graded sovereignty levels** — ⚠️ **not yet passed; details will change** | **High** |
| **Sustainability** | Well-Architected pillar; **>half of orgs have or plan a sustainability initiative including cloud carbon tracking** | Medium |

**Goes stale fastest:** §2 → `cloud-models-providers-and-primitives`, §13 → `cloud-migration-sovereignty-and-ai-workloads`, and the market figures throughout. **Essentially never
stale:** §1 → `cloud-models-providers-and-primitives`, §4 → `cloud-architecture-and-resilience`, §6.2 → `cloud-architecture-and-resilience`–6.3's principles, §8 → `cloud-cost-security-and-operations`, §9 → `cloud-cost-security-and-operations`, §10 → `cloud-migration-sovereignty-and-ai-workloads`, §15.

---

## §18. The Canon

### 18.1 Books

| Author | Work | Why |
|---|---|---|
| **Kleppmann** | ***Designing Data-Intensive Applications*** | The forces underneath every distributed cloud decision |
| **Beyer, Jones, Petoff & Murphy** | ***Site Reliability Engineering*** + *The SRE Workbook* | **Free online.** §9 → `cloud-cost-security-and-operations` and §6 → `cloud-architecture-and-resilience` in full |
| **Nygard** | ***Release It!*** (2nd ed.) | ⚠️ **Still the best book on production failure modes** — §6 → `cloud-architecture-and-resilience` |
| **Adzic & Chatley** et al. | *Serverless* literature | §5 → `cloud-architecture-and-resilience`'s trade-offs |
| **Burns, Beda, Hightower** | *Kubernetes: Up and Running* | §5 → `cloud-architecture-and-resilience` |
| **Morris** | ***Infrastructure as Code*** (2nd ed.) | §4 → `cloud-architecture-and-resilience` |
| **Forsgren, Humble & Kim** | ***Accelerate*** | The delivery-performance evidence base |
| **Storment & Fuller** | ***Cloud FinOps*** (2nd ed.) | §7 → `cloud-cost-security-and-operations`, and the standard text |
| **Newman** | *Building Microservices* | §12 → `cloud-migration-sovereignty-and-ai-workloads`'s coupling questions |
| **Vogels / Werner Vogels' writing** | *All Things Distributed* | Design-for-failure from the source |

### 18.2 Primary sources — use these over blogs
**AWS Well-Architected Framework**, **Azure Well-Architected Framework**, and **Google
Cloud Architecture Framework** (all free, all genuinely good, all vendor-shaped).
**Microsoft's Cloud Design Patterns** and **AWS Prescriptive Guidance**. **The provider
post-incident reports** — ⚠️ **read these; they are the best free distributed-systems
education available.** **The CNCF landscape** (with a sense of humour about its size).
**FinOps Foundation** (framework, **State of FinOps**, and **FOCUS**). **Flexera State of
the Cloud** (annual, 15th edition). **Synergy Research** and **Omdia** for market data.
**EUR-Lex** for the Data Act text itself, rather than summaries of it.

### 18.3 People and commentary
**Corey Quinn** (*Last Week in AWS* — ⚠️ **the sharpest and funniest cloud-cost commentary
anywhere, and unusually willing to say what vendors won't**), **Werner Vogels**,
**Charity Majors** (observability, and on-call as a design constraint), **Liz Fong-Jones**,
**Gergely Orosz** (*The Pragmatic Engineer*), **Forrest Brazeal**, **Adrian Cockcroft**,
**Kelsey Hightower** (⚠️ **including his scepticism about Kubernetes over-adoption**),
**Simon Wardley** (mapping, and the strategic view of commoditization).

---

## §19. Quick Reference

### 19.1 Design checklist
- [ ] RTO and RPO defined **per workload**, not globally (§6.3 → `cloud-architecture-and-resilience`)
- [ ] **Dependency map including SaaS and their underlying providers** (§6.3 → `cloud-architecture-and-resilience`)
- [ ] ⚠️ Does anything silently depend on a single region — including IAM, DNS, CI/CD, or
      monitoring? (§6.2 → `cloud-architecture-and-resilience`)
- [ ] Degraded mode designed, not just up/down (§6.3 → `cloud-architecture-and-resilience`)
- [ ] Failover **tested**, not documented (§6.3 → `cloud-architecture-and-resilience`)
- [ ] Tagging strategy enforced before spend scales (§7 → `cloud-cost-security-and-operations`)
- [ ] Commitment and spot mix modelled (§7.2 → `cloud-cost-security-and-operations`)
- [ ] Egress and cross-AZ paths deliberate (§11.3 → `cloud-migration-sovereignty-and-ai-workloads`)
- [ ] Workload identity, not long-lived keys (§8 → `cloud-cost-security-and-operations`)
- [ ] Least privilege from deny-all (§8 → `cloud-cost-security-and-operations`)
- [ ] Logging on, retained, and outside the failure domain (§8 → `cloud-cost-security-and-operations`, §9 → `cloud-cost-security-and-operations`)
- [ ] SLOs from user-visible behaviour; alerts on symptoms (§9 → `cloud-cost-security-and-operations`)
- [ ] IaC for everything; no console changes in prod (§4 → `cloud-architecture-and-resilience`)
- [ ] ⚠️ EU contracts reviewed against the **12 Jan 2027** ban (§11.2 → `cloud-migration-sovereignty-and-ai-workloads`)
- [ ] Exit path documented — data formats, APIs, IAM, not just egress cost (§12 → `cloud-migration-sovereignty-and-ai-workloads`)

### 19.2 Numbers worth remembering
- **~29%** of IaaS/PaaS spend wasted (Flexera 2026) — **up, not down**
- **Fewer than half** of orgs use any one commitment discount
- **Spot: 60–90% cheaper** for interruptible work
- **GPUs ~18%** of AI-forward spend; **30–40% utilization** when statically provisioned
- **AI ~19%** of cloud spend, from ~8% in 2023
- **~21%** of workloads repatriated; cloud still growing
- **AWS us-east-1 outage: ~14–15 hours**, October 2025
- **⚠️ 12 January 2027** — EU egress and switching fee ban

### 19.3 Triage
| Symptom | First look |
|---|---|
| Bill jumped and nobody knows why | Untagged resources; egress; a new AI workload (§7 → `cloud-cost-security-and-operations`) |
| Bill high but usage flat | Idle resources, orphaned storage, no commitments (§7.2 → `cloud-cost-security-and-operations`) |
| Outage despite multi-AZ | ⚠️ Regional control-plane dependency (§6.2 → `cloud-architecture-and-resilience`) |
| Failed over but still down | Data tier, CI/CD, or monitoring in the failed region (§6.2 → `cloud-architecture-and-resilience`) |
| Serverless costs more than expected | Sustained volume — the curve inverted (§5 → `cloud-architecture-and-resilience`) |
| Kubernetes consuming the team | You may not need it (§5 → `cloud-architecture-and-resilience`) |
| Cross-AZ charges surprising | Chatty services spanning zones (§11.3 → `cloud-migration-sovereignty-and-ai-workloads`) |
| "We're multi-cloud" but can't fail over | You have workload distribution, not portability (§12 → `cloud-migration-sovereignty-and-ai-workloads`) |
| Compliance auditor unsatisfied despite EU region | ⚠️ Residency ≠ sovereignty (§11.1 → `cloud-migration-sovereignty-and-ai-workloads`) |

---

## §20. Sources and Method

**Method.** Narrative review. The architectural material — §1 → `cloud-models-providers-and-primitives`, §4 → `cloud-architecture-and-resilience`, §6.3 → `cloud-architecture-and-resilience`'s principles, §8 → `cloud-cost-security-and-operations`,
§9 → `cloud-cost-security-and-operations`, §10 → `cloud-migration-sovereignty-and-ai-workloads`, §15 — rests on the provider Well-Architected frameworks, SRE literature, and
long-stable practice, and does not move much. **The economics, market structure, and
regulation move fast**, and those were verified in **August 2026** with four targeted
searches; every such claim is flagged **[VERSIONED]** and carries a decay rating in §17.

**Search log** (August 2026): cloud market share and AI capex · EU Data Act cloud
switching, egress fees, and sovereignty · the October–November 2025 outages and resilience
lessons · FinOps, cloud waste, and repatriation.

**Primary and near-primary sources consulted (selected):**
- **Market**: Synergy Research figures as reported via Statista and multiple trackers;
  Omdia's Q4 2025 cloud infrastructure analysis; company earnings coverage (Amazon,
  Microsoft, Alphabet Q1 2026). **⚠️ The methodological explanation for the divergent share
  figures came from a tracker that showed its working** — I've reproduced the reasoning
  rather than picking a number
- **EU Data Act**: legal analyses from **Alston & Bird**, **McCann FitzGerald**,
  **Kemp IT Law**, **CMS**, and **Turing Law** for the switching-charge provisions,
  transition rules, and enforcement structure; **CSIS** for the Data Act / DMA friction
  analysis; contemporaneous coverage for the June 2026 Cloud and AI Development Act
  proposal
- **Outages**: incident analyses from **Cockroach Labs' 2025 outage review**,
  **DevOps.com**, **Datacenter Knowledge**, **INE**, and independent write-ups; AWS's own
  post-mortem as reported. **⚠️ I did not read the provider post-incident reports directly**
- **FinOps**: **Flexera *State of the Cloud* 2026** (n=753) via its own materials and
  secondary reporting; **FinOps Foundation *State of FinOps* 2026**; CIO Dive's coverage of
  the repatriation and waste figures

**Confidence statement.** **High confidence** in §1 → `cloud-models-providers-and-primitives`, §3–§5 → `cloud-models-providers-and-primitives`, `cloud-architecture-and-resilience`, §6.2 → `cloud-architecture-and-resilience`–6.3, §8–§10 → `cloud-cost-security-and-operations`, `cloud-migration-sovereignty-and-ai-workloads`, §15 — these
are architectural principles and widely-corroborated practice. **High confidence in the
EU Data Act dates and structure** in §11.2 → `cloud-migration-sovereignty-and-ai-workloads`, which came from multiple independent legal
analyses agreeing on the 12 September 2025 and **12 January 2027** dates; the Regulation
number and text are checkable at EUR-Lex and I'd recommend doing so before relying on it
commercially. **High confidence in the outage facts** in §6.1 → `cloud-architecture-and-resilience`, which are consistently
reported across many independent sources, though **root-cause descriptions are
summarized from secondary analyses rather than from the provider post-incident reports
themselves.**

**⚠️ Lower confidence, deliberately flagged, on the numbers.** **Market share figures
genuinely conflict by 4+ percentage points across reputable sources for methodological
reasons I've explained in §2 → `cloud-models-providers-and-primitives`** — treat any single figure as directional. **Capex figures
are company guidance, not actuals.** **Waste, repatriation, and GPU-utilization figures
are survey-based** (Flexera n=753, FinOps Foundation n≈523 for some measures), carry
self-report bias, and vary between surveys — Harness reported ~21% waste against Flexera's
29% in overlapping periods. **The us-east-1 concentration figures (~69% of usage, 44%+ of
requests) come from different methodologies measuring different things** and should not be
combined. Several FinOps-adjacent sources are **vendor-published with an obvious interest
in the size of the problem they sell tooling for**, which I've weighted accordingly. §16 is
opinion labelled as such.
