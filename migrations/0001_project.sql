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
    config          jsonb NOT NULL,
    created_at      timestamptz NOT NULL DEFAULT now(),
    updated_at      timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT project_cycle_bounded CHECK (cycle >= 1 AND cycle <= max_cycles + 1)
);

CREATE UNIQUE INDEX project_repo_uniq ON project (repo_path);
