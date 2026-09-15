---
name: performance-optimization
description: "Production performance reference covering Python (profiling with py-spy/Scalene, GIL and free-threading in 3.13t/3.14t, NumPy/Pandas vectorization 100–740x wins, Numba/Cython/PyPy, asyncio best practices, ASGI vs WSGI), Next.js/TypeScript (Core Web Vitals, RSC bundle discipline, PPR/Cache Components, App Router caching layers, Turbopack, DB pooling), and Azure cloud (compute cold starts, ACA/KEDA scale-to-zero, messaging service selection, Cosmos DB vs PostgreSQL, Redis ConnectionMultiplexer, Front Door CDN/WAF, VMSS autoscale, cost tiers). Use when diagnosing or fixing performance bottlenecks in Python services, Next.js apps, or Azure infrastructure."
---

# Performance Maxing in Production: Python, Next.js/TypeScript, and Azure Cloud

## Core Principle

**The biggest wins come from architecture, not micro-optimization.** In Python, vectorizing Pandas/NumPy loops yields 100–740x speedups while profiler-guided fixes routinely cut P99 ~40%. In Next.js, pushing `"use client"` to the leaves and using RSC streaming/PPR cuts First Load JS 50–70% and moves TTFB from ~350ms to ~40–90ms. In Azure, choosing the right compute tier matters more than any code tweak.

**Measure first. Never optimize without before-numbers.**

---

## Python Performance

### Profiling Toolkit

| Tool              | Type        | Use for                                                   | Command / Notes                                      |
|-------------------|-------------|-----------------------------------------------------------|------------------------------------------------------|
| `cProfile`        | Deterministic | Whole-program overview, first pass                        | `python -m cProfile -s cumtime app.py`               |
| `line_profiler`   | Deterministic | Per-line timing in hot functions                          | `@profile` decorator; `kernprof -l -v script.py`     |
| `memory_profiler` | Deterministic | Per-line memory                                           | `@profile`; `mprof run`/`mprof plot`                 |
| `py-spy`          | Sampling    | **Production** — attaches to live PID, ~0.1ms overhead, no restart | `py-spy top --pid 1234`; `py-spy record -o out.svg --pid 1234 --duration 30` |
| `Scalene`         | Sampling    | Deep dives — separates Python vs native vs system %, per-line memory, copy-volume detection | `scalene app.py` or `%scalene` in Jupyter; 10–20% overhead |

**Investigation loop:**
1. `py-spy`/`pyinstrument` → find the hot path
2. `Scalene` → classify: Python %? (vectorize/algorithm) native %? (library/IO) memory? (copy volume)
3. `line_profiler` → zoom in on the specific function

**Real case:** `py-spy top` revealed a `copy.deepcopy` in a retry loop; replacing it dropped P99 ~40%.

### The GIL, Threading, and Free-Threading

**GIL behavior:** Only one thread runs Python bytecode at a time.
- **I/O-bound** work → threading works (threads release the GIL while waiting on I/O)
- **CPU-bound** work → use `multiprocessing` / `concurrent.futures.ProcessPoolExecutor`

**Multiprocessing caveat:** Each process has interpreter-creation + data-copy overhead. For small per-task work (e.g., per-row DataFrame operations), multiprocessing can be 2–10x *slower*. Per-task work must be large enough to amortize the cost.

**Free-threaded Python:**

| Version  | Status                                                           |
|----------|------------------------------------------------------------------|
| 3.13     | Phase I — experimental (`python3.13t`); ~40% single-thread penalty |
| 3.14     | Phase II — officially supported, still opt-in (`python3.14t`); "roughly 5–10% single-thread penalty" (official docs); specializing adaptive interpreter enabled |

Phase II status from the Python 3.14 "What's New" docs: "the free-threaded build of Python is now supported and no longer experimental."

**C-extension safety:** If you import a C extension that hasn't declared thread-safety, the interpreter silently re-enables the GIL for the whole process. Check with `sys._is_gil_enabled()` after imports.

**Install:** `uv python install 3.14t` or python.org installers / deadsnakes PPA.

**Real benchmark:** Free-threaded multi-threaded DataFrame row processing cut time ≥50% (sometimes >80%) vs single-thread; multiprocessing on the same small tasks degraded performance.

