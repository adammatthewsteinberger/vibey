# claudeloop — add the missing GEMINI.md and .agent/ surfaces

You are working unattended in a disposable git worktree of `claudeloop`
(`~/git/claudeloop`), on branch `chore/agent-docs`. Pass `--cwd`
explicitly wherever it exists (`run`, `sessions`, and whatever else has
landed via the separately-tracked guardrails work by the time you run
this — check `claudeloop --help` per-subcommand rather than assuming).

This is a real, mature codebase — 100% branch-covered on all four
architectural layers, CI-gated. Do not weaken any gate, delete a test, or
add a coverage exclusion to get to green. This task is documentation-only:
you should not need to touch `src/` or `tests/` at all.

## Why this task exists

claudeloop is the fleet's reference implementation for most things and
its agent docs are already solid: `AGENTS.md` and `CLAUDE.md` (62 lines
each, near-twins), 8 skills in `.claude/skills/`, 9 rules in
`.cursor/rules/`, 8 files under `.agents/`. Two real gaps remain:

- **No `GEMINI.md`** — cursorloop and codexloop are also missing this,
  tracked separately for them; claudeloop should get one as part of this
  same fleet-wide effort.
- **No `.agent/` directory** (Antigravity rules format) — only
  `~/git/agyloop` has this so far, being added across the fleet as part
  of this same effort.

## What to build

1. **`GEMINI.md`** — same facts as `AGENTS.md`/`CLAUDE.md`, different
   agent's emphasis. Look at how `~/git/agyloop/GEMINI.md` diverges from
   its own `AGENTS.md` (denser, fewer words per fact, an "Auth" section
   moved up front since that's what a Gemini-driven agent needs to
   resolve first) and write claudeloop's version with that same spirit —
   not a copy of agyloop's content, which is specific to the Google
   Antigravity/Gemini API surface agyloop wraps and doesn't apply to
   claudeloop (a Claude Agent SDK runner). claudeloop's `GEMINI.md` is for
   an agent *using Gemini as the coding model* to orient itself in this
   codebase — same audience as `AGENTS.md`/`CLAUDE.md`, different agent.
   Read claudeloop's own `AGENTS.md`/`CLAUDE.md` and the real source
   (onion layers, the CLAUDE_CODE_RETRY_WATCHDOG note, `bypassPermissions`
   default, the `--wind-down-at`/`--cwd` guardrails work if landed by the
   time you do this) rather than inventing facts.
2. **`.agent/rules/<topic>.md`** — mirror the existing 8
   `.claude/skills/*/SKILL.md` topics (rest-surface, agent-sdk,
   architecture, domain-model, docs, releasing, quality-gates, testing) in
   the Antigravity rules format. `~/git/agyloop/.agent/rules/` is the only
   existing example in the fleet — check its shape carefully (frontmatter,
   file naming, how procedural content is structured there vs in a Claude
   `SKILL.md`) since you have no second example to cross-check against.

Do **not** touch the existing `AGENTS.md`, `CLAUDE.md`, `.claude/skills/`,
`.cursor/rules/`, or `.agents/` unless you find a real, factual
inaccuracy while cross-referencing them to write `GEMINI.md` — if so, fix
it and say so in the commit message, but that's a bonus, not the point.

## Accuracy bar

Every claim must be true of claudeloop's actual code today. If unsure,
check the source rather than asserting.

## Verification

```bash
for L in domain application infrastructure cli; do
  uv run pytest tests/$L --cov="claudeloop.$L" --cov-branch --cov-report=term-missing --cov-fail-under=100
done
uv run ruff check . && uv run ruff format --check .
uv run mypy --strict src/claudeloop
uv run lint-imports
uv run bandit -q -r src/claudeloop
uv run pip-audit
```

Confirm these percentages are identical to before your change (docs-only).
If a "Claude skill frontmatter" CI check exists (it does, per
`.github/workflows/`), make sure your new `.claude/skills/` entries — if
you add any beyond `GEMINI.md`/`.agent/` — pass it; you're not adding new
Claude skills in this task, so this should be a non-issue, but verify.
Commit with a Conventional Commit message, push to `chore/agent-docs`.

Done: **CLAUDELOOP_TASK_FULLY_COMPLETE** — only when `GEMINI.md` and
`.agent/rules/` both exist, are consistent with the existing
`AGENTS.md`/`CLAUDE.md`/`.claude/skills/` content, and are verified
accurate.
