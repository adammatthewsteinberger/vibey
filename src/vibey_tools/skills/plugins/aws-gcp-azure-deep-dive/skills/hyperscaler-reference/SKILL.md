---
name: hyperscaler-reference
description: "Use when checking a cloud anti-pattern, mapping a service to its equivalent on another provider, checking what moved in egress pricing under the EU Data Act switching regime or in the AI-driven competitive position (verified August 2026), correcting a misconception, looking up a limit or quota, or needing a picker and a new-environment checklist. Companion to the other aws-gcp-azure-deep-dive skills."
---

# AWS, GCP and Azure: Anti-Patterns, Service Equivalence, What Moved, and Numbers

> **Part 5 of 5** of the *AWS, GCP and Azure Deep Dive* reference (plugin `aws-gcp-azure-deep-dive`), covering §19–§26. Sibling skills: `hyperscaler-framing-responsibility-identity-and-hierarchy` (§0–§4), `hyperscaler-networking-compute-containers-and-serverless` (§5–§8), `hyperscaler-storage-databases-analytics-and-observability` (§9–§13), `hyperscaler-cost-reliability-iac-lock-in-and-migration` (§14–§18). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Architecture and IAM models are stable. Two areas moved. See §21 below for egress pricing under the EU Data Act switching regime, and the AI-driven shift in market position.

> **⚠️ Scope.** Assumes you know what cloud computing *is*. This is **the comparative
> layer**: where the three genuinely differ, and where the differences bite.
> Complements a cloud-computing reference (general concepts), a Linux server admin
> reference (what runs on the instances), and an IT infrastructure/governance reference
> (identity governance, RBAC theory, on-prem).
>
> **⚠️ GOTCHA** boxes mark things that cause outages or surprise bills.
>
> **The three ideas that organize everything below:**
> 1. **⚠️ The three clouds are not interchangeable, and the service feature lists are the
>    least important difference.** **What actually differs is the identity model, the
>    resource hierarchy, and the network model** — **§3–§5 → `hyperscaler-framing-responsibility-identity-and-hierarchy`, `hyperscaler-networking-compute-containers-and-serverless`.** ⚠️ **Everything above those
>    three is broadly comparable; everything about migration difficulty is determined by
>    them.**
> 2. **⚠️ Data gravity is the real lock-in, not APIs.** **Moving compute is a project.
>    Moving petabytes is an economic decision** — and §21.1 explains why that decision
>    just changed.
> 3. **⚠️ Cloud cost surprises are almost never compute.** **They're data transfer, idle
>    provisioned resources, and per-request charges on managed services** — **§14 → `hyperscaler-cost-reliability-iac-lock-in-and-migration`.**

---

## §19. Anti-Patterns

```
⚠️ Lift-and-shift and stop — datacentre architecture at cloud prices (§18)
⚠️ One giant account/subscription/project for everything — no blast radius control (§4)
⚠️ Long-lived static access keys instead of roles/managed identities/federation (§3)
⚠️ Broad grants high in the hierarchy "temporarily" (§3.3)
⚠️ Public object storage buckets for internal convenience (§2)
⚠️ Kubernetes for three services (§7)
⚠️ Serverless for steady high-volume traffic (§8)
⚠️ Multi-region before multi-AZ is solid — or before failover is tested (§15)
⚠️ Untagged resources, no budgets, no anomaly alerts (§14)
⚠️ Buying reservations for over-provisioned instances (§14)
⚠️ SELECT * on unpartitioned analytics tables (§11)
⚠️ Console-driven infrastructure with IaC "coming later" (§16)
⚠️ Multi-cloud for resilience with untested failover (§17)
⚠️ Ignoring egress in the architecture, then discovering it in the invoice (§14, §21.1)
⚠️ Treating the SLA as a guarantee (§15)
```

---

## §20. Service Equivalence

