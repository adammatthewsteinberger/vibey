# 0003 — An event-sourced ledger is the conversation's source of truth

**Status:** accepted · **Date:** 2026-08-14

**Owes:** a sub-doctrine (not yet proposed) — the ledger is append-only: corrections supersede, nothing is ever updated or deleted (nearest parent: doctrine 7, beside 7.a).

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
that cannot emit structured output need an extraction step. The log grows without
bound.

**Mitigation.** Extraction is deterministic today, with no model call per turn.
Engines with a structured verdict are parsed directly
(`application/verdict_extraction.py`, which mints the ids and deduplicates against
open items); engines without one go through `application/text_verdict_fallback.py`,
a line-prefix heuristic (`Question:`, `Decision:`, `Assumption:`, …) that stands in
for the cheap `TRIVIAL`-effort extraction call the design calls for and is the seam
that call would replace. Partitioning `event` by `(project_id, cycle)` and a
`vibey ledger archive` command are planned for when a project's ledger passes
~500k rows; neither exists yet (`vibey ledger` has only `show`). Nothing is ever
deleted.

## Implementation notes

- `seq` is **gapless per project**, allocated in the same transaction as the
  insert. Gaplessness is what makes "the range `[1200, 1478]`" an exact,
  verifiable set — rule R6 of the gate depends on it.
- `UPDATE` and `DELETE` on `event` are `DO INSTEAD NOTHING` rules
  (`migrations/0002_event.sql`). Append-only is enforced by the database, not by
  discipline.
- `seq` comes from the `event_seq` counter row, incremented by an upsert inside
  `append_event()`, the same function that inserts the event; the row lock on the
  counter serializes writers per project, and `UNIQUE (project_id, seq)` backs it.
- Redaction runs on write, not read: a secret must never reach the column.
- `provenance` (`trusted` / `agent` / `untrusted`) travels with every event, so
  content fetched from the web is marked as data rather than instruction all the
  way through to the receiving engine's seed prompt.

## Alternatives rejected

- **Vendor transcripts as the source of truth.** Each is readable only by its own
  vendor's tooling, and no deterministic gate can be written over a chat
  transcript.
- **A mutable state table with a history column.** Once a row is updated, "what did
  we decide in cycle 1" depends on the history being kept correctly by every
  writer. Append-only makes a correction a first-class event instead.
- **Summaries as state.** The ESAA-Conversational result above: summarized context
  strings do not reconstruct consistent state in the receiver.
