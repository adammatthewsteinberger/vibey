# Runbook: agent-surface sync — one customization set, every IDE and bot

## Goal

Every installed agent platform on the operator's machine — Claude Code,
Cursor, Codex CLI, Antigravity/Gemini, and whatever comes next — carries
the **same set of customizations at any given point in time**: skills,
rules, MCP servers, plugins, marketplaces, subagents/custom agents, and
top-level instruction files (CLAUDE.md / GEMINI.md / AGENTS.md and kin).

Two managed halves:

1. **Initial sync**: inventory every installed platform's customizations,
   reconcile them into one canonical store, and project the union back so
   every platform starts from the same complete set.
2. **Maintenance loop**: a recurring job that keeps them converged
   forever after — a change made *anywhere* (a rule edited in Cursor, an
   MCP server added in Claude Code, a skill deleted in Codex) is picked
   up on the next run and propagated everywhere else. Additions, updates,
   and deletions all flow.

And one front door: the whole set is manageable from vibey —
`vibey surface add|update|delete|list|diff|sync` — so the operator can
drive it centrally *or* keep editing inside their IDEs and let the loop
reconcile.

## Current state (verified)

- vibey already enforces a repo-level version of this idea by convention:
  `.claude/skills/`, `.cursor/rules/`, `.agents/skills/`, `.agent/rules/`
  must be updated in the same PR (CLAUDE.md's agent-surface maintenance
  rule). This workstream generalizes it to the **machine level** (user
  scope), makes it **mechanical instead of conventional**, and covers
  kinds the repo rule doesn't (MCP servers, plugins, marketplaces).
- The docwatch runbook (04) already designs the digest-manifest pattern
  (content hash per item, append-only snapshots) this loop reuses.
- Nothing in vibey today reads or writes user-scope platform config.

## Design

### The canonical store

A git repository (default `~/.vibey/surface-store`, operator-overridable)
is the source of truth. Every customization is one canonical item:

```
store/
  skills/<name>/           # SKILL.md + assets (AgentSkills-spec shape)
  rules/<name>.md          # plain instruction rules
  agents/<name>.md         # subagent/custom-agent definitions
  mcp/<name>.json          # canonical MCP server def (command/url, env refs, scopes)
  plugins/<name>.json      # plugin identity + source (marketplace, version policy)
  marketplaces/<name>.json
  instructions/<name>.md   # CLAUDE.md/GEMINI.md-class top-level files
  manifest.json            # per-item content hash × per-platform projection state + tombstones
```

Git gives history, rollback, and (later) multi-machine sync for free —
push the store to a private remote and a second machine converges too.

### Platform adapters (the projection seam)

One `SurfaceAdapter` Protocol per platform, in `infrastructure/surface/`:
`inventory() -> [Item]`, `project(item) -> None`, `remove(item_ref)`,
each adapter owning the native locations and formats:

