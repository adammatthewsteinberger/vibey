---
name: cloud-models-providers-and-primitives
description: "Use when choosing a cloud model or provider, or reasoning about the basic building blocks: IaaS, PaaS and SaaS, the deployment models, the five NIST characteristics, the provider landscape (AWS, Azure, Google Cloud and the second tier) and how to choose between them, and the primitives — compute, storage classes, networking and VPCs, and identity and IAM. Includes the router for the whole cloud-computing reference."
---

# Cloud Computing: Models, the Provider Landscape, and the Primitives

> **Part 1 of 5** of the *Cloud Computing* reference (plugin `cloud-computing`), covering §0–§3. Sibling skills: `cloud-architecture-and-resilience` (§4–§6), `cloud-cost-security-and-operations` (§7–§9), `cloud-migration-sovereignty-and-ai-workloads` (§10–§14), `cloud-reference` (§15–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
>    control-plane dependencies nobody had drawn (§6 → `cloud-architecture-and-resilience`). **Map what you actually depend on,
>    not what you think you depend on.**
> 3. **Cost is an architectural property, not an operational afterthought.** It is
>    determined by design decisions — data placement, service selection, egress paths —
>    and **discovered on an invoice 30 days later** (§7 → `cloud-cost-security-and-operations`). Design for it up front or pay
>    for it forever.

---

## §0. Routing

| Asked about... | Go to |
|---|---|
| Service and deployment models | §1 |
| Which provider, and market reality | §2 |
| Compute, storage, networking, identity | §3 |
| Architecture and Well-Architected | §4 → `cloud-architecture-and-resilience` |
| Containers, Kubernetes, serverless | §5 → `cloud-architecture-and-resilience` |
| **Resilience, and the 2025 outage lessons** | **§6 → `cloud-architecture-and-resilience`** |
| **Cost engineering and FinOps** | **§7 → `cloud-cost-security-and-operations`** |
| Security and shared responsibility | §8 → `cloud-cost-security-and-operations` |
| Operations and observability | §9 → `cloud-cost-security-and-operations` |
| Migration strategy | §10 → `cloud-migration-sovereignty-and-ai-workloads` |
| **Sovereignty, the EU Data Act, egress** | **§11 → `cloud-migration-sovereignty-and-ai-workloads`** |
| Multi-cloud and lock-in | §12 → `cloud-migration-sovereignty-and-ai-workloads` |
| AI workloads and their economics | §13 → `cloud-migration-sovereignty-and-ai-workloads` |
| Sustainability | §14 → `cloud-migration-sovereignty-and-ai-workloads` |
| "Don't do this" | §15 → `cloud-reference` |
| "Which side is right?" | §16 → `cloud-reference` |
| "Is this still current?" | §17 → `cloud-reference` |
| Books and resources | §18 → `cloud-reference` |

---

## §1. Models

### 1.1 Service models

```
On-prem  →  IaaS  →  CaaS  →  PaaS  →  FaaS  →  SaaS
◄─────────── you manage more        you manage less ───────────►
◄─────────── more control           less operational burden ───►
◄─────────── more lock-in risk?     ⚠️ see §12 — it's not that simple
```

**[DURABLE] The trade-off is real in both directions**, and the common mistake is
optimizing only one end. Managed services cost more per unit and less in engineering time;
raw IaaS is cheaper per unit and you pay for it in people. **⚠️ The comparison people skip
is the fully-loaded one** — a managed database's premium is frequently less than one
engineer's fraction of time keeping a self-hosted one patched, backed up, and monitored.

### 1.2 Deployment models
**Public**, **private**, **hybrid** (⚠️ **the actual state of most large enterprises**,
whatever the strategy deck says), **multi-cloud** (§12 → `cloud-migration-sovereignty-and-ai-workloads`), and **edge**. **Sovereign cloud**
is now a distinct category with regulatory meaning rather than a marketing label (§11 → `cloud-migration-sovereignty-and-ai-workloads`).

### 1.3 The five NIST characteristics
On-demand self-service, broad network access, resource pooling, rapid elasticity,
measured service. **[DURABLE] Dated 2011 and still the cleanest definition** — and
"measured service" is the one that quietly determines your architecture (§7 → `cloud-cost-security-and-operations`).

---

## §2. The Provider Landscape

**[VERSIONED — and read the ⚠️ in this section before quoting any number.]**

**Market structure as of Q1 2026**: the Big Three hold roughly **60–68%** of global cloud
infrastructure spend, with the market reaching **~$129B in Q1 2026, growing ~35% YoY** —
described as the **ninth consecutive quarter of increasing year-over-year growth**.

> **⚠️ GOTCHA — the share figures genuinely conflict across sources, and you should know
> why before citing them.** Synergy Research puts Q1 2026 at **AWS 28%, Azure 21%, Google
> Cloud 14%**. Other widely-circulated figures give **AWS 30% / Azure 24–25% / GCP 13%**,
> and others still **AWS 32% / Azure 23% / GCP 11%**.
>
> **The discrepancy is methodological, not an error.** One analysis explains it directly:
> Azure's higher share estimates **exceed a straight revenue calculation because Synergy
> weights IaaS-and-PaaS spend, where Azure is stronger** — and separately, **Microsoft
> does not break out Azure revenue at all, only its growth rate**, so any "Azure revenue"
> figure is derived. **Both kinds of figure are valid; they measure different scopes.**
> **Cite the source and the scope, or don't cite the number.**

**Growth is the more interesting story than share**: Azure and Google Cloud have been
growing substantially faster off smaller bases, with Google Cloud posting the highest rates
of the three. **AI is the driver** — AI-related spending was reported at **~19% of total
cloud spend in 2026, up from ~8% in 2023.**

**⚠️ The capex arms race is the structural fact underneath all of it.** 2026 guidance
figures in circulation: **Amazon ~$200B, Microsoft ~$190B, Alphabet ~$180–190B.** This
functions as a moat — the cost of building global infrastructure excludes almost everyone
— and it carries genuine risk: **the Big Three are betting hundreds of billions that AI
demand will justify the build-out, and if it disappoints the write-downs would be
enormous.** For a buyer, large capex commitments are **both a supply signal and a
lock-in signal.**

**Choosing** — the honest criteria, roughly in order: **existing skills and contracts**
(⚠️ **usually decisive and rarely stated**), **the specific services you need**,
**regional and data-residency footprint** (§11 → `cloud-migration-sovereignty-and-ai-workloads`), **pricing for your actual shape of
workload**, **enterprise agreements and discounts**, and **regulatory posture**.
**Beyond the Big Three**: Oracle Cloud, IBM, Alibaba, and the **"neoclouds"** — GPU-focused
providers (CoreWeave, Lambda and others) estimated collectively at a small but real share
segment. **Cloudflare, Fastly, Vercel, Fly.io** for edge; **DigitalOcean, Hetzner,
Scaleway** for straightforward compute at markedly lower prices.

---

## §3. The Primitives

**[DURABLE] Every provider has these under different names. Learn the primitive, map the
name.**

**Compute**: VMs (⚠️ **still the majority of cloud spend**), containers (§5 → `cloud-architecture-and-resilience`), serverless
functions, GPU/accelerator instances (§13 → `cloud-migration-sovereignty-and-ai-workloads`), bare metal. **Pricing modes matter more than
instance choice**: on-demand, reserved/committed (1–3 year, **large discounts**), savings
plans, **spot/preemptible** (⚠️ **60–90% cheaper and interruptible — enormously underused
for batch, CI, and fault-tolerant work**), dedicated hosts.

**Storage**, and **⚠️ picking the wrong class is one of the most common cost errors**:

| Type | Use | ⚠️ Watch |
|---|---|---|
| **Object** (S3, Blob, GCS) | The default for almost everything: static assets, data lakes, backups | Request costs at high volume; egress (§11 → `cloud-migration-sovereignty-and-ai-workloads`) |
| **Block** (EBS, Managed Disks) | Filesystem for a VM | ⚠️ **Provisioned, not consumed — you pay for the size you asked for, idle or not** |
| **File** (EFS, Azure Files) | Shared POSIX access | Expensive per GB |
| **Archive** (Glacier, Archive tier) | Long-term retention | ⚠️ **Retrieval time and retrieval cost — and early-deletion fees** |

**⚠️ Lifecycle policies are free money and routinely unconfigured.** Object storage tiering
from hot → cool → archive on an age rule takes minutes to set and runs forever.

**Networking**: VPC/VNet, subnets, security groups/NSGs, load balancers (L4 and L7),
DNS, CDN, private endpoints, peering, transit gateway/hub-spoke, NAT gateways
(⚠️ **a surprisingly large and invisible line item at volume**).

**Identity** — **[DURABLE] the most important primitive and the most commonly
misconfigured** (§8 → `cloud-cost-security-and-operations`): workload identity (⚠️ **use it — long-lived access keys are the
single most common cloud breach vector**), roles and policies, federation, and
**least privilege as an actual practice rather than an aspiration**.

**Managed data services**: relational, NoSQL, cache, search, queues and streams, data
warehouse. **⚠️ Each is a lock-in decision as well as an architecture decision** (§12 → `cloud-migration-sovereignty-and-ai-workloads`).