**Adopt for:** CPU-bound parallel workloads (image processing, transforms, ML inference) once your key dependencies ship free-threaded wheels.

### Faster CPython (3.11 → 3.14)

| Version | Key improvement                                              | Speedup vs. 3.10        |
|---------|--------------------------------------------------------------|-------------------------|
| 3.11    | Specializing adaptive interpreter (PEP 659); zero-cost exceptions; frame optimizations | 1.25x avg; recursive functions 1.7x |
| 3.12    | Refined specialization; per-interpreter GIL groundwork      | —                       |
| 3.13    | Experimental free-threading + experimental JIT (0–5% today) | —                       |
| 3.14    | More aggressive inlining/specialization                      | Cumulatively ~40–50% faster than 3.10 |

**Upgrading the interpreter is one of the highest-ROI changes** — recompile/retest and you get speedups with no code change.

The 3.13 JIT is currently 0–5% — infrastructure for future gains, not a reason to upgrade today.

### NumPy/Pandas Vectorization

**The single biggest per-effort win in data code.**

| Method             | Time (10k rows, element-wise) | Relative          |
|--------------------|-------------------------------|-------------------|
| Vectorized         | ~0.001s                       | 1x (baseline)     |
| `apply()`          | ~0.13s                        | ~100x slower      |
| `iterrows()`       | ~0.74s                        | ~740x slower      |

Why loops are slow: every iteration goes through the Python interpreter with per-object type checks. NumPy pushes the loop into pre-compiled SIMD C operating on homogeneous contiguous memory.

**Rules:**
1. Prefer native vectorized column operations and boolean indexing
2. `df.apply(fn, raw=True)` bypasses Series overhead when you must use `apply`
3. Use `itertuples`, never `iterrows`, if you must loop
4. `np.vectorize` is convenience, not performance — it's a for-loop
5. Drop to `.to_numpy()` for 2x–3000x gains in some cases
6. When not vectorizable, use Numba

**Memory:** choose smallest dtypes, use categoricals for low-cardinality strings, prefer `float32`, store data as Parquet.

### Compilation and Acceleration

| Tool    | Best for                                              | Benchmark                                   | Limitation                              |
|---------|-------------------------------------------------------|---------------------------------------------|-----------------------------------------|
| Numba `@njit` | Numeric Python/NumPy with minimal code change   | Pairwise distance: pure Python 13,400ms → NumPy 111ms → Numba **9.12ms** (Numba/Cython ~1300–1500x over pure Python, ~10x over NumPy) | Only numeric/NumPy-compatible code; no arbitrary Python objects |
| Cython  | Distributable libraries, typed memoryviews, C calls  | ~9.87ms (similar to Numba); Numba beat Cython 20–300% in some loop cases | More effort; needs static typing to shine |
| PyPy    | Long-running pure-Python loop-heavy code after warmup | Good | Weaker C-extension compat; larger footprint; not for short scripts |
| ctypes/cffi | Calling existing C libraries                    | —                                           | Need an existing compiled library       |

**Caveat:** Cython/Numba still pay Python↔native conversion overhead at call boundaries. Best after profiling identifies a small hot set of functions.

### Asyncio Best Practices

**`asyncio.gather` vs `asyncio.TaskGroup`:**
- `gather` runs concurrently but does NOT cancel siblings on failure
- `TaskGroup` (3.11+) gives structured concurrency: any task failure cancels the rest and raises `ExceptionGroup` (handle with `except*`)

**Always set timeouts on every external call.**

**Antipatterns:**
1. **Blocking the event loop** with CPU-bound code or sync I/O (`time.sleep`, `json.loads` on huge strings, sync DB drivers) — offload with `await loop.run_in_executor(pool, fn)` or `asyncio.to_thread`
2. **Un-awaited tasks getting GC'd** — the event loop holds only weak refs; collect tasks in a `set` and `add_done_callback(s.discard)`
3. **Sharing asyncio objects across threads**

The eager task factory (`asyncio.eager_task_factory`) can speed async-heavy `gather`/`TaskGroup` workloads (up to ~50% in some cases).

