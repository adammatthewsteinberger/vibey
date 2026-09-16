# AGENTS.md

`vibey`: a queue-based, six-phase conductor for autonomous software delivery.
Built on PostgreSQL and five `*loop` autonomous session runners (claudeloop,
codexloop, cursorloop, agyloop, and the opt-in local qwenloop), which live in this
repository under `src/vibey_runners/`. It orchestrates design → build → review with
an optional visual-design interstitial, plus an opt-in Azure deployment stage
set. Pre-1.0. Python 3.12+.

**This file is deliberately short — it holds facts, not procedures.** Every
"how do I..." lives in a skill below; every "why was it built this way"
lives in `docs/architecture/decisions/`.

## Non-negotiables

- **Never block a worker on a human.** Human input is a *parked job* plus a
  `human_gate` row, never a thread waiting on stdin.
- **Credits ≠ rate limit.** `CreditsExhausted` has no `resets_at` field and
  must never acquire one. This is enforced at three independent layers: the
  type definition, a property test, and a database CHECK constraint.
- **A capacity rejection always outranks a completion claim.**
- **`domain/` stays pure.** No I/O, no async, no clock, no network — enforced by
  `tests/domain/test_domain_purity.py`, which walks the AST. On imports: stdlib,
  itself, and **any family package that is itself dependency-free** (`vibey-gh`,
  `vibey-skills`, `vibey-runners-common` all declare `dependencies = []`, so they
  add nothing stdlib-only did not already allow). `vibey_bootstrap` is forbidden
  here by name, not by category — it carries the Azure SDK and OpenTelemetry, so
  it would pull a third-party graph in transitively. Use it from
  `infrastructure/`. Enforced by `import-linter` in CI, not convention. ADR-0017.
- **Dogfood the family, always.** If a capability exists inside this family, use
  it — do not reimplement it and do not reach for a third-party equivalent. The
  bar is not "is ours better", it is "does ours do this at all". Between using
  `vibey_bootstrap`'s retry or dead-letter routing and hand-rolling one, use
  ours. A new implementation of something the family already ships needs a
  written reason at the call site, and the reason must be a capability gap — in
  which case the fix is to add it to ours. ADR-0017; sub-doctrine 10.e.
- **Everything-as-code, and never less of it.** If a thing can be declared in the
  repository and reconciled from it, that is how it is done — branch protection,
  repository profile, pipelines, policy, infrastructure. No settings page, no
  one-off `gh api`, no runbook step that says "then set X". And **everything that
  can be generic and configurable must be**: a hard-coded value that could have
  been a key is a decision taken away from the next adopter, silently. Never
  change anything to a state that is less generic or less configurable. ADR-0018;
  sub-doctrine 12.c.
- **A governing rule is a ratified sub-doctrine, or it is not a rule.** Anything
  that can be spelled out explicitly as a sub-doctrine in the governance corpus
  must be — filed under one of the sealed Twelve in
  `src/vibey_tools/gh/docs/doctrines.md`, and ratified by the operator's merge per
  Article IV.4, under the authority Article I.1 places above every other. No
  exceptions. The test: it binds future decisions, it survives a rewrite, and it
  is about conduct rather than mechanism. An ADR records the decision; the canon
  records the law. Both get written. ADR-0020.
- **Code lives in classes, and every class has an interface beside it.** A
  module-level function is the method of last resort, and its reason is written
  at the definition. `src/<pkg>/services/github_service.py` implies
  `src/<pkg>/services/interfaces/github_service_interface.py`. Interfaces
  declare; they never consume. New and changed code from 2026-09-15; the
  existing tree converges module by module. ADR-0016; sub-doctrine 9.b.
- **The handoff no-loss gate is not negotiable.** A handoff that fails the
  gate is a retry, an escalation to full-transcript mode, or a human gate —
  never a silent partial.
- **Every job is idempotent under replay.** Workers die; the lease expires
  and another worker picks it up.
- **The ledger is append-only.** No updates, no deletes. Corrections are new
  events that supersede prior ones.
