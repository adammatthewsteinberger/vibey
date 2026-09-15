---
name: okta-workflows-hooks-streaming
description: "Use when designing Okta Workflows event hooks, streaming hooks, or handler/helper flow patterns: streaming helper flows that cannot be stopped and don't respect deactivation (10,000-record standard search limit, up to a 1 million-record maximum, ~13 hours for 500,000 records, ~25 hours for 1 million); the rigid streaming contract requiring inputs named exactly Record and State (both Object); State NOT being a mutable cross-page accumulator (the paginateData limitation) and the Connector Builder Paginate card object/break/path 'Do while' workaround with its 5,000-iteration cap; event hook hard limits and no ordering guarantee (3-second completion timeout, single retry, 400,000 events/24h with a 280,000 warning, max 25 active event hooks, 500 trigger flows, 100 events/payload, 100 inline hooks); API Endpoint flows dropping the connection at 60s sync / 120s async (API Connector Close, Call Flow Async + Return Raw); and finding the calling flow via the Caller object's root_wf_id. Triggers on streaming, can't stop a flow, Record and State, paginate, break/path, event hook limits, no ordering guarantee, root_wf_id, API Connector Close, inline hook 3s."
---

# Okta Workflows — Event Hooks, Streaming Hooks & Handler Flow Patterns (§4)

Six quirks covering the hook/streaming/handler-flow layer.

## Quirk 4.1 — Streaming helper flows cannot be stopped and don't respect deactivation

"You can't stop a flow once the execution begins. A helper flow that streams data from a search or
list card runs until the API returns all records or the flow reaches the specified maximum number of
records. Also, an in-progress flow doesn't stop running if you deactivate the flow." Streaming handles
data sets that exceed the 10,000-record standard search limit, up to a **1 million-record maximum**;
"Processing 500,000 records takes approximately 13 hours. Processing 1 million records takes
approximately 25 hours."

- *Source:* about-streaming.htm

## Quirk 4.2 — Streaming helper flow contract is rigid: inputs MUST be named `Record` and `State` (both Object)

"In the helper flow, create two input entries: Record and State. Set the type for both fields to
Object… The helper flow requires the input fields to be named Record and State." `Record` = current
item being processed; `State` = parent-defined extra inputs sent with every record.

- *Source:* search-with-streaming.htm

## Quirk 4.3 — `State` is NOT a mutable cross-page accumulator (the paginateData custom-parameter limitation)

The docs describe `State` as parent-defined inputs sent to the helper flow with each record; there is
no documented mechanism for the helper flow to mutate `State` and have that change survive to the next
record/page. This is the structural limitation behind the user's finding that streaming Handler Flows
do not thread custom/user-defined parameters through the built-in paginate mechanism.

- *Workaround:* Implement manual cursor-based pagination. For raw HTTP, use the Connector Builder
  Paginate card, which "acts like a 'Do while' loop": pass an `object` containing a break key
  (commonly named `break`) set to FALSE plus a `path` field naming that key; the helper flow updates
  the object each iteration and *removes* the `path` key to stop. "Proper use of the path field is
  important… If it isn't properly managed, the flow could run until it hits the maximum count of 5,000
  iterations." For state that must persist across pages, externalize it to a Tables row keyed by run
  ID rather than relying on `State`.
- *Sources:* http_paginate.htm; maxkatz.net Tips #73 (recursive Okta API pagination template)

## Quirk 4.4 — Event hook hard limits and no ordering guarantee

Event hook completion timeout is 3 seconds with a single retry (4xx = no retry; 2xx = success;
redirects not followed). Limits: 400,000 applicable events / 24h per org (System Log warning at
280,000; resets 24h after the first event); max 25 active event hooks/org; max 500 flows using an Okta
event card as trigger; max 100 events per event hook payload; max 100 inline hooks/org (3s timeout
each). "There's no guarantee for the order of event hook delivery or flow execution" — a
deactivation-event flow may run before or after a reactivation, so the user state may have changed.

- *Source:* workflows-system-limits.htm

## Quirk 4.5 — API Endpoint flows drop the connection at 60s (sync) / 120s (async)

Synchronous API-endpoint connections terminate at 60 seconds (the flow itself keeps running); async
waits drop at 120s. Inline hooks time out at 3s. Workaround: add API Connector Close as the first card
to release the HTTP connection immediately, then process asynchronously; or use Call Flow Async +
Return Raw.

- *Sources:* workflows-system-limits.htm; architecture-best-practices.htm

## Quirk 4.6 — Finding the calling flow from a helper

The first Helper Flow card exposes a `Caller` object containing `root_wf_id`. `root_wf_id` reliably
resolves only the immediate caller one level deep; for robust multi-level lineage use Event metadata
in Execution Log Streaming.

- *Source:* maxkatz.net Tips #57
