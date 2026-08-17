# vibey — comprehensive agent-facing documentation (from scratch)

You are working unattended in a disposable git worktree of `vibey`
(`~/git/vibey`), on branch `chore/agent-docs`. Pass `--cwd` explicitly to
`run`/`sessions` (the only commands that support it — a separate,
already-tracked gap).

This is a real, mature codebase — 100% branch-covered on all four
architectural layers, CI-gated. Do not weaken any gate, delete a test, or
add a coverage exclusion to get to green. This task is documentation-only:
you should not need to touch `src/` or `tests/` at all. If you find
yourself wanting to, stop and reconsider — the gap this task closes is
agent-facing docs, not code.

## Why this task exists

vibey currently has **none** of the agent-facing documentation surface
that its four sibling repos (`~/git/claudeloop`, `~/git/codexloop`,
`~/git/cursorloop`, `~/git/agyloop`) already have: no `AGENTS.md`, no
`CLAUDE.md`, no `GEMINI.md`, no `.claude/skills/`, no `.cursor/rules/`, no
`.agent/`, no `.agents/`. This is the orchestrator repo of the whole fleet
and the one with the most context-dense architecture (six-phase
conductor, onion layers, Postgres queue, ledger/no-loss gate, engine
rotation) — exactly the kind of repo where an agent picking up a task
cold benefits most from good facts-first orientation.

**Read the sibling repos' patterns first, as a quality bar, not a
template to copy verbatim** — vibey's own architecture and vocabulary are
different (phases not turns, projects not sessions, Postgres queue not a
single-process runner) and the docs must reflect what vibey actually is:

- `~/git/agyloop/AGENTS.md`, `CLAUDE.md`, `GEMINI.md` — the most complete
  set in the fleet. Note `AGENTS.md`/`CLAUDE.md` are near-twins (facts
  only, pointer table to skills/ADRs/docs, "maintenance" note at the
  bottom); `GEMINI.md` is written for a different agent's context budget
  and emphasis, not a mechanical copy.
