# Workflow reference

Repair and conflict publication are optimistic exact-head updates. Immediately before
committing, and again after any non-fast-forward push rejection, the trusted publisher
compares the PR head with the SHA that was evaluated. A concurrent update converts the old
run into a successful stale no-op; it never force-pushes, overwrites newer work, consumes a
repair attempt, or mutates a permanent branch from an obsolete checkout.

Issue automation turns an eligible published issue into one guarded solution branch and
linked pull request, which then enters this same path with no exemption. Branch intake
opens draft PRs. CI and provenance validate code. Documentation validates
the complete docs contract and periodically authors guarded refresh PRs. PR automation
aggregates exact-head scans, reviews outside contributions, repairs failures, and resolves
conflicts. The merge train squash-merges to develop and rebase-merges promotions to main.
Release publishes develop builds to TestPyPI and main builds to PyPI. Release surfaces
publish branch-specific ProperDocs and GHCR artifacts; repository profile maintains
description, homepage, topics, and verifies releases, deployments, and packages. If a
trusted post-merge workflow fails on `develop` or `main`, release repair reviews its logs
and returns a fixable problem through an ordinary guarded PR.

`CI` and `Release` are not managed templates; `vibey-gh install` never writes them, because
every repository's build, test, and publish steps differ. They must exist under those exact
names, because `github-release.yml`, `release-surfaces.yml`, and `release-repair.yml` all
key off a `workflow_run` named `Release` (and `release-repair.yml` also watches `CI`). A
`Release` workflow that runs on `develop`/`main`, derives the version with `vibey-gh
version --apply`, builds, and publishes through the `testpypi`/`pypi` trusted-publishing
environments is what the rest of this reference assumes exists.

## Issue automation

`Issue automation` runs on `issues` (`opened`, `reopened`, `labeled`), `workflow_dispatch`
with an issue number, and — when `[issue_automation].retain_schedule_backstop` is set — a
twice-daily recovery sweep that dispatches only the issues `vibey-gh issue-automation
list-eligible` reports.

The `evaluate` job holds `contents: read` and `issues: read`. It runs trusted default-branch
workflow code, installs the published `vibey-gh` package (never the adopting repository's
own package), and emits one structured decision: `solve`, `skip`, or `blocked`, each with a
stated reason. Only `solve` starts the privileged `solve` job; `blocked` labels and comments
once through the `exhausted` job.

The `solve` job checks out trusted automation under `automation/` and the configured base
branch under `target/` with `persist-credentials: false`. A trusted step renders the issue
into `briefing/issue.md`; the pinned Claude Code Action then runs from a disposable
credential-free Git context with `Read,Glob,Grep,Edit,Write` and no `Bash`, `gh`, or
`Agent` tool, and is told the briefing is an untrusted report rather than an instruction.
It edits files only.

Publication is a separate trusted step that validates the branch against the configured
namespace and the permanent branches, normalizes provenance headers with
`vibey-gh check --ci --apply`, commits with the repository's own configured trailer from
`vibey-gh trailer`, pushes one non-empty-source refspec, and opens one linked pull request
containing `Closes #N`. It publishes nothing when the agent returned `solved=false` or
produced no diff. `branch-intake.yml` is rendered to ignore the same namespace so the two
never race. From there the proposal is an ordinary pull request with no exemption from
scans, review, repair, or the merge train.

Attempts are budgeted per issue content fingerprint and stored in one machine-readable
issue comment, so a redispatch of unchanged text is a no-op and an edit starts a new
lineage.

## Conversation

`Conversation` runs on `issue_comment` (`created`) and `pull_request_review_comment`
(`created`) against any thread, plus `workflow_dispatch` with a subject number and an
optional exact comment ID. The cheapest possible loop guard runs before a runner is even
claimed: `github.event.sender.type != 'Bot'`, combined with a check that the triggering
comment contains the configured mention (`workflow_dispatch` is exempt, since a human
explicitly named the subject). This is the one failure mode unique to conversation — a
reply that mentions the trigger again would otherwise recurse and bill indefinitely — so it
is excluded before anything else is considered.

