---
name: okta-workflows-field-guide
description: "Use when starting or architecting an Okta Workflows identity source-of-truth → Okta sync pipeline (e.g. Entra ID), or when you need the cross-cutting rules that govern every other Okta Workflows skill: the TL;DR, the five key findings, the single most important architectural rule (never do bulk/looping work synchronously in a parent flow — use Stream Matching Records or For Each - Ignore Errors with bounded concurrency into helper flows), the design-phase / bulk-sync / state-across-pages / Preview→Production / guardrail / Entra Recommendations, the Caveats (THEORY and UNCONFIRMED labels, no latency SLA, the two concurrency figures), and the recent 2025–2026 platform changes (Okta ITP connector, Send Slackbot Message deprecation, Connector Builder Polling Monitors, OKTA-928020 / OKTA-858112 / OKTA-946866 fixes). Triggers on Okta Workflows quirks overview, Entra to Okta sync design, Stream Matching Records vs For Each, DynamicScale, event-driven vs scheduled batch sync, and 'where do I start' Okta Workflows questions."
---

# Okta Workflows Field Guide — Overview, Rules, Recommendations & Caveats

A field reference for **identity source-of-truth → Okta sync pipelines (e.g. Entra ID)**. This overview skill carries the
cross-cutting material — the TL;DR, key findings, top-level architectural rule, recommendations,
caveats, and recent platform changes. The eight companion skills cover each area in depth:
`okta-workflows-branching` (§1), `okta-workflows-loops` (§2), `okta-workflows-tables` (§3),
`okta-workflows-hooks-streaming` (§4), `okta-workflows-connectors` (§5),
`okta-workflows-execution-limits` (§6), `okta-workflows-error-handling` (§7), and
`okta-workflows-deployment` (§8).

## TL;DR

- Okta Workflows' biggest production traps for an Entra → Okta sync are **silent type/case
  sensitivity** in comparison and Tables cards, **hard record caps that differ per card** (Tables
  Search Rows caps at 3,500 rows; Azure AD Search Groups at 4,000; Azure AD Search Group Members at
  900), and **asynchronous concurrency that floods downstream API rate limits** — all have concrete,
  documented workarounds below.
- The single most important architectural rule: **never do bulk/looping work synchronously in a
  parent flow** — use "Stream Matching Records" or "For Each - Ignore Errors" with a bounded
  `concurrency` value (1–10) into helper flows, and remember **streamed flows cannot be stopped once
  started** (deactivating the flow does not halt an in-progress stream).
- All four of the user's calibration quirks are confirmed and expanded, plus approximately 30
  additional documented quirks across branching, loops, Tables, hooks/streaming, connectors,
  execution limits, error handling, and flopack deployment.

## Key Findings

1. Workflows performs **no implicit type conversion** in comparisons — the number one source of "why
   did my If/Else take the wrong branch" bugs.
2. Tables "Search Rows" (searchRows2) is **case-sensitive AND caps at 3,500 rows** regardless of the
   Limit field.
3. The Azure AD/Entra connector uses **delegated (not app-only)** permissions, **silently fails on
   mail-enabled security/distribution groups**, and has **three different record caps** across its
   cards.
4. Streaming and async loops trade memory safety for loss of control — **you cannot stop them
   mid-execution**.
5. **Flow throttling is now an automated platform feature** that will silently limit resource-heavy
   loop/table flows.

## Recommendations

1. **Immediately (design phase):** Standardize a type-coercion convention — every comparison
   explicitly sets both operand types; normalize all string keys to lower case before Table writes
   AND searches. Build one central error-logging helper flow that writes failures (with the Caller
   `root_wf_id`) to a dedicated Errors table.
2. **Before any bulk sync:** Replace all unbounded loops with For Each - Ignore Errors at
   `concurrency=5` (tune down to 1 if you see `core.concurrency.org.limit.violation` in the System
   Log; raise toward 10 only if well under the 30-concurrent Okta-connector ceiling). For more than
   900 Entra group members, more than 4,000 Entra groups/users, or more than 3,500 Table rows,
   switch to Stream Matching Records or Offset-based pagination.
3. **For state across pages:** Do not rely on the streaming `State` object as an accumulator —
   persist run state to a Tables row keyed by run ID, or implement the Connector Builder Paginate
   `object` / `break` / `path` do-while pattern.
4. **For Preview → Production promotion:** Script re-creation of connections and re-population of
   lookup tables post-import; keep helper flows in the same exported folder to preserve references;
   validate flopack `name` / folder-name match and connector names before import.
5. **Guardrails/benchmarks that change the plan:** If event volume approaches 280,000/day
   (event-hook warning threshold) or 400,000/day (hard cutoff), or if flows get throttled, move from
   event-driven to scheduled batch sync and/or purchase DynamicScale. If synchronous API-endpoint
   flows approach 60s, refactor with API Connector Close + Call Flow Async.
6. **Entra specifics:** Use a dedicated Entra service *user* account (delegated auth only — no
   app-only); exclude mail-enabled security/distribution groups from sync (they will fail on write
   cards); avoid `#` in Search Group Members inputs; and fully re-connect (not merely reauthorize)
   whenever you change connector scopes.

## Recent Platform Changes (2025–2026)

- **2025.05.1:** Okta ITP connector added (Global Token Revocation, Retrieve/Upsert User Risk,
  Universal Logout, etc.); **Send Slackbot Message card fully deprecated** — update flows or they
  error; fix OKTA-928020 (space-only or duplicate names for folders/flows/tables were previously
  allowed).
- **2025.06.1:** Smartsheet sheet-count deprecated; fix OKTA-858112 (Zendesk List Group Members
  didn't return all members); fix for Branching Lookup values starting with a number and containing
  text not saving correctly.
- **2025 broader:** Connector Builder Polling Monitors (custom event triggers for APIs without
  webhooks); AI-agent events became event-hook-eligible; root CA certificate baseline updated to Dec
  31, 2024 (CAs removed from the Common CA DB after Mar 11, 2023 deprecated in 2025.03.0); fix
  OKTA-946866 ("In Workflows, the Okta Connector app didn't display a list of available connector
  actions").
- *Sources:* help.okta.com Workflows production release notes; workflows-version-history.htm;
  devforum.okta.com 2025.06.1 release thread.

## Caveats

- Okta Workflows is a continuously updated SaaS with no discrete version numbers; specific card
  behaviors (especially the "tip-bug" 1.3 and fixed OKTA-xxxxx items) may already differ in the
  target org. Validate each quirk in the Ionis sandbox before relying on a workaround.
- The Tables concurrent-write race condition (3.5) is an inference from the documented read-then-write
  upsert pattern, not an explicitly documented bug — **labeled THEORY**.
- No confirmed public bug report was found for APP_GROUP/OKTA_GROUP filtering misbehavior, nor for
  the Entra Search Group Members card silently dropping paginated results beyond its documented
  900-record cap — **treat those specific claims as UNCONFIRMED**.
- Latency has no SLA (Workflows is multi-tenant) and execution can vary 10x or more. Do not build
  hard timing assumptions into sync reconciliation logic.
- Two concurrency figures coexist and are easily confused: the **Okta connector** limit (30
  concurrent Workflows → org requests) versus the **org-wide** API concurrency limit (default 75
  simultaneous transactions, tracked separately for M365 vs. other traffic). Confirm which governs
  each card path.
