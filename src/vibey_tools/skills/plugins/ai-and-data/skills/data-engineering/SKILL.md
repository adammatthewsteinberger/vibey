---
name: data-engineering
description: "Production data engineering reference covering ELT/ETL patterns, dbt project structure, orchestration (Airflow/Dagster/Prefect), Python data stack (pandas/Polars/DuckDB/Spark), cloud warehouses (Snowflake/BigQuery/Azure Fabric), lakehouse formats (Iceberg/Delta/Hudi), CDC with Debezium, SCD2, data quality, feature stores, and ML productionization with MLflow. Use when answering questions about data pipelines, SQL optimization, warehouse cost control, Python data tools, gradient boosting, A/B testing, or modern data stack architecture."
---

# Data Engineering & Data Science Production Reference

## ELT vs ETL — Decision Framework

**ELT is the production default** on modern cloud warehouses (Snowflake, BigQuery, Databricks). Load raw data first, transform in-warehouse with dbt. Storage/compute decoupling makes this cheaper and operationally simpler than a separate transformation tier.

**ETL still wins when:**
- Compliance requires pre-load masking/tokenization (HIPAA, PCI DSS)
- Source data must be filtered before reaching governed storage
- Destination is an operational system, not a warehouse

**ELT advantages:** preserves raw data for reprocessing when business logic changes; no transformation infrastructure to manage; one pipeline to operate.

---

## Pipeline Design Principles

- **Idempotency is non-negotiable** — re-running a job must produce the same result; enables safe backfills and retries
- **At-least-once semantics** (with idempotent writes/dedup) for most analytics; exactly-once is expensive and rarely necessary
- **Late-arriving data**: handle with watermarks and windowing
- **Late-arriving dimensions** (fact arrives before its dimension): use placeholder/inferred dimension rows rather than dropping facts or accepting null FKs
- **Watermark storage**: store in an audit table in the target DB, not just an orchestrator variable — makes it debuggable

---

## Incremental Loads & CDC

**Watermark-based incremental**: pull rows where `updated_at > last_watermark`. Store the watermark in the target DB audit table.

