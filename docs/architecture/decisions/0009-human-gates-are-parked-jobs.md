# 0009 — Human gates park jobs; they never block workers

**Status:** accepted · **Date:** 2026-08-14

## Context

Vibey inherits a hard rule from the `*loop` family: **never block on a human.**
Those runners enforce it by *denying* any tool call that would ask a question,
pushing the model to proceed on a stated assumption instead.

But vibey's Phase 1 and Phase 3 are *defined* as conversations with a human. The
rule and the requirement appear to contradict.

## Decision

They don't, once the rule is read precisely. The rule is **never block a worker**,
not "never involve a human." Vibey inverts control:

- **Vibey owns the conversation**, not the engine. Engines are used for the
  autonomous parts of Phases 1 and 3 (research, synthesis, demo generation,
  triage). The interactive turn-taking is vibey's.
- **A handler that needs a human returns `Park(gate)`.** The worker writes a
  `human_gate` row, sets the job to `awaiting_human`, and **releases its lease and
  picks up the next job.** No thread waits on stdin.
- The developer answers via `vibey answer <gate_id>`, the TUI, or a notification
  action. That writes the answer, flips the job to `ready`, and `NOTIFY` wakes a
  worker.

## Rationale

Parking rather than blocking means an unanswered Phase 1 question does not stall
the three research jobs running in parallel, and an unanswered Phase 3 triage
question does not stall the rest of the queue. The developer can walk away
mid-interview and come back; work that does not depend on the answer keeps going.

It also preserves the property that makes Phase 2 safe: no code path anywhere in
vibey waits on a human, so a worker pool cannot be deadlocked by an absent
developer.

## Gate anatomy

```python
@dataclass(frozen=True, slots=True)
class HumanGate:
    gate_id: UUID
    job_id: UUID
    kind: GateKind      # question | approval | escalation | budget | handoff_failure
    prompt: str
    options: tuple[GateOption, ...]   # structured choices wherever possible
    default: str | None
    timeout_at: datetime | None
```

**Structured options wherever possible.** A gate that offers three labeled choices
is answerable from a phone notification; one that demands prose is not.

**Timeout defaults.** A gate with a `default` and a `timeout_at` auto-resolves,
which is what makes overnight runs viable for low-stakes decisions. Every
auto-resolution is recorded as an `AssumptionStated` event, so the decision is
visible, travels through every handoff, and is checked by gate rule R4. An
assumption taken at 3 a.m. because nobody answered is exactly the kind of thing
that must not vanish.

## Consequences

**Good.** Interactive phases and a never-blocking worker pool coexist. Parallel
work continues around an open question. Gates are durable — a crash does not lose
one.

**Bad.** More states in the job machine (`awaiting_human`, `awaiting_capacity`) and
a UX surface to build for answering. A gate raised with no notification configured
can sit unnoticed; `vibey status` surfaces open gates prominently and the TUI
shows a count.
