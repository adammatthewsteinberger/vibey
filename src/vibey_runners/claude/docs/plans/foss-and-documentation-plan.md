# Plan: claudeloop — FOSS release infrastructure, documentation, and Claude skills

> **Status.** This is the approved plan being executed to turn `claudeloop` into a
> published FOSS project. Preserved here verbatim as the design record; the
> gitflow branch originally called `dev` throughout this document was renamed to
> `develop` immediately after `git init`, and every reference below reflects
> that rename. See [`../contributing/development.md`](../contributing/development.md)
> for the living contributor workflow.

## Context

The `claudeloop` package currently exists as a working but unpublished M1 core: a tested domain layer under `src/claudeloop/domain/`, 86 passing tests at 99.5% coverage, and quality tooling configured in `pyproject.toml`. What it is *not* yet is a project anyone else can find, install, trust, or contribute to.

**It is not even a git repository.** There is no `.git`, no `.gitignore` (despite `.mypy_cache/`, `.ruff_cache/`, `.import_linter_cache/`, `.coverage`, and `.venv/` already sitting in the tree), no `LICENSE` file, no CI, and `.claude/` holds nothing but `settings.local.json`.

This plan turns it into a published, self-explanatory MIT-licensed project on PyPI under `adammatthewsteinberger`, with documentation thorough enough that a stranger can contribute on day one, and a set of Claude Code skills that make *Claude* an effective contributor to this specific codebase. It does not implement M2–M5 of the architecture plan — that roadmap is preserved into `docs/` as part of this work.

### Decisions taken

| Decision | Choice | Why |
|---|---|---|
| Distribution name | **`claudeloop`** | Verified free: `pypi.org/simple/claudeloop/` and the JSON API both 404. GitHub `adammatthewsteinberger/claudeloop` also 404. |
| Release automation | **release-please** | Opens a reviewable release PR instead of bot-pushing to `main`, which is what a protected-`main` gitflow needs. |
| Documentation | **Markdown + MkDocs Material** | Files stay plainly readable in-repo so `CLAUDE.md` and skills link straight to paths, while GitHub Pages gets a searchable site for the PyPI metadata URL. |

### Findings from the deep scan that this plan fixes

1. **PyPI name collision forced a rename.** The working title `autoclaude` was rejected by PyPI as too similar to existing packages (`auto-claude`, `autoclaude-cli`). The distribution, import, and CLI name is therefore **`claudeloop`**.
2. **The name is not reserved until first publish.** A PyPI *pending* publisher reserves nothing. Publishing a real `0.1.0` early is the mitigation, not an afterthought.
3. **The license is asserted but not granted.** `pyproject.toml` says `license = { text = "MIT" }` — the deprecated PEP 621 spelling — and there is no `LICENSE` file on disk at all. Migrate to PEP 639 (`license = "MIT"` + `license-files`) and add the actual file.
4. **`mypy --strict` benefits nobody downstream.** There is no `src/claudeloop/py.typed` marker, so every type in this package is invisible to consumers. For a package billed as a library, that is a real gap.
5. **PyPI metadata is bare.** No classifiers, no keywords, no `[project.urls]`, and `authors = [{ name = "Adam" }]` with no email.

## Deliverables

### 1. Git foundation

`git init`, then create `main` and branch `develop` from it, with the M1 tree as the initial commit. Add:

- **`.gitignore`** — Python standard plus the caches already present (`.venv/`, `.coverage`, `.mypy_cache/`, `.ruff_cache/`, `.import_linter_cache/`, `.pytest_cache/`, `.hypothesis/`, `__pycache__/`, `dist/`, `build/`, `*.egg-info/`).
- **`.gitattributes`** — normalize line endings; mark `docs/` and vendored content for linguist.
- **`.editorconfig`** — matches ruff's 100-column line length so non-ruff editors don't fight it.

Move `claude_autoresume.py` to `legacy/claude_autoresume.py` with a header comment marking it the reference implementation being replaced, and link it from the architecture docs. It is the source of every behavioral requirement and should not simply vanish.

### 2. Packaging and PyPI metadata (`pyproject.toml`)

Fix the five scan findings: PEP 639 license fields, full trove classifiers, `keywords`, `[project.urls]` (Homepage, Repository, Documentation, Issues, Changelog), a real author name and email, and create **`src/claudeloop/py.typed`** (picked up automatically by the existing `packages = ["src/claudeloop"]` config).

