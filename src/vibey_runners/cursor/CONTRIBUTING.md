# Contributing to cursorloop

Thank you for considering a contribution. This document is meant to be
command-level and specific — if something here is unclear or you hit a
situation it doesn't cover, that's a bug in this document; please open an
issue or a PR fixing it.

## Environment setup

```bash
git clone https://github.com/adammatthewsteinberger/cursorloop.git
cd cursorloop
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,docs]"
pre-commit install
```

Requires **Python 3.12+** on **macOS or Linux**. Windows is not a supported
target. Auth for live Cursor runs is `CURSOR_API_KEY` (never a foreign vendor
API-key env var); the default test suite needs no account.

## The branch model (gitflow)

```
main         ← always releasable; vibey-gh promotes develop into this
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
   vibey-gh promotes develop into main with a derived version bump; the push
   to main publishes to PyPI. See docs/contributing/release.md.

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
feat(domain): add a router-* model ladder
fix(infra): record hooks restore metadata before mutating hooks.json
docs(architecture): add ADR for the billing lexicon
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
mypy src/cursorloop
pytest                         # default: not system
pytest -m system               # scripted system harness; no Cursor account
lint-imports
bandit -q -r src/cursorloop
pip-audit
mkdocs build --strict
```

Or the subset wired into hooks: `pre-commit run --all-files`.

Coverage floors, enforced per layer in CI (pass `--cov=cursorloop.<layer>
--cov-fail-under=100` as CI does): domain, application, infrastructure, and
cli — **100% each**.

## Testing philosophy

- **Fakes over mocks.** Every port gets a real class implementing the same
  `Protocol`, checked by `mypy --strict`.
- **No real sleeping, ever, in a test.** `FakeClock` / `FakeSleeper`.
- **Hypothesis property tests for anything numeric or time-based** — e.g.
  `parse_retry_after` must never raise on `nan` or mixed-offset datetimes.
- **`# pragma: no cover` must carry a reason.**

## The onion architecture import rule

`domain/` imports nothing but the standard library. `application/` imports
`domain/` and defines ports as `Protocol`. `infrastructure/` is the *only*
place `cursor_sdk` may appear in an `import` statement. `cli/` talks to
`application/` via `bootstrap.py`, never to `infrastructure/` directly.
Nothing, anywhere, imports `anthropic` or `claude_agent_sdk`.

Enforced by `import-linter` in CI and pre-commit — not by convention. See
[ADR-0001](docs/architecture/decisions/0001-onion-architecture.md).

## Non-negotiables (do not regress these)

- Never block on a human.
- Exhausted credits ≠ waitable rate-limit window (`CreditsExhausted` has no reset).
- A capacity rejection always outranks a completion claim.
- No Anthropic / `claude_agent_sdk` dependency; no foreign vendor auth env fallbacks.
- Default model profile is `composer-2.5`; Grok is a profile, not a product.
- Ambiguous capacity signals bias toward `CreditsExhausted`.

## PR checklist

- [ ] Branch created from `develop`, named `feature/<short-description>`
- [ ] Commits (or the squash-merge title) follow Conventional Commits
- [ ] `pre-commit run --all-files` passes
- [ ] `pytest` and `pytest -m system` pass; 100% coverage holds on every layer touched
- [ ] New numeric or time-based logic has a Hypothesis property test
- [ ] No new cross-layer imports that `lint-imports` would reject
- [ ] Docs updated if behavior changed
- [ ] Agent surfaces kept in sync (Claude / Cursor / Codex / Antigravity)
- [ ] A new ADR under `docs/architecture/decisions/` if this PR makes a
      hard, non-obvious design call
- [ ] You agree to the [Code of Conduct](CODE_OF_CONDUCT.md) and to license
      this contribution under the MIT License

## Getting help

| I want to... | Go here |
|---|---|
| User/operator docs | [https://adammatthewsteinberger.github.io/cursorloop/](https://adammatthewsteinberger.github.io/cursorloop/) |
| Ask a question or discuss design | [GitHub Discussions](https://github.com/adammatthewsteinberger/cursorloop/discussions) |
| Report a bug | [Bug report form](https://github.com/adammatthewsteinberger/cursorloop/issues/new?template=bug_report.yml) |
| Propose a feature | [Feature request form](https://github.com/adammatthewsteinberger/cursorloop/issues/new?template=feature_request.yml) |
| Report a vulnerability | [SECURITY.md](SECURITY.md) — privately |
| Design context | [`docs/plans/architecture-and-roadmap.md`](docs/plans/architecture-and-roadmap.md) |
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
