---
name: azure-services-catalog
description: "Azure service selection and production implementation guide covering compute (Container Apps, AKS, Functions, App Service), messaging (Service Bus, Event Hubs, Event Grid), networking (hub-spoke, Virtual WAN, private endpoints), storage, databases (SQL, Cosmos DB, PostgreSQL), AI/Microsoft Foundry, cost optimization, IaC, identity, and 2024–2026 deprecations. Use when advising on Azure architecture decisions, service comparisons, migration planning, or production configuration patterns."
---

# Azure Services Catalog: Production Decision & Implementation Guide

## The Four Highest-Leverage Decision Clusters

### 1. Compute — the Four-Way Decision

Microsoft's own Azure Architecture Center guidance establishes a clear preference order:

1. **Azure Container Apps (ACA)** — the modern default for container workloads. Built on Kubernetes + KEDA + Dapr but hides the control plane; scale-to-zero, event-driven scaling, no node-pool management. Key constraint: single top-level security boundary (the Container Apps environment) with unrestricted intra-environment communication and a shared Log Analytics workspace — if you need granular multi-workload isolation, use AKS or multiple ACA environments.
2. **AKS** — only when you need direct Kubernetes API access, custom service mesh, node-level control, or strict multi-workload isolation.
3. **Azure Functions (Flex Consumption)** — event-driven spiky workloads. Flex Consumption is now the recommended default (GA November 2024): scale from zero to 1,000 instances, no cold start with Always Ready, VNet integration, per-function scaling, configurable instance memory, Linux-only.
4. **App Service** — straightforward HTTP services and web apps. Deployment slots enable zero-downtime blue-green via slot swap.

**Anti-pattern to avoid:** every additional service is operational surface area and on-call burden — resist the Swiss Army knife.

#### Compute Details

**Virtual Machines — series selection:**
- B: burstable, dev/test
- D: general purpose
- E: memory-optimized (databases/caches)
- F: compute-optimized
- L: storage-optimized
- N: GPU
- H: HPC
- Use Availability Zones over Availability Sets for new production workloads; VMSS for scale
- Managed disks: Standard HDD (dev/backup) → Standard SSD (light production) → Premium SSD (production) → Ultra Disk/Premium SSD v2 (highest IOPS, databases)

**AKS networking models (decision is fixed at cluster creation):**
- **kubenet**: UDR-based, ~400-node limit, IP-efficient but limited
- **Azure CNI**: pods get VNet IPs, direct connectivity but IP-hungry
- **Azure CNI Overlay**: pods get IPs from a private CIDR, fixed /24 per node (~250 pods), scales to 5,000 nodes, comparable throughput to host networking — **now the recommended default**
- **Azure CNI Powered by Cilium**: eBPF dataplane, no kube-proxy, built-in network policy + observability, Linux-only
- **Identity**: AAD Pod Identity is deprecated — migrate to Workload Identity
- Standard/Premium tier supports up to 5,000 nodes

**ACA 2024–2025 additions:**
- Dynamic Sessions (GA): Hyper-V-isolated sandboxes for running untrusted/LLM-generated code
- Jobs: event-driven/scheduled/manual batch
- Serverless GPU (preview)
- Native Azure Functions hosting
- Free managed TLS certificates

**App Service tiers:** Free/Shared/Basic/Standard/Premium/Isolated
- App Service Environment (ASE) v3: only justified for network isolation/compliance at scale (max 200 instances vs 30 on Premium)

**Functions — Flex Consumption vs alternatives:**
- Flex Consumption: Linux-only, VNet, per-function scaling, ~zero cold starts with Always Ready
- Classic Consumption: caps at 10-minute execution, 200 instances, no VNet; cold starts 1–3s (.NET/JS/Python), 3–7s (Java)
- Premium (~$150–170/month minimum for EP1): eliminates cold starts via always-ready + prewarmed; worth it if not on Flex

---

### 2. Messaging — the Most-Confused Cluster

**The canonical distinction:** an **event** is a lightweight notification of a state change; a **message** is actionable data with delivery expectations.