**Debezium** (dominant open-source CDC):
- Reads the database transaction log (WAL/binlog) via Kafka Connect — not polling
- Captures every insert/update/delete in order with minimal source impact
- Supports MySQL, Postgres, MongoDB, SQL Server, Oracle
- **Incremental snapshots** (v1.6+): interleaves snapshotting with streaming using watermark approach (from Netflix's DBLog paper) — no long table locks
- Note: log-based CDC on Postgres may require config changes and a restart

---

## SCD2 Implementation

Use `effective_from` / `effective_to` / `is_current` columns.

**Reliable cross-platform pattern (two steps):**
1. Close changed rows (set `effective_to`, `is_current = 0`)
2. Insert new current versions

A single MERGE cannot do both UPDATE and INSERT from one source row without the nested INSERT-over-MERGE-OUTPUT trick.

**Options:**
- **dbt snapshots**: cleaner when Silver layer is dbt-managed
- **Manual MERGE**: more control (e.g., Spark Delta MERGE in lakehouse pipelines)

**Query patterns:**
- Current state: `WHERE is_current = 1`
- Historical: `WHERE order_date BETWEEN effective_from AND effective_to`
- Forgetting these joins duplicates fact rows

---

## dbt Project Structure

Three-layer architecture:

| Layer | Description | Materialization | Rules |
|---|---|---|---|
| **Staging** | 1:1 with sources; rename/cast/basic categorization | Views | No joins; prefix `stg_` |
| **Intermediate** | Business logic, joins, re-graining | Ephemeral | Referenced by only one downstream (if more, make it a macro) |
| **Marts** | Wide/denormalized entities | Tables | ≤4–6 joins; prefix by domain |

**Materialization progression:** view → table (when query is slow) → incremental (only when table builds are too slow).

**Anti-patterns to avoid:**
- `finance_orders` vs `marketing_orders` — build one source of truth instead
- Splitting ML vs reporting marts
- Using seeds to load source data
- Using tags instead of folders as primary selectors

**dbt tests**: `not_null`, `unique`, `accepted_values`, `relationships` on every model. Using thresholds/severities to suppress failing tests hides anomalies and erodes audit trust.

---

## Orchestration — Tool Selection

| Tool | Best for | Weakness |
|---|---|---|
| **Airflow** | Enterprise, 100+ pipelines, 1,000+ providers (MWAA/Cloud Composer/Astronomer) | Steeper learning curve; needs running instance to test DAGs |
| **Dagster** | Greenfield/dbt-centric platforms; software-defined assets, local testing (swap Snowflake for DuckDB) | ~1/4 of Airflow's integrations |
| **Prefect** | Python-native, fastest laptop-to-production | Serverless cold starts 5–15s; near-real-time workloads feel this |

**Migration rule:** 50+ working Airflow DAGs → stay and adopt TaskFlow incrementally; Dagster migration runs ~10–20 DAGs/month via `dagster-airflow`.

---

## Data Quality — Layered Approach

- **dbt tests**: shift-left checks inside transformation layer
- **Great Expectations**: 300+ expectations, automated profiling, human-readable Data Docs; expressive Python validation-as-code
- **Soda Core**: YAML-based, SQL-native, lightweight
- **Deequ** (Amazon, Spark-native): massive-scale checks without sampling
- **Pandera**: DataFrame schema validation (pandas, Polars, PySpark, Ibis backends); use for feature-engineering checks, drift detection, ETL decorators

Most mature teams combine dbt tests (model layer) + Great Expectations or Soda Core (distribution/profiling checks dbt can't express).

---

## Python Data Stack

### pandas
- Optimize memory: categorical dtypes for low-cardinality strings, downcast numerics, chunk large CSVs (`chunksize`), Arrow-backed dtypes (pandas 2.x)
- Avoid row-wise `apply`/`iterrows` — vectorize
- Single-threaded for most ops (GIL-bound)

### Polars (Rust-based, columnar Arrow)
- Multi-threaded by default
- **Lazy API**: predicate pushdown, projection pruning, operation fusion, streaming mode for larger-than-RAM data
- Benchmarks vs pandas (NYC taxi 12.7M rows): 25× faster CSV reads, 5–10× faster aggregations, joins up to ~13.75×
- 650GB Delta test on 32GB EC2: Polars 12 min vs PySpark >1 hour
- Parquet write performance converges (both delegate to PyArrow C++)

### DuckDB (in-process OLAP)
- Vectorized execution; reads Parquet/S3 directly with columnar pushdown
- 1M-row query: ~3.84s vs pandas' ~19.57s
- 5–10× faster group-bys on >100M rows
- Best for local/embedded analytics and as a dbt/test backend

### PySpark
- Use DataFrame API (Catalyst optimizer) over RDDs
- Avoid data skew (salting, AQE); prefer broadcast joins when one side fits in memory
- **Only reach for Spark when data won't fit on a single node** or you need distributed/streaming/MLlib

### Arrow/PyArrow
Zero-copy columnar IPC — the lingua franca between Polars, DuckDB, pandas 2.x, and Spark.

---

## Data Quality at Scale — Pydantic vs Pandera

**Pandera**: tabular validation (DataFrameSchema or class-based DataFrameModel); use for DataFrame-level checks.

**Pydantic V2**: record/object validation; core rewritten in Rust as `pydantic-core` — "about 17× faster than V1." Use for API/record validation.

Integration: Pandera uses Pydantic for coercion; embed Pydantic models row-wise only for very small (~100-row) frames.

---

## Batch vs Streaming Decision

| Need | Recommendation |
|---|---|
| Sub-second latency, business acts on it (fraud, dynamic pricing) | True streaming (Flink or Kafka + consumer) |
| Seconds of latency acceptable | Micro-batch (Spark Structured Streaming) |
| Minutes/hours acceptable | Batch ELT |

**Flink**: true event-at-a-time, p99 latencies <100ms; more resource-efficient for low-latency.
**Spark Streaming**: ~2–5s; wins when you share resources across batch and streaming or already run Databricks/Delta.

**Cost lever**: BigQuery streaming costs $0.01/200MB; micro-batch loading is free — a major difference at scale.

---

## SQL & CTE Best Practices

### CTE vs subquery vs temp table
- CTEs and subqueries are **performance-equivalent** in modern engines (Postgres 12+, BigQuery, Snowflake)
- CTEs win on readability and avoiding repeated scans
- Postgres ≤11 materialized CTEs (optimization fence); Postgres 12+ inlines them
- Snowflake: CTE referenced twice scanned 1.3MB vs 2.7MB for repeated subquery
- Temp tables benefit from indexing for complex multi-step manipulation

### Window Functions
- `ROW_NUMBER` (unique sequential), `RANK` (gaps on ties), `DENSE_RANK` (no gaps)
- `LAG`/`LEAD` (prior/next row), `FIRST_VALUE`/`LAST_VALUE`
- **Critical**: `ROWS` vs `RANGE` frames — RANGE includes all peer rows with equal ordering values; the default `RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW` can produce surprising results with ties

### Query Optimization
- Read EXPLAIN ANALYZE plans; confirm partition pruning fires and predicate pushdown reaches scans
- **BigQuery**: partition on DATE/TIMESTAMP/INT, cluster on high-cardinality filter columns; filtering one month of 5-year table scans ~1/60th
- **Snowflake**: automatic micro-partitioning with min/max metadata; manual clustering keys for large frequently-filtered tables (50–70% data reduction); note clustering/elimination uses only first ~5 characters (so YYYYMMDD clusters by YYYYM effectively)

### Anti-patterns
- Correlated subqueries (re-execute per outer row — rewrite as joins)
- `DISTINCT` to paper over join fan-out (fix the join grain instead)
- Implicit type coercion (silently kills index/partition usage)
- `SELECT *` on columnar stores (BigQuery bills full column scan regardless of LIMIT)

---

## Cloud Warehouse Cost Controls

### Snowflake
- **Auto-suspend at 60s** for ETL/short bursts; 5–10 min for cache-sensitive BI
- Enable auto-resume; use **Economy scaling policy** for batch to avoid cluster thrashing
- Multi-cluster scales out for concurrency, not single-query speed
- Capacity pricing (1–3 yr) saves ~15–25% vs on-demand
- **Cost killers**: zombie warehouses (`AUTO_SUSPEND=0`), over-provisioned dev XL warehouses, excessive Time Travel retention on truncate-reload tables, runaway reclustering on high-churn tables

### BigQuery
- On-demand: $6.25/TiB scanned (first 1 TiB/month free); `SELECT *` on 10TB = $62.50; LIMIT does not reduce cost
- Editions (Standard/Enterprise/Enterprise Plus) charge per slot-hour; autoscaling GA Feb 2025
- Break-even from on-demand to slots: ~300–500 TiB/month steady scanning
- Use `INFORMATION_SCHEMA.JOBS` / `JOBS_TIMELINE` for cost attribution
- Tables untouched 90 days → long-term storage at half price automatically

### Azure / Microsoft Fabric
- **Fabric Lakehouse** (Spark-primary) vs **Fabric Warehouse** (T-SQL-primary, full read/write)
- All data in OneLake (Delta Parquet) — Spark notebooks, T-SQL, and Power BI Direct Lake read the same table without copies
- Synapse dedicated pool → Fabric Warehouse migration: ~30–50% cost reduction vs always-on Synapse; expect 4–8 weeks per pool
- Databricks: reserved/committed compute + predictive optimization + right-sized clusters = 30–70% savings

---

## Lakehouse Table Formats

| Format | Best for | Notes |
|---|---|---|
| **Iceberg** | Interoperability standard; partition evolution as metadata operation | Databricks acquired Tabular (Iceberg creators); AWS S3 Tables, Snowflake Polaris catalog |
| **Delta** | Largest installed base; Microsoft Fabric default | Most large enterprises; Databricks default |
| **Hudi** | Streaming/CDC upserts (Merge-on-Read first-class) | Vendor (Onehouse) benchmarks favor it for upserts — run your own TPC-DS |

---

## Azure Databricks Optimization

- `OPTIMIZE`: compacts small files (~1GB target)
- `ZORDER BY`: co-locates data for high-cardinality filter columns
- `VACUUM`: removes unreferenced files (default 7-day retention via `delta.deletedFileRetentionDuration`)
- **Liquid clustering** (`CLUSTER BY`, GA DBR 15.2+): redefine clustering keys without rewriting data
- **Automatic liquid clustering** (`CLUSTER BY AUTO`, DBR 15.4+) + **predictive optimization**: Unity Catalog auto-selects keys and runs OPTIMIZE/VACUUM/ANALYZE on serverless compute
- Limit clustering to 1–4 high-value filter/join columns; don't partition tables under ~1TB

---

## Schema Evolution & Data Contracts

- Use a schema registry (Confluent) with Avro for Kafka to enforce backward/forward compatibility
- **Open Data Contract Standard (ODCS) v3.1.0** (Apache 2.0, maintained by Bitol under Linux Foundation AI & Data): machine-readable producer-consumer agreements covering schema + semantics + SLAs
- **Data Contract CLI**: lint, test against Snowflake/BigQuery/Databricks, detect breaking changes, export to dbt/Avro/JSON Schema
- **Rule of thumb**: one person → skip the contract; two+ teams depend on it in production → write one

---

## Feature Stores

**Solve:** training-serving skew, online/offline consistency, feature reuse.

| Store | Type | Best for |
|---|---|---|
| **Feast** (Linux Foundation) | Open-source, bring-your-own-infra | Cost/flexibility/no lock-in; you own pipeline and writes to online store |
| **Tecton** (ex-Uber Michelangelo team) | Managed; includes transformation/compute | Mission-critical real-time; eliminates skew "by construction"; sub-10ms p99 online serving |

**Offline store**: BigQuery/Snowflake/S3 for point-in-time-correct training sets.
**Online store**: Redis/DynamoDB for low-latency inference.

Use Feast for flexibility; Tecton for managed SLAs on real-time use cases.

---

## MLflow — Production Patterns

Four components: **Tracking** (log params/metrics/artifacts per run), **Projects** (reproducible packaging), **Models** (flavors for deployment), **Model Registry** (versioning + lineage + lifecycle).

**Modern champion/challenger pattern (MLflow 2.9.0+):**
- Fixed stages (`Staging/Production/Archived`) are deprecated
- Use **aliases**: mutable named pointers like `champion`/`challenger`
- Reference: `models:/MyModel@champion`
- Promote by reassigning the alias

**Production deployment patterns:**
- Batch scoring for non-latency-sensitive use
- Online inference behind managed endpoint for real-time
- **Shadow mode**: run new model on live traffic without acting, before promotion
- **Champion/challenger**: controlled rollout via alias reassignment

---

## ML Modeling Best Practices

### Feature Engineering
- Target encoding for high-cardinality categoricals (with CV/smoothing to prevent leakage)
- One-hot for low cardinality; embeddings for very high cardinality
- Temporal features (lags, rolling windows): build carefully to avoid leakage
- **Never compute encodings/scalers on full dataset before splitting**

### Model Validation
- **Time-series CV** (expanding/rolling window) for temporal data — never shuffle-split
- **Group-k-fold** when records cluster (same user/entity)
- Calibrate probabilities (Platt/isotonic) for reliable scores
- scikit-learn `Pipeline + ColumnTransformer`: canonical leakage guard — preprocessing fit only on training folds

### Gradient Boosting (Tabular Data Default)
All three are competitive; no significant differences under Wilcoxon–Holm analysis (arXiv 2407.00956):

| Library | Strength | Weakness |
|---|---|---|
| **LightGBM** | Fastest (~7× vs XGBoost); best for very large datasets | Leaf-wise growth overfits small data |
| **CatBoost** | Best with many categorical features (native handling); strong defaults | |
| **XGBoost** | Slight accuracy/generalization edge in some benchmarks; Kaggle workhorse | Slowest grid search on large data |

**Tuning sequence**: benchmark all three with defaults → tune the frontrunner: lower `learning_rate` + more estimators with early stopping, reduce `max_depth`/`num_leaves`, raise L1/L2, subsample.

### A/B Testing
- Pre-compute sample size from MDE, alpha, and power (typically 80%)
- **Peeking problem**: checking results repeatedly inflates Type I error
- **Fixed-horizon tests**: no peeking, decide at planned N — maximum rigor
- **Sequential testing** (O'Brien-Fleming or Pocock alpha-spending): valid peeking and early stopping
- A/A tests validate randomization
- Multi-armed bandits: good for many-armed, low-stakes optimization; not for clean causal readouts

---

## Data Mesh — What Actually Works

Incremental product mindset (in order):
1. **Ownership**: every dataset has a named accountable owner
2. **Contracts**: written quality/freshness/completeness SLAs in YAML
3. **Discoverability**: catalog registration
4. **Governance**: automatic access control, audit, lineage

The "full mesh topology" without a self-serve platform fails — domain teams default to ad-hoc pipelines. The self-serve platform is the most underinvested principle.

---

## Staged Implementation Roadmap

**Stage 1 (weeks 0–8):** ELT on cloud warehouse + dbt (staging/intermediate/marts). Enable cost guardrails: Snowflake auto-suspend 60s + Economy; BigQuery partitioning/clustering; Databricks Unity Catalog + predictive optimization. Add dbt tests on every model.

**Stage 2 (months 2–4):** Layer Great Expectations or Soda Core for distribution/profiling checks. Data contracts (ODCS + Data Contract CLI) for datasets two+ teams depend on. Deploy orchestrator matched to team. SCD2 via dbt snapshots or two-step MERGE.

**Stage 3 (months 4–8):** Replace pandas bottlenecks with Polars/DuckDB before reaching for Spark — only adopt Spark when data genuinely exceeds single-node memory. CDC via Debezium with incremental snapshots. Streaming only where sub-second latency drives business action.

**Stage 4 (months 6–12):** scikit-learn Pipeline + ColumnTransformer to prevent leakage; time-series/group CV; MLflow Registry aliases (champion/challenger). Gradient boosting (benchmark LightGBM/CatBoost/XGBoost). Feature store only when reuse and training-serving skew are real pain points.
