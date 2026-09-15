---
name: okta-workflows-tables
description: "Use when working with Okta Workflows Tables (the built-in data store): Search Rows (searchRows2) being case-sensitive ('The search expression is case sensitive') with no 'starts with' for text; the hard 3,500-row return cap regardless of the Limit field (page with the 0-based Offset input); table hard limits (500,000 rows/table, 64 columns/table, 16 KB / 16,000 chars per cell, 200 tables paid / 100 free); the Where Expression JSON lhs/op/join/rhs quirk when testing with variables; the no-native-upsert read-then-write race (Search Rows → If/Else on Row ID empty → Create Row or Update Row, duplicate rows under concurrency, serialize with a concurrency=1 helper — labeled THEORY); and high-frequency table requests triggering throttling. Triggers on Search Rows, searchRows2, case-sensitive table search, 3500 rows, Offset pagination, Where Expression, upsert, Create Row / Update Row race, table row/column/cell limits, To Lower Case."
---

# Okta Workflows — Tables (Built-in Data Store) (§3)

Six quirks. Normalize case before writing AND searching, and never assume Search Rows returns more
than 3,500 rows.

## Quirk 3.1 — Search Rows (searchRows2) is case-sensitive

The Search Rows card documentation states plainly: "The search expression is case sensitive." Numeric
conditions are fine; text matching fails on case mismatch, and there is no "starts with" for text.

- *Workaround:* Normalize case with a Text - To Lower Case card before writing AND before searching,
  or pull all rows and use a List - Filter (Custom) helper flow to perform case-insensitive/starts-with
  matching.
- *Sources:* Okta docs stash_searchrows2.htm; support.okta.com
  searching-a-table-using-a-custom-filter-in-workflows; maxkatz.net 2024/01/19

## Quirk 3.2 — Hard 3,500-row return cap regardless of Limit

"Regardless of the limit selected, the function card returns a maximum of 3,500 rows from the
selected table" (stash_searchrows2.htm). Confirmed independently by Max Katz "Workflows Tips #36"
(maxkatz.net, 2022/09/09): "If a filter or limit is not applied to the table search, a maximum of
3,500 rows from the selected table will be read by the Search Rows function card." Critical for
sync-reconciliation tables that can grow large.

- *Workaround:* Page with the Offset input (0-based) in a recursive/paginated helper flow, or design
  tables to be queried by indexed key columns returning fewer than 3,500 rows.

## Quirk 3.3 — Table hard limits

500,000 rows/table; 64 columns/table; 16 KB (16,000 chars) per cell; 200 tables (paid) / 100 (free).
"You can't add a row to a table after you've reached the limit."

- *Source:* workflows-system-limits.htm

## Quirk 3.4 — Where Expression JSON quirk when testing with variables

When passing a variable into the Where Expression and testing the card, you must hand-edit the Where
Expression JSON (lhs/op/join/rhs structure) or the test returns wrong output. Example:
`{"expr":[{"lhs":"Country","op":"=","join":"AND","rhs":"Brazil"},{"lhs":"Code","op":"=","join":"AND","rhs":"BR"}]}`.

- *Source:* maxkatz.net 2023/10/25

## Quirk 3.5 — No native upsert / concurrent-write race risk (THEORY)

There is no atomic upsert; the documented pattern is Search Rows → If/Else on Row ID empty → Create
Row or Update Row. When multiple concurrent flow executions (e.g., many event-hook-triggered flows)
run this read-then-write against the same table/key, there is a classic race window that can create
duplicate rows. **This concurrency/locking risk is a plausible-but-not-explicitly-documented inference
from the read-then-write pattern — label as THEORY.** Mitigation: funnel all table writes through a
single-concurrency (`concurrency=1`) helper flow or a scheduled batch to serialize writes.

- *Sources:* support.okta.com how-to-conditionally-update-a-table; upsert-example

## Quirk 3.6 — High-frequency table requests trigger throttling

"Table requests" is an explicit throttling resource: "Flows with highly active event cards that make
requests through Tables function cards" are called out as throttling-eligible.

- *Source:* about-execution-limits.htm
