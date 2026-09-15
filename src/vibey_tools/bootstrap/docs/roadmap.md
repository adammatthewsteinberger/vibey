# Roadmap

**Goal:** the one-call, fail-closed cross-cutting layer for Azure workloads — bootstrap chain, outbox delivery, tamper-evident audit, bounded retry, optional-by-extra transports.

This roadmap is **living** (vibey-gh#211): it stays active until the goal above is
achieved and every active contributor has clearly agreed the project is done —
neither is ever assumed. Changes requested while this file is stale are treated as
a risk requiring human confirmation.

## Now

- Doctrine wave: paper published.
- 100% per-module coverage enforced; the delivery and audit theorems pinned by test.

## Next

- Transport growth by demand, always optional-by-extra.
- Track Azure SDK CVE churn (the pinned-floor discipline in pyproject).

## Done means

Every family service bootstraps through one call with zero copy-pasted infrastructure code, and contributors sign off the layer is feature-complete.

*Maintained by the contributors; the exact-head review flags this page when it goes
stale against the changelog.*
