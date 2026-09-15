# vibey-bootstrap examples (v2 + v3)

A flat, numbered, copy-paste-friendly library of usage examples. Each numbered
file demonstrates one concept and runs in isolation; every file is self-contained
(no shared helpers) so you can drop one into your project and it works.

**Current library version:** `3.0.0` — see [MIGRATING-TO-V3.md](../MIGRATING-TO-V3.md)
for v3-only features (db/outbox, email, HTTP client, AKS runtime, scaffold CLI,
ten logging transports).

## 30-second quick start

```python
from vibey_bootstrap.alerts import install_global_exception_hooks, register_dispatcher
from vibey_bootstrap.bootstrap import ensure_bootstrap
from vibey_bootstrap.logging import configure_logging


def my_email_sender(recipients, subject, html_body):
    ...  # any callable matching this signature


configure_logging()
install_global_exception_hooks()
ensure_bootstrap()
register_dispatcher(my_email_sender, recipients=["dev-alerts@example.com"])
```

See [01_quickstart.py](01_quickstart.py) for a runnable version with a mock sender.

## Running the examples

```bash
# Most examples short-circuit Azure calls in mock mode:
export USE_MOCK_BOOTSTRAP=true

# Some examples reset shared state (counters, latency histograms):
export AZURE_BOOTSTRAP_ALLOW_RESET=1

# Run any example directly:
python examples/01_quickstart.py
```

## Reading order

The files are numbered roughly by how foundational they are — start at 01 and read
until you stop seeing relevant patterns.

| # | File | Use this if you need to … |
| --- | ---- | ------------------------- |
| 01 | [01_quickstart.py](01_quickstart.py) | Set up a brand-new project with production-grade defaults in 30 seconds |
| 02 | [02_structured_logging.py](02_structured_logging.py) | Format extras as greppable `key=repr` pairs; mask secrets at the call site |
| 03 | [03_correlation_scope.py](03_correlation_scope.py) | Propagate correlation IDs across nested sync + async calls |
| 04 | [04_traced_decorator.py](04_traced_decorator.py) | Add latency + alert-on-error to any function with one decorator |
| 05 | [05_slow_thresholds.py](05_slow_thresholds.py) | Get a WARN alert when an operation breaches its time budget |
| 06 | [06_counters.py](06_counters.py) | Track best-effort observability counts across threads |
| 07 | [07_local_settings.py](07_local_settings.py) | Use `local.settings.json` for dev without overriding existing env |
| 08 | [08_exception_hierarchy.py](08_exception_hierarchy.py) | Classify pipeline errors as dead-letter vs retry |
| 09 | [09_soft_fail.py](09_soft_fail.py) | Continue with a degraded result when an optional sub-feature breaks |
| 10 | [10_phases.py](10_phases.py) | Run a multi-stage pipeline where one stage's bug must not nuke the rest |
| 11 | [11_validation.py](11_validation.py) | Reject poison queue payloads before downloading blobs |
| 12 | [12_path_safety.py](12_path_safety.py) | Defend filename interpolation against bidi-overrides + path traversal |
| 13 | [13_security_compare.py](13_security_compare.py) | Compare API keys / tokens in constant time |
| 14 | [14_retry.py](14_retry.py) | Wrap Azure/AI calls with tenacity + counter conventions |
| 15 | [15_ingress_classifier.py](15_ingress_classifier.py) | Run the four-gate ingress pipeline |
| 16 | [16_zip_bomb_defense.py](16_zip_bomb_defense.py) | Reject archives with excessive entries or uncompressed size |
| 17 | [17_ratelimit.py](17_ratelimit.py) | Add per-endpoint token-bucket rate limiting to FastAPI |
| 18 | [18_notify.py](18_notify.py) | Build sender-vs-dev email bodies without leaking forensics |
| 19 | [19_subscription.py](19_subscription.py) | Renew Graph webhook subscriptions in a SIGTERM-responsive loop |
| 20 | [20_pdf_sanitize.py](20_pdf_sanitize.py) | Strip JavaScript / OpenAction from untrusted PDFs |
| 21 | [21_consumer_wrapper.py](21_consumer_wrapper.py) | Dispatch Service Bus messages with DLQ vs abandon classification |
| 22 | [22_identity.py](22_identity.py) | Pick the right Azure credential without hardcoding defaults |
| 23 | [23_audit_logs.py](23_audit_logs.py) | Emit audit lines with masking + truncation + ISO-8601 timestamps |
| 24 | [24_failclose.py](24_failclose.py) | Codify fail-closed for auth, fail-open for features |
| 25 | [25_webhook_route.py](25_webhook_route.py) | Wire a Graph-style webhook with handshake + dedup + rate limit |
| 26 | [26_sb_lock.py](26_sb_lock.py) | Hold Service Bus message locks across long-running handlers |
| 27 | [27_alerts_dispatcher.py](27_alerts_dispatcher.py) | Send WARN / ERROR / CRITICAL alerts with dedup + escalation |
| 28 | [28_global_exception_hooks.py](28_global_exception_hooks.py) | Page on-call for uncaught sync + asyncio exceptions |
| 29 | [29_health_probes.py](29_health_probes.py) | Implement `/health/live` + `/health/ready` for Kubernetes |
| 30 | [30_fastapi_middleware.py](30_fastapi_middleware.py) | Time every request, suppress probe noise, alert on 5xx |
| 31 | [31_heartbeat_watchdog.py](31_heartbeat_watchdog.py) | Watchdog a stuck consumer; emit pulse logs on a heartbeat |
| 32 | [32_config_refresh.py](32_config_refresh.py) | Flip `LOG_LEVEL` in App Config without redeploy |
| 33 | [33_dlq_digest.py](33_dlq_digest.py) | Send a daily DLQ digest with embedded pending-alerts summary |
| 34 | [34_dlq_resubmit_tokens.py](34_dlq_resubmit_tokens.py) | Issue HMAC-signed action tokens for DLQ resubmit links |
| 35 | [35_openai_tracker.py](35_openai_tracker.py) | Track AI cost + tokens; alert on threshold breach |
| 36 | [36_scheduler.py](36_scheduler.py) | Parse 5- or 6-field NCRONTAB into APScheduler CronTrigger |
| 37 | [37_metrics_endpoint.py](37_metrics_endpoint.py) | Expose latency + counters + AI usage at `/api/metrics` |
| 38 | [38_logging_transports.py](38_logging_transports.py) | Toggle console / App Insights / Sumo Logic via registry |
| **39** | **[39_v3_transports.py](39_v3_transports.py)** | **v3:** enable all ten logging transports (panther, file, blob, sql, nosql, adx, event_hubs) |
| **44** | **[44_db_outbox_email.py](44_db_outbox_email.py)** | **v3:** SQLAlchemy session + transactional outbox + ACS email drain |
| **45** | **[45_http_client.py](45_http_client.py)** | **v3:** hardened `requests` session with retry + correlation headers |
| **46** | **[46_scaffold_cli.py](46_scaffold_cli.py)** | **v3:** `vibey-bootstrap` CLI + Python API for Terraform/Bicep/Helm/GitOps templates |

