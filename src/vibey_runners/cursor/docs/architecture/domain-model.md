# Domain model

The domain answers one question — *should the loop run, wait, or stop right
now?* — from values, not I/O:

- **Capacity ADT** — a verdict on whether the vendor can take another turn:
  available, rate-limited (a waitable window), or exhausted credits (not
  waitable). Classification is driven by the billing and rate-limit lexicons
  from configuration, so a vendor's new error phrasing is a config change.
- **Waiting policy** — a bounded probe: waits carry a deadline
  (`max_wait_seconds`), never an open-ended sleep.
- **Budget ledger** — every turn's cost accrues against `max_dollars`; the
  ledger stops the run *before* an overrun, not after.
- **Completion verdicts** — the fence/marker/reconciliation evidence (see
  [completion detection](../guides/completion-detection.md)) reduced to one
  typed verdict.
- **Run-loop state machine** — the states and transitions in
  [run-loop.md](run-loop.md), consuming the values above.

Everything here is a frozen dataclass or an enum, so a transition is a fact
you can assert in a test.
