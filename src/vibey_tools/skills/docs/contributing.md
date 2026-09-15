# Contributing

The full workflow lives in
[CONTRIBUTING.md](https://github.com/adammatthewsteinberger/vibey-skills/blob/main/CONTRIBUTING.md);
repository conventions and the `SKILL.md` format are in
[CLAUDE.md](https://github.com/adammatthewsteinberger/vibey-skills/blob/main/CLAUDE.md).

## The short version

A plugin is a directory under `plugins/`:

```
plugins/<plugin-name>/
  .claude-plugin/plugin.json    name, version, description, author
  README.md                     overview + skill list
  skills/<skill-name>/SKILL.md  one skill per directory
```

After any change:

1. Bump `version` in that plugin's `.claude-plugin/plugin.json`.
2. Mirror `version`, `description`, and `category` into `.claude-plugin/marketplace.json`.
3. Run the validator — it is stdlib-only, so no setup is needed:

   ```bash
   python3 tools/validate_manifests.py
   python3 tools/check_links.py
   ```

CI runs both, plus `mkdocs build --strict`, which fails on any broken internal doc link.

## What belongs here

Skills must be **generally useful and vendor-neutral where possible**. Do not contribute
material specific to one organisation's internal systems: no internal hostnames, service
names, project codenames, resource identifiers, or findings about a private deployment. If a
skill can only be followed by people inside one company, it belongs in that company's own
private marketplace instead.

Documentation links must be **absolute** in the root Markdown files, because PyPI renders
`README.md` against its own project URL and relative links break there. Inside `docs/`, use
relative links so `mkdocs build --strict` can verify them.

## Building the docs

```bash
pip install -e ".[docs]"
mkdocs serve
```

The [Skills reference](reference/index.md) is generated from `plugins/**` at build time by
`docs/gen_reference.py` — never edit those pages directly; edit the `SKILL.md` they come from.
