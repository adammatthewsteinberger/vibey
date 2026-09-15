---
name: vibey-bootstrap-typescript
description: "Use when consuming an vibey-bootstrap Python backend (v4.0.0) from TypeScript/Next.js, or porting its framework-agnostic primitives to TypeScript. vibey-bootstrap is pure Python with no npm distribution. Covers the exact HTTP contract (x-api-key endpoints → 401/429, Graph-style webhook handshake/202/401/400, health probes, /api/metrics shape) with typed App Router client code, plus native TS reimplementations: structured JSON logging, correlation via AsyncLocalStorage, mask_* helpers, in-memory counters, TokenBucket, constant-time compare, and HMAC-SHA256 action tokens that interoperate byte-for-byte with Python's tokens module. Also includes the master env-var reference (v1–v3), testing notes (AZURE_BOOTSTRAP_ALLOW_RESET, USE_MOCK_BOOTSTRAP), and troubleshooting. Triggers on calling a Python vibey-bootstrap backend from Next.js, validationToken webhook, DATABASE_URL/outbox patterns, or interoperable HMAC tokens."
---

> **vibey-bootstrap** is the library formerly published as `azure-bootstrap` (renamed in 4.0.0: package `vibey-bootstrap`, import `vibey_bootstrap`, CLI `vibey-bootstrap`; `azbootstrap` remains as a deprecated alias). Feature-tier labels below (v2 primitives, v3 modules) are historical and unchanged.

# Azure Bootstrap — TypeScript/Next.js Integration & Pattern Ports

> **`vibey-bootstrap` is a pure Python package** with **no JavaScript/TypeScript
> distribution** — you cannot `npm install` or `import` it from a Next.js app. This
> skill covers two distinct, legitimate things: (Part 7) calling a Python backend that
> *uses* this library from Next.js over its HTTP surface, and (Part 8) reimplementing
> the library's framework-agnostic primitives natively in TS.

## 7. TypeScript/Next.js — A: HTTP client integration

This documents the **exact HTTP contract** a Python backend exposes when it wires up
`vibey_bootstrap.auth`, `health`, `metrics`, and `fastapi_middleware`, then gives typed
Next.js (App Router) client code to consume it.

> Conventions assumed below: backend base URL in `process.env.BACKEND_URL`; the API
> key in **server-only** `process.env.BACKEND_API_KEY` (never `NEXT_PUBLIC_*`).

### 7.1 API-key-protected endpoints

**Contract:** header `x-api-key` (the backend reads it via FastAPI `Header` and passes
it to `verify_api_key_header`, env `API_KEY`). On mismatch → **`401`** with
`{"detail": "Unauthorized"}`. If the backend env var is unset, the check is **fail-open
by default** (passes) unless the backend opted into strict mode.

Keep the key server-side. Use a Route Handler (or Server Action) as a proxy so the
browser never sees it:

```ts
// app/api/admin/reload/route.ts
import { NextResponse } from "next/server";

export async function POST() {
  const res = await fetch(`${process.env.BACKEND_URL}/api/admin/reload`, {
    method: "POST",
    headers: { "x-api-key": process.env.BACKEND_API_KEY! },
    cache: "no-store",
  });
  if (res.status === 401) return NextResponse.json({ error: "unauthorized" }, { status: 401 });
  if (res.status === 429) return NextResponse.json({ error: "rate_limited" }, { status: 429 });
  return NextResponse.json(await res.json(), { status: res.status });
}
```

```ts
// lib/backend.ts — a small typed wrapper, server-side only
export async function callBackend<T>(path: string, init: RequestInit = {}): Promise<T> {
  const res = await fetch(`${process.env.BACKEND_URL}${path}`, {
    ...init,
    headers: { "x-api-key": process.env.BACKEND_API_KEY!, ...init.headers },
    cache: "no-store",
  });
  if (!res.ok) throw new Error(`backend ${path} -> ${res.status}`);
  return res.json() as Promise<T>;
}
```

### 7.2 Graph-style webhook

`install_graph_webhook_route` exposes one `POST` path with two modes:

| Request | Response |
|---|---|
| `POST {path}?validationToken=<t>` (subscription handshake) | `200` + **plaintext** body `<t>` (not JSON) |
| `POST {path}` body `{"value":[{ "clientState", "subscriptionId", "resourceData": { "id" } }]}` | `202` (accepted) |
| clientState missing/mismatch, or endpoint unconfigured | `401` (empty body) |
| rate-limited | `429` (empty body) |
| malformed JSON | `400` |

