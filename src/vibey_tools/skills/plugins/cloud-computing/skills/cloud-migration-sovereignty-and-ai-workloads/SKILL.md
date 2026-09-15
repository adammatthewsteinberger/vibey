---
name: cloud-migration-sovereignty-and-ai-workloads
description: "Use when planning a migration, answering a data-residency or sovereignty question, arguing about multi-cloud, or sizing AI infrastructure: migration strategy and the 7 Rs, data residency versus sovereignty and the EU Data Act's January 2027 egress deadline, multi-cloud and lock-in assessed honestly, GPU and AI-workload economics, and sustainability and carbon accounting."
---

# Cloud Computing: Migration, Sovereignty, Multi-Cloud, AI Workloads, and Sustainability

> **Part 4 of 5** of the *Cloud Computing* reference (plugin `cloud-computing`), covering §10–§14. Sibling skills: `cloud-models-providers-and-primitives` (§0–§3), `cloud-architecture-and-resilience` (§4–§6), `cloud-cost-security-and-operations` (§7–§9), `cloud-reference` (§15–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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

## §10. Migration

**[DURABLE] The 6 (or 7) Rs, and most organizations pick wrong:**

| Strategy | What | When |
|---|---|---|
| **Rehost** ("lift and shift") | Move as-is | Speed, deadline pressure. ⚠️ **You inherit every existing problem and gain little** |
| **Replatform** | Minor optimizations en route (managed DB, containerize) | ⚠️ **The pragmatic sweet spot for most workloads** |
| **Refactor / re-architect** | Redesign for cloud-native | High value, high cost. Reserve for what earns it |
| **Repurchase** | Move to SaaS | Commodity capability |
| **Retire** | Turn it off | ⚠️ **Consistently underused — a surprising share of any estate is unused** |
| **Retain** | Leave it | Regulatory, or the business case isn't there |
| **Relocate** | Move hypervisor-level | VMware-style bulk moves |

**⚠️ The characteristic mistakes**: lift-and-shift everything then be surprised the bill
went up (you moved a fixed-capacity design onto per-hour billing); **rewriting everything
at once** (see Strangler Fig in a design-patterns reference); **migrating without a
dependency map**; **no rollback plan**; and **treating migration as a project rather than
the start of an operating model change** — which is the one that actually determines
whether it works.

**[DURABLE] Migrate in waves**, starting with something low-risk that teaches you the
operational model, and **measure before and after** so the business case survives contact
with the invoice.

---

## §11. Sovereignty, the EU Data Act, and Egress

**[VERSIONED — and §11.2 contains the most consequential dated fact in this document.]**

### 11.1 Data residency vs. sovereignty

**⚠️ The distinction that most organizations get wrong**, and one 2026 analysis names it
directly as **"the residency illusion" — the belief that a local data center footprint
satisfies sovereignty.** It doesn't.

- **Residency** — the data physically sits in region X.
- **Sovereignty** — **no foreign jurisdiction can compel access to it.**

**The gap is legal, not technical**: **US providers remain subject to US legal demands
under the CLOUD Act regardless of where the data sits**, which sits in tension with EU
sovereignty principles and GDPR Article 48. **A Frankfurt region does not solve this by
itself.** What narrows the gap: customer-managed keys with hold-your-own-key
arrangements, confidential computing, EU-operated sovereign offerings, and architectures
where the **provider cannot access unencrypted data** rather than merely promising not to.

### 11.2 ⚠️ The EU Data Act — the January 2027 deadline

**Regulation (EU) 2023/2854.** Entered into force 11 January 2024; **switching provisions
applicable from 12 September 2025**; **the critical date is 12 January 2027.**

| Date | What |
|---|---|
| **12 Sept 2025** | Cloud switching rights became **enforceable** across the EU — portability and switching-support obligations live |
| **Sept 2025 → Jan 2027** | Transition. Switching and egress charges permitted **only at direct, transparent, pre-agreed cost** — not exceeding costs directly incurred |
| **12 Sept 2026** | Products released after this date must be designed so **user data is accessible by default** |
| **⚠️ 12 January 2027** | **All switching charges, including data egress fees, are banned outright** for in-scope providers serving EU customers — **IaaS, PaaS and SaaS alike**, and **for every provider serving EU customers, not only European ones** |

**What remains chargeable**: standard service and subscription fees, proportionate early
termination fees on fixed-term contracts, and genuinely optional premium migration
services. **⚠️ Expect providers to move residual switching cost into base pricing** —
industry observers anticipated exactly this during the transition window.

**Enforcement** is delegated to **national authorities designated by each member state**,
with **penalties set in local legislation** — so they vary across the EU, though the Act
requires them to be effective.

> **⚠️ GOTCHA — three things to act on now.** **(1) The deadline is 12 January 2027, not
> 2026** — a commonly muddled point. **(2) Contracts do not auto-fix themselves**:
> auto-renewal clauses and migration-fee terms must be actively reviewed or the old cost
> structure stays in force. **(3) The fee was only the most visible lock-in.**
> **Proprietary APIs, vendor-specific data formats, and IAM binding keep you locked in
> long after the invoice line disappears** — six months' lead time is barely enough for
> serious exit planning.

**Note also**: AWS, Azure and Google **already waived egress fees for full exits in 2024**,
ahead of the regulation — but that is narrower than what 2027 requires. And the **DMA is
separately investigating AWS and Azure as potential gatekeepers**, which would add
interoperability obligations; **⚠️ analysts have flagged genuine friction between the two
regimes**, including conflicting compliance timelines and split enforcement (member states
for the Data Act, the Commission for the DMA).

**[VERSIONED] On 3 June 2026 the European Commission proposed the Cloud and AI Development
Act** as part of a Tech Sovereignty Package, proposing an **EU-wide method for assessing
how sovereign a cloud or AI service actually is, with graded levels for public-sector
providers.** ⚠️ **Still to pass Parliament and Council — details will change** — but the
direction is that "sovereign cloud" becomes a regulated standard rather than a sales claim.

### 11.3 Egress in practice

**[DURABLE] Data transfer pricing is asymmetric by design**: ingress free, egress charged,
**cross-AZ and cross-region transfer charged**, and internet egress most expensive.

**The architectural responses**: keep compute next to data; **use CDN for repeated
external delivery**; be deliberate about cross-AZ chatter (⚠️ **a chatty microservice mesh
spanning AZs is a recurring surprise line item**); use private endpoints; consider
providers with different egress models for egress-heavy workloads.

---

## §12. Multi-Cloud and Lock-In

**[CONTESTED, and worth stating both cases properly.]**

**⚠️ Multi-cloud reported adoption is high — around 87% by one 2026 count — but the term
covers three very different things**, and conflating them causes most of the confusion:

| Meaning | Reality |
|---|---|
| **Different workloads on different clouds** | ⚠️ **This is what most "multi-cloud" actually is.** Common, sensible, often the residue of acquisitions |
| **The same workload portable across clouds** | Expensive. Constrains you to the lowest common denominator |
| **The same workload running actively on several** | Rare, genuinely hard, occasionally justified |

**The case for**: negotiating leverage, regulatory requirement, resilience against
provider failure (§6 → `cloud-architecture-and-resilience`), best-of-breed service selection, avoiding concentration risk.
**The case against**: **you multiply operational surface, split your team's expertise,
forgo deep managed services, lose volume discounts, and pay inter-cloud egress** — and the
2025 outages showed that **cross-provider failover is much harder than owning it is.**

**[DURABLE] The pragmatic position most practitioners land on**: **develop against open
standards and abstract where it's cheap** — Kubernetes, OpenTelemetry, Terraform,
Postgres-compatible databases, S3-compatible object storage. **If a provider offers a
proprietary service with genuine business value, use it — but understand the trade-off
explicitly** and document the exit path. **⚠️ The worst outcome is accidental lock-in: you
paid the abstraction cost, and you're still locked in via IAM, data formats, and
operational habit.**

**[VERSIONED] And note the regulatory shift**: from January 2027 the EU removes the
*financial* barrier to switching (§11.2) — **which makes the technical and contractual
lock-in the whole of the problem** rather than one part of it.

---

## §13. AI Workloads

**[VERSIONED — the fastest-moving economics in cloud right now.]**

**⚠️ AI has broken the cost assumptions that FinOps was built on**, and the numbers make
the point: **GPUs reportedly make up ~18% of spend at AI-forward organizations, up from
~4% in 2023**, and **statically provisioned GPU fleets run at only 30–40% utilization.**
**Idle accelerators are the fastest-growing waste category and the most expensive per
hour.** **AI cost management is now cited as the top FinOps priority (98% of practitioners
in the 2026 FinOps Foundation survey), and the most-wanted skillset.**

**What's structurally different from conventional workloads:**
- **Training** is bursty, enormous, and interruption-tolerant — **⚠️ a near-perfect fit
  for spot/preemptible capacity that is widely under-exploited.**
- **Inference** is steady-state and latency-sensitive; economics are dominated by
  utilization and batching.
- **⚠️ Capacity, not price, is often the binding constraint.** Reservations and
  capacity blocks matter more than hourly rate.
- **⚠️ Forecasting is structurally harder** — which is precisely why Flexera attributes the
  waste reversal to AI outpacing existing tagging and attribution practice (§7.1 → `cloud-cost-security-and-operations`).
- **Data gravity intensifies.** Training data is enormous; moving it is expensive; **this
  is a lock-in force as much as a cost one.**
- **Token-based pricing for managed model APIs is a genuinely different cost model** —
  per-request, variable by output length, and easy to lose control of.

**[DURABLE] The engineering responses**: track **cost per training run and cost per
inference/token**; use spot for training with checkpointing; batch and cache inference;
right-size the model to the task; and **attribute AI spend to teams and features from day
one** — retrofitting attribution is what the 2026 waste numbers are measuring.

---

## §14. Sustainability

**[VERSIONED] Now a Well-Architected pillar and, in the EU, an emerging reporting
obligation.** Flexera has reported **over half of organizations having or planning a
sustainability initiative including carbon-footprint tracking of cloud use.**

**What actually reduces emissions**, in rough order: **region selection** (⚠️ **carbon
intensity of the grid varies enormously by region — often the single largest lever and the
cheapest to pull**), **utilization** (an idle instance is pure waste in both senses),
**right-sizing**, **efficient architectures** (serverless and spot improve fleet-level
utilization), **storage lifecycle**, and **workload time-shifting** to low-carbon hours
where the work is deferrable.

**⚠️ Read provider claims carefully.** "Carbon neutral" via offsets, "100% renewable" via
annual matching, and **"24/7 carbon-free energy" (hourly matching) are materially
different claims** — the third is much stronger. Providers publish carbon tooling; treat
the methodology as part of the number.
