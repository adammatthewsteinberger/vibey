---
name: architecture-patterns
description: "Comprehensive reference for software architecture patterns and their Azure implementations (2026 edition). Covers compute architectures (monolith, microservices, serverless, EDA), communication patterns (REST, gRPC, GraphQL, WebSockets, messaging), data architecture (relational, document, vector, lakehouse), secrets management, API gateway and edge, resilience patterns (retry, circuit breaker, saga, outbox), multi-tenancy, observability, security (Zero Trust, IAM, encryption), AI/ML patterns (RAG, LLM gateway, AI agents), and integration patterns. Use when recommending specific Azure services, choosing between architectural patterns, implementing resilience strategies, or building AI-native applications on Azure."
---

# Architecture Patterns and Azure Implementations (2026 Edition)

## Core Principle
Pattern choice should follow the problem, not the technology. The Azure Well-Architected Framework's own guidance: "Choose a pattern based on the problem you need to solve, not the technology you want to use."

**The highest-leverage decisions are the irreversible ones:** Cosmos DB partition key, event schema/versioning strategy, multi-tenancy isolation model, and secrets architecture. Get these wrong and remediation is a re-platform, not a config change.

---

# PART 1: COMPUTE ARCHITECTURES

## Compute Decision Ladder (2026 Default)
```
App Service (modular monolith)
    → Azure Container Apps (serverless containers — simpler default for most containerized workloads)
        → AKS (full Kubernetes only when you need the API, operators, mesh, or fine-grained node control)
```
Azure Functions Flex Consumption fills the event-driven serverless tier.

## Monolithic Architecture

**When to use:** Startup stage, small teams, domain not yet well understood.

**Azure mapping:**
- **App Service (Web Apps)**: default modular-monolith host
- **Azure Spring Apps**: Spring Boot
- **Blue-green/zero-downtime**: App Service **deployment slots** — deploy to staging, warm it, swap (near-instant, reversible)
- **Strangler migration**: Front Door or App Gateway as façade

**Production gotchas:**
- Slot swaps carry app settings unless marked "slot setting" — classic cause of staging config leaking to production
- Cold slots cause first-request latency post-swap; use `applicationInitialization` warm-up paths
- **Anti-pattern:** decomposing before you have module boundaries — creates a distributed big ball of mud

**Decision trigger:** Stay monolithic until you have measurable deployment contention between teams or a clearly independent scaling/availability requirement for a subsystem.

## Microservices Architecture

**Azure mapping:**
- **Azure Container Apps (ACA)**: serverless Kubernetes abstraction with KEDA and Dapr built in; the right default for most microservices
- **AKS**: managed Kubernetes when you need the full API; **Istio-based service mesh add-on** is Microsoft-supported (managed istiod, AZ-aware, integrates with Managed Prometheus/Grafana)
- **Service Bus** for async; **APIM** as the front door

**AKS Istio add-on constraints:**
- Does NOT work on clusters using **Azure CNI Powered by Cilium**
- Does NOT work alongside the deprecated OSM add-on or self-managed Istio
- Does NOT yet support sidecar-less **Ambient** mode
- Blocks `EnvoyFilter`, `WasmPlugin`, `IstioOperator`, and several other CRDs

**Production gotchas:**
- A **shared database violates the pattern** and silently recouples teams
- **Anti-pattern:** distributed monolith — services deployed in lockstep

**Decision trigger:** Independent deployability or scaling of a subsystem is a hard requirement, and you have the platform/observability maturity to pay the distributed-systems tax.

## Serverless Architecture

**Azure Functions plans:**
| Plan | Notes |
|---|---|
| **Flex Consumption** (Recommended, GA Dec 2024) | VNet integration at no extra cost, instance memory selection (512/2048/4096 MB), per-instance concurrency scaling, "Always Ready" to eliminate cold starts, configurable max instances (min 40, max 1,000, default 100), Hyper-V isolation |
| Consumption | Legacy |
| Premium | Higher cost, pre-warmed |
| Dedicated | Always-on App Service Plan |

