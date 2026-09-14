# Writing and building documentation

## Where content belongs

| Content | Goes in |
|---|---|
| An always-true fact, cheap to state, that every session needs | `CLAUDE.md` and `AGENTS.md` (kept deliberately short — see below) |
| A procedure for working on a specific part of this codebase | `.claude/skills/<name>/SKILL.md` **mirrored to** `.cursor/rules/<name>.mdc` **and** `.agents/skills/<name>/SKILL.md` |
| User-facing "how do I..." | `docs/getting-started/` or `docs/guides/` |
| System design that explains *what* exists and *how the pieces fit* | `docs/architecture/` |
| The *reasoning* behind one specific hard decision, preserved for posterity | `docs/architecture/decisions/` (an ADR) |
| Generated API documentation | `docs/reference/api.md`, via `mkdocstrings` — don't hand-write type signatures that already exist as docstrings |
| Contributor process | `docs/contributing/` |
| Historical plans, kept verbatim once superseded by living docs | `docs/plans/` |

The dividing line between routers and skills is explicit:
**`CLAUDE.md` / `AGENTS.md` hold facts; skills/rules hold procedures.**

When procedural guidance changes, update **all three** agent trees in the
same PR: `.claude/skills/`, `.cursor/rules/`, `.agents/skills/`.

## Building the docs site locally

```bash
pip install -e ".[docs]"
mkdocs serve
```

Open `http://127.0.0.1:8000`. Live-reloads on save.

## The strict build CI runs

```bash
mkdocs build --strict
```

`--strict` turns every warning — most commonly a broken internal link, or a
page referenced in `nav:` (in `mkdocs.yml`) that doesn't exist — into a
build failure. Run this locally before opening a PR that touches `docs/`;
it's exactly what `docs.yml` runs in CI, so a strict-build failure there
means it would have failed for you too.

## Writing style for this project's docs

- **Plain markdown, no docs-only syntax beyond what's in `mkdocs.yml`'s
  `markdown_extensions`** (admonitions, code fences, tables). Every page
  should read correctly as plain text on GitHub, since `CLAUDE.md` and the
  skills link directly to file paths under `docs/`, not to built site URLs.
- **Link by relative path**, not by absolute site URL, so links work both on
  GitHub and in the built site. **Exception: `README.md` at the repo root**
  is also the PyPI project description — PyPI rewrites relative links under
  `https://pypi.org/project/claudeloop/`, which 404s. Use absolute
  `https://adammatthewsteinberger.github.io/claudeloop/...` and GitHub
  `blob`/`tree` URLs in `README.md` only.
- **State the "why," not just the "what."** A page that only restates what a
  function's signature already says isn't earning its place — the value is
  in explaining the reasoning a stranger can't get from reading the code
  alone. This is exactly what the ADRs in `architecture/decisions/` are for.
- **Mark roadmap content explicitly.** Anything describing a not-yet-built
  milestone should open with an `!!! note "Roadmap"` admonition, so a reader
  never mistakes a design intention for current behavior. Grep the docs tree
  for `!!! note "Roadmap"` to find every page that needs updating as a
  milestone lands.

## Keeping docs honest as milestones land

When a milestone from
[`../plans/architecture-and-roadmap.md`](../plans/architecture-and-roadmap.md)
ships, update every page carrying a `Roadmap` admonition for the feature
that just landed — remove the admonition, correct any command examples that
were aspirational, and add or update the relevant ADR if the implementation
diverged from the original plan.

## GitHub About box (not stored in git)

The repository **Description**, **Website**, and **Topics** live in GitHub
Settings → General, not in this tree. Keep them in lockstep with
`pyproject.toml`:

| Field | Value |
|---|---|
| Description | The `[project].description` string from `pyproject.toml` (GitHub caps this at 350 characters) |
| Website | `https://adammatthewsteinberger.github.io/claudeloop/` |
| Topics | `python`, `cli`, `anthropic`, `claude`, `claude-code`, `llm`, `agent`, `automation`, `mit-license` |
| Default branch | `develop` (contributors PR here; `main` stays the releasable line) |
| Discussions | enabled |
| Wiki | disabled — documentation lives in `docs/` |

Forks that republish should set the same shape on their own repo, pointing
Website at their own docs URL.
