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
    capacity_state   text,
    resets_at        timestamptz,
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

CREATE TABLE rotation_cursor (
    project_id  uuid NOT NULL REFERENCES project(id) ON DELETE CASCADE,
    engine_id   text NOT NULL,
    current     integer NOT NULL DEFAULT 0,
    "order"     integer NOT NULL,
    PRIMARY KEY (project_id, engine_id)
);