| Service | Use For | Key Features |
|---|---|---|
| **Service Bus** | Transactional messages, orders, financial | FIFO via sessions, transactions, dead-lettering, duplicate detection, scheduled messages |
| **Event Hubs** | Telemetry streams, IoT, logs, clickstreams | Millions of events/sec, Kafka-compatible endpoint, Capture to Blob/ADLS |
| **Event Grid** | Reactive pub/sub ("react when X happens") | HTTP + MQTT, Event Grid Namespaces (MQTT broker, pull delivery); does NOT guarantee ordering |
| **Storage Queue** | Basic decoupling, cheap queuing | Simple REST-based; no sessions, transactions, or duplicate detection |

These are **complementary**. The canonical example: e-commerce uses Service Bus for orders, Event Hubs for telemetry, and Event Grid for shipment notifications.

---

### 3. Networking — Hub-Spoke vs Virtual WAN

**Hub-and-spoke:** full routing control, lower cost at small scale, supports specific third-party NVAs.

**Virtual WAN:** Microsoft-managed hub with native transitive routing and "routing intent" (auto-route all spoke traffic through Azure Firewall).

**Crossover point:** ~2–3 active regions or ~30 spokes, or when branch/SD-WAN connectivity at scale is needed.

**vWAN gotchas:**
- NAT Gateway is not supported in a vWAN hub
- Long-lived TCP flows through shared Azure Firewall drop on idle timeouts/instance recycling — workloads need bidirectional TCP keep-alives

**Private Endpoint vs Service Endpoint:**

| | Service Endpoint | Private Endpoint |
|---|---|---|
| Cost | Free | ~$7–8/month + data processing |
| On-premises access | No | Yes (via ExpressRoute/VPN) |
| DNS resolution | Public DNS | Private DNS (must configure) |
| Third-party support | No | Yes (Snowflake, etc.) |
| When required | Never (legacy) | SQL MI, ASE, AKS private API server, on-prem access |

---

### 4. Databases — the Three-Way Decision

**Azure SQL Database:** relational, DTU or vCore model, serverless tier (auto-pause), Hyperscale for large DBs, elastic pools for multi-tenant SaaS.

- **SQL Managed Instance:** near-full SQL Server compatibility; requires private endpoints (not service endpoints)

**Cosmos DB:** globally distributed NoSQL. The #1 performance lever is **partition key selection** — choose high cardinality, even RU/storage distribution, and a key that appears in query filters.
- Five consistency levels: Strong → Bounded Staleness → Session (default) → Consistent Prefix → Eventual
- Session consistency tokens must be passed explicitly between microservices or read-your-writes breaks
- Hierarchical partition keys and partition-level auto-failover (new 2025–2026) ease scaling
- **Warning:** "Scale failures are almost always design failures" — invest in partition-key design before launch; Cosmos DB is expensive and unforgiving when misused
- Reserve for genuine global-distribution or flexible-schema needs

**PostgreSQL:**
- **Flexible Server:** zone-redundant HA, burstable tiers, read replicas — use for migrating/modernizing existing PostgreSQL or Oracle apps
- **Cosmos DB for PostgreSQL (Citus):** for new cloud-native apps needing horizontal sharding
- Single Server is the deprecated path — do not use

---

## Storage Redundancy Decision Matrix

| Tier | Durability | Notes |
|---|---|---|
| LRS | 11 nines | Dev/test only; lowest cost |
| ZRS | 12 nines | **Production minimum**; ~25% premium over LRS |
| GRS/GZRS | ~16 nines | Geo-redundant backup |
| RA-GZRS | 16 nines | Business-critical; adds read access to secondary |

**Critical:** archive tier is not supported on ZRS, GZRS, or RA-GZRS — only LRS/GRS/RA-GRS.

**Access tiers:** Hot → Cool (30-day min) → Cold (90-day min) → Archive (180-day min, hours to rehydrate)

**Action:** set lifecycle management policies to auto-tier aging data from day one — this is the primary cost lever.

---

## AI & Microsoft Foundry