The `evaluate` job holds read-only `contents: read`, `issues: read`, and `pull-requests:
read`. It runs trusted default-branch workflow code, installs the published `vibey-gh`
package, resolves the subject and comment ID from either the dispatch inputs or the
triggering event, and calls `vibey-gh conversation evaluate` to compute one of `skip`,
`blocked`, `answer`, or `act` with a stated reason. `evaluate` checks, in order: the
automation's own identities (never answered), whether conversation is enabled, whether the
comment mentions the configured trigger, whether the thread is open, whether this exact
comment was already answered, whether the author is trusted or `respond_to_untrusted` is
set, and whether the thread's interaction budget is exhausted. Only `answer` or `act` starts
the privileged `respond` job.

The `respond` job checks out trusted automation under `automation/` and the thread's branch
(a pull request head) or the default branch (an issue) under `target/`, both with
`persist-credentials: false` for the read-only pull-request case. A trusted step renders the
thread into `briefing/thread.md` with `vibey-gh conversation context`; the pinned Claude Code
Action then runs from a disposable credential-free Git context with
`Read,Glob,Grep,Edit,Write` and no `Bash`, `gh`, or `Agent` tool, and is told the briefing is
an untrusted report rather than an instruction. When `may_change_files` is false — every case
except a trusted author on a pull request with changes allowed — it answers only and any
edits are discarded. When true, it may also make a clear, bounded change to the pull request,
following existing conventions and updating documentation and tests as the change requires.

Publication is a separate trusted step. When files changed and `may_change_files` was true,
it refuses an unsafe or permanent (`develop`/`main`) head ref, refuses a cross-repository
(fork) head, normalizes provenance headers with `vibey-gh check --ci --apply`, commits with
the repository's own configured trailer, and pushes directly to the existing PR branch — no
new branch or pull request is opened, since the change belongs to the thread it answers. The
answer is then always posted with `vibey-gh conversation reply`, noting whether a commit was
pushed, whether the request needs a human decision, and whether part of the thread tried to
redirect the request, and the interaction is recorded against the thread's budget with
`vibey-gh conversation record-response`. Attempts are budgeted per thread and stored in one
machine-readable issue comment, the same `vibey_gh.github_state` mechanism issue automation
uses.

## CodeQL

`CodeQL` runs on push and pull request against `develop` and `main`, plus a weekly Monday
schedule as a backstop. With `security-events: write` and read-only `contents: read`, it
runs the immutably pinned `github/codeql-action` initializer and analyzer against the
Python codebase. It is one of the required `scan_workflows` entries PR automation
aggregates before publishing the merge gate.

## API drift — not installed, and not yours

`API drift (Cloud Agents OpenAPI)` is **this project's own self-test and is not a managed
template**. It calls `vibey_gh.surfaces.parity()` to prove every canonical capability is
exposed through all five surfaces — MCP, API, CLI, SDK, and webhook — which is a statement
about vibey-gh, not about a repository that installs it.

It used to ship to every adopter and sit in the default `scan_workflows`, so an adopting
repository received a required-looking gate that tested this library rather than their own
product, and had to work out for themselves that it should come back out. It now lives in
this repository's own `.github/workflows/`, hand-authored, exactly as `ci.yml` and
`release.yml` do — what is specific to one repository is that repository's to author.

## Conventional Commits

`Conventional Commits` runs from trusted base-branch workflow code on PR open, reopen,
synchronization, and ready-for-review events. It inspects the exact PR head without
executing repository code. For same-repository, linear topic branches, it normalizes every
nonconforming subject, preserves commit bodies and provenance trailers, and publishes the
rewritten history with an exact-SHA `--force-with-lease`. It refuses forks, merge commits,
stale heads, and any branch named by the configured integration or release branch; the
literal `develop` and `main` names are denied independently as defense in depth. It never
deletes a branch. The resulting synchronize event reruns all ordinary scans.

## Branch intake

`Branch intake` runs on every push whose branch is not `develop`, `main`, or under the
`vibey-gh/repair/` or `vibey-gh/issue/` namespaces — issue automation and repair publish
their own linked pull requests, and intake must not race them. With `contents: read` and
`pull-requests: write`, it opens exactly one draft pull request against `develop` for a
branch that has no open PR yet. This intentionally runs on every push rather than once per
branch name: a branch name reused after its previous PR merged must still get a fresh
draft, since a historical closed PR must never suppress intake for the new lineage.

## CI

