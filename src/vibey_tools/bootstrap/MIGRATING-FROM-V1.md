# Migrating from v1 to v2

## TL;DR: nothing to do

If your app does:

```python
from azure_bootstrap import initialize_application, get_bootstrap_logger
```

…upgrading to v2 needs zero code changes. Every v1 symbol is exported with
the same behavior. Pin `azure-bootstrap>=2.0,<3` and you're done.

## Opt-in upgrade (recommended)

For the v2 production-grade defaults:

```python
from azure_bootstrap.alerts import install_global_exception_hooks, register_dispatcher
from azure_bootstrap.bootstrap import ensure_bootstrap
from azure_bootstrap.logging import configure_logging


def my_email_sender(recipients, subject, html_body):
    # any callable matching this signature works
    ...


configure_logging()
install_global_exception_hooks()
ensure_bootstrap()
register_dispatcher(my_email_sender, recipients=["dev-alerts@example.com"])
```

After this, every line emitted via stdlib `logging` carries correlation IDs,
extra fields render as `key=repr(value)` pairs, and uncaught exceptions fire
CRITICAL alerts.

## Extras matrix

The base install gives you all of Tier 1 plus any always-on primitives
that ship stdlib-only. Tier 2 and Tier 3 modules with runtime
dependencies are gated behind pip extras.

### Tier 1 — always-on (no extra needed)

Included in `pip install azure-bootstrap`:

| Module | Import path | Brings |
| --- | --- | --- |
| Logging | `azure_bootstrap.logging` | `configure_logging`, formatter, masking, correlation, noise silencing |
| Tracing | `azure_bootstrap.tracing` | `@traced`, latency histograms, slow thresholds |
| Counters | `azure_bootstrap.counters` | `bump_counter`, `counter_snapshot` |
| Bootstrap | `azure_bootstrap.bootstrap` | `ensure_bootstrap`, `load_local_settings` |
| Exceptions | `azure_bootstrap.exceptions` | `PipelineError` tree + `is_unrecoverable` |
| Soft-fail | `azure_bootstrap.softfail` | `soft_fail`, `soft_fail_with` |
| Phases | `azure_bootstrap.phases` | `run_phase`, `run_phases` |
| Validation | `azure_bootstrap.validation` | `queue_message_schema`, `validate_message` |
| Path safety | `azure_bootstrap.path_safety` | `sanitize_path_segment`, `confine_to_root` |
| Security | `azure_bootstrap.security` | `compare_secrets`, `verify_api_key_header` |
| Identity | `azure_bootstrap.identity` | `build_credential`, `credential_health` |
| Audit | `azure_bootstrap.audit` | `build_audit_extra` |
| Fail-close | `azure_bootstrap.failclose` | `require_env`, `optional_env`, `fail_open_env` |

### Tier 2 — opt-in extras

| Need | Install | Import path |
| --- | --- | --- |
| Tiered alert dispatcher | `pip install azure-bootstrap[alerts]` | `azure_bootstrap.alerts` |
| Health-probe helpers | `pip install azure-bootstrap[health]` | `azure_bootstrap.health` |
| FastAPI timing/alert middleware | `pip install azure-bootstrap[fastapi]` | `azure_bootstrap.fastapi_middleware` |
| Heartbeat + consumer watchdog | `pip install azure-bootstrap[heartbeat]` | `azure_bootstrap.heartbeat` |
| Dynamic log-level refresh | `pip install azure-bootstrap[config-refresh]` | `azure_bootstrap.config_refresh` |
| Tenacity retry wrappers | `pip install azure-bootstrap[retry]` | `azure_bootstrap.retry` |
| 4-gate attachment classifier | `pip install azure-bootstrap[ingress]` | `azure_bootstrap.ingress` |
| TokenBucket rate-limiter | `pip install azure-bootstrap[ratelimit]` | `azure_bootstrap.ratelimit` |
| Two-tier notification builders + throttle | `pip install azure-bootstrap[notify]` | `azure_bootstrap.notify` |
| Subscription renewal loop | `pip install azure-bootstrap[subscription]` | `azure_bootstrap.subscription` |
| Graph webhook + API-key helpers | `pip install azure-bootstrap[auth]` (pair with `[fastapi]`) | `azure_bootstrap.auth` |

### Tier 3 — advanced opt-in extras

| Need | Install | Import path |
| --- | --- | --- |
| Service Bus DLQ + consumer wrapper | `pip install azure-bootstrap[servicebus]` | `azure_bootstrap.servicebus` |
| Service Bus message lock | `pip install azure-bootstrap[sb-lock]` (pair with `[servicebus]`) | `azure_bootstrap.sb_lock` |
| AI token & cost accounting | `pip install azure-bootstrap[openai]` | `azure_bootstrap.openai` |
| HMAC-signed action tokens | `pip install azure-bootstrap[tokens]` | `azure_bootstrap.tokens` |
| NCRONTAB → APScheduler | `pip install azure-bootstrap[scheduler]` | `azure_bootstrap.scheduler` |
| `/api/metrics` aggregation | `pip install azure-bootstrap[metrics]` | `azure_bootstrap.metrics` |
| PDF action stripping | `pip install azure-bootstrap[pdf-safety]` | `azure_bootstrap.pdf_safety` |

### Everything at once

```bash
pip install 'azure-bootstrap[all]'
```

## Examples library

The [examples/](examples/) directory holds 38 numbered single-concept
files and 3 end-to-end app templates. Each numbered file demonstrates
one v2 primitive in 50–200 lines. See
[examples/README.md](examples/README.md) for the reading order; the
suggested adoption order below cross-references the relevant examples.