> Examples 40–43 were reserved during planning; v3 content uses 39, 44–46.

## v3 examples — required extras

| Example | Install |
| --- | --- |
| 39 | `pip install vibey-bootstrap[logging-all]` (or individual `[panther]`, `[bloblog]`, `[sqllog]`, `[nosqllog]`, `[adxlog]`, `[eventhubslog]`) |
| 44 | `pip install vibey-bootstrap[db,email]` + `DATABASE_URL`, `ACS_*` env |
| 45 | `pip install vibey-bootstrap[http]` |
| 46 | base install (`vibey-bootstrap` console script included) |

## By tier

| Tier 1 (stdlib only) | Tier 2 (opt-in) | Tier 3 (advanced) | v3 (3.0.0) |
| --- | --- | --- | --- |
| 01–13, 22–24 | 14–19, 27–32, 38 | 20–21, 25–26, 33–37 | 39, 44–46 |
| | 17, 29–31 | | |

## pip extras (v2 + v3)

| Example | Required extra |
| --- | --- |
| 14_retry | `[retry]` |
| 17, 25, 29–30, 37 | `[fastapi]` |
| 20_pdf_sanitize | `[pdf-safety]` |
| 32, 36 | `[scheduler]` |
| 38 | `[transports]` + `[sumologic]` for Sumo |
| 39 | `[logging-all]` or per-transport extras |
| 44 | `[db]`, `[email]` |
| 45 | `[http]` |
| 46 | core (scaffold CLI) |
| Everything else | base install only |

## End-to-end app templates

- [e2e_azure_function.py](e2e_azure_function.py) — Azure Function with lazy bootstrap, correlation, `@traced`, audit
- [e2e_fastapi_pipeline.py](e2e_fastapi_pipeline.py) — FastAPI + Graph webhook + health + metrics
- [e2e_aks_sb_worker.py](e2e_aks_sb_worker.py) — AKS Service Bus consumer with heartbeat + SIGTERM

For v3 AKS helpers (`build_info`, `install_sigterm_handler`, leader election), see
[docs/USAGE.md](../docs/USAGE.md) § v3 additions and [MIGRATING-TO-V3.md](../MIGRATING-TO-V3.md).

## Contributing

When you add a module to `vibey_bootstrap/`, add a numbered example and a row in
the **Reading order** table above.
