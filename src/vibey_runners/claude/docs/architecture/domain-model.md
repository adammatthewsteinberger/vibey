# Domain model reference

Every type below lives in `src/claudeloop/domain/`, has zero third-party
imports, and is fully covered by `tests/domain/`. This page documents what
each module contains and *why* it's shaped the way it is — for line-level API
docs, see the mkdocstrings-generated [reference](../reference/api.md).

## `errors.py` — the error hierarchy

```python
AutoclaudeError                    # base for every error claudeloop raises itself
├── InvalidPlanError               # a plan file couldn't be parsed into work items
├── InvalidSessionSelectorError    # a session selector is malformed
├── BudgetExceededError            # a run exceeded its turn/dollar/attempt budget
└── AuthenticationFailedError      # terminal — credentials invalid/revoked
```

Pure `Exception` subclasses, raised by `__post_init__` validators throughout
the rest of this module. Nothing here carries I/O state (no file handles, no
HTTP response objects) — just enough context to explain what was invalid.

## `plan.py` — `WorkPlan`, `PlanItem`

Parses a markdown handoff file into a `WorkPlan`: the raw text plus any
checkbox items found in it (`- [ ] ...` / `- [x] ...`, both bullet styles,
either case for `x`). A plan with no checkboxes is still valid — bare
free-text instructions — just with an empty `items` tuple.

```python
plan = WorkPlan.parse(markdown_text)
plan.remaining_items  # tuple[PlanItem, ...] — the ones not yet done
plan.is_fully_done  # True only if it HAS items and all are done
plan.with_items_marked_done(frozenset({"item text", ...}))  # new WorkPlan
```

