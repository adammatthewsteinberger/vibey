# ADR 0004: Adaptive probing instead of a single blind sleep

## Status

Accepted. Implemented in M1 (policy); probe adapter planned for M2/M3.

## Context

`legacy/claude_autoresume.py` (lines 505 and 667) does `time.sleep(wait_seconds)` — one sleep call
to either a parsed reset time or a fixed fallback, then a single retry.
Two problems, both explicitly requested to be fixed during planning:

1. A `WindowExhausted` rejection with a far-future `resets_at` (a seven-day
   window, say) sleeps the *entire* remaining duration even if an
   overage-driven rejection lifts hours or days earlier.
2. A `CreditsExhausted` rejection (see [ADR 0003](0003-credits-exhausted-distinct-from-window-exhausted.md))
   has no reset time at all — only a human buying credits resolves it, and
   that top-up can happen at any moment, including moments before the fixed
   fallback wait elapses.

## Decision

The waiting policy (`domain/waiting.py`) never computes "how long to sleep."
It computes **the next instant to probe**, and the run loop schedules a
cheap, throwaway turn at that instant rather than blocking. Behavior differs
by state:

- `CreditsExhausted` — exponential backoff between a short interval (default
  120s) and a ceiling (default 600s), with no upper bound derived from a
  timestamp, because none exists.
- `WindowExhausted(resets_at=...)` — probes at
  `min(resets_at + grace, now + window_probe_interval)`, so a long window
  still gets checked periodically rather than trusting the reset time
  blindly for its full duration.
- `WindowExhausted(resets_at=None)` — falls back to the interval alone.

## Consequences

- A credit top-up or an early overage lift is noticed within one probe
  interval, not at the end of a fixed sleep — directly satisfying the
  requirement that the system "handle if the user adds more credits between
  the time that the system ran out of the session limit and when the
  session limit would otherwise reset naturally."
- The probe itself must be cheap and side-effect-free: a one-token prompt,
  `max_turns=1`, no tools, `setting_sources=None` (no `CLAUDE.md` loaded),
  and `no-session-persistence` so it leaves no transcript and doesn't
  pollute the working session with throwaway "OK" turns. A rejected probe
  is not billed by the API, so the cadence is safe to run frequently.
- `next_probe_instant()` had a real bug caught by a Hypothesis property test
  during development: unbounded exponential backoff
  (`interval * factor**probe_count`) overflows Python's `timedelta` maximum
  magnitude at surprisingly modest probe counts. The fix computes the
  backoff in float seconds and clamps to the ceiling *before* constructing
  a `timedelta`. This is exactly the class of bug example-based tests tend
  to miss — see
  [`../../contributing/testing.md`](../../contributing/testing.md) for why
  property tests are mandatory for anything with a numeric or time-based
  invariant.
- `config.max_wait`, when set, bounds the total time a run will spend
  waiting before giving up entirely — a run should never wait literally
  forever even under this design, just far more responsively than a fixed
  sleep would.
