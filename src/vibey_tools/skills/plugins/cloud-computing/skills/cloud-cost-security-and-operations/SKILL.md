---
name: cloud-cost-security-and-operations
description: "Use when a cloud bill, a security boundary, or an on-call problem needs work: cost engineering and FinOps (commitments and reservations, rightsizing, where the money actually goes wrong), security and the shared responsibility model (IAM, misconfiguration, encryption, and the provider-versus-customer line), and operations and observability — logs, metrics, traces, SLOs and incident response."
---

# Cloud Computing: Cost Engineering, Security, and Operations

> **Part 3 of 5** of the *Cloud Computing* reference (plugin `cloud-computing`), covering §7–§9. Sibling skills: `cloud-models-providers-and-primitives` (§0–§3), `cloud-architecture-and-resilience` (§4–§6), `cloud-migration-sovereignty-and-ai-workloads` (§10–§14), `cloud-reference` (§15–§20). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
>    and **discovered on an invoice 30 days later** (§7). Design for it up front or pay
>    for it forever.

---

## §7. Cost Engineering and FinOps

**[VERSIONED in figures, DURABLE in method.]**

### 7.1 The state of it

**⚠️ Cloud waste reversed a five-year improving trend in 2026.** Flexera's 2026 *State of
the Cloud* (n=753 cloud decision-makers, 15th edition) estimates **29% of IaaS/PaaS spend
is wasted, up from 27%** — with the reversal **attributed largely to AI adoption
outpacing the tagging, attribution, and governance practices FinOps teams had built for
predictable workloads like VMs and storage.**

Other 2026 findings worth knowing: **managing cloud spend is the top priority (84%),
surpassing security**; **FinOps team prevalence ~63%** and **Cloud Centers of Excellence
~71%**; **fewer than half of organizations use any one commitment discount per provider**
(⚠️ **that is free money left on the table**); and **~21% of workloads have been
repatriated**, though **new cloud workloads outstrip the exits, so cloud continues to
grow.**

**⚠️ The nature of the work has shifted, and this matters for expectation-setting**:
practitioners consistently report that **the large, obvious waste has already been
addressed** — what remains is **smaller savings distributed across more workloads,
requiring deeper analysis and tighter engineering collaboration.** More respondents now
prioritize governance, forecasting, and organizational alignment over pure optimization.

### 7.2 Where the money actually goes wrong

| Cause | Fix |
|---|---|
| **Idle and zombie resources** | Scheduled shutdown for non-prod; automated detection |
| **Over-provisioning** | Right-size continuously against real utilization |
| **⚠️ Orphaned storage** — detached volumes, old snapshots past any retention policy | Lifecycle policies (§3 → `cloud-models-providers-and-primitives`) |
| **No commitment coverage** | Reserved instances / savings plans on your stable baseline |
| **Not using spot** | ⚠️ 60–90% cheaper for interruptible work |
| **Egress and cross-AZ transfer** | ⚠️ **Frequently the invisible line item** (§11 → `cloud-migration-sovereignty-and-ai-workloads`) |
| **Wrong storage class** | Tiering (§3 → `cloud-models-providers-and-primitives`) |
| **Untagged resources** | ⚠️ **You cannot allocate what you cannot attribute** |
| **⚠️ Idle GPUs** | §13 → `cloud-migration-sovereignty-and-ai-workloads` — the fastest-growing waste category |

**[DURABLE] The FinOps method**: **Inform** (visibility, tagging, allocation, showback) →
**Optimize** (rightsizing, commitments, architecture) → **Operate** (governance,
forecasting, continuous improvement). **Federated model** — a small central team enabling
embedded champions, because **central teams cannot scale by headcount.**

**[VERSIONED] FOCUS** (FinOps Open Cost and Usage Specification) standardizes cost and
usage data across providers, addressing the normalization problem as FinOps expands to
cover SaaS, licensing, Kubernetes, and data platforms.

**⚠️ The measure that changes behaviour: unit economics.** Cost per transaction, per
customer, per feature — **not the aggregate bill.** An aggregate that goes up is
ambiguous; a cost-per-order that goes up is a bug.

**[DURABLE] And the engineering point**: cost is set at design time. **The three
decisions that dominate are data placement (egress), service selection (managed vs.
self-run), and the commitment/spot mix.** Everything after that is optimization at the
margins.

---

## §8. Security and Shared Responsibility

**[DURABLE] The shared responsibility model, stated precisely because it's constantly
misread:**

```
                     IaaS        PaaS        SaaS
Data & access     ─ YOU ──────── YOU ──────── YOU ──►  ⚠️ ALWAYS YOU
Application       ─ YOU ──────── YOU ──────── provider
Runtime/OS        ─ YOU ──────── provider ─── provider
Virtualization    ─ provider ─── provider ─── provider
Physical          ─ provider ─── provider ─── provider
```

**⚠️ "Security *of* the cloud" is theirs; "security *in* the cloud" is yours — and the
overwhelming majority of cloud breaches are on the customer side of that line.**

**The recurring failure modes**, roughly by frequency: **public storage buckets**,
**over-permissive IAM** (⚠️ **wildcard policies that were "temporary"**), **long-lived
access keys** (⚠️ **use workload identity/OIDC federation instead — this single change
removes the most common breach vector**), **secrets in code or environment variables**
(use a managed secret store), **unencrypted data**, **open security groups**, **no MFA on
privileged accounts**, **unpatched images**, and **⚠️ no logging, which turns an incident
into an unanswerable question.**

**The practices that matter**: **least privilege, enforced** (start deny-all, add
specifically); **defense in depth**; **zero trust** (⚠️ **network location is not
authorization** — an internal VPC is not a trust boundary); **encryption at rest and in
transit** with **customer-managed keys where it's warranted** (§11 → `cloud-migration-sovereignty-and-ai-workloads`); **network
segmentation and private endpoints**; **policy as code** (Sentinel, OPA, Azure Policy,
SCPs) to make misconfiguration structurally impossible rather than merely discouraged;
and **CSPM/CNAPP tooling** for continuous posture assessment.

**Compliance**: SOC 2, ISO 27001, PCI DSS, HIPAA, FedRAMP, DORA. **⚠️ Provider
certification does not make you compliant** — it means the underlying platform can support
a compliant deployment. The configuration is yours.

---

## §9. Operations and Observability

**[DURABLE] The three signals plus two**: metrics, logs, traces — and **profiles** and
**events** are increasingly treated as first-class.

**[VERSIONED] OpenTelemetry is the vendor-neutral standard** and the right default for
instrumentation, precisely because it decouples your instrumentation from your backend
choice — which is a lock-in decision you'd rather not make twice.

**What to actually measure**: **SLIs and SLOs** derived from user-visible behaviour, with
**error budgets** driving the release-vs-stability conversation; the **RED method**
(Rate, Errors, Duration) for services; **USE** (Utilization, Saturation, Errors) for
resources; and **⚠️ the four golden signals** — latency, traffic, errors, saturation.

**⚠️ Alert on symptoms, not causes.** Alert on "users are seeing errors," not "CPU is at
80%." **Every alert should be actionable and should map to a runbook** — alert fatigue is
a reliability problem, not an annoyance.

**Also**: distributed tracing (⚠️ **essential once you have more than a handful of
services**), structured logging with correlation IDs, **synthetic monitoring** (⚠️ **you
want to know before your users tell you**), **status-page and provider-health integration
into your own alerting** (a 2025 lesson — §6 → `cloud-architecture-and-resilience`), and **cost as an observability signal**
(§7).
