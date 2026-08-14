CREATE TYPE provenance AS ENUM ('trusted','agent','untrusted');

CREATE TABLE event (
    event_id        uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    project_id      uuid NOT NULL REFERENCES project(id) ON DELETE CASCADE,
    seq             bigint NOT NULL,
    cycle           integer NOT NULL,
    phase           phase NOT NULL,
    kind            text NOT NULL,
    engine_id       text,
    job_id          uuid,
    causation_id    uuid,
    correlation_id  uuid NOT NULL,
    provenance      provenance NOT NULL DEFAULT 'agent',
    produced_at     timestamptz NOT NULL DEFAULT now(),
    payload         jsonb NOT NULL,
    digest          text NOT NULL,
    CONSTRAINT event_seq_uniq UNIQUE (project_id, seq)
);

CREATE INDEX event_project_seq   ON event (project_id, seq);
CREATE INDEX event_kind          ON event (project_id, kind, seq);
CREATE INDEX event_correlation   ON event (correlation_id, seq);
CREATE INDEX event_payload_gin   ON event USING gin (payload jsonb_path_ops);

-- Append-only: no UPDATE, no DELETE. Enforced, not merely intended.
CREATE RULE event_no_update AS ON UPDATE TO event DO INSTEAD NOTHING;
CREATE RULE event_no_delete AS ON DELETE TO event DO INSTEAD NOTHING;

CREATE TABLE event_seq (
    project_id  uuid PRIMARY KEY REFERENCES project(id) ON DELETE CASCADE,
    next_seq    bigint NOT NULL DEFAULT 1
);

CREATE OR REPLACE FUNCTION append_event(
    p_project_id     uuid,
    p_cycle          integer,
    p_phase          phase,
    p_kind           text,
    p_engine_id      text,
    p_job_id         uuid,
    p_causation_id   uuid,
    p_correlation_id uuid,
    p_provenance     provenance,
    p_payload        jsonb,
    p_digest         text
) RETURNS bigint
LANGUAGE plpgsql AS $$
DECLARE s bigint;
BEGIN
    INSERT INTO event_seq (project_id, next_seq)
    VALUES (p_project_id, 2)
    ON CONFLICT (project_id) DO UPDATE SET next_seq = event_seq.next_seq + 1
    RETURNING next_seq - 1 INTO s;

    INSERT INTO event (
        project_id, seq, cycle, phase, kind, engine_id, job_id,
        causation_id, correlation_id, provenance, payload, digest
    ) VALUES (
        p_project_id, s, p_cycle, p_phase, p_kind, p_engine_id, p_job_id,
        p_causation_id, p_correlation_id, p_provenance, p_payload, p_digest
    );

    RETURN s;
END $$;
