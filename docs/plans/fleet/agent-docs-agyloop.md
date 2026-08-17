# agyloop — accuracy audit of the existing agent-facing documentation

You are working unattended in a disposable git worktree of `agyloop`
(`~/git/agyloop`), on branch `chore/agent-docs`. Pass `--cwd` explicitly
everywhere it exists (agyloop has excellent `--cwd` coverage).

This is a real, mature codebase — 100% branch-covered on all four
architectural layers, CI-gated. Do not weaken any gate, delete a test, or
add a coverage exclusion to get to green. This task is documentation-only:
you should not need to touch `src/` or `tests/` at all.

## Why this task exists

Unlike its four sibling repos, `agyloop` already has all seven
agent-facing documentation surfaces: `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`,
`.claude/skills/` (8 topics), `.cursor/rules/` (9), `.agent/rules/` (9),
`.agents/skills/` (8) — it's the reference the other four repos' equivalent
tasks are using as their quality bar. **This task is not "build the
missing surfaces"** (there aren't any) — it's a deliberate accuracy audit,
since these files are easy to let drift out of date as the real codebase
changes underneath them, and nobody has specifically checked them recently.

## What to do

Read every one of the seven surfaces end to end
(`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, every file under
`.claude/skills/`, `.cursor/rules/`, `.agent/rules/`, `.agents/skills/`)
and cross-check every factual claim against the real, current source:

- Layer map and import-linter contract — does `domain/` still forbid
  exactly what the docs say (check `pyproject.toml`'s forbidden-modules
  list / `.importlinter` config directly, don't trust the doc)?
- Version numbers, command examples, config keys, CLI flag names — do they
  still match `agyloop --help` and the actual source?
- The `CreditsExhausted`-has-no-`resets_at` invariant and any other
  "non-negotiables" — still true, still enforced the way the docs
  describe?
- `docs/architecture/decisions/` references — do the ADR numbers/titles
  cited in the skills still exist and still say what's claimed?
- Anything referencing another repo in the fleet (claudeloop, codexloop,
  cursorloop, vibey) — is the comparison still accurate given those repos
  have been actively changing?
- The four-way consistency the docs themselves demand
  (`AGENTS.md`'s own "maintenance" note: Claude/Cursor/Codex/Antigravity
  trees update together) — do `.claude/skills/`, `.cursor/rules/`,
  `.agent/rules/`, and `.agents/skills/` actually still say the same
  things as each other for each topic, or have they drifted since they
  were written?

Fix whatever you find wrong, drop anything you can't verify rather than
leave a plausible-sounding guess, and add anything genuinely missing that
you notice while doing this pass (a new skill topic only if something
significant has no coverage anywhere — don't manufacture busywork).

## Accuracy bar

Every claim in every file must be true of agyloop's actual code today.
Prefer "verified, fixed N inaccuracies, dropped M stale claims" as your
outcome over "everything already looked fine" unless you genuinely
checked hard and found nothing — a rubber-stamp pass defeats the point
of an audit task.

## Verification

```bash
for L in domain application infrastructure cli; do
  uv run pytest tests --cov="agyloop.$L" --cov-fail-under=100
done
uv run ruff check . && uv run ruff format --check .
uv run mypy --strict src/agyloop
uv run lint-imports
uv run bandit -q -r src/agyloop
uv run pip-audit
uv run mkdocs build --strict
```

Confirm these percentages are identical to before your change (docs-only).
Commit with a Conventional Commit message, push to `chore/agent-docs`.

Done: **AGYLOOP_TASK_FULLY_COMPLETE** — only when you've personally
verified every claim across all seven surfaces against the real source,
fixed what was wrong, and confirmed the four renderings of each topic are
mutually consistent.