**Critical Flex Consumption constraints:**
- Subnet names cannot contain underscores
- Use at least a /27 subnet (smaller can fail gateway creation silently)
- Reserve ~40 IPs per app
- **Cannot share a subnet between an ACA environment and a Flex Consumption app**
- All Flex apps share a default **250-core regional subscription quota** — a single app scaled to 1,000 × 512 MB instances can consume the entire quota

**Retirements to schedule:**
- Legacy Linux Consumption plan retires **September 30, 2028** → migrate to Flex Consumption
- In-process .NET model retires **November 2026**

**Durable Functions patterns:**
- Orchestrator/activity/entity; chaining; fan-out/fan-in; eternal orchestrations (`ContinueAsNew`)
- **Human-approval**: `WaitForExternalEvent` + a durable timer for timeout/escalation
- **Critical rule: orchestrators must be deterministic** — never call `DateTime.Now`/`Date.now()`, random, or direct I/O inside an orchestrator; use `context.CurrentUtcDateTime` and delegate I/O to activities

**Decision trigger:** Spiky/bursty or event-driven workloads where idle cost matters; choose Flex Consumption unless you need a feature only on another plan.

## Event-Driven Architecture (EDA)

### Azure Messaging: Three First-Class Services

| Service | Job | Key Features |
|---|---|---|
| **Service Bus** | Enterprise queues/topics | Ordering (sessions), transactions, DLQ, scheduled messages, duplicate detection |
| **Event Grid** | Reactive pub/sub | MQTT v3.1.1/v5.0 broker (Namespaces), HTTP pull delivery, 24hr retry with exponential backoff |
| **Event Hubs** | High-throughput streaming | Kafka-compatible endpoint, consumer groups, Capture to ADLS/Blob |

Most real EDA architectures use all three: Event Hubs for ingestion, Service Bus for reliable work queues, Event Grid for reactive system events.

**Event Grid Namespaces note:** Standard tier and classic topics (Basic) are different resource models — Namespaces currently support Event Hubs as the only push destination for namespace topics.

**MQTT scale:** A single Event Grid namespace (40 throughput units) demonstrated 200,000 publishers + 200,000 subscribers at ~40,000 messages/second.

**Anti-pattern:** Using events for request/response where the caller needs an immediate consistent answer.

### Outbox Pattern
Solves the dual-write problem: write the business change and the outbox event in one local transaction, then relay to the broker. Required whenever you publish events from a write DB.

---

# PART 2: COMMUNICATION PATTERNS

## REST
- Stateless, uniform interface, resource-based URLs
- **Richardson Maturity Model**: L0 (RPC-over-HTTP) → L3 (hypermedia)
- Verb idempotency: GET/PUT/DELETE idempotent; POST not
- Errors: **RFC 7807 Problem Details**
- Pagination: offset (simple, breaks under inserts) vs cursor/keyset (stable)
- **Azure:** APIM for full lifecycle; Functions HTTP triggers for lightweight endpoints; APIM imports OpenAPI directly

## gRPC
- Protocol Buffers IDL, binary serialization, four call types (unary, server/client/bidirectional streaming)
- Wins for internal, performance-critical, strongly-typed service-to-service
- **Azure ACA**: supports gRPC (HTTP/2). On **AKS**: need an L7 gRPC-aware ingress (NGINX or Traefik) for per-method routing and TLS — a plain L4 LB won't route
- **APIM** has added gRPC passthrough support
- **Critical:** Validate end-to-end HTTP/2 from client through ingress to pod; a single HTTP/1.1 hop breaks streaming

## GraphQL
- Schema-first; queries, mutations, subscriptions
- **N+1 problem** solved with **DataLoader** batching
- **Federation** (Apollo Federation, schema stitching) composes a supergraph from subgraphs
- **Azure:** APIM supports GraphQL passthrough and **synthetic GraphQL** (resolvers over REST/SOAP backends), plus depth/complexity limiting policies

## WebSockets & Real-Time
- **Azure Web PubSub**: WebSocket-native pub/sub, high fan-out
- **Azure SignalR Service**: SignalR protocol with transport negotiation (WebSockets → SSE → long-poll)
- Choose Web PubSub for raw WebSocket scale; SignalR when using the .NET SignalR model

