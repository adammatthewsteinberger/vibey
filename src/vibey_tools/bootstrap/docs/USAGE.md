# Using `vibey-bootstrap` — Complete Usage Guide

> A practitioner's guide to consuming **vibey-bootstrap** (formerly **azure-bootstrap**,
> v4.0.0) from a real codebase — in **Python** and in **TypeScript / Next.js**.

### v3.0.0 additions (2026-06-29)

3.0.0 adds **seven optional logging transports** (`panther`, `file`, `blob`, `sql`,
`nosql`, `adx`, `event_hubs`), a **DB/outbox/email** stack, **hardened HTTP**,
**AKS runtime helpers**, **governance**, and a **`vibey-bootstrap scaffold` CLI**.
Everything is opt-in behind pip extras. See [MIGRATING-TO-V3.md](../MIGRATING-TO-V3.md).

| Extra | Purpose |
|-------|---------|
| `panther`, `bloblog`, `sqllog`, `nosqllog`, `adxlog`, `eventhubslog` | Individual transports |
| `logging-all` | All transport dependencies |
| `db` | SQLAlchemy + Alembic + outbox |
| `email` | ACS sender |
| `http`, `http-async` | Sync requests + optional httpx |
| `documentdb` | Mongo/Cosmos access |
| `governance`, `aks` | Budget guard + pod runtime (stdlib) |


## 0. Read this first

`vibey-bootstrap` solves the **logging ↔ configuration circular dependency** every
Azure Functions / container app hits at startup (you need logging to report config
loading, but App Insights logging needs config to initialize). On top of that v1
core, v2 adds a large, opt-in, framework-agnostic "cross-cutting layer": structured
logging, correlation, tracing, counters, tiered alerts, an error vocabulary, ingress
hardening, Service Bus plumbing, webhook auth, AI usage tracking, health probes, and
a v2.1 logging-transport layer (console / App Insights / Sumo Logic).

