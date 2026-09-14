# Development setup

## Clone and install

```bash
git clone https://github.com/adammatthewsteinberger/claudeloop.git
cd claudeloop
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev,docs]"
pre-commit install
```

`pre-commit install` is the only hook-setup command you need — the repo's
`.pre-commit-config.yaml` declares `default_install_hook_types: [pre-commit,
commit-msg]`, so this one command wires up *both* the lint/format hooks
(`pre-commit` stage) and the Conventional Commits enforcement (`commit-msg`
stage). You do not need `--hook-type commit-msg`.

Requires Python 3.10+ on macOS or Linux. The GitHub default branch is
**`develop`** — branch from it and open PRs into it. `main` is releasable
history for release-please. See the repo-root `CONTRIBUTING.md` for the
Code of Conduct and inbound=outbound MIT contribution license.

## The branch model (gitflow)

```
main         ← always releasable; release-please opens PRs against this
  ▲
develop      ← integration branch; feature branches target this
  ▲
feature/*    ← your work
```

1. Branch from `develop`: `git checkout -b feature/short-description develop`.
2. Commit using [Conventional Commits](https://www.conventionalcommits.org/)
   — the `commit-msg` hook rejects anything else. See the type list below.
3. Open a PR into `develop`. CI (`ci.yml`) runs the full matrix.
4. **Merge strategy matters**: `feature/*` → `develop` is **squash-merged**
   with a conventional-commit-formatted title (GitHub's squash-merge box
   lets you edit the title — make it conventional even if individual commits
   on the branch weren't perfectly clean). `develop` → `main` is a **merge
   commit**, not a squash, so the individual conventional commits survive
   for release-please to parse when deciding the next version bump.
5. release-please watches `main` and maintains a standing "chore(release):
   x.y.z" PR accumulating unreleased changes. Merging *that* PR is what cuts
   a release — see [release-process.md](release-process.md).

## Conventional Commits — the type list

| Type | Use for | Triggers |
|---|---|---|
| `feat` | A new feature | minor bump |
| `fix` | A bug fix | patch bump |
| `feat!` / `fix!` (or a `BREAKING CHANGE:` footer) | A breaking change | major bump |
| `docs` | Documentation only | no bump |
| `style` | Formatting, whitespace — no logic change | no bump |
| `refactor` | Neither a fix nor a feature | no bump |
| `perf` | A performance improvement | patch bump |
| `test` | Adding or correcting tests | no bump |
| `build` | Build system or dependency changes | no bump |
| `ci` | CI configuration changes | no bump |
| `chore` | Anything else (repo maintenance) | no bump |
| `revert` | Reverts a previous commit | depends on what's reverted |

Examples:

```
feat(domain): add CreditsExhausted as a distinct capacity state
fix(waiting): clamp exponential backoff before constructing timedelta
docs(architecture): add ADR for the retry-watchdog decision
test(loop): cover the credit top-up probe sequence
```

An optional scope in parentheses (`domain`, `waiting`, `loop`, `cli`, `docs`,
...) is encouraged but not enforced — it makes the generated changelog far
more scannable.

## Fixing a failed commit-msg hook

If `git commit` is rejected, your editor already has the message you typed —
fix the first line to match `<type>[optional scope]: <description>` and
commit again. `--strict` mode is enabled, so unlisted types are rejected
too; stick to the table above.

## Running the quality gates locally

See [testing.md](testing.md) for the test suite specifically. The full gate
set, in the order CI runs them:

```bash
ruff check src tests
ruff format --check src tests
mypy src/claudeloop
pytest
lint-imports
bandit -q -r src/claudeloop
pip-audit
```

`pre-commit run --all-files` runs the subset of these wired into hooks
(ruff, mypy, bandit, import-linter) against your working tree without
needing to remember each command individually.

## Where new code belongs

See [`../architecture/overview.md`](../architecture/overview.md#where-new-code-belongs-a-quick-test)
for the decision test, and the
[`claudeloop-architecture`](https://github.com/adammatthewsteinberger/claudeloop/blob/main/.claude/skills/claudeloop-architecture/SKILL.md)
Claude Code skill if you're using Claude Code itself to contribute — it
applies the same test automatically.
