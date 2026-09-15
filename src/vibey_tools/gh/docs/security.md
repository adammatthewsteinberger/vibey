# Security architecture

Workflows use least-privilege job permissions and immutable third-party action revisions.
Privileged `pull_request_target` jobs read trusted workflow code and may inspect untrusted
content but cannot execute it. AI tools edit only named scopes; trusted shell steps verify
paths and publish one commit. Secrets never enter prompts or artifacts. The merge train
rechecks exact-head gates immediately before mutation.

Issue text is an adversary-controlled input to a privileged job, so issue automation
narrows it twice. First by authority: an issue from outside the configured owner and
trusted-author set cannot start a solution job until a maintainer applies the configured
label, unless the repository explicitly sets `solve_untrusted_authors`. Second by shape: a
trusted step renders the issue into a bounded briefing file, the agent is told it is a
report rather than an instruction and reports attempted redirection through
`prompt_injection_observed`, and nothing derived from issue text reaches a shell command or
a workflow expression. The one place issue text does reach is the branch name, and only as
a regex-sanitized slug of the title (stripped to `[a-z0-9-]+`, length-capped). Branch names
are the issue number, a hash of its content, and that slug, validated against the
configured namespace and permanent branches, and published by a trusted step the agent
cannot reach.

Advanced branch diagnostics are opt-in and metadata-only. Events exclude application
values, exception text, arguments, locals, environment values, and secrets. Each JSONL
record carries invocation and GitHub correlation, a monotonic sequence, and the preceding
record's SHA-256 digest; recomputing the chain detects truncation, reordering, or mutation
within the retained stream. Operators must protect and expire `VIBEY_GH_DEBUG_LOG` like
other diagnostic telemetry. The hash chain is tamper-evident, not a digital signature;
ship it to append-only or independently authenticated storage when adversarial log writers
are in scope.

The managed CodeQL workflow analyzes Python changes on both delivery branches and their
pull requests. The API-drift workflow independently verifies that every canonical
capability remains available through MCP, API, CLI, SDK, and webhook boundaries.

Claude Code Action requires a Git repository at the workspace root for its own setup.
Managed workflows satisfy that contract with a disposable repository containing no source
checkout or persisted credential. It has a clean repository URL as `origin` because the
action requires that remote during setup. A deliberately nonmatching non-write-user sentinel
forces the action's credential-helper and secret-scrubbing path, so the token is never
embedded in `.git/config` and no additional actor is authorized. Untrusted source remains
under `target/`, checked out with `persist-credentials: false`. The disposable context is
removed with `always()` before trusted persistence or publishing. Only the later trusted
publish step attaches `GH_TOKEN` through `gh auth setup-git`; no Claude step can read that
authenticated context.

Claude observability is sanitized by default. The action's `track_progress` input is
strictly gated to its supported direct PR/issue events; privileged automation events rely
on job-phase visibility so an unsupported progress mode cannot fail the review itself.
Raw `show_full_output` logging can expose
assistant messages, tool results, repository contents, and CI material, so managed
workflows accept it only from an explicit manual dispatch when configuration opts in and
GitHub reports private repository visibility. Public and event-triggered runs fail closed.
Execution logs may instead be retained as access-controlled 90-day workflow artifacts.

Before a repair session, trusted automation downloads failed-check metadata and available
failed-job logs for the exact PR head into a bounded local diagnostic bundle. The bundle
is treated as untrusted input, capped at 200,000 bytes, and read-only to the diagnosis;
repository code is still never executed in the privileged job. This avoids speculative
repairs when optional CI MCP tools are unavailable without granting Claude shell access.

Repair and conflict-resolution publication never trusts the head it evaluated. The trusted
publisher re-reads the PR's current head immediately before committing and again after any
non-fast-forward push rejection. A mismatch means a human or another bot advanced the PR
concurrently, so the run is discarded as a stale no-op: it never force-pushes, never
overwrites the newer commit, never consumes a repair attempt, and never mutates a permanent
branch from an obsolete checkout. This applies even when `develop` or `main` is itself the
PR head during a promotion, which is exactly when clobbering unreviewed newer content would
be most damaging. See [Workflows](workflows.md) for the exact recheck points.

