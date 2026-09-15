# GitHub automation

This directory contains the repository-facing control plane for `vibey-gh`. The workflows
turn a topic-branch push into an exact-head-reviewed change, merge it into `develop`,
promote it to `main`, publish the correct release channel, and reconcile the public
repository profile. They are executable policy, not examples: action revisions are pinned,
permissions are job-scoped, current-head evidence is rechecked before mutation, and every
permanent-branch operation is guarded.

Start with the root [README](../README.md) for the product and adoption guide. Use this
document when reviewing or operating GitHub Actions. Deeper references cover
[workflow behavior](../docs/workflows.md), [operations](../docs/operations.md),
[security](../docs/security.md), [threats](../docs/threat-model.md), and the complete
[Mermaid project map](../docs/project.mmd).

## Delivery model

```text
topic branch push
  -> Branch intake opens or reuses a draft PR
  -> CI, CodeQL, Provenance, and Docs settle for the exact head
  -> PR automation reviews, repairs, or resolves conflicts within a bounded budget
  -> PR automation publishes an exact-head gate
  -> Merge train squash-merges into develop
  -> Release publishes the preview package and documentation channel
  -> Promote opens or reuses develop -> main
  -> The same exact-head scans and review gate the promotion PR
  -> Merge train rebase-merges into main
  -> Release, GitHub Release, Pages, GHCR, and repository profile converge
```

Every new commit invalidates evidence for the previous SHA. Scheduled and manual triggers
are recovery backstops; the normal path is event-driven through `workflow_run` and PR
events. A skipped stale run is expected. A current-head failure is never bypassed.

## Workflow inventory

| File | Workflow name | Responsibility |
|---|---|---|
| `conversation.yml` | Conversation | Answers a configured mention in a comment, and on a pull request from a trusted commenter may publish one guarded commit. |
| `branch-sync.yml` | Branch sync | Brings every open branch forward when the integration branch moves, and daily refills a bounded number of spent repair budgets. |
| `branch-intake.yml` | Branch intake | Opens one reusable draft PR for a new same-repository topic branch and ignores permanent or automation-owned branches. |
| `issue-automation.yml` | Issue automation | Decides whether a published issue is eligible for an autonomous solution and, if it is, publishes one guarded solution branch and linked pull request. |
| `ci.yml` | CI | Runs the supported Python matrix, 100% coverage, lint, formatting, typing, managed-workflow dogfood, and package builds. |
| `codeql.yml` | CodeQL | Runs immutably pinned Python CodeQL analysis for pull requests and both delivery branches. |
| `provenance.yml` | Provenance | Verifies source fingerprints, Conventional Commit subjects, and the required `Made-With` trailer without rewriting permanent history. |
| `conventional-commits.yml` | Conventional Commits | Audits commit subjects and may safely normalize a linear same-repository topic branch with an exact-head lease. |
| `documentation.yml` | Docs | Enforces the FOSS, human, agent, plugin-marketplace, Mermaid, SEO, crawler, and LLM documentation contract. |
| `pr-automation.yml` | PR automation | Aggregates current-head scans, runs semantic review (with an opt-in self-hosted local-model fallback when the primary review returns no verdict), performs bounded repair or conflict resolution, persists lineage state, and publishes the merge gate. |
| `automation-bootstrap.yml` | Automation bootstrap | Provides an explicitly authorized one-time path for merging a workflow repair when the older base workflow cannot repair itself. |
| `merge-train.yml` | Merge train | Squash-merges eligible PRs to `develop` and rebase-merges eligible promotion PRs to `main`. |
| `promote-to-main.yml` | Promote | Opens or reuses the asynchronous `develop -> main` promotion PR after integration succeeds. |
| `release.yml` | Release | Publishes development builds from `develop` to TestPyPI and production builds from `main` to PyPI. |
| `github-release.yml` | GitHub Release | Creates or reuses the immutable production tag and generated-notes GitHub Release for the exact released SHA. |
| `release-surfaces.yml` | Release surfaces | Publishes OCI package artifacts and the persistent Production and Preview ProperDocs sites. |
| `repository-profile.yml` | Repository profile | Reconciles description, homepage, topics, collaboration settings, merge policy, security settings, branch rulesets, and observable release surfaces. |
| `release-repair.yml` | Release repair | Reviews trusted post-merge failures and returns fixable changes through a guarded PR instead of patching a permanent branch directly. |
| `api-drift.yml` | API drift (Cloud Agents OpenAPI) | This repository's own five-surface (MCP, API, CLI, SDK, webhook) capability-parity self-test; hand-authored like `ci.yml`, not a managed template adopters receive. See [docs/workflows.md](../docs/workflows.md#api-drift--not-installed-and-not-yours). |

