-- Adds the optional VISUAL_DESIGN interstitial (M5 task 5.6/5.7) between
-- DESIGN and BUILD. Forward-only: existing rows keep their current phase
-- value untouched, this only widens what the column accepts.
ALTER TYPE phase ADD VALUE IF NOT EXISTS 'visual_design' AFTER 'design';