### Platform History and Current State
- Azure AI Studio → Azure AI Foundry (Ignite 2024) → **Microsoft Foundry** (Ignite 2025, now GA)
- 1,900+ models from OpenAI, Meta, and more (11,000+ including community models per Microsoft marketing)

### Two Project Models (Not at Full Feature Parity)
- **Hub-based projects:** built on Azure ML (`Microsoft.MachineLearningServices`); legacy path
- **Foundry projects:** built on Cognitive Services (`Microsoft.CognitiveServices/account`); **all new generative-AI investment goes here** — new model-centric features available only here
- An existing Azure OpenAI resource can be upgraded to a Foundry resource preserving endpoint and keys

### Agent Capabilities
- **Foundry Agent Service** (GA May 2025): connected agents for multi-agent orchestration without external orchestrators
- **Workflows** (visual + YAML, preview from Ignite 2025): coordinate multiple agents
- Agent types: managed no-code **Prompt agents** (GA) and **Hosted agents** (preview), both behind the Responses API
- Tools: Code Interpreter, Logic Apps (1,400+ connectors), Functions, OpenAPI, MCP, Deep Research, Agent2Agent (A2A)

### Microsoft Agent Framework
- Open-source successor to **both Semantic Kernel and AutoGen** (now in maintenance mode)
- Public preview October 1, 2025; **1.0 GA April 2026**
- Five stable orchestration patterns: sequential, concurrent, handoff, group chat, Magentic
- Native MCP and A2A support

### Deployment Options
| Option | When to Use |
|---|---|
| **Standard deployment** (preferred) | Foundry resource, no hub required, regional/data-zone/global processing |
| **Serverless API endpoints** (MaaS) | Pay-per-token, OpenAI/partner models, hub required |
| **Managed compute** | Hugging Face/NVIDIA NIM/custom models, billed per compute-hour |

### PTU vs Pay-as-You-Go
- **Pay-as-you-go (standard/token-based):** variable, experimental, or low-volume workloads
- **PTU (Provisioned Throughput Units):** production with predictable traffic needing guaranteed latency; billed hourly per PTU regardless of usage
- **Critical:** quota does not guarantee capacity — **deploy the model first, then buy the matching reservation**
- Spillover routes PTU overflow (429s) to a standard deployment

### When to Choose What
- **Microsoft Foundry:** end-to-end generative-AI/agent apps and the broad catalog — the default
- **Raw Azure OpenAI:** only when you need OpenAI models alone (upgrade path to Foundry recommended)
- **Azure Machine Learning:** custom model training, full MLOps, and the model registry

### Vector Search for RAG
- **Azure AI Search:** default for Azure-native teams — hybrid (BM25 + vector) search, built-in semantic ranker, security trimming, indexer-managed ingestion
- **pgvector:** cheaper for small corpora already on PostgreSQL
- **Cosmos DB vector search:** globally distributed apps already on Cosmos
- At ≤100k vectors, all options are fast enough — decision driver is features, cost model, and operational ownership

### APIM as AI Gateway
A major 2024–2026 pattern:
- `azure-openai-token-limit` policy for TPM throttling per subscription key
- Backend pool load balancing (round-robin/weighted/priority) and circuit breakers honoring `Retry-After`
- Route to PTU first, spill over to pay-as-you-go across regions on 429s
- `azure-openai-emit-token-metric` → Application Insights for per-team showback
- APIM is integrated into Microsoft Foundry; not a separate offering
- Azure-Samples/AI-Gateway repo provides 30+ deployable Bicep/policy labs

---

## Cost Optimization

**Layered commitment strategy:**

| Tool | Discount | Best For |
|---|---|---|
| **Reservations** | Up to 72% vs pay-as-you-go | Stable steady-state compute; locked to VM family + region |
| **Savings Plans** | Up to 65% vs pay-as-you-go | Evolving compute; $/hour commitment flexible across families/regions/services |
| **Spot VMs** | Up to 90% vs pay-as-you-go | Fault-tolerant/batch; no SLA, ~30-second eviction notice |