## Message Queues
- **Service Bus Queues**: sessions for FIFO/ordering, duplicate detection, DLQ, scheduled messages, transactions
  - **Premium**: VNet isolation, messages **up to 100 MB (AMQP only; must raise default 1 MB)**
  - **Standard/Basic**: 256 KB message limit
- **Storage Queues**: cheap, simple, high-volume alternative
- Poison messages auto-move to DLQ after max delivery count

## Event Streaming (Kafka Pattern)
- Immutable append-only log; consumer groups track own offset; partitions = parallelism; compaction maintains latest-state
- **Azure Event Hubs**: Kafka-compatible endpoint (no code change), consumer groups, **Capture** to ADLS/Blob, Standard/Premium/Dedicated tiers
- **Confluent Cloud on Azure vs Event Hubs**: Confluent for full Kafka ecosystem (Connect, ksqlDB, Schema Registry, exactly-once Streams); Event Hubs for managed, lower-ops Azure-native ingestion

---

# PART 3: DATA ARCHITECTURE PATTERNS

## Relational (RDBMS)

**Azure services:**
- **Azure SQL Database**: DTU / vCore / serverless / **Hyperscale** (>100 TB)
- **Azure SQL Managed Instance**: near-full SQL Server compat for lift-and-shift
- **PostgreSQL Flexible Server**: zone-redundant HA, read replicas, **built-in PgBouncer** (must be explicitly enabled)
- **MySQL Flexible Server**

**Production gotchas:**
- Azure SQL serverless auto-pause causes cold-start latency on first connection after idle
- **Connection pooling is mandatory at scale** — exhaustion is a top outage cause
- PostgreSQL Flexible Server's built-in PgBouncer must be explicitly enabled

## Document (Cosmos DB for NoSQL)

**The partition key is the single most critical and irreversible decision.** A poor partition key (low cardinality or skewed access) creates hot partitions that throttle (429s) regardless of provisioned RUs — and you **cannot change a container's partition key in place**; you must migrate.

- Five **consistency levels**: strong, bounded staleness, session (default), consistent prefix, eventual
- **Change feed**: built-in CDC
- Multi-region writes

## Key-Value (Redis)
- **Azure Cache for Redis / Azure Managed Redis**: Basic/Standard/Premium/Enterprise/Enterprise Flash
- Clustering, geo-replication, modules (**RediSearch, RedisJSON, RedisTimeSeries**) on Enterprise tier
- RediSearch powers APIM semantic caching

**Caching patterns:**
| Pattern | How It Works | Use When |
|---|---|---|
| Cache-aside (lazy loading) | App checks cache, loads on miss, populates | Most common default |
| Write-through | Write cache + DB together | Need consistency, can accept write latency |
| Write-behind | Write cache, async flush | Need write speed, can tolerate durability risk |
| Read-through | Cache fetches transparently | Simplify app code |
| Refresh-ahead | Proactively refresh before expiry | Predictable access patterns |

**Thundering herd / cache stampede:** Mitigate with probabilistic early expiration or a mutex on cache rebuild.

## Vector Search

**Full Azure menu:**
| Service | Algorithm | Notes |
|---|---|---|
| **Azure AI Search** | Hybrid BM25+vector+semantic reranker | Full retrieval stack; `vector_semantic_hybrid` is Microsoft's recommended default |
| **Cosmos DB for NoSQL** | DiskANN (GA) | Sub-20ms at scale; requires ≥1,000 vectors or falls back to full scan |
| **PostgreSQL Flexible Server + pgvector** | HNSW | Familiar SQL interface |
| **Azure SQL Database** | Native VECTOR type + `VECTOR_DISTANCE` (GA June 2025); DiskANN indexes (preview) | Co-locate with operational data |
| **Azure Cache for Redis (Enterprise)** | RediSearch vector | Ultra-low latency |

