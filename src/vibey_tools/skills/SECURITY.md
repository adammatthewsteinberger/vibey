# Security Policy

## Supported versions

The latest released version of `vibey-skills` is the only supported version.
Fixes ship in a new release rather than as patches to older ones.

## Reporting a vulnerability

**Please do not open a public issue for a security problem.**

Report it through GitHub's private vulnerability reporting instead:

1. Go to this repository's **Security** tab.
2. Choose **Report a vulnerability**.
3. Describe the issue, the affected files or version, and how to reproduce it.

This routes the report privately to the maintainers. There is no security email address —
private vulnerability reporting is the only intended channel, so reports stay confidential
until a fix is available.

You can expect an initial acknowledgement within about a week. If a report is accepted, we
will work with you on a fix and credit you in the release notes unless you ask otherwise.

## What is in scope

This project is a collection of Markdown skill files, JSON manifests, and a small
stdlib-only Python CLI that copies those files into a local directory. The realistic threat
surface is therefore narrow, and reports in these areas are in scope:

- **Path traversal or arbitrary write** in the `vibey-skills install` command — for example a
  plugin or skill name that escapes the `--dest` directory.
- **Path traversal or symlink escape** in the context-engine commands — `vibey-skills
  index build --output` writing its index directory, symlinked skill sources or index
  boundaries that should fail closed, and the file writes made by `packet` and
  `evaluate`.
- **Supply-chain integrity** — anything suggesting the published PyPI artifact does not match
  the tagged source, or a weakness in the release workflow's Trusted Publishing setup.
- **Malicious or unsafe guidance in skill content** — a `SKILL.md` that instructs an agent to
  run a destructive command, exfiltrate data, disable a security control, or that recommends
  a pattern with a known vulnerability. Skills are read by AI agents that may act on them, so
  we treat bad guidance as a security issue, not just a documentation bug.
- **Secrets or internal identifiers** committed to this repository.

## What is out of scope

- Vulnerabilities in third-party products that a skill merely *describes* (report those to
  the relevant vendor).
- The accuracy of a citation or a purely editorial disagreement — open a normal issue.
- Findings from automated scanners without a demonstrated impact on this project.

## A note on skill content

Agent Skills are instructions loaded into an AI agent's context. Treat them as you would any
executable dependency: review what you install, and prefer installing only the plugins you
need rather than `--all` if you are working in a sensitive environment.
