# 0018 — If it can be declared in the repository, it is declared in the repository

**Status:** accepted · **Date:** 2026-09-15 · **Extends:** ADR-0017

**Canon:** sub-doctrine 12.c — *the declared state*, filed under doctrine 12 — Humans first (ADR-0020). It is law from the operator's ratifying merge of the change that carries it.

## Context

ADR-0017 says: if the family already does it, use the family. This is the other
half of the same idea, and it is about *where the state lives* rather than which
code touches it.

A surprising amount of how these projects actually behave is not in the
repository. Branch protection, required status checks, repository description and
topics, dependabot ignores, environments, publisher trust, whether a repository
is archived — all of it is real configuration that changes what happens on a
push, and all of it can be set by clicking.

Clicked state has three properties that make it the worst kind: it has no
history, so nobody can say when it changed or why; it has no review, so nobody
agreed to it; and it cannot be recreated, so a repository that loses it is
restored from somebody's memory.

This is not hypothetical here. Measured before this change, `vibey`'s own
`.vibey-gh.toml` declared neither `[rulesets]` nor `[repository_profile]` (both
were added in the same commit as this record) — while
`vibey-gh`, which this repository now contains, ships `rulesets.py` to reconcile
branch protection from exactly that key, and a `[repository_profile]` block that
`vibey-skills` already uses for its description and topics. The capability was
built here, shipped here, adopted elsewhere, and not turned on at home.

## Decision

**Anything that can be `*-as-code` must be `*-as-code`, and no option that
degrades this is ever the right one.**

Infrastructure as code. Configuration as code. Policy as code. Pipelines as code.
Documentation as code. Repository settings as code. If a thing can be declared in
a file, reviewed in a pull request, and reconciled from that file, that is how it
is done — not by clicking, not by a runbook step that says "then set X in the
settings page", and not by a shell command someone runs by hand and does not
record.

Three consequences of taking that literally:

**Declared, not just documented.** A README paragraph describing the branch
protection you should have is not configuration as code. The test is whether the
state can be *reconstructed* from the repository. If a stranger with admin rights
and a clone cannot restore it, it is not as-code yet.

**Reconciled, not just written.** A declaration nobody applies drifts, and a
drifted declaration is worse than none because it reads as true. Where there is a
reconciler, it runs in CI: `vibey-gh rulesets`, `vibey-gh install`,
`repository-profile.yml`. Where a declaration cannot be reconciled
automatically — some of it genuinely cannot, see below — it is still declared,
and the check becomes "does reality match the file", which a job can answer even
when it cannot fix it.

**Never trade it away for convenience.** When a change offers a quicker path that
moves state out of the repository — pasting a value into a settings page instead
of adding a key, a one-off `gh api` call instead of a declaration, a manual step
in a release runbook — that path is not taken. The quicker option is the one that
costs later, and it costs at the worst moment: restoring a repository, onboarding
a person, or explaining an incident.

### Generic and configurable, never less

**Everything that can be made generic and configurable must be made generic and
configurable, and nothing is ever changed to a state that is less generic or less
configurable.** Not "where convenient" — as an absolute. A hard-coded value that
could have been a key, a special case that could have been a rule, a path that
could have been discovered: each one is a decision taken away from whoever adopts
this next, and taken away silently.

The test is the same as the one above: could the next caller need it different?
If yes, it is configuration. A default is fine — a default is configurability
with an opinion. A constant is not.

Two examples from the change that produced this ADR, both of which started as a
one-line special case and were not left there:

**Bypass actors.** `vibey-gh` validated every ruleset bypass actor as
`<type>:<numeric id>`, which made this repository's live configuration
inexpressible — `OrganizationAdmin` has no id, and GitHub returns `actor_id:
null` for it. The quick fix was to special-case that one string where vibey's
config is read. What landed instead was `IDLESS_BYPASS_ACTOR_TYPES`, a named set
covering `OrganizationAdmin` and `DeployKey`, validated in both directions: an
id-less type given an id is rejected, because the API rejects it too. Every
adopter gets the capability, not just this repository.

**Project roots.** `find_root` walked up to `.git`, because a repository used to
be a project. In a monorepo `src/vibey_tools/gh` *is* a project — its own
distribution, version line and fingerprint globs — inside a repository whose root
belongs to something else, and walking past it loaded the wrong configuration
silently. The quick fix was to pass an explicit root from the two call sites that
noticed. What landed instead: **a directory carrying its own `.vibey-gh.toml`
stops the walk.** No new marker file, no path list, no monorepo-specific branch —
the file that already means "a project lives here" now means it to the resolver
too. The standalone case is unchanged, because there the config sits at the git
root and both rules give the same answer.

Note what both have in common. The generic version was not more work than the
special case; it was the same work aimed at the general shape instead of at the
instance in front of it. That is usually true, and it is why this is a rule
rather than a trade-off to weigh each time.

### Where it meets ADR-0017

Use *our* as-code tooling. `vibey-gh` already reconciles rulesets, managed
workflows, release assets, dependabot ignores and repository profile from
`.vibey-gh.toml`. Reaching for a general-purpose tool to do something vibey-gh
already does would satisfy this ADR and violate the previous one. If ours cannot
express something, the fix is to teach ours — which is the mechanism by which
this doctrine improves the product rather than just constraining it.

### The honest limit

Some state has no as-code path at all today. A PyPI trusted publisher is
configured on PyPI. GitHub environments and their secrets are configured on
GitHub. Repository archival is a click. For these the rule degrades to its
weakest useful form and no further: **the desired state is recorded in the
repository anyway**, in the configuration file that would own it if an API
existed, and a job verifies reality against it where the API allows reading. That
is not as-code, and it should not be described as if it were — but it is the
difference between a gap somebody can close and a gap nobody can see.

## Consequences

**A backlog of things this repository already has the tooling for:**

| Gap | Today | Declare in |
|---|---|---|
| Branch protection and required checks | declared in this change; **not yet reconciled** — `repository-profile.yml`, which runs `vibey-gh rulesets`, is not in `[install] workflows` | `[rulesets]` in `.vibey-gh.toml`, reconciled by `vibey-gh rulesets` |
| Repository description and topics | declared in this change; **not yet reconciled** for the same reason | `[repository_profile]`, reconciled by `repository-profile.yml` |
| Which checks a pull request must wait for | partly clicked, partly `[pr_automation] scan_workflows` | one place, the config |

**And a backlog of things it does not, recorded so they are visible:** PyPI
trusted publishers for the ten distributions this tree will publish; the
per-package GitHub environments they publish through; repository archival state
across the organisation. Each gets a declaration in the repository and a
verification step, even though none can be applied from one.

**The cost is that some changes get slower**, because a settings toggle becomes a
pull request. That is the intended effect, not a side effect: the toggle was
always a change to how the project behaves, and it was only ever fast because it
skipped review.
