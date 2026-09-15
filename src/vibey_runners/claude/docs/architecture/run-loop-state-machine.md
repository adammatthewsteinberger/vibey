# The run-loop state machine

`src/claudeloop/domain/loop.py` implements the autonomous run loop as a pure
state machine: every transition is a function of `(RunState, an event, now)`
returning `(new RunState, Decision)`. Nothing in this module performs I/O —
`application/runner.py` is the layer that actually executes
a `Decision` against real ports. This separation is what makes the loop's
logic — including the parts that matter most, like never treating a rate
limit as "done" — testable without a live Claude Code session, a real clock,
or real waiting.

## States

```
                    ┌───────────┐
                    │ PREFLIGHT │  entered once, at run start
                    └─────┬─────┘
                          │
              ┌───────────┼───────────┐
              ▼           ▼           ▼
        ┌─────────┐  ┌─────────┐  (terminal)
        │ RUNNING │◄─┤ WAITING │
        └────┬────┘  └────┬────┘
             │             │
             ▼             ▼
      (turn completes) (probe fires)
             │             │
             └──────┬──────┘
                     ▼
          COMPLETE | FAILED  (terminal)
```

| Phase | Entered when | The `Decision` it produces |
|---|---|---|
| `PREFLIGHT` | Run starts | Check capacity before spending a real attempt — mirrors `preflight_wait()` in the legacy script, so a run started right after a manual session hit its limit doesn't immediately burn another attempt into the same wall. |
| `RUNNING` | Capacity is available | `SendTurn` — either the plan-file text (first turn) or a continuation prompt. |
| `WAITING` | Capacity is exhausted | `ScheduleProbe(at=...)` — never a blind sleep; see [`domain-model.md`](domain-model.md#waitingpy-waitpolicyconfig-next_probe_instant). |
| (implicit, inside `WAITING`) | A scheduled probe fires | `RunProbe` — a cheap, throwaway turn purely to re-check capacity. |
| `COMPLETE` | A real turn returned `Done` while capacity was `Available` | `Finish(success=True, reason=summary)` |
| `FAILED` | Authentication failure, a `Blocked` verdict, budget exhaustion, or `max_wait` exceeded | `Finish(success=False, reason=...)` |

## The three decision functions

### `decide_preflight(state, capacity, *, now)`

The very first branch of every run. `AuthenticationFailed` aborts
immediately — there's no scenario where retrying helps. `Available` sends the
first turn. Anything else (`WindowExhausted` or `CreditsExhausted`) enters
`WAITING` before a single real turn is spent.

### `decide_after_turn(state, *, capacity, verdict, now)`

Called once a real turn has completed. This is where the loop's single most
important invariant lives, and it's worth stating precisely because it's
easy to get backwards:

> **A capacity rejection always outranks a completion claim.**

A turn that gets cut off mid-response by a rate limit can, by coincidence,
contain text that looks like a completion marker or even a well-formed but
stale structured-output block from before the cutoff. `decide_after_turn`
checks `capacity` before it ever looks at `verdict` — if capacity isn't
`Available`, the function routes straight to `WAITING` regardless of what the
verdict claims. This is directly tested as
`test_after_turn_limit_outranks_completion_claim` in
`tests/domain/test_loop.py`.

When capacity *is* available, the verdict decides: `Done` → `COMPLETE`;
`Blocked` → `FAILED` with the blocking reason recorded; `Continue` → stays
`RUNNING` and sends another turn, **unless** the budget ledger reports
`any_exhausted`, in which case the run fails cleanly rather than spending a
turn it can't afford.

### `decide_after_probe(state, capacity, *, now, config)`

Called once a throwaway probe (not a real turn — no budget is spent)
completes while `WAITING`. `Available` resumes `RUNNING` immediately.
Anything else re-enters the waiting policy, incrementing `probe_count` so the
backoff in `domain/waiting.py` continues from where it left off rather than
resetting.

## Worked example: the credit top-up scenario

This is the scenario the project was explicitly built to handle correctly,
and it has a dedicated test
(`test_credit_topup_sequence_resumes_after_several_failed_probes` in
`tests/domain/test_loop.py`) that exercises the full state sequence:

1. `decide_preflight` sees `CreditsExhausted` → `WAITING`, first probe
   scheduled ~120s out.
2. Four consecutive probes each return `CreditsExhausted` again — each call
   to `decide_after_probe` reschedules with a longer backoff, capped at the
   configured ceiling (default 600s).
3. On a later probe, capacity has returned (a human added credits) —
   `decide_after_probe` sees `Available` and transitions straight back to
   `RUNNING`, producing `SendTurn`.

No step in that sequence involved a blind sleep to a fixed deadline —
`CreditsExhausted` carries no `resets_at` at all (see
[`domain-model.md`](domain-model.md#capacitypy-capacitystate)), so the *only*
way this scenario can ever resolve is a policy that keeps checking.

## `Decision` is a closed union

```python
Decision = SendTurn | RunProbe | ScheduleProbe | Finish
```

The executor (`application/runner.py`) pattern-matches
exhaustively on this union rather than the state machine reaching out and
performing the action itself. Keeping "decide what to do" and "do it"
strictly separate is what lets the entire state machine — including the
credit-top-up sequence above — be tested in `tests/domain/` with zero mocks,
zero real waiting, and zero SDK dependency.