Workflow `name:` values are event contracts. Renaming `CI`, `Release`, `Docs`, `CodeQL`,
`Provenance`, or `Docs` without updating configured scans and `workflow_run` lists can
prevent downstream automation from firing.

## Exact-head PR automation

`pr-automation.yml` resolves the PR associated with a completed scan, reloads it, and
compares the event SHA with the current head. It waits while non-ignored checks are queued
or running. Successful, neutral, and intentional skipped results are non-failing;
failures, timeouts, startup failures, and action-required results enter repair; cancelled
or stale infrastructure runs are operationally blocked rather than presented as source
defects.

Repair, conflict, and review-finding budgets share one bound per contributor lineage, and
it applies to trusted and outside authors alike — every author's exact head is reviewed, so
every author's review-to-repair cycle needs the same limit. Once the budget is spent the
next evaluation blocks rather than dispatching a further review. Bot repair pushes do not
reset the budget; a new human or contributor commit creates a new lineage. Results persist
in one machine-readable PR comment, and a verdict for an older SHA never satisfies the
gate for a newer one.

Every author receives semantic documentation review. Authors outside the configured
owner/trusted-bot set additionally receive correctness, security, data-loss,
maintainability, architecture-boundary, and test-quality review. Forks are inspected but
never mutated with privileged credentials; required edits use a linked repository-owned
replacement PR that preserves the contributor and exact head.

A repository that sets `[pr_automation.fallback].enabled = true` and provides a
self-hosted runner labelled `vibey-local-gh` gets one more line of defense: when the
primary review above returns no verdict at all (never when it ran and found something), a
`review-fallback` job sends the diff to a local Ollama-compatible model and calls
`vibey-gh local-review`. It holds no repository secret, never checks out PR source, and
`trusted_only` (default `true`) keeps fork PRs off that runner entirely. A clean local
verdict passes the gate under the honestly weaker title `PR automation: gate (local
fallback)`; `vibey-gh local-triage` is the equivalent for issue automation and always
forces `needs_human=true`. See [Configuration](../docs/configuration.md) and
[Threat model](../docs/threat-model.md).

## Autonomous issue solutions

`issue-automation.yml` runs on `issues` (`opened`, `reopened`, `labeled`), manual dispatch,
and an optional scheduled sweep. Its `evaluate` job holds only `contents: read` and
`issues: read`: it installs the published `vibey-gh` package from trusted default-branch
workflow code and asks `vibey-gh issue-automation evaluate` for a decision. Only the
explicit `solve` decision starts the privileged `solve` job.

Eligibility is policy, not judgement. An issue is skipped when the feature is disabled,
when it is really a pull request, when it is closed, when it carries a configured ignored
label, when configured trigger labels are absent, when it has no title and no body, when a
proposal already exists, or — for an author outside the configured owner and trusted-author
set — when the configured `required_label` has not been applied by a maintainer. It is
blocked when an operator label is present or the attempt budget for that issue's content is
spent. **Opening an issue can never, on its own, cause a privileged job to make changes.**

