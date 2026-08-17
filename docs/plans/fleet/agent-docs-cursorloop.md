# cursorloop — add the missing CLAUDE.md, GEMINI.md, and .agent/ surfaces

You are working unattended in a disposable git worktree of `cursorloop`
(`~/git/cursorloop`), on branch `chore/agent-docs`. cursorloop has good
`--cwd` coverage — use it wherever a command supports it.

This is a real, mature codebase — 100% branch-covered on all four
architectural layers, CI-gated. Do not weaken any gate, delete a test, or
add a coverage exclusion to get to green. This task is documentation-only:
you should not need to touch `src/` or `tests/` at all.

## Why this task exists

cursorloop is in reasonable shape but has real gaps compared to its
sibling repos (`~/git/claudeloop`, `~/git/codexloop`, `~/git/agyloop`):

- Has `AGENTS.md` (53 lines) and `CURSOR.md` (53 lines, presumably a
  near-twin of `AGENTS.md` — check) but **no `CLAUDE.md`**. Every sibling
  repo that has `AGENTS.md` also has a `CLAUDE.md` near-twin; cursorloop
  is the odd one out.
- **No `GEMINI.md`** (codexloop is also missing this — tracked separately
  for it — but cursorloop should get one as part of this task regardless).
- Has 8 skills in `.claude/skills/` and 8 rules in `.cursor/rules/`
  (capacity-taxonomy, doctor, control-plane, autonomous-run, testing,
  never-block, model-profiles, completion) and 8 files under `.agents/` —
  reasonably complete on that front, **but no `.agent/` directory**
  (Antigravity format — only `~/git/agyloop` has this so far, being added
  fleet-wide as part of this same effort).

## What to build

**Read the sibling repos' patterns first, as a quality bar — cursorloop's
own topic set (capacity-taxonomy, doctor, control-plane, autonomous-run,
never-block, model-profiles, completion, testing) is already good and
domain-specific; don't replace it, just close the format gaps around it:**

1. **`CLAUDE.md`** — read cursorloop's existing `AGENTS.md` and `CURSOR.md`
   first (check exactly how they relate — are they identical, or does
   `CURSOR.md` diverge the way `~/git/agyloop`'s `CLAUDE.md` diverges
   slightly from its `AGENTS.md`?). Write `CLAUDE.md` as the near-twin of
   `AGENTS.md`, following whatever small-diff pattern the sibling repos
   use between their own `AGENTS.md`/`CLAUDE.md` pairs (title line, minor
   pointer-table reordering, a maintenance-note phrasing tweak — check
   `~/git/agyloop`'s actual diff between the two files for the pattern to
   follow, it's small and mechanical).
2. **`GEMINI.md`** — same facts as `AGENTS.md`, different agent's
   emphasis. Look at how `~/git/agyloop/GEMINI.md` diverges from its own
   `AGENTS.md` (denser, an "Auth" section moved up, fewer words per fact)
   and write cursorloop's version with that same spirit — not a mechanical
   copy of agyloop's content, which is Gemini/Antigravity-API-specific and
   doesn't apply to cursorloop (a Cursor Agent runner, not a Gemini one).
   cursorloop's `GEMINI.md` is for an agent *using Gemini as the coding
   model* to orient itself in this codebase, same audience as
   `AGENTS.md`/`CLAUDE.md`, just a different agent.
3. **`.agent/rules/<topic>.md`** — mirror the existing 8
   `.claude/skills/*/SKILL.md` topics (capacity-taxonomy, doctor,
   control-plane, autonomous-run, testing, never-block, model-profiles,
   completion) in the Antigravity rules format. `~/git/agyloop/.agent/rules/`
   is the only existing example in the fleet — check its shape carefully
   (frontmatter, file naming) since you have no second example to
   cross-check against, and note anywhere cursorloop's actual content
   doesn't map cleanly onto agyloop's format so the next repo doing this
   (codexloop, vibey) has real precedent to follow, not just agyloop's.

Do **not** touch the existing `.claude/skills/`, `.cursor/rules/`,
`.agents/`, `AGENTS.md`, or `CURSOR.md` unless you find something in them
that's factually wrong while cross-referencing for `CLAUDE.md`/`GEMINI.md`
— if you do find a real inaccuracy, fix it and say so in the commit
message, but that's a bonus, not the point of this task.

## Accuracy bar

Every claim must be true of cursorloop's actual code today. If unsure,
check the source rather than asserting.

## Verification

```bash
uv run pytest tests --cov=cursorloop.domain --cov-branch --cov-fail-under=100
uv run pytest tests --cov=cursorloop.application --cov-branch --cov-fail-under=100
uv run pytest tests --cov=cursorloop.infrastructure --cov-branch --cov-fail-under=100
uv run pytest tests --cov=cursorloop.cli --cov-branch --cov-fail-under=100
uv run ruff check src tests && uv run ruff format --check src tests
uv run mypy --strict src/cursorloop
uv run lint-imports
uv run bandit -q -r src/cursorloop
uv run pip-audit
```

Confirm these percentages are identical to before your change (docs-only).
Commit with a Conventional Commit message, push to `chore/agent-docs`.

Done: **CURSORLOOP_TASK_FULLY_COMPLETE** — only when `CLAUDE.md`,
`GEMINI.md`, and `.agent/rules/` all exist, are consistent with the
existing `AGENTS.md`/`.claude/skills/` content, and are verified accurate.
