---
name: hyperscaler-cost-reliability-iac-lock-in-and-migration
description: "Use when the commercial or operational reality matters more than the feature list: cost mechanics including commitments, egress and the line items that surprise people, reliability, regions and what an SLA actually promises, infrastructure as code across the native and third-party tools, lock-in and multi-cloud assessed honestly rather than ideologically, and migration approaches and their realistic effort."
---

# AWS, GCP and Azure: Cost Mechanics, Reliability and SLAs, Infrastructure as Code, Lock-In, and Migration

> **Part 4 of 5** of the *AWS, GCP and Azure Deep Dive* reference (plugin `aws-gcp-azure-deep-dive`), covering §14–§18. Sibling skills: `hyperscaler-framing-responsibility-identity-and-hierarchy` (§0–§4), `hyperscaler-networking-compute-containers-and-serverless` (§5–§8), `hyperscaler-storage-databases-analytics-and-observability` (§9–§13), `hyperscaler-reference` (§19–§26). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
>
> **Currency:** Architecture and IAM models are stable. Two areas moved. See §21 → `hyperscaler-reference` for egress pricing under the EU Data Act switching regime, and the AI-driven shift in market position.

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
>    Moving petabytes is an economic decision** — and §21.1 → `hyperscaler-reference` explains why that decision
>    just changed.
> 3. **⚠️ Cloud cost surprises are almost never compute.** **They're data transfer, idle
>    provisioned resources, and per-request charges on managed services** — **§14.**

---

## §14. ⚠️ Cost Mechanics

**⚠️ Compute is almost never the surprise. These are:**
```
1. ⚠️ DATA TRANSFER — egress to internet, cross-region, cross-AZ, NAT processing.
   ⚠️ Ingress is free everywhere; egress is billed everywhere (§21.1)
2. ⚠️ IDLE PROVISIONED RESOURCES — unattached disks, idle load balancers,
   forgotten dev environments, over-provisioned databases, ⚠️ and unattached
   public IPv4 addresses, which AWS now charges hourly for
3. ⚠️ PER-REQUEST CHARGES — API calls, object operations, function invocations,
   ⚠️ and BigQuery bytes scanned. Individually trivial, collectively enormous
4. ⚠️ LOG AND METRIC INGESTION — often the second-largest line after compute
5. ⚠️ UNUSED COMMITMENTS — reservations bought for capacity you no longer run
6. ⚠️ SUPPORT PLANS — a percentage of spend, and it scales with your bill
```
**⚠️ The discipline (FinOps) that actually works:**
- ⚠️ **Tag/label everything and enforce it by policy** — **unattributable spend never gets
  cleaned up, because nobody owns it.**
- **Budgets and anomaly alerts** — ⚠️ **an alert at 50% of monthly budget on day 8 is what
  catches a runaway job before it costs five figures.**
- ⚠️ **Right-size before you commit.** **Buying a three-year reservation for an
  over-provisioned instance locks in the waste.**
- **Lifecycle policies on storage; TTLs on logs.**
- ⚠️ **Kill non-prod outside working hours** — **often 60–70% of non-prod cost, and it's
  the easiest large saving available.**
- ⚠️ **Showback/chargeback changes behaviour more than any technical control**, because it
  puts the cost in front of the team creating it.
> **⚠️ GOTCHA — cross-AZ traffic is billed on AWS and it catches people building
> "highly available" architectures.** ⚠️ **A chatty microservice mesh spread across three
> AZs pays per GB in both directions for internal traffic**, and **the same architecture
> that improves availability can multiply the network bill.** **Zone-aware routing helps;
> knowing it exists helps more.**

---

## §15. Reliability, Regions and SLAs

```
Region        geographic area, ⚠️ independent failure domain
AZ / Zone     ⚠️ isolated DC(s) within a region — separate power, cooling, network
Multi-AZ      ⚠️ THE baseline for production. Cheap insurance, small complexity
Multi-region  ⚠️ expensive, complex, and needed far less often than proposed
```
**⚠️ Design principle**: **assume every individual component fails.** **Health checks,
retries with exponential backoff and jitter, circuit breakers, timeouts on every call,
graceful degradation, and idempotent operations.**
**⚠️ SLAs are refunds, not guarantees.** ⚠️ **A 99.99% SLA does not mean you get 99.99% —
it means you get a service credit worth a small fraction of your bill if you don't.**
**Your composite availability is the product of your dependencies', and it is always lower
than any single component's.**
**⚠️ The real failure modes are correlated ones**: **a regional control-plane outage, a bad
config push, an expired certificate, a DNS mistake, or a dependency on a single global
service.** ⚠️ **Multi-AZ protects against a datacentre; it does not protect against a
control-plane failure or your own bad deploy** — **and historically, control-plane and
config-push failures have caused more large outages than facility failures.**
**⚠️ Test failover, or you don't have failover** (see an IT infrastructure reference §13).

