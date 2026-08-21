# Runbook: one tree, two shared libraries — submodules, version sync, and what actually belongs in them

## Goal

Bring the whole `vibey-*` family into one working tree as git submodules,
put every repo on the current `vibey-skills` and (where it applies)
`vibey-bootstrap`, keep them there, and move genuinely shared logic into
those libraries instead of maintaining N copies.

## Current state (measured 2026-08-21, not assumed)

The family on GitHub is seven repos:

| Repo | Latest | What it is |
|---|---|---|
| `vibey` | — | the conductor |
| `claudeloop` | 0.6.1 | session runner |
| `codexloop` | 0.3.1 | session runner |
| `cursorloop` | 0.6.0 | session runner |
| `agyloop` | 0.4.1 | session runner |
| `vibey-skills` | **v2.14.0** | Claude Code plugin marketplace: 18 plugins / 71 Agent Skills. On PyPI |
| `vibey-bootstrap` | **v4.0.0** | Azure Functions cross-cutting layer: App Config + Key Vault + App Insights, Service Bus, scaffold CLI. On PyPI |

Two findings change the shape of this work, and both came from looking
rather than assuming:

**1. No repo depends on either library today.** Not vibey, not any runner.
They appear only as README "related projects" links. So this is not an
upgrade — it is adoption, and adoption has design questions an upgrade
does not.

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

There is a fourth, larger duplication that the file-hash scan does not
see: CI workflows, release-please configuration, docs scaffolding, and
the four agent-surface router files exist in near-identical form in every
repo. That is real, and it is a better first target than the code,
because it has no semantic reconciliation cost.

## The vibey-bootstrap scope question — decide this first

`vibey-bootstrap` is, by its own description, **the Azure Functions
cross-cutting layer**. vibey and the four runners are CLI tools. They do
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

**(b) is the reading that matches the intent**, but it changes the
library's identity and its published contract for existing users, so it
is an explicit decision to record — not something to infer and start
building. Everything below assumes (b); if (a) is chosen, the extraction
work needs a new home and the rest of this runbook still stands.

## Design

### Submodules

`vibey` becomes the umbrella tree; each other repo is a submodule under
`repos/`. Submodules and not a true monorepo, because each package
already publishes to PyPI on its own release-please cadence and has its
own CI, gates, and version history — collapsing that into one repo throws
away working machinery to solve a problem nobody has.

What the umbrella buys is the thing that is genuinely missing: one place
to run a family-wide check, which is precisely what runbook 18's
extraction scan and the currency check need.

- Pinned by commit, as submodules always are. A submodule bump is a
  reviewable commit in `vibey`, which is a feature: it makes "the family
  moved" an event with a diff.
- CI in the umbrella runs the *family-level* checks only. Per-repo gates
  stay in the repo that owns them; duplicating them in the umbrella would
  double every CI bill for nothing.
- Contributors keep working in the individual repos. The umbrella is not
  a required checkout for ordinary work, and the docs must say so, or
  every contributor pays a submodule tax for a workflow they never use.

### Version sync

"Synced" needs a definition, because the naive one is wrong: these
packages are independently versioned and independently useful, so forcing
a single version number across them would be theatre.

What actually needs to hold:

1. Every repo depends on a **compatible, current** `vibey-skills` — same
   major, at or above the current minor.
2. Every submodule pointer in the umbrella references a commit that is on
   its repo's `develop` or `main` — never a detached WIP commit.
3. A release of a shared library triggers a bump PR in every consumer,
   automatically. Manual propagation across seven repos will not happen
   twice.

Runbook 18's currency dimension is the enforcement arm; this runbook
builds the plumbing it measures.

### vibey-skills adoption

There is already a concrete, self-identified gap to close.
`infrastructure/provision/agent_surface.py` says in its own docstring:

> The marketplace skill directories (`.claude/skills/`, `.agents/skills/`,
> `.cursor/rules/`, `.agent/`) ... are not materialized here: there is no
> `vibey-skills` ... marketplace available in this build environment to
> pull skill content from. Only the four router files -- the part that's
> genuinely self-contained -- are provisioned. Replace this docstring
> note, not the emitter's signature, once real marketplace access exists.

That is the adoption task, already scoped by the person who wrote the
limitation. With the library as a dependency, provisioning materializes
real skills into a BUILD worktree instead of only the routers.

The enforcement half: **every AI request a run issues does so with the
current skills loaded**, and the session records which version was in
play. A run that cannot name its skills version fails the currency check
— "probably current" is not a measurement. Produced code that makes its
own AI requests references the skills library rather than inlining
prompts.

## Work items

1. Record the vibey-bootstrap scope decision, (a) or (b).
2. Add the six repos as submodules under `repos/`; umbrella CI runs
   family-level checks only.
3. Family-level version-sync check + auto-bump PRs on library release.
4. Adopt `vibey-skills` in vibey; close the `agent_surface.py` gap so
   skills are materialized, not just routers.
5. Per-session skills-version manifest + the enforcement that no AI
   request goes out without it.
6. Extract the measured 440 lines (`handoff_marker`, `verbosity`,
   `forecast`) into the shared library; the runners consume it.
7. Extract the shared CI/release/docs scaffolding — larger win, no
   semantic reconciliation cost.
8. Feed the reconciliation backlog (the ~85 diverged modules) in as
   individual, prioritized items. Do not attempt this as one change.

## Verification

- `git submodule status` in a fresh clone lists six pinned repos, all on
  a published branch commit.
- A `vibey-skills` release opens a bump PR in every consumer without
  anyone asking it to.
- A BUILD worktree contains real skill content, and `agent_surface.py`'s
  docstring caveat is deleted because it is no longer true.
- A run's ledger names the skills version it used; a run with none fails
  the currency check.
- `handoff_marker` and `verbosity` exist once in the family, and all four
  runners still pass their own gates on the shared implementation.

## Needs from operator

- The vibey-bootstrap scope decision.
- Confirmation that submodules (not a merged monorepo) is the intent.
- PyPI publish rights for the shared libraries, already in hand.

## Risks

- **Assuming the shared core is bigger than it is.** Measured: 187 lines
  across all four. A plan budgeted for "consolidate the duplication" will
  overrun the moment it meets the ~85 diverged modules.
- **Breaking vibey-bootstrap's existing users** if its scope broadens.
  A major version and a migration note, or a second package.
- **Submodule friction** for contributors who never needed the umbrella.
  Mitigated by keeping per-repo workflows first-class and saying so.
- **Skills currency becoming a hard blocker.** If a run cannot start
  because the marketplace is briefly unreachable, the enforcement has
  converted an advisory into an outage. It needs a cached last-known-good
  and a recorded degraded state, not a hard stop.