Tighten the coverage gate as layers land rather than leaving one global `--cov-fail-under=95`: per-package thresholds, 100% for `domain` and `application`.

### 3. GitHub Actions

Four workflows. Note that **`publish-to-pypi.yml` is a load-bearing filename** — PyPI's pending-publisher configuration matches on the workflow's *filename*, so this must be registered on PyPI exactly as named.

| Workflow | Trigger | Purpose |
|---|---|---|
| `ci.yml` | push/PR to `main`/`develop` | Matrix 3.10–3.13: ruff, `mypy --strict`, pytest+coverage, import-linter, bandit, pip-audit |
| `release-please.yml` | push to `main` | Maintain the release PR; on merge, tag and create the GitHub Release |
| `publish-to-pypi.yml` | `release: published` | Build, then publish to PyPI via Trusted Publishing |
| `docs.yml` | push to `main` | Build MkDocs and deploy to GitHub Pages |

**`publish-to-pypi.yml` shape** — two jobs, and the split is the security control, not ceremony. The build job runs your code and your dependencies but holds no OIDC token; the publish job holds the token and runs nothing but the upload:

```yaml
permissions:
  contents: read          # workflow-level default-deny baseline

jobs:
  build:                  # no id-token here, deliberately
    # actions/checkout@v7, actions/setup-python@v7
    # python -m build   (not `hatch build` — no custom hooks to justify it)
    # twine check --strict dist/*
    # actions/upload-artifact@v7
  publish:
    needs: build
    environment:
      name: pypi
      url: https://pypi.org/p/claudeloop
    permissions:
      id-token: write     # job-scoped, mandatory for Trusted Publishing
    # actions/download-artifact@v8   ← note: v8, while upload is v7
    # pypa/gh-action-pypi-publish pinned to SHA dc37677b2e1c63e2034f94d8a5b11f265b73ba33  # v1.14.2
```

Pin every action to a commit SHA with a trailing version comment, and let Dependabot's `github-actions` ecosystem bump them — that is what makes SHA pinning sustainable instead of rot-inducing. Do **not** set `attestations:`; it defaults to true for Trusted Publishing flows, and a separate sigstore step is now redundant. Do **not** add an API-token fallback — it would disable secretless publishing for no benefit.

Add **`.github/dependabot.yml`** covering `pip`, `github-actions`, and `pre-commit`.

**Manual steps the maintainer must perform** (documented in `docs/contributing/release-process.md`, since they cannot be automated):
1. Create the GitHub repo `adammatthewsteinberger/claudeloop`, push `main` and `develop`, set `main` as default.
2. On PyPI → Publishing → add a **pending publisher**: project `claudeloop`, owner `adammatthewsteinberger`, repo `claudeloop`, workflow **`publish-to-pypi.yml`**, environment `pypi`.
3. Create the GitHub environment `pypi` with himself as required reviewer — this is the human gate that makes Trusted Publishing stronger than a repo-scoped token, given that anyone with commit access can otherwise modify publishing workflows.
4. Protect `main`: require CI green, no force-push.
5. Enable GitHub Pages (source: Actions).

### 4. Git hooks and Conventional Commits

**`.pre-commit-config.yaml`** with `default_install_hook_types: [pre-commit, commit-msg]`, so contributors run a single `pre-commit install` and get both hook types — nobody can forget the `--hook-type commit-msg` flag because it isn't needed.

Hooks: `astral-sh/ruff-pre-commit` (lint + format), `pre-commit/pre-commit-hooks` (trailing whitespace, EOF, merge conflicts, large files, YAML/TOML validation), `compilerla/conventional-pre-commit` v4.4.0 pinned at the `commit-msg` stage, plus local `mypy` and `bandit` passes.

Use pre-commit's current stage names (`pre-commit`, `commit-msg`, `pre-push`) — `commit`/`push` were deprecated in 3.2.0.

### 5. Community health files