`CI` and `Release` are the two workflows `vibey-gh install` never renders, because every
repository's build, test, and publish steps differ; they must exist under those exact
names because other release workflows key off a `workflow_run` named `Release` (and
`release-repair.yml` also watches `CI`). `CI` runs on push and pull request against
`develop` and `main` with the default read-only token. Its `test` job runs pytest across
Python 3.11–3.13; `lint` runs Black, isort, Ruff, and mypy, then dogfoods the managed
automation by asserting `vibey_gh.install.installed()` reports no drift between the
repository's rendered workflows and its configuration; `build` builds the wheel and sdist,
checks them with `twine check`, and asserts every managed template and release theme asset
is packaged inside the wheel. `CI` is one of the required `scan_workflows` entries PR
automation aggregates.

## Provenance

`Provenance` runs on push to every branch and on every pull request, with read-only
`contents: read`. It installs the tooling (from source when the repository under test is
`vibey-gh`/`vibey-bootstrap` itself, otherwise the published package) and runs `vibey-gh
check --ci`, which performs the fingerprint and Conventional Commits verification that is
the server-side half of the provenance rule — backstopping the pre-push hook, which lives
in a clone and can be skipped with `--no-verify` or simply never installed. A promotion PR
from `develop` into `main` checks provenance without rewriting or re-auditing
already-admitted history; an ordinary PR checks only the commits it adds, via `--commits
BASE_SHA..HEAD`.

## Docs (documentation contract and maintenance)

`Docs` (workflow file `documentation.yml`) runs on pull request, push to `develop`/`main`,
a weekly Monday 07:23 UTC schedule, and manual dispatch. Its `contract` job holds
read-only `contents: read` and runs `vibey-gh check --ci` — the same fingerprint-checking
entry point `Provenance` uses — to verify every required documentation surface exists and
is current. Its `maintain` job runs only on schedule or `workflow_dispatch`, holds
`contents: write`, `id-token: write`, and `pull-requests: write`, checks out `develop`
onto a fresh `vibey-gh/docs/refresh-<run_id>` branch, and runs the pinned Claude Code
Action as a comprehensive documentation author restricted to `Read,Glob,Grep,Edit,Write`.
The job fails unless Claude's structured result reports `complete=true` with zero
`gaps_remaining`; only then does a trusted step commit, push the branch, and open one pull
request against `develop`.

## PR automation

`PR automation` is the aggregation, review, repair, and merge-gating hub. It triggers on
`pull_request_target` (opened, reopened, synchronize, ready-for-review) against
`develop`/`main`; on completion of every workflow named in `scan_workflows` (`CI`,
`Provenance`, `CodeQL`, `Docs`, and `Conventional Commits` by default); on a six-hourly
recovery schedule; and on manual dispatch.
Top-level permissions are `actions: read`, `checks: read`, `contents: read`, and
`pull-requests: read`, with individual jobs elevating further. `evaluate` resolves the PR
and its exact head SHA and calls `vibey-gh pr-automation evaluate` to compute an aggregate
`state` (`ready`, `review`, `repair`, `conflict`, `blocked`, or `pending`). `review`
(when state is `ready` or `review`) checks out the untrusted head read-only beside trusted
automation and runs the pinned Claude Code Action, restricted to `Read,Glob,Grep` plus a
scoped inline-comment tool and read-only `gh pr` commands, to produce the structured
semantic review this repair task itself receives as input. `mirror-fork` opens a
repository-owned replacement PR when a fork needs repair or has a conflict. `repair`
collects exact-head failed-check evidence into `diagnostics/`, runs Claude with
`Read,Glob,Grep,Edit,Write` and no execution tools, and — only when the branch is still at
the expected head — publishes one commit back to the PR branch. `resolve-conflict`
materializes a same-repository merge conflict, lets Claude edit only the conflicting
paths, and publishes one resolution commit. `escalate` labels and comments once when the
repair-attempt budget is exhausted.