`clientState` is checked **constant-time** against `GRAPH_WEBHOOK_CLIENT_STATE`;
dedup is keyed on `(subscriptionId, resourceData.id)`. Payload types:

```ts
// lib/webhook-types.ts
export interface GraphNotification {
  clientState?: string;
  subscriptionId?: string;
  resourceData?: { id?: string };
}
export interface GraphNotificationBatch { value: GraphNotification[]; }
```

If you instead want a Next.js Route Handler to *receive* such webhooks (a parallel TS
implementation of the same contract):

```ts
// app/api/webhooks/email/route.ts
import { NextRequest, NextResponse } from "next/server";
import { timingSafeEqual } from "node:crypto";
import type { GraphNotificationBatch } from "@/lib/webhook-types";

function safeEqual(a?: string, b?: string): boolean {
  if (!a || !b) return false;
  const ab = Buffer.from(a), bb = Buffer.from(b);
  return ab.length === bb.length && timingSafeEqual(ab, bb);
}

export async function POST(req: NextRequest) {
  // 1. validation handshake — echo the token as plaintext
  const token = req.nextUrl.searchParams.get("validationToken");
  if (token) return new NextResponse(token, { status: 200, headers: { "content-type": "text/plain" } });

  // 2. live notification
  let batch: GraphNotificationBatch;
  try { batch = await req.json(); } catch { return new NextResponse(null, { status: 400 }); }

  const expected = process.env.GRAPH_WEBHOOK_CLIENT_STATE;
  for (const n of batch.value ?? []) {
    if (!safeEqual(n.clientState, expected)) return new NextResponse(null, { status: 401 });
    const messageId = n.resourceData?.id;
    if (messageId) queueBackgroundWork(messageId); // your dedup + dispatch
  }
  return new NextResponse(null, { status: 202 });
}
```

### 7.3 Health probes

`check_*` helpers each return `{"status": "ok" | "not_configured" | "error", ...}`
(no HTTP 5xx for an unconfigured optional dependency). A typical `/health/ready` body:

```ts
export interface Probe { status: "ok" | "not_configured" | "error"; message?: string; mock?: boolean; }
export interface ReadyResponse {
  status: "ok"; app_config: Probe; app_insights: Probe; app_insights_logging?: Probe;
}
```

```ts
// app/status/page.tsx — server component
export default async function StatusPage() {
  const res = await fetch(`${process.env.BACKEND_URL}/health/ready`, { cache: "no-store" });
  const ready = (await res.json()) as ReadyResponse;
  const healthy = res.ok && Object.values(ready).every(
    (v) => typeof v !== "object" || v.status !== "error");
  return <main>Backend: {healthy ? "✅ healthy" : "⚠️ degraded"}</main>;
}
```

### 7.4 `/api/metrics`

`build_metrics_snapshot()` JSON shape (sections are present only if the backend has
that module wired):

```ts
export interface MetricsSnapshot {
  latency: Record<string, { count: number; errors: number; slow: number;
                            p50: number; p95: number; p99: number; max: number; last_seen?: number }>;
  alert_counters: Record<string, number>;
  ai_usage?: { by_deployment: Record<string, unknown>;
               totals: { calls: number; total_tokens: number; cost_usd: number; rate_limit_events: number } };
  bootstrap_initialized?: boolean;
  last_sb_settle_age_seconds?: number | null;
}
```

### 7.5 Correlation IDs & rate limiting

- The Python middleware does **not** emit an `X-Correlation-ID` response header —
  correlation lives in server-side context vars. If you want end-to-end correlation,
  generate an id in Next.js, send it as a custom header, and have the backend read it
  into `correlation_scope(...)`.
- `429` responses carry **empty bodies** by design. Honor `Retry-After` if present and
  back off; don't parse the body for budget state.

## 8. TypeScript/Next.js — B: porting the patterns to TypeScript

These are **equivalent reimplementations**, not bindings — drop them into a Next.js
app that has no Python backend. They mirror the Python semantics closely; the token
helper in 8.6 is deliberately **wire-compatible** with the Python side.

### 8.1 Structured JSON logging (mirrors `JsonLogFormatter`)