- **`LICENSE`** — MIT, © 2026 Adam Matthew Steinberger.
- **`CONTRIBUTING.md`** — exhaustive and command-level, not generic. Covers: environment setup, the gitflow model (`feature/*` → `develop` → `main`), the Conventional Commits contract with the full type list and worked examples, how to install and troubleshoot hooks, every quality gate and how to fix each failure, the testing philosophy (fakes over mocks, no real sleeping, property tests), the onion import rule and what `import-linter` will reject, and the PR checklist. Merge strategy is explicit: **squash** `feature/*` → `develop` with a conventional title, **merge commit** `develop` → `main` so individual conventional commits survive for release-please to parse.
- **`CODE_OF_CONDUCT.md`** — Contributor Covenant 2.1.
- **`SECURITY.md`** — genuinely load-bearing here, not boilerplate: this tool bypasses Claude Code permissions, handles API keys, and writes audit logs. Covers the reporting channel, response expectations, and the threat model.
- **`CHANGELOG.md`** — seeded, then owned by release-please. Never hand-edited.
- **`.github/ISSUE_TEMPLATE/`** — YAML issue *forms* (`bug_report.yml`, `feature_request.yml`) with `required: true` on version/OS/Python/command, plus `config.yml` with `blank_issues_enabled: false`. A CLI bug report is useless without those fields.
- **`.github/PULL_REQUEST_TEMPLATE.md`** — short checklist; long ones get ignored.

Skipping as cargo cult for a solo project at this stage: `CITATION.cff`, `FUNDING.yml`, `CODEOWNERS`, and badge walls (README gets four badges: PyPI version, Python versions, CI, license).

### 6. Documentation (`docs/` + MkDocs Material)

`mkdocs.yml` with Material theme, `mkdocstrings[python]` for API reference, search, and nav. Every page is plain markdown that reads correctly on GitHub so `CLAUDE.md` and skills can link file paths directly.

```
docs/
├── index.md                        # what it is, why it exists
├── getting-started/                # installation, quickstart, configuration
├── guides/                         # autonomous-runs, rate-limits-and-credits,
│                                   #   never-blocking, completion-detection, rest-api-surface
├── architecture/
│   ├── overview.md                 # onion layers + the import contract
│   ├── domain-model.md             # every value object and ADT, with rationale
│   ├── ports-and-adapters.md
│   ├── run-loop-state-machine.md   # states, transitions, decision table
│   └── decisions/                  # ADRs, one per hard call already made
├── reference/                      # cli.md, api.md (mkdocstrings-generated)
├── contributing/                   # development, testing, release-process, documentation
└── plans/
    ├── architecture-and-roadmap.md # the approved M1–M5 plan, migrated verbatim
    └── foss-and-documentation-plan.md  # THIS plan
```

The ADRs are where the hard-won research belongs, so the reasoning survives the people who did it. At minimum: why the Agent SDK replaced subprocess; why `CreditsExhausted` is a distinct state from `WindowExhausted`; why waiting probes instead of sleeping; why `CLAUDE_CODE_RETRY_WATCHDOG` is off by default; why the REST surface is generated rather than hand-written; why `AskUserQuestion` is denied-with-guidance rather than auto-answered.

**`README.md`** is rewritten as the project's front door: badges, what problem it solves, install, a 30-second quickstart, a feature overview, a link map into `docs/`, and project status honestly stating that M1 is complete and M2–M5 are roadmap.

### 7. Claude Code skills (`.claude/skills/`)

Eight skills, each `.claude/skills/<name>/SKILL.md` — exactly one level deep, since category subdirectories are not scanned. All prefixed `claudeloop-` because **personal skills override project skills of the same name**, so an unprefixed `testing` skill in someone's `~/.claude/skills/` would silently shadow ours.

| Skill | Covers |
|---|---|
| `claudeloop-architecture` | Onion layers, where new code belongs, the import-linter contract, composition root |
| `claudeloop-domain-model` | Every value object and ADT; capacity/classification/waiting/completion semantics |
| `claudeloop-agent-sdk` | `ClaudeAgentOptions` fields, `RateLimitEvent`, the credits-vs-window distinction, never-block mechanisms, the probe design |
| `claudeloop-rest-surface` | Introspection, the Typer binder, the drift gate |
| `claudeloop-testing` | pytest layout, fakes over mocks, `FakeClock`/`FakeSleeper`, property tests, coverage gates |
| `claudeloop-quality-gates` | Running and *fixing* ruff, mypy, import-linter, bandit, pip-audit |
| `claudeloop-releasing` | gitflow, conventional commits, release-please, Trusted Publishing |
| `claudeloop-docs` | Writing and building docs, where each kind of content belongs |

