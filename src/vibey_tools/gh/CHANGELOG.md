# Changelog

All notable changes are recorded in immutable [GitHub Releases](https://github.com/the-vibey-project/vibey-gh/releases).
This file follows Keep a Changelog and semantic versioning conventions.

## Unreleased

- Add `vibey-gh marketplace` and the `[marketplace]` section: one Claude Code marketplace at
  the repository root, rendered from the workspace members' own manifests. `/plugin
  marketplace add owner/repo` reads exactly `<repo>/.claude-plugin/marketplace.json`, and a
  monorepo that absorbed its marketplaces as members (vibey ADR-0021) had nothing there —
  `the-vibey-project/vibey: no readable .claude-plugin/marketplace.json`. The root manifest
  now carries every member's plugins with their sources re-rooted, under a name of its own
  (Claude Code registers one marketplace per name per user, and each member's package still
  ships its manifest under its own name). `--check` and `check` report drift; a member
  defect is a named error. `MarketplaceRenderer` arrives with its seam declared in
  `vibey_gh/interfaces/` (vibey ADR-0016), the package's first.

- Add `vibey-gh book --site-dir site --title T --author A`, which exports the already-built
  documentation site as a book: a valid EPUB 3.0 package with Dublin Core metadata, and a
  print-ready HTML sized to the standard 6in x 9in KDP paperback trim. Chapters come from
  the site's own nav, in nav order, so the copy doctrine's tier ordering carries into the
  book unchanged. Stdlib-only, like the rest of the package.

- Let the local review fallback reach a pull request the diff API refuses. GitHub's diff
  API refuses a pull request beyond roughly 300 changed files, which is exactly the shape
  of a migration or adoption sweep — observed on a 347-file provenance sweep that could
  therefore never be reviewed at all, paid or local. The fallback job now reconstructs the
  same merge-base diff itself when `gh pr diff` fails: it fetches the base and head refs,
  deepens a shallow trusted checkout until their histories connect, and diffs one against
  the other. That reconstruction is read-only and executes no repository code, so the
  no-execution guarantee is untouched, and `max_diff_chars` still caps what reaches the
  model either way.

- Add an optional `[documentation] google_site_verification` setting: the bare Search
  Console "HTML tag" verification token, rendered as a `<meta
  name="google-site-verification">` tag on every published documentation page and the
  channel-picker landing page so verification survives Pages redeploys. Restricted to
  `^[A-Za-z0-9_-]{1,128}$`, which also rejects a pasted whole `<meta>` tag.
- Stop the required automation document from hijacking an adopter's front page. GitHub
  resolves a repository's landing README as `.github/README.md` first and the root
  `README.md` only if that is absent — so requiring `.github/README.md` replaced every
  adopting repository's *product* README with maintainer-facing automation notes, on the
  page a user lands on. Both this project and its first adopter were serving the wrong
  document, and nothing written inside the file could change it: the name is what GitHub
  reads. The required file is now `.github/AUTOMATION.md`, configurable as
  `[documentation].automation_doc`, and `github_readme_sections` /
  `github_readme_min_words` are renamed to `automation_doc_sections` /
  `automation_doc_min_words` — the former names are still read, so existing configuration
  keeps working. An adopting repository should rename its own `.github/README.md` to
  match, which is what makes its product README the one GitHub shows again.

- Stop the gate deadlocking on a pull request with nothing wrong with it. Two faults met.
  The rollup counted `Evaluate current head` — the job computing the rollup, still running
  while it counts — so the state reads "pending" from inside its own run; that survived
  only because a later run saw the earlier evaluate completed. And `Conventional Commits`
  gated through its `enforce` check while being absent from `scan_workflows`, which is
  also what `pr-automation.yml` renders into its `workflow_run` trigger, so finishing
  announced nothing. Put together: the last scan fires the final evaluation, `enforce`
  completes after it, and no run ever looks again. The pull request sits blocked with
  every check green, nothing failing and nothing to rerun, until the scheduled backstop
  notices hours later. Every job this workflow publishes is now excluded from its own
  rollup, pinned against the template so a job added later cannot start gating itself, and
  `Conventional Commits` is a scan workflow so its completion re-triggers evaluation.

- Let a repository that *is* vibey-gh run its own working tree. The hooks resolved
  `command -v vibey-gh` first, so a globally installed copy won — and since `develop` is
  ahead of the last release nearly always, that copy compared the repository's managed
  assets against the older ones it bundles, called them out of date, and refused the push
  with a provenance error that had nothing wrong behind it. Installing the CLI the obvious
  way, to satisfy an adopting repository's hook, was enough to lock this one. The hooks now
  detect self-hosting the same way the workflow templates already do — `name = "vibey-gh"`
  in `pyproject.toml`, plus the package directory — and run `python3 -m vibey_gh.cli`
  against the checkout, which needs no install and no virtualenv because the package is
  dependency-free stdlib. An adopting repository matches neither condition and falls
  straight through to its installed CLI, exactly as before.
- Finish the code-block colours: give every token a legible default rather than naming
  them one at a time. The previous pass covered strings and keywords and missed
  `.hljs-subst`, so `$(git rev-parse HEAD)` inside a shell string stayed at 1.33:1 — in
  the very example that tells a reader how to list their check names. `.hljs-code` and
  `.hljs-formula` were under the line too, at 4.06:1. A catch-all now sets a readable
  colour for any token, including ones this stylesheet has never heard of, and the palette
  overrides the ones worth distinguishing; it precedes the palette because an attribute
  selector and a class have equal specificity and source order decides. The contrast test
  could not have caught this on its own — it measured the colours that were declared, and
  the broken token had none — so a second test asserts the catch-all exists and comes
  first.

- Make code blocks readable on the published documentation site. The theme ships two
  highlight.js palettes and enables the *light* one by default (`#hljs-dark` carries
  `disabled`), so its token colours are chosen for a white page — while this stylesheet
  paints every code block `#080c17`. A string literal rendered `#032f62` on near-black,
  a contrast ratio of 1.48:1 against a 4.5:1 standard: not merely low-contrast but
  genuinely unreadable, and a configuration sample is mostly string literals. The
  stylesheet now supplies its own token palette, every colour of it measured at AA or
  better, covering both `.hljs-*` and the Pygments classes a `pymdownx.highlight` site
  emits instead. A test computes the contrast of every token colour against the forced
  background and fails below AA, since "looks fine to me" is what shipped this.
