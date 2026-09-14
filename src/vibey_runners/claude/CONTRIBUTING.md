# Contributing to claudeloop

Thank you for considering a contribution. This document is meant to be
command-level and specific — if something here is unclear or you hit a
situation it doesn't cover, that's a bug in this document; please open an
issue or a PR fixing it.

## Table of contents

1. [Environment setup](#environment-setup)
2. [The branch model](#the-branch-model-gitflow)
3. [Conventional Commits](#conventional-commits)
4. [Git hooks](#git-hooks)
5. [Quality gates](#quality-gates)
6. [Testing philosophy](#testing-philosophy)
7. [The onion architecture import rule](#the-onion-architecture-import-rule)
8. [PR checklist](#pr-checklist)
9. [Getting help](#getting-help)
10. [Code of Conduct](#code-of-conduct)
11. [License of contributions](#license-of-contributions)

## Environment setup

```bash
git clone https://github.com/adammatthewsteinberger/claudeloop.git
cd claudeloop
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,docs]"
pre-commit install
```

Requires Python 3.10+ on **macOS or Linux**. Windows is not a supported
target — CI and classifiers are Unix-only; see
[`docs/getting-started/installation.md`](docs/getting-started/installation.md).
The GitHub default branch is **`develop`** (the integration branch you PR
into). `main` is the releasable line that release-please watches.

See [`docs/contributing/development.md`](docs/contributing/development.md) for
the full version of this page, including where new code belongs in the
onion architecture.

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
   matrix (Python 3.10–3.13).
4. Your feature branch is **squash-merged** into `develop` — give the
   squash-merge title a conventional-commit-formatted summary of the whole
   PR, even if your individual commits weren't perfectly conventional
   along the way.
5. Periodically, `develop` is merged into `main` as a **merge commit** (not
   squashed) so every conventional commit that landed on `develop` survives
   individually for release-please to parse.
6. release-please then maintains a standing release PR on `main`; merging
   *that* PR is what actually cuts a version and publishes to PyPI. See
   [`docs/contributing/release-process.md`](docs/contributing/release-process.md).

## Conventional Commits

Every commit message must follow
[Conventional Commits](https://www.conventionalcommits.org/):

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

Allowed types (enforced by the `commit-msg` hook in `--strict` mode — any
other type is rejected):

| Type | Use for | Version bump |
|---|---|---|
| `feat` | A new feature | minor |
| `fix` | A bug fix | patch |
| `feat!` / `fix!` / a `BREAKING CHANGE:` footer | A breaking change | major |
| `docs` | Documentation only | none |
| `style` | Formatting, no logic change | none |
| `refactor` | Neither a fix nor a feature | none |
| `perf` | A performance improvement | patch |
| `test` | Adding or correcting tests | none |
| `build` | Build system or dependencies | none |
| `ci` | CI configuration | none |
| `chore` | Anything else | none |
| `revert` | Reverting a previous commit | depends |

```
feat(domain): add CreditsExhausted as a distinct capacity state
fix(waiting): clamp exponential backoff before constructing timedelta
docs(architecture): add ADR for the retry-watchdog decision
```

The **scope** (`domain`, `waiting`, `loop`, `cli`, `docs`, ...) in
parentheses is optional but strongly encouraged — it makes the
release-please-generated changelog dramatically more scannable.

## Git hooks

Installed with a single command:

```bash
pre-commit install
```

This wires up **both** hook types this repo uses — `pre-commit` (ruff lint
+ format, generic file hygiene, local mypy/bandit/import-linter checks) and
`commit-msg` (Conventional Commits enforcement) — because
`.pre-commit-config.yaml` declares `default_install_hook_types: [pre-commit,
commit-msg]`. You do not need `--hook-type commit-msg`; if you've seen that
flag suggested elsewhere, it isn't necessary here.

**Troubleshooting:**

- *"My commit was rejected with a Conventional Commits error"* — your
  editor still has the message you typed; fix the first line to match
  `<type>[scope]: <description>` using a type from the table above and
  commit again.
- *"A hook failed and modified files"* — ruff's `--fix` and `ruff-format`
  hooks can rewrite files in place. `git status`, review the changes,
  `git add` them, and commit again — this is expected pre-commit behavior,
  not a failure to work around.
- *"Hooks are slow the first time"* — pre-commit builds an isolated
  environment per hook repo on first run and caches it. Subsequent commits
  are fast.
- *"I need to bypass hooks for an emergency commit"* — `git commit
  --no-verify`. Use sparingly; CI will still enforce everything the hooks
  would have caught.

## Quality gates

Run the full set locally before opening a PR:

```bash
ruff check src tests
ruff format --check src tests
mypy src/claudeloop
pytest
lint-imports
bandit -q -r src/claudeloop
pip-audit
```

Or the subset wired into hooks, against your working tree:

```bash
pre-commit run --all-files
```

**Fixing common failures:**

| Gate | Symptom | Fix |
|---|---|---|
| `ruff check` | Lint error | `ruff check --fix src tests` for auto-fixable ones; the rest need a manual edit |
| `ruff format --check` | Formatting diff | `ruff format src tests` |
| `mypy` | Type error | Add/correct type annotations. `domain/` and `application/` run under `--strict` — no `Any` escape hatches without a documented reason |
| `pytest` | A test fails or coverage drops below the per-package floor | See [Testing philosophy](#testing-philosophy) below |
| `lint-imports` | An onion-layering violation | See [The onion architecture import rule](#the-onion-architecture-import-rule) |
| `bandit` | A flagged security pattern | Either fix it, or — if it's a genuine false positive like an exhaustiveness `assert` — add a `# nosec B1xx` with an inline comment explaining *why* it's not a real issue (two examples already exist in `src/claudeloop/domain/loop.py`) |
| `pip-audit` | A dependency has a known CVE | Bump the dependency; if no fix is available yet, document the exposure and mitigation in the PR |

## Testing philosophy

Full detail: [`docs/contributing/testing.md`](docs/contributing/testing.md).
The short version:

- **Fakes over mocks.** Every port gets a real class implementing the same
  `Protocol`, checked by `mypy --strict` — not a `unittest.mock.Mock`.
- **No real sleeping, ever, in a test.** `FakeClock`/`FakeSleeper` let a
  simulated seven-day rate-limit wait, or a scripted credit-top-up sequence,
  run in microseconds.
- **Hypothesis property tests for anything numeric or time-based.** This
  already caught a real `timedelta` overflow bug in the backoff calculation
  during development — see
  [ADR 0004](docs/architecture/decisions/0004-adaptive-waiting-with-probes-not-sleep.md).
- **`domain/` and `application/` require 100% coverage.** These layers have
  zero I/O and zero third-party dependencies — there's no excuse for an
  untested branch, and this is precisely the code deciding whether an
  unattended run keeps going, waits, or gives up.
- **`# pragma: no cover` must carry a reason.** A bare pragma with no
  explanation will be rejected in review.

## The onion architecture import rule

`domain/` imports nothing but the standard library. `application/` imports
`domain/` and defines ports as `Protocol`, never a concrete SDK type.
`infrastructure/` is the *only* place `anthropic` or `claude_agent_sdk` may
appear in an `import` statement. `cli/` talks to `application/` use cases via
`bootstrap.py`, never to `infrastructure/` directly.

This is enforced by `import-linter` — running in CI and in the pre-commit
hooks — not by convention. If your PR needs to import across a layer
boundary this rule forbids, that's a signal the code belongs in a different
layer, not a signal to weaken the contract. See
[`docs/architecture/overview.md`](docs/architecture/overview.md) for the
full layer table and the "where does new code belong" decision test, and
[ADR 0001](docs/architecture/decisions/0001-onion-architecture-with-import-linter.md)
for why this was chosen over convention-only layering.

## PR checklist

- [ ] Branch created from `develop`, named `feature/<short-description>`
- [ ] Commits (or at minimum the squash-merge title) follow Conventional Commits
- [ ] `pre-commit run --all-files` passes
- [ ] `pytest` passes with coverage gates met (100% on any `domain`/`application` code touched)
- [ ] New numeric or time-based logic has a Hypothesis property test, not just examples
- [ ] No new cross-layer imports that `lint-imports` would reject
- [ ] Docs updated if behavior changed — including removing a `!!! note "Roadmap"` admonition if this PR implements something previously marked as roadmap
- [ ] A new ADR added under `docs/architecture/decisions/` if this PR makes a hard, non-obvious design call worth preserving the reasoning for
- [ ] You agree to the [Code of Conduct](CODE_OF_CONDUCT.md) and to license this contribution under the MIT License

## Getting help

| I want to... | Go here |
|---|---|
| User/operator docs | [https://adammatthewsteinberger.github.io/claudeloop/](https://adammatthewsteinberger.github.io/claudeloop/) |
| Ask a question or discuss design | [GitHub Discussions](https://github.com/adammatthewsteinberger/claudeloop/discussions) |
| Report a bug | [Bug report form](https://github.com/adammatthewsteinberger/claudeloop/issues/new?template=bug_report.yml) |
| Propose a feature | [Feature request form](https://github.com/adammatthewsteinberger/claudeloop/issues/new?template=feature_request.yml) |
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