### ASGI vs. WSGI

WSGI (Flask/classic Django): one request per worker; a worker blocks while waiting on DB/IO.

ASGI (FastAPI/Starlette, Django async): asyncio event loop — one Uvicorn worker handles thousands of concurrent in-flight I/O-bound requests.

**Benchmarks (Python 3.13, single vCPU, I/O-bound):**

| Scenario                        | FastAPI       | Flask           |
|---------------------------------|---------------|-----------------|
| Auth + DB/JSON endpoint         | ~435 RPS      | ~315–344 RPS    |
| Plaintext                       | ~22,000 RPS   | ~3,200 RPS      |
| Async SQLAlchemy + Postgres      | ~8,200 RPS    | ~1,900 RPS      |

FastAPI is generally ~3x+ Flask on I/O-bound concurrency. Real apps with business logic compress these gaps. For CPU-bound or simple sync apps the async advantage shrinks.

### Database from Python

- Use SQLAlchemy connection pooling (avoid per-request connects)
- Batch queries to avoid N+1
- Use `selectinload`/`joinedload` for eager loading
- Use async drivers (asyncpg) under ASGI

---

## Next.js / TypeScript Performance

### Core Web Vitals Targets

| Metric | Good threshold | Current web failure rate |
|--------|---------------|--------------------------|
| LCP    | <2.5s         | ~38% of mobile pages fail (HTTP Archive 2025) |
| INP    | <200ms        | ~23% of mobile pages fail; 43% of websites fail per CrUX/Semrush |
| CLS    | <0.1          | ~19% of mobile pages fail |

Only 48% of mobile / 56% of desktop pages pass all three.

**INP replaced FID on March 12, 2024.** INP measures full interaction latency (input delay + processing + presentation) at the 75th percentile across ALL interactions, not just the first.

### What Moves Each Metric

**LCP:**
- Preload the LCP image with `fetchpriority="high"` + `next/image priority`
- Modern formats (AVIF/WebP via `next/image`)
- SSR/static shell so content is in the initial HTML
- Critical CSS inlining

**INP:**
- Break up long JavaScript tasks (>50ms blocks the main thread)
- Defer/facade third-party scripts (YouTube: poster image → iframe on click)
- Self-host analytics
- Passive event listeners; debounce handlers

**CLS:**
- Explicit `width`/`height` on all media (or `aspect-ratio`)
- Reserve space for ads/banners
- `font-display: swap` with matched fallback metrics (`next/font` handles this)

### RSC Bundle Discipline

`"use client"` marks a **module boundary** — everything imported by a client module becomes client-side code. A single misplaced directive silently promotes large subtrees.

**Golden rules:**
1. Push `"use client"` to leaf nodes (only the interactive input, not its parent card)
2. Fetch data in parallel across sibling Server Components
3. Wrap each independent slow dependency in its own `<Suspense>` with a **dimension-matched skeleton** (avoids CLS)
4. Pass Server Components as `children` into Client Component wrappers

Full RSC adoption reports **50–70% First Load JS reduction** and improved INP from reduced hydration cost.

### App Router Caching: The Four Layers

Understanding all four is required to diagnose cache bugs:

| Layer                | Scope              | What it caches                    | Invalidated by          |
|----------------------|--------------------|-----------------------------------|-------------------------|
| Request Memoization  | Single render      | Identical `fetch` calls           | Automatic per render    |
| Data Cache           | Across requests/deploys | `fetch` results with `next: { revalidate, tags }` | `revalidatePath`, `revalidateTag` |
| Full Route Cache     | Across requests    | Prerendered HTML + RSC payload for static routes | Revalidation or rebuild |
| Router Cache         | Client-side in-memory | Visited routes/layouts          | Navigation/time (~30s stale minimum) |

**v15+ change:** `fetch` is no longer cached by default (`no-store`). You opt in with `cache: 'force-cache'` or `next: { revalidate }`.

### PPR / Cache Components

Static shell served from edge (TTFB ~40–90ms) while dynamic holes stream in one HTTP response.

PPR mental model: *everything outside `<Suspense>` is static, everything inside is dynamic.*

