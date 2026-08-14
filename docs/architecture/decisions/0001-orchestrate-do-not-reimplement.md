# 0001 — Orchestrate the `*loop` runners; do not reimplement them

**Status:** accepted · **Date:** 2026-08-14

## Context

Four autonomous session runners already exist and are mature in the one dimension
that is hardest to get right: `claudeloop`, `codexloop`, `cursorloop`, and
`agyloop` each classify a provider rejection into *waitable rate-limit window* vs
*exhausted credits that only a human can fix*, never block on a human, write
savepoints, and expose a mid-run control plane over a documented run directory.

Vibey needs an autonomous build phase. The obvious options are to build a fifth
runner that talks to all four providers directly, or to drive the four existing
ones.

## Decision

**Vibey drives the existing runners as subprocesses through a uniform
`EngineAdapter`.** It never calls a provider API for build work. Each runner is an
*engine*: vibey builds its argv from a descriptor, spawns it, tails its
`events.jsonl`, writes its `inbox/`, and reads its snapshots.

## Consequences

**Good.** The hardest, most vendor-specific logic — capacity classification,
wait policy, never-blocking, session resumption — is inherited rather than
rewritten four times. Each runner keeps improving independently. A fifth vendor is
a new descriptor plus an adapter, not a new provider integration.

**Bad.** Vibey depends on four pre-1.0 projects that will drift. Their CLI
surfaces already diverge (different effort vocabularies, different session verbs,
different sandbox flags — see
[rotation-and-engines.md §1](../../plans/rotation-and-engines.md#1-the-verified-divergence)).

**Mitigation, and it is the load-bearing part of this decision:** an executable
**conformance suite**. Every descriptor claim — flags, state directory, run-dir
shape, snapshot schema, capacity mapping, done marker, control-plane behavior — is
asserted against the installed binary by `vibey doctor --conformance`. A failing
check marks that engine **ineligible for rotation**, not fatal. Vibey degrades to
three engines rather than crashing mid-cycle.

## Alternatives rejected

- **A fifth unified runner.** Would duplicate the credits-vs-window logic four
  times, and every provider change would be vibey's problem. The `*loop` family
  exists precisely because that logic is subtle enough to deserve its own project.
- **Import the runners as libraries.** Their public surface is a CLI; their Python
  internals are explicitly not a stable API, and importing four packages with
  conflicting vendor SDK dependencies into one process is a dependency-resolution
  problem with no good answer.
- **A hosted LLM gateway (LiteLLM/OpenRouter) instead of the runners.** A gateway
  routes *model calls*. It does not run an agentic coding session, manage a
  workspace, or resume across a five-hour rate-limit window. Wrong altitude.