```ts
// lib/logger.ts
const SECRET_KEYS = new Set(["authorization","api_key","apikey","password","token",
  "secret","client_secret","connection_string"]);

function maskSecrets(o: Record<string, unknown>): Record<string, unknown> {
  const out: Record<string, unknown> = {};
  for (const [k, v] of Object.entries(o)) out[k] = SECRET_KEYS.has(k.toLowerCase()) && v ? "***" : v;
  return out;
}

export function log(level: "INFO"|"WARNING"|"ERROR"|"DEBUG",
                    logger: string, message: string, extra: Record<string, unknown> = {}) {
  const line = { timestamp: new Date().toISOString(), level, logger, message, ...maskSecrets(extra) };
  (level === "ERROR" ? console.error : console.log)(JSON.stringify(line));
}
```

### 8.2 Correlation context (mirrors `correlation_scope` via `AsyncLocalStorage`)

```ts
// lib/correlation.ts
import { AsyncLocalStorage } from "node:async_hooks";
import { randomUUID } from "node:crypto";

type Ctx = Record<string, string>;
const als = new AsyncLocalStorage<Ctx>();

export function correlationScope<T>(fn: () => T, fields: Ctx = {}): T {
  const ctx: Ctx = { correlation_id: fields.correlation_id ?? randomUUID().replace(/-/g, "").slice(0, 12), ...fields };
  return als.run(ctx, fn);
}
export const getCorrelationId = () => als.getStore()?.correlation_id;
export const getContext = () => als.getStore() ?? {};
```

### 8.3 Masking helpers (mirror `mask_*`)

```ts
export const maskApiKey = (s?: string) => (!s || s.length < 4 ? "***" : `***${s.slice(-4)}`);
export const maskBearer = (t?: string) => (t?.startsWith("Bearer") ? "Bearer ***" : "***");
export const maskEmail = (e?: string) => {
  if (!e || !e.includes("@")) return "***";
  const [local, domain] = e.split("@");
  return `***${local.slice(-2)}@${domain}`;
};
```

### 8.4 In-memory counters (mirror `bump_counter` / `counter_snapshot`)

```ts
const counters = new Map<string, number>();
export const bumpCounter = (name: string, n = 1) => counters.set(name, (counters.get(name) ?? 0) + n);
export const counterSnapshot = () => Object.fromEntries(counters);
```

### 8.5 Token bucket (mirrors `ratelimit.TokenBucket` + presets)

```ts
// lib/token-bucket.ts
export class TokenBucket {
  private tokens: number; private last = performance.now() / 1000;
  constructor(private budget: number, private refillPerSecond: number) { this.tokens = budget; }
  consume(n = 1): boolean {
    const now = performance.now() / 1000;
    this.tokens = Math.min(this.budget, this.tokens + (now - this.last) * this.refillPerSecond);
    this.last = now;
    if (this.tokens >= n) { this.tokens -= n; return true; }
    return false;
  }
}
export const webhookBucket = () => new TokenBucket(240, 4);   // 240 burst, 4/s
export const adminBucket   = () => new TokenBucket(30, 0.5);  // 30 burst, 0.5/s
```

> In-process buckets only protect a single Node instance. On Vercel/serverless or
> multi-replica deployments, back the limiter with Redis/Upstash for a shared budget.

### 8.6 HMAC-SHA256 action tokens — **interoperable with Python `tokens`**

Same wire format as `vibey_bootstrap.tokens` / the Service-Bus resubmit token:
`base64url(json).base64url(hmac_sha256)`, payload sorted-keys with `exp` (unix
seconds) and `act`. A token minted here verifies in Python and vice-versa — so a
Next.js admin UI can issue a `dlq_resubmit` token the Python consumer accepts.