**Decision:** Full retrieval stack → AI Search. Data already in Cosmos/SQL, want no extra system → built-in vector search. Pure billion-scale vector workload → dedicated vector DB may be cheaper.

## Data Lakes & Lakehouses
- **ADLS Gen2**: hierarchical namespace on Blob
- **Microsoft Fabric OneLake**: universal tenant-wide logical lake (built on ADLS Gen2); all tabular data in **Delta Parquet**; zero-copy **Shortcuts** to S3/GCS/ADLS; **Mirroring** for zero-ETL from Cosmos/SQL/PostgreSQL/Snowflake (GA Nov 15, 2023)
- **Medallion architecture**: Bronze (raw) → Silver (cleaned) → Gold (business-ready)
- **Data Mesh on Azure**: Fabric workspaces (domains) governed centrally via **Microsoft Purview** (catalog, lineage, sensitivity labels)

---

# PART 4: SECRETS MANAGEMENT

**Never store secrets in config files, baked images, or source control.**

**Azure Key Vault (Standard = software-protected; Premium = HSM-backed)**
- **Key Vault references** in App Service/Functions: `@Microsoft.KeyVault(...)`
- **AKS**: Secrets Store CSI Driver + AKV provider mounts secrets as files or syncs to K8s Secrets; combine with **Workload Identity** for zero-secret-in-config
- Key Vault references resolve at app start and on a refresh interval — rotating a secret doesn't instantly propagate unless you handle refresh
- Cache high-RPS secret reads to avoid throttling

**Azure Managed HSM**: dedicated, FIPS 140-2 Level 3, single-tenant.

**HashiCorp Vault on Azure**: beats Key Vault for true dynamic secrets (short-lived, on-demand), multi-cloud, or Vault Agent sidecar injection.

**Injection patterns:** Startup pull, sidecar injection (Vault Agent / Dapr), or **CSI driver mount** (AKS preferred).

---

# PART 5: API GATEWAY & EDGE

## Azure API Management (APIM)

**Tiers:** Consumption / Basic / Standard / Premium / Developer (plus v2 tiers)

**APIM AI Gateway capabilities:**
- `azure-openai-token-limit`: TPM enforcement
- `azure-openai-emit-token-metric`: usage to App Insights split by subscription/IP/custom dimension
- **Semantic caching**: `azure-openai-semantic-cache-store/lookup` using Azure Managed Redis + RediSearch + an embeddings model
- **Backend pools**: round-robin/weighted/priority load balancing and circuit breaker to spill **PTU → PAYG**
- Unified model API across providers

**Semantic caching gotcha:** Silently no-ops if the external Redis cache lacks RediSearch or isn't wired as an APIM external cache. Set similarity threshold carefully: too loose returns wrong cached answers.

## Load Balancing Decision Matrix

| Service | Layer | Scope | Use When |
|---|---|---|---|
| **Azure Load Balancer** | L4 | Regional | VMs/VMSS |
| **Application Gateway v2** | L7 | Regional | WAF, TLS termination, URL/path routing, cookie affinity; AKS ingress via AGIC |
| **Azure Front Door** | L7 + CDN | Global | HTTP(S) with CDN, WAF, geo-routing, caching — **now the unified Azure CDN/edge platform** |
| **Traffic Manager** | DNS | Global | DNS-based routing (performance/priority/weighted/geographic) |

**CDN retirements:**
- **Azure CDN Standard from Microsoft (classic) retires September 30, 2027**
- **Azure Front Door (classic) retires March 31, 2027**
- Classic profiles already blocked new creation and managed certs as of August 15, 2025
- Migrate using the zero-downtime migration tool

---

# PART 6: RESILIENCE PATTERNS

## Catalog (Azure Architecture Center)

