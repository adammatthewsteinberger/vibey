# Runbook: one tree, two shared libraries — the monorepo, version sync, and what actually belongs in them

> **Status (2026-09-15):** landed as a merged monorepo, not submodules — subtree
> imports with history (runners 2026-09-10, tools 2026-09-15) plus a uv workspace (ADR-0021). The
> submodule plan below is superseded. Done: the single tree (item 2),
> vibey-skills adoption for context packets (item 4, PR #82), the
> vibey-bootstrap scope decision (item 1, by ADR-0017). Open: the
> skills-version manifest (item 5), the domain extraction (item 6), shared
> scaffolding (item 7), the reconciliation backlog (item 8).

## Goal

Bring the whole `vibey-*` family into one working tree (landed as a
uv workspace, ADR-0021; the original plan was git submodules), put every
package on the current `vibey-skills` and (where it applies)
`vibey-bootstrap`, keep them there, and move genuinely shared logic into
those libraries instead of maintaining N copies.

## Current state (originally measured 2026-08-21; updated 2026-09-15)

On 2026-08-21 the family was seven GitHub repositories. It is now one
repository holding ten packages:

| Package | Path | Version | What it is |
|---|---|---|---|
| `vibey` | `src/vibey` | 0.6.0 | the conductor |
| `claudeloop` | `src/vibey_runners/claude` | 0.8.0 | session runner |
| `codexloop` | `src/vibey_runners/codex` | 0.4.0 | session runner |
| `cursorloop` | `src/vibey_runners/cursor` | 0.7.0 | session runner |
| `agyloop` | `src/vibey_runners/agy` | 0.5.0 | session runner |
| `qwenloop` | `src/vibey_runners/qwen` | 0.2.0 | local-model session runner (ADR-0015) |
| `vibey-runners-common` | `src/vibey_runners/common` | 0.1.0 | shared runner application interfaces and use cases |
| `vibey-gh` | `src/vibey_tools/gh` | 1.73.0 | provenance, versioning, merge train, release automation |
| `vibey-skills` | `src/vibey_tools/skills` | 2.19.10 | Agent Skills marketplace and context-packet engine |
| `vibey-bootstrap` | `src/vibey_tools/bootstrap` | 4.2.3 | Azure cross-cutting layer: App Config, Key Vault, App Insights |

Two findings changed the shape of this work, and both came from looking
rather than assuming:

**1. On 2026-08-21, no repo depended on either library.** Not vibey, not
any runner. So this was not an upgrade — it was adoption. *Update
2026-09-15:* vibey now declares `vibey-skills>=2.18,<3` (the `skills`
extra, invoked as a process by `infrastructure/skills_context.py`, PR #82)
and `vibey-gh>=1.2` (dev), both resolved from the workspace. claudeloop
and codexloop consume `vibey-runners-common`; cursorloop, agyloop and
qwenloop do not yet. `src/vibey` still imports no `vibey_bootstrap` code
(ADR-0017 records the gap).

**2. The shared surface is far smaller than it looks.** All four runners
share ~88 module *names*, which invites the conclusion that there is a
large common core waiting to be lifted out. Hashing the contents
(normalising the package name) says otherwise:

| Scope | Files | Lines |
|---|---|---|
| Identical across **all four** runners | 2 (`domain/handoff_marker.py`, `domain/verbosity.py`) | 187 |
| Identical across **three** | 1 (`domain/forecast.py`) | 253 |
| Same name, diverged implementation | ~85 | — |

So the lift-and-shift candidate is roughly **440 lines across three pure
domain modules**. Everything else that looks shared has drifted, and
consolidating it is a *reconciliation* project — deciding which of four
divergent implementations is correct — not a packaging one. Plan the
budget for that, not for the packaging.

*Update 2026-09-15:* the first extraction to land was not these modules
but `vibey-runners-common` (shared application interfaces and
`usecases/completion.py`), which this runbook never planned.
`handoff_marker.py`, `verbosity.py` and `forecast.py` are still duplicated
in all four original runners; item 6 is open and should target
`vibey-runners-common`.

There is a fourth, larger duplication that the file-hash scan does not
see: CI workflows, release configuration, docs scaffolding, and the four
agent-surface router files existed in near-identical form in every repo.
The monorepo made most of the CI half moot — only root workflows run, and
release-please is retired (ADR-0028) — but the subtrees still carry their
inert `.github/` trees and their own docs scaffolding.

## The vibey-bootstrap scope question — decide this first

`vibey-bootstrap` is, by its own description, **the Azure Functions
cross-cutting layer**. vibey and the five runners are CLI tools. They do
not use App Configuration, Key Vault, Application Insights, or Service
Bus.

"Every repo uses the latest vibey-bootstrap" therefore does not
straightforwardly apply, and there are two honest readings:

- **(a) Keep its scope.** The currency mandate applies only where Azure
  Functions are actually in play — today, nothing in this family. It
  stays a product this family publishes rather than one it consumes.
- **(b) Broaden it** into the general cross-cutting layer for the family,
  with the Azure Functions material becoming one module inside it. This
  is what makes "scan for things to add to vibey-bootstrap" meaningful,
  and it is where the 440 shared lines and the shared CI/tooling would
  land.

**Decision recorded 2026-09-15: (b), by ADR-0017.** `vibey_bootstrap` is
the family's cross-cutting layer (retry, dead-letter routing,
correlation-scoped logging, secret masking, health probes), used from
`infrastructure/` behind ports and forbidden in `domain/` because it
carries the Azure SDK and OpenTelemetry (named in `.importlinter`). Work
item 1 is closed. Adopting it in `src/vibey` is ADR-0017's work, not yet
done.

## Design

### Monorepo (landed; supersedes the submodule plan)

> **Superseded by ADR-0021.** This section originally planned `vibey` as an
> umbrella tree with each other repository as a git submodule under
> `repos/`, on the grounds that each package already had its own CI,
> release-please cadence and history. That plan was not adopted.

What landed is a merged monorepo (runners imported 2026-09-10, tools
2026-09-15):

- The five runners and three tools were imported as subtrees **with
  history preserved** — `src/vibey_runners/{claude,codex,cursor,agy,qwen}`
  and `src/vibey_tools/{gh,skills,bootstrap}` — and `vibey-runners-common`
  was added at `src/vibey_runners/common` (2026-09-10). There is no `.gitmodules`.
- The root `pyproject.toml` registers them as a uv workspace
  (`[tool.uv.workspace] members = ["src/vibey_runners/*", "src/vibey_tools/*"]`),
  and `tool.uv.sources` resolves `vibey-gh` and `vibey-skills` from the tree
  (`{ workspace = true }`). That is uv metadata, stripped at build time, so
  the published requirement strings are unchanged.
- Each package still publishes to PyPI as its own project and keeps its own
  quality gates (ADR-0022): the root CI `tools` matrix runs `vibey-gh`,
  `vibey-skills` and `vibey-bootstrap` with their original commands on their
  published Python floors; the subtrees' own `.github/` trees do not run.
- Releases are cut by `vibey-gh promote`, not release-please (ADR-0028).
- The sibling GitHub repositories no longer exist; their PyPI projects do.

What the single tree buys is what the submodule plan wanted — one place to
run a family-wide check — plus atomic cross-package changes and one lock
file (`uv lock --check` gates CI).

### Version sync

"Synced" needs a definition, because the naive one is wrong: these
packages are independently versioned and independently useful, so forcing
a single version number across them would be theatre.

What actually needs to hold:

1. Every package depends on a **compatible, current** `vibey-skills` — same
   major, with a range that includes the in-tree version.
2. Every workspace member resolves from the tree, and `uv lock --check`
   passes (the submodule-pointer rule this item used to state no longer
   applies).
3. A version change in a shared library that falls outside a consumer's
   declared range fails CI in the same change, rather than waiting for a
   bump PR.

Runbook 18's currency dimension is the enforcement arm; this runbook
builds the plumbing it measures.

### vibey-skills adoption

On 2026-08-21, `infrastructure/provision/agent_surface.py` said in its
own docstring that no `vibey-skills` marketplace was available, so only
the four router files were provisioned.

That gap closed in PR #82 (ADR-0031). When a project enables
`skills_context`, `infrastructure/skills_context.py` invokes the
`vibey-skills` process/JSON contract, and a bounded context packet is
appended to the engine plan; the generated index and packets live under
`.vibey/` and are excluded from commits. The full marketplace is
deliberately not copied into every worktree; routers remain the stable
cross-engine surface.

The enforcement half: **every AI request a run issues does so with the
current skills loaded**, and the session records which version was in
play. A run that cannot name its skills version fails the currency check
— "probably current" is not a measurement. Produced code that makes its
own AI requests references the skills library rather than inlining
prompts.

## Work items

1. Record the vibey-bootstrap scope decision, (a) or (b). **Done: (b),
   ADR-0017.**
2. ~~Add the six repos as submodules under `repos/`~~ — superseded. **Done
   as** subtree imports + uv workspace (ADR-0021).
3. Family-level version-sync check. Largely covered by the workspace lock
   and `uv lock --check`; a pin-range check remains.
4. Adopt `vibey-skills` in vibey. **Done** (context packets, PR #82,
   ADR-0031).
5. Per-session skills-version manifest + the enforcement that no AI
   request goes out without it.
6. Extract the measured 440 lines (`handoff_marker`, `verbosity`,
   `forecast`) into `vibey-runners-common`; the runners consume it.
7. Remove the subtrees' inert `.github/` trees and share docs
   scaffolding — the CI/release half is mostly done by the monorepo.
8. Feed the reconciliation backlog (the ~85 diverged modules) in as
   individual, prioritized items. Do not attempt this as one change.

## Verification

- `uv lock --check` passes and every runner and tool resolves from the
  tree. (Replaces the submodule check.) Done.
- A `vibey-skills` version outside a consumer's range fails CI in the
  same change.
- A BUILD worktree receives a bounded skills packet, and `agent_surface.py`'s
  docstring caveat is deleted because it is no longer true. Done (PR #82).
- A run's ledger names the skills version it used; a run with none fails
  the currency check.
- `handoff_marker` and `verbosity` exist once in the repository, and all
  four runners still pass their own gates on the shared implementation.

## Needs from operator

- Nothing new. The scope decision is recorded (ADR-0017), the monorepo
  question is closed (ADR-0021), and PyPI publish rights are in hand.

## Risks

- **Assuming the shared core is bigger than it is.** Measured: 187 lines
  across all four. A plan budgeted for "consolidate the duplication" will
  overrun the moment it meets the ~85 diverged modules.
- **Breaking vibey-bootstrap's existing users** if its scope broadens.
  A major version and a migration note, or a second package.
- **Absorbed packages losing their bar.** Moving into one tree can quietly
  lower what a package was held to. ADR-0022 is the mitigation: each
  keeps its own gates, run by the root CI on its published floors.
- **Skills currency becoming a hard blocker.** If a run cannot start
  because the marketplace is briefly unreachable, the enforcement has
  converted an advisory into an outage. It needs a cached last-known-good
  and a recorded degraded state, not a hard stop.