- Reservations apply before Savings Plans when both match
- Stack **Azure Hybrid Benefit** for Windows/SQL licensing on top of Reservations
- Start with 30–60 days of usage data, then use Azure Cost Management recommendations

---

## IaC: Bicep vs Terraform

**Consensus:** both are production-ready; standardize on one for new projects.

| | Bicep | Terraform |
|---|---|---|
| Best for | Azure-only teams | Multi-cloud or heavy third-party integration |
| State file | No | Yes (management overhead) |
| Azure day-0 support | Yes | Delayed (provider maturity) |
| Provider ecosystem | Azure-only | Mature, broad |
| CI/CD | Azure CLI native | State management required |

Migration between them is rarely worth it — standardize on one and let old projects attrit.

---

## Identity & Zero Trust

- **Managed Identities:** always preferred over service principals for Azure-to-Azure auth — no secret management, no credential rotation
- **Zero Trust stack:** Entra ID + Conditional Access + PIM (just-in-time role activation) + Defender for Cloud
- Use **Azure RBAC built-in roles** at the narrowest scope — avoid Owner/Contributor at subscription/management-group scope
- **Key Vault references:** let App Service/Functions/AKS consume secrets without storing them in config
- Distinguish **Azure RBAC** (resource-plane) from **Entra ID roles** (directory/tenant-plane)

---

## Service Retirements — Act Now

| Service | Status | Action Required |
|---|---|---|
| **Log Analytics agent (MMA)** | Retired November 2024 | Migrate to Azure Monitor Agent (AMA) with Data Collection Rules |
| **Azure AD B2C** | No new sales May 1, 2025; P2 discontinues March 15, 2026; support "until at least May 2030" | Migrate to **Microsoft Entra External ID** (GA Sept 2024); plan 3–9 months for migration |
| **AzureAD/MSOnline PowerShell** | Deprecated March 2024, retiring through 2025 | Migrate to Microsoft Graph PowerShell; Azure AD Graph API blocked for new apps |
| **Prompt Flow** | Retires April 20, 2027 | Migrate to Microsoft Agent Framework |

**Entra External ID migration note:** B2C custom policies don't port directly; Entra External ID still has gaps (OTP-only MFA, tenant-level branding) — validate feature parity before committing.

---

## Production Staging Roadmap

### Stage 1 — Foundation (landing zone first)
- Cloud Adoption Framework landing zone with management-group hierarchy
- Hub-spoke networking with Azure Firewall; ZRS storage defaults
- Managed identities everywhere
- Azure Policy guardrails (Audit/Deny/DeployIfNotExists)
- Bicep or Terraform IaC
- **Trigger to migrate to Virtual WAN:** exceed 2–3 active regions or ~30 spokes, or need branch/SD-WAN at scale

### Stage 2 — Compute by workload
- Default container workloads → Container Apps
- Escalate to AKS only for: Kubernetes API access, custom service mesh, multi-workload isolation, node-level control
- Functions Flex Consumption for event-driven; App Service for web apps

### Stage 3 — Data and messaging
- Map each integration to the right messaging service (don't standardize on one)
- Relational default: Azure SQL or PostgreSQL Flexible Server
- Reserve Cosmos DB for genuine global-distribution or flexible-schema needs

### Stage 4 — AI
- Build on Microsoft Foundry (Foundry projects) for new generative-AI/agent work
- Start on pay-as-you-go → move to PTU once traffic is predictable (deploy first, reserve second)
- Front all AI traffic with APIM as an AI gateway
- RAG: default to Azure AI Search

### Stage 5 — Cost
- After 30–60 days of data: Reservations on steady-state + Savings Plans on variable + Spot on fault-tolerant
- Stack Azure Hybrid Benefit
- Target high Effective Savings Rate (coverage × utilization), not maximum headline discount

### Stage 6 — Govern and observe
- Mandatory tags via Policy
- Defender for Cloud for posture
- Azure Monitor with AMA + Data Collection Rules (MMA is gone)
- Track retirements against the Azure Retirement Workbook
