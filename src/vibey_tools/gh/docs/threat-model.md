# Threat model

Protected assets include repository contents, permanent branches, secrets, packages,
releases, Pages deployments, provenance, and maintainer identity. Adversaries may control
fork contents, PR metadata, logs, model prompts, generated output, and dependency names.
Controls include no privileged execution of PR code, exact-SHA decisions, argument/path
validation, bounded attempts, guarded refspecs, immutable pins, independent CI, no
delete/force operations on main or develop, and an optimistic-concurrency recheck of the PR
head immediately before and after every repair or conflict publish, which converts a
concurrent human or bot update into a stale no-op instead of overwriting it. The narrow
exception is a lease-protected force-update of a same-repository topic branch to repair
commit subjects; exact-head, linear-history, repository-ownership, and permanent-branch
guards all precede it. A fork, merge commit, stale event, or concurrent push fails closed.
Operators must protect repository secrets and review changes to `.vibey-gh.toml`'s
`[rulesets]` block, especially `bypass_actors`. That field defaults to the repository
admin role rather than to nobody, which is a deliberate availability trade: a ruleset has
no "include administrators" toggle, so an empty bypass list turns any check that stops
reporting — an outage, an exhausted budget, a renamed job — into a branch nobody can merge
to. The default grants no authority it does not already imply, since anyone able to bypass
a ruleset can equally rewrite it; a repository wanting the stricter posture sets
`bypass_actors = []` and accepts that recovery then means editing the ruleset by hand.

The integration and release branch rulesets are themselves reconciled, not merely assumed:
`vibey_gh.rulesets` builds each desired ruleset from configuration and compares it against
what GitHub actually has before `repository-profile.yml` applies the difference.
`RulesetConfig` refuses to construct at all when `allow_force_pushes` or `allow_deletions`
is `true`, so the non-deletion, non-rewrite guarantee this document claims cannot be
disabled by a single configuration key — that path fails at load time, before any workflow
runs. A rule type an existing ruleset carries that configuration does not mention is never
removed; it is merged back into the payload untouched and reported as unexpected, so a
reconciliation can never look like a deletion. A ruleset the API refuses raises rather than
being swallowed, because a skipped reconciliation is indistinguishable from a satisfied
one from the outside — the same failure mode the exact-head gate and branch reconciliation
below already refuse to risk.

Comments are the least guarded input in a repository: anyone with an account can write one,
on anything, at any time. Conversation therefore answers only a configured mention, and
only from the owner or a trusted author unless `respond_to_untrusted` is deliberately set —
answering everyone is a spending decision, not a default. Comment text reaches the model
only through a bounded briefing written by a trusted step; the model holds no `Bash`, `gh`,
`Agent`, or Git tool, and the answer is posted by a trusted step rather than by the model.
File changes are narrower still: only on a pull request, only from a trusted commenter,
never on a fork or a permanent branch, and never more than one commit. Interactions per
thread are budgeted so a conversation cannot become an unbounded work queue. The loop guard
comes first in every path — the automation's own reply contains the trigger, so answering
itself would recurse and bill indefinitely; `ignore_actors` cannot be emptied while
conversation is enabled, and the workflow additionally refuses any sender GitHub reports as
a bot before a runner is claimed.

An outside author cannot steer automation at a permanent branch from either end. GitHub
already refuses them write access; behind that, `evaluate` terminally blocks any untrusted
pull request whose head ref is the configured integration or release branch (whose repair
push would land there) and any aimed at the release branch, which must only ever receive a
promotion. Blocked is terminal, so no review, repair, conflict resolution, or gate runs for
either shape. A fork is moved forward only through GitHub's update-branch endpoint, which
merges rather than rewrites and succeeds only where the contributor enabled maintainer
edits; rebasing, closing, and deleting a fork are unreachable under every configuration.

Branch reconciliation after realign is the second deliberate force-update path, and the
only automated deletion path besides merged-topic cleanup. Both are confined by
`vibey_gh.reconcile.deletable()`, which refuses the configured integration and release
branches, the literal `develop` and `main` independently, every fork branch, and any ref
that is empty, begins with `-`, or contains `:` or `..`. `rebase_branch()` and
`delete_branch()` each re-check that predicate and raise rather than proceed, so no caller
can reach a protected ref by passing one in. Rebases publish with an exact-SHA
`--force-with-lease`, so a branch that moved in the meantime refuses the push instead of
being overwritten. A pull request is closed only when `git cherry` reports that every one
of its commits is already upstream by patch identity; a ref that cannot be read reports
unique work instead, so an unreadable branch fails closed. A contributor's branch carrying
unique work is never rewritten, deleted, or closed — it receives a comment.

Published issues are a distinct adversary-controlled asset with a lower barrier than a
fork PR: anyone with an account can create one, and the `issues` event runs privileged
default-branch workflow code. The controls are authority, shape, and budget. Authority: the
`solve` job runs only for an explicit `solve` decision from `vibey_gh.issue_automation`,
which refuses an outside author's issue until a maintainer applies the configured label.
Shape: issue text reaches the model only through a bounded briefing file written by a
trusted step, labelled as an untrusted report, with the model holding no `Bash`, `gh`,
`Agent`, or Git tool; branch names derive from the issue number, a SHA-256 of its content,
and a regex-sanitized slug of the title (stripped to `[a-z0-9-]+`, length-capped, so no
issue text can escape into a shell command or workflow expression), and a trusted publisher
independently re-validates the namespace, the permanent-branch denylist, and the
update-only refspec before pushing. Budget: attempts are
counted per content fingerprint, so a redispatch cannot spend the budget twice and a
resource-exhaustion attempt through repeated events is bounded by `max_attempts`. The
resulting pull request receives ordinary review, repair, and merge-train treatment; nothing
about its origin exempts it.

