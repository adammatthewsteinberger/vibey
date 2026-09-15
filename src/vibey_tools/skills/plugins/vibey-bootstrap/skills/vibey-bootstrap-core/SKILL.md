---
name: vibey-bootstrap-core
description: "Use when installing or consuming the vibey-bootstrap Python library (v4.0.0) and its v1 core. Covers pip install and the optional-extras matrix (fastapi, servicebus, sumologic, logging-all, db, email, http, documentdb, governance, aks, vibey-bootstrap scaffold, all, etc.), the 4-phase bootstrap that breaks the logging↔configuration circular dependency, initialize_application / get_bootstrap_logger, configuration precedence and the local-override rule, EnhancedConfigRepository, SecretsRepository, Key Vault references, DI interfaces, RepositoryError/ConfigurationError/KeyVaultError, and v1 environment variables (APPLICATIONINSIGHTS_CONNECTION_STRING, AZURE_APP_CONFIGURATION_CONNECTION_STRING, AZURE_KEY_VAULT_URL, LOG_LEVEL). Triggers on vibey-bootstrap, vibey_bootstrap, Azure Functions/container app startup config, App Configuration + Key Vault loading, load_to_environ, or pip install vibey-bootstrap extras."
---

> **vibey-bootstrap** is the library formerly published as `azure-bootstrap` (renamed in 4.0.0: package `vibey-bootstrap`, import `vibey_bootstrap`, CLI `vibey-bootstrap`; `azbootstrap` remains as a deprecated alias). Feature-tier labels below (v2 primitives, v3 modules) are historical and unchanged.

# Azure Bootstrap — Installation & v1 Core (4-phase bootstrap)

`vibey-bootstrap` solves the **logging ↔ configuration circular dependency** every
Azure Functions / container app hits at startup (you need logging to report config
loading, but App Insights logging needs config to initialize). On top of that v1
core, v2 adds a large, opt-in, framework-agnostic "cross-cutting layer": structured
logging, correlation, tracing, counters, tiered alerts, an error vocabulary, ingress
hardening, Service Bus plumbing, webhook auth, AI usage tracking, health probes, a
v2.1 logging-transport layer (console / App Insights / Sumo Logic), and v4.0.0 adds
seven more logging transports plus DB/outbox, email, hardened HTTP, AKS runtime,
governance, and an `vibey-bootstrap` scaffold CLI — all opt-in behind pip extras.

> **`vibey-bootstrap` is a pure Python package.** It is published to PyPI and has
> **no JavaScript/TypeScript distribution** — you cannot `npm install` or `import` it
> from a Next.js app. (For TS, see the `vibey-bootstrap-typescript` skill: HTTP client
> integration with a Python backend, and porting the patterns to TypeScript.)

**Compatibility:** Python **≥ 3.11**. Distribution: `pip install vibey-bootstrap`
(PyPI, MIT). v4.0.0 is **additive** — every v1/v2 import path, symbol, signature, and
default is unchanged; opt into new extras and env flags. See `MIGRATING-TO-V3.md`.

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
cryptography>=48.0.1,<49  # GHSA-537c-gmf6-5ccf (via azure-identity/msal)
pyjwt>=2.13.0          # PYSEC-2026-175..179 (via msal)
```

### Optional extras matrix

Source of truth: `pyproject.toml`. Many extras are empty markers (`[]`): the code is
**stdlib-only** and already importable without the extra — the extra exists for
discoverability / intent, and only pulls real dependencies where a third-party package
is genuinely required.

| Extra | Installs | What it unlocks |
|---|---|---|
| `fastapi` | `fastapi>=0.110` | `fastapi_middleware`, webhook route, API-key dep, `fastapi_rate_limit` |
| `servicebus` | `azure-servicebus>=7.11` | `servicebus.*` consumer/DLQ helpers |
| `sb-lock` | — (uses `servicebus`) | `sb_lock` message-lock renewal |
| `scheduler` | `apscheduler>=3.10` | `scheduler.parse_cron_trigger` |
| `retry` | `tenacity>=8.0` | `retry.build_retry` + Azure/AI presets |
| `pdf-safety` | `pypdf>=6.13.3` | `pdf_safety.sanitize_pdf_for_passthrough` |
| `sumologic` | `requests>=2.32.0` | `SumoLogicHandler` transport |
| `panther` | `requests>=2.32.0` | Panther SIEM transport |
| `bloblog` | `azure-storage-blob>=12.19` | Blob Storage log transport |
| `sqllog` | `sqlalchemy>=2.0` | SQL table log transport |
| `nosqllog` | `pymongo>=4.6` | Mongo/Cosmos log transport |
| `nosqllog-cosmos` | `azure-cosmos>=4.5` | Cosmos-native log transport |
| `adxlog` | `azure-kusto-ingest`, `azure-kusto-data` | ADX log transport |
| `eventhubslog` | `azure-eventhub>=5.11` | Event Hubs log transport |
| `logging-all` | all transport deps above | every logging transport |
| `transports` | — (stdlib) | transport registry + console/app-insights |
| `alerts` | — (stdlib) | tiered alert dispatcher |
| `health` | — (stdlib) | readiness probes |
| `heartbeat` | — (stdlib) | heartbeat + consumer watchdog |
| `config-refresh` | — (stdlib) | `refresh_log_flags` |
| `ingress` | — (stdlib) | 4-gate attachment classifier |
| `ratelimit` | — (stdlib) | `TokenBucket` + presets |
| `notify` | — (stdlib) | two-tier notification builders |
| `subscription` | — (stdlib) | resource renewal loop |
| `auth` | — (uses `fastapi`) | webhook + API-key guards |
| `identity` | — (`azure-identity` in core) | `build_credential` |
| `audit` | — (stdlib) | `build_audit_extra` |
| `failclose` | — (stdlib) | `require_env` / `optional_env` / `fail_open_env` |
| `openai` | — (stdlib) | AI usage tracker |
| `tokens` | — (stdlib) | HMAC action tokens |
| `metrics` | — (stdlib) | `build_metrics_snapshot` |
| `db` | `sqlalchemy>=2.0`, `alembic>=1.13` | `get_db`, outbox, Alembic helpers |
| `email` | `azure-communication-email>=1.0` | `AcsEmailSender` |
| `http` | `requests>=2.32.0` | `build_session()`, `request_with_retry()` |
| `http-async` | `httpx>=0.27` | `build_async_client()`, `async_request_with_retry()` |
| `documentdb` | `pymongo>=4.6` | `mongo_client_from_env()` |
| `governance` | — (stdlib) | `budget_guard()`, `track_usage()` |
| `aks` | — (stdlib) | `build_info()`, `install_sigterm_handler()`, leader election |
| `all` | fastapi, servicebus, apscheduler, requests, blob, sqlalchemy, alembic, pymongo, ACS email, kusto, eventhub, httpx | aggregate of all third-party deps |
| `dev` / `test` | tooling / test deps | development & CI |

The `vibey-bootstrap` console script (`vibey-bootstrap list`, `vibey-bootstrap scaffold`) ships with
the core install — no extra required. Templates live under `vibey_bootstrap.contrib`.

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
  `vibey_bootstrap.logging` — see the `vibey-bootstrap-primitives` skill.)
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
