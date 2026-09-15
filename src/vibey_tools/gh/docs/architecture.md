# Architecture

The canonical, whole-project machine-readable architecture is
[`project.mmd`](project.mmd). It is a required Mermaid artifact enforced by deterministic
and semantic review gates; changes to modules, interfaces, workflows, security boundaries,
or release paths must update it in the same pull request.

`vibey-gh` is a dependency-free Python CLI whose configuration model feeds pure policy
decisions, GitHub CLI adapters, installation code, and immutable workflow templates.
Configuration lives in `.vibey-gh.toml`; templates are rendered during installation and
their exact bytes are verified in CI. Remote mutation is isolated to explicit commands
and guarded workflow steps. PR automation separates untrusted inspection/editing from
trusted commit and push operations. Issue automation applies the same separation to a
lower-authority input: `vibey_gh.issue_automation` decides eligibility, renders untrusted
issue text into a bounded briefing, and leaves branch publication to a trusted step.
`vibey_gh.conversation` applies the same pattern to a third, even lower-authority input —
a comment mentioning the configured trigger — deciding eligibility (mention, trust,
interaction budget, and a self-reply loop guard checked first), rendering the untrusted
thread into a bounded briefing, and leaving both the reply and any bounded file change to a
trusted step. `vibey_gh.github_state` is the single implementation of durable
marker-comment state, shared by all three.

When a primary Claude path returns no verdict at all, `vibey_gh.local_review` offers two
opt-in fallbacks through the same Ollama-compatible endpoint on the same distinct,
non-privileged self-hosted runner. For pull requests, `local-review` reviews the diff and
reports a narrower verdict than the primary review's documentation-contract schema. For
issues, `local-triage` does deliberately less than the solver it backs up — a local model
must never inherit the write access the paid solver earned — so it writes no code and
pushes no branch: it produces one bounded, schema-constrained analysis (root cause,
approach, likely files, risks), posted as a single deduplicated comment with `needs_human`
forced true, while the paid solver retries on its own schedule. Both are a separate
security boundary from every other AI path in this project — a self-hosted rather than
GitHub-hosted runner, excluded from fork pull requests by `trusted_only` — documented in
full in [Configuration](configuration.md) under `[pr_automation.fallback]` and
`[issue_automation]` `fallback_enabled`.

The repository also ships a Claude-standard plugin marketplace
(`.claude-plugin/marketplace.json`), registered and enabled for project sessions by
`.claude/settings.json`. Its four plugins — `vibey-gh-development`, `vibey-gh-documentation`,
`vibey-gh-release-security`, and `vibey-gh-pr-automation` — each carry a manifest, skills, and
a specialist agent that back the corresponding automation surface (development/testing review,
the documentation contract audit, release and provenance auditing, and PR review/repair/conflict
resolution respectively); the development, documentation, and PR-automation plugins additionally
ship slash commands. This is a separate, human-invoked surface: nothing in it runs
automatically in a CI job.

See also the [threat model](threat-model.md), [workflow reference](workflows.md), and
[configuration reference](configuration.md).