- Say why a model call failed, at every AI step. The action reports only
  `--json-schema was provided but Claude did not return structured_output` — the symptom —
  and the gate then tells an operator to check a log that does not contain the cause. It
  is in the execution record the run already writes: an immediate `is_error` at zero cost
  with an empty `modelUsage` is the API refusing the call outright, which is a different
  thing from a model that answered badly, and the two want different responses. Each step
  now reports `is_error`, `subtype`, turns, cost and model-call count into the job summary,
  quotes what the run said, and adds an explicit note when there were no model calls at
  all. A failure that genuinely burned tokens does not get that note, so exhausted credit
  and an exhausted turn budget stop looking identical. The step runs only on failure and
  never masks it, and the quoted text is fenced rather than interpolated, since model
  output may echo the pull request.

- Stop shipping this project's own self-test to the repositories that install it.
  `api-drift.yml` calls `vibey_gh.surfaces.parity()` — a statement about vibey-gh, not
  about an adopter's product — yet it was a managed template installed everywhere *and*
  named in the default `scan_workflows`. An adopting repository therefore received a
  required-looking gate that tested this library, and had to work out on its own that it
  should be excluded again; at least one did exactly that, permanently, with a comment
  explaining why. It is now hand-authored in this repository alongside `ci.yml` and
  `release.yml`, which already establish that repository-specific workflows are that
  repository's to author. Adopters get neither the workflow nor the scan entry. A
  repository that had excluded it can drop that exclusion.