- **Every commit follows Conventional Commits.** Enforced by a pre-commit hook.
- **Never implement on `main`.** Feature PRs squash into `develop` through the
  merge train (`vibey-gh merge-train`); `develop` is promoted to `main` by
  `vibey-gh promote` as a **rebase** merge, keeping history linear
  (`.vibey-gh.toml [branches]`). A push to `develop` publishes `vibey-dev` to
  TestPyPI; a push to `main` publishes `vibey` to PyPI. ADR-0028.

## Layer map

```
domain → application → infrastructure → cli, tui
                                  ▲
                          bootstrap.py
                   (the sole composition root)
```

Dependencies point inward only, enforced by `import-linter` in CI. Four of the
five layers carry a **100% branch coverage floor** enforced in CI as separate
gates: `domain/`, `application/`, `infrastructure/`, `cli/` each fail the build
under 100%. `tui/` is outside the floor, a recorded exemption. ADR-0023.

**Workspace tenants.** The map above covers `src/vibey` only. The repository is a
uv workspace (`[tool.uv.workspace] members = ["src/vibey_runners/*",
"src/vibey_tools/*"]`, ADR-0021) whose other members are absorbed with history:

- `src/vibey_runners/{claude,codex,cursor,agy,qwen}` — claudeloop, codexloop,
  cursorloop, agyloop, qwenloop; `src/vibey_runners/common` — vibey-runners-common.
- `src/vibey_tools/gh` — vibey-gh (provenance, merge train, promotion, release,
  and the governance canon under `docs/`); `src/vibey_tools/skills` —
  vibey-skills; `src/vibey_tools/bootstrap` — vibey-bootstrap.

Each tenant keeps its own `pyproject.toml`, version, Python floor (3.10+ for
claudeloop, vibey-runners-common and vibey-skills; 3.11+ for vibey-gh and
vibey-bootstrap; 3.12+ for the other runners and vibey), test suite and gates
(ADR-0022). The old sibling GitHub repositories are gone; the PyPI names are
unchanged.

## The six-phase model

```
INTAKE → ① DESIGN → [optional VISUAL_DESIGN] → ② BUILD ⇄ ③ REVIEW

③ REVIEW ── user declines deployment ────────────────→ DONE (local)
       │ user opts into deployment
       ▼
④ DEPLOY_DESIGN → ⑤ DEPLOY_EXECUTE → ⑥ DEPLOY_REVIEW → DONE (deployed)
   interactive       autonomous          interactive
```

Phases ①, ③, ④, ⑥ and the optional VISUAL_DESIGN stage talk to you. Phases ②
and ⑤ run unattended. The deployment stage set (④–⑥) is entered only after
explicit opt-in; declining deployment records a successful local completion.

## The queue and engines

- **Queue backend:** PostgreSQL 17, never SQLite. `FOR UPDATE SKIP LOCKED` is
  the reason; see ADR-0002.
- **Engines:** `claudeloop`, `codexloop`, `cursorloop`, and `agyloop` are the
  default paid-engine pool. `qwenloop` is a fifth, default-off local engine
  (`VIBEY_FEATURE_QWENLOOP` or `[features] qwenloop = true`; ADR-0015 records
  which switch reaches which command). In BUILD rotation it is a standby,
  considered only when enabled and no eligible paid engine is available. For
  DESIGN it is the sovereign provider (`vibey worker --provider qwenloop` →
  `QwenloopDesignProvider`, ADR-0027), which sub-doctrine 8.a makes the preferred
  path, not the fallback.
- **Rotation:** `domain/rotation.py::select()` implements smooth-weighted
  round-robin selection (ADR-0005) and is wired in production: `bootstrap.py`
  builds `EngineSelector`, and BUILD jobs pick their engine per job through
  `SelectingEngineProvider` → `EngineSelector`.
- **Handoff:** when an engine hits `CreditsExhausted`, vibey produces a
  `HandoffBrief`, verifies it against the no-loss gate, and seeds the next
  engine. The full ledger is always written to disk inside the receiving
  worktree.

## Commands worth memorizing