Repair and solve budgets persist in a single marker comment per PR or issue, located by
pattern match rather than by comment author (see [Threat model](threat-model.md)). On a
public repository any commenter can forge or edit that marker to reset `attempts` or
`heals`, so the stored counters are a cost control, not an access control. They cannot
authorize an unreviewed merge: the review job re-runs on every SHA that reaches `ready` or
`review`, and the exact-head recheck above still gates every publish independently of the
stored state.

The Conventional Commits job is the sole guarded exception that may force-update history.
It can act only on a same-repository topic branch, only from an exact checked SHA, only on
linear history, and only with `--force-with-lease`. Permanent branches are rejected by
both configured and literal names. The job executes the trusted normalizer, never PR code,
and a concurrent contributor push makes the lease fail closed.
Promotion PRs from the integration branch to the release branch skip that history
normalizer entirely. Provenance still checks the complete repository state, but does not
re-audit or rewrite historical subjects already admitted to the protected integration
branch.

The automation-bootstrap workflow is a second guarded exception: a manually dispatched,
admin-only squash merge that bypasses the ordinary PR-automation review because privileged
workflow code is loaded from the trusted base branch and a PR cannot self-repair it. It
requires administrator permission on the actor, an open non-draft PR that exactly matches
the dispatched head SHA and targets `develop`, changed files confined to workflow,
template, or automation-core paths, and every non-gate check run on that exact SHA —
including CodeQL, API drift, documentation, provenance, build, and lint — completed
successfully before the `--match-head-commit` merge runs. It never deletes a permanent
branch. See [Threat model](threat-model.md) for the full rationale.

The local-model review fallback (`[pr_automation.fallback]`, `vibey_gh.local_review`, the
`local-review`/`local-triage` CLI commands) is a distinct security boundary from every
other AI path in this project: it runs on a repository-provided
`[self-hosted, vibey-local-gh]` runner rather than a GitHub-hosted one, only when the
primary Claude review returned no verdict at all. GitHub's own guidance is that
self-hosted runners should almost never serve a public repository, because any contributor
can open a pull request against one; `trusted_only` (default on) removes that risk by
excluding fork pull requests from the fallback entirely, leaving them to fail closed to
`PR automation: review incomplete` like any other unresolved review. The `review-fallback`
job holds only `contents: read` — no secret and no token capable of mutating the
repository — and the diff reaches a locally served Ollama-compatible model as text; the
model has no shell, no tools, and no network beyond the local inference port. Ollama's
`format` parameter constrains decoding to the response schema, so the output shape is
guaranteed, but a small local model's judgments are not: the fallback verdict omits the
documentation-contract fields the primary review certifies, and the gate names the result
`PR automation: gate (local fallback)` so it is never mistaken for a full review. See
[Configuration](configuration.md#pr_automationfallback) for the field reference.

Webhook receivers must use a strong `VIBEY_GH_WEBHOOK_SECRET`, verify HMAC over the exact
raw body, and place `VIBEY_GH_WEBHOOK_STATE_DIR` on access-controlled durable storage.
Accepted IDs use atomic mode-0600 marker creation, preventing replay across restarts and
concurrent CLI processes. Operators own TLS, rate limits, request-size limits, backups,
retention, and safe pruning of expired claims.

The opt-in `[pr_automation.fallback]` local-model review/triage path runs on a self-hosted
runner rather than a GitHub-hosted one, so it sits outside the credential-free ephemeral
Git context described above by design: it holds no repository secret at all
(`permissions: contents: read`), never checks out PR source, and reaches only a local
inference port with the diff or issue text as plain data. `trusted_only` (default `true`)
keeps fork pull requests off that runner entirely. See [Threat model](threat-model.md) for
the full boundary and blast-radius analysis.