- Add `[ai]`, so the AI steps can be pointed at an endpoint other than Anthropic's. Every
  one of them runs Claude Code, which honours `ANTHROPIC_BASE_URL`, so a gateway serving
  the Anthropic Messages API — LiteLLM and similar translate it to Gemini, Qwen, GitHub
  Models, or a model on your own hardware — is the whole of what it takes. Teaching five
  workflows a second vendor's request shape would buy nothing the gateway does not.
  `base_url` empty keeps the current endpoint, so nothing changes until asked, and
  `auth_secret` names a repository secret rather than carrying a token, because this file
  is committed. All seven call sites carry the hook, asserted by a test: a missed one
  would keep billing the original endpoint silently. The whole `env:` block is emitted or
  omitted rather than set empty, since an empty `ANTHROPIC_BASE_URL` points at nothing
  rather than at the default, and the secret fills both header conventions because Claude
  Code sends `x-api-key` while some gateways read `Authorization`.

- Install the packages a documentation site actually declares. The published-site build
  named exactly `properdocs` and its theme, with no way to extend the list, and ProperDocs
  depends on none of the plugins a real site configures — so a repository whose
  `properdocs.yml` used `mkdocs-gen-files`, `mkdocs-literate-nav`, a Material theme, or any
  `pymdownx.*` extension failed the `--strict` build on the first one it reached. Adding
  them was impossible without forking the workflow. `[documentation].site_requirements`
  now extends the install, a `site_requirements_file` (`docs/requirements.txt` by
  convention) is installed when present, and `properdocs_version` is no longer hardcoded.
  Each requirement is shell-quoted, so a specifier carrying spaces or extras stays one
  argument; a newline in one is refused at load time rather than quoted away, since it
  would otherwise end the install line and begin an arbitrary command. Both hooks are
  no-ops by default.
- Remove `README_SECTIONS`, `GITHUB_README_SECTIONS`, and `MERMAID_REQUIRED_TERMS` from
  `vibey_gh.documentation`, along with their unreferenced twins in `vibey_gh.config`. The
  documentation contract became configuration, and these were the literal copies left
  behind — importable, but describing *this* project's docs, which is exactly what an
  adopter is not held to. A repository wanting these headings declares them under
  `[documentation]`. `README_PROVENANCE` is unaffected and still enforced.
- Require checks that can actually report, and keep a way out when they cannot. The
  default `required_checks` were built from `scan_workflows`, which names *workflows*; a
  required status check names a *check run*, which for Actions is the job's name. So a
  fresh install demanded "CI", "Docs", and "API drift (Cloud Agents OpenAPI)" — three
  contexts nothing produces. That does not fail, it waits: the branch reports "N of M
  required status checks are expected" forever. And because a ruleset has no "include
  administrators" toggle the way the branch protection it replaced did, an empty
  `bypass_actors` meant nobody could merge past it, owner included. The defaults now name
  jobs the bundled templates actually render, `bypass_actors` defaults to the repository
  admin role, and a test asserts every default check is a job some template renders.
- Actually send the ruleset request body. `gh api` ignores stdin unless told to read it, so
  every reconciliation failed with HTTP 422 "data cannot be null" while the payload it had
  built was perfectly good — it simply never left the process.
- Merge the integration branch forward locally when GitHub refuses to. Its update-branch
  endpoint declines a branch it considers conflicting, which is exactly when a branch needs
  moving forward, and it computes that without this repository's merge drivers — so a
  changelog every branch appends to conflicts there while merging cleanly here. The
  fallback is an ordinary merge commit pushed without force: the branch moves forward and
  is never rewritten, and forks stay untouched.
- Report why an update was refused instead of "no detail reported".

- Identify a comment the same way whichever GitHub API produced it. A webhook numbers a
  comment; `gh issue view` returns a GraphQL node instead. They name the same comment and
  never match each other, and `int("IC_kwDO...")` raises — so the first real mention ever
  sent to the conversation feature crashed before it could answer. The numeric form,
  recovered from the comment's own URL when only the node is given, is now the single
  identity stored and compared.
