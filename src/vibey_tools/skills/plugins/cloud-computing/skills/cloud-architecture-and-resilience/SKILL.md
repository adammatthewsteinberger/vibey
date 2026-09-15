---
name: cloud-architecture-and-resilience
description: "Use when designing or hardening a cloud architecture: the Well-Architected trade-offs, regions and availability zones, containers, Kubernetes and serverless and when each is the wrong answer, and resilience — what the 2025 outages actually taught about control-plane dependencies, multi-region failover, static stability, and designing for blast radius."
---

# Cloud Computing: Architecture, Containers and Serverless, and Resilience

> **Part 2 of 5** of the *Cloud Computing* reference (plugin `cloud-computing`), covering §4–§6. Sibling skills: `cloud-models-providers-and-primitives` (§0–§3), `cloud-cost-security-and-operations` (§7–§9), `cloud-migration-sovereignty-and-ai-workloads` (§10–§14), `cloud-reference` (§15–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Verified August 2026. See §17 → `cloud-reference` for the currency snapshot and what goes stale first.

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
>    control-plane dependencies nobody had drawn (§6). **Map what you actually depend on,
>    not what you think you depend on.**
> 3. **Cost is an architectural property, not an operational afterthought.** It is
>    determined by design decisions — data placement, service selection, egress paths —
>    and **discovered on an invoice 30 days later** (§7 → `cloud-cost-security-and-operations`). Design for it up front or pay
>    for it forever.

---

## §4. Architecture

**[DURABLE] The Well-Architected framing is genuinely useful, and the six pillars are
consistent across providers** (AWS's naming; Azure and Google have near-equivalents):
**Operational excellence, Security, Reliability, Performance efficiency, Cost
optimization, Sustainability.**

**⚠️ The pillars conflict, and that's the point.** Reliability costs money. Security costs
latency. Cost optimization costs resilience. **A framework that told you they were all
compatible would be useless — its value is in forcing the trade-off into the open.**

**[DURABLE] The principles that carry the most weight:**
- **Design for failure.** Everything fails. Assume it (§6).
- **Loose coupling** — queues and events between components so one failure doesn't
  propagate synchronously.
- **Statelessness at the compute tier** so instances are disposable.
- **⚠️ Immutable infrastructure** — replace rather than patch. **This single practice
  eliminates configuration drift**, which is the root cause of an enormous share of
  incidents.
- **Everything as code** — infrastructure, policy, pipelines. Reviewable, versioned,
  reproducible.
- **Automate everything you'd otherwise do at 3am.**
- **Right-size continuously**, not once at launch.

**Infrastructure as Code**: **Terraform / OpenTofu** (multi-cloud standard),
**Pulumi** (real programming languages), **CloudFormation / ARM / Bicep** (native),
**CDK** (native, in code), **Crossplane** (Kubernetes-native). ⚠️ **State management,
drift detection, and a plan-review discipline matter more than the tool choice.**

---

## §5. Containers, Kubernetes, and Serverless

**Containers** package the app and its dependencies. **[DURABLE] The genuine win is
environment parity** — the same artifact runs everywhere.

**Kubernetes** is the orchestration standard and **⚠️ the most over-adopted technology in
this document.** It is genuinely excellent at multi-team, multi-service platforms at scale;
it is genuinely a poor fit for a team of five running three services. **The honest test:
do you have the operational capacity to run it, or are you adopting a platform team's
problem without the platform team?** Managed control planes (EKS/AKS/GKE) remove some but
not most of the burden.

**The lighter options are underrated**: **Cloud Run, ECS/Fargate, Container Apps,
App Runner, Fly.io** — containers without cluster operations. **For most workloads this is
the right answer**, and the fact that it's less impressive is not an argument.

**Serverless / FaaS** — event-driven, scale-to-zero, per-invocation billing.
**⚠️ The constraints are design forces, not details**: cold starts, execution time limits,
statelessness, **local development friction**, vendor coupling in the event model, and
**⚠️ cost that inverts at sustained high volume** — serverless is cheap when idle and
expensive when busy, which is exactly backwards from a VM. **Model both curves before
committing.**

---

## §6. Resilience — and the 2025 Lessons

**[VERSIONED in the specifics, DURABLE in the lesson. This section is the most important
practical material in the document.]**

### 6.1 What happened

**October–November 2025 delivered three object lessons within weeks:**

- **20 October 2025 — AWS us-east-1**, roughly **14–15 hours**. Root cause: **a latent race
  condition in DynamoDB's DNS management system** that **wiped out DNS records for critical
  endpoints**, cascading into failures across dozens of AWS services and the long tail of
  applications depending on them.
- **29 October 2025 — Azure**, tied to **Azure Front Door** (its CDN and routing layer)
  and reported as involving global identity management, degrading a broad set of
  Azure-fronted services.
- **18 November 2025 — Cloudflare**: a **Bot Management configuration change doubled the
  size of a feature file, exceeding a hard-coded limit in the traffic proxy**, crashing
  and restarting processes across the global network. Widespread 5xx errors across major
  services. ⚠️ **For two hours Cloudflare's own engineers believed they were under
  DDoS attack** — the wave pattern looked like one — and only identified it by correlating
  with their rollout timing.

### 6.2 What it actually taught

> **⚠️ GOTCHA — the lesson that cost the most money: many engineers had done everything
> "right."** They deployed across multiple availability zones, implemented health checks,
> and followed the Well-Architected Framework. **None of it mattered when the region
> failed.**
>
> **The durable principle: the failure domain of a cloud service is almost always larger
> than the region boundary your architecture diagram implies.**

**The specific structural findings worth carrying:**
- **⚠️ Multi-AZ is not multi-region.** AZ redundancy protects against a datacenter
  failure, not a regional control-plane failure.
- **⚠️ us-east-1 is a global single point of failure**, not merely a region. It is AWS's
  oldest, largest, and usually cheapest region, attracting a disproportionate share of
  workloads — one analysis put it at **~69%** of AWS usage and another measured
  **44%+ of AWS requests**. **Certain global operations (parts of IAM, Route 53,
  global-service control operations) are anchored there.** Audit whether your failover
  path silently routes through it.
- **⚠️ Control-plane dependencies are the hidden coupling.** Many organizations with
  multi-region deployments still failed because their **databases, queues, or functions**
  remained single-region.
- **⚠️ The supporting cast takes you down, not the primary infrastructure.** As one
  analysis of the 2025 incidents put it: what took organizations down **wasn't their
  primary infrastructure — it was the supporting mechanisms.** When Docker Hub went
  offline, teams couldn't pull containers; **third-party monitoring and alerting failed
  because it sat behind Cloudflare.**
- **⚠️ Shared bottleneck layers.** DNS, CDN, identity, and security have become chokepoints
  where a single misconfiguration disrupts huge portions of the internet.
- **The common pattern across all three: a subtle defect in one subsystem triggering
  global cascading failure** — and the diagnosis offered by practitioners is not "human
  error" but **immature blast-radius modelling**: teams push changes without understanding
  their dependency surface.

### 6.3 What to actually do

**[DURABLE] In order of value per unit of effort:**
1. **Map your real dependency graph**, including SaaS tools and their underlying
   providers. **⚠️ If your team uses Jira, you have an AWS dependency** — treat those as
   Tier-1 dependencies in BCP/DR planning.
2. **Define RTO and RPO per workload**, and be honest that not everything needs the same
   ones.
3. **Design degraded modes.** ⚠️ **Read-only from a standby, feature toggles disabling
   non-critical paths, and graceful degradation beat a binary up/down** — and they're far
   cheaper than full active-active.
4. **Harden DNS**: dual providers with health checks, sensible TTLs, regional endpoints,
   and **no hidden dependency on one region for control traffic.**
5. **Decouple control plane from data plane** — CI/CD, IaC state, artifact registries and
   runbooks must stay reachable when your primary provider is down.
6. **Choose replication mode per workload deliberately** — async, sync/quorum, or log
   shipping, with an RPO per domain (orders ≈ 0, analytics tolerates minutes).
7. **Application-level resilience**: timeouts everywhere, exponential backoff with jitter,
   circuit breakers.
8. **⚠️ Test the failover.** An untested runbook is a hypothesis. **Game days and chaos
   engineering exist because the failover path is itself a system that can be broken.**
9. **The framing to aim for**: when the provider fails, you want to be asking **"should we
   fail over?"** against agreed parameters — **not "can we?"**

**⚠️ And be honest about the cost.** Multi-region roughly doubles infrastructure cost and
substantially increases complexity. **Single-region is a legitimate choice for
non-critical workloads with clear stakeholder expectations** — what's not legitimate is
making it by accident.
