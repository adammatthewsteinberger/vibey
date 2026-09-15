---
name: debugging-and-observability
description: "Comprehensive practitioner guide to debugging, logging, error handling, and production observability (2026): Agans' nine rules, delta debugging, reproducibility imperative, correlation/trace IDs, OpenTelemetry (CNCF graduated May 11 2026), structured logging (slog/Pino/Serilog/structlog), four observability signals (logs/metrics/traces/profiling), eBPF zero-instrumentation telemetry, SLO-based burn-rate alerting, resilience patterns (retries with jitter, circuit breakers, bulkheads), distributed debugging, AI debugging limitations (OpenRCA 11–36%), and language-specific patterns for Python, TypeScript/JavaScript, and Go."
---

# Debugging and Observability — Practitioner Reference Guide (2026)

## Core Principles

**Systematic beats heroic.** The fastest debuggers reproduce the failure, gather data ("quit thinking and look"), bisect the search space, and change one thing at a time. Reproducibility and correlation IDs are the two highest-leverage investments any team can make.

**Observability has consolidated around OpenTelemetry**, which graduated from the CNCF on May 11, 2026. Structured logging is the universal default. The frontier is wide structured events ("Observability 2.0"), continuous profiling as a fourth signal, and eBPF zero-instrumentation telemetry.

**AI helps at the margins but is not trustworthy unsupervised.** Veracode's 2025 study found 45% of AI-generated code introduced OWASP Top 10 vulnerabilities. The OpenRCA benchmark shows the best model solved only 11.34% of real root-cause-analysis cases at publication (rising toward ~36% by 2026). Use AI for triage, localization, and first-draft fixes — gate everything behind tests and human review.

---

## Part 1 — The Debugging Mindset and Process

### The Scientific Method Applied to Debugging

Debugging is hypothesis-driven science: **observe → hypothesize → predict → test → analyze → repeat.** The cardinal sin is "debugging by changing things and seeing what happens" — mutating code based on guesses rather than evidence. Form a falsifiable hypothesis, predict what you'd observe if it were true, then test it.

### David Agans' Nine Rules of Debugging

From *Debugging: The 9 Indispensable Rules* (2002, ISBN 978-0-8144-7457-0) — technology-agnostic, canonical mindset framework:

