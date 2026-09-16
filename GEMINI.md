# GEMINI.md

`vibey`: a queue-based, six-phase conductor for autonomous software delivery.
Orchestrates claudeloop, codexloop, cursorloop, and agyloop (plus opt-in local
qwenloop) via PostgreSQL queue with lossless handoff. All five runners live in
this repository under `src/vibey_runners/`. Facts only —
procedures live in `.agent/rules/`
(mirrors of `.claude/skills/` and `.cursor/rules/`).

## Non-negotiables

- Never block on a human. `ask_question` equivalent is a parked job, not
  stdin.
- Credits ≠ rate-limit window. `CreditsExhausted` has no `resets_at` —
  enforced by type, property test, and DB CHECK constraint.
- `domain/` stays pure: no I/O, no async, no clock, no network
  (`tests/domain/test_domain_purity.py`, AST walk). Imports: stdlib, itself, and
  dependency-free family packages only (`vibey-gh`, `vibey-skills`,
  `vibey-runners-common`); `vibey_bootstrap` forbidden by name (Azure SDK,
  OpenTelemetry) — use it from `infrastructure/`. `import-linter` enforces.
  ADR-0017.
- Dogfood the family. If the family ships a capability, use it; a second
  implementation needs a written capability-gap reason at the call site, and
  the fix is to add it to ours. ADR-0017; sub-doctrine 10.e.
- Everything-as-code, never less generic. Declare it in the repo and reconcile
  from it — no settings page, no one-off `gh api`. Never change anything to a
  less generic or less configurable state. ADR-0018; sub-doctrine 12.c.
- A governing rule is a ratified sub-doctrine, or it is not a rule. File it
  under one of the sealed Twelve in `src/vibey_tools/gh/docs/doctrines.md`,
  ratified by the operator's merge. An ADR records the decision; the canon
  records the law. ADR-0020.
- Code lives in classes, each with an interface beside it
  (`services/x.py` → `services/interfaces/x_interface.py`). Module-level
  functions are last resort with a written reason. Interfaces declare, never
  consume. New and changed code from 2026-09-15. ADR-0016; sub-doctrine 9.b.
- Capacity rejection outranks a completion claim.
- No-loss handoff gate is not negotiable. Failed gate → retry, escalation to
  full-transcript mode, or human gate — never silent partial.
- Every job is idempotent under replay.
- Ledger is append-only.
- Conventional Commits enforced by pre-commit hook.
- Never implement on `main`. PRs squash into `develop` via the merge train
  (`vibey-gh merge-train`); `vibey-gh promote` rebase-merges `develop` into
  `main` (linear history). `develop` → TestPyPI `vibey-dev`; `main` → PyPI.
  ADR-0028.

## Layer map

```
domain → application → infrastructure → cli, tui
                                  ▲
                          bootstrap.py
```

Dependencies point inward. `import-linter` enforces. Four of the five layers
(all but `tui/`) carry a 100% branch coverage floor — separate CI gates for
domain, application, infrastructure, cli. ADR-0023.

Map covers `src/vibey` only. The repo is a uv workspace (ADR-0021) whose other
tenants keep their own pyproject, version, Python floor, tests and gates
(ADR-0022): `src/vibey_runners/{claude,codex,cursor,agy,qwen,common}`
(claudeloop, codexloop, cursorloop, agyloop, qwenloop, vibey-runners-common) and
`src/vibey_tools/{gh,skills,bootstrap}` (vibey-gh, vibey-skills,
vibey-bootstrap). Sibling GitHub repos are gone; PyPI names unchanged.

## Queue and engines

- **Queue:** PostgreSQL 17, never SQLite (`FOR UPDATE SKIP LOCKED`, ADR-0002).
- **Engines:** claudeloop, codexloop, cursorloop, agyloop — the paid pool,
  rotated per BUILD job via smooth weighted round robin
  (`SelectingEngineProvider` → `EngineSelector` → `domain/rotation.select()`,
  ADR-0005). `qwenloop` is a fifth, default-off local engine
  (`VIBEY_FEATURE_QWENLOOP` or `[features] qwenloop`). In BUILD rotation it is a
  standby, considered only when enabled and no eligible paid engine is
  available (ADR-0015). For DESIGN it is the sovereign provider
  (`vibey worker --provider qwenloop`, ADR-0027), the preferred path under
  sub-doctrine 8.a.
- **Handoff:** when `CreditsExhausted`, vibey verifies brief against no-loss
  gate (10 rules: R1–R10), writes full ledger to receiving worktree, seeds
  next engine.

## Phases

Six phases plus optional visual interstitial: INTAKE → ① DESIGN → [VISUAL_DESIGN] →
② BUILD ⇄ ③ REVIEW. After ③: deployment opt-in → ④ DEPLOY_DESIGN → ⑤ DEPLOY_EXECUTE →
⑥ DEPLOY_REVIEW → DONE(deployed); or deployment opt-out → DONE(local).
Interactive: ①, ③, ④, ⑥, VISUAL_DESIGN. Autonomous: ②, ⑤.

## Commands

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

## Surfaces

| Need | Go to |
|---|---|
| Procedures | `.agent/rules/`, `.claude/skills/`, `.cursor/rules/`, `.agents/skills/` |
| Comprehensive architecture diagram | `docs/project.mmd` |
| Formal model (research paper) | `docs/paper.md` — https://the-vibey-project.github.io/vibey/main/paper/ · https://the-vibey-project.github.io/vibey/main/paper.pdf |
| Documentation as a book | https://the-vibey-project.github.io/vibey/main/book.pdf · https://the-vibey-project.github.io/vibey/main/book.epub · https://the-vibey-project.github.io/vibey/main/book-print.html |
| Governing law (doctrines, constitution) | `src/vibey_tools/gh/docs/doctrines.md` |
| CLI reference | `docs/reference/cli.md` |
| `vibey.toml` schema reference | `docs/reference/configuration.md` |
| Architecture | `docs/plans/architecture-and-roadmap.md` |
| Domain model | `docs/plans/domain-model.md` |
| Handoff protocol | `docs/plans/handoff-protocol.md` |
| Rotation & engines | `docs/plans/rotation-and-engines.md` |
| Data model | `docs/plans/data-model.md` |
| Phase protocols | `docs/plans/phase-protocols.md` |
| Implementation plan | `docs/plans/implementation-plan.md` |
| ADRs | `docs/architecture/decisions/` (34 ADRs: 0001–0034) |
| User-facing docs | `README.md` Quickstart, `docs/guides/` |
| Expansion runbooks | `docs/runbooks/expansion/` (21 runbooks, `00-master-plan.md` first) |
| Contribution workflow, hooks, branch flow, PR expectations | `CONTRIBUTING.md` |
| Security policy and disclosure | `SECURITY.md` |

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
