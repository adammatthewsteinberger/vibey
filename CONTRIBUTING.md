# Contributing to vibey

Thank you for considering a contribution. This document is meant to be
command-level and specific — if something here is unclear or you hit a
situation it doesn't cover, that's a bug in this document; please open an
issue or a PR fixing it.

## Table of contents

1. [Environment setup](#environment-setup)
2. [The branch model](#the-branch-model)
3. [Conventional Commits](#conventional-commits)
4. [Provenance](#provenance)
5. [Quality gates](#quality-gates)
6. [The workspace tenants](#the-workspace-tenants)
7. [The onion architecture import rule](#the-onion-architecture-import-rule)
8. [Protected tests](#protected-tests)
9. [Agent surfaces](#agent-surfaces)
10. [Decisions and governing rules](#decisions-and-governing-rules)
11. [The paper and the book](#the-paper-and-the-book)
12. [PR checklist](#pr-checklist)
13. [Getting help](#getting-help)
14. [Code of Conduct](#code-of-conduct)
15. [License of contributions](#license-of-contributions)

## Environment setup

```bash
git clone https://github.com/the-vibey-project/vibey.git
cd vibey
uv sync --extra dev
# The framework hooks, all three stages. Without --hook-type the commit-msg
# and pre-push hooks are never installed and the suite never runs locally.
uv run pre-commit install --hook-type pre-commit --hook-type commit-msg --hook-type pre-push
# Then the provenance hooks. This points core.hooksPath at .githooks; the
# tracked .githooks/*.local shims chain back to the framework hooks above.
uv run vibey-gh install
```

Requires **Python 3.12+**, **PostgreSQL**, and **macOS or Linux**. Windows is
not a supported target. The suite reads `VIBEY_TEST_DATABASE_URL` (default
`postgresql://$USER@localhost:5432/vibey_test`); that role needs `CREATEDB`,
because the session builds a migrated `vibey_test_template` and clones one
`vibey_test_<worker>` per xdist worker. The default suite needs no engine
binaries and no paid accounts: tests marked `paid` are deselected unless you
ask for them (ADR-0030).

## The branch model

```
main         ← always releasable; every push publishes to PyPI (release.yml)
  ▲ rebase merge — main's ruleset permits only rebase. The promotion PR is
  │ opened by `vibey-gh promote` (promote-to-main.yml); after a release,
  │ develop is realigned to main's tree.
develop      ← integration branch; every push publishes a vibey-dev build to TestPyPI
  ▲ squash merge — develop's ruleset permits only squash
feature/*    ← your work
```

1. `git checkout -b feature/short-description develop`
2. Commit using [Conventional Commits](#conventional-commits).
3. Open a PR **into `develop`**, never `main`.
4. You do not press Merge. Once the PR has one approval, a green `gates`
   check (ci.yml) and a successful `PR automation / gate` check
   (pr-automation.yml), the merge train (`vibey-gh merge-train`,
   merge-train.yml) squash-merges it. A draft PR is never merged by the
   train. To see why a PR is not moving:
   `gh workflow run merge-train.yml -f pr=<N> -f dry_run=true`.
5. `vibey-gh promote` opens the promotion PR from `develop` into `main`; it is
   rebase-merged, `release.yml` publishes, and `develop` is realigned.

Never implement on `main`.

## Conventional Commits

Every commit message follows
[Conventional Commits](https://www.conventionalcommits.org/): `feat`, `fix`,
`docs`, `style`, `refactor`, `perf`, `test`, `build`, `chore`, `ci`,
`revert`. Two hooks act on the message: `conventional-pre-commit` rejects a
bad subject, and vibey-gh's `.githooks/commit-msg` appends the `Made-With:`
provenance trailer. The version of the next release is derived from what
changed (`vibey-gh version`, configured by `[version]` in `.vibey-gh.toml`),
not from the commit types (ADR-0028).

A commit made in the GitHub web UI — including an accepted Copilot autofix —
bypasses both hooks and fails the `Provenance` check. Reword it locally before
merge.

## Provenance

Every source file under `src/`, `tests/` and `scripts/`, and every workflow,
carries a fingerprint header, and every commit carries the `Made-With:`
trailer. The pre-push hook refuses a push whose fingerprints are not intact,
and the `Provenance` job (provenance.yml) audits the PR's commit range in CI.

```bash
uv run vibey-gh check            # what is missing
uv run vibey-gh check --apply    # add missing file headers
```

## Quality gates

On `git commit` the hooks run only ruff (`--fix`) and ruff-format. Everything
else runs on `git push`: first `vibey-gh check`, then the test suite, mypy
--strict, import-linter, the four 100% branch-coverage gates, bandit and
pip-audit. CI (ci.yml, job `gates`) enforces the same seven gates, of which
Gate 4 is the four per-layer floors (ADR-0023):

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy --strict src/vibey

# One test run with coverage, then the per-layer 100% branch gates:
uv run pytest -q -p no:cacheprovider --cov=vibey --cov-branch --cov-report=
uv run coverage report --include='src/vibey/domain/*' --fail-under=100
uv run coverage report --include='src/vibey/application/*' --fail-under=100
uv run coverage report --include='src/vibey/infrastructure/*' --fail-under=100
uv run coverage report --include='src/vibey/cli/*' --fail-under=100

uv run lint-imports
uv run bandit -q -r src/vibey
uv run pip-audit
```

There is no "coverage debt" mechanism: a PR that drops any layer below 100%
branch coverage does not merge. A `pragma: no cover`, `noqa`, `nosec` or
`type: ignore` needs its reason written beside it. Every `None`-default
keyword argument needs both-sides tests.

CI also runs a multi-arch container build with four image contracts and a
Helm install on minikube with four cluster contracts
([Kubernetes guide](docs/guides/kubernetes.md), ADR-0025).

## The workspace tenants

This repository is a uv workspace (ADR-0021). `src/vibey` is the conductor;
`src/vibey_runners/{claude,codex,cursor,agy,qwen,common}` are the `*loop`
runners; `src/vibey_tools/{gh,skills,bootstrap}` are vibey-gh, vibey-skills
and vibey-bootstrap. Each was imported with its history and is still published
to PyPI under its own name.

The root gates above cover `src/vibey` only. A tenant keeps every gate it was
already held to (ADR-0022), run from its own directory with its own command,
on the Python floors its wheel publishes — exactly as ci.yml's `tools` and
`tools-lint` jobs do:

| Tenant | Checks |
|---|---|
| `src/vibey_tools/gh` | `pip install -e ".[dev]"`, `python -m pytest -q` (100% branch floor), `black --check vibey_gh test`, `isort --check-only vibey_gh test`, `mypy vibey_gh`, and the managed-automation drift check; Python 3.11–3.13 |
| `src/vibey_tools/skills` | `python3 tools/validate_manifests.py`, `python3 tools/check_links.py`, `PYTHONPATH=src python3 -m unittest discover -s tests`; Python 3.10 and 3.12 |
| `src/vibey_tools/bootstrap` | `pip install -e ".[test,all]"`, `pytest test/ -m "not integration" --cov=vibey_bootstrap` (100% line floor); Python 3.11–3.12 |
| `src/vibey_runners/*` | each runner's own `ruff`, `mypy --strict`, `lint-imports` and `pytest`, per its `CONTRIBUTING.md` |

A change to a vibey-gh template (`src/vibey_tools/gh/vibey_gh/templates/`)
must be re-rendered at both roots, or the drift check fails:

```bash
uv run vibey-gh install
(cd src/vibey_tools/gh && uv run vibey-gh install)
```

## The onion architecture import rule

```
domain → application → infrastructure → cli, tui
                                  ▲
                          bootstrap.py (the sole composition root)
```

Dependencies point inward only, enforced by `import-linter` in CI — not by
convention. `domain/` has no I/O, no async, no clock and no network, verified
by an AST-walking purity test; on imports it allows the standard library and
the dependency-free family packages (`vibey-gh`, `vibey-skills`,
`vibey-runners-common`), never `vibey_bootstrap` (ADR-0017). New I/O goes in
`infrastructure/` behind a `Protocol` declared in `application/interfaces/`;
wiring happens only in `bootstrap.py`.

New and changed code lives in classes, and every class has an interface beside
it in a mirrored `interfaces/` package (`src/vibey/foo/bar.py` ↔
`src/vibey/foo/interfaces/bar_interface.py`). Interface modules import only the
standard library and other interfaces. A module-level function is the
exception, with its reason written at the definition (ADR-0016).

## Protected tests

A small set of test files encode contracts that must not drift
(`tests/system/test_delivery_stage_set.py`, `tests/domain/test_noloss*.py`,
`tests/domain/test_briefing.py`, `tests/infrastructure/db/test_chaos.py`,
and everything under `tests/live/`). Do not modify them without explicit
maintainer sign-off in the PR description; changes to them are reviewed as
contract changes, not test edits.

## Agent surfaces

When a skill or procedure changes, update all four agent-surface trees in
the same PR: `.claude/skills/`, `.cursor/rules/`, `.agents/skills/`, and
`.agent/rules/`. CLAUDE.md, AGENTS.md and GEMINI.md hold facts, not
procedures, and change together.

## Decisions and governing rules

An architectural choice is an ADR in
`docs/architecture/decisions/NNNN-slug.md`: a status and date line, Context,
Decision, Consequences, and Alternatives rejected. Adding one means the next
contiguous number, an entry in the `properdocs.yml` nav (a title with no
colon, or the book exporter drops the chapter), and bumping the "(N ADRs)"
count in CLAUDE.md, AGENTS.md, GEMINI.md, README.md and docs/index.md;
`tests/meta/test_adr_counts.py` fails otherwise.

A **governing rule** — one that binds future decisions, survives a rewrite,
and is about conduct rather than mechanism — is not law until it is a
sub-doctrine in `src/vibey_tools/gh/docs/doctrines.md`, filed under one of the
sealed Twelve, and ratified by the operator's merge (ADR-0020; Constitution
Article II.3). Propose one per pull request, as a draft, regenerate the index
in the same change, and cite it from the ADR that argues it:

```bash
(cd src/vibey_tools/gh && uv run vibey-gh corpus-index && uv run vibey-gh corpus-index --check)
```

## The paper and the book

Two documents are built from this tree on every release and published on the
docs site beside the pages they mirror:

- **The research paper.** Source `docs/paper.md`, compiled by
  `vibey-gh paper` to [PDF](https://the-vibey-project.github.io/vibey/main/paper.pdf),
  and published as [HTML](https://the-vibey-project.github.io/vibey/main/paper/).
  Keep it to the constrained Markdown the renderer converts: a `# Title`, a
  `**Abstract.**` paragraph, `##` sections, lists, tables, ```` ```latex ````
  fences, and a `## References` list.
- **The book.** Every page in `properdocs.yml` nav order, exported by
  `vibey-gh book` as [PDF](https://the-vibey-project.github.io/vibey/main/book.pdf),
  [EPUB](https://the-vibey-project.github.io/vibey/main/book.epub) and
  [print HTML](https://the-vibey-project.github.io/vibey/main/book-print.html).
  A nav edit is a book edit.

Both are also attached to each GitHub Release as permanent assets. Preview
copies of everything are published under `/develop/`.

## PR checklist

- [ ] Branched from `develop`; targets `develop` (not `main`)
- [ ] Commits (or the squash-merge title) follow Conventional Commits
- [ ] `uv run vibey-gh check` passes (file headers and `Made-With:` trailers)
- [ ] `uv run pre-commit run --all-files --hook-stage pre-push` passes
- [ ] All four 100% branch-coverage gates pass
- [ ] If a tenant under `src/vibey_runners/` or `src/vibey_tools/` changed, its own checks pass
- [ ] New or changed classes have an interface beside them (ADR-0016)
- [ ] Protected tests untouched (or sign-off obtained and noted)
- [ ] Agent-surface trees updated if a procedure changed
- [ ] Docs updated if behavior changed; a new ADR bumps the count and the nav
- [ ] Any new governing rule is proposed as a sub-doctrine, with the corpus index regenerated
- [ ] I agree to the [Code of Conduct](CODE_OF_CONDUCT.md) and to license
      this contribution under the MIT License

## Getting help

See [SUPPORT.md](SUPPORT.md) for the right channel. Usage questions belong
in [Discussions](https://github.com/the-vibey-project/vibey/discussions),
not bug reports.

## Code of Conduct

This project follows the
[Contributor Covenant 2.1](CODE_OF_CONDUCT.md). By participating you agree
to uphold it.

## License of contributions

By contributing, you agree that your contributions are licensed under the
[MIT License](LICENSE).
