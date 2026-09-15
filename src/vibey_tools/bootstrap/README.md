# vibey-bootstrap

> **Now part of the vibey monorepo.** `vibey-bootstrap` lives in [the-vibey-project/vibey](https://github.com/the-vibey-project/vibey) at [`src/vibey_tools/bootstrap`](https://github.com/the-vibey-project/vibey/tree/develop/src/vibey_tools/bootstrap) (vibey ADR-0021). It is still published on PyPI as [`vibey-bootstrap`](https://pypi.org/project/vibey-bootstrap/).

> The cross-cutting layer for Azure Functions, FastAPI services, and AKS workers.
> One call bootstraps logging → App Configuration + Key Vault → Application Insights
> and hands you a populated `os.environ`. Everything past that (alerts, tracing,
> Service Bus, ten log transports, a scaffold CLI) is opt-in via pip extras.
> Used across 17+ Azure Functions repos at Vizius.

Formerly **azure-bootstrap** — see [NOTICE.md](https://github.com/the-vibey-project/vibey/blob/develop/src/vibey_tools/bootstrap/NOTICE.md).

[![PyPI](https://img.shields.io/pypi/v/vibey-bootstrap.svg)](https://pypi.org/project/vibey-bootstrap/)
[![Downloads](https://img.shields.io/pypi/dm/vibey-bootstrap.svg)](https://pypi.org/project/vibey-bootstrap/)
[![Python](https://img.shields.io/pypi/pyversions/vibey-bootstrap.svg)](https://pypi.org/project/vibey-bootstrap/)
[![CI/CD](https://github.com/the-vibey-project/vibey/actions/workflows/ci.yml/badge.svg)](https://github.com/the-vibey-project/vibey/actions/workflows/ci.yml)
[![Docs](https://img.shields.io/badge/docs-usage%20guide-blue.svg)](https://github.com/the-vibey-project/vibey/blob/develop/src/vibey_tools/bootstrap/docs/USAGE.md)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](https://github.com/the-vibey-project/vibey/blob/develop/src/vibey_tools/bootstrap/LICENSE)

## Why

Every Azure app hits the same startup deadlock: you need logging to report
config loading, but App Insights logging needs config to initialize. Most repos
solve it with a copy-pasted `src/infrastructure/` folder that drifts. This
library is that folder, done once, tested, and versioned.

The **four-phase bootstrap** breaks the cycle:

1. **Console logging** — works immediately, before anything loads.
2. **Telemetry from env** — App Insights if `APPLICATIONINSIGHTS_CONNECTION_STRING` is already set.
3. **Configuration** — Azure App Configuration + Key Vault references → `os.environ`.
   Local values (`local.settings.json`, your shell) always win; nothing is overwritten.
4. **Telemetry upgrade** — if the connection string only arrived via config, upgrade now.

Guarantees: the v1 API surface is preserved byte-identical across v2, v3, and v4
(v4 changes only the distribution and import name — see
[MIGRATING-TO-V4.md](https://github.com/the-vibey-project/vibey/blob/develop/src/vibey_tools/bootstrap/MIGRATING-TO-V4.md)); every
extra is opt-in and most are stdlib-only; log transports never block, never raise,
and use a bounded buffer. `USE_MOCK_BOOTSTRAP=true` runs everything without Azure.

## Quick start

```bash
pip install vibey-bootstrap
```

```python
import os
from vibey_bootstrap import initialize_application, get_bootstrap_logger

logger = get_bootstrap_logger(__name__)   # usable before bootstrap completes
config_repo = initialize_application()     # runs all four phases

db_host = os.getenv("DATABASE_HOST")       # App Config + Key Vault values are in os.environ
```

Requires Python 3.11+. Falls back to plain environment variables when App
Configuration is not configured, so the same code runs locally and in Azure.

## Worked example: production-grade logging in four lines

```python
from vibey_bootstrap.alerts import install_global_exception_hooks, register_dispatcher
from vibey_bootstrap.bootstrap import ensure_bootstrap
from vibey_bootstrap.logging import configure_logging


def my_email_sender(recipients, subject, html_body):
    ...  # any callable with this signature (Graph, SendGrid, ACS)


configure_logging()
install_global_exception_hooks()
ensure_bootstrap()
register_dispatcher(my_email_sender, recipients=["dev-alerts@example.com"])
```

After this, every line emitted through stdlib `logging` carries a correlation
ID, extra fields render as greppable `key=repr(value)` pairs, noisy third-party
loggers are silenced, and uncaught exceptions fire CRITICAL alerts with dedup,
rate-limiting, and escalation. Runnable version:
[examples/01_quickstart.py](https://github.com/the-vibey-project/vibey/blob/develop/src/vibey_tools/bootstrap/examples/01_quickstart.py).

## What's in the box

| Layer | Install | You get |
| --- | --- | --- |
| **v1 core** | `vibey-bootstrap` | Four-phase bootstrap, `EnhancedConfigRepository`, `TelemetryManager` |
| **v2 Tier 1** (always on, stdlib) | `vibey-bootstrap` | Structured logging, correlation IDs, masking, `@traced`, counters, error vocabulary, soft-fail, phases, validation, path safety, fail-close env helpers |
| **v2 Tier 2/3** (opt-in) | `[alerts]`, `[fastapi]`, `[servicebus]`, `[retry]`, … | Tiered alerts, FastAPI middleware, health probes, heartbeat, Service Bus consumer + DLQ, webhook auth, ingress hardening, HMAC tokens, AI usage tracker |
| **v3** (opt-in) | `[logging-all]`, `[db]`, `[email]`, `[http]`, `[aks]`, … | Ten log transports, SQLAlchemy + outbox, ACS email, hardened HTTP client, DocumentDB factory, AKS runtime helpers, governance, `vibey-bootstrap` scaffold CLI |

```bash
# Common combinations
pip install 'vibey-bootstrap[alerts,fastapi,health]'
pip install 'vibey-bootstrap[servicebus,sb-lock,retry,heartbeat]'
pip install 'vibey-bootstrap[all]'
```

The full extras matrix (40+ extras, what each pulls in, when you need it) is in
the [Usage Guide](https://github.com/the-vibey-project/vibey/blob/develop/src/vibey_tools/bootstrap/docs/USAGE.md#1-installation--extras).

<details>
<summary>Feature inventory by release</summary>

**v2** — structured logging (`ExtraFieldsFormatter`, `correlation_scope`,
secret/email/control-char masking, noisy-logger silencing) · `@traced` with
latency histograms and slow-budget alerts · `alert_dev_team` with WARN / ERROR /
CRITICAL, dedup + rate-limit + escalation, `install_global_exception_hooks` ·
`PipelineError` → `UnrecoverableError` / `TransientError` with `is_unrecoverable`,
soft-fail and per-phase guards · 4-gate attachment classifier (extension → MIME →
size → magic bytes), zip-bomb defense, PDF action stripping, filename sanitizer +
root confinement · Service Bus `handle_message` with dead-letter-vs-abandon
routing and `lock_for_process` · `install_graph_webhook_route` with validation
handshake, clientState verification, dedup, rate limit · AI usage tracker (tokens
+ cost, sliding windows, soft TPM cap) · health probes, FastAPI middleware,
heartbeat + consumer watchdog, dynamic log-level refresh, DLQ digest with
HMAC-signed resubmit tokens, `/api/metrics` aggregator.

**v3** — ten logging transports (console, App Insights, Sumo Logic, Panther, file,
blob, SQL, NoSQL, ADX, Event Hubs; all share `_BufferedShipper` guarantees) ·
SQLAlchemy session factory, Alembic helpers, transactional outbox · `AcsEmailSender`
· hardened sync `requests` session + optional async `httpx` · Mongo/Cosmos client
factory from env · AKS `build_info`, SIGTERM handlers, leader-election stub ·
budget guard + usage tracking hooks · `vibey-bootstrap list|scaffold` for
Terraform/Bicep/Helm/GitOps/CI/policy templates.

Every entry is cataloged by tier in the
[CHANGELOG](https://github.com/the-vibey-project/vibey/blob/develop/src/vibey_tools/bootstrap/CHANGELOG.md).

</details>

## Examples

[examples/](https://github.com/the-vibey-project/vibey/tree/develop/src/vibey_tools/bootstrap/examples/)
holds 46 numbered single-concept files plus 3 end-to-end app templates. Every
file runs with `USE_MOCK_BOOTSTRAP=true` and ends with an `# ── Expected output ──`
block. Start with:

| File | Concept |
| --- | --- |
| [01_quickstart.py](https://github.com/the-vibey-project/vibey/blob/develop/src/vibey_tools/bootstrap/examples/01_quickstart.py) | 30-second setup |
| [03_correlation_scope.py](https://github.com/the-vibey-project/vibey/blob/develop/src/vibey_tools/bootstrap/examples/03_correlation_scope.py) | Correlation IDs across nested calls |
| [09_soft_fail.py](https://github.com/the-vibey-project/vibey/blob/develop/src/vibey_tools/bootstrap/examples/09_soft_fail.py) | Degraded-result pattern |
| [21_consumer_wrapper.py](https://github.com/the-vibey-project/vibey/blob/develop/src/vibey_tools/bootstrap/examples/21_consumer_wrapper.py) | Service Bus handler |
| [39_v3_transports.py](https://github.com/the-vibey-project/vibey/blob/develop/src/vibey_tools/bootstrap/examples/39_v3_transports.py) | All ten log sinks |
| [e2e_azure_function.py](https://github.com/the-vibey-project/vibey/blob/develop/src/vibey_tools/bootstrap/examples/e2e_azure_function.py) | Full Azure Function |
| [e2e_fastapi_pipeline.py](https://github.com/the-vibey-project/vibey/blob/develop/src/vibey_tools/bootstrap/examples/e2e_fastapi_pipeline.py) | Full FastAPI app |
| [e2e_aks_sb_worker.py](https://github.com/the-vibey-project/vibey/blob/develop/src/vibey_tools/bootstrap/examples/e2e_aks_sb_worker.py) | Full AKS Service Bus consumer |

Reading order and per-example extras:
[examples/README.md](https://github.com/the-vibey-project/vibey/blob/develop/src/vibey_tools/bootstrap/examples/README.md).

## Docs & links

- **[Documentation](https://github.com/the-vibey-project/vibey/tree/develop/src/vibey_tools/bootstrap/docs)** — usage guide, migration guides, and the generator for the API reference covering all 45 public packages
- **[Usage Guide](https://github.com/the-vibey-project/vibey/blob/develop/src/vibey_tools/bootstrap/docs/USAGE.md)** — installation & extras matrix, every subpackage, three end-to-end recipes, TypeScript/Next.js integration
- **API Reference** — rendered from docstrings and signatures at docs-build time by [`docs/gen_pages.py`](https://github.com/the-vibey-project/vibey/blob/develop/src/vibey_tools/bootstrap/docs/gen_pages.py); the standalone Pages site that hosted it has been retired
- **[CHANGELOG](https://github.com/the-vibey-project/vibey/blob/develop/src/vibey_tools/bootstrap/CHANGELOG.md)** · **[v1 → v2](https://github.com/the-vibey-project/vibey/blob/develop/src/vibey_tools/bootstrap/MIGRATING-FROM-V1.md)** · **[v2 → v3](https://github.com/the-vibey-project/vibey/blob/develop/src/vibey_tools/bootstrap/MIGRATING-TO-V3.md)** (additive) · **[v3 → v4](https://github.com/the-vibey-project/vibey/blob/develop/src/vibey_tools/bootstrap/MIGRATING-TO-V4.md)** (rename only; pin `vibey-bootstrap>=4,<5`)
- **[PyPI](https://pypi.org/project/vibey-bootstrap/)** · **[Issues](https://github.com/the-vibey-project/vibey/issues)** · **[Security policy](https://github.com/the-vibey-project/vibey/blob/develop/src/vibey_tools/bootstrap/SECURITY.md)**

## Related projects

Part of the same open-source family — MIT, on PyPI:

- **[claudeloop](https://github.com/the-vibey-project/vibey/tree/develop/src/vibey_runners/claude)** · **[codexloop](https://github.com/the-vibey-project/vibey/tree/develop/src/vibey_runners/codex)** · **[cursorloop](https://github.com/the-vibey-project/vibey/tree/develop/src/vibey_runners/cursor)** · **[agyloop](https://github.com/the-vibey-project/vibey/tree/develop/src/vibey_runners/agy)** — autonomous coding-session runners with the same contract, different vendor
- **[vibey](https://github.com/the-vibey-project/vibey)** — six-phase queue conductor over the loop runners — background reading: the [vibey research paper](https://the-vibey-project.github.io/vibey/main/paper/) ([PDF](https://the-vibey-project.github.io/vibey/main/paper.pdf)) and the vibey book ([PDF](https://the-vibey-project.github.io/vibey/main/book.pdf), [EPUB](https://the-vibey-project.github.io/vibey/main/book.epub), [print HTML](https://the-vibey-project.github.io/vibey/main/book-print.html)).
- **[vibey-skills](https://github.com/the-vibey-project/vibey/tree/develop/src/vibey_tools/skills)** — Claude Code plugin marketplace: 127 plugins / 644 Agent Skills (includes a plugin for this library)
- **[homebrew-tap](https://github.com/adammatthewsteinberger/homebrew-tap)** — `brew tap adammatthewsteinberger/tap`
- **[clippy-pet](https://github.com/adammatthewsteinberger/clippy-pet)** — the fun one

## Contributing

```bash
git clone https://github.com/the-vibey-project/vibey.git
cd vibey/src/vibey_tools/bootstrap             # vibey-bootstrap lives here in the vibey monorepo
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev,test,all]"
pytest -m "not integration"          # unit suite with coverage
```

Branch from `develop`, Conventional Commits, PRs need green CI (unit + integration
+ docs build). Coverage floor is 85% (90% for new code). Details in
[CONTRIBUTING.md](https://github.com/the-vibey-project/vibey/blob/develop/src/vibey_tools/bootstrap/CONTRIBUTING.md);
AI-assistant context lives in
[CLAUDE.md](https://github.com/the-vibey-project/vibey/blob/develop/src/vibey_tools/bootstrap/CLAUDE.md).

## License & attribution

MIT — see [LICENSE](https://github.com/the-vibey-project/vibey/blob/develop/src/vibey_tools/bootstrap/LICENSE). Originally developed as
TheViziusGroup/azure-bootstrap while at The Vizius Group; republished here as
adammatthewsteinberger/vibey-bootstrap with The Vizius Group's permission — see
[NOTICE.md](https://github.com/the-vibey-project/vibey/blob/develop/src/vibey_tools/bootstrap/NOTICE.md).

---

Built by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com) · [more open source](https://vibewithadam.matthewsteinberger.com/open-source)
