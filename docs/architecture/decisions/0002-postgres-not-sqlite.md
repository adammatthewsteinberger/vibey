# 0002 — PostgreSQL, not SQLite, for the queue and ledger

**Status:** accepted · **Date:** 2026-08-14

## Context

Vibey must run on a laptop. SQLite is the natural instinct for a local tool: no
daemon, one file, zero setup. Vibey's workload is N concurrent worker processes
claiming jobs, plus an append-only event ledger with payload queries.

## Decision

**PostgreSQL 17.** `vibey up` resolves a database in three steps: an existing
instance via `--pg-url`, a Docker/Podman Compose service, or a local `pg_ctl`
cluster initialized under `.vibey/pgdata`.

## Rationale

The disqualifying issue is concrete and not a matter of taste: **SQLite has no
row-level locking, therefore no `SELECT … FOR UPDATE SKIP LOCKED`.** WAL mode
solves reader/writer blocking; vibey's contention is writer/writer — several
workers competing to claim the next job. The standard SQLite workaround
(mark-a-row-locked, then return it) leaks: if the worker dies after the mark, that
row stays locked forever. Surviving worker death is a core requirement (workers
*will* be killed; the reaper is the design), so a queue that leaks on crash is not
a candidate.

Postgres additionally gives, all of which vibey uses:

| Feature | Used for |
|---|---|
| `FOR UPDATE SKIP LOCKED` | job claim |
| `LISTEN` / `NOTIFY` | worker wakeup without polling |
| `jsonb` + GIN | ledger payload queries and projections |
| advisory locks | serializing phase transitions |
| `CHECK` constraints | making "credits never have a reset time" unrepresentable |
| range partitioning | keeping gate range-queries on the hot partition |

## Consequences

**Good.** The queue is correct under concurrency and crash. Ledger queries are
real queries. The same storage substrate as the sibling `apg-*` projects, so the
operational knowledge already exists.

**Bad.** A "local tool" now needs a database. This is real friction and the main
cost of this decision.

**Mitigation.** `vibey up` makes it one command with three fallbacks, and
`vibey doctor` diagnoses each. The `pg_ctl` path means a developer with Postgres
installed but no Docker still gets a zero-config experience.

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
