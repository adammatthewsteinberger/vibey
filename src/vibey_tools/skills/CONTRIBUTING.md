# Contributing to vibey-skills

> Read [CLAUDE.md](https://github.com/adammatthewsteinberger/vibey-skills/blob/main/CLAUDE.md) before making changes. It is the governing convention for this
> repository and takes precedence over this document wherever they overlap.

This repository is a **Claude Code plugin marketplace**: 127 plugins composed of 644 Agent
Skills. The application code is a packaging CLI plus a retrieval context engine — nearly every contribution
is Markdown (skill content) and JSON (manifests). "Correct" means valid manifests and
accurate, well-triggered skill content.

Contributions are welcome. By submitting a pull request you agree that your contribution is
licensed under the same [MIT License](https://github.com/adammatthewsteinberger/vibey-skills/blob/main/LICENSE) that covers this project — inbound licensing
matches outbound, with no separate CLA to sign.

Questions, bug reports, and proposals all go through
[GitHub issues](https://github.com/adammatthewsteinberger/vibey-skills/issues). For
suspected security issues, see [SECURITY.md](https://github.com/adammatthewsteinberger/vibey-skills/blob/main/SECURITY.md) instead. Participation is governed
by our [Code of Conduct](https://github.com/adammatthewsteinberger/vibey-skills/blob/main/CODE_OF_CONDUCT.md).

---

## The fingerprint

Every code change carries it, and CI enforces it. Source files in `tools/`, `src/`,
`docs/*.py` and `.github/workflows/` take a header comment; **every commit** takes a
`Made-With:` trailer, which covers the changes that cannot hold a comment.

```bash
pip install "vibey-gh==1.56.0"   # or: pip install -e ".[dev]"
vibey-gh install                 # writes the hooks and points core.hooksPath at them
vibey-gh check --apply           # adds missing headers
```

## Branching

`feature/*` -> `develop` -> `main`. Work on a `feature/*` branch and open a pull
request into `develop`; never commit to `develop` directly.

`feature/* -> develop` is **squash**-merged and `develop -> main` is **rebase**-merged,
always and only — both enforced by the branch rulesets. Pushes to `develop` publish to
TestPyPI, pushes to `main` publish to PyPI, and `develop` is realigned to `main`
automatically after a release. Do not realign or back-merge by hand.

Two weekly trains move work along on Mondays: `merge-train.yml` squash-merges
ready pull requests into `develop`, and `promote-to-main.yml` rebase-merges `develop`
into `main` when their contents differ.

## Table of contents

1. [Repository layout](#1-repository-layout)
2. [Source of truth](#2-source-of-truth)
3. [Anatomy of a plugin](#3-anatomy-of-a-plugin)
4. [Writing a SKILL.md](#4-writing-a-skillmd)
5. [Common tasks](#5-common-tasks)
6. [Validation](#6-validation)
7. [Conventions](#7-conventions)

---

## 1. Repository layout

```
.claude-plugin/marketplace.json   Marketplace manifest (the entry point Claude Code reads)
plugins/                          Authoritative plugin sources, one directory per plugin
  <plugin>/.claude-plugin/plugin.json   Plugin manifest
  <plugin>/README.md                    Plugin overview + skill list
  <plugin>/skills/<skill>/SKILL.md      Individual skill definition
src/vibey_skills/                 Python package + `vibey-skills` CLI
tools/validate_manifests.py       Manifest and skill-frontmatter validator
README.md / CLAUDE.md             Overview + Claude Code conventions
.cursor/rules/claude.mdc          Cursor rules (aliases CLAUDE.md)
```

## 2. Source of truth

- `plugins/` is the **only** source of truth for skill content. Edit skills there.
- `.claude-plugin/marketplace.json` is the manifest Claude Code reads when the repo is added
  with `/plugin marketplace add`. Each entry's `source` points at a directory under `plugins/`.
- The Python wheel *maps in* `plugins/` rather than holding a second copy, so there is never a
  duplicate of a skill to keep in sync.

## 3. Anatomy of a plugin

```
plugins/<plugin-name>/
  .claude-plugin/plugin.json    Manifest: name, version, description, author
  README.md                     Human overview + a bullet per skill
  skills/<skill-name>/SKILL.md  One skill per directory
```

`plugin.json`:

```json
{
  "name": "agile-delivery",
  "version": "0.1.0",
  "description": "Agile Delivery: …",
  "author": { "name": "Adam Matthew Steinberger", "email": "adam@matthewsteinberger.com" }
}
```

`name` must match the directory name **and** the `name`/`source` in
`.claude-plugin/marketplace.json`.

## 4. Writing a SKILL.md

A skill is a single `SKILL.md`: YAML frontmatter, then a Markdown body.

```markdown
---
name: delivery-velocity
description: Use when … Triggers on … Also triggers on …
---

# Delivery Velocity

<body>
```

- `name` (required) — kebab-case, matches the skill directory name.
- `description` (required) — **the trigger**. It is the only text Claude sees when deciding
  whether to load the skill, so write it as "Use when …" plus concrete trigger phrases:
  the tasks, tools, and terms that should activate it. Be specific; vague descriptions
  either over-trigger or never fire.
- Body — keep it self-contained and evidence-grounded. Cite sources for factual claims.

Skills should be generally useful. Do not contribute content that documents a specific
organization's internal systems, hostnames, ticket IDs, or personnel — anything that would
only make sense inside one company belongs in a private marketplace, not this one.

## 5. Common tasks

### Edit an existing skill

1. Edit `plugins/<plugin>/skills/<skill>/SKILL.md`.
2. Bump `version` in `plugins/<plugin>/.claude-plugin/plugin.json`.
3. Mirror `version`, `description`, and `category` into the matching entry in
   `.claude-plugin/marketplace.json`.
4. Update `plugins/<plugin>/README.md` if the skill's summary changed.

### Add a skill to a plugin

1. Create `plugins/<plugin>/skills/<new-skill>/SKILL.md`.
2. Add a bullet for it in `plugins/<plugin>/README.md`.
3. Bump the plugin `version` and mirror it into `.claude-plugin/marketplace.json`.
4. Update the skill count and summary for that plugin in the root [README.md](https://github.com/adammatthewsteinberger/vibey-skills/blob/main/README.md) table.

### Add a new plugin

1. Create `plugins/<plugin>/` with `.claude-plugin/plugin.json`, `README.md`, and at least
   one skill under `skills/`.
2. Add a plugin entry to `.claude-plugin/marketplace.json` with `name`, `source`
   (`./plugins/<plugin>`), `description`, `version`, `category`, and `author`.
3. Add a row to the plugin table in the root [README.md](https://github.com/adammatthewsteinberger/vibey-skills/blob/main/README.md).

## 6. Validation

Before opening a pull request, run the validator:

```bash
python3 tools/validate_manifests.py
```

It checks that every manifest parses, that each plugin's `name` matches its directory, that
every marketplace `source` resolves, that marketplace and plugin versions agree, that every
`SKILL.md` has frontmatter with a matching `name` and a non-empty `description`, that skill
names are unique marketplace-wide, and that `pyproject.toml`'s version matches
`marketplace.json`'s `metadata.version`. CI runs the same command, plus `uv build` and
`uvx twine check dist/*`.

Also keep these in sync, or installation breaks:

- Each plugin's `name` is identical across its directory name, its `plugin.json`, and its
  `marketplace.json` entry.
- Each `marketplace.json` entry's `version`/`description` match the plugin's `plugin.json`.
- Each plugin `README.md` lists exactly the skills present in its `skills/` directory.
- The root `README.md` plugin table reflects current versions, categories, and skill counts.

## 7. Conventions

- `author` is always `{ "name": "Adam Matthew Steinberger", "email":
  "adam@matthewsteinberger.com" }`, in both
  `plugin.json` and each `marketplace.json` entry, matching `authors`/`maintainers` in
  `pyproject.toml`. The MIT copyright in `LICENSE` is held jointly by **The Vizius Group**
  (where the project was originally developed as `vibe-engineering-skills`) and **Adam
  Matthew Steinberger** — see `NOTICE.md`. Do not add any *other* person's name or email to
  tracked files.
- Plugin and skill names are kebab-case and unique within the marketplace.
- Versioning is per-plugin semver in `plugin.json`. Most plugins are `0.1.0`; revised ones
  are `0.2.0`. Bump the version whenever a plugin's skills change.
- The package version in `pyproject.toml` (single-sourced from
  `src/vibey_skills/__init__.py`) must equal `marketplace.json`'s
  `metadata.version`.

---

*Questions? Check [CLAUDE.md](https://github.com/adammatthewsteinberger/vibey-skills/blob/main/CLAUDE.md) first, then
[open a GitHub issue](https://github.com/adammatthewsteinberger/vibey-skills/issues/new).*