---

## §16. Infrastructure as Code

```
Native      CloudFormation    ARM / ⚠️ Bicep       Deployment Manager (legacy)
Multi       ⚠️ Terraform / OpenTofu — the de facto standard across all three
Typed       ⚠️ CDK / CDKTF / Pulumi — real languages, real abstractions
Config      Ansible, Chef, Puppet
```
**⚠️ Terraform is the practical default** — **provider coverage across all three, a mature
module ecosystem, and skills that transfer.** ⚠️ **The OpenTofu fork exists following
Terraform's licence change and is a genuine consideration for organizations sensitive to
that.** **Bicep is a real improvement over raw ARM templates and worth using if you're
Azure-only.**
**⚠️ The practices that matter more than the tool**: **remote state with locking** (⚠️ **two
engineers applying simultaneously against local state is a genuine way to destroy
infrastructure**), **state file treated as sensitive — it contains secrets**, **plan
review in CI before apply**, **modules for repeated patterns**, **and drift detection.**
> **⚠️ GOTCHA — manual console changes are the enemy of IaC and everyone makes them.**
> ⚠️ **Once a resource is modified out of band, the next apply may revert it, fail, or
> destroy and recreate it.** **The practical answer is not "never touch the console" —
> it's read access by default, break-glass for writes, and drift detection that tells you
> when it's happened.**

---

## §17. ⚠️ Lock-In and Multi-Cloud, Honestly

**⚠️ Lock-in is real and it is not primarily about APIs.**
```
LOW lock-in     VMs, containers, object storage, managed Postgres/MySQL,
                Kubernetes ⚠️ (portable in principle; the surrounding
                integrations are what actually bind you)
MEDIUM          managed queues, load balancers, IAM integration patterns
⚠️ HIGH         proprietary databases (DynamoDB, Spanner, Cosmos), serverless
                event architectures, ⚠️ the analytics stack, and IAM itself
⚠️ HIGHEST      DATA GRAVITY and TEAM EXPERTISE — the two nobody puts on the list
```
**⚠️ Multi-cloud is frequently proposed and rarely done well.** **The honest breakdown:**
- **⚠️ Multi-cloud for *resilience* mostly doesn't work as intended.** **You end up with
  the lowest common denominator of both platforms, double the operational surface, a team
  expert in neither, and — critically — an active/passive setup whose failover has never
  been tested and therefore won't work.**
- **⚠️ Multi-cloud that DOES work is usually best-of-breed per workload**: **analytics on
  BigQuery, the enterprise estate on Azure, a product on AWS.** **Separate workloads,
  separate teams, deliberate seams.**
- **⚠️ Multi-cloud as negotiating leverage is real** — **credible ability to move improves
  your terms even if you never move** (see a business reference §12 on BATNA).
- **⚠️ Much multi-cloud is not chosen. It's acquired** — through mergers, shadow IT, and
  SaaS vendors running elsewhere. **Reported multi-cloud adoption figures largely
  describe this, not deliberate architecture.**

**⚠️ The pragmatic middle**: **keep the portable things portable — containers, standard
SQL, IaC, and avoid gratuitous proprietary dependencies — while using managed services
where they genuinely earn their lock-in.** ⚠️ **Refusing all proprietary services to
preserve optionality means rebuilding what you're already paying for, which is usually the
more expensive mistake.**

---

## §18. Migration

**⚠️ The 7 Rs**: **rehost (lift-and-shift), replatform, repurchase, refactor, retire,
retain, relocate.**
**⚠️ Retire first.** **A meaningful share of any legacy estate is running things nobody
uses, and migrating them costs money forever.**
**⚠️ Rehost is underrated by architects and correctly rated by people with deadlines** —
**it's fast, low-risk, and gets you a position from which to modernize.** ⚠️ **The failure
mode is stopping there and paying cloud prices for datacentre architecture, which is the
single most common reason cloud migrations don't deliver the promised savings.**
**⚠️ Data migration dominates the timeline**: **bulk transfer appliances (Snowball, Data
Box, Transfer Appliance) for large volumes, then ongoing sync, then cutover.** ⚠️ **The
network is almost always the constraint, and moving petabytes over the internet is not a
plan.**
**⚠️ Repatriation is a real and growing pattern** — **predictable, steady, high-volume
workloads can be genuinely cheaper on owned hardware, and §21.1 → `hyperscaler-reference` removes one of the
barriers to acting on that.** **The cloud's economics favour variable and spiky
workloads; they do not automatically favour everything.**
