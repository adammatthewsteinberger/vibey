# Changelog

All notable changes to the vibey-bootstrap library (formerly azure-bootstrap).

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/); the
project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [4.0.0] — 2026-08-18

**Breaking — rename only.** `azure-bootstrap` is now **`vibey-bootstrap`**,
republished under
[adammatthewsteinberger/vibey-bootstrap](https://github.com/adammatthewsteinberger/vibey-bootstrap)
with the permission of The Vizius Group (see [NOTICE.md](NOTICE.md)). No
runtime behaviour, symbol, signature, default, or environment variable changed;
the major bump exists because the import path changed. Upgrade path:
[MIGRATING-TO-V4.md](MIGRATING-TO-V4.md).

### Changed

- **PyPI distribution**: `azure-bootstrap` → `vibey-bootstrap`. Extras keep
  their names.
- **Import package**: `azure_bootstrap` → `vibey_bootstrap` (every subpackage
  moves with it, e.g. `vibey_bootstrap.alerts`, `vibey_bootstrap.transports`).
- **Console script**: `vibey-bootstrap` is the primary entry point for the
  scaffold CLI (`list` / `scaffold` / `version`).
- **Repository / docs / issue URLs**: `TheViziusGroup/azure-bootstrap` →
  `adammatthewsteinberger/vibey-bootstrap`; documentation site moves to
  <https://adammatthewsteinberger.github.io/vibey-bootstrap/>.
- `[project] authors` / `maintainers` email → `adam@matthewsteinberger.com`;
  `__author__` → Adam Matthew Steinberger.
- `LICENSE` now carries both copyright lines (The Vizius Group; Adam Matthew
  Steinberger). Added `NOTICE.md` with the attribution history and a
  matching **License & attribution** section in the README.
- CI: package name, coverage/build paths, and the Trusted Publisher comment
  updated for the new names. Job structure unchanged. The new PyPI/TestPyPI
  projects need their own Trusted Publisher entries before the first publish.

### Deprecated

- `azbootstrap` console script — still installed and functional in 4.x; prints
  a one-line notice to stderr and delegates to `vibey-bootstrap`. Will be
  removed in a future major release.

## [3.0.1] — 2026-08-10

One runtime fix to `azure_bootstrap.health`; everything else is infrastructure
and documentation. No import paths, symbols, or signatures changed.

### Added

- **Documentation site** at <https://theviziusgroup.github.io/azure-bootstrap/>,
  built with MkDocs Material and deployed by a new `docs.yml` workflow on every
  push to `main` (pull requests build a downloadable preview but do not deploy).
  It carries a generated API reference for all 45 public packages, rendered from
  their docstrings and signatures by `mkdocstrings`/`griffe`.

  The site is assembled at build time by `docs/gen_pages.py` from the existing
  repo-root markdown — nothing is duplicated and nothing is committed by a docs
  build. `README.md` and friends remain the single source of truth and stay
  correct as read on GitHub and PyPI; the generator rewrites their links and
  translates heading anchors between GitHub's and python-markdown's differing
  slug rules.
- New `docs` pip extra with the site toolchain. Deliberately **not** part of
  `all`, which remains the runtime aggregate. Build with
  `pip install -e ".[docs,all]"`.
- CI: `validate-dev-installation` job — installs the exact
  `3.0.1.devYYYYMMDDHHMMSS` build back from TestPyPI and asserts
  `azure_bootstrap.__version__` matches what was built.
- `azure-appconfiguration>=1.9.0` to `[project] dependencies`. It already
  arrived transitively via `azure-appconfiguration-provider`, but
  `azure_bootstrap.health` now imports it directly, so it is declared.
- Tests covering the live branch of `check_app_config_health()` — connection
  string, endpoint + credential, error truncation, and that the probe consumes
  exactly one setting.

### Changed

- `check_app_config_health()` now probes Azure App Configuration with
  `AzureAppConfigurationClient` and pulls a single setting, instead of calling
  the provider's `load()`. `load()` downloaded every setting **and resolved
  Key Vault references** on each call, making a readiness probe as expensive as
  a full bootstrap — and able to fail for reasons unrelated to whether App
  Configuration is reachable.
- `[project.urls] Documentation` now points at the documentation site rather
  than the GitHub README anchor.
- CI: `develop`-branch dev builds now publish to **TestPyPI** instead of PyPI
  (`publish-dev` job, `environment: testpypi`, OIDC Trusted Publisher). The
  public PyPI release history now contains only real releases; pre-releases are
  no longer reachable via `pip install azure-bootstrap --pre`. Dev builds keep
  their `.devN` version signature and are installable from
  `https://test.pypi.org/simple/`.

### Fixed

- CI: anchored the dev-version `sed` rewrites (`^version = "..."$` /
  `^__version__ = "..."$`) and added post-rewrite verification. The previous
  unanchored expressions would also rewrite any other `version = "..."` line in
  `pyproject.toml` (e.g. `target-version`), silently corrupting the build.
- CI: `validate-installation` now installs the exact published version rather
  than whatever PyPI resolves for a bare package name — closing a race where a
  slow index would let the job validate the *previous* release and pass.
- Docs: `CONTRIBUTING.md` referred throughout to a `dev` branch that does not
  exist (the branch is `develop`), and claimed CI "doesn't publish" from it.
- Docs: `README.md` had an unclosed ```` ``` ```` fence in the "Run Tests"
  section, which swallowed the `### Build Package` heading into the code block
  and inverted every fence after it. This mis-rendered on both GitHub and PyPI.

## [3.0.0] — 2026-06-29

**Additive flagship release.** No existing import paths, symbols, signatures, or
defaults changed. v1/v2 code runs unchanged; opt into new extras and env flags.

### Added — Pillar 1 (transports)

- Shared internal `_BufferedShipper` base; rebased `sumologic`, `panther`, `blob`, `sql`, `nosql` handlers.
- New transports: `panther`, `file`, `blob`, `sql`, `nosql`, `adx`, `event_hubs`.
- Extended `configure_transports()` for all ten sinks.

### Added — Pillar 2 (runtime)

- `azure_bootstrap.db` — SQLAlchemy 2 engine/session, `get_db`, `db_health`, RLS helpers.
- `azure_bootstrap.db.migrations` — Alembic conventions (`upgrade_to_head`, env.py template).
- `azure_bootstrap.db.outbox` — transactional outbox with `drain_outbox`.
- `azure_bootstrap.email` — `AcsEmailSender` (ACS).
- `azure_bootstrap.http` — hardened `requests` client + optional `httpx` async stack.
- `azure_bootstrap.documentdb` — Mongo/Cosmos client factory.
- `azure_bootstrap.aks` — SIGTERM handlers, `build_info`, KEDA metric helper, leader election.
- `azure_bootstrap.governance` — budget guard + usage tracker.
- Extensions: `identity` tenant cred + cache, `audit` chaining, `auth` HMAC verify,
  `ratelimit` multi-unit, `servicebus` async/replay/ws router.

### Added — Pillar 3 (assets)

- `azure_bootstrap.contrib.templates/*` — Terraform, Bicep, Helm, GitOps, CI/CD, policy starters.
- `azbootstrap` console script (`scaffold`, `list`, `version`).

### New pip extras

`panther`, `bloblog`, `sqllog`, `nosqllog`, `adxlog`, `eventhubslog`, `logging-all`,
`db`, `documentdb`, `email`, `http`, `http-async`, `governance`, `aks`.

## [2.1.2] — 2026-06-29

Security patch. **No source code changes** — only dependency version floors are
raised to remediate known CVEs in transitive and optional dependencies. The
public API, behavior, and the 469-test / 87.48 %-coverage suite are unchanged.

### Security

- **`cryptography>=48.0.1,<49`** (new core pin) — GHSA-537c-gmf6-5ccf. Pulled in
  transitively via `azure-identity` / `msal`; the `<49` cap keeps it within
  msal's `cryptography<49` requirement.
- **`pyjwt>=2.13.0`** (new core pin) — PYSEC-2026-175 through -179. Pulled in
  via `msal`; stays under msal's `PyJWT<3` cap.
- **`pypdf>=6.13.3`** (was `>=4.0`) in the `[pdf-safety]` extra — CVE-2026-48155,
  -48156, -48735, -49460, -49461, -54530, -54531 and GHSA-jm82-fx9c-mx94.
- **`starlette>=1.3.1`** (new pin) in the `[fastapi]` and `[all]` extras —
  PYSEC-2026-248/-249, CVE-2026-48817/-48818. `starlette` is FastAPI's transitive
  dependency; FastAPI's floor (`>=0.110`) already permits it.

Not pinned: `msgpack` (GHSA-6v7p-g79w-8964) and `pip` (PYSEC-2026-196) flagged by
`pip-audit` are dev-tooling dependencies (via `CacheControl` / the installer), not
part of azure-bootstrap's runtime dependency tree.

## [2.1.1] — 2026-06-29

Documentation-only release. **No code changes** — the package contents, public
API, runtime behavior, and the 469-test / 87.48 %-coverage suite are
byte-identical to 2.1.0. Because 2.1.0 is already published to PyPI (and PyPI
versions are immutable — a version can never be re-uploaded, even after
deletion), these documentation corrections ship as a patch release.

### Fixed

- **README links now resolve on PyPI.** Every repo-relative link in `README.md`
  (e.g. `](CHANGELOG.md)`, `](examples/)`) was rewritten to an absolute
  `https://github.com/TheViziusGroup/azure-bootstrap/blob/main/…` (or `/tree/`
  for directories) URL. PyPI renders the README as the project long-description
  with no repository base URL, so relative links silently 404 there; they only
  worked on GitHub. Absolute URLs resolve on both surfaces.
- Refreshed stale figures: README and CONTRIBUTING now state **469 passing
  tests / 87.48 % coverage** (were 423 / 87.07 %); README and
  MIGRATING-FROM-V1 now reference **38 numbered examples** (were 37) and 42
  total runnable examples.

### Added

- `docs/USAGE.md` — a long-form end-to-end usage guide (Python and
  TypeScript/Next.js) covering the v2.1 logging-transport layer — added to the
  tracked tree.

## [2.1.0] — 2026-05-21

Added a **logging transport layer** — a standardized way to choose where logs
go. **Strictly additive**: every v1 and v2.0 symbol (including
`configure_logging()` and `TelemetryManager`) is unchanged, and the public API
surface is unchanged. The registry and the console / App Insights transports are
stdlib-only; the Sumo Logic transport requires the new `[sumologic]` extra, which
pulls `requests` (its `urllib3` Retry adapter handles backoff + `Retry-After`).
`requests` is imported lazily, so `import azure_bootstrap` still works without
the extra.

### Added
- **Transport registry** (`azure_bootstrap.transports`): `register_transport`,
  `enable_transport`, `disable_transport`, `list_transports`, and the
  convenience `configure_transports(console=…, app_insights=…, sumo_logic=…)`.
  A transport is a named `logging.Handler` factory; enable attaches it to the
  root logger, disable detaches (and closes) it. Idempotent.
- **Three first-class transports**, each independently toggleable from code or
  via a per-transport env flag (`CONSOLE_LOGGING_ENABLED`,
  `APP_INSIGHTS_LOGGING_ENABLED`, `SUMO_LOGIC_LOGGING_ENABLED`); explicit code
  params win over env.
  - `console` — the standard `StreamHandler` + `ExtraFieldsFormatter` stack.
  - `app_insights` — delegates to the existing v1 `TelemetryManager`
    (`configure_azure_monitor`). _Limitation:_ disabling only detaches the
    OpenTelemetry handler from the root logger; it does not tear down the
    underlying exporter.
  - `sumo_logic` — `SumoLogicHandler`: buffered, background-thread, batched
    newline-delimited-JSON POST to a Sumo Logic HTTP Source. Never blocks, never
    raises; flushes on interval / buffer-size / `atexit`; bounded buffer drops
    oldest under backpressure. Ships via a `requests.Session` whose mounted
    `urllib3` `Retry` adapter retries 408/429/5xx with exponential backoff +
    jitter, **honors `Retry-After`** (so 429 throttling is resent, not silently
    dropped), and does not retry 401/other-4xx. Batches are capped by record
    count **and** byte size (~1 MB, Sumo's documented sweet spot) and gzip-
    compressed above a threshold (`Content-Encoding: gzip`). Supports auth-header
    mode (`x-sumo-token`) and per-request `X-Sumo-Fields`. Bumps
    `sumologic.transport.{posts,ok,error,throttled,dropped,records}` counters.
    Configured via `SUMO_LOGIC_COLLECTOR_URL` (+ optional
    `SUMO_LOGIC_COLLECTOR_TOKEN` / `_SOURCE_CATEGORY` / `_SOURCE_HOST` /
    `_FIELDS` / `_BATCH_SIZE` / `_MAX_BATCH_BYTES` / `_GZIP_THRESHOLD` /
    `_FLUSH_INTERVAL` / `_MAX_BUFFER` / `_TIMEOUT`).
- **`JsonLogFormatter`** (`azure_bootstrap.logging`) — one JSON object per
  record (timestamp, level, logger, message, exception, correlation fields, and
  masked `extra={}` fields), reusing the existing masking + `CorrelationFilter`.
- `configure_transports` applies `effective_log_level()` to the root logger so
  enabled transports receive records at the configured level.
- New extras: `transports` (stdlib-only, `= []`) and `sumologic`
  (`["requests>=2.32.0"]`).
- Example [38_logging_transports.py](examples/38_logging_transports.py).
- Test-only `_reset_transports()` gated by `AZURE_BOOTSTRAP_ALLOW_RESET=1`.

## [2.0.0] — 2026-05-18

Major expansion: bakes in the cross-cutting logging, observability, alerting,
and Azure-integration primitives that every project was re-implementing on
top of v1. **No v1 imports change.** All new functionality is additive and
gated behind optional extras where it has runtime dependencies.

### Added

#### Tier 1 — always-on (stdlib-only)

- `azure_bootstrap.logging` — `configure_logging()` (idempotent),
  `ExtraFieldsFormatter` (key=repr pairs, two-space gap, filters reserved +
  underscore-prefixed keys), `LoggingExtraConflictError`, `CorrelationFilter`,
  `correlation_scope()` context manager with arbitrary kwargs, `mask_api_key`,
  `mask_bearer_token`, `mask_email_address`, `mask_secrets_in_dict`,
  `sanitize_for_log` (strips control chars 0x00–0x1f, 0x7f), `content_preview`,
  `safe_json_dumps`, `_safe_repr` (primitive-only, never invokes arbitrary
  `__repr__`), `silence_noisy_loggers` with sensible defaults (`pdfminer`,
  Azure SDK chatty paths, `urllib3`, etc.), `debug_logging_enabled`,
  `effective_log_level`, `env_flag`, `register_secret_keys`,
  `register_noisy_logger`.
- `azure_bootstrap.tracing` — `@traced` decorator (auto-detects async, records
  latency on success + error, lazy alert dispatch, sensitive-arg masking,
  slow-budget alerts), `@traced_async` (alias), `timed_operation` context
  manager, `log_exception_context`, `latency_snapshot` with p50/p95/p99/max
  per operation, `register_slow_threshold`, `default_slow_threshold`.
- `azure_bootstrap.counters` — thread-safe `bump_counter`, `counter_snapshot`.
- `azure_bootstrap.bootstrap` — `ensure_bootstrap` (lazy idempotent wrapper
  around v1 `initialize_application`), `bootstrap_initialized`,
  `load_local_settings` (Azure-Functions-style JSON loader, never overrides
  existing env).
- Top-level — `refresh_setting(*names)` (net-new v2 function — re-reads
  named keys from the cached App Configuration repo).

#### Tier 2 — opt-in

- `azure_bootstrap.alerts` (extra: `alerts`) — `AlertSeverity`,
  `alert_dev_team` (tiered: WARN log-only, ERROR digest + escalation,
  CRITICAL email), `register_dispatcher` (caller supplies any
  `send(recipients, subject, html)` callable), dedup (default 10-min window),
  rate-limit (default 30/hour, folds overflow into digest),
  escalation ladder (5 ERRORs in 15m → CRITICAL), `drain_pending_alerts`,
  `render_pending_alerts_html`, `install_global_exception_hooks` (chains
  previous `sys.excepthook` + asyncio handler), `reset_state` (test-only).
- `azure_bootstrap.health` (extra: `health`) — `check_app_config_health`,
  `check_app_insights_health`, `check_app_insights_logging` (walks every
  handler to detect an attached Azure Monitor handler).
- `azure_bootstrap.fastapi_middleware` (extra: `fastapi`) —
  `install_middleware(app, …)` for FastAPI: probes silent, non-probes log +
  alert on 5xx/uncaught.
- `azure_bootstrap.heartbeat` (extra: `heartbeat`) — `start_heartbeat`,
  `start_consumer_watchdog` (1-hour resilence cooldown longer than alerts
  dedup), `record_consumer_iteration`, `record_message_settled`,
  `start_background_monitors`.
- `azure_bootstrap.config_refresh` (extra: `config-refresh`) —
  `refresh_log_flags` for APScheduler `CronTrigger(minute='*')`.

#### Tier 3 — advanced opt-in

- `azure_bootstrap.tokens` (extra: `tokens`) — `issue_action_token`,
  `verify_action_token`, `InvalidActionToken`. HMAC-SHA256 +
  `hmac.compare_digest`, sorted-keys JSON, base64url-no-pad.
- `azure_bootstrap.servicebus` (extra: `servicebus`) — `check_dlq_growth_rate`
  (CRITICAL on excessive growth), `run_dlq_digest` (daily digest email with
  optional resubmit link + pending-alerts summary), `build_dlq_digest_body`,
  `issue_resubmit_token`, `verify_resubmit_token`, `InvalidResubmitToken`,
  re-exports for consumer watchdog primitives.
- `azure_bootstrap.openai` (extra: `openai`) — `record_usage`, `acquire`
  (soft TPM cap; never blocks longer than `AI_RATE_LIMIT_MAX_WAIT_SECONDS`),
  `record_rate_limit_event`, `usage_snapshot` with sliding windows (60s, 60m,
  24h), `check_thresholds_and_alert` (30-min per-key cooldown),
  `register_pricing`, `AiUsageTracker`. Default pricing includes GPT-4o
  family, o1, GPT-5-mini AND Claude 3.5 Sonnet/Haiku, Claude 3 Opus/Haiku.
  Per-deployment env overrides via `AI_PRICING_<NORMALIZED>_INPUT_PER_1K` /
  `_OUTPUT_PER_1K`.
- `azure_bootstrap.scheduler` (extra: `scheduler`) — `parse_cron_trigger`
  (5- and 6-field NCRONTAB → APScheduler CronTrigger, fallback to `*/15`).
- `azure_bootstrap.metrics` (extra: `metrics`) — `build_metrics_snapshot`
  for `/api/metrics` endpoints, soft-imports each contributor.

### Changed

- `__version__` bumped to `2.0.0`.
- `azure_bootstrap/services/application_bootstrap.py:initialize_application`
  now caches the returned repo via `get_last_initialized_repo()` so the new
  `refresh_setting` can re-read keys without re-running bootstrap. The
  function signature and return type are unchanged.
- Coverage threshold raised from 80 % → 85 % for new code.
- Optional dependencies: new keys `alerts`, `health`, `fastapi`, `heartbeat`,
  `config-refresh`, `servicebus`, `openai`, `tokens`, `scheduler`, `metrics`,
  `all` under `[project.optional-dependencies]`.

### Added (Part 2 — error handling & defensive coding)

#### Tier 1 — always-on (stdlib-only)

- `azure_bootstrap.exceptions` — project-neutral exception hierarchy:
  `PipelineError`, `UnrecoverableError` (marker; subclasses
  `InvalidMessageError`, `OversizedAttachmentError`,
  `MalformedAttachmentError`, `ZipBombError`, `UpstreamResourceMissing`),
  `TransientError` (marker; subclasses `RateLimitError`, `NetworkError`,
  `AuthenticationError`). `is_unrecoverable(exc)` classifier;
  `register_unrecoverable(*types)` for SDK exceptions outside the tree.
- `azure_bootstrap.softfail` — `soft_fail_with(...)`, `soft_fail(...)`
  context manager, `SoftFailResult`. Both re-raise unrecoverable exceptions
  by default (set `re_raise_unrecoverable=False` to opt out).
- `azure_bootstrap.phases` — `run_phase(...)`, `run_phases(...)`,
  `PhaseResult`. `run_phase` NEVER re-raises; per-phase counter convention
  `{namespace}.{name}.{ok|failed|<aggregate>}`.
- `azure_bootstrap.validation` — `validate_message`, `MessageSchema`,
  `FieldRule`, `queue_message_schema(...)` helper. Default path-field
  rules reject `..` and `://` substrings.
- `azure_bootstrap.path_safety` — `sanitize_path_segment(...)` (strips
  bidi/zero-width chars first), `confine_to_root(raw, allowed_root)`.
- `azure_bootstrap.security` — `compare_secrets(a, b)`,
  `verify_api_key_header(...)` async FastAPI helper.

#### Tier 2 — opt-in

- `azure_bootstrap.retry` (extra: `retry`) — `build_retry(...)`,
  `retry_azure_transient(...)`, `retry_ai_transient(...)`. Counter
  conventions: `{ns}.runs`, `{ns}.calls.ok`, `{ns}.calls.invalid_response`,
  `{ns}.calls.rate_limit_or_http_error`, `{ns}.calls.unexpected_error`.
- `azure_bootstrap.ingress` (extra: `ingress`) — `AttachmentClassifier`,
  `ExtensionAllowlist`, `MimeAllowlist`, `classify_bytes`,
  `enforce_size_cap`, `enforce_zip_safety_limits`. Fixed gate order:
  extension → MIME → size → magic-byte. Counter conventions:
  `attachment.rejected.{gate}`, `attachment.classified.{kind}`,
  `attachment.mismatched_extension`.
- `azure_bootstrap.ratelimit` (extra: `ratelimit`) — `TokenBucket`,
  `fastapi_rate_limit`, `webhook_bucket`, `admin_bucket` presets.
  Atomic refill+check+consume; 429 response body empty by default.
- `azure_bootstrap.notify` (extra: `notify`) — `should_notify_sender`
  per-sender throttle; `build_failure_alert_body`,
  `build_validation_notice_body`, `build_unprocessable_notification`
  two-tier email body builders. Sender bodies abuse-safe (no correlation
  IDs / tracebacks / blob paths leaked to the sender side).
- `azure_bootstrap.subscription` (extra: `subscription`) —
  `RenewableResource`, `SubscriptionGone`, `ensure_resource`,
  `renewal_loop`. Renewal loop sleeps in ≤ 5 s slices for SIGTERM
  responsiveness.

#### Tier 3 — advanced opt-in

- `azure_bootstrap.pdf_safety` (extra: `pdf-safety`) —
  `sanitize_pdf_for_passthrough(reader)` strips catalog OpenAction,
  /AA, /JavaScript, /Names, /URI; per-page /AA + /OpenAction;
  per-annotation /A + /AA; AcroForm-field /A + /AA. Best-effort
  (returns the reader unchanged on any exception).
- `azure_bootstrap.servicebus.consumer_wrapper` (existing `servicebus`
  extra) — `handle_message(receiver, msg, processor, ...)` end-to-end
  consumer with schema validation, correlation scope, dead-letter vs
  abandon routing via `is_unrecoverable`, best-effort `notify_failure`
  before dead-letter, `record_message_settled()` in `finally`.

### Added (Part 3 — security, identity, audit)

#### Tier 1 — always-on

- `azure_bootstrap.identity` — `build_credential(...)` prefers
  `WorkloadIdentityCredential` over `ClientSecretCredential` over
  `DefaultAzureCredential`. `credential_kind()` probe; `credential_health()`
  acquires a token and reports latency. Never logs the client secret.
- `azure_bootstrap.audit` — `build_audit_extra(operation, **fields)`
  masks email-shaped values via `mask_email_address`, other secret-named
  fields via `mask_api_key`; truncates subject/error/traceback/etc. via
  `sanitize_for_log`; always inserts UTC ISO-8601 `timestamp`.
- `azure_bootstrap.failclose` — `require_env(name)`, `optional_env(name)`,
  `fail_open_env(name)`. `ConfigurationError` re-exported from
  `azure_bootstrap.models.exceptions` (single canonical class; v1 callers
  unchanged).

#### Tier 2 — opt-in

- `azure_bootstrap.auth` (extra: `auth`) — `WebhookDedup`,
  `verify_webhook_client_state`, `validation_token_handshake`,
  `install_graph_webhook_route(app, path, ...)` FastAPI route installer.
  Pipeline: validation token → rate limit → JSON parse → per-entry
  clientState → dedup → background dispatch → 202 Accepted. 401/429
  responses omit body.
- `azure_bootstrap.sb_lock` (extra: `sb-lock`) — `lock_for_process`
  context manager + `ManagedLock` OO variant. Default
  `max_lock_renewal_seconds=3600`. Swallows AutoLockRenewer construction
  failure (defense, not correctness).

### Skipped (per user scope decision)

Three Part-3 modules were explicitly cut as too niche / unusual for a
Python library:

- `azure_bootstrap.parity/` (Helm chart App-Config-vs-Key-Vault parity
  check)
- `azure_bootstrap.github_oidc/` (federated-credential setup + CLI)
- `azure_bootstrap.manifests/` (bundled Helm-templated K8s YAMLs)

Apps that need these can lift the reference snippets from the spec into
their own deploy tooling.

### Documentation

- New flat examples library under [examples/](examples/) — 37 numbered
  single-concept files (`01_quickstart.py` … `37_metrics_endpoint.py`)
  plus three end-to-end app templates (`e2e_azure_function.py`,
  `e2e_fastapi_pipeline.py`, `e2e_aks_sb_worker.py`). Every example is
  runnable with `USE_MOCK_BOOTSTRAP=true` (no real Azure required) and
  ends with an `# ── Expected output ──` block. See
  [examples/README.md](examples/README.md) for the reading order +
  per-example pip-extra requirements.
- New [MIGRATING-FROM-V1.md](MIGRATING-FROM-V1.md) with the v1 → v2
  upgrade path + extras matrix.
- [README.md](README.md), [CLAUDE.md](CLAUDE.md),
  [CONTRIBUTING.md](CONTRIBUTING.md) refreshed for the v2 surface
  (extras matrix, repository structure, coverage thresholds, version
  references).

### Preserved (v1 contract, byte-identical)

Every entry in v1's `__all__` is still exported from the top-level package
and behaves exactly as before:

`initialize_application`, `get_bootstrap_logger`,
`create_enhanced_config_repository`, `ensure_bootstrap_logging`,
`telemetry_manager`, `ApplicationBootstrap`, `BootstrapLogger`,
`ExtraFieldsFormatter` (the v1 JSON-with-pipe one — the new v2 formatter
lives at `azure_bootstrap.logging.formatter.ExtraFieldsFormatter`),
`TelemetryManager`, `EnhancedConfigRepository`, `SecretsRepository`,
`ApplicationBootstrapInterface`, `BootstrapLoggerInterface`,
`TelemetryManagerInterface`, `EnhancedConfigRepositoryInterface`,
`SecretsRepositoryInterface`, `RepositoryError`, `ConfigurationError`,
`KeyVaultError`, `__version__`.

See [MIGRATING-FROM-V1.md](MIGRATING-FROM-V1.md) for the opt-in upgrade path.

---

## [1.0.0] — 2026-04-09

Initial public release. See [CLAUDE.md](CLAUDE.md) § Version History for
details.
