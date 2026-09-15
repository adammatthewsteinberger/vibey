# 0001 — Orchestrate the `*loop` runners; do not reimplement them

**Status:** accepted · **Date:** 2026-08-14

**Owes:** a sub-doctrine (not yet proposed) — vibey drives its runners and never calls a provider API for build work (nearest ratified neighbour: 10.e, *the family first*).

## Context

Four autonomous session runners already existed when this was decided, and they are
mature in the one dimension that is hardest to get right: `claudeloop`, `codexloop`,
`cursorloop`, and `agyloop` each classify a provider rejection into *waitable rate-limit window* vs
*exhausted credits that only a human can fix*, never block on a human, write
savepoints, and expose a mid-run control plane over a documented run directory. A fifth, the
local-model `qwenloop`, has since joined as an opt-in engine
([ADR-0015](0015-qwenloop-standby.md)).

Vibey needs an autonomous build phase. The obvious options are to build a fifth
runner that talks to all four providers directly, or to drive the four existing
ones.

## Decision

**Vibey drives the existing runners as subprocesses through a uniform
`EngineAdapter`.** It never calls a provider API for build work. Each runner is an
*engine*: vibey builds its argv from a descriptor, spawns it, tails its
`events.jsonl`, writes its `inbox/`, and reads its snapshots.

This still holds after the runners moved into this repository. They are uv
workspace members under `src/vibey_runners/{claude,codex,cursor,agy,qwen,common}`
([ADR-0021](0021-one-tree-history-preserved.md)), each keeping its own gates
([ADR-0022](0022-absorbed-packages-keep-their-own-gates.md)) and its own PyPI
project, and `src/vibey` imports none of them: the conductor reaches every runner
only as a subprocess, through its descriptor.

## Consequences

**Good.** The hardest, most vendor-specific logic — capacity classification,
wait policy, never-blocking, session resumption — is inherited rather than
rewritten per vendor. Each runner keeps improving independently. A fifth engine is
a new descriptor plus an adapter, not a new provider integration — which is how
`qwenloop` was added (`infrastructure/engines/descriptors.py::QWENLOOP`).

**Bad.** Vibey depends on five pre-1.0 runners that drift independently, even now
that they live in this monorepo and version separately on PyPI. Their CLI
surfaces already diverge (different effort vocabularies, different session verbs,
different sandbox flags — see
[rotation-and-engines.md §1](../../plans/rotation-and-engines.md#1-the-verified-divergence)).

**Mitigation, and it is the load-bearing part of this decision:** an executable
**conformance suite** (`application/conformance.py`). Every descriptor claim —
binary and minimum version, flags, state directory, run-dir shape, snapshot schema,
capacity mapping, done marker, control-plane behavior, structured verdict (nine
checks) — is asserted against the installed binary by `vibey doctor --conformance`
(`--record` persists the result to `engine_health`). A failing check sets
`conformance_ok = false`, which `domain/rotation.py::eligible()` treats as
**ineligible for rotation**, not fatal. Vibey degrades to the remaining engines
rather than crashing mid-cycle. The suite has already paid for itself: its `flags`
check found that codexloop's original `--effort` projection and every non-agyloop
isolation flag were fabricated (see the note at the top of `descriptors.py`).

## Alternatives rejected

- **A single unified runner.** Would duplicate the credits-vs-window logic per
  vendor, and every provider change would be vibey's problem. The `*loop` family
  exists precisely because that logic is subtle enough to deserve its own project.
- **Import the runners as libraries.** Their public surface is a CLI; their Python
  internals are explicitly not a stable API, and importing four packages with
  conflicting vendor SDK dependencies into one process is a dependency-resolution
  problem with no good answer. Absorbing the runners into one uv workspace
  (ADR-0021) did not change this: they resolve in one workspace now, but the conductor
  still talks to their CLIs, not their internals.
- **A hosted LLM gateway (LiteLLM/OpenRouter) instead of the runners.** A gateway
  routes *model calls*. It does not run an agentic coding session, manage a
  workspace, or resume across a five-hour rate-limit window. Wrong altitude.
