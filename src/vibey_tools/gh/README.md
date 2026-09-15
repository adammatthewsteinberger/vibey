# vibey-gh

Shipping a change safely through review, merge, versioning, and release usually means
hand-wiring a dozen GitHub Actions steps — and they drift out of sync, silently skip a
check, or let a stale result approve code that has since changed. `vibey-gh` replaces that
hand-wired path with one event-driven, auditable contract: push a branch, and the tooling
carries it through review, repair, merge, release, and documentation on its own, stopping
only when a human decision is genuinely required.

Three ideas make that safe to run unattended:

- **Exact-head evaluation.** Every decision — a passing check, an AI review, a merge — is
  tied to the exact current commit SHA. A result computed for an older commit can never
  wave through a newer one, even if nothing else about the pull request changed.
- **The merge train.** One automated process merges a pull request only once its exact
  current head is green, conflict-free, and approved, so merges happen one at a time in a
  controlled sequence instead of racing each other.
- **Dual-channel releases.** Two independent publishing channels — a `develop`-based
  preview channel (TestPyPI, preview docs) and a `main`-based production channel (PyPI,
  production docs) — so a preview build can never be mistaken for a production one.

Around that sits provenance fingerprinting, derived version bumps, comprehensive
documentation maintenance, and post-release branch realignment — all covered below.

**No dependencies.** Everything is stdlib. This runs in every CI job of every repository
that adopts it, so a dependency it grows is a dependency all of them grow.

> **In one sentence:** install `vibey-gh` once, describe your repository in
> `.vibey-gh.toml`, and let exact-head gates carry a change from its first push through
> review, bounded repair, protected-branch merge, release, documentation, packages, and
> provenance—while stopping for conditions that require an operator.

## Start here

