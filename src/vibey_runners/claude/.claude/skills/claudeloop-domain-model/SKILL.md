---
name: claudeloop-domain-model
description: Explains every value object and ADT in src/claudeloop/domain/ — CapacityState (Available/WindowExhausted/CreditsExhausted/AuthenticationFailed), TurnSignals classification, CompletionVerdict (Done/Continue/Blocked), the wait-probe policy in waiting.py, Budget/BudgetLedger, and the run-loop state machine in loop.py. Use this whenever reading, modifying, or extending anything in src/claudeloop/domain/ or tests/domain/, whenever the user asks about rate-limit classification, credits vs. rate limits, capacity states, completion detection, the waiting/backoff policy, or the run-loop state machine, and whenever adding a new domain type or branch. Make sure to consult this before touching domain/classify.py, domain/waiting.py, domain/completion.py, or domain/loop.py — the ordering of branches in each is deliberate and tested, and an out-of-order edit silently reintroduces bugs this project was specifically built to fix.
allowed-tools: Read Grep Glob
---

# claudeloop domain model

Everything in `src/claudeloop/domain/` is a frozen dataclass or a closed
union of them, has zero third-party imports, and requires 100% test
coverage. This skill is the map; for full prose explanation with rationale
see `docs/architecture/domain-model.md`.

## `capacity.py` — CapacityState

```python
CapacityState = Available | WindowExhausted | CreditsExhausted | AuthenticationFailed
```

**The single most important fact in this codebase**: `CreditsExhausted` has
**no `resets_at` field at all** — not `None`, the type literally doesn't
carry one — because waiting for a clock can never fix an empty credits
balance. `WindowExhausted` carries `resets_at: datetime | None`.
`is_waitable(state)` is `False` only for `AuthenticationFailed`.

**Never conflate these two states** and never add a `resets_at` field to
`CreditsExhausted` "for consistency" — that would silently reintroduce the
exact bug (`claudeloop` replacing sleeping-an-hour-forever with something
smarter) this project exists to fix.

## `classify.py` — TurnSignals → CapacityState

`classify(signals: TurnSignals) -> CapacityState`. Reads **three
independent SDK signals** (a `RateLimitEvent`, `ResultMessage
.api_error_status`, `AssistantMessage.error`) — never trust
`RateLimitEvent` alone; it's reportedly dropped on some adapter paths.

**Ordering is load-bearing, in this exact sequence:**

1. `assistant_error == "authentication_failed"` → `AuthenticationFailed`, checked FIRST, outranks everything.
2. `rate_limit_status == "allowed_warning"` → `Available` (NOT a rejection — this is the exact false positive that caused multi-day cooldowns in the legacy script).
3. A rejection signal present → split further: credit signals (`error_code == "credits_required"`, `disabled_reason == "out_of_credits"`, a set `overage_disabled_reason`) win over a stray `resets_at` — check credits BEFORE falling through to `WindowExhausted`.
4. Anything else rejected → `WindowExhausted`, falling back to `rate_limit_type="unknown", resets_at=None` if thin.

If you're editing `classify.py`, preserve this order and re-run
`tests/domain/test_classify.py` — every branch above has a dedicated test
asserting it, including the adversarial case where a `resets_at` is present
alongside a credits signal (credits must still win).

## `completion.py` — CompletionVerdict

```python
CompletionVerdict = Done | Continue | Blocked
```

Primary signal: `StructuredVerdict` from `ClaudeAgentOptions.output_format`
(`{complete, remaining_work, blocked_on, summary}`). `blocked_on` outranks
`complete` — never let a turn claim both — and **terminates the run**. It is
only for true external/human blockers; waitable self-started work belongs in
`remaining_work` with `blocked_on: null` (schema descriptions + autonomy
prompt reinforce this). Fallback (only when `structured is None`):
substring-match `CLAUDELOOP_TASK_FULLY_COMPLETE` (or the configured marker)
in raw output text — this is a fallback, not the primary path, and must stay
that way; the substring approach has two documented failure modes (collision
with user prompt text, truncation inside a limit message).

## `waiting.py` — WaitPolicyConfig & next_probe_instant()

`next_probe_instant(state, *, now, started_waiting_at, probe_count, config)
-> datetime`. **Never returns a duration to sleep — always the next instant
to probe.** Behavior differs by `CapacityState` type:

- `CreditsExhausted` — exponential backoff, `credits_probe_interval`
  (default 120s) to `credits_probe_ceiling` (default 600s). **Compute the
  backoff in float seconds and clamp to the ceiling BEFORE constructing a
  `timedelta`** — `interval * factor**probe_count` unclamped overflows
  `timedelta`'s magnitude limit at realistic probe counts. A Hypothesis
  property test caught this during development; don't reintroduce it.
- `WindowExhausted(resets_at=X)` — `min(X + reset_grace, now +
  window_probe_interval)`. Never trust a far-future `resets_at` alone; the
  interval bound is what catches an early overage lift or credit top-up.
- `WindowExhausted(resets_at=None)` — falls back to `window_probe_interval`.

`config.max_wait`, when set, clamps every candidate to
`started_waiting_at + max_wait`; `wait_exceeded()` is the paired "give up"
check.

**Any new numeric field on `WaitPolicyConfig` needs a `__post_init__`
validation AND a Hypothesis property test** covering its invariant across
the full input space — not just hand-picked examples. See
`tests/domain/test_waiting.py` for the existing property tests as a
template.

## `budget.py` — Budget, BudgetLedger

Immutable. `spend_turn()` / `spend_attempt()` return a **new** ledger, never
mutate. `any_exhausted` ORs `turns_exhausted | dollars_exhausted |
attempts_exhausted`. An unset cap (`None`) is never exhausted.

## `loop.py` — the run-loop state machine

`Phase = PREFLIGHT | RUNNING | WAITING | PROBING | COMPLETE | FAILED`.
Three pure decision functions:

- `decide_preflight(state, capacity, *, now)` — before spending the first
  real turn.
- `decide_after_turn(state, *, capacity, verdict, now)` — **the single most
  important invariant in the whole codebase**: capacity is checked BEFORE
  verdict, always. A `Done` verdict on a turn that also hit a rejection is
  discarded — see `test_after_turn_limit_outranks_completion_claim`. Never
  reorder this check.
- `decide_after_probe(state, capacity, *, now, config)` — after a throwaway
  probe while waiting.

`Decision = SendTurn | RunProbe | ScheduleProbe | Finish` — a closed union
the `application/runner.py` executor pattern-matches
exhaustively, never partially.

## `plan.py` / `session.py`

`WorkPlan.parse(markdown)` extracts checkbox items (`- [ ]` / `- [x]`, both
bullet styles, either case). `with_items_marked_done(frozenset)` reconciles
a turn's `remaining_work` back against the plan. `SessionSelector =
PlanFileSelector | ExplicitSessionSelector | MostRecentSessionSelector` —
the legacy script's three input modes as a closed union instead of
if/elif on optional fields.

## Full reference

`docs/architecture/domain-model.md` (complete prose walkthrough),
`docs/architecture/run-loop-state-machine.md` (the state machine in detail,
including the credit-top-up worked example),
`docs/architecture/decisions/0003-*.md` through `0004-*.md` (why
`CreditsExhausted` is distinct, why probing beats sleeping).