| Capability | AWS | Azure | GCP |
|---|---|---|---|
| VMs | EC2 | Virtual Machines | Compute Engine |
| Autoscaling | Auto Scaling Group | VM Scale Sets | Managed Instance Group |
| Serverless functions | Lambda | Functions | Cloud Functions |
| Serverless containers | Fargate / App Runner | Container Apps | **⚠️ Cloud Run** |
| Managed Kubernetes | EKS | AKS | **⚠️ GKE** |
| Object storage | S3 | Blob Storage | Cloud Storage |
| Block storage | EBS | Managed Disks | Persistent Disk / Hyperdisk |
| File storage | EFS / FSx | Azure Files | Filestore |
| Managed relational | RDS / Aurora | Azure SQL / Flexible | Cloud SQL / AlloyDB |
| Global distributed DB | Aurora DSQL | **Cosmos DB** | **⚠️ Spanner** |
| NoSQL | DynamoDB | Cosmos DB | Firestore / Bigtable |
| Cache | ElastiCache | Azure Cache for Redis | Memorystore |
| Data warehouse | Redshift | Fabric / Synapse | **⚠️ BigQuery** |
| ETL | Glue | Data Factory | Dataflow / Dataproc |
| Streaming | Kinesis / MSK | Event Hubs | Pub/Sub |
| BI | QuickSight | **Power BI** | Looker |
| Message queue | SQS | Service Bus / Queue Storage | Pub/Sub / Tasks |
| Event bus | EventBridge | Event Grid | Eventarc |
| Workflow | Step Functions | Logic Apps / Durable | Workflows |
| API gateway | API Gateway | API Management | API Gateway / Apigee |
| CDN | CloudFront | Azure Front Door / CDN | Cloud CDN |
| DNS | Route 53 | Azure DNS | Cloud DNS |
| Load balancer | ALB / NLB | Load Balancer / App Gateway | **⚠️ Global LB** |
| Private network | VPC | VNet | **⚠️ VPC (global)** |
| Private service access | PrivateLink | Private Link | Private Service Connect |
| On-prem link | Direct Connect | ExpressRoute | Cloud Interconnect |
| Identity | IAM | **⚠️ Entra ID + Azure RBAC** | Cloud IAM |
| Secrets | Secrets Manager / SSM | Key Vault | Secret Manager |
| Key management | KMS / CloudHSM | Key Vault / Managed HSM | Cloud KMS |
| Audit log | **CloudTrail** | **Activity Log** | **Cloud Audit Logs** |
| Monitoring | CloudWatch | Azure Monitor | Cloud Monitoring |
| Tracing | X-Ray | Application Insights | Cloud Trace |
| Posture management | Security Hub | Defender for Cloud | Security Command Center |
| Policy guardrails | SCPs / Config | Azure Policy | Organization Policy |
| Native IaC | CloudFormation | Bicep / ARM | (Terraform in practice) |
| ML platform | SageMaker | Azure ML / Foundry | Vertex AI |
| Model API | Bedrock | Azure OpenAI / Foundry | Vertex / Gemini API |
| Edge compute | Lambda@Edge / CloudFront Fn | Azure Functions on Edge | Cloud Run / CDN |

---

## §21. What Moved — verified August 2026

### 21.1 ⚠️ Egress pricing and the EU Data Act — the lock-in economics changed
**⚠️ This is the most consequential structural change in cloud economics in years, and
it's under-appreciated because it happened through regulation rather than product.**

**What happened, in sequence:**
- **⚠️ Google moved first, in January 2024**, becoming **the first provider to stop
  charging egress fees for customers switching away.**
- **AWS followed in March 2024, waiving data transfer out to the internet for customers
  leaving** — **noting that over 90% of its customers already pay nothing for egress
  under the 100 GB monthly free allowance.**
- **Microsoft completed the set in mid-March 2024** with free egress for customers leaving
  Azure.
- **⚠️ The EU Data Act is the driver.** **It came into force 11 January 2024 and became
  applicable 12 September 2025**, and ⚠️ **it bans cloud switching and egress charges
  outright from 12 January 2027**, following the transition period.