`review-fallback` runs only when `[pr_automation.fallback].enabled` is set, the primary
`review` job produced no verdict at all (not a review that ran and found something), the
event is not a fork pull request (`trusted_only`), and the run is not a dry run. Unlike
every other job in this workflow it targets a distinct `[self-hosted, vibey-local-gh]`
runner rather than `ubuntu-latest`, and holds only `contents: read` — no secret, and no
token capable of mutating the repository. It fetches the exact-head diff with `gh pr diff`,
falling back to a local merge-base reconstruction when GitHub's diff API refuses a pull
request beyond roughly 300 changed files, then runs `vibey-gh local-review` against an
Ollama-compatible endpoint (`qwen2.5-coder:14b` by default) with the diff as the only input:
no shell, no tools, and no network beyond the local inference port reach the model. See
[Configuration](configuration.md#pr_automationfallback) for the full field reference and
[Security](security.md) for the trust boundary this runner introduces. `gate` publishes the
final `PR automation / gate` check run for the exact head and, on success, dispatches
`merge-train.yml`. When the primary review returned no verdict and the fallback ran and
found nothing blocking, the gate still succeeds but titles the check run
`PR automation: gate (local fallback)` so the weaker signal is never mistaken for the
primary review's; when neither produced a usable verdict, it titles the check run
`PR automation: review incomplete` for an operator to resolve.

Every `[pr_automation].scan_workflows` entry names a `workflow_run` this aggregation
waits on, so each one must be a workflow that runs on `pull_request` or
`pull_request_target`. A workflow that only triggers on `push` can never complete for a
pull request: `state` never leaves `pending`, `gate` — which requires `state !=
'pending'` — never runs, and the `PR automation / gate` check-run is never published. Made
a required check on the branch ruleset, that is a silent, total, and permanent lockout.
`vibey-gh check` fails on any named workflow that exists but cannot fire for a pull
request; a name absent from `.github/workflows/` is not an error, since it may live
elsewhere or under another name.

## Merge train

`Merge train` runs on completion of `PR automation`, a weekly Monday recovery schedule,
and manual dispatch (optionally scoped to one PR, optionally `dry_run`). With `actions:
read`, `contents: write`, and `pull-requests: write`, it resolves the gated PR and runs
`vibey-gh merge-train`, which squash-merges every currently ready PR into `develop`.

## Branch sync

`Branch sync` runs on every push to `develop`, a nightly `37 5 * * *` schedule, and manual
dispatch with an optional `dry_run` input. Top-level permissions are read-only
`contents: read`; each job elevates only what it needs. It holds two independent jobs that
never run in the same trigger.

The `sync` job (push or manual dispatch, never schedule; `contents: write`,
`pull-requests: write`) checks out trusted default-branch automation and runs `vibey-gh
reconcile-branches`, the CLI entry point over `vibey_gh/reconcile.py`. For every open pull
request it classifies the branch by `git cherry` patch identity against `develop`: a branch
with nothing unique has its PR closed and (when configured) its branch deleted; a branch
automation owns and that is behind is rebased onto the new tip, dropping the
now-duplicated commits; a contributor's own branch is left untouched and, when behind,
either merged forward through GitHub's update-branch endpoint (with the contributor's
consent implied by "allow maintainer edits") or left with an explanatory comment. Forks are
only ever moved forward, never rewritten, rebased, closed, or deleted. `dry_run` decides
and reports without mutating anything. `[branch_sync]` and `[realign]` in configuration
control this behavior; see [Configuration](configuration.md).

The `heal` job (schedule only; `actions: write`, `contents: read`, `pull-requests: write`)
runs `vibey-gh pr-automation self-heal` to refill the repair budget of every pull request
labeled `vibey-gh:repair-exhausted`, up to `branch_sync.max_self_heals` refills per lineage,
so a transient outage does not permanently strand a PR that a human has not yet noticed.
Each healed pull request then has `pr-automation.yml` re-dispatched against its exact head
SHA, returning it to ordinary review and repair with no exemption.

## Promote

`Promote` (workflow file `promote-to-main.yml`) runs on completion of `Merge train`, a
weekly Monday schedule, and manual dispatch. With `contents: write` and `pull-requests:
write`, it runs `vibey-gh promote`, which compares `develop` and `main` by tree content
rather than commit count, derives the next version, and opens or reuses a promotion pull
request; that PR then goes through the same scans, `PR automation` gate, and a rebase
merge to `main` as any other change. `AUTOMERGE_TOKEN` is required here because a
ruleset-required approving review cannot be satisfied by the default `GITHUB_TOKEN`.

## Release

