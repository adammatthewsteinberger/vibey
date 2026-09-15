---
name: okta-workflows-deployment
description: "Use when versioning, deploying, promoting, or moving Okta Workflows between orgs (Preview/sandbox → Production) via flopack import/export: export stripping all connection information and table DATA so only the schema survives ('you need to restore all card connections', 'tables are recreated according to the table schema… but the tables are initially empty'); broken references requiring manual remapping on import (a helper flow that wasn't included in the export must be replaced before the import completes); flopack/template schema rules (workflow.flopack and workflow.json must be valid JSON, the name value's 50-char limit must exactly match the enclosing folder, connector names must match connectors.json, folder name must satisfy regex ^[a-z0-9_]{2,50}$, and the details object — flowCount, helperFlowsCount, mainFlowsCount, flos[] with id/name/type/screenshotURL, tags — must exactly match the flopack or CI validation fails); and max folder depth 5 plus duplicate-folder not copying table data. Triggers on flopack, workflow.json, export/import flows, restore connections, empty tables after import, broken references, connectors.json, folder depth 5, duplicate folder, Preview to Production promotion."
---

# Okta Workflows — Versioning, Deployment & Flopack Import/Export (§8)

Four quirks. Critical when moving Preview/sandbox → Production: exports carry structure, not
connections or data.

## Quirk 8.1 — Export strips connections and table DATA (schema only)

"The export function removes all connection information and table data." On import, "you need to
restore all card connections" and "tables are recreated according to the table schema… but the tables
are initially empty." Critical when moving Preview/sandbox → Production.

- *Sources:* about-folders.htm; export-import-flows.htm

## Quirk 8.2 — Broken references require manual remapping on import

"If any of the imported flows refer to a flow that wasn't included in the export (for example, a helper
flow called to handle a list), you must specify a replacement flow to complete the import." Missing
references are flagged and block completion until resolved.

- *Sources:* export-import-flows.htm; about-folders.htm

## Quirk 8.3 — flopack/template schema rules

`workflow.flopack` and `workflow.json` must be valid JSON; the `name` value has a 50-char limit and
must exactly match the enclosing folder; connector names must match `connectors.json`; folder name
must satisfy regex `^[a-z0-9_]{2,50}$`. The `details` object (flowCount, helperFlowsCount,
mainFlowsCount, `flos[]` with id/name/type/screenshotURL, tags) must exactly match the flopack or CI
validation fails.

- *Source:* github.com/okta/workflows-templates README

## Quirk 8.4 — Max folder depth 5; duplicate-folder doesn't copy table data

An import that would exceed 5 levels is offered as a top-level folder instead. Duplicating a folder
copies table schema but not data (must be transferred manually); references within the folder repoint
to duplicates, external references stay unchanged; creation dates reset to the duplication date.

- *Sources:* export-import-flows.htm; about-folders.htm
