# 0021 — One tree, history preserved: the family is absorbed as subtrees in a uv workspace

**Status:** accepted · **Date:** 2026-09-15 · **Supersedes:** the submodule design in runbook 19

## Context

Runbook 19 (2026-08-21) planned to bring the family into one working tree as **git submodules** under `repos/`, explicitly "not a true monorepo", because each package published on its own cadence with its own CI and gates, and asked the operator to confirm that submodules were the intent. What landed between 2026-09-10 and 2026-09-15 is the other answer.

Five runners (`claudeloop`, `codexloop`, `cursorloop`, `agyloop`, `qwenloop`) were imported with `git subtree` into `src/vibey_runners/<name>` and three tools (`vibey-gh`, `vibey-skills`, `vibey-bootstrap`) into `src/vibey_tools/<name>`, each commit carrying `git-subtree-dir`/`git-subtree-split` trailers so every line still has its author and date. A shared `vibey-runners-common` package was added beside the runners. `pyproject.toml` registers `src/vibey_runners/*` and `src/vibey_tools/*` as uv workspace members and resolves `vibey-gh` and `vibey-skills` from the tree. The sibling GitHub repositories were then retired; the PyPI names were not.

## Decision

**The family lives in this repository as absorbed subtrees, history preserved, in one uv workspace.** Concretely:

- **Subtree import, not submodule and not copy.** A submodule is a pointer to a repository that must keep existing; a copy discards the record of who wrote what. A subtree import keeps the history in this tree and lets the source repository go away.
- **One workspace, per-package projects.** Each absorbed package keeps its own `pyproject.toml`, name, version, `requires-python`, test suite and lint configuration. The workspace globs (`src/vibey_runners/*`, `src/vibey_tools/*`) mean a new member registers itself — `common` needed no wiring.
- **Resolve from the tree, publish as before.** `[tool.uv.sources]` points `vibey-gh` and `vibey-skills` at the workspace. This is uv metadata stripped at build time; the published requirement strings stay as `[project.optional-dependencies]` declares them, which is exactly the difference from the git pin that once broke publishing with PyPI's "400 Can't have direct dependency". The PyPI distributions continue to exist under their own names.
- **The tooling is a declared path, never a search.** `.vibey-gh.toml [install] self_source = "src/vibey_tools/gh"`, because a workflow that searched the tree for a package declaring `name = "vibey-gh"` would install whatever a pull request planted.
- **The runtime image is not the tree.** `deploy/docker/Dockerfile` copies `src/vibey/` and only the one subtree it must build (`vibey-skills`); `COPY src/ ./src/` had been shipping ~160 MB of runner and tool sources into an image that cannot execute them.

## Consequences

**Good.** One place to run a family-wide check, which was the whole point of runbook 19. Cross-package changes (a runner interface moving into `common`, a tool fix vibey depends on) are one reviewed pull request instead of a release-and-bump dance across seven repositories. The canon (`src/vibey_tools/gh/docs/`) and its corpus index travel with the code that checks them.

**Bad, and accepted.** The workspace lock resolves at the intersection of every member's floor, which is 3.12, so a uv environment cannot exercise the 3.10/3.11 floors the tools publish — CI's `tools` matrix uses plain `pip` and `setup-python` for that reason (see ADR-0022). Root `pytest` only sees `tests/`; the absorbed suites had to be gated separately. `ruff` now runs over ~1,840 files. The runbook-19 verification steps written for submodules (`git submodule status`, six pinned repos) are void and the runbook needs a superseded banner pointing here.

**Left open.** ADR-0020 already records that the law now physically lives inside one package's documentation and does not settle whether that is right. The `vibey-bootstrap` scope question runbook 19 asked first (Azure-Functions-only, or the family's cross-cutting layer) is still unrecorded; ADR-0017 treats it as the latter in practice.

## Alternatives rejected

- **Git submodules under `repos/`** (runbook 19's design). Keeps seven repositories alive, seven CI bills, and a submodule tax on every contributor; a family-wide refactor is still N pull requests plus N pointer bumps. Rejected once the goal became one reviewed change per cross-cutting fix rather than one place to run a scan.
- **Separate repositories, PyPI as the only seam** (the status quo). This is what produced the runbook-19 finding that no repo depended on either library — the seam was too expensive to cross, so nobody crossed it.
- **Copy the sources in without history.** Same tree shape, but every absorbed line becomes anonymous and the provenance gate (`vibey-gh` fingerprints) starts from a lie about authorship.
- **One package, one version.** Collapsing eight distributions into `vibey` would break every existing `pip install claudeloop` and make a runner bump a conductor release. The workspace keeps the distributions independent for exactly this reason.
