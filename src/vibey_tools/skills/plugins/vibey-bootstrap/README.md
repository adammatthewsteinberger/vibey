# Azure Bootstrap Plugin

Formerly the `azure-bootstrap` plugin — the library was renamed **vibey-bootstrap** in 4.0.0 (import `vibey_bootstrap`, CLI `vibey-bootstrap`).

Usage reference for the **Azure Bootstrap Library** (`vibey-bootstrap`, v4.0.0) — a pure
Python package (PyPI, MIT, Python ≥ 3.11) that solves the logging↔configuration circular
dependency at Azure Functions / container app startup, then layers on a framework-agnostic
cross-cutting layer (structured logging, correlation, tracing, counters, tiered alerts,
ingress hardening, Service Bus plumbing, webhook auth, AI usage tracking, health probes,
ten logging transports, DB/outbox, ACS email, hardened HTTP, AKS runtime, governance, and
an `vibey-bootstrap` scaffold CLI).

- **vibey-bootstrap-core**: Installation and the optional-extras matrix (v2 + v3), plus the v1 4-phase bootstrap — `initialize_application`, configuration precedence and the local-override rule, the config repository / secrets repository API, interfaces, exceptions, v1 environment variables, and the `vibey-bootstrap` CLI entry point.
- **vibey-bootstrap-primitives**: v2 Tier 1 always-on stdlib primitives and all ten logging transports (console, App Insights, Sumo Logic, Panther, file, blob, sql, nosql, ADX, Event Hubs).
- **vibey-bootstrap-subpackages**: Opt-in Tier 2 / Tier 3 subpackages, v3 runtime modules (db/outbox, email, http, documentdb, aks, governance, scaffold templates), v3 extensions (HMAC verify, async Service Bus, audit chain, tenant credentials), and four end-to-end recipes.
- **vibey-bootstrap-typescript**: Consuming a Python backend that uses the library from Next.js (API-key endpoints, Graph-style webhook, health probes, `/api/metrics`), porting the framework-agnostic primitives natively to TypeScript (including HMAC action tokens that interoperate byte-for-byte with Python), and the master environment-variable / testing / troubleshooting appendices.