1. **Understand the system** — Read the manual; know the fundamentals, roadmap, and tools. "If you don't understand some part of the system, that always seems to be where the problem is."
2. **Make it fail** — Reproduce reliably. Do it again, start at the beginning, *stimulate* the failure (don't simulate it), find the uncontrolled condition behind intermittents, and record everything to find the "signature." Never throw away a debugging tool.
3. **Quit thinking and look** — Get data first. "It is a capital mistake to theorize before one has data" (Sherlock Holmes, quoted by Agans). Build instrumentation in, add instrumentation on, but watch out for Heisenberg effects. Guess only to focus the search.
4. **Divide and conquer** — Binary-search the problem space; narrow the range with successive approximation.
5. **Change one thing at a time** — Isolate variables; use a known-good case for comparison. (Most-violated rule along with #6.)
6. **Keep an audit trail** — Write down what you did, in what order, and what happened. (Most-violated rule along with #5.)
7. **Check the plug** — Question assumptions; the simplest cause (unplugged cable, wrong config) is often it.
8. **Get a fresh view** — Ask for help, get an outside perspective (the mechanism behind pair debugging and rubber-ducking).
9. **If you didn't fix it, it ain't fixed** — Verify the fix actually eliminated the cause; intermittent "fixes" that aren't confirmed will recur.

### Psychology of Debugging

Cognitive biases actively sabotage debugging:
- **Confirmation bias** — seeking evidence for your favored hypothesis
- **Anchoring** — fixating on the first explanation
- **Availability heuristic** — blaming the most recently-seen bug class
- **Expert blind spots** — senior engineers skip steps a junior would check (the curse of expertise)

Agans' Rule 8 ("get a fresh view") is the institutional countermeasure.

### Rubber Duck Debugging

Explaining code line-by-line to an inanimate object works through the **self-explanation effect** (Chi, de Leeuw, Chiu & LaVancher, *Cognitive Science* 18(3):439–477, 1994) and the production effect. Articulation forces tacit assumptions explicit, exposing the gap between what you *think* the code does and what it says.

**Caveat:** Widely-circulated "fixes 56% more bugs" claims trace only to low-quality secondary sources with no underlying study. The legitimate evidence base is the self-explanation and metacognition literature, not a controlled debugging trial.

### Timeboxing and Escalation Discipline

Gloria Mark (UC Irvine, 2004) found it takes an average of **23 minutes 15 seconds** to fully return to a task after an interruption. Timebox solo debugging (30–60 minutes) before escalating to pair debugging, and protect debugging sessions from interruption.

### The Reproducibility Imperative

**"If it can't be reproduced it can't be fixed."** Strategies:
- Pin down exact failure conditions (inputs, environment, timing, concurrency, load, data state)
- Build a **minimum reproducible example (MRE)** — often the single most powerful step
- "Works in staging, fails in production" points to environment differences (config, data scale, network)
- Watch for date/time bugs (timezone, DST, leap year, clock skew) and platform-specific bugs (ARM vs x86, runtime/browser versions)
- **Heisenbugs** are concurrency bugs that change behavior when observed

### Divide and Conquer Techniques

- Binary search on code paths
- **`git bisect`** to find the commit that introduced a regression
- Program slicing to find statements affecting a variable
- Mocking dependencies to isolate the failing component
- The "wolf fence" partition-and-test algorithm

### Delta Debugging and Bisection

**Delta debugging** (Andreas Zeller, Saarland University, 1999; formalized in Zeller & Hildebrandt, *IEEE TSE* 28(2):183–200, 2002, DOI 10.1109/32.988498) automates minimization using a binary-search-with-twist algorithm (`ddmin`) to reduce a failing input to a *1-minimal* test case where no single element can be removed.

**Canonical case study:** Mozilla crashed after 95 user actions; the prototype automatically reduced it to **3 relevant actions** and simplified **896 lines of HTML to the single line** that caused the failure, in 139 automated test runs (~35 minutes on a 500 MHz PC).

Modern reducers (Perses, C-Reduce, DustMite) build on delta debugging; it pairs naturally with fuzzing. Worst case is O(n²).

---

## Part 2 — Correlation/Trace IDs: The Distributed Debugging Primitive

**Correlation IDs are the fundamental distributed-debugging primitive.** Every system should propagate them from day one.

- **Without them:** you can see *that* errors spiked
- **With them:** you can see the error came from one tenant on the canary in eu-west-1 with a specific feature flag enabled

Propagate request context through the call chain without threading parameters everywhere using per-language mechanisms:
- **Java:** MDC (Mapped Diagnostic Context)
- **Python:** `contextvars`
- **Node.js:** `AsyncLocalStorage`
- **Go:** `context` package

The **W3C TraceContext** standard propagates `traceparent`/`tracestate` headers across service boundaries.

**High-cardinality attributes are essential for root cause.** High-cardinality fields let you answer "is this affecting everyone, or only a specific subset?" — distinguishing a generic error spike from "the error spike is coming from user:8675309 on the canary deployment in eu-west-1 who has the new-checkout-flow feature flag enabled."

---

## Part 3 — Structured Logging

### Philosophy and Design

Logs are the primary data source when production bugs can't be reproduced locally. Watch the **Heisenberg problem**: excessive logging changes the timing/behavior of the system being observed and can itself cause performance issues on hot paths.

**Structured over unstructured logging is the modern default.** JSON is the lingua franca. The rule: **the message field is a static, greppable string; variable data goes in structured fields.**

### Log Levels

| Level | Purpose |
|-------|---------|
| TRACE | Finest detail |
| DEBUG | Diagnostic |
| INFO | Business events |
| WARN | Recoverable/unusual |
| ERROR | Failures needing attention |
| FATAL/CRITICAL | Process death |

Run production at INFO or WARN. Support **dynamic level adjustment at runtime without restart.**

Common misuse: logging everything at INFO, or using ERROR for recoverable conditions (causing alert fatigue).

### What to Log / Not Log

**Log:**
- Entry/exit of critical operations
- The *why*, not just the *what*
- Request/response metadata (method, path, status, duration)
- Full exception stack traces with the original cause chain (don't swallow `initCause`)
- Third-party API calls (endpoint, status, latency, retries)
- Slow queries
- Security events (authn/authz outcomes — mandatory for compliance)

**Never log:**
- Passwords, tokens, API keys
- SSNs, credit-card/PCI data, HIPAA PHI
- Use field-level masking/scrubbing (`ReplaceAttr` in Go slog, redaction in Pino, Serilog enrichers)
- Avoid high-frequency hot-path logging

### Good Log Record Fields

A complete log record carries: timestamp (UTC), level, message, service/component, correlation/trace ID, user/tenant context, environment, host/pod, and additional structured fields. The emerging standard for field naming is **OpenTelemetry semantic conventions** (e.g., `http.method`, `http.status_code`, `exception.type`/`exception.message`/`exception.stacktrace`).

### Sampling at Volume

- **Head-based:** decide at ingestion
- **Tail-based:** decide after seeing the outcome — keeps all errors
- **Reservoir/structured downsampling:** configurable rates per category
- Always sample errors at 100% regardless of base rate

### Logging Frameworks by Language (2026)

**Java/JVM:**
- SLF4J (API) + Logback is the modern default
- Log4j 2 for high-performance async appenders
- Avoid `java.util.logging`
- Lombok `@Slf4j`, MDC for context

**Python:**
- stdlib `logging` (baseline)
- **structlog** — best-in-class for structured logging
- **loguru** — best developer experience
- `python-json-logger` for JSON output
- `contextvars` for propagation

**Node.js:**
- **Pino** — fastest (JSON-first, low overhead; benchmarks show roughly 7× faster than Winston using worker-thread transport)
- **Winston** — most popular
- Never `console.log` in production
- `AsyncLocalStorage` for context propagation

**Go:**
- **`log/slog`** (standard library since Go 1.21, largest stdlib addition since Go 1) — now the recommended default
- Frontend `Logger` + pluggable `Handler` (TextHandler/JSONHandler)
- Benchmarks slower than **zap** (Uber) and **zerolog** (zero-allocation) for hot-path work; the Go team optimized for the ≤5-attribute case (>95% of real usage)
- Use zap/zerolog only for hot-path allocation-sensitive logging; logrus is legacy

**.NET/C#:**
- `Microsoft.Extensions.Logging` abstraction with `ILogger<T>` + DI
- **Serilog** — the leading structured choice (rich sinks, enrichers)
- NLog — mature alternative

**Rust:**
- `log` (API) + env_logger for simple cases
- **tracing** (Tokio) — the async-aware ecosystem standard

**Ruby:** stdlib Logger, Ougai, semantic_logger, Rails logger

**PHP:** **Monolog** (PSR-3) is the standard

### Log Aggregation and Storage

**Shipping patterns:** sidecar (Fluentd/Fluent Bit), DaemonSet shippers, application-direct

**Fluent Bit** — lightweight, high-performance C-based shipper  
**Fluentd** — heavier, plugin-rich Ruby-based aggregator

**Backends:**
- **ELK/EFK stack** — Elasticsearch + Logstash/Beats/Fluentd + Kibana
- **OpenSearch** — AWS's Apache-2.0 fork of Elasticsearch
- **Grafana Loki** — label-indexed, no full-text index, LogQL; the cost-efficient choice
- **Splunk** — enterprise dominant, SPL
- **Datadog Logs**
- **Azure Monitor/Log Analytics** — KQL
- **AWS CloudWatch Logs** — Logs Insights, metric filters

Cost management: tiered hot/warm/cold retention and selective indexing.

---

## Part 4 — OpenTelemetry (CNCF Graduated May 11, 2026)

**OpenTelemetry graduated from the CNCF on May 11, 2026** (announced May 21, 2026 at the Observability Summit), confirming its status as the de facto observability standard — the second-highest-velocity CNCF project after Kubernetes.

**Scale:** Over 12,000 contributors from over 2,800 companies. In the past twelve months, the OTel JavaScript API package was downloaded more than 1.36 billion times and the Python API package surpassed 1.3 billion downloads, both setting new monthly download records in April 2026.

**What OTel provides:**
- Unified traces, metrics, logs, and (now) profiling under one SDK
- Zero-code auto-instrumentation (Java agent, Python auto-instrumentation, Node require hook)
- **OTel Collector** — filter/batch/route between app and backend
- **OTel Operator** — Kubernetes webhook-injected instrumentation
- **Profiling signal** — reached public **alpha** in 2026; profiles added to OTLP in v1.3.0; bi-directional links from metrics/traces/logs to the exact line of code consuming a resource

**Adopt OTel now.** Auto-instrument for traces, emit structured JSON logs with trace IDs, propagate correlation IDs from day one. This is the highest-leverage observability investment.

---

## Part 5 — The Four Observability Signals

The four signals complement each other:

| Signal | Purpose |
|--------|---------|
| **Metrics** | Numeric time-series — *alert you* |
| **Logs** | Discrete events with context — *explain what happened* |
| **Traces** | Request flow across services — *show where* |
| **Continuous Profiling** | CPU/memory/goroutine flame graphs in production — *show how much* |

### Distributed Tracing

A trace = trace ID + spans (span ID, parent, attributes, events, status).

Sampling strategies: head-based, tail-based (decide after outcome), adaptive.

**Backends:** Jaeger, Zipkin, Grafana Tempo, Honeycomb, Datadog APM, Azure Monitor, AWS X-Ray.

Always include trace ID + span ID in every log record for log↔trace correlation. The `otelslog` bridge (Go), WinstonInstrumentation, and Serilog Activity enrichment do this automatically.

### Continuous Profiling

Always-on, aggregated CPU/memory profiling in production for trend analysis and deploy-correlated regression detection. Overhead is typically under 1% at production sampling rates.

**Tools:** Parca (CNCF), Grafana Pyroscope, Google Cloud Profiler, Datadog Continuous Profiler.

### APM and Error Tracking

**APM:** Datadog APM (market leader), New Relic, Dynatrace, Elastic APM, Honeycomb (wide events, high cardinality, BubbleUp).

**Error tracking:**
- **Sentry** — dominant; unified errors+traces+replays+profiling+logs; free tier: 5,000 errors
- **Rollbar** — focused error tracking, aggressive grouping; free: 5,000 events/month
- **Bugsnag** — mobile/gaming strength, stability scores
- **Raygun** — deployment-correlated, RUM, user-impact prioritization

**Sentry Seer:** Runs RCA → Solution → Code Generation using issue context, traces, logs, and profiles. Vendor-reported "94.5% accuracy / 38,000+ issues helped" — not independently audited.

**AI observability assistants:**
- **Datadog Watchdog RCA** — automatically identifies causal relationships between symptoms and pinpoints root cause; no configuration required
- **Dynatrace Davis AI** — deterministic, causation-based engine performing automatic fault-tree analysis across a real-time dependency graph; correlates events sharing a root cause into a single "problem"

---

## Part 6 — eBPF for Production Debugging

eBPF runs sandboxed programs in the Linux kernel for observability without kernel-module changes or app instrumentation — **"zero-instrumentation observability."**

**Key tools:**
- **Pixie** (CNCF) — auto-captures HTTP/gRPC/DNS/MySQL/Postgres/Redis without instrumentation libraries
- **Cilium Hubble** — network observability
- **Tetragon** (Cilium sub-project, CNCF) — security observability and kernel-level runtime enforcement; typically <1% overhead
- **bpftrace** — scripting interface for ad-hoc eBPF programs
- **kubectl-trace** — run bpftrace programs on Kubernetes nodes

In 2025, AWS EKS adopted Cilium as a default CNI. The OTel eBPF profiling agent (donated by Elastic) brought whole-system continuous profiling.

**Limitations:** Linux-only, kernel-version requirements, steep expertise curve.

---

## Part 7 — SLO-Based Burn-Rate Alerting

**The core tension:** too few alerts miss problems; too many cause alert fatigue. The SRE philosophy is **symptom-based alerting** on user-visible behavior, not cause-based alerting.

### SLO-Based Multi-Window Burn-Rate Alerting (Google SRE Workbook, Ch. 5)

**Burn rate** = how fast you consume the error budget relative to the rate that would exactly exhaust it over the SLO window.

**Recommended multi-window, multi-burn-rate setup (30-day SLO window):**

| Trigger | Burn Rate | Long Window | Short Window | Action |
|---------|-----------|-------------|--------------|--------|
| Page immediately | ~14.4 | 1 hour | 5 min | 2% budget consumed |
| Ticket | ~6 | 6 hours | 30 min | 5% budget consumed |
| Track | ~1 | 3 days | 6 hours | 10% budget consumed |

The short secondary window (1/12 of the long window) reduces false positives.

**Example threshold:** If your error rate is fine but burn rate exceeds ~14.4 on a 1-hour window, page immediately; if a 1% error rate sits on a 99.9% SLO, that's a 10× burn — treat it as an active incident.

ML-based anomaly detection (Datadog Watchdog, Dynatrace Davis) supplements static thresholds.

**OpsGenie sunset notice:** End of sale June 4, 2025; full end of support April 5, 2027, after which all OpsGenie data is deleted. Migrate to PagerDuty, incident.io, Jira Service Management, or Compass.

---

## Part 8 — Error Handling: Design and Patterns

### Philosophy

The fundamental question is propagate vs. handle locally. "Let it crash" (Erlang/Elixir — supervised processes restart cleanly) suits systems with strong supervision and isolation; defensive handling suits monoliths without it.

Distinguish **recoverable vs. unrecoverable** and **fail-fast vs. fail-safe.**

**Most dangerous anti-pattern:** catching an exception and doing nothing (swallowing). Preserve the original cause and stack trace — the "poisoned exception" problem is re-throwing without chaining.

### Result Types vs. Exceptions

Functional approaches make errors part of the type signature:
- Rust: `Result<T,E>`
- Go: `(value, error)`
- Haskell: `Either`
- Scala: `Try`

Exception-based languages (Java, Python, C#) separate the happy path but risk invisible control flow. **Railway-oriented programming** (Scott Wlaschin) chains fallible operations via Result types.

Libraries bringing result types to exception languages: Vavr (Java), **neverthrow** (TypeScript), OneOf/FluentResults (.NET).

### Error Type Design

Taxonomy: system, application, user, transient (retryable), permanent (not retryable). Structured errors carry both a human message and machine-readable fields (code, status, context).

**RFC 9457 (Problem Details for HTTP APIs, July 2023, obsoletes RFC 7807):** The standard for machine-readable HTTP errors, using media type `application/problem+json` with members `type` (URI identifying the problem type), `title`, `status`, `detail`, and `instance`, plus custom extension members.

Critically: "Problem details are not a debugging tool for the underlying implementation" — don't leak internals in API responses.

### Resilience Patterns (from Michael Nygard, *Release It!*, 2007/2018)

#### Retry with Exponential Backoff and Jitter

Formula: `delay = random(0, min(cap, base × 2^attempt))`

AWS's Marc Brooker showed **full jitter** dramatically reduces synchronized retry storms ("thundering herd") vs. no-jitter backoff: "In the case with 100 contending clients, we've reduced our call count by more than half." AWS SDKs use jittered exponential backoff with a 20-second cap and a token-bucket retry quota.

**Rules:**
- Only retry idempotent operations and transient errors (429, 503, network timeouts)
- Never retry 401/403
- Typical caps: 3–5 max attempts, 10–30s max delay

#### Circuit Breaker (Nygard)

State machine: **closed → open → half-open**. Trips on a failure threshold to stop hammering a failing dependency, preventing cascade and resource exhaustion.

**Reference implementations:**
- **Resilience4j** — JVM de facto standard (after Netflix Hystrix entered maintenance mode in 2018)
- **Polly** — .NET
- Istio/Envoy outlier detection (mesh-level, no code changes)
- sony/gobreaker (Go)
- pybreaker (Python)

Resilience4j nesting: `Retry(CircuitBreaker(RateLimiter(TimeLimiter(Bulkhead(fn)))))`.

#### Bulkhead

Isolate resource pools so one dependency's failure doesn't drain all threads/connections.

#### Additional Patterns

- **Timeout:** never wait forever; budget cascading timeouts in call chains
- **Fallback:** graceful degradation — cached/default/partial response
- **Idempotency keys:** for safe retries; distributed idempotency checks
- **Saga:** compensating transactions for distributed recovery
- **Health checks:** liveness vs. readiness vs. startup probes

### HTTP API Error Handling

Map status codes correctly: 2xx success, 3xx redirect, 4xx client error, 5xx server error.

Recurring decisions: 404 vs 200-with-error-body; 403 vs 404 for security (hide existence); 422 vs 400 for validation. Provide field-level validation error lists. Keep error response shapes consistent across microservices. Separate detailed *internal* errors (logged) from safe *external* messages (no stack traces, SQL, or connection strings in API responses).

---

## Part 9 — Distributed Debugging

### Why Distributed Debugging Is Hard

The **fallacies of distributed computing** each create a debugging challenge: network is reliable, latency is zero, bandwidth is infinite, network is secure, topology is static, one administrator, transport cost is zero, network is homogeneous.

**Partial failures** (a service that is up but slow, degraded, or returning wrong answers) are harder than binary up/down. **Clock skew** means timestamps from different services can't be totally ordered without vector clocks or hybrid logical clocks. Delivery semantics (at-most-once / at-least-once / exactly-once) determine retry safety.

### Debugging Microservices

- Service dependency maps (Istio/Linkerd mesh observability, APM-generated maps)
- Distributed tracing as the critical RCA tool ("the trace shows you exactly where a request failed")
- Event-driven debugging via message correlation IDs and dead-letter-queue analysis (Kafka, RabbitMQ, Service Bus)
- gRPC status codes and `google.rpc.Status` error details

### Production Debugging Techniques

- Feature flags to isolate code paths
- Canary/dark launches as controlled experiments
- Trace-ID correlation to find the *source* vs. *amplifier* of a failure
- Log-based event reconstruction
- Correlating error spikes with deploys/config/traffic

**Profiling tools:**
- Heap dumps: Eclipse MAT (JVM), dotMemory (.NET)
- Thread dumps: jstack (deadlock/starvation)
- CPU profiling: async-profiler (JVM), py-spy (Python), pprof (Go), perf (Linux)
- Network: tcpdump, Wireshark

**Kubernetes:** `kubectl exec`, **ephemeral debug containers** (`kubectl debug`), pod describe/events, cross-pod log streaming.

### Chaos Engineering

Chaos engineering as proactive debugging — built on **Netflix's Chaos Monkey** (invented 2011, open-sourced 2012, Apache 2.0). The Simian Army extended it: Latency Monkey injects network latency, Chaos Gorilla simulates AZ failure, Chaos Kong a whole Region.

**Principles of Chaos Engineering** (principlesofchaos.org):
1. Build a hypothesis around steady-state behavior
2. Vary real-world events
3. Run experiments in production
4. Automate to run continuously
5. **Minimize blast radius**

**Tools:**
- **AWS Fault Injection Service (FIS)** — managed, real fault injection with CloudWatch-alarm stop conditions and auto-rollback
- **Azure Chaos Studio** — GA at Ignite November 2023; service-direct and agent-based faults
- **Gremlin** — enterprise platform with granular blast-radius control, safe halt/rollback, reliability scoring

---

## Part 10 — AI Debugging Limitations

### OpenRCA Benchmark (The Hard Evidence)

**OpenRCA benchmark** (ICLR 2025, Microsoft/Tsinghua — 335 real failure cases across three enterprise systems with 68+ GB of telemetry):
- Best model at publication (Claude 3.5): solved only **11.34%** of failure cases
- Best model by 2026 (Claude Opus 4.6): approximately **36%**

This is real progress but remains far below human reliability and far below coding benchmarks.

### Security Risks

**Veracode's 2025 GenAI Code Security Report** tested 100+ LLMs across 80 tasks:
- **45% of AI-generated code introduced an OWASP Top 10 vulnerability**
- Failure rates: 86% for XSS (CWE-80), 88% for log injection (CWE-117); Java worst at 72%
- "Increasing the scale of the model does not improve security" — a structural problem
- CodeRabbit's analysis found AI-produced code carries a **2.74× higher vulnerability rate** than human-written code

### What AI Is Good For

- Log summarization and triage
- Error localization
- Rubber-ducking (explaining code)
- First-draft fixes for well-understood bug classes
- Autofix of scanning alerts (GitHub Copilot Autofix, Sentry Seer)

### What AI Misses

- Context-dependent bugs
- Distributed and timing bugs
- Hardware-level bugs
- Security-sensitive code paths (especially authentication, cryptography, input handling, data access)

### Safe AI Debugging Practices

- Gate all AI-generated fixes behind tests and human review
- Mandate SAST, dependency, and secret scanning on every commit *at the point of code generation*
- Never merge AI-generated security-adjacent code without mandatory human security review regardless of confidence score
- Treat vendor-reported accuracy metrics (Sentry's "94.5% accuracy", GitHub Copilot's "two-thirds remediated") as directional, not audited

---

## Part 11 — Language-Specific Debugging Patterns

### Python

- **`pdb`/`ipdb`**: commands `n` (next), `s` (step), `c` (continue), `p` (print), `bt` (backtrace), `l` (list), `q` (quit)
- **`breakpoint()`** builtin (Python 3.7+) — invokes pdb by default
- **py-spy** — sampling profiler that attaches to running processes without restart
- **objgraph** — reference graphs for memory leak investigation
- **mypy/pylint/pyflakes** — static analysis
- `logging.exception()` for full context including stack trace
- asyncio debug mode (`loop.set_debug(True)`)
- `raise X from Y` chaining; `contextlib.suppress`
- EAFP (Easier to Ask Forgiveness than Permission) vs LBYL (Look Before You Leap) — Python idiom prefers EAFP

### TypeScript/JavaScript

- **Chrome DevTools** — breakpoints, scope, network, performance, memory profiler
- **VS Code launch.json** — configurable debug sessions
- Source maps to map minified → source
- Extended console methods: `.error`, `.warn`, `.table`, `.group`, `.time`, `.trace`, `.assert`
- `--async-stack-traces` for better async debugging
- **React/Vue/Redux DevTools** browser extensions
- React error boundaries for component-level error isolation
- **Replay.io** — deterministic browser session recording; CI Agent auto-records every Playwright/Cypress test run and posts root-cause analysis as PR comment
- `unhandledRejection`/`uncaughtException` handlers for process-level error capture
- **neverthrow** — result types for TypeScript without exceptions

### Go

- **Delve** (`dlv debug/test/attach/core`) — the Go debugger
- **`go tool pprof`** — CPU/heap/goroutine/mutex/block flame graphs
- **`go test -race`** / **ThreadSanitizer** — race condition detection
- Runtime deadlock detector (built-in)
- **goleak** — goroutine leak detection in tests
- **`log/slog`** — standard library structured logging (Go 1.21+)
- **`go vet`/staticcheck** — static analysis
- `errors.Is`/`errors.As` (Go 1.13+), `%w` wrapping, sentinel and custom error types
- The `(value, error)` idiom — the Go team withdrew `if err != nil` reduction proposals in 2024–2025; the pattern will stay

### Java/JVM

- Diagnostic JVM flags: `-XX:+HeapDumpOnOutOfMemoryError`, `-XX:+PrintGCDetails`
- jstack (thread dumps), jmap (heap), jstat (statistics), jconsole/JMX
- VisualVM and Java Mission Control for live profiling
- SLF4J + Logback + MDC (Mapped Diagnostic Context)
- Java 14+ helpful NPE messages name the null variable
- Anti-pattern: wrapping checked exceptions in RuntimeException without context

### .NET/C#

- Visual Studio debugger (IntelliTrace historical debugging, pinned variables)
- `dotnet-dump`/`dotnet-trace`/`dotnet-counters`
- PerfView, BenchmarkDotNet
- WinDbg + SOS extension
- Serilog + `Microsoft.Extensions.Logging`
- OpenTelemetry for .NET

---

## Part 12 — Advanced Debugging Tools

### Interactive Debuggers

Power moves underused by most engineers:
- **Conditional breakpoints** — break only when a condition holds; invaluable for intermittent bugs
- **Data breakpoints/watchpoints** — break when a memory location changes; for tracking mutations
- **Remote debugging** — attach to a running process on a server/container (mind security and JIT-deoptimization overhead in production)

### Time-Travel / Deterministic-Replay Debugging

- **rr** (Mozilla, Linux) — record execution once, replay deterministically
- **WinDbg TTD** (Windows Time Travel Debugging)
- **UDB** (Undo)
- **Replay.io** (JavaScript/web) — records a deterministic browser session; CI Agent posts root-cause analysis and suggested fix as PR comment; documented case: traced a React race condition to root cause in 7 minutes

### Snapshot Debugging

**Lightrun / Rookout** — inject logpoints/breakpoints into running production code without restart or source changes.

### Memory Debugging

Leak detection via heap profiling and memory-growth monitoring. Common causes: lingering references, JS event-listener leaks, unintended statics.

**Tools:** Eclipse MAT (JVM), dotMemory (.NET), AddressSanitizer/MemorySanitizer/Valgrind (C/C++), `gc`/objgraph (Python reference cycles), Chrome DevTools heap snapshots (V8).

### Concurrency Debugging

- **ThreadSanitizer** — C/C++/Go/Rust race detection; `go test -race`
- Helgrind (Valgrind tool)
- SpotBugs (Java static analysis)
- jstack thread dumps (JVM deadlock)
- Go's runtime deadlock detector
- **goleak** — goroutine leak detection

Async pitfalls: Promise swallowing, `await` in loops, event-loop blocking. Connection-pool exhaustion is a frequent concurrency-induced production failure.

### Network and Database Debugging

**Network:** curl/httpie, Postman/Insomnia, Wireshark/tcpdump, `openssl s_client` for TLS chains, dig/nslookup for DNS, grpcurl for gRPC.

**Database/query debugging:**
- `EXPLAIN`/`EXPLAIN ANALYZE` for query plans (missing indexes, table scans, join strategy)
- **N+1 detection:** Bullet (Rails), Django Debug Toolbar, Hibernate SQL logging
- Deadlock logs (MySQL) and `pg_locks`+`pg_stat_activity` (Postgres)
- Enable SQL logging in ORMs (Hibernate, EF, SQLAlchemy, ActiveRecord) to defeat the ORM transparency problem

---

## Part 13 — Testing for Debuggability

Tests are debugging tools: a focused failing test pinpoints exactly what broke.

- Use descriptive names (`should_throw_when_X`)
- Prefer one logical assertion per test
- Write assertion messages that explain the failure without reading the test
- Good assertion libraries: AssertJ (Java), FluentAssertions (.NET), pytest's introspecting asserts, Jest's diff output
- Snapshot testing catches unexpected output changes

### Mutation Testing

Finds tests that pass even when code is broken:
- PIT (Java)
- Stryker (JS/TS)
- mutmut (Python)

Mutation score is a signal of test suite quality.

### Property-Based Testing

Generates edge cases automatically and **shrinks** failures to a minimal example (automating MRE creation):
- Hypothesis (Python)
- fast-check (JS)
- QuickCheck (Haskell)

Stateful variants find state-dependent bugs.

---

## Part 14 — Customer Issue Triage

### Bug Report Requirements

A good bug report captures: steps to reproduce, expected vs. actual behavior, environment, frequency, severity, business impact, customer screenshots/logs.

**Triage questions:** All users or some? Did something change? Is there a workaround? What is the urgency?

### Severity Classification (Industry-Standard)

| Priority | Meaning |
|----------|---------|
| P0 | Production down |
| P1 | Major feature broken |
| P2 | Workaround exists |
| P3 | Minor |
| P4 | Enhancement |

SLA turnaround scales with severity. The "can we reproduce it?" gate drives prioritization.

### Root Cause Analysis

**Five Whys** (Toyota/Ohno) — drills from symptom to systemic cause. Known limitation: assumes a single linear causal chain. Complex software systems fail through **networks of contributing conditions**, not single root causes.

Complementary techniques:
- **Fishbone/Ishikawa** — categorize causes
- **Fault Tree Analysis** — top-down deductive
- **FMEA** — proactive risk assessment
- **Change analysis** — correlate the bug's appearance with recent code/config/infra/data changes (usually the fastest path to a "smoking gun")

Avoid "fix the symptom not the cause" — verify the proposed root cause explains *all* observed symptoms.

### Fix, Test, Prevent

1. Write a failing regression test *before* fixing (TDD fix discipline)
2. Decide minimal patch vs. refactor
3. Verify in production via canary + monitoring + customer confirmation
4. Address the systemic cause: add observability, validation, error handling, tests
5. Maintain a blameless culture

---

## Part 15 — Observability 2.0

**Charity Majors (Honeycomb)** defines observability via control theory: "the ability to ask any question of your systems — understand any internal state just by observing it from the outside — without having to predict that question in advance." This is about **unknown-unknowns**, requiring **high cardinality and high dimensionality** with no pre-aggregation.

**Observability 1.0:** three pillars (metrics, logs, traces) in separate tools; cost driven by cardinality.

**Observability 2.0:** a single source of truth of **arbitrarily-wide structured events** stored in a columnar database, from which metrics/traces are derived; cost driven by traffic/architecture, scaling with business value. "You can derive metrics from these wide events. And you can't go any other direction."

**Observability-Driven Development (ODD):** engineers design the right logs, metrics, and spans *before* a bug happens. Missing observability is "dark debt." Test that your instrumentation actually emits correctly.

**Caveat:** "Observability 2.0" is a contested framing advanced primarily by Majors/Honeycomb (a vendor with a commercial interest in wide-event tooling). The three-pillars model remains widely and effectively used.

---

## Quick Reference: Decision Thresholds

| Situation | Action |
|-----------|--------|
| Cannot reliably reproduce a bug | Stop fixing; invest in reproduction infrastructure (record/replay, better logging) |
| Burn rate >14.4 on 1-hour window | Page immediately — treat as active incident |
| AI fix touches auth/crypto/input handling/data access | Mandatory human security review regardless of confidence |
| Solo debugging >30–60 minutes | Rubber-duck or pair (Agans' Rule 8) |
| Error rate 1% on 99.9% SLO | That's 10× burn rate — active incident |

---

## Caveats on Sources

- **Vendor-reported metrics are not independent.** Sentry's "94.5% accuracy," GitHub Copilot Autofix's timing improvements, and Pino's "7× faster than Winston" all come from vendors and controlled harnesses — treat as directional.
- **The "rubber duck fixes 56% more bugs" claim is unsupported.** No underlying study. The legitimate basis is the self-explanation literature (Chi et al., 1994).
- **Interruption-cost figures vary.** "23 minutes 15 seconds" is Gloria Mark's well-cited finding; downstream "50–100% more bugs" multipliers circulate in practitioner blogs without consistently traceable primary studies.
- **OpenRCA scores are evolving.** The 11.34% (2025, Claude 3.5) vs ~36% (2026, Claude Opus 4.6) gap reflects model improvement; some practitioners argue the benchmark's structure may overstate real-world readiness.
- **"Observability 2.0"** is a contested vendor framing; the three-pillars model remains widely and effectively used.
- **Chaos Monkey founding year:** Wikipedia dates invention to 2011, open-source release to 2012; some sources say 2010.
- Tool comparisons reflect the 2026 landscape; verify current pricing and feature tiers before committing.