- **In September 2025 Google went further with Data Transfer Essentials**, offering
  **zero-cost ongoing multi-cloud transfers for eligible EU and UK intra-organisation
  traffic** — **beyond the Act's minimum of at-cost pass-through.**
- **⚠️ In 2026 the ground shifted again**: **AWS Interconnect for multicloud reached
  general availability in April with Google Cloud as its first partner, followed in May
  by a free 500 Mbps interconnect tier per region with no per-gigabyte charges on the
  connection.**
- **⚠️ Regulatory pressure moved from anticipated to actual**: **the European
  Commission's own Digital Markets Act page confirms a preliminary determination,
  published 25 June 2026, that AWS and Azure should be designated "gatekeepers"** — the
  first time the DMA has reached cloud infrastructure rather than consumer platforms.
  ⚠️ **Secondary reporting, not confirmed on the Commission's own page, puts the
  companies' deadline to submit written representations at September 2026 and a final
  decision around October 2026.**

> **⚠️ GOTCHA — read the fine print, because the headlines overstate this considerably.**
> ⚠️ **The exit waivers are narrow: they generally require a FULL exit, notification of
> intent, account termination, completion within a limited window (reported at 60 days),
> and credits applied only AFTER the transfer completes.** **Partial migrations are
> case-by-case.** **⚠️ And none of this touches ORDINARY egress**, which is what most
> organizations actually pay.

**⚠️ Ordinary egress rates, as reported for 2026 — treat as approximate and verify against
current pricing pages:**
```
Internet egress (entry tier)  ⚠️ ~$0.09/GB AWS · ~$0.087/GB Azure ·
                              ~$0.12/GB GCP Premium Tier
                              ⚠️ Tiered — falls as monthly volume rises
Inter-region                  ⚠️ commonly ~$0.02/GB
Cross-AZ                      ⚠️ commonly ~$0.01/GB — and this one surprises people (§14)
Ingress                       ⚠️ free on all three
Zero-egress alternatives      Cloudflare R2, Backblaze B2, Wasabi at $0
```
**⚠️ Also worth knowing**: **AWS charges hourly for public IPv4 addresses (reported at
$0.005/hour)**, ⚠️ **so IPv6 adoption eliminates both that charge and the NAT gateway it
often implies** — **one of the larger easy wins available.** **And Google raised peering
egress rates on 1 May 2026** (**North America roughly doubling on CDN Interconnect, Direct
and Carrier Peering**), **while standard internet egress was unchanged** — ⚠️ **a reminder
that the direction of travel isn't uniformly downward.**

**⚠️ Why this matters strategically**: **exit costs were a genuine lock-in mechanism and a
distortion in every cloud-vs-on-prem TCO comparison.** ⚠️ **Removing them by 2027 makes
repatriation and hybrid strategies more viable, and strengthens your negotiating position
whether or not you ever move** (§17 → `hyperscaler-cost-reliability-iac-lock-in-and-migration`, §18 → `hyperscaler-cost-reliability-iac-lock-in-and-migration`).

### 21.2 ⚠️ The competitive position shifted — AI capacity is the driver
**⚠️ The stable "AWS then Azure then a distant Google" picture is no longer accurate, and
the cause is AI infrastructure demand.**

> **⚠️ GOTCHA — market share figures disagree meaningfully between sources and I'm not
> going to pretend otherwise.** ⚠️ **For Q1/Q2 2026 I found AWS reported at 28%, 29% and
> 30%; Azure at 20%, 21% and 24%; Google Cloud at 13%, 14% and 15%.** **Synergy Research
> Group is the most commonly cited source and puts Q1 2026 at roughly AWS 28% / Azure 21%
> / Google 14%.** ⚠️ **Methodologies differ on what counts as "cloud infrastructure," and
> Microsoft does not report Azure revenue as a standalone dollar figure at all — Azure
> dollar figures in circulation are analyst estimates applied to disclosed growth rates.**
> **Trust the direction, not the decimal.**

