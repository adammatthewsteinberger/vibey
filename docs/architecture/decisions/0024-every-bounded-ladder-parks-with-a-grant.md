# 0024 — Every bounded ladder ends in a park that can grant more

**Status:** accepted · **Date:** 2026-08-20 (recorded 2026-09-15) · **Extends:** ADR-0009, ADR-0006

## Context

The first unattended validation runs found three ways for the BUILD phase to spend money without converging. `build.verify` retried the same failing gate command seven times with nothing in between able to change the code — the escalation ladder (ADR-0006) raises effort, it never repairs. `build.integrate` spawned a fresh repair session on every failure with no bound at all, and pointed the repair at the item branch where the merge conflict does not exist. And nothing capped cycle spend: the budget source was never wired, so a repair storm burned until a human noticed — it did, live (#56, #58).

The opposite failure is as bad. A ladder that simply fails at its bound leaves a work item terminally dead with a fix one session away; and `escalation_exhausted` was exactly that dead end — answering the gate un-parked the job, the attempts were still past the ladder, and it parked again forever.

## Decision

**A deterministic failure enters a bounded repair ladder; the bound is a parked gate; the gate can grant more. Nothing in the autonomous path is unbounded and nothing is terminal.**

- **Verify.** A failing gate command raises an `f_verify_<item>` finding carrying both output streams, enqueues a repair `build.implement` for the same item (the worktree manager re-checks out the item branch so the fix lands where the deferred verify will look), and *defers* the verify with a 10-minute backoff instead of burning an attempt. While a finding is open, a re-failing verify only defers again — never a second session on the same failure. At `max_rounds` (3) the job parks as `verify_repair_exhausted`.
- **Integrate.** Same shape (`max_repair_rounds` 3, `integrate_repair_exhausted`), and the repair prompt says what a merge conflict actually needs: merge the integration branch into the worktree, resolve, commit, re-verify.
- **Rounds are counted from the ledger**, not from process memory: findings raised for the item this cycle. Durable, replay-safe, and correct after a worker dies mid-ladder.
- **A completed repair session resolves its finding** the moment it completes; the follow-up verify decides whether the fix worked. Without this the ladder livelocks (found live, #59).
- **Budget brake.** `LedgerBudgetSource` sums the cycle's real spend — `cost_usd` on `TurnCompleted` plus explicit `BudgetSpent` corrections — against caps from project config. Caps are opt-in (`vibey new --max-cycle-dollars/--max-cycle-turns`); an exhausted budget parks `budget_exhausted` **before** a session starts, never after.
- **Every park advertises its grant.** `verify_repair_exhausted` accepts `--raw '{"max_rounds": N}'`, `escalation_exhausted` accepts `max_attempts` (granted attempts run at the ladder's top effort), `budget_exhausted` accepts `max_dollars`/`max_turns`. The park is a decision point, not a dead end.

## Consequences

**Good.** Spend is bounded by construction: three sessions per item per ladder, then a human. A dead worker cannot reset a counter. Every exhausted bound is one `vibey answer` away from continuing, with the number to type printed in the park prompt.

**Bad.** Three parameters (rounds, backoff, caps) that a project may need to tune, and a verify that defers rather than fails looks idle for ten minutes to someone watching. The brake only sees spend engines actually report; an engine that omits `cost_usd` is invisible to it (agyloop cost events remain an open item).

**Rule status.** "No unbounded autonomous loop, and no terminal failure a human cannot widen" binds every future ladder, survives a rewrite, and is about how the project treats people and money. It passes ADR-0020's test and owes a sub-doctrine, not yet proposed; the parent doctrine and the wording are the operator's to ratify.

## Alternatives rejected

- **Retry the gate with escalating effort** (the pre-#48 behaviour). Effort cannot fix code nothing has changed.
- **Fail terminally at the bound.** The `escalation_exhausted` dead end, generalized.
- **Unbounded repair** (integrate before #52). A storm of paid sessions that cannot converge.
- **Count rounds in memory.** Resets on every worker death, which is the case the ledger exists for.
- **A silent default budget cap.** Rejected in favour of opt-in: a cap nobody set is a failure nobody can explain.