- **New to the project?** Start with [The mental model](#the-mental-model).
- **Evaluating the project?** Read [Why vibey-gh](#why-vibey-gh), then
  [What happens after a push](#what-happens-after-a-push).
- **Installing it?** Follow [Requirements](#requirements), [Quick start](#quick-start),
  and [Adoption checklist](#adoption-checklist).
- **Operating it?** Keep [Workflows](#workflows), [Failure and recovery model](#failure-and-recovery-model),
  [Troubleshooting](#troubleshooting), and [.github/AUTOMATION.md](.github/AUTOMATION.md) (workflow
  inventory, AI trust boundary, and admin recovery paths) nearby.
- **Extending it?** Begin with [Architecture](#architecture),
  [Security model](#security-model), and [CONTRIBUTING.md](CONTRIBUTING.md).

### What vibey-gh does—and does not do

`vibey-gh` is a repository delivery control plane, not a replacement for your test suite,
package builder, or application runtime. Your repository owns what “correct” means. This
project owns the transitions around that evidence: when a result is current, when a repair
is permitted, when a protected branch may advance, which release channel receives an
artifact, and what proof travels with it.

It is deliberately opinionated about four invariants:

1. **Only exact-head evidence counts.** A green check or review for an older commit cannot
   authorize the current commit.
2. **Repair may improve the work, never the standard.** Automation cannot lower coverage,
   remove a required job, soften an assertion, or disguise an operational failure as code.
3. **Permanent branches may advance but may never be deleted.** Managed workflows can
   merge into `develop` and `main`; no managed path emits a deletion refspec for either.
4. **Untrusted work is data in privileged jobs.** Source and logs may be inspected or
   edited, but contributor-controlled commands are not executed beside write credentials.

## The mental model

Think of `vibey-gh` as an assembly line for your repository's changes. You push code to a
branch; the tooling then handles the parts that would otherwise mean babysitting an Actions
tab or manually clicking "merge": it opens a pull request, waits for your tests to pass,
has an AI reviewer look for problems, attempts one bounded automatic fix if something is
wrong, merges the result once everything checks out, derives a new version number,
publishes the package, and updates the documentation site — all tied to the exact commit
that was actually reviewed, so nothing is ever approved based on a stale result. If a step
needs a human — a missing secret, a failing external service, a request too ambiguous to
act on — the automation stops and says so instead of guessing.

The rest of this document assumes no prior familiarity with those steps. Later sections
build on this picture as they introduce project-specific terms and configuration.

## Why vibey-gh

GitHub can run tests, but a dependable open-source delivery system needs much more than a
green test job. It must intake branches, keep documentation honest, review outside work,
repair actionable failures without weakening gates, merge through protected branches,
derive versions, publish to the correct registry, create releases and packages, deploy
discoverable documentation, preserve provenance, and recover safely when a trusted
post-merge job fails. `vibey-gh` installs that complete event-driven path as one portable,
auditable contract.

Use it when you want `develop` to be the integration channel, `main` to be production,
and every transition between them to be reproducible and policy checked.

## Requirements

- Python 3.11 or newer, Git, and the GitHub CLI (`gh`).
- A GitHub repository with Actions enabled and Pages configured for Actions deployments.
- `ANTHROPIC_API_KEY` for AI review, repair, conflict resolution, and documentation upkeep.
- `AUTOMERGE_TOKEN` when the default Actions token cannot merge or manage repository settings.
- PyPI and TestPyPI trusted-publishing environments when Python publication is enabled.

The installed Python runtime has no third-party dependencies. Workflow-only tools are
pinned to immutable action revisions and run in GitHub-hosted jobs.

## Quick start

```bash
pip install vibey-gh
vibey-gh install
```

Commit the generated hooks, workflows, assets, and configuration; configure the required
secrets and publishing environments; then verify the complete installation:

```bash
vibey-gh check --ci
git status --short
```

Push a topic branch. Branch intake creates a draft PR, exact-head scans decide when it is
stable, and the event chain handles review, repair, merge, promotion, publication, docs,
tagging, GitHub Release creation, and repository-profile reconciliation.

### Adoption checklist

1. Create or confirm permanent `develop` and `main` branches.
2. Install `vibey-gh` on a topic branch and review every generated file before committing.
3. Author your own `CI` and `Release` workflows with those exact names; `install` does not
   render them, and the rest of this checklist assumes they exist. See
   [What gets installed](#what-gets-installed) for the required `Release` behavior.
4. Add a repository-level `ANTHROPIC_API_KEY`; environment-only secrets are not available
   to the PR automation jobs that perform guarded review and repair.
5. Add `AUTOMERGE_TOKEN` when the default Actions token cannot merge through your ruleset,
   update repository settings, or create the required pull requests.
6. In **Settings → Actions → General**, grant read/write workflow permissions and allow
   Actions to create and approve pull requests.
7. Configure GitHub Pages to deploy from **GitHub Actions**.
8. Configure `testpypi` and `pypi` trusted-publishing environments if this is a Python
   package. `develop` is the preview channel; `main` is production.
9. Configure the branch ruleset. Require your ordinary scans plus
   `PR automation / gate`; do not use a rule that automatically deletes `develop` after a
   promotion merge.
10. Run `vibey-gh check --ci`, inspect `git diff`, commit the generated assets, and push.
11. Confirm the first branch creates one draft PR and that the exact-head gate—not an older
    workflow result—controls its merge.

### What gets installed

The installer manages `.githooks/`, selected files under `.github/workflows/`, and the
release-site assets used by the dual-channel Pages deployment. Existing hooks are moved to
`<hook>.local` and chained. Managed workflow files are replaced when their rendered source
changes; opt out of individual workflows with `[install].workflows` rather than editing a
generated copy that the next installation will overwrite.

Every managed workflow installs this tooling with `pip install vibey-gh`, floating on
whatever the latest published release is, by default — so upgrading changes nothing until
you ask. Set `[install].pin_version = true` to pin that install to the exact version that
rendered the file (`vibey-gh==X.Y.Z`) instead; `vibey-gh install` then owns bumping the pin
on every future release, as one visible diff, rather than it moving silently underneath you.
The self-hosting path this repository uses to install itself from source is never pinned.

`install` does **not** render `CI` or `Release` workflows: every repository's build, test,
and publish steps are different, so these two stay hand-authored by the adopting
repository. This is intentional, not an oversight, but the names and behavior are load
bearing: `release-repair.yml` watches for a `workflow_run` named exactly `CI`, and
`github-release.yml`, `release-surfaces.yml`, and `release-repair.yml` all watch for one
named exactly `Release`. Your `Release` workflow must run on `develop` and `main`, derive
and apply the version with `vibey-gh version --apply` (or an equivalent explicit
`--dev`/`--since` invocation), build the package, and publish it through the `testpypi`
(from `develop`) and `pypi` (from `main`) trusted-publishing environments named in
[Requirements](#requirements). Skip or misname either workflow and the installer, gate, and
docs will all stay green while GitHub Release creation, release surfaces, repository-profile
reconciliation, and release repair silently never trigger.

### What happens after a push

An eligible issue joins this same path at the top, having produced the branch itself:

```text
issue published
      │
      ▼
eligibility policy (author trust, labels, budget, content fingerprint)
      │
      ├── ineligible ──► skipped or blocked, with a stated reason
      └── eligible ────► one bounded solution attempt on a namespaced branch
                                      │
                                      ▼
                       one commit + one linked PR that closes the issue
```

```text
topic branch push
      │
      ▼
one reusable draft PR
      │
      ▼
all configured scans settle for the exact head SHA
      │
      ├── actionable failure ──► bounded AI repair ──► new SHA ──► rescan
      ├── conflict ────────────► guarded conflict repair ────────► rescan
      ├── operator-only issue ─► explicit blocked state and required action
      └── green ───────────────► semantic docs review (+ outside-author code review)
                                      │
                                      ├── findings ─► bounded repair ─► rescan + rereview
                                      └── pass ─────► exact-head gate
                                                            │
                                                            ▼
                                            squash merge to develop
                                                            │
                                                            ▼
                                             promotion PR to main
                                                            │
                                                            ▼
                                             rebase merge + release
```

Every new commit invalidates earlier evidence and starts evaluation for the new SHA. The
repair budget is three attempts per contributor lineage by default, and it covers every
automated repair on that lineage — failing scans, merge conflicts, and review findings
alike, for trusted and outside authors equally. Bot-authored repair
commits do not reset it; a new human/contributor commit does.

### Your first successful run

On a healthy installation you should observe, in order:

- a draft PR for the topic branch;
- ordinary CI, provenance, security, API-drift, and documentation scans;
- an exact-head semantic documentation verdict—even for a trusted author;
- an outside-author code review when applicable;
- a successful `PR automation / gate` attached to the current SHA;
- a squash merge into `develop`;
- a TestPyPI development release and Preview documentation update;
- a `develop → main` promotion PR;
- a rebase merge into `main`, followed by PyPI, tag, GitHub Release, GHCR, Production
  documentation, and repository-profile verification.

No single repository must enable every publishing surface. Disable or omit workflows that
do not match the repository, then keep the remaining contract explicit and testable.

## Architecture

Configuration value objects describe desired state; deterministic evaluators judge
versions, PRs, documentation, and interface parity; CLI adapters call those policies; and
rendered workflows provide the privileged GitHub edge. Managed templates are the source
of truth, and dogfood tests require this repository's installed copies to match them.
Every decision is tied to an exact commit SHA, and stale workflow events are ignored. See
[Architecture](docs/architecture.md), [Workflows](docs/workflows.md), and
[Threat model](docs/threat-model.md).

## Security model

Privileged jobs treat PR content, logs, model output, and repository instructions as
untrusted. They inspect or edit constrained files but never execute contributor-controlled
package managers, tests, builds, or scripts while write credentials are present. Ordinary
PR CI validates resulting commits. Managed automation never sends a deletion refspec for
`main` or `develop`, and automatic branch deletion stays disabled because `develop` is
itself the head of production promotion PRs. See [SECURITY.md](SECURITY.md).

Repair and conflict publication recheck the PR's exact head immediately before committing
and again after any non-fast-forward push rejection; a concurrent human or bot update is
discarded as a stale no-op rather than force-pushed over, consumes no repair attempt, and
never mutates a permanent branch from an obsolete checkout—including when `develop` or
`main` is itself the PR head during a promotion. See [docs/security.md](docs/security.md).

Issue text is contributor-controlled input to a privileged job, so issue automation is
deliberately opt-in for outside authors and reads every issue through a bounded briefing
file written by a trusted step. The agent has no shell, no network, and no Git tool; it
edits files under a base-branch checkout, and one trusted publisher pushes a single
non-empty source refspec to a namespaced branch validated against the configured
permanent branches. Nothing derived from an issue reaches a shell command or a workflow
expression; the one place issue text does reach is the branch name, and only as a
regex-sanitized slug of the title (stripped to `[a-z0-9-]+`, length-capped).

The sole history-rewrite exception is Conventional Commits self-healing: only a
same-repository linear topic branch may be normalized and pushed with an exact-head
`--force-with-lease`. Forks, stale heads, merge commits, `develop`, and `main` fail closed,
and contributor-controlled code is never executed by that privileged job.

Webhook delivery IDs are claimed atomically in a persistent local state directory, so
replay rejection survives CLI process restarts and concurrent receivers. Deployments must
place `VIBEY_GH_WEBHOOK_STATE_DIR` on durable, access-controlled storage and retain the raw
request bytes for HMAC verification; see [the CLI and adapter reference](docs/cli.md).

The opt-in local-model review/triage fallback runs on a self-hosted runner, which GitHub
itself warns against exposing to public-repository pull requests. `trusted_only` (default
`true`) keeps fork PRs off that runner entirely, and the job holds only `contents: read` —
no secret, and no token capable of pushing, merging, or mutating the repository. Trusted
steps use `gh`/`git` to assemble the diff or issue text; only the local model's own
execution is confined to the loopback inference port, with no shell, `gh`, or network
access of its own. See [Threat model](docs/threat-model.md) for the full boundary.

## Commands

| Command | Human purpose |
|---|---|
| `vibey-gh check [--apply] [--commits RANGE] [--ci]` | Verify installed assets, file fingerprints, commit trailers, traceable branch logging, documentation, marketplace structure, and interface parity; optionally add a missing source header or collapse a header duplicated within a file. |
| `vibey-gh install` | Render configured workflows, install/chains hooks, and install release-site assets. |
| `vibey-gh version [--since REF] [--dev BUILD] [--apply] [--explain]` | Derive, explain, print, or apply the next release version. |
| `vibey-gh trailer` / `trailer-key` | Print the configured provenance trailer or its key for scripts and workflows. |
| `vibey-gh conventional-message [--file COMMIT_EDITMSG]` / `conventional-check --commits BASE..HEAD` | Normalize one commit message or audit every subject in a revision range against Conventional Commits. |
| `vibey-gh merge-train [--pr N] [--method METHOD] [--dry-run]` | Judge one or all PRs and merge only policy-ready exact heads. |
| `vibey-gh pr-automation evaluate --pr N --head-sha SHA` | Return the stable structured decision for one exact PR head. |
| `vibey-gh pr-automation ready-draft --pr N --head-sha SHA` | Mark a stable exact draft head ready without racing newer commits. |
| `vibey-gh pr-automation record-review` / `record-repair` | Persist machine-readable lineage state used by retries and exact-head gating. |
| `vibey-gh pr-automation mirror-fork --pr N` | Preserve a fork head in a linked repository-owned replacement PR when repair needs write access. |
| `vibey-gh pr-automation ensure-labels` | Idempotently create the automation’s operational labels. |
| `vibey-gh issue-automation evaluate --issue N` | Return the stable structured decision for one issue, including its solution branch. |
| `vibey-gh issue-automation context --issue N [--output FILE]` | Render one issue as a bounded, explicitly untrusted briefing for an agent to read. |
| `vibey-gh issue-automation record-solution --issue N --input JSON` | Persist the machine-readable attempt lineage a retry and its budget depend on. |
| `vibey-gh issue-automation list-eligible` | List every open issue a recovery sweep should dispatch. |
| `vibey-gh issue-automation ensure-labels` | Idempotently create the issue automation’s operational labels. |
| `vibey-gh promote [--no-wait]` | Open or reuse the asynchronous `develop → main` promotion PR. |
| `vibey-gh github-release --target SHA [--version VERSION]` | Create or reuse an immutable tag and GitHub Release for an exact production SHA. |
| `vibey-gh realign` | Align identical `develop` and `main` trees after a rebase merge without discarding work. |
| `vibey-gh paper --author NAME` | Render docs/paper.md — the repository's journal-grade research paper — as an IEEEtran LaTeX document, one TeX compile away from a submission-shaped PDF. |
| `vibey-gh book --site-dir site --title T --author A` | Export the built docs site as an EPUB 3.0 plus a KDP print-ready HTML — the docs as a publishable book, chapters in nav order. |
| `vibey-gh local-authority --once` | The capped-lane sync loop: green local branches reach their remotes by themselves while local is the source of truth; drop `--once` for the daemon form. |
| `vibey-gh failover --once` | The operator-seat failover engine: paid lane down, the seat moves to the first healthy local agent (qwenloop, then opencode) and moves back on recovery — configured per machine in `~/.config/vibey-gh/failover.toml`, off until enabled; drop `--once` for the daemon form. |
| `vibey-gh report-superseded --index pypi\|testpypi --project NAME --version VERSION` | Report which prior releases a published version supersedes, since PyPI has no yank API; never yanks anything itself. Add `--governance-since REF` to evaluate Article V.4: a ratified governance change names every previous release, zero exceptions. |
| `vibey-gh local-review [--diff FILE]` | Review a diff with a local Ollama-compatible model when the primary paid review returns no verdict at all. Opt-in fallback; see `[pr_automation.fallback]`. |
| `vibey-gh doctor` | Offline adoption preflight: reads `.vibey-gh.toml`, `pyproject.toml`, and `.github/workflows/` on disk (no network, no credentials, no execution) to catch a config key silently ignored in the wrong section, a merge train stuck forever with no installed gate workflow, a ruff rule that fails every stamped file, contending Pages deployers, and superseded fingerprint headers. |
| `vibey-gh local-triage [--issue FILE]` | Triage an issue with the same local model when the primary paid solver produces nothing. Always marks the result `needs_human`. |
| `vibey-gh pr-automation self-heal [--pr N]` | Refill a spent repair budget, itself bounded so a permanent failure still stops. |
| `vibey-gh conversation evaluate\|context\|reply\|record-response` | Decide, brief, answer, and budget one comment-driven interaction. |
| `vibey-gh reconcile-branches [--dry-run]` | Rebase, close, or leave each open branch stranded by a realign rewrite. |
| `vibey-gh rulesets [--dry-run]` | Reconcile the integration and release branch rulesets from `[rulesets]`. |
| `vibey-gh sdk|api|mcp|webhook CAPABILITY` | Invoke the same canonical capability through each supported public surface. |

Run `vibey-gh --help` and read [docs/cli.md](docs/cli.md) for the full reference.

`install` also declares `CHANGELOG.md merge=union` in `.gitattributes`. Every branch
appends to the same changelog section, so without it every merge strands every other open
branch on a conflict that carries no information and has to be resolved by hand. The union
driver keeps both sides. It only takes effect from the branch being merged *into*, so it
has to reach the integration branch before the topic branches that follow benefit. An
existing `.gitattributes` is appended to, never rewritten.

`install` writes the git hooks and workflow files into your repository and points
`core.hooksPath` at them. A hook you already have is moved aside to `<name>.local` and
chained, never discarded — adopting this should not silently drop checks somebody thought
were important.

## What it does

### Provenance, enforced in two places

Every code change carries a fingerprint. Source files get a header comment; **every commit
gets a Conventional Commit subject and a trailer**. The local hook normalizes the subject
before appending provenance, and CI audits the complete PR range. The trailer is what makes
the rule total — a change to a Markdown file or
a JSON manifest still arrives as a commit, and the commit is fingerprinted even when the
file cannot be.

```bash
vibey-gh check                 # are the hooks installed and the fingerprints intact?
vibey-gh check --apply         # add missing file headers and dedupe a repeated header
vibey-gh check --commits main..HEAD    # and every commit trailer in a range
```

The `pre-push` hook refuses the push if either half is missing, to any branch, local or
remote. `git push --no-verify` still works, because a hook that cannot be bypassed in an
emergency gets uninstalled instead; CI applies the same rule server-side, so skipping it
locally defers the failure rather than avoiding it.

### Advanced, fully traceable branch diagnostics

Every configured Python source is compiled during `vibey-gh check`, and every control-flow
opcode must be supported by the package-wide branch tracer. Enable it only when diagnosing
a run; normal commands remain quiet:

```bash
VIBEY_GH_DEBUG=1 vibey-gh check
VIBEY_GH_DEBUG=1 VIBEY_GH_DEBUG_LOG=.vibey-gh/branch-trace.jsonl vibey-gh merge-train
```

The JSONL stream records each branch evaluation and, when CPython exposes the successor,
its taken or fallthrough outcome. Every event includes a schema version, trace ID,
monotonic sequence, UTC and monotonic timestamps, PID, thread ID, source, function, line,
bytecode offset/opcode/target, GitHub run/attempt/SHA correlation, the previous event hash,
and its own SHA-256 hash. That produces an ordered, tamper-evident chain that can be joined
back to a CI invocation. It records control-flow metadata only—never locals, arguments,
return values, exception messages, environment values, or secrets. Set
`VIBEY_GH_TRACE_ID` to propagate an existing correlation ID; otherwise a UUID is generated.

`vibey-gh` itself only ever instruments its own installed package: `VIBEY_GH_DEBUG` traces
`vibey_gh`'s internals, not a consuming project's source tree. Projects embedding
`vibey_gh.debugging.enable(roots=(your_package_dir,))` directly get branch tracing scoped
to their own code instead.

### Versions derived, not remembered

```bash
vibey-gh version --since origin/main --explain     # what should this release be?
vibey-gh version --since origin/main --apply       # write it to every version file
vibey-gh version --dev "$GITHUB_RUN_NUMBER"        # <release>.dev<n> for a TestPyPI build
```

| what changed | bump |
|---|---|
| a `content_path` | **minor** — users receive something new |
| only a `code_path` | **patch** — an internal fix |
| neither | **none** — docs and CI do not reach an installed user |
| the version already moved | **none** — a deliberate bump is in place; never double it |

`none` is a legitimate answer. This has to be automatic: a PyPI upload with
`skip-existing` turns an unbumped release into a green run that publishes nothing,
silently, with no warning anywhere. A human-maintained version is a silent-failure
generator.

Version files may be Python (`__version__ = "..."`), JSON (a `version` key, at the top
level or under `metadata`), or TOML (the `[project]` table — and only that table, because
`pyproject.toml` has others carrying a `version` key and bumping the wrong one is worse
than not bumping).

### The merge train

```bash
vibey-gh merge-train --dry-run
vibey-gh merge-train --method squash
```

The normal path is event-driven: the PR-automation gate dispatches
`vibey-gh merge-train --pr NUMBER` as soon as the exact current head is green. The weekly
and manual modes remain recovery backstops. A ready PR is open, current with its target,
conflict-free, green, free of requested changes, and carries a successful exact-head
`PR automation / gate` when an outside-author review is required.

Outside authors receive a fresh structured Claude review after scans pass. Findings feed
the same bounded repair loop as failed scans. Forks are never mutated with privileged
credentials; when a fork needs edits, automation preserves its exact head in a linked
repository-owned replacement PR.

### PR review and repair automation

`branch-intake.yml` opens exactly one draft PR when a new same-repository topic branch is
first pushed. It ignores the integration branch, release branch, and automation-owned fork
repair branches. Later pushes reuse the existing PR. Once the configured scans for the
exact draft head are complete and green, PR automation marks it ready and immediately
continues through review, repair, gating, and the merge train. A conflicted draft is the
one case that does not wait: conflicts are classified before draft status, because a draft
that conflicts can never become ready — promotion requires a clean merge — so leaving it to
`ready_draft` would strand it forever. Same-repository conflicted drafts therefore enter
conflict resolution directly; fork drafts still wait, since their conflict path closes the
contributor's pull request. Pending, failing, stale,
conflicting, closed, and fork draft heads are no-ops; they are never promoted prematurely.

`pr-automation.yml` reacts to configured scan-workflow completions, re-reads the entire
current-head check rollup, and publishes an explicit check run on that exact SHA. It waits
for pending scans, separates cancelled infrastructure from actionable failures, and allows
at most three repair commits per contributor lineage. Because every author's exact head
is reviewed, the same budget bounds the review-to-repair cycle too: once it is spent the
next evaluation blocks instead of dispatching another review. A new contributor commit
starts a
new lineage; bot repair pushes do not reset the counter.

Conflicting same-repository PRs enter a bounded conflict-resolution job instead of failing
permanently. The job materializes Git's exact unresolved path set without executing
repository code, gives the constrained agent read/search/edit access only, rejects edits
outside that set, rechecks the head SHA, and publishes one ordinary non-force resolution
commit. Fork conflicts continue through the repository-owned replacement-PR path. Conflict
attempts share the three-attempt repair budget, so an ambiguous merge cannot loop forever.

Review and repair use the immutable-pinned Claude Code Action with selected `vibey-skills`.
The privileged jobs may inspect source and CI logs but may not execute contributor package
managers, tests, builds, scripts, or binaries. Ordinary PR CI validates every repair push.
The agent has no Git mutation tool: one trusted publisher may push a non-empty source
(`HEAD:refs/heads/<exact-pr-branch>`) only to the exact PR branch. This deliberately
permits forward updates to `develop` or `main` when either is the PR head, while making a
Git deletion refspec (`:branch`) structurally impossible. Managed merges automatically
update `develop` and `main`, but no managed command uses `--delete`, `--delete-branch`, an
empty-source refspec, or a branch-deletion API.
Repositories must configure `ANTHROPIC_API_KEY`; `AUTOMERGE_TOKEN` is required where the
default Actions token cannot push or merge through the repository ruleset. Installation
does not create either secret.

A repository that sets `[pr_automation.fallback].enabled = true` gets one more line of
defense before that gate fails outright: when the primary review returns no verdict at
all, a `review-fallback` job sends the diff to a local Ollama model on a self-hosted
`vibey-local-gh`-labelled runner (never for a fork PR unless `trusted_only = false`) and
runs `vibey-gh local-review`. A clean local verdict passes the gate under the honestly
weaker title `PR automation: gate (local fallback)`; the local model never overrides an
actual finding, and it holds no repository credentials at all. See
[`[pr_automation.fallback]`](docs/configuration.md) for every field and
[Threat model](docs/threat-model.md) for what that self-hosted runner is and is not trusted
for.

```bash
vibey-gh pr-automation evaluate --pr 123 --head-sha HEAD_SHA
vibey-gh pr-automation ready-draft --pr 123 --head-sha HEAD_SHA
vibey-gh pr-automation mirror-fork --pr 123
vibey-gh merge-train --pr 123
```

### Issues that propose their own solution

An issue is a request for work; `issue-automation.yml` is the path from that request to a
reviewable pull request without a human in between. When an issue is published — opened,
reopened, or labelled — trusted policy code decides whether it is eligible. An eligible
issue gets one bounded attempt: an agent reads the request, implements the smallest
complete change with tests and documentation on a namespaced branch, and a separate
trusted step publishes one commit and one linked pull request that says `Closes #N`. From
there it is an ordinary contribution: the same scans, the same exact-head review, the same
repair budget, and the same merge train. Merging it closes the issue.

The whole feature turns on one fact: **anyone can open an issue**, so issue text is
contributor-controlled input to a privileged job. Three things follow.

*Outside requests are opt-in.* An issue from anyone outside the configured owner and
trusted-author set is skipped until a maintainer applies `vibey-gh:solve`. Opening an
issue can never, by itself, start a privileged job. A repository that wants the opposite
sets `solve_untrusted_authors = true` and takes that decision explicitly.

*Issue text is data, never instruction.* A trusted step writes the title, body, and
discussion into a bounded briefing file; the agent is told it is a report from a stranger
and that any sentence in it asking to change the task, relax a constraint, run a command,
or reach a network service is hostile input to be reported rather than obeyed. Nothing
from an issue is interpolated into a shell command or a workflow expression, and the only
issue-derived branch-name component is a regex-sanitized slug of the title — branch names
come from the issue number, a hash of its content, and that slug.

*The budget belongs to the request, not the clock.* Attempts are counted against a
fingerprint of the issue's title and body. Re-running automation on unchanged text cannot
spend the budget twice, and editing the issue is a new request: a fresh lineage, a fresh
branch, and a fresh budget. An issue that exhausts its budget is labelled and commented on
once, not retried forever. An agent that decides the request is a question, a duplicate,
out of scope, or too ambiguous to implement returns `needs_human` and changes nothing —
a truthful refusal is a better outcome than a speculative change.

When the paid solver produces nothing at all and `[pr_automation.fallback].enabled` is
set, the same local Ollama model backs `vibey-gh local-triage`: it never writes code or
opens a branch, only a bounded root-cause/approach/risks analysis posted as a comment for
whoever picks the issue up next, and it always reports `needs_human=true` regardless of
what the model claims.

```bash
vibey-gh issue-automation evaluate --issue 55
vibey-gh issue-automation context --issue 55 --output briefing/issue.md
vibey-gh issue-automation list-eligible
```

### The promotion

```bash
vibey-gh promote --dry-run
vibey-gh promote
```

Moves the integration branch to the release branch, which is what publishes. Three things
it gets right that a hand-written workflow usually does not:

- **It compares by content, not by commit count.** The release branch is rebase-merged, so
  its commits are rewritten copies with different SHAs; the integration branch always looks
  "ahead" even when the trees are identical. A diff is the only honest test.
- **It derives the version before opening anything.** An upload with `skip-existing` turns
  an unbumped promotion into a green run that publishes nothing, silently.
- **It hands the PR to the same event gate as every other change.** `promote` no longer
  holds a runner open with `gh pr checks --watch`; scans, automated review, and the
  exact-head merge train finish the promotion asynchronously. `--wait` retains the legacy
  synchronous mode for recovery.

### Realignment

```bash
vibey-gh realign
```

When the release branch is rebase-merged its commits are rewritten copies with new SHAs,
so the integration branch's tip is never an ancestor of it and a fast-forward is
impossible — yet a ruleset with a strict up-to-date policy treats it as behind, which
blocks the next promotion.

Rewriting the integration branch strands every topic branch cut from a commit the rewrite
replaced: the branch still holds the old copy, so Git reports a conflict for work that is
already upstream, through nobody's fault. Realign therefore reconciles open pull requests
straight afterwards, and the decision turns on patch identity rather than SHA — `git
cherry` still recognises a commit that was re-created upstream under a new SHA.

| What the branch carries | What happens |
|---|---|
| Nothing not already upstream | Its pull request is closed with an explanation and the branch is deleted |
| Unique work on an automation-owned branch | Rebased onto the new tip; rebase drops the duplicated commits itself |
| Unique work on anyone else's branch | Left exactly as it is, with a comment explaining the rebase they may want |
| Anything on a fork | Never touched |

No permanent branch can reach either mutating path: `deletable()` and `rebasable()` refuse
the configured integration and release branches and the literal `develop` and `main`
independently, and every rebase publishes with an exact-SHA `--force-with-lease`. Set
`[realign].reconcile_branches = false` to keep the old behaviour, or turn off closing,
deleting, or commenting individually.

The guard is **tree equality, not ancestry**: this runs only when a diff between the two
branches is empty, so it converges two identical contents onto one history and cannot
discard work. If the integration branch has anything the release branch does not, it is
left alone and says so.

## Configuration

```toml
[pr_automation]
enabled = true
scan_workflows = ["CI", "Provenance", "CodeQL", "Docs", "Conventional Commits"]
ignored_checks = ["PR automation / gate", "gate", "Merge train / merge"]
max_repair_attempts = 3
model = "claude-sonnet-5"
review_untrusted_authors = true
repair_untrusted_authors = true
replace_fork_prs = true
retain_schedule_backstop = true

[pr_automation.observability]
sanitized_progress = true
archive_execution_file = true
allow_private_full_output = false

[branch_sync]
enabled = true                       # run the sync and self-heal jobs at all
update_contributor_branches = true   # merge the integration branch forward via GitHub's update-branch endpoint; never a rewrite
max_self_heals = 2                   # repair-budget refills allowed before a lineage stays exhausted for a human (0-10; 0 disables)

[realign]
reconcile_branches = true            # reconcile open branches after a realign rewrite
automation_prefixes = ["vibey-gh/"]  # branches this automation may rebase on its own
close_duplicates = true              # close a PR whose commits are all already upstream
delete_duplicate_branches = true     # and delete that branch; never a permanent one
notify_contributor_branches = true   # comment on a human branch instead of rewriting it

[issue_automation]
enabled = true
model = "claude-sonnet-5"
max_attempts = 2
max_turns = 200                      # per-attempt turn budget; raise for large issues
branch_prefix = "vibey-gh/issue"
base_branch = ""                     # blank uses branches.integration
solve_untrusted_authors = false
required_label = "vibey-gh:solve"
trigger_labels = []                  # empty means every otherwise-eligible issue
ignored_labels = ["question", "discussion", "duplicate", "wontfix", "vibey-gh:solve-blocked"]
open_pull_request = true
draft_pull_request = true
retain_schedule_backstop = true

[github_release]
enabled = true
tag_prefix = "v"
generate_notes = true
require_new_version = false          # a versionless release-branch push is a no-op, not an error

[rulesets]
enabled = true

[rulesets.integration]
# Check-RUN names, not workflow names. A check run is named for its job, so the "CI"
# workflow reports as "Lint", "Build", "Test (3.12)" and never as "CI". Requiring a
# workflow name waits forever and blocks the branch outright — see the note below.
required_checks = [
  "Provenance", "Analyze Python", "Documentation contract", "PR automation / gate",
]
strict_required_checks = true          # branch must be up to date before merging
required_approvals = 0                 # PR automation gates instead
dismiss_stale_reviews = true
require_conversation_resolution = true
require_linear_history = true
require_signed_commits = false
allow_force_pushes = false             # rejected at load time if true
allow_deletions = false                # rejected at load time if true
bypass_actors = ["RepositoryRole:5"]   # repository admin; [] means nobody, including you

[rulesets.release]
required_checks = ["Provenance", "Analyze Python", "Documentation contract"]
strict_required_checks = true
required_approvals = 1
require_linear_history = true
allow_force_pushes = false
allow_deletions = false
bypass_actors = ["RepositoryRole:5"]

[repository_profile]
enabled = true
description = "A configurable repository description"
topics = ["automation", "documentation", "github-actions"]
has_issues = true
has_projects = true
has_wiki = false
has_discussions = true
allow_squash_merge = true
allow_merge_commit = false
allow_rebase_merge = true
allow_auto_merge = true
delete_branch_on_merge = false
web_commit_signoff_required = true
vulnerability_alerts = true
automated_security_fixes = true

[documentation]
enabled = true
ai_maintenance = true
model = "claude-sonnet-5"
production_label = "Production"
preview_label = "Preview"
production_indexing = true
preview_indexing = false
generate_robots = true
generate_sitemap_index = true
generate_llms_txt = true
generate_llms_full_txt = true
generate_json_ld = true
bottom_nav = true       # previous/next bar at the bottom of every published page
author_name = "Adam Matthew Steinberger"
author_url = "https://vibewithadam.matthewsteinberger.com"
google_analytics_id = ""                    # empty disables it; set a GA4 ID like "G-XXXXXXXXXX" to enable
google_site_verification = ""                # bare Search Console "HTML tag" token; leave empty to skip verification
# ProperDocs depends on none of the plugins your site declares, so a site using
# mkdocs-gen-files or pymdownx.* must name them here or the --strict build fails.
site_requirements = []                      # e.g. ["mkdocs-gen-files", "pymdown-extensions>=10.7"]
site_requirements_file = "docs/requirements.txt"   # installed when present; "" disables
properdocs_version = "1.6.7"
```

`CodeQL` is a real managed Python security-analysis workflow using an immutably pinned
official action. The scan names above therefore map to concrete required checks rather
than advisory placeholders. Add your own workflow names to `scan_workflows` — each must
have a `pull_request` or `pull_request_target` trigger, which `vibey-gh check` verifies.

`[rulesets]` is what actually sets the branch protection the rest of this document
describes, rather than leaving it for an adopter to configure by hand from prose.
`repository-profile.yml` reconciles a ruleset per permanent branch from this block —
required status checks, review and conversation-resolution requirements, linear history,
and signed commits — using the same idempotent read-compare-write shape it already uses
for settings and topics. `allow_force_pushes` and `allow_deletions` are rejected at
configuration load time if set to `true`, not merely defaulted to `false`, so the
non-deletion, non-rewrite guarantee cannot become one keystroke away from disabled. An
existing rule type the configuration does not mention is never removed, only reported, and
a ruleset the API refuses fails the job with the API's own reason. Omitting `[rulesets]`
entirely, or setting `enabled = false`, leaves the repository exactly as untouched as
before this feature existed. Run `vibey-gh rulesets --dry-run` to inspect the diff first.

Issue automation is closed by default for people you have not vouched for.
`solve_untrusted_authors = false` means an outside author's issue waits for a maintainer
to apply `required_label`; only then can it start a privileged job. `trigger_labels`
narrows the feature further — set it to `["bug"]` and only labelled bugs are ever
attempted. `ignored_labels` is the escape hatch in the other direction: an issue carrying
one is never attempted, whoever wrote it. `branch_prefix` names the namespace every
proposal branch lives under; it is validated against the configured permanent branches,
and `branch-intake.yml` is rendered to yield that namespace so the two never race to open
the same pull request. Set `open_pull_request = false` to publish only the branch, or
`enabled = false` to keep the workflow installed and inert.

Google Analytics is off by default and fully generic: `google_analytics_id` accepts any
repository's own GA4 measurement ID (`G-XXXXXXXXXX`), and leaving it empty means no
analytics script tag is ever emitted and no request reaches Google. When set, the same ID
is injected into every page of both generated documentation channels and the
channel-picker landing page.

`google_site_verification` proves ownership of the published site to Google Search
Console without an uploaded verification file, which release-surfaces would otherwise
wipe on every rebuild of the Pages root. Set it to the bare token from Search Console's
"HTML tag" verification method — the `content="..."` value, not the whole `<meta>` tag —
and it is rendered into a `<meta name="google-site-verification">` tag on every published
page and the channel-picker landing page, so verification survives redeploys.

Sanitized progress is the safe default. Claude's progress-comment mode is enabled only for
the direct PR/issue events the action supports; `workflow_run`, `workflow_dispatch`, and
`pull_request_target` retain safe phase-level job visibility without requesting that
unsupported mode. Raw Claude JSON is never emitted during ordinary PR or scan-triggered
runs. A repository may opt into private diagnostics with
`allow_private_full_output = true`, then manually dispatch `PR automation` with
`full_claude_output = true`. The workflow fails closed unless the event is manual and the
repository visibility is private. Execution records remain 90-day artifacts when
`archive_execution_file` is enabled.

### Comprehensive documentation and AI maintenance

The `Docs` workflow enforces the deterministic FOSS and multi-agent documentation contract
on every push and pull request. That structural check is intentionally necessary but not
sufficient: after scans settle, PR automation performs an exact-head semantic audit for
every author. It compares the README and complete documentation suite with source, tests,
configuration, packaging, workflows, releases, and the CLI/SDK/API/MCP/webhook capability
registry. A PR cannot pass merely by containing expected filenames or headings. It must be
accurate, complete, human-readable, operationally useful, and free of actionable findings.

Findings enter the same bounded repair loop as a failing scan. The repaired SHA is rescanned
and rereviewed; an older documentation verdict never satisfies the gate. A scheduled or
manually dispatched maintenance job remains a repository-wide backstop: it creates missing
documentation, repairs stale claims, and opens a guarded documentation PR. It never
executes repository code in the privileged job, commits application changes, or mutates a
permanent branch directly. It must return `complete=true` with no remaining gaps before a
documentation PR may be published; PR-creation errors fail loudly.

The deterministic file-presence suite (`documentation.required_files`) includes `README`,
changelog, license, conduct, contribution, security, support, the project diagram, GitHub,
hooks, Claude, Cursor, Gemini, Codex/Agents, and generic-agent documentation. Deeper guides
such as architecture, operations, testing, release, governance, accessibility, dependency,
threat-model, troubleshooting, and ADR documentation are not covered by that file-presence
check; they are kept accurate by the exact-head semantic audit described above, which reads
every doc against source, tests, configuration, and workflows. The repository also contains
a Claude-standard plugin marketplace at `.claude-plugin/marketplace.json` with development,
documentation, release-security, and PR-automation plugins. Each plugin ships a manifest,
skills, and specialist agents; the development, documentation, and PR-automation plugins
additionally ship commands (release-security ships agents and skills without commands).
`.claude/settings.json` registers and enables the marketplace for project sessions.

The Pages build emits production and preview sitemaps, a root sitemap index, `robots.txt`,
`llms.txt`, `llms-full.txt`, canonical links, indexing policy, Open Graph/Twitter metadata,
Schema.org JSON-LD, and repository/revision provenance. Repository identity and URLs are
derived at build time, so adopting repositories never inherit `vibey-gh` metadata.

### Five-surface capability parity

Every canonical capability is exposed and tested through all five supported surfaces:

- Python SDK: `vibey_gh.surfaces.invoke(...)`
- CLI: the native command and the `sdk`, `api`, `mcp`, and `webhook` projections
- JSON API: `api_dispatch` and `/v1/capabilities/<name>`
- MCP: `initialize`, `tools/list`, and `tools/call`
- Webhook: HMAC-SHA256 authenticated, delivery-ID replay-safe dispatch

Seven CLI commands are deliberately outside this canonical registry, each for its own
reason documented in detail in `docs/cli.md`:

- `conventional-message` and `conventional-check` are local git-hook/CI helpers that
  consume stdin, commit-message files, or revision ranges. Exposing those host-specific
  mutation primitives through a remote API, MCP tool, or webhook would expand privilege
  without adding an automation capability.
- `report-superseded` is a read-only reporting helper: it prints which prior releases an
  index supersedes and a management URL for a human to act on, since PyPI exposes no yank
  API. It never mutates anything, so there is nothing for a remote surface to invoke.
  Under Article V.4 of the Constitution its report becomes a demand: a ratified change to
  a founding document names every previous release for yanking, and the human is the
  executor only because the platform reserves the click for a browser.
- `failover` is machine-level by design: its config never enters a repository, its seats
  are operator-supplied commands, and it stays disabled until the operator writes
  `enabled = true` — an engine that hands the operator seat around must never gain a
  remote surface or a default-on path.
- `local-review` and `local-triage` are local-model fallbacks that only run when the
  primary paid review or solver produced no verdict at all. They require a self-hosted
  runner and a local Ollama-compatible model, and must never gain remote/API/webhook
  exposure.
- `doctor` is a purely local, read-only diagnostic: it reads files already on disk (no
  network, no credentials, no execution) to judge whether the local configuration and
  installed workflows will function. There is no remote resource for an API, MCP, or
  webhook caller to act on — the answer only means something on the machine that holds
  the checkout.
- `book` only reads an already-built local site directory and a local site configuration
  and writes local files (an EPUB and a print-ready HTML). There is no remote resource for
  an API, MCP, or webhook caller to act on, and exposing it remotely would mean shipping a
  built site's bytes through a surface with no such contract today.

Every other repository automation capability in `surfaces.CAPABILITIES` remains available
through all five forms.

The parity contract enumerates every capability from one registry, invokes every adapter,
and fails CI if any surface is absent or divergent. Because `Docs` is a configured scan,
missing documentation or interface parity blocks the exact-head PR gate and enters the
bounded repair loop before merge.

After the configured `Release` workflow succeeds on `main`, the managed
`github-release.yml` workflow tags that exact commit and creates a generated-notes GitHub
Release. It is safe to rerun: an existing matching tag/release is reused, while an
existing tag at a different SHA is never moved. By default that mismatch is treated as an
intentional no-op — e.g. a versionless docs- or tooling-only push — and is only turned into
a loud failure when `[github_release] require_new_version = true` opts the repository into
the stricter behavior.

The managed `release-surfaces.yml` workflow follows every successful release on either
branch. It builds two persistent ProperDocs sites under the repository's GitHub Pages
domain: `/develop/` is the test documentation released with TestPyPI, while `/main/` is
the production documentation released with PyPI. A small root page links both channels.
Because GitHub Pages has one deployment per repository, each run restores the latest
successful artifact for the other channel before deploying; one branch never erases the
other branch's site.

GitHub Packages does not provide a PyPI registry. The workflow therefore publishes the
exact wheel and source distribution from the successful `Release` run as an OCI artifact
at `ghcr.io/<owner>/<repository>/python`. Every artifact receives its immutable version
and `sha-<commit>` tags, plus `develop` for test releases or `main` and `latest` for
production releases. The normal TestPyPI and PyPI uploads remain authoritative and are
unchanged.

After release surfaces succeed, `repository-profile.yml` reconciles the repository's
description, topics, homepage, collaboration features, merge methods, automatic merge,
commit signoff, branch retention, vulnerability alerts, automated security fixes, and —
from `[rulesets]` — the integration and release branch rulesets themselves.
An empty description derives
a repository-specific description from the consuming repository name. It verifies that
Pages, a GitHub Release, a deployment, and the OCI package really exist—the public API
does not expose fictional “show Releases/Deployments/Packages” switches—and, now that
ruleset reconciliation runs first in the same job, that `develop` and `main` really are
protected. Profile updates use `AUTOMERGE_TOKEN` when available and never create, update,
push, or delete a branch.

If a trusted post-merge workflow fails on `develop` or `main`, `release-repair.yml`
reviews its logs with the same constrained agent used for PR repair. A fixable problem is
committed to a new `vibey-gh/repair/release-*` branch and returned through a normal PR,
where all checks and the merge train apply. It never pushes a repair directly to—and can
never delete—`develop` or `main`. Credential, billing, repository-setting, registry, and
other operator-only failures are reported with an explicit required action instead of
being disguised as code fixes.

Everything project-specific lives in `.vibey-gh.toml`, so the logic beside it stays
general. Every key has a default; a repository that agrees with them needs no file at all.

```toml
[fingerprint]
text    = "Made with love by ..."          # the source-header comment
trailer = "Made-With: ..."                 # the commit trailer
sources = ["src/**/*.py", ".github/workflows/*.yml"]

[version]
files         = ["pyproject.toml", "src/pkg/__init__.py"]
content_paths = ["plugins/"]               # a change here is a MINOR release
code_paths    = ["src/"]                   # a change here alone is a PATCH

[branches]
integration = "develop"
release     = "main"

[merge_train]
owner           = "your-login"
trusted_authors = ["your-login", "dependabot[bot]"]
```



## Workflows

| Workflow | Responsibility |
|---|---|
| Branch intake | Turns a new topic branch into one reusable draft PR. |
| Issue automation | Turns an eligible published issue into one guarded solution branch and linked PR. |
| Branch sync | Brings open branches forward on every merge; daily, refills a bounded number of spent repair budgets. |
| Conversation | Answers `@vibey-gh` in a comment, and may make the change when a trusted author asks on a PR. |
| Conventional Commits | Normalizes guarded same-repository topic history and republishes it with an exact-head lease. |
| CI\* / Provenance / CodeQL / Docs | Validate code, history, security, human docs, agent docs, plugins, and interfaces. |
| PR automation | Aggregates exact-head scans; reviews, repairs, resolves conflicts, and gates. |
| Merge train | Squash-merges into `develop` and rebase-merges promotions into `main`. |
| Promote | Opens or reuses the `develop` → `main` promotion PR once the merge train advances `develop`. |
| Release\* | Publishes `develop` dev builds to TestPyPI and `main` releases to PyPI. |
| GitHub Release | Tags the exact production commit and generates release notes. |
| Release surfaces | Publishes GHCR artifacts and Production/Preview ProperDocs sites. |
| Repository profile | Enforces repository metadata, policy settings, security, and public surfaces. |
| Release repair | Returns trusted post-merge fixes through an ordinary guarded PR. |
| Automation bootstrap | Manual, admin-gated escape hatch that merges a fix to broken privileged workflow code when a PR cannot repair its own gate. |

\* `CI` and `Release` are not rendered by `vibey-gh install`; see
[What gets installed](#what-gets-installed) for the exact name and behavior contract
every other row in this table depends on.

Scheduled and manual triggers are recovery backstops; normal delivery is event driven.

## Failure and recovery model

The automation distinguishes failures by what can safely resolve them:

| Condition | Automated response | Human action |
|---|---|---|
| Test, lint, type, coverage, documentation, or review finding | Inspect and edit under the bounded repair policy; push one repair commit; rescan the new SHA | Review the escalation only if the attempt budget is exhausted |
| Same-repository merge conflict | Materialize the exact conflict set; allow edits only to conflicted files; push one ordinary resolution commit | Resolve manually if the conflict is ambiguous or the budget expires |
| Fork PR needs edits | Create a linked repository-owned replacement PR with attribution | Continue discussion on the linked PR when needed |
| Missing secret, expired token, billing/credit exhaustion, registry denial, unsupported runner, or unavailable external service | Mark `vibey-gh:automation-blocked`; make no speculative source edit | Correct the named repository or provider setting, then redispatch |
| Three unsuccessful repair attempts in one contributor lineage | Mark `vibey-gh:repair-exhausted`; publish remaining failures and run links | Push a new human-authored commit or deliberately reset the lineage |
| Issue too ambiguous, out of scope, or blocked on an operator decision | Return `needs_human`, change nothing, mark `vibey-gh:solve-blocked` | Answer the question in the issue, or refine and edit it to start a new lineage |
| Solution attempt returns no result at all (turn-budget exhaustion or an infrastructure failure) | Comment once naming the cause; mark `vibey-gh:solve-blocked` | Split the issue into smaller requests, or raise `[issue_automation].max_turns` |
| Configured unsuccessful solution attempts for one issue lineage | Mark `vibey-gh:solve-exhausted`; comment once with the reason | Edit the issue to restate the request, or take it manually |
| Exact-head review returns no verdict (exhausted API credits, missing key, model unavailable) | If `[pr_automation.fallback].enabled` and the PR is same-repository (or `trusted_only = false`), a local Ollama model on a self-hosted runner reviews the diff; a clean local verdict publishes a passing `PR automation: gate (local fallback)` gate naming the weaker reviewer. Otherwise, publish a failing `PR automation: review incomplete` gate naming the operator cause; never silently infer a verdict from the primary path alone | Correct the operator condition and rerun the review, or treat a local-fallback pass as the degraded signal it is |
| Stale workflow completion | Ignore it; it cannot create a successful current-head gate | None |
| Failed trusted post-merge release workflow | Open a repair branch and ordinary PR; never patch a permanent branch directly | Correct operator-only infrastructure failures |

Repair jobs can read and edit files but cannot run contributor-controlled package managers,
tests, builds, scripts, or binaries while privileged credentials are present. The ordinary
unprivileged PR scans execute the repaired code. This separation is why a repair result is
always followed by a new scan rather than being treated as proof of correctness.

## Day-two operations

If Conventional Commits rewrites your topic branch, preserve unpushed work, run
`git fetch origin`, and rebase it onto the new explicit `origin/<topic-branch>` head. With
no unpushed work, reset only that local topic branch to its remote counterpart. Never
reset or force-push `develop` or `main`.

### Upgrade vibey-gh

Upgrade the package on a topic branch, rerun `vibey-gh install`, and commit the rendered
workflow and asset differences. Never hand-copy only one generated workflow: templates,
configuration rendering, tests, and the dogfood copies form one versioned contract.

```bash
python -m pip install --upgrade vibey-gh
vibey-gh install
vibey-gh check --ci
git diff -- .github .githooks
```

### Disable a managed surface intentionally

Use configuration rather than deleting a generated file. For example, a repository that
publishes no Python package can omit the release workflows from `[install].workflows`.
`vibey-gh check` then verifies the chosen subset instead of repeatedly reinstalling a file
the repository does not want.

### Recover a missed event

Use the workflow’s manual dispatch with the PR number and exact current head SHA. Scheduled
backstops also redispatch open PR evaluations. Re-running an old workflow is harmless: the
exact-head comparison prevents its result from authorizing a newer commit.

Dispatch `Issue automation` with an issue number to retry one issue, and
`vibey-gh issue-automation list-eligible` to see what its scheduled sweep would pick up.
Re-dispatching an issue whose text has not changed cannot spend a second attempt or open a
second pull request; the stored content fingerprint makes the retry a no-op.

### Audit an automation decision

Start with the PR’s `PR automation / gate`, then follow the linked workflow run. The job
summary contains the evaluated SHA, aggregate scans, trust classification, repair attempt,
semantic review result, and merge decision. Review artifacts are retained for 90 days.
State comments use machine-readable markers and are updated idempotently rather than
creating an unbounded comment stream. The marker is located by pattern, not by comment
author, so its stored attempt/heal counters are a cost control rather than an access
control on public repositories — see [Security architecture](docs/security.md) and
[Threat model](docs/threat-model.md).

## Project documentation map

| Need | Canonical document |
|---|---|
| Human overview and adoption | This README |
| Complete CLI arguments | [docs/cli.md](docs/cli.md) |
| Every configuration field | [docs/configuration.md](docs/configuration.md) |
| Components and dependency direction | [docs/architecture.md](docs/architecture.md) |
| Workflow triggers, permissions, and transitions | [docs/workflows.md](docs/workflows.md) |
| Operating and recovering the system | [docs/operations.md](docs/operations.md) |
| Releases and publishing channels | [docs/releases.md](docs/releases.md) |
| Threats and privileged-job boundaries | [docs/threat-model.md](docs/threat-model.md) and [SECURITY.md](SECURITY.md) |
| Security architecture | [docs/security.md](docs/security.md) |
| Local development and verification | [docs/development.md](docs/development.md) and [docs/testing.md](docs/testing.md) |
| Common failures | [docs/troubleshooting.md](docs/troubleshooting.md) |
| Governance, support, and conduct | [docs/governance.md](docs/governance.md), [SUPPORT.md](SUPPORT.md), and [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md) |
| Accessibility standards | [docs/accessibility.md](docs/accessibility.md) |
| Dependency policy | [docs/dependencies.md](docs/dependencies.md) |
| Roadmap and priorities | [docs/roadmap.md](docs/roadmap.md) |
| GitHub Actions workflow reference and admin recovery paths | [.github/AUTOMATION.md](.github/AUTOMATION.md) |
| Agent instructions and skills | [AGENTS.md](AGENTS.md), [CLAUDE.md](CLAUDE.md), [GEMINI.md](GEMINI.md), `.cursor/`, `.agent/`, `.agents/`, and `.claude/` |
| Architectural decisions | [docs/adr/README.md](docs/adr/README.md) |

## Troubleshooting

- Empty Anthropic key: define `ANTHROPIC_API_KEY` as a repository secret, not only an
  environment secret, and confirm the privileged workflow can read it.
- Review-blocked promotion: verify the exact-head `PR automation / gate`; admin fallback
  is permitted only after all independent policy checks pass.
- Pages 404: select **GitHub Actions** as the Pages source and rerun Release surfaces.
- Repository profile failure: give `AUTOMERGE_TOKEN` the administration and security
  permissions required to reconcile the configured settings.
- Wrong package index: `develop` must select TestPyPI and `main` must select PyPI.
- An issue that never gets a proposal: check the evaluation reason in the `Issue
  automation` job summary. An outside author's issue is skipped by design until a
  maintainer applies `vibey-gh:solve`; an ignored or missing trigger label, an exhausted
  budget, and a `vibey-gh:solve-blocked` label are the other stated reasons.

See [docs/troubleshooting.md](docs/troubleshooting.md) and [SUPPORT.md](SUPPORT.md); include
the workflow URL, exact SHA, and redacted failing-step output when asking for help.

## Contributing

Read [CONTRIBUTING.md](CONTRIBUTING.md), [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md), and
[AGENTS.md](AGENTS.md). Changes must preserve the dependency-free runtime, Python 3.11,
100% line and branch coverage, immutable action pins, provenance, and permanent-branch
non-deletion guarantee. Report vulnerabilities through [SECURITY.md](SECURITY.md), not a
public issue.

### Taking the hooks without the workflows

`install` writes the managed workflows alongside the hooks. A repository that already has richer
ones of its own can decline them:

```toml
[install]
workflows = []          # hooks and the CLI only
# workflows = ["provenance.yml"]   # or just the ones you want
```

This is not cosmetic. `check` verifies that everything it manages is present and current,
so without it a repository that deliberately keeps its own workflows would fail the check
forever — and a check that cannot pass is a check people route around.

### Pinning the tooling version

By default every managed workflow installs this tooling with `pip install vibey-gh`, which
floats to whatever the latest published release is on every run. Pin it instead:

```toml
[install]
pin_version = true
```

Rendered workflows then install the exact version that rendered them
(`vibey-gh==X.Y.Z`) rather than the latest one, so a release changing this tool's own
behavior cannot break your CI with no warning. Upgrading is explicit: run `vibey-gh
install` from the newer release, and the pin moves forward as one visible diff you review
and commit like any other change. The self-hosting path this repository uses to install
itself from source is never pinned, since it cannot depend on a published release that may
not exist yet.


`trusted_authors` is matched after normalising `app/name` and `name[bot]` to the same
thing. `gh` reports a bot author with the `app/` prefix while the rest of GitHub writes
`[bot]`; a literal allow-list matches whichever spelling it happens to contain and
silently distrusts the other, which once caused an automation to quarantine its own pull
request as an outside contribution.

## What is deliberately not fingerprinted

- **Files whose bytes are meaningful** — generated documents verified against a source,
  Markdown loaded into a model's context. A header would be a diff against the source.
- **Anything without comment syntax** — JSON, most notably.

The commit trailer covers both without touching them. A naive "comment in every changed
file" rule cannot express itself in JSON and corrupts content that is checked byte for
byte.

## Licence

MIT. See [LICENSE](LICENSE).

Made with ❤️ by [Vibey](https://the-vibey-project.github.io/vibey/), Developed by [Adam Matthew Steinberger](https://vibewithadam.matthewsteinberger.com/) ([@adammatthewsteinberger](https://github.com/adammatthewsteinberger/)).