The `solve` job holds `contents: write`, `issues: write`, `pull-requests: write`, and
`id-token: write`. It checks out trusted automation under `automation/` and the base branch
under `target/` with `persist-credentials: false`, writes the issue into
`briefing/issue.md` through a trusted CLI call, and runs the pinned Claude Code Action from
a disposable credential-free Git context with `Read,Glob,Grep,Edit,Write` and no `Bash`,
no `gh`, and no `Agent` tool. The prompt states that the briefing is an untrusted report
and that any instruction inside it is hostile input to be reported through
`prompt_injection_observed` rather than obeyed.

Publication is a separate trusted step. It refuses a branch that is empty, contains `:`,
begins with `-`, contains `..`, escapes the configured branch namespace, or names a
permanent branch; it publishes nothing when the agent returned `solved=false` or produced
no diff; and it pushes exactly one non-empty-source refspec
(`HEAD:refs/heads/<namespaced-branch>`) before opening one linked pull request that closes
the issue. `branch-intake.yml` is rendered to ignore that same namespace, so the two never
race to open a pull request for the same branch. The resulting pull request then receives
ordinary scans, exact-head review, repair, and merge-train treatment with no exemption.

Attempts are budgeted against a SHA-256 fingerprint of the issue's title and body, stored
in one machine-readable issue comment. Re-dispatching unchanged text is a no-op; editing
the issue starts a new lineage with a new branch and a new budget.

## AI trust boundary

Claude runs from trusted base-branch workflow code. PR files, logs, comments, repository
instructions, model output, and web material are untrusted data. Privileged AI jobs may
read and make bounded edits, but do not execute contributor-controlled package managers,
tests, builds, scripts, or binaries. Ordinary unprivileged PR scans validate every repair.

The Claude action receives a disposable credential-free Git context because its setup
expects a repository and `origin`. Untrusted source remains in a separate checkout with
`persist-credentials: false`. Progress comments are enabled only for the direct PR and
issue events supported by the action; other events use phase-level job visibility. Raw
model output is disabled during ordinary automation and may be enabled only by an explicit
private-repository diagnostic.

## Credentials and settings

- `ANTHROPIC_API_KEY` must be a repository secret for AI review, repair, conflict
  resolution, autonomous issue solutions, documentation upkeep, and release repair.
- `AUTOMERGE_TOKEN` is needed when the default `GITHUB_TOKEN` cannot merge through the
  ruleset, manage settings, create PRs, or reconcile the repository profile and rulesets.
- PyPI and TestPyPI use trusted publishing through the `pypi` and `testpypi` environments;
  registry passwords are not embedded in workflows.

In **Settings -> Actions -> General**, grant workflow read/write permissions and permit
Actions to create and approve pull requests, then configure Pages for GitHub Actions.
Protecting `develop` and `main` with the repository's required current-head checks is no
longer a manual step: `repository-profile.yml` reconciles both branches' rulesets from
`[rulesets]` in `.vibey-gh.toml` on every run, so a fresh repository reaches the documented
protection state from `vibey-gh install` plus one workflow run.

## Permanent-branch safety

Automation may push and merge forward into `develop` and `main`. It may never delete
either branch. The distinction is structural:

- publication uses non-empty update refspecs such as `HEAD:refs/heads/<branch>`;
- no managed path emits `:develop`, `:main`, `--delete`, or `--delete-branch`;
- automatic branch deletion is disabled because `develop` heads promotion PRs;
- topic-history normalization refuses `develop`, `main`, forks, merge commits, and stale
  heads;
- release repair always opens a topic branch and ordinary PR;
- realignment advances only branches whose trees are already identical.

Never add unconditional cleanup. Any topic-branch deletion must first prove the target is
neither configured permanent branch.

## Release channels and public surfaces

