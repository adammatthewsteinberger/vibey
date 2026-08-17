# codexloop — bring agent-facing documentation up to fleet parity

You are working unattended in a disposable git worktree of `codexloop`
(`~/git/codexloop`), on branch `chore/agent-docs`. `codexloop` has no
`--cwd` on most commands yet (a separate, already-tracked gap) — stay in
your worktree's directory and never `cd` out of it.

This is a real, mature codebase — 100% branch-covered on all four
architectural layers, CI-gated. Do not weaken any gate, delete a test, or
add a coverage exclusion to get to green. This task is documentation-only:
you should not need to touch `src/` or `tests/` at all.

## Why this task exists

`codexloop`'s agent-facing docs are the thinnest in the fleet. Compare:

- `AGENTS.md` is 10 lines, `CLAUDE.md` is 5 lines — both far shorter than
  the ~55-60 line files in `~/git/claudeloop`, `~/git/cursorloop`,
  `~/git/agyloop`.
- No `GEMINI.md` at all (claudeloop and cursorloop are also missing this
  one — that's tracked separately for them — but codexloop should get one
  as part of this task regardless).
- Only **one** skill/rule exists — `codexloop-run` — versus 8-9 in each
  sibling repo. There is no architecture, testing, releasing,
  quality-gates, domain-model, docs, or agent-integration skill at all.
- No `.agent/` directory (only `~/git/agyloop` has this so far; also being
  added there and to the other repos as part of the same fleet-wide
  effort — add it here too).

## What to build, and the reference pattern

**Read the sibling repos' patterns first, as a quality bar, not a
template to copy verbatim** — codexloop drives OpenAI Codex, not Claude or
Gemini/Antigravity, and its own domain concepts (QuotaExhausted, body-first
classification, the `codexloop api` generated-REST surface + drift gate,
app-server vs exec transport) are what actually need documenting, not a
reskin of another repo's topics:

- `~/git/agyloop/AGENTS.md`, `CLAUDE.md`, `GEMINI.md` — the fullest
  example of the three-file pattern (facts only, pointer table at the
  bottom, a short "maintenance" note). `AGENTS.md`/`CLAUDE.md` are
  near-twins; `GEMINI.md` is written with different emphasis for a
  different agent's context budget, not a mechanical copy — write
  codexloop's `GEMINI.md` with that same spirit.
- `~/git/agyloop/.claude/skills/*/SKILL.md` — frontmatter shape
  (`name`, `description`, `allowed-tools`), short and procedural.
- `~/git/cursorloop/.claude/skills/` — proof that the topic set should be
  domain-specific, not templated: cursorloop's 8 skills
  (capacity-taxonomy, doctor, control-plane, autonomous-run, testing,
  never-block, model-profiles, completion) reflect cursorloop's own
  domain, not a copy of agyloop's list. **Pick codexloop's own topics**
  by reading its actual code and docs.

Strong candidates for codexloop's skill topics, verify each is real
before writing it up — read the actual source, don't guess from the
names: architecture (onion layers, import-linter contract — confirm the
exact forbidden-import rules, `pyproject.toml` bans `anthropic`/
`claude-agent-sdk`/`claudeloop` per the existing `AGENTS.md` line, is
`fastapi` also banned per the domain-purity contract found earlier in this
fleet's own audit work — check `pyproject.toml`'s forbidden-modules list
directly), testing (the per-layer 100% floors, the codex shim fakes —
`tests/shim/fake_codex.py` + `fake_appserver.py`, genuinely the only
executable-process fakes in the fleet, worth documenting well since
they're a good pattern other repos could learn from), quota-and-capacity
(`QuotaExhausted` has no reset field, body-first classification — what
does that actually mean, read `domain/classify.py` or wherever it lives),
completion-detection (own-line marker matching — `domain/completion.py`,
`_marker_on_own_line`), rest-surface (the generated `codexloop api`
command tree + `api_baseline.json` drift gate — note honestly that this
baselines the *OpenAI SDK's* surface, not codexloop's own, if that's still
accurate per this fleet's own earlier audit), releasing (check
`release-please-config.json`, and honestly note if `publish-testpypi.yml`
still has no test-job gate — don't paper over a known gap), docs.

Build all seven surfaces:

1. **`AGENTS.md`** — expand to the sibling repos' depth and register
   (facts only, not procedures — "how do I" belongs in a skill).
2. **`CLAUDE.md`** — near-twin of `AGENTS.md`.
3. **`GEMINI.md`** — same facts, different agent's emphasis.
4. **`.claude/skills/<topic>/SKILL.md`** — the topic set above, verified
   against real code, one skill per topic.
5. **`.cursor/rules/<topic>.mdc`** — same content, Cursor's format (check
   an agyloop `.mdc` file's frontmatter shape first).
6. **`.agent/rules/<topic>.md`** — same content, Antigravity format
   (agyloop is the only existing example — check its shape carefully).
7. **`.agents/skills/<topic>/`** — mirrors `.claude/skills/`.

Keep the existing `codexloop-run` skill/rule — expand or fold it into
whichever new topic makes sense (probably its own thing, or part of an
"architecture"/"cli" skill) rather than deleting real existing content.

## Accuracy bar

Every claim must be true of codexloop's actual code today. If unsure,
check the source rather than asserting — a wrong fact actively misleads
the next agent more than a missing one does.

## Verification

```bash
uv run pytest -q --cov=codexloop.domain --cov-fail-under=100
uv run pytest -q --cov=codexloop.application --cov-fail-under=100
uv run pytest -q --cov=codexloop.infrastructure --cov-fail-under=100
uv run pytest -q --cov=codexloop.cli --cov-fail-under=100
uv run ruff check . && uv run ruff format --check .
uv run mypy --strict src/codexloop
uv run lint-imports
uv run bandit -q -r src/codexloop
uv run pip-audit
```

Confirm these percentages are identical to before your change (docs-only,
should not move coverage at all). Commit with a Conventional Commit
message, push to `chore/agent-docs`.

Done: **CODEXLOOP_TASK_FULLY_COMPLETE** — only when all seven surfaces
exist, are mutually consistent, cover codexloop's own real domain (not a
reskin of another repo's topics), and are verified accurate.
