# Okta Workflows Plugin

A field reference for **Okta Workflows**, framed around **identity source-of-truth → Okta sync pipelines (e.g. Entra ID)**. It
captures the platform's production quirks, hard record caps, and verified workarounds — with every
claim tied to its source (Okta docs `.htm` pages, Okta support KB articles, `maxkatz.net` tips, and
release notes), and the two speculative items explicitly labeled **THEORY** and **UNCONFIRMED**.

The guide is split into nine skills: one overview plus one per section of the underlying field
reference.

- **okta-workflows-field-guide**: The cross-cutting overview — TL;DR, the five key findings, the
  single most important architectural rule (**never do bulk/looping work synchronously in a parent
  flow** — use Stream Matching Records or For Each - Ignore Errors with bounded `concurrency` into
  helper flows), the six Recommendations (design-phase type coercion, bulk-sync concurrency, state
  across pages, Preview → Production promotion, guardrails/benchmarks, Entra specifics), the Caveats
  (the THEORY/UNCONFIRMED labels, no latency SLA, the two easily-confused concurrency figures), and
  the recent **2025–2026** platform changes (Okta ITP connector, Send Slackbot Message deprecation,
  Connector Builder Polling Monitors, OKTA-928020 / OKTA-858112 / OKTA-946866).
- **okta-workflows-branching** (§1): The If/Else and If/ElseIf card family — **no implicit type
  coercion** in comparisons (the silent wrong branch: `"6"` Text vs `30` Number, `"80" > "9"`),
  don't nest more than 3 If/ElseIf, the pass-a-value-into-an-If/ElseIf tip-bug (Flow Control -
  Assign), Return / Continue If acting as anonymous helper flows inside If/ElseIf and If Error
  blocks, not being able to drag outputs from inside a branch to cards after the block (Create
  Outputs), and If/Else supporting only one condition (And/Or/Not/XNOR).
- **okta-workflows-loops** (§2): Looping constructs — For Each - Ignore Errors (`asyncEach`) and its
  `concurrency` input flooding the Okta connector ceiling (30 concurrent / 15 GET per-user /
  `core.concurrency.org.limit.violation`), "ignores errors" only from the parent's perspective,
  plain For Each returning no outputs (Map/Reduce or a shared Table/stash), deeply nested iteration
  cards triggering CPU-time throttling, and the List - Filter starts-with gotcha.
- **okta-workflows-tables** (§3): The built-in data store — Search Rows (`searchRows2`) being
  **case-sensitive** with no "starts with", the hard **3,500-row** return cap regardless of Limit
  (Offset pagination), the table hard limits (500,000 rows / 64 columns / 16 KB per cell / 200/100
  tables), the Where Expression JSON quirk, the no-native-upsert read-then-write race (**THEORY**),
  and high-frequency table requests triggering throttling.
- **okta-workflows-hooks-streaming** (§4): Event hooks, streaming hooks & handler flow patterns —
  streaming flows that **cannot be stopped** and ignore deactivation (up to 1M records, ~13h/500k,
  ~25h/1M), the rigid `Record`/`State` contract, `State` not being a cross-page accumulator plus the
  Connector Builder Paginate `object`/`break`/`path` do-while workaround (5,000-iteration cap), event
  hook hard limits and no ordering guarantee (3s timeout, 400,000/24h, 25 hooks, 500 trigger flows,
  100 events/payload, 100 inline hooks), the 60s/120s API-endpoint connection drop (API Connector
  Close, Call Flow Async + Return Raw), and the `Caller` `root_wf_id`.
- **okta-workflows-connectors** (§5): The Okta and Azure AD / Microsoft Entra ID connectors — Okta
  Search Groups exact `eq` only (Custom Search Criteria `sw`/`ew`), the APP_GROUP / OKTA_GROUP /
  BUILT_IN Type semantics (**UNCONFIRMED** filtering bug), Search Group Rule keyword search, the Okta
  connector rate limits (30 / 15 / 6,000-per-minute, DynamicScale multipliers), Entra
  delegated-permissions-only (no app-only — use a service account), reauthorization breaking on scope
  change, the three Entra record caps (Search Groups 4,000, Search Group Members 900, Search Users
  4,000; no `#` in member input), mail-enabled security / distribution groups silently failing, the
  List Contact Folder 2-level cap, and hard-coded-`domain` search cards.
- **okta-workflows-execution-limits** (§6): The resource model — the platform hard limits (100 MB
  memory, 2,000,000 steps, recursion 250 "Stack limit exceeded", 1 MB "too large to display" payload,
  10 invocations/sec, 30-day history, file 10 MB / 2 GB / SFTP 25 MB, 30-day pause), the plan-gated
  active flow counts (5 / 50 / 150 / unlimited, legacy ALM 100), automated flow throttling as a
  platform feature, and the export flow rate limits (15-minute window, 10 / 100 / 300 / 1000).
- **okta-workflows-error-handling** (§7): Error handling & retry — card-level retry firing **only on
  429** (and 504 in Connector Builder), custom retry status codes via a List Construct card and the
  "Specified errors" Raw Request dialog, the max-3-nested-If-Error-blocks recommendation, and error
  propagation from helper flows (Return Error / Return Error If outside the block).
- **okta-workflows-deployment** (§8): Versioning, deployment & flopack import/export — export
  stripping **connections and table data** (schema only), broken references requiring manual remapping
  on import, the flopack/template schema rules (valid JSON, 50-char `name` matching the folder,
  `connectors.json` names, the `^[a-z0-9_]{2,50}$` folder regex, the `details` object), and max folder
  depth 5 with duplicate-folder not copying table data.

## Scope

This plugin documents the **quirks, limits, and workarounds** of the Okta Workflows platform as they
apply to an Entra ID → Okta identity-sync pipeline. It is a reference distilled from official Okta
documentation and support KB articles, Max Katz's "Workflows Tips" series, and Okta release notes —
not a general Okta Workflows tutorial and not a substitute for validating each behavior in your target
org (Okta Workflows is a continuously updated SaaS with no discrete version numbers).
