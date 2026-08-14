# 0008 — Git worktree per work item; containers for real isolation

**Status:** accepted · **Date:** 2026-08-14

## Context

Phase 2 builds several work items in parallel, each driven by a different engine.
Two agents editing the same checkout corrupt each other: one rewrites a file
mid-edit, tests fail for unrelated reasons, and the failure is attributed to the
wrong item.

## Decision

**Every `build.implement` job gets its own git worktree and branch.** Integration
happens on a dedicated integration worktree.

```
.vibey/worktrees/
├── c1-item-001/     branch vibey/c1/item-001
├── c1-item-004/     branch vibey/c1/item-004
└── c1-integration/  branch vibey/c1/integration
```

**Additionally**, three isolation levels are selectable per project:

| Level | Mechanism | Protects against |
|---|---|---|
| `worktree` (default) | git worktree + engine destructive-command denies | concurrent-edit corruption |
| `container` | Docker/Podman, repo bind-mounted, egress allow-listed | filesystem escape, exfiltration |
| `vm` | Firecracker / Lima microVM | kernel-level escape |

## Rationale

Worktrees remove the shared mutable resource rather than trying to lock it, which
is the standard answer to a standard concurrency problem. This became the
convergent industry pattern during 2026 — multiple agent CLIs shipped
one-worktree-per-write-capable-agent within the same period.

**A worktree is not a sandbox**, and this is worth stating loudly because the
convenience of worktrees invites the confusion. A worktree stops agent A from
overwriting agent B's file. It does nothing to stop either from running `rm -rf ~`,
reading `~/.ssh`, or POSTing the repository somewhere. For unattended overnight
runs — which is vibey's whole premise — that gap matters.

Hence `container` as the recommended level for autonomous operation, with an
egress allow-list restricted to the provider API hosts the engines need.
`vibey doctor` warns when it sees `isolation = "worktree"` together with an
unattended Phase 2.

## Consequences

**Good.** Parallel builds are conflict-free by construction. Conflicts surface at
integration, where they can be reasoned about, rather than as mysterious mid-build
corruption. Each worktree is independently savepoint-able and unwind-able.

**Bad.** Disk cost — N checkouts of the repo. Some toolchains (node_modules,
virtualenvs, build caches) are expensive to rebuild per worktree.

**Mitigation.** Worktrees are reclaimed on item completion. A per-project
`bootstrap` hook in `vibey.toml` can hard-link or share caches across worktrees.
`vibey gc` cleans orphans left by killed workers, and the worktree manager is
crash-safe: `SIGKILL` mid-create leaves no orphan.

**Bad.** `container` mode adds a Docker dependency and slows iteration.
Accepted: it is opt-in, and the default stays `worktree` for supervised work.
