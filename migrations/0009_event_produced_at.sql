-- Preserve the timestamp supplied by an engine/application event. The original
-- 11-argument function used the column default and silently replaced it with
-- insertion time. Keep that function for compatibility and add the corrected
-- overload for new callers.
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
    p_produced_at    timestamptz,
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
        causation_id, correlation_id, provenance, produced_at, payload, digest
    ) VALUES (
        p_project_id, s, p_cycle, p_phase, p_kind, p_engine_id, p_job_id,
        p_causation_id, p_correlation_id, p_provenance, p_produced_at, p_payload, p_digest
    );

    RETURN s;
END $$;