Authoring rules, from verified guidance:

- Frontmatter stays within the portable spec subset (`name`, `description`, and `allowed-tools` where useful) so the skills remain valid if ever packaged. `name` matches the directory.
- **Descriptions must be deliberately "pushy."** Claude's documented failure mode is *under*-triggering skills. Each description states what it does, when to use it, explicit trigger phrases, and negative scope.
- SKILL.md bodies stay **under 500 lines**; anything longer moves into `references/` linked **one level deep only** (Claude may partially read files reached through a second hop).
- Bodies are written as standing instructions, not one-time steps — once invoked, a skill stays in context and is not re-read on later turns.

There is no validation: malformed frontmatter loads silently with empty metadata and the skill simply never triggers. A CI check parses every `SKILL.md`'s frontmatter and fails on malformed YAML, a missing `description`, or a `name` that disagrees with its directory.

### 8. `CLAUDE.md`

Deliberately the shortest document in the repo — a router, not a manual. Facts that are always true and cheap to state; everything procedural lives in a skill, everything explanatory in `docs/`. The dividing line is explicit in the authoring guidance: **CLAUDE.md holds facts, skills hold procedures.**

Contents: one-paragraph project identity; the layer map with the import rule in a sentence; the non-negotiables (never block on a human, credits ≠ rate limit, domain stays pure, conventional commits); the handful of commands worth memorizing; and a link table into `docs/`, `.claude/skills/`, `CONTRIBUTING.md`, and `legacy/claude_autoresume.py`.

## Execution order

1. Git init, `.gitignore`, `.gitattributes`, `.editorconfig`, move legacy script, initial commit on `main`, branch `develop`.
2. `LICENSE`, `py.typed`, `pyproject.toml` metadata fixes.
3. `.pre-commit-config.yaml`; install hooks; verify the commit-msg hook rejects a non-conventional message.
4. Deep read of `src/claudeloop/domain/` and `tests/domain/` so docs and skills describe what the code *does*, not what the plan intended.
5. `docs/` tree, `mkdocs.yml`, both plan documents migrated into `docs/plans/`.
6. `README.md`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, `CHANGELOG.md`, issue/PR templates.
7. `.claude/skills/` — eight skills plus the frontmatter CI check.
8. `CLAUDE.md` last, once every target it links exists.
9. Workflows: `ci.yml`, `release-please.yml`, `publish-to-pypi.yml`, `docs.yml`, `dependabot.yml`, release-please config and manifest.

## Verification

- **Hooks** — attempt a commit with the message `wip` and confirm the `commit-msg` hook rejects it; confirm `feat: add x` passes. Run `pre-commit run --all-files` clean.
- **Quality gates locally** — `ruff check`, `ruff format --check`, `mypy --strict`, `pytest` with coverage gate, `lint-imports`, `bandit -r src`, `pip-audit`. All must pass before the first push.
- **Package builds and is installable** — `python -m build`, then `twine check --strict dist/*`, then `pipx install dist/*.whl` in a scratch dir and confirm the `claudeloop` entry point resolves.
- **Typing ships** — confirm `py.typed` is present inside the built wheel (`unzip -l dist/*.whl`); without it the `mypy --strict` investment is invisible downstream.
- **Docs build** — `mkdocs build --strict` must pass with zero warnings, which catches every broken internal link.
- **Skills load** — run `claude --debug` in the repo and confirm all eight skills are discovered with non-empty descriptions and no parse errors; confirm the CI frontmatter check fails when a `description` is deliberately removed.
- **CI** — open a throwaway PR into `develop` and confirm the matrix runs green across 3.10–3.13.
- **Release dry run** — publish `0.1.0` to **TestPyPI** first via `workflow_dispatch`, install it from TestPyPI in a clean venv, and only then run the real PyPI publish. This validates the OIDC wiring before it matters.
- **Release loop** — merge a `feat:` commit to `main`, confirm release-please opens a release PR with the right bump and changelog entry, merge it, and confirm the GitHub Release fires `publish-to-pypi.yml` and the artifact lands on PyPI with attestations.
