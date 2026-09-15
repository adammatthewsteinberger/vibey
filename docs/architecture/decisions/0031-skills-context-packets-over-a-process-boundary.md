# 0031 — Skills context is a packet compiled over a process boundary, shadow before inject

**Status:** accepted · **Date:** 2026-08-22 (PR #82; recorded 2026-09-15) · **Extends:** ADR-0011, ADR-0017

## Context

Runbook 19 asked that every AI request a run issues go out with the current skills loaded and that the session record which version was in play. `vibey-skills` already ships a deterministic context engine that, given a request, returns a bounded Markdown packet plus a manifest. The open questions were where the boundary sits, how a packet reaches a prompt, and how to find out whether it helps before it changes what engines see.

## Decision

**`VibeySkillsContextCompiler` asks the independently versioned `vibey-skills` CLI for one packet per implement job, over a subprocess, and the BUILD implement handler uses it in one of three modes.**

- **Process boundary.** `python -m vibey_skills.cli index` (once, under a lock) and `... packet --request --index --budget --output`. The conductor never imports `vibey_skills`; the packet's shape is the CLI's JSON contract and the provenance names the version that produced it.
- **Everything lands in the worktree**: `.vibey/context/skills/<job>.request.json`, `.packet.md`, `.packet.json`. The receiving engine, and a human, can read exactly what was compiled.
- **Three modes, chosen per project at `vibey new`** (`--skills-context-mode off|shadow|inject`, `--skills-context-budget` 1,000–32,000, default 6,000) and stored in the project's own config — there is no static `[skills_context]` table in `vibey.toml`. **Shadow** compiles the packet and records it as a ledger artifact without touching the prompt; **inject** appends it to the implement prompt when the compile reported `ok`. Shadow exists so the packet can be measured against real runs before it is allowed to steer one.
- **Only when the prompt is ours.** A job carrying an explicit seed prompt (a handoff brief, a repair instruction) is not augmented; the brief is already the context.
- **The result never carries the raw task text**, so a packet artifact in the ledger cannot become a second copy of a secret-bearing prompt.
- **`skills` is an extra**, resolved from the workspace since ADR-0021; the earlier git pin is what broke publishing outright (PyPI's "400 Can't have direct dependency").

## Consequences

**Good.** Skills content reaches BUILD sessions with a recorded version and budget, off by default, observable before it is influential. The packet is reproducible from the request file.

**Bad.** One more subprocess per implement job (bounded by a 120s timeout); the index is rebuilt per worktree; and the conductor consumes a family package as a CLI rather than as code — ADR-0017 would prefer the import, and this ADR records the seam deliberately: the CLI is `vibey-skills`' stable contract and the packet, not the engine, is what the ledger needs. Revisit when `vibey_skills` publishes a library API with the same provenance.

**Rule status.** Mechanism; does not pass ADR-0020's test.

## Alternatives rejected

- **Import `vibey_skills` and call the engine in-process.** Couples the conductor's release to the marketplace's internals and loses the CLI's versioned contract; kept as the future direction if the library API stabilises.
- **A static `[skills_context]` table in `vibey.toml`.** The mode is a per-project experiment setting decided at creation; a global default would flip inject on for projects that never measured shadow.
- **Inject only, no shadow.** No way to know whether the packet helps or harms before it changes engine behaviour.
- **Provision skills as files via ADR-0011's agent-surface emitter instead.** Solves a different problem (routers per IDE); the packet is task-scoped and budgeted, the surface is static.
