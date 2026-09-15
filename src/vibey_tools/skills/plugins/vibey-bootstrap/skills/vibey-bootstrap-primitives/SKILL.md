---
name: vibey-bootstrap-primitives
description: "Use for vibey-bootstrap v2 Tier 1 always-on stdlib primitives and the v2.1/v3.0 logging transports (ten sinks). Covers configure_logging / JsonLogFormatter, correlation_scope and CorrelationFilter (contextvars), masking helpers (mask_api_key/mask_bearer_token/mask_email_address/mask_secrets_in_dict), @traced tracing + bump_counter/latency_snapshot, bootstrap helpers (ensure_bootstrap, load_local_settings, refresh_setting), the error vocabulary (PipelineError/UnrecoverableError/TransientError, is_unrecoverable), soft_fail/run_phases, validate_message, sanitize_path_segment/confine_to_root, compare_secrets and failclose, identity build_credential, audit, and configure_transports for console/app_insights/sumo_logic/panther/file/blob/sql/nosql/adx/event_hubs. Triggers on vibey_bootstrap structured logging, correlation IDs, DEBUG_LOGGING_ENABLED, Sumo Logic or Panther transport, FILE_LOG_PATH, or @traced."
---

> **vibey-bootstrap** is the library formerly published as `azure-bootstrap` (renamed in 4.0.0: package `vibey-bootstrap`, import `vibey_bootstrap`, CLI `vibey-bootstrap`; `azbootstrap` remains as a deprecated alias). Feature-tier labels below (v2 primitives, v3 modules) are historical and unchanged.

# Azure Bootstrap — v2 Tier 1 Primitives & Logging Transports (v2.1 + v3.0)

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
  (auth-critical settings → **fail closed**).
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

## 4. Python: logging transports (v2.1 + v3.0 — ten sinks)

A **transport** is a named factory `Callable[[], logging.Handler | None]`. Enabling
attaches its handler to the root logger; disabling detaches and closes it. This
decouples *where logs go* from *how they're formatted*.

```python
from vibey_bootstrap import (
    configure_transports, register_transport,
    enable_transport, disable_transport, list_transports,
)

# One call to wire built-ins (explicit bool wins; else env flag):
configure_transports(console=True, app_insights=False, sumo_logic=True)

# v3.0 — enable additional sinks in one call:
configure_transports(console=True, panther=True, file=True, blob=True, sql=True,
                     nosql=True, adx=True, event_hubs=True)

list_transports()   # {'console': {'registered': True, 'enabled': True}, ...}
```

`configure_transports()` also sets the root logger to `effective_log_level()` so
enabled transports actually receive records. It is idempotent and re-runnable.

### Built-in transports (ten total)

| Name | Handler | Extra | Env flag | Default |
|---|---|---|---|---|
| `console` | `StreamHandler` + `ExtraFieldsFormatter` + `CorrelationFilter` | stdlib | `CONSOLE_LOGGING_ENABLED` | **on** |
| `app_insights` | OpenTelemetry handler (delegates to v1 `TelemetryManager`) | stdlib | `APP_INSIGHTS_LOGGING_ENABLED` | off |
| `sumo_logic` | `SumoLogicHandler` (buffered async POST) | `[sumologic]` | `SUMO_LOGIC_LOGGING_ENABLED` | off |
| `panther` | Panther SIEM HTTP Source | `[panther]` | `PANTHER_LOGGING_ENABLED` | off |
| `file` | Rotating local log file (`JsonLogFormatter`) | stdlib | `FILE_LOGGING_ENABLED` | off |
| `blob` | Azure Blob Storage NDJSON | `[bloblog]` | `BLOB_LOGGING_ENABLED` | off |
| `sql` | SQL table append | `[sqllog]` | `SQL_LOGGING_ENABLED` | off |
| `nosql` | Mongo/Cosmos collection append | `[nosqllog]` | `NOSQL_LOGGING_ENABLED` | off |
| `adx` | Azure Data Explorer ingest | `[adxlog]` | `ADX_LOGGING_ENABLED` | off |
| `event_hubs` | Azure Event Hubs producer | `[eventhubslog]` | `EVENTHUBS_LOGGING_ENABLED` | off |

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
| `SUMO_LOGIC_COLLECTOR_URL` | — (required) | HTTP Source endpoint (unset → transport stays off) |
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

### v4.0.0 transports — shared `_BufferedShipper` contract

All v3 network/storage transports subclass `_BufferedShipper` — the same guarantees as
Sumo Logic: **never block the caller, never raise, bounded buffer with drop counting**,
background flush thread, batch by count and bytes, flush at `atexit`. Factories return
`None` (soft no-op) when required env vars are unset or the pip extra is missing.

| Name | Key env vars (factory soft no-op if unset) |
|---|---|
| `panther` | `PANTHER_API_HOST`, `PANTHER_LOG_SOURCE_ID` / `PANTHER_LOG_SOURCE_TOKEN` (or `PANTHER_API_KEY`) |
| `file` | `FILE_LOG_PATH` (+ optional `FILE_LOG_ROOT`, `FILE_LOG_ROTATION`, `FILE_LOG_MAX_BYTES`, …) |
| `blob` | `BLOB_*` connection/container settings |
| `sql` | `SQL_LOG_DSN`, `SQL_LOG_TABLE` |
| `nosql` | `NOSQL_LOG_URI`, `NOSQL_LOG_DATABASE`, `NOSQL_LOG_COLLECTION` |
| `adx` | `ADX_CLUSTER_URI`, `ADX_DATABASE` |
| `event_hubs` | `EVENTHUB_FQNS`, `EVENTHUB_NAME` |

Install all transport deps with `pip install 'vibey-bootstrap[logging-all]'`. See
`examples/39_v3_transports.py`.