**⚠️ The direction is consistent across every source:**
- **⚠️ Google Cloud is the share gainer.** **Reported at $24.8B revenue in Q2 2026, up 82%
  year over year and accelerating from 63% the prior quarter.** **Operating income
  reported at $8.8B on a ~35.6% margin** — ⚠️ **a business that turned its first profit
  in 2023.**
- **⚠️ The backlog number is the most forward-looking figure in the data**: **Google
  Cloud's sales backlog reported at $514B, up from around $106B a year earlier.**
  **These are multi-year contracted commitments that convert to revenue slowly.**
- **Azure grew roughly 40% for two consecutive quarters.** **AWS remains much the largest
  by revenue** — ⚠️ **though reported AWS growth figures for the same period range from
  24% to 37% across sources, which is a larger spread than it should be and another reason
  to treat these numbers as directional.**
- **AWS's share has eroded gradually from 31–32% in 2022–2023** — ⚠️ **through slower
  growth, not decline.** **The market is expanding fast enough that everyone is growing.**
- **Omdia put Q4 2025 cloud infrastructure spending at $110.9B, up 29%** — **the sixth
  consecutive quarter above 20% growth** — **and forecast 27% growth for 2026.**

**⚠️ The operationally relevant consequence, which matters more than the share table:**
**capacity is constrained.** ⚠️ **Google explicitly cited capacity constraints as a
limiting factor in Q1 2026.** **Enterprises are signing long-term deals to lock in compute
years ahead.** **In practice this means: GPU and accelerator availability varies by region,
quota requests are real gating items, and capacity commitments are increasingly part of
enterprise negotiations** (§12 → `hyperscaler-storage-databases-analytics-and-observability`). ⚠️ **Architect on the assumption that the accelerator you
want may not be available in the region you want it in.**

**⚠️ A second-order consequence worth naming**: **hyperscaler capex is now large enough to
make electricity access a strategic constraint on cloud growth**, **tying region
availability and expansion timelines to grid capacity** (see a power engineering reference
§12).

---

## §22. Misconceptions

| Misconception | Correction |
|---|---|
| The clouds are broadly interchangeable | ⚠️ **IAM, hierarchy and networking differ deeply** (§1 → `hyperscaler-framing-responsibility-identity-and-hierarchy`, §3 → `hyperscaler-framing-responsibility-identity-and-hierarchy`) |
| Comparison matrices tell you which to pick | ⚠️ **Existing agreements and team skills usually dominate** (§1 → `hyperscaler-framing-responsibility-identity-and-hierarchy`) |
| Cloud is cheaper than on-prem | ⚠️ **For variable workloads. Steady high volume often isn't** (§18 → `hyperscaler-cost-reliability-iac-lock-in-and-migration`) |
| Lift-and-shift delivers cloud savings | ⚠️ **Datacentre architecture at cloud prices** (§18 → `hyperscaler-cost-reliability-iac-lock-in-and-migration`) |
| Entra Global Admin can manage Azure resources | ⚠️ **Different authorization systems** (§3.2 → `hyperscaler-framing-responsibility-identity-and-hierarchy`) |
| An IAM Allow means the permission works | ⚠️ **It's an intersection, and any Deny wins** (§3.1 → `hyperscaler-framing-responsibility-identity-and-hierarchy`) |
| Project-level policy can restrict an inherited GCP role | ⚠️ **Inheritance is additive** (§3.3 → `hyperscaler-framing-responsibility-identity-and-hierarchy`) |
| Tags are an isolation boundary | ⚠️ **They're a convention. Use accounts/subs/projects** (§4 → `hyperscaler-framing-responsibility-identity-and-hierarchy`) |
| S3 is eventually consistent | ⚠️ **Strongly consistent since 2020** (§9 → `hyperscaler-storage-databases-analytics-and-observability`) |
| Serverless is always cheaper | ⚠️ **There's a crossover point; steady traffic is dearer** (§8 → `hyperscaler-networking-compute-containers-and-serverless`) |
| You need Kubernetes | ⚠️ **Below organizational scale it's a tax** (§7 → `hyperscaler-networking-compute-containers-and-serverless`) |
| A 99.99% SLA means 99.99% uptime | ⚠️ **It means a service credit if not** (§15 → `hyperscaler-cost-reliability-iac-lock-in-and-migration`) |
| Multi-AZ protects against outages | ⚠️ **Not control-plane failures or your own bad deploy** (§15 → `hyperscaler-cost-reliability-iac-lock-in-and-migration`) |
| Multi-cloud improves resilience | ⚠️ **Usually the opposite, with untested failover** (§17 → `hyperscaler-cost-reliability-iac-lock-in-and-migration`) |
| Compute is the big cost | ⚠️ **Transfer, idle resources and per-request charges** (§14 → `hyperscaler-cost-reliability-iac-lock-in-and-migration`) |
| Internal traffic is free | ⚠️ **Cross-AZ and cross-region are billed** (§14 → `hyperscaler-cost-reliability-iac-lock-in-and-migration`) |
| Egress fees are gone now | ⚠️ **Only for narrow full-exit cases until Jan 2027 in the EU** (§21.1) |
| Google is a distant third | ⚠️ **Reported 82% YoY growth and a $514B backlog** (§21.2) |
| GPU capacity is available on demand | ⚠️ **Constrained; quotas and commitments are real** (§21.2) |

