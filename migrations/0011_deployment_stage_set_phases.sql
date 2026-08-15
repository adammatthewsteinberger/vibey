-- Adds the 3-phase deployment stage set (M10): deploy_design, deploy_execute, deploy_review.
ALTER TYPE phase ADD VALUE IF NOT EXISTS 'deploy_design' BEFORE 'deploy';
ALTER TYPE phase ADD VALUE IF NOT EXISTS 'deploy_execute' BEFORE 'deploy';
ALTER TYPE phase ADD VALUE IF NOT EXISTS 'deploy_review' BEFORE 'deploy';
