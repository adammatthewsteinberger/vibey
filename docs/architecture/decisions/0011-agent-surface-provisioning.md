# 0011 — One source of truth, materialized into every engine's guidance files

**Status:** accepted · **Date:** 2026-08-14

## Context

Each engine reads different guidance files:

| Engine | Reads |
|---|---|
| Claude Code / `claudeloop` | `CLAUDE.md`, `.claude/skills/`, `.claude/settings.json` |
| Codex / `codexloop` | `AGENTS.md`, `.agents/skills/` |
| Cursor / `cursorloop` | `CURSOR.md`, `.cursor/rules/` |
| Antigravity / `agyloop` | `GEMINI.md`, `.agent/` |

If these disagree, rotating engines silently changes the project's rules mid-build:
item 3 is written to one style guide and item 4 to another, and the diff review
blames the code rather than the configuration. The `*loop` repos already maintain
all four surfaces by hand and treat drift between them as a bug — vibey should not
recreate that maintenance burden per project.

## Decision

**Vibey materializes all four surfaces from one source, into each worktree, at job
start.**

Source of truth: `vibey.toml` (`[provision] plugins = [...]`) plus the project's
own accepted spec. Output, per worktree:

```
CLAUDE.md   AGENTS.md   CURSOR.md   GEMINI.md      ← generated, each a router
.claude/skills/  .agents/skills/  .cursor/rules/   ← same skills, native format
.vibey/context/
├── spec.md         acceptance.md    nfr.md
├── decisions.md    open-items.md
└── handoff/brief.md  handoff/ledger.jsonl
```

The four root files are thin routers. They state the same non-negotiables and
point at `.vibey/context/` for everything that changes. Skills are pulled by name
from the local `vibe-engineering-skills` marketplace, so
`plugins = ["software-architecture", "quality-engineering", "security-first-dev"]`
gives every engine the same practitioner vocabulary.

Provisioning is **idempotent and content-addressed**: a job that finds the correct
digests already present writes nothing.

## Rationale

This is the "automated repository for IDEs" requirement, and it is what makes
round-robin rotation produce coherent code rather than four dialects. It also
closes a real correctness gap: an engine that has never seen the project's
architecture rules will violate them confidently, and the violation surfaces as a
review finding three hours later.

Generating rather than hand-maintaining means a change to the project's rules
propagates to all four surfaces in one edit — the same reason the `*loop` repos
mirror their skills in a single PR.

## Consequences

**Good.** Every engine starts from identical guidance. Adding a fifth engine is a
new emitter, not a new documentation burden. The marketplace's 71 skills become
project vocabulary by naming a plugin.

**Bad.** Generated files in the repo. Vibey writes them **inside the worktree**,
and adds them to `.git/info/exclude` for that worktree rather than to the project's
`.gitignore`, so a project that maintains its own `CLAUDE.md` is not clobbered and
generated content never lands in a commit.

**Bad.** A project may already have hand-written guidance. Vibey's emitter merges
rather than overwrites: existing content is preserved, and vibey's section is
delimited by markers so re-provisioning updates only its own block.