```bash
# CI job `uv-lock` (runs first)
uv lock --check

# CI job `gates`: the 7-gate sweep over src/vibey (Postgres 17 service)
uv sync --extra dev
uv run ruff check .
uv run ruff format --check .
uv run mypy --strict src/vibey

# Single test run with coverage, then per-layer 100% gates
uv run pytest -q -p no:cacheprovider --cov=vibey --cov-branch --cov-report=
uv run coverage report --include='src/vibey/domain/*' --fail-under=100
uv run coverage report --include='src/vibey/application/*' --fail-under=100
uv run coverage report --include='src/vibey/infrastructure/*' --fail-under=100
uv run coverage report --include='src/vibey/cli/*' --fail-under=100

uv run lint-imports
uv run bandit -q -r src/vibey
uv run pip-audit

# CI job `tools`: each tool's own suite, plain pip, on its Python floor and newer
(cd src/vibey_tools/gh && pip install -e ".[dev]" && python -m pytest -q)
(cd src/vibey_tools/skills && pip install -e . && python3 tools/validate_manifests.py && python3 tools/check_links.py && PYTHONPATH=src python3 -m unittest discover -s tests)
(cd src/vibey_tools/bootstrap && pip install -e ".[test,all]" && pytest test/ -m "not integration" --cov=vibey_bootstrap --cov-report=term)

# CI job `tools-lint`: vibey-gh's own linters
(cd src/vibey_tools/gh && python -m black --check vibey_gh test && isort --check-only vibey_gh test && python -m mypy vibey_gh)
```

CI (`.github/workflows/ci.yml`) also runs `image` (amd64 and arm64 builds with
four image contracts) and `cluster-smoke` (Helm install on minikube with four
cluster contracts). `tools-lint` additionally checks that vibey-gh's managed
automation has no drift.

## Where to go for everything else

| Need | Go to |
|---|---|
| How to work on any specific part of this codebase | `.claude/skills/`, `.cursor/rules/`, `.agents/skills/`, `.agent/rules/` |
| Comprehensive architecture diagram (layers, phases, data flow, security boundary, release channels) | `docs/project.mmd` |
| The formal model: ledger invariant, queue semantics, gate soundness | The research paper — source `docs/paper.md`; published at https://the-vibey-project.github.io/vibey/main/paper/ and https://the-vibey-project.github.io/vibey/main/paper.pdf |
| The whole documentation, offline, in reading order | The book — https://the-vibey-project.github.io/vibey/main/book.pdf · https://the-vibey-project.github.io/vibey/main/book.epub · https://the-vibey-project.github.io/vibey/main/book-print.html (built from `properdocs.yml` nav on every release) |
| The governing law: the Twelve Doctrines, sub-doctrines, the Constitution | `src/vibey_tools/gh/docs/doctrines.md`, `constitution.md` (index: `corpus-index.json`) |
| Every CLI command, subcommand, flag, default | `docs/reference/cli.md` |
| Full `vibey.toml` schema | `docs/reference/configuration.md` |
| Full architecture | `docs/plans/architecture-and-roadmap.md` |
| Domain model | `docs/plans/domain-model.md` |
| Data model | `docs/plans/data-model.md` |
| Handoff protocol | `docs/plans/handoff-protocol.md` |
| Rotation & engines | `docs/plans/rotation-and-engines.md` |
| Phase protocols | `docs/plans/phase-protocols.md` |
| Implementation plan | `docs/plans/implementation-plan.md` |
| System design and why each hard call was made | `docs/architecture/decisions/` (34 ADRs) |
| User-facing docs | `README.md` Quickstart, `docs/guides/` |
| Expansion workstreams (JIRA, clouds, k8s, clients, …) | `docs/runbooks/expansion/` (21 runbooks, `00-master-plan.md` first) |
| Contribution workflow, hooks, branch flow, PR expectations | `CONTRIBUTING.md` |
| Security policy and disclosure | `SECURITY.md` |

**Maintenance:** when procedural guidance changes, update Claude skills,
Cursor rules, Codex skills, and Antigravity rules in the **same PR**.

<!-- vibey:begin -->
This section is generated by vibey. Do not edit inside these markers --
changes here are overwritten on the next provisioning run.

## Non-negotiables

- None

## Skill plugins

none

## Full context

See .vibey/context/ for the accepted spec, acceptance criteria, NFRs, decisions, and open items.
<!-- vibey:end -->
