# Rate limits vs. exhausted credits

This is the distinction `claudeloop` exists to get right. Both look
identical from the outside — an HTTP 429 — but only one of them will ever
resolve by waiting.

## The two kinds of "no"

| | `WindowExhausted` | `CreditsExhausted` |
|---|---|---|
| What it means | A five-hour / seven-day / seven-day-Opus / seven-day-Sonnet / overage window is temporarily used up | The account has no usage credits left |
| Resolves by waiting? | **Yes** — once `resets_at` passes | **No** — never, on its own |
| Resolves by | The clock | A human buying more credits |
| Carries a `resets_at`? | Usually | **Never** — the type has no such field |
| `claudeloop`'s response | Probes near the reset time (with a fallback interval so it doesn't trust a far-future timestamp blindly) | Probes on a bounded backoff and notifies you that action is needed |

A real example of the second case, captured during development:

```json
"apiErrorStatus": 429, "error": "rate_limit",
"errorDetails": "... \"error_code\":\"credits_required\",
  \"disabled_reason\":\"out_of_credits\", \"can_user_purchase_credits\":true"
```

No reset time appears anywhere in that payload, because none exists. A tool
that sleeps a fixed hour and retries — which is exactly what the legacy
script this project replaces did — will do that forever.

## How classification works

`domain/classify.py`'s `classify()` function reads three independent
signals from a turn — the SDK's typed `RateLimitEvent`, the result's
`api_error_status`, and the assistant message's `error` field — specifically
because `RateLimitEvent` is reportedly dropped on some code paths, and a
single point of failure in the one function that decides "should I wait or
give up" is not acceptable. See
[`../architecture/domain-model.md#classifypy-turnsignals-capacitystate`](../architecture/domain-model.md#classifypy-turnsignals-capacitystate)
for the exact precedence rules, and
[ADR 0003](../architecture/decisions/0003-credits-exhausted-distinct-from-window-exhausted.md)
for why credit signals outrank a stray reset timestamp if both happen to be
present.

## Handling a credit top-up mid-wait

If `claudeloop` is waiting on `CreditsExhausted` and you add credits to your
account, it notices on the **next scheduled probe** — not at some fixed
deadline, because there isn't one to wait for. The probe cadence
(`--credits-probe-interval`, default 120s, backing off to
`--credits-probe-ceiling`, default 600s) is what bounds how long it takes to
notice; see
[ADR 0004](../architecture/decisions/0004-adaptive-waiting-with-probes-not-sleep.md)
for why this is a scheduled probe loop rather than a single sleep, and
[`../architecture/run-loop-state-machine.md`](../architecture/run-loop-state-machine.md#worked-example-the-credit-top-up-scenario)
for the exact state sequence, which is directly covered by a test.

## What the probe itself costs

The throwaway turn `claudeloop` sends to re-check capacity is deliberately
minimal — one token, no tools, no `CLAUDE.md` loaded, and configured not to
persist a transcript — so it costs nothing meaningful and doesn't pollute
your session history with "OK" turns. A rejected probe isn't billed by the
API either way.
