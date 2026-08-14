# 0004 — Handoffs are gated by a deterministic no-loss predicate

**Status:** accepted · **Date:** 2026-08-14

## Context

The requirement is that passing a conversation between AIs must not lose data. The
natural implementation — ask the outgoing model for a summary and seed the next
one with it — loses constraints, unanswered questions, stated assumptions, and
deferred findings, and it loses them **silently**. Nothing in that code path can
report a drop.

## Decision

**A handoff is not accepted until a pure, deterministic predicate over
`(ledger_range, brief)` returns no violations.** The gate is
`domain/noloss.py::verify()`: stdlib only, no I/O, **no model call**, ten rules,
matching on ids rather than on text.

On failure: regenerate the brief with the specific violations fed back (≤3
attempts) → escalate to `FULL_TRANSCRIPT` mode, inlining the entire range → raise
a human gate. It never proceeds on a failed gate.

## Rationale

Two design choices make this work, and both are load-bearing:

**1. Ids are minted by vibey, not by the agent.** Every closable thing — an open
question, a recorded decision, a stated assumption, an unresolved finding — gets an
id at append time, assigned by infrastructure. The agent cannot forget to
identify one, because it never had the opportunity. Matching is then set
difference over ids, which is exact. Text-similarity matching would let a
paraphrase hide an omission, which is precisely the failure mode being prevented.

**2. The gate is not an LLM.** A gate implemented as "ask a model whether this
summary lost anything" has exactly the failure mode it is meant to catch, and it
fails in a correlated way with the model that wrote the summary. A set-difference
over ids cannot be talked out of a violation.

The floor case proves the design is sound: vibey can always generate a brief
**deterministically from the projections the gate checks**, which passes by
construction. So "every engine is unavailable to write a brief" degrades fluency,
never fidelity.

## The rules

R1 remaining work · R2 open questions · R3 decisions · R4 assumptions ·
R5 open findings · R6 range integrity (digest + `to_seq == max(seq)` + count) ·
R7 referenced artifacts · R8 budget carry · R9 hard constraints from the spec ·
R10 containment (a brief may not grant tools, change permissions, or mutate
acceptance criteria).

R1–R9 are closure rules. R10 is the security control: a brief is *data for the
next engine*, never authority over the project. A compromised or hallucinated
brief can waste a turn; it cannot redirect the work.

## Consequences

**Good.** "Lossless" is a check that can fail, with a named item, not an
aspiration. Gate outcomes are stored per attempt, so quality is measurable:
"which rule fires most, for which engine pair, in which phase" is a query.

**Bad.** Handoffs cost more — up to three brief generations, and occasionally a
full-transcript inline that is expensive in tokens. Vibey pays it rather than
proceed on a failed gate.

**Bad.** The gate is only as good as the id minting. If a closable thing is never
recorded as an event, the gate cannot check it. This is the residual risk, and it
is why extraction (ADR-0003) matters as much as the gate itself.

## Alternatives rejected

- **Trust the summary.** The status quo. Fails silently, which is the worst
  property a data-integrity mechanism can have.
- **Always send the full transcript.** Correct but wasteful, and it hits context
  limits on long projects, at which point it silently truncates — reintroducing
  the same failure with extra steps.
- **LLM-as-judge gate.** Correlated failure with the summarizer; non-deterministic;
  untestable by property.