---

## §23. Numbers

```
⚠️ Market share Q1 2026 (Synergy, most-cited)  AWS ~28% · Azure ~21% · GCP ~14%
   ⚠️ Other sources: AWS 28–30% · Azure 20–24% · GCP 13–15% — see §21.2
Cloud infra spend Q4 2025 (Omdia)              $110.9B, +29% YoY
2026 forecast growth (Omdia)                   ~27%
Google Cloud Q2 2026 revenue                   ~$24.8B, +82% YoY
Google Cloud backlog                           ~$514B (from ~$106B a year earlier)
⚠️ Internet egress entry rate                   ~$0.087–0.12/GB across the three
⚠️ Inter-region transfer                        ~$0.02/GB typical
⚠️ Cross-AZ transfer                            ~$0.01/GB typical
Ingress                                        $0 everywhere
AWS public IPv4                                ~$0.005/hour per address
⚠️ EU Data Act full egress/switching ban        12 January 2027
EU Data Act applicability                      12 September 2025
Non-prod shutdown outside hours                ⚠️ typically 60–70% of non-prod cost
Multi-AZ                                       ⚠️ the production baseline
Utilization above which queues explode         ~80% (see an IT infra reference §18)
```
⚠️ **Every price above is approximate, tiered, region-dependent and changes.** **Use them
for architecture reasoning; use the pricing calculator for decisions.**

---

## §24. Resources

**⚠️ Primary sources beat books here, because books date within a year:**
- **⚠️ The Well-Architected Frameworks** — **AWS Well-Architected, Azure Well-Architected,
  Google Cloud Architecture Framework.** **Free, vendor-written, and genuinely the best
  structured thinking each publishes.** ⚠️ **Read your provider's and at least one other —
  the differences in emphasis are informative.**
- **Provider pricing calculators** — ⚠️ **the only authoritative cost source.**
- **Cloud Adoption Frameworks** (all three) for organizational structure and landing zones.
- **CIS Benchmarks** per platform for security baselines.

| Author | Work | Why |
|---|---|---|
| **Kleppmann** | ***Designing Data-Intensive Applications*** | ⚠️ **The best book on the data layer under all of this** |
| **Burns et al.** | *Kubernetes: Up and Running* | §7 → `hyperscaler-networking-compute-containers-and-serverless` |
| **Google** | ***SRE Book*** / *SRE Workbook* | ⚠️ **Free online. §15 → `hyperscaler-cost-reliability-iac-lock-in-and-migration`'s reliability thinking** |
| **Storment & Fuller** | *Cloud FinOps* | §14 → `hyperscaler-cost-reliability-iac-lock-in-and-migration` |
| **Brikman** | *Terraform: Up & Running* | §16 → `hyperscaler-cost-reliability-iac-lock-in-and-migration` |
| **Adkins et al.** | *Building Secure and Reliable Systems* | Google, free online |

