# 0011 — One source of truth, materialized into every engine's guidance files

**Status:** accepted · **Date:** 2026-08-14 · **Extended by:** ADR-0031

**Owes:** a sub-doctrine (not yet proposed) — agent guidance has one source of truth, materialized for every engine and changed for all of them in the same change (nearest parent: doctrine 9, beside 9.a).

## Context

Each engine reads different guidance files:

| Engine | Reads |
|---|---|
| Claude Code / `claudeloop` | `CLAUDE.md`, `.claude/skills/`, `.claude/settings.json` |
| Codex / `codexloop` | `AGENTS.md`, `.agents/skills/` |
| Cursor / `cursorloop` | `CURSOR.md`, `.cursor/rules/` |
| Antigravity / `agyloop` | `GEMINI.md`, `.agent/` |
| Local Qwen / `qwenloop` | `QWEN.md`, `.agents/skills/` |

If these disagree, rotating engines silently changes the project's rules mid-build:
item 3 is written to one style guide and item 4 to another, and the diff review
blames the code rather than the configuration. The `*loop` runners — now in this
repository under `src/vibey_runners/` — maintain their own surfaces by hand and
treat drift between them as a bug; vibey should not recreate that maintenance
burden per project.

## Decision

**Vibey materializes every engine's router file from one source, into each BUILD
worktree, at the start of every `build.implement` job.**

Source of truth: `vibey.toml` (`[provision] plugins = [...]`) plus the project's
own accepted spec. Output:

```
project repo:
.vibey/context/                                       ← written when the design spec is accepted
├── spec.md  acceptance.md  nfr.md
└── decisions.md  open-items.md

each BUILD worktree:
CLAUDE.md  AGENTS.md  CURSOR.md  GEMINI.md  QWEN.md   ← generated routers
.vibey/context/skills/<job_id>.packet.md (+ .json)    ← only with skills_context (ADR-0031)
.vibey/handoff/ledger.jsonl                           ← full BUILD ledger, on wind-down
```

The five root files (`domain/provision.py::RouterFile`) are thin routers. They
carry the same marker-delimited block — the non-negotiables, the skill plugins, and
a pointer to `.vibey/context/` for everything that changes. The accepted-spec files are
written to the project repository's `.vibey/context/`, which is git-excluded, and
nothing copies them into a worktree yet, so from inside a worktree that pointer
currently resolves only to the skills packets. The handoff brief is not
a file: it is rendered into the incoming engine's seed prompt
(`application/seed_prompt.py`), and the full ledger beside it is written only on a
wind-down ([ADR-0007](0007-rotate-at-boundaries.md)).

Skills are not copied into the worktree. The in-tree `vibey-skills` marketplace
(`src/vibey_tools/skills`, formerly `vibe-engineering-skills`) is reached as a
separate process: when a project enables `skills_context` at `vibey new`, it
compiles a bounded packet per implement job and, in `inject` mode, appends it to the
engine's prompt ([ADR-0031](0031-skills-context-packets-over-a-process-boundary.md)).

`[provision] plugins` is parsed from `vibey.toml`, but the composition root does not
yet pass it (or any non-negotiables) to the provisioner, so generated routers
currently say `None` and `none` in those two places.

Provisioning is **idempotent and content-addressed**: a job that finds the correct
digests already present writes nothing.

## Rationale

This is the "automated repository for IDEs" requirement, and it is what makes
round-robin rotation produce coherent code rather than a dialect per engine. It also
closes a real correctness gap: an engine that has never seen the project's
architecture rules will violate them confidently, and the violation surfaces as a
review finding three hours later.

Generating rather than hand-maintaining means a change to the project's rules
propagates to every surface in one edit — the same reason this repository updates
its Claude, Cursor, Codex, and Antigravity skill trees in a single PR.

## Consequences

**Good.** Every engine starts from identical guidance. Adding qwenloop was one new
`RouterFile` member, not a new documentation burden. The marketplace's 644 skills
(127 plugins) become project vocabulary through a bounded packet rather than a copy.

**Bad.** Generated files in the repo. Vibey writes them **inside the worktree**,
and adds them to the repository's shared `.git/info/exclude` (the git common
directory every worktree reads) rather than to the project's `.gitignore`, so a project that maintains its own `CLAUDE.md` is not clobbered and
generated content never lands in a commit.

**Bad.** A project may already have hand-written guidance. Vibey's emitter merges
rather than overwrites: existing content is preserved, and vibey's section is
delimited by markers (`<!-- vibey:begin -->` … `<!-- vibey:end -->`) so
re-provisioning updates only its own block.

## Alternatives rejected

- **Hand-maintain each engine's file.** The drift the runners already fight: item 3
  and item 4 get built to different rules.
- **One file, symlinked per engine.** Engines read different filenames and different
  skill formats; a symlink cannot translate between them.
- **Copy the whole marketplace into every worktree.** Hundreds of skills per
  checkout, most irrelevant to the item; a bounded packet chosen per job is the
  point.
