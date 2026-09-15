# 0008 — Git worktree per work item; containers for real isolation

**Status:** accepted · **Date:** 2026-08-14

**Owes:** nothing — mechanism (ADR-0020)

## Context

Phase 2 builds several work items in parallel, each driven by a different engine.
Two agents editing the same checkout corrupt each other: one rewrites a file
mid-edit, tests fail for unrelated reasons, and the failure is attributed to the
wrong item.

## Decision

**Every `build.implement` job gets its own git worktree and branch.** Integration
happens on a dedicated integration worktree.

```
.vibey/worktrees/1/
├── item-001/      branch vibey/1/item-001
├── item-004/      branch vibey/1/item-004
└── integration/   branch vibey/1/integration
```

Naming lives in `domain/worktree.py` (`.vibey/worktrees/<cycle>/<item_id>`, branch
`vibey/<cycle>/<item_id>`); the integration worktree is the reserved item id
`integration` (`infrastructure/git/integration_branch.py`). Item branches are cut
from the cycle's integration branch once it exists, so later items stack on
already-integrated code. `build.integrate` merges into it one job at a time under a
Postgres advisory lock ([ADR-0029](0029-integrate-serialized-by-advisory-lock.md)).

**Additionally**, three isolation levels are designed, selectable per project as
`[isolation] level` in `vibey.toml`:

| Level | Mechanism | Protects against | Status |
|---|---|---|---|
| `worktree` (default) | git worktree + engine destructive-command denies | concurrent-edit corruption | implemented |
| `container` | Docker/Podman, worktree mounted, hardened defaults (`infrastructure/container/`: no network, read-only root, all capabilities dropped, `no-new-privileges`) | filesystem escape, exfiltration | executor implemented, **not wired into dispatch** |
| `vm` | Firecracker / Lima microVM | kernel-level escape | **designed, not implemented** |

The config parser accepts all three levels and an `egress` list, but every dispatch
path today builds its `RunSpec` with `IsolationLevel.WORKTREE`. A level only selects
per-descriptor argv flags, and those are empty for every engine except agyloop's
`--safe`; the conformance suite found the other engines' isolation flags had been
invented and removed them. `OciContainerExecutor` is not referenced by the
composition root or any handler.

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

Hence `container` as the recommended level for autonomous operation, with egress
restricted to the provider API hosts the engines need. That is the target, not the
present: the container executor's default is no network at all, an allow-list is
not implemented, and a `vibey doctor` warning for `level = "worktree"` on an
unattended Phase 2 is planned but does not exist. Until container dispatch lands,
unattended runs have worktree isolation plus whatever the runners themselves deny.

## Consequences

**Good.** Parallel builds are conflict-free by construction. Conflicts surface at
integration, where they can be reasoned about, rather than as mysterious mid-build
corruption. Each worktree is independently savepoint-able and unwind-able.

**Bad.** Disk cost — N checkouts of the repo. Some toolchains (node_modules,
virtualenvs, build caches) are expensive to rebuild per worktree.

**Mitigation (partial).** The worktree manager is crash-safe: `SIGKILL` mid-create
leaves no orphan, and `create()` heals a half-registered path.
`WorktreeManager.reclaim_orphans()` removes directories git no longer recognizes,
but nothing calls it yet and there is no `vibey gc` command. Reclaiming worktrees on
item completion and a per-project cache-sharing `bootstrap` hook in `vibey.toml`
are planned; today worktrees stay on disk until removed by hand.

**Bad.** `container` mode adds a Docker dependency and slows iteration.
Accepted: it is opt-in, and the default stays `worktree` for supervised work.

## Alternatives rejected

- **A shared checkout with file locks.** Locks the symptom; agents still race on
  tests, caches, and generated files.
- **A full clone per item.** The same isolation as a worktree at N times the disk,
  without the shared object store, and integration becomes a fetch between
  repositories.
- **Containers instead of worktrees.** A container over one shared checkout still
  shares the checkout. The two compose; neither substitutes for the other.
