# Changelog

Releases of `vibey-skills` are recorded as
[GitHub Releases](https://github.com/adammatthewsteinberger/vibey-skills/releases), each
generated from the pull requests it contains — see
[Releasing](https://github.com/adammatthewsteinberger/vibey-skills/blob/main/CLAUDE.md#releasing)
in CLAUDE.md for how a release is built and published. That is the authoritative,
per-version record; this file is not a parallel copy of it.

The version currently published is single-sourced from
[`src/vibey_skills/__init__.py`](https://github.com/adammatthewsteinberger/vibey-skills/blob/main/src/vibey_skills/__init__.py)
and mirrored into
[`.claude-plugin/marketplace.json`](https://github.com/adammatthewsteinberger/vibey-skills/blob/main/.claude-plugin/marketplace.json)'s
`metadata.version` — the two are validated to agree on every push.

For what changed in a specific plugin, see that plugin's own `version` in its
`.claude-plugin/plugin.json`, alongside the version history in
[the marketplace manifest](https://github.com/adammatthewsteinberger/vibey-skills/blob/main/.claude-plugin/marketplace.json).
