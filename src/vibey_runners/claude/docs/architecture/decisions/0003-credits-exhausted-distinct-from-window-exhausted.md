# ADR 0003: `CreditsExhausted` as a distinct state from `WindowExhausted`

## Status

Accepted. Implemented in M1.

## Context

`claude_autoresume.py` treats every rate-limit rejection identically: parse a
reset time if one is findable in the message text, otherwise fall back to a
fixed `--wait-minutes` (default 60), sleep, retry. A real transcript captured
during development contains a rejection that this logic handles badly:

```json
"apiErrorStatus": 429, "isApiErrorMessage": true, "error": "rate_limit",
"errorDetails": "429 {... \"error_code\":\"credits_required\",
  \"can_user_purchase_credits\":true, \"exhausted_included_allowance\":false,
  \"disabled_reason\":\"out_of_credits\"}"
```

There is no reset time here, and there never will be one — the account is
out of usage credits, and only a human purchasing more can change that. The
legacy script's fallback path sleeps 60 minutes and retries. Forever. It has
no way to distinguish "wait an hour, the window resets" from "this will
never resolve on its own."

## Decision

Model `CreditsExhausted` as a separate variant of `CapacityState`, disjoint
from `WindowExhausted`, and — critically — give it **no `resets_at` field at
all**. This isn't a `None` default; the type itself doesn't have the concept.

## Consequences

- `classify()` checks credit signals (`error_code == "credits_required"`,
  `disabled_reason == "out_of_credits"`, a set `overage_disabled_reason`)
  and routes to `CreditsExhausted` **even if a `resets_at` timestamp happens
  to be present alongside them** — credits outrank a stray reset time,
  because waiting for a clock can never fix an empty balance regardless of
  what timestamp rode along with the rejection.
- The waiting policy (`domain/waiting.py`) branches on the type of
  `CapacityState`, not on whether a `resets_at` is `None` — which means the
  compiler-level type system (via `mypy --strict`, since `resets_at` simply
  doesn't exist on `CreditsExhausted`) rules out ever writing
  `now + resets_at` against a state that has no reset time, rather than that
  invariant living only in a runtime `None` check someone could accidentally
  skip.
- This directly enables the credit-top-up probe behavior in
  [ADR 0004](0004-adaptive-waiting-with-probes-not-sleep.md): because
  `CreditsExhausted` is its own type, the wait policy can give it an entirely
  different strategy (bounded exponential backoff with no upper deadline
  derived from a timestamp) instead of forcing every rejection through one
  "parse a time or guess" code path.
