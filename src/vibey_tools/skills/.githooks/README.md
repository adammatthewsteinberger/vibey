# Git hooks

This directory is wired up as `core.hooksPath` by `vibey-gh install` (see
[CONTRIBUTING.md](https://github.com/adammatthewsteinberger/vibey-skills/blob/main/CONTRIBUTING.md)).
Both files are generated and managed by `vibey-gh` — do not edit them directly; a manual
edit is silently reported as "out of date" the next time `vibey-gh check` runs, and is
overwritten the next time `vibey-gh install` runs. If you need repository-specific hook
behavior on top of these, add `commit-msg.local` or `pre-push.local` alongside them —
both hooks chain to a `.local` file of the same name when one is present.

- **`commit-msg`** — appends the repository's fingerprint trailer
  (`Made-With: …`, see [CLAUDE.md](https://github.com/adammatthewsteinberger/vibey-skills/blob/main/CLAUDE.md#the-fingerprint))
  to a commit message if it isn't already present, and prefixes a non-Conventional-Commits
  subject with `chore: `.
- **`pre-push`** — refuses the push if `vibey-gh` isn't installed, or if
  `vibey-gh check --quiet` fails (a missing fingerprint header, a stale managed workflow,
  or — once enabled — the documentation contract). `git push --no-verify` is the
  intentional escape hatch for an emergency push.

Neither hook is a substitute for CI: the same checks run again, unconditionally, in
[.github/workflows/provenance.yml](https://github.com/adammatthewsteinberger/vibey-skills/blob/main/.github/workflows/provenance.yml)
and
[.github/workflows/ci.yml](https://github.com/adammatthewsteinberger/vibey-skills/blob/main/.github/workflows/ci.yml),
because a hook lives in a clone — it can be bypassed with `--no-verify`, and a fresh clone
that never ran `vibey-gh install` has no hook at all.