**When to use:** Pages with a stable shell and small dynamic regions — product pages, pricing, marketing surfaces where ~80% of layout is cacheable.

**Skip PPR for:** Fully authenticated pages (account settings, live dashboards), high-frequency live data.

**Debugging:** A single `cookies()`/`headers()`/`connection()` call outside Suspense makes the entire route fully dynamic. Use `NEXT_LOG_LEVEL=debug next build` to identify what's forcing dynamic rendering.

Build output marks PPR routes with ◐.

### Turbopack (Default in Next.js 16)

Dev: dramatically faster HMR; claimed ~400% faster `next dev`, 10x HMR on large projects.

Production (Cal.com controlled cold-build test, Next 15.5.2):
- ~19% faster median build (187s → 152s)
- But ~211KB larger shared chunk; +279KB median First Load JS per route (all 151 routes)

**A/B test First Load JS before switching production builds.** Hybrid (Turbopack dev, Webpack prod) is a valid fallback.

### Database from Next.js: Prisma in Serverless

**The connection exhaustion problem:** `connection_limit` is per-instance. 20 pods × pool 20 = 400 connections, potentially exceeding DB max of 300.

**Solutions:**
1. Singleton Prisma client (`globalThis` guard to survive HMR)
2. External pooler: PgBouncer, Prisma Accelerate, or `@prisma/adapter-pg`
3. Set `connection_limit=1` for serverless instances; scale up with the external pooler

**DataLoader pattern for N+1:**
```ts
// Instead of: for each userId, await db.user.findUnique(userId)
// Batch: await db.user.findMany({ where: { id: { in: userIds } } })
```

Real case: per-pod pool reduced to 15 + a concurrency semaphore + DataLoader dropped p95 from 1.8s to 280ms with no schema change.

---

## Azure Cloud Performance

### Compute Tiers and Cold Starts

| Plan               | Cold start        | Notes                                                        |
|--------------------|-------------------|--------------------------------------------------------------|
| Consumption        | 2–7s (.NET isolated); >10s with heavy DI | Scales to zero after ~20 min; Microsoft now labels it "legacy" for new workloads |
| Flex Consumption   | Near-zero with "always ready" instances | Recommended for new serverless; VNet support                 |
| Premium            | ~200ms (pre-warmed) | Keeps ≥1 instance warm                                       |
| Dedicated/App Service | None (always-on) | No scale-to-zero; rule-based autoscale                       |

**Cheap cold-start mitigation (Consumption plan):** Azure Monitor availability tests pinging every ~5 min + smaller packages + `RUN_FROM_PACKAGE=1` + ReadyToRun compilation.

Linux Consumption plan retires Sept 30, 2028 — new Linux serverless should start on Flex Consumption.

### Container Apps + KEDA Scale-to-Zero

Define `minReplicas: 0` + scale rules. No charge at zero.

50+ KEDA scalers: HTTP concurrency, Service Bus queue length, Event Hubs, CPU/mem. HTTP concurrency recomputed every 15s; cooldown + stabilization windows configurable (e.g., 300s scale-down stabilization).

**Warning:** If ingress is disabled and you set neither `minReplicas≥1` nor a custom rule, the app scales to zero and cannot restart.

**ACA cost crossover:** Above ~40% average monthly utilization, ACA dedicated or AKS reserved becomes cheaper than ACA consumption.

### Messaging Service Selection

| Service      | Latency      | Throughput    | Best for                                           | Key characteristic                     |
|--------------|--------------|---------------|---------------------------------------------------|----------------------------------------|
| Event Grid   | Sub-second   | Moderate      | Reacting to Azure resource events, fan-out notifications | Lightweight routing; ~$0.60/M ops; events ≤1MB |
| Event Hubs   | Variable     | Millions/sec  | Telemetry, logs, clickstream, replay              | It is a log, not a queue               |
| Service Bus  | <5ms (Premium) | High       | Orders, payments, FIFO + sessions + transactions  | Enterprise broker; dead-lettering; duplicate detection |

**All three are at-least-once → consumers must be idempotent.**

**Common combination:** Event Grid reacts → Service Bus guarantees downstream processing; Event Hubs captures telemetry.

