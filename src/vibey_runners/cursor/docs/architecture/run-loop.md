# Run-loop state machine

```
PREFLIGHT → RUNNING ↔ WAITING/PROBING → COMPLETE | FAILED
```

- **PREFLIGHT** — doctor-grade checks: auth proven, plan parsed, budget and
  timeout bounds loaded. A run that cannot pass preflight never starts.
- **RUNNING** — turns execute under two watchdogs: `turn_timeout_seconds` for
  a hung turn and `stall_timeout_seconds` for silent output.
- **WAITING/PROBING** — entered only for capacity verdicts that are waitable
  (rate-limit windows). A bounded probe re-tests capacity; `max_wait_seconds`
  caps the whole excursion. Credit exhaustion never enters this state — it
  fails fast instead.
- **COMPLETE / FAILED** — terminal; the JSONL audit trail and savepoints
  record how the run got there.

**Capacity outranks completion**: a completion signal observed while capacity
says stop is recorded but not trusted, because a starved model emits
plausible-looking final output.