| Pattern | Purpose | Azure Implementation |
|---|---|---|
| **Retry with exponential backoff + jitter** | Handle transient failures | Polly (.NET), Tenacity (Python) |
| **Circuit Breaker** (Closed/Open/Half-Open) | Stop calling a failing dependency | Polly; APIM backend circuit breaker |
| **Bulkhead** | Isolate resource pools | Thread pool isolation; ACA scale units |
| **Timeout** | Fail fast | Set at every network hop |
| **Fallback** | Graceful degradation | Return cached data, default response |
| **Health Endpoint Monitoring** | `/health/live`, `/health/ready` | App Service health check; AKS probes |
| **Idempotency** | Safe retry of mutations | Idempotency keys on write endpoints |
| **Saga** | Distributed transactions | Choreography vs orchestration; compensating transactions; Durable Functions |
| **Outbox** | Transactional event publishing | Write business change + outbox in one local transaction, relay to broker |
| **Queue-Based Load Leveling** | Smooth bursty load | Service Bus + Competing Consumers |

**WAF-recommended pairings:**
- Retry + Circuit Breaker
- Queue-Based Load Leveling + Competing Consumers
- Saga built on Compensating Transaction

## High Availability

**RTO/RPO drives architecture:**
- 99.9% → single-region zone-redundant
- 99.99% → multi-region

**Azure services:**
- **Availability Zones**: enable for all production resources
- **Cosmos DB multi-region**: multi-region writes with automatic conflict resolution
- **Azure SQL**: active geo-replication / failover groups
- **Redis Premium**: geo-replication
- **ACR**: geo-replication
- **Front Door / Traffic Manager**: multi-region routing

**Service Bus geo features (mutually exclusive on same namespace):**
- **Geo-Disaster Recovery**: metadata only
- **Geo-Replication** (recommended): metadata + message data; doesn't yet support large messages; preview on partitioned namespaces

**Critical sizing gotcha:** Redundancy is architecture; resiliency is behavior. Two zones behind a LB but Zone B sized for 50% load — Zone A fails, B is overwhelmed, the whole service degrades. **Size failover capacity for full load.**

**Chaos engineering:** Azure Chaos Studio.

---

# PART 7: CONFIGURATION & FEATURE FLAGS

- **Azure App Configuration**: feature flags + key-value store, **Sentinel key** for atomic multi-key refresh, geo-replication, Key Vault references
- App Service Application Settings/Connection Strings for simple cases

**Feature flag types:**
| Type | Purpose |
|---|---|
| Release toggles | Decouple deploy from release — the CI/CD enabler |
| Experiment toggles | A/B testing; progressive rollout (10%→50%→100%) |
| Ops toggles | Kill switches |
| Permission toggles | By user segment or tier |

Manage flag lifecycle/hygiene as technical debt. Third-party options: **LaunchDarkly** (Marketplace ISV), **Unleash** on AKS.

---

# PART 8: MULTI-TENANCY

**Isolation models:**

| Model | Isolation | Cost | Complexity |
|---|---|---|---|
| **Silo** | Isolated resources per tenant | Highest | Lowest |
| **Pool** | Shared resources, tenant-ID-keyed | Lowest | Highest |
| **Bridge (Hybrid)** | Shared for small, isolated for large/premium | Medium | Medium |

**Azure implementations:**
- **Azure SQL Elastic Pools**: pool-based with RLS or separate DBs
- **Cosmos DB**: partition key = tenant ID for pool; separate accounts/containers for silo
- **AKS**: namespace-per-tenant (soft isolation) vs node-pool-per-tenant (hard isolation)
- **APIM**: product/subscription per tenant with tenant-specific rate limits
- **Entra External ID / Azure AD B2C**: customer identity

**Critical gotcha:** Pool model with tenant-ID partition key in Cosmos DB risks a hot partition when one large tenant dominates — same irreversible partition-key trap, now with cross-tenant blast radius. Consider a composite key or bridge model for "whale" tenants.

---

# PART 9: OBSERVABILITY

## Three Pillars + One
- **Metrics**: numeric time-series, cheap, alertable
- **Logs**: discrete events, structured JSON preferred, expensive at scale
- **Traces**: distributed request tracing, spans, **W3C Trace Context** propagation
- **Profiles** (fourth pillar): CPU/memory flame graphs

**OpenTelemetry (OTel)** is the unifying standard (collector, SDK, semantic conventions).

