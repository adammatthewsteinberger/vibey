# Usage

The console script is `vibey-skills`. `vibe-skills` — the short alias from the
`vibe-engineering-skills` era — still works but prints a one-line deprecation warning and
will be removed in a future release.

## Listing

```bash
vibey-skills list                       # every plugin, its skills, and trigger descriptions
vibey-skills list --plugin azure-cloud-infra
vibey-skills list --json                # machine-readable
```

## Installing

```bash
vibey-skills install --all                        # all 644 skills
vibey-skills install security-principles azure-cloud-infra
vibey-skills install --all --dest ./.claude/skills
vibey-skills install --all --dry-run              # print the plan, touch nothing
vibey-skills install --all --link                 # symlink instead of copy
```

## Conflicts and updates

`install` uses `cp -n` semantics: a destination that already exists is **skipped**, and the
skipped names are printed at the end. This is deliberate — the alternative silently destroys
a skill you edited locally.

```console
$ vibey-skills install --all
vibey-skills: copied 644 skill(s) into /Users/you/.claude/skills

$ vibey-skills install --all
vibey-skills: 644 skill(s) already present, skipped: agile-delivery, ...
vibey-skills: re-run with --force to overwrite
```

To update after a release, overwrite explicitly:

```bash
vibey-skills install --all --force
```

`--link` symlinks instead of copying, so skills track the installed package version and a
`uv tool upgrade` updates them in place.

## Indexing and retrieval

The context engine turns the installed skill library into a searchable index:

```bash
vibey-skills index build --output ~/.vibey-skills-index
vibey-skills index inspect ~/.vibey-skills-index
vibey-skills search "threat modeling" --index ~/.vibey-skills-index --limit 10
vibey-skills packet --request "review a Terraform module" \
    --index ~/.vibey-skills-index --output packet.md --manifest packet.json
vibey-skills evaluate --cases cases.json --index ~/.vibey-skills-index
```

`index build` compiles every `SKILL.md` into a local SQLite index, `search` queries it,
`packet` assembles a budgeted context packet for an agent, and `evaluate` scores
retrieval quality. The full design, hardening notes, and evaluation methodology are in
[the retrieval context engine page](rag-context-engine.md).

## Locating the packaged files

```bash
vibey-skills path          # the packaged plugins/ root
vibey-skills marketplace   # the packaged marketplace.json, for /plugin marketplace add
```

## Programmatic use

```python
from vibey_skills import iter_skills, plugins_root

for skill in iter_skills():
    print(skill.plugin, skill.name, skill.path)
```
