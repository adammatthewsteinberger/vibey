CREATE TYPE open_kind AS ENUM ('question','decision','assumption','finding');

CREATE TABLE open_item (
    item_id       text PRIMARY KEY,
    project_id    uuid NOT NULL REFERENCES project(id) ON DELETE CASCADE,
    kind          open_kind NOT NULL,
    opened_seq    bigint NOT NULL,
    closed_seq    bigint,
    superseded_by text REFERENCES open_item(item_id),
    blocking      boolean NOT NULL DEFAULT false,
    severity      text,
    ambiguity     text,
    body          jsonb NOT NULL,
    normalized    text NOT NULL
);

CREATE INDEX open_item_open ON open_item (project_id, kind)
    WHERE closed_seq IS NULL AND superseded_by IS NULL;
CREATE INDEX open_item_norm ON open_item (project_id, kind, normalized);