## Azure Mapping
- **Azure Monitor**: metrics
- **Log Analytics**: logs + KQL
- **Application Insights**: APM — distributed tracing, dependency map, live metrics, sampling
- **Azure Managed Grafana**: dashboards
- **Azure Monitor OpenTelemetry Distro**: recommended path for new apps — one-line export to App Insights, simultaneously exports to any OTLP endpoint

**Production gotcha:** Incomplete distributed traces usually come from inconsistent sampling across nodes — if one service applies head-based sampling without propagating the decision via W3C headers, downstream spans get dropped. In Azure Functions, don't run the Azure Monitor distro in the isolated worker if the host already instruments — duplicate telemetry.

---

# PART 10: SECURITY ARCHITECTURE

## Zero Trust
"Never trust, always verify; assume breach; least privilege."

**Azure reference stack:** Entra ID + Conditional Access + **PIM** (just-in-time privileged access) + Defender for Cloud + Private Endpoints + Azure Firewall.

## IAM & OAuth 2.0 Flows

| Flow | Use When |
|---|---|
| **Authorization Code + PKCE** | Web/native apps with user interaction |
| **Client Credentials** | Machine-to-machine (M2M) |
| **Device Code** | Devices with no browser |

- **Managed Identities** (system-assigned vs user-assigned): eliminate secrets for Azure-to-Azure — always prefer over service principals for anything in Azure
- **Workload Identity Federation**: OIDC trust without secrets; use on AKS with **Workload Identity**

## Encryption
- **At rest**: Storage SSE (PMK default, CMK via Key Vault), Azure Disk Encryption, **TDE** for Azure SQL
- **In transit**: TLS 1.2/1.3
- **Envelope encryption**: DEK wrapped by KEK; rotate without downtime by supporting two active key versions
- **CMK vs PMK**: CMK gives data sovereignty but adds Key Vault dependency to every read/write path

---

# PART 11: DATA PIPELINE ARCHITECTURES

## ETL vs ELT
- **ETL**: transforms before load (legacy, for constrained targets)
- **ELT**: loads raw, transforms in place (modern default — leverage cloud compute)
- **Azure Data Factory**: ETL/ELT orchestration, mapping data flows, Copy activity

## Stream Processing
- Windowing: tumbling (fixed, non-overlapping), sliding (overlapping), session (activity-based)
- **Azure Stream Analytics**: SQL-based stream processing
- **Databricks Structured Streaming**: high-throughput stateful
- **Azure Event Hubs**: ingestion layer

## Lambda vs Kappa
- **Lambda**: batch (accurate) + speed (real-time) + serving layers — two code paths to maintain
- **Kappa**: single stream path with replay — simpler operationally
- **Modern recommendation**: Kappa with Event Hubs + Databricks Structured Streaming + Delta Lake

## CDC (Change Data Capture)
- Capture row-level DB changes as a stream for cache invalidation, search-index sync, replication, audit
- **Debezium**: de facto connector
- **Azure**: SQL/MI change tracking + ADF; **Cosmos DB change feed** (built-in); Debezium on AKS feeding Event Hubs; **Fabric Mirroring** for zero-ETL into OneLake

---

# PART 12: AI/ML ARCHITECTURE PATTERNS

## RAG (Retrieval-Augmented Generation)

### Pipeline
1. **Ingestion**: load → chunk → embed → index
2. **Retrieval**: embed query → similarity/hybrid search → retrieve context
3. **Generation**: context + query → LLM → response

### Chunking Strategies
- Fixed-size, semantic/sentence-aware, hierarchical (small-to-big), structure-aware

### Retrieval Approaches
- Dense (vector), sparse (BM25), **hybrid (RRF fusion)** — hybrid is best in practice
- **Reranking** with a cross-encoder boosts top-K precision

### Azure AI Search (Recommended)
Per Microsoft's own benchmarking: hybrid search (BM25 keyword + vector via RRF) plus a transformer-based **semantic ranker** is "the most effective retrieval engine for most scenarios."