## Behavior changes you might notice

- **Two `ExtraFieldsFormatter` classes coexist.** The v1 class at
  `azure_bootstrap.services.bootstrap_logging.ExtraFieldsFormatter` is
  unchanged — it still renders extras as ` | {json}`. The new v2 class at
  `azure_bootstrap.logging.formatter.ExtraFieldsFormatter` renders extras as
  `key='value'` pairs after a two-space gap. **`configure_logging()` installs
  the v2 formatter.** If you call `initialize_application()` (v1) without
  calling `configure_logging()`, you get the v1 format.

- **`DEBUG_LOGGING_ENABLED` is now a required second factor for DEBUG.**
  Setting `LOG_LEVEL=DEBUG` alone produces INFO output. Both `LOG_LEVEL=DEBUG`
  and `DEBUG_LOGGING_ENABLED=true` are needed. This is belt-and-suspenders
  against a stray manifest leaking DEBUG into prod. Add it explicitly to your
  dev `local.settings.json` if you want DEBUG output locally.

- **`@traced(alert_on_error=…)` will silently fail without the `alerts` extra.**
  Tracing is Tier 1 and works fine without alerts installed. When alerts is
  missing, the `alert_on_error` path is a no-op — only the log line fires.
  Install `azure-bootstrap[alerts]` to enable.

- **Noisy loggers (pdfminer, urllib3, azure.identity, etc.) are silenced by
  default** when you call `configure_logging()`. Pass
  `silence_defaults=False` if you need the firehose.

## What didn't change

- `initialize_application()` signature, return type, and 4-phase behavior.
- `get_bootstrap_logger()` signature and return type.
- `telemetry_manager` singleton identity.
- All 16 non-version exports in v1's `__all__`.
- The CI/CD workflow at `.github/workflows/ci-cd.yml`.
- The package's Python requirement (`>=3.11`).

## Suggested adoption order (Parts 2 + 3)

After landing the v2 quick-start (see
[examples/01_quickstart.py](examples/01_quickstart.py)), adopt the
defensive/security primitives in this order — each step is
independently valuable so you can stop whenever the next module isn't
relevant to your project:

1. **`azure_bootstrap.failclose`** — Replace `os.environ.get(...) or raise
   ConfigurationError(...)` patterns with `require_env(name)`. Lowest
   friction, immediate clarity. See
   [examples/24_failclose.py](examples/24_failclose.py).
2. **`azure_bootstrap.exceptions`** — Subclass `UnrecoverableError` for
   your dead-letter-worthy errors; let everything else fall under
   `TransientError`. The `is_unrecoverable(exc)` classifier then drives
   the consumer wrapper's routing. See
   [examples/08_exception_hierarchy.py](examples/08_exception_hierarchy.py).
3. **`azure_bootstrap.softfail`** — Wrap optional sub-features (AI
   summarization, third-party enrichment) so a single failure produces a
   degraded result rather than killing the pipeline. See
   [examples/09_soft_fail.py](examples/09_soft_fail.py).
4. **`azure_bootstrap.validation`** — Replace ad-hoc queue payload
   parsing with `queue_message_schema(...)`. Catches poison messages
   cheaply at the consumer entry point. See
   [examples/11_validation.py](examples/11_validation.py).
5. **`azure_bootstrap.path_safety` + `azure_bootstrap.ingress`** — If
   your pipeline touches user-supplied filenames or attachment bytes,
   the bidi-stripping segment sanitizer + four-gate classifier are the
   minimum bar. See [examples/12_path_safety.py](examples/12_path_safety.py)
   and [examples/15_ingress_classifier.py](examples/15_ingress_classifier.py).
6. **`azure_bootstrap.retry`** — Replace ad-hoc tenacity wrappers with
   `retry_azure_transient(...)` / `retry_ai_transient(...)`. Free
   counter wiring + `before_sleep_log`. See
   [examples/14_retry.py](examples/14_retry.py).
7. **`azure_bootstrap.audit.build_audit_extra`** — Replace `extra={...}`
   at audit log sites with the helper. Single source of masking +
   truncation conventions. See
   [examples/23_audit_logs.py](examples/23_audit_logs.py).
8. **`azure_bootstrap.identity.build_credential`** — Replace ad-hoc
   `DefaultAzureCredential()` instantiation. Prefers Workload Identity
   without any code changes on your part. See
   [examples/22_identity.py](examples/22_identity.py).
9. **`azure_bootstrap.auth.install_graph_webhook_route`** — Replace
   hand-rolled Graph webhook handlers. Validation handshake, clientState
   verification, dedup, rate limiting, background dispatch — all wired.
   See [examples/25_webhook_route.py](examples/25_webhook_route.py).
10. **`azure_bootstrap.sb_lock.lock_for_process`** + Service Bus
    `handle_message` — Wrap existing consumers; the wrapper handles
    schema validation, correlation scoping, and dead-letter routing.
    See [examples/26_sb_lock.py](examples/26_sb_lock.py) and
    [examples/21_consumer_wrapper.py](examples/21_consumer_wrapper.py).

For complete app skeletons see the three end-to-end templates:
[examples/e2e_azure_function.py](examples/e2e_azure_function.py),
[examples/e2e_fastapi_pipeline.py](examples/e2e_fastapi_pipeline.py),
[examples/e2e_aks_sb_worker.py](examples/e2e_aks_sb_worker.py).
