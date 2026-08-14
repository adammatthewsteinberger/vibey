CREATE TABLE human_gate (
    gate_id     uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id  uuid NOT NULL REFERENCES project(id) ON DELETE CASCADE,
    job_id      uuid REFERENCES job(id) ON DELETE CASCADE,
    kind        text NOT NULL,
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

CREATE TABLE artifact (
    artifact_id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id  uuid NOT NULL REFERENCES project(id) ON DELETE CASCADE,
    cycle       integer NOT NULL,
    kind        text NOT NULL,
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
