---
name: okta-workflows-loops
description: "Use when building or debugging looping constructs in Okta Workflows: For Each - Ignore Errors (the asyncEach card) and its concurrency input flooding downstream Okta/Graph rate limits (30 concurrent Workflows → Okta org requests, 15 concurrent GET /users/{id}, the core.concurrency.org.limit.violation System Log event, and the separate org-wide 75-transaction limit); 'For Each - Ignore Errors' only ignoring errors from the parent's perspective (handle errors in the helper flow); plain For Each returning no output values (use Map/Reduce or a shared Table/stash); deeply nested iteration cards (For Each, Map, Reduce) triggering CPU-time throttling; the List - Filter substring / starts-with direction gotcha (List - Filter (Custom)); and when to switch to Stream Matching Records for very large lists. Triggers on For Each, asyncEach, concurrency, parallel branch executions, 429 rate limit, Map/Reduce no outputs, List Filter Custom, Stream Matching Records."
---

# Okta Workflows — Looping Constructs (§2)

Five quirks. The governing rule (see `okta-workflows-field-guide`): never do bulk/looping work
synchronously in a parent flow.

## Quirk 2.1 — Unbounded For Each / async concurrency floods downstream rate limits

"For Each - Ignore Errors" (the `asyncEach` card) takes a `concurrency` (Number) input: "Number of
items in the list to process in parallel. If it is important that the items are processed in
sequence, use 1. Otherwise a higher number like 5 or 10 will cause your flow to complete sooner."
With no throttle, parallel branch executions each fire Okta/Graph API calls and hit the Okta
connector's hard concurrency ceiling (30 concurrent Workflows → Okta org requests; 15 concurrent GET
/users/{id}). A 429 due to a concurrency limit shows a `core.concurrency.org.limit.violation` event
in the System Log.

- *Workaround:* Set `concurrency` explicitly (1 for strict ordering; 5–10 for throughput, staying
  well under the connector ceiling). For very large lists prefer Stream Matching Records, which
  paginates with low memory.
- *Sources:* Okta docs list_asynceach.htm, architecture-best-practices.htm, developer.okta.com
  rl2-concurrency
- *Note:* Two distinct concurrency numbers apply. The **Okta connector** limit is 30 concurrent
  Workflows → org requests (workflows-system-limits.htm). The **org-wide** API concurrency limit is a
  separate default of 75 simultaneous transactions, tracked separately for Microsoft 365 vs. all
  other traffic (developer.okta.com rl2-concurrency). Design against whichever applies to the
  specific card.

## Quirk 2.2 — "For Each - Ignore Errors" only ignores errors from the PARENT's perspective

"While the card name implies that it ignores errors, this is only true from the parent flow
perspective. You can handle errors in your helper flows." A failing item won't stop the batch, but
you get no parent-level signal — implement logging/error capture inside the helper flow (e.g., write
failures to a Tables error log).

- *Source:* architecture-best-practices.htm

## Quirk 2.3 — Plain For Each returns no outputs

"The For Each function card does not return any output values." To collect results, use Map/Reduce or
have the helper flow write to a shared Table/stash.

- *Source:* list_each.htm

## Quirk 2.4 — Deeply nested iteration cards can trigger CPU-time throttling

Per the Execution limits page: "Flows that exceed CPU time limits may use highly nested child flow
structures with nested iteration cards, such as For Each, Map, or Reduce. Deeply nested iteration
cards can exponentially grow the number of executions."

- *Source:* about-execution-limits.htm

## Quirk 2.5 — Filter direction / substring gotcha

The built-in List - Filter checks substring membership in a specific direction; community guidance
(Max Katz) recommends the List - Filter (Custom) card with a helper flow for "starts with"/arbitrary
text matching, since the built-in filter and Tables searches don't support starts-with text
semantics.

- *Source:* maxkatz.net custom list filter guide
