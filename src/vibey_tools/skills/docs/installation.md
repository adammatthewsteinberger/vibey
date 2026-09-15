# Installation

## As a Claude Code marketplace

The native route. Claude Code reads the marketplace manifest and manages plugins for you.

```bash
# From the Git remote
/plugin marketplace add adammatthewsteinberger/vibey-skills

# ...or from a local clone
/plugin marketplace add /path/to/vibey-skills

# Browse, then install what you want
/plugin
/plugin install security-principles@vibey-skills
```

## From PyPI

The same skills ship as a Python package with **no runtime dependencies**, so `uvx` can run
it without a resolution step. Useful when you want the skills in a harness other than
Claude Code, or you would rather not clone.

```bash
# Run without installing
uvx vibey-skills install --all

# ...or install the CLI persistently
uv tool install vibey-skills
pip install vibey-skills
```

Requires Python 3.10 or newer.

!!! note "Upgrading from vibe-engineering-skills"
    The package was renamed to `vibey-skills` in 2.0.0. `pip uninstall vibe-engineering-skills`
    (or `uv tool uninstall vibe-engineering-skills`), then install `vibey-skills` as above. The
    `vibe-skills` command still works as a deprecated alias; `vibe-engineering-skills` (the long
    command) was removed. If you added the marketplace under its old name, re-add it as
    `adammatthewsteinberger/vibey-skills` and install plugins as `<plugin>@vibey-skills`.

## Where skills get installed

`install` copies each skill directory to `~/.claude/skills/<skill-name>/` by default,
creating the directory if it does not exist. Override with `--dest`:

```bash
vibey-skills install --all --dest ./.claude/skills   # project-local instead of user-global
```

Existing directories are **skipped, never overwritten** — see
[Usage](usage.md#conflicts-and-updates).