**Anti-pattern:** Using Service Bus for everything, or buying Event Hubs throughput units "for the future."

### Databases

| Service                        | Best for                                               | Watch out for                                   |
|--------------------------------|--------------------------------------------------------|-------------------------------------------------|
| PostgreSQL Flexible Server     | Lift-and-shift/modernization; read-heavy workloads with read replicas; burstable tier for dev | Async read replicas (single primary writes only) |
| Cosmos DB                      | Global distribution, guaranteed low latency, multi-region multi-master writes | Cost vs Table/Blob for simple cases; partition-key design is critical |
| Cosmos DB for PostgreSQL (Citus) | Distributed/sharded Postgres; high write scalability, multi-tenant, real-time analytics | Requires choosing a distribution column upfront |

Use burstable (B-series) tier for dev/variable Flexible Server load. Co-locate DB and app in the same region.

### Azure Cache for Redis

**Never use Basic tier in production** (single node, no SLA). Use Standard/Premium/Enterprise (at least C1).

**ConnectionMultiplexer rules (StackExchange.Redis):**
- Use a **single long-lived `ConnectionMultiplexer`** — creating one per request is the #1 Redis mistake
- Set `AbortOnConnectFail=false` and let it auto-reconnect
- Avoid `IsConnected` polling
- Consider separate multiplexers for large vs. small keys

**Pipelining:** Pipeline commands to maximize network throughput. Avoid expensive commands like `KEYS`.

**Clustering (Premium+):**

| Policy               | Characteristics                                            |
|----------------------|------------------------------------------------------------|
| OSS clustering       | Clients connect directly to nodes; best latency/throughput; needs client cluster support |
| Enterprise clustering | Single proxy endpoint; simpler; possible bottleneck       |

Throughput scales ~linearly with shards (e.g., P4 × 10 shards ≈ 2.5M RPS). Redis is single-threaded per node. On Premium, scale out (cluster) before scaling up.

**Note:** Azure Cache for Redis has a published retirement timeline — evaluate Azure Managed Redis for new builds.

### Application Insights Sampling

| Mode             | Behavior                                                      | Recommendation          |
|------------------|---------------------------------------------------------------|-------------------------|
| Adaptive (default) | Dynamically adjusts to `MaxTelemetryItemsPerSecond` target; keeps complete end-to-end transactions | Use in production       |
| Fixed-rate       | Constant %                                                    | Use when you need precise % |
| 100% (no sampling) | Full fidelity                                               | Development/debugging only |

Typical production sampling: 10–25%.

**Distributed tracing caveat:** If a busy server samples down to 0.1% while clients sample 100%, trace correlation breaks. Standardize sampling rates across services.

**Research context (Google Dapper):** Tracing at 100% imposed 1.5% throughput / 16% response time overhead; sampling at 0.01% cut to 0.20% latency / 0.06% throughput.

### VMSS Autoscale

**Use different scale-out and scale-in thresholds.** Microsoft explicitly warns that scaling out at >50% CPU and in at <50% causes oscillation ("flapping"). Thresholds must be "sufficiently different."

**Microsoft's recommended example:** Scale out at >70% CPU, scale in at <20%.

**Best practice ("scale out fast, scale in slow"):**
- Keep a 40–50 percentage-point gap between scale-out and scale-in thresholds
- Set cooldowns longer than instance startup time
- Use 10–15 minute smoothing windows

**Sanity check:** After a scale-out, per-instance CPU should still sit above the scale-in threshold. Example: 4 instances at 75% → adding one gives 75×4/5 = 60% — still above the scale-in threshold of 20%.

When multiple rules trigger, the highest resulting instance count wins.

### Azure Front Door / CDN

**Caching defaults:** If `Cache-Control` isn't present on the origin response, AFD randomly determines a cache duration of 1–3 days. Max: 366 days. AFD honors `private`/`no-cache`/`no-store`.

**Compression (Standard/Premium):** Compresses MIME-type responses between 1 KB and 8 MB. Brotli takes precedence over gzip when both are accepted. On cache-miss, compresses at the POP.

**WAF:** Custom rules evaluate before managed rule sets. DRS 2.0+ uses anomaly scoring (earlier versions block on first match). Policy changes propagate globally in under 20 minutes.

