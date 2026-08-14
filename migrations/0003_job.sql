CREATE TYPE job_state AS ENUM (
    'ready','leased','succeeded','failed','awaiting_human','awaiting_capacity','cancelled'
);

CREATE TABLE job (
    id                uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id        uuid NOT NULL REFERENCES project(id) ON DELETE CASCADE,
    cycle             integer NOT NULL,
    phase             phase NOT NULL,
    kind              text NOT NULL,
    state             job_state NOT NULL DEFAULT 'ready',
    priority          integer NOT NULL DEFAULT 0,
    work_item_id      text,
    payload           jsonb NOT NULL DEFAULT '{}'::jsonb,
    requirement       jsonb NOT NULL DEFAULT '{}'::jsonb,
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

CREATE INDEX job_claim ON job (project_id, priority DESC, run_after ASC, id ASC)
    WHERE state = 'ready';

CREATE INDEX job_expiring ON job (lease_expires_at) WHERE state = 'leased';

CREATE TABLE job_dependency (
    job_id            uuid NOT NULL REFERENCES job(id) ON DELETE CASCADE,
    depends_on_job_id uuid NOT NULL REFERENCES job(id) ON DELETE CASCADE,
    PRIMARY KEY (job_id, depends_on_job_id),
    CONSTRAINT no_self_dep CHECK (job_id <> depends_on_job_id)
);

CREATE INDEX job_dep_reverse ON job_dependency (depends_on_job_id);