```ts
// lib/action-token.ts
import { createHmac, timingSafeEqual } from "node:crypto";

const b64url = (b: Buffer) => b.toString("base64url");
// Python uses json.dumps(sort_keys=True, separators=(",",":")) — match it exactly:
function canonicalJson(obj: Record<string, unknown>): string {
  const keys = Object.keys(obj).sort();
  return `{${keys.map((k) => `${JSON.stringify(k)}:${JSON.stringify(obj[k])}`).join(",")}}`;
}

export function issueActionToken(secret: string, action: string,
    ttlSeconds = 86400, payload: Record<string, unknown> = {}): string {
  const body = { ...payload, exp: Math.floor(Date.now() / 1000) + ttlSeconds, act: action };
  const payloadBytes = Buffer.from(canonicalJson(body), "utf-8");
  const sig = createHmac("sha256", secret).update(payloadBytes).digest();
  return `${b64url(payloadBytes)}.${b64url(sig)}`;
}

export function verifyActionToken(secret: string, token: string, expectedAction: string): Record<string, unknown> {
  const [p, s] = token.split(".");
  if (!p || !s) throw new Error("malformed token");
  const payloadBytes = Buffer.from(p, "base64url");
  const provided = Buffer.from(s, "base64url");
  const expected = createHmac("sha256", secret).update(payloadBytes).digest();
  if (provided.length !== expected.length || !timingSafeEqual(provided, expected)) throw new Error("signature mismatch");
  const body = JSON.parse(payloadBytes.toString("utf-8"));
  if (body.act !== expectedAction) throw new Error("wrong action");
  if (typeof body.exp !== "number" || body.exp < Math.floor(Date.now() / 1000)) throw new Error("expired");
  return body;
}
```

> **Interop caveats.** Byte-compatibility depends on the JSON serialization matching
> Python's `json.dumps(sort_keys=True, separators=(",",":"))`. The helper above
> reproduces sorted keys and compact separators, but keep payload values to JSON
> primitives (strings, ints, bools) — non-ASCII strings and floats can serialize
> differently across runtimes and will break the signature. Use the **same shared
> secret** on both sides (a Key Vault secret).

### 8.7 Constant-time compare (mirrors `compare_secrets`)

```ts
import { timingSafeEqual } from "node:crypto";
export function compareSecrets(a?: string, b?: string): boolean {
  if (!a || !b) return false;
  const ab = Buffer.from(a, "utf-8"), bb = Buffer.from(b, "utf-8");
  return ab.length === bb.length && timingSafeEqual(ab, bb);
}
```

## 9. Appendices

### 9.1 Master environment-variable reference

| Variable | Default | Area |
|---|---|---|
| `APPLICATIONINSIGHTS_CONNECTION_STRING` | — | telemetry (v1) |
| `AZURE_APP_CONFIGURATION_CONNECTION_STRING` | — | App Config (v1) |
| `AZURE_APPCONFIG_ENDPOINT` | — | App Config via AAD (health) |
| `AZURE_KEY_VAULT_URL` | — | Key Vault (v1) |
| `AZURE_TENANT_ID` / `AZURE_CLIENT_ID` / `AZURE_CLIENT_SECRET` | — | `build_credential` |
| `LOG_LEVEL` | `INFO` | logging |
| `DEBUG_LOGGING_ENABLED` | off | DEBUG second gate |
| `USE_MOCK_BOOTSTRAP` | off | mock bootstrap / probes |
| `FUNCTIONS_WORKER_RUNTIME` | — | Azure Functions detection |
| `CONSOLE_LOGGING_ENABLED` | on | transport flag |
| `APP_INSIGHTS_LOGGING_ENABLED` | off | transport flag |
| `SUMO_LOGIC_LOGGING_ENABLED` | off | transport flag |
| `SUMO_LOGIC_COLLECTOR_URL` (+ `_TOKEN`, `_SOURCE_CATEGORY`, `_SOURCE_HOST`, `_FIELDS`, `_BATCH_SIZE`, `_MAX_BATCH_BYTES`, `_GZIP_THRESHOLD`, `_FLUSH_INTERVAL`, `_MAX_BUFFER`, `_TIMEOUT`) | see primitives skill | Sumo transport |
| `PANTHER_LOGGING_ENABLED`, `PANTHER_API_HOST`, `PANTHER_LOG_SOURCE_*` | off | Panther transport (v3) |
| `FILE_LOGGING_ENABLED`, `FILE_LOG_PATH`, `FILE_LOG_ROOT`, `FILE_LOG_ROTATION`, … | off | local file transport (v3) |
| `BLOB_LOGGING_ENABLED`, `BLOB_*` | off | Blob log transport (v3) |
| `SQL_LOGGING_ENABLED`, `SQL_LOG_DSN`, `SQL_LOG_TABLE` | off | SQL log transport (v3) |
| `NOSQL_LOGGING_ENABLED`, `NOSQL_LOG_URI`, `NOSQL_LOG_DATABASE` | off | NoSQL log transport (v3) |
| `ADX_LOGGING_ENABLED`, `ADX_CLUSTER_URI`, `ADX_DATABASE` | off | ADX log transport (v3) |
| `EVENTHUBS_LOGGING_ENABLED`, `EVENTHUB_FQNS`, `EVENTHUB_NAME` | off | Event Hubs log transport (v3) |
| `DATABASE_URL` | — | SQLAlchemy / outbox (v3 `[db]`) |
| `ACS_CONNECTION_STRING`, `ACS_SENDER_ADDRESS` | — | ACS email (v3 `[email]`) |
| `NOSQL_URI`, `NOSQL_DATABASE` | — | documentdb client (v3) |
| `BUILD_VERSION` / `APP_VERSION`, `GIT_SHA`, `POD_NAME`, `POD_NAMESPACE`, `NODE_NAME` | — | AKS build info (v3) |
| `LEADER_ELECTION_CONFIGMAP` | — | AKS leader election (v3) |
| `SERVICE_BUS_TRANSPORT_TYPE` | `amqp` | `amqp` or `websocket` (v3) |
| `API_KEY` | — | `verify_api_key_header` |
| `GRAPH_WEBHOOK_CLIENT_STATE` | — (required for webhooks) | webhook auth |
| `DEV_ALERTS_ENABLED`, `DEV_ALERT_RECIPIENTS`, `ALERT_DEDUP_WINDOW_SECONDS`, `ALERT_MAX_PER_HOUR`, `ALERT_ESCALATE_AFTER`, `ALERT_ESCALATE_WINDOW_SECONDS`, `ALERT_CRITICAL_SUBJECT_PREFIX` | see Part 5 | `alerts` dispatcher |
| `HEARTBEAT_INTERVAL_SECONDS` / `WATCHDOG_*` | see Part 5 | heartbeat |
| `AI_TPM_LIMIT[_<DEPLOYMENT>]`, `AI_COST_ALERT_HOURLY_DOLLARS`, `AI_COST_ALERT_DAILY_DOLLARS`, `AI_HIGH_USAGE_TOKENS_HOURLY` | — | `openai` tracker |
| `AZURE_BOOTSTRAP_ALLOW_RESET` | off | **test-only** (see 9.2) |