---

## §25. Quick Reference

### 25.1 Picker
| Question | Answer |
|---|---|
| Which cloud? | ⚠️ **Existing agreements + team skills, unless §1 → `hyperscaler-framing-responsibility-identity-and-hierarchy`'s exceptions apply** |
| Large-scale analytics? | ⚠️ **BigQuery is the strongest argument for GCP** (§11 → `hyperscaler-storage-databases-analytics-and-observability`) |
| Windows/AD-heavy estate? | ⚠️ **Azure, and it's not close** (§1 → `hyperscaler-framing-responsibility-identity-and-hierarchy`) |
| Broadest service catalogue? | AWS (§1 → `hyperscaler-framing-responsibility-identity-and-hierarchy`) |
| Kubernetes at scale? | ⚠️ **GKE** (§7 → `hyperscaler-networking-compute-containers-and-serverless`) |
| Do I need Kubernetes? | ⚠️ **Probably not below many-teams scale** (§7 → `hyperscaler-networking-compute-containers-and-serverless`) |
| I have a Dockerfile and want it live | ⚠️ **Cloud Run / Container Apps / App Runner** (§8 → `hyperscaler-networking-compute-containers-and-serverless`) |
| Environment separation? | ⚠️ **Separate accounts / subscriptions / projects** (§4 → `hyperscaler-framing-responsibility-identity-and-hierarchy`) |
| How do I avoid static credentials? | ⚠️ **Roles, managed identities, workload identity federation** (§3 → `hyperscaler-framing-responsibility-identity-and-hierarchy`) |
| Why is the bill high? | ⚠️ **Transfer, idle resources, log ingestion — not compute** (§14 → `hyperscaler-cost-reliability-iac-lock-in-and-migration`) |
| Cheapest easy saving? | ⚠️ **Kill non-prod overnight; move to ARM; right-size** (§6 → `hyperscaler-networking-compute-containers-and-serverless`, §14 → `hyperscaler-cost-reliability-iac-lock-in-and-migration`) |
| Multi-region? | ⚠️ **Only after multi-AZ is solid AND failover is tested** (§15 → `hyperscaler-cost-reliability-iac-lock-in-and-migration`) |
| Multi-cloud? | ⚠️ **Best-of-breed per workload, or leverage. Not resilience** (§17 → `hyperscaler-cost-reliability-iac-lock-in-and-migration`) |
| Can I leave without paying egress? | ⚠️ **Narrow full-exit terms today; EU ban Jan 2027** (§21.1) |

### 25.2 New-environment checklist
- [ ] ⚠️ **Separate account/subscription/project per environment** (§4 → `hyperscaler-framing-responsibility-identity-and-hierarchy`)
- [ ] ⚠️ **Org-level guardrails: SCPs / Azure Policy / Org Policy** (§4 → `hyperscaler-framing-responsibility-identity-and-hierarchy`)
- [ ] ⚠️ **Audit logging on, org-wide, written where operators can't alter it** (§13 → `hyperscaler-storage-databases-analytics-and-observability`)
- [ ] ⚠️ **No static keys — roles / managed identities / federation** (§3 → `hyperscaler-framing-responsibility-identity-and-hierarchy`)
- [ ] MFA (phishing-resistant) on all human production access (§3 → `hyperscaler-framing-responsibility-identity-and-hierarchy`)
- [ ] ⚠️ **Tagging enforced by policy from day one** (§4 → `hyperscaler-framing-responsibility-identity-and-hierarchy`, §14 → `hyperscaler-cost-reliability-iac-lock-in-and-migration`)
- [ ] ⚠️ **Budgets and anomaly alerts before anything is deployed** (§14 → `hyperscaler-cost-reliability-iac-lock-in-and-migration`)
- [ ] IaC with remote locked state; state treated as secret (§16 → `hyperscaler-cost-reliability-iac-lock-in-and-migration`)
- [ ] Multi-AZ for anything production (§15 → `hyperscaler-cost-reliability-iac-lock-in-and-migration`)
- [ ] ⚠️ **Private endpoints for managed services** (§5 → `hyperscaler-networking-compute-containers-and-serverless`)
- [ ] Storage lifecycle policies and log TTLs (§9 → `hyperscaler-storage-databases-analytics-and-observability`, §14 → `hyperscaler-cost-reliability-iac-lock-in-and-migration`)
- [ ] ⚠️ **Know your egress paths before the architecture is fixed** (§14 → `hyperscaler-cost-reliability-iac-lock-in-and-migration`, §21.1)

