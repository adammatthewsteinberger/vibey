# 0009 — Human gates park jobs; they never block workers

**Status:** accepted · **Date:** 2026-08-14 · **Extended by:** ADR-0024

**Owes:** a sub-doctrine (not yet proposed) — human input is a parked job plus a `human_gate` row, never a worker waiting on a person (nearest parent: doctrine 12, humans first).

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
- **A handler that needs a human returns `Park(HumanGateRequest)`.** The worker
  writes a `human_gate` row *before* releasing the lease (so the job never looks
  claimable without the row that explains it), sets the job to `awaiting_human`,
  and **picks up the next job.** No thread waits on stdin. Raising a gate sends
  `NOTIFY vibey_gate_raised`.
- The developer answers with `vibey answer <gate_id>` (question/answer pairs,
  `--defaults`, `--choice`, `--verdict`, or `--raw` JSON), or, on Kubernetes,
  through the `VibeyProject` resource's `spec.answers`, which the operator applies
  through the same code path ([ADR-0025](0025-kubernetes-operator-crd-keda.md)).
  Answering writes the answer, flips the job to `ready`, and
  `NOTIFY vibey_job_ready` wakes a worker. A TUI answer path and actionable
  notifications are planned, not built.

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
class HumanGateRequest:                 # application/dto.py
    kind: str                           # free string; see below
    prompt: str
    options: tuple[str, ...] = ()       # structured choices wherever possible
    default_answer: str | None = None
    timeout_at: datetime | None = None
```

The persisted row (`HumanGateRecord`, table `human_gate`) adds `gate_id`,
`project_id`, `job_id`, `answer` (JSON), `raised_at`, `answered_at`, and
`answered_by`. Kinds are strings, not an enum. Those raised today are `question`,
`approval`, `choice`, `budget_exhausted`, `escalation_exhausted`,
`verify_repair_exhausted`, `integrate_repair_exhausted`, `too_many_wind_downs`,
`handoff_gate_failed`, `deploy_interview`, `deploy_acceptance`,
`deploy_demo_review`, and `deploy_failure_triage`. The `*_exhausted` gates end a
bounded ladder, and their answer can grant more of what ran out
([ADR-0024](0024-every-bounded-ladder-parks-with-a-grant.md)).

**Structured options wherever possible.** A gate that offers three labeled choices
is answerable from a phone notification; one that demands prose is not.

**Timeout defaults (designed, not implemented).** A gate with a `default_answer`
and a `timeout_at` is meant to auto-resolve, which is what would make overnight
runs viable for low-stakes decisions. Every auto-resolution would be recorded as an
`AssumptionStated` event, so the decision is visible, travels through every
handoff, and is checked by gate rule R4. Today the columns exist but no worker
expires a gate; `default_answer` is used only when a handler reads an answered gate
that lacks a choice, and an overnight run still waits for a human to answer. An
assumption taken at 3 a.m. because nobody answered is exactly the kind of thing
that must not vanish.

## Consequences

**Good.** Interactive phases and a never-blocking worker pool coexist. Parallel
work continues around an open question. Gates are durable — a crash does not lose
one.

**Bad.** More states in the job machine (`awaiting_human`, `awaiting_capacity`) and
a UX surface to build for answering. A gate raised with no notification configured
can sit unnoticed. `vibey status` and the `vibey watch` dashboard show the
`awaiting_human` job count in the queue depth, and the operator projection sets a
`Parked` condition naming the first open gate; none of them yet lists open gates
with their prompts.

## Alternatives rejected

- **A worker that waits on stdin.** One absent developer deadlocks the pool, which
  breaks the rule this record starts from.
- **Let the engine ask the question.** The `*loop` runners deny question tools by
  design; vibey would be re-enabling exactly what they forbid, inside a session
  that cannot survive the wait.
- **A separate pool of interactive workers.** Two kinds of worker double the lease
  and reaper surface and still hold a process per open question; parking holds
  nothing.
