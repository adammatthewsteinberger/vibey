# Operations

`ANTHROPIC_API_KEY` is required. Add `AUTOMERGE_TOKEN` only when the default
`GITHUB_TOKEN` cannot satisfy branch rulesets or repository-settings writes; PyPI/TestPyPI
use trusted publishing environments.

## What `AUTOMERGE_TOKEN` must be able to do

The token appears in a minority of the workflows' `GH_TOKEN` assignments — reading the
pull request, commenting, labelling, merging, and pushing the promotion's version bump.
For a fine-grained personal access token that means exactly:

| Permission | Level |
|---|---|
| Contents | Read and write |
| Pull requests | Read and write |
| Workflows | Read and write |
| Actions | Read |
| Metadata | Read (mandatory) |

**Workflows is not optional.** GitHub refuses any push that creates or updates a file
under `.github/workflows/` from a token without it — `! [remote rejected] ... (refusing
to allow a Personal Access Token to create or update workflow ... without workflow
scope)` — and an automated repair is *more* likely than a human to touch a workflow,
because workflow drift is exactly what reviews flag on tooling pull requests. Without
this permission the repair commits cleanly, the push is rejected, and the pull request
silently stops advancing (#172).

**Checks is deliberately absent, and the fine-grained token UI offers no such permission.**
Check runs can only be created by a GitHub App, so the gate is published with
`GITHUB_TOKEN` — which is one — and no PAT permission exists or is needed for it. The
workflows' own `permissions:` blocks govern `GITHUB_TOKEN`, not this PAT; do not read
`checks: read` there as a token requirement.

Three failure modes worth knowing before they cost an afternoon, because each presented as
something else in production:

- **A fine-grained token expires** (a year at most) and returns as `HTTP 401: Bad
  credentials` inside a step whose name says nothing about credentials. A classic token
  with the single `repo` scope covers everything above and supports no expiration — the
  trade is that it reaches every repository the account can.
- **A fine-grained token only reaches the repositories in its own grant list.** The secret
  being set on a repository proves nothing: two repositories out of a token's list behaved
  identically to two inside it for reads, then failed every privileged write. The merge
  train reported each failure as *"the ruleset refused it"* until it learned to print the
  API's own error.
- **The account behind the token is what bypasses rulesets.** The merge train's `--admin`
  fallback works only if that account holds a bypass role on the ruleset; the token's
  permissions cannot add standing its owner does not have.

## Recovering from a review with no verdict

`PR automation: review incomplete` means the primary exact-head review returned no verdict
at all — check API credit balance, the `ANTHROPIC_API_KEY` secret, and model availability,
then rerun the review; this is never a defect in the pull request. If
`[pr_automation.fallback].enabled` is set and a self-hosted `vibey-local-gh` runner is
registered, the same no-verdict condition instead dispatches a local Ollama model against
the diff; a clean local verdict passes the gate as `PR automation: gate (local fallback)`
rather than blocking it. That title always names the weaker reviewer — treat it as a
signal to still fix the primary path's root cause, not as a fully reviewed pass.

## Local-authority mode — when the paid lane is capped

When API credits are exhausted, evaluations fail rather than review, and the operator's
machine becomes the source of truth (#206). `vibey-gh local-authority` keeps remotes
tracking green local state: each pass pushes any clean, check-passing local branch that
is ahead of its upstream, with an explicit pre-fetch `--force-with-lease` so remote work
this machine has not integrated always refuses the push. Run it as a login daemon
(launchd/systemd) pointing at `vibey-gh local-authority` with no `--once`; reviews meanwhile
come from `vibey-gh local-review` verdicts recorded on the pull request.

Recovery is automatic by design: every evaluation tries the paid lane first, so the
human's only act is adding credits — the next evaluation simply succeeds, and this loop
idles (nothing-ahead is a no-op).

## Everything else

Enable Actions write permissions, PR creation,
GitHub Pages via Actions, Packages, Releases, and Deployments. Use workflow dispatch for
recovery. Inspect exact run and head SHA before retrying. Never solve a blocked release by
deleting, force-pushing, weakening a gate, or switching production to TestPyPI.

To retry one issue, dispatch `Issue automation` with its number; `vibey-gh
issue-automation list-eligible` shows what the scheduled sweep would pick up. A redispatch
of unchanged issue text is a no-op, so retrying is safe. An issue labelled
`vibey-gh:solve-blocked` is waiting on a human decision named in the issue's state comment,
and one labelled `vibey-gh:solve-exhausted` has spent its budget; editing the issue body
restates the request and starts a new lineage. To stop the feature without uninstalling it,
set `[issue_automation].enabled = false` in reviewed configuration.

When a bug in privileged workflow code itself blocks a repair PR from repairing its own
gate, dispatch `Automation bootstrap` (see [Workflows](workflows.md)) with the exact PR
number, exact head SHA, and explicit authorization. It requires administrator permission
and every independent gate already passing on that SHA, and it is the only path that
squash-merges to `develop` without an ordinary PR automation review.

To preview what `Branch sync` would rebase, close, update, or leave without mutating
anything, dispatch it manually with `dry_run = true`; the decisions are printed to the run
summary. The nightly schedule run of its `heal` job refills the repair budget of every pull
request labeled `vibey-gh:repair-exhausted`, up to `branch_sync.max_self_heals` times per
lineage, and re-dispatches `PR automation` against each healed PR's exact head SHA. Once
that budget is spent for a lineage, the label stays and only a human — typically by pushing
a new commit or editing the PR — starts a fresh lineage. See [Workflows](workflows.md) and
`[branch_sync]` in [Configuration](configuration.md).

When Conventional Commits rewrites a topic branch, synchronize the local checkout before
new work. Preserve unpushed work first, then use `git fetch origin` and rebase it onto the
new remote head; if there is no unpushed work, reset the local topic branch to its explicit
`origin/<branch>` ref. Never run either operation against `develop` or `main`. The workflow
has no per-run bypass: correct the commit locally when a fork or merge-containing branch
cannot be repaired automatically. Disable the managed workflow only through reviewed
`[install].workflows` configuration, which makes the policy change visible to CI.
