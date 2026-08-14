CREATE TABLE handoff (
    handoff_id      uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id      uuid NOT NULL REFERENCES project(id) ON DELETE CASCADE,
    cycle           integer NOT NULL,
    phase           phase NOT NULL,
    job_id          uuid REFERENCES job(id) ON DELETE SET NULL,
    from_engine     text,
    to_engine       text NOT NULL,
    reason          text NOT NULL,
    from_seq        bigint NOT NULL,
    to_seq          bigint NOT NULL,
    range_digest    text NOT NULL,
    envelope        jsonb NOT NULL,
    gate_mode       text NOT NULL,
    gate_attempts   integer NOT NULL DEFAULT 1,
    gate_violations jsonb NOT NULL DEFAULT '[]'::jsonb,
    accepted        boolean NOT NULL DEFAULT false,
    created_at      timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT handoff_range_sane CHECK (to_seq >= from_seq)
);

CREATE INDEX handoff_pair ON handoff (project_id, from_engine, to_engine, created_at DESC);