The repair/solve attempt budget itself is adversary-reachable. `vibey_gh.github_state`
locates the one marker comment holding `attempts`, `heals`, and the last reviewed SHA by
regexing the newest comment body for `<!-- marker:{...} -->`; it does not check who posted
that comment. On a public repository, any accountholder who can comment on the PR or
issue — including its own author — can post a hidden marker resetting the stored counters,
and `upsert_comment` locates "the existing" comment the same unauthenticated way, so a later
legitimate update silently edits the forged one instead of rejecting it. This cannot force
an unreviewed merge: `PRAutomation`'s review job re-runs whenever `evaluate` reaches `ready`
or `review` regardless of the stored `review_passed` value, and every merge still requires
the exact-head gates above. What a forged marker can do is defeat `max_repair_attempts`,
`max_self_heals`, and `max_attempts` as cost controls, turning the advertised bounded
repair/solve budget into repeated paid Claude invocations. The reusable Python capability
does not itself bind state to a trusted author or sign the payload; operators who need a
hard cost ceiling on a public repository should restrict who can comment on
automation-managed PRs and issues.

Fork PR heads are a distinct adversary-controlled asset: the fork owner controls the head
commit but never receives privileged credentials. When a fork PR needs a repair it cannot
receive directly, the `mirror-fork` job (`contents: write`, `issues: write`,
`pull-requests: write`, gated on `needs.evaluate.outputs.fork == 'true'`) calls
`vibey_gh.pr_automation.mirror_fork()` to open a repository-owned replacement PR that
mirrors the exact fork head with attribution; the original fork branch is never pushed to,
and the replacement PR carries the `vibey-gh:external-repair` label and re-enters ordinary
`PRAutomation`/`Guard` review from there. Same-repository merge conflicts take a narrower
path: the `resolve-conflict` job checks out the exact conflicting head with
`persist-credentials: false`, materializes only the paths Git reports as unresolved, runs
the model against that bounded set with edits restricted to those paths and no command
execution, then independently re-verifies the resolved diff touches only the materialized
conflict paths and that the PR head still matches the expected exact SHA before pushing one
guarded resolution commit — the same optimistic-concurrency recheck used elsewhere converts
a concurrent update into a no-op rather than an overwrite.

The second narrow exception is the manually dispatched automation-bootstrap admin merge,
used only to recover from a broken privileged workflow that a normal PR cannot repair
because privileged workflow code is loaded from the trusted base branch, not the PR head.
Only a repository administrator can trigger it, and only with explicit `workflow_dispatch`
authorization naming an exact PR and head SHA. Before merging, the workflow independently
re-verifies that the PR is open, non-draft, targets `develop`, and matches the supplied head
exactly; that its changed files are confined to workflow, template, or automation-core
paths; and that every non-gate check run on that exact SHA — including CodeQL, API drift,
documentation, provenance, build, and lint — completed successfully. It then performs a
`--match-head-commit` admin squash merge, which bypasses ordinary `PRAutomation` and `Guard`
review but never deletes a permanent branch. This trades the semantic review step for an
administrator's explicit authorization plus the same independent deterministic gates,
scoped to the one case those gates cannot otherwise unblock.

The opt-in local-model review fallback introduces a distinct asset and a distinct
boundary: a repository-provided `[self-hosted, vibey-local-gh]` runner, rather than a
GitHub-hosted one, that GitHub itself warns should almost never serve a public repository
because any accountholder can open a pull request against it. The `trusted_only` setting
(on by default) is what removes that exposure — it excludes fork pull requests from
`review-fallback` entirely, so only a same-repository head, whose author GitHub has
already authorized, ever reaches that runner. The job runs only when the primary Claude
review produced no verdict at all, never when a review ran and returned findings, and it
holds `contents: read` and nothing else: no secret, and no token capable of pushing,
merging, or mutating the repository, so compromising that runner cannot itself authorize a
merge. The diff still reaches a model as text; the local model has no shell, no tools, and
no network beyond the loopback inference port, matching the no-execution rule the primary
review follows. Because a small local model's judgments are unreliable even though Ollama's
schema-constrained decoding guarantees the response shape, the fallback's verdict omits the
documentation-contract fields and the gate names the result `PR automation: gate (local
fallback)`, so a degraded signal can never silently stand in for the primary review's.

The AI action's Git-discovery requirement is isolated from source and persisted credentials.
During model execution, workspace-root `.git` points only to an ephemeral empty repository.
Its clean `origin` satisfies action initialization, while a nonmatching actor sentinel selects
the token-free credential-helper and secret-scrubbing path without authorizing anyone.
Exact source is a separate `target/` checkout with persisted credentials disabled. The
context is destroyed before trusted code authenticates and publishes. Tests require this
ordering and fail if a Claude-facing target checkout persists credentials.