> [!IMPORTANT]
> **`vibey-bootstrap` is a pure Python package.** It is published to PyPI and has
> **no JavaScript/TypeScript distribution** — you cannot `npm install` or `import` it
> from a Next.js app. Accordingly, the TypeScript/Next.js half of this guide covers
> two distinct, legitimate things:
>
> 1. **[Part 7 — HTTP client integration](#7-typescriptnextjs--a-http-client-integration):**
>    calling a Python backend (that *uses* this library) from Next.js over its HTTP
>    surface — webhook routes, `x-api-key` endpoints, health probes, `/api/metrics`.
> 2. **[Part 8 — Porting the patterns](#8-typescriptnextjs--b-porting-the-patterns-to-typescript):**
>    reimplementing the library's framework-agnostic primitives natively in TS
>    (structured JSON logging, correlation via `AsyncLocalStorage`, masking, counters,
>    token bucket, **HMAC action tokens that interoperate byte-for-byte** with Python).

**Compatibility:** Python **≥ 3.11**. Distribution: `pip install vibey-bootstrap`
(PyPI, MIT). Every v1 public symbol is preserved byte-identical across v2.

### Table of contents

1. [Installation & extras](#1-installation--extras)
2. [Python: the v1 core (4-phase bootstrap)](#2-python-the-v1-core-4-phase-bootstrap)
3. [Python: v2 Tier 1 primitives (always-on, stdlib-only)](#3-python-v2-tier-1-primitives-always-on-stdlib-only)
4. [Python: v2.1 transports (logging routing)](#4-python-v21-transports-logging-routing)
5. [Python: v2 Tier 2 / Tier 3 subpackages (opt-in)](#5-python-v2-tier-2--tier-3-subpackages-opt-in)
6. [Python: three end-to-end recipes](#6-python-three-end-to-end-recipes)
7. [TypeScript/Next.js — A: HTTP client integration](#7-typescriptnextjs--a-http-client-integration)
8. [TypeScript/Next.js — B: porting the patterns to TypeScript](#8-typescriptnextjs--b-porting-the-patterns-to-typescript)
9. [Appendices](#9-appendices)

---

## 1. Installation & extras

```bash
pip install vibey-bootstrap                       # core only
pip install 'vibey-bootstrap[fastapi]'            # one extra
pip install 'vibey-bootstrap[fastapi,servicebus,sumologic]'   # several
pip install 'vibey-bootstrap[all]'                # the aggregate extra
```

### Core dependencies (always installed)

```text
azure-appconfiguration-provider>=1.0.0
azure-keyvault-secrets>=4.7.0
azure-identity>=1.15.0
azure-monitor-opentelemetry>=1.2.0
opentelemetry-api>=1.22.0
# Pinned minimums for CVE remediation:
azure-core>=1.38.0     # CVE-2026-21226
filelock>=3.20.3       # CVE-2025-68146, CVE-2026-22701
urllib3>=2.7.0         # CVE-2026-21441 + CVE-2026-44431/44432
```

### Optional extras matrix

Source of truth: [`pyproject.toml`](../pyproject.toml). Many extras are empty
markers (`[]`): the code is **stdlib-only** and already importable without the
extra — the extra exists for discoverability / intent, and only pulls real
dependencies where a third-party package is genuinely required.

| Extra | Pulls | When you need |
| --- | --- | --- |
| `[alerts]` | stdlib only | Tiered alert dispatcher + global excepthooks |
| `[health]` | core deps | App Config + App Insights health probes |
| `[fastapi]` | `fastapi` | Request middleware, webhook route, rate-limit dep |
| `[heartbeat]` | stdlib only | Background heartbeat + consumer watchdog |
| `[config-refresh]` | stdlib only | Dynamic `LOG_LEVEL` refresh via App Config |
| `[servicebus]` | `azure-servicebus` | DLQ digest, growth alarm, consumer wrapper, sb_lock |
| `[openai]` | stdlib only | AI usage tracker (SDK-agnostic) |
| `[tokens]` | stdlib only | HMAC action tokens |
| `[scheduler]` | `apscheduler` | NCRONTAB parser |
| `[metrics]` | stdlib only | `/api/metrics` aggregator |
| `[retry]` | `tenacity` | Pre-configured retry wrappers |
| `[ingress]` | stdlib only | 4-gate attachment classifier |
| `[pdf-safety]` | `pypdf` | PDF action stripping |
| `[ratelimit]` | stdlib only | TokenBucket |
| `[notify]` | stdlib only | Two-tier notification builders + throttle |
| `[subscription]` | stdlib only | Renewal loop pattern |
| `[identity]` | core deps | `build_credential` (Workload Identity preferred) |
| `[auth]` | (pair with `[fastapi]`) | Graph webhook + API-key helpers |
| `[sb-lock]` | (pair with `[servicebus]`) | Message lock auto-renewer |
| `[audit]` | stdlib only | Audit-log conventions |
| `[failclose]` | stdlib only | Env-var fail-closed-vs-open helpers |
| `[transports]` | stdlib only | Logging transport registry (console / App Insights / Sumo Logic) |
| `[sumologic]` | `requests` | Buffered POST to a Sumo Logic HTTP Source (urllib3 Retry, gzip, Retry-After) |
| `[panther]` | `requests` | Panther log ingest transport |
| `[bloblog]` | `azure-storage-blob` | NDJSON append/block blob logging |
| `[sqllog]` | `sqlalchemy` | Relational DB log shipper |
| `[nosqllog]` | `pymongo` | MongoDB / Cosmos (Mongo API) document shipper |
| `[adxlog]` | `azure-kusto-*` | Azure Data Explorer streaming ingest |
| `[eventhubslog]` | `azure-eventhub` | Event Hubs live-tail producer |
| `[logging-all]` | all transport deps | Every logging sink at once |
| `[db]` | `sqlalchemy`, `alembic` | Session factory + migrations + outbox |
| `[email]` | `azure-communication-email` | ACS transactional email |
| `[http]` | `requests` | Sync HTTP client with retry |
| `[http-async]` | `httpx` | Async HTTP client |
| `[documentdb]` | `pymongo` | DocumentDB client factory |
| `[governance]` | stdlib only | Budget guard + usage tracking |
| `[aks]` | stdlib only | AKS runtime helpers + leader election |
| `[all]` | everything above | All extras at once |
| `[dev]` / `[test]` / `[docs]` | tooling | Development, CI, and the documentation-site toolchain |

```bash
# Common combinations
pip install 'vibey-bootstrap[alerts,fastapi,health]'
pip install 'vibey-bootstrap[servicebus,sb-lock,retry,heartbeat]'
pip install 'vibey-bootstrap[all]'
```

---

## 2. Python: the v1 core (4-phase bootstrap)

### The problem and the solution

Configuration loading wants logging to report progress; App Insights logging wants
configuration to initialize. The library breaks the cycle in four phases:

1. **Console logging** — works immediately (always).
2. **Telemetry from env** — try App Insights from `APPLICATIONINSIGHTS_CONNECTION_STRING`.
3. **Configuration load** — Azure App Configuration + Key Vault → `os.environ`.
4. **Telemetry upgrade** — if the connection string only arrived via config, upgrade to App Insights now.

### Quick start (the canonical pattern)

```python
import os
from vibey_bootstrap import initialize_application, get_bootstrap_logger

logger = get_bootstrap_logger(__name__)     # works before bootstrap completes
config_repo = initialize_application()       # runs all four phases
# Every App Config + Key Vault value is now in os.environ:
db_host = os.getenv("DATABASE_HOST")
```

### Configuration precedence & the local-override rule

Lookup order, highest priority first:

1. **Environment variables** (`os.environ`) — local overrides always win
2. **In-process cache** (prior `get_value()` results)
3. **Azure App Configuration** (Key Vault references auto-resolved)
4. **Key Vault** (direct, via the secrets repository)
5. **Default values**

`load_to_environ()` **never overwrites an existing `os.environ` key** — so anything
set by `local.settings.json` (or your shell) survives, and only *new* remote keys are
added. App Config can store Key Vault *references* (a JSON `{"uri": "...vault.../secrets/..."}`);
the provider resolves them transparently, so `os.getenv("DATABASE_PASSWORD")` returns
the actual secret, not the URI.

### Configuration sources: two ways to run

**Enterprise** — App Configuration + Key Vault (`local.settings.json` for a Function app):

```json
{
  "Values": {
    "AZURE_APP_CONFIGURATION_CONNECTION_STRING": "Endpoint=https://...;Id=...;Secret=...",
    "AZURE_KEY_VAULT_URL": "https://myvault.vault.azure.net/",
    "AZURE_APP_CONFIG_LABEL": "dev"
  }
}
```

**Simple** — environment variables only. The library falls back gracefully when
App Configuration is not configured, so the same code runs locally and in Azure:

```json
{
  "Values": {
    "DATABASE_HOST": "localhost",
    "DATABASE_NAME": "mydb",
    "API_KEY": "your-api-key"
  }
}
```

```python
# local.settings.json sets: USE_MOCK_DB = "true"
# App Config has:          USE_MOCK_DB = "false"
# After bootstrap:         os.getenv("USE_MOCK_DB") → "true"   (local wins)
```

### API reference — entry points

```python
from vibey_bootstrap import (
    initialize_application, get_bootstrap_logger,
    ensure_bootstrap_logging, create_enhanced_config_repository,
)
```

| Symbol | Signature | Behavior |
|---|---|---|
| `initialize_application` | `(secrets_repository: SecretsRepositoryInterface \| None = None) -> EnhancedConfigRepositoryInterface` | Runs the 4-phase bootstrap; loads all config to `os.environ`; caches the repo for `refresh_setting()`. Raises `RuntimeError` on unrecoverable failure. |
| `get_bootstrap_logger` | `(name: str) -> logging.Logger` | A logger usable immediately; auto-configures bootstrap logging on first call. |
| `ensure_bootstrap_logging` | `() -> None` | Idempotent bootstrap-logging setup. |
| `create_enhanced_config_repository` | `(app_config_connection_string=None, secrets_repository=None, auto_load_to_environ=False) -> EnhancedConfigRepositoryInterface` | Factory for the config repository. |

### API reference — classes

```python
from vibey_bootstrap import (
    ApplicationBootstrap, BootstrapLogger, ExtraFieldsFormatter,
    TelemetryManager, telemetry_manager,
    EnhancedConfigRepository, SecretsRepository,
)
```

- **`ApplicationBootstrap(secrets_repository=None)`** — orchestrator. `.initialize()`
  runs the four phases and returns the repo; `.get_config_repository()`,
  `.is_bootstrap_completed()`.
- **`BootstrapLogger`** — `.configure_bootstrap_logging(level=None)` (class method;
  level falls back to `LOG_LEVEL` env, then `INFO`).
- **`ExtraFieldsFormatter`** — `logging.Formatter` that appends `extra={}` fields to
  each line. (v1 lives in `services.bootstrap_logging`; a v2 variant lives in
  `vibey_bootstrap.logging` — see Part 3.)
- **`TelemetryManager` / `telemetry_manager`** (singleton) —
  `.configure(connection_string=None, allow_reconfigure=False) -> bool` and
  `.try_upgrade_from_config(config_repository) -> bool`. Best-effort: always falls
  back to console logging rather than raising.
- **`EnhancedConfigRepository`** — key methods:

  | Method | Purpose |
  |---|---|
  | `get_value(key, default=None) -> str \| None` | env → cache → App Config → Key Vault → default |
  | `get_secret_value(key, default=None) -> str \| None` | direct Key Vault lookup |
  | `get_all_values() -> dict[str, str]` | merged view (env wins) |
  | `load_to_environ() -> int` | populate `os.environ`; returns count of **new** keys |
  | `refresh() -> None` | clear cache + reload (used by `refresh_setting`) |
  | `get_repository_metrics() -> dict` | availability + counts |
  | `is_app_config_available()` / `is_key_vault_available()` | feature probes |

- **`SecretsRepository(vault_url=None)`** — `get_secret`, `set_secret`,
  `delete_secret`, `list_secrets`, `is_available` (reads `AZURE_KEY_VAULT_URL`).

### Interfaces (DI / type hints) and exceptions

```python
from vibey_bootstrap import (
    ApplicationBootstrapInterface, BootstrapLoggerInterface,
    TelemetryManagerInterface, EnhancedConfigRepositoryInterface,
    SecretsRepositoryInterface,
    RepositoryError, ConfigurationError, KeyVaultError,   # ConfigurationError, KeyVaultError subclass RepositoryError
)
```

### v1 environment variables

| Variable | Used by | Purpose |
|---|---|---|
| `APPLICATIONINSIGHTS_CONNECTION_STRING` | `TelemetryManager` | App Insights telemetry |
| `AZURE_APP_CONFIGURATION_CONNECTION_STRING` | `EnhancedConfigRepository` | App Configuration endpoint |
| `AZURE_APPCONFIG_ENDPOINT` | health probe / AAD auth | App Config endpoint (credential-based) |
| `AZURE_KEY_VAULT_URL` | `SecretsRepository` | Key Vault endpoint |
| `LOG_LEVEL` | bootstrap + telemetry logging | `DEBUG`/`INFO`/`WARNING`/`ERROR` (default `INFO`) |
| `FUNCTIONS_WORKER_RUNTIME` | bootstrap logging | presence triggers Azure-Functions log setup |

### v2 top-level re-exports (additive)

The v1 surface (`initialize_application`, `get_bootstrap_logger`,
`create_enhanced_config_repository`, `telemetry_manager`, and the rest of the
original `__all__`) is preserved byte-identical. The most common v2 primitives
are also re-exported from the top-level namespace:

```python
from vibey_bootstrap import (
    # Logging
    configure_logging, correlation_scope, get_correlation_id, set_correlation_id,
    mask_api_key, mask_email_address, mask_secrets_in_dict, sanitize_for_log,
    # Tracing + counters
    traced, latency_snapshot, bump_counter, counter_snapshot,
    # Bootstrap
    ensure_bootstrap, bootstrap_initialized, load_local_settings, refresh_setting,
    # Exception hierarchy
    PipelineError, UnrecoverableError, TransientError,
    InvalidMessageError, RateLimitError, NetworkError, is_unrecoverable,
    # Soft-fail + phases + validation
    soft_fail, soft_fail_with, SoftFailResult,
    run_phase, run_phases, PhaseResult,
    validate_message, MessageSchema, queue_message_schema,
    # Path / security
    sanitize_path_segment, confine_to_root, compare_secrets,
)
```

Everything else is reachable via its subpackage (e.g.
`from vibey_bootstrap.alerts import alert_dev_team`). The authoritative list is
[`vibey_bootstrap/__init__.py`](../vibey_bootstrap/__init__.py).

---

## 3. Python: v2 Tier 1 primitives (always-on, stdlib-only)

Everything here is importable from the top-level `vibey_bootstrap` namespace (or its
subpackage) with **no extra installed**.

### Structured logging

```python
from vibey_bootstrap import configure_logging, JsonLogFormatter
from vibey_bootstrap.logging import (
    ExtraFieldsFormatter, effective_log_level, env_flag, debug_logging_enabled,
)

configure_logging(
    format_string="%(asctime)s %(levelname)s %(name)s %(message)s",  # default
    silence_defaults=True,        # silence noisy third-party loggers (urllib3, azure.*, …)
    extra_noisy_loggers=(),       # add your own to silence
)
```

`configure_logging()` is **idempotent** (it `force`-replaces handlers), installs the
`ExtraFieldsFormatter` + a `CorrelationFilter`, and sets the root level via
`effective_log_level()`. The level honors `LOG_LEVEL`, but **`DEBUG` requires a second
gate**: `DEBUG_LOGGING_ENABLED` must also be truthy, else it clamps to `INFO` (defends
against a stray manifest leaking DEBUG into prod). In DEBUG, an `extra={}` key that
collides with a reserved `LogRecord` attribute raises `LoggingExtraConflictError`.

- **`JsonLogFormatter(*, ensure_ascii=False, mask_extras=True)`** — one JSON object
  per line. Fields: `timestamp` (ISO-8601 UTC), `level`, `logger`, `message`,
  `exception` (only with `exc_info`), plus every non-reserved `extra={}` field
  (correlation IDs included). Secret-keyed extras are redacted via
  `mask_secrets_in_dict`. **Never raises** — falls back to a minimal document. Use it
  for remote ingestion (this is what the Sumo Logic transport uses).

### Correlation context

```python
from vibey_bootstrap import correlation_scope, get_correlation_id, set_correlation_id
from vibey_bootstrap.logging import CorrelationFilter

with correlation_scope("req-123", user_id="u-456", email_id="e-789") as cid:
    logger.info("processing")   # log line auto-includes correlation_id, user_id, email_id
```

`correlation_scope(correlation_id=None, **fields)` pushes context for the `with` block
(generates a 12-char hex id when `None`), and `CorrelationFilter` attaches every set
context var as a record attribute. Built on `contextvars`, so it is **async- and
task-safe**. `get_correlation_id()` / `set_correlation_id(value)` read/write outside a
scope.

### Masking & sanitization

```python
from vibey_bootstrap import (
    mask_api_key, mask_bearer_token, mask_email_address,
    mask_secrets_in_dict, safe_json_dumps, sanitize_for_log,
)
from vibey_bootstrap.logging import register_secret_keys, content_preview
```

| Function | Behavior |
|---|---|
| `mask_api_key(s)` | `***` if `None`/<4 chars, else `***{last4}` |
| `mask_bearer_token(t)` | `Bearer ***` if it starts with `Bearer`, else `***` |
| `mask_email_address(e)` | `***{last2-local}@{domain}` |
| `mask_secrets_in_dict(d)` | shallow copy; redacts **truthy** values at ~20 secret-keyed names (`authorization`, `x-api-key`, `api_key`, `password`, `token`, `client_secret`, `connection_string`, …) |
| `register_secret_keys(*names)` | extend the secret-key allowlist at runtime |
| `sanitize_for_log(v, max_len=256)` | strip control chars → `?`, truncate |
| `safe_json_dumps(obj)` | JSON with `default=repr`; never raises |
| `content_preview(text, max_len=500)` | truncate a body for preview |

### Tracing & counters

```python
from vibey_bootstrap import traced, latency_snapshot, bump_counter, counter_snapshot

@traced(operation="reports.process", alert_on_error="error",
        sensitive_args=("api_key",), slow_threshold_seconds=2.0)
def process(report_id: str, api_key: str) -> dict: ...
```

`@traced` works on **sync or async** functions (auto-detected). It records latency on
every call (success and exception), logs entry/exit **only at DEBUG** (the hot path
skips `inspect.signature` when DEBUG is off), masks `sensitive_args` (and anything that
"looks" sensitive) in logs, and — if the `alerts` subpackage is importable — fires a
slow-budget `WARN` and/or an `alert_on_error` alert. With no alerts extra it silently
degrades to log-only. `latency_snapshot()` returns
`{operation: {count, errors, slow, p50, p95, p99, max, last_seen}}`. `bump_counter(name, n=1)`
is thread-safe and never raises; `counter_snapshot()` returns a copy.

### Bootstrap helpers

```python
from vibey_bootstrap import (
    ensure_bootstrap, bootstrap_initialized, load_local_settings, refresh_setting,
)
```

| Function | Behavior |
|---|---|
| `ensure_bootstrap()` | lazy, idempotent wrapper over `initialize_application()`; short-circuits when `USE_MOCK_BOOTSTRAP` is truthy; re-raises on failure after logging |
| `bootstrap_initialized() -> bool` | process-local flag — wire into `/health/ready` |
| `load_local_settings(path="local.settings.json") -> int` | load Azure-Functions-style settings; skips `_`-prefixed keys; never overwrites existing env; returns count |
| `refresh_setting(*names)` | re-read named keys from the cached App Config repo into `os.environ`; best-effort, no-op before `initialize_application()` |

### Error vocabulary

```python
from vibey_bootstrap import (
    PipelineError, UnrecoverableError, TransientError,
    InvalidMessageError, RateLimitError, NetworkError, is_unrecoverable,
)
```

`PipelineError` is the base. `UnrecoverableError` (→ `InvalidMessageError`,
`OversizedAttachmentError`, `MalformedAttachmentError`, `ZipBombError`,
`UpstreamResourceMissing`) means "dead-letter it." `TransientError` (→ `RateLimitError`,
`NetworkError`, `AuthenticationError`) means "retry/back off." `is_unrecoverable(exc)`
is a single classifier the retry/soft-fail/consumer helpers all consult.

### Resilience — soft-fail & phases

```python
from vibey_bootstrap import (
    soft_fail, soft_fail_with, SoftFailResult, run_phase, run_phases, PhaseResult,
)

# Degrade gracefully with a fallback value:
res = soft_fail_with(fetch_thumbnail, blob_id, fallback=None,
                     operation="thumbnail.fetch", counter_name="thumbnail.failed")
if res.degraded:
    logger.warning("thumbnail unavailable", extra={"reason": res.reason})

# Context-manager form:
with soft_fail(operation="enrich") as state:
    record["extra"] = enrich(record)
if state["degraded"]:
    ...

# Sequential pipeline that never aborts mid-way:
results = run_phases([("download", download), ("parse", parse), ("index", index)])
```

`soft_fail_with(...)` re-raises `UnrecoverableError` by default
(`re_raise_unrecoverable=True`) — set `False` to swallow everything in `catch`.
`run_phase`/`run_phases` **never re-raise**; each bumps `{namespace}.{name}.ok` /
`.failed` counters and returns `PhaseResult(name, ok, value, exception, elapsed_seconds)`.

### Validation

```python
from vibey_bootstrap import validate_message, queue_message_schema, MessageSchema

schema = queue_message_schema(
    required_fields=("correlation_id",),
    path_field="blob_path", path_required_prefix="reports/",
)
data = validate_message(payload, schema)   # raises InvalidMessageError on violation
```

Building a schema with a `path_field` automatically adds path-traversal defense
(forbidden substrings `..` and `://`). On failure `validate_message` bumps a counter
and raises `InvalidMessageError` (an `UnrecoverableError` — so consumers dead-letter).

### Path safety

```python
from vibey_bootstrap import sanitize_path_segment, confine_to_root

safe = sanitize_path_segment(user_filename)            # strips bidi/zero-width, caps 64 chars
path = confine_to_root(raw, allowed_root="/data/work") # raises ValueError on escape
```

`confine_to_root` canonicalizes both sides (`expanduser().resolve()`) before
comparison, defeating `..` traversal **and** symlink escape.

### Security & fail-close

```python
from vibey_bootstrap import compare_secrets
from vibey_bootstrap.failclose import require_env, optional_env, fail_open_env
```

- `compare_secrets(a, b) -> bool` — constant-time (`hmac.compare_digest`); `False` on
  any `None`/empty input.
- `require_env(name, message=None)` — return value or raise `ConfigurationError`
  (auth-critical settings — **fail closed**).
- `optional_env(name, default="")` — stripped value or default (URLs with sane defaults).
- `fail_open_env(name)` — value when truthy, else `None` ("feature disabled" semantics).

### Identity & audit

```python
from vibey_bootstrap.identity import build_credential, credential_kind, CredentialKind
from vibey_bootstrap.audit import build_audit_extra

cred = build_credential()   # ClientSecret (if secret set) → WorkloadIdentity → DefaultAzureCredential
logger.info("EMAIL_AUDIT", extra=build_audit_extra("send", sender=addr, subject=subj))
```

`build_credential(*, tenant_id=None, client_id=None, client_secret=None, prefer=None,
token_file_path=...)` codifies the credential preference (Workload Identity first in a
cluster — no client secrets in pod env). `credential_kind()` previews the choice
without constructing anything (handy for health probes). `build_audit_extra(operation,
**fields)` always injects `operation` + a UTC ISO-8601 `timestamp`, masks email/secret
fields, and truncates long fields (`subject`, `error`, `traceback`, …).

### Tier 1 environment variables

| Variable | Default | Purpose |
|---|---|---|
| `LOG_LEVEL` | `INFO` | base log level |
| `DEBUG_LOGGING_ENABLED` | off | **second gate** required for DEBUG output |
| `USE_MOCK_BOOTSTRAP` | off | short-circuit `ensure_bootstrap()` (local/dev/tests) |

---

## 4. Python: v2.1 transports (logging routing)

A **transport** is a named factory `Callable[[], logging.Handler | None]`. Enabling
attaches its handler to the root logger; disabling detaches and closes it. This
decouples *where logs go* from *how they're formatted*.

```python
from vibey_bootstrap import (
    configure_transports, register_transport,
    enable_transport, disable_transport, list_transports,
)

# One call to wire the three built-ins (explicit bool wins; else env flag):
configure_transports(console=True, app_insights=False, sumo_logic=True)

list_transports()   # {'console': {'registered': True, 'enabled': True}, ...}
```

`configure_transports()` also sets the root logger to `effective_log_level()` so
enabled transports actually receive records. It is idempotent and re-runnable.

### Built-in transports

| Name | Handler | Env flag | Default |
|---|---|---|---|
| `console` | `StreamHandler` + `ExtraFieldsFormatter` + `CorrelationFilter` | `CONSOLE_LOGGING_ENABLED` | **on** |
| `app_insights` | OpenTelemetry handler (delegates to v1 `TelemetryManager`) | `APP_INSIGHTS_LOGGING_ENABLED` | off |
| `sumo_logic` | `SumoLogicHandler` (buffered async POST) | `SUMO_LOGIC_LOGGING_ENABLED` | off |

Two caveats: (1) the `console` transport installs **the same** `StreamHandler` stack
as `configure_logging()` — enabling both produces duplicate console lines, so pick one;
(2) if you also call `configure_logging()` (which does `basicConfig(force=True)` and
replaces root handlers), call it **before** `configure_transports()`, which reconciles
against the live root handlers on each run. Disabling `app_insights` only detaches the
OTel handler (the exporter is not torn down). A custom sink is one call away:

```python
register_transport("my_syslog", lambda: logging.handlers.SysLogHandler())
enable_transport("my_syslog")
```

### `SumoLogicHandler` deep-dive

Requires the `[sumologic]` extra (`requests`). `make_sumo_logic_handler()` returns
`None` (a **soft no-op**) when `SUMO_LOGIC_COLLECTOR_URL` is unset *or* when `requests`
isn't installed — so enabling the transport without the extra never errors.

Behavior: `emit()` only appends to an in-memory bounded `deque` (a daemon thread does
the network I/O — **never blocks, never raises**). It ships **NDJSON** (via
`JsonLogFormatter`), gzips bodies at/above the threshold, batches by count **and**
byte size (Sumo's 100 KB–1 MB sweet spot), and uses a `urllib3` `Retry` adapter that
retries `408/429/5xx` with backoff+jitter, **honors `Retry-After`**, and never retries
`401`/other 4xx. Flushes on interval, on `batch_size`, and at `atexit`. Counters:
`sumologic.transport.{posts,ok,error,throttled,dropped,records}`.

```python
import os
os.environ["SUMO_LOGIC_COLLECTOR_URL"] = "https://collectors.sumologic.com/receiver/v1/http/XXXX"
os.environ["SUMO_LOGIC_LOGGING_ENABLED"] = "true"
configure_transports(sumo_logic=True)   # or rely on the env flag alone
```

| Env var | Default | Purpose |
|---|---|---|
| `SUMO_LOGIC_COLLECTOR_URL` | — (required) | HTTP Source endpoint (unset ⇒ transport stays off) |
| `SUMO_LOGIC_COLLECTOR_TOKEN` | — | `x-sumo-token` auth header |
| `SUMO_LOGIC_SOURCE_CATEGORY` | — | `X-Sumo-Category` |
| `SUMO_LOGIC_SOURCE_HOST` | — | `X-Sumo-Host` |
| `SUMO_LOGIC_FIELDS` | — | `X-Sumo-Fields` (`k=v,k2=v2`) |
| `SUMO_LOGIC_BATCH_SIZE` | `100` | records per POST |
| `SUMO_LOGIC_MAX_BATCH_BYTES` | `1000000` | byte cap per POST |
| `SUMO_LOGIC_GZIP_THRESHOLD` | `1024` | gzip bodies ≥ this |
| `SUMO_LOGIC_FLUSH_INTERVAL` | `5.0` | timer flush (s) |
| `SUMO_LOGIC_MAX_BUFFER` | `10000` | buffer cap (oldest dropped on overflow) |
| `SUMO_LOGIC_TIMEOUT` | `5.0` | POST timeout (s) |

### v3.0.0 transports (seven additional sinks)

All v3 network/storage transports subclass `_BufferedShipper` — the same guarantees as
Sumo Logic: **never block the caller, never raise, bounded buffer with drop counting**,
background flush thread, batch by count and bytes, flush at `atexit`.

| Name | Extra | Env flag | Factory env (soft no-op if unset) |
|---|---|---|---|
| `panther` | `[panther]` | `PANTHER_LOGGING_ENABLED` | `PANTHER_API_HOST`, `PANTHER_LOG_SOURCE_*` |
| `file` | stdlib | `FILE_LOGGING_ENABLED` | `FILE_LOG_PATH`, rotation settings |
| `blob` | `[bloblog]` | `BLOB_LOGGING_ENABLED` | `BLOB_*` connection/container settings |
| `sql` | `[sqllog]` | `SQL_LOGGING_ENABLED` | `SQL_LOG_DSN`, `SQL_LOG_TABLE` |
| `nosql` | `[nosqllog]` | `NOSQL_LOGGING_ENABLED` | `NOSQL_URI`, database/collection |
| `adx` | `[adxlog]` | `ADX_LOGGING_ENABLED` | `ADX_CLUSTER_URI`, `ADX_DATABASE` |
| `event_hubs` | `[eventhubslog]` | `EVENTHUBS_LOGGING_ENABLED` | `EVENTHUB_FQNS`, `EVENTHUB_NAME` |

```python
from vibey_bootstrap import configure_transports

configure_transports(
    console=True,
    panther=True,
    blob=True,
    sql=True,
    nosql=True,
    adx=True,
    event_hubs=True,
)
```

See [examples/39_v3_transports.py](../examples/39_v3_transports.py). Install all deps
with `pip install 'vibey-bootstrap[logging-all]'`.

### v3.0.0 runtime modules (non-transport)

| Module | Extra | Key APIs |
|---|---|---|
| `vibey_bootstrap.db` | `[db]` | `get_sessionmaker()`, `Outbox`, `drain_outbox()` |
| `vibey_bootstrap.email` | `[email]` | `AcsEmailSender` |
| `vibey_bootstrap.http` | `[http]` | `build_session()`, `request_with_retry()` |
| `vibey_bootstrap.http.async_client` | `[http-async]` | `build_async_client()` |
| `vibey_bootstrap.documentdb` | `[documentdb]` | `mongo_client_from_env()` |
| `vibey_bootstrap.aks` | `[aks]` | `build_info()`, `install_sigterm_handler()` |
| `vibey_bootstrap.governance` | `[governance]` | `budget_guard()`, `track_usage()` |
| `vibey_bootstrap.contrib.scaffold` | core | `vibey-bootstrap list`, `vibey-bootstrap scaffold` |

Examples: [44](../examples/44_db_outbox_email.py), [45](../examples/45_http_client.py),
[46](../examples/46_scaffold_cli.py).

---

## 5. Python: v2 Tier 2 / Tier 3 subpackages (opt-in)

Concise reference; each is an independent import path. See `examples/` for runnable
demos (the numbers below reference numbered example files).

### `alerts` — tiered dispatcher
```python
from vibey_bootstrap.alerts import (
    register_dispatcher, alert_dev_team, AlertSeverity, install_global_exception_hooks,
)
register_dispatcher(my_email_sender, recipients=["dev-alerts@example.com"])
install_global_exception_hooks()    # uncaught sync/async exceptions auto-alert
alert_dev_team(AlertSeverity.ERROR, subject="x failed", context={...}, dedup_key="x")
```
`register_dispatcher(sender, recipients=None)` wires a sender
(`(recipients, subject, html_body) -> None`); `alert_dev_team(severity, subject,
context=None, dedup_key=None)` fires one. `AlertSeverity` = `WARN | ERROR | CRITICAL`:
**WARN is log-only**, **ERROR** is logged + queued to the digest and may escalate to
CRITICAL, **CRITICAL** sends an email immediately (subject to the kill switch +
rate-limit). `@traced(alert_on_error=...)` and most subpackages emit through this.
Tunables (env): `DEV_ALERTS_ENABLED` (kill switch, default on), `DEV_ALERT_RECIPIENTS`,
`ALERT_DEDUP_WINDOW_SECONDS` (600), `ALERT_MAX_PER_HOUR` (30), `ALERT_ESCALATE_AFTER`
(5), `ALERT_ESCALATE_WINDOW_SECONDS` (900), `ALERT_CRITICAL_SUBJECT_PREFIX`.

### `fastapi_middleware` — request timing + 5xx alerts
```python
from vibey_bootstrap.fastapi_middleware import install_middleware
install_middleware(app, probe_paths=("/health/live","/health/ready"),
                   alert_subject_prefix="[svc] ", fire_alerts=True)
```
Probe paths are **silent**. Non-probes log INFO (`<400`) / WARNING (`>=400`). A `5xx`
fires an ERROR alert (`http_5xx:{path}:{status}`); an uncaught exception fires
`http_crash:{path}:{type}` then re-raises. No headers added; correlation lives in
context vars, not HTTP headers.

### `health` — readiness probes
```python
from vibey_bootstrap.health import (
    check_app_config_health, check_app_insights_health, check_app_insights_logging,
)
```
Each returns `{"status": "ok" | "not_configured" | "error", ...}` (adds `"mock": True`
under `USE_MOCK_BOOTSTRAP`). `check_app_config_health` does a live App Config load;
the App Insights checks are fast readiness checks.

### `auth` — webhook + API-key (needs `fastapi`)
```python
from vibey_bootstrap.auth import (
    install_graph_webhook_route, WebhookDedup, verify_api_key_header,
    verify_webhook_client_state, validation_token_handshake,
)
install_graph_webhook_route(app, "/api/webhooks/email",
    background_handler=on_message, rate_limit_bucket=webhook_bucket(),
    dedup=WebhookDedup(ttl_seconds=600))
```
HTTP contract is documented in [Part 7](#7-typescriptnextjs--a-http-client-integration).
`verify_api_key_header(x_api_key, *, env_var="API_KEY", fail_open_when_unset=True)` is
an async FastAPI dependency raising `HTTPException(401)` on mismatch.

### `ratelimit` — token bucket
```python
from vibey_bootstrap.ratelimit import (
    TokenBucket, fastapi_rate_limit, webhook_bucket, admin_bucket,
)
bucket = TokenBucket(budget=240, refill_per_second=4.0, name="webhook")
@app.post("/x", dependencies=[Depends(fastapi_rate_limit(bucket))])
async def x(): ...
```
`consume(n=1.0) -> bool`; `snapshot()` for monitoring. Presets:
`webhook_bucket()` = 240 burst / 4 per s; `admin_bucket()` = 30 burst / 0.5 per s.
`fastapi_rate_limit` returns **429 with an empty body** (no budget leak).

### `retry` — tenacity wrappers (needs `tenacity`)
```python
from vibey_bootstrap.retry import build_retry, retry_azure_transient, retry_ai_transient

@retry_azure_transient(operation="blob.download")   # 3 attempts, 2–10s, NetworkError|RateLimitError
def download(): ...

@retry_ai_transient(operation="openai.chat")        # 7 attempts, 2–120s, RateLimitError
def chat(): ...
```

### `ingress` — 4-gate attachment classifier
```python
from vibey_bootstrap.ingress import AttachmentClassifier, ClassifiedKind, enforce_zip_safety_limits

result = AttachmentClassifier().classify(           # gates: extension → MIME → size → magic-byte
    filename=name, content_type=mime, size_bytes=len(data), content=data,
)
if result.allowed:
    handle(result.kind)        # "pdf" | "zip"
```
`classify(...)` is **keyword-only** and returns
`ClassificationResult(allowed, kind, reject_reason, extension_mismatch)`.
`ClassifiedKind` is a **string literal** — `"pdf" | "zip" | "reject"` (the
classifier's `allowed_kinds` defaults to `("pdf", "zip")`). Zip-bomb defense:
`enforce_zip_safety_limits(data)` (defaults 500 MB uncompressed / 1000 entries via
`MAX_ZIP_UNCOMPRESSED_BYTES` and `MAX_ZIP_ENTRIES`).

### `notify` — two-tier notifications
```python
from vibey_bootstrap.notify import (
    build_failure_alert_body, build_unprocessable_notification,
    build_validation_notice_body, should_notify_sender, UnprocessableReason,
)
# Builders are keyword-only:
ops_html = build_failure_alert_body(
    attachment_name=name, correlation_id=cid, sender=addr,
    error_summary=str(exc)[:500], audience="ops",
)
if should_notify_sender(addr):    # per-sender throttle (max_per_hour=3, window_seconds=3600)
    subject, html, text, reason = build_unprocessable_notification(
        failure_reason=UnprocessableReason.VALIDATION_FAILURE,
        sender=addr, attachment_summary=[], correlation_id=cid,
    )
```
Ops get full forensics (`build_failure_alert_body`); senders get a sanitized message
(`build_unprocessable_notification`, which returns a `(subject, html, text, reason)`
tuple). All builders take **keyword-only** args.

### `heartbeat` — pulse + consumer watchdog
```python
from vibey_bootstrap.heartbeat import (
    start_background_monitors, record_consumer_iteration, record_message_settled,
)
monitors = start_background_monitors(stop_event)   # heartbeat + watchdog daemons
```
Call `record_consumer_iteration()` each loop; the watchdog fires an ERROR alert after
silence (default 30 min). Env: `HEARTBEAT_INTERVAL_SECONDS`,
`WATCHDOG_INTERVAL_SECONDS`, `WATCHDOG_SB_SILENCE_SECONDS`.

### `config_refresh` — dynamic log flags (run on a schedule)
```python
from vibey_bootstrap.config_refresh import refresh_log_flags
refresh_log_flags(("DEBUG_LOGGING_ENABLED", "LOG_LEVEL"))   # re-reads App Config; reapplies logging
```

### `subscription` — resource renewal loop
```python
from vibey_bootstrap.subscription import ensure_resource, renewal_loop, SubscriptionGone
```
Idempotent find-or-create + a SIGTERM-responsive renewal thread (sleeps in ≤5 s
slices). Built for Graph webhook subscriptions but generic.

### `servicebus` — consumer + DLQ (needs `azure-servicebus`)
```python
from vibey_bootstrap.servicebus import handle_message, run_dlq_digest, issue_resubmit_token
handle_message(receiver, msg, processor, schema=schema,
               correlation_field="correlation_id", source="consumer", counter_namespace="sb")
```
`handle_message(receiver, msg, processor, *, schema=None, correlation_field="correlation_id",
extra_correlation_fields=(), source="consumer", counter_namespace="sb")` parses JSON →
validates → opens `correlation_scope` → calls your processor → classifies failures via
`is_unrecoverable` into **complete / abandon / dead-letter**, and returns
`(processed: bool, failed: bool)`. `processor` is a `MessageProcessor` Protocol
(`process(payload)` + `notify_failure(payload, error)`). The DLQ digest
(`run_dlq_digest`) sends HMAC-signed resubmit tokens —
`issue_resubmit_token(secret, *, ttl_seconds=86400)` /
`verify_resubmit_token(secret, token)`.

### `sb_lock` — message-lock renewal (needs `azure-servicebus`)
```python
from vibey_bootstrap.sb_lock import lock_for_process, ManagedLock
with lock_for_process(receiver, msg, max_lock_renewal_seconds=3600):
    ...   # broker won't redeliver mid-process
```

### `openai` — AI usage tracker
```python
from vibey_bootstrap.openai import record_usage, acquire, usage_snapshot, check_thresholds_and_alert
record_usage("gpt-4o", prompt_tokens=1200, completion_tokens=300)
```
Sliding-window tokens + cost (built-in pricing for GPT-4o & Claude 3 families;
override via `register_pricing`). Soft TPM cap via `acquire`. Env:
`AI_TPM_LIMIT[_<DEPLOYMENT>]`, `AI_COST_ALERT_HOURLY_DOLLARS`,
`AI_COST_ALERT_DAILY_DOLLARS`, `AI_HIGH_USAGE_TOKENS_HOURLY`.

### `tokens` — HMAC-SHA256 action tokens
```python
from vibey_bootstrap.tokens import issue_action_token, verify_action_token, InvalidActionToken
tok = issue_action_token(SECRET, action="dlq_resubmit", ttl_seconds=86400, payload={"id": "m1"})
body = verify_action_token(SECRET, tok, expected_action="dlq_resubmit")   # raises InvalidActionToken
```
Token = `base64url(json_payload).base64url(hmac_sha256)`; payload carries `exp` (unix
seconds) + `act`. **This is the interop point for the TS port in Part 8.**

### `scheduler` — NCRONTAB parser (needs `apscheduler`)
```python
from vibey_bootstrap.scheduler import parse_cron_trigger
trigger = parse_cron_trigger("0 */5 * * * *")   # 5- or 6-field NCRONTAB → APScheduler CronTrigger
```

### `metrics` — aggregate snapshot
```python
from vibey_bootstrap.metrics import build_metrics_snapshot
snap = build_metrics_snapshot()
# {"latency": {...}, "alert_counters": {...}, "ai_usage": {...},
#  "bootstrap_initialized": bool, "last_sb_settle_age_seconds": float|None}
```
Soft-imports contributors — sections for absent modules are simply omitted.

### `pdf_safety` — strip active content (needs `pypdf`)
```python
from vibey_bootstrap.pdf_safety import sanitize_pdf_for_passthrough
reader = sanitize_pdf_for_passthrough(reader)   # removes OpenAction/AA/JavaScript/URI; best-effort
```

---

## 6. Python: three end-to-end recipes

These mirror the runnable skeletons in [`examples/`](../examples/) — the canonical,
tested source. Each runs offline with `USE_MOCK_BOOTSTRAP=true ... --dry-run`. Start
at [`examples/README.md`](../examples/README.md) for the full numbered reading order
(`01_quickstart.py` … `38_logging_transports.py`).

### 6.1 Azure Function ([`examples/e2e_azure_function.py`](../examples/e2e_azure_function.py))

Lazy idempotent startup, per-request correlation, a fully traced handler, audit lines:

```python
import logging, uuid
from vibey_bootstrap.alerts import install_global_exception_hooks, register_dispatcher
from vibey_bootstrap.audit import build_audit_extra
from vibey_bootstrap.bootstrap import ensure_bootstrap
from vibey_bootstrap.counters import bump_counter
from vibey_bootstrap.logging import configure_logging, correlation_scope
from vibey_bootstrap.tracing import traced

logger = logging.getLogger(__name__)
_started = False

def _startup() -> None:
    global _started
    if _started:
        return
    configure_logging()
    install_global_exception_hooks()
    ensure_bootstrap()
    register_dispatcher(my_email_sender, recipients=["dev-alerts@example.com"])
    _started = True

@traced(operation="example.handle_request", alert_on_error="error")
def handle_request(payload: dict) -> dict:
    bump_counter("example.requests.processed")
    return {"ok": True}

def http_handler(request_id: str | None, body: dict) -> dict:
    _startup()
    cid = request_id or uuid.uuid4().hex[:12]
    with correlation_scope(cid, request_id=cid):
        logger.info("REPORT_AUDIT", extra=build_audit_extra("http_request", method="POST"))
        return handle_request(body)

# In function_app.py:
# @app.route(route="hello", auth_level=func.AuthLevel.FUNCTION)
# def hello(req): return func.HttpResponse(json.dumps(http_handler(req.headers.get("X-Request-Id"), req.get_json())))
```
> Note: stdlib `LogRecord` reserves the key `name` — use a different `extra` key
> (e.g. `payload_name`) when forwarding caller values.

### 6.2 FastAPI pipeline ([`examples/e2e_fastapi_pipeline.py`](../examples/e2e_fastapi_pipeline.py))

Bootstrap + alerts + middleware + webhook + health + API-key admin + `/api/metrics`:

```python
from fastapi import Depends, FastAPI, Header
from vibey_bootstrap.alerts import install_global_exception_hooks, register_dispatcher
from vibey_bootstrap.auth import WebhookDedup, install_graph_webhook_route, verify_api_key_header
from vibey_bootstrap.bootstrap import ensure_bootstrap
from vibey_bootstrap.fastapi_middleware import install_middleware
from vibey_bootstrap.health import check_app_config_health, check_app_insights_health
from vibey_bootstrap.logging import configure_logging
from vibey_bootstrap.metrics import build_metrics_snapshot
from vibey_bootstrap.ratelimit import admin_bucket, fastapi_rate_limit, webhook_bucket

configure_logging(); install_global_exception_hooks(); ensure_bootstrap()
register_dispatcher(my_email_sender, recipients=["dev-alerts@example.com"])

app = FastAPI()
install_middleware(app, probe_paths=("/health/live", "/health/ready"))

install_graph_webhook_route(app, "/api/webhooks/email",
    background_handler=on_message,
    rate_limit_bucket=webhook_bucket(name="email_webhook"),
    dedup=WebhookDedup(ttl_seconds=600))

@app.get("/health/ready")
def ready() -> dict:
    return {"status": "ok",
            "app_config": check_app_config_health(),
            "app_insights": check_app_insights_health()}

admin_bkt = admin_bucket(name="admin_actions")
@app.post("/api/admin/reload", dependencies=[Depends(fastapi_rate_limit(admin_bkt))])
async def admin_reload(x_api_key: str = Header(default=None)) -> dict:
    await verify_api_key_header(x_api_key)
    return {"reloaded": True}

@app.get("/api/metrics")
def metrics() -> dict:
    return build_metrics_snapshot()
```

### 6.3 AKS Service Bus worker ([`examples/e2e_aks_sb_worker.py`](../examples/e2e_aks_sb_worker.py))

Consumer loop, heartbeat + watchdog, lock-per-message, SIGTERM-clean shutdown:

```python
import signal, threading
from vibey_bootstrap.bootstrap import ensure_bootstrap
from vibey_bootstrap.heartbeat import record_consumer_iteration, start_background_monitors
from vibey_bootstrap.identity import build_credential
from vibey_bootstrap.logging import configure_logging
from vibey_bootstrap.sb_lock import lock_for_process
from vibey_bootstrap.servicebus import handle_message
from vibey_bootstrap.validation import queue_message_schema

def main_loop(receiver, processor, stop_event):
    schema = queue_message_schema(required_fields=("correlation_id",),
                                  path_field="blob_path", path_required_prefix="reports/")
    while not stop_event.is_set():
        record_consumer_iteration()
        msg = receiver.receive()
        if msg is None:
            if stop_event.wait(0.1): break
            continue
        with lock_for_process(receiver, msg, max_lock_renewal_seconds=3600):
            handle_message(receiver, msg, processor, schema=schema,
                           correlation_field="correlation_id", source="consumer", counter_namespace="sb")

def main_pod():
    configure_logging(); ensure_bootstrap()
    credential = build_credential()   # WorkloadIdentity in-cluster
    stop_event = threading.Event()
    signal.signal(signal.SIGTERM, lambda *_: stop_event.set())
    monitors = start_background_monitors(stop_event)
    try:
        main_loop(real_receiver, real_processor, stop_event)
    finally:
        stop_event.set()
        for t in monitors: t.join(timeout=5)
```

---

## 7. TypeScript/Next.js — A: HTTP client integration

This section documents the **exact HTTP contract** a Python backend exposes when it
wires up `vibey_bootstrap.auth`, `health`, `metrics`, and `fastapi_middleware`, then
gives typed Next.js (App Router) client code to consume it.

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

---

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

---

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
| `SUMO_LOGIC_COLLECTOR_URL` (+ `_TOKEN`, `_SOURCE_CATEGORY`, `_SOURCE_HOST`, `_FIELDS`, `_BATCH_SIZE`, `_MAX_BATCH_BYTES`, `_GZIP_THRESHOLD`, `_FLUSH_INTERVAL`, `_MAX_BUFFER`, `_TIMEOUT`) | see Part 4 | Sumo transport |
| `API_KEY` | — | `verify_api_key_header` |
| `GRAPH_WEBHOOK_CLIENT_STATE` | — (required for webhooks) | webhook auth |
| `DEV_ALERTS_ENABLED`, `DEV_ALERT_RECIPIENTS`, `ALERT_DEDUP_WINDOW_SECONDS`, `ALERT_MAX_PER_HOUR`, `ALERT_ESCALATE_AFTER`, `ALERT_ESCALATE_WINDOW_SECONDS`, `ALERT_CRITICAL_SUBJECT_PREFIX` | see Part 5 | `alerts` dispatcher |
| `HEARTBEAT_INTERVAL_SECONDS` / `WATCHDOG_*` | see Part 5 | heartbeat |
| `AI_TPM_LIMIT[_<DEPLOYMENT>]`, `AI_COST_ALERT_HOURLY_DOLLARS`, `AI_COST_ALERT_DAILY_DOLLARS`, `AI_HIGH_USAGE_TOKENS_HOURLY` | — | `openai` tracker |
| `AZURE_BOOTSTRAP_ALLOW_RESET` | off | **test-only** (see 9.2) |

### 9.2 Testing note

Subpackages with global state (counters, latency histograms, alert dispatcher,
transports, webhook dedup, …) expose `reset_state()` / `_reset_*` helpers **gated by
`AZURE_BOOTSTRAP_ALLOW_RESET=1`**. The test suite sets it once in
[`test/conftest.py`](../test/conftest.py); **production code must never set it.** For
local/dev runs without Azure, set `USE_MOCK_BOOTSTRAP=true` to make `ensure_bootstrap()`
a no-op and the health/identity probes return `{"status":"ok","mock":true}`.

### 9.3 Troubleshooting

| Symptom | Cause / fix |
|---|---|
| Sumo transport silently does nothing | `SUMO_LOGIC_COLLECTOR_URL` unset, or `[sumologic]` extra (`requests`) not installed — `make_sumo_logic_handler()` returns `None` by design. |
| App Insights never "upgrades" | The connection string wasn't present in env at phase 2 and isn't in App Config either; verify `APPLICATIONINSIGHTS_CONNECTION_STRING`. |
| `ImportError` from `install_graph_webhook_route` / `fastapi_rate_limit` | Install the `fastapi` extra. |
| DEBUG logs missing despite `LOG_LEVEL=DEBUG` | Also set `DEBUG_LOGGING_ENABLED=true` (the second gate). |
| `LoggingExtraConflictError` | An `extra={}` key collides with a reserved `LogRecord` attribute (e.g. `name`, `msg`, `args`) — rename it. |
| `ConfigurationError` from webhook | `GRAPH_WEBHOOK_CLIENT_STATE` is unset; the endpoint refuses all entries (`401`). |

### 9.4 Further reading

- [`README.md`](../README.md) — overview + extras matrix
- [`examples/README.md`](../examples/README.md) — numbered reading order (01 → 38 + e2e_*)
- [`CHANGELOG.md`](../CHANGELOG.md) — release-by-release surface
- [`MIGRATING-FROM-V1.md`](../MIGRATING-FROM-V1.md) — v1 → v2 adoption