`with_items_marked_done` is how a turn's structured `remaining_work` verdict
(see [`completion.py`](#completionpy-completionverdict) below) gets
reconciled back against the plan's own checklist between turns, so the audit
log can show *which* items are actually left rather than one boolean.

## `session.py` — `SessionRef` and the selector union

`SessionRef` is a resolved pointer to a Claude Code session (id, cwd, and
optional enrichment: last-modified time, git branch, first-prompt preview).

Three ways to *ask* for a session, modeled as a closed union rather than
optional/nullable fields on one class — the legacy script's three input
modes made explicit as types instead of `if prompt_file: ... elif
session_id: ... else: ...`:

```python
SessionSelector = PlanFileSelector | ExplicitSessionSelector | MostRecentSessionSelector
```

| Selector | Legacy equivalent |
|---|---|
| `PlanFileSelector(plan_path)` | `python3 claude_autoresume.py handoff.md` |
| `ExplicitSessionSelector(session_id)` | `python3 claude_autoresume.py --session-id <id>` |
| `MostRecentSessionSelector(cwd)` | no arguments — auto-detect the most recent session |

## `capacity.py` — `CapacityState`

The core insight this module encodes: **not every rejection is the same kind
of "no."** A five-hour rate-limit window and an empty credits balance both
surface as an HTTP 429, but only one of them will ever resolve by waiting.

```python
CapacityState = Available | WindowExhausted | CreditsExhausted | AuthenticationFailed
```

- **`Available(utilization: float | None)`** — capacity exists; spend a real
  turn. `utilization` is informational (from an `allowed_warning` signal) and
  must never itself block a turn.
- **`WindowExhausted(rate_limit_type, resets_at)`** — a
  `five_hour` / `seven_day` / `seven_day_opus` / `seven_day_sonnet` / `overage`
  window is rejected. `resets_at` is the trusted reset instant *when known* —
  it is `None`, not a guess, when the signal didn't carry one.
- **`CreditsExhausted(can_purchase: bool = True)`** — no token/time budget
  fixes this. There is **no `resets_at` field on this type at all** — that's
  deliberate, not an oversight, because a clock advancing can never resolve
  an empty credits balance. Only a human buying more can, which is why the
  waiting policy (below) treats this state completely differently.
- **`AuthenticationFailed(detail)`** — terminal. `is_waitable()` returns
  `False` only for this state; every other state is, by construction,
  something a wait-and-retry loop can eventually clear.

## `classify.py` — `TurnSignals` → `CapacityState`

This is the direct, tested replacement for `extract_limit_signals()` in
`legacy/claude_autoresume.py` (lines 276–333), which regex-matched raw
stream-json text against phrases like `"usage limit"` / `"try again later"`.
`classify()` instead operates on typed fields the Agent SDK has already
parsed:

```python
def classify(signals: TurnSignals) -> CapacityState: ...
```

`TurnSignals` deliberately gathers fields from **three different SDK
surfaces** — `RateLimitEvent`, `ResultMessage.api_error_status`, and
`AssistantMessage.error` — rather than trusting `RateLimitEvent` alone. The
Claude Code binary contains the string `[sdkMessageAdapter] Ignoring
rate_limit_event message`, suggesting that event is dropped on some adapter
paths; classification must not have a single point of failure.

**Ordering matters and is tested explicitly** (see
`tests/domain/test_classify.py`):

1. `assistant_error == "authentication_failed"` outranks everything —
   terminal, checked first, regardless of what else the turn carried.
2. `rate_limit_status == "allowed_warning"` is **not** a rejection. This is
   the exact false positive that caused multi-day cooldowns in the legacy
   script: `allowed_warning` carries a far-future weekly `resetsAt` just like
   a real rejection does, so a classifier that doesn't special-case it will
   misfire on ordinary healthy traffic.
3. A rejection (`status == "rejected"` OR `api_error_status == 429` OR
   `assistant_error == "rate_limit"`) is then split: credit signals
   (`error_code == "credits_required"`, `disabled_reason ==
   "out_of_credits"`, or a set `overage_disabled_reason`) win over a stray
   reset time — a `resets_at` present alongside a credits signal is ignored,
   because waiting can never fix that state regardless of what timestamp
   rode along with it.
4. Anything left is `WindowExhausted`, falling back to
   `rate_limit_type="unknown", resets_at=None` when the signal is thin.

## `completion.py` — `CompletionVerdict`

```python
CompletionVerdict = Done | Continue | Blocked
```

Primary source: a structured JSON verdict the model returns every turn via
`ClaudeAgentOptions.output_format`:

```json
{"complete": bool, "remaining_work": [str], "blocked_on": str | null, "summary": str}
```

`evaluate()` maps that (as a `StructuredVerdict`) to the union above, with
`blocked_on` outranking `complete` — a turn can't claim done and blocked at
once, and a non-null `blocked_on` **terminates the run as failed**. It is
only for true external/human blockers (credentials, billing, required human
decisions); waitable self-started work (background tasks, pending suites)
belongs in `remaining_work` with `blocked_on: null`. When `structured` is
`None` (older model, or structured output unsupported), it falls back to
substring-matching a legacy marker (`CLAUDELOOP_TASK_FULLY_COMPLETE` by
default) in the raw output text, exactly as `claude_autoresume.py` does
today — but only as a fallback, not the primary mechanism, because a marker
can collide with the user's own prompt text or appear inside a truncated
limit message. The run loop (below) never trusts a `Done` verdict over a
real capacity rejection, regardless of which detection path produced it.

## `waiting.py` — `WaitPolicyConfig` & `next_probe_instant()`

The direct replacement for `time.sleep(wait_seconds)` in the legacy script
(line 655). `next_probe_instant()` returns *the next instant to check again*
— never a single long sleep — because the whole point is noticing a mid-wait
credit top-up or an overage lift before a fixed deadline arrives.

```python
def next_probe_instant(
    state: CapacityState,
    *,
    now,
    started_waiting_at,
    probe_count,
    config: WaitPolicyConfig = ...,
) -> datetime: ...
```

Behavior by state:

- **`CreditsExhausted`** — exponential backoff from
  `credits_probe_interval` (default 120s) up to `credits_probe_ceiling`
  (default 600s), computed in float seconds and clamped *before*
  constructing a `timedelta` — an unclamped `interval * factor**probe_count`
  overflows `timedelta`'s ~2.7-million-year magnitude limit well within
  realistic probe counts, which a Hypothesis property test caught during
  development (see the property tests in `tests/domain/test_waiting.py`).
- **`WindowExhausted(resets_at=...)`** — probes at
  `min(resets_at + reset_grace, now + window_probe_interval)`. The
  `resets_at` bound is the expected path; the interval bound is what catches
  a top-up that lifts an overage-driven rejection *before* the window would
  naturally roll over — without it, a seven-day window's `resets_at` would
  mean waiting up to a week to notice capacity actually returned days ago.
- **`WindowExhausted(resets_at=None)`** — falls back to
  `window_probe_interval` alone.
- `config.max_wait`, when set, clamps every candidate instant to
  `started_waiting_at + max_wait`; `wait_exceeded()` is the corresponding
  "give up" check the run loop uses to fail rather than wait forever.

## `budget.py` — `Budget`, `BudgetLedger`

Immutable spend tracking for an unattended, potentially multi-day run.
`Budget` declares optional caps (`max_turns`, `max_dollars`, `max_attempts`);
`BudgetLedger` tracks consumption against it, and every spend
(`spend_turn()`, `spend_attempt()`) returns a **new** ledger rather than
mutating in place — the same immutability discipline as the rest of the
domain layer, which is what makes the run-loop state machine's transitions
pure functions.

## `loop.py` — the run-loop state machine

Ties every module above together into `RunLoopStateMachine`: a set of pure
functions from `(RunState, event, now)` to `(RunState, Decision)`. This is
the piece `application/runner.py` executes against real ports
ports — `domain/loop.py` itself performs no I/O; it only decides what I/O
should happen next.

```
Phase: PREFLIGHT → RUNNING → WAITING → PROBING → COMPLETE | FAILED
```

| Function | Called when | Key rule |
|---|---|---|
| `decide_preflight` | run starts | Mirrors `preflight_wait()` in the legacy script — check capacity before spending a real attempt. |
| `decide_after_turn` | a real turn completed | **A capacity rejection always outranks a completion claim** — even a `Done` verdict, because a limit message truncating mid-response could coincidentally contain marker-like text. Tested explicitly as `test_after_turn_limit_outranks_completion_claim`. |
| `decide_after_probe` | a throwaway probe turn completed while waiting | Re-classifies; `Available` resumes running, anything else reschedules. |

`Decision` is itself a closed union (`SendTurn | RunProbe | ScheduleProbe |
Finish`) so the executor in `application/` can pattern-match on exactly what
to do without the state machine reaching out and performing it directly.

## Design principles this module holds itself to

1. **Every public type is a frozen dataclass or a closed union of them.**
   No mutation, no inheritance hierarchies standing in for sum types.
2. **No third-party imports, ever.** `domain/` imports only `dataclasses`,
   `datetime`, `enum`, `typing`, and its own siblings. This is enforced by
   `import-linter`, not just convention.
3. **Every branch is a tested branch.** The domain package carries a 100%
   coverage floor in CI specifically because untested branches here are the
   most consequential kind of bug — they're the code that decides whether an
   unattended, multi-day run keeps going, waits, or gives up.
4. **Hypothesis property tests, not just examples**, for anything with a
   numeric or time-based invariant (`waiting.py`'s backoff and clamping).
   Property tests are what caught the `timedelta` overflow bug during
   development — an example-based test at any specific `probe_count` would
   have passed right up until it didn't in production.