**Split TCP:** AFD terminates client TCP at the nearest POP; connection setup happens over 3–5 short roundtrips instead of 3–5 long roundtrips.

**Note:** AFD documents an in-progress migration from anycast to unicast routing — verify current behavior for latency-sensitive decisions.

### Cost-Performance Tiers

**B-series (burstable):**
- Accumulates CPU credits when below baseline; burns credits above baseline; throttles to baseline when credits depleted
- B1s baseline: ~10% (banks 6 credits/hr); B2s baseline: ~40%
- Credits lost on redeploy to new node; retained on same-node stop/start
- Good for: web servers, dev/test, small DBs with spiky load
- NOT for: sustained high CPU (throttles; D-series wins)

**Spot VMs:**
- Up to ~75–90% cheaper than pay-as-you-go
- 30-second eviction notice
- No high availability guarantees
- For: fault-tolerant, stateless, batch workloads

**Reserved Instances:**
- Up to ~72% discount for 1- or 3-year commitment
- "Use-it-or-lose-it" per hour; stopped VMs still consume reservation hours
- Not available for Spot

---

## Staged Recommendations

**Stage 1 — Measure (week 1):**
Wire up RUM (`onINP` from web-vitals), py-spy/Scalene on hottest Python services, Application Insights with adaptive sampling (start 100% to baseline, then drop to 10–25%). Capture before-numbers: P50/P95/P99 latency, RPS, First Load JS per route, LCP/INP/CLS at 75th percentile, DB connection counts, Function cold-start frequency. Optimize nothing yet.

**Stage 2 — Highest ROI per effort (weeks 2–4):**
- Python: upgrade interpreter to 3.12/3.13; vectorize the worst Pandas loops; move blocking calls off the event loop. Act on any function >5% of total CPU in the profiler.
- Next.js: push `"use client"` to leaves; parallelize server fetches; add Suspense streaming with matched skeletons; set `priority` on LCP images; use `next/font`. Act on any route with First Load JS >300KB or INP >200ms.
- Azure: move latency-sensitive Functions off Consumption to Flex/Premium; add a singleton Redis multiplexer + pipelining; fix Prisma/SQLAlchemy pooling (singleton + external pooler) if you see connection exhaustion.

**Stage 3 — Architecture (weeks 4+):**
Adopt PPR/Cache Components for mixed static+dynamic pages (target TTFB <100ms); KEDA scale-to-zero on ACA for bursty/background workloads; choose the right messaging service per pattern; right-size VMs; apply Reserved Instances for steady baseline + Spot for fault-tolerant batch. Pilot free-threaded Python 3.14t for CPU-bound parallel workloads.

**Thresholds that change the plan:**
- INP stays >200ms after JS work → bottleneck is third-party scripts or hydration; facade/defer them
- Turbopack increases First Load JS in A/B → keep Webpack for prod
- B-series VMs throttle (credits hitting zero) → switch to D-series
- ACA average utilization exceeds ~40%/month → move to dedicated/AKS reserved
- Adaptive sampling breaks trace correlation → standardize sampling rates across services

---

## Caveats

- **Benchmarks are workload-specific.** RPS figures (~3x FastAPI vs Flask), vectorization multipliers (100–740x), and cold-start numbers (2–7s) come from specific tests/configs. Always benchmark your own workload.
- **Version flux.** PPR/Cache Components, Turbopack-as-default, and free-threading all landed across Next.js 16 and Python 3.14 (both Oct 2025). Some behaviors described above changed between v14/v15/v16 — always identify which major version you're on before debugging cache behavior.
- **Free-threading is not universally production-ready.** C-extension ecosystem support is still catching up; importing a non-thread-safe extension silently re-enables the GIL. The 3.13 JIT is a 0–5% win today.
- **Some figures are single-source.** Cosmos-for-PG "500% faster" is one user's report. "Scale out fast, scale in slow" 40–50pt gap and ACA 40%-utilization crossover are best-practice/third-party guidance, not official Microsoft thresholds. The flapping-avoidance principle IS official Microsoft guidance.
- **Microsoft publishes no official ms latency figure for WAF** — treat any specific number skeptically.
