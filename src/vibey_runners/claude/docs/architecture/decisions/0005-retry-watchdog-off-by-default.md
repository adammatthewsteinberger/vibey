# ADR 0005: `CLAUDE_CODE_RETRY_WATCHDOG` left off by default

## Status

Accepted. Planned for the M2/M3 agent gateway adapter.

## Context

Claude Code (since v2.1.186) supports `CLAUDE_CODE_RETRY_WATCHDOG=1`, which
retries 429/529 errors indefinitely in-process, backing off up to five
minutes between attempts, and — when the response carries a rate-limit reset
time — waiting out the remaining window automatically. This looks, at first
glance, like it makes most of this project's waiting logic unnecessary.

## Decision

The outer `claudeloop` run loop does **not** set
`CLAUDE_CODE_RETRY_WATCHDOG=1` by default. A `--retry-watchdog` flag is
planned to opt into it for users who prefer the built-in behavior.

## Consequences

Setting the watchdog would mean the `claude` subprocess itself blocks for
however long a limit lasts — potentially hours or days — with none of the
following available to the caller during that time:

- **No progress reporting.** `claudeloop`'s `ProgressReporter` port and
  audit log exist specifically so a human (or a monitoring system) can see
  *why* nothing is happening right now, not just that nothing is happening.
- **No credit-vs-window discrimination.** The watchdog retries 429s
  uniformly; it has no concept of `CreditsExhausted` being fundamentally
  different from `WindowExhausted` (see [ADR 0003](0003-credits-exhausted-distinct-from-window-exhausted.md)),
  so it cannot fire the `Notifier` port to tell a human "this one needs you
  to act, waiting alone will never resolve it."
- **No `--max-wait`.** The watchdog's backoff is unbounded by design;
  `claudeloop`'s policy has an explicit, configurable ceiling after which a
  run gives up cleanly rather than hanging indefinitely with no operator
  visibility.
- **Nothing in the audit log.** A multi-hour in-process retry inside the SDK
  subprocess produces no structured record of *when* capacity was lost and
  regained — exactly the information `domain/waiting.py`'s design is built
  to surface ("capacity restored at probe #7, 26m into a 5h window").

The watchdog remains a reasonable choice for simpler use cases, which is why
it's exposed as an explicit opt-in rather than removed as an option — but
`claudeloop`'s own probe-based waiting (see
[ADR 0004](0004-adaptive-waiting-with-probes-not-sleep.md)) is the default
specifically because it's observable and can distinguish the one case
(exhausted credits) where waiting is never going to work.
