---
name: okta-workflows-execution-limits
description: "Use when hitting or planning around Okta Workflows execution limits and the resource model: the platform hard limits (100 MB instance memory; 2,000,000 max steps/flow; recursion limit 250 with the 'Stack limit exceeded' error; 1 MB payload per execution-history message with the 'The data returned successfully, but is too large to display' message that is explicitly NOT an error; 10 invocations/sec/flow flow-execution rate limit then 429; 30-day execution history; file attachments 10 MB, download/upload 2 GB, SFTP 25 MB, 30-day file retention; 30-day max pause duration); plan-gated active flow counts (Free Trial/Starter 5, Light 50, Medium 150, Maximum unlimited, legacy Advanced Lifecycle Management 100 parent flows, turned-off flows don't count); automated flow throttling as a platform feature ('Okta has identified that this flow has exceeded expected resource usage… the resource allocation for it has been limited', doesn't prevent completion, lower threshold on Free Trial/Starter); and export flow rate limits (15-minute window; Starter 10, Light 100, Medium 300, Maximum 1000; exceeding fails the whole export). Triggers on Stack limit exceeded, recursion limit 250, 2 million steps, too large to display, 10 invocations per second, active flow limit, flow throttling, export rate limit."
---

# Okta Workflows — Execution Limits & Resource Model (§6)

Four quirks describing the platform's hard limits, plan gating, throttling, and export caps.

## Quirk 6.1 — Key platform hard limits

Instance memory 100 MB; max steps/flow 2 million; recursion limit 250 (error: "Stack limit
exceeded"); payload limit 1 MB per execution-history message (message: "The data returned
successfully, but is too large to display" — explicitly NOT an error, no data impact); flow-execution
rate limit 10 invocations/sec/flow (then 429); execution history retained 30 days; file attachments 10
MB, download/upload 2 GB, SFTP 25 MB, file retention 30 days; max pause duration 30 days.

- *Source:* workflows-system-limits.htm

## Quirk 6.2 — Active flow count is plan-gated

Free Trial/Starter: 5; Light: 50; Medium: 150; Maximum: unlimited. Legacy Advanced Lifecycle
Management entitlement: 100 parent flows. Turned-off flows don't count.

- *Source:* workflows-system-limits.htm

## Quirk 6.3 — Automated flow throttling is now a platform feature

The internal system-limit analyzer throttles flows exceeding CPU time, table requests, memory, or
helper-flow counts within a window: "Okta has identified that this flow has exceeded expected resource
usage. This flow will complete, but the resource allocation for it has been limited." Loop-heavy and
table-heavy sync flows are prime candidates; Free Trial and Starter plans have a lower throttling
threshold. Throttling "doesn't impact or prevent the completion of a flow."

- *Source:* about-execution-limits.htm

## Quirk 6.4 — Export flow rate limits (15-min window)

Export capacity resets every 15 minutes; caps are plan-based (Starter 10, Light 100, Medium 300,
Maximum 1000). Exceeding the cap fails the entire export with no partial output.

- *Source:* workflows-system-limits.htm
