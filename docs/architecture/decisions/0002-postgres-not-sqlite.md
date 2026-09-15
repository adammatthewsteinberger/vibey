# 0002 — PostgreSQL, not SQLite, for the queue and ledger

**Status:** accepted · **Date:** 2026-08-14

**Owes:** nothing — mechanism (ADR-0020)

## Context

Vibey must run on a laptop. SQLite is the natural instinct for a local tool: no
daemon, one file, zero setup. Vibey's workload is N concurrent worker processes
claiming jobs, plus an append-only event ledger with payload queries.

## Decision

**PostgreSQL 17.** Vibey connects to the database named by `VIBEY_PG_URL` and
refuses to start without it (`bootstrap.py::database_url()` raises
`DatabaseNotConfigured`); there is deliberately no silent local default. Schema
migrations live in `migrations/` and are resolved relative to the package, so a
source checkout and the container image use the same files.

A three-step resolver — an explicit `--pg-url`, then a Docker/Podman Compose
service, then a local `pg_ctl` cluster under `.vibey/pgdata` — is designed but not
built. The silent fallback to `postgresql://<user>@localhost:5432/vibey` that once
stood in for it was removed after autonomous BUILD jobs running the test suite
with `VIBEY_PG_URL` unset wrote 78 projects into the operator's real database in
eleven minutes; the docstring on `database_url()` records the incident.

## Rationale

The disqualifying issue is concrete and not a matter of taste: **SQLite has no
row-level locking, therefore no `SELECT … FOR UPDATE SKIP LOCKED`.** WAL mode
solves reader/writer blocking; vibey's contention is writer/writer — several
workers competing to claim the next job. The standard SQLite workaround
(mark-a-row-locked, then return it) leaks: if the worker dies after the mark, that
row stays locked forever. Surviving worker death is a core requirement (workers
*will* be killed; the reaper is the design), so a queue that leaks on crash is not
a candidate.

Postgres additionally gives (the first five are in use today; partitioning is
reserved for when the ledger grows):

| Feature | Used for |
|---|---|
| `FOR UPDATE SKIP LOCKED` | job claim |
| `LISTEN` / `NOTIFY` | worker wakeup without polling (`vibey_job_ready`); a raised gate also sends `vibey_gate_raised`, which nothing listens to yet |
| `jsonb` + GIN | ledger payload queries and projections (`event_payload_gin`) |
| advisory locks | serializing `build.integrate` per `(project_id, cycle)` ([ADR-0029](0029-integrate-serialized-by-advisory-lock.md)) |
| `CHECK` constraints | making "credits never have a reset time" unrepresentable (`engine_health.credits_never_have_a_deadline`) |
| range partitioning | planned, not used: no table is partitioned today |

Phase transitions are not serialized by a lock; `project` rows move by a
compare-and-set `UPDATE … WHERE phase = $expected`, so a stale transition
matches no row.

## Consequences

**Good.** The queue is correct under concurrency and crash. Ledger queries are
real queries. The same storage substrate as the sibling `apg-*` projects, so the
operational knowledge already exists.

**Bad.** A "local tool" now needs a database. This is real friction and the main
cost of this decision.

**Mitigation (partial).** Today the operator supplies `VIBEY_PG_URL`; a missing
value fails immediately with the exact `export` line to run rather than guessing.
On Kubernetes the Helm chart runs an in-cluster `postgres:17-alpine` by default
(`postgres.enabled` in `deploy/helm/vibey/values.yaml`) or points at a managed
instance through an existing secret; see [ADR-0025](0025-kubernetes-operator-crd-keda.md).
The planned `vibey up` command, with the three fallbacks above and matching
`vibey doctor` diagnostics, is what would make a laptop install zero-config; it is
not implemented.

## Alternatives rejected

- **SQLite + WAL.** Disqualified above.
- **Redis.** Adds a daemon *and* loses durability guarantees and relational
  queries. If a daemon is acceptable, Postgres strictly dominates.
- **Filesystem queue (directories + `flock`).** What the `*loop` runners' `inbox/`
  does for single-run control. It does not survive multi-worker contention or give
  dependency ordering, and it makes the ledger unqueryable.
- **An embedded durable-execution library (DBOS-style).** The 2026 pattern for
  this shape, and attractive — but it is Postgres-backed anyway, so it does not
  remove the dependency; it only adds a framework on top of it.