- Semantic ranker is an L2 step that reranks the top 50 L1 results, scoring on a 0–4 scale
- Set `k`/`maxTextRecallSize` to sum ≥50 to give the reranker a full input set
- **Integrated vectorization** chunks and embeds inside the indexer pipeline

### Azure AI Foundry Evaluators (for RAG)
Microsoft's recommended RAG combination: **Retrieval + Groundedness + Relevance + Content Safety**

Available evaluators: Retrieval, Document Retrieval, Groundedness, Groundedness Pro, Relevance, Response Completeness, Coherence, Fluency, QA, Intent Resolution, Tool Call Accuracy, Task Adherence, risk/safety, textual-similarity (BLEU/ROUGE/METEOR/GLEU/F1).

**Note:** RAGAS is not a native Foundry evaluator — RAGAS integration in the Microsoft ecosystem is via MLflow on Azure Databricks.

## APIM AI Gateway (Front All LLM Traffic from Day One)
- `azure-openai-token-limit`: TPM enforcement
- `azure-openai-emit-token-metric`: usage to App Insights
- **Semantic caching**: Azure Managed Redis + RediSearch + embeddings model
- **Backend pools**: PTU → PAYG spillover on circuit-breaker

## AI Agent Architecture

### Microsoft Agent Framework (Successor to Semantic Kernel + AutoGen)
- **RC 1.0: February 19, 2026; GA targeted end of Q1 2026**
- Both Semantic Kernel and AutoGen are now in maintenance mode
- Unifies AutoGen's multi-agent abstractions with Semantic Kernel's enterprise features (session state, middleware, telemetry)
- Graph-based workflows: sequential, concurrent, handoff, group-chat with checkpointing and human-in-the-loop
- Built on Microsoft.Extensions.AI; supports MCP/A2A/AG-UI; `UseOpenTelemetry()` built in

### Azure AI Foundry Agent Service (GA, May 2025)
- Connected Agents (point-to-point) and multi-agent Workflows
- 1,400+ Logic Apps connectors as tools
- SharePoint/Fabric/Bing knowledge; MCP and A2A tools
- BYO-VNet private networking with no public egress (next-gen GA)

### Agent Memory Patterns
- In-context (history window)
- External vector store (Cosmos DB / Redis / AI Search) for semantic retrieval
- Episodic memory for cross-session state
- **Foundry managed Memory** (preview)

**Host agent loops on ACA or AKS. Durable Functions** can host deterministic, fault-tolerant agent orchestrations that survive restarts and pause for human input at zero compute cost.

## ML Training & Inference
- **Azure Machine Learning**: training, managed online/batch endpoints, MLflow, model registry
- **AzureML SDK v1 reaches EOL June 30, 2026** → migrate to SDK v2

## Prompt Flow Retirement
**Prompt Flow retires April 20, 2027** — no longer recommended for new development. Migrate to **Microsoft Agent Framework** before the date; runtime container images no longer receive updates.

---

# PART 13: INTEGRATION PATTERNS

## Enterprise Integration Patterns (EIP) — Hohpe & Woolf
Key patterns implemented in Azure:
- **Message Channel, Router, Translator, Filter**: Service Bus native
- **Splitter, Aggregator, Scatter-Gather**: Durable Functions for stateful aggregation
- **Dead Letter Channel**: Service Bus DLQ
- **Idempotent Receiver**: Duplicate detection + idempotency keys
- **Competing Consumers**: Service Bus + KEDA auto-scaling

## Workflow Orchestration
| Service | Best For |
|---|---|
| **Durable Functions** | Code-first, fault-tolerant, stateful workflows; human-approval; agent loops |
| **Logic Apps** | GUI-based + 1,400+ connectors; enterprise integration |
| **ADF / Fabric Pipelines** | Data workflows |
| **Copilot Studio** | Conversational/agentic workflows |

## Hybrid Integration
- **ADF Self-hosted Integration Runtime**: on-prem data access
- **APIM self-hosted gateway**: on-prem API exposure
- **Azure Arc**: project on-prem/multi-cloud resources into Azure's control plane
- **Logic Apps Standard on Arc**: edge workflow execution
- **Azure Relay / Hybrid Connections**: lightweight tunneling

