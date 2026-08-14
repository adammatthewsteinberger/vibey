# 0003 — An event-sourced ledger is the conversation's source of truth

**Status:** accepted · **Date:** 2026-08-14

## Context

Rotating engines means engine B must continue what engine A was doing. The
"conversation" currently lives in vendor-specific artifacts: a Claude Code
`~/.claude/projects/**/*.jsonl` transcript, a Codex rollout, a Cursor bridge log.
None of them is readable by the others.

## Decision

**The source of truth is an append-only event log in a vendor-neutral schema,
stored in Postgres.** Vendor transcripts are copied in as *attachments* referenced
by events — evidence, not state. Every derived view (the handoff brief, the
decision log, the open-items list, the cost report) is a **projection** that can be
rebuilt by replaying the log.

## Rationale

This follows the published result for exactly this problem
([ESAA-Conversational](https://arxiv.org/pdf/2606.23752)): replaying a logical
event log reconstructs consistent state in a receiving agent even when the two
agents' internal representations differ, whereas passing summarized context
strings does not.

Three properties fall out that vibey needs:

1. **Any engine can be the receiver.** The log has no vendor shape.
2. **Nothing is lost by construction.** Corrections are new events that supersede
   old ones; nothing is overwritten, so "what did we decide in cycle 1" is always
   answerable in cycle 4.
3. **The no-loss gate becomes possible.** A deterministic check over a log is
   feasible ([ADR-0004](0004-no-loss-gate-on-handoff.md)); a deterministic check
   over a chat transcript is not.

## Consequences

**Good.** Handoff is verifiable. Audit is free. Projections can be added later
without migration — just replay. Debugging a bad build is reading a log, not
guessing.

**Bad.** Every meaningful agent output must be *translated* into events. Engines
that cannot emit structured output need an extraction step, which costs a cheap
model call per turn. The log grows without bound.

**Mitigation.** Extraction runs at `TRIVIAL` effort — the cheapest tier available.
`event` is partitioned by `(project_id, cycle)` past ~500k rows, and
`vibey ledger archive` compresses old cycles. Nothing is ever deleted.

## Implementation notes

- `seq` is **gapless per project**, allocated in the same transaction as the
  insert. Gaplessness is what makes "the range `[1200, 1478]`" an exact,
  verifiable set — rule R6 of the gate depends on it.
- `UPDATE` and `DELETE` on `event` are `DO INSTEAD NOTHING` rules. Append-only is
  enforced by the database, not by discipline.
- Redaction runs on write, not read: a secret must never reach the column.
- `provenance` (`trusted` / `agent` / `untrusted`) travels with every event, so
  content fetched from the web is marked as data rather than instruction all the
  way through to the receiving engine's seed prompt.