- Rename the mention trigger to `@vibey-gh`, matching the tool's own name.
- Stop imposing this project's documentation contract on the repositories that install it.
  A project using vibey-gh as a dependency was required to carry a `## Why vibey-gh`
  heading in its own product README, this tool's branded provenance sentence verbatim, an
  and an architecture diagram naming this tool's modules — none of which describe the
  adopter's product. Those narrative requirements are now configuration with no default, so
  an adopter declares what *their* documentation must contain. The agent-docs layout still
  applies to every managed repository, because those files describe the adopter's own
  project and make it navigable to an agent; only their vibey-gh-specific contents are no
  longer demanded. This repository's own contract is unchanged: it declares the narrative
  requirements explicitly in its `.vibey-gh.toml`, so its internals stay fully documented
  and enforced.
- Make the generated release commit a Conventional Commit. `Release 1.23.0` does not stay
  on the release branch: any topic branch that later merges the integration branch in pulls
  it into its own commit range, where the provenance gate reads it like any other commit
  and rejects the subject. That blocked a pull request outright, and bounded repair could
  not fix it because the problem was history rather than file content. Now
  `chore(release): 1.23.0`.
- Add `[install].pin_version` to pin every managed workflow's `pip install vibey-gh` to the
  exact version that rendered it (`vibey-gh==X.Y.Z`) instead of floating on the latest
  release. An adopter could not previously pin this by hand: `vibey-gh install` regenerates
  every managed file from its template, so an edited install line was reported as out of
  date and silently reverted on the next install. `vibey-gh install` now owns bumping the
  pin, so upgrading is an explicit, reviewable diff. Unset, behavior is unchanged. The
  self-hosting `pip install -e .` branch is never pinned.
- Fail `vibey-gh check` when a `[pr_automation].scan_workflows` entry names a workflow
  that exists but has no `pull_request` or `pull_request_target` trigger. Such a workflow
  can never complete for a pull request, so `state` never leaves `pending`, `gate` never
  runs, and — made a required check — no pull request could ever merge, silently and
  permanently. A name absent from `.github/workflows/` is left alone, since it may live
  elsewhere or under another name.

- Declare `CHANGELOG.md merge=union` in `.gitattributes` so branches appending to the same
  section merge instead of conflicting. Every open branch adds an Unreleased entry, so each
  merge stranded every other one on a conflict carrying no information — four manual
  resolutions in a single afternoon, and the reason automated branch reconciliation kept
  deciding to rebase and then failing to. Configurable through `[install].union_merge_paths`,
  and appended to an adopter's existing `.gitattributes` rather than rewriting it.

- Say so on the issue when a solution attempt produces nothing. An attempt that exhausted
  its turn budget left no branch, no label, and no comment, so twenty minutes and real
  tokens looked from the issue exactly like nothing having happened. The issue now receives
  one comment naming the agent's outcome and the usual cause, and is labelled so it is
  visible in a listing.
- Make the attempt's turn budget configurable through `[issue_automation].max_turns`.

- Report whether a branch reconciliation actually took effect, not merely what it decided.
  A rebase that conflicted and aborted printed exactly like one that succeeded and left the
  job green, so two stranded pull requests looked reconciled across four runs while neither
  branch had moved. The decision and its outcome are now printed separately, and a run that
  could not apply an action says how many.
- Stop `github-release.yml` from failing on a release-branch push that carries no version
  bump. A docs-only or tooling-only promotion is expected, by an adopting repository's own
  `version.content_paths`/`code_paths` configuration, to publish nothing new — `publish()`
  now treats a version already tagged at a different commit as that intentional no-op
  rather than an error, unless the new `[github_release] require_new_version` opts a
  repository into the stricter behavior.