| Platform | Where its customizations live (adapter's territory) |
|---|---|
| Claude Code | `~/.claude/skills/`, `~/.claude/agents/`, `~/.claude/CLAUDE.md`, MCP via `claude mcp` / `~/.claude.json`, plugins + marketplaces via `claude plugin` |
| Cursor | `~/.cursor/rules/` (user rules), Cursor MCP config, extensions/marketplace entries it exposes on disk |
| Codex CLI | `~/.codex/config.toml` (MCP, instructions), `~/.codex/skills/` where supported, `AGENTS.md`-class files |
| Antigravity | `~/.gemini/`-class config, `GEMINI.md`, `.agent/rules/` user scope, its MCP registration |

Format translation is the adapter's job: a canonical skill projects to a
Cursor `.mdc` rule, a canonical MCP def projects into each tool's own
config schema, canonical instructions project to the platform's file name.
An adapter reports what kinds it supports; unsupported kinds are recorded
as `not_projectable` in the manifest, never silently dropped. Discovery
probes (`which claude`, config-dir existence) decide which adapters are
active on this machine — platforms come and go without config edits.

### Sync semantics (the part that must be right)

- Three states per item per platform in the manifest: canonical hash,
  last-projected hash, last-inventoried hash. That triangle classifies
  every situation: new-in-platform (adopt into store → propagate),
  changed-in-platform (update store → propagate), deleted-in-platform
  (tombstone → delete everywhere), changed-in-store (project out),
  diverged-in-two-platforms-since-last-sync (**conflict**).
- **Conflicts never auto-resolve.** A conflict parks a vibey human gate
  showing both diffs, with the answer contract picking a winner
  (`--raw '{"winner": "cursor"}'`) or keeping both under new names. The
  no-silent-partial principle from the handoff gate applies verbatim.
- **Deletes need tombstones**: "absent on platform A" is only a delete if
  the manifest says A previously had it; tombstones stop resurrection
  ping-pong between sync runs. Tombstones expire after a configurable
  horizon (default 90 days).
- **Trust boundary**: MCP servers, plugins, and marketplaces are
  executable. First-seen items adopted *from* a platform are recorded
  with provenance (which platform, when, content hash) and — by default —
  propagate immediately per the operator's autosync intent, but a
  `surface.trust: gate_new_executables` config flips first-seen
  MCP/plugin adoption to a human gate. Secrets in MCP env blocks are
  stored as env-var *references*, never values; the store must stay free
  of credentials so it can be pushed to a remote.

### The two halves

1. **`vibey surface init`** — the initial sync: run every adapter's
   inventory, build the union, park conflict gates where platforms
   disagree, write the canonical store + manifest, project the union back
   out. Idempotent; a dry-run mode (`--plan`) prints the full
   add/update/delete matrix per platform before anything is written.
2. **`surface.sync` job** — the maintenance loop: a serial vibey job kind
   scheduled on the worker heartbeat (default every 15 minutes; also
   runnable on demand via `vibey surface sync`). Each run: inventory →
   classify against manifest → propagate → commit the store (one
   conventional commit per run, `chore(surface): sync — 2 adds, 1 update,
   1 delete from cursor`) → update manifest. The job is idempotent under
   replay like every vibey job; a crashed run replays cleanly because
   classification derives from the manifest triangle, not from memory.

### CLI (the central front door)

```
vibey surface init [--plan]              # initial sync
vibey surface sync [--plan]              # run the loop once, now
vibey surface status                     # per-platform convergence table
vibey surface diff <item>                # canonical vs each platform
vibey surface list [--kind mcp|skill|…]
vibey surface add <kind> <name> [--from-file|--from-platform cursor|--json …]
vibey surface update <kind> <name> …
vibey surface delete <kind> <name>       # tombstones + removes everywhere
```

`add`/`update`/`delete` write the canonical store and project immediately
— no waiting for the next loop tick.

## Work items (vibey decomposition seed)

1. Canonical store + manifest model (domain: pure classification of the
   hash triangle into add/update/delete/conflict — this is the testable
   heart) + git-backed store adapter.
2. `SurfaceAdapter` Protocol + in-memory fake + port-parity tests.
3. Claude Code adapter (richest surface first: skills, agents, CLAUDE.md,
   MCP, plugins/marketplaces via the `claude` CLI).
4. Cursor adapter (rules `.mdc` translation, MCP config).
5. Codex adapter (config.toml round-trip without clobbering unrelated
   keys — TOML-preserving edits).
6. Antigravity adapter.
7. `surface.sync` job kind + scheduling + conflict human gates with the
   `--raw '{"winner": …}'` contract.
8. CLI verb set + `--plan` dry-run rendering.
9. Trust config (`gate_new_executables`) + secrets-as-references
   enforcement (a store scan that fails on anything credential-shaped —
   reuse the redaction patterns).
10. Live validation on this machine: seed a skill from vibey, watch it
    appear in all four platforms; edit a rule in Cursor, watch the loop
    adopt + propagate it; delete an MCP server via the CLI, watch it
    vanish everywhere; force a two-platform conflict and answer the gate.

## Verification

Fixture gates green (100% floors as ever); the pure classifier
property-tested (no hash triangle maps to silence — every state has
exactly one classification). Live: the four scenarios in item 10 executed
on this machine and transcribed into an evidence file, plus a
kill-mid-sync replay proving idempotency, and `vibey surface status`
showing full convergence at the end.

## Needs from operator

Nothing to start (all four platforms are installed here). A private git
remote for the store if multi-machine sync is wanted later.

## Risks

- Native formats drift (Cursor's rule format, `claude` CLI surfaces) —
  adapters are behind a Protocol, and docwatch (04) watches these
  platforms' docs already.
- Clobbering hand-edited platform config: adapters do surgical,
  key-scoped edits (TOML/JSON preserving), never whole-file rewrites of
  shared config files; every projection is preceded by a manifest check
  that the platform copy matches last-projected state (else it's a
  change to adopt, not overwrite).
- Sync loops fighting the user mid-edit: the loop only adopts a change
  when the file has been stable for one full interval (mtime debounce).
- Executable trust spread is the real hazard — provenance recording is
  mandatory, the gate flag exists, and the store's git history is the
  audit log.