`Release` (not a managed template) runs on push to `main` and `develop` with read-only
`contents: read`. Its `build` job dogfoods `vibey_gh.install.installed()` before
publishing, stamps a `--dev` version on `develop` builds via `vibey-gh version --apply`,
and builds the wheel and sdist. `testpypi` (needs `build`, `develop` only) and `pypi`
(needs `build`, `main` only) each hold `id-token: write` and publish through
trusted-publishing environments pinned to their respective branch. `realign` (needs
`build` and `pypi`, `main` only, `contents: write`) runs `vibey-gh realign` to converge
`develop` back onto `main` when their trees are content-identical; it never force-pushes
over unmerged `develop` work and skips gracefully when `AUTOMERGE_TOKEN` is absent. A
successful realign then reconciles every open pull request against the rewritten
`develop`, the same as [Branch sync](#branch-sync); because this job only holds
`contents: write`, that follow-up can fail for lack of `pull-requests: write` or because
GitHub is unreachable, and such a failure is logged rather than failing the job — the
realign already succeeded and must stand regardless of whether the follow-up reconciled
every branch. This repository's own `testpypi`/`pypi` jobs additionally run `vibey-gh
report-superseded` right after each publish step, printing which already-released versions
the new one supersedes; see [Releases](releases.md).

## GitHub Release

`GitHub Release` runs on completion of `Release` (only when it succeeded on `main`) or
manual dispatch with an explicit target SHA. With `contents: write`, it checks out the
exact released commit and runs `vibey-gh github-release --target <sha>` to create an
immutable tag and an idempotent GitHub Release for that commit.

## Release surfaces

`Release surfaces` runs on completion of `Release` on `develop` or `main`, or manual
dispatch naming a channel and a source run. Its `context` job resolves the channel;
`package` (`actions: read`, `contents: read`, `packages: write`) publishes the built wheel
and sdist as an OCI artifact to GitHub Packages, tagged with the channel and `latest` on
`main`; `docs` (`actions: read`, `contents: read`, `pages: write`, `id-token: write`)
builds a branch-specific ProperDocs site with the managed release theme and deploys it to
the shared `github-pages` environment under a channel-specific path, restoring the other
channel's existing site alongside it. When `documentation.google_analytics_id` is set, the
same GA4 measurement ID is injected into every generated page and the channel-picker page;
left empty (the default), no analytics script is emitted anywhere.

## Repository profile

`Repository profile` runs on completion of `Release surfaces` or manual dispatch, with
read-only `actions: read`, `contents: read`, `deployments: read`, and `packages: read`. It
reconciles the repository's description, homepage, topics, and collaboration/security
settings to the configured values, then — when `[rulesets].enabled` — checks out the
default branch, installs `vibey-gh`, and reconciles the integration and release branch
rulesets from `[rulesets]` before verifying the public release surfaces are actually live:
the Pages homepage responds, at least one release and one deployment exist, the GHCR
package is reachable, and `develop`/`main` remain protected. Ruleset reconciliation runs
before that verification step in the same job, so the branches it protects are already
current by the time the check runs. A ruleset the API refuses fails the job with the API's
own reason instead of being silently skipped.

## Release repair

`Release repair` runs on completion of `CI`, `Provenance`, `Release`, `Release surfaces`,
or `GitHub Release` on `develop` or `main`, only when that run's conclusion was `failure`.
With `contents: write`, `id-token: write`, `issues: write`, `pull-requests: write`, and
read-only `actions`/`checks`, it first confirms the branch is still at the failed SHA (a
stale failure is a no-op) and that no repair branch already exists for that run. It checks
out the exact failed revision, runs Claude in a credential-free context restricted to
`Read,Glob,Grep,Edit,Write` plus read-only CI-log tools, and — only when the structured
result reports `fixable=true` and the branch is still current — publishes one commit to a
new `vibey-gh/repair/release-<branch>-<run_id>` branch and opens an ordinary pull request
that re-enters the same scans, review, and merge train as any other change. It never
pushes directly to or deletes a permanent branch.

## Automation bootstrap

`Automation bootstrap` is a manual `workflow_dispatch` with three required inputs: the PR
number, the exact reviewed head SHA, and an explicit `authorize` boolean. It exists only for
the case where privileged workflow code itself is broken and a PR therefore cannot repair
its own gate. With `contents: write`, `pull-requests: write`, and `checks: read`, the job
verifies that the dispatching actor holds administrator permission; that the PR is open,
non-draft, targets `develop`, and exactly matches the dispatched head SHA; that changed
files are confined to workflow, template, or automation-core paths; and that every non-gate
check run on that exact SHA — including CodeQL, the API-drift parity check,
the Documentation contract, Provenance, Build, and Lint — completed successfully. Only then does it perform an
admin `--match-head-commit` squash merge into `develop`, bypassing ordinary PR automation
review, and delete the source branch, and only when that branch is same-repository and not
a configured or literal permanent branch. See [Security](security.md) and
[Threat model](threat-model.md) for the full rationale.