- Answer a configured mention in a comment. Everything else here reacts to scans, issues,
  and branches; none of it could hear "also handle the empty case" written under a pull
  request. Mentioning `@vibey-gh` now has the automation read the thread and answer, and — on
  a pull request, from a trusted commenter — make the change and push one guarded commit.
  Outside commenters get no response unless a repository opts in, comment text reaches the
  model only as a bounded untrusted briefing, interactions per thread are budgeted, and the
  automation refuses to answer its own comments so a reply cannot recurse indefinitely.

- Keep a successful realign successful when its branch reconciliation cannot reach GitHub.
  Reconciliation is a follow-up that needs credentials some contexts do not have, and a
  branch left unreconciled is a nuisance rather than a reason to report the realign as
  failed and leave the caller believing the branches never converged.

- Normalize formatting deterministically in the repair job. The repair agent holds no
  shell, so it cannot run a formatter: it hand-formats, guesses the line length, fails the
  lint gate, and the next attempt reformats the other way — a loop that spends the whole
  repair budget without converging. The trusted step now runs the repository's own declared
  formatters, which read their settings from its configuration rather than from a guess.
- Reconcile the `ruff` and `isort` import rules, which were mutually unsatisfiable: each
  rejected the other's output for a module imported both plainly and under an alias, so no
  number of attempts could make such a file green. A test now proves the two agree and do
  not oscillate.

- Bring open branches forward automatically whenever the integration branch moves, so a
  conflict never accumulates. Automation-owned branches are rebased; every other branch,
  fork included, is merged forward through GitHub's own update-branch endpoint, which
  never rewrites a contributor's history and succeeds only where they enabled maintainer
  edits.
- Refill a spent repair budget on a daily schedule, itself bounded by
  `branch_sync.max_self_heals`, so a transient outage stops being a permanent halt that
  only a human notices — while a genuinely stuck pull request still stops for good.
- Terminally block any outside author's pull request whose head is a permanent branch or
  whose base is the release branch, so no untrusted work can steer automation at `develop`
  or `main` from either end.

- Reconcile open topic branches after realign rewrites the integration branch. A branch
  cut from a replaced commit previously reported a conflict covering work that had already
  landed, through nobody's fault. Realign now closes and deletes a branch whose commits are
  all upstream by patch identity, rebases an automation-owned branch that carries real
  work, and leaves a contributor's branch untouched with an explanatory comment. Every
  action is individually configurable through `[realign]`, and no permanent, fork, or
  unsafe ref can reach a mutating path.

- Resolve conflicts on draft pull requests instead of stranding them. Conflict is now
  classified before draft status: a conflicted draft could never be promoted, because
  promotion requires a clean merge, and conflict resolution never ran because it was a
  draft — so every conflicted branch-intake and issue-solution pull request deadlocked.
  Fork drafts still wait, because their conflict path closes the contributor's pull
  request.

- Bound the review-to-repair cycle for every author. The budget check sat behind an
  outside-author condition, so a trusted author's exact-head review could request repair
  after repair without limit; it is now applied wherever another review would be
  dispatched, which is the only point that is reachable while each repair publishes a new
  head.
- Persist the per-lineage attempt reset that was previously computed and discarded. A new
  human commit started a fresh lineage in the evaluation but never in the stored record, so
  the documented per-lineage budget silently behaved as a cumulative per-pull-request one.
  Both paths now share `lineage_for()` and cannot disagree.
- Add an optional, generic `[documentation] google_analytics_id` setting: configure any
  repository's own GA4 measurement ID to inject Google Analytics into every page of both
  generated documentation channels and the channel-picker page. Empty (the default)
  disables it entirely, emitting no script tag and making no request to Google.

- Fix `conventional-commits.yml` installing the adopting repository's own default-branch
  checkout and assuming that yields the `vibey-gh` CLI: it now detects genuine self-hosting
  the same way `provenance.yml` does and otherwise installs the published package, and the
  commit-conformance check fails loudly instead of treating "command not found" as a false
  `if` condition that then barrels ahead into a doomed history rewrite. Fix the same
  adopting-repo-assumption bug in four `pr-automation.yml` installation steps.
