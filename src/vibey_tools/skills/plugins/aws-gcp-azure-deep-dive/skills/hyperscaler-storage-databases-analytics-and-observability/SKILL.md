---
name: hyperscaler-storage-databases-analytics-and-observability
description: "Use when choosing a data or platform service: object, block and file storage and the storage classes and retrieval characteristics, the managed database offerings relational and otherwise, the analytics and warehouse stacks, the AI/ML service layers and what is genuinely differentiated, and observability — the native logging, metrics and tracing products and their limits."
---

# AWS, GCP and Azure: Storage, Databases, Analytics, AI/ML Services, and Observability

> **Part 3 of 5** of the *AWS, GCP and Azure Deep Dive* reference (plugin `aws-gcp-azure-deep-dive`), covering §9–§13. Sibling skills: `hyperscaler-framing-responsibility-identity-and-hierarchy` (§0–§4), `hyperscaler-networking-compute-containers-and-serverless` (§5–§8), `hyperscaler-cost-reliability-iac-lock-in-and-migration` (§14–§18), `hyperscaler-reference` (§19–§26). Section numbers are shared across the set; a reference written as §N → `skill` points into that sibling skill.
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
>    provisioned resources, and per-request charges on managed services** — **§14 → `hyperscaler-cost-reliability-iac-lock-in-and-migration`.**

---

## §9. Storage

```
Object     S3               Blob Storage       Cloud Storage
Block      EBS              Managed Disks      Persistent Disk / Hyperdisk
File       EFS / FSx        Azure Files        Filestore
Archive    Glacier tiers    Archive tier       Archive / Coldline
```
**⚠️ Storage classes are the main cost lever**, **and the trap is retrieval**: ⚠️ **archive
tiers are cheap to store and expensive and SLOW to retrieve, with minimum storage
durations that charge you if you delete early.** **Lifecycle policies that move data down
tiers automatically are the right pattern; moving data you actually read is not.**
**⚠️ S3 is strongly consistent** (**since 2020 — older material saying otherwise is
wrong**); **all three now offer strong read-after-write consistency for objects.**
**⚠️ Object storage is not a filesystem.** **No atomic rename, no partial update, and
list operations are expensive at scale** — **which is why "S3 as a database" patterns fall
over.**

---

## §10. Databases

```
Relational     RDS / Aurora     Azure SQL / Flexible Server  Cloud SQL / AlloyDB
Distributed    ⚠️ Aurora DSQL / Spanner-likes  Cosmos DB    ⚠️ SPANNER
NoSQL doc/kv   DynamoDB         Cosmos DB          Firestore / Bigtable
Cache          ElastiCache      Azure Cache        Memorystore
Graph/other    Neptune, Timestream  various        Bigtable
```
**⚠️ Spanner and Cosmos DB are genuinely distinguishing**: **globally distributed with
strong consistency (Spanner) or tunable consistency (Cosmos).** ⚠️ **Both are expensive
and both solve a problem most applications do not have.**
**⚠️ DynamoDB's constraint is its virtue**: **single-digit-millisecond at any scale,
provided you design the access patterns first.** ⚠️ **It punishes relational thinking
severely — if you find yourself wanting a join, you modelled it wrong or picked the wrong
store.**
**⚠️ The managed-database tradeoff, stated plainly**: **you give up superuser access, some
extensions, and fine-grained tuning, in exchange for backups, patching, failover and
replication you'd otherwise build.** **For most teams that's the right trade** —
⚠️ **but check extension support and version currency before committing, because the gap
between "PostgreSQL" and "managed PostgreSQL" is where migrations stall.**

---

## §11. Analytics

```
Warehouse      Redshift         ⚠️ Fabric / Synapse    ⚠️ BIGQUERY
Lake           S3 + Glue + Athena  ADLS + Fabric      GCS + BigLake
ETL            Glue             Data Factory        Dataflow / Dataproc
Streaming      Kinesis / MSK    Event Hubs          Pub/Sub + Dataflow
BI             QuickSight       ⚠️ Power BI          Looker
```
> **⚠️ BigQuery is GCP's strongest product and the clearest reason to choose GCP.**
> ⚠️ **Genuinely serverless — no cluster to size, no nodes to manage, separated storage
> and compute from the start.** **Redshift has moved toward this with serverless options
> but carries its cluster heritage; Fabric is Microsoft's consolidation attempt and is
> capable but has been a moving target.**
> **⚠️ BigQuery's cost model is the thing to watch**: **on-demand pricing charges per byte
> SCANNED, so an unpartitioned table plus `SELECT *` is a genuinely expensive mistake.**
> **Partition, cluster, select only the columns you need, and consider capacity pricing
> above steady volume** (see a reporting/dashboards reference §7).

**⚠️ Power BI is a real reason organizations choose Azure** — **licensing bundled with
Microsoft 365 makes it the default in a large share of enterprises regardless of where
the data lives.**

---

## §12. AI/ML Services

```
Managed platform  SageMaker      Azure ML / Foundry   Vertex AI
Model API         ⚠️ Bedrock      ⚠️ Azure OpenAI      ⚠️ Vertex / Gemini API
Own accelerator   Trainium/Inferentia  —              ⚠️ TPUs
```
**⚠️ The multi-model API layer is where the competition now sits**: **Bedrock, Azure AI
Foundry and Vertex all offer several model families behind one interface with
enterprise-grade data handling.** ⚠️ **The practical differentiators are which models are
available, in which regions, with what data-residency and retention commitments — and
those change frequently enough that any specific claim here would be stale.** **Check the
current model availability matrix rather than trusting a comparison article.**
**⚠️ GPU and accelerator capacity is genuinely constrained** (§21.2 → `hyperscaler-reference`) — **availability by
region, and the need for quota requests and sometimes capacity commitments, is now a real
architectural constraint rather than a formality.**

---

## §13. Observability

```
Metrics/logs   CloudWatch       Azure Monitor       Cloud Monitoring/Logging
Tracing        X-Ray            App Insights        Cloud Trace
Audit          ⚠️ CloudTrail     ⚠️ Activity Log      ⚠️ Cloud Audit Logs
```
**⚠️ The audit log is the one you must configure correctly and retain**: **CloudTrail,
Activity Log and Cloud Audit Logs are how you answer "who did this and when" after an
incident.** ⚠️ **Ensure they're enabled organization-wide, written to an account/project
the operators of the audited estate cannot modify, and retained long enough to matter.**
⚠️ **Data-plane logging (e.g. object-level reads) is usually OFF by default and is
frequently what you need.**
**⚠️ Native observability is adequate and expensive at volume** — **log ingestion and
retention charges are a common surprise line item, and this is why third-party
observability vendors exist.**
