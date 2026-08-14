CREATE TYPE work_item_state AS ENUM (
    'pending','implementing','verifying','ready','integrated','blocked','waived'
);

CREATE TABLE work_item (
    item_id         text NOT NULL,
    project_id      uuid NOT NULL REFERENCES project(id) ON DELETE CASCADE,
    cycle           integer NOT NULL,
    title           text NOT NULL,
    state           work_item_state NOT NULL DEFAULT 'pending',
    acceptance_ids  text[] NOT NULL DEFAULT '{}',
    depends_on      text[] NOT NULL DEFAULT '{}',
    branch          text,
    worktree_path   text,
    attempt         integer NOT NULL DEFAULT 0,
    current_effort  smallint NOT NULL DEFAULT 1,
    last_engine     text,
    verification    jsonb NOT NULL DEFAULT '{}'::jsonb,
    blocked_reason  text,
    PRIMARY KEY (project_id, cycle, item_id)
);