- `~/git/agyloop/.claude/skills/*/SKILL.md` (8 topics: architecture,
  testing, releasing, quality-gates, domain-model, docs, rest-surface,
  agent-sdk) — read a couple to see the depth/tone: short, frontmatter
  with `name`/`description`/`allowed-tools`, procedural (this is where
  "how do I..." lives, per `AGENTS.md`'s own stated split).
- `~/git/agyloop/.cursor/rules/*.mdc` — same content, Cursor's `.mdc`
  format (check the frontmatter shape, it differs from Claude's).
- `~/git/agyloop/.agent/rules/*.md` — same content again, the Antigravity
  format.
- `~/git/agyloop/.agents/skills/` — mirrors `.claude/skills/`.
- Also skim `~/git/cursorloop/.claude/skills/` — a **completely
  different** topic set (capacity-taxonomy, doctor, control-plane,
  autonomous-run, testing, never-block, model-profiles, completion) that
  reflects cursorloop's own domain instead of a generic template. This is
  the important lesson: **pick vibey's own topics from what actually
  matters in vibey, don't just port agyloop's list.**

## What to build

1. **`AGENTS.md`** (repo root) — facts, not procedures, matching the
   sibling repos' register. Must cover, accurately (verify each claim
   against the real code, don't guess): the onion layer map
   (`domain/ → application/ → infrastructure/ → cli/, tui/`, with
   `bootstrap.py` as composition root), the four hard gates
   (`domain`+`application`+`infrastructure`+`cli` each at 100% branch
   coverage, enforced per-layer in CI — not an aggregate number), the
   7-gate sweep commands, Conventional Commits (check if there's a commit
   hook enforcing it, like the sibling repos), the six-phase model
   (① DESIGN → ② BUILD ⇄ ③ REVIEW, optional VISUAL DESIGN interstitial,
   optional ④–⑥ deployment stage set), the no-loss gate and why it's the
   single most safety-critical invariant (`domain/noloss.py`,
   `CreditsExhausted` having no `resets_at` — this exact invariant is
   enforced at three independent layers per `HANDOFF.md`, cite that if
   still accurate), Postgres as the queue backend (never SQLite, `FOR
   UPDATE SKIP LOCKED`), and a pointer table to skills/ADRs/docs mirroring
   the sibling repos' format. Read `README.md`,
   `docs/plans/architecture-and-roadmap.md`, `docs/plans/domain-model.md`,
   and the ADR index in `docs/architecture/decisions/` before writing a
   word — this file's job is to compress the real architecture, not
   invent one.
2. **`CLAUDE.md`** — near-twin of `AGENTS.md`, adjust only what the
   sibling repos adjust between their own pairs (check the diffs, they're
   small: title line, the pointer-table ordering, the maintenance note's
   phrasing).
3. **`GEMINI.md`** — same facts, different agent, different emphasis —
   look at how agyloop's `GEMINI.md` diverges from its `AGENTS.md` (denser,
   fewer words per fact, an "Auth" section specific to what a Gemini-driven
   agent needs to know first) and write vibey's own version with that
   spirit, not that content.
4. **`.claude/skills/<topic>/SKILL.md`** — pick vibey's own topic set by
   reading the codebase and identifying what an agent actually needs
   procedural guidance for. Strong candidates, verify each is real before
   writing it up: architecture (onion + import-linter contract, where new
   code goes), testing (the 100%-per-layer gate, Postgres-required
   integration tests, the chaos test and no-loss property suite being
   *protected* per `implementation-plan.md`'s "Bootstrapping" section —
   this is a real, load-bearing fact worth its own skill or a strong
   callout), releasing (check `release-please-config.json` and
   `.github/workflows/release-please.yml`, `publish-to-pypi.yml` — note
   honestly if the publish workflow has no test gate, that's a real,
   already-tracked gap elsewhere, don't paper over it here), domain-model
   (phases, jobs, ledger, handoff, rotation — `docs/plans/domain-model.md`
   is your source), engine-adapters (how vibey drives the four `*loop`
   binaries — `LoopProcessAdapter`, `build_argv`, the `--run-id`
   requirement if that fix has landed by the time you do this — check),
   quality-gates (the 7-gate sweep, what each one catches). Match the
   sibling skills' frontmatter shape exactly (`name`, `description`,
   `allowed-tools`) and depth (short, procedural, a "why" only where
   non-obvious).
5. **`.cursor/rules/<topic>.mdc`** — same content as each Claude skill,
   Cursor's format. Check an agyloop `.mdc` file's frontmatter shape
   before writing vibey's.
6. **`.agent/rules/<topic>.md`** — same content again, Antigravity format
   (agyloop is currently the only repo with this directory — check its
   shape carefully since you have no second example to cross-check
   against).
7. **`.agents/skills/<topic>/`** — mirrors `.claude/skills/`.

**Consistency requirement, stated explicitly in every sibling repo's
`AGENTS.md`:** when a fact or procedure changes, all four+ trees (Claude,
Cursor, Codex/`.agents`, Antigravity) update together, in the same PR.
Since you're authoring all of them from scratch in this one task, that's
automatically satisfied — just don't let the four renderings of the same
topic drift from each other while you write them.

## Accuracy bar

Every claim in every file must be true of the actual codebase today, not
aspirational or copied from a sibling repo's different architecture. If
you're not sure something is still accurate (e.g., a specific coverage
number, a specific gate command, whether a feature has landed), go check
the source or the CI config rather than asserting it. A wrong fact in an
agent-orientation doc is worse than a missing one — it actively misleads
the next agent that reads it.

## Verification

This is a docs-only change, so the normal 4-layer coverage floors are
unaffected (confirm this — running the gate sweep and seeing identical
percentages to before your change is the proof, not an assumption).
Still run the full sweep for real and confirm nothing broke:

```bash
for L in domain application infrastructure cli; do
  uv run pytest -q -p no:cacheprovider --cov="vibey.$L" --cov-branch --cov-fail-under=100
done
uv run ruff check . && uv run ruff format --check .
uv run mypy --strict src/vibey
uv run lint-imports
uv run bandit -q -r src/vibey
uv run pip-audit
```

If any Claude skill files need YAML frontmatter validation, check whether
`.github/workflows/` in the sibling repos runs a "Claude skill frontmatter"
check (claudeloop's CI has one) — vibey doesn't appear to have this gate
yet, which is fine, just make sure your frontmatter is well-formed anyway
(valid YAML, required keys present) since it'll be added eventually.

Commit with a Conventional Commit message. Push to `chore/agent-docs`.

Done: **CLAUDELOOP_TASK_FULLY_COMPLETE** — only when all seven surfaces
(AGENTS.md, CLAUDE.md, GEMINI.md, `.claude/skills/`, `.cursor/rules/`,
`.agent/rules/`, `.agents/skills/`) exist, are mutually consistent, and
are verified accurate against the real codebase — not estimated.