---

# PART 14: INFRASTRUCTURE PATTERNS

## Containers & Orchestration

**ACA KEDA gotcha:** Scale-to-zero with Service Bus can scale down prematurely when messages process faster than the polling interval — lower `pollingInterval` or set `minReplicas: 1` for steady low-frequency traffic. KEDA's default cooldown is 300s.

**AKS node pool types:** Azure CNI (standard), Azure CNI Overlay (scalable), Azure CNI Powered by Cilium (note: incompatible with Istio add-on).

## GitOps
- **Flux v2**: AKS GitOps extension, Arc-enabled Kubernetes — security: signed commits, image automation, Key Vault for secrets (not in Git)
- **Argo CD**: on AKS

## Platform Engineering
- **Azure Deployment Environments**: self-service infrastructure
- **Backstage on AKS**, Port/Cortex SaaS: developer portals

---

# CROSS-CUTTING DECISION FRAMEWORK

## Event-Driven vs Request-Response
- Synchronous: when the user needs an immediate consistent answer
- Asynchronous: for background work, decoupling, resilience
- The **dual-write problem** demands either **Outbox** or **Saga** — never two independent writes

## Make vs Buy vs Configure
- Build custom only for differentiating logic
- Prefer managed PaaS for undifferentiated heavy lifting
- Configure open-source when you need control and have ops capacity
- Run TCO including operational toil

## Conway's Law
Systems mirror team communication structure. The **Inverse Conway Maneuver** designs team structure to produce the desired architecture. **Team Topologies**: stream-aligned, platform, enabling, complicated-subsystem teams.

---

# STAGED ROLLOUT GUIDANCE

**Stage 1 — Start simple.**
- Modular monolith on **App Service** with deployment slots
- Azure SQL or PostgreSQL Flexible Server (with PgBouncer)
- Key Vault references for secrets
- App Insights via the OpenTelemetry distro from day one
- Write ADRs for irreversible choices
- *Advance when:* measurable deployment contention or a subsystem with a distinct scaling/availability profile

**Stage 2 — Decompose deliberately.**
- Move to **ACA** (not AKS) for first microservices — KEDA + Dapr without cluster ops
- **Service Bus** for async; **Outbox pattern** to avoid dual writes
- **APIM** as the front door; database-per-service
- *Advance to AKS when:* full Kubernetes API, custom operators, service mesh, or fine-grained node/GPU control

**Stage 3 — Scale and harden.**
- AKS + **Istio add-on** for mTLS (plan CNI — not Cilium); **Workload Identity** + CSI secrets; **Flux** for GitOps
- Availability Zones everywhere; multi-region only once SLO crosses ~99.95%
- Pair Retry + Circuit Breaker; Queue-Based Load Leveling + Competing Consumers
- Define RTO/RPO before choosing geo-replication topology

**Stage 4 — Add AI-native capability.**
- RAG: **Azure AI Search** (`vector_semantic_hybrid`) + Azure OpenAI; co-locate vectors in Cosmos DB/Azure SQL to avoid a separate service
- **APIM AI Gateway** (token limits, semantic caching, PTU→PAYG spillover) on day one
- Agents: **Foundry Agent Service** (GA) + **Microsoft Agent Framework** (GA targeted end of Q1 2026)
- **Migrate off Prompt Flow before April 20, 2027**

---

# PLATFORM MIGRATIONS TO SCHEDULE NOW

| Migration | Deadline |
|---|---|
| Front Door classic → Standard/Premium | March 31, 2027 |
| Azure CDN classic → Front Door | September 30, 2027 |
| AzureML SDK v1 → v2 | June 30, 2026 |
| Linux Consumption Functions → Flex Consumption | September 30, 2028 |
| In-process .NET Functions model → isolated | November 2026 |
| Semantic Kernel / AutoGen → Microsoft Agent Framework | Before GA (end Q1 2026) |
| Prompt Flow → Microsoft Agent Framework | Before April 20, 2027 |
| Analytics → Microsoft Fabric / OneLake (medallion) | Ongoing |
