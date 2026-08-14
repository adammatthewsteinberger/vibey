# Data Model

> PostgreSQL 17. All timestamps `timestamptz`. All ids `uuid` except `event.seq`
> (gapless bigint per project) and human-facing item ids (short prefixed strings).
> Migrations are forward-only, applied by `vibey migrate`.

---

## 1. Why PostgreSQL

Recorded fully in [ADR-0002](../architecture/decisions/0002-postgres-not-sqlite.md).
The short version:

| Requirement | SQLite | PostgreSQL |
|---|---|---|
| N workers claiming jobs concurrently | no row locks, **no `SKIP LOCKED`** | `FOR UPDATE SKIP LOCKED` |
| Crash-safe leases | mark-then-return leaks locked rows forever | lease + expiry + reaper |
| Worker wakeup without polling | poll only | `LISTEN` / `NOTIFY` |
| Ledger payload queries | `json1`, no real index | `jsonb` + GIN |
| Phase-transition mutual exclusion | file lock | advisory locks |

WAL mode fixes reader/writer blocking; vibey's contention is writer/writer.

---

## 2. Entity relationships

```mermaid
erDiagram
    project ||--o{ cycle_record : has
    project ||--o{ job : has
    project ||--o{ event : has
    project ||--o{ engine_health : tracks
    project ||--|| rotation_cursor : has
    job ||--o{ job_dependency : "depends on"
    job ||--o{ human_gate : raises
    job ||--o{ handoff : triggers
    event ||--o{ open_item : projects
    project ||--o{ work_item : has
    work_item ||--o{ job : "implemented by"
    handoff }o--|| engine_health : from
    handoff }o--|| engine_health : to
```

---

## 3. Core tables

### 3.1 `project`

```sql
CREATE TYPE phase AS ENUM (
    'intake','design','build','review','deploy','done','abandoned'
);

CREATE TABLE project (
    id              uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    name            text NOT NULL,
    repo_path       text NOT NULL,
    phase           phase NOT NULL DEFAULT 'intake',
    cycle           integer NOT NULL DEFAULT 1,
    max_cycles      integer NOT NULL DEFAULT 10,
    config          jsonb NOT NULL,           -- the resolved vibey.toml
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT project_cycle_bounded CHECK (cycle >= 1 AND cycle <= max_cycles + 1)
);

CREATE UNIQUE INDEX project_repo_uniq ON project (repo_path);
```

### 3.2 `event` — the ledger

```sql
CREATE TYPE provenance AS ENUM ('trusted','agent','untrusted');

CREATE TABLE event (
    event_id        uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id      uuid NOT NULL REFERENCES project(id) ON DELETE CASCADE,
    seq             bigint NOT NULL,
    cycle           integer NOT NULL,
    phase           phase NOT NULL,
    kind            text NOT NULL,
    engine_id       text,                     -- NULL for vibey-authored events
    job_id          uuid,
    causation_id    uuid,
    correlation_id  uuid NOT NULL,
    provenance      provenance NOT NULL DEFAULT 'agent',
    produced_at     timestamptz NOT NULL DEFAULT now(),
    payload         jsonb NOT NULL,
    digest          text NOT NULL,            -- sha256 of canonical payload
    CONSTRAINT event_seq_uniq UNIQUE (project_id, seq)
);

CREATE INDEX event_project_seq   ON event (project_id, seq);
CREATE INDEX event_kind          ON event (project_id, kind, seq);
CREATE INDEX event_correlation   ON event (correlation_id, seq);
CREATE INDEX event_payload_gin   ON event USING gin (payload jsonb_path_ops);

-- Append-only: no UPDATE, no DELETE. Enforced, not merely intended.
CREATE RULE event_no_update AS ON UPDATE TO event DO INSTEAD NOTHING;
CREATE RULE event_no_delete AS ON DELETE TO event DO INSTEAD NOTHING;
```

**Gapless `seq`.** One sequence per project, allocated inside the insert
transaction:

```sql
CREATE TABLE event_seq (
    project_id  uuid PRIMARY KEY REFERENCES project(id) ON DELETE CASCADE,
    next_seq    bigint NOT NULL DEFAULT 1
);

CREATE OR REPLACE FUNCTION append_event(...) RETURNS bigint
LANGUAGE plpgsql AS $$
DECLARE s bigint;
BEGIN
    UPDATE event_seq SET next_seq = next_seq + 1
    WHERE project_id = p_project_id
    RETURNING next_seq - 1 INTO s;

    INSERT INTO event (project_id, seq, ...) VALUES (p_project_id, s, ...);
    RETURN s;
END $$;
```

