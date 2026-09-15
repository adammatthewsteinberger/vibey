# 0029 — Integrates are serialized by a Postgres advisory lock, and contention is a Defer

**Status:** accepted · **Date:** 2026-08-19 (recorded 2026-09-15) · **Extends:** ADR-0002, ADR-0008, ADR-0009

## Context

Phase ② builds work items in parallel across worktrees (ADR-0008) and merges each into one integration branch per cycle. The integration branch is a single shared git ref: two workers merging into it at once corrupt each other, and nothing serialized them — the integrate handler's own docstring said so. Once rotation and multiple workers went live (#41, #42) the race was real.

ADR-0002 anticipated advisory locks for *phase transitions* (`pg_advisory_xact_lock` in the data-model plan). What actually needed serializing was the integrate, and an integrate is not a transaction: it is a sequence of git subprocesses and ledger writes over many seconds.

## Decision

**`build.integrate` for one `(project_id, cycle)` runs under a session-level Postgres advisory lock, acquired with `pg_try_advisory_lock`, and a failed acquisition is a short Defer.**

- **`IntegrationLock` is an application seam** (`try_acquire`/`release`), implemented by `PostgresAdvisoryLock`. The key is the first 8 bytes of `sha256("vibey.integrate:<project>:<cycle>")` as a signed 64-bit integer, namespaced so it can never collide with any other advisory-lock use in the database.
- **Session-level, deliberately.** A session lock lives on the connection that took it, so the held lock pins its pooled connection out of the pool until release. Releasing the connection back would silently drop the lock the moment another query reused the session. A transaction-level lock cannot span a merge that runs outside any transaction.
- **Never block.** `try_acquire` returns `False` on contention and the job defers; a worker never waits on a lock. The never-block-a-worker rule (ADR-0009) applies to locks as it applies to humans.
- **Release in a `finally`**, after the kind/work-item guards, so a crashed merge cannot wedge the branch for every other worker; a lock whose holder dies is released by Postgres when the connection drops.

## Consequences

**Good.** N workers share one integration branch safely with no coordinator, using the database already required by ADR-0002. Cross-connection contention is proven against real Postgres in the suite, and all faked end-to-end runs carry the real lock in the path.

**Bad.** One pooled connection is unavailable for the duration of a merge; pool size must allow for it. A deferred integrate looks idle to an observer for one backoff.

**Rule status.** The mechanism does not pass ADR-0020's test. The clause "a worker never blocks on a lock; contention is a Defer" extends the standing never-block rule, and belongs in the sub-doctrine ADR-0009 owes rather than one of its own.

## Alternatives rejected

- **`pg_advisory_xact_lock`** (the plan). Scoped to a transaction; the merge is not one.
- **A git-side lock (`flock` on the repository, `git update-ref` CAS).** Local to one filesystem; fails across pods sharing a database but not a disk.
- **A row lock on the cycle record.** Held for the merge's duration it blocks every other reader of that row, and it blocks rather than defers.
- **A single dedicated integrate worker.** Removes parallel integrates entirely and reintroduces a coordinator the queue was designed not to need.
- **Blocking `pg_advisory_lock`.** Simpler, and exactly the thing the never-block rule forbids.
