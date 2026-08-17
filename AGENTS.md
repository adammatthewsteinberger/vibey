# AGENTS.md

`vibey`: a queue-based, six-phase conductor for autonomous software delivery.
Built on PostgreSQL and the `*loop` autonomous session runners (claudeloop,
codexloop, cursorloop, agyloop). It orchestrates design → build → review with
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
- **`domain/` stays pure.** Stdlib only, no I/O, no async, no third-party
  imports — enforced by `import-linter` in CI, not convention.
- **The handoff no-loss gate is not negotiable.** A handoff that fails the
  gate is a retry, an escalation to full-transcript mode, or a human gate —
  never a silent partial.
- **Every job is idempotent under replay.** Workers die; the lease expires
  and another worker picks it up.
- **The ledger is append-only.** No updates, no deletes. Corrections are new
  events that supersede prior ones.
- **Every commit follows Conventional Commits.** Enforced by a pre-commit hook.
- **Never implement on `main`.** Feature PRs squash into `develop`; `develop`
  merge-commits into `main`.

## Layer map

```
domain → application → infrastructure → cli, tui
                                  ▲
                          bootstrap.py
                   (the sole composition root)
```

Dependencies point inward only, enforced by `import-linter` in CI. Every layer
carries a **100% branch coverage floor** enforced in CI as four separate gates:
`domain/`, `application/`, `infrastructure/`, `cli/` each fail the build under
100%.

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

- **Queue backend:** PostgreSQL, never SQLite. `FOR UPDATE SKIP LOCKED` is
  the reason; see ADR-0002.
- **Engines:** `claudeloop`, `codexloop`, `cursorloop`, `agyloop` — four
  autonomous session runners that vibey orchestrates via round-robin rotation.
- **Handoff:** when an engine hits `CreditsExhausted`, vibey produces a
  `HandoffBrief`, verifies it against the no-loss gate, and seeds the next
  engine. The full ledger is always written to disk inside the receiving
  worktree.

## Commands worth memorizing

```bash
# Full 7-gate CI sweep
uv run ruff check .
uv run ruff format --check .
uv run mypy --strict src/vibey

# Per-layer 100% coverage gates
uv run pytest -q -p no:cacheprovider --cov=vibey.domain --cov-branch --cov-fail-under=100
uv run pytest -q -p no:cacheprovider --cov=vibey.application --cov-branch --cov-fail-under=100
uv run pytest -q -p no:cacheprovider --cov=vibey.infrastructure --cov-branch --cov-fail-under=100
uv run pytest -q -p no:cacheprovider --cov=vibey.cli --cov-branch --cov-fail-under=100

uv run lint-imports
uv run bandit -q -r src/vibey
uv run pip-audit
```

## Where to go for everything else

| Need | Go to |
|---|---|
| How to work on any specific part of this codebase | `.claude/skills/`, `.cursor/rules/`, `.agents/skills/`, `.agent/rules/` |
| System design and why each hard call was made | `docs/architecture/decisions/` (14 ADRs) |
| Full architecture | `docs/plans/architecture-and-roadmap.md` |
| Domain model | `docs/plans/domain-model.md` |
| Data model | `docs/plans/data-model.md` |
| Handoff protocol | `docs/plans/handoff-protocol.md` |
| Rotation & engines | `docs/plans/rotation-and-engines.md` |
| Phase protocols | `docs/plans/phase-protocols.md` |
| Implementation plan | `docs/plans/implementation-plan.md` |
| User-facing docs | `docs/getting-started/`, `docs/guides/` |

**Maintenance:** when procedural guidance changes, update Claude skills,
Cursor rules, Codex skills, and Antigravity rules in the **same PR**.
