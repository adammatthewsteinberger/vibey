# Contributing to codexloop

Thank you for considering a contribution. This document is meant to be
command-level and specific — if something here is unclear or you hit a
situation it doesn't cover, that's a bug in this document; please open an
issue or a PR fixing it.

## Environment setup

```bash
git clone https://github.com/adammatthewsteinberger/codexloop.git
cd codexloop
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,docs]"
pre-commit install
```

Requires **Python 3.12+** on **macOS or Linux**. Windows is not a supported
target. Live runs need the `codex` CLI on `PATH` and either `codex login` or
`OPENAI_API_KEY`; the default test suite needs neither.

## The branch model (gitflow)

```
main         ← always releasable; release-please opens release PRs against this
  ▲ (merge commit — preserves individual conventional commits)
develop      ← integration branch; feature branches target this
  ▲ (squash-merge — one conventional-commit-titled squash per feature)
feature/*    ← your work
```

1. `git checkout -b feature/short-description develop`
2. Commit using [Conventional Commits](#conventional-commits).
3. Open a PR **into `develop`**, not `main`. CI runs the full quality-gate
   matrix.
4. Your feature branch is **squash-merged** into `develop` — give the squash
   title a conventional-commit-formatted summary of the whole PR.
5. Periodically, `develop` is merged into `main` as a **merge commit**.
   release-please maintains a standing release PR on `main`; merging *that*
   is what cuts a version and publishes to PyPI. Every push to `develop`
   publishes to TestPyPI. See [docs/publishing.md](docs/publishing.md).

Never implement on `main`.

## Conventional Commits

Every commit message must follow
[Conventional Commits](https://www.conventionalcommits.org/):

```
<type>[optional scope]: <description>
```

Allowed types (enforced by the `commit-msg` hook in `--strict` mode):
`feat` (minor bump), `fix` / `perf` (patch), `feat!` / `fix!` / a
`BREAKING CHANGE:` footer (major), and `docs`, `style`, `refactor`, `test`,
`build`, `ci`, `chore`, `revert` (no bump).

```
feat(domain): add usage_not_included to the quota code set
fix(argv): never emit --full-auto
docs(architecture): add ADR for the optional app-server transport
```

## Git hooks

`pre-commit install` wires up **both** `pre-commit` (ruff lint + format,
mypy, bandit, import-linter) and `commit-msg` (Conventional Commits) because
`.pre-commit-config.yaml` declares
`default_install_hook_types: [pre-commit, commit-msg]`.

- Conventional Commits rejection — fix the first line to
  `<type>[scope]: <description>` and commit again.
- A hook rewrote files — `git add` the fixes and commit again.
- Emergency bypass: `git commit --no-verify`. CI still enforces the gates.

## Quality gates

Run the full set locally before opening a PR:

```bash
ruff check src tests
ruff format --check src tests
mypy --strict src/codexloop
pytest                         # default: not live and not system
pytest -m system               # scripted system harness; no OpenAI account
pytest -m live                 # real Codex account (opt-in)
lint-imports
bandit -q -r src/codexloop
pip-audit
mkdocs build --strict
```

Or the subset wired into hooks: `pre-commit run --all-files`.

Coverage floor: **100% for the whole package**
(`pytest --cov=codexloop --cov-fail-under=100`).

## Testing philosophy

- **Fakes over mocks.** Every port gets a real class implementing the same
  `Protocol`, checked by `mypy --strict`.
- **No real sleeping, ever, in a test.** `FakeClock` / `FakeSleeper` let a
  simulated weekly-window wait or a scripted top-up run in microseconds.
- **Hypothesis property tests for anything numeric or time-based** — in
  particular, no input whose `error.code` is in the non-waitable set may
  ever produce a waitable state.
- **`# pragma: no cover` must carry a reason.**

## The onion architecture import rule

`domain/` imports nothing but the standard library. `application/` imports
`domain/` and defines ports as `Protocol`. `infrastructure/` is the *only*
place `openai` may appear in an `import` statement or `codex` may be spawned.
`cli/` talks to `application/` via `bootstrap.py`, never to
`infrastructure/` directly. Nothing, anywhere, imports `anthropic` or
`claude_agent_sdk`.

Enforced by `import-linter` in CI and pre-commit — not by convention. See
[ADR 0001](docs/architecture/adr/0001-onion-import-linter.md).

## Non-negotiables (do not regress these)

- Never block on a human.
- Quota / billing ≠ rate-limit window (`CreditsExhausted` has no reset).
- A capacity rejection always outranks a completion claim.
- Body-first classification: `error.code` / `error.type` before HTTP status.
- Never bare `codex`. Never `--full-auto`.

## PR checklist

- [ ] Branch created from `develop`, named `feature/<short-description>`
- [ ] Commits (or the squash-merge title) follow Conventional Commits
- [ ] `pre-commit run --all-files` passes
- [ ] `pytest` and `pytest -m system` pass; the 100% coverage floor holds
- [ ] New numeric or time-based logic has a Hypothesis property test
- [ ] No new cross-layer imports that `lint-imports` would reject
- [ ] Docs updated if behavior changed
- [ ] Agent surfaces kept in sync (Claude / Cursor / Codex / Antigravity)
- [ ] A new ADR under `docs/architecture/adr/` if this PR makes a hard,
      non-obvious design call
- [ ] You agree to the [Code of Conduct](CODE_OF_CONDUCT.md) and to license
      this contribution under the MIT License

## Getting help

| I want to... | Go here |
|---|---|
| User/operator docs | [https://adammatthewsteinberger.github.io/codexloop/](https://adammatthewsteinberger.github.io/codexloop/) |
| Ask a question or discuss design | [GitHub Discussions](https://github.com/adammatthewsteinberger/codexloop/discussions) |
| Report a bug | [Bug report form](https://github.com/adammatthewsteinberger/codexloop/issues/new?template=bug_report.yml) |
| Propose a feature | [Feature request form](https://github.com/adammatthewsteinberger/codexloop/issues/new?template=feature_request.yml) |
| Report a vulnerability | [SECURITY.md](SECURITY.md) — privately |
| Same map, shorter | [SUPPORT.md](SUPPORT.md) |

Blank issues are disabled on purpose. If none of the forms fit, open a
Discussion instead of a free-form issue.

## Code of Conduct

Participation in this project is governed by the
[Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). Report
unacceptable behavior to adam@matthewsteinberger.com.

## License of contributions

This repository is MIT-licensed ([LICENSE](LICENSE)). By opening a pull
request you agree that your contribution is provided under the same MIT
License (inbound = outbound). There is no CLA.