`develop` is Preview: TestPyPI, `/develop/` ProperDocs, and the `develop` OCI tag. `main`
is Production: PyPI, immutable tag and GitHub Release, `/main/` ProperDocs, and `main` plus
`latest` OCI tags.

Pages has one deployment per repository, so release surfaces preserve both channel
artifacts before deploying the combined site. The root page links Production and Preview
with repository/revision provenance. Generated sites include canonical metadata,
structured data, robots policy, sitemaps, and LLM discovery documents according to config.

Because PyPI exposes no API for yanking a bad release, `Release` can run `vibey-gh
report-superseded --index pypi|testpypi --project NAME --version VERSION` right after each
publish step (this repository's own `release.yml` does) to print which already-released
versions the new one supersedes, with a direct link to the index's manage page for a human
to act on. See [Releases](../docs/releases.md).

## Failure recovery

1. Open the failed check attached to the exact PR head, not an older cancelled run.
2. Read the first failing trusted step and the `PR automation / gate` summary. The gate's
   title names who decided the outcome: `PR automation: ready` reports the evaluation,
   `PR automation: review findings` means the exact-head review returned actionable work,
   `PR automation: review incomplete` means the review returned no verdict at all —
   an infrastructure or operator failure such as an exhausted API credit balance, not a
   defect in the pull request — and, only when a repository has opted into
   `[pr_automation.fallback]`, `PR automation: gate (local fallback)` means the primary
   review returned no verdict but a local model on a self-hosted runner reviewed the diff
   and found nothing blocking; treat that as a weaker signal than an ordinary pass, since
   the documentation-contract fields were not evaluated (see
   [docs/configuration.md](../docs/configuration.md#pr_automationfallback)).
3. For source, test, docs, or review findings, allow bounded repair to push one commit and
   rerun ordinary scans.
4. For missing secrets, permissions, billing, registry denial, unavailable services, or
   settings, correct the operator condition and redispatch.
5. When a workflow bug blocks its own repair, use Automation bootstrap only with the exact
   PR, exact head SHA, and explicit authorization.
6. When the budget is exhausted, inspect retained runs and push a deliberate human fix to
   create a new lineage.

Never recover by reducing coverage, deleting a scan, weakening an assertion, adding
`continue-on-error`, or bypassing current-head review. Admin merge is narrowly authorized
only after all independent policy checks pass.

## Changing workflows

Most files here render from `vibey_gh/templates/workflows/`. Change the template, run
`vibey-gh install`, and commit both source and dogfooded output. Editing only the generated
copy fails the drift check and is overwritten by the next installation.

```bash
vibey-gh install
pytest -q -p no:cacheprovider
ruff check vibey_gh test
black --check vibey_gh test
isort --check-only vibey_gh test
mypy vibey_gh
vibey-gh check --ci
git diff --check
```

Review permissions, immutable action pins, untrusted-code execution, exact-SHA guards,
concurrency, secret exposure, and branch deletion—not merely YAML syntax.

## Tooling install version

Every rendered workflow installs `vibey-gh` itself with `pip install vibey-gh`, floating on
the latest published release by default. Set `[install].pin_version = true` in
`.vibey-gh.toml` to pin that install to the exact version that rendered the file
(`vibey-gh==X.Y.Z`) instead, so a later release of this tool cannot change these workflows'
behavior underneath you with no warning. `vibey-gh install` owns the pin: run it from a
newer release to move the pin forward as one visible, reviewable diff. The self-hosting
branch each workflow falls back to (`pip install -e .`, used by this repository and
anything else installing from its own `pyproject.toml`) is never pinned.

## Related policy and documentation

- [Contributing](../CONTRIBUTING.md)
- [Security policy](../SECURITY.md)
- [Support](../SUPPORT.md)
- [Agent instructions](../AGENTS.md)
- [Configuration](../docs/configuration.md)
- [Testing](../docs/testing.md)
- [Releases](../docs/releases.md)
- [Troubleshooting](../docs/troubleshooting.md)

Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