### 9.2 Testing note

Subpackages with global state (counters, latency histograms, alert dispatcher,
transports, webhook dedup, …) expose `reset_state()` / `_reset_*` helpers **gated by
`AZURE_BOOTSTRAP_ALLOW_RESET=1`**. The test suite sets it once in `test/conftest.py`;
**production code must never set it.** For local/dev runs without Azure, set
`USE_MOCK_BOOTSTRAP=true` to make `ensure_bootstrap()` a no-op and the health/identity
probes return `{"status":"ok","mock":true}`.

### 9.3 Troubleshooting

| Symptom | Cause / fix |
|---|---|
| Sumo transport silently does nothing | `SUMO_LOGIC_COLLECTOR_URL` unset, or `[sumologic]` extra (`requests`) not installed → `make_sumo_logic_handler()` returns `None` by design. |
| v3 transport silently does nothing | Required env vars unset or pip extra missing — factories return `None` (soft no-op); check `list_transports()`. |
| `ImportError` from `get_db` / `drain_outbox` | Install the `[db]` extra (`sqlalchemy`, `alembic`). |
| `ImportError` from `request_with_retry` | Install the `[http]` extra (`requests`). |
| App Insights never "upgrades" | The connection string wasn't present in env at phase 2 and isn't in App Config either; verify `APPLICATIONINSIGHTS_CONNECTION_STRING`. |
| `ImportError` from `install_graph_webhook_route` / `fastapi_rate_limit` | Install the `fastapi` extra. |
| DEBUG logs missing despite `LOG_LEVEL=DEBUG` | Also set `DEBUG_LOGGING_ENABLED=true` (the second gate). |
| `LoggingExtraConflictError` | An `extra={}` key collides with a reserved `LogRecord` attribute (e.g. `name`, `msg`, `args`) — rename it. |
| `ConfigurationError` from webhook | `GRAPH_WEBHOOK_CLIENT_STATE` is unset; the endpoint refuses all entries (`401`). |

### 9.4 Further reading

- `README.md` — overview + extras matrix
- `docs/USAGE.md` — complete usage guide (Python + TypeScript)
- `examples/README.md` — numbered reading order (01 → 46 + e2e_*)
- `CHANGELOG.md` — release-by-release surface
- `MIGRATING-FROM-V1.md` — v1 → v2 adoption
- `MIGRATING-TO-V3.md` — v4.0.0 opt-in features (additive, no breaking changes)