Serializing appends per project is intentional. The ledger is the one place where
ordering is the whole point, and a project produces at most a few events per
second — the contention is negligible and the guarantee is absolute. Rule R6 of
the [no-loss gate](handoff-protocol.md#62-the-rules) depends on it.

### 3.3 `job` — the queue

```sql
CREATE TYPE job_state AS ENUM (
    'ready','leased','succeeded','failed','awaiting_human','awaiting_capacity','cancelled'
);

CREATE TABLE job (
    id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id        uuid NOT NULL REFERENCES project(id) ON DELETE CASCADE,
    cycle             integer NOT NULL,
    phase             phase NOT NULL,
    kind              text NOT NULL,          -- 'build.implement', …
    state             job_state NOT NULL DEFAULT 'ready',
    priority          integer NOT NULL DEFAULT 0,
    work_item_id      text,
    payload           jsonb NOT NULL DEFAULT '{}'::jsonb,
    requirement       jsonb NOT NULL DEFAULT '{}'::jsonb,  -- effort + capabilities + excluded
    idempotency_key   text NOT NULL,
    attempts          integer NOT NULL DEFAULT 0,
    max_attempts      integer NOT NULL DEFAULT 7,
    run_after         timestamptz NOT NULL DEFAULT now(),
    lease_owner       text,
    lease_expires_at  timestamptz,
    assigned_engine   text,
    last_error        jsonb,
    created_at        timestamptz NOT NULL DEFAULT now(),
    updated_at        timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT job_idem_uniq UNIQUE (project_id, idempotency_key),
    CONSTRAINT job_lease_consistent CHECK (
        (state = 'leased') = (lease_owner IS NOT NULL AND lease_expires_at IS NOT NULL)
    )
);

-- The claim index. Partial: only 'ready' rows are ever scanned.
CREATE INDEX job_claim ON job (project_id, priority DESC, run_after ASC, id ASC)
    WHERE state = 'ready';

-- The reaper index.
CREATE INDEX job_expiring ON job (lease_expires_at) WHERE state = 'leased';

CREATE TABLE job_dependency (
    job_id            uuid NOT NULL REFERENCES job(id) ON DELETE CASCADE,
    depends_on_job_id uuid NOT NULL REFERENCES job(id) ON DELETE CASCADE,
    PRIMARY KEY (job_id, depends_on_job_id),
    CONSTRAINT no_self_dep CHECK (job_id <> depends_on_job_id)
);

CREATE INDEX job_dep_reverse ON job_dependency (depends_on_job_id);
```

**`idempotency_key`** is `sha256(project_id || cycle || kind || subject)`. Enqueue
uses `ON CONFLICT (project_id, idempotency_key) DO NOTHING`, so a supervisor that
crashes after enqueueing but before committing its own state cannot create
duplicate work on restart.

### 3.4 Claim, heartbeat, ack, reap

```sql
-- CLAIM
UPDATE job SET
    state            = 'leased',
    lease_owner      = $1,
    lease_expires_at = now() + $2::interval,
    attempts         = attempts + 1,
    updated_at       = now()
WHERE id = (
    SELECT j.id FROM job j
    WHERE j.state = 'ready'
      AND j.run_after <= now()
      AND j.project_id = $3
      AND NOT EXISTS (
          SELECT 1 FROM job_dependency d
          JOIN job p ON p.id = d.depends_on_job_id
          WHERE d.job_id = j.id AND p.state <> 'succeeded'
      )
    ORDER BY j.priority DESC, j.run_after ASC, j.id ASC
    FOR UPDATE SKIP LOCKED
    LIMIT 1
)
RETURNING *;

-- HEARTBEAT (every lease/3)
UPDATE job SET lease_expires_at = now() + $2::interval
WHERE id = $1 AND lease_owner = $3 AND state = 'leased';

-- ACK success
UPDATE job SET state='succeeded', lease_owner=NULL, lease_expires_at=NULL, updated_at=now()
WHERE id = $1 AND lease_owner = $2;

-- NACK with backoff (full jitter, capped at 15 min)
UPDATE job SET
    state            = CASE WHEN attempts >= max_attempts THEN 'failed' ELSE 'ready' END,
    lease_owner      = NULL,
    lease_expires_at = NULL,
    run_after        = now() + (least(power(2, attempts) * interval '2 seconds',
                                      interval '15 minutes') * random()),
    last_error       = $3,
    updated_at       = now()
WHERE id = $1 AND lease_owner = $2;

-- REAP (supervisor, every 10s)
UPDATE job SET state='ready', lease_owner=NULL, lease_expires_at=NULL, updated_at=now()
WHERE state='leased' AND lease_expires_at < now();
```

The reaper is what makes worker death safe, and is why every handler must be
idempotent (non-negotiable #6): a reaped job *will* be executed again.

### 3.5 `work_item`

```sql
CREATE TYPE work_item_state AS ENUM (
    'pending','implementing','verifying','ready','integrated','blocked','waived'
);

CREATE TABLE work_item (
    item_id         text NOT NULL,            -- 'item-014', stable across cycles
    project_id      uuid NOT NULL REFERENCES project(id) ON DELETE CASCADE,
    cycle           integer NOT NULL,
    title           text NOT NULL,
    state           work_item_state NOT NULL DEFAULT 'pending',
    acceptance_ids  text[] NOT NULL DEFAULT '{}',
    depends_on      text[] NOT NULL DEFAULT '{}',
    branch          text,
    worktree_path   text,
    attempt         integer NOT NULL DEFAULT 0,
    current_effort  smallint NOT NULL DEFAULT 1,   -- Effort IntEnum
    last_engine     text,
    verification    jsonb NOT NULL DEFAULT '{}'::jsonb,
    blocked_reason  text,
    PRIMARY KEY (project_id, cycle, item_id)
);
```

### 3.6 `open_item` — the gate's working set

A projection, rebuildable from `event`, materialized because the
[no-loss gate](handoff-protocol.md) queries it on every handoff.

```sql
CREATE TYPE open_kind AS ENUM ('question','decision','assumption','finding');

CREATE TABLE open_item (
    item_id       text PRIMARY KEY,           -- 'q_7f3a', 'd_44a1', 'a_0c2f', 'f_21c9'
    project_id    uuid NOT NULL REFERENCES project(id) ON DELETE CASCADE,
    kind          open_kind NOT NULL,
    opened_seq    bigint NOT NULL,
    closed_seq    bigint,                     -- NULL = still open
    superseded_by text REFERENCES open_item(item_id),
    blocking      boolean NOT NULL DEFAULT false,
    severity      text,
    ambiguity     text,                       -- 'clear' | 'needs_clarification'
    body          jsonb NOT NULL,
    normalized    text NOT NULL               -- for dedup on restatement
);

CREATE INDEX open_item_open ON open_item (project_id, kind)
    WHERE closed_seq IS NULL AND superseded_by IS NULL;
CREATE INDEX open_item_norm ON open_item (project_id, kind, normalized);
```

`normalized` is a lowercased, punctuation-stripped, stopword-reduced form used to
recognize when an agent restates an existing open question in different words —
which would otherwise create a second id and make the gate demand both.

### 3.7 `handoff`

```sql
CREATE TABLE handoff (
    handoff_id      uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id      uuid NOT NULL REFERENCES project(id) ON DELETE CASCADE,
    cycle           integer NOT NULL,
    phase           phase NOT NULL,
    job_id          uuid REFERENCES job(id) ON DELETE SET NULL,
    from_engine     text,                     -- NULL when synthesized
    to_engine       text NOT NULL,
    reason          text NOT NULL,
    from_seq        bigint NOT NULL,
    to_seq          bigint NOT NULL,
    range_digest    text NOT NULL,
    envelope        jsonb NOT NULL,
    gate_mode       text NOT NULL,            -- strict | full_transcript | human | forced
    gate_attempts   integer NOT NULL DEFAULT 1,
    gate_violations jsonb NOT NULL DEFAULT '[]'::jsonb,
    accepted        boolean NOT NULL DEFAULT false,
    created_at      timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT handoff_range_sane CHECK (to_seq >= from_seq)
);

CREATE INDEX handoff_pair ON handoff (project_id, from_engine, to_engine, created_at DESC);
```

Keeping every attempt's violations makes gate quality measurable: which rules fire
most, for which engine pairs, at which phases.

### 3.8 `engine_health` and `rotation_cursor`

```sql
CREATE TYPE circuit_state AS ENUM ('closed','half_open','open');

CREATE TABLE engine_health (
    project_id       uuid NOT NULL REFERENCES project(id) ON DELETE CASCADE,
    engine_id        text NOT NULL,
    installed        boolean NOT NULL DEFAULT false,
    version          text,
    conformance_ok   boolean NOT NULL DEFAULT false,
    conformance_at   timestamptz,
    auth_ok_at       timestamptz,
    circuit          circuit_state NOT NULL DEFAULT 'closed',
    capacity_state   text,                    -- last classified CapacityState
    resets_at        timestamptz,             -- ONLY ever set for WindowExhausted
    probe_next_at    timestamptz,
    probe_attempt    integer NOT NULL DEFAULT 0,
    consecutive_fail integer NOT NULL DEFAULT 0,
    ewma_failure     double precision NOT NULL DEFAULT 0.0,
    cost_usd_cycle   numeric(12,4) NOT NULL DEFAULT 0,
    selected_count   bigint NOT NULL DEFAULT 0,
    PRIMARY KEY (project_id, engine_id),
    CONSTRAINT credits_never_have_a_deadline CHECK (
        capacity_state IS DISTINCT FROM 'CreditsExhausted' OR resets_at IS NULL
    )
);
```

That last `CHECK` is the schema-level expression of the family's hardest-won rule:
**exhausted credits can never carry a reset time.** Conflating it with a rate-limit
window is the exact bug the `*loop` projects exist to avoid, so vibey makes it
impossible to represent, not merely discouraged.

```sql
CREATE TABLE rotation_cursor (
    project_id  uuid NOT NULL REFERENCES project(id) ON DELETE CASCADE,
    engine_id   text NOT NULL,
    current     integer NOT NULL DEFAULT 0,   -- SWRR running value
    "order"     integer NOT NULL,             -- deterministic tie-break
    PRIMARY KEY (project_id, engine_id)
);
```

The cursor is updated in the **same transaction** as the job claim, so a crash
between selecting an engine and leasing a job cannot advance the cursor without
doing the work.

### 3.9 `human_gate`

```sql
CREATE TABLE human_gate (
    gate_id     uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id  uuid NOT NULL REFERENCES project(id) ON DELETE CASCADE,
    job_id      uuid REFERENCES job(id) ON DELETE CASCADE,
    kind        text NOT NULL,     -- question | approval | escalation | budget | handoff_failure
    prompt      text NOT NULL,
    options     jsonb NOT NULL DEFAULT '[]'::jsonb,
    default_answer text,
    answer      jsonb,
    raised_at   timestamptz NOT NULL DEFAULT now(),
    timeout_at  timestamptz,
    answered_at timestamptz,
    answered_by text
);

CREATE INDEX human_gate_open ON human_gate (project_id, raised_at)
    WHERE answered_at IS NULL;
```

### 3.10 `artifact` and `budget_ledger`

```sql
CREATE TABLE artifact (
    artifact_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id  uuid NOT NULL REFERENCES project(id) ON DELETE CASCADE,
    cycle       integer NOT NULL,
    kind        text NOT NULL,       -- spec | demo | migration | diff | report | transcript
    path        text NOT NULL,
    digest      text NOT NULL,
    produced_by text,
    seq         bigint NOT NULL,
    created_at  timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE budget_ledger (
    project_id  uuid NOT NULL REFERENCES project(id) ON DELETE CASCADE,
    cycle       integer NOT NULL,
    phase       phase NOT NULL,
    engine_id   text NOT NULL,
    turns       bigint NOT NULL DEFAULT 0,
    tokens_in   bigint NOT NULL DEFAULT 0,
    tokens_out  bigint NOT NULL DEFAULT 0,
    dollars     numeric(12,4) NOT NULL DEFAULT 0,
    PRIMARY KEY (project_id, cycle, phase, engine_id)
);
```

---

## 4. Notifications

```sql
-- After enqueue / gate answer / circuit half-open:
NOTIFY vibey_job_ready, '<project_id>';
NOTIFY vibey_gate_raised, '<gate_id>';
NOTIFY vibey_phase_changed, '<project_id>';
```

Workers `LISTEN vibey_job_ready` and fall back to a 5-second poll, so a missed
notification costs latency, never correctness.

---

## 5. Phase transitions are serialized

```sql
SELECT pg_advisory_xact_lock(hashtext('vibey:phase:' || $1::text));
```

Taken by the supervisor around every transition. Multiple supervisors are safe;
only one transitions a given project at a time.

---

## 6. Retention

| Table | Policy |
|---|---|
| `event` | **never deleted** — it is the ledger. `vibey ledger archive` moves cycles older than N to a compressed partition |
| `job` | `succeeded` rows pruned after 30 days; `failed` kept until acknowledged |
| `handoff` | kept with the ledger |
| `artifact` | rows kept; files garbage-collected by `vibey gc` when unreferenced by any open item |

`event` is partitioned by `(project_id, cycle)` range once a project exceeds
~500k events, which keeps the gate's range queries on the hot partition.

---

## 7. Migrations

Plain SQL files, forward-only, applied in lexical order, tracked in
`schema_migration(version, applied_at, checksum)`. `vibey migrate --check` fails if
an applied migration's checksum changed — an edited migration is a bug, not a
convenience.

Every migration is tested by applying it to a container-fresh database *and* to a
database seeded with the previous version's fixture data.