- Report the exact-head gate's outcome truthfully when the review, not the scans, decides
  it: a review that returned actionable findings and a review that returned no verdict at
  all are now distinct, named states instead of a failing check whose summary claims every
  scan and review passed.

- Add autonomous issue automation: an eligible published issue is evaluated by trusted
  policy code, implemented by a constrained agent that reads the issue only as bounded
  untrusted data, and published as one guarded solution branch and linked pull request
  that closes the issue on merge.
- Treat issue text as an adversary-controlled input to a privileged job: outside authors
  are opt-in behind a configurable maintainer label, the agent holds no shell, `gh`,
  subagent, or Git tool, and nothing derived from an issue reaches a shell command, a
  workflow expression, or a branch name.
- Budget autonomous solution attempts against a fingerprint of the issue's title and body,
  so a redispatch of unchanged text cannot spend the budget twice and editing an issue
  starts a new lineage with a new branch.
- Render `branch-intake.yml` to yield the configured issue-solution branch namespace, so
  branch intake and issue automation never race to open the same pull request.
- Extract durable marker-comment automation state into `vibey_gh.github_state`, shared by
  pull-request and issue automation instead of duplicated across them.

- Require advanced debug instrumentation for every Python control-flow branch and add
  opt-in, correlated, metadata-only JSONL tracing with tamper-evident SHA-256 chaining.
- Enforce genuine 100% line and branch coverage with pytest-cov and align all contributor
  and testing documentation with the executable gate.
- Fix a duplicated provenance header in the packaged source modules and make the
  fingerprint check detect and repair a header repeated within a file, not just a header
  that is missing.
- Treat concurrent PR-head advances during repair or conflict publication as stale no-ops
  while preserving ordinary non-fast-forward protection and never force-pushing.
- Check operator-block and budget-exhausted labels before conflict-resolution eligibility,
  so a blocked or exhausted PR no longer triggers automated conflict resolution.
- Stop flagging a marketplace plugin whose source is the repository root (`.`) as an unsafe
  external source.
- Rewrite the release-channel navigation "Home" link to the correct Pages root instead of
  leaving its `href` unset.
- Replace the placeholder GitHub automation README with a comprehensive operator guide
  and enforce its required sections, minimum depth, and exact provenance deterministically.
- Fix GraphQL-only PR-state comment updates, synchronize package version metadata,
  correct constrained Claude command patterns, and ship real managed CodeQL and
  five-surface API-drift gates.
- Validate the capability-keyed parity matrix in its documented orientation.
- Add a configurable comprehensive FOSS and multi-agent documentation contract.
- Add guarded AI documentation authoring and repair automation.
- Add configurable crawler, sitemap, SEO, structured-data, and LLM discovery surfaces.
- Enforce and safely self-heal Conventional Commit subjects on guarded topic branches.
- Require a comprehensive, current Mermaid architecture map at `docs/project.mmd`.
- Use the native GitHub workflow credential when persisting AI review and repair state.
- Run Claude Code Action from a disposable, credential-free Git context while keeping
  untrusted pull-request checkouts isolated from repository credentials.
- Add configurable sanitized Claude progress, restricted execution artifacts, and a
  fail-closed manual raw-output diagnostic restricted to private repositories.
- Keep promotion PR checks non-destructive: skip topic-history normalization for
  permanent branches and verify repository provenance without re-auditing admitted history.
- Give repair agents a bounded trusted diagnostic bundle containing exact-head failed
  check metadata and available failed-job logs before they classify or edit anything.
- Satisfy Claude Code Action's required `origin` through its token-free credential-helper
  path without authorizing non-write actors or persisting a token in Git configuration.
- Gate Claude progress comments to the direct PR and issue event types supported by the
  action, preserving phase-level visibility for automated workflow events.

## Historical releases

See GitHub Releases for versioned notes, tags, artifacts, and provenance attestations.