---

## §26. Method

**§1–§20 → `hyperscaler-framing-responsibility-identity-and-hierarchy`, `hyperscaler-networking-compute-containers-and-serverless`, `hyperscaler-storage-databases-analytics-and-observability`, `hyperscaler-cost-reliability-iac-lock-in-and-migration` rest on stable material** — **IAM models, resource hierarchies, network
architecture, service equivalences and cost mechanics** — **and none of it needed
verification.** ⚠️ **Service names churn (Azure AD → Entra ID, Synapse → Fabric) but the
underlying architecture is durable, which is why §20 is a capability table rather than a
feature comparison.**

**Two searches were run in August 2026**, on **egress pricing and the EU Data Act** and
**market position** — ⚠️ **the two areas where a 2024-vintage answer is now materially
wrong.**

**Confidence.** **High** in §1–§20 → `hyperscaler-framing-responsibility-identity-and-hierarchy`, `hyperscaler-networking-compute-containers-and-serverless`, `hyperscaler-storage-databases-analytics-and-observability`, `hyperscaler-cost-reliability-iac-lock-in-and-migration`. ⚠️ **§3 → `hyperscaler-framing-responsibility-identity-and-hierarchy` is the section I'd most want read** — **the
Entra/Azure-RBAC split, AWS's intersecting-policies-with-explicit-deny evaluation, and
GCP's additive inheritance are the three things that most reliably catch experienced
engineers moving between platforms**, **and they're structural rather than incidental.**

**High** in §21.1's sequence — **Google January 2024, AWS March 2024, Microsoft mid-March
2024, EU Data Act applicable 12 September 2025 with the full charge ban from 12 January
2027** — **which is consistent across many independent sources including a UK CMA
appendix.** ⚠️ **I've flagged hard that the exit waivers are far narrower than the
headlines suggest, because that's the part that actually determines whether you can act on
it.** **The DMA gatekeeper designation is reported expectation, not decided, and I've said
so.** ⚠️ **Specific per-GB rates are approximate and tiered; verify against pricing pages.**

⚠️ **§21.2 contains a disagreement I've flagged rather than resolved.** **Market share
figures vary by several points across sources, and reported AWS growth for the same period
ranged from 24% to 37% — a spread wide enough that at least some of it is measurement
error or definitional difference rather than reality.** ⚠️ **Microsoft doesn't disclose
Azure as a standalone revenue figure, so any Azure dollar number you see is an estimate.**
**I've given the most-cited Synergy figures, shown the range, and said to trust the
direction.** **The direction — Google gaining fast, AWS eroding through slower growth in a
rapidly expanding market, capacity constrained — is consistent everywhere and is the part
that affects architecture decisions.**

⚠️ **Sourcing caution**: **much of the cloud-comparison and egress material online is
published by vendors selling migration tooling, FinOps platforms, interconnect services or
competing storage** — **and the framing tends toward urgency about lock-in.** **The
underlying facts recur across independent sources including regulatory filings; the
"act now" framing around them is marketing.** **Where I could anchor on a regulator (the
CMA appendix, the Data Act dates) or a primary earnings release, I did.**
