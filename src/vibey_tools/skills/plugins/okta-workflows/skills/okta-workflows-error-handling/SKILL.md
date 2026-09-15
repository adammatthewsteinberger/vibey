---
name: okta-workflows-error-handling
description: "Use when building error handling and retry logic in Okta Workflows: card-level retry firing ONLY on HTTP 429 Too Many Requests (and 504 in Connector Builder) — 'You can't set error handling for other HTTP errors', default Retry 0 times, default After 5 minutes, Then options Halt Flow / Return Values / Run another Flow, Connector Builder default 'retry on 429 and 504… three times between one and three seconds', and non-429 retries needing an If Error block; custom retry status codes via a List Construct card, renaming its output (retry_codes), selecting 'Specified errors' in the Raw Request card's Error Handling dialog, and dragging it into the Status Codes field; the recommended limit of no more than three nested If Error blocks; and error propagation from helper flows (If Error / Try blocks act as anonymous helper flows, a Return proceeds after the block, use Return Error / Return Error If outside the block to propagate a hard failure). Triggers on 429 retry, 504, retry on other HTTP errors, retry_codes, List Construct, Specified errors, Raw Request error handling, nested If Error blocks, Return Error, Try block propagation."
---

# Okta Workflows — Error Handling & Retry Mechanism (§7)

Four quirks. The key surprise: automatic card-level retry only ever fires on 429.

## Quirk 7.1 — Card-level retry ONLY fires on HTTP 429 (and 504 in Connector Builder)

"Retries for cards in flows only take place as a result of HTTP 429 Too Many Requests errors. You
can't set error handling for other HTTP errors." Default Retry is 0 times; default After is 5 minutes;
Then options are Halt Flow / Return Values / Run another Flow. In Connector Builder, the default is
"retry on 429 and 504… three times between one and three seconds." For non-429 retries you must use an
If Error block.

- *Sources:* set-error-handling.htm; best-practices-rate-limits.htm

## Quirk 7.2 — Custom retry status codes via List Construct

To retry on other codes, add a List Construct card listing the codes, rename its output (e.g.,
`retry_codes`), select "Specified errors" in the Raw Request card's Error Handling dialog, and drag
`retry_codes` into the Status Codes field.

- *Source:* best-practices-rate-limits.htm

## Quirk 7.3 — Max 3 nested If Error blocks

"To avoid parsing errors caused by complex error handling, Okta recommends a limit of no more than
three nested If Error blocks."

- *Source:* architecture-best-practices.htm

## Quirk 7.4 — Error propagation from helper flows

If Error/Try blocks act as anonymous helper flows; a Return inside them proceeds *after* the block
rather than halting. To propagate a hard failure to the parent, use Return Error / Return Error If
outside the block.

- *Source:* errorhandling_trycatch.htm
