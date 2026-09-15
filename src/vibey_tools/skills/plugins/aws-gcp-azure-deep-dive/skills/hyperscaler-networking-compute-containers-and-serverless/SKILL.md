---
name: hyperscaler-networking-compute-containers-and-serverless
description: "Use when placing workloads: networking including VPC models, peering, private connectivity and the egress paths, compute and the instance families and pricing modes, containers and the managed Kubernetes offerings and how much each provider actually manages, and serverless including the function platforms, their cold-start and concurrency behaviour, and where serverless stops being the right answer."
---

# AWS, GCP and Azure: Networking, Compute, Containers and Kubernetes, and Serverless

> **Part 2 of 5** of the *AWS, GCP and Azure Deep Dive* reference (plugin `aws-gcp-azure-deep-dive`), covering §5–§8. Sibling skills: `hyperscaler-framing-responsibility-identity-and-hierarchy` (§0–§4), `hyperscaler-storage-databases-analytics-and-observability` (§9–§13), `hyperscaler-cost-reliability-iac-lock-in-and-migration` (§14–§18), `hyperscaler-reference` (§19–§26). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
>    resource hierarchy, and the network model** — **§3–§5 → `hyperscaler-framing-responsibility-identity-and-hierarchy`.** ⚠️ **Everything above those
>    three is broadly comparable; everything about migration difficulty is determined by
>    them.**
> 2. **⚠️ Data gravity is the real lock-in, not APIs.** **Moving compute is a project.
>    Moving petabytes is an economic decision** — and §21.1 → `hyperscaler-reference` explains why that decision
>    just changed.
> 3. **⚠️ Cloud cost surprises are almost never compute.** **They're data transfer, idle
>    provisioned resources, and per-request charges on managed services** — **§14 → `hyperscaler-cost-reliability-iac-lock-in-and-migration`.**

---

## §5. Networking

```
                AWS              Azure            GCP
Virtual net     VPC              VNet             ⚠️ VPC (GLOBAL, not regional)
Subnets         ⚠️ AZ-scoped      regional         ⚠️ regional
Peering         VPC Peering      VNet Peering     VPC Peering
Hub/transit     Transit Gateway  vWAN / hub-spoke  Network Connectivity Center
Private access  PrivateLink      Private Link      Private Service Connect
On-prem         Direct Connect   ExpressRoute      Cloud Interconnect
LB              ALB/NLB          Azure LB/App GW   ⚠️ Global LB (anycast, single IP)
DNS             Route 53         Azure DNS         Cloud DNS
```
> **⚠️ GOTCHA — GCP's VPC is global and this is a real architectural difference, not a
> marketing point.** ⚠️ **A single GCP VPC spans regions with subnets in each; AWS and
> Azure networks are regional and multi-region requires explicit peering or transit.**
> **GCP's global load balancer similarly gives you one anycast IP worldwide.** ⚠️ **For
> genuinely global applications this meaningfully reduces architectural complexity, and
> it's GCP's strongest structural advantage after BigQuery.**

**⚠️ Private connectivity to managed services is the pattern to internalize**: **PrivateLink
/ Private Link / Private Service Connect keep traffic off the public internet and are
increasingly a compliance requirement.**
**⚠️ NAT gateways are a classic cost trap** — **they charge per hour AND per GB processed,
and a chatty workload egressing through NAT can cost more in NAT processing than in the
transfer itself** (§14 → `hyperscaler-cost-reliability-iac-lock-in-and-migration`).

---

## §6. Compute

```
VMs             EC2              Azure VMs        Compute Engine
Autoscale       ASG              VMSS             MIG
Discounted      ⚠️ Savings Plans / RIs   Reserved / Savings Plans   ⚠️ CUDs +
                                                   AUTOMATIC sustained-use discounts
Interruptible   ⚠️ Spot (bid, 2min warning)  Spot VMs   ⚠️ Spot/preemptible (24h cap)
Own silicon     ⚠️ Graviton (ARM)  Cobalt (ARM)    ⚠️ Axion (ARM); TPUs for ML
```
**⚠️ ARM instances are the most reliable easy win available**: **Graviton and equivalents
typically offer materially better price-performance for workloads that recompile
cleanly** — **which is most interpreted and JVM/Go workloads, and container images that
have arm64 variants.** ⚠️ **Check your dependencies for native extensions first.**
**⚠️ Spot/preemptible is genuinely large savings for fault-tolerant work** — **batch, CI,
stateless web behind a queue** — ⚠️ **and catastrophic for anything that can't be
interrupted mid-operation.** **GCP's flavour has a hard 24-hour cap; AWS's runs until
capacity is reclaimed.**
**⚠️ Commitment discounts**: **GCP's sustained-use discounts apply automatically, which is
a real usability advantage; AWS and Azure require you to actively buy commitments, and
unpurchased commitment is the single most common source of overspend on those two.**

---

## §7. Containers and Kubernetes

```
Managed K8s     EKS              AKS              ⚠️ GKE
Serverless K8s  ⚠️ Fargate        ACI / AKS Auto   GKE Autopilot
Registry        ECR              ACR              Artifact Registry
Simple runner   App Runner       Container Apps   ⚠️ Cloud Run
```
> **⚠️ GKE is the strongest managed Kubernetes of the three, and this is not a close
> call.** ⚠️ **Google originated Kubernetes; GKE has the most mature autoscaling
> (including node auto-provisioning), the best upgrade handling, and Autopilot removes
> node management entirely.** **EKS has improved substantially but historically required
> more assembly — add-ons, IRSA setup, networking plugins.** **AKS sits between them and
> integrates well with Entra.**

**⚠️ The question worth asking before any of this**: **do you actually need Kubernetes?**
⚠️ **For a small number of services, Cloud Run / Container Apps / App Runner deliver most
of the benefit at a fraction of the operational cost.** **Kubernetes pays off at
organizational scale — many teams, many services, needing a common platform** —
⚠️ **and below that threshold it is usually a substantial and unnecessary operational tax.**

---

## §8. Serverless

```
FaaS       Lambda           Azure Functions    Cloud Functions
Container  ⚠️ Fargate/Lambda container  Container Apps  ⚠️ CLOUD RUN
Workflow   Step Functions   Logic Apps / Durable  Workflows
Events     EventBridge      Event Grid         Eventarc / Pub-Sub
API        API Gateway      APIM               API Gateway / Apigee
```
**⚠️ Cloud Run is the standout**: **it runs any container that listens on a port, scales
to zero, and has none of FaaS's packaging constraints.** ⚠️ **It is the easiest path from
"I have a Dockerfile" to "it's in production and costs nothing when idle" on any of the
three.**
**⚠️ Serverless caveats that apply everywhere**: **cold starts** (⚠️ **worse for JVM/.NET,
mitigated by provisioned concurrency — which costs money and removes the scale-to-zero
benefit**), **execution time limits**, **⚠️ per-invocation pricing that becomes more
expensive than a VM above a sustained request rate**, **and the difficulty of local
testing.**
> **⚠️ GOTCHA — serverless is cheap for spiky/low traffic and expensive for steady high
> traffic.** ⚠️ **There is a crossover point where a small always-on instance is
> dramatically cheaper**, and **teams that adopted serverless for cost reasons at low
> volume frequently discover this the hard way after growth.**
