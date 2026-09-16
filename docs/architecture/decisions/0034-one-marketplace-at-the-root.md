# 0034 — One Claude Code marketplace at the repository root, rendered from the workspace members

**Status:** accepted · **Date:** 2026-09-15

## Context

`/plugin marketplace add owner/repo` — the form people type, and the form the family's
documentation had implied since the sibling repositories were retired — reads exactly one
file: `<repo>/.claude-plugin/marketplace.json`. There is no subdirectory form of the
shorthand; `--sparse` narrows the checkout, it does not move the manifest.

ADR-0021 absorbed `vibey-skills` (127 plugins, 644 skills) and `vibey-gh` (four plugins)
into this tree as workspace members, and each kept its manifest where its own PyPI package
expects it: `src/vibey_tools/skills/.claude-plugin/marketplace.json` and
`src/vibey_tools/gh/.claude-plugin/marketplace.json`. The root had nothing, so the
shorthand failed with `the-vibey-project/vibey: no readable .claude-plugin/marketplace.json`,
and the documented workaround (`uvx vibey-skills marketplace`, then adding the printed path)
reached only the skills half.

Two facts of the consumer shape the answer. Relative plugin sources resolve against the
marketplace root — the directory holding `.claude-plugin/` — so `./src/vibey_tools/skills/plugins/x`
is a valid source from the repository root, and `../` is refused. And Claude Code registers
**one marketplace per name per user**: a root manifest named `vibey-skills` would collide,
for anyone who had already registered the packaged one, with the manifest PyPI still ships.

## Decision

The repository root carries one `.claude-plugin/marketplace.json`, named `vibey`, holding
every plugin of every member with its source re-rooted to the repository — and that file is
**rendered, never hand-maintained**. `[marketplace] members` in `.vibey-gh.toml` declares the
members; `vibey-gh marketplace` renders the manifest from theirs; `vibey-gh marketplace --check`
and `vibey-gh check` fail when the file on disk is not what the members render to. Each member's
own manifest is untouched, so `vibey-skills` on PyPI keeps working under its own name.

The renderer is a class behind a declared seam — `MarketplaceRenderer` implements
`vibey_gh/interfaces/marketplace_renderer_interface.py`, the first `interfaces/` package in
the absorbed vibey-gh — per ADR-0016's rule that a tenant converges as it is touched.

## Rationale

**Everything-as-code (ADR-0018).** A hand-copied list of 131 plugins is a second source of
truth that drifts the first time a member adds one. The corpus index (`vibey-gh corpus-index`)
already established the pattern for this repository: build the derived file from its sources
at reconcile time and make drift a failing check.

**Dogfood the family (ADR-0017).** vibey-gh is the tool that reconciles declared state for
every repository in the family, and it already validates `.claude-plugin/marketplace.json`
as one of the agent-docs files it expects. Rendering the root manifest is that tool's job,
not a root-level script's.

**A name of its own.** The one-per-name rule makes `vibey` the only name that lets the
repository marketplace and the packaged `vibey-skills` marketplace be registered side by
side. `<plugin>@vibey` is what the README teaches; `<plugin>@vibey-skills` remains the
packaged route.

**Containment is checked, not assumed.** Every rewritten source must start with `./`, carry
no `..` and no backslash, and resolve to a directory holding `.claude-plugin/plugin.json`
inside the repository; one plugin name declared by two members is an error. A member the
root cannot be rendered from is named, never silently skipped.

## Consequences

- `/plugin marketplace add the-vibey-project/vibey` then `/plugin install <plugin>@vibey`
  is the documented, and only necessary, install path. The packaged route stays documented
  second.
- Adding a plugin to a member is a two-step change: the member's manifest, then
  `vibey-gh marketplace`; forgetting the second step fails `vibey-gh check` in CI
  (`provenance.yml`) rather than shipping a stale root.
- A repository with no `[marketplace] members` is unaffected: nothing is rendered and
  nothing is checked, which is every standalone adopter of vibey-gh.
- `vibey_gh/interfaces/` exists now, with its own `.importlinter` contract that it never
  imports the modules that consume it.
